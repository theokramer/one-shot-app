# Prompt library: briefs that produce beautiful, high-converting screens

These are the briefs the run writes for itself (and for any subagent) before building a
funnel screen. They follow the prompting practices that reliably move model output away
from generic UI:

- **Name the failure mode and the defaults to avoid**, explicitly. Without that, a model
  settles on the most common patterns in its training data (Anthropic, *Prompting for
  frontend aesthetics*).
- **Steer one dimension at a time**: typography, colour/theme, motion, backgrounds/depth.
- **Lock a theme** in one tagged block and reuse it verbatim for every screen, so screen 9
  looks like screen 1.
- **Commit before coding**: state the chosen font, palette and pattern, then build.
- **Give the why and the evidence**: the screen's job, the user's state at that moment,
  and the references (Mobbin/Appllama/web links) the decision comes from. With "No research", say "built-in pattern".
- **One screen per brief.** Then screenshot it, critique it against written criteria, and
  iterate. Judging the render beats judging the code.
- **XML tags** separate context, references, constraints and the output contract.
- Write the brief **into the repo** (`docs/briefs/<screen>.md`), so a later round or a
  subagent starts from the same text.

---

## 1. `<design_direction>`: written once into DESIGN.md, pasted into every screen brief

```xml
<design_direction app="<App>">
  Failure mode to avoid: "AI-generated app" look. Generic iOS-blue buttons, purple/blue
  gradients on white, glassmorphism everywhere, emoji as icons, evenly spread timid colour,
  centred-everything stacks, stock illustrations, identical card grids, Inter/Roboto/Poppins.
  Typography: <display face> for headlines (weight 800–900, sizes ≥ 3× body), SF Pro /
  system for body and controls. Tabular numbers for scores, prices and timers.
  Colour: <dominant> + one sharp accent <hex>; ink/paper tokens; dark mode designed, not
  inverted. Colour means something (accent = the action or the win), not decoration.
  Depth & background: <e.g. real renders on soft paper, layered gradients from the brand
  hue, grain>; never flat grey placeholders.
  Motion: one orchestrated entrance per screen (staggered rise, 40–60 ms steps), springs on
  touch, haptics on the win and on purchase. Nothing loops for no reason.
  Imagery: real app renders/captures or licensed 3D (Blender, CC0). No AI people.
  Native feel: HIG navigation, sheets, safe areas, 44 pt targets, Dynamic Type survives.
  Mascot: <name + mood per screen from MASCOT.md, ≤ 25 % of the screen, never near the
  price or CTA> (or "none").
</design_direction>
```

Pick the specifics from the app's domain and the references, vary them between apps
(light vs dark, serif vs grotesk), and record them in `DESIGN.md`. The
The chosen design skill (e.g. `appllama-app-design-skill`) sets the quality bar; this block makes it concrete.

## 2. Screen brief (one per funnel screen)

```xml
<screen_brief id="onboarding_07_plan">
  <job>Turn the user's answers into a concrete promise they want to pay for.</job>
  <user_state>Just finished the live squat test (form score 81). Motivated, curious, 90 s in.</user_state>
  <must_show>Their goal in their words · a dated outcome · a chart from today to goal · one CTA</must_show>
  <references>
    <ref app="Flo" url="<ref link>">dated outcome headline above the chart</ref>
    <ref app="Duolingo" url="<ref link>">progress curve with a marked "you are here"</ref>
  </references>
  <direction>Pattern group A ("dated promise + curve"). Do not mix in group B.</direction>
  <design_direction>…paste block 1…</design_direction>
  <copy_rules>Outcome, not features. Second person. ≤ 8 words headline. No invented stats.</copy_rules>
  <states>loading (≤ 1.2 s, animated build-up) · error → retry</states>
  <acceptance>
    Readable in 3 s · one primary action · matches screens 1–6 visually ·
    localized strings keyed · VoiceOver labels · works on SE size
  </acceptance>
  <output>Code for this screen only, then a simulator screenshot for critique.</output>
</screen_brief>
```

## 3. Onboarding copy brief

