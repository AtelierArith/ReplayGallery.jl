import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("export_video", Path(__file__).parents[1] / "scripts" / "export_video.py")
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cast = self.root / "a cast.cast"
        self.cast.write_text('{"version":2,"width":80,"height":24}\n')

    def test_missing_input_and_bad_extension(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            video.export_video(self.root / "absent", self.root / "out.gif")
        with self.assertRaisesRegex(ValueError, "must end"):
            video.export_video(self.cast, self.root / "out.txt")

    def test_missing_tool_is_actionable(self):
        with patch.object(video.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "Required tool not found: agg"):
                video.export_video(self.cast, self.root / "out.gif")

    def test_existing_output_requires_explicit_overwrite(self):
        out = self.root / "out.gif"
        out.write_bytes(b"old")
        with self.assertRaisesRegex(ValueError, "already exists"):
            video.export_video(self.cast, out)
        self.assertEqual(out.read_bytes(), b"old")

    def test_failed_and_interrupted_exports_preserve_existing_output(self):
        out = self.root / "out.gif"
        out.write_bytes(b"old")
        for error in (subprocess.CalledProcessError(1, "agg"), KeyboardInterrupt()):
            with patch.object(video, "tool", return_value="agg"), patch.object(video.subprocess, "run", side_effect=error):
                with self.assertRaises(type(error)):
                    video.export_video(self.cast, out, overwrite=True)
            self.assertEqual(out.read_bytes(), b"old")
            self.assertEqual(list(self.root.glob(".replay-export-*")), [])

    def test_repeated_export_and_spaces(self):
        out = self.root / "a video.gif"
        def render(argv, **kwargs):
            self.assertEqual(argv[2], str(self.cast.resolve()))
            Path(argv[-1]).write_bytes(b"GIF89a")
        with patch.object(video, "tool", return_value="agg"), patch.object(video.subprocess, "run", side_effect=render):
            first = video.export_video(self.cast, out)
            second = video.export_video(self.cast, out, overwrite=True)
        self.assertEqual(first["input_sha256"], second["input_sha256"])
        self.assertEqual(out.read_bytes(), b"GIF89a")


if __name__ == "__main__":
    unittest.main()
