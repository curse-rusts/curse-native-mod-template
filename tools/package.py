#!/usr/bin/env python3
"""Package the mod as a source-only `.cmod` the Curse registry and launcher take.

The archive holds `curse-native.json` and the bundle under `mixins/<id>/`
(`curse-mixin.toml`, the `api/` package, README and LICENSE), with fixed dates and
modes, so the same sources always give the same bytes and the same SHA-256.
Curse's `curse_mods::index::native` reads it without running anything; the
launcher compiles it on the pinned Curse revision.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_FILES = ('curse-mixin.toml', 'README.md', 'LICENSE')


def bundle_files(root):
    files = []
    for name in BUNDLE_FILES:
        path = root / name
        if path.is_file():
            files.append(path)
    for path in sorted((root / 'api').rglob('*')):
        if path.is_file() and 'target' not in path.relative_to(root).parts:
            files.append(path)
    return files


def package(root=ROOT, out=None, quiet=False):
    compat = json.loads((root / 'compatibility.json').read_text())
    mixin = tomllib.loads((root / 'curse-mixin.toml').read_text())
    mod = mixin['mod']
    mod_id, version = mod['id'], mod['version']
    if not mod_id or not mod_id.replace('_', '').isalnum() or not mod_id.islower():
        raise SystemExit('the registry takes ids of lowercase letters, digits and _ only')
    if mixin.get('compatibility', {}).get('curse_revision') != compat['curse_revision']:
        raise SystemExit('curse-mixin.toml and compatibility.json pin different Curse revisions')
    api = mixin.get('api', {}).get('path')
    if not api or not (root / api / 'Cargo.toml').is_file():
        raise SystemExit('curse-mixin.toml [api] path must name a package in the bundle')
    manifest = dict(schema=1, id=mod_id, version=version, game=compat['game'],
                    horizon=compat['curse_revision'], mixins=compat['curse_mixins_revision'])
    files = {'curse-native.json': (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()}
    prefix = f'mixins/{mod_id}/'
    for path in bundle_files(root):
        name = prefix + path.relative_to(root).as_posix()
        files[name] = path.read_bytes()
    target = Path(out) if out else root / 'target' / f'{mod_id}-{version}.cmod'
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    result = dict(file=str(target), size=target.stat().st_size,
                  sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    if not quiet:
        print(json.dumps(result, indent=2))
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path)
    package(ROOT, parser.parse_args().out)


if __name__ == '__main__':
    main()
