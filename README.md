# one-shot-app: a Claude Code skill

**Build a monetized iOS app from a pitch.** Keep it local, review individual actions, or
let the skill carry out an approved plan up to an App Store Connect build.

It combines app scaffolding, monetization, store preparation and reusable implementation
guidance in one workflow.

## What one run does

1. **Pitch.** You describe the idea, optionally with a reference app or screenshot.
2. **Tick boxes.** Clickable menus for the modules, how complete App Store Connect should be,
   languages, permissions and a spend cap. Almost no typing. Want a mascot? It sketches three
   original concepts and you pick one before it starts.
3. **Connect selected services.** It verifies access only for the services you approve.
4. **One plan, one "Go".**
5. **Build and verify.** It tests the app in a separate simulator and prepares assets.
   External changes and uploads follow your approval choices. You get a report and a short to-do list.

**Modules you can tick:**

| Area | Modules |
|---|---|
| Money | RevenueCat subscriptions · Superwall onboarding + multi-page paywall · free trial · win-back, promo offers, offer codes, cancel flow |
| Backend | Cloudflare Worker (AI keys server-side, D1/R2, website) · Supabase · GitHub repo + CI/CD · localization |
| Growth | Meta Ads, TikTok Ads and Apple Search Ads attribution (switchable after launch without a new build) · a TikTok/Reels clip |
| Store | screenshot variations · preview video · review walkthrough video · header/search art · custom product pages |
| Stack | Expo / React Native or native SwiftUI |

Prepare support, privacy, terms and imprint pages locally. Hosting follows your publication approval.

## Requirements

- macOS with Xcode, plus [Claude Code](https://claude.com/claude-code) (the desktop app is
  best: it adds the simulator panel and the browser)
- For App Store work, Apple Developer access and an App Store Connect key scoped to the task
- Free accounts and CLIs: GitHub (`gh`), RevenueCat (`rc`), Superwall (`superwall`), and
  optionally Cloudflare (`wrangler`), Supabase, a Gemini API key, and Meta/TikTok ad accounts
- **Plugins are your choice, none required**: on first run you pick your design research
  (Mobbin MCP, Appllama MCP, plain web research, or none), design skills
  (`appllama-app-design-skill`, `frontend-design`, or the built-in rules), image/video
  generation (Gemini API, Sunra, local Blender/Pillow, or none) and music (ACE-Step, silent,
  or your own track). Every step works with any combination.

The first run checks the tools and accounts needed for your choices. A local build does
not require App Store Connect or GitHub credentials.

## Install

```bash
git clone https://github.com/theokramer/one-shot-app.git ~/.claude/skills/one-shot-app
```

Then in Claude Code: `/one-shot-app`, or just say "build me an app".

## Your data stays yours

Keep personal data outside the skill folder. On first use it asks for what it needs
(mostly multiple choice) and saves it to
`~/.one-shot-app/` on your Mac:

| File | What |
|---|---|
| `config.json` | account keys (chmod 600). Secrets are typed only into a hidden terminal prompt, never into chat |
| `profile.json` | your library: identity, imprint, App Review contact, ad-account IDs, last menu answers, preferences, past apps |
| `learnings.md` | what it learned from your runs |

Nothing is asked twice. Each run needs fewer clicks than the last. Set `ONE_SHOT_HOME` to
keep the data somewhere else.

Local storage does not mean that data can never leave the machine. Approved imprint
details are published on app websites; review contact is sent to App Store Connect;
service integrations receive the account data they need. Anything printed by a tool or
included in chat enters the assistant context. The skill starts with a redacted summary
and uses local scripts for private fields. Enter personal contact details with
`profile.py set-private <field>` in your own terminal.

## Autonomy and safety

The skill starts in **Local only**. Choose per-action approval or scoped autonomy before
connecting accounts. You can turn individual actions off, approve each proposal, do it
yourself, or authorize the assistant to run it automatically. Pushing a branch, merging a
PR, deploying a site and uploading a build are separate choices. Automatic merges and
uploads start disabled. The [permissions guide](references/permissions.md) explains the
scope, cost limits, and human approvals.

The skill runs inside your agent and uses the tools and credentials you give it. Keep
credentials disconnected for local work. Use restricted credentials and provider approval
gates to enforce limits when you connect services.

## Sharing a modified copy

```bash
python3 assets/scripts/package.py scan            # current files, including tracked private files
python3 assets/scripts/package.py scan --history  # also reachable commits and author metadata
python3 assets/scripts/package.py zip ~/Desktop   # filtered source package after a current-file scan
```

The scanner checks known personal values and common patterns; it cannot prove anonymity.
Review the output and any text or media manually. Git history and the repository owner's
GitHub identity remain public even when the latest files have been cleaned. Packaging
excludes private notes, environment files, contact exports and media, and does not include
Git history. It refuses to export into a nonempty directory so stale files cannot leak.

## License

Created and maintained by [Theo Kramer](https://github.com/theokramer). MIT, see [LICENSE](LICENSE).
