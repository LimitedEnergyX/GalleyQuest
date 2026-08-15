# -*- coding: utf-8 -*-
"""(1) Consolidate stock items that are the SAME ingredient with slightly different
names: pick the common (shortest) name, repoint every recipe_ingredient to it AND
rename those rows to the common name, merge status (OK>LOW>OUT), delete the
specialized duplicates. (2) Pantry reality check: set near-universal staples to OK.
FK repoint happens BEFORE delete so no link is lost.
"""
import os, sys, re
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

STRIP = {"fresh","cooked","raw","canned","tinned","frozen","dried","ground","shredded","minced",
 "diced","chopped","sliced","grated","boneless","skinless","lean","whole","baby","ripe","large",
 "small","mild","unsalted","salted","plain","cold","warm","softened","melted","drained","cubed",
 "peeled","crushed","breast","thigh","thighs","fillet","fillets","shank","drumstick","extra",
 "virgin","light","of","for","the","a"}
def singular(s):
    if s.endswith("oes"): return s[:-2]
    if s.endswith("ies") and len(s) > 4: return s[:-3]+"y"
    if s.endswith("ss"): return s
    if s.endswith("s") and len(s) > 3: return s[:-1]
    return s
def norm(name):
    s = re.sub(r"\(.*?\)"," ", (name or "").lower()).split(",")[0]
    s = re.sub(r"[^a-z0-9\s-]"," ", s)
    return singular(" ".join(t for t in s.split() if t not in STRIP).strip())

RANK = {"OK":3,"LOW":2,"OUT":1}
def best_status(items):
    return max((i.get("status") or "OUT" for i in items), key=lambda s: RANK.get(s,0))

STAPLES = {"olive oil","garlic","onion","salt","pepper","black pepper","turmeric","cumin","paprika",
 "cinnamon","oregano","thyme","rosemary","bay leaf","chili powder","chilli powder","curry powder",
 "ginger","rice","brown rice","pasta","flour","whole wheat flour","all-purpose flour","sugar",
 "brown sugar","honey","egg","milk","butter","vinegar","tamari","soy sauce","baking powder",
 "baking soda","cornstarch","oat","breadcrumb","tomato paste","lemon","lime","mustard",
 "garlic-infused olive oil","basil","cilantro","parsley","dill","olive or avocado oil"}

stock = _db.get("stock_items", "select=id,name,status")
groups = defaultdict(list)
for s in stock:
    groups[norm(s["name"])].append(s)

consolidated = deleted = repointed = 0
for key, items in groups.items():
    if len(items) < 2:
        continue
    canon = sorted(items, key=lambda i: (len(i["name"]), i["name"].lower()))[0]
    others = [i for i in items if i["id"] != canon["id"]]
    member_ids = [i["id"] for i in items]
    # repoint + rename every recipe row linked to any member -> canonical
    for j in range(0, len(member_ids), 60):
        chunk = member_ids[j:j+60]
        st, b = _db.patch("recipe_ingredients", "stock_item_id=in.(%s)" % ",".join(chunk),
                          {"stock_item_id": canon["id"], "ingredient_name": canon["name"]})
        if st < 400 and isinstance(b, list): repointed += len(b)
    # merge status onto canonical, then delete the specialized dupes
    _db.patch("stock_items", "id=eq.%s" % canon["id"], {"status": best_status(items)})
    oid = [i["id"] for i in others]
    for j in range(0, len(oid), 60):
        _db.delete("stock_items", "id=in.(%s)" % ",".join(oid[j:j+60]))
    consolidated += 1; deleted += len(others)
    if consolidated <= 15:
        print("  merge -> %-22s  (dropped: %s)" % (canon["name"], ", ".join(i["name"] for i in others)))

# ---- pantry reality check on surviving stock ----
survivors = _db.get("stock_items", "select=id,name,status")
ok_ids = [s["id"] for s in survivors if norm(s["name"]) in STAPLES and s["status"] != "OK"]
flipped = 0
for j in range(0, len(ok_ids), 60):
    st, b = _db.patch("stock_items", "id=in.(%s)" % ",".join(ok_ids[j:j+60]), {"status": "OK"})
    if st < 400 and isinstance(b, list): flipped += len(b)

print()
print("duplicate groups consolidated :", consolidated)
print("specialized stock items deleted:", deleted)
print("recipe rows repointed/renamed  :", repointed)
print("pantry staples flipped to OK   :", flipped)
print("stock items total now          :", _db.count("stock_items"))
print("unlinked ingredient rows       :", _db.count("recipe_ingredients","stock_item_id=is.null"))
