# CI/CD — merge a PR, land in App Store Connect

Two workflows, copied from `assets/workflows/` with `__APP_NAME__` substituted:

- **`ci.yml`** — builds unsigned on every PR and every push to `main`. Fast, no secrets.
  This is the check the PR loop waits on.
- **`app-store.yml`** — on push to `main`, archives with signing and uploads. Gated behind a
  repo variable.

## Secrets — read straight from config.json, never typed

Phase 4 verified all three values exist and that the `.p8` is where it says it is. Set them
without ever printing the key:

```bash
gh api -X PUT "repos/$OWNER/$REPO/environments/app-store"

KEY_ID=$(python3 -c "import json;print(json.load(open('$HOME/.one-shot-app/config.json'))['appStoreConnect']['keyId'])")
ISSUER=$(python3 -c "import json;print(json.load(open('$HOME/.one-shot-app/config.json'))['appStoreConnect']['issuerId'])")
P8=$(python3 -c "import json,os;print(os.path.expanduser(json.load(open('$HOME/.one-shot-app/config.json'))['appStoreConnect']['privateKeyPath']))")

gh secret set ASC_KEY_ID              --env app-store --body "$KEY_ID"
gh secret set ASC_ISSUER_ID           --env app-store --body "$ISSUER"
gh secret set ASC_PRIVATE_KEY_BASE64  --env app-store < <(base64 -i "$P8")
```

The environment is created first so the user can later add a required reviewer and make
every upload need a human click.

**Never** copy the `.p8` into the repo, never print its contents, never paste it into chat.
Encode straight from the path.

Verify without shipping anything:

```bash
gh secret list --env app-store
```

## The App Store Connect app record

**This is done in phase 4, not here.** The public API refuses `POST /v1/apps`, and
`fastlane produce` won't take the `.p8`. Use:

```bash
rc setup apple <rc-app-id> --project-id <rc-project-id>    # in the user's terminal
```

It signs into the user's Apple ID (password + 2FA typed by **the user**), creates the app
record with the store name you give it, and creates the In-App Purchase key and the ASC
key for RevenueCat. Phase 4 polls until the record exists:

```bash
superwall asc get "/v1/apps?filter[bundleId]=<bundle.id>" --json
```

By this phase the record exists, so CI only needs the build. If it somehow doesn't, that
is a phase-4 failure: put `rc setup apple …` at the top of the to-do list and carry on
with everything that doesn't need it. Never handle the Apple ID password.

The store name must be unique across the whole App Store. Phase 3 checked it with the iTunes
search API; keep two fallback names ready in `docs/RUN.md`.

## Arming the deploy

```yaml
if: ${{ vars.APP_STORE_DEPLOY_ENABLED == 'true' }}
```

With `appStoreDeploy.armOnSetup: true` in `config.json` — the default — Phase 10 arms it:

```bash
gh variable set APP_STORE_DEPLOY_ENABLED --body true
```

That is what makes the pipeline autonomous: a merged PR becomes a TestFlight build without
anyone touching a dashboard. Set `armOnSetup` to `false` for a run that should stay on the
ground.

Say plainly in the final report that it is armed, and that the next merge ships.

## Why merges, not pushes

`main` is protected by convention, not by branch rules: everything after the one-shot
arrives through a squashed PR (see [pr-mode.md](pr-mode.md)). The upload therefore triggers
once per accepted change, with a build number Apple assigns — no collisions from repeated
pushes, no half-finished branch reaching TestFlight.

`concurrency.cancel-in-progress` is `false` on the upload and `true` on CI: a superseded PR
build is worthless, a half-delivered upload confuses App Store Connect.

## Signing

`-allowProvisioningUpdates` with the ASC key lets Xcode create the certificate and profile on
the runner. No fastlane match, no manual profile management.

For that to work: `CODE_SIGN_STYLE = Automatic`, `DEVELOPMENT_TEAM` set in the pbxproj, and
the bundle id registered on the portal. `ci/ExportOptions.plist` uses `destination = upload`,
so `-exportArchive` both exports and delivers — no separate `altool` step.

## Build numbers

`manageAppVersionAndBuildNumber = true` lets Apple assign build numbers, so concurrent or
repeated merges never collide over `CURRENT_PROJECT_VERSION`. `MARKETING_VERSION` is bumped
by hand for a real version change — and that is a decision to ask about, not to make.

## Verification

```bash
gh workflow list
gh run list --limit 5
```

`ci.yml` must be green before the phase is done. Do **not** trigger `app-store.yml` to test
it — that ships a build. Read it, confirm the secrets exist, and move on.

## For the final report

Record it in `docs/RUN.md` for the final report: CI is green, the deploy workflow exists and
is armed (or not, and why), the secrets are set, the app record exists. Then continue. There
is no stop here.
