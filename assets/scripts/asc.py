#!/usr/bin/env python3
"""App Store Connect API client for one-shot runs. Reads the key from ~/.one-shot-app/config.json
and never prints it.

    asc.py call GET  /v1/apps?filter[bundleId]=com.x.y
    asc.py call POST /v1/winBackOffers '{"data": {...}}'        (FULL=1 for untruncated output)
    asc.py attach-build   <appStoreVersionId> <buildNumber> [--app <appId>]   # waits for VALID, then attaches
    asc.py upload-preview <file.mp4> <appStoreVersionId> <locale> [--type IPHONE_67] [--frame 00:00:03:00]
    asc.py upload-review-attachment <file> <appStoreVersionId>
    asc.py app-id <bundleId>

Nothing here submits for review.
Needs: python3 -m pip install --user PyJWT cryptography
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

import jwt

import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
import paths  # noqa: E402
CFG = paths.CONFIG
BASE = "https://api.appstoreconnect.apple.com"
_tok: tuple[str, float] | None = None


def token() -> str:
    global _tok
    if _tok and _tok[1] > time.time() + 60:
        return _tok[0]
    c = json.loads(CFG.read_text())["appStoreConnect"]
    now = int(time.time())
    t = jwt.encode({"iss": c["issuerId"], "iat": now, "exp": now + 1100, "aud": "appstoreconnect-v1"},
                   pathlib.Path(os.path.expanduser(c["privateKeyPath"])).read_text(),
                   algorithm="ES256", headers={"kid": c["keyId"], "typ": "JWT"})
    _tok = (t, now + 1100)
    return t


def asc(method: str, path: str, body=None, ok=(200, 201, 204)):
    data = json.dumps(body).encode() if isinstance(body, (dict, list)) else (body.encode() if body else None)
    req = urllib.request.Request(BASE + path, data=data, method=method.upper(),
                                 headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        if e.code in ok:
            return json.loads(msg) if msg else {}
        raise SystemExit(f"{method} {path} → HTTP {e.code}\n{msg[:4000]}")


def rel(t, i):
    return {"data": {"type": t, "id": i}}


def upload_parts(ops, blob: bytes):
    for op in ops:
        q = urllib.request.Request(op["url"], data=blob[op["offset"]:op["offset"] + op["length"]], method=op["method"])
        for h in op.get("requestHeaders") or []:
            q.add_header(h["name"], h["value"])
        urllib.request.urlopen(q, timeout=600).read()


def app_id(bundle):
    d = asc("GET", f"/v1/apps?filter[bundleId]={bundle}")["data"]
    return d[0]["id"] if d else None


def attach_build(version_id, number, app=None):
    if not app:
        app = asc("GET", f"/v1/appStoreVersions/{version_id}/app")["data"]["id"]
    for _ in range(90):
        d = asc("GET", f"/v1/builds?filter[app]={app}&filter[version]={number}")["data"]
        if d and d[0]["attributes"]["processingState"] == "VALID":
            asc("PATCH", f"/v1/appStoreVersions/{version_id}/relationships/build", rel("builds", d[0]["id"]))
            print("attached build", number)
            return
        if d and d[0]["attributes"]["processingState"] in ("FAILED", "INVALID"):
            raise SystemExit(f"build {number} is {d[0]['attributes']['processingState']}")
        time.sleep(30)
    raise SystemExit(f"timed out waiting for build {number}")


def upload_preview(path, version_id, locale, ptype="IPHONE_67", frame="00:00:03:00"):
    locs = asc("GET", f"/v1/appStoreVersions/{version_id}/appStoreVersionLocalizations")["data"]
    loc = next((x["id"] for x in locs if x["attributes"]["locale"] == locale), None)
    if not loc:
        raise SystemExit(f"no {locale} localization on this version")
    sets = [s for s in asc("GET", f"/v1/appStoreVersionLocalizations/{loc}/appPreviewSets")["data"]
            if s["attributes"]["previewType"] == ptype]
    st = sets[0]["id"] if sets else asc("POST", "/v1/appPreviewSets", {"data": {
        "type": "appPreviewSets", "attributes": {"previewType": ptype},
        "relationships": {"appStoreVersionLocalization": rel("appStoreVersionLocalizations", loc)}}})["data"]["id"]
    for x in asc("GET", f"/v1/appPreviewSets/{st}/appPreviews")["data"]:
        asc("DELETE", f"/v1/appPreviews/{x['id']}")
    blob = pathlib.Path(path).read_bytes()
    p = asc("POST", "/v1/appPreviews", {"data": {"type": "appPreviews", "attributes": {
        "fileName": os.path.basename(path), "fileSize": len(blob), "mimeType": "video/mp4",
        "previewFrameTimeCode": frame}, "relationships": {"appPreviewSet": rel("appPreviewSets", st)}}})["data"]
    upload_parts(p["attributes"]["uploadOperations"], blob)
    asc("PATCH", f"/v1/appPreviews/{p['id']}", {"data": {"type": "appPreviews", "id": p["id"], "attributes": {
        "uploaded": True, "sourceFileChecksum": hashlib.md5(blob).hexdigest()}}})
    for _ in range(40):
        s = asc("GET", f"/v1/appPreviews/{p['id']}")["data"]["attributes"].get("assetDeliveryState") or {}
        print(s.get("state"), s.get("errors") or "")
        if s.get("state") in ("COMPLETE", "FAILED"):
            return
        time.sleep(20)


def upload_review_attachment(path, version_id):
    rd = asc("GET", f"/v1/appStoreVersions/{version_id}/appStoreReviewDetail")["data"]["id"]
    for x in asc("GET", f"/v1/appStoreReviewDetails/{rd}/appStoreReviewAttachments")["data"]:
        asc("DELETE", f"/v1/appStoreReviewAttachments/{x['id']}")
    blob = pathlib.Path(path).read_bytes()
    a = asc("POST", "/v1/appStoreReviewAttachments", {"data": {"type": "appStoreReviewAttachments", "attributes": {
        "fileName": os.path.basename(path), "fileSize": len(blob)},
        "relationships": {"appStoreReviewDetail": rel("appStoreReviewDetails", rd)}}})["data"]
    upload_parts(a["attributes"]["uploadOperations"], blob)
    r = asc("PATCH", f"/v1/appStoreReviewAttachments/{a['id']}", {"data": {
        "type": "appStoreReviewAttachments", "id": a["id"],
        "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(blob).hexdigest()}}})
    print(r["data"]["attributes"].get("assetDeliveryState"))


def opt(args, name, default=None):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, a = a[0], a[1:]
    if cmd == "call":
        out = asc(a[0], a[1], a[2] if len(a) > 2 else None)
        s = json.dumps(out, indent=1)
        print(s if os.environ.get("FULL") else s[:6000])
    elif cmd == "app-id":
        print(app_id(a[0]))
    elif cmd == "attach-build":
        app = opt(a, "--app")
        attach_build(a[0], a[1], app)
    elif cmd == "upload-preview":
        t, f = opt(a, "--type", "IPHONE_67"), opt(a, "--frame", "00:00:03:00")
        upload_preview(a[0], a[1], a[2], t, f)
    elif cmd == "upload-review-attachment":
        upload_review_attachment(a[0], a[1])
    else:
        raise SystemExit(f"unknown command {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
