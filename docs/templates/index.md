# ReplayGallery.jl

Reproducible Julia terminal examples recorded with
[Replay.jl](https://github.com/AtelierArith/Replay.jl), played back in the browser
with [asciinema-player](https://github.com/asciinema/asciinema-player).

Recordings are reviewed snapshots, not evidence that every dependency still works.
Each recording's [provenance](https://github.com/AtelierArith/ReplayGallery.jl/blob/main/recordings/provenance.json)
records the source commit, asciinema version and checksums; this documentation site
never executes the examples.

{{EXAMPLES}}

## What the labels mean

| Label | Meaning |
| --- | --- |
| **Validated** | Recorded from the current source inputs, with the resolved manifests preserved. |
| **Stale** | The example source has changed since the recording was validated. |
| **Historical** | Migrated from Replay.jl and not revalidated against current dependencies. |
| **No recording** | No reviewed recording yet. Missing output is not a validation pass. |
| **SIXEL** | SIXEL graphics cannot be rendered by the browser player; run it in a SIXEL-capable terminal. |

## Next steps

- [Recording guide](./recording.md) — record or refresh an example.
- [Exporting video](./video.md) — turn a cast into GIF or MP4.
- [Replay.jl API documentation](https://AtelierArith.github.io/Replay.jl/dev/).
