"""One-shot migration: load a backup export into the NEW Supabase project.
config.js must already be repointed to the new project. Inserts in FK order,
preserves every id/timestamp, and tags existing meal_plan rows with slot='Dinner'.
Usage: python migrate_to_new_project.py <backup_dir>
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

NEW_REF = "bmonsbhzegertusvlqnb"
ORDER = ["stock_items", "recipes", "recipe_ingredients", "meal_plan",
         "grocery_extra_items", "grocery_dismissed_items"]


def insert_batched(t, rows, batch=400):
    done = 0
    for i in range(0, len(rows), batch):
        chunk = rows[i:i + batch]
        st, body = _db.insert(t, chunk)
        if st >= 400:
            raise SystemExit("INSERT %s failed at row %d: HTTP %s %s" % (t, i, st, str(body)[:400]))
        done += len(chunk)
    return done


def main():
    backup = sys.argv[1]
    # Safety: never run against the old project by accident.
    assert _db.PROJECT_REF == NEW_REF, "config.js is NOT pointing at the new project (ref=%s)" % _db.PROJECT_REF
    print("target project:", _db.PROJECT_REF)
    for t in ORDER:
        rows = json.load(open(os.path.join(backup, t + ".json"), encoding="utf-8"))
        if t == "meal_plan":
            for r in rows:
                if not r.get("slot"):
                    r["slot"] = "Dinner"
        n = insert_batched(t, rows)
        print("  %-24s inserted %d / %d" % (t, n, len(rows)))
    print("--- verify counts on new project ---")
    for t in ORDER:
        print("  %-24s %d rows" % (t, _db.count(t)))


if __name__ == "__main__":
    main()
