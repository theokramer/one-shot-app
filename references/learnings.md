# Implementation guidance

Read this before phase 1. Keep user-specific preferences, accounts and history in the
local data home; load only the portions needed for the current task.

Where new learnings go at the end of a run (phase 11):
- about **this user** (taste, accounts, their apps): `~/.one-shot-app/learnings.md` and the
  library (`profile.py add-pref`)
- about **one app**: that repo's `LEARNINGS.md`
- **general and reusable by anyone**: here, written without names, IDs or paths

## Default design guidance (saved preferences can override this)

- Make the design decisions yourself; ask only about permission, money, naming and legal data.
- Premium and real, never "AI-generated looking": real captures, licensed 3D (Poly Haven
  CC0, ABO CC BY 4.0, MPFB/MakeHuman CC0 for people, rendered in Blender), never stick
  figures. Check faces and motion frame by frame.
- One viral, shareable feature per app; more depth than competitors around one clear centre.
- Store art and videos follow [launch-assets.md](launch-assets.md); onboarding and paywalls
  follow [conversion.md](conversion.md).
- Ask before any spend; never submit for review, spend or launch ads without an explicit OK.


## App Review checks

| Guideline | Check | Rule |
|---|---|---|
| 5.1.1(iv) | Permission priming | One "Continue" button that always leads to the system prompt |
| 2.1(b) | Selected subscription matches the purchase | Test that the selected plan is the one purchased; the legal text follows the selected plan |
| 5.1.2 | Privacy declarations and tracking consent | Labels = code = manifest = policy. ATT only with real tracking SDKs |
| 1.3 | Kids-category SDK suitability | No Kids category with any analytics or ads SDK |
| 2.3.2 | Clear paid-feature descriptions | Description lists free vs Pro, trial, renewal, Terms/Privacy |
| 3.1.2 | (rule) | Paywall: price, period, trial, auto-renew, Restore, Terms, Privacy |
| 5.1.2(i) | (proactive) | Explicit consent naming the AI provider before sending user data |
| 4.3 | (risk) | Two similar apps on one account. Check the library's `apps` for overlap before naming a new one |

The ASC API shows submission history but **not** the rejection text. That lives in
Resolution Center / each app's History page (🌐), which goes back about 180 days. Use only review correspondence supplied or authorized for the current app; do not search
unrelated chat logs.


## App Store Connect

- App records: only through `rc setup apple` (Apple ID + 2FA by the user). It also makes the
  In-App Purchase key and the ASC key for RevenueCat. If it fails halfway, a key may be left
  over and count toward Apple's limit, so reuse or revoke it.
- The first subscription has to go in with an app version
  (`FIRST_SUBSCRIPTION_MUST_BE_SUBMITTED_ON_VERSION`).
- Subscriptions need a review screenshot, or they stay "Missing Metadata".
- fastlane deliver: `LANG=en_US.UTF-8`, an inline key JSON, `socialMedia` in the age-rating
  JSON.
- Asset Library (header/search art) and App Privacy only work in the web UI. The language
  dropdown adds a new language if you click one row too low.
- Product Page Optimization only opens after launch. Custom product pages work before.
- Screenshot sets are moving to an "asset library" model (API 4.5+). If a set endpoint
  answers oddly, read the current docs.
- Generative-AI apps: exclude mainland China from availability. `POST /v2/appAvailabilities`
  with every territory inline (`available: false` only for `CHN`) works in one call.
- The store name limit is 30 characters, including the ": benefit" part. Check the length of
  every name option before offering it, in every language.
- Adding an `appInfoLocalization` auto-creates the matching `appStoreVersionLocalization`, so
  a follow-up POST for the version text returns 409. Read, then PATCH.
- Copyright (`appStoreVersions.copyright`) and Content Rights (web UI → App Information) are
  easy to miss and block submission. Set both in the baseline.
- The newer web UI has no screenshot well on the version page: screenshots and previews are
  API-only, and the "Header and Search Results" tabs take direct file uploads. A custom
  product page cannot be made the default; to promote one, replace the default page's set.
- Decide the default screenshot set **before** uploading: replacing it means deleting
  screenshots (sets hold at most 10), and write tools may block deletes.
- Win-back offers and offer codes need an **approved** subscription (409
  `NON_APPROVED_SUBSCRIPTION`; win-back `startDate` must also be at least two days out).
  Promotional offers can be created before review. Queue the rest for launch day.
- Subscription review screenshot: one real capture of the paywall, uploaded to every
  product (`superwall asc screenshots upload <file> --subscription <id>`).
- The App Review contact phone/name has to be real; take it from config or put it on the
  to-do list.

