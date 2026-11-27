# Monetization — RevenueCat owns entitlements, Superwall owns presentation

## The one architectural rule

**RevenueCat is the source of truth for what a customer is entitled to. Superwall is a
presentation layer that never transacts.** Superwall hands the tapped product to
`RCPurchaseController`, RevenueCat purchases it, and the `CustomerInfo` stream pushes the
resulting entitlements back into `Superwall.shared.subscriptionStatus`.

```
        ┌─────────────┐   presents    ┌──────────────┐
        │  Superwall  │ ────────────▶ │  Paywall UI  │
        │  (campaign) │               └──────┬───────┘
        └─────────────┘                      │ user taps buy
               ▲                             ▼
               │ subscriptionStatus   ┌──────────────────────┐
               │                      │ RCPurchaseController │
               └───────────────────── │  (PurchaseController)│
                                      └──────────┬───────────┘
                                                 │ purchase / restore
                                                 ▼
                                      ┌──────────────────────┐
                                      │      RevenueCat      │──▶ entitlements
                                      └──────────────────────┘
```

Configuring Superwall without a `purchaseController` lets it transact directly, which
immediately gives you two disagreeing sources of truth. Don't.

---

## Step 1: Provision RevenueCat with the `rc` CLI

Use the `rc` CLI for RevenueCat provisioning:
**`rc` only, always `--project-id`, never change the default project, never the RevenueCat
MCP, never the dashboard in a browser.** The `revenuecat-cli` skill is the flag reference
(`rc commands --schemas --json` for exact flags).

The project and app already exist from phase 4.2, and `rc setup apple` (phase 4.3) has
connected the App Store keys. Now, idempotently:

```bash
P=<proj id>; A=<app id>; RC="rc --project-id $P --json --no-input --yes"
$RC entitlements create --lookup-key pro --display-name "<App> Pro"
$RC products create ...   # <bundle>.pro.yearly and .pro.weekly, App Store, subscription
$RC entitlements attach <entl> <prod_yearly> <prod_weekly>   # the step everyone forgets
$RC offerings create ...  # lookup key "default"; then: $RC offerings set-current <ofrng>
$RC packages create <ofrng> --lookup-key '$rc_annual' --display-name "Yearly"
$RC packages create <ofrng> --lookup-key '$rc_weekly' --display-name "Weekly"
$RC packages attach <pkg> <prod>                              # one product per package
rc apps keys $A --project-id $P --json                        # → appl_… public SDK key (goes in source)
rc webhooks create --name "TikTok relay" --url <worker>/hooks/revenuecat/<secret>   # TikTok module only
rc offerings verify <ofrng> --project-id $P
```

Script it in Python (`subprocess` + `json`), so every ID is read back rather than copied
by hand, and write them into `docs/RUN.md`.

The attachment is the critical part. Without `entitlement ← products`, a real purchase
completes and Pro stays off: the customer paid and still sees the free tier.

Fallback only if `rc` is unavailable: `assets/scripts/revenuecat.py provision` (REST v2 with
`revenuecat.apiV2Key` from config; needs read_write scopes).

## Step 2 — Provision Superwall over the CLI

```bash
superwall apps create "<AppName>" --platform ios --bundle "<bundle.id>"
superwall apps list --json          # read back the pk_… key and the numeric app/project ids
superwall entitlements list --project <pid> --json   # 'pro' is auto-created with the app
superwall products create "<bundle.id>.pro.annual"  --name "<AppName> Pro (annual)" \
  --price 29.99 --currency EUR --period year --trial-days 3 \
  --entitlement <numeric-entitlement-id> --project <pid> --app <aid>
superwall products create "<bundle.id>.pro.monthly" --name "<AppName> Pro (monthly)" \
  --price 4.99 --currency EUR --period month \
  --entitlement <numeric-entitlement-id> --project <pid> --app <aid>
superwall products storekit --project <pid> --app <aid> --out Products.storekit
```

