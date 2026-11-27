#!/usr/bin/env python3
"""Provision a RevenueCat project over the REST v2 API.

Why not the MCP connector: its bearer token is whatever the user authorised in
the Claude connector UI, which in practice is scoped read-only. The run then
gets all the way to the entitlement step and dies with

    The client needs at least the project_configuration:entitlements:read_write
    scope to access this endpoint.

by which point the app is already built. A secret v2 key from config.json with
explicit scopes allows provisioning. Verify checks authentication without any writes.

Resume against an existing project only after verifying its ID and passing --project-id.

    revenuecat.py verify
    revenuecat.py provision --apply --app-name MyApp --bundle-id com.example.myapp \
        --entitlement pro --annual com.example.myapp.pro.annual \
        --monthly com.example.myapp.pro.monthly
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
import paths  # noqa: E402
from http_safety import open_request  # noqa: E402
CONFIG = paths.CONFIG

REQUIRED_SCOPES = [
    "project_configuration:projects:read_write",
    "project_configuration:apps:read_write",
    "project_configuration:entitlements:read_write",
    "project_configuration:products:read_write",
    "project_configuration:offerings:read_write",
    "project_configuration:packages:read_write",
    "project_configuration:api_keys:read",
]


def load_config() -> dict:
    if not CONFIG.exists():
        die(f"{CONFIG} is missing. Copy config.example.json and fill it in.")
    return json.loads(CONFIG.read_text())


def die(message: str, code: int = 1):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


class RevenueCat:
    def __init__(self, key: str, base: str):
        self.key = key
        self.base = base.rstrip("/")

    def request(self, method: str, path: str, body: dict | None = None):
        req = urllib.request.Request(
            f"{self.base}{path}",
            method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with open_request(req, timeout=60) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            try:
                parsed = json.loads(detail)
                message = parsed.get("message", detail)
            except json.JSONDecodeError:
                message = detail
            raise RevenueCatError(exc.code, message) from None

    # --- find-or-create helpers ---------------------------------------------

    def items(self, path: str) -> list:
        return self.request("GET", path).get("items", [])

    def find(self, path: str, field: str, value: str):
        return next((i for i in self.items(path) if i.get(field) == value), None)

    def ensure_app(self, project_id: str, name: str, bundle_id: str) -> str:
        for app in self.items(f"/projects/{project_id}/apps?limit=100"):
            if (app.get("app_store") or {}).get("bundle_id") == bundle_id:
                print(f"app      reused   {app['id']}  {bundle_id}")
                return app["id"]
        created = self.request(
            "POST",
            f"/projects/{project_id}/apps",
            {"name": name, "type": "app_store", "app_store": {"bundle_id": bundle_id}},
        )
        print(f"app      created  {created['id']}  {bundle_id}")
        return created["id"]

    def ensure_entitlement(self, project_id: str, lookup_key: str, display_name: str) -> str:
        existing = self.find(f"/projects/{project_id}/entitlements?limit=100", "lookup_key", lookup_key)
        if existing:
            print(f"entitle  reused   {existing['id']}  {lookup_key}")
            return existing["id"]
        created = self.request(
            "POST",
            f"/projects/{project_id}/entitlements",
            {"lookup_key": lookup_key, "display_name": display_name},
        )
        print(f"entitle  created  {created['id']}  {lookup_key}")
        return created["id"]

    def ensure_product(self, project_id: str, app_id: str, store_identifier: str, display_name: str) -> str:
        for product in self.items(f"/projects/{project_id}/products?limit=100"):
            if product.get("store_identifier") == store_identifier:
                print(f"product  reused   {product['id']}  {store_identifier}")
                return product["id"]
        created = self.request(
            "POST",
            f"/projects/{project_id}/products",
            {
                "app_id": app_id,
                "store_identifier": store_identifier,
                "type": "subscription",
                "display_name": display_name,
            },
        )
        print(f"product  created  {created['id']}  {store_identifier}")
        return created["id"]

    def ensure_offering(self, project_id: str, lookup_key: str, display_name: str) -> str:
        existing = self.find(f"/projects/{project_id}/offerings?limit=100", "lookup_key", lookup_key)
        if existing:
            print(f"offering reused   {existing['id']}  {lookup_key}")
            return existing["id"]
        created = self.request(
            "POST",
            f"/projects/{project_id}/offerings",
            {"lookup_key": lookup_key, "display_name": display_name},
        )
        print(f"offering created  {created['id']}  {lookup_key}")
        return created["id"]

    def ensure_package(self, project_id: str, offering_id: str, lookup_key: str, display_name: str, position: int) -> str:
        path = f"/projects/{project_id}/offerings/{offering_id}/packages?limit=100"
        existing = self.find(path, "lookup_key", lookup_key)
        if existing:
            print(f"package  reused   {existing['id']}  {lookup_key}")
            return existing["id"]
        created = self.request(
            "POST",
            f"/projects/{project_id}/offerings/{offering_id}/packages",
            {"lookup_key": lookup_key, "display_name": display_name, "position": position},
        )
        print(f"package  created  {created['id']}  {lookup_key}")
        return created["id"]

    def attach_to_entitlement(self, project_id: str, entitlement_id: str, product_ids: list[str]):
        self.request(
            "POST",
            f"/projects/{project_id}/entitlements/{entitlement_id}/actions/attach_products",
            {"product_ids": product_ids},
        )
        print(f"attach   entitlement <- {len(product_ids)} product(s)")

    def attach_to_package(self, project_id: str, package_id: str, product_id: str):
        self.request(
            "POST",
            f"/projects/{project_id}/packages/{package_id}/actions/attach_products",
            {"products": [{"product_id": product_id, "eligibility_criteria": "all"}]},
        )
        print(f"attach   package     <- {product_id}")

    def public_sdk_key(self, project_id: str, app_id: str) -> str:
        keys = self.items(f"/projects/{project_id}/apps/{app_id}/public_api_keys")
        for key in keys:
            value = key.get("key") or key.get("api_key") or ""
            if value.startswith("appl_"):
                return value
        return keys[0].get("key", "") if keys else ""


class RevenueCatError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status} — {message}")
        self.status = status
        self.message = message


def client() -> RevenueCat:
    cfg = load_config()
    key = os.environ.get("REVENUECAT_V2_KEY") or cfg.get("revenuecat", {}).get("apiV2Key", "")
    if not key:
        die(
            "revenuecat.apiV2Key is empty in config.json.\n"
            "  Create one: RevenueCat → Project settings → API keys → New → Secret (v2)\n"
            "  Required scopes:\n    " + "\n    ".join(REQUIRED_SCOPES)
        )
    return RevenueCat(key, "https://api.revenuecat.com/v2")


def cmd_verify(_args):
    """Check authentication using a read-only request."""
    rc = client()
    try:
        rc.items("/projects?limit=1")
    except RevenueCatError as exc:
        die(f"cannot list projects (HTTP {exc.status})")
    print("RevenueCat key can list projects; write permissions were not tested")


def cmd_provision(args):
    rc = client()
    if args.project_id:
        rc.request("GET", f"/projects/{args.project_id}")
        project_id = args.project_id
    else:
        if rc.find("/projects?limit=100", "name", args.app_name):
            die("Project name already exists. Verify its ID and pass --project-id to reuse it.")
        project_id = rc.request("POST", "/projects", {"name": args.app_name})["id"]
    app_id = rc.ensure_app(project_id, args.app_name, args.bundle_id)
    entitlement_id = rc.ensure_entitlement(project_id, args.entitlement, f"{args.app_name} Pro")

    annual_id = rc.ensure_product(project_id, app_id, args.annual, f"{args.app_name} Pro (annual)")
    monthly_id = rc.ensure_product(project_id, app_id, args.monthly, f"{args.app_name} Pro (monthly)")

    # The entitlement is the single source of truth for access; without this
    # attach, a real purchase never flips isProActive.
    rc.attach_to_entitlement(project_id, entitlement_id, [annual_id, monthly_id])

    offering_id = rc.ensure_offering(project_id, "default", f"{args.app_name} Pro")
    annual_pkg = rc.ensure_package(project_id, offering_id, "$rc_annual", "Annual", 1)
    monthly_pkg = rc.ensure_package(project_id, offering_id, "$rc_monthly", "Monthly", 2)
    rc.attach_to_package(project_id, annual_pkg, annual_id)
    rc.attach_to_package(project_id, monthly_pkg, monthly_id)

    sdk_key = rc.public_sdk_key(project_id, app_id)
    print()
    print(json.dumps({
        "project_id": project_id,
        "app_id": app_id,
        "entitlement_id": entitlement_id,
        "offering_id": offering_id,
        "sdk_key": sdk_key,
    }, indent=2))
    if not sdk_key:
        print("warning: no public SDK key returned — check the api_keys:read scope",
              file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="check authentication without writing")

    prov = sub.add_parser("provision", help="create project, app, entitlement, products, offering")
    prov.add_argument("--app-name", required=True)
    prov.add_argument("--bundle-id", required=True)
    prov.add_argument("--entitlement", default="pro")
    prov.add_argument("--annual", required=True, help="App Store product id for the annual plan")
    prov.add_argument("--monthly", required=True, help="App Store product id for the monthly plan")

    prov.add_argument("--apply", action="store_true", help="perform approved writes")
    prov.add_argument("--project-id", help="explicit ID of an existing project")
    args = parser.parse_args()
    if args.command == "provision" and not args.apply:
        parser.error("provision requires --apply after approval")
    if args.command == "provision" and args.project_id and not re.fullmatch(r"[A-Za-z0-9_-]+", args.project_id):
        parser.error("invalid RevenueCat project ID")
    {"verify": cmd_verify, "provision": cmd_provision}[args.command](args)


if __name__ == "__main__":
    main()
