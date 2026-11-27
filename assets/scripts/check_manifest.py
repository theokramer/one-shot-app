#!/usr/bin/env python3
"""Fails a release before upload if a privacy manifest would make Apple mark the binary invalid.

Apple's upload check passes these builds; App Review then flips the version to
"Invalid Binary" with ITMS-91064, and the reason arrives only by email. So check first.

  python3 check_manifest.py <path.xcarchive | path.app | ios/AppName/PrivacyInfo.xcprivacy>

Rules (from Apple's manifest validation):
- The app's own manifest: NSPrivacyTracking true  -> NSPrivacyTrackingDomains must list
  at least one domain (e.g. Meta SDK: ep1.facebook.com).
- NSPrivacyTracking false -> NSPrivacyTrackingDomains must be empty.
- Any data type collected "for tracking" requires NSPrivacyTracking true.
- Every manifest must parse as a plist.
SDK manifests inside frameworks/bundles get the same consistency check, reported as
warnings (you can't edit them, but you should know).
Exit 1 on any error in the app's own manifest.
"""
import pathlib
import plistlib
import sys


def problems(m):
    out = []
    tracking = m.get("NSPrivacyTracking")
    domains = m.get("NSPrivacyTrackingDomains") or []
    tracked_types = [d.get("NSPrivacyCollectedDataType") for d in m.get("NSPrivacyCollectedDataTypes") or []
                     if d.get("NSPrivacyCollectedDataTypeTracking")]
    if tracking is True and not domains:
        out.append("NSPrivacyTracking is true but NSPrivacyTrackingDomains is empty "
                   "(ITMS-91064). List the tracking SDKs' domains, e.g. ep1.facebook.com for Meta.")
    if tracking is not True and domains:
        out.append("NSPrivacyTrackingDomains is not empty but NSPrivacyTracking is not true (ITMS-91064).")
    if tracked_types and tracking is not True:
        out.append(f"data types marked as tracking ({', '.join(map(str, tracked_types))}) but NSPrivacyTracking is not true.")
    return out


def app_dir(target):
    if target.suffix == ".xcarchive":
        apps = sorted((target / "Products/Applications").glob("*.app"))
        if len(apps) != 1:
            raise SystemExit(f"expected one .app in {target}")
        return apps[0]
    return target


def main(argv):
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    target = pathlib.Path(argv[1])
    if target.name == "PrivacyInfo.xcprivacy":
        own, others = target, []
    else:
        app = app_dir(target)
        own = app / "PrivacyInfo.xcprivacy"
        others = sorted(p for p in app.rglob("PrivacyInfo.xcprivacy") if p != own)
    errors = 0
    if not own.exists():
        print(f"ERROR {own}: missing; the app needs its own privacy manifest")
        return 1
    for path, mine in [(own, True)] + [(p, False) for p in others]:
        try:
            m = plistlib.loads(path.read_bytes())
        except Exception as e:  # noqa: BLE001
            print(f"{'ERROR' if mine else 'WARN '} {path}: does not parse ({e})")
            errors += mine
            continue
        for msg in problems(m):
            print(f"{'ERROR' if mine else 'WARN '} {path}: {msg}")
            errors += mine
    if errors:
        print("Privacy manifest check failed: fix app.json -> ios.privacyManifests, then "
              "`npx expo prebuild --clean` (prebuild never updates an existing PrivacyInfo.xcprivacy).")
        return 1
    print(f"privacy manifests OK ({1 + len(others)} checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
