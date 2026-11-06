#!/usr/bin/env python3
"""Stage, validate and refresh allowlisted references from an authorized checkout."""
from __future__ import annotations
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from verify import ROOT, shipped_files, digest, verify, write_manifest

RESOURCES = ['fontlab_python_api.json', 'fontlab_python_api.llm.md', 'fontlab_python_api_chat.json',
             'chat_system_prompt_appendix.md', 'fontlab_python_agent_guide.md', 'fontlab_action_catalog.json', 'vfj_schema.json']
MCP = ['GUIDE.md', 'LLM.md', 'fontlab-mcp.json', 'VFJ.md', 'client.py']
RELATIVES = ['Resources/'+name for name in RESOURCES] + ['docs/mcp/'+name for name in MCP]
PUBLIC_BASIS = ('Source-derived FontLab snapshot recorded in SOURCE.json, including local changes; '
                'not tied to a released build number. Discover installed tools and schemas before use.')
PUBLIC_LEGACY = ('Older installations can differ in save behavior, error reporting and master targeting. '
                 'Use a matching application/bridge pair and verify the required workflow on disposable data.')


def adapt_public(candidate):
    guide = candidate/'Resources/fontlab_python_agent_guide.md'
    text = guide.read_text(encoding='utf-8')
    text = re.sub(r'\[([^]]+)\]\((\.\./(?:workspace2|pygate|common|tests)/[^)]+)\)',
                  r'[\1](../docs/PROVENANCE.md#source-references)', text)
    text = text.replace('(fontlab_python_mcp_spec.md)', '(../docs/SETUP.md)')
    for name in ('scripting-api-fixes.md', 'scripting-crash-fixes.md'):
        text = text.replace('(../docs/' + name + ')', '(../docs/PROVENANCE.md#source-references)')
    guide.write_text(text, encoding='utf-8')
    guide = candidate/'docs/mcp/GUIDE.md'
    text = guide.read_text(encoding='utf-8').replace('(../../common/mcp/SETUP.md)', '(../SETUP.md)').replace('(../../common/mcp/VERIFICATION.md)', '(../VERIFICATION.md)')
    intro = ('# Using FontLab’s MCP\n\nThis is a source-derived reference snapshot, not a promise that every '
             'installed FontLab 9 release contains these capabilities. See [provenance](../PROVENANCE.md). '
             'Use a matching application/bridge pair and compare installed `tools/list` with this reference. '
             '`serverInfo.version` is not a feature version.\n\n')
    if '- **For people:**' in text:
        text = intro + text[text.index('- **For people:**'):]
    start = text.find('The generated documents combine exact')
    end = text.find('## VFJ schema discovery and validation', start)
    if start != -1 and end != -1:
        text = text[:start] + ('Reference maintenance is documented in [MAINTAINING.md](../MAINTAINING.md). '
            'The public kit includes `SOURCE.json` for origin and `manifest.json` for shipped-file hashes. '
            'Private source-file checksums and source-only generators are not included here.\n\n') + text[end:]
    text = re.sub(r'Regression checks: `python3 tests/test_vfj_schema.py`,.*?temporary fonts\.',
                  'For this kit, run `python3 tools/verify.py` and `python3 -m unittest discover -s tests -v` '
                  'from the kit root. Source-only native regressions require an authorized source checkout; '
                  'see [verification](../VERIFICATION.md).', text, flags=re.S)
    guide.write_text(text, encoding='utf-8')
    path = candidate/'docs/mcp/fontlab-mcp.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data.pop('source_sha256', None)
    data['compatibility']['basis'] = PUBLIC_BASIS
    data['compatibility']['legacy'] = PUBLIC_LEGACY
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    path = candidate/'docs/mcp/LLM.md'
    text = path.read_text(encoding='utf-8')
    text, count = re.subn(r'(## Compatibility\s*\n\s*```json\n).*?(\n```)',
                          lambda match: match[1]+json.dumps(data['compatibility'],ensure_ascii=False,indent=2)+match[2],
                          text, count=1, flags=re.S)
    if count != 1: raise ValueError('Missing compatibility block in MCP agent reference')
    path.write_text(text, encoding='utf-8')


def sync(source, root=ROOT):
    source, root = Path(source).resolve(), Path(root).resolve()
    for name in RELATIVES:
        path = source/name
        if not path.is_file(): raise ValueError('Source reference missing: ' + name)
        if any(item.is_symlink() for item in [path, *path.parents] if item != source and item.is_relative_to(source)):
            raise ValueError('Refusing symlinked source reference: ' + name)
    revision = subprocess.check_output(['git','rev-parse','HEAD'], cwd=source, text=True).strip()
    modified = bool(subprocess.check_output(['git','status','--porcelain'], cwd=source, text=True).strip())
    originals = {path.relative_to(root).as_posix(): digest(path) for path in shipped_files(root)}
    if (root/'manifest.json').exists(): originals['manifest.json'] = digest(root/'manifest.json')
    with tempfile.TemporaryDirectory(prefix='aidus-sync-') as directory:
        candidate = Path(directory)/'kit'; candidate.mkdir()
        for name in originals:
            target = candidate/name; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root/name, target)
        for name in RELATIVES: shutil.copyfile(source/name, candidate/name)
        adapt_public(candidate)
        origin = {'snapshot_date': date.today().isoformat(), 'fontlab_source_revision': revision,
                  'source_worktree_modified': modified, 'python_runtime_claim': 'source capabilities, not installed runtime introspection',
                  'api_overlay': 'current Python binding registrations plus marked historical introspection fallback',
                  'license': json.loads((root/'SOURCE.json').read_text(encoding='utf-8')).get('license', 'MIT')}
        (candidate/'SOURCE.json').write_text(json.dumps(origin, indent=2)+'\n', encoding='utf-8')
        errors = verify(candidate, check_manifest=False)
        if errors: raise ValueError('Staged reference validation failed; kit unchanged:\n' + '\n'.join(errors))
        write_manifest(candidate)
        # Do not replace files someone edited while the snapshot was being checked.
        current = {path.relative_to(root).as_posix(): digest(path) for path in shipped_files(root)}
        if (root/'manifest.json').exists(): current['manifest.json'] = digest(root/'manifest.json')
        if current != originals:
            raise ValueError('Kit changed during synchronization; no files replaced')
        for name in [*RELATIVES, 'SOURCE.json', 'manifest.json']:
            destination = root/name
            handle, temporary = tempfile.mkstemp(prefix='.aidus-sync-', dir=destination.parent)
            os.close(handle)
            try:
                shutil.copyfile(candidate/name, temporary)
                os.replace(temporary, destination)
            finally:
                if os.path.exists(temporary): os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    args = parser.parse_args()
    try: sync(args.source)
    except (ValueError, OSError, subprocess.SubprocessError) as exc: parser.error(str(exc))
    print('Validated and refreshed allowlisted references. Run tests before release.')


if __name__ == '__main__':
    main()
