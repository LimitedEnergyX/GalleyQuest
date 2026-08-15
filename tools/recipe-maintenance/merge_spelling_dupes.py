# -*- coding: utf-8 -*-
"""Merge four confirmed spelling-variant duplicate stock items into their canonical
form: repoint + rename every linked recipe_ingredient to the canonical, merge
status (OK>LOW>OUT), delete the duplicate. Explicitly scoped to these exact pairs
-- no fuzzy matching -- so coriander/cilantro (genuinely different) is untouched.
Backup already captured by the preceding recategorize run.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

RANK = {"OK": 3, "LOW": 2, "OUT": 1}
PAIRS = [("Shallot", "Challot"),
         ("Red chilli", "Red chilly"),
         ("Green chile", "Green chilli"),
         ("Long-grain white rice", "Long Grain White Rice")]

rows = _db.get("stock_items", "select=id,name,status")
byname = {r["name"]: r for r in rows}
for canon, dupe in PAIRS:
    c, d = byname.get(canon), byname.get(dupe)
    if not c or not d:
        print("  skip (missing): %s / %s" % (canon, dupe)); continue
    st, b = _db.patch("recipe_ingredients", "stock_item_id=eq.%s" % d["id"],
                      {"stock_item_id": c["id"], "ingredient_name": canon})
    n = len(b) if isinstance(b, list) else 0
    best = max([c["status"] or "OUT", d["status"] or "OUT"], key=lambda s: RANK.get(s, 0))
    _db.patch("stock_items", "id=eq.%s" % c["id"], {"status": best})
    _db.delete("stock_items", "id=eq.%s" % d["id"])
    print("  merged %-24s <- %-22s (%d recipe row(s), status %s)" % (canon, dupe, n, best))

print("stock_items now:", _db.count("stock_items"))