Two traps, each worth a round trip:

- `--entitlement` takes the **numeric id** from `superwall entitlements list --json`, not
  the string `pro`. Passing `pro` fails with `Unable to decode "pro" into a number`.
- With more than one Superwall project you must pass `--project` and `--app` on every
  command, or the CLI refuses with `Multiple projects found`.

Point the shared scheme at the generated `Products.storekit` so the simulator shows real
prices — inside `<LaunchAction>`, path relative to the `.xcscheme`:

```xml
<StoreKitConfigurationFileReference identifier = "../../../Products.storekit">
</StoreKitConfigurationFileReference>
```

## Step 3 — Campaigns and placements

```bash
superwall campaigns create "<AppName> Pro" paywall_generic --project <pid> --app <aid>
for p in onboarding_paywall feature_history feature_export …; do
  superwall campaigns placement <campaign-id> "$p" --project <pid> --app <aid>
done
```

Placement strings are a published contract — see
[onboarding-paywalls.md](onboarding-paywalls.md).

## Step 4: The paywall itself (paywall-as-code + native fallback)

Superwall paywalls can now be written as code and published from the CLI:

```bash
cd <repo> && superwall create            # makes superwall/ (paywalls/<name>/, config.ts)
# write the paywall in React under superwall/paywalls/pro/app/, messages/<lang>.ts per language
npx superwall@latest publish -m "Initial Pro paywall" --no-interactive
superwall campaigns ... # put the published paywall on the campaign that carries the placements
```

The `superwall-framework` skill (installed by `superwall login`) and
`superwall-editor` cover the layout system. Design it from the paywall research (chosen tools, [research-sources.md](research-sources.md)). It must
show price, period, trial terms, auto-renew text, Restore, Terms and Privacy, and the legal
line has to **follow the selected plan**.

The app **also** ships a native paywall that always works:

- SwiftUI: `assets/swift/PaywallGate.swift` + `NativePaywallView.swift`
- Expo: `assets/expo/Monetise.tsx` falls back to the `/paywall` route

If Superwall hasn't presented within 4 s, or it skips or errors, the native paywall shows.
If the native one is already up when Superwall arrives late, Superwall's is dismissed. Without
this fallback, a campaign with no paywall assigned lets **every gate fall open** and free
equals Pro.

## Step 4b: Experiments from day one, and the retention product

Read `paywallVariants`, `priceTests`, `retentionPrice` and `retentionForm` from `docs/RUN.md`.

**Why every price is its own product:** one App Store product has one price per
storefront. A price test therefore means several products in the **same subscription
group**, so users can switch between them and RevenueCat sees one subscription. Never use
a different group for a tested price.

| Product | Example id | Price | Shown where | Group level |
|---|---|---|---|---|
| Default yearly | `<bundle>.pro.yearly` | default (e.g. $39.99) | every paywall, variant A | 1 (highest) |
| Test yearly B / C | `<bundle>.pro.yearly.b`, `.c` | e.g. $49.99 / $29.99 | price-test variants only | same level as default |
| Weekly or monthly | `<bundle>.pro.weekly` / `.monthly` | e.g. $6.99 / $9.99 | the one short plan next to yearly (a paywall shows two plans, never three) | 1 |
| Retention yearly ("that price, every year") | `<bundle>.pro.yearly.retention` | e.g. $9.99 | retention surfaces only | lowest level |

Set it up in all three systems:

1. **App Store Connect**: create every product in the group, with a price, localizations,
   the review screenshot and the same trial (the retention product has **no trial**). All
   products are submitted with v1. Products added later need a new version.
2. **RevenueCat**: attach **every** product to the `pro` entitlement, so a buyer of any
   variant is Pro. Offerings: `default` (A), `price_b`, `price_c`, and `retention` (the
   retention product, or the yearly with the offer). Superwall picks the products;
   RevenueCat only has to recognise them.
