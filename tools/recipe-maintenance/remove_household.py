# -*- coding: utf-8 -*-
"""Sanitize stock to cooking/food only: delete every remaining non-food household
item (the household_other bucket now holds just paper towels + Lysol). Unlink any
recipe rows first (there should be none). GalleyQuest tracks food only.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

rows = _db.get("stock_items", "select=id,name,category")
targets = [r for r in rows if (r.get("category") or "") == "household_other"]
print("removing:", [t["name"] for t in targets])
for t in targets:
    _db.patch("recipe_ingredients", "stock_item_id=eq.%s" % t["id"], {"stock_item_id": None})
    _db.delete("stock_items", "id=eq.%s" % t["id"])

print("stock_items now:", _db.count("stock_items"))
print("household_other remaining:", _db.count("stock_items", "category=eq.household_other"))
