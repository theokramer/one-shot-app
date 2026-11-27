#!/bin/bash
# Copy to scripts/release.sh in the app repo. Run after approving an Apple build upload.
# Usage: release.sh --upload [--archive PATH]
# Metadata and App Review submission are separate actions.
set -euo pipefail
if [[ ${1:-} != --upload ]]; then
  echo "Usage: release.sh --upload [--archive PATH]. Confirm the destination before uploading." >&2
  exit 2
fi
shift
if [[ ${DELIVER:-0} == 1 ]]; then
  echo "Metadata is a separate action. Use the approved metadata workflow." >&2
  exit 2
fi
AR=
if [[ $# -eq 2 && $1 == --archive ]]; then
  AR=$2
  [[ $AR == /* ]] || AR=$PWD/$AR
elif [[ $# -ne 0 ]]; then
  echo "Expected --archive PATH or no arguments" >&2
  exit 2
fi
cd "$(dirname "$0")/.."
umask 077
CFG=${ONE_SHOT_HOME:-$HOME/.one-shot-app}/config.json
RELEASE_TMP=$(mktemp -d)
trap 'rm -rf -- "$RELEASE_TMP"' EXIT
python3 - "$CFG" > "$RELEASE_TMP/config" <<'PY'
from pathlib import Path
import json
import re
import sys
config = json.loads(Path(sys.argv[1]).read_text())
asc = config["appStoreConnect"]
key_path = str(Path(asc["privateKeyPath"]).expanduser().resolve(strict=True))
for value in (asc["keyId"], asc["issuerId"], config["developer"]["appleTeamID"]):
    if not re.fullmatch(r"[A-Za-z0-9-]+", value):
        raise SystemExit("Invalid signing identifier")
    print(value)
if "\n" in key_path or "\r" in key_path:
    raise SystemExit("Unsupported key path")
print(key_path)
PY
{
  IFS= read -r KEY
  IFS= read -r ISSUER
  IFS= read -r TEAM
  IFS= read -r P8
} < "$RELEASE_TMP/config"
AUTH=(-allowProvisioningUpdates -authenticationKeyPath "$P8" -authenticationKeyID "$KEY" -authenticationKeyIssuerID "$ISSUER")
if [[ -z $AR ]]; then
  shopt -s nullglob
  workspaces=(ios/*.xcworkspace)
  if [[ -z ${APP:-} ]]; then
    [[ ${#workspaces[@]} -eq 1 ]] || { echo "Specify the exact workspace with APP" >&2; exit 2; }
    APP=$(basename "${workspaces[0]}" .xcworkspace)
  fi
  [[ -d ios/$APP.xcworkspace && $APP != */* ]] || { echo "Invalid workspace" >&2; exit 2; }
  AR=$RELEASE_TMP/build.xcarchive
  xcodebuild -workspace "ios/$APP.xcworkspace" -scheme "$APP" -configuration Release \
    -destination generic/platform=iOS -archivePath "$AR" \
    DEVELOPMENT_TEAM="$TEAM" CODE_SIGN_STYLE=Automatic "${AUTH[@]}" archive
fi
[[ -f $AR/Info.plist ]] || { echo "A complete Xcode archive is required" >&2; exit 1; }
python3 - "$AR/Info.plist" "$TEAM" <<'PY_CHECK_ARCHIVE'
import json
import plistlib
from pathlib import Path
import sys
app = json.loads(Path("app.json").read_text())["expo"]["ios"]
with Path(sys.argv[1]).open("rb") as archive:
    properties = plistlib.load(archive).get("ApplicationProperties", {})
if properties.get("CFBundleIdentifier") != app["bundleIdentifier"] or properties.get("Team") != sys.argv[2]:
    raise SystemExit("Archive does not match this project's app bundle and signing team")
PY_CHECK_ARCHIVE

# ExportOptions uses Apple's upload destination, so there is no persistent key copy.
cat > "$RELEASE_TMP/ExportOptions.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key><string>app-store-connect</string>
  <key>destination</key><string>upload</string>
  <key>teamID</key><string>$TEAM</string>
  <key>signingStyle</key><string>automatic</string>
  <key>uploadSymbols</key><true/>
  <key>manageAppVersionAndBuildNumber</key><false/>
</dict>
</plist>
PLIST
xcodebuild -exportArchive -archivePath "$AR" -exportPath "$RELEASE_TMP/export" \
  -exportOptionsPlist "$RELEASE_TMP/ExportOptions.plist" "${AUTH[@]}"
