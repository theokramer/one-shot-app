# Intake: pitch, menu, questions, plan

Four short steps, all before anything is built. Together they should take the user about
five minutes of clicking, and less every run, because of the library. Phase 4
([connect.md](connect.md)) sits between the questions and the plan.

---

## 0. First-run setup, and the library

```bash
python3 "$SKILL/assets/scripts/setup.py" status      # exit 1 = first run / core config missing
```

**If it's a first run** (no `~/.one-shot-app/`, or core fields missing), greet in one line
("First time: two minutes of setup, then this is never asked again") and collect what's
missing. **Choices first, typing last, secrets never in chat:**

1. `setup.py detect` → GitHub login and orgs, git name/email, project folders, installed
   tools. Turn them into options.
2. One `AskUserQuestion` card (≤ 4 questions), pre-filled from `detect`:
   - **GitHub owner**: `<login>` · `<org1>` · `<org2>`
   - **Bundle ID prefix**: `com.<login>` · `com.<org>` · "Other"
   - **Projects folder**: the detected folders (`~/Documents` · `~/Developer` · …)
   - **Default stack**: Expo · SwiftUI
3. A second card: **App Store Connect API key**: "I have a .p8 key file" · "Help me create
   one" (steps: ASC → Users and Access → Integrations → App Store Connect API → Team key, App
   Manager. It downloads once; move it outside any repo). **Gemini (optional)**: "Add a key
   later" · "I have a key". **Support email for app sites**: git email · "Other".
