# Module catalog

Every box in the menu maps to a row here. Phase 4 uses this file to decide what to
install, what to log into and what to do in Chrome while the user is still there. Phase 5
uses it to write the plan.

Legend: **Tool**: what drives it (CLI first). **Login**: one-time interactive login
the user runs. **Attended**: what must happen in phase 4 with the user present.
**Unattended Chrome**: browser work done later using the phase-4 sign-ins. **Tick**:
the permission it needs from round C. **User-only**: never automated, always on the to-do
list.

---

## Always on (core)

| | |
|---|---|
| Tool | Xcode + `xcrun simctl`, `gh`, `git`, Python 3 + Pillow + PyJWT, `ffmpeg`, Node 20+/`npx` (Expo) |
| Login | `gh auth login` (scopes `repo`, `workflow`) |
| Attended | Simulator panel attach (surfaces the device-access prompt) |
| Library | `assets/scripts/profile.py`: identity, **imprint** (needed for every app website), review contact, ad-account IDs, last menu, preferences, past apps. Gaps are asked once and saved |
| Notes | Own simulator: `xcrun simctl create "<App> QA" "iPhone 17 Pro"`. At least 15 GB free disk; archives fail cryptically when the disk is full. |

## App Store Connect (always on; "Write to App Store Connect" tick for writes)

| | |
|---|---|
| Tool | `superwall asc …` (signed proxy: subscriptions, offers, prices, availability, versions, builds, metadata), `assets/scripts/asc.py` (raw API with the `.p8` from config), `fastlane deliver` (metadata + screenshots), `xcrun altool` (upload) |
| Login | `superwall login`; use the direct API or have the user configure the proxy after approving the credential transfer |
| Attended | **Creating the app record.** The public API refuses `POST /v1/apps`. Run `rc setup apple <rc-app-id> --project-id <id>` **in the user's terminal**. It signs into the Apple ID (password + 2FA by the user), creates the app record, and creates the in-app purchase key plus the ASC key for RevenueCat in one go. Give the exact store name to type. Then poll `superwall asc get "/v1/apps?filter[bundleId]=<bundle>"` until it exists. A Chrome sign-in to appstoreconnect.apple.com is also needed if any unattended Chrome item below is in the plan. |
| Unattended Chrome | App Privacy questionnaire + **Publish**, compliance forms (AI-generated content, security), medical-device declaration (usually "No"), Asset Library header/search art, reading Resolution Center history |
| User-only | Paid Apps Agreement + banking/tax (once per account), **Submit for Review** |

## RevenueCat subscriptions

| | |
|---|---|
| Tool | `rc` CLI (`brew install revenuecat/tap/rc` or `npx @revenuecat/cli`). Always `--project-id`, `--json --no-input --yes`. **Never** change the default project, use the RC MCP, or the RC dashboard in a browser. |
| Login | `rc auth login` |
| Attended | `rc setup apple …` (see above). It creates the in-app purchase key that RevenueCat needs to validate receipts. If it fails at the key step ("Couldn't create the in-app purchase key"), check ASC → Users and Access → Integrations for a half-created key and reuse or revoke it. Apple limits how many there can be. |
| Tick | Create & connect accounts |
| Verify | `rc offerings verify <ofrng> --project-id <p>` and `rc offerings preview <app> --public-api-key appl_… --app-user-id x` ("no attached paywall" is expected, because paywalls belong to Superwall) |
| Ref | [monetization.md](monetization.md) |

## Superwall onboarding + paywall

| | |
|---|---|
| Tool | `superwall` CLI v2.7+: `bootstrap`, `apps`, `products`, `entitlements`, `campaigns … placements`, and **paywall-as-code** (`superwall create` → `superwall/` dir, `npx superwall@latest publish -m "…" --no-interactive`). The old "paywalls can't be authored from the CLI" wall is gone. |
| Login | `superwall login` |
| Skills | `superwall-integrate`, `superwall-placements`, `superwall-dashboard`, `app-onboarding-questionnaire`; research per round T ([research-sources.md](research-sources.md)) |
| Tick | Create & connect accounts |
| Ref | [onboarding-paywalls.md](onboarding-paywalls.md) |

## Free trial / intro offer

`superwall asc offers create` (introductory offer, `FREE_TRIAL`, e.g. `THREE_DAYS`) on the
yearly product, in all territories. The paywall shows the trial only when the store says the
user is eligible. Show trial reminders only after a trial has actually started.

## Retention & discounts

