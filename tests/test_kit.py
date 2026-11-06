import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import reference
import doctor
import verify
from client import Client, ToolError


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class KitTests(unittest.TestCase):
    def test_offline_verification(self):
        self.assertEqual(verify.verify(), [])

    def test_live_smoke_requires_explicit_opt_in(self):
        result = subprocess.run([sys.executable, str(ROOT/'tools/live_smoke.py'),
                                 '--bridge', 'not-a-real-bridge'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--allow-disposable-edits', result.stderr)

    def test_member_lookup(self):
        record = reference.lookup_class('flLayer', 'addComponent')
        self.assertIn('QTransform', record['m'])
        self.assertEqual(reference.lookup_class('flInstance', 'tfn')['pd']['access'], 'read')
        self.assertIn('s', reference.lookup_class('flItems', 'notifyChangesApplied'))
        with self.assertRaises(ValueError): reference.lookup_class('NoSuchClass')

    def test_vfj_references_and_search(self):
        result = reference.lookup_vfj('glyph')['schema']
        self.assertIn('component', result['$defs'])
        for item in verify.walk(result):
            if isinstance(item, dict) and '$ref' in item:
                self.assertIn(item['$ref'][8:], result['$defs'])
        results = reference.search('glyph', limit=2)
        self.assertEqual(len(results['results']), 2)
        self.assertTrue(results['truncated'])

    def test_preview_refuses_unadvertised_dry_run(self):
        module = load('preview', 'examples/preview_construction.py')
        class Fake:
            def __init__(self, supported): self.supported = supported; self.calls = []
            def tools(self): return [{'name':'build_glyph', 'inputSchema':{'properties':{'dry_run':{'type':'boolean'}} if self.supported else {}}}]
            def call(self, name, **args): self.calls.append((name,args)); return {'status':'validated'}
        unavailable = Fake(False)
        with self.assertRaises(RuntimeError): module.preview(unavailable, 1, 'A', 'Regular', '=B')
        self.assertEqual(unavailable.calls, [])
        available = Fake(True); module.preview(available, 1, 'A', 'Regular', '=B')
        self.assertTrue(available.calls[0][1]['dry_run'])
        self.assertFalse(available.calls[0][1]['replace'])

    def test_capability_comparison(self):
        actual = [{'name':'a','inputSchema':{'type':'object'}},{'name':'new','inputSchema':{}}]
        expected = [{'name':'a','inputSchema':{}},{'name':'missing','inputSchema':{}}]
        self.assertEqual(doctor.compare_tools(actual, expected), {
            'missing_from_installed':['missing'],'additional_installed':['new'],'schema_differences':['a']})

    def test_manifest_detects_changed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'README.md').write_text('original')
            verify.write_manifest(root); (root/'README.md').write_text('changed')
            self.assertIn('Manifest mismatch: README.md', verify.verify(root))


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.script = Path(self.temp.name)/'bridge.py'
        self.script.write_text('''import json,sys,time
for line in sys.stdin:
    request=json.loads(line)
    if 'id' not in request: continue
    method=request['method']
    if method=='initialize': result={'protocolVersion':'2024-11-05'}
    elif method=='tools/list': result={'tools':[{'name':'list_fonts','inputSchema':{'type':'object'}}]}
    else:
        name=request['params']['name']
        if name=='wait': time.sleep(10)
        result={'content':[{'type':'text','text':json.dumps({'fonts':[]})}]}
        if name=='bad': result={'isError':True,'content':[{'type':'text','text':'Expected test failure'}]}
    print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}),flush=True)
''')
        original = subprocess.Popen
        self.patcher = patch('client.subprocess.Popen', side_effect=lambda command, **kwargs:
                             original([sys.executable, str(self.script)], **kwargs))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop(); self.temp.cleanup()

    def test_discovery_read_and_error(self):
        with Client('fake-test-bridge', timeout=3) as client:
            self.assertEqual(client.tools()[0]['name'], 'list_fonts')
            self.assertEqual(client.call('list_fonts'), {'fonts':[]})
            with self.assertRaises(ToolError): client.call('bad')

    def test_timeout_closes_without_retry(self):
        client = Client('fake-test-bridge', timeout=.2)
        try:
            with self.assertRaises(TimeoutError): client.call('wait')
            self.assertTrue(client._closed)
        finally: client.close()


if __name__ == '__main__': unittest.main()
