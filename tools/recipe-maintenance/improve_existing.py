"""Apply improvements to existing recipes, one at a time, with verification + rollback.

Usage:
  python improve_existing.py --dry-run     (default; no writes)
  python improve_existing.py --apply

Reads .local/recipe-maintenance/existing_improvements.py (IMPROVEMENTS dict).
Sets recipe instructions/notes and fills EXISTING-ingredient quantities matched
by name. Preserves recipe id, name, theme, ingredient ids, and stock_item_id.
Writes existing-recipe-changes.json under a timestamped report dir.
"""
import os, sys, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

IMP_PATH = os.path.join(_db.ROOT, ".local", "recipe-maintenance", "existing_improvements.py")


def load_improvements():
    ns = {}
    exec(open(IMP_PATH, encoding="utf-8").read(), ns)
    return ns["IMPROVEMENTS"]


def fetch_recipe(rid):
    rows = _db.get("recipes", "id=eq.%s&select=*,recipe_ingredients(id,ingredient_name,quantity,stock_item_id)" % rid)
    return rows[0] if rows else None


def norm(s):
    return (s or "").strip()


def verify(before, after, rid):
    errs = []
    if after["id"] != rid:
        errs.append("recipe id changed")
    if not norm(after.get("instructions")):
        errs.append("instructions empty")
    aings = after.get("recipe_ingredients") or []
    if not aings:
        errs.append("no ingredients")
    names = {}
    for ing in aings:
        if not norm(ing.get("quantity")):
            errs.append("blank quantity: %s" % ing.get("ingredient_name"))
        if not norm(ing.get("ingredient_name")):
            errs.append("blank ingredient name")
        k = norm(ing.get("ingredient_name")).lower()
        names[k] = names.get(k, 0) + 1
        b = before["ingredients"].get(ing["id"])
        if b and b.get("stock_item_id") != ing.get("stock_item_id"):
            errs.append("stock link changed: %s" % ing.get("ingredient_name"))
    dups = [k for k, v in names.items() if v > 1]
    if dups:
        errs.append("duplicate ingredient names: %s" % dups)
    if len(aings) != len(before["ingredients"]):
        errs.append("ingredient count changed")
    return errs


def rollback(rid, before):
    try:
        _db.patch("recipes", "id=eq.%s" % rid,
                  {"instructions": before["instructions"], "notes": before["notes"]})
        for ing_id, b in before["ingredients"].items():
            _db.patch("recipe_ingredients", "id=eq.%s" % ing_id, {"quantity": b["quantity"]})
        after = fetch_recipe(rid)
        return norm(after.get("instructions")) == norm(before["instructions"])
    except Exception:
        return False


def apply_one(rid, imp, dry):
    rec = fetch_recipe(rid)
    if not rec:
        return {"id": rid, "status": "MISSING", "error": "recipe not found"}
    ings = rec.get("recipe_ingredients") or []
    before = {
        "instructions": rec.get("instructions"), "notes": rec.get("notes"),
        "ingredients": {ing["id"]: {"name": ing["ingredient_name"],
                                    "quantity": ing["quantity"],
                                    "stock_item_id": ing["stock_item_id"]} for ing in ings},
    }
    qmap = imp.get("quantities", {})
    ql = {k.strip().lower(): v for k, v in qmap.items()}
    planned = []
    for ing in ings:
        cur_q = norm(ing.get("quantity"))
        nm = norm(ing.get("ingredient_name"))
        new_q = qmap.get(ing["ingredient_name"]) or qmap.get(nm) or ql.get(nm.lower())
        if new_q:
            if cur_q != norm(new_q):
                planned.append((ing["id"], new_q, nm))
        elif not cur_q:
            return {"id": rid, "name": rec.get("name"), "status": "INCOMPLETE",
                    "error": "no quantity mapping for ingredient '%s'" % nm, "before": before}
    rec_fields = {}
    if "instructions" in imp and norm(imp["instructions"]) != norm(rec.get("instructions")):
        rec_fields["instructions"] = imp["instructions"]
    if "notes" in imp and norm(imp["notes"]) != norm(rec.get("notes")):
        rec_fields["notes"] = imp["notes"]
    change = {"id": rid, "name": rec.get("name"), "theme": rec.get("theme"),
              "fields_changed": list(rec_fields.keys()), "quantities_set": len(planned),
              "ingredients_added": 0, "ingredients_removed": 0,
              "stock_links_preserved": sum(1 for i in ings if i.get("stock_item_id")),
              "before": before}
    if dry:
        change["status"] = "DRY-OK"
        return change
    try:
        if rec_fields:
            st, body = _db.patch("recipes", "id=eq.%s" % rid, rec_fields)
            if st >= 400:
                raise RuntimeError("recipe patch %s: %s" % (st, body))
        for ing_id, new_q, nm in planned:
            st, body = _db.patch("recipe_ingredients", "id=eq.%s" % ing_id, {"quantity": new_q})
            if st >= 400:
                raise RuntimeError("ingredient patch %s (%s): %s" % (ing_id, nm, body))
        after = fetch_recipe(rid)
        errs = verify(before, after, rid)
        if errs:
            raise RuntimeError("verify: " + "; ".join(errs))
        change["status"] = "APPLIED"
        change["after"] = {"instructions": after.get("instructions"), "notes": after.get("notes"),
                           "ingredients": [{"name": i["ingredient_name"], "quantity": i["quantity"],
                                            "stock_item_id": i["stock_item_id"]} for i in (after.get("recipe_ingredients") or [])]}
        return change
    except Exception as e:
        rb = rollback(rid, before)
        change["status"] = "FAILED_ROLLED_BACK" if rb else "FAILED_ROLLBACK_FAILED"
        change["error"] = str(e)
        return change


def main():
    dry = ("--apply" not in sys.argv)
    imps = load_improvements()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance",
                          ts + ("-existing-dryrun" if dry else "-existing-cleanup"))
    os.makedirs(outdir, exist_ok=True)
    results, stopped = [], False
    for rid, imp in imps.items():
        r = apply_one(rid, imp, dry)
        results.append(r)
        print("%-46s %-8s qty=%s" % ((r.get("name") or rid)[:45], r["status"], r.get("quantities_set", "-")))
        if r["status"].startswith("FAILED") or r["status"] in ("INCOMPLETE", "MISSING"):
            stopped = True
            print("  ERROR:", r.get("error"))
            break
    json.dump(results, open(os.path.join(outdir, "existing-recipe-changes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    ok = sum(1 for r in results if r["status"] in ("APPLIED", "DRY-OK"))
    print("OUTDIR=%s" % outdir)
    print("MODE=%s processed=%d ok=%d stopped=%s" % ("DRY" if dry else "APPLY", len(results), ok, stopped))
    if stopped:
        sys.exit(2)


if __name__ == "__main__":
    main()
