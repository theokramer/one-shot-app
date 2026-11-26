#!/usr/bin/env python3
"""The one-shot-app library: what the skill knows about the user, so nothing is asked twice.

    profile.py init                              # create profile.json (seeded from config.json) if missing
    profile.py missing --for website,review,meta,tiktok   # exit 1 + list of missing fields
    profile.py get imprint.city                  # one value
    profile.py set imprint.city=Berlin imprint.postalCode=10115 ...
    profile.py confirm imprint                   # stamp confirmedAt = today
    profile.py add-pref "Store art: phones fully visible, never cut at the bottom"
    profile.py add-app name=MyApp bundle=com.example.myapp stack=expo dir="~/Documents/MyApp" category="habit tracker"
    profile.py save-menu '{"money":["RevenueCat subscriptions"], ...}'
    profile.py imprint-html --lang de|en         # the imprint page body, for site/gen.py
    profile.py summary                           # short, non-sensitive overview for the intake

Personal data: lives in ~/.one-shot-app/ (see paths.py), never in the skill folder or a repo.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import sys

import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
import paths  # noqa: E402

PROFILE = paths.PROFILE
EXAMPLE = paths.PROFILE_EXAMPLE
CONFIG = paths.CONFIG

# what each purpose needs. "|" = any one of them is enough
NEEDS = {
    "website": ["imprint.name|imprint.companyName", "imprint.street", "imprint.postalCode", "imprint.city",
                "imprint.country", "imprint.email", "imprint.phone", "imprint.confirmedAt"],
    "review": ["reviewContact.firstName", "reviewContact.lastName", "reviewContact.email", "reviewContact.phone"],
    "meta": ["accounts.metaAdAccountId"],
    "tiktok": ["accounts.tiktokAdvertiserId"],
    "identity": ["identity.fullName", "identity.email"],
}
COMPANY_NEEDS = ["imprint.legalForm", "imprint.registerEntry"]


def today():
    return dt.date.today().isoformat()


def load():
    if not PROFILE.exists():
        init(quiet=True)
    return json.loads(PROFILE.read_text())


def save(p):
    PROFILE.write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n")
    PROFILE.chmod(0o600)


def dig(p, path):
    cur = p
    for k in path.split("."):
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def put(p, path, value):
    cur = p
    keys = path.split(".")
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value


def init(quiet=False):
    paths.ensure_home(create_files=False)
    if PROFILE.exists():
        if not quiet:
            print("profile.json exists")
        return
    p = json.loads(EXAMPLE.read_text())
    if CONFIG.exists():
        c = json.loads(CONFIG.read_text())
        d = c.get("developer") or {}
        rc = d.get("reviewContact") or {}
        for k in ("firstName", "lastName", "email", "phone"):
            if rc.get(k):
                p["reviewContact"][k] = rc[k]
        if d.get("appleAccountEmail"):
            p["identity"]["email"] = p["identity"]["email"] or d["appleAccountEmail"]
            p["reviewContact"]["email"] = p["reviewContact"]["email"] or d["appleAccountEmail"]
        sub = (c.get("cloudflare") or {}).get("workersSubdomain")
        if sub:
            p["accounts"]["cloudflareWorkersSubdomain"] = sub
    save(p)
    if not quiet:
        print("created", PROFILE)


def missing(purposes):
    p = load()
    out = []
    for purpose in purposes:
        need = list(NEEDS.get(purpose, []))
        if purpose == "website" and dig(p, "imprint.companyName"):
            need += COMPANY_NEEDS
        for field in need:
            alts = field.split("|")
            if not any(dig(p, a) for a in alts):
                out.append((purpose, field.replace("|", " or ")))
        if purpose == "website":
            ca = dig(p, "imprint.confirmedAt")
            if ca and (dt.date.today() - dt.date.fromisoformat(ca)).days > 365:
                out.append((purpose, "imprint.confirmedAt (older than 12 months: re-confirm)"))
    return out


def imprint_html(lang):
    i = load()["imprint"]
    e = lambda s: html.escape(s or "")  # noqa: E731
    holder = i.get("companyName") or i.get("name")
    lines = [e(holder)]
    if i.get("companyName") and i.get("legalForm"):
        lines[0] += f" ({e(i['legalForm'])})"
    if i.get("companyName") and i.get("name"):
        lines.append(("Vertreten durch: " if lang == "de" else "Represented by: ") + e(i["name"]))
    lines += [e(i.get("street")), f"{e(i.get('postalCode'))} {e(i.get('city'))}", e(i.get("country"))]
    de = lang == "de"
    contact = [f"{'E-Mail' if de else 'Email'}: <a href=\"mailto:{e(i.get('email'))}\">{e(i.get('email'))}</a>",
               f"{'Telefon' if de else 'Phone'}: {e(i.get('phone'))}"]
    extra = []
    if i.get("registerEntry"):
        extra.append(f"<h2>{'Registereintrag' if de else 'Register entry'}</h2><p>{e(i['registerEntry'])}</p>")
    if i.get("vatId"):
        extra.append(f"<h2>{'Umsatzsteuer-ID' if de else 'VAT ID'}</h2><p>"
                     f"{'Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG' if de else 'VAT identification number (§ 27a UStG)'}: "
                     f"{e(i['vatId'])}</p>")
    resp = i.get("responsibleForContent") or i.get("name") or holder
    extra.append(f"<h2>{'Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV' if de else 'Responsible for content (§ 18 (2) MStV)'}</h2>"
                 f"<p>{e(resp)}, {'Anschrift wie oben' if de else 'address as above'}</p>")
    extra.append(f"<h2>{'Verbraucherstreitbeilegung' if de else 'Consumer dispute resolution'}</h2><p>"
                 + ("Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer "
                    "Verbraucherschlichtungsstelle teilzunehmen." if de else
                    "We are neither willing nor obliged to take part in dispute resolution proceedings before a "
                    "consumer arbitration board.") + "</p>")
    title = "Impressum" if de else "Imprint"
    sub = "Angaben gemäß § 5 DDG" if de else "Information pursuant to § 5 DDG (German Digital Services Act)"
    return (f"<h1>{title}</h1><p>{sub}</p><p>" + "<br>".join(x for x in lines if x.strip()) + "</p>"
            f"<h2>{'Kontakt' if de else 'Contact'}</h2><p>" + "<br>".join(contact) + "</p>" + "".join(extra))


def summary():
    p = load()
    have = lambda path: "✓" if dig(p, path) else "—"  # noqa: E731
    print(f"identity      {have('identity.fullName')} name  {have('identity.email')} email")
    print(f"imprint       {'complete' if not missing(['website']) else 'incomplete: ' + ', '.join(f for _, f in missing(['website']))}")
    print(f"reviewContact {'complete' if not missing(['review']) else 'incomplete: ' + ', '.join(f for _, f in missing(['review']))}")
    print(f"accounts      meta ad {have('accounts.metaAdAccountId')}  tiktok {have('accounts.tiktokAdvertiserId')}")
    md = p.get("menuDefaults", {})
    print(f"last menu     {md.get('updatedAt') or 'none'}")
    print(f"preferences   {len(p.get('preferences', {}).get('items', []))} saved")
    print(f"apps          {', '.join(a.get('name', '?') for a in p.get('apps', {}).get('items', [])) or 'none'}")


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, a = a[0], a[1:]
    if cmd == "init":
        init()
    elif cmd == "missing":
        purposes = a[a.index("--for") + 1].split(",") if "--for" in a else list(NEEDS)
        m = missing(purposes)
        for purpose, field in m:
            print(f"{purpose}: {field}")
        if not m:
            print("nothing missing")
        raise SystemExit(1 if m else 0)
    elif cmd == "get":
        v = dig(load(), a[0])
        print(json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else (v or ""))
    elif cmd == "set":
        p = load()
        for kv in a:
            k, v = kv.split("=", 1)
            put(p, k, v)
        save(p)
        print("saved", ", ".join(kv.split("=", 1)[0] for kv in a))
    elif cmd == "confirm":
        p = load()
        put(p, f"{a[0]}.confirmedAt", today())
        save(p)
        print("confirmed", a[0])
    elif cmd == "add-pref":
        p = load()
        items = p.setdefault("preferences", {}).setdefault("items", [])
        if not any(x.get("text") == a[0] for x in items):
            items.append({"text": a[0], "date": today()})
        save(p)
        print("saved preference")
    elif cmd == "add-app":
        p = load()
        app = dict(kv.split("=", 1) for kv in a)
        app.setdefault("added", today())
        items = p.setdefault("apps", {}).setdefault("items", [])
        items[:] = [x for x in items if x.get("bundle") != app.get("bundle")] + [app]
        save(p)
        print("saved app", app.get("name"))
    elif cmd == "save-menu":
        p = load()
        md = json.loads(a[0])
        md["updatedAt"] = today()
        p.setdefault("menuDefaults", {}).update(md)
        save(p)
        print("saved menu defaults")
    elif cmd == "imprint-html":
        lang = a[a.index("--lang") + 1] if "--lang" in a else "de"
        print(imprint_html(lang))
    elif cmd == "summary":
        summary()
    else:
        raise SystemExit(f"unknown command {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
