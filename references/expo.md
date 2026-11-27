# Expo / React Native path

Used for three shipped Expo apps. Use this instead of [scaffold.md](scaffold.md)
(SwiftUI) when "Expo" was picked. [app-build.md](app-build.md) still applies for the
product side.

## Scaffold

```bash
npx create-expo-app@latest <App> --template default   # expo-router
cd <App> && npx expo install expo-dev-client           # dev only, never in the release build (see below)
```

- **Dev build, never Expo Go.** Native modules (Superwall, RevenueCat, FBSDK, MediaPipe,
  Skia, maps) need `npx expo run:ios`.
- `app.json`: `ios.bundleIdentifier`, `ios.buildNumber` (bump every upload),
  `ios.appleTeamId` = **`config.developer.appleTeamID`**. Watch out: the certificate shows
  a *personal* ID, which is **not** the team ID from ASC → Membership.
  `ITSAppUsesNonExemptEncryption: false`, `CFBundleAllowMixedLocalizations: true` when
  localized, `ios.privacyManifests` filled.
- Typical stack that worked: expo-router (native tabs), Reanimated 4, Skia,
  zustand (persisted), TanStack Query, expo-image, expo-haptics.
- Libraries with known fixes: **react-native-maps ≥ 1.29** (1.20 crashes on the new
  architecture when pins are tapped fast); `expo-secure-store` with
  `{"faceIDPermission": false}` unless Face ID is really used.

## Native config

- `npx expo prebuild --platform ios --no-install && (cd ios && LANG=en_US.UTF-8 pod install)`
  every time plugins, Info.plist, locales or native modules change.
- **prebuild merges Info.plist; it never removes keys.** To drop a stale key, write a tiny
  config plugin (e.g. `plugins/withoutDevKeys.js` that deletes the keys), and make sure the release build
  contains **no expo-dev-client** (it adds the local-network permission, a review flag).
- Xcode 26 + Expo SDK 58: `patches/expo-modules-jsi+58.x.patch` via patch-package
  (JavaScriptExecutor resumed async jobs off the JS thread → random SIGSEGV/SIGBUS on
  iOS 26). Re-check after every Expo upgrade; drop it once expo/expo#52462 is fixed.
- Simulator release builds that hit keychain-entitlement errors: build with
  `CODE_SIGN_IDENTITY=- CODE_SIGNING_REQUIRED=NO`.

## Monetization

Template: `assets/expo/Monetise.tsx`. It contains:

- `CustomPurchaseControllerProvider` (Superwall presents, RevenueCat buys and restores)
- `SuperwallProvider` + a `Bridge` that registers placements and falls back to the native
  paywall after **4 s** or on `onSkip`/`onError`, closes a late Superwall paywall if the
  native one already took over, and mirrors `isPro` into `setSubscriptionStatus`
- onboarding answers sent as Superwall user attributes, so campaigns can target them

**The bug that froze an onboarding at 200 % CPU:** `useUser().update`,
`setSubscriptionStatus`, `dismiss` and `registerPlacement` change identity on every
render. Never put them in an effect's dependency array. Call them through refs (the
template does).

Paywall-as-code: `superwall create` makes `superwall/`. Write the paywall in React there,
add `messages/<lang>.ts` per language, and ship with
`npx superwall@latest publish -m "…" --no-interactive`.

## Release

Template: `assets/expo/release.sh`. It archives, exports with the ASC key from config,
and uploads with `altool`, then optionally runs `fastlane deliver` for metadata.

- **Superwall's libcel xcframework always breaks the end of `xcodebuild archive`** with a
  signature collision, and no archive `Info.plist` is written. The app inside is complete
  and signed. The script writes the plist by hand and exports. Don't try to "fix" it.
- Archive ~10 min. Run it in the background, then `asc.py attach-build` waits for
  `VALID` (5–15 min) and attaches it.

## QA in the simulator

- Your own device: `xcrun simctl create "<App> QA" "iPhone 17 Pro"`, and always pass that
  UDID to avoid interacting with another session's app.
- Taps sometimes stop arriving while the app is fine. Check with `sample <pid>`; if the
  main thread is idle, `xcrun simctl shutdown <udid> && xcrun simctl boot <udid>`. Don't
  chase it as an app bug.
- Persisted state: `…/data/Containers/Data/Application/<id>/Library/Application Support/<bundle>/`
  (AsyncStorage manifest), or the sqlite file. Edit it with the app terminated, to seed
  screenshots or reset a free-use counter.
- Locale: `xcrun simctl spawn <udid> defaults write -g AppleLanguages -array de-DE`, then
  reboot the simulator.
- Clean status bar: `xcrun simctl status_bar <udid> override --time 9:41 --batteryState charged --batteryLevel 100 --cellularBars 4 --wifiBars 3`.
- Animations: `xcrun simctl io <udid> recordVideo` (wait for "Recording started" before
  tapping), then pull frames with ffmpeg.
- Metro `ENOTEMPTY` when another project bundles at the same time: clear the cache and
  rebuild. Disk full shows up as "error opening … for output": clear
  `~/Library/Developer/Xcode/DerivedData/<App>-*` and old recordings.
- A device ID kept in the keychain survives reinstalls, so free-use counters don't reset
  on reinstall. That's intended, but remember it when a demo hits a paywall early.

## i18n

`t()` exported as `tr` (because `t` is usually the theme), English strings as keys,
`de.json` etc. Whole-sentence keys, `{placeholders}`, decimal comma, permission texts via
`expo.locales` → `locales/<lang>.json`. Extract strings with a TS-AST script and translate
in bulk, then fix by hand anything that reads machine-made.
