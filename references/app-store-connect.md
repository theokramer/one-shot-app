# App Store Connect: filling it to the chosen depth

Surfaces, in order of preference:

1. `superwall asc …`: signed proxy, no JWT. Apps, subscription groups, subscriptions,
   prices, intro offers, availability, review screenshots, versions, builds, metadata.
2. `python3 $SKILL/assets/scripts/asc.py call METHOD PATH [JSON]`: raw API with the `.p8`
   (needs PyJWT + requests). Use it for anything the proxy lacks: preview videos, review
   attachments, custom product pages, win-back, promotional offers, offer codes, age
   rating, App Store version localizations. Subcommands: `attach-build`, `upload-preview`,
   `upload-review-attachment` (see the script's `--help`).
3. `fastlane deliver` for bulk metadata + screenshots per locale. It needs
   `LANG=en_US.UTF-8`, the key JSON with the key **inline**, and an
   `age_rating.json` that includes `socialMedia`.
4. Claude in Chrome, only for things with no API (marked 🌐 below), using the
   phase-4 sign-in.

Never submit for review. Leave it at "Ready for Review" / "Prepare for Submission" with
everything green.

---

## Baseline: always done

| Item | How | Gotchas |
|---|---|---|
| App record | `rc setup apple` (phase 4) | public API can't create apps |
| Subscription group + products | `superwall asc subscription-groups create`, `subscriptions create` | group name = "<App> Pro" |
| Prices | `superwall asc prices points` → `prices set` per product, all territories | pick the price point by customer price in USD, then let Apple equalize |
| Subscription localizations | `superwall asc localizations add` for every language | name + description, ≤ 45 chars |
| Subscription review screenshot | `superwall asc screenshots upload`: a real capture of the paywall | missing → products stay "Missing Metadata" |
| First subscription | must be submitted **with the app version**: `FIRST_SUBSCRIPTION_MUST_BE_SUBMITTED_ON_VERSION` | don't try to submit it alone; attach it to the version when the user submits |
| Availability | all territories; **exclude mainland China for generative-AI apps** (Apple needs a Chinese government licence) | |
| Metadata per locale | `fastlane/metadata/<locale>/` → deliver: name (30), subtitle (30), promo text (170), description (paid features + trial + renewal terms + Terms/Privacy links, else 2.3.2), keywords (100, no spaces, no repeats of name/subtitle), What's New, URLs | the first 3 lines of the description carry the conversion |
| Category, age rating | asc.py `ageRatingDeclarations`; deliver `--app_rating_config_path` | `socialMedia` key needed |
| Support / privacy / terms / imprint URLs | site Worker (see [launch-assets.md](launch-assets.md)) | must resolve before review |
| Export compliance | `ITSAppUsesNonExemptEncryption = NO` in Info.plist / `app.json` | |
| App Privacy | answers in `store/APP_PRIVACY.md`, derived from the code, then 🌐 fill + **Publish** (needs the "Write to ASC" tick; if ASC asks for re-auth, put it on the to-do list) | must match the privacy manifest + policy + SDK manifests. Ads SDKs → tracking = yes for Device ID, Purchase History, Product Interaction |
| Compliance forms | 🌐 AI-generated content (models, safeguards, reporting), Security; medical-device declaration (usually No) | answers drafted in `store/COMPLIANCE.md` |
| Review notes + contact | asc.py `appStoreReviewDetails`: how to test, free vs Pro, AI + consent, ATT, languages, no login needed. Contact name/email/phone from the library (`profile.py get reviewContact`). The intake already asked for anything missing; never invent it | keep current with every build |
| Build | upload, wait for `VALID`, attach: `asc.py attach-build <versionId> <buildNumber>` | bump the build number every upload |
| Screenshots (one set) | 6.9" **1320×2868** required (6.5" 1242×2688 optional); iPhone only unless the app supports iPad. **No iPhone Duo screenshots** (the user removed them) | see the style rules in launch-assets.md |

---

## Extras (from round B)

### Screenshot variations
At least three distinct, internally consistent sets (e.g. full phone on paper, full phone
on brand colour with one continuous line across slides, panorama/"bridge" with elements
crossing slide edges). The default product page gets the one marked **(Recommended)**. The
final report shows a contact sheet of every set so the user can switch the default in one
reply. Upload via `fastlane deliver` or asc.py `appScreenshotSets`.

