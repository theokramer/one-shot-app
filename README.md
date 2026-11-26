# one-shot-app: a Claude Code skill

<!-- demo:start -->
<!-- demo:end -->

**Pitch an iOS app, tick a few boxes, do the sign-ins, and walk away.** Hours later there's
a finished, monetized app in App Store Connect, waiting only for you to press "Submit".

It was built from shipping four real subscription apps (one SwiftUI, three Expo), and every
rule in it comes from something that broke along the way, including real App Review
rejections.

## What one run does

1. **Pitch.** You describe the idea, optionally with a reference app or screenshot.
2. **Tick boxes.** Clickable menus for the modules, how complete App Store Connect should be,
   languages, permissions and a spend cap. Almost no typing.
3. **Connect everything.** It checks every tool, login and key up front, and does all the
   steps that need you (Apple 2FA, Chrome sign-ins) while you're still there.
4. **One plan, one "Go".**
5. **Unattended.** It researches every funnel screen on Mobbin, builds the app, tests it
   in its own simulator, fixes what it finds, makes the store assets, fills App Store
   Connect, uploads the build and runs a review audit. You get a report and a short to-do list.

**Modules you can tick:**

| Area | Modules |
|---|---|
| Money | RevenueCat subscriptions · Superwall onboarding + multi-page paywall · free trial · win-back, promo offers, offer codes, cancel flow |
| Backend | Cloudflare Worker (AI keys server-side, D1/R2, website) · Supabase · GitHub repo + CI/CD · localization |
| Growth | Meta Ads, TikTok Ads and Apple Search Ads attribution (switchable after launch without a new build) · a TikTok/Reels clip |
| Store | screenshot variations · preview video · review walkthrough video · header/search art · custom product pages |
| Stack | Expo / React Native or native SwiftUI |

Every app also gets support, privacy, terms and imprint (Impressum) pages, hosted for you.

## Requirements

- macOS with Xcode, plus [Claude Code](https://claude.com/claude-code) (the desktop app is
  best: it adds the simulator panel and the browser)
- An Apple Developer Program membership, and an App Store Connect API key (team key, App
  Manager access)
- Free accounts and CLIs: GitHub (`gh`), RevenueCat (`rc`), Superwall (`superwall`), and
  optionally Cloudflare (`wrangler`), Supabase, a Gemini API key, and Meta/TikTok ad accounts
- **Plugins are your choice, none required**: on first run you pick your design research
  (Mobbin MCP, Appllama MCP, plain web research, or none), design skills
  (`appllama-app-design-skill`, `frontend-design`, or the built-in rules), image/video
  generation (Gemini API, Sunra, local Blender/Pillow, or none) and music (ACE-Step, silent,
  or your own track). Every step works with any combination.

You don't need to set these up in advance. The first run checks everything and prints the
exact install and login commands for the modules you picked.

## Install

```bash
git clone <this repo> ~/.claude/skills/one-shot-app
```

Then in Claude Code: `/one-shot-app`, or just say "build me an app".

## Your data stays yours

The skill folder contains **no personal data**, so you can update or share it freely.
On first use it asks for what it needs (mostly multiple choice) and saves it to
`~/.one-shot-app/` on your Mac:

| File | What |
|---|---|
| `config.json` | account keys (chmod 600). Secrets are typed only into a hidden terminal prompt, never into chat |
| `profile.json` | your library: identity, imprint, App Review contact, ad-account IDs, last menu answers, preferences, past apps |
| `learnings.md` | what it learned from your runs |

Nothing is asked twice. Each run needs fewer clicks than the last. Set `ONE_SHOT_HOME` to
keep the data somewhere else.

## Guardrails

It never types your passwords, 2FA codes, tokens or payment details, never buys anything,
never starts ads, never spends beyond your cap, and **never submits for App Review**.
You stay responsible for what you publish: check the generated privacy policy, terms and
imprint. They're drafts from your own data, not legal advice.

## Record your own run

`assets/demo/` has a time-lapse recorder and an assembler that turns a run into a short
video and GIF. See [assets/demo/README.md](assets/demo/README.md).

## Sharing a modified copy

```bash
python3 assets/scripts/package.py scan          # proves no personal data is in the shared files
python3 assets/scripts/package.py zip ~/Desktop  # clean zip
```

## License

MIT, see [LICENSE](LICENSE).
