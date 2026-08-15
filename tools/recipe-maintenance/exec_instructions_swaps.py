"""Instructions-text pass: mirror the deterministic ingredient swaps in the recipe
prose so it stops naming the old fats/oils. Safe, literal replacements only:
  <seed/veg> oil -> olive oil ; margarine -> butter ; shortening -> olive oil.
Meat/sugar/cheese prose is contextual and left for a manual pass. Reports changes.
"""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

recs = _db.get("recipes", "select=id,name,instructions")
oil_rx = re.compile(r"\b(canola|vegetable|sunflower|soybean|soya|corn|safflower|grapeseed|peanut)\s+oil\b", re.I)
marg_rx = re.compile(r"\bmargarine\b", re.I)
short_rx = re.compile(r"\bshortening\b", re.I)

changed = 0; samples = []
for r in recs:
    txt = r.get("instructions") or ""
    if not txt: continue
    new = oil_rx.sub("olive oil", txt)
    new = marg_rx.sub("butter", new)
    new = short_rx.sub("olive oil", new)
    if new != txt:
        st, body = _db.patch("recipes", "id=eq.%s" % r["id"], {"instructions": new})
        if st < 400 and body:
            changed += 1
            if len(samples) < 12: samples.append(r["name"])

print("recipes with instruction text updated:", changed)
for s in samples: print("   -", s)
