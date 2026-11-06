#!/usr/bin/env python3
"""Offline checks of release files, local links, and reference consistency."""
from __future__ import annotations
import argparse
import ast
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {".git", "__pycache__", ".venv", "dist", "reports"}
REQUIRED = {
    'README.md', 'AGENTS.md', 'LICENSE.md', 'SECURITY.md', 'SOURCE.json', 'pyproject.toml',
    'docs/SETUP.md', 'docs/ARCHITECTURE.md', 'docs/MAINTAINING.md', 'docs/PROVENANCE.md',
    'docs/VERIFICATION.md', 'docs/RELEASE.md', 'prompts/AIDUS.md',
    'config/README.md', 'config/mcp.example.json', 'config/aidus_config.example.json',
    'config/agents.example.yml', 'tools/verify.py', 'tools/reference.py', 'tools/doctor.py',
    'tools/sync_references.py', 'tools/package.py', 'tools/live_smoke.py', 'docs/INSTALLED_TEST.md', 'examples/README.md',
    'examples/inspect_font.py', 'examples/preview_construction.py', 'examples/embedded_inspect.py',
    'tests/test_kit.py',
}
REQUIRED.update('Resources/' + name for name in (
    'fontlab_python_api.json', 'fontlab_python_api.llm.md', 'fontlab_python_api_chat.json',
    'chat_system_prompt_appendix.md', 'fontlab_python_agent_guide.md',
    'fontlab_action_catalog.json', 'vfj_schema.json'))
REQUIRED.update('docs/mcp/' + name for name in ('GUIDE.md', 'LLM.md', 'fontlab-mcp.json', 'VFJ.md', 'client.py'))


def inventory(root=ROOT):
    """Never follow file, directory or dangling symlinks when examining a release."""
    files, errors = [], []
    def visit(directory):
        for path in sorted(directory.iterdir()):
            relative = path.relative_to(root).as_posix()
            if path.name in EXCLUDED_DIRS or path.name == '.DS_Store':
                continue
            if path.is_symlink():
                errors.append('Symlink not allowed: ' + relative)
            elif path.is_dir():
                visit(path)
            elif path.is_file():
                if path.name != 'manifest.json': files.append(path)
            else:
                errors.append('Unsupported filesystem entry: ' + relative)
    visit(root)
    return sorted(files), errors


def shipped_files(root=ROOT):
    files, errors = inventory(root)
    if errors: raise ValueError('; '.join(errors))
    return files


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root=ROOT):
    record = {'format_version': 1, 'files': {path.relative_to(root).as_posix(): digest(path) for path in shipped_files(root)}}
    temporary = root/'manifest.json.tmp'
    temporary.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temporary.replace(root/'manifest.json')


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values(): yield from walk(child)
    elif isinstance(value, list):
        for child in value: yield from walk(child)


def without_fences(text):
    return re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', text)


def anchors(text):
    text = without_fences(text)
    result, counts = set(), {}
    for title in re.findall(r'(?m)^#{1,6}\s+(.+?)\s*#*$', text):
        title = html.unescape(re.sub(r'<[^>]*>', '', title)).lower()
        slug = re.sub(r'[^\w\- ]', '', title).replace(' ', '-')
        index = counts.get(slug, 0); counts[slug] = index + 1
        result.add(slug if not index else slug + '-' + str(index))
    result.update(re.findall(r'<a\s+(?:name|id)=["\']([^"\']+)', text, re.I))
    return result


def markdown_errors(path, text, root, texts):
    errors = []
    visible = without_fences(text)
    targets = re.findall(r'\]\(([^)\n]+)\)', visible)
    targets += re.findall(r'(?m)^\s*\[[^]]+\]:\s+(\S+)', visible)
    for raw in targets:
        target = raw.strip().strip('<>')
        parts = urlsplit(target)
        if parts.scheme or parts.netloc: continue
        linked = (path.parent/unquote(parts.path)).resolve() if parts.path else path.resolve()
        label = path.relative_to(root).as_posix() + ' -> ' + target
        if not linked.is_relative_to(root.resolve()):
            errors.append('Link escapes kit: ' + label); continue
        if not linked.exists():
            errors.append('Broken local link: ' + label); continue
        if parts.fragment and linked.suffix.lower() == '.md':
            content = texts.get(linked)
            if content is None:
                errors.append('Link points to a non-release file: ' + label)
            elif unquote(parts.fragment) not in anchors(content):
                errors.append('Broken heading link: ' + label)
    return errors


