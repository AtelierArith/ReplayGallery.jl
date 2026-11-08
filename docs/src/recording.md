# Recording guide

Recordings in this gallery are produced with
[Replay.jl](https://github.com/AtelierArith/Replay.jl) and `asciinema`, then reviewed
before they are committed. See the
[repository README](https://github.com/AtelierArith/ReplayGallery.jl#record-an-example)
for the full workflow and safety notes; this page is a short version.

## Prerequisites

- The exact Julia version in `julia-version` (currently 1.13.3), and Python 3.11+.
- `asciinema` 2.4.0 (`python -m pip install asciinema==2.4.0`).
- A POSIX PTY environment (Linux or macOS; use WSL on Windows).

`record.py` checks `julia --version` against `julia-version` before doing any work,
so a locally installed LTS or a newer stable release cannot silently produce a
recording with a different runtime.

## Record an example

From the repository root:

```sh
julia --startup-file=no --project=. scripts/setup.jl
python scripts/record.py helloworld
asciinema play artifacts/helloworld.cast
```

`scripts/setup.jl` pins Replay to the commit in `replay-source.toml`. The recorder
copies the example into a temporary working environment, warms up packages, records
with fixed terminal dimensions, and checks the cast and Julia error output. Output is
replaced only after a successful recording.

## Review and import

Recordings execute Julia code. Review the example and the produced cast before
committing, and use a clean Julia depot (`JULIA_DEPOT_PATH`) as CI does. Import the
recording workflow artifact with:

```sh
python scripts/import_recording.py NAME ARTIFACT_DIRECTORY
```

The importer refuses mismatched source inputs or corrupt casts, and preserves the
resolved manifests under `recordings/manifests/`.

## Adding an example

1. Add `examples/<name>/app.jl` (and a `Project.toml` if it needs packages).
2. Add an entry to [`examples.json`](https://github.com/AtelierArith/ReplayGallery.jl/blob/main/examples.json).
3. Record it and commit the cast plus the updated provenance.
4. Rebuild this site; the example page is generated from the catalog automatically.
