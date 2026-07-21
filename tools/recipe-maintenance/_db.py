"""Shared PostgREST helpers for the GalleyQuest recipe-maintenance toolkit.

Credential-free: reads the Supabase URL + anon key from the app's local
config.js at runtime. Never prints or logs the key or Authorization headers.
Standard library only.
"""
import os, re, json, hashlib, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG = os.path.join(ROOT, "config.js")
TABLES = ["recipes", "recipe_ingredients", "stock_items", "meal_plan",
          "grocery_extra_items", "grocery_dismissed_items"]


def load_config():
    txt = open(CONFIG, encoding="utf-8").read()
    url = re.search(r"SUPABASE_URL\s*=\s*'([^']+)'", txt).group(1).rstrip("/")
    key = re.search(r"SUPABASE_ANON_KEY\s*=\s*'([^']+)'", txt).group(1)
    return url, key


_URL, _KEY = load_config()
PROJECT_REF = re.search(r"https://([a-z0-9]+)\.supabase\.co", _URL).group(1)


def _headers(extra=None):
    h = {"apikey": _KEY, "Authorization": "Bearer " + _KEY,
         "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def _req(method, path, body=None, headers=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(_URL + path, data=data, method=method,
                                 headers=headers or _headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8")
            return r.status, dict(r.headers), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        parsed = raw
        if raw and raw.strip()[:1] in "{[":
            try:
                parsed = json.loads(raw)
            except Exception:
                pass
        return e.code, dict(e.headers), parsed


def get(table, params="select=*"):
    st, hd, body = _req("GET", "/rest/v1/%s?%s" % (table, params))
    if st >= 400:
        raise RuntimeError("GET %s -> %s: %s" % (table, st, body))
    return body or []


def count(table, filt=""):
    q = "select=id" + (("&" + filt) if filt else "")
    st, hd, body = _req("GET", "/rest/v1/%s?%s" % (table, q),
                        headers=_headers({"Prefer": "count=exact"}))
    if st >= 400:
        raise RuntimeError("COUNT %s -> %s: %s" % (table, st, body))
    return int(hd.get("Content-Range", "*/0").split("/")[-1])


def insert(table, obj):
    return _req("POST", "/rest/v1/%s" % table, obj,
                _headers({"Prefer": "return=representation"}))[:3:2]


def patch(table, filt, obj):
    return _req("PATCH", "/rest/v1/%s?%s" % (table, filt), obj,
                _headers({"Prefer": "return=representation"}))[:3:2]


def delete(table, filt):
    return _req("DELETE", "/rest/v1/%s?%s" % (table, filt))[:3:2]


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def backup(dest_dir, purpose, branch="", commit=""):
    """Read-only export of all six tables + a manifest. Returns the manifest."""
    os.makedirs(dest_dir, exist_ok=True)
    manifest = {
        "timestamp": os.path.basename(dest_dir.rstrip("/\\")),
        "purpose": purpose, "branch": branch, "commit": commit,
        "supabase_project_ref": PROJECT_REF,
        "note": "read-only export; no credential values stored",
        "tables": {}, "file_sha256": {},
    }
    for t in TABLES:
        rows = get(t, "select=*&order=id")
        p = os.path.join(dest_dir, t + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        manifest["tables"][t] = len(rows)
        manifest["file_sha256"][t + ".json"] = sha256_file(p)
    with open(os.path.join(dest_dir, "backup-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest
