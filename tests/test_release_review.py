import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import verify
import package
import sync_references


def fixture(directory, name='kit'):
    root = Path(directory)/name
    root.mkdir()
    for source in verify.shipped_files(ROOT):
        target = root/source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    verify.write_manifest(root)
    return root


class ReleaseChecks(unittest.TestCase):
    def test_missing_required_file_not_hidden_by_new_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (root/'config/agents.example.yml').unlink()
            verify.write_manifest(root)
            self.assertIn('Missing required release file: config/agents.example.yml', verify.verify(root))

    def test_heading_links_and_path_containment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (Path(tmp)/'outside.md').write_text('# Outside\n')
            with (root/'README.md').open('a') as stream:
                stream.write('\n[broken](docs/SETUP.md#missing-heading)\n[escape](../outside.md)\n')
            errors = verify.verify(root, check_manifest=False)
            self.assertTrue(any(e.startswith('Broken heading link:') for e in errors))
            self.assertTrue(any(e.startswith('Link escapes kit:') for e in errors))
            self.assertEqual(verify.anchors('# Same title\n## Same title\n'), {'same-title','same-title-1'})

    def test_directory_and_dangling_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (Path(tmp)/'outside').mkdir()
            try:
                (root/'linked-dir').symlink_to(Path(tmp)/'outside', target_is_directory=True)
                (root/'missing-link').symlink_to(Path(tmp)/'absent')
            except (OSError, NotImplementedError):
                self.skipTest('Symlink creation unavailable on this platform')
            errors = verify.verify(root, check_manifest=False)
            self.assertIn('Symlink not allowed: linked-dir', errors)
            self.assertIn('Symlink not allowed: missing-link', errors)
            with self.assertRaises(ValueError): verify.write_manifest(root)

    def test_corrupt_manifest_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (root/'manifest.json').write_text('{broken')
            self.assertTrue(any(e.startswith('Invalid or missing manifest:') for e in verify.verify(root)))

    def test_appendix_drift_is_detected_even_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            path = root/'Resources/chat_system_prompt_appendix.md'
            path.write_text(path.read_text().replace('get_vfj_schema\tR\t', 'get_vfj_schema\tM\t'))
            verify.write_manifest(root)
            self.assertIn('Chat appendix: text/JSON MCP contract mismatch', verify.verify(root))

    def test_mcp_argument_drift_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            path = root/'docs/mcp/fontlab-mcp.json'
            data = json.loads(path.read_text())
            tool = next(t for t in data['tools'] if t['name']=='set_glyph')
            tool['inputSchema']['required'].remove('glyph_data')
            path.write_text(json.dumps(data))
            errors = verify.verify(root, check_manifest=False)
            self.assertTrue(any('native MCP argument/description/effect mismatch: set_glyph' in e for e in errors))

    def test_decoded_json_privacy_and_local_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            personal = '/' + 'Users' + '/' + 'example' + '/private.txt'
            credential = 'sk-' + 'A'*32
            # Unicode escapes must not bypass checks, and reports never echo values.
            payload = json.dumps({'path':personal,'api_key':credential}).replace('A', '\\u0041')
            (root/'leak.json').write_text(payload)
            (root/'config/host.local.json').write_text('{}')
            errors = verify.verify(root, check_manifest=False)
            self.assertTrue(any('Personal filesystem path in JSON:' in e for e in errors))
            self.assertTrue(any('Credential-valued JSON field:' in e for e in errors))
            self.assertTrue(any('Local configuration must not be shipped:' in e for e in errors))
            self.assertFalse(any(credential in e or personal in e for e in errors))


class ReleaseOperations(unittest.TestCase):
    def test_invalid_incoming_reference_keeps_kit_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            source = fixture(tmp, 'source')
            path = source/'Resources/fontlab_python_api_chat.json'
            data = json.loads(path.read_text()); data['mcp'].pop('get_vfj_schema')
            path.write_text(json.dumps(data))
            before = {p.relative_to(root):verify.digest(p) for p in root.rglob('*') if p.is_file()}
            with patch('sync_references.subprocess.check_output', side_effect=['0'*40,'']):
                with self.assertRaisesRegex(ValueError, 'Staged reference validation failed'):
                    sync_references.sync(source, root)
            after = {p.relative_to(root):verify.digest(p) for p in root.rglob('*') if p.is_file()}
            self.assertEqual(before, after)

    def test_sync_preserves_public_adaptations_and_validates_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            source = fixture(tmp, 'source')
            path = source/'docs/mcp/fontlab-mcp.json'
            data = json.loads(path.read_text()); data['source_sha256'] = {'private.cpp':'0'*64}
            data['compatibility']['basis'] = 'internal issue reference'
            path.write_text(json.dumps(data))
            with patch('sync_references.subprocess.check_output', side_effect=['0'*40,'']):
                sync_references.sync(source, root)
            self.assertEqual(verify.verify(root), [])
            self.assertEqual(json.loads((root/'SOURCE.json').read_text())['license'], 'MIT')
            result = json.loads((root/'docs/mcp/fontlab-mcp.json').read_text())
            self.assertNotIn('source_sha256', result)
            self.assertEqual(result['compatibility']['basis'], sync_references.PUBLIC_BASIS)

    def test_clean_archive_has_exact_manifest_contents_and_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp)
            (root/'reports').mkdir(); (root/'reports/local.txt').write_text('local report excluded')
            first, second = Path(tmp)/'first.zip', Path(tmp)/'second.zip'
            package.build_archive(first, root)
            package.build_archive(second, root)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            manifest = json.loads((root/'manifest.json').read_text())['files']
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(set(archive.namelist()), {'fontlab-aidus-kit/'+n for n in manifest}|{'fontlab-aidus-kit/manifest.json'})
                for name, value in manifest.items():
                    self.assertEqual(hashlib.sha256(archive.read('fontlab-aidus-kit/'+name)).hexdigest(), value)
            with self.assertRaises(FileExistsError): package.build_archive(first, root)

    def test_packager_rejects_tampered_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fixture(tmp); (root/'README.md').write_text('tampered')
            archive = Path(tmp)/'bad.zip'
            with self.assertRaisesRegex(ValueError, 'Release verification failed'):
                package.build_archive(archive, root)
            self.assertFalse(archive.exists())


if __name__ == '__main__': unittest.main()
