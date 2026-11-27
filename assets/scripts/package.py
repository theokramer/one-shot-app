#!/usr/bin/env python3
"""Check for likely private data and build a filtered source package.

    package.py scan                 # current files; nonzero on findings
    package.py scan --history       # also reachable Git content and author metadata
    package.py zip [OUT_DIR]        # current-file scan, then a source-only zip
    package.py export DIR           # current-file scan, then export to an empty directory

Checks are heuristic, not proof of anonymity. Review prose and media manually.
Known identity values are read locally from ONE_SHOT_HOME, never printed.
History checks cover available refs, not deleted remote refs, forks or caches.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import paths  # noqa: E402

PRIVATE_NAMES = {"config.json", "profile.json", "secrets.json", "learnings.local.md",
                 ".one-shot-app", "review_information", "frames", "recordings", "storyboard.json"}
EXCLUDE_NAMES = PRIVATE_NAMES | {".DS_Store", "__pycache__", ".git", "dist", "node_modules", ".venv", "venv"}
PRIVATE_SUFFIXES = {".p8", ".pem", ".key", ".p12", ".pfx", ".mobileprovision", ".cer"}
SOURCE_SUFFIXES = {".md", ".py", ".sh", ".swift", ".ts", ".tsx", ".template", ".yml", ".yaml"}
ROOT_FILES = {"README.md", "SKILL.md", "LICENSE", ".gitignore", "config.example.json", "profile.example.json"}
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
    "phone": re.compile(r"(?<!\w)\+\d[\d ()-]{8,}\d"),
    "home path": re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._-]+"),
    "Windows home path": re.compile(r"[A-Z]:\\Users\\[A-Za-z0-9._-]+", re.I),
    "Google key": re.compile(r"\bAIza[0-9A-Za-z_-]{20,}"),
    "service key": re.compile(r"\b(?:sk|appl|goog|sbp|sb_secret)_[A-Za-z0-9_-]{16,}"),
    "OpenAI key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "AWS key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{15,}"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
ALLOWED_EMAILS = {"noreply@anthropic.com", "a@b.de"}
GENERIC = {"https://api.revenuecat.com/v2", "Copilot", "iphoneos iphonesimulator", "~/Documents", "Deutschland",
           "Expo / React Native", "English + German", "German", "weekly + yearly, 3-day trial", "iPhone 17 Pro"}


def private_path(rel):
    return any(p in PRIVATE_NAMES or p == ".env" or p.startswith(".env.") for p in rel.parts) or rel.suffix.lower() in PRIVATE_SUFFIXES


def excluded(rel):
    return private_path(rel) or any(p in EXCLUDE_NAMES for p in rel.parts) or rel.suffix == ".pyc"


def linked(path):
    rel = path.relative_to(paths.SKILL_DIR)
    return any((paths.SKILL_DIR.joinpath(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts) + 1))


def in_data_home(path):
    return path.resolve().is_relative_to(paths.HOME.resolve())


def shared_files():
    """Allow only skill source, never arbitrary local files, media or private exports."""
    for directory, dirs, files in os.walk(paths.SKILL_DIR, followlinks=False):
        base = pathlib.Path(directory)
        dirs[:] = [d for d in dirs if not excluded((base / d).relative_to(paths.SKILL_DIR))
                   and not (base / d).is_symlink() and not in_data_home(base / d)]
        for name in sorted(files):
            p = base / name
            rel = p.relative_to(paths.SKILL_DIR)
            if excluded(rel) or linked(p) or in_data_home(p):
                continue
            if str(rel) in ROOT_FILES or (len(rel.parts) > 1 and rel.parts[0] in {"assets", "references"} and p.suffix in SOURCE_SUFFIXES):
                yield p, rel


def personal_values():
    vals = set()

    def walk(obj, key=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if not k.startswith("_"):
                    walk(v, k)
        elif isinstance(obj, list):
            for v in obj:
                walk(v, key)
        elif isinstance(obj, str):
            value = obj.strip()
            if len(value) >= 4 and value not in GENERIC and not value.startswith("gemini-"):
                vals.add(value)
                if key in {"fullName", "name"}:
                    vals.update(w for w in value.split() if len(w) >= 4)

    keep = {"developer", "appStoreConnect", "revenuecat", "gemini", "netlify", "supabase", "cloudflare",
            "identity", "imprint", "reviewContact", "accounts"}
    for path in (paths.CONFIG, paths.PROFILE):
        if path.exists():
            data = json.loads(path.read_text())
            for key in keep & data.keys():
                walk(data[key], key)
            for app in (data.get("apps") or {}).get("items", []):
                for key in ("name", "bundle", "dir", "ascAppId"):
                    if app.get(key):
                        walk(app[key], "name" if key == "name" else key)
    return vals


def git(*args):
    return subprocess.check_output(["git", "-C", str(paths.SKILL_DIR), *args], stderr=subprocess.PIPE)


def is_repository():
    try:
        return pathlib.Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() == paths.SKILL_DIR.resolve()
    except (OSError, subprocess.CalledProcessError):
        return False


def email_example(value):
    domain = value.rsplit("@", 1)[-1].lower()
    return value in ALLOWED_EMAILS or domain in {"example.com", "example.org", "example.net"} or domain.endswith((".invalid", ".example"))


def inspect_text(label, data, vals, hits):
    try:
        text = data.decode("utf-8")
        if "\0" in text:
            raise ValueError("binary")
    except (UnicodeDecodeError, ValueError):
        hits.add((label, "non-text content: manual privacy review required"))
        return
    for value in vals:
        if re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text, re.I):
            hits.add((label, "known personal value (redacted)"))
    for kind, pattern in PATTERNS.items():
        if any(not (kind == "email" and email_example(m.group())) for m in pattern.finditer(text)):
            hits.add((label, kind + " (redacted)"))


def scan(history=False):
    hits = set()
    try:
        vals = personal_values()
        files = {str(rel): p for p, rel in shared_files()}
        repo = is_repository()
        if repo:
            for raw in git("ls-files", "-z").split(b"\0"):
                if not raw:
                    continue
                rel = pathlib.Path(os.fsdecode(raw))
                if private_path(rel):
                    hits.add((str(rel), "private path is tracked; ignoring it does not untrack it"))
                    continue
                files[str(rel)] = paths.SKILL_DIR / rel
        for label, path in files.items():
            if linked(path) or in_data_home(path):
                hits.add((label, "tracked link or data-home file requires removal"))
            elif path.exists():
                inspect_text(label, path.read_bytes(), vals, hits)
        if history:
            if not repo:
                hits.add(("Git history", "unavailable: this is not a Git repository"))
            else:
                if git("rev-parse", "--is-shallow-repository").strip() == b"true":
                    hits.add(("Git history", "incomplete: fetch full history before publishing"))
                blobs = {}
                for commit in git("rev-list", "--all").decode().splitlines():
                    label = f"commit {commit[:12]} metadata"
                    metadata = git("show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%B", commit)
                    inspect_text(label, metadata, vals, hits)
                    names = metadata.decode().splitlines()
                    if names[0] != "one-shot-app contributors" or names[2] != "one-shot-app contributors":
                        hits.add((label, "author/committer identity: review required"))
                    for entry in git("ls-tree", "-rz", commit).split(b"\0"):
                        if not entry:
                            continue
                        meta, raw = entry.split(b"\t", 1)
                        mode, kind, oid = meta.decode().split()
                        rel = pathlib.Path(os.fsdecode(raw))
                        where = f"{commit[:12]}:{rel}"
                        if private_path(rel) or mode == "120000":
                            hits.add((where, "private path or symlink in history"))
                        if kind == "blob":
                            blobs.setdefault(oid, where)
                for oid, label in blobs.items():
                    inspect_text(label, git("cat-file", "blob", oid), vals, hits)
    except (OSError, ValueError, subprocess.CalledProcessError):
        # Do not include exception text: it may contain private JSON or filesystem paths.
        print("Scan failed: a required file, profile or Git object could not be read. No package created.")
        return 1
    for label, kind in sorted(hits):
        print(f"  ! {label}: {kind}")
    scope = "current files and available Git history" if history else "current files (Git history not checked)"
    print(f"Checked {len(files)} current files; {len(hits)} finding(s) in {scope}.")
    print("Heuristic check only: review prose, identifiers and media manually before publishing.")
    return 1 if hits else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("scan", "zip", "export"), nargs="?", default="scan")
    parser.add_argument("destination", nargs="?")
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    if args.command == "export" and not args.destination:
        parser.error("export requires an empty destination directory")
    if scan(args.history):
        raise SystemExit(1)
    if args.command == "scan":
        return
    dest = pathlib.Path(args.destination or "~/Desktop").expanduser().resolve()
    if dest.is_relative_to(paths.SKILL_DIR.resolve()):
        raise SystemExit("Choose a destination outside the skill directory")
    if args.command == "export" and dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise SystemExit("Export destination must be empty; stale files could contain private data")
    dest.mkdir(parents=True, exist_ok=True)
    files = list(shared_files())
    if args.command == "zip":
        archive = dest / f"one-shot-app-{dt.date.today().isoformat()}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path, rel in files:
                zf.write(path, pathlib.Path("one-shot-app") / rel)
        print("Wrote source archive")
    else:
        for path, rel in files:
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest / rel)
        print("Exported source files")


if __name__ == "__main__":
    main()
