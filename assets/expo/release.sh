#!/bin/bash
# TEMPLATE: archive → export → upload an Expo iOS app, then (optionally) push metadata and screenshots.
# Does NOT submit for review. Copy to scripts/release.sh in the app repo; run from anywhere.
#
#   APP=<XcodeName> ./scripts/release.sh          # build + upload
#   SKIP_ARCHIVE=1 ./scripts/release.sh          # re-export/upload an existing archive
#   DELIVER=1 VERSION=1.0.0 ./scripts/release.sh  # also run fastlane deliver from store/fastlane
#
# Reads the ASC key and team ID from ~/.one-shot-app/config.json and never prints them.
# Bump expo.ios.buildNumber in app.json first; run `npx expo prebuild` if native config changed.
set -euo pipefail
cd "$(dirname "$0")/.."
CFG=${ONE_SHOT_HOME:-$HOME/.one-shot-app}/config.json
SKILL=${ONE_SHOT_SKILL:-$HOME/.claude/skills/one-shot-app}
read -r KEY ISSUER P8 TEAM < <(python3 -c "import json,os;c=json.load(open('$CFG'));a=c['appStoreConnect'];print(a['keyId'],a['issuerId'],os.path.expanduser(a['privateKeyPath']),c['developer']['appleTeamID'])")
BUNDLE=$(python3 -c "import json;print(json.load(open('app.json'))['expo']['ios']['bundleIdentifier'])")
APP=${APP:-$(ls -d ios/*.xcworkspace | head -1 | xargs basename | sed 's/.xcworkspace//')}
AUTH=(-allowProvisioningUpdates -authenticationKeyPath "$P8" -authenticationKeyID "$KEY" -authenticationKeyIssuerID "$ISSUER")
AR=ios/build/$APP.xcarchive

if [ "${SKIP_ARCHIVE:-}" != 1 ]; then
  rm -rf "$AR" ios/build/export
  (cd ios && xcodebuild -workspace "$APP.xcworkspace" -scheme "$APP" -configuration Release \
     -destination generic/platform=iOS -archivePath "build/$APP.xcarchive" \
     DEVELOPMENT_TEAM="$TEAM" CODE_SIGN_STYLE=Automatic "${AUTH[@]}" archive > /tmp/$APP-archive.log 2>&1) || true
fi

APPDIR=$AR/Products/Applications/$APP.app
[ -d "$APPDIR" ] || { echo "archive failed; see /tmp/$APP-archive.log"; exit 1; }

# Superwall's libcel xcframework makes the end of `archive` fail with a signature collision,
# before the archive Info.plist is written. The .app is complete and signed, so write the plist.
if [ ! -f "$AR/Info.plist" ]; then
  V=$(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$APPDIR/Info.plist")
  BN=$(/usr/libexec/PlistBuddy -c "Print :CFBundleVersion" "$APPDIR/Info.plist")
  ID=$(codesign -dvv "$APPDIR" 2>&1 | sed -n 's/^Authority=\(Apple .*\)/\1/p' | head -1)
  cat > "$AR/Info.plist" <<P
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>ApplicationProperties</key><dict><key>ApplicationPath</key><string>Applications/$APP.app</string><key>Architectures</key><array><string>arm64</string></array><key>CFBundleIdentifier</key><string>$BUNDLE</string><key>CFBundleShortVersionString</key><string>$V</string><key>CFBundleVersion</key><string>$BN</string><key>SigningIdentity</key><string>$ID</string><key>Team</key><string>$TEAM</string></dict><key>ArchiveVersion</key><integer>2</integer><key>CreationDate</key><date>$(date -u +%Y-%m-%dT%H:%M:%SZ)</date><key>Name</key><string>$APP</string><key>SchemeName</key><string>$APP</string></dict></plist>
P
fi

cat > ios/build/ExportOptions.plist <<P
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>method</key><string>app-store-connect</string><key>destination</key><string>export</string><key>teamID</key><string>$TEAM</string><key>signingStyle</key><string>automatic</string><key>uploadSymbols</key><true/><key>manageAppVersionAndBuildNumber</key><false/></dict></plist>
P
(cd ios && xcodebuild -exportArchive -archivePath "build/$APP.xcarchive" -exportPath build/export \
   -exportOptionsPlist build/ExportOptions.plist "${AUTH[@]}" > /tmp/$APP-export.log 2>&1) || { tail -20 /tmp/$APP-export.log; exit 1; }

mkdir -p ~/.appstoreconnect/private_keys && ln -sf "$P8" ~/.appstoreconnect/private_keys/AuthKey_$KEY.p8
xcrun altool --upload-app -t ios -f "ios/build/export/$APP.ipa" --apiKey "$KEY" --apiIssuer "$ISSUER" 2>&1 | tail -3

if [ "${DELIVER:-}" = 1 ]; then
  T=$(mktemp -d); trap 'rm -rf "$T"' EXIT; umask 077
  python3 -c "import json,sys;print(json.dumps({'key_id':sys.argv[1],'issuer_id':sys.argv[2],'key':open(sys.argv[3]).read(),'in_house':False}))" "$KEY" "$ISSUER" "$P8" > "$T/k.json"
  (cd store && LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 fastlane deliver --api_key_path "$T/k.json" \
     --app_identifier "$BUNDLE" --app_version "${VERSION:-1.0.0}" --metadata_path fastlane/metadata \
     --screenshots_path fastlane/screenshots --skip_binary_upload --overwrite_screenshots --force \
     --submit_for_review false --precheck_include_in_app_purchases false --run_precheck_before_submit false \
     --app_rating_config_path fastlane/age_rating.json)
fi
echo "Uploaded. Next: python3 $SKILL/assets/scripts/asc.py attach-build <versionId> <buildNumber>"
