# Mobbin playbook: research every funnel screen before building it

Mobbin is the main design input for this skill. Use it **heavily**, but in the way it works
best: Mobbin answers **one screen, flow or section per query**. "Design my whole app" is too
broad for it, so the skill breaks the app into a research matrix and runs it.

Before the first search in a run: invoke `mobbin:best-practices`, then `mobbin:search`
(their rules win wherever they differ from this file). If the Mobbin tools aren't in the
session or a call is refused, say so in one line, and fall back to Appllama
(`appllama-usage`) for screens. Never design "from memory of Mobbin".

## Call settings (same for the whole run)

- `platform: "ios"`, `output_destination: "code"`, `output_tool`: omit
- `task_intent`: one fixed English sentence for the whole run, e.g.
  "Build a high-converting subscription iOS app for <domain>". No personal data.
- `search_screens` `mode`: `standard` for a bare type, `deep` for 1–3 constraints
- More results: the same query with `exclude_screen_ids` (screens) or the next `page`
  (flows/sections). Weak results → reword the query, never just raise `limit`

## The research matrix (phase 5–7)

Write `docs/RESEARCH.md` with one row per target, run the queries, **look at every image**,
and record 3–6 references per target (app name + `mobbin_url` + the one decision worth
taking). Queries follow Mobbin's rules: the target type first, the domain noun, at most 3
constraints, no taste words, no "best".

| Target | Tool | Query recipes (pick 1–2, swap in the domain) |
|---|---|---|
| Whole onboarding journey | `search_flows` | "<domain> app onboarding" · "onboarding questionnaire" · "Duolingo onboarding" (named apps for structure) |
| Welcome screen | `search_screens` | "<domain> app welcome screen" |
| Question step | `search_screens` deep | "onboarding question with multiple choice" · "onboarding goal selection" |
| First win inside onboarding | `search_flows` | "<domain> first use during onboarding" · "trying the core feature during onboarding" |
| Plan / results screen | `search_screens` deep | "personalized plan summary" · "onboarding results with a progress chart" |
| Commitment | `search_screens` | "commitment pledge screen" |
| Permission priming | `search_screens` deep | "notification permission priming" · "tracking permission explanation" |
| Paywall (onboarding) | `search_flows` + `search_screens` deep | flow: "multi-step paywall during onboarding"; screen: "paywall with a free trial timeline" · "paywall with plan cards and a free trial button" · "<domain> app paywall" |
| Feature-gate paywall | `search_screens` deep | "paywall for a locked feature" |
| Exit / discount offer | `search_screens` deep | "discount offer after closing paywall" |
| Post-purchase | `search_screens` | "subscription purchase confirmation" |
| Home / core loop | `search_screens` | "<domain> app home screen" · "<domain> home with no data" (empty state) |
| Progress / streak | `search_screens` deep | "streak and progress screen" · "weekly progress chart" |
| Share the win | `search_flows` | "sharing a result to social media" |
| Notifications settings, cancel flow | `search_flows` | "cancel subscription flow" · "notification preferences" |
| Rate prompt timing | `search_flows` | "app rating request after completing a task" |
| App Store page (marketing) | `search_sections` (web) + Appllama listings | "app download hero" · "app feature grid"; Appllama for the top apps' store screenshots |

Do the whole onboarding flow and the paywall first: they carry the conversion.

## Turning references into design (not copies)

1. **Group** each target's references by the direction they take (e.g. paywall: "plan
   cards + timeline" vs "single CTA + toggle"). Build each screen from **one direction
   whole**, never a mix of two.
2. **Precedent = 2+ products** doing the same thing; one product is just an example. Prefer
   precedent for conversion-critical decisions (paywall layout, CTA placement, progress bar).
3. **Take decisions, not looks**: structure, order, what's on screen, CTA wording pattern.
   The look comes from `docs/DESIGN.md` (the app's own system). Never copy another app's
   brand, copy or illustrations. Mobbin is for seeing how many products solve a problem.
4. Write the decision into `docs/DESIGN.md` → "Patterns", with the `mobbin_url`s that back
   it. The final report cites them ("onboarding modelled on Duolingo, Calm and Flo flows").

## Variations and polish

- For the onboarding paywall and the welcome screen, use `mobbin:redesign-screen` in
  **explore** mode on the built screen. Up to three variations, one per direction, as
  before/after boards. Pick one yourself (unattended) and ship it; put the boards in the
  final report. Ship the other variations as Superwall campaign variants when "Superwall" is
  ticked, so the A/B test is ready.
- After building any funnel screen, take a simulator screenshot and run
  `mobbin:redesign-screen` in **targeted** mode on the weakest screen of the funnel
  (one per QA round). Its report goes into `docs/DECISIONS.md`.

## Collections (only with the user's OK)

`save_content` / `create_collection` are only for when the user wants references kept. The
library records the answer (`profile.py get preferences` → "Save Mobbin references to a
collection per app: yes/no"). If no answer is recorded, add it as a yes/no question to the
missing-library-data card in intake step 3 (it's asked once, ever), then save it with
`profile.py add-pref`. With "yes": one private
collection per app, named "<App>: funnel references", holding the locked references per
target. Its link goes in the final report.

## What the user reads

Mobbin's own evidence rules apply to every claim in reports and `DESIGN.md`: name the
products and link the screens; no "most apps", "research shows" or "best-in-class"; no
promise that a screen *will* convert. Conversion data from RevenueCat/Superwall is cited
as theirs, in [conversion.md](conversion.md), not as Mobbin's.
