#!/usr/bin/env python3
"""Check the bundle manifest, the package and the mod library without the game.

Compiles `api/` as an ordinary library against a tiny `curse-client` stub, so the
check runs offline and never needs the pinned Curse source.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import package  # noqa: E402

ID = re.compile(r'^[a-z0-9_]{1,64}$')


def read():
    return (tomllib.loads((ROOT / 'curse-mixin.toml').read_text()),
            json.loads((ROOT / 'compatibility.json').read_text()))


def check_manifest():
    mixin, compat = read()
    mod = mixin['mod']
    assert ID.match(mod['id']), mod['id']
    assert mod['version'] == '0.1.0', mod['version']
    assert mixin['compatibility']['curse_revision'] == compat['curse_revision']
    assert mixin['api']['path'] == 'api'
    api = tomllib.loads((ROOT / 'api' / 'Cargo.toml').read_text())
    assert api['package']['name'] == f"mod-{mod['id']}", api['package']['name']
    assert api['package']['version'] == mod['version']
    dep = api['dependencies']['curse-client']
    assert dep['git'] == compat['curse_repository'], dep['git']
    assert dep['rev'] == compat['curse_revision'], dep['rev']
    lib = (ROOT / 'api' / 'src' / 'lib.rs').read_text()
    assert 'pub fn hooks() -> Box<dyn Hooks>' in lib
    assert 'fn player_logged_in' in lib
    return mod['id'], mod['version'], compat


def check_package(mod_id, version, compat):
    with tempfile.TemporaryDirectory(prefix='curse-package-') as scratch:
        first = package.package(ROOT, Path(scratch) / 'first.cmod', quiet=True)
        second = package.package(ROOT, Path(scratch) / 'second.cmod', quiet=True)
        assert first.read_bytes() == second.read_bytes(), 'packaging is not reproducible'
        with zipfile.ZipFile(first) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names))
            for name in names:
                parts = name.split('/')
                assert '..' not in parts and '\\' not in name and not name.startswith('/')
            manifest = json.loads(archive.read('curse-native.json'))
            assert manifest == dict(schema=1, id=mod_id, version=version, game=compat['game'],
                                    horizon=compat['curse_revision'],
                                    mixins=compat['curse_mixins_revision'])
            prefix = f'mixins/{mod_id}/'
            bundle = [n for n in names if n != 'curse-native.json']
            for name in bundle:
                assert name.startswith(prefix), name
                rest = name[len(prefix):]
                assert rest.endswith(('.rs', '.toml')) or rest.split('/')[-1].startswith(
                    ('README', 'LICENSE', 'LICENCE', 'COPYING', 'NOTICE')), rest
            mixin = tomllib.loads(archive.read(prefix + 'curse-mixin.toml').decode())
            assert mixin['mod']['id'] == manifest['id']
            assert mixin['mod']['version'] == manifest['version']
            assert mixin['compatibility']['curse_revision'] == manifest['horizon']


STUB = '''
pub mod mod_api {
    pub trait Hooks: Send + Sync {
        fn player_logged_in(&self, _host: &mut dyn Host, _event: &mut PlayerLoggedInEvent<'_>) {}
    }
    pub trait Host {
        fn tell(&mut self, _player: u128, _text: Text);
    }
    #[derive(Debug, PartialEq)]
    pub struct Text(String);
    impl Text {
        pub fn literal(text: impl Into<String>) -> Self {
            Text(text.into())
        }
    }
    pub struct PlayerLoggedInEvent<'a> {
        pub player: u128,
        pub name: &'a str,
    }
}
'''


def check_library():
    cargo = shutil.which('cargo')
    if not cargo:
        raise SystemExit('cargo not found: cannot compile the mod library')
    with tempfile.TemporaryDirectory(prefix='curse-library-') as scratch:
        scratch = Path(scratch)
        stub = scratch / 'curse-client'
        (stub / 'src').mkdir(parents=True)
        (stub / 'Cargo.toml').write_text(
            '[package]\nname = "curse-client"\nversion = "0.0.0"\nedition = "2024"\n')
        (stub / 'src' / 'lib.rs').write_text(STUB)
        api = scratch / 'api'
        shutil.copytree(ROOT / 'api', api,
                        ignore=shutil.ignore_patterns('target', 'Cargo.lock'))
        manifest = (api / 'Cargo.toml').read_text()
        manifest = re.sub(r'(?m)^curse-client = .*$',
                          'curse-client = { path = "../curse-client" }', manifest)
        assert '"../curse-client"' in manifest
        (api / 'Cargo.toml').write_text(manifest)
        env = dict(os.environ, CARGO_TARGET_DIR=str(scratch / 'target'))
        subprocess.run([cargo, 'test', '--offline', '--quiet'], cwd=api, check=True, env=env)


if __name__ == '__main__':
    mod_id, version, compat = check_manifest()
    check_package(mod_id, version, compat)
    check_library()
    print(f'{mod_id} {version}: manifest, package and library checks pass')