```xml
<onboarding_copy app="<App>" audience="<who>" first_win="<one sentence>">
  For each screen give: headline (≤ 8 words), sub (≤ 14 words), CTA (≤ 3 words).
  Voice: <confident coach / warm designer / …>. Use the user's answers as variables.
  Play back what they told us. Never: fake testimonials, numbers we can't prove, "AI-powered".
  Write en and de together (de whole sentences, natural, not word-for-word).
</onboarding_copy>
```

## 4. Paywall brief

```xml
<paywall_brief placement="onboarding_paywall" pages="3">
  page 1, value: 3–4 outcome bullets built from the answers (icons, no feature jargon)
  page 2, trust: trial timeline Today · Day <n-1> reminder · Day <n> billed; "Cancel anytime in Settings"
  page 3, plans: yearly preselected + "Most popular", weekly second; total price large,
          per-week only beside the total; CTA names the trial; Restore · Terms · Privacy
  Legal line updates with the selected plan. Close (×) visible after 2 s, never hidden.
  Variants: as many designs and prices as docs/RUN.md says (paywallVariants × priceTests,
  ≤ 4 variants), e.g. A = this at $39.99; B = single page + trial toggle at $39.99; C = A at $49.99.
  References: <ref links per page>
</paywall_brief>
```

## 4b. Retention paywall brief

```xml
<retention_paywall_brief trigger="transaction_abandon | paywall_decline | cancel flow | winback" price="<retentionPrice>/yr">
  One screen. Headline: a personal reason to stay, from their goal and progress ("Keep your
  12-day streak"). The price as the hero: "<price> per year", plus the exact renewal terms
  (every year at <price>, or first year only, then <regular price>). One CTA, plus "No thanks"
  in plain text. Restore · Terms · Privacy. Shown once per user. Never "only today" or fake timers.
</retention_paywall_brief>
```

## 5. Screenshot headline brief

```xml
<store_screenshots app="<App>" locale="en-US">
  Slide 1 = the first win/viral moment, 2 = how it works, 3 = the personal result,
  4–6 = features as outcomes, 7 = the habit/progress. Headlines 2–5 words, readable at
  thumbnail size, verbs first. Keyword from the subtitle appears in slides 1–2.
  Three set directions: <paper> · <brand colour> · <panorama bridge>. Real captures only.
</store_screenshots>
```

## 6. Preview video storyboard

```xml
<preview_storyboard length="25s" locale="en-US">
  0–3 s the win (no logo intro) · 3–8 s how · 8–18 s three features, one caption each ·
  18–23 s the result/progress · 23–25 s end card. Real app only, no onboarding screens.
  Captions ≤ 5 words, inside the safe area. Music: per round T (ACE-Step <mood>, <bpm> · silent · own track).
</preview_storyboard>
```

## 7. Conversion critique

Run on the real screenshots of the whole funnel, in order. Ideally a subagent with fresh
context and only the images and this prompt, so it judges what a new user sees.

```xml
<conversion_critique>
  You are a new user who installed <App> from an ad promising "<promise>".
  For each screenshot, in order, answer briefly:
  1. In 3 seconds, what is this screen asking me to do? Is it the same as its job: <job>?
  2. What would make me hesitate or quit here?
  3. Is the value I'll get clearer than on the previous screen?
  4. Visual: anything generic, misaligned, inconsistent with the other screens, or hard to
     read at arm's length? If there is a mascot: is it on-model, and does it help or distract?
  Then list the 5 changes with the biggest likely effect on reaching the first win and
  starting the trial, most important first, each tied to one screen.
  Do not praise. Do not invent statistics.
</conversion_critique>
```

Fix the top findings, re-screenshot, and keep the before/after for the final report.

## 7b. Mascot concept brief

In [mascot.md §4](mascot.md#4-the-concept-brief): three original concepts, written and
sketched in step 3 so the user picks one before the plan.

## 8. Briefing a subagent

When research or a critique goes to a subagent: give it the goal, the exact targets, the
tool rules from [research-sources.md](research-sources.md) (and [mobbin-playbook.md](mobbin-playbook.md) for Mobbin), what to return (a table:
target · app · reference link · decision), and what not to do (no saving, no building). It
starts cold, so everything it needs must be in the brief.

Sources: [Anthropic cookbook: prompting for frontend aesthetics](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics),
[Claude blog: improving frontend design through skills](https://claude.com/blog/improving-frontend-design-through-skills).
