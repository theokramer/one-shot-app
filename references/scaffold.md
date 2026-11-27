# Scaffold — repo and Xcode project

Goal of this phase: an empty-but-real app that launches in the simulator, with SPM
dependencies resolved, pushed to a GitHub repo. No features yet.

## Why there's no XcodeGen here

The project file is generated from a template in `assets/project/`. That template uses
`objectVersion = 77` with a `PBXFileSystemSynchronizedRootGroup`, which means **Xcode picks
up Swift files by folder membership**. You never edit the pbxproj to add a file. That
removes the single most fragile part of scripted iOS project generation and means no
XcodeGen or Tuist install is required.

The only reasons to touch the pbxproj after generation are: adding an SPM package, or
adding a build setting that feeds an `Info.plist` variable.

## Directory layout

```
<AppName>/
├── <AppName>.xcodeproj/
│   ├── project.pbxproj
│   └── xcshareddata/xcschemes/<AppName>.xcscheme     ← must be shared; CI needs it
├── <AppName>/
│   ├── <AppName>App.swift
│   ├── Assets.xcassets/
│   ├── Design/Theme.swift
│   ├── Features/<Feature>/…
│   ├── Model/
│   ├── Services/
│   └── Store/
├── Info.plist
├── Products.storekit
├── ci/ExportOptions.plist
├── docs/{SPEC.md,DESIGN.md}
├── .github/workflows/{ci.yml,app-store.yml}
├── .gitignore
└── README.md
```

`Features/` holds one folder per screen area. `Services/` holds anything that talks to the
outside world. `Store/` holds observable state owned by the app. Keep it that way — the
demo and screenshot phases both navigate by this structure.

## Generating the project

Copy each file from `assets/project/` and substitute the placeholders:

| Placeholder | Value | Appears in |
|---|---|---|
| `__APP_NAME__` | PascalCase target name, e.g. `Spotted` | project, scheme, Info.plist, workflows, Swift |
| `__DISPLAY_NAME__` | What appears under the icon, e.g. `MyApp` | Info.plist |
| `__UPPER_NAME__` | `__APP_NAME__` upper-snake-cased, e.g. `SPOTTED` — used for DEBUG env var names | `AppConfiguration.swift` |
| `__BUNDLE_ID__` | `<bundleIdPrefix>.<lowercase>` | project |
| `__TEAM_ID__` | `developer.appleTeamID` from config | project, ExportOptions |
| `__DEPLOYMENT_TARGET__` | `defaults.deploymentTarget`, default `17.0` | project |
| `__CATEGORY__` | `public.app-category.*` matching the app | Info.plist |
| `__REVENUECAT_PUBLIC_KEY__` | The `appl_…` SDK key from Phase 7 | `AppEntryPoint.swift` |
| `__SUPERWALL_PUBLIC_KEY__` | The `pk_…` SDK key from Phase 7 | `AppEntryPoint.swift` |
| `__WEBSITE_HOST__` | Marketing/privacy host, from Phase 9 | `AppConfiguration.swift` |

Files to generate: `project.pbxproj.template`, `xcscheme.template`, `Info.plist.template`,
`gitignore.template`, `ExportOptions.plist.template`.

The last three placeholders aren't known until Phases 7 and 9. Copy those Swift templates
in when you reach the phase that supplies the value, not during scaffolding — a file
carrying `__REVENUECAT_PUBLIC_KEY__` compiles fine and fails silently at runtime.

**Before every commit, assert no placeholder survived:**

```bash
grep -rn "__[A-Z_]\+__" --include='*.swift' --include='*.plist' \
  --include='*.pbxproj' --include='*.yml' . && echo "UNSUBSTITUTED" || echo clean
```

The scheme's `BlueprintIdentifier` must match the native target's UUID in the pbxproj
(`A1000000000000000000006` in the template). If you change UUIDs, change both.

### Permissions

Add a usage-description key to `Info.plist` for every permission in the spec, with a string
that says what the app does with it and, where true, that it stays on device. Apple rejects
vague strings. Only add keys for permissions the app actually requests — an unused
`NSCameraUsageDescription` is a review flag.

### Build settings as Info.plist variables

Anything environment-specific goes in as a build setting referenced from `Info.plist`:

```
// project.pbxproj, both Debug and Release
SUPABASE_URL = "https://xxxx.supabase.co";
SUPABASE_PUBLISHABLE_KEY = sb_publishable_xxxx;

// Info.plist
<key>__APP_NAME__SupabaseURL</key>
<string>$(SUPABASE_URL)</string>
```

and read it through an `AppConfiguration` enum that validates and fails closed — copy
`assets/swift/AppConfiguration.swift`. Publishable keys only. Nothing that would hurt if
someone unzipped the IPA.

## SPM dependencies

Already in the template:

- `https://github.com/superwall/Superwall-iOS` — `SuperwallKit`, upToNextMajor 4.0.0
- `https://github.com/RevenueCat/purchases-ios-spm.git` — `RevenueCat` + `RevenueCatUI`,
  upToNextMajor 5.0.0

To add another package you need four coordinated edits in the pbxproj:
`XCRemoteSwiftPackageReference` → `XCSwiftPackageProductDependency` → `PBXBuildFile` →
references in `packageReferences`, `packageProductDependencies`, and the frameworks phase.
Follow the existing RevenueCat entries exactly; they show all four.

Resolve before building:

```bash
xcodebuild -project <AppName>.xcodeproj -scheme <AppName> -resolvePackageDependencies
```

## Verify it builds — before anything else

```bash
xcodebuild -project <AppName>.xcodeproj -scheme <AppName> -configuration Debug \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO clean build 2>&1 | tail -30
```

A scaffold that doesn't compile is worse than no scaffold — every later error looks like a
feature bug. Fix it here.

## GitHub repo

```bash
git init -b main
git add -A
git commit -m "Scaffold <AppName> iOS project"
# Run after separate approvals for repo creation and the initial push.
gh repo create <githubOwner>/<kebab>-ios --private --source=. --remote=origin --push
```

Private by default. The user can flip it public; you shouldn't. If `gh` isn't authenticated,
Phase 4 should already have caught it.

`.gitignore` must cover `xcuserdata/`, `DerivedData/`, `.DS_Store`, `*.p8`, `.env`, and
`config.json`. Check that no credential is in the first commit before pushing:

```bash
git diff --cached --name-only | xargs grep -lE 'sk_|p8|BEGIN PRIVATE KEY|_secret' 2>/dev/null
```
