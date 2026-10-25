import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import import_recording


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'recordings').mkdir()
        (self.root / 'recordings/provenance.json').write_text('{}')
        self.artifacts = self.root / 'artifacts'
        self.artifacts.mkdir()
        self.cast = self.artifacts / 'demo.cast'
        self.cast.write_text('{"version":2,"width":80,"height":24}\n[0.1,"o","hello"]\n')
        self.manifest = self.artifacts / 'gallery-Manifest.toml'
        self.manifest.write_text('julia_version = "1.13.2"\n')
        self.receipt = {'kind': 'validated', 'input_sha256': 'expected',
                        'cast_sha256': hashlib.sha256(self.cast.read_bytes()).hexdigest(),
                        'manifests': {self.manifest.name: hashlib.sha256(self.manifest.read_bytes()).hexdigest()}}

    def tearDown(self):
        self.temp.cleanup()

    def import_it(self):
        (self.artifacts / 'demo.json').write_text(json.dumps(self.receipt))
        with patch.object(import_recording, 'ROOT', self.root), patch.object(import_recording, 'catalog', return_value=[{'name': 'demo', 'record': True}]), patch.object(import_recording, 'fingerprint', return_value='expected'):
            import_recording.import_recording('demo', self.artifacts)

    def test_import_preserves_manifest_and_repeats(self):
        self.import_it()
        self.import_it()
        self.assertEqual((self.root / 'recordings/manifests/demo/gallery-Manifest.toml').read_bytes(), self.manifest.read_bytes())
        self.assertEqual((self.root / 'recordings/demo.cast').read_bytes(), self.cast.read_bytes())

    def test_corrupt_manifest_rejected_without_import(self):
        self.manifest.write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'Manifest checksum'):
            self.import_it()
        self.assertFalse((self.root / 'recordings/demo.cast').exists())

    def test_local_development_and_stale_inputs_rejected(self):
        self.receipt['kind'] = 'development'
        with self.assertRaises(ValueError):
            self.import_it()
        self.receipt['kind'] = 'validated'
        self.receipt['input_sha256'] = 'old'
        with self.assertRaises(ValueError):
            self.import_it()

    def test_path_traversal_rejected(self):
        self.receipt['manifests'] = {'../secret': 'irrelevant'}
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            self.import_it()
