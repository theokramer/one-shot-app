---
name: one-shot-app
description: Build a complete, monetized, shippable iOS app from one pitch, in one unattended run. The user explains the idea, ticks the modules they want (RevenueCat, Superwall onboarding + paywall, Cloudflare/Supabase backend, Meta Ads, TikTok Ads, localization, GitHub CI/CD…), picks how complete App Store Connect should be (screenshots, preview video, review video, offers, retention, custom product pages…), grants permissions once, does every sign-in up front, approves one plan, and walks away. Expo or SwiftUI. Use when the user wants to build a new app from scratch, says "build me an app", "one-shot", invokes /one-shot-app, or asks to repeat the one-shot setup for a new idea.
user-invocable: true
---

# One-Shot App

Pitch → tick boxes → connect everything → one plan → **walk away** → a finished app in App
Store Connect, waiting only for the user's "submit".

Before you start, read [references/learnings.md](references/learnings.md) for reusable
implementation guidance. Load only the saved preferences relevant to the current task;
do not dump the user's profile or personal learnings into chat or tool output.

## The contract with the user

The user is present for **two short blocks at the start**. After that they should be able
to leave.

```
 ATTENDED (~10–20 min)                          UNATTENDED (hours)
 ┌──────────────────────────────────────────┐
 │ 0 Library        load what's known       │   ┌───────────────────────────────────────┐
 │ 1 Pitch          what do you want?       │   │ 6 Build app + self-QA loop            │
 │ 2 Menu           tick modules + store    │   │ 7 Monetization, onboarding, paywalls  │
 │                  depth + permissions     │   │ 8 Backend, ads SDKs, localization     │
 │ 3 Questions      only what can't be      │──▶│ 9 Store assets, ASC fill, site        │
 │                  inferred                │   │10 Upload build, attach, final audit   │
 │ 4 Connect        every CLI/MCP/login/    │   │11 Final report + the user's to-do     │
 │                  Chrome sign-in, proved  │   └───────────────────────────────────────┘
 │ 5 Plan           one approval: "Go"      │
 └──────────────────────────────────────────┘
```

**After "Go", never ask a question.** If a decision comes up, decide it, and write it into
`docs/DECISIONS.md`. If something truly needs the user (a password, a token paste, a payment
detail, a click Apple only allows a human to make), do not stop. Do everything else, and
put that item on the final to-do list. A run that stops at hour two because it needs a
2FA code has failed. That is why phase 4 exists.

## Phase map

| # | Phase | Mode | Reference |
|---|---|---|---|
| 0 | First-run setup if needed (`setup.py status`), else load the library silently | ⏸ first run only | [intake.md](references/intake.md#0-first-run-setup-and-the-library) |
| 1 | Pitch: "What app do you want to build?" | ⏸ | [intake.md](references/intake.md) |
| 2 | Menu: modules, store depth, permissions (`AskUserQuestion`, multi-select) | ⏸ | [intake.md](references/intake.md), [modules.md](references/modules.md) |
| 3 | Follow-up questions: name, stack, pricing, free vs Pro | ⏸ | [intake.md](references/intake.md) |
| 4 | **Connect**: install, log in, prove every credential, do all Chrome work that needs the user | ⏸ **hard gate** | [connect.md](references/connect.md) |
| 5 | Plan: `docs/PLAN.md` and a short summary, one approval | ⏸ **last question** | [intake.md](references/intake.md) |
| 6 | Research matrix (with the chosen research tools), then scaffold + build the app (first win + retention loop first), then an autonomous QA loop | ▶ | [research-sources.md](references/research-sources.md) · [mobbin-playbook.md](references/mobbin-playbook.md) · [prompts.md](references/prompts.md) · [scaffold.md](references/scaffold.md) (SwiftUI) · [expo.md](references/expo.md) (Expo) · [app-build.md](references/app-build.md) · [demo.md](references/demo.md) |
| 7 | Monetization + high-converting onboarding + multi-page paywalls (if ticked) | ▶ | [conversion.md](references/conversion.md) · [monetization.md](references/monetization.md) · [onboarding-paywalls.md](references/onboarding-paywalls.md) |
| 8 | Backend · ads attribution · localization (if ticked) | ▶ | [backend.md](references/backend.md) · [ads-attribution.md](references/ads-attribution.md) |
| 9 | Store assets (conversion-ordered) + App Store Connect to the chosen depth + website | ▶ | [conversion.md](references/conversion.md#5-the-app-store-page-that-converts) · [launch-assets.md](references/launch-assets.md) · [app-store-connect.md](references/app-store-connect.md) |
| 10 | CI/CD (if ticked), upload, attach build, full review audit + conversion critique | ▶ | [cicd.md](references/cicd.md) · [app-store-connect.md](references/app-store-connect.md) |
| 11 | Final report, to-do list, `LEARNINGS.md`, hand off to the PR loop | ⏸ | [pr-mode.md](references/pr-mode.md) |

Track phases with `mcp__ccd_turn__update_plan` (or TaskCreate outside the desktop app), one
step per phase, so the user can glance at progress from their phone.

## Rules that shape everything

**1. Everything that needs the user happens before "Go".** Logins, `rc setup apple` (Apple
2FA), Chrome sign-ins, creating ad accounts, token pastes, agreeing to terms. Phase 4 has
the full list. Chrome work that *doesn't* need the user (App Privacy answers, Asset Library
uploads, compliance forms) runs later, unattended, using the sign-ins made in phase 4.
Before "Go", check that each of those sites is actually signed in.

**2. CLI and MCP first, Chrome last.** Order of preference: the project's CLI (`rc`,
`superwall`, `superwall asc`, `wrangler`, `gh`, `fastlane`, `xcrun`), then the App Store
Connect API (`assets/scripts/asc.py`), then an MCP server (Mobbin, Appllama, Supabase), then Claude in
Chrome. Only use Chrome when there is no API: App Privacy, Asset Library
header/search art, compliance forms, Meta/TikTok dashboards, Resolution Center. When a tool
is missing, say exactly what to install (phase 4 prints it). Don't silently fall back to
Chrome.

