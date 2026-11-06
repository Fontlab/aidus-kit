#!/usr/bin/env python3
"""Opt-in live integration test. Creates/edits/closes only its own disposable font."""
from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'docs/mcp'))
from client import Client, ToolError


async def sdk_read(bridge, font_id):
    # Optional: run with the installed Aidus Core interpreter to test its SDK.
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    async with stdio_client(StdioServerParameters(command=str(bridge))) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            if 'get_glyph' not in {tool.name for tool in tools.tools}:
                raise RuntimeError('Aidus SDK session lacks get_glyph')
            result = await session.call_tool('get_glyph', {'font_id':font_id,'glyph_name':'A'})
            if result.isError: raise RuntimeError('Aidus SDK glyph read failed')
            data = json.loads(result.content[0].text)
            if data['layers'][0]['advanceWidth'] != 650:
                raise RuntimeError('Aidus SDK readback differs')


def check(condition, message):
    if not condition: raise RuntimeError(message)


def run(bridge, aidus_sdk=False):
    if aidus_sdk:
        import mcp  # Fail before creating any font if the optional dependency is absent.
    passed = []
    family = 'Aidus kit disposable ' + uuid.uuid4().hex
    with Client(bridge) as client:
        before = client.call('list_fonts')
        previous = None
        try: previous = client.call('get_active_font')['id']
        except ToolError: pass
        owned = set()
        def call(name, **args): return client.call(name, **args)
        try:
            tools = {tool['name']:tool for tool in client.tools()}
            required = {'new_font','close_font','set_active_font','get_glyph','get_vfj_schema',
                        'set_glyph','list_glyphs','build_glyph','save_font','open_font','run_python'}
            check(required <= tools.keys(), 'Installed build lacks required test tools')
            for name in ('set_glyph','build_glyph'):
                check(tools[name]['inputSchema']['properties'].get('dry_run',{}).get('type')=='boolean',
                      name+' does not advertise dry_run; refusing test')
            font_id = call('new_font',family_name=family,style_name='Regular')['font']['id']
            owned.add(font_id)
            glyph = {'name':'A','unicode':'0041','layers':[{'name':'Regular','advanceWidth':600,
                'elements':[{'elementData':{'contours':[{'nodes_list':[
                    {'x':0,'y':0},{'x':300,'y':0},{'x':300,'y':500},{'x':0,'y':500}]}]}}]}]}
            call('get_vfj_schema',topic='glyph'); passed.append('schema discovery')
            # New fonts may already contain default glyphs: compare to the actual baseline.
            baseline = call('list_glyphs',font_id=font_id)
            call('set_glyph',font_id=font_id,glyph_name='A',create=True,glyph_data=glyph,dry_run=True)
            check(call('list_glyphs',font_id=font_id)==baseline,'Dry run changed glyph inventory')
            passed.append('dry-run inventory preservation')
            call('set_glyph',font_id=font_id,glyph_name='A',create=True,glyph_data=glyph)
            probe = ('import fontlab as fl; import fontpr; p=fl.flPackage(fl.CurrentFont()); '
                     'assert int(p.fgId)==%d; assert fontpr.available(); '
                     "print(len(p.findName('A').findLayer('Regular').shapes[0].contours[0].nodes()))") % int(font_id)
            result = call('run_python',code='exec('+repr(probe)+', {})')
            check(result.get('success') and result.get('stdout','').strip()=='4','Embedded Python read failed')
            passed.append('embedded Python and fontpr inspection')
            data = call('get_glyph',font_id=font_id,glyph_name='A')
            data['layers'][0]['advanceWidth']=650
            call('set_glyph',font_id=font_id,glyph_name='A',glyph_data=data)
            check(call('get_glyph',font_id=font_id,glyph_name='A')['layers'][0]['advanceWidth']==650,'Edit readback failed')
            passed.append('create edit readback')
            call('build_glyph',font_id=font_id,glyph_name='A.copy',layer_name='Regular',recipe='=A',dry_run=True)
            passed.append('construction preview')
            with tempfile.TemporaryDirectory(prefix='aidus-kit-font-') as directory:
                path = str(Path(directory)/'disposable.vfj')
                call('save_font',font_id=font_id,path=path)
                call('close_font',font_id=font_id,save=False); owned.remove(font_id)
                # open_font returns status/path/errors, not a font summary.
                call('open_font',path=path)
                candidates = [f for f in call('list_fonts')['fonts'] if f.get('family_name')==family]
                owned.update(f['id'] for f in candidates)
                check(len(candidates)==1,'Could not identify reopened disposable font uniquely')
                font_id = candidates[0]['id']
                check(call('get_glyph',font_id=font_id,glyph_name='A')['layers'][0]['advanceWidth']==650,'Reopened data differs')
                passed.append('save reopen preservation')
                if aidus_sdk:
                    asyncio.run(asyncio.wait_for(sdk_read(bridge,font_id),60))
                    passed.append('Aidus-installed MCP SDK read')
                call('close_font',font_id=font_id,save=False); owned.remove(font_id)
        finally:
            # Recover our uniquely named font even if creation/open returned unexpectedly.
            owned.update(f['id'] for f in call('list_fonts')['fonts'] if f.get('family_name')==family)
            for font_id in owned: call('close_font',font_id=font_id,save=False)
            if previous is not None: call('set_active_font',font_id=previous)
        check(call('list_fonts')==before,'Original font inventory/active state differs after cleanup')
        passed.append('original font inventory restored')
    return {'passed':passed,'provider_calls':0,'user_font_edits':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bridge',required=True,type=Path)
    parser.add_argument('--allow-disposable-edits',action='store_true')
    parser.add_argument('--aidus-sdk',action='store_true')
    args=parser.parse_args()
    if not args.allow_disposable_edits:
        parser.error('Live edits require --allow-disposable-edits; use doctor.py for read-only checks')
    print(json.dumps(run(args.bridge,args.aidus_sdk),indent=2))


if __name__=='__main__': main()