def sections(text):
    result, current = {}, None
    for line in text.splitlines():
        if line.startswith('[') and ']' in line:
            current = line[1:line.index(']')]; result[current] = []
        elif current and line:
            result[current].append(line)
    return result


def text_reference_errors(text, data, label):
    errors = []
    blocks = sections(text)
    mcp_rows = {line.split('\t', 1)[0]: line for line in blocks.get('mcp', [])}
    expected_rows = {name: '\t'.join((name, 'M' if entry.get('m') else 'R', ','.join(entry['r']), entry['d']))
                     for name, entry in data['mcp'].items()}
    if mcp_rows != expected_rows: errors.append(label + ': text/JSON MCP contract mismatch')
    class_names = {name[6:] for name in blocks if name.startswith('class:')}
    if class_names != set(data['c']): errors.append(label + ': text/JSON class inventory mismatch')
    for name, record in data['c'].items():
        lines = blocks.get('class:' + name, [])
        for kind in ('m', 's'):
            actual = dict(line[2:].split('\t', 1) for line in lines if line.startswith(kind+':') and '\t' in line)
            if actual != record.get(kind, {}): errors.append(label + ': text/JSON ' + kind + ' mismatch in ' + name)
        props, details = [], {}
        for line in lines:
            if not line.startswith('p:'): continue
            if '\t' not in line: props = line[2:].split(',') if line[2:] else []
            else:
                values = line[2:].split('\t', 2)
                details[values[0]] = {'access': values[1], 'd': values[2] if len(values)>2 else ''}
        if props != record.get('p', []) or details != record.get('pd', {}):
            errors.append(label + ': text/JSON property mismatch in ' + name)
    return errors


