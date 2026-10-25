#!/usr/bin/env python3
"""Render a local asciicast as GIF or MP4 using optional external CLI tools."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def tool(name):
    executable = shutil.which(name)
    if executable is None:
        raise ValueError(f"Required tool not found: {name}; see docs/video.md")
    return executable


def export_video(source, output, *, overwrite=False):
    source, output = Path(source), Path(output)
    if not source.is_file():
        raise ValueError(f"Recording does not exist: {source}")
    if output.suffix.lower() not in (".gif", ".mp4"):
        raise ValueError("Output must end in .gif or .mp4")
    if source.resolve() == output.resolve():
        raise ValueError("Input and output must be different files")
    if output.exists() and not overwrite:
        raise ValueError(f"Output already exists (use --overwrite): {output}")
    agg = tool("agg")
    is_mp4 = output.suffix.lower() == ".mp4"
    ffmpeg = tool("ffmpeg") if is_mp4 else None
    ffprobe = tool("ffprobe") if is_mp4 else None
    output.parent.mkdir(parents=True, exist_ok=True)
    # Temporary siblings keep failed/interrupted conversions from replacing a good file.
    with tempfile.TemporaryDirectory(prefix=".replay-export-", dir=output.parent) as work:
        gif = Path(work) / "render.gif"
        subprocess.run([agg, "--quiet", str(source.resolve()), str(gif)], check=True)
        rendered = gif
        probe = None
        if is_mp4:
            rendered = Path(work) / "render.mp4"
            subprocess.run([
                ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(gif),
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(rendered),
            ], check=True)
            probe = json.loads(subprocess.check_output([
                ffprobe, "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height,pix_fmt:format=duration",
                "-of", "json", str(rendered),
            ], text=True))
            if not probe.get("streams") or float(probe["format"]["duration"]) <= 0:
                raise ValueError("Video validation failed: no playable video stream")
        if rendered.stat().st_size == 0:
            raise ValueError("Conversion produced an empty file")
        if output.exists() and not overwrite:
            raise ValueError(f"Output appeared during export: {output}")
        rendered.replace(output)
    return {"input": str(source), "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "output": str(output), "output_bytes": output.stat().st_size, "probe": probe}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output only after successful conversion")
    args = parser.parse_args()
    try:
        result = export_video(args.recording, args.output, overwrite=args.overwrite)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Export failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
