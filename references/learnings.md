# Learnings from past one-shot runs

Read this before phase 1, together with the user's own `~/.one-shot-app/learnings.md`
(their taste, accounts and history). Everything here cost hours once, while building real
subscription apps (one SwiftUI, three Expo) with this skill.

Where new learnings go at the end of a run (phase 11):
- about **this user** (taste, accounts, their apps): `~/.one-shot-app/learnings.md` and the
  library (`profile.py add-pref`)
- about **one app**: that repo's `LEARNINGS.md`
- **general and reusable by anyone**: here, written without names, IDs or paths

## Default taste (the user's library preferences override this)

- Make the design decisions yourself; ask only about permission, money, naming and legal data.
- Premium and real, never "AI-generated looking": real captures, licensed 3D (Poly Haven
  CC0, ABO CC BY 4.0, MPFB/MakeHuman CC0 for people, rendered in Blender), never stick
  figures. Check faces and motion frame by frame.
- One viral, shareable feature per app; more depth than competitors around one clear centre.
- Store art and videos follow [launch-assets.md](launch-assets.md); onboarding and paywalls
  follow [conversion.md](conversion.md).
- Ask before any spend; never submit for review, spend or launch ads without an explicit OK.


## Apple review lessons (real rejections behind this skill)

| Guideline | What happened | Rule |
|---|---|---|
| 5.1.1(iv) | A priming screen had "Turn on camera" + "Not now" | One "Continue" button that always leads to the system prompt |
| 2.1(b) | Picking weekly still bought annual (rejected twice) | Test that the selected plan is the one purchased; the legal text follows the selected plan |
| 5.1.2 | Privacy labels didn't match; an unneeded tracking prompt was shown | Labels = code = manifest = policy. ATT only with real tracking SDKs |
| 1.3 | Analytics SDK in a Kids-category app | No Kids category with any analytics or ads SDK |
| 2.3.2 | Paid features unclear in the description | Description lists free vs Pro, trial, renewal, Terms/Privacy |
| 3.1.2 | (rule) | Paywall: price, period, trial, auto-renew, Restore, Terms, Privacy |
| 5.1.2(i) | (proactive) | Explicit consent naming the AI provider before sending user data |
| 4.3 | (risk) | Two similar apps on one account. Check the library's `apps` for overlap before naming a new one |

The ASC API shows submission history but **not** the rejection text. That lives in
Resolution Center / each app's History page (🌐), which goes back about 180 days. Older
texts can be found by grepping `~/.claude/projects/*/*.jsonl` for "Guideline" / "We noticed".


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
- Generative-AI apps: exclude mainland China from availability.
- The App Review contact phone/name has to be real; take it from config or put it on the
  to-do list.

## RevenueCat / Superwall

- `rc` CLI only, `--project-id` always, never switch the default project. "Offering has no
  attached paywall" from `rc offerings verify` is expected.
- Apple server notifications → RevenueCat (V2): RC app page → "Apply in App Store Connect"
  or `rc setup apple`.
- A test device that never logs in to RC with its own app user ID breaks server-side Pro
  checks. Call `Purchases.logIn(deviceId)` before the first server call.
- Superwall paywall-as-code works (`superwall create`, `npx superwall@latest publish`).
  Native fallback after 4 s.
- Expo: the `useUser().update` dependency-array loop froze onboarding (200 % CPU). Use refs.

## Build / tooling

- The Superwall libcel signature collision on archive is harmless: write the archive
  `Info.plist` by hand (the release script does).
- The Apple **team** ID (ASC → Membership) ≠ the personal ID shown on the signing certificate.
- Keep ≥ 15 GB free disk. Clear the app's DerivedData and old recordings.
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
