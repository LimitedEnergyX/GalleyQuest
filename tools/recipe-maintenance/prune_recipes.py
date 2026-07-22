"""Rank recipes by how many SINGLE-USE ingredients they need (ingredients used in
no other recipe) = least pantry-efficient, and optionally prune the worst.
Skips any recipe currently on the meal plan.

Usage:
  python prune_recipes.py [N]           # dry-run: list the N worst offenders (default 30)
  python prune_recipes.py --apply N     # delete the N worst offenders (+ their ingredients)
"""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db


def main():
    apply = "--apply" in sys.argv
    nums = [int(a) for a in sys.argv[1:] if a.isdigit()]
    n = nums[0] if nums else 30
    recs = _db.get("recipes", "select=id,name,theme,notes,recipe_ingredients(stock_item_id)")
    usage = Counter()
    for r in recs:
        for sid in set(i["stock_item_id"] for i in (r.get("recipe_ingredients") or []) if i["stock_item_id"]):
            usage[sid] += 1
    planned = set(p["recipe_id"] for p in _db.get("meal_plan", "select=recipe_id") if p.get("recipe_id"))

    scored = []
    for r in recs:
        sids = set(i["stock_item_id"] for i in (r.get("recipe_ingredients") or []) if i["stock_item_id"])
        single = sum(1 for sid in sids if usage[sid] <= 1)
        cuisine = ""
        m = (r.get("notes") or "").split("\n")[0]
        if m.startswith("Cuisine:"):
            cuisine = m.split(":", 1)[1].strip()
        scored.append((single, len(sids), r["name"], r["id"], cuisine))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    candidates = [s for s in scored if s[3] not in planned][:n]

    print("%d recipes total. Worst offenders by single-use ingredients (top %d):" % (len(recs), n))
    for single, tot, name, rid, cuisine in candidates:
        print("  %-32s %d/%-2d single-use  [%s]" % (name[:32], single, tot, cuisine or "-"))

    if apply:
        for single, tot, name, rid, cuisine in candidates:
            _db.delete("recipe_ingredients", "recipe_id=eq.%s" % rid)
            _db.delete("recipes", "id=eq.%s" % rid)
        print("\nDELETED %d recipes. recipes now %d" % (len(candidates), _db.count("recipes")))


if __name__ == "__main__":
    main()