### App preview video
- 886×1920 (or 1080×1920) H.264, 30 fps, **15–30 s** (Apple's limit), AAC audio track
  (silent is fine; music per the round-T choice).
- **The real app, not the onboarding.** Brisk but readable: 2–3 s per scene, a short
  caption per scene, no long wait at the start, the viral moment in the first 3 s, and an
  end card.
- One per language. Poster frame set by `previewFrameTimeCode`.
- `asc.py upload-preview <file.mp4> <versionId> <locale> [--type IPHONE_67] [--frame 00:00:03:00]`

### Review walkthrough video
- One continuous take from a fresh install: onboarding → every permission prompt →
  paywall (switch plans so the legal text updates) → every feature → settings / restore.
- Calm pace (2–3 s per screen), no frozen picker frames, about 3–5 min. Trim with
  mpdecimate, then check a contact sheet.
- `asc.py upload-review-attachment <file.mp4> <versionId>`

### Header + search-results art (Asset Library) 🌐
- Header 3840×1646 (safe area centred 1646×661), search results 3840×2560 (safe area
  2168×1030 at 836,765), PNG without alpha.
- The benefit must be stated plainly in the search art (e.g. "Your floor plan, as a 3D home,
  then shake your phone for a new style").
- One calm continuous background, real app renders, **no product cut-outs** (they leave
  white fringes) and no floating objects.
- No public API: upload in Chrome. **Check the language selector label before each upload.**
  The menu lists localized languages above unlocalized ones, and one click too low *adds a
  new language* (Catalan got added by accident once). Delete stray localizations with
  asc.py.

### Custom product pages + A/B
- Custom product pages (up to 35): one per screenshot set, each with its own URL for ads.
  asc.py `appCustomProductPages` → versions → localizations → screenshot sets.
- **Product Page Optimization** (real A/B, ≤ 3 treatments) only opens once the app is live,
  so it goes in `POST_LAUNCH.md` with the exact sets to test.

---

## Offers and retention

| Offer | API | Notes |
|---|---|---|
| Intro offer / free trial | `superwall asc offers create` | on the default and tested yearly products (not the retention product); all territories; the paywall reads eligibility |
| Price-test products | `superwall asc subscriptions create` per price, same group | `.yearly.b`, `.yearly.c`; all go to review with v1 ([monetization.md step 4b](monetization.md#step-4b-experiments-from-day-one-and-the-retention-product)) |
| Retention product | `superwall asc subscriptions create` | `.yearly.retention` at the chosen price (e.g. $9.99), lowest group level, no trial; shown only on retention surfaces |
| Promotional offers | asc.py `POST /v1/subscriptionPromotionalOffers` | signed with the In-App Purchase key that RevenueCat holds; used in the cancel flow and the exit paywall |
| Offer codes | asc.py `POST /v1/subscriptionOfferCodes` → `subscriptionOfferCodeCustomCodes` or `…OneTimeUseCodes` | write codes to `store/OFFER_CODES.md` (git-ignored) |
| Win-back offers | asc.py `POST /v1/winBackOffers` | eligibility: paid duration, time since lapse, wait between offers; priority HIGH for the best one. Default offer: first year at the retention price |
| Retention Messaging | Apple's Retention Messaging API (preview) + a Worker endpoint | if the account doesn't have access, write the endpoint and a `POST_LAUNCH.md` step; don't fail the run |
| In-app cancel flow | RC Customer Center with a promo offer | `revenuecat:revenuecat-customer-center` |
| Exit offer | Superwall placement on `transaction_abandon` → discounted paywall | product = the promotional offer or a cheaper SKU |

API paths and payloads drift, so check them against Apple's current docs (`WebFetch
developer.apple.com/documentation/appstoreconnectapi/...`) before the first call. A 4xx
response is information, not a reason to switch to Chrome.

---

## Final review audit (phase 10, always)

Run before the final report, and fix what fails:

- [ ] Fresh install of the **release** build works start to finish offline-tolerant
- [ ] Paywall: price, period, trial, auto-renew text, Restore, Terms, Privacy; the selected
      plan is the one bought (sandbox or StoreKit config)
- [ ] Permission priming says "Continue" and always reaches the system prompt
- [ ] AI consent names the provider before the first upload; there's a Settings switch
- [ ] No unused permission keys (Face ID from expo-secure-store, local network from
      expo-dev-client, which must never ship). `NSPhotoLibraryAddUsageDescription` is
      present if any share sheet exists (otherwise "Save Image" crashes)
- [ ] App Privacy ⇔ privacy manifest ⇔ policy ⇔ SDK list all agree; ATT shown only if
      tracking SDKs are present
- [ ] Icon 1024, no alpha; screenshots match the current UI
- [ ] Review notes current; reviewer video attached; contact filled
- [ ] Subscriptions "Ready to Submit", attached to the version
- [ ] Duplicate-app risk (4.3) checked against the account's other apps
- [ ] Kids category is not used if any analytics/ads SDK is present (1.3)