def verify(root=ROOT, check_manifest=True):
    root = Path(root)
    files, errors = inventory(root)
    relative_files = {path.relative_to(root).as_posix() for path in files}
    for missing in sorted(REQUIRED-relative_files): errors.append('Missing required release file: ' + missing)
    # Do not read through unsafe trees, including a symlinked manifest.
    if any(error.startswith('Symlink') for error in errors): return errors
    if check_manifest:
        try:
            manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
            expected = manifest['files']
            if manifest.get('format_version') != 1 or not isinstance(expected, dict):
                raise ValueError('unsupported manifest format')
            if any(not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts
                   or not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value)
                   for name, value in expected.items()):
                raise ValueError('invalid manifest file entry')
            actual = {path.relative_to(root).as_posix(): digest(path) for path in files}
            for name in sorted(set(expected) | set(actual)):
                if expected.get(name) != actual.get(name): errors.append('Manifest mismatch: ' + name)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append('Invalid or missing manifest: ' + str(exc))
    personal = re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/|[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9_.-]+[\\/]')
    secret = re.compile(r'(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    texts = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() in {'.vfj','.vfc','.vfb','.ttf','.otf','.woff','.woff2','.pem','.key','.p12','.pfx'}:
            errors.append('Font or private-key data must not be shipped: ' + relative)
        if any(part.lower().endswith(('.ufo','.vfjp')) for part in path.relative_to(root).parts):
            errors.append('Font package must not be shipped: ' + relative)
        basename = path.name.lower()
        if basename == '.env' or basename.startswith('.env.') or basename == 'aidus_config.json' or '.local.' in basename:
            errors.append('Local configuration must not be shipped: ' + relative)
        try: text = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            errors.append('Unexpected binary or unreadable file: ' + relative); continue
        texts[path.resolve()] = text
        if personal.search(text): errors.append('Personal filesystem path: ' + relative)
        if secret.search(text): errors.append('Credential-like content: ' + relative)
        try:
            if path.suffix == '.json':
                data = json.loads(text)
                for value in walk(data):
                    if isinstance(value, str):
                        if personal.search(value): errors.append('Personal filesystem path in JSON: ' + relative)
                        if secret.search(value): errors.append('Credential-like JSON content: ' + relative)
                    if isinstance(value, dict):
                        for key, item in value.items():
                            if re.fullmatch(r'(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|authorization)', key, re.I) and isinstance(item, str) and item:
                                if not item.startswith(('env:', '<', 'YOUR_', 'PLACEHOLDER')):
                                    errors.append('Credential-valued JSON field: ' + relative)
            if path.suffix == '.py': ast.parse(text, filename=relative)
        except (ValueError, SyntaxError) as exc: errors.append(relative + ': ' + str(exc))
    for path in files:
        if path.suffix.lower() == '.md' and path.resolve() in texts:
            errors += markdown_errors(path, texts[path.resolve()], root, texts)
    try:
        def read(name): return json.loads(texts[(root/name).resolve()])
        full, chat = read('Resources/fontlab_python_api.json'), read('Resources/fontlab_python_api_chat.json')
        mcp = read('docs/mcp/fontlab-mcp.json')
        tools = {tool['name']:tool for tool in mcp['tools']}
        if len(tools) != len(mcp['tools']): errors.append('Duplicate MCP tool names')
        if set(full['mcp']) != set(tools) or set(chat['mcp']) != set(tools): errors.append('MCP tool sets differ across catalogs')
        for name, tool in tools.items():
            schema = tool['inputSchema']; required = set(schema.get('required', []))
            args = [key + ('' if key in required else '?') for key in schema.get('properties', {})]
            effect = tool['effect']; mutates = not effect.startswith('read') and effect != 'pure calculation'
            for label, data in [('full',full), ('chat',chat)]:
                entry = data['mcp'].get(name, {})
                if entry.get('r') != args or entry.get('d') != tool['description'] or bool(entry.get('m')) != mutates:
                    errors.append(label + ': native MCP argument/description/effect mismatch: ' + name)
        for name in chat['c']:
            for kind in ('m','s','pd'):
                for member, value in chat['c'][name].get(kind, {}).items():
                    if full['c'][name].get(kind, {}).get(member) != value:
                        errors.append('Chat/full member mismatch: ' + name + '.' + member)
            if not set(chat['c'][name].get('p', [])) <= set(full['c'][name].get('p', [])):
                errors.append('Chat/full property inventory mismatch: ' + name)
        appendix = texts[(root/'Resources/chat_system_prompt_appendix.md').resolve()]
        errors += text_reference_errors(appendix, chat, 'Chat appendix')
        errors += text_reference_errors(texts[(root/'Resources/fontlab_python_api.llm.md').resolve()], full, 'Full text reference')
        if len(appendix.encode('utf-8')) > 262144: errors.append('Appendix exceeds app loader budget')
        if chat.get('actions') != read('Resources/fontlab_action_catalog.json'): errors.append('Chat/action catalog mismatch')
        catalog = read('Resources/vfj_schema.json')
        if set(catalog['topics'])-{'overview'} != set(catalog['$defs']): errors.append('VFJ topic/definition inventory mismatch')
        for value in walk(catalog['$defs']):
            if isinstance(value, dict) and '$ref' in value:
                ref = value['$ref']
                if not ref.startswith('#/$defs/') or ref[8:] not in catalog['$defs']: errors.append('Unresolved VFJ reference: ' + ref)
    except (KeyError, TypeError, OSError, ValueError) as exc: errors.append('Catalog verification failed: ' + str(exc))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-manifest', action='store_true', help='Validate content before recording reviewed changes')
    args = parser.parse_args()
    errors = verify(check_manifest=not args.refresh_manifest)
    if not errors and args.refresh_manifest:
        write_manifest()
        errors = verify()
    if errors:
        for error in errors: print(error)
        return 1
    print('Verified release files, hashes, links and heading anchors, Python syntax and reference contracts.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
