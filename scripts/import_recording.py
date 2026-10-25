"""Import a reviewed, current-input CI artifact without executing downloaded code."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import re
from gallery import ROOT, catalog, check_cast, fingerprint


def import_recording(name, artifacts):
    if name not in {e['name'] for e in catalog() if e['record']}:
        raise ValueError('Unknown recording')
    receipt = json.loads((artifacts / (name + '.json')).read_text())
    cast = artifacts / (name + '.cast')
    check_cast(cast)
    if receipt.get('kind') != 'validated' or receipt.get('input_sha256') != fingerprint(name):
        raise ValueError('Artifact inputs do not match this checkout; regenerate')
    if receipt.get('cast_sha256') != hashlib.sha256(cast.read_bytes()).hexdigest():
        raise ValueError('Artifact cast checksum mismatch')
    manifests = receipt.get('manifests', {})
    if not manifests:
        raise ValueError('Artifact has no reproducibility manifests')
    for filename, checksum in manifests.items():
        if not re.fullmatch(r'[a-z][a-z0-9_-]*-Manifest\.toml', filename):
            raise ValueError('Unsafe manifest filename')
        if hashlib.sha256((artifacts / filename).read_bytes()).hexdigest() != checksum:
            raise ValueError('Manifest checksum mismatch')
    target = ROOT / 'recordings'
    provenance = json.loads((target / 'provenance.json').read_text())
    provenance[name] = receipt
    manifest_directory = target / 'manifests' / name
    manifest_directory.mkdir(parents=True, exist_ok=True)
    for filename in manifests:
        shutil.copyfile(artifacts / filename, manifest_directory / filename)
    shutil.copyfile(cast, target / cast.name)
    (target / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('artifact_directory', type=Path)
    args = parser.parse_args()
    import_recording(args.name, args.artifact_directory)
