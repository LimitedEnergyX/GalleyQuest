"""Ingest spoken/typed pantry items into stock_items. Matches existing items
(updates their status) or adds new ones (categorized). Used by the update-pantry
skill for the Claude Dispatch path (speak on phone -> PC-side Claude runs this).

Input: a JSON array from a file or stdin:
  [{"name": "milk", "status": "OK", "quantity": "1 gal"},
   {"name": "flour", "status": "OUT", "category": "pantry_dry_goods"}]
status defaults to OK; category is inferred if omitted.

Usage:
  python stock_cli.py upsert <file.json>      # or:  ... upsert -   (read stdin)
  python stock_cli.py upsert --dry-run <file.json>
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db
import link_stock
import stock_from_recipes

VALID_CATS = {"produce", "bakery", "deli_prepared", "meat_seafood", "dairy_eggs",
              "frozen", "pantry_dry_goods", "canned_goods", "condiments_spices",
              "snacks", "beverages", "household_other"}


def norm(name):
    return " ".join(link_stock.tokens(name))


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "upsert":
        print(__doc__)
        sys.exit(1)
    dry = "--dry-run" in sys.argv
    src = [a for a in sys.argv[2:] if a != "--dry-run"][0]
    raw = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    try:
        items = json.loads(raw)
        assert isinstance(items, list)
    except Exception as e:
        print("Could not parse JSON array: %s" % e)
        sys.exit(1)

    existing = _db.get("stock_items", "select=id,name,notes")
    by_key = {norm(s["name"]): s for s in existing}
    by_name = {s["name"]: s for s in existing}
    curated = {norm(k): v for k, v in link_stock.CURATED_RAW.items()}

    def resolve(name):
        k = norm(name)
        if k in by_key:
            return by_key[k], None
        if k in curated and curated[k] in by_name:
            return by_name[curated[k]], None
        canon = stock_from_recipes.canonical(name)
        if canon:
            ck = norm(canon)
            if ck in by_key:
                return by_key[ck], None
            return None, canon
        return None, name.strip()

    updated, added = [], []
    for it in items:
        raw_name = (it.get("name") or "").strip()
        if not raw_name:
            continue
        status = it.get("status") if it.get("status") in ("OK", "LOW", "OUT") else "OK"
        note = it.get("quantity") or it.get("notes")
        match, new_name = resolve(raw_name)
        if match:
            body = {"status": status}
            if note:
                body["notes"] = note
            if not dry:
                _db.patch("stock_items", "id=eq.%s" % match["id"], body)
            updated.append((raw_name, match["name"], status))
        else:
            cat = it.get("category") if it.get("category") in VALID_CATS else stock_from_recipes.categorize(new_name)
            if not dry:
                _db.insert("stock_items", {"name": new_name, "category": cat, "status": status, "notes": note})
            added.append((new_name, cat, status))

    print("%sUPDATED %d, ADDED %d" % ("[dry-run] " if dry else "", len(updated), len(added)))
    for r, name, st in updated:
        print("  updated  %-22s -> %-24s [%s]" % (r[:22], name[:24], st))
    for name, cat, st in added:
        print("  added    %-24s [%s] [%s]" % (name[:24], cat, st))


if __name__ == "__main__":
    main()
