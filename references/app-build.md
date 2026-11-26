# Building the app itself

> **Build order: the first win and the habit loop come first, everything else after.**
> Before writing any screen, run its row of the Mobbin [research matrix](mobbin-playbook.md)
> and write its [screen brief](prompts.md#2-screen-brief-one-per-funnel-screen). The
> retention mechanics in [conversion.md §4](conversion.md#4-retention-day-1-day-7-renewal)
> (progress memory, a next step on home, notifications tied to the plan, never-empty
> states, deep links) are part of v1, not polish.


This is the phase where the actual product gets written. The spec is the contract; build
what it says and nothing it doesn't.

## Order of work

1. **`Design/Theme.swift`** — the palette, type scale, spacing, and radii from
   `docs/DESIGN.md` as Swift constants. Everything else references these. No literal
   `Color(hex:)` outside this file, no `.padding(17)` anywhere.
2. **`Model/`** — the types from the spec's data model. Plain structs, `Codable`,
   `Identifiable`, `Sendable` where they cross actors.
3. **`Store/`** — `@Observable` classes owning state and persistence. One store per domain.
   This is where SwiftData/`UserDefaults`/file IO lives, never in a view.
4. **`Services/`** — anything talking outward: network, location, camera, the purchase
   controller.
5. **`Features/`** — the screens, one folder per area.
6. **`Features/Root/RootView.swift`** — the shell: tab bar or navigation stack, plus the
   onboarding gate.

Build and run after each of 1–6. A compile error found three layers later costs more than
the six builds.

## Conventions

- **SwiftUI + `@Observable`.** Not `ObservableObject`, not UIKit, not TCA. Deployment target
  is 17.0, so `@Observable` and `@Environment(Type.self)` are available.
- **`@MainActor`** on stores and services that touch UI state. Swift 6 concurrency checking
  is on; fix the warnings rather than suppressing them.
- **Views stay dumb.** A view reads state and sends intent. Any `if` more complex than a
  presentation choice belongs in the store.
- **One file per type**, named after it.
- **No placeholder content in shipped code.** No "TODO", no `Text("Coming soon")`, no
  `// implement later`. If it's in the spec, build it; if it isn't, don't stub it. A demo
  full of dead buttons fails the QA loop and wastes the user's time.

## Persistence

Default to **SwiftData** for anything list-shaped and user-owned. `UserDefaults` for flags
and small preferences only (`hasOnboarded`, unit choices). Files under Application Support
for images and blobs, never in `UserDefaults`, never in `Documents` unless the user is meant
to see them in Files.

If the spec calls for sync across devices or a server-side capability, that's Phase 8 —
build the local layer now with a clean seam so the backend can slot behind it.

## Empty states and seed data

Every list screen needs a designed empty state — it is the first thing a new user sees and
it is the thing that ruins App Store screenshots later.

Add a debug-only seeding path so the demo and screenshot phases have realistic content:

```swift
#if DEBUG
extension AppStore {
    func seedForDemo() { /* realistic, plausible, non-placeholder content */ }
}
#endif
```

"Realistic" means content a real user would have. Not `Item 1`, `Item 2`, `Test`. This one
detail is the difference between screenshots that convert and screenshots that look like a
tutorial.

## Accessibility

Not optional, and cheap if done inline: Dynamic Type support (no fixed-height text
containers), `accessibilityLabel` on every icon-only control, and a contrast check on the
palette. Apple review does look.

## Gating

Wire the free/pro table from the spec against `RCPurchaseController.isProActive` and
`Superwall.shared.register`. See [monetization.md](monetization.md) Step 5. Do this as you
build each feature, not as a pass at the end — retrofitting gates is how you end up with a
free tier that leaks.

## Definition of done for this phase

- Every screen in the spec exists and is reachable.
- The core loop can be completed end to end in the simulator.
- No placeholder strings, no dead controls.
- Debug seeding produces a screenshot-worthy state.
- `xcodebuild` clean, and warnings addressed rather than accumulated.
