import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import launcher


class LauncherTests(unittest.TestCase):
    def environment(self, root):
        env_python = root / ".venv" / "python"
        env_python.parent.mkdir()
        env_python.touch()
        (root / "requirements.txt").write_text("pandas==2.3.3\n", encoding="utf-8")
        return patch.multiple(launcher, ROOT=root, ENV=root / ".venv", ENV_PYTHON=env_python,
                              MARKER=root / ".venv" / ".testingstudio-installed")

    def test_first_install_uses_prebuilt_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.environment(root), patch("launcher.subprocess.run") as run:
                launcher.install()
                self.assertEqual(run.call_count, 2)
                for call in run.call_args_list:
                    self.assertIn("--only-binary=:all:", call.args[0])
                self.assertEqual(launcher.MARKER.read_text().strip(), launcher.requirements_fingerprint())

    def test_failed_install_can_be_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.environment(root), patch("launcher.subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")):
                with self.assertRaises(subprocess.CalledProcessError):
                    launcher.install()
                self.assertFalse(launcher.MARKER.exists())

    def test_unchanged_successful_install_skips_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.environment(root), patch("launcher.subprocess.run") as run:
                launcher.MARKER.write_text(launcher.requirements_fingerprint())
                launcher.install()
                run.assert_not_called()

    def test_changed_requirements_repair_existing_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.environment(root), patch("launcher.subprocess.run") as run:
                launcher.MARKER.write_text("TestingStudio Sprint 1\n")
                launcher.install()
                self.assertEqual(run.call_count, 2)
                self.assertEqual(launcher.MARKER.read_text().strip(), launcher.requirements_fingerprint())