**2b. Any tools, or none.** Research (Mobbin, Appllama, web, none), design skills, image
and video generation (Gemini, Sunra, local, none) and music (ACE-Step, silent, own track) are
picked in menu round T and saved in the library. Every step has an equivalent for each
choice ([research-sources.md](references/research-sources.md)). Never assume a plugin is
there, and never fail because one isn't.

**3. Permission is asked once, up front, item by item.** The menu has a permissions
question. What the user ticks there is the standing approval for this run, and nothing
more. Anything not ticked goes on the to-do list; don't ask about it mid-run. Some things
are never covered, whatever is ticked: typing passwords, 2FA codes, API tokens or payment
details into a website; approving Claude's own permission prompts; submitting for App
Review; spending beyond the cap the user named. Say this plainly in the menu, so nobody
expects a run that can't happen.

**4. Writing to `main` is fine for the first run.** No branches, no PRs. The user wants to
sit down to a finished app, not review fourteen PRs. After phase 11 this inverts
permanently ([pr-mode.md](references/pr-mode.md)).

**5. The build stays green, and the app is tested by you, not by the user.** Compile after
every phase, then drive the real app in your **own** named simulator (`<App> QA`). Never use
the shared iPhone 17 simulator, because other sessions use it. Fix what you find. The demo
becomes a self-QA loop unless the user ticked "Stop for a demo" in the menu.

**6. Money is a hard line.** Generation APIs (Gemini image/video, Sunra, ElevenLabs) cost
real money. Stay within the spend cap from the menu. Default to $0 extra: local renders,
Blender, free CC0 assets. Never buy, never enter payment details, and never launch ads.

**7. Never ask twice: the library.** `profile.json` (via `assets/scripts/profile.py`)
remembers the user: identity, imprint data, review contact, ad-account IDs, last run's menu
answers, standing preferences, and every shipped app. Start with the redacted `summary`
and `missing` commands. Local scripts should read contact details and credentials directly
for their intended destination without printing them. Load only relevant preferences into
the assistant context, and save only information needed for future runs.

**8. Conversion is the product.** The funnel (store page → first win → onboarding →
paywall → day 1/day 7) gets more care than any feature. Every funnel screen is researched
with the research tools picked in menu round T
([research-sources.md](references/research-sources.md); Mobbin specifics in
[mobbin-playbook.md](references/mobbin-playbook.md)), briefed with a
written brief ([prompts.md](references/prompts.md)), built, screenshotted, critiqued and
improved. The rules and benchmarks are in [conversion.md](references/conversion.md). The
first win is reached in **≤ 60 s and ≤ 8 taps, inside onboarding**, and QA measures it.

