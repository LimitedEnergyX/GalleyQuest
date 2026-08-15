# -*- coding: utf-8 -*-
"""Fix the 'household_other' catch-all.

The auto-linker's guess_cat() fell back to household_other whenever it couldn't
keyword-match an item, so ~90 real food ingredients landed in the same bucket as
genuine household goods (paper towels, cleaning supplies). This moves each food
item to its correct supermarket aisle via grouped PATCHes and leaves only true
non-food household items behind. Backs the DB up first. Category-field only --
no recipe links are touched.
"""
import os, sys, re
from collections import defaultdict
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

# Genuine non-food / household consumables -> stay in household_other (matched by substring).
STAY_SUB = ["papertowel", "lysol", "sanitizer", "distilledwater", "detergent", "bleach", "napkin"]

CATS = {
 "produce": ["Beetroot","Birds-eye chilly","Broccoli","Challot","Chinese broccoli",
   "Galangal","Green chile","Green chilli","Jerusalem artichoke","Mint","Okra",
   "Pak choi","Parsnip","Pea","Red chilli","Red chilly","Shallot","Snow pea",
   "Tomatillo","Marinated tofu","Tofu"],
 "meat_seafood": ["Clam","Flank or skirt steak","Flank steak","Lamb","Lamb leg",
   "Lamb mince","Mussel","Sausage","Seafood mix","Squid","Wieners or frankfurter"],
 "pantry_dry_goods": ["Bulgur wheat","Farfalle","Fettuccine","Golden raisin","Grit",
   "Lasagne sheet","Linguine","Peanut","Shelled hazelnut","Split pea","Starch",
   "Walnut","Ziti"],
 "condiments_spices": ["Cajun","Caper","Cardamom","Chili seasoning","Chilli flake",
   "Coriander","Doubanjiang","Fajita seasoning","Galangal paste","Garam masala",
   "Green olive","Italian dressing","Italian seasoning","Kosher salt",
   "Prepared horseradish","Red chilli flake","Saffron","Sage","Star anise",
   "Tahini paste","Vanilla extract","Vinaigrette dressing"],
 "canned_goods": ["Hominy","Passata","Pineapple chunk","Sardine","Sauerkraut","Water chestnut"],
 "dairy_eggs": ["Creme fraiche","Gruyere","Mascarpone","Pecorino"],
 "bakery": ["9-inch unbaked pastry shell","Baguette","English muffin","Pie crust","Pizza dough"],
 "beverages": ["Cooking wine","Dry sherry","Dry white wine","Marsala wine","Sake","Vodka","White wine"],
 "snacks": ["Corn chip"],
}
FALLBACK = [("gruy", "dairy_eggs")]  # diacritic-safe net for Gruyere

def norm(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())
target = {norm(nm): cat for cat, names in CATS.items() for nm in names}

# ---- backup first ----
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dest = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
        "..", "..", ".local", "backups", ts + "-pre-recategorize"))
m = _db.backup(dest, purpose="recategorize household_other stock items")
print("backup ->", dest)
print("  stock_items:", m["tables"].get("stock_items"), "| recipe_ingredients:", m["tables"].get("recipe_ingredients"))

rows = _db.get("stock_items", "select=id,name&category=eq.household_other")
moves = defaultdict(list); unmatched = []
for r in rows:
    n = norm(r["name"])
    if any(t in n for t in STAY_SUB):
        continue
    if n in target:
        moves[target[n]].append(r["id"])
    else:
        hit = next((c for c, names in CATS.items() for nm in names
                    if len(norm(nm)) >= 4 and norm(nm) in n), None) \
              or next((c for tok, c in FALLBACK if tok in n), None)
        (moves[hit].append(r["id"]) if hit else unmatched.append(r["name"]))

moved = 0
print("\nmoves:")
for cat, ids in sorted(moves.items()):
    for j in range(0, len(ids), 80):
        st, b = _db.patch("stock_items", "id=in.(%s)" % ",".join(ids[j:j+80]), {"category": cat})
        if st < 400 and isinstance(b, list): moved += len(b)
        else: print("  PATCH FAIL", cat, st, str(b)[:120])
    print("  %-18s %d" % (cat, len(ids)))

print("\nmoved total:", moved)
print("still in household_other:")
for r in _db.get("stock_items", "select=name&category=eq.household_other&order=name"):
    print("   -", r["name"])
if unmatched:
    print("UNMATCHED (left as-is, review):", unmatched)
