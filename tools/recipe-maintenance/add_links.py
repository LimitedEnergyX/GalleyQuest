# -*- coding: utf-8 -*-
"""Stock-link pass:
 1) Link every unlinked recipe_ingredient to an existing stock item when the
    normalized names match (fixes the 'in-stock/out-of-stock by wording' bug).
 2) For substantial ingredients with no stock item, ADD one (status OUT so it
    flows into the grocery list) and link the rows to it.
Grouped PATCHes (id=in.(...)) keep request count low. Reports before/after.
"""
import os, sys, re
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

STRIP = {"fresh","cooked","raw","canned","tinned","frozen","dried","ground","shredded",
 "minced","diced","chopped","sliced","grated","boneless","skinless","lean","whole","baby",
 "ripe","large","small","mild","unsalted","salted","plain","cold","warm","softened","melted",
 "drained","cubed","peeled","crushed","breast","thigh","thighs","fillet","fillets","shank",
 "drumstick","extra","virgin","light","of","for","the","a"}
SYN = {"cooked rice":"rice","white rice":"rice","cooked white rice":"rice",
 "garlic-infused olive oil":"olive oil","garlic infused olive oil":"olive oil"}
STOP = {"water","salt","pepper","black pepper","sea salt","salt and pepper","to taste","pinch","ice"}

def singular(s):
    if s.endswith("oes"): return s[:-2]
    if s.endswith("ies") and len(s) > 4: return s[:-3] + "y"
    if s.endswith("ss"): return s
    if s.endswith("s") and len(s) > 3: return s[:-1]
    return s

def norm(name):
    s = (name or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.split(",")[0]
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    toks = [t for t in s.split() if t not in STRIP]
    s = singular(" ".join(toks).strip())
    return SYN.get(s, s)

CAT = [("meat_seafood",["salmon","cod","fish","chicken","turkey","beef","pork","shrimp","prawn","tuna","haddock","meatball"]),
 ("bakery",["tortilla","bread","breadcrumb","bun","pita","naan"]),
 ("pantry_dry_goods",["rice","quinoa","oat","lentil","flour","noodle","pasta","broth","stock","coconut","tamari","soy","miso","curry paste","fish sauce","honey","sesame","bean","chickpea","cracker","syrup","vinegar"]),
 ("dairy_eggs",["egg","milk","yogurt","cheese","butter","cream"]),
 ("produce",["spinach","carrot","avocado","tomato","potato","onion","garlic","ginger","bok choy","pepper","cucumber","celery","pumpkin","squash","zucchini","fennel","banana","blueberr","berry","lemon","lime","basil","cilantro","parsley","dill","mushroom","cabbage","kale","scallion","leek"]),
 ("condiments_spices",["turmeric","cumin","paprika","cinnamon","oregano","thyme","rosemary","curry","oil","sauce","spice","herb","miso"])]
def guess_cat(nm):
    for cat, kws in CAT:
        if any(k in nm for k in kws): return cat
    return "household_other"

stock = _db.get("stock_items", "select=id,name")
ings  = _db.get("recipe_ingredients", "select=id,ingredient_name,stock_item_id")
before_unlinked = sum(1 for i in ings if not i["stock_item_id"])

existing = {}
for s in stock:
    existing.setdefault(norm(s["name"]), s["id"])

groups = defaultdict(list)
unmatched = defaultdict(list); disp = {}
for i in ings:
    if i["stock_item_id"]:
        continue
    nm = norm(i["ingredient_name"])
    if not nm:
        continue
    if nm in existing:
        groups[existing[nm]].append(i["id"])
    else:
        unmatched[nm].append(i["id"]); disp.setdefault(nm, nm)

to_add = [nm for nm in unmatched if nm not in STOP and len(nm) >= 2]
new_payload = [{"name": disp[nm][:1].upper() + disp[nm][1:], "category": guess_cat(nm), "status": "OUT"} for nm in to_add]
added = 0
if new_payload:
    st, body = _db.insert("stock_items", new_payload)
    if st >= 400 or not isinstance(body, list):
        raise SystemExit("stock insert failed: HTTP %s %s" % (st, str(body)[:200]))
    added = len(body)
    for nm, ins in zip(to_add, body):
        groups[ins["id"]].extend(unmatched[nm])

linked = 0
for sid, ids in groups.items():
    for j in range(0, len(ids), 80):
        chunk = ids[j:j+80]
        st, b = _db.patch("recipe_ingredients", "id=in.(%s)" % ",".join(chunk), {"stock_item_id": sid})
        if st < 400 and isinstance(b, list): linked += len(b)
        elif st >= 400: print("  patch fail HTTP %s %s" % (st, str(b)[:100]))

after_unlinked = _db.count("recipe_ingredients", "stock_item_id=is.null")
print("unlinked ingredient rows: %d -> %d" % (before_unlinked, after_unlinked))
print("new stock items added   : %d (status OUT)" % added)
print("ingredient rows linked  : %d" % linked)
print("stock_items total now   : %d" % _db.count("stock_items"))
