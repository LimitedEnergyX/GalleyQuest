"""Read-only: regenerate the diet-cleanup edit set under an ANTI-INFLAMMATORY
framework on the full live data (2090 ingredient rows). Produces corrected CSVs +
a summary. Nothing is written to the database here.

Framework:
  CUT (inflammatory) -> rewrite/remove:
    seed/vegetable oil -> olive/avocado oil
    processed/cured meat -> fresh unprocessed cut (or omit if minor)
    refined sugar/syrup -> reduce/omit
    refined white/AP flour -> whole-grain flour
    shortening/margarine (trans) -> olive oil/butter
    heavy dairy fat (heavy/double cream, sour cream, mascarpone) -> reduce/lighter
    excess cheese / butter -> reduce (keep as accent)
    processed carb snacks (chips/crackers) -> reduce/omit
  KEEP / FAVOR (anti-inflammatory) -> never edited:
    nuts, seeds, whole grains, cruciferous, leafy greens, legumes, allium,
    tomato, ginger/turmeric, herbs & spices (incl chili/cayenne), fish, olive oil, fruit
"""
import os, sys, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

TMP = r"C:\Users\RDPJarvis\AppData\Local\Temp"
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".local", "anti_inflammatory"))
os.makedirs(OUT, exist_ok=True)

def load_csv(name):
    with open(os.path.join(TMP, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

# ---- inflammatory ingredient rules: (category, regex, exclusions, proposed_change) ----
RULES = [
 ("seed_veg_oil", r"\b(canola|vegetable|corn|soybean|soya|sunflower|safflower|grapeseed|peanut) oil\b|\boil for (deep )?frying\b|\bfrying oil\b", [], "Swap to olive or avocado oil"),
 ("processed_meat", r"\b(bacon|sausage|chorizo|salami|pepperoni|prosciutto|pancetta|bologna|frankfurter|wiener|jerky|corned beef|black pudding|hot dog|deli meat)\b|\bham\b", ["mushroom"], "Swap to a fresh, unprocessed cut of the same protein (or omit if minor)"),
 ("refined_flour", r"\b(all[- ]?purpose flour|plain flour|white flour|cake flour|white bread flour)\b", [], "Swap to whole-wheat / whole-grain flour"),
 ("trans_fat", r"\b(shortening|margarine|hydrogenated)\b", [], "Swap to olive oil or butter"),
 ("refined_sugar", r"\b(sugar|brown sugar|powdered sugar|icing sugar|caster sugar|corn syrup|maple syrup|syrup|molasses|golden syrup)\b", ["sugar snap"], "Reduce by half, or omit if a minor flavour addition"),
 ("heavy_dairy_fat", r"\b(heavy cream|double cream|sour cream|mascarpone|clotted cream|condensed milk|creme fraiche|cr\u00e8me fra\u00eeche)\b", [], "Reduce, or use a lighter version"),
 ("butter", r"\bbutter\b", ["peanut butter","almond butter","nut butter","cocoa butter","apple butter","butter bean","buttermilk","butternut","butter lettuce"], "Reduce, or use olive oil"),
 ("cheese", r"\b(shredded cheese|cream cheese|parmesan|mozzarella|monterey|provolone|pecorino|feta|blue cheese|cheddar|cheese)\b", [], "Reduce (use less; keep as an accent, not the base)"),
 ("processed_snack", r"\b(tortilla chips|corn chips|potato chips|\bchips\b|crackers)\b", [], "Reduce or omit"),
]
COMP = [(c, re.compile(p, re.I), ex, ch) for (c, p, ex, ch) in RULES]

def classify(name):
    if not name: return None
    n = name.lower()
    for c, rx, ex, ch in COMP:
        if rx.search(name):
            if ex:
                stripped = n
                for e in ex: stripped = stripped.replace(e, "")
                if not rx.search(stripped):
                    continue
            return (c, ch)
    return None

# ---- pull live ----
recs = {r["id"]: r for r in _db.get("recipes", "select=id,name,theme")}
ings = _db.get("recipe_ingredients", "select=id,recipe_id,ingredient_name,quantity")

# ---- ingredient-row rewrites (full data) ----
diffs = []
cat_counts = {}
for r in ings:
    hit = classify(r["ingredient_name"])
    if not hit: continue
    c, ch = hit
    cat_counts[c] = cat_counts.get(c, 0) + 1
    rec = recs.get(r["recipe_id"], {})
    diffs.append({"recipe_id": r["recipe_id"], "recipe_name": rec.get("name",""), "theme": rec.get("theme",""),
                  "ingredient_row_id": r["id"], "current_ingredient_name": r["ingredient_name"],
                  "current_quantity": r.get("quantity",""), "trigger_category": c, "proposed_change": ch})

with open(os.path.join(OUT, "ai_rewrite_diffs.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(diffs[0].keys())); w.writeheader(); w.writerows(diffs)

# ---- dessert cut list (reuse handoff's hand-curated desserts; framework-agnostic) ----
v3 = load_csv("live_recipe_review_v3_priority.csv")
dessert_cuts = [r for r in v3 if r["verdict"].strip().lower()=="cut" and r["severity"].strip().lower()=="dessert"]

# ---- revised stock removal: processed/cured meat only (KEEP nuts + whole wheat, per anti-inflammatory) ----
stock = load_csv("crohns_stock_removal_1.csv")
stock_remove = [r for r in stock if r["trigger_type"] in ("processed_meat","processed_meat_jerky")]
stock_keep   = [r for r in stock if r["trigger_type"] not in ("processed_meat","processed_meat_jerky")]

with open(os.path.join(OUT, "ai_stock_removal.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(stock_remove[0].keys())); w.writeheader(); w.writerows(stock_remove)

# ---- report ----
print("== INGREDIENT REWRITES (full 2090 rows, anti-inflammatory) ==")
print("  total rewrite rows:", len(diffs), " across", len({d['recipe_id'] for d in diffs}), "recipes")
for c in sorted(cat_counts, key=lambda k:-cat_counts[k]):
    print("    %-16s %4d" % (c, cat_counts[c]))
print()
print("== DESSERT CUTS (delete) ==", len(dessert_cuts))
for r in dessert_cuts: print("    -", r["name"])
print()
print("== STOCK REMOVE (processed/cured meat only) ==", len(stock_remove))
for r in stock_remove: print("    -", r["stock_item_name"])
print("== STOCK KEPT (reversed - anti-inflammatory or neutral) ==", len(stock_keep))
for r in stock_keep: print("    +", r["stock_item_name"], "(%s)" % r["trigger_type"])
print()
print("wrote:", OUT)
print("  ai_rewrite_diffs.csv, ai_stock_removal.csv")
# emit machine-usable id lists for the executor
import json
json.dump({"dessert_cut_ids":[r["recipe_id"] for r in dessert_cuts],
           "stock_remove_ids":[r["stock_item_id"] for r in stock_remove]},
          open(os.path.join(OUT,"exec_targets.json"),"w"), indent=2)
