"""Apply the deterministic anti-inflammatory ingredient-name swaps only:
  seed/vegetable oil        -> olive oil (or 'olive or avocado oil' if it was frying oil)
  refined white/AP flour    -> whole wheat flour
  shortening                -> olive oil ; margarine -> butter
Quantities are preserved. Rows on already-deleted desserts simply match nothing.
Reads ai_rewrite_diffs.csv; reports how many rows actually changed.
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".local", "anti_inflammatory"))
rows = list(csv.DictReader(open(os.path.join(OUT, "ai_rewrite_diffs.csv"), encoding="utf-8")))

def new_name(cat, name):
    n = name.lower()
    if cat == "seed_veg_oil":
        return "olive or avocado oil" if "fry" in n else "olive oil"
    if cat == "refined_flour":
        return "whole wheat flour"
    if cat == "trans_fat":
        return "olive oil" if "shortening" in n else "butter"
    return None

applied, samples = 0, []
for r in rows:
    if r["trigger_category"] not in ("seed_veg_oil", "refined_flour", "trans_fat"):
        continue
    nn = new_name(r["trigger_category"], r["current_ingredient_name"])
    st, body = _db.patch("recipe_ingredients", "id=eq.%s" % r["ingredient_row_id"], {"ingredient_name": nn})
    if st < 400 and isinstance(body, list) and body:
        applied += 1
        if len(samples) < 12:
            samples.append("%-22s -> %-22s [%s]" % (r["current_ingredient_name"][:22], nn, r["recipe_name"]))
    elif st >= 400:
        print("  FAIL %s -> %s %s" % (r["ingredient_row_id"], st, str(body)[:100]))

print("deterministic swaps applied:", applied)
for s in samples: print("   ", s)
