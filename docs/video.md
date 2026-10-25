# Export a terminal recording as video

Replay generates terminal output, not a native video container. Use the gallery's
recording workflow to create an asciicast, then convert it locally to **GIF or MP4**.
No screen capture, online upload, Julia video dependency, or GitHub permission is
required. The generated MP4 is an ordinary H.264/yuv420p video suitable for slides
and video players; it contains no audio. Terminal recordings cannot capture GUI
windows or SIXEL graphics.

## Optional prerequisites

- Python 3 (standard library only).
- [`agg` 1.9.0](https://github.com/asciinema/agg/releases/tag/v1.9.0), the official
  asciinema GIF renderer. Use the asset for your OS/architecture, or a package
  manager following the [official installation guide](https://docs.asciinema.org/manual/agg/installation/).
  Pin the release rather than downloading `latest` in automated workflows.
- For MP4 only, [FFmpeg](https://ffmpeg.org/download.html), including `ffprobe`,
  with the `libx264` encoder enabled (`ffmpeg -encoders` lists it).
  The end-to-end check used FFmpeg **7.1.5**. Distribution packages may use another
  supported version; record `ffmpeg -version` with your result.

Place the executables on `PATH`. For example, the official Linux x86-64 GNU agg
1.9.0 binary has SHA-256
`f111e315cd71056b116302342553dd765b7297579ed511f111d0cedb442aeda6`:

```sh
curl --fail --location --output agg \
  https://github.com/asciinema/agg/releases/download/v1.9.0/agg-x86_64-unknown-linux-gnu
printf '%s  agg\n' f111e315cd71056b116302342553dd765b7297579ed511f111d0cedb442aeda6 | sha256sum --check
chmod +x agg
export PATH="$PWD:$PATH"
agg --version
ffmpeg -version
```

That hash applies **only** to the named Linux binary; verify other assets against
GitHub's release asset `digest` field. These external tools are not vendored into
Replay or this gallery.

## Convert

From the repository root, using any existing local cast:

```sh
python scripts/export_video.py recordings/helloworld.cast output/hello.gif
python scripts/export_video.py recordings/helloworld.cast output/hello.mp4
```

The script prints input SHA-256, output size and (for MP4) `ffprobe` metadata,
including codec, dimensions and duration. It pads odd pixel dimensions for H.264,
uses `yuv420p`, and sets `faststart` for web playback. Paths with spaces are safe;
commands are passed directly as argument arrays, not evaluated in a shell.

An existing output is preserved unless you explicitly pass `--overwrite`:

```sh
python scripts/export_video.py recordings/helloworld.cast output/hello.mp4 --overwrite
```

Even with `--overwrite`, failed or interrupted conversion leaves the old file
intact. Rendering happens in a temporary directory; the output is replaced only
after successful encoding and video-stream validation. Fonts affect rendering,
so use the same font installation to reproduce pixels exactly. Keep the input
cast and tool versions as the reproducible source rather than committing generated
MP4/GIF files to the repository.

Video conversion is deliberately separate from fast static documentation builds.
Heavy renderers are never installed just to build the gallery site.
