# Mascot: asked, sketched and picked before "Go"

A mascot is the cheapest way to give an app a face. It makes onboarding feel like a
conversation, it makes the first win a celebration, and it gives win-back and
notifications a voice people recognise. It also has to be **decided before "Go"**,
because it shapes the icon, every funnel screen, the screenshots and the preview video.
So the question is part of the attended block, and the user picks from real concepts,
never a description in prose.

## 1. The question (step 3, in the same card as name and pricing)

```jsonc
{ "header": "Mascot", "multiSelect": false,
  "question": "Should <AppName> have a mascot that guides onboarding, celebrates wins and appears in the store assets?",
  "options": [
    { "label": "Yes, show me ideas", "description": "I sketch 3 original mascot concepts right now; you pick one (or tweak one) before the plan." },
    { "label": "No mascot", "description": "Clean product UI only; the brand is carried by type, colour and real captures." },
    { "label": "I have one", "description": "You give an image or SVG path once; I build the expression set from it." } ] }
```

Mark "Yes, show me ideas" **(Recommended)** for consumer, habit, learning, kids, health,
pets and coaching apps, and "No mascot" for pro tools, finance, productivity for work and
anything that must look serious. Pre-select last run's answer from
`menuDefaults.mascot` ("(Same as last time)"). Save the answer with
`profile.py save-menu '{"mascot": "…"}'`.

## 2. The concept step (right after the card, still attended)

Runs only for "Yes, show me ideas". It takes 2–4 minutes; tell the user in one line
("Sketching 3 mascot ideas, about 3 minutes.").

1. **Write three concepts** with the brief in §4. They must differ in kind, not only in
   colour: e.g. one animal, one object-come-alive, one abstract blob/creature. Each ties to
   the app's job (a plant app: a seedling with a leaf cowlick; a sleep app: a moth that
   dims its own glow).
2. **Check originality.** Not a known character, not a rename of one, and not the
   signature mascot of a big app in the category (no green owl for a learning app). If the
   research tool from round T is connected, search the category's top apps for their
   mascots and steer away from them.
