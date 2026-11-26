# Onboarding flow and paywalls: built separately, composed at runtime

## What a high-converting onboarding looked like in practice

The full structure, paywall pages and copy rules are in [conversion.md](conversion.md) §2–3,
the research queries in [mobbin-playbook.md](mobbin-playbook.md), and the briefs in
[prompts.md](prompts.md). Onboarding paywalls are **multi-page** (value → trial timeline →
plans), and the campaign ships with variants A/B(/C) ready to test.

Research first: `mobbin:search` (flows: "onboarding questionnaire", "paywall", "permission
priming" in the same category as the app) and the `app-onboarding-questionnaire` skill.
Then the shape that worked in shipped apps:

1. Welcome: the promise plus 3 benefits, with a real render or clip from the app
2. Goal → pain ("what's held you back") → personal choices (style, level, room…)
3. **The benefit, felt**: the user tries the core feature inside onboarding (a fitness coach: a
   real squat test with a form score; a home-design app: "now shake it" on their 3D model). This beats any
   claim.
4. Answers turned into a plan ("From 12 to 20 clean reps by <date>"), with the plan screen's
   button "Commit to my plan" → paywall
5. Permission priming (location, notifications, ATT) with a single **"Continue"** button.
   ATT comes last, right before the paywall.
6. Paywall (`onboarding_paywall`), then straight into the first real action

Never: fake reviews, invented statistics, a trial-reminder screen before the paywall, or
a "Not now" on priming screens.


## The requirement

The onboarding flow and the paywall are **two independent Superwall entities**. Not one
paywall with question screens glued to the front. This is what lets you:

- show the flow alone (first launch, no pricing yet)
- show a paywall alone (a feature gate mid-session)
- chain flow → paywall (the classic questionnaire-to-offer funnel)
- swap which paywall a given flow ends on, per audience, without shipping a build
- A/B two paywalls behind one placement

If the paywall is embedded inside the flow, every one of those becomes a code change. Keep
them separate.

## Placement matrix

Placements are the app's *vocabulary*; campaigns decide what each one shows. Register
these from Swift, then wire campaigns to them in the dashboard.

| Placement | Fired when | Normally presents |
|---|---|---|
| `onboarding_start` | First launch, before the main UI | The **Flow** — questions, value props, permission asks |
| `onboarding_paywall` | Flow completes | A paywall tuned for a warm, just-onboarded user |
| `paywall_generic` | Generic "upgrade" tap (settings, banner) | The standard paywall |
| `feature_<name>` | A specific gated capability is used | A paywall whose copy names that feature |
| `paywall_winback` | A lapsed subscriber returns | A discounted offer |

Name them in `snake_case` and keep them stable — a renamed placement is a broken campaign.
Declare them once as constants so no string is typed twice:

```swift
enum Placement {
    static let onboardingStart   = "onboarding_start"
    static let onboardingPaywall = "onboarding_paywall"
    static let generic           = "paywall_generic"
    static func feature(_ name: String) -> String { "feature_\(name)" }
}
```

Use the `superwall-placements` skill when deciding *where* in the app the feature gates
belong — it audits the codebase for the right moments rather than sprinkling them.

## Composition — the three modes

All three come from one Swift call site. What differs is dashboard configuration.

**Flow only** — campaign on `onboarding_start` presents a Flow whose last screen is a
"Get started" button. `onboarding_paywall` has no campaign, so it skips, and the register
feature block runs immediately.

**Paywall only** — `onboarding_start` has no campaign (or the user is a holdout), so it
skips straight through; `onboarding_paywall` presents.

**Flow then paywall** — both have campaigns. The flow's terminal button dismisses, the app
fires `onboarding_paywall`, the paywall presents. Because they're separate entities, the
flow's answers are available as Superwall user attributes and can *select* which paywall
variant appears:

```swift
Superwall.shared.setUserAttributes([
    "goal": selectedGoal,
    "experience_level": level
])
```

Then in the dashboard, add audience rules on `onboarding_paywall` filtering on
`user.goal == "…"` so different answers land on different paywalls. This is the whole
point of the separation — use it.

## Building the flow and the paywalls

Superwall paywalls cannot be created from the CLI — `superwall paywalls create` answers
`create is not supported for paywalls yet`, and the editor needs a browser session with a
pairing code. An autonomous run therefore builds **both native paths first**, and treats
Superwall-designed screens as an upgrade:

| Piece | Built by the run | Superwall equivalent |
|---|---|---|
| Onboarding questions | `OnboardingView` (native, always runs) | a Flow on `onboarding_start` |
| Paywall | `NativePaywallView` via `PaywallGate` | a paywall assigned to the campaign |

Copy `assets/swift/PaywallGate.swift` and `assets/swift/NativePaywallView.swift` into
`Features/Paywall/`, attach `.paywallGate()` at the root, and route every gate through
`PaywallGate.shared.present(_:onEntitled:)`. Fill `PaywallCopy.current` from the spec's
free/pro table and the Phase 9 terms/privacy URLs.

The native paywall pulls prices, periods and trial lengths from the RevenueCat offering, so
it can never disagree with what the customer is charged, and it carries everything guideline
3.1.2 demands on one screen. Pull the palette and type from `Design/Theme.swift` so it
doesn't look like it came from a different app.

For Superwall-authored screens (better paywalls, real A/B testing), these skills help.
The paywall itself is written as code and published from the CLI (see
[monetization.md](monetization.md), step 4); the editor is only for later hand-tuning:

- **`superwall-editor`** — attaches to a live browser editor session by pairing code.
- **`superwall-dashboard`** — campaigns, audience rules, paywall assignment.
- **`app-onboarding-questionnaire`** — designs the question sequence itself, encoding
  conversion patterns from high-performing subscription apps.

The run never stops for a pairing code. Code-first publish plus the native fallback cover it.

## The Swift presenter, with a native fallback

Copy `assets/swift/OnboardingPresenter.swift`. The shape that matters:

```swift
let handler = PaywallPresentationHandler()
handler.onSkip  { [weak self] _ in Task { @MainActor in self?.phase = .fallback } }
handler.onError { [weak self] _ in Task { @MainActor in self?.phase = .fallback } }

Superwall.shared.register(placement: Placement.onboardingStart, handler: handler) { [weak self] in
    Task { @MainActor in
        guard let self, self.phase != .fallback else { return }
        self.phase = .done
        store.hasOnboarded = true
    }
}
```

Three things are easy to get wrong here:

1. **The feature block fires on skip too.** A skipped placement (no campaign, holdout,
   offline) still runs the block. Without the `phase != .fallback` guard you mark onboarding
   complete for a user who never saw it, and they never see it again.
2. **A native fallback must exist.** Ship a plain SwiftUI `OnboardingView` covering the same
   ground. A user whose first launch is offline must still reach the app. Both paths must
   converge on the same completion state.
3. **`phase` starts `.idle` and `start()` guards on it** so a re-render doesn't present
   twice.

## Permissions inside the flow

Permission screens live in the Superwall flow, but only the app can show a native prompt.
That bridge is `SuperwallActionHandler` — see [monetization.md](monetization.md) Step 4. If
you put a permission screen in the flow, verify the corresponding branch exists in the
handler and that the `Info.plist` usage string is present. All three or none.

## Verification

Before leaving this phase:

```bash
superwall campaigns list
superwall paywalls list
superwall doctor
```

Then in the simulator: fresh install → flow presents → complete it → paywall presents →
close it → app is usable in free mode. Then delete the app, turn on airplane mode, install
again → native fallback presents. That second test is the one everybody skips and it is the
one that catches a broken first launch.