4. One plain message for the remaining typed values, all non-secret: Apple **Team ID**
   (ASC → Membership; not the certificate's personal ID), ASC **Key ID** and **Issuer ID**,
   and the **path** to the `.p8`. Never search the disk for key files. Save them with
   `setup.py set developer.appleTeamID=… appStoreConnect.keyId=… …`.
5. **Secrets** (Gemini key, optional fallbacks): start `setup.py secret gemini.apiKey` in the
   user's terminal (`mcp__terminal__run_in_terminal`). They paste into a hidden prompt. Never
   ask for a key in chat.
6. The library's personal fields (name, imprint, review contact) are collected by the
   [missing-data card](#missing-library-data-asked-once-ever) in step 3, so first-run users
   go through it once.
7. `setup.py status` → exit 0, then continue with the pitch.

Returning users skip all of this. Then load the library silently:

```bash
python3 "$SKILL/assets/scripts/profile.py" summary
python3 "$SKILL/assets/scripts/profile.py" missing --for website,review,identity
```

`~/.one-shot-app/profile.json` (plus `~/.one-shot-app/learnings.md`) is everything earlier runs learned about the user: identity, imprint,
review contact, account IDs (Meta ad account, TikTok advertiser), last run's menu
answers, standing preferences, and every app shipped so far. Read it all (`cat` is fine;
it's local) and treat it as already answered:

- **Never ask for anything the library holds.** Use it, and mention it in a single line
  ("Using your saved imprint and review contact").
- **Preferences** are standing instructions. Apply them without restating them.
- **Apps** drive the name-collision and duplicate-app (4.3) check.
- What's **missing** is collected once in step 3, then saved, so the next run doesn't
  ask again.

---

## 1. Pitch

Open with exactly this, nothing before it:

> **Hey, what app do you want to build?**
>
> Explain the idea however you like: who it's for, the one thing it must do brilliantly,
> and the feature you'd show on TikTok. If you have a reference (an App Store link, a
> screenshot, a website, a paywall you like), drop it in too.

Then **actually look at what they gave you** before asking anything:

- **App Store link or app name**: `WebFetch` the listing. If Appllama is connected, pull
  its screens and flows (`appllama-usage` skill). Note the hook, what the paywall gates,
  the price, and how its screenshots sell.
- **Screenshot or image**: `Read` it. Note density, colour temperature, corner radii, type
  weight.
- **Website**: the value proposition, and the words they use for their own features.

Reply with three or four lines on what you took from it, plus **the one viral feature**
you'd build (one TikTok-able moment, e.g. "shake your phone for a new room style", or a
scored clip of your squat form). That's how a misread gets caught early.

The user's standing design brief applies to every app, so don't ask about it again: research
real apps on **Mobbin** (`mobbin:search`) before drawing UI, follow
**`appllama-app-design-skill`**, choose one cohesive direction yourself, avoid generic
AI-looking UI, and never ask about colours, fonts or layouts.

---

## 2. The menu: ticking boxes

**Multiple choice is the default for every question in this skill.** The user clicks. They
type only what no option can hold: the pitch itself, a postal address, a name you couldn't
guess. Rules:

- Every question goes through `AskUserQuestion` with 2–4 concrete options. "Other" is always
  added automatically, so typing stays possible without being required.
- Pre-fill options from the library, the pitch and the context: suggested names, the saved
  email, the saved phone, last run's answers ("(Same as last time)").
- Where several answers can be true, use `multiSelect: true`.
- Batch up to 4 questions per call. Never ask in prose what a card could ask.
- A free-text request is one message listing exactly the fields needed, and only after
  every field that can be a choice has been asked as one.

Three `AskUserQuestion` calls. Each allows at most 4 questions with 4 options, and the user
can always pick "Other". Use `multiSelect: true` wherever several answers can be true.
Mark options from the library's `menuDefaults` as **"(Same as last time)"**. Where you'd pick
differently for *this* app, put "(Recommended)" on your pick instead, with a few words on
why in its description. A repeat run should be a handful of clicks. Recommend based on the
pitch, not out of habit: no Cloudflare for an app that needs no server, no ads SDKs for a
utility nobody will advertise.

Read [modules.md](modules.md) first. It says what each option costs in tools, sign-ins and
permissions, which you need in order to recommend honestly.

### Round A: what to build

```jsonc
[
  { "header": "Money", "multiSelect": true,
    "question": "Which monetization pieces should the app ship with?",
    "options": [
      { "label": "RevenueCat subscriptions", "description": "Entitlement 'pro', products in App Store Connect, offering, purchase + restore, server notifications." },
      { "label": "Superwall onboarding + paywall", "description": "High-converting questionnaire onboarding and a code-first Superwall paywall, both with native fallbacks." },
      { "label": "Free trial / intro offer", "description": "e.g. 3-day free trial on yearly. Set in App Store Connect and shown truthfully on the paywall." },
      { "label": "Retention & discounts", "description": "Win-back offers, promotional offers, offer codes, a cancel flow (RevenueCat Customer Center) and an exit-offer paywall." } ] },
  { "header": "Backend", "multiSelect": true,
    "question": "What does it need behind the app?",
    "options": [
      { "label": "Cloudflare Worker", "description": "Server-side AI/API keys (OpenAI → Workers AI fallback), D1/R2 storage, rate limits, and it also hosts the support/privacy/terms site." },
      { "label": "Supabase", "description": "Accounts, sync across devices, shared/social data." },
      { "label": "GitHub repo + CI/CD", "description": "Private repo, CI on every push, App Store upload on merge to main, PR + Copilot review loop afterwards." },
      { "label": "Localization", "description": "App + store listing in more languages (asked next). English stays primary." } ] },
  { "header": "Growth", "multiSelect": true,
    "question": "Which growth and ads pieces should be wired in now?",
    "options": [
      { "label": "Meta Ads attribution", "description": "Facebook SDK + ATT + RevenueCat Meta integration, so ad-driven installs and purchases show up. Ads can start later without a new build." },
      { "label": "TikTok Ads attribution", "description": "TikTok Business SDK + RevenueCat webhook → TikTok Events API relay. App ID/token set on the server after launch, no new build." },
      { "label": "Apple Search Ads attribution", "description": "AdServices token → RevenueCat. No ATT needed." },
      { "label": "TikTok/Reels clip", "description": "A vertical 15–30 s clip of the viral feature for organic posting." } ] },
  { "header": "Stack", "multiSelect": false,
    "question": "Which stack?",
    "options": [
      { "label": "Expo / React Native", "description": "Fast iteration, 3D/Skia, native modules when needed. Three of the four reference apps use it." },
      { "label": "Native SwiftUI", "description": "Smallest binary, best for heavy Apple frameworks (ARKit, Vision, widgets)." } ] }
]
```

### Round B: how complete App Store Connect should be

The basics are **always** done and are not offered: app record, subscriptions with prices,
review screenshot and localizations, availability, age rating, category, metadata,
support/privacy/terms URLs, App Privacy answers, export compliance, review notes, build
upload and attach. These options are the extras:

```jsonc
[
  { "header": "Visuals", "multiSelect": true,
    "question": "Which store visuals should I make and upload?",
    "options": [
      { "label": "Screenshot variations", "description": "3+ distinct, connected sets from real captures, all required sizes; you pick one as the default in the final report." },
      { "label": "App preview video", "description": "15–30 s, the real app (not onboarding), brisk with captions per scene and ACE-Step music; one per language." },
      { "label": "Header + search art", "description": "Asset Library header (3840×1646) and search-results art (3840×2560). Browser-only upload." },
      { "label": "Custom product pages", "description": "Every screenshot variation as its own product page, for ads and for an A/B test once the app is live." } ] },
  { "header": "Offers", "multiSelect": true,
    "question": "Which offers and review extras should be set up?",
    "options": [
      { "label": "Review walkthrough video", "description": "A calm, full-length recording (onboarding → paywall → every feature) attached for App Review." },
      { "label": "Win-back offers", "description": "Discount shown by Apple to lapsed subscribers (App Store + in-app via StoreKit)." },
      { "label": "Promo offers + offer codes", "description": "Subscription offer key, a promotional offer for cancel/exit flows, and an offer-code campaign for influencers." },
      { "label": "Retention messaging", "description": "Cancel flow in-app (RevenueCat Customer Center with a discount) and Apple's Retention Messaging API where available." } ] },
  { "header": "Languages", "multiSelect": true,
    "question": "Which languages besides English should the app and store listing support? (English is always included.)",
    "options": [
      { "label": "German", "description": "App, permission texts, paywall, website, listing, screenshots and preview video in German." },
      { "label": "Spanish", "description": "Same depth in Spanish (Spain + Latin America listing)." },
      { "label": "French", "description": "Same depth in French." },
      { "label": "Japanese", "description": "Same depth in Japanese; large subscription market." } ] },
  { "header": "Run style", "multiSelect": false,
    "question": "After the plan is approved, should I stop anywhere?",
    "options": [
      { "label": "Fully unattended", "description": "I build, test, fix and fill the store on my own; you get a final report with screenshots and a short to-do list." },
      { "label": "One demo stop", "description": "I stop once when the app runs, before store assets, so you can ask for changes." } ] }
]
```

Tick nothing in Languages → English only. "Other" takes any further languages (e.g.
"Italian, Portuguese"). Every chosen language means: strings + permission texts +
paywall messages + website pages + store metadata + screenshots + preview video, and a
simulator pass in that locale. Save the choice as `menuDefaults.languages`.

### Round C: permissions and money

Before calling it, say in one line what is **never** done, whatever is ticked:

> Whatever you tick, I won't type passwords, 2FA codes, API tokens or payment details into
> a website, approve my own permission prompts, buy anything, start ads, or submit for App
> Review. Those stay yours, and I'll queue any that come up for you.

```jsonc
[
  { "header": "Allowed", "multiSelect": true,
    "question": "What may I do without asking again during this run?",
    "options": [
      { "label": "Create & connect accounts", "description": "New RevenueCat/Superwall project, Meta developer app + link to your ad account, TikTok Events Manager data source, RevenueCat integrations and webhooks. Includes accepting those platforms' developer terms." },
      { "label": "Write to App Store Connect", "description": "Create the app record (with your `rc setup apple`), subscriptions, prices, offers, availability, listing, uploads, attach builds, publish App Privacy. Never submits for review." },
      { "label": "Deploy to the web", "description": "Create the GitHub repo, set secrets, deploy Cloudflare Workers (backend + site), Supabase project." },
      { "label": "Spend on AI generation", "description": "Gemini image/video etc. up to the cap you choose next. Without this tick: $0, local renders only." } ] },
  { "header": "Spend cap", "multiSelect": false,
    "question": "Maximum extra spend on generation APIs for this run?",
    "options": [
      { "label": "$0", "description": "Local only: Blender, CC0 assets, Pillow, ffmpeg." },
      { "label": "Up to $5", "description": "Icon concepts and a few images." },
      { "label": "Up to $20", "description": "Plus one or two short AI video clips." },
      { "label": "Up to $50", "description": "Plenty of headroom; I still log every call's cost." } ] },
  /* the name and pricing questions from step 3 can ride along in this same call */
]
```

Write the answers to `docs/RUN.md` (modules, depth, languages, run style, permissions, cap)
straight away. Every later phase reads it, and the final report quotes it back. Save the
menu answers (not the permissions, which are per run) to the library:
`profile.py save-menu '{"money": [...], "backend": [...], ...}'`.

---

## 3. Follow-up questions (only what you can't infer)

Usually one call with two questions, often merged into round C:

| Question | Notes |
|---|---|
| **Name** | Card with 3 concrete names as options (the user can still type one via "Other"). **Before offering them, check each one is free**: search the App Store in the US and DE (`https://itunes.apple.com/search?term=<name>&entity=software&country=us`, then `country=de`). Two working titles were taken mid-run once and had to be renamed. Also check the user's own apps in the library (`apps`) for duplicate-app risk (4.3): two similar apps on one account is a rejection risk. |
| **Pricing** | Card with 3–4 options. Default recommendation: **weekly + yearly, 3-day trial on yearly** (e.g. $6.99/wk, $39.99/yr), unless the library has `defaults.pricing`. Alternatives: monthly + yearly with a 7-day trial; yearly only; lifetime + yearly. |
| **Free vs Pro** | Propose it, don't ask it. Default is a **hard nudge** (backed by the data in [conversion.md](conversion.md)); the library's preferences override it: the core "wow" feature is Pro after one free taste, browsing stays free, everything with ongoing cost is Pro (e.g. a fitness coach: form analysis Pro, exercise library free, coach 1 message/day, most programs locked). |

Don't ask about colours, fonts, architecture, persistence, deployment target or folder
layout. Decide them.

### Missing library data (asked once, ever)

If `profile.py missing` reported gaps, ask **choice-able fields as an `AskUserQuestion`
card first**, with options pre-filled from the library and the context:

| Field | Options |
|---|---|
| Imprint email | the saved account email · `support@<app-domain>` if a domain exists · "Other" |
| Imprint phone | the saved review-contact phone · "No phone, use a contact form on the site" · "Other" |
| Person or company | "Private person (sole trader)" · "Company (GmbH/UG/…)" |
| VAT ID | "None (small business, § 19 UStG)" · "I have one" (then typed) |
| App Review phone | the saved number · "Same as imprint" |
| Country | "Deutschland" · "Österreich" · "Schweiz" |
| Mobbin collections | "Yes, save each app's references to a private collection" · "No" |

Only what's left (street, postcode, city, and names nobody could guess) goes into one
plain chat message, for example:

> For the website's **imprint (Impressum)**, which German law requires on every app site, and
> the **App Review contact**, I need these once. I'll save them, so later apps won't ask:
>
> - Full name (or company name + legal form + representative)
> - Postal address for service of documents: street, postcode, city, country. No PO box;
>   a paid c/o imprint service address works if you don't want your home address public
> - Email and phone for the imprint (published)
> - VAT ID / register entry, if you have one
> - App Review contact phone (not published), if different

Save the answers with `profile.py set imprint.street=… …`, then `profile.py confirm imprint`.
Never guess or fill in a placeholder. If the user skips it, the run builds the site
without `/imprint` and puts it first on the to-do list. Re-confirm the imprint once
`confirmedAt` is more than 12 months old ("Is this still right?", showing what's saved).

Anything new the user mentions along the way (a new ad account, a support email, "always do
X") goes into the library right away: `profile.py set …` / `add-pref "…"`.

### Naming (derived)

- Directory: `<parentDir>/<AppName>` (from `config.json`, default `~/Documents`)
- Bundle ID: `<bundleIdPrefix>.<lowercasename>`. The prefix comes from `config.json`
  (keep the one in config).
- Repo: `<githubOwner>/<kebab-name>-ios` (check with `gh repo view`; a 404 means it's free)
- Store name: `<Name>: <benefit>` up to 30 chars (e.g. "Roomly: AI Home Design")
- Entitlement `pro`; products `<bundle>.pro.yearly`, `<bundle>.pro.weekly`

---

## 4. Connect (phase 4)

Now run [connect.md](connect.md) for the ticked modules. Don't write the plan until the
gate passes. A plan built on a credential that doesn't work is fiction.

---

## 5. The plan: the last question

Create the project directory, `git init`, and write:

- `docs/SPEC.md`: one-sentence pitch, the core loop, screens (4–8), data model, the free
  vs Pro table (the paywall's contract), permissions with exact usage strings, explicitly
  out of scope.
- `docs/DESIGN.md`: the `<design_direction>` block ([prompts.md](prompts.md#1-design_direction-written-once-into-designmd-pasted-into-every-screen-brief)),
  palette tokens, type scale, shape and motion, components, and "Patterns" with the Mobbin
  references each decision comes from. Run the onboarding-flow and paywall rows of the
  [research matrix](mobbin-playbook.md#the-research-matrix-phase-57) **before** writing it,
  so the plan already says which flows the funnel is modelled on.
- In `docs/SPEC.md`, also: **the first win** (one sentence), the time-to-first-win budget,
  and the retention loop ([conversion.md](conversion.md#1-fast-wins-designing-the-first-60-seconds)).
- `docs/PLAN.md`: phases 6–11 with every step for the ticked modules, in order. Mark
  **who** does each step (`auto` / `auto-chrome` / `user-later`). Also: the expected
  user to-do list (known in advance, e.g. "Paste the Meta client token into RevenueCat"),
  the spend estimate against the cap, and a rough duration.

Then show the plan in chat in **at most 15 lines**:

```
**<AppName>**: <one sentence>
Viral moment: <the feature>
Stack: Expo · RevenueCat + Superwall · Cloudflare · Meta + TikTok · EN/DE
Free vs Pro: <one line>
Store: full basics + 3 screenshot sets, preview video EN/DE, review video, win-back
Unattended: everything below except ↓
Your to-do at the end (known now): App Privacy "Publish" click if Apple asks for re-auth · Submit for review
Spend: ~$3 of your $20 cap · Time: ~4–6 h
```

Link the three files and ask once: **"Go?"** After the user says go, commit `docs/`, and
from then on there are no more questions until the final report.
