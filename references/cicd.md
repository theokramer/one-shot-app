# CI/CD and App Store Connect uploads

Copy the unsigned `ci.yml` independently of the upload workflow. Use GitHub-hosted
runners, read-only tokens and no secrets for pull requests. Require a PR and passing
CI on `main`, and block force pushes and branch deletion.

Install `app-store.yml` only if selected. It starts off. Before placing a key in GitHub,
ask for separate approval to share that key with the exact repository environment.
Use a scoped key only for the approved app when available. Restrict the `app-store`
environment to the exact `main` branch before entering secrets. Use environment
secrets `ASC_KEY_ID`, `ASC_ISSUER_ID` and `ASC_PRIVATE_KEY_BASE64`. The user may add
them directly or explicitly authorize the transfer. Keep repository-wide secrets empty.
Never copy the key into Git or print it.

If the user requires a GitHub environment reviewer, configure and verify that gate
before enabling uploads. If the plan cannot enforce it, keep the workflow disabled
and use a user-dispatched upload or a local handoff, according to the chosen permission.

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

## Choose the upload mode

| Repository variable | Effect |
|---|---|
| Unset | Disabled (default). |
| `APP_STORE_DEPLOY_MODE=manual` | The workflow runs only when the user chooses **Run workflow** for `main`. |
| `APP_STORE_DEPLOY_MODE=automatic` | Every push to protected `main` uploads a build. Set it only after explicit approval for ongoing uploads and verified branch protection. |

Use a required environment reviewer if the user wants a separate approval after dispatch
or merge. If no such reviewer can be configured and that gate is required, leave the
workflow disabled. Explain that automatic mode can continue after the session. Remove
the variable to disarm future jobs. Cancel already queued jobs in GitHub if needed.
Legacy `APP_STORE_DEPLOY_ENABLED` values do not enable this version.

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
is armed (or not, and why), the selected mode, environment restrictions and any approvals still pending.
