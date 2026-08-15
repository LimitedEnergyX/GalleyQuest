# -*- coding: utf-8 -*-
"""Second consolidation pass: merge SYNONYM / regional-variant stock items
(prawn=shrimp, aubergine=eggplant, courgette=zucchini, spring onion/scallion=green
onion, capsicum=bell pepper, garbanzo=chickpea, rocket=arugula, mange tout=snow pea).
Does NOT split on commas (avoids merging distinct branded flavours). Repoints +
renames recipe rows to the common name, merges status, deletes the duplicates.
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
SYN = [("spring onion","green onion"),("scallion","green onion"),("prawn","shrimp"),
 ("aubergine","eggplant"),("courgette","zucchini"),("capsicum","bell pepper"),
 ("garbanzo","chickpea"),("rocket","arugula"),("mange tout","snow pea"),("beetroot","beet")]
def singular(s):
    if s.endswith("oes"): return s[:-2]
    if s.endswith("ies") and len(s) > 4: return s[:-3]+"y"
    if s.endswith("ss"): return s
    if s.endswith("s") and len(s) > 3: return s[:-1]
    return s
def norm(name):
    s = re.sub(r"\(.*?\)"," ", (name or "").lower())          # keep commas (branded flavours stay distinct)
    s = re.sub(r"[^a-z0-9\s,-]"," ", s)
    for pat, rep in SYN:
        s = re.sub(r"\b"+pat+r"s?\b", rep, s)
    s = " ".join(t for t in s.split() if t not in STRIP).strip()
    return singular(s)

RANK = {"OK":3,"LOW":2,"OUT":1}
stock = _db.get("stock_items", "select=id,name,status")
groups = defaultdict(list)
for s in stock:
    groups[norm(s["name"])].append(s)

consolidated = deleted = repointed = 0
for key, items in groups.items():
    if len(items) < 2:
        continue
    canon = sorted(items, key=lambda i: (len(i["name"]), i["name"].lower()))[0]
    ids = [i["id"] for i in items]
    for j in range(0, len(ids), 60):
        st, b = _db.patch("recipe_ingredients", "stock_item_id=in.(%s)" % ",".join(ids[j:j+60]),
                          {"stock_item_id": canon["id"], "ingredient_name": canon["name"]})
        if st < 400 and isinstance(b, list): repointed += len(b)
    _db.patch("stock_items", "id=eq.%s" % canon["id"],
              {"status": max((i.get("status") or "OUT" for i in items), key=lambda s: RANK.get(s,0))})
    others = [i["id"] for i in items if i["id"] != canon["id"]]
    for j in range(0, len(others), 60):
        _db.delete("stock_items", "id=in.(%s)" % ",".join(others[j:j+60]))
    consolidated += 1; deleted += len(others)
    print("  merge -> %-18s (dropped: %s)" % (canon["name"], ", ".join(i["name"] for i in items if i["id"] != canon["id"])))

print()
print("synonym groups consolidated :", consolidated)
print("stock items deleted         :", deleted)
print("recipe rows repointed       :", repointed)
print("stock items total now       :", _db.count("stock_items"))
