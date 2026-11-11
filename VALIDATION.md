# Validation

Checked on Linux with Rust 1.95.0 on 2026-11-11, on the sources committed here
and the revisions in `compatibility.json`.

| Check | Result |
|---|---|
| `python3 tools/test_template.py` | Pass |
| `cargo fmt --manifest-path api/Cargo.toml --check` | Pass |
| `cargo curse-mod check target/example_mod-0.1.0.cmod` | Pass |

`tools/test_template.py` runs three checks:

- **Manifest.** `curse-mixin.toml` parses; `[mod] id` and `version` are valid;
  `[compatibility] curse_revision` matches `compatibility.json`; `[api] path` is
  `api`; `api/Cargo.toml` is package `mod-example_mod` and depends on
  `curse-client` at the same commit and repository.
- **Package.** `target/example_mod-0.1.0.cmod` holds `curse-native.json` and the
  bundle under `mixins/example_mod/`, only files the registry accepts; two runs
  give the same bytes (4424 bytes, SHA-256
  `01ad63dc74f05cdada2b9dbb4e02dfdd0d75fe3d0792cac8aa2da23d53e1c7ed`).
- **Library.** `api/` compiles offline against a tiny `curse-client` stub and
  its unit test passes (`greeting_names_the_player`).

`cargo curse-mod check` is the registry's own reader; it reports
`example_mod 0.1.0 (native-mod, format
native-1/6733a206366a67ef50dbb2e45a4d98e2df707ad1/e59da9094f0c2fdda6c627fe9eff22dec6a906f0,
for 26.3)`.

## Not checked here

The mod library was not built against the real pinned Curse source: that source
is not public and its dependency set is not cached in this environment. The
trait signature used here (`player_logged_in`, `Host::tell`, `Text::literal`)
is the one `cargo curse-mod new --template native` writes for the same revision;
`api/src/lib.rs` was compared with that generated example.

No game was launched, and no Minecraft resources or player data were read or
changed. `cargo curse-mod check` does not compile native code. Interactive
behaviour remains a manual check with `curse-launcher native-build` on a Curse
instance.
