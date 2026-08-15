"""Read-only: quantify how incomplete the handoff's rewrite diffs are, given the
1000-vs-2090 truncation. Approx re-scan of ALL live recipe_ingredients using the
handoff's documented Crohn's+weight ingredient-level rules, compared to the 121-row
diff file. Also checks ID freshness. Never mutates anything.
"""
import os, sys, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

TMP = r"C:\Users\RDPJarvis\AppData\Local\Temp"
def load_csv(name):
    with open(os.path.join(TMP, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

diffs   = load_csv("crohns_weight_rewrite_diffs.csv")
stockrm = load_csv("crohns_stock_removal_1.csv")
v3      = load_csv("live_recipe_review_v3_priority.csv")

diff_ids  = set(r["ingredient_row_id"] for r in diffs)
stock_ids = set(r["stock_item_id"] for r in stockrm)
cut_ids    = set(r["recipe_id"] for r in v3 if r["verdict"].strip().lower() == "cut")
change_ids = set(r["recipe_id"] for r in v3 if r["verdict"].strip().lower() == "change")

ings = _db.get("recipe_ingredients", "select=id,recipe_id,ingredient_name")
rec_ids_live   = set(r["id"] for r in _db.get("recipes", "select=id"))
stock_ids_live = set(r["id"] for r in _db.get("stock_items", "select=id"))
ing_ids_live   = set(r["id"] for r in ings)

# approximate documented Crohn's+weight ingredient-level triggers (word-boundary + exceptions)
TRIG = {
 "processed_meat": (r"\b(bacon|sausage|chorizo|salami|pepperoni|frankfurter|wiener|prosciutto|pancetta|jerky|ham|corned beef|black pudding|hot dog)\b", []),
 "whole_nuts":     (r"\b(peanut|walnut|almond|cashew|pistachio|hazelnut|pecan|macadamia)\b", ["peanut butter","almond butter","almond milk","almond flour","almond extract"]),
 "corn":           (r"\bcorn\b", ["corn tortilla","cornstarch","corn starch","corn flour","cornflour","cornbread","cornmeal","corn oil"]),
 "dried_fruit":    (r"\b(raisin|sultana|currant)\b|dried (cranberr|apricot|fruit)", []),
 "cruciferous":    (r"\b(cabbage|kale|broccoli|brussels)\b", []),
 "whole_wheat":    (r"\b(whole wheat|wholemeal|bran)\b", []),
 "seeds":          (r"\b(sesame seed|seeds?)\b", ["seed oil","seedless"]),
 "heavy_dairy_fat":(r"\b(sour cream|heavy cream|double cream|cream cheese|mascarpone|creme fraiche|condensed milk|butter)\b", ["peanut butter","butter bean","buttermilk","butternut","nut butter","almond butter","apple butter","cocoa butter","butter lettuce"]),
 "cheese":         (r"\b(cheese|parmesan|mozzarella|feta|monterey|provolone|pecorino)\b", []),
 "spicy":          (r"\b(chile|chili|chilli|cayenne|hot sauce|jalapeno|jalape\u00f1o|harissa|gochujang|szechuan|sichuan|sriracha|tabasco|chipotle)\b", []),
 "added_sugar":    (r"\b(sugar|syrup|molasses)\b", ["sugar snap"]),
}
comp = {k: (re.compile(p, re.I), ex) for k, (p, ex) in TRIG.items()}

def is_trigger(name):
    if not name: return False
    n = name.lower()
    for rx, ex in comp.values():
        if rx.search(name):
            if any(e in n for e in ex):
                stripped = n
                for e in ex: stripped = stripped.replace(e, "")
                if not rx.search(stripped):
                    continue
            return True
    return False

matched = [r for r in ings if is_trigger(r["ingredient_name"])]
matched_ids = set(r["id"] for r in matched)
change_with_diff = set(r["recipe_id"] for r in diffs)

print("=== truncation impact on the 121-row rewrite diffs ===")
print("live recipe_ingredients rows:            ", len(ings))
print("full-scan trigger-bearing rows (approx): ", len(matched))
print("rows the handoff diff actually edits:    ", len(diffs))
print("  of the full-scan hits, covered by diff:", len(diff_ids & matched_ids))
print("  MISSED (trigger rows NOT in the diff):  ", len(matched_ids - diff_ids))
print()
print("=== ID freshness (do the handoff's targets still exist?) ===")
print("diff ingredient_row_ids present in live: %d / %d" % (len(diff_ids & ing_ids_live), len(diff_ids)))
print("stock removal ids present in live:       %d / %d" % (len(stock_ids & stock_ids_live), len(stock_ids)))
print("Cut recipe ids present in live:          %d / %d" % (len(cut_ids & rec_ids_live), len(cut_ids)))
print("Change recipe ids present in live:       %d / %d" % (len(change_ids & rec_ids_live), len(change_ids)))
print()
print("=== coverage gaps ===")
print("Change recipes (v3):                     ", len(change_ids))
print("Change recipes with >=1 diff row:        ", len(change_with_diff & change_ids))
print("Change recipes with NO diff row:         ", len(change_ids - change_with_diff))
