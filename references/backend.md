# Backend: Cloudflare Worker or Supabase, only when the app needs one

## The decision

Build a backend **only** if the spec requires at least one of:

- **Accounts or cross-device sync** — the user's data must outlive the device.
- **Server-side AI or a third-party API** — because the credential cannot ship in the
  binary. This is the most common trigger. One shipped app needed it purely to keep an AI provider key
  off the device.
- **Shared or social data** — leaderboards, feeds, anything one user's device writes and
  another reads.
- **Server-validated entitlements** beyond what RevenueCat already gives you (rare —
  RevenueCat webhooks usually cover it).

If none apply, skip this phase entirely. Do not scaffold an unused project "for later."
A local-first app with SwiftData ships faster and has fewer ways to fail.

Say in one line which trigger fired, or that none did.

**Which one:** pick a **Cloudflare Worker** when the
need is server-side AI/API keys, rate limiting, light storage (D1/R2) and hosting the
support site. Pick **Supabase** when there are real accounts, sync or shared/social data.
Both are fine for a single app if each does its own job.

## Setup: Cloudflare Worker

Load `cloudflare:workers-best-practices` and `cloudflare:wrangler` before writing code.

```
backend/                 Worker "<kebab>-api"  → https://<kebab>-api.<subdomain>.workers.dev
  src/index.ts           routes: /v1/device, /v1/config, feature endpoints, /hooks/revenuecat/<secret>
  wrangler.jsonc         vars: model names, DEVICE_DAILY, GLOBAL_DAILY, RC_PUBLIC_KEY; D1/R2 bindings
  test/                  a local stub that speaks the OpenAI wire format, plus a smoke script
site/                    Worker "<kebab>"      → support / privacy / terms
```

- **AI**: OpenAI first if `OPENAI_API_KEY` is set (the user runs `wrangler secret put`), with
  **Workers AI as automatic fallback**, so the app works without any key. The model and
  base URL are vars, not code.
- **Device identity**: `/v1/device` issues an HMAC-signed device token; the app keeps it in
  the keychain and uses the same ID as the RevenueCat app user ID (`Purchases.logIn`).
- **Pro checks on the server**: verify the entitlement with RevenueCat's REST API using the
  device ID (cache briefly). Free limits are enforced per device per day (402 when the
  limit is hit), with a global daily cap so a bug can't burn the budget.
- **`/v1/config`**: runtime switches the app reads on launch (TikTok IDs, feature flags,
  minimum version), so post-launch changes need no build.
- **Privacy**: delete uploads after processing, results after a short TTL, and state both
  in the privacy policy. Pass the user's language through (`accept-language` / `x-lang`).
- Before going public, put App Attest in front of `/v1/device` (or note it in
  `POST_LAUNCH.md`).
- **Never rename a Worker that holds secrets.** Secrets can't be read back or copied.

## Setup: Supabase

Invoke the **`supabase` skill** for the actual work — it carries current API surface and
auth patterns. Before writing any schema, also load
**`supabase-postgres-best-practices`**; RLS and column types are exactly the things that
are painful to change after data exists.

Use the `mcp__supabase__*` tools where available, otherwise the `supabase` CLI with the
access token from `config.json`.

```
supabase/
├── config.toml
├── migrations/
│   └── <timestamp>_init.sql
└── functions/
    └── <name>/index.ts
```

## Auth

Default to **anonymous sign-in**. It gives every install a stable `auth.uid()` to hang RLS
on without asking anyone to create an account — which is the right trade for a v1 consumer
app, and matches the SwiftUI reference app.

Sign in once at launch, persist the session, and only offer account linking (Apple/email)
if the spec calls for sync across devices.

## Row-level security — non-negotiable

Every table gets RLS enabled, in the same migration that creates it. Not a follow-up.

```sql
alter table public.items enable row level security;

create policy "owner reads own items"
  on public.items for select
  using (auth.uid() = user_id);

create policy "owner writes own items"
  on public.items for insert
  with check (auth.uid() = user_id);
```

A table without a policy is invisible; a table without RLS is public. Confirm with
`mcp__supabase__get_advisors` before moving on and fix anything it flags.

## Edge functions

This is where third-party credentials live. The function reads them from its own secrets;
the app only ever calls the function.

```bash
supabase secrets set PROVIDER_API_KEY=…
supabase functions deploy <name>
```

The function must: verify the caller's JWT, validate and bound the input (size limits on
uploads especially), call the provider, and return a narrow shape. Never proxy an arbitrary
URL, and never echo the provider's raw error back to the client.

## The client side

`Services/SupabaseClient.swift`, configured from `AppConfiguration` — project URL and
publishable key come through build settings into `Info.plist`, as in
[scaffold.md](scaffold.md).

The publishable key is not a secret; it identifies the project. Every row it can reach is
fenced by RLS. Say that in a comment so nobody later "fixes" it by moving it somewhere
clever.

Network code fails closed and degrades: if the backend is unreachable, the app keeps working
against local state and syncs later. A first launch that shows a spinner because Supabase is
down is a one-star review.

## Verification

- `mcp__supabase__get_advisors` clean (security *and* performance).
- Every table has RLS enabled and at least one policy.
- No provider credential appears anywhere under the app source directory:
  ```bash
  grep -rIl "$(printf 'sk-\|Bearer \|BEGIN PRIVATE KEY')" <AppName>/ && echo "LEAK" || echo clean
  ```
- The app launches and works with the network disabled.
