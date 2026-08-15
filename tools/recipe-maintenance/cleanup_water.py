# -*- coding: utf-8 -*-
"""Water cleanup. In GalleyQuest plain water is infinite: recipe 'water' rows are
left unlinked, so they never count as missing and never get shopped. Remove two
items that should not be tracked as shoppable ingredients:
  - 'Reserved pasta water' -- a cooking-step artifact, not a grocery item. Unlink
    its recipe row (back to infinite water), then delete the stock item.
  - 'Distilled Water (1 gal)' -- standalone household item, 0 recipe links. Delete.
Unlink-before-delete so no recipe row is orphaned.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

allrows = _db.get("stock_items", "select=id,name")
targets = [t for t in allrows if any(k in (t["name"] or "").lower()
                                     for k in ("reserved pasta water", "distilled water"))]
print("targets:", [t["name"] for t in targets])
for t in targets:
    st, b = _db.patch("recipe_ingredients", "stock_item_id=eq.%s" % t["id"], {"stock_item_id": None})
    n = len(b) if isinstance(b, list) else 0
    _db.delete("stock_items", "id=eq.%s" % t["id"])
    print("  removed %-26s (unlinked %d recipe row(s) -> infinite water)" % (t["name"], n))

print("stock_items now:", _db.count("stock_items"))
