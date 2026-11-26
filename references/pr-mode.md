# Phase 11: final report, then PR mode

## The final report (the user comes back to this)

One message, and nothing in it is a surprise:

1. **Headline**: "<App> is built, tested and ready for review in App Store Connect" (or
   exactly what isn't).
2. **Screenshots** of the key screens (SendUserFile), plus contact sheets of every
   screenshot set and icon concept, with the defaults marked.
3. **What was done**, grouped by the ticked modules, one line each, with IDs in
   `docs/RUN.md`.
4. **Decisions made for you**: the top 5 from `docs/DECISIONS.md`.
5. **Your to-do**: a numbered list of only the things the run could not do (token pastes,
   publish clicks that needed re-auth, Paid Apps Agreement, the submit itself), each with
   the exact link or command. Mark which ones are needed before submitting and which on
   launch day (`store/POST_LAUNCH.md`).
6. **Spend**: what was spent vs the cap.
6b. **Funnel**: first win time and taps, onboarding/paywall screen counts, the Mobbin
   flows it was modelled on (links), the critique's before/after, and the paywall variants
   ready to A/B.
7. One question: **"Submit for review?"** (it's the user's click, or explicit go-ahead.)

Also write `LEARNINGS.md` in the app repo (IDs, how to ship a build, gotchas from this
run), add what you learned about this user to `~/.one-shot-app/learnings.md`, put general,
reusable lessons (no names, IDs or paths) in the skill's `references/learnings.md`, and
save a short project memory with the IDs.

**Update the library**, so the next run asks less:

```bash
P="python3 $SKILL/assets/scripts/profile.py"
$P add-app name="<App>" bundle=<bundle> stack=<expo|swiftui> dir="<path>" category="<one line>" ascAppId=<id>
$P add-pref "<each correction or standing wish the user voiced in this run>"
$P set accounts.<id>=<value>     # any account ID discovered in this run
```

A correction the user made ("phones cut off look weird", "no Duo screenshots") is a
preference. Save it in their words, shortened.

# PR mode: the autonomous review loop

## The switch

The initial build goes straight to `main`, because reviewing pull requests for an app that
does not exist yet is pointless. **That ends at Phase 11.** From then on, in that repo,
forever:

> Every change goes on a branch. Every branch gets a pull request. Copilot reviews it.
> Its comments get addressed. When CI is green and the review is clean, **the loop merges
> itself** — and the merge is what ships a build.

Write this into the generated repo's `CLAUDE.md` so it survives the session. Say it out
loud at handoff too, so the user knows the rules changed.

## Why it merges itself

The earlier version of this skill forbade merging. That was wrong for this workflow: it
left every change parked on a branch waiting for a human, which defeats the point of a
one-shot pipeline. The user's review happens where it is cheapest — on the running app at
the final report (or the demo stop), and on the App Store build before release — not on diffs of code they
did not write.

`github.autoMerge` in `config.json` controls it. Set it to `false` and the loop stops after
the review and hands the PR over instead.

## The loop, step by step

```bash
# 1. Branch
git checkout main && git pull --ff-only
git checkout -b <type>/<short-description>

# 2. Work, committing as you go. Build before you push — always.
xcodebuild -project <App>.xcodeproj -scheme <App> -configuration Debug \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build 2>&1 | tail -20

# 3. Open the PR
git push -u origin HEAD
gh pr create --title "<type>: <what changed>" --body "$(cat <<'EOF'
...
EOF
)"

# 4. Ask Copilot for a review
gh api -X POST "repos/$OWNER/$REPO/pulls/$PR/requested_reviewers" \
  -f 'reviewers[]=Copilot'
```

**The reviewer slug is the literal string `Copilot`.** `copilot-pull-request-reviewer`
returns `422 Reviews may only be requested from collaborators`. This costs ten minutes to
rediscover every time; it is written down here so it is not rediscovered.

Copilot review must be enabled for the repository or the org. If the request 422s even with
the right slug, Copilot code review is not available on that plan — record it, skip the
review step, and carry on rather than blocking the run.

```bash
# 5. Wait for the review, then read it
gh api "repos/$OWNER/$REPO/pulls/$PR/reviews" \
  --jq '.[] | "\(.user.login): \(.state)"'
gh api "repos/$OWNER/$REPO/pulls/$PR/comments" \
  --jq '.[] | "\(.path):\(.line) [\(.id)] \(.body)"'
```

**Poll `/reviews`, not `requested_reviewers`.** The moment Copilot posts, it removes itself
from `requested_reviewers` — a script watching that field concludes the request failed. The
review shows up under the login `copilot-pull-request-reviewer[bot]` with state `COMMENTED`,
even though the request was made with the slug `Copilot`. Those three different names for
one actor are the whole reason this paragraph exists.

The summary comment lands on `/reviews`; the actionable line-level notes land on
`/comments`, each with an `id` you need to reply to it.

Poll every 30 seconds up to `github.reviewTimeoutSeconds` (default 420). Copilot usually
answers inside two minutes. If it never does, proceed on CI alone and say so in the summary
— a silent reviewer must not deadlock the pipeline.

### Give Copilot the project's context

A reviewer that doesn't know the house rules writes generic notes. Ship this once, in
Phase 10, and every later review gets sharper:

```
.github/instructions/ios.instructions.md
```

Put in it what `CLAUDE.md` says about the architecture — RevenueCat owns entitlements,
`Design/Theme.swift` is the only source of colour, money is integer cents, views stay dumb,
new files are picked up by folder membership — plus the free/pro contract. Keep it short;
it is a briefing, not a manual.

### 6. Address every comment, then re-review

Each comment gets one of two outcomes, and both are visible in the thread:

- **Fixed** — make the change, then reply on the comment saying what you changed.
- **Declined** — reply saying why, in one sentence. A comment that is wrong about the code,
  or is a style preference that contradicts `CLAUDE.md`, is fine to decline. Silently
  ignoring it is not.

```bash
gh api -X POST "repos/$OWNER/$REPO/pulls/$PR/comments/$COMMENT_ID/replies" \
  -f body='Fixed in <sha> — <one line>.'
```

Then push the fixes and request a fresh review:

```bash
git push
gh api -X POST "repos/$OWNER/$REPO/pulls/$PR/requested_reviewers" -f 'reviewers[]=Copilot'
```

**Two review rounds maximum.** If round two still raises substantive issues, stop, leave the
PR open, and tell the user what is contested. Endless self-review rounds burn credits and
usually mean the change needed a conversation, not another commit.

### 7. Merge

Only when all three hold:

```bash
gh pr checks $PR --watch     # every check green
```

- CI is green.
- Every Copilot comment is either fixed or answered.
- `github.autoMerge` is `true`.

```bash
gh pr merge $PR --squash --delete-branch
```

Squash, so `main` reads as one commit per task. Then say plainly in the summary: what
merged, what Copilot raised, what you declined and why, and — if the deploy is armed — that
a build is now on its way to App Store Connect.

## What still stops the loop

Autonomy is not the same as no judgement. Stop and ask when:

- The change would alter the **free/pro contract** in `docs/SPEC.md`. That is pricing.
- The change **deletes user data** or migrates a SwiftData model destructively.
- Copilot flags a **security** issue you cannot conclusively refute.
- CI is red for a reason you do not understand. Fix what you understand; escalate what you
  do not, rather than disabling the check.
- The PR would bump `MARKETING_VERSION` — a version number is a release decision.

## PR body

Short and honest.

```markdown
## What
<One or two sentences.>

## Why
<The reason. Link the request.>

## Verified
- [x] Builds clean
- [x] Ran in the simulator: <what you actually exercised>
- [ ] <Anything monetization-related re-tested>

## Notes
<Tradeoffs, deferrals, risk. What a reviewer should push back on.>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

Include a simulator screenshot for anything visual.

## Because main deploys

Once `APP_STORE_DEPLOY_ENABLED` is `true`, a merge archives and uploads. Two consequences
worth stating in the PR when relevant:

- A merge consumes a build number and appears in TestFlight. Not free, not silent.
- Build numbers are assigned by Apple; `MARKETING_VERSION` is bumped by hand for a real
  version change.
