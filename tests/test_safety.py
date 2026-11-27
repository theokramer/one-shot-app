import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "assets/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SafetyTests(unittest.TestCase):
    def test_write_commands_fail_before_credential_loading_without_opt_in(self):
        commands = [
            [sys.executable, str(SCRIPTS / "asc.py"), "attach-build", "version", "123"],
            [sys.executable, str(SCRIPTS / "netlify_deploy.py"), "--dir", "fixture", "--site", "fixture"],
            [sys.executable, str(SCRIPTS / "revenuecat.py"), "provision", "--app-name", "Fixture",
             "--bundle-id", "com.example.fixture", "--annual", "annual", "--monthly", "monthly"],
            ["bash", str(ROOT / "assets/expo/release.sh")],
        ]
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, ONE_SHOT_HOME=temp, PYTHONDONTWRITEBYTECODE="1")
            for command in commands:
                with self.subTest(command=command):
                    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=5)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertRegex(result.stderr, r"--apply|--upload")
                    self.assertEqual(list(Path(temp).iterdir()), [])

    def test_asc_rejects_release_access_and_delete_without_network(self):
        asc = load("asc")
        with mock.patch.object(asc, "token", side_effect=AssertionError("credential accessed")):
            for method, path in [
                ("POST", "/v1/reviewSubmissions"),
                ("POST", "/v1/appStoreVersionReleaseRequests"),
                ("POST", "/v1/userInvitations"),
                ("DELETE", "/v1/appPreviews/123"),
                ("POST", "/v1/appStoreVersions/../../reviewSubmissions"),
            ]:
                with self.subTest(path=path), self.assertRaises(SystemExit):
                    asc.asc(method, path)
        asc.check_request("PATCH", "/v1/appStoreVersions/version-id/relationships/build")
        asc.check_request("GET", "/v1/apps?limit=1")

    def test_revenuecat_verification_never_writes(self):
        rc = load("revenuecat")
        client = mock.Mock(spec_set=["items"])
        with mock.patch.object(rc, "client", return_value=client), contextlib.redirect_stdout(io.StringIO()):
            rc.cmd_verify(None)
        client.items.assert_called_once_with("/projects?limit=1")

    def test_netlify_rejects_links_hidden_paths_and_private_file_types(self):
        netlify = load("netlify_deploy")
        for rel in (".git/config", "assets/.env", "assets/key.p8", "review_information/email.txt", "assets/leak.txt"):
            with self.subTest(rel=rel), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                file = directory / rel
                file.parent.mkdir(parents=True, exist_ok=True)
                if rel == "assets/leak.txt":
                    file.symlink_to(directory / "nonexistent")
                else:
                    file.write_text("fixture")
                with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                    netlify.zip_dir(directory)

    def test_redirect_never_reissues_authenticated_request(self):
        module = load("http_safety")
        request = urllib.request.Request("https://example.com", headers={"Authorization": "Bearer fixture"})
        handler = module.NoRedirect()
        self.assertIsNone(handler.redirect_request(request, None, 302, "", {}, "https://example.org"))

    def test_setup_detect_uses_only_local_commands_by_default(self):
        setup = load("setup")
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            with mock.patch.object(setup, "run", return_value="") as run, \
                 mock.patch.object(Path, "home", return_value=Path(temp)), \
                 mock.patch.object(setup.paths, "CONFIG", Path(temp) / "config.json"):
                setup.detect()
        self.assertTrue(all(call.args[0][0] == "git" for call in run.call_args_list))


if __name__ == "__main__":
    unittest.main()