3. **Render a concept sheet per idea** with the round-T image choice
   ([research-sources.md](research-sources.md#images-and-video)):

   | Image choice | Concept sheet |
   |---|---|
   | Gemini API / Sunra | one image per concept: front view, neutral pose, plain background, plus a tiny 64 px icon crop. ≈ 3 images. Only if generation spend is approved and within the budget ([permissions.md](permissions.md)); otherwise (no key, budget $0, not approved) use the local route |
   | Local only / No generation / $0 cap | hand-written **SVG** per concept (flat shapes, 2–3 brand colours, big eyes), rendered with `qlmanage -t -s 768 -o <dir> <file>.svg`. An SVG mascot is also the most consistent and animatable option for the app itself |

4. **Make one contact sheet** (`docs/mascot/concepts.png`, Pillow): the three concepts side
   by side, each with its name, a one-line personality, and a 60 px version on light and on
   dark so the user sees how it reads small. Show it to the user (`Read` the PNG, or send it
   as a file in the desktop app).
5. **Ask the pick** as a card. Use `preview` for each concept's details:

```jsonc
{ "header": "Pick mascot", "multiSelect": false,
  "question": "Which mascot should <AppName> get? (Other: tweak one, e.g. \"#2 but a fox\")",
  "options": [
    { "label": "1 · <Name>", "description": "<form> · <personality in 5 words>", "preview": "<the concept's card from §4 as markdown>" },
    { "label": "2 · <Name>", "description": "…", "preview": "…" },
    { "label": "3 · <Name>", "description": "…", "preview": "…" },
    { "label": "No mascot after all", "description": "Drop it; the plan goes ahead without one." } ] }
```

A tweak typed under "Other" gets **one** redraw of that concept and a yes/no card. After
that, decide. Never more than two rounds: the user came to leave, not to art-direct.

Write the chosen concept to `docs/MASCOT.md` (the card from §4 plus the expression list
from §5) and link it from `docs/DESIGN.md`. The plan's summary line names it
("Mascot: Sprout, a seedling with a leaf cowlick").

## 3. "I have one"

Ask for the path in one message, `Read` it, describe back in one line what you see, and
write `docs/MASCOT.md` from it. If it's a raster image, the expression set is generated
from it as the reference (Gemini/Sunra) or traced to SVG by hand (local). Save the path to
the library only if the user says it's their brand mascot for future apps too
(`profile.py add-pref "Brand mascot: <path>"`).

## 4. The concept brief

```xml
<mascot_brief app="<App>" job="<the app's one job>" audience="<who>">
  Failure mode to avoid: generic "cute AI blob" mascots, clip-art animals, anything that
  looks like an existing character or a big app's mascot, thin lines, gradients that turn
  to mud at 40 px, more than 3 colours, text on the body.
  Make it: one silhouette recognisable in solid black at 40 px; one signature feature
  (a cowlick, an antenna, a scarf) that survives at icon size; big readable eyes; head
  ≥ 40 % of the height; colours from DESIGN.md (dominant + accent), not new ones.
  Tie it to the job: its form or prop shows what the app does, and its personality is how
  the app talks (encouraging coach, calm friend, cheeky rival).
  Output per concept:
    Name (1–2 syllables, easy in every chosen language, no clash with the app name)
    Form · signature feature · palette hexes
    Personality in 3 words · how it talks (one sample line in onboarding voice)
    Where it shines: onboarding guide / first-win celebration / win-back / icon (yes/no)
    Image prompt (for the generator) or SVG plan (for local)
</mascot_brief>
```

## 5. Production (unattended, phase 6–9)

Make the master first, then everything else from it, so the character never drifts.

- **Master**: the chosen concept redrawn clean at 2048 px (transparent PNG) or as a tidy
  SVG with named layers (body, eyes, mouth, feature).
- **Expression set** (transparent PNG @3x or SVG variants): `neutral`, `happy`,
  `thinking` (loading/analysing), `celebrate` (first win, purchase), `encourage` (streak
  at risk), `sad-miss-you` (win-back, retention paywall), `sleep` (empty states, quiet
  hours). With Gemini/Sunra, always pass the master as the reference image and the same
  style line; reject any frame whose silhouette or palette drifts.
- **Motion** (no extra cost): idle bob 2–3 px, blink every 4–6 s, a squash-and-stretch hop
  on `celebrate`, all with Reanimated springs (Expo) or SwiftUI `phaseAnimator`. Respect
  Reduce Motion. An SVG mascot can move eyes and mouth directly.
- **Assets live in** `assets/mascot/` with a `Mascot` component taking `mood` and `size`.

## 6. Where it appears (and where it doesn't)

| Surface | Use |
|---|---|
| Onboarding | the guide: it asks the questions in its voice, reacts to answers (`thinking` → `happy`), small (≤ 25 % of the screen), never covering the CTA |
| First win | `celebrate` with haptic + confetti or a hop: the emotional peak of the funnel |
| Paywall | at most a small accent near the headline. **Never** next to the price, the trial terms or the CTA, and never on the plan cards |
| Retention / exit paywall, win-back | `sad-miss-you` with the retention price: the strongest place for it |
| Empty states, loading, errors | `sleep` / `thinking`, with a line in its voice |
| Notifications, widget | its voice in copy ("Sprout is thirsty"); the widget may show it small |
| App icon | one of the 3–4 icon concepts must be the mascot's face or feature ([launch-assets.md](launch-assets.md#app-icon)); pick it only if it beats the others at 40 px |
| Screenshots, preview video | in 1–2 of the screenshot panels and the end card, beside real captures, never replacing them |
| Website, TikTok clip | hero on the landing page; the clip's narrator or end card |

QA (phase 6 loop and the conversion critique): the mascot never pushes the first win past
the 60 s / 8-tap budget, never hides a control, stays on-model on every screen, and the
funnel still makes sense with it removed.
