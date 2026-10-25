"""Record one catalog example; fail on timeout/errors and preserve exact input metadata."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import tomllib
from datetime import datetime, timezone
from gallery import ROOT, catalog, check_cast, fingerprint


def descendants(pid):
    # asciinema creates a separate PTY session; a process-group kill alone misses it.
    listing = subprocess.check_output(['ps', '-axo', 'pid=,ppid='], text=True)
    children = {}
    for line in listing.splitlines():
        child, parent = map(int, line.split())
        children.setdefault(parent, []).append(child)
    result = []
    pending = list(children.get(pid, []))
    while pending:
        child = pending.pop()
        result.append(child)
        pending.extend(children.get(child, []))
    return result


def run(command, *, timeout=900, cwd=ROOT, env=None, capture=False):
    proc = subprocess.Popen(command, cwd=cwd, env=env, start_new_session=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.STDOUT if capture else None, text=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
    except BaseException:
        # Only terminate processes descended from this command, never unrelated Julia.
        children = descendants(proc.pid)
        for pid in reversed(children):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        for pid in reversed(children):
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if proc.stdout:
            proc.stdout.close()
        raise
    if proc.returncode:
        raise RuntimeError(f'Command failed with exit status {proc.returncode}: {shlex.join(map(str, command))}\n' + (output or '')[-5000:])
    return output or ''


def julia_error(text):
    """Return useful diagnostics even when Julia colors its ERROR prefix."""
    plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    match = re.search(r'(?:^|[\r\n])ERROR:', plain)
    return plain[match.start():match.start() + 5000] if match else None


def record(name, output, julia='julia', timeout=900):
    entry = next((e for e in catalog() if e['name'] == name), None)
    if entry is None or not entry['record']:
        raise ValueError(f'Not a recordable example: {name}')
    if not (ROOT / 'Manifest.toml').exists():
        raise ValueError('Run julia --project=. scripts/setup.jl first')
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    identity = fingerprint(name)
    with tempfile.TemporaryDirectory(prefix=name + '-environment-', dir=output) as temporary:
        example_directory = Path(temporary) / name
        shutil.copytree(ROOT / 'examples' / name, example_directory,
                        ignore=shutil.ignore_patterns('Manifest.toml', '.CondaPkg', '__pycache__'))
        if not (example_directory / 'Project.toml').exists():
            shutil.copyfile(ROOT / 'Project.toml', example_directory / 'Project.toml')
            shutil.copyfile(ROOT / 'Manifest.toml', example_directory / 'Manifest.toml')
        return record_example(entry, example_directory, output, julia, timeout, identity)


def record_example(entry, example_directory, output, julia, timeout, identity):
    name = entry['name']
    command = [julia, '--startup-file=no', '--project=' + str(ROOT)] + entry['options'] + [str(example_directory / 'app.jl')]
    env = os.environ.copy()
    # Limit package lookup; this does NOT disable startup.jl in Replay child processes.
    # Use a clean Julia depot for reproducible unattended recordings (as in CI).
    env['JULIA_LOAD_PATH'] = '@:@stdlib'
    env['TERM'] = 'xterm-256color'
    # Warm up separately so installation/precompilation is not in the recording.
    warmup = run(command, timeout=timeout, cwd=example_directory, env=env, capture=True)
    if error := julia_error(warmup):
        raise RuntimeError('Julia reported an error during warmup:\n' + error)
    # Write atomically: failed/repeated recordings must not overwrite valid output.
    with tempfile.TemporaryDirectory(prefix=name + '-', dir=output) as temporary:
        cast = Path(temporary) / (name + '.cast')
        status_file = Path(temporary) / 'exit-status'
        shell_command = (shlex.join(command) + '; status=$?; printf \"%s\" \"$status\" > '
                         + shlex.quote(str(status_file)) + '; exit \"$status\"')
        run(['asciinema', 'rec', '--quiet', '--cols', '80', '--rows', '24',
             '--command', shell_command, str(cast)], timeout=timeout, cwd=example_directory, env=env)
        if not status_file.exists() or status_file.read_text() != '0':
            raise RuntimeError('Recorded command failed or did not finish')
        text = check_cast(cast)
        plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
        if error := julia_error(plain):
            raise RuntimeError('Julia reported an error in the recording:\n' + error)
        if name == 'numbered_prompt' and not all(marker in plain for marker in ['In [1]:', 'In [2]:', 'Out[1]']):
            raise RuntimeError('Numbered prompt/output markers are absent')
        if name == 'interactive_menu' and not all(marker in plain for marker in ['choice = 2', 'cancelled = -1', 'again = 1']):
            raise RuntimeError('Menu selection/cancel/repeat markers are absent')
        if fingerprint(name) != identity:
            raise RuntimeError('Source inputs changed during recording; rerun from a stable checkout')
        manifests = {}
        for label, source in [('gallery', ROOT / 'Manifest.toml'),
                              (name, example_directory / 'Manifest.toml')]:
            if source.exists():
                target = output / (label + '-Manifest.toml')
                shutil.copyfile(source, target)
                manifests[target.name] = hashlib.sha256(source.read_bytes()).hexdigest()
        replay = tomllib.loads((ROOT / 'Manifest.toml').read_text())['deps']['Replay'][0]
        pinned = tomllib.loads((ROOT / 'replay-source.toml').read_text())
        is_pinned = replay.get('repo-rev') == pinned['rev'] and replay.get('repo-url') == pinned['url']
        receipt = {'kind': 'validated' if is_pinned else 'development', 'input_sha256': identity,
                   'cast_sha256': hashlib.sha256(cast.read_bytes()).hexdigest(),
                   'julia': run([julia, '--version'], capture=True).strip(),
                   'asciinema': run(['asciinema', '--version'], capture=True).strip(),
                   'recorded_at': datetime.now(timezone.utc).isoformat(),
                   'source_commit': run(['git', 'rev-parse', 'HEAD'], capture=True).strip(),
                   'replay_source': (ROOT / 'replay-source.toml').read_text(),
                   'manifests': manifests}
        cast.replace(output / cast.name)
        (output / (name + '.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    return output / (name + '.cast')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts')
    parser.add_argument('--julia', default='julia')
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    print(record(args.name, args.output, args.julia, args.timeout))
