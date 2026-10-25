# ReplayGallery.jl

A separate home for [Replay.jl](https://github.com/AtelierArith/Replay.jl)'s full
terminal examples. Core API documentation stays small; this gallery keeps slow
package installation, recording, and optional video conversion out of core CI.

## Browse and run

The [catalog](examples.json) lists all examples, including
[numbered prompts](examples/numbered_prompt/app.jl) and
[interactive menus](examples/interactive_menu/app.jl) with selection, cancellation
and a repeated request. The `examples/` directories
were migrated from Replay.jl, retaining their license. SIXEL examples require a
SIXEL-capable terminal and cannot be rendered by asciinema-player.

```sh
# From this repository's root; Julia stable or LTS, Python 3.11+.
julia --startup-file=no --project=. scripts/setup.jl
julia --startup-file=no --project=. examples/helloworld/app.jl

# Static docs: offline, no Julia and no third-party Python dependencies.
python -m unittest discover -s tests -v
python scripts/gallery.py build
python -m http.server --directory build 8000
```

Open http://localhost:8000 (rather than opening the HTML as a file: the player
loads recordings using HTTP). The **Static gallery** CI artifact `gallery-site`
contains this same self-contained site. This repository does not automatically
publish a website or change GitHub Pages settings.

## Record an example

The recorder uses POSIX PTYs/process management (Linux/macOS; use WSL on Windows).

```sh
python -m pip install asciinema==2.4.0
julia --startup-file=no --project=. scripts/setup.jl
python scripts/record.py helloworld
asciinema play artifacts/helloworld.cast
```

`setup.jl` pins Replay to the commit in [replay-source.toml](replay-source.toml).
A local `REPLAY_PATH` checkout override is available for development; such receipts
are labeled `development` and cannot be imported as validated recordings.
The recorder copies an example to a temporary working environment (excluding local
manifests/Conda state), warms up packages first, then records with fixed terminal
dimensions. Package-mode demonstrations cannot mutate the source checkout.
Source inputs are checked before and after recording to reject concurrent edits.
It checks the cast format and Julia error output, fails on process errors/timeouts,
and replaces output only after a successful recording. A timeout or interruption
terminates the command and its tracked descendants, including separate PTY sessions. `--julia PATH` and
`--timeout SECONDS` are available. Recordings execute Julia code; review example
changes before running them locally. Use a clean Julia depot (`JULIA_DEPOT_PATH`) as in CI: disabling startup files in
the parent process does not disable startup.jl in all child processes launched by
Replay. Local startup customizations can affect results. Run from a clean checkout and do not enter
credentials or personal data in a recorded session.

The numbered-prompt example uses Julia's real REPL prompts with ghostwriting
turned off; its recorder additionally verifies numbered input/output markers.
See [video export](docs/video.md) for an actual GIF/MP4 file rather than a cast.

## Fast CI without hiding missing validation

- **Static gallery** validates the catalog, vendored player checksums, and cast
  checksums, runs Python unit tests, then builds HTML. It never installs Julia or
  runs examples, downloads CDN assets, or depends on previous workflow artifacts.
- **Validate recordings** independently runs only changed recordable examples.
  Shared recorder, dependency/source pin, catalog, or workflow changes select all
  recordable examples. Documentation-only changes select none. Initial migration
  validates all added recordable examples, with at most four jobs in parallel.
- Manual **Validate recordings** dispatch accepts one name or `all`. Julia's
  package/artifact cache speeds installation but is never evidence of successful
  execution. Every selected example is warmed up and recorded again.
- Each recording artifact contains a cast, a receipt with source-input checksum,
  Julia/asciinema versions and checkout commit, and the exact resolved root/example
  `Manifest.toml` files. Restore those manifests with the recorded Julia version
  and instantiate to reproduce that environment. The importer preserves verified
  manifests in `recordings/manifests/NAME/` alongside committed cast provenance,
  so reviewed recordings remain reproducible after workflow artifacts expire. Source projects without a
  manifest resolve dependencies anew on a subsequent refresh.
- Local recording receipts may name a local-only Git commit; their source-input
  fingerprints identify the verified contents, not a claim that the commit is
  publicly available. CI receipts refer to the actual GitHub checkout commit.
- No workflow writes commits or triggers recursive recording builds. Artifacts
  expire according to repository retention. Review and import a result with
  `python scripts/import_recording.py NAME ARTIFACT_DIRECTORY`, then submit a PR.
  The importer refuses mismatched inputs or corrupt casts. Review the cast's
  contents before committing: checksums are integrity checks, not a secret scan.

The original gallery's recordings were migrated from Replay.jl's `gh-pages` branch;
[provenance](recordings/provenance.json) records source commits and checksums.
Unrefreshed recordings are deliberately labeled **historical**, not validation of
new sources or current dependencies. Refreshed examples replace these snapshots
only after recording validation and preserve their resolved manifests. Missing and stale recordings are displayed
explicitly. A successful static build does **not** mean recording CI passed.

## Updating the player and dependencies

The browser player is pinned to **asciinema-player 3.17.0**. Its JavaScript, CSS,
license, official release URL and SHA-256 hashes are vendored in `assets/`.
There is no unpinned “latest” download in docs builds. To update it:

1. Review [official releases](https://github.com/asciinema/asciinema-player/releases)
   and license/security changes.
2. Download both release assets and the license from the same selected tag;
   update `assets/vendor.json` with that version, release URL and file hashes.
3. Run Python tests/build and inspect playback of a migrated and a newly generated
   cast. Submit these asset changes in a reviewed PR.

Update the immutable Replay commit in `replay-source.toml` in a PR. Such a change
selects all recordings. The gallery recording runtime uses Julia's stable `1`
selector; Replay's own test suite, not this example gallery, covers both `1` and
`lts`. Browser/site-only changes stay independent of both Julia test matrices.

The migrated Julia helper in `scripts/ensure_recording.jl` retains regression tests
(`julia tests/recordings.jl`) for missing/existing/forced recordings. The new Python
recorder intentionally always refreshes selected examples rather than considering
an existing file a successful new validation.