## RevenueCat / Superwall

- `rc` CLI only, `--project-id` always, never switch the default project. "Offering has no
  attached paywall" from `rc offerings verify` is expected.
- Apple server notifications → RevenueCat (V2): the RC app page may only offer "Reveal" for
  the URL (no apply button) and `rc setup apple` may not set it. The URL is a secret, so the
  user reveals it and pastes it into App Store Connect → App Information → Production Server
  URL in the attended block. Check it before "Go".
- `rc` subcommand `--help` can print the root help. Find flags from the error messages
  (`--store-id is required`, `app ID is required`) or `rc schema`; grants and attaches take
  positional IDs (`rc customers grant <customer> <entitlement> --duration weekly`).
- Superwall paywall-as-code folders must be kebab-case (`superwall/paywalls/my-paywall`);
  folders with underscores are not discovered. `campaigns placements create` needs `--yes`.
- Superwall paywall: keep the CTA visible above the fold (sticky actions bar), and compute
  "Save X %" against twelve monthly payments, not weekly × 52 (a 90 %+ badge reads as a trick).
- A test device that never logs in to RC with its own app user ID breaks server-side Pro
  checks. Call `Purchases.logIn(deviceId)` before the first server call.
- Superwall paywall-as-code works (`superwall create`, `npx superwall@latest publish`).
  Native fallback after 4 s.
- Expo: avoid dependency-array loops involving `useUser().update`; use stable refs.

## Build / tooling

- The Superwall libcel signature collision on archive is harmless: write the archive
  `Info.plist` by hand (the release script does).
- The Apple **team** ID (ASC → Membership) ≠ the personal ID shown on the signing certificate.
- Keep ≥ 15 GB free disk. Clear the app's DerivedData and old recordings. Check disk and swap
  before every heavy job; an archive plus local music generation on 18 GB RAM once pushed
  swap to 20 GB and the disk under 2 GB. Generate music before builds, alone.
- Simulator Release builds: `CODE_SIGNING_ALLOWED=NO` strips the keychain entitlement, so
  secure storage fails and every API call looks "offline". Use `CODE_SIGN_IDENTITY=-
  CODE_SIGNING_REQUIRED=NO`. Map only network failures to "offline" in the API client.
- `expo run:ios` re-runs `pod install` without a UTF-8 locale and dies on CDN hiccups. Export
  `LANG=en_US.UTF-8`, run `pod install` once yourself, then build with `xcodebuild`.
- A Debug build without expo-dev-client asks Metro on port 8081. For another port, set
  `defaults write <bundle> RCT_jsLocation 127.0.0.1:<port>` on the simulator.
- Don't copy `node_modules` (or `.git`) from another project to save time; it breaks module
  resolution. Do a clean install.
- `expo-secure-store` adds `NSFaceIDUsageDescription` unless configured with
  `faceIDPermission: false`; prebuild never removes keys, so rebuild with `--clean`.
- Simulator taps get dropped while an archive saturates the CPU. Capture screenshots and
  videos when no build is running, and screenshot after each step.
- Cloudflare's bot protection answers 403 to Python's default `urllib` user agent; scripts
  that call the app's Worker must send their own `User-Agent`.
- LLM output: strip markdown emphasis (`*word*`) from every string server-side before it
  reaches chat bubbles or notifications.
- Expo Router: after onboarding, `replace('/')` and then `push` the first detail screen, so
  the back button returns to the tabs.
- Simulator: your own named device; tap delivery can hang (reboot it); the shared iPhone 17
  belongs to other sessions.
- Gemini: images `gemini-3-pro-image` / `gemini-3.1-flash-image`, video
  `gemini-omni-1.2-flash` via `POST /v1beta/interactions` with
  `response_format {type: 'video', …}` (~$0.42 per 6 s 720p clip), translation
  `gemini-2.5-flash`. A 429 "spending cap" means the user raises the cap in Google Cloud.
  A Gemini *subscription* (AI Pro, Edu) does not fund the API.
- Free commercial-use data: Open-Meteo's free tier is **non-commercial** (needs a key for
  commercial use); OpenStreetMap is ODbL (attribution).
- Auto mode blocks searching the disk for `.p8` / key files. Use the paths in config.json
  and never hunt for keys in other projects.

## Ads

- Meta rejects the iPhone Store ID before launch; TikTok won't register an app before
  launch. Wire everything with server-provided IDs, and finish the rest on launch day
  (`POST_LAUNCH.md`).
- Claude never types tokens or payment details, even with permission. Hand the user the
  exact field.
- Ad SDKs mean App Privacy has tracking = yes, plus an ATT prompt.
