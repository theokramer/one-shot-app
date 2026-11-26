# Conversion, retention and fast wins

The product isn't the app. It's the funnel: **store page → install → first win →
onboarding → paywall → day 1 → day 7 → renewal.** Every phase of the run builds one piece
of it, and every piece is researched on Mobbin first ([mobbin-playbook.md](mobbin-playbook.md))
and briefed with the prompts in [prompts.md](prompts.md).

The numbers below come from vendor data (RevenueCat, Superwall), so treat them as
direction, not law. They explain *why* the rules exist.

| Fact | Source | Consequence for the build |
|---|---|---|
| ~82 % of trial starts happen on install day; most within the first minutes | RevenueCat SOSA 2025, "Fix your funnel" (Nov 2025) | The first session is the business. Onboarding + paywall get the most care of anything in the app |
| Hard paywall: median trial→paid ~10.7 % vs ~2.1 % freemium; 1-year retention about equal (27 % vs 28 %) | RevenueCat SOSA 2026 | The user's "hard nudge" taste is backed by data: gate the core value, keep a taste free |
| Multi-page onboarding paywalls 12.4 % vs single-page 9.1 % (observational, 40M opens) | Superwall blog, May 2026 | Paywall = 2–3 screens: value → what happens (trial timeline) → plans |
| Paywall moved earlier + a 3-screen context carousel: 2 % → 8 % → 15 % trial opt-in (one test) | RevenueCat, "How top apps approach paywalls" | Never bury the paywall after the app; give it context screens right before |
| An honest trial timeline + reminder: +23 % conversion, −55 % complaints (Blinkist) | same | Show "Today / Day 2 reminder / Day 3 billed" on the trial paywall |
| 20–30 % of trial users cancel in the first 3 hours | same | Post-purchase aftercare plus an immediate first win after paying |
| A commitment screen ("I commit to …", hold-to-commit) doubled D30 retention in one case | RevenueCat, "Fix your funnel" | Put a commitment step before the paywall |
| Faster time-to-first-value → higher D1; a D1→D7 cliff signals first-run problems | CleverTap, Appcues | Design the first session around **one** win, reached in under 60 s |

---

## 1. Fast wins: designing the first 60 seconds

Before any screen is built, write into `docs/SPEC.md`:

- **The first win**: the one moment the user feels the value (a home-design app: their own
  floor plan turned 3D; a fitness coach: their squat form scored). One sentence.
- **Time-to-first-win budget**: ≤ 60 s and ≤ 8 taps from first launch, **inside
  onboarding**, before the paywall. QA measures both (see [demo.md](demo.md)).
- **What's faked vs real** in that win: it must be real. Use sample data only if the user's
  own input isn't possible yet (and then switch to theirs the moment it is).

Rules:
1. **Value before commitment.** No account and no permission before the first win, unless
   the win itself needs it (camera for a scan). Then prime it with "Continue".
2. **Defaults over choices.** Pre-select the most common answer; one decision per screen.
3. **The win is shareable.** The viral moment exports as a clip or image with the app's
   mark, in one tap.
4. **After the paywall, land on action, not a home screen**: "Add your first room" /
   "Film your next set". Purchase aftercare: confirm what's unlocked, then go.

## 2. Onboarding that converts

Structure (adapt the count; each screen has one job):

| # | Screen | Job | Mobbin query (see playbook) |
|---|---|---|---|
| 1 | Welcome | promise + proof (a real render or clip), one CTA | "<domain> app welcome screen" |
| 2–4 | Questionnaire | goal, pain, level/preferences. Self-identification makes the plan personal | "onboarding question with multiple choice" (`search_flows`: "<domain> onboarding questionnaire") |
| 5 | Social proof / mechanism | *how* it works, not testimonials you don't have. Never fake reviews or numbers | "onboarding screen explaining how it works" |
| 6 | **First win, live** | the user does the core action now | flow: "<domain> first use during onboarding" |
| 7 | Personal plan | answers → a concrete outcome with a date ("From 12 to 20 clean reps by Mar 3"), a chart | "personalized plan summary screen" |
| 8 | Commitment | "I commit to …" / hold-to-commit | "commitment pledge screen" |
| 9 | Permissions | notifications (tied to *their* plan), ATT last; one "Continue" button each | "notification permission priming screen" |
| 10–12 | Paywall (multi-page) | value recap → trial timeline → plans | see §3 |
| 13 | Post-purchase | what's unlocked → straight into action | "subscription purchase confirmation screen" |

