# QA loop (and the optional demo stop)

By default the user is gone by now, so **you** are the demo audience. Build the app, drive
every flow in the simulator, fix what's broken, and repeat until a fresh install runs clean
end to end. The final report shows the result.

If the user ticked **"One demo stop"** in the menu, stop once after the QA loop passes,
before phase 9: show screenshots, take their change requests, apply them, and re-QA. That
is the only allowed stop. Otherwise, never wait for the user here.

Use your own simulator (`<App> QA`, created with `xcrun simctl create`), never the shared
iPhone 17.

## Protocol

### 1. Open the panel first

```
mcp__Claude_Code_iOS_Simulator__control  action: "attach"
```

Before building. It's cheap, it opens instantly on a booted simulator, and it surfaces the
one-time device-access prompt while the user is still at the keyboard. If nothing is booted
it errors harmlessly — boot or build, then retry.

### 2. Build and launch

```bash
xcodebuild -project <AppName>.xcodeproj -scheme <AppName> -configuration Debug \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -derivedDataPath build 2>&1 | tail -20
```

Then `action: "launch"` with the built `.app` path and the bundle id.

### 3. Drive it yourself

Do not ask the user to test it. You test it, they watch.

- Complete the onboarding flow, tapping through every question.
- Confirm the paywall presents after the flow, and that it shows **real prices** (from
  `Products.storekit`) rather than blanks.
- Dismiss it and confirm the app is usable in free mode.
- Seed demo data, then run the core loop end to end.
- Hit at least one `feature_*` gate and confirm the right paywall appears.
- Visit every screen in the spec.

Screenshot each key screen as you go. Save under `screenshots/captured/` — Phase 9 reuses
these where they're good enough.

### 4. Fix what you find, then report

Bugs you hit are yours to fix now, not to report as findings. Rebuild and re-verify.

Then report honestly, in this shape:

> **`<AppName>` is running.** *(screenshots)*
>
> **Working:** onboarding flow → paywall, <core loop>, <feature>, free/pro gating.
> **Stubbed:** <anything not real, and why>.
> **Left out:** <what the spec deferred>.
> **Known rough:** <what you'd change with more time>.
>
> (Demo stop only:) What do you want changed before I make the store assets?

Never claim something works that you didn't exercise. If the paywall showed blank prices,
say so — don't let them find it in TestFlight.

### 4b. Conversion QA (every round)

- **First win**: from a fresh install, time it and count taps to the first win. It must be
  ≤ 60 s and ≤ 8 taps. If it isn't, cut or merge screens before anything else.
- **Funnel screenshots**: capture every onboarding + paywall screen in order and run the
  [conversion critique](prompts.md#7-conversion-critique) (a subagent with fresh eyes).
  Fix the top 3 findings per round.
- **Weakest screen**: one per round, improved with the chosen tools: `mobbin:redesign-screen` targeted (Mobbin), `get_screen` similars of its closest reference (Appllama), or the critique alone (web / none).
- **Day-2 check**: advance the simulator clock or trigger the scheduled notification; the
  deep link lands on the right screen and the home shows a next step.

### 5. Loop until clean

Unattended: rerun the full pass after every fix round, including a **fresh install of the
Release build**. Things only break there (dev-client permission keys, missing usage
strings, Superwall timing). Stop when one complete pass finds nothing. Commit each round
on `main` with a plain message.

Demo stop: apply the user's changes, re-QA, and continue to phase 9 without asking again.

Also exercise, when the module is ticked: every language (switch the simulator locale),
the ATT prompt, the AI-consent dialog, an offline launch (the native fallback paywall must
appear within 4 s), restore, and a sandbox/StoreKit purchase of **each** plan (the bought
product must match the selected one).

## Gotchas

- **Blank paywall prices** → `Products.storekit` isn't in the scheme's StoreKit
  configuration, or product ids don't match RevenueCat.
- **Flow never presents** → no campaign on `onboarding_start`; the presenter correctly fell
  back to native. Check `superwall campaigns list`.
- **Permission button does nothing** → `SuperwallActionHandler` missing that branch, or the
  `Info.plist` usage string is absent.
- **Onboarding never shows again after a skip** → the `phase != .fallback` guard is missing
  and the feature block marked it complete. See
  [onboarding-paywalls.md](onboarding-paywalls.md).
- **Empty screens in screenshots** → seed data didn't run. Fix before Phase 9; it's the
  single biggest conversion killer in the store listing.

## Status bar

Before capturing anything intended for the store, set a clean status bar:

```bash
xcrun simctl status_bar booted override --time "9:41" \
  --cellularBars 4 --wifiBars 3 --batteryState charged --batteryLevel 100
```
