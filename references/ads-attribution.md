# Ads attribution: Meta, TikTok, Apple Search Ads

The goal isn't running ads. It's that **on launch day, ads can be switched on in minutes
with no new app version**, and every install and purchase that came through an ad shows up
in that network and in RevenueCat.

Template: `assets/expo/ads.ts` (Expo). For SwiftUI, apply the same calls via FBSDKCoreKit,
TikTokBusinessSDK and AppTrackingTransparency.

## In the app (every network)

1. **ATT prompt** at the end of onboarding, right **before the paywall**, behind a priming
   screen with a single "Continue" button (no "Not now"; see 5.1.1(iv)). Returning users
   are asked on launch if the status is still undetermined.
2. Start the SDKs only **after** the ATT answer. Without consent they still report
   aggregated data (SKAdNetwork/AEM).
3. `Purchases.collectDeviceIdentifiers()`, plus per-network IDs into RevenueCat
   (`setFBAnonymousID`, `enableAdServicesAttributionTokenCollection()`).
4. SKAdNetwork IDs for Meta and TikTok in Info.plist (`SKAdNetworkItems`).
5. Privacy manifest + App Privacy: tracking = **yes** for Device ID, Purchase History,
   Product Interaction. Name Meta and TikTok in the privacy policy.
6. **Attribution must never break the app**: wrap it in try/catch, and use a 5 s timeout
   on the config fetch.
7. Verify on the simulator: launch, then grep the log for `ep2.facebook.com/…/<META_APP_ID>`.

## Meta

| Step | Where | Who |
|---|---|---|
| Create the Meta app (type Business/Other), add iOS platform + bundle ID | developers.facebook.com, 🌐 phase 4 | Claude (tick "Create & connect") |
| Turn **off** "Log in-app events automatically" (RevenueCat sends purchases, so they'd be counted twice) | App settings | Claude |
| Link the app to the ad account / business portfolio | Business settings / Ads Manager | Claude, phase 4 |
| Client token → RevenueCat → Integrations → Meta Ads (**App Events API**, App ID + client token) | RevenueCat dashboard | **user pastes**, phase 4 |
| Conversions API dataset + token (optional, needs a business portfolio) | Events Manager | post-launch, user |
| iPhone Store ID | App settings → Basic → iOS | **post-launch** (Meta rejects it until the listing is live) |

App ID + client token go into `app.json` (`react-native-fbsdk-next` plugin) or
Info.plist. Both are public identifiers, not secrets.

## TikTok

RevenueCat has **no TikTok integration**, so use a relay:

```
RevenueCat webhook ──▶ Worker /hooks/revenuecat/<RC_WEBHOOK_AUTH> ──▶ TikTok Events API
```

- The app starts the TikTok Business SDK with an App ID and token from
  `GET <worker>/v1/config`. When those are empty (pre-launch), the SDK simply doesn't
  start. After launch, `wrangler secret put TIKTOK_APP_ID` / `TIKTOK_ACCESS_TOKEN`
  switches it on. **No new build.**
- RC webhook: `rc` CLI (or the RevenueCat API) → URL with a random path secret, events
  INITIAL_PURCHASE, RENEWAL, TRIAL_CONVERTED.
- TikTok Ads account: if none exists, the **user** creates it (company, industry, budget,
  payment). Claude can open the form and say exactly which fields it needs.
- Events Manager → Connect data source → App → TikTok SDK only works once the app is live
  (TikTok crawls the store URL), so it goes in `POST_LAUNCH.md`.

## Apple Search Ads

`Purchases.enableAdServicesAttributionTokenCollection()`. No ATT, no setup.

## `store/POST_LAUNCH.md` (always written when any ads module is ticked)

A five-minute checklist per network for the day the app goes live: exact URLs, the
`wrangler secret put` commands, the curl check (`/v1/config` shows the IDs), what to turn
off to avoid double counting, and the Product Page Optimization test to start.
