#!/usr/bin/env python3
"""Deploy the support/privacy site to Netlify.

App Review rejects a submission whose support or privacy URL does not resolve, so
these pages cannot be "written but not deployed". This uses Netlify's zip-deploy
endpoint directly — no CLI to install, no interactive login.

Idempotent: the site is created on the first run and updated on every one after.

    netlify_deploy.py --dir AppStorePackage/website --site myapp-site
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import sys
import urllib.error
import urllib.request
import zipfile

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
import paths  # noqa: E402
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
        with urllib.request.urlopen(req, timeout=180) as resp:
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
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                archive.write(path, path.relative_to(directory).as_posix())
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", required=True, help="directory to deploy")
    parser.add_argument("--site", required=True, help="Netlify site name (becomes <name>.netlify.app)")
    args = parser.parse_args()

    directory = pathlib.Path(args.dir).resolve()
    if not (directory / "index.html").exists():
        die(f"{directory}/index.html not found")

    site = find_site(args.site)
    if site:
        print(f"site   reused   {site['name']}")
    else:
        site = call("POST", "/sites", {"name": args.site})
        print(f"site   created  {site['name']}")

    payload = zip_dir(directory)
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
