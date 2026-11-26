#!/usr/bin/env python3
"""First-run setup and account config for one-shot-app.

    setup.py status                      # first run? which config fields are still empty (no values printed)
    setup.py init                        # create ~/.one-shot-app/ (migrates an old in-skill config)
    setup.py set developer.appleTeamID=ABCDE12345 projects.parentDir=~/Developer ...   # non-secret values
    setup.py secret gemini.apiKey        # hidden prompt; run by the USER in their own terminal
    setup.py detect                      # facts the skill can pre-fill as options (gh login, Xcode, …)

Secrets are only ever typed by the user into the hidden prompt, never into chat, and
never printed back. Values go to ~/.one-shot-app/config.json (chmod 600).
"""
from __future__ import annotations

import getpass
import json
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402

SECRETS = {"gemini.apiKey", "revenuecat.apiV2Key", "netlify.authToken", "supabase.accessToken"}
# what a first run needs before the menu (the rest is per module and checked by preflight)
CORE = ["developer.appleTeamID", "developer.bundleIdPrefix", "developer.githubOwner",
        "appStoreConnect.keyId", "appStoreConnect.issuerId", "appStoreConnect.privateKeyPath"]
OPTIONAL = ["developer.appleAccountEmail", "projects.parentDir", "cloudflare.workersSubdomain", "gemini.apiKey"]


def load():
    paths.ensure_home()
    return json.loads(paths.CONFIG.read_text())


def save(c):
    paths.CONFIG.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
    paths.CONFIG.chmod(0o600)


def dig(c, path):
    for k in path.split("."):
        if not isinstance(c, dict):
            return None
        c = c.get(k)
    return c


def put(c, path, v):
    ks = path.split(".")
    for k in ks[:-1]:
        c = c.setdefault(k, {})
    c[ks[-1]] = v


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return p.stdout.strip() if p.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def status():
    first = not paths.CONFIG.exists() or not paths.PROFILE.exists()
    c = load()
    missing = [f for f in CORE if not dig(c, f)]
    opt = [f for f in OPTIONAL if not dig(c, f)]
    p8 = dig(c, "appStoreConnect.privateKeyPath")
    if p8 and not pathlib.Path(p8).expanduser().exists():
        missing.append("appStoreConnect.privateKeyPath (file not found)")
    print(f"data home   {paths.HOME}")
    print(f"first run   {'yes' if first or missing else 'no'}")
    print("missing     " + (", ".join(missing) if missing else "nothing"))
    print("optional    " + (", ".join(opt) if opt else "all set"))
    raise SystemExit(1 if missing else 0)


def detect():
    """Facts to turn into pre-filled options, so the user clicks instead of typing."""
    gh = run(["gh", "api", "user", "--jq", ".login"])
    orgs = run(["gh", "api", "user/orgs", "--jq", ".[].login"]).split()
    git_email = run(["git", "config", "--global", "user.email"])
    git_name = run(["git", "config", "--global", "user.name"])
    dirs = [d for d in ("~/Documents", "~/Developer", "~/Projects", "~/code") if pathlib.Path(d).expanduser().is_dir()]
    out = {
        "githubLogin": gh, "githubOrgs": orgs,
        "bundlePrefixSuggestions": [f"com.{gh.lower()}"] + [f"com.{o.lower()}" for o in orgs[:2]] if gh else [],
        "gitName": git_name, "gitEmail": git_email,
        "projectDirs": dirs,
        "xcode": bool(shutil.which("xcodebuild")),
        "tools": {t: bool(shutil.which(t)) for t in ("gh", "rc", "superwall", "fastlane", "ffmpeg", "node", "pod")},
    }
    print(json.dumps(out, indent=1))


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, a = a[0], a[1:]
    if cmd == "init":
        for m in paths.ensure_home() or ["already set up at " + str(paths.HOME)]:
            print(m)
    elif cmd == "status":
        status()
    elif cmd == "detect":
        detect()
    elif cmd == "set":
        c = load()
        for kv in a:
            k, v = kv.split("=", 1)
            if k in SECRETS:
                raise SystemExit(f"{k} is a secret: the user runs `setup.py secret {k}` in their own terminal")
            put(c, k, str(pathlib.Path(v).expanduser()) if k.endswith(("Path", "parentDir")) and v.startswith("~") else v)
        save(c)
        print("saved", ", ".join(kv.split("=", 1)[0] for kv in a))
    elif cmd == "secret":
        k = a[0]
        if not sys.stdin.isatty():
            raise SystemExit("run this in your own terminal: it asks with a hidden prompt")
        v = getpass.getpass(f"{k} (input hidden): ").strip()
        if not v:
            raise SystemExit("nothing entered, nothing saved")
        c = load()
        put(c, k, v)
        save(c)
        print(f"saved {k} to {paths.CONFIG}")
    else:
        raise SystemExit(f"unknown command {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
