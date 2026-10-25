import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gallery
import record


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ['examples', 'assets', 'recordings', 'scripts']:
            shutil.copytree(gallery.ROOT / name, self.root / name)
        for name in ['Project.toml', 'examples.json', 'replay-source.toml']:
            shutil.copyfile(gallery.ROOT / name, self.root / name)

    def tearDown(self):
        self.temp.cleanup()

    def test_catalog_complete(self):
        self.assertEqual(len(gallery.catalog(self.root)), 21)
        self.assertEqual(len(gallery.validate(self.root)[1]), len(list((self.root / "recordings").glob("*.cast"))))

    def test_selection(self):
        self.assertEqual(gallery.selected(['README.md', 'assets/gallery.css'], self.root), [])
        self.assertEqual(gallery.selected(['examples/iris/app.jl'], self.root), ['iris'])
        self.assertEqual(gallery.selected(['examples/iris/Project.toml'], self.root), ['iris'])
        self.assertEqual(gallery.selected(['examples/sixel/app.jl'], self.root), [])
        self.assertEqual(len(gallery.selected(['scripts/record.py'], self.root)), 19)
        self.assertEqual(len(gallery.selected(['replay-source.toml'], self.root)), 19)
        self.assertEqual(len(gallery.selected(['tests/recordings.jl'], self.root)), 19)

    def test_input_identity(self):
        before = gallery.fingerprint('helloworld', self.root)
        other = gallery.fingerprint('iris', self.root)
        script = self.root / 'examples/helloworld/app.jl'
        script.write_text(script.read_text() + '\n# changed\n')
        self.assertNotEqual(before, gallery.fingerprint('helloworld', self.root))
        self.assertEqual(other, gallery.fingerprint('iris', self.root))

    def test_vendor_tampering_fails(self):
        (self.root / 'assets/asciinema-player.css').write_text('bad')
        with self.assertRaises(ValueError):
            gallery.validate(self.root)

    def test_corrupt_recording_fails(self):
        (self.root / 'recordings/helloworld.cast').write_text('{bad json')
        with self.assertRaises(ValueError):
            gallery.validate(self.root)

    def test_empty_recording_fails(self):
        path = self.root / 'empty.cast'
        path.write_text('{"version":2,"width":80,"height":24}\n')
        with self.assertRaises(ValueError):
            gallery.check_cast(path)

    def test_build_is_offline_and_escapes_source(self):
        missing = self.root / 'recordings/numbered_prompt.cast'
        if missing.exists():
            missing.unlink()
        script = self.root / 'examples/helloworld/app.jl'
        script.write_text('println("<script>alert(1)</script>")')
        output = gallery.build(self.root)
        html = (output / 'index.html').read_text()
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertIn('Historical recording', html)
        self.assertIn('No reviewed recording yet', html)
        self.assertNotIn('src="https://', html)
        self.assertEqual(len(list((output / 'recordings').glob('*.cast'))), len(list((self.root / 'recordings').glob('*.cast'))))

    def test_stale_recording_label(self):
        path = self.root / 'recordings/provenance.json'
        provenance = json.loads(path.read_text())
        provenance['helloworld'].update(kind='validated', input_sha256='outdated', manifests={})
        path.write_text(json.dumps(provenance))
        output = gallery.build(self.root)
        self.assertIn('Stale recording', (output / 'index.html').read_text())

    def test_failed_command_propagates(self):
        with self.assertRaises(Exception):
            record.run([sys.executable, '-c', 'raise SystemExit(9)'], capture=True)

    def test_timeout(self):
        import subprocess
        with self.assertRaises(subprocess.TimeoutExpired):
            record.run([sys.executable, '-c', 'import time; time.sleep(30)'], timeout=0.05, capture=True)


if __name__ == '__main__':
    unittest.main()

