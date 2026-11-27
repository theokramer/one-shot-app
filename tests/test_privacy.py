"""Privacy regressions use synthetic data, isolated Git repos and a fake screen recorder."""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("skill_package", ROOT / "assets/scripts/package.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.root = self.base / "skill"
        self.root.mkdir()
        self.home = self.base / "private"
        self.home.mkdir()
        for name, value in {"SKILL_DIR": self.root, "HOME": self.home,
                            "CONFIG": self.home / "config.json", "PROFILE": self.home / "profile.json"}.items():
            patch = mock.patch.object(package.paths, name, value)
            patch.start()
            self.addCleanup(patch.stop)
        self.write("README.md", "Generic skill documentation.\n")

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def git(self, *args):
        env = dict(os.environ, GIT_AUTHOR_NAME="one-shot-app contributors",
                   GIT_COMMITTER_NAME="one-shot-app contributors",
                   GIT_AUTHOR_EMAIL="contributors@example.invalid",
                   GIT_COMMITTER_EMAIL="contributors@example.invalid")
        return subprocess.check_output(["git", "-C", str(self.root), "-c", "core.hooksPath=/dev/null", *args], env=env, stderr=subprocess.PIPE)

    def scan(self, history=False):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            result = package.scan(history)
        return result, out.getvalue()

    def test_source_archive_excludes_private_files_media_and_directory_links(self):
        for name in (".env", ".env.production", "learnings.local.md", "review_information/contact.txt",
                     "assets/scripts/.env", "assets/demo/raw.jpg", "assets/demo/demo.mp4", "assets/scripts/private.pem"):
            self.write(name, "private fixture")
        self.write("assets/scripts/helper.py", "print('ok')\n")
        (self.home / "private.md").write_text("Private fixture")
        (self.root / "references").symlink_to(self.home, target_is_directory=True)
        dest = self.base / "out"
        with mock.patch.object(sys, "argv", ["package.py", "zip", str(dest)]), contextlib.redirect_stdout(io.StringIO()):
            package.main()
        with zipfile.ZipFile(next(dest.glob("*.zip"))) as archive:
            self.assertEqual(set(archive.namelist()), {"one-shot-app/README.md", "one-shot-app/assets/scripts/helper.py"})

    def test_tracked_private_file_fails_even_without_identifier_patterns(self):
        self.git("init", "-q")
        self.write(".env", "INTERNAL=fixture\n")
        self.git("add", ".env")
        result, out = self.scan()
        self.assertEqual(result, 1)
        self.assertIn("private path is tracked", out)
        self.assertNotIn("INTERNAL=fixture", out)

    def test_license_is_checked_against_known_identity(self):
        name = "Fixture Person"
        package.paths.PROFILE.write_text(json.dumps({"identity": {"fullName": name}}))
        self.write("LICENSE", "Copyright " + name)
        result, out = self.scan()
        self.assertEqual(result, 1)
        self.assertIn("LICENSE", out)
        self.assertNotIn(name, out)

    def test_secret_match_is_redacted(self):
        secret = "ghp_" + "a1B2" * 10
        self.write("README.md", secret)
        result, out = self.scan()
        self.assertEqual(result, 1)
        self.assertNotIn(secret, out)

    def test_deleted_secret_is_found_in_history(self):
        self.git("init", "-q")
        secret = "AIza" + "a1B2" * 10
        self.write("README.md", secret)
        self.git("add", ".")
        self.git("commit", "-qm", "Initial fixture")
        self.write("README.md", "Generic documentation")
        self.git("add", ".")
        self.git("commit", "-qm", "Clean current fixture")
        self.assertEqual(self.scan()[0], 0)
        result, out = self.scan(history=True)
        self.assertEqual(result, 1)
        self.assertIn("Google key", out)
        self.assertNotIn(secret, out)

    def test_commit_identity_is_flagged(self):
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "Fixture", "--author=Fixture Author <fixture" + "@" + "unit.test>")
        result, out = self.scan(history=True)
        self.assertEqual(result, 1)
        self.assertIn("author/committer identity", out)
        self.assertNotIn("Fixture Author", out)

    def test_nontext_tracked_file_requires_review(self):
        self.git("init", "-q")
        self.write("image.png", "image\0data")
        self.git("add", ".")
        self.assertEqual(self.scan()[0], 1)

    def test_unreadable_profile_fails_closed(self):
        package.paths.PROFILE.write_text("{broken")
        result, out = self.scan()
        self.assertEqual(result, 1)
        self.assertIn("Scan failed", out)
        self.assertNotIn("{broken", out)

    def test_export_refuses_stale_destination(self):
        dest = self.base / "export"
        dest.mkdir()
        (dest / "private.txt").write_text("private fixture")
        with mock.patch.object(sys, "argv", ["package.py", "export", str(dest)]), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            package.main()
        self.assertFalse((dest / "README.md").exists())


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.data = json.loads((ROOT / "profile.example.json").read_text())
        self.data["identity"]["fullName"] = "Private Fixture Name"
        self.data["apps"]["items"] = [{"name": "Unannounced Fixture App"}]
        self.data["toolDefaults"]["music"] = "private-track-location"
        self.data["imprint"].update(name="Private Fixture Name", street="Fixture Street", city="Fixture City")
        (self.base / "profile.json").write_text(json.dumps(self.data))

    def run_profile(self, *args, input=None):
        env = dict(os.environ, ONE_SHOT_HOME=str(self.base), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run([sys.executable, str(ROOT / "assets/scripts/profile.py"), *args], env=env,
                              input=input, text=True, capture_output=True)

    def test_summary_does_not_disclose_names_apps_or_paths(self):
        run = self.run_profile("summary")
        self.assertEqual(run.returncode, 0, run.stderr)
        for value in ("Private Fixture Name", "Unannounced Fixture App", "private-track-location", "Fixture Street"):
            self.assertNotIn(value, run.stdout)
        self.assertIn("1 saved", run.stdout)

    def test_imprint_requires_file_output_and_never_prints_contact(self):
        denied = self.run_profile("imprint-html")
        self.assertNotEqual(denied.returncode, 0)
        output = self.base / "public" / "imprint.html"
        run = self.run_profile("imprint-html", "--output", str(output))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Fixture Street", output.read_text())
        self.assertNotIn("Fixture Street", run.stdout + run.stderr + denied.stdout + denied.stderr)

    def test_private_input_refuses_noninteractive_use(self):
        run = self.run_profile("set-private", "imprint.city", input="Hidden Fixture\n")
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn("Hidden Fixture", run.stdout + run.stderr)
        self.assertEqual(json.loads((self.base / "profile.json").read_text())["imprint"]["city"], "Fixture City")

    def test_private_input_saves_without_echoing_value(self):
        spec = importlib.util.spec_from_file_location("skill_profile", ROOT / "assets/scripts/profile.py")
        profile = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(profile)
        out = io.StringIO()
        with mock.patch.object(profile, "PROFILE", self.base / "profile.json"), \
             mock.patch.object(sys, "argv", ["profile.py", "set-private", "imprint.city"]), \
             mock.patch.object(sys.stdin, "isatty", return_value=True), \
             mock.patch.object(profile.getpass, "getpass", return_value="Hidden Fixture"), \
             contextlib.redirect_stdout(out):
            profile.main()
        self.assertEqual(json.loads((self.base / "profile.json").read_text())["imprint"]["city"], "Hidden Fixture")
        self.assertNotIn("Hidden Fixture", out.getvalue())


class SetupTests(unittest.TestCase):
    def test_detect_does_not_print_git_name_or_email(self):
        spec = importlib.util.spec_from_file_location("skill_setup", ROOT / "assets/scripts/setup.py")
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        def fake_run(cmd):
            return "Private Fixture Identity" if cmd[0] == "git" else ""
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(setup, "run", side_effect=fake_run), \
             mock.patch.object(pathlib.Path, "home", return_value=pathlib.Path(td)), \
             mock.patch.object(setup.paths, "CONFIG", pathlib.Path(td) / "config.json"), \
             contextlib.redirect_stdout(out):
            setup.detect()
        self.assertNotIn("Private Fixture Identity", out.getvalue())
        self.assertTrue(json.loads(out.getvalue())["gitIdentityConfigured"])


class RecorderTests(unittest.TestCase):
    def test_default_and_invalid_arguments_never_capture(self):
        script = ROOT / "assets/demo/record_timelapse.sh"
        for args in ([], ["--window-id", "0", "/tmp/unused"], ["--window-id", "12", "/tmp/unused", "0"]):
            run = subprocess.run(["bash", str(script), *args], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)

    def test_selected_window_capture_stops_on_failure_without_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            base = pathlib.Path(td)
            stub = base / "screencapture"
            log = base / "args"
            stub.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$CAPTURE_ARGS"\nexit 1\n')
            stub.chmod(0o755)
            env = dict(os.environ, PATH=str(base) + os.pathsep + os.environ["PATH"], CAPTURE_ARGS=str(log))
            run = subprocess.run(["bash", str(ROOT / "assets/demo/record_timelapse.sh"), "--window-id", "123", str(base / "frames")],
                                 env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            args = log.read_text().splitlines()
            self.assertEqual(args[args.index("-l") + 1], "123")
            self.assertNotIn("-D", args)
            self.assertIn("stopped", run.stderr)


if __name__ == "__main__":
    unittest.main()
