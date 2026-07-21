"""Verify recipe database integrity. Read-only.

Usage: python verify_recipe_database.py [--baseline <backup recipes.json>]
Exit 0 = PASS, 1 = FAIL.
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db


def norm_name(n):
    return re.sub(r"\s+", " ", (n or "").strip().lower())


def main():
    baseline_ids = None
    if "--baseline" in sys.argv:
        p = sys.argv[sys.argv.index("--baseline") + 1]
        baseline_ids = set(r["id"] for r in json.load(open(p, encoding="utf-8")))
    recs = _db.get("recipes", "select=id,name,theme,instructions,notes,recipe_ingredients(id,ingredient_name,quantity,stock_item_id)")
    ings_all = _db.get("recipe_ingredients", "select=id,recipe_id")
    stock_ids = set(s["id"] for s in _db.get("stock_items", "select=id"))
    plans = _db.get("meal_plan", "select=id,recipe_id")
    recipe_ids = set(r["id"] for r in recs)

    checks = []
    def chk(name, ok, detail=""):
        checks.append((name, ok, detail))

    no_ing = [r["name"] for r in recs if not (r.get("recipe_ingredients") or [])]
    blank_q = [(r["name"], i["ingredient_name"]) for r in recs
               for i in (r.get("recipe_ingredients") or []) if not (i.get("quantity") or "").strip()]
    blank_n = [r["name"] for r in recs
               for i in (r.get("recipe_ingredients") or []) if not (i.get("ingredient_name") or "").strip()]
    weak = [r["name"] for r in recs if len((r.get("instructions") or "").strip()) < 30]
    chk("every recipe has >=1 ingredient", not no_ing, no_ing)
    chk("every ingredient has a quantity", not blank_q, blank_q[:12])
    chk("every ingredient has a name", not blank_n, blank_n[:12])
    chk("every recipe has useful instructions", not weak, weak)

    seen = {}
    for r in recs:
        seen.setdefault(norm_name(r["name"]), []).append(r["name"])
    dups = [v for v in seen.values() if len(v) > 1]
    chk("no duplicate recipe names", not dups, dups)

    orphans = [i["id"] for i in ings_all if i["recipe_id"] not in recipe_ids]
    chk("no orphan recipe_ingredients", not orphans, orphans[:12])

    bad_plan = [p["recipe_id"] for p in plans if p.get("recipe_id") and p["recipe_id"] not in recipe_ids]
    chk("meal_plan recipe links resolve", not bad_plan, bad_plan)

    bad_stock = [(r["name"], i["ingredient_name"]) for r in recs
                 for i in (r.get("recipe_ingredients") or [])
                 if i.get("stock_item_id") and i["stock_item_id"] not in stock_ids]
    chk("stock_item_id links resolve", not bad_stock, bad_stock[:12])

    THEMES = {"Mexican", "Thai", "Asian", "Crock Pot", "Grab Night", "Invention", "Open"}
    bad_theme = [(r["name"], r["theme"]) for r in recs if r.get("theme") is not None and r["theme"] not in THEMES]
    chk("all themes accepted (or null)", not bad_theme, bad_theme)

    if baseline_ids is not None:
        missing = [i for i in baseline_ids if i not in recipe_ids]
        chk("all baseline recipe IDs preserved", not missing, missing)

    allok = True
    for name, ok, detail in checks:
        print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  -> %r" % (detail,)))
        allok = allok and ok
    print("recipes=%d recipe_ingredients=%d" % (len(recs), len(ings_all)))
    print("RESULT=%s" % ("PASS" if allok else "FAIL"))
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