| Piece | How |
|---|---|
| Win-back offers | ASC API `winBackOffers` (asc.py): eligibility (paid ≥ N months, lapsed ≥ N days), discount, period, priority. Shown by Apple on the store and in-app via StoreKit 2 / RC `getEligibleWinBackOffers`. |
| Promotional offers | Needs the **subscription offer key** (ASC → Users and Access → Integrations → In-App Purchase key, which `rc setup apple` already created and RC holds). Create offers with asc.py `subscriptionPromotionalOffers`. Used by the cancel flow and the exit paywall. |
| Offer codes | asc.py `subscriptionOfferCodes` + one-time or custom codes (e.g. `LAUNCH30`). Codes go into `store/OFFER_CODES.md`, never into the repo history. |
| Retention price | The menu's round B2 sets it (e.g. **$9.99/yr**) and its form: its own `.yearly.retention` product renewing at that price, or "first year only" as a promo/win-back offer on the normal yearly. Shown only on the surfaces below. Setup: [monetization.md step 4b](monetization.md#step-4b-experiments-from-day-one-and-the-retention-product) |
| Cancel flow | RevenueCat **Customer Center** (`revenuecat:revenuecat-customer-center` skill) with a promotional-offer "before you go" path. Superwall `transaction_abandon` / `paywall_decline` placements show an exit-offer paywall. |
| Retention Messaging API | Apple's server API (preview) that shows a retention message on the cancel sheet. Needs a server endpoint (Cloudflare Worker) plus enrollment. If ASC doesn't offer it to this account yet, write the endpoint stub and put "enable when available" in `POST_LAUNCH.md`, so the run doesn't fail. |
| Ref | [app-store-connect.md](app-store-connect.md#offers-and-retention) |

## Cloudflare Worker (backend + site)

| | |
|---|---|
| Tool | `npx wrangler` (deploy, `secret put`, `d1`, `r2`, `types`), `cloudflare:workers-best-practices`, `cloudflare:wrangler` skills |
| Login | `npx wrangler login` (browser OAuth, so the user clicks Allow) |
| Attended | If the app needs OpenAI: the user runs `npx wrangler secret put OPENAI_API_KEY` themselves and pastes the key. The run never asks for keys in chat and never searches the disk for them. Workers AI requires its own approval and spending limit. |
| Tick | Deploy to the web |
| Notes | Worker names are permanent homes for secrets. Secrets can't be copied, so keep the name even after a rename (keep the old Worker name after an app rename). Rate-limit per device and cap daily spend (`DEVICE_DAILY`/`GLOBAL_DAILY`). |
| Ref | [backend.md](backend.md) |

## Supabase

`supabase` skill + `supabase-postgres-best-practices`; `mcp__supabase__*` or the CLI with
the token from config. Login: `supabase login`, or MCP `/mcp` auth. Requires a separate backend deployment grant. Ref: [backend.md](backend.md).

## GitHub repo + CI/CD

Create a private repo only with approval. Install unsigned CI first. Pushes, merging,
credential sharing and upload automation are separate grants. For Expo, add the approved
native prebuild step or use local archiving. See [CI/CD](cicd.md) and [PR mode](pr-mode.md).

## Localization

Strings keyed by the English text (`de.json` etc.), whole-sentence keys (German articles
change), permission texts per language (`expo.locales` / `InfoPlist.strings`), backend
answers in the user's language (`accept-language` / `x-lang`), listing + screenshots +
preview per locale. Translate with Gemini (`gemini-2.5-flash`) if spend is allowed,
otherwise yourself. Then **check every screen in the simulator in that language**.

## Meta Ads attribution

| | |
|---|---|
| Tool | `react-native-fbsdk-next` / FBSDK (auto-logging **off**), `expo-tracking-transparency` / ATT, RC `setFBAnonymousID` + `collectDeviceIdentifiers` |
| Attended (Chrome) | User signed into developers.facebook.com + Business/Ads Manager. Claude creates the Meta app (tick), adds iOS platform + bundle ID, links the ad account. **User pastes** the client token into RevenueCat → Integrations → Meta Ads (App Events API), because tokens are never typed by Claude. |
| Post-launch | iPhone Store ID can only be saved once the listing is live, so it goes in `POST_LAUNCH.md`. |
| Ref | [ads-attribution.md](ads-attribution.md) |

## TikTok Ads attribution

| | |
|---|---|
| Tool | `react-native-tiktok-business-sdk` / TikTok Business SDK; IDs fetched from the Worker `/v1/config` so they can be set after launch without a build. RevenueCat has no TikTok integration, so use an RC webhook → Worker → TikTok Events API relay. |
| Attended (Chrome) | User signed into ads.tiktok.com. If no ads account exists: the **user** fills the company, industry and payment fields (payment details are never typed by Claude). |
| Post-launch | Events Manager → App → TikTok SDK only accepts a live App Store URL, so the App ID and token are set via `wrangler secret put` after launch. |
| Ref | [ads-attribution.md](ads-attribution.md) |

## Apple Search Ads attribution

`Purchases.enableAdServicesAttributionTokenCollection()` (RC). No ATT, no login. Tick:
none.

## TikTok/Reels clip

Recorded from the simulator (`simctl io recordVideo`), cut with ffmpeg, captions drawn
locally, music per the round-T choice (ACE-Step, silent or own track), 9:16,
under 30 s, the viral moment in the first second.

## Mascot (asked in step 3, not a menu tick)

Three original concepts are sketched and one is picked **before "Go"**. Then a master
plus an expression set (neutral, happy, thinking, celebrate, encourage, sad-miss-you,
sleep), a `Mascot` component with idle motion, and placement in onboarding, the first
win, win-back, empty states, one icon concept, 1–2 screenshots and the site. Images come
from the round-T choice (Gemini/Sunra within the cap, or local SVG at $0). Ref:
[mascot.md](mascot.md)