3. **Superwall**: one paywall per design × price, all published from `superwall/`. One
   campaign on `onboarding_paywall` (and `paywall_generic`) with the variants split evenly
   (2 → 50/50, 3 → 34/33/33; paywall designs × prices → the cross product, capped at 4
   variants, so drop the weakest combinations first). **No holdout.** Feature-gate
   placements show the variant the user was already assigned, so people don't see two prices.
4. **Retention surfaces** (only these ever show the retention price):
   - Superwall `transaction_abandon` and `paywall_decline` → the retention paywall, **once
     per user** (a Superwall audience filter on a user attribute `retention_offer_seen`)
   - RevenueCat Customer Center cancel flow → "Before you go" with the retention offer
   - Win-back (lapsed subscribers): an ASC win-back offer on the default yearly, at the
     retention price for the first year, plus Superwall `paywall_winback`
   - Apple's cancel sheet via Retention Messaging (where available): the promotional offer
5. **"First year only" form**: no extra product. Create a **promotional offer** (pay up
   front, 1 year, at the retention price) on the default yearly, and the same as a
   **win-back offer**. The cancel flow and the exit paywall redeem the promo offer through
   RevenueCat (`Purchases.getPromotionalOffer` / `purchase(package:promotionalOffer:)`).
6. Never use a dark pattern. The retention paywall says the price, the period and that it
   renews (at that price, or at the regular price after the first year), with Restore,
   Terms and Privacy like every paywall.

Name products and paywalls so the analytics read themselves (`yearly.b`,
`pw_multi_49`, `pw_single_39`). Write the experiment table (variant · design · products ·
split · placement) into `docs/EXPERIMENTS.md`, and the readout plan into `POST_LAUNCH.md`:
the primary metric is **trial→paid revenue per paywall view** (Superwall's results plus
RevenueCat charts), checked once each variant has ~100 trials. Don't run RevenueCat
Experiments on the same users at the same time, because two systems splitting the same
traffic make both readings useless.

## Step 5 — Wire the app

Configuration order is load-bearing:

```swift
Purchases.configure(withAPIKey: "appl_…")                  // 1. RevenueCat first
let controller = RCPurchaseController()                     // 2. sets .shared
Superwall.configure(apiKey: "pk_…", purchaseController: controller)
controller.syncSubscriptionStatus()                         // 3. after both
Superwall.shared.delegate = SuperwallActionHandler.shared   // 4. last, so flow buttons work
```

Both keys are public client SDK keys and belong in source. They are deliberately not routed
through `AppConfiguration` — that indirection exists for per-environment backend URLs, which
these are not.

## Step 6 — Gate as you build, not afterwards

Wire the free/pro table against `RCPurchaseController.shared.isProActive` and
`PaywallGate.shared.present` **as each feature is written**. Retrofitting gates is how you
end up with a free tier that leaks.

For a countable limit, check first and present only when the limit is hit:

```swift
if store.canAddRecurring(isPro: purchases.isProActive) {
    isCreating = true
} else {
    PaywallGate.shared.present(Placement.feature(Placement.Feature.recurringLimit)) {
        isCreating = true
    }
}
```

## Step 7 — Apple's side

Subscriptions must exist in App Store Connect or the paywall renders with no prices. Use
the proxy's typed commands (see [app-store-connect.md](app-store-connect.md)):

```bash
superwall asc subscription-groups create ...
superwall asc subscriptions create ...      # one ready for review
superwall asc prices set ... ; superwall asc offers create ...   # trial
superwall asc localizations add ... ; superwall asc screenshots upload ...  # paywall capture
```

Product ids must match the ones given to RevenueCat and Superwall exactly.

## Verification before leaving this phase

```bash
rc offerings verify <ofrng> --project-id <p>
superwall doctor
```

Then in the simulator: hit a gated feature → a paywall appears (Superwall's or the native
one) → prices are real, not placeholders → Restore is visible → buy against the StoreKit
config → the gate opens and stays open after a relaunch.
