"""Full send: apply the remaining anti-inflammatory ingredient-row edits.
 - processed_meat: SWAP to a fresh/uncured version when it's the main protein;
   OMIT (delete the row) when it's a cured accent (bacon/salami/pepperoni/...).
 - refined_sugar / cheese / butter / heavy_dairy_fat / processed_snack: halve the
   quantity (parse leading number, keep the unit). Non-numeric quantities skipped.
Rows on deleted desserts match nothing. Reports what changed.
"""
import os, sys, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".local", "anti_inflammatory"))
rows = list(csv.DictReader(open(os.path.join(OUT, "ai_rewrite_diffs.csv"), encoding="utf-8")))

SWAP = [  # (keyword, fresh replacement) -- checked in order (main-protein cases)
 ("corned beef", "fresh sliced roast beef"),
 ("frankfurter", "uncured chicken or turkey sausage"),
 ("wiener", "uncured chicken or turkey sausage"),
 ("hot dog", "uncured chicken or turkey sausage"),
 ("chorizo", "fresh lean ground pork or turkey (mild-seasoned)"),
 ("sausage", "fresh ground pork or turkey"),
 ("ham", "fresh cooked chicken or turkey"),
]
OMIT = ["bacon", "salami", "pepperoni", "prosciutto", "pancetta", "black pudding"]

def frac(x):
    for v, s in [(0.25,"1/4"),(0.5,"1/2"),(0.75,"3/4"),(0.333,"1/3"),(0.667,"2/3")]:
        if abs(x - v) < 0.02: return s
    return None

def fmt(x):
    if abs(x - round(x)) < 1e-6: return str(int(round(x)))
    whole = int(x); rem = x - whole
    f = frac(rem)
    if f: return (str(whole)+" "+f) if whole else f
    return ("%.2f" % x).rstrip("0").rstrip(".")

def halve(q):
    q = (q or "").strip()
    m = re.match(r"^(\d+\s+\d+/\d+|\d+/\d+|\d+\.\d+|\d+)\b", q)
    if not m: return None
    tok = m.group(1)
    if " " in tok:  # mixed "1 1/2"
        a, b = tok.split(); n, d = b.split("/"); val = int(a) + int(n)/int(d)
    elif "/" in tok:
        n, d = tok.split("/"); val = int(n)/int(d)
    else:
        val = float(tok)
    return (fmt(val/2) + q[m.end():]).strip()

meat_swap = meat_omit = reduced = skipped = 0
samples = []
for r in rows:
    cat = r["trigger_category"]; rid = r["ingredient_row_id"]; name = r["current_ingredient_name"]
    if cat == "processed_meat":
        n = name.lower()
        repl = next((v for kw, v in SWAP if kw in n), None)
        if repl:
            st, body = _db.patch("recipe_ingredients", "id=eq.%s" % rid, {"ingredient_name": repl})
            if st < 400 and body: meat_swap += 1
        elif any(k in n for k in OMIT):
            st, body = _db.delete("recipe_ingredients", "id=eq.%s" % rid)
            if st < 400: meat_omit += 1
        continue
    if cat in ("refined_sugar", "cheese", "butter", "heavy_dairy_fat", "processed_snack"):
        nq = halve(r["current_quantity"])
        if nq is None or nq == (r["current_quantity"] or "").strip():
            skipped += 1; continue
        st, body = _db.patch("recipe_ingredients", "id=eq.%s" % rid, {"quantity": nq})
        if st < 400 and body:
            reduced += 1
            if len(samples) < 10:
                samples.append("%-16s %-10s -> %-10s [%s]" % (name[:16], (r['current_quantity'] or '')[:10], nq[:10], r["recipe_name"][:22]))

print("processed meat  : swapped %d, omitted %d" % (meat_swap, meat_omit))
print("portions halved : %d   (skipped %d non-numeric quantities)" % (reduced, skipped))
for s in samples: print("   ", s)
print("live recipe_ingredients now:", _db.count("recipe_ingredients"))
