#!/usr/bin/env python3
"""Phase 4 gate: prove every tool, login and key the ticked modules need.

The failure this prevents: the run gets two hours in, hits a missing login or key, and
stops while the user is away. Service checks are read-only and limited to explicitly selected modules.

    preflight.py --modules core,asc,revenuecat,superwall,cloudflare --stack expo
    preflight.py --modules core           # local checks only

Modules: core, github, asc, revenuecat, superwall, cloudflare, supabase, gemini, netlify,
         meta, tiktok, localization   ("all" = every module)
Exit 0 = the run can proceed unattended. Otherwise it prints, grouped, what to install
(Claude may run these after an OK), what to log into (the user runs these), and what
must happen in Chrome during the attended block.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.error
import urllib.request

import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
import paths  # noqa: E402
from http_safety import open_request  # noqa: E402

SKILL_DIR = paths.SKILL_DIR
CONFIG = paths.CONFIG
EXAMPLE = paths.CONFIG_EXAMPLE
ALL = ["core", "github", "asc", "revenuecat", "superwall", "cloudflare", "supabase",
       "gemini", "netlify", "meta", "tiktok", "localization"]

OK, WARN, FAIL, INFO = "ok", "warn", "fail", "info"
results: list[tuple[str, str, str, str, str]] = []  # state, label, detail, kind, remedy


def record(state, label, detail="", kind="", remedy=""):
    """kind: install | login | config | chrome | user, which groups remedies in the report."""
    results.append((state, label, detail, kind, remedy))


def run(cmd, timeout=60, cwd=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return 1, str(exc)


def need_tool(tool, install, label=None):
    if shutil.which(tool):
        record(OK, label or tool)
        return True
    record(FAIL, label or tool, "not installed", "install", install)
    return False


def pymod(mod, pkg):
    try:
        __import__(mod)
        record(OK, f"python {pkg}")
    except ImportError:
        record(FAIL, f"python {pkg}", "not importable", "install",
               f"python3 -m pip install --user --break-system-packages {pkg}")


# --- core --------------------------------------------------------------------

def check_core(cfg, stack):
    need_tool("xcodebuild", "Install Xcode, then: sudo xcode-select -s /Applications/Xcode.app", "xcode")
    need_tool("git", "xcode-select --install")
    need_tool("python3", "brew install python")
    need_tool("ffmpeg", "brew install ffmpeg")
    pymod("PIL", "Pillow")
    if stack == "expo":
        if need_tool("node", "brew install node   (Node 20+)"):
            code, out = run(["node", "--version"])
            major = out.lstrip("v").split(".")[0]
            if code == 0 and major.isdigit() and int(major) < 20:
                record(FAIL, "node version", out, "install", "Install Node 20+ (nvm install 22)")
        need_tool("npx", "comes with node")
        need_tool("pod", "brew install cocoapods", "cocoapods")
    free = shutil.disk_usage("/").free / 1e9
    if free < 8:
        record(FAIL, "disk", f"{free:.1f} GB free", "user",
               "Free space: clear ~/Library/Developer/Xcode/DerivedData and old recordings (archives need ~10 GB)")
    elif free < 15:
        record(WARN, "disk", f"{free:.1f} GB free", "user", "Tight for archive + videos; clear DerivedData")
    else:
        record(OK, "disk", f"{free:.0f} GB free")


# --- services ----------------------------------------------------------------

def check_github(cfg):
    if not need_tool("gh", "brew install gh"):
        return
    code, out = run(["gh", "auth", "status"])
    if code != 0:
        record(FAIL, "github login", "not logged in", "login", "gh auth login")
        return
    record(OK, "github login", "authenticated")
    if cfg is not None and not (cfg.get("developer") or {}).get("githubOwner"):
        record(FAIL, "config developer.githubOwner", "empty", "config", "Your GitHub user or org")


def asc_jwt(cfg):
    import jwt  # noqa: PLC0415
    c = cfg["appStoreConnect"]
    now = int(time.time())
    return jwt.encode({"iss": c["issuerId"], "iat": now, "exp": now + 900, "aud": "appstoreconnect-v1"},
                      pathlib.Path(os.path.expanduser(c["privateKeyPath"])).read_text(),
                      algorithm="ES256", headers={"kid": c["keyId"], "typ": "JWT"})


def check_asc(cfg, check_proxy=False):
    if cfg is None:
        return
    c = cfg.get("appStoreConnect") or {}
    for f in ("keyId", "issuerId", "privateKeyPath"):
        if not c.get(f):
            record(FAIL, f"config appStoreConnect.{f}", "empty", "config",
                   "ASC → Users and Access → Integrations → Team key with App Manager access")
    p8 = pathlib.Path(os.path.expanduser(c.get("privateKeyPath", "") or "/nonexistent"))
    if not p8.exists():
        record(FAIL, "asc .p8", "file not found at privateKeyPath", "config", "Point privateKeyPath at AuthKey_*.p8")
        return
    if any((parent / ".git").exists() for parent in p8.resolve().parents):
        record(FAIL, "asc .p8", "lives inside a git repo", "config", "Move it outside any repository")
        return
    try:  # the direct API, which asc.py uses
        req = urllib.request.Request("https://api.appstoreconnect.apple.com/v1/apps?limit=1",
                                     headers={"Authorization": "Bearer " + asc_jwt(cfg)})
        with open_request(req, timeout=30) as r:
            json.load(r)
        record(OK, "asc api (.p8)", "key accepted")
    except urllib.error.HTTPError as exc:
        record(FAIL, "asc api (.p8)", f"HTTP {exc.code}", "config", "Key revoked, or wrong issuer/key id")
    except ImportError:
        record(FAIL, "asc api (.p8)", "PyJWT missing, so the key can't be tested", "install",
               "python3 -m pip install --user --break-system-packages PyJWT cryptography")
    except Exception as exc:  # noqa: BLE001
        record(WARN, "asc api (.p8)", str(exc)[:80])
    if check_proxy:
        code, out = run(["superwall", "asc", "get", "/v1/apps?limit=1", "--json"], timeout=90)
        record(OK if code == 0 and '"data"' in out else FAIL, "asc proxy",
               "checked existing connection", "login",
               "Use the direct API or connect the proxy yourself after approving the transfer")
    if not shutil.which("fastlane"):
        record(WARN, "fastlane", "not installed (bulk metadata/screenshots)", "install", "brew install fastlane")
    record(INFO, "asc app record", "created in the attended block", "user",
           "rc setup apple <rc-app-id> --project-id <id>   (Apple ID + 2FA, typed by you)")


def check_revenuecat():
    if not need_tool("rc", "brew install revenuecat/tap/rc   (or: npx @revenuecat/cli)", "rc cli"):
        return
    _, out = run(["rc", "auth", "status", "--json", "--no-input"], timeout=30)
    try:
        d = json.loads(out)
        authed = bool(d.get("data", d).get("authenticated"))
    except (json.JSONDecodeError, AttributeError):
        authed = False
    record(OK if authed else FAIL, "rc login", "authenticated" if authed else "not logged in", "login",
           "rc auth login")


def check_superwall():
    if not need_tool("superwall", "npm i -g superwall", "superwall cli"):
        return
    code, out = run(["superwall", "whoami"])
    ok = code == 0 and ("session" in out.lower() or "@" in out)
    record(OK if ok else FAIL, "superwall login", "ok" if ok else "not logged in", "login", "superwall login")


def check_cloudflare():
    if not shutil.which("npx"):
        record(FAIL, "npx", "not installed", "install", "brew install node")
        return
    _, out = run(["npx", "-y", "wrangler", "whoami"], timeout=120)
    low = out.lower()
    ok = "you are logged in" in low
    record(OK if ok else FAIL, "wrangler login", "ok" if ok else "not logged in", "login", "npx wrangler login")


def check_supabase(cfg):
    tok = ((cfg or {}).get("supabase") or {}).get("accessToken")
    if shutil.which("supabase"):
        code, _ = run(["supabase", "projects", "list"], timeout=60)
        record(OK if code == 0 else FAIL, "supabase login", "", "login", "supabase login")
    elif tok:
        record(OK, "supabase token", "in config")
    else:
        record(FAIL, "supabase", "no CLI and no token", "install",
               "brew install supabase/tap/supabase && supabase login   (or authorize the Supabase MCP via /mcp)")


def check_gemini(cfg):
    key = ((cfg or {}).get("gemini") or {}).get("apiKey", "")
    if not key:
        record(WARN, "gemini", "no key; icon/translation fall back to local", "config",
               "Optional: https://aistudio.google.com/apikey, then: setup.py secret gemini.apiKey")
        return
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models",
                                 headers={"x-goog-api-key": key})
    try:
        with open_request(req, timeout=30) as resp:
            json.load(resp)
        record(OK, "gemini", "key accepted (spend cap shows on the first generation)")
    except urllib.error.HTTPError as exc:
        hint = ("Spend cap reached: raise it in Google Cloud billing (a Gemini subscription does not fund the API)"
                if exc.code == 429 else "Regenerate the key at aistudio.google.com/apikey")
        record(FAIL, "gemini", f"HTTP {exc.code}", "user", hint)
    except Exception as exc:  # noqa: BLE001
        record(WARN, "gemini", str(exc)[:80])


def check_netlify(cfg):
    token = ((cfg or {}).get("netlify") or {}).get("authToken", "")
    if not token:
        record(FAIL, "netlify", "no token", "config", "Netlify → User settings → Applications → token (or use Cloudflare)")
        return
    req = urllib.request.Request("https://api.netlify.com/api/v1/user", headers={"Authorization": f"Bearer {token}"})
    try:
        with open_request(req, timeout=30):
            record(OK, "netlify", "token accepted")
    except Exception as exc:  # noqa: BLE001
        record(FAIL, "netlify", str(exc)[:80], "config", "Regenerate the token")


def check_profile(mods):
    """The library: personal data the run must not have to ask for mid-run."""
    script = SKILL_DIR / "assets" / "scripts" / "profile.py"
    purposes = ["website", "review"] + [m for m in ("meta", "tiktok") if m in mods]
    code, out = run(["python3", str(script), "missing", "--for", ",".join(purposes)])
    if code == 0:
        record(OK, "library (profile.json)", "imprint, review contact" + (", ad accounts" if len(purposes) > 2 else ""))
        return
    gaps: dict[str, list[str]] = {}
    for line in out.splitlines():
        purpose, _, field = line.partition(": ")
        gaps.setdefault(purpose, []).append(field.replace("imprint.", "").replace("reviewContact.", ""))
    for purpose, fields in gaps.items():
        if purpose in ("meta", "tiktok"):
            record(INFO, f"library {purpose}", "account id unknown (found in the attended block, then saved)")
        else:
            record(FAIL, f"library {purpose}", "missing: " + ", ".join(fields), "user",
                   "Ask once for the missing imprint / review-contact data (intake step 3), then "
                   "profile.py set … && profile.py confirm imprint")


def check_tools_choice():
    """Round-T tools: are the chosen ones installed? (MCP connection itself: ToolSearch in-session.)"""
    try:
        td = json.loads(paths.PROFILE.read_text()).get("toolDefaults", {}) if paths.PROFILE.exists() else {}
    except json.JSONDecodeError:
        td = {}
    chosen = set(td.get("research", []) + td.get("design", []) + td.get("images", []) + [td.get("music", "")])
    if not chosen - {""}:
        record(INFO, "tools", "not chosen yet (menu round T)")
        return
    home = pathlib.Path.home()
    skills = {d.name for d in (home / ".claude" / "skills").glob("*")}
    plugins = {d.name for d in (home / ".claude" / "plugins" / "cache").glob("*/*")}
    checks = {
        "Mobbin MCP": ("mobbin" in plugins, "Install the Mobbin plugin and authorize it via /mcp, or drop it in round T"),
        "Appllama MCP": ("appllama-usage" in skills, "Add the Appllama MCP + appllama-usage skill and authorize via /mcp, or drop it"),
        "appllama-app-design-skill": ("appllama-app-design-skill" in skills, "Install appllama-app-design-skill, or pick 'Built-in rules only'"),
        "frontend-design": ("frontend-design" in skills, "Install the frontend-design skill, or drop it"),
        "Sunra": (bool(shutil.which("sunra")), "Install the sunra CLI and run `sunra login`, or drop it"),
        "Local only": (pathlib.Path("/Applications/Blender.app").exists() or bool(shutil.which("blender")),
                       "Optional: install Blender for 3D renders (Pillow/ffmpeg still work without it)"),
        "ACE-Step (local)": ("ace-step-song" in skills, "Install an ace-step-song skill + ACE-Step, or pick 'Silent'"),
    }
    for name in sorted(chosen - {""}):
        if name in checks:
            ok, fix = checks[name]
            state = OK if ok else (WARN if name == "Local only" else FAIL)
            record(state, f"tool {name}", "installed" if ok else "not found", "install", "" if ok else fix)
        elif name == "Gemini API":
            check_gemini(json.loads(paths.CONFIG.read_text()) if paths.CONFIG.exists() else None)


def check_chrome(mods):
    sites = []
    if "meta" in mods:
        sites.append("developers.facebook.com + business.facebook.com")
    if "tiktok" in mods:
        sites.append("ads.tiktok.com")
    if "asc" in mods:
        sites.append("appstoreconnect.apple.com (App Privacy, Asset Library, compliance forms)")
    for s in sites:
        record(INFO, "chrome sign-in", s, "chrome",
               f"Sign in to {s} in Chrome with the Claude extension connected; Claude checks it in the attended block")


# --- report ------------------------------------------------------------------

def report() -> int:
    width = max(len(r[1]) for r in results) + 2
    icon = {OK: "✓", WARN: "!", FAIL: "✗", INFO: "·"}
    for state, label, detail, _, _ in results:
        print(f"  {icon[state]} {label.ljust(width)}{detail}")
    fails = [r for r in results if r[0] == FAIL]
    groups = {"install": "Install (Claude can run these after your OK)",
              "login": "Log in (you run these; they open a browser or ask for a code)",
              "config": f"Fill in {paths.CONFIG}  (python3 <skill>/assets/scripts/setup.py helps)",
              "user": "Needs you",
              "chrome": "Attended Chrome block"}
    print()
    for kind, title in groups.items():
        items = [r for r in results if r[3] == kind and r[0] in (FAIL, WARN, INFO)]
        if items:
            print(title + ":")
            seen = set()
            for st, _label, _detail, _, remedy in items:
                if remedy and remedy not in seen:
                    seen.add(remedy)
                    print(f"  {'✗' if st == FAIL else '·'} {remedy}")
            print()
    if fails:
        print(f"{len(fails)} blocker(s). The run cannot proceed unattended until these are fixed.")
        return 1
    print("Ready. Every tool, login and key for the selected modules is verified.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--modules", default="core")
    ap.add_argument("--stack", choices=["expo", "swiftui"], default="expo")
    ap.add_argument("--check-asc-proxy", action="store_true", help="read-only check of an existing approved Superwall proxy connection")
    a = ap.parse_args()
    mods = set(ALL if a.modules == "all" else [m.strip() for m in a.modules.split(",") if m.strip()])
    mods.add("core")

    for msg in paths.ensure_home():
        print("·", msg)
    cfg = None
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
        except json.JSONDecodeError as exc:
            record(FAIL, "config.json", f"invalid JSON: {exc}", "config", "Fix the syntax")
    else:
        if EXAMPLE.exists():
            shutil.copy(EXAMPLE, CONFIG)
        record(FAIL, "config.json", "created from the example", "config", f"Fill the required fields in {CONFIG}")

    print(f"one-shot-app preflight  modules={','.join(sorted(mods))}  stack={a.stack}\n")
    check_core(cfg, a.stack)
    checks = {"github": lambda: check_github(cfg), "asc": lambda: check_asc(cfg, a.check_asc_proxy),
              "revenuecat": check_revenuecat, "superwall": check_superwall,
              "cloudflare": check_cloudflare, "supabase": lambda: check_supabase(cfg),
              "gemini": lambda: check_gemini(cfg), "netlify": lambda: check_netlify(cfg)}
    for name, fn in checks.items():
        if name in mods:
            fn()
    check_profile(mods)
    check_tools_choice()
    check_chrome(mods)
    raise SystemExit(report())


if __name__ == "__main__":
    main()
