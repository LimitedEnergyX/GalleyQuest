"""Import the curated recipe set in batches, with per-recipe verify + rollback.

Reads the newest .local/recipe-maintenance/*-import-build/final-import.json.
--dry-run (default) validates + reports only; --apply writes to the database.

For each recipe: insert the recipe row, bulk-insert its ingredients, read the
recipe back with its ingredients embedded and verify (name matches, ingredient
count matches, every quantity nonempty). Any failure rolls that recipe back
(delete ingredients + recipe) and is logged; the run continues. Recipes are
processed in batches of 10 with an authoritative count check after each batch.
"""
import os, sys, json, re, glob, datetime, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db


def norm_name(n):
    return re.sub(r"\s+", " ", (n or "").strip().lower())


def latest_final():
    d = sorted(glob.glob(os.path.join(_db.ROOT, ".local", "recipe-maintenance", "*-import-build")))[-1]
    return json.load(open(os.path.join(d, "final-import.json"), encoding="utf-8"))


def insert_recipe(r):
    body = {"name": r["name"], "theme": r["theme"],
            "instructions": r["instructions"], "notes": r.get("notes", "")}
    st, resp = _db.insert("recipes", body)
    if st not in (200, 201) or not resp:
        return None, (st, resp)
    return resp[0]["id"], None


def insert_ingredients(rid, ings):
    rows = [{"recipe_id": rid, "ingredient_name": i["name"],
             "quantity": i["quantity"], "stock_item_id": None} for i in ings]
    return _db.insert("recipe_ingredients", rows)


def verify_recipe(rid, r):
    got = _db.get("recipes", "id=eq.%s&select=id,name,recipe_ingredients(ingredient_name,quantity)" % rid)
    if not got:
        return "recipe not found on readback"
    g = got[0]
    if norm_name(g["name"]) != norm_name(r["name"]):
        return "name mismatch"
    gi = g.get("recipe_ingredients") or []
    if len(gi) != len(r["ingredients"]):
        return "ingredient count mismatch %d!=%d" % (len(gi), len(r["ingredients"]))
    for i in gi:
        if not (i.get("quantity") or "").strip():
            return "blank quantity on readback"
    return None


def rollback(rid):
    _db.delete("recipe_ingredients", "recipe_id=eq.%s" % rid)
    _db.delete("recipes", "id=eq.%s" % rid)


def main():
    apply = "--apply" in sys.argv
    final = latest_final()
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log = {"mode": "apply" if apply else "dry-run", "started": ts,
           "batches": [], "imported": [], "failed": []}
    existing = set(norm_name(x["name"]) for x in _db.get("recipes", "select=name"))
    before = _db.count("recipes")
    before_ing = _db.count("recipe_ingredients")
    print("MODE=%s start_recipes=%d start_ingredients=%d to_import=%d" % (log["mode"], before, before_ing, len(final)))

    for bi in range(0, len(final), 10):
        batch = final[bi:bi + 10]
        bnum = bi // 10 + 1
        for r in batch:
            nn = norm_name(r["name"])
            if nn in existing:
                log["failed"].append({"name": r["name"], "reason": "duplicate (pre-insert check)"})
                continue
            if not apply:
                log["imported"].append({"name": r["name"], "ingredients": len(r["ingredients"]), "dry": True})
                existing.add(nn)
                continue
            rid, err = insert_recipe(r)
            if not rid:
                log["failed"].append({"name": r["name"], "reason": "recipe insert failed %r" % (err,)})
                continue
            st, resp = insert_ingredients(rid, r["ingredients"])
            if st not in (200, 201):
                rollback(rid)
                log["failed"].append({"name": r["name"], "reason": "ingredient insert failed %s: %r" % (st, resp)})
                continue
            verr = verify_recipe(rid, r)
            if verr:
                rollback(rid)
                log["failed"].append({"name": r["name"], "reason": "verify failed: %s" % verr})
                continue
            existing.add(nn)
            log["imported"].append({"name": r["name"], "id": rid, "ingredients": len(r["ingredients"])})
        now = _db.count("recipes")
        log["batches"].append({"batch": bnum, "recipes_now": now})
        done = len([x for x in log["imported"] if not x.get("dry")]) if apply else len(log["imported"])
        print("batch %d: recipes_now=%d imported=%d failed=%d" % (bnum, now, done, len(log["failed"])))
        if apply:
            time.sleep(0.25)

    after = _db.count("recipes")
    after_ing = _db.count("recipe_ingredients")
    log["end_recipes"] = after
    log["end_ingredients"] = after_ing
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance",
                          ts + ("-import-apply" if apply else "-import-dryrun"))
    os.makedirs(outdir, exist_ok=True)
    json.dump(log, open(os.path.join(outdir, "import-log.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    done = len([x for x in log["imported"] if not x.get("dry")]) if apply else len(log["imported"])
    print("OUTDIR=%s" % outdir)
    print("imported=%d failed=%d recipes %d->%d ingredients %d->%d" % (
        done, len(log["failed"]), before, after, before_ing, after_ing))


if __name__ == "__main__":
    main()
