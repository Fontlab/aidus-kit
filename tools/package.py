#!/usr/bin/env python3
"""Create a verified release ZIP from manifest entries only."""
from __future__ import annotations
import argparse
import hashlib
from datetime import date
import json
import os
from pathlib import Path
import tempfile
import zipfile
from verify import ROOT, EXCLUDED_DIRS, verify


def build_archive(output, root=ROOT, overwrite=False):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists() and not overwrite:
        raise FileExistsError('Archive exists; use --overwrite after review')
    if output.is_relative_to(root) and output.relative_to(root).parts[0] not in EXCLUDED_DIRS:
        raise ValueError('Put archives outside the kit or in its excluded dist directory')
    errors = verify(root)
    if errors: raise ValueError('Release verification failed:\n' + '\n'.join(errors))
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    snapshot = json.loads((root/'SOURCE.json').read_text(encoding='utf-8'))
    day = date.fromisoformat(snapshot['snapshot_date'])
    if day.year < 1980: raise ValueError('ZIP snapshot date must be 1980 or later')
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix='aidus-release-', suffix='.zip', dir=output.parent)
    os.close(handle)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name in sorted(set(manifest['files']) | {'manifest.json'}):
                info = zipfile.ZipInfo('fontlab-aidus-kit/' + name, (day.year,day.month,day.day,0,0,0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                source = root/name
                if source.is_symlink() or not source.resolve().is_relative_to(root):
                    raise ValueError('Release file became an unsafe path: ' + name)
                data = source.read_bytes()
                if name != 'manifest.json' and hashlib.sha256(data).hexdigest() != manifest['files'][name]:
                    raise ValueError('Release file changed during packaging: ' + name)
                if name == 'manifest.json' and json.loads(data) != manifest:
                    raise ValueError('Manifest changed during packaging')
                archive.writestr(info, data)
        # A failed build never truncates an existing archive.
        if output.exists() and not overwrite: raise FileExistsError('Archive appeared during build')
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'dist/fontlab-aidus-kit-0.1.0.zip')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try: path = build_archive(args.output, overwrite=args.overwrite)
    except (ValueError, OSError, KeyError) as exc: parser.error(str(exc))
    print('Created verified archive:', path)


if __name__ == '__main__':
    main()