Copy rules: outcomes, not features; the user's words from the questionnaire played back;
no brand jargon; a progress bar; back always allowed except on one-way doors (after
purchase). The `app-onboarding-questionnaire` skill drafts the question set; Mobbin decides
the patterns.

## 3. Paywalls that convert (and pass review)

- **Multi-page in onboarding**: (a) what you get, as 3–4 outcome bullets with icons, using
  their answers; (b) the honest trial timeline; (c) plans.
- **Plans**: lead with yearly, selected by default, badge "Most popular" (not "cheapest");
  weekly as the second choice; at most 2–3 options. Show the **total** price prominently
  (a per-week breakdown may appear only next to the real total, or App Review can reject
  it), trial terms, auto-renew text, Restore, Terms, Privacy.
- **Trial**: a toggle or a trial-labelled CTA ("Start my 3-day free trial"), reminder
  promise, and a schedule for the reminder notification.
- **Feature-gate paywalls** (`feature_*`) name the feature tapped in the headline.
- **Exit offer** (if "Retention & discounts" is ticked): on decline/abandon, a discounted
  plan once, never more often.
- **Dark-mode paywall** variant for young audiences; test it via the Superwall campaign
  split, not by guessing.
- Track paywall views, view→trial, trial→paid and refunds per placement (Superwall +
  RevenueCat charts), and report them in `POST_LAUNCH.md` as the first things to watch.

## 4. Retention: day 1, day 7, renewal

Build these into v1 (they're cheap and they compound):

| Mechanic | Rule |
|---|---|
| Habit loop | one daily action under 2 min, visible progress (streak, chart, before/after), a next step always on the home screen |
| Notifications | opt-in tied to their plan; at the time they chose; content that's *theirs* ("Waves are good at your spot tomorrow 7am"). Max 1/day. Local first |
| Progress memory | history of their wins (rooms, reps, scores) as a gallery: the reason not to delete the app |
| Empty states | never empty: a sample plus "do your first …" |
| Re-entry | deep links from notifications to the exact screen; widgets / Live Activities where natural |
| Trial users | day-1 "here's what you can do next" nudge; trial-ending reminder (promised on the paywall) |
| Cancel flow | RC Customer Center: ask why → offer a fix or a promo offer → cancel stays easy |
| Win-back | ASC win-back offer + Superwall `paywall_winback` for lapsed subscribers |

## 5. The App Store page that converts

- **Name + subtitle** = keyword + benefit ("FormCoach: Squat Tracker").
- **Screenshot 1–3 carry the page**: slide 1 = the first win / viral moment with a
  benefit headline; 2 = how it works; 3 = the personal result; then features; last =
  proof or the habit. Headlines are outcomes, 2–5 words, readable at thumbnail size.
- **Preview video** (autoplays, muted): the win in the first 3 s, captions carry the story,
  the real app only.
- Research the category's top pages on Mobbin and Appllama before writing a headline
  ([mobbin-playbook.md](mobbin-playbook.md#app-store-page)). Make 3 variations (custom
  product pages now, Product Page Optimization after launch).
- Description: first 3 lines = promise + what's free/Pro + trial terms.
- Rate prompt (`SKStoreReviewController` / `expo-store-review`) **only right after a win**
  (third successful core action), never on launch and never after a paywall.

## 6. The conversion review (phase 10, before the final report)

Run the [conversion critique prompt](prompts.md#conversion-critique) against the real
screenshots of every funnel screen, fix the top findings, and put the before/after in the
final report. Also report: first win time and taps, onboarding screen count, paywall pages,
and which Mobbin flows each step was modelled on.

Sources: [RevenueCat SOSA 2026](https://www.revenuecat.com/state-of-subscription-apps-2026/),
[RevenueCat benchmarks 2026](https://revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026),
[RevenueCat: fix onboarding funnels](https://www.revenuecat.com/blog/growth/fix-onboarding-funnels),
[RevenueCat: how top apps approach paywalls](https://www.revenuecat.com/blog/growth/how-top-apps-approach-paywalls),
[Superwall: multi-page paywalls](https://www.superwall.com/blog/new-postmulti-page-onboarding-paywalls-convert-37-better-than-single-page-heres-why),
[CleverTap: retention](https://clevertap.com/blog/mobile-app-retention/),
[Apple: asset best practices](https://developer.apple.com/app-store/asset-best-practices/).
