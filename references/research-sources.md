# Research and generation sources: one job, any tool

The run never depends on a particular plugin. Each research or generation step below
names what it needs; this file says how each tool choice from menu round T does it. Read the
choice from `docs/RUN.md` → tools. When several sources are chosen, use each for what it is
best at (last column).

## Design research

| Step | Mobbin MCP | Appllama MCP | Web research only | No research |
|---|---|---|---|---|
| Setup | `mobbin:best-practices` + `mobbin:search`; rules in [mobbin-playbook.md](mobbin-playbook.md) | `appllama-usage` skill; `get_credits` first (free). Set a run budget (default ≤ 150 calls) and log it in `docs/RESEARCH.md` | `WebFetch` / `WebSearch` | nothing |
| Category leaders | — | `search_apps` (category query, sort by revenue) → `get_app` for the top 3–5 | WebSearch "<category> app" → App Store listings | — |
| Whole onboarding journey | `search_flows` "<domain> app onboarding" | `list_app_screens` with `flow=onboarding` for 2–3 top apps, **in journey order**; `get_flow_apps` "onboarding" | listing screenshots + the apps' websites (journeys aren't visible; infer carefully) | the structure in [conversion.md §2](conversion.md#2-onboarding-that-converts) |
| One screen type (welcome, question, plan, permission, home, empty state…) | `search_screens` (rules in the playbook) | `search_screens` `mode="semantic"` (by meaning) or `"keyword"` with `screen_type`/`element` filters; `get_screen` gives up to 5 similar screens from other apps | Apple HIG pages for the pattern | built-in briefs in [prompts.md](prompts.md) |
| Paywall pages | `search_flows` + `search_screens` deep | `list_app_screens` `flow=paywall` for top apps; `get_flow_apps` "paywall" | listing screenshots that show the paywall | [conversion.md §3](conversion.md#3-paywalls-that-convert-and-pass-review) |
| **Competitor prices** (default and retention price) | — | `get_app` → in-app purchase pricing for each competitor | the "In-App Purchases" section of each App Store listing | ask nothing; use the menu price and note "unchecked" |
| App Store page (screenshots, subtitle, order) | `search_sections` for marketing heroes | top apps' store screenshots from `get_app` / screens | the competitors' App Store listings | [conversion.md §5](conversion.md#5-the-app-store-page-that-converts) |
| Variations of a built screen | `mobbin:redesign-screen` explore/targeted | `get_screen` similars of the closest reference → build 2–3 directions yourself | — | the conversion critique only |
| Saved references | collection per app (if the library says yes) | screen ids in `docs/RESEARCH.md` (media links expire in ~1 h, so keep ids, re-fetch media) | URLs in `docs/RESEARCH.md` | — |
| **Best at** | breadth of patterns per screen type | depth: real top-grossing journeys, revenue context, prices | free, always available | speed |

Rules for all sources:
- **Look at every image** before citing it. Evidence is a link (Mobbin `mobbin_url`,
  Appllama `app_id/screen_id`, or a URL), and every claim in `DESIGN.md` and the report
  names the products.
- **Precedent = 2+ products.** Take decisions (structure, order, CTA pattern), never another
  app's brand, copy or art.
- Appllama: ignore the watermark in the top-left corner and never reproduce it; no catalog
  sweeping (study real tasks only); when credits run out, finish with the other chosen
  sources and say so in the final report.
- With **No research**, `DESIGN.md` says "Patterns: built-in playbook, no external research",
  and the final report says it once. No fake citations.

## Design guidance skills

| Choice | Use |
|---|---|
| `appllama-app-design-skill` | quality bar, HIG, motion, simulator verification loop for every screen |
| `frontend-design` | aesthetic direction (DESIGN.md) and the website |
| Built-in rules only | `<design_direction>` and screen briefs from [prompts.md](prompts.md) (always applied anyway) |

## Images and video

| Need | Gemini API | Sunra | Local only | No generation |
|---|---|---|---|---|
| App icon | `gemini-3-pro-image` concepts | `sunra` image model | Blender render or vector composition | typographic/vector icon (Pillow / SVG → PNG) |
| Hero art / textures | Gemini textures (must match real captures) | Sunra | Blender + CC0 assets (Poly Haven), gradients | brand colour + real captures |
| Short clips (onboarding, store) | `gemini-omni-1.2-flash` image-to-video (≈ $0.42 / 6 s) | `sunra` video | Blender animation, simulator recordings | simulator recordings only |
| Translations | `gemini-2.5-flash` | — | yourself | yourself |

Every paid call is logged with its cost against the spend cap. If the cap is $0, paid
options behave like "Local only".

## Music

| Choice | Use |
|---|---|
| ACE-Step (local) | `ace-step-song` skill: instrumental, the brand mood, length to the cut |
| Silent | silent AAC track (Apple requires an audio track); the captions carry the story |
| My own track | the file path saved in the library (`profile.py set accounts.musicTrack=…`); trim and fade with ffmpeg |
