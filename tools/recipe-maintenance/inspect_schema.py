"""Summarize the live schema by sampling one row per table (exact column names
+ example values to infer types). Read-only; reads config.js (via _db).
Usage: python inspect_schema.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

TABLES = ["stock_items", "recipes", "recipe_ingredients", "meal_plan",
          "grocery_extra_items", "grocery_dismissed_items"]


def main():
    for t in TABLES:
        rows = _db.get(t, "select=*&limit=1")
        n = _db.count(t)
        print("\n=== %s  (%d rows) ===" % (t, n))
        if rows:
            for k, v in rows[0].items():
                vv = repr(v)
                if len(vv) > 60:
                    vv = vv[:57] + "..."
                print("  %-22s %s" % (k, vv))
        else:
            print("  (no rows to sample)")


if __name__ == "__main__":
    main()
