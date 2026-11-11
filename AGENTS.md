# Working on this Curse native mod

Read README.md and compatibility.json before editing. This repository is a mod
bundle, separate from the Curse game source and from curse-mixins: never edit
the original Curse checkout or player resources, and do not commit game
binaries, exported sources or Minecraft assets.

Keep `curse-mixin.toml`, `compatibility.json` and the `curse-client` revision in
`api/Cargo.toml` in sync. Keep gameplay logic in plain functions under
`api/src/` so it stays unit-testable; implement hooks in `api/src/lib.rs`.

Validate with `python3 tools/test_template.py`, `cargo fmt --manifest-path
api/Cargo.toml --check` and, when the pinned source is available,
`cargo test --manifest-path api/Cargo.toml`. Keep validation claims and pinned
revisions honest.
