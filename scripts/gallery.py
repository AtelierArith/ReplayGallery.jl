"""Offline, standard-library-only gallery validation and HTML generation."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def catalog(root=ROOT):
    entries = json.loads((root / "examples.json").read_text())
    names = [e["name"] for e in entries]
    if len(set(names)) != len(names) or not all(re.fullmatch(r"[a-z][a-z0-9_]*", n) for n in names):
        raise ValueError("Example names must be unique safe identifiers")
    actual = {p.parent.name for p in (root / "examples").glob("*/app.jl")}
    if set(names) != actual:
        raise ValueError(f"Catalog/example mismatch: {set(names) ^ actual}")
    for entry in entries:
        if not isinstance(entry["record"], bool) or not isinstance(entry["options"], list):
            raise ValueError("Invalid recording metadata")
    return entries


def fingerprint(name, root=ROOT):
    """Input identity, not proof of successful execution or a cache hit."""
    paths = [root / "Project.toml", root / "examples.json", root / "replay-source.toml"]
    paths += sorted((root / "scripts").glob("*.py"))
    paths += sorted((root / "scripts").glob("*.jl"))
    paths += sorted(p for p in (root / "examples" / name).rglob("*")
                    if p.is_file() and p.suffix in (".jl", ".toml") and p.name != "Manifest.toml")
    digest = hashlib.sha256()
    for path in paths:
        digest.update(str(path.relative_to(root)).encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def check_cast(path):
    lines = path.read_text().splitlines()
    if not lines:
        raise ValueError(f"Empty recording: {path}")
    header = json.loads(lines[0])
    if header.get("version") != 2 or header.get("width", 0) <= 0 or header.get("height", 0) <= 0:
        raise ValueError(f"Unsupported asciicast header: {path}")
    last = 0
    output = []
    for line in lines[1:]:
        time, kind, text = json.loads(line)
        if not isinstance(time, (float, int)) or time < last or kind not in ("o", "i") or not isinstance(text, str):
            raise ValueError(f"Invalid event in {path}")
        last = time
        if kind == "o":
            output.append(text)
    if not output:
        raise ValueError(f"Recording contains no output: {path}")
    return "".join(output)


def validate(root=ROOT):
    entries = catalog(root)
    vendor = json.loads((root / "assets/vendor.json").read_text())
    for name, expected in vendor["sha256"].items():
        if hashlib.sha256((root / "assets" / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Vendored asset hash mismatch: {name}")
    provenance = json.loads((root / "recordings/provenance.json").read_text())
    for path in (root / "recordings").glob("*.cast"):
        check_cast(path)
        entry = provenance[path.stem]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["cast_sha256"]:
            raise ValueError(f"Recording hash mismatch: {path.name}")
        if entry.get("kind") == "validated":
            for filename, expected in entry["manifests"].items():
                if not re.fullmatch(r'[a-z][a-z0-9_-]*-Manifest\.toml', filename):
                    raise ValueError("Unsafe manifest filename")
                manifest = root / "recordings/manifests" / path.stem / filename
                if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
                    raise ValueError("Imported manifest checksum mismatch")
    return entries, provenance


def selected(changed, root=ROOT):
    entries = catalog(root)
    eligible = {e["name"] for e in entries if e["record"]}
    shared = ("scripts/", "tests/recordings.jl", ".github/workflows/recordings.yml")
    if any(p in ("Project.toml", "examples.json", "replay-source.toml") or p.startswith(shared) for p in changed):
        return sorted(eligible)
    return sorted({p.split("/")[1] for p in changed
                   if p.startswith("examples/") and len(p.split("/")) > 2} & eligible)


def build(root=ROOT, output=None):
    entries, provenance = validate(root)
    output = output or root / "build"
    output.mkdir(parents=True, exist_ok=True)
    # All assets local: no live CDN lookup, Julia installation or recording here.
    shutil.copytree(root / "assets", output / "assets", dirs_exist_ok=True)
    shutil.copytree(root / "recordings", output / "recordings", dirs_exist_ok=True)
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>ReplayGallery.jl</title>',
             '<link rel="stylesheet" href="assets/asciinema-player.css">',
             '<link rel="stylesheet" href="assets/gallery.css">',
             '<script src="assets/asciinema-player.min.js"></script><main>',
             '<h1>ReplayGallery.jl</h1><p>Reproducible Julia terminal examples.</p>',
             '<p><a href="https://github.com/AtelierArith/ReplayGallery.jl">Source &amp; recording guide</a> · '
             '<a href="https://AtelierArith.github.io/Replay.jl/dev/">Replay API documentation</a></p>',
             '<p>Recordings are reviewed snapshots, not evidence that every dependency still works. '
             'See each recording’s provenance below. Static documentation never executes examples.</p><nav><ul>']
    parts += [f'<li><a href="#{e["name"]}">{html.escape(e["title"])}</a></li>' for e in entries]
    parts.append('</ul></nav>')
    for entry in entries:
        name = entry["name"]
        source = (root / "examples" / name / "app.jl").read_text()
        parts.append(f'<section id="{name}"><h2>{html.escape(entry["title"])}</h2>')
        parts.append(f'<p><a href="https://github.com/AtelierArith/ReplayGallery.jl/tree/main/examples/{name}">Source &amp; dependencies</a></p>')
        parts.append(f'<pre><code>{html.escape(source)}</code></pre>')
        parts.append(f'<pre>python scripts/record.py {name}</pre>')
        path = root / "recordings" / f"{name}.cast"
        if not entry["record"]:
            parts.append('<p>SIXEL rendering is not supported by the browser player. Run this example in a SIXEL-capable terminal; it is not part of recording CI.</p>')
        elif path.exists():
            meta = provenance[name]
            status = 'Historical recording migrated from Replay.jl (not revalidated against current dependencies).'
            if meta.get('kind') == 'validated':
                status = ('Validated recording for these source inputs.' if meta.get('input_sha256') == fingerprint(name, root)
                          else 'Stale recording: source inputs have changed; rerun recording CI.')
            parts.append(f'<p class="status">{status}</p><p><a href="recordings/{name}.cast">Download cast</a> · '
                         '<a href="recordings/provenance.json">Provenance</a></p>')
            parts.append(f'<div id="player-{name}"></div><script>AsciinemaPlayer.create("recordings/{name}.cast", document.getElementById("player-{name}"), {{preload: false}});</script>')
        else:
            parts.append('<p>No reviewed recording yet. Run the example or download the recording workflow artifact; missing output is not a validation pass.</p>')
        parts.append('</section>')
    parts.append('</main></html>')
    (output / "index.html").write_text('\n'.join(parts))
    (output / ".nojekyll").touch()
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'build', 'select'])
    parser.add_argument('paths', nargs='*')
    args = parser.parse_args()
    if args.command == 'select':
        print(json.dumps(selected(args.paths)))
    elif args.command == 'validate':
        validate()
        print('Catalog, player checksums and recording provenance valid.')
    else:
        print(build())
