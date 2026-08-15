"""Execute the safe, aligned subset: delete the 23 dessert recipes (cascades to
their recipe_ingredients) + delete the 5 processed/cured-meat stock items.
IDs come from regen_anti_inflammatory.py's exec_targets.json. Verifies via counts.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".local", "anti_inflammatory"))
t = json.load(open(os.path.join(OUT, "exec_targets.json")))
cut_ids, stock_ids = t["dessert_cut_ids"], t["stock_remove_ids"]

b_rec, b_stock, b_ing = _db.count("recipes"), _db.count("stock_items"), _db.count("recipe_ingredients")

rec_ok = 0
for rid in cut_ids:
    st, body = _db.delete("recipes", "id=eq.%s" % rid)
    if st >= 400: print("  FAIL recipe %s -> %s %s" % (rid, st, str(body)[:120]))
    else: rec_ok += 1
stock_ok = 0
for sid in stock_ids:
    st, body = _db.delete("stock_items", "id=eq.%s" % sid)
    if st >= 400: print("  FAIL stock %s -> %s %s" % (sid, st, str(body)[:120]))
    else: stock_ok += 1

a_rec, a_stock, a_ing = _db.count("recipes"), _db.count("stock_items"), _db.count("recipe_ingredients")
print("recipes:            %d -> %d  (target -%d, HTTP-ok %d)" % (b_rec, a_rec, len(cut_ids), rec_ok))
print("stock_items:        %d -> %d  (target -%d, HTTP-ok %d)" % (b_stock, a_stock, len(stock_ids), stock_ok))
print("recipe_ingredients: %d -> %d  (cascade removed %d)" % (b_ing, a_ing, b_ing - a_ing))
print("VERIFY:", "OK" if (b_rec - a_rec == len(cut_ids) and b_stock - a_stock == len(stock_ids)) else "MISMATCH - check above")
