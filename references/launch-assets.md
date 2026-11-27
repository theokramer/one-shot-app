# Launch assets: icon, screenshots, videos, metadata, website

Runs in phase 9, after the app has passed its own QA loop (or the user's demo stop).
Uploading is in [app-store-connect.md](app-store-connect.md); this file is about *making*
the assets well.

## App icon

- Generate **3–4 distinct concepts** and judge them at real home-screen size (60/120/180 px
  contact sheet on light *and* dark wallpaper). One idea, readable at 40 px, no text, no
  thin strokes.
- Made with the round-T image choice ([research-sources.md](research-sources.md#images-and-video)):
  Gemini or Sunra concepts (within the spend cap; keys from `~/.one-shot-app/config.json`,
  never printed), a Blender render or vector composition (local), or a typographic/vector
  icon (no generation).
- If the app has a mascot (`docs/MASCOT.md`), one concept is its face or signature
  feature. It wins only if it reads better at 40 px than the others.
- Pick the best concept yourself, write the reasoning into `DECISIONS.md`, and show the
  rest in the final report so the user can swap with one word.
- Export 1024×1024, **no alpha, no rounded corners**: `sips -g hasAlpha icon.png` → `no`.

## Screenshots: default style rules

Order and headlines follow [conversion.md §5](conversion.md#5-the-app-store-page-that-converts)
and the [headline brief](prompts.md#5-screenshot-headline-brief). The preview video follows the
[storyboard](prompts.md#6-preview-video-storyboard): the app video in a device frame on a
colorful background, captions on the background rather than on the video.


1. **Only real app captures**, from your QA simulator with a clean status bar and
   realistic seeded data. Never AI-drawn UI.
2. **No AI backgrounds by default.** Keep the background visually consistent with real
   captures. Use flat brand colour, the app's own paper tone, or one continuous drawn
   element. If the image choice and spend allow it, Gemini or Sunra may draw an abstract texture, but only if it
   matches the captures.
3. **The phone is fully visible or deliberately cropped** (e.g. the top half, cropped at a
   clear line). Never cut off at the bottom edge.
4. **The set is connected**: same background, type and layout on every slide. Better
   still, something that runs across slide edges (a continuous line, a phone bridging two
   slides, a panorama).
5. **No product cut-outs** (white fringes) and no floating objects.
6. Headline = benefit, 2–5 words, local type (Pillow), large. The first slide carries the
   conversion and shows the viral moment.
7. 5–7 slides. 6.9" 1320×2868 (optionally also 6.5" 1242×2688). No Duo, and no iPad unless
   the app supports it.

When "Screenshot variations" is ticked, build **at least three sets** with genuinely different
ideas (paper / brand colour / panorama "spill" or "bridge"). Render a contact sheet of each,
choose the default, and keep the others for custom product pages. The `appstore-screenshots`
and `aso-appstore-screenshots` skills help with copy and layout; the compositor is your own
Pillow script in `store/`, so the rules above stay enforced.

Per language: re-capture in that locale (the simulator in de-DE etc.). That also checks
the translation on every screen.

## Video capture basics

- `xcrun simctl io <udid> recordVideo --codec h264 raw.mp4`; wait for "Recording started"
  before the first tap.
- Remove dead time with `mpdecimate`, then check a contact sheet (1 fps tiles) for frozen
  pickers or repeated screens before calling it done.
- Music per round T: **ACE-Step** (`ace-step-song` skill, instrumental, brand mood), silent, or the user's own track. Check
  the loudness (`ffmpeg -af ebur128`) and listen to a sample. Never hand-synthesize music.
- Captions: drawn locally, one short line per scene, inside the safe area.

Specs for the preview video and the review video: [app-store-connect.md](app-store-connect.md#extras-from-round-b).

## TikTok/Reels clip (if ticked)

1080×1920, under 30 s, the viral moment in the first second, captions burned in, music
per round T, end card with the app name. Save to `marketing/`.

## Store metadata

Write `store/fastlane/metadata/<locale>/` (name, subtitle, promotional_text, description,
keywords, release_notes, support_url, privacy_url, marketing_url) and
`review_information/` (notes, contact) outside the repository, or in its ignored directory.
Read contact values locally without printing them. Before any commit, verify
`git ls-files -- ":(glob)**/review_information/**"` is empty; `.gitignore` does not untrack
existing files. Rules in
[app-store-connect.md](app-store-connect.md#baseline-always-done).

`store/APP_PRIVACY.md`: list every SDK and server in the build and what each receives,
then the answers per data type (collected? linked? tracking? purpose). Derive it from the
code and the SDKs' own privacy manifests, never from a template. `store/COMPLIANCE.md`:
AI-generated content form (models, safeguards, reporting path), security form.

## Website: written and deployed

Support, privacy, terms **and imprint** URLs must resolve before review. Every app site has
these five pages, in every app language, with all five linked in every page's footer:

| Page | Content |
|---|---|
| `/` | one screen: icon, name, the promise, App Store badge (once live), footer |
| `/support` | contact email, FAQ (free vs Pro, how to cancel/restore, data deletion), response time |
| `/privacy` | the controller (the imprint identity), **every** processor: RevenueCat, Superwall, the Worker host, AI providers (OpenAI, Workers AI), Meta, TikTok, with what each gets; the AI consent and how to withdraw it; retention; rights (GDPR) |
| `/terms` | the subscription terms (auto-renew, trial, cancel in Settings), Apple's standard EULA reference, acceptable use for AI features |
| `/imprint` (`/impressum` alias) | **Impressum** per § 5 DDG, rendered from the library: `python3 $SKILL/assets/scripts/profile.py imprint-html --lang de --output site/public/imprint.html` (and `--lang en`). Name or company + legal form + representative, a postal address for service (no PO box), email, phone, register entry and VAT ID if present, responsible person per § 18 (2) MStV, consumer-dispute statement |

**The imprint data comes from the library, never from a guess.** Confirm which name,
address, email, phone and optional register/tax fields will be public during intake.
Reuse that approval for this run; do not substitute private review-contact details.
Render directly to a file with `profile.py imprint-html --lang de --output <file>` and
inspect it locally rather than printing its contents into tool output. If
`profile.py missing --for website` reports gaps, the intake asks for them once (see
[intake.md](intake.md#3-follow-up-questions-only-what-you-cant-infer)) and saves them.
A run never publishes a site with a placeholder imprint. If the data is somehow still
missing at phase 9, deploy without `/imprint`, put "Imprint data" at the top of the to-do
list, and don't fill in an address.

In the app: Settings/About links to Support, Privacy, Terms and Imprint (opened in an
in-app browser sheet), and the paywall links Terms and Privacy.

- **Default host: Cloudflare.** A tiny `site/gen.py` writes `site/public/*.html` in the
  app's palette, and a static-assets Worker `<kebab>` serves it (`npx wrangler deploy` in
  `site/`) at `https://<kebab>.<workersSubdomain>.workers.dev`. Language versions go
  under `/de/…`, and the footer has a language switch.
- Fallback: Netlify via `assets/scripts/netlify_deploy.py` if `netlify.authToken` is in
  config.
- Keep it modest: one stylesheet, no framework. The credits belong in the app.
- `curl -sI` every URL (all five, all languages) → 200 before moving on.