**9. Never submit for App Review.** Get everything to "Ready for Review", then stop. The
final message asks once.

## Non-negotiables (architecture)

- **RevenueCat owns entitlements. Superwall owns presentation.** Superwall never transacts.
  Every purchase goes through a purchase controller (`RCPurchaseController` in Swift,
  `CustomPurchaseControllerProvider` in Expo).
- **Onboarding flow and paywall are separate**, with separate placements, so either can
  show alone or chained.
- **Every placement has a native fallback.** If Superwall hasn't presented within 4 s
  (offline, no campaign, error), show the native onboarding or paywall. Without the paywall
  fallback, free equals Pro.
- **Experiments ship in v1**: every tested price is its own product in the same
  subscription group, all attached to `pro`. The **retention price** (e.g. $9.99/yr) only
  ever appears to people who are leaving (cancel, decline, lapsed), and once per user.
- **Attach products to the entitlement.** Otherwise a purchase completes and Pro stays off.
- **No secrets in the binary.** Only public SDK keys go in the app. Provider keys live in
  Cloudflare/Supabase secrets or GitHub secrets. The `.p8` and `config.json` are never
  printed and never committed.
- **RevenueCat is driven with the `rc` CLI**, always with `--project-id`. Never change the
  default project, and never use the RevenueCat MCP or a browser for it.
- **Every app website has Support, Privacy, Terms and an Imprint (Impressum)**, rendered
  from the library's real data, never placeholders. The app's Settings links to all four.
- **Store art is built from real captures.** No AI-drawn UI, no AI backgrounds by default,
  phones fully visible or deliberately cropped, never cut off at the bottom.
- **The paywall shows** price, period, trial terms, auto-renew text, Restore, Terms and
  Privacy, and buys the plan that is selected (Guideline 2.1(b)).
- **Permission priming screens say "Continue"** and always lead to the system prompt. No
  "Not now" (Guideline 5.1.1(iv)).
- **Name the AI provider in an explicit consent before sending data to it** (Guideline
  5.1.2(i)).
- **The App Privacy answers match the code, the SDKs, the privacy policy and the privacy
  manifest exactly** (Guideline 5.1.2).

## Where things live

- **Keep personal data outside the skill and generated repositories.** Each user's data
  belongs in their data home `~/.one-shot-app/` (override with `ONE_SHOT_HOME`; see
  `assets/scripts/paths.py`):
  - `config.json`: secrets and account keys (template: `config.example.json`). Read it in
    local scripts, never print it, never ask for anything already in it.
  - `profile.json`: the library, with the user's non-secret data and history (template:
    `profile.example.json`, managed by `assets/scripts/profile.py`). The imprint fields are
    published on approved app websites; review contact goes to App Store Connect. Values
    printed by tools or included in chat become part of the assistant context. Other
    account data is sent only to the services needed for the authorized task.
  - `learnings.md`: personal learnings; read only task-relevant portions, append in phase 11.
  - None of these is ever copied into a repo or into the skill folder.
- Before publishing, run `assets/scripts/package.py scan` and separately `scan --history`
  for Git history. These are heuristic checks, not a guarantee. Review text and media too.
- Keep App Review contact exports outside repositories, or in an ignored
  `review_information/` directory. Verify they are not tracked before committing. Confirm
  which imprint fields will be public during intake, before the existing plan approval.
- `assets/scripts/setup.py` handles first-run setup (`status`, `detect`, `set`, and
  `secret` for hidden input in the user's own terminal).
- `assets/scripts/preflight.py --modules …` is the phase-4 gate.
- `assets/scripts/asc.py` is an App Store Connect API client and the uploaders (preview
  video, review attachment, build attach).
- `assets/expo/` holds Expo templates (Monetise bridge, ads attribution, release script).
- `assets/swift/` holds SwiftUI templates (RC purchase controller, paywall gate, onboarding
  presenter).
- Every generated repo gets `LEARNINGS.md`, `docs/SPEC.md`, `docs/DESIGN.md`,
  `docs/PLAN.md`, `docs/DECISIONS.md`, `store/` (metadata, privacy answers, review notes,
  `POST_LAUNCH.md`), and a `CLAUDE.md` with the PR-loop rule.
