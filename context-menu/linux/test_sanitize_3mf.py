import tempfile
import unittest
import zipfile
from pathlib import Path

import sanitize_3mf


class Sanitize3mfTests(unittest.TestCase):
    def test_creates_copy_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "modelo con espacios.3mf"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Metadata/project_settings.config",
                                 '{"raft_first_layer_expansion":-1,"tree_support_wall_count":"-1"}')
                archive.writestr("3D/3dmodel.model", "unchanged")
            original = source.read_bytes()

            result = sanitize_3mf.sanitize_3mf(source)

            self.assertEqual(result.total_fixes, 2)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(result.output, source.with_name("modelo con espacios_sanitizado.3mf"))
            with zipfile.ZipFile(result.output) as archive:
                self.assertEqual(archive.read("3D/3dmodel.model"), b"unchanged")
                self.assertEqual(archive.read("Metadata/project_settings.config"),
                                 b'{"raft_first_layer_expansion":"0","tree_support_wall_count":"0"}')

    def test_unchanged_file_creates_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "ok.3mf"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Metadata/project_settings.config", '{"tree_support_wall_count":"0"}')
            self.assertIsNone(sanitize_3mf.sanitize_3mf(source).output)
            self.assertEqual(list(Path(tmp).iterdir()), [source])

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "modelo.3mf"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("Metadata/project_settings.config", '{"tree_support_wall_count":-1}')
            output = source.with_name("modelo_sanitizado.3mf")
            output.write_bytes(b"keep")
            with self.assertRaises(sanitize_3mf.SanitizeError):
                sanitize_3mf.sanitize_3mf(source)
            self.assertEqual(output.read_bytes(), b"keep")

    def test_invalid_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.3mf"
            source.write_bytes(b"not a zip")
            with self.assertRaises(sanitize_3mf.SanitizeError):
                sanitize_3mf.sanitize_3mf(source)


if __name__ == "__main__":
    unittest.main()
