#!/usr/bin/env python3
"""Deploy the support/privacy site to Netlify.

App Review rejects a submission whose support or privacy URL does not resolve, so
these pages cannot be "written but not deployed". This uses Netlify's zip-deploy
endpoint directly — no CLI to install, no interactive login.

Ship only a reviewed public build directory. Updating an existing site requires its ID.

    netlify_deploy.py --dir AppStorePackage/website --site myapp-site --apply
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
import zipfile

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
import paths  # noqa: E402
from http_safety import open_request  # noqa: E402
CONFIG = paths.CONFIG
API = "https://api.netlify.com/api/v1"


def die(message: str):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def token() -> str:
    if not CONFIG.exists():
        die(f"{CONFIG} missing")
    value = (json.loads(CONFIG.read_text()).get("netlify") or {}).get("authToken", "")
    if not value:
        die("netlify.authToken is empty in config.json — Netlify → User settings → "
            "Applications → New access token")
    return value


def call(method: str, path: str, body=None, content_type="application/json"):
    data = body
    if content_type == "application/json" and body is not None:
        data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=data,
        headers={"Authorization": f"Bearer {token()}", "Content-Type": content_type},
    )
    try:
        with open_request(req, timeout=180) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        die(f"{method} {path} → HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}")


def find_site(name: str):
    for site in call("GET", "/sites?per_page=200") or []:
        if site.get("name") == name:
            return site
    return None


def zip_dir(directory: pathlib.Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        public_types = {".html", ".css", ".js", ".mjs", ".svg", ".png", ".jpeg", ".jpg",
                        ".webp", ".ico", ".woff", ".woff2", ".avif", ".txt", ".xml"}
        for path in sorted(directory.rglob("*")):
            rel = path.relative_to(directory)
            if path.is_symlink():
                die("Deploy directory contains a symlink. Review and rebuild it.")
            if any(part.startswith(".") or part in {"review_information", "frames", "recordings"} for part in rel.parts):
                die("Deploy directory contains a hidden or private path. Review and rebuild it.")
            if path.is_file():
                if path.suffix.lower() not in public_types:
                    die("Deploy directory contains an unexpected file type. Review and rebuild it.")
                archive.write(path, rel.as_posix())
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", required=True, help="directory to deploy")
    parser.add_argument("--site", required=True, help="Netlify site name (becomes <name>.netlify.app)")
    parser.add_argument("--apply", action="store_true", help="publish the approved public files")
    parser.add_argument("--site-id", help="required when updating an existing site")
    args = parser.parse_args()
    if not args.apply:
        parser.error("publishing requires --apply after approval")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.site):
        parser.error("enter the exact Netlify site name")
    if args.site_id and not re.fullmatch(r"[A-Za-z0-9_-]+", args.site_id):
        parser.error("invalid Netlify site ID")

    directory = pathlib.Path(args.dir).resolve()
    if not (directory / "index.html").exists():
        die(f"{directory}/index.html not found")

    payload = zip_dir(directory)
    if args.site_id:
        site = call("GET", f"/sites/{args.site_id}")
        if site.get("id") != args.site_id or site.get("name") != args.site:
            die("Existing site does not match the approved site name and ID")
        print(f"site   reused   {site['name']}")
    else:
        if find_site(args.site):
            die("Site already exists. Verify its ID and pass --site-id to update it.")
        site = call("POST", "/sites", {"name": args.site})
        print(f"site   created  {site['name']}")

    deploy = call("POST", f"/sites/{site['id']}/deploys", payload, content_type="application/zip")

    url = site.get("ssl_url") or site.get("url") or f"https://{args.site}.netlify.app"
    print(f"deploy {deploy.get('state', 'submitted')}  {len(payload)} bytes")
    print()
    print(json.dumps({
        "base_url": url,
        "support_url": f"{url}/support.html",
        "privacy_url": f"{url}/privacy.html",
        "terms_url": f"{url}/terms.html",
    }, indent=2))


if __name__ == "__main__":
    main()
