# Curse native mod template

A minimal native **Curse** mod. It has the same layout
`cargo curse-mod new <path> --template native` writes: a `curse-mixin.toml`
bundle manifest, and an `api/` package the Curse launcher links into the game
and whose `hooks()` returns the mod's `Hooks` implementation.

The example implements one hook, `Hooks::player_logged_in`, and greets each
player who joins. The greeting is a plain function with a unit test, so the
gameplay logic stays testable without the game.

## Requirements

Linux, Rust 1.95.0 (`rust-toolchain.toml`), Python 3.11+ and Git. Building the
mod against the real game also needs access to the pinned Curse source.

## Start a mod

Use GitHub's **Use this template → Create a new repository**, clone it, then
rename the example:

1. `curse-mixin.toml`: set `[mod] id` and `version`. The id is 1–64 lowercase
   letters, digits and `_`, the registry's rule.
2. `api/Cargo.toml`: rename the package to `mod-<id>` and match the version.
3. `api/src/lib.rs`: replace the greeting with your own hooks and logic.
4. `compatibility.json`: keep the revisions in sync (see below).
5. Run `cargo generate-lockfile` once you have the pinned source, then the
   checks in [Validation](#validation).

## Layout

```text
curse-mixin.toml        Bundle manifest: [mod], [compatibility], [api]
compatibility.json      Exact Curse and curse-mixins revisions and the game version
api/                    The package the launcher links into the game
  Cargo.toml            Package `mod-<id>`, depends on curse-client at the pinned rev
  src/lib.rs            hooks() and Hooks implementation
tools/package.py        Deterministic source-only .cmod
tools/test_template.py  Manifest, package and library checks without the game
.github/workflows/ci.yml
```

`curse-mixin.toml` carries three things:

```toml
[mod]
id = "example_mod"
version = "0.1.0"

[compatibility]
curse_revision = "6733a206366a67ef50dbb2e45a4d98e2df707ad1"

[api]
path = "api"
```

- `[compatibility] curse_revision` is the exact Curse commit the mod is made
  for. The launcher builds the `api` package on that source.
- `[api] path` names the trait mod package inside the bundle. Its library
  exports `pub fn hooks() -> Box<dyn curse_client::mod_api::Hooks>`.
- This bundle has no injections, modules, bridges or mixin crates, so the
  launcher skips curse-mixins and compiles the package alone.

A mod that needs to patch the game's own source declares that with
`[[module]]`/`[[injection]]` entries and does go through curse-mixins; a bundle
that only implements `Hooks` does not.

## Build and run

The launcher builds the folder as it is:

```sh
curse-launcher native-build . --instance <instance> --trust-native-code
```

Native mods run with the player's rights and are not sandboxed. The first
install shows a trust notice and every build waits behind a warning.

To compile the library on its own, fetch the pinned source through Cargo:

```sh
cargo test --manifest-path api/Cargo.toml
```

`tools/test_template.py` runs the same library test against a stub
`curse-client`, offline and without the game source; use it in CI or when the
Curse checkout is not at hand.

## Pin a revision

A native mod builds on one exact Curse commit, and every mod of a player's
build that pins another commit may still apply and compile, but the launcher
asks before mixing them. Pin a Nightly's commit (or a release's): Nightly
source stays downloadable under its `nightly-source/<date>-<short>` tag after
the Nightly is replaced.

To move to another commit, update all three places:

1. `compatibility.json` → `curse_revision`;
2. `curse-mixin.toml` → `[compatibility] curse_revision`;
3. `api/Cargo.toml` → the `curse-client` dependency's `rev`.

Then rerun the checks. `tools/test_template.py` fails when the three disagree.

`curse_mixins_revision` in `compatibility.json` is only recorded in the
registry manifest; this bundle uses no mixin, so the launcher does not build
with it.

## Package

```sh
python3 tools/package.py
```

It writes `target/<id>-<version>.cmod`: `curse-native.json` plus the bundle
under `mixins/<id>/` (manifest, `api/`, README, LICENSE), with fixed dates and
modes, so the same sources always give the same bytes and SHA-256. Submit the
file to the Curse mod registry; a maintainer reads the source before listing
it.

## Validation

```sh
python3 tools/test_template.py
cargo fmt --manifest-path api/Cargo.toml --check
```

`tools/test_template.py` checks that the manifest parses and matches
`compatibility.json` and `api/Cargo.toml`, that the package contains only
what the registry accepts and is byte-for-byte reproducible, and that the
mod library compiles and its test passes. With a Curse checkout that has the
pin, `cargo curse-mod check target/<id>-<version>.cmod` runs the registry's own
reader over the package.

See [VALIDATION.md](VALIDATION.md) for the results recorded for this template.

License: [MIT](LICENSE).
