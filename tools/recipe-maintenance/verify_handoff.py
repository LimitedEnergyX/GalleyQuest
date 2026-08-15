"""Read-only verification of the live GalleyQuest DB against the diet-cleanup
handoff. Prints TRUE row counts (count=exact, uncapped), the unlinked-ingredient
count, and runs ONE harmless insert+delete to confirm anon write access (which
also reveals the RLS posture). Never prints the anon key.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

print("project_ref:", _db.PROJECT_REF, "(expect bmonsbhzegertusvlqnb = live)")
print()

claimed = {"recipes": 233, "recipe_ingredients": 1000, "stock_items": 293}

print("=== TRUE row counts (PostgREST count=exact, uncapped) ===")
for t in _db.TABLES:
    n = _db.count(t)
    tag = ""
    if t in claimed:
        c = claimed[t]
        tag = "   handoff=%d  %s" % (c, "MATCH" if c == n else "MISMATCH (%+d)" % (n - c))
    print("  %-24s %6d%s" % (t, n, tag))

total_ri = _db.count("recipe_ingredients")
unlinked = _db.count("recipe_ingredients", "stock_item_id=is.null")
pct = (100.0 * unlinked / total_ri) if total_ri else 0
print()
print("=== unlinked ingredients (no stock_item_id) ===")
print("  %d of %d (%.1f%%)    handoff said 240 of 1000 (24%%)" % (unlinked, total_ri, pct))

print()
print("=== harmless write test (insert + delete a dummy stock_items row) ===")
tn = "__verify_write_test__"
st, body = _db.insert("stock_items", {"name": tn, "category": "household_other", "status": "OK"})
if st >= 400:
    print("  INSERT blocked -> HTTP %s: %s" % (st, str(body)[:200]))
    print("  => anon WRITE NOT available (RLS without anon policy, or revoked grants).")
else:
    new_id = body[0]["id"] if isinstance(body, list) and body else None
    print("  INSERT ok (HTTP %s) id=%s" % (st, new_id))
    dst, _dbody = _db.delete("stock_items", "id=eq.%s" % new_id)
    left = _db.count("stock_items", "name=eq.%s" % tn)
    print("  DELETE HTTP %s ; leftover test rows after cleanup: %d" % (dst, left))
    print("  => anon WRITE available; execution can proceed." if left == 0 else "  => WARN: cleanup left a row, investigate.")
