# Phase 4: Verify approved connections

Use the [permissions policy](permissions.md) before signing in or calling authenticated
services. Phase 4 is verification. Keep local work moving when credentials or approvals
are missing. Defer provisioning and other remote writes until their exact scope is approved.

---

## 4.1 Machine check (automatic, ~30 s)

```bash
python3 "$SKILL/assets/scripts/preflight.py" \
  --modules core,asc,revenuecat,superwall,cloudflare,meta,tiktok,gemini   # only the ticked ones
```

It checks each tool, each login and each key for the given modules, and prints **one
consolidated list** of what's missing with the exact command. Show that list to the user
as a single block, for example:

> To run fully on its own, the run needs these once:
>
> ```bash
> brew install revenuecat/tap/rc
> ```
> ```bash
> rc auth login
> ```
> ```bash
> npx wrangler login
> ```
>
> Run them in your terminal (or tell me to run the installs; logins have to be yours),
> then say "done".

- **Installs** (`brew install …`, `npm i -g …`, `pip install …`): run them yourself once the
  user OKs. They're local and reversible.
- **Logins** (`gh auth login`, `superwall login`, `rc auth login`, `npx wrangler login`,
  `supabase login`): the user runs these. They open a browser or ask for a code.
- **MCP servers that need auth** (Mobbin, Supabase, Appllama): tell the user to authorize
  them via `/mcp`. Claude can't start OAuth itself. Only the tools picked in round T are needed. If
  one can't be connected, offer to drop it (the run falls back to the other chosen sources,
  or to web research) and record that in `docs/RUN.md`.
- **Gemini key**: if `gemini.apiKey` is in config and preflight gets HTTP 429 ("spending
  cap"), the user has to raise the cap in Google Cloud. A Gemini *subscription* (AI Pro,
  Edu) does **not** fund the API. Say this up front if any spend is planned.

Re-run the affected checks. A failed check blocks only the dependent action. A Superwall proxy connection is optional and must already be configured by the user if selected. Prefer the direct API when it supports the task.

Preflight also reads the library (`~/.one-shot-app/profile.json`). Missing imprint or review-contact data
shows up under "Needs you". It should already have been collected in intake step 3; if
not, ask for it now in the same message as the logins.

**Use the library to shorten the attended block.** If `accounts.metaAdAccountId` /
`tiktokAdvertiserId` are saved, link to those accounts directly instead of searching for
them, and skip "create an ads account". Every ID discovered during this block (new ad
account, business portfolio, support inbox) is saved with `profile.py set accounts.…`
before you move on.

## 4.2 Provision the accounts that the attended steps need

These are remote writes. Do them only after the exact target and action have been approved for this run. Otherwise move them to the plan or handoff.

1. Check the store name is free (US + DE iTunes search) and the bundle ID is unused.
2. `rc projects create --name <App>` → `rc apps create` (App Store, bundle ID). Save the
   IDs to `docs/RUN.md`. Don't touch the default project.
3. `superwall apps create` (or `superwall bootstrap`), and save the IDs.
4. Cloudflare: `npx wrangler deploy` of an empty Worker `<kebab>-api` and the site Worker
   `<kebab>`, so the URLs exist for the privacy policy and the SDK config.

## 4.3 The attended block (user at the keyboard, ~5–10 min)

Present it as **one numbered checklist**, run it, and confirm each item with a check of
your own (never take "done" on faith):

| # | Step | Who | How Claude verifies |
|---|---|---|---|
| 1 | `rc setup apple <rc-app> --project-id <p>`: sign in, 2FA, **create the app** with the exact store name, create both keys | user in terminal (`mcp__terminal__run_in_terminal` to start it, so the user just types) | poll `superwall asc get "/v1/apps?filter[bundleId]=…"` until total ≥ 1; `rc apps show` shows the keys configured |
| 2 | Chrome: sign in to **appstoreconnect.apple.com** (only if an unattended-Chrome ASC item is planned) | user | open ASC in a new tab and see the Apps page, not the login |
| 3 | Chrome: sign in to **developers.facebook.com** + Business Manager (Meta ticked) | user | Claude opens My Apps |
| 4 | Claude creates the Meta app, adds iOS + bundle ID, links the ad account (tick "Create & connect") | Claude in Chrome | App ID recorded in `docs/RUN.md` |
| 5 | **User pastes** the Meta client token into RevenueCat → app → Integrations → Meta Ads (App Events API) and into `wrangler secret put META_CLIENT_TOKEN` if the server needs it | user | `rc` shows the integration; the Worker config endpoint responds |
| 6 | Chrome: sign in to **ads.tiktok.com** (TikTok ticked). If there's no ads account, the **user** completes company/industry/payment | user | Claude sees Events Manager |
| 7 | OpenAI key (if wanted): user runs `npx wrangler secret put OPENAI_API_KEY` | user | `wrangler secret list` shows the name |
| 7b | Apple server notifications → RevenueCat: **user** checks the existing Production and Sandbox routes in ASC → App Information. For a new direct connection, apply RevenueCat's setup to both or paste the URL privately into both and choose V2. Before changing an existing route, confirm the affected consumer and agree how to preserve delivery, including forwarding if needed. | user | Verify the approved app and both configured environments with the user or a test notification, without exposing the URLs in tool output or logs. |
| 8 | Paid Apps Agreement is active (ASC → Business) | user, only if it isn't | asc.py / Chrome check |
| 9 | Simulator panel attach, to accept device access once | Claude | screenshot works |

Rules for this block:

- Use Chrome only when needed for an approved action. The user signs in themselves. Load all the Chrome tools in
  one `ToolSearch` call. Work in new tabs. If the extension isn't connected, ask the user to
  connect it, and don't fall back silently.
- The built-in browser pane **doesn't share** the user's Chrome sign-ins. Use Claude in
  Chrome for anything the user signed into in Chrome.
- Never type a password, 2FA code, API token, client token or payment detail, even if
  the user offers or insists. Hand over the exact field and the exact value's location
  ("App settings → Advanced → Client token").
- The user accepts developer terms. Creating an app and linking an ad account each need
  an approved action and destination. Unapproved actions stay on the to-do list.

## 4.4 Prove the unattended path

After read access is approved, run one read-only check per selected surface, and
record it in `docs/RUN.md`:

- `superwall asc get /v1/apps/<id>` → 200
- `rc offerings list --project-id <p>` → 200
- `npx wrangler whoami` → logged in
- Chrome tab on ASC shows the app (if planned)
- `gh api user` → 200
- Gemini `GET /v1beta/models` → 200 (if spend is allowed)

Only now go to step 5 of [intake.md](intake.md) (the plan).

---

## What can never be pre-authorized (put it on the to-do list)

- Submitting for App Review
- Paid Apps Agreement, banking, tax
- Typing a password, 2FA code, token or payment detail anywhere
- Launching or funding ads
- Anything costing money beyond the cap
- Registering the TikTok app in Events Manager, and saving the Meta iPhone Store ID (both
  need the app to be live)
