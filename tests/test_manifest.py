"""check_manifest.py rejects the manifests Apple turns into ITMS-91064."""
import importlib.util
import pathlib
import plistlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_manifest", ROOT / "assets/scripts/check_manifest.py")
cm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cm)


def run(manifest):
    with tempfile.TemporaryDirectory() as d:
        app = pathlib.Path(d) / "X.xcarchive/Products/Applications/X.app"
        app.mkdir(parents=True)
        (app / "PrivacyInfo.xcprivacy").write_bytes(plistlib.dumps(manifest))
        return cm.main(["x", str(app.parents[2])])


class ManifestTests(unittest.TestCase):
    def test_tracking_without_domains_fails(self):
        self.assertEqual(run({"NSPrivacyTracking": True, "NSPrivacyTrackingDomains": []}), 1)

    def test_domains_without_tracking_fails(self):
        self.assertEqual(run({"NSPrivacyTracking": False, "NSPrivacyTrackingDomains": ["ep1.facebook.com"]}), 1)

    def test_tracked_data_requires_tracking(self):
        m = {"NSPrivacyTracking": False, "NSPrivacyCollectedDataTypes": [
            {"NSPrivacyCollectedDataType": "NSPrivacyCollectedDataTypeDeviceID", "NSPrivacyCollectedDataTypeTracking": True}]}
        self.assertEqual(run(m), 1)

    def test_valid_manifests_pass(self):
        self.assertEqual(run({"NSPrivacyTracking": True, "NSPrivacyTrackingDomains": ["ep1.facebook.com"]}), 0)
        self.assertEqual(run({"NSPrivacyTracking": False, "NSPrivacyTrackingDomains": []}), 0)


if __name__ == "__main__":
    unittest.main()