class RecorderTests(unittest.TestCase):
    def test_failed_recording_preserves_previous_cast(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Manifest.toml').write_text('')
            (root / 'Project.toml').write_text('')
            (root / 'examples/demo').mkdir(parents=True)
            output = root / 'artifacts'
            output.mkdir()
            old = output / 'demo.cast'
            old.write_text('previous validated recording')
            entry = {'name': 'demo', 'record': True, 'options': []}
            # Simulate asciinema returning success without its child finishing.
            with patch.object(record, 'ROOT', root), patch.object(record, 'catalog', return_value=[entry]), patch.object(record, 'fingerprint', return_value='test'), patch.object(record, 'run', return_value=''):
                with self.assertRaisesRegex(RuntimeError, 'did not finish'):
                    record.record('demo', output)
            self.assertEqual(old.read_text(), 'previous validated recording')
            self.assertEqual(sorted(p.name for p in output.iterdir()), ['demo.cast'])

    def test_failed_warmup_preserves_previous_cast(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'Manifest.toml').write_text('')
            (root / 'Project.toml').write_text('')
            (root / 'examples/demo').mkdir(parents=True)
            output = root / 'artifacts'
            output.mkdir()
            old = output / 'demo.cast'
            old.write_text('previous validated recording')
            entry = {'name': 'demo', 'record': True, 'options': []}
            with patch.object(record, 'ROOT', root), patch.object(record, 'catalog', return_value=[entry]), patch.object(record, 'fingerprint', return_value='test'), patch.object(record, 'run', return_value='ERROR: failed'):
                with self.assertRaisesRegex(RuntimeError, 'warmup'):
                    record.record('demo', output)
            self.assertEqual(old.read_text(), 'previous validated recording')

class IsolationTests(unittest.TestCase):
    def test_example_environment_is_staged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'examples/demo'
            source.mkdir(parents=True)
            (source / 'Project.toml').write_text('# original')
            (source / 'app.jl').write_text('println("demo")')
            (source / 'Manifest.toml').write_text('local manifest must not be reused')
            (root / 'Manifest.toml').write_text('')
            entry = {'name': 'demo', 'record': True, 'options': []}
            def simulated_record(entry, staged, output, julia, timeout, identity):
                self.assertNotEqual(staged, source)
                self.assertFalse((staged / 'Manifest.toml').exists())
                (staged / 'Project.toml').write_text('changed by package mode')
                return 'ok'
            with patch.object(record, 'ROOT', root), patch.object(record, 'catalog', return_value=[entry]), patch.object(record, 'fingerprint', return_value='test'), patch.object(record, 'record_example', side_effect=simulated_record):
                self.assertEqual(record.record('demo', root / 'artifacts'), 'ok')
            self.assertEqual((source / 'Project.toml').read_text(), '# original')
            self.assertEqual(list((root / 'artifacts').iterdir()), [])

    def test_timeout_stops_child_in_separate_session(self):
        import subprocess
        import time
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / 'heartbeat'
            child = f'import pathlib,time\np=pathlib.Path({str(heartbeat)!r})\nwhile True:\n p.write_text(str(time.monotonic()))\n time.sleep(0.01)'
            parent = f'import subprocess,os,time\nsubprocess.Popen([{sys.executable!r}, "-c", {child!r}], start_new_session=True)\ntime.sleep(30)'
            with self.assertRaises(subprocess.TimeoutExpired):
                record.run([sys.executable, '-c', parent], timeout=0.3, capture=True)
            self.assertTrue(heartbeat.exists())
            value = heartbeat.read_text()
            time.sleep(0.1)
            self.assertEqual(value, heartbeat.read_text())


class JuliaDiagnosticTests(unittest.TestCase):
    def test_colored_error_is_detected_and_reported(self):
        text = "julia> broken()\r\n\x1b[91mERROR: \x1b[39mUndefVarError: missing\nStacktrace: test"
        self.assertIn('UndefVarError: missing', record.julia_error(text))
        self.assertNotIn('\x1b', record.julia_error(text))

    def test_echoed_error_string_is_not_a_failure(self):
        self.assertIsNone(record.julia_error('julia> \"ERROR:\"\n\"ERROR:\"\n'))
