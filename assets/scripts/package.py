#!/usr/bin/env python3
"""Build a shareable copy of the skill and prove it contains nothing personal.

    package.py scan                 # privacy scan only (exit 1 on any hit)
    package.py zip [OUT_DIR]        # scan, then write one-shot-app-<date>.zip (default: ~/Desktop)
    package.py export DIR           # scan, then copy a clean tree to DIR (e.g. a git repo to push)

The scan looks for every value in YOUR data home (~/.one-shot-app/config.json, profile.json),
plus emails, phone numbers, /Users/<name> paths, .p8 files and key-shaped strings, in every
file that would be shared. Data-home files and symlinks are never included.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import shutil
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402

EXCLUDE_NAMES = {"config.json", "profile.json", ".DS_Store", "__pycache__", ".git", "dist"}
EXCLUDE_SUFFIX = {".p8", ".pyc"}
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"\+\d{2}[\d \-]{8,}"),
    "home path": re.compile(r"/Users/(?!<)[A-Za-z0-9._-]+"),
    "google key": re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    "revenuecat key": re.compile(r"\b(sk|appl|goog)_[A-Za-z0-9]{16,}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
ALLOWED = {"noreply@anthropic.com", "support@<app-domain>", "a@b.de"}
GENERIC = {"https://api.revenuecat.com/v2", "Copilot", "iphoneos iphonesimulator", "~/Documents", "Deutschland",
           "Expo / React Native", "English + German", "German", "weekly + yearly, 3-day trial", "iPhone 17 Pro"}


def shared_files():
    for p in sorted(paths.SKILL_DIR.rglob("*")):
        rel = p.relative_to(paths.SKILL_DIR)
        if any(part in EXCLUDE_NAMES for part in rel.parts) or p.suffix in EXCLUDE_SUFFIX or p.is_symlink():
            continue
        if p.is_file():
            yield p, rel


def personal_values():
    vals = set()

    def walk(o, key=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if not k.startswith("_"):
                    walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str):
            v = o.strip()
            if len(v) >= 5 and v not in GENERIC and not v.startswith(("http://", "https://api.", "gemini-")):
                vals.add(v)
                if " " in v and key in ("fullName", "name"):
                    vals.update(w for w in v.split() if len(w) >= 4)

    # only identifying sections; menu answers, preferences and defaults are generic labels
    keep = {"developer", "appStoreConnect", "revenuecat", "gemini", "netlify", "supabase", "cloudflare",
            "identity", "imprint", "reviewContact", "accounts"}
    for f in (paths.CONFIG, paths.PROFILE):
        if f.exists():
            try:
                d = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            for k in keep & d.keys():
                walk(d[k], k)
            for app in (d.get("apps") or {}).get("items", []):
                for k in ("name", "bundle", "dir", "ascAppId"):
                    if app.get(k):
                        walk(app[k], "name" if k == "name" else k)
    return vals


def scan() -> int:
    vals = personal_values()
    hits = []
    for p, rel in shared_files():
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for v in vals:
            if rel.name == "LICENSE" and rel.parent == pathlib.Path("."):
                continue  # the author credit is intentional
            if re.search(r"(?<![\w])" + re.escape(v) + r"(?![\w])", text, re.IGNORECASE):
                hits.append((str(rel), "your data", v[:3] + "…"))
        for name, rx in PATTERNS.items():
            for m in rx.findall(text):
                m = m if isinstance(m, str) else m[0]
                if m not in ALLOWED and not m.startswith("/Users/<"):
                    hits.append((str(rel), name, m[:4] + "…"))
    for rel, kind, sample in sorted(set(hits)):
        print(f"  ✗ {rel}: {kind} ({sample})")
    n = len(set(hits))
    print(f"{n} hit(s) in {sum(1 for _ in shared_files())} files." if n else "Clean: no personal data in the shared files.")
    return 1 if n else 0


def main():
    a = sys.argv[1:] or ["scan"]
    if scan() and a[0] != "scan-only":
        raise SystemExit("Fix the hits above before sharing.")
    if a[0] == "zip":
        out = pathlib.Path(a[1] if len(a) > 1 else "~/Desktop").expanduser()
        out.mkdir(parents=True, exist_ok=True)
        z = out / f"one-shot-app-{dt.date.today().isoformat()}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for p, rel in shared_files():
                zf.write(p, pathlib.Path("one-shot-app") / rel)
        print("wrote", z)
    elif a[0] == "export":
        dest = pathlib.Path(a[1]).expanduser()
        for p, rel in shared_files():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest / rel)
        print("exported to", dest)


if __name__ == "__main__":
    main()
