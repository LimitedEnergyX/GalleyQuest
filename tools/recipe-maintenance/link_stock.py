"""Auto-link recipe ingredients to pantry Stock items by name. Precision-first.

Two link sources, both safe:
  - exact   : ingredient's normalized token set == a stock item's (e.g.
              "black pepper" -> "Black pepper", "beef broth" -> "Beef broth").
  - curated : a hand-verified synonym map for common generics / brand names /
              spelling variants ("salt" -> "Morton iodized salt",
              "spring onions" -> "Green onions", "cornstarch" -> "Corn starch").

Deliberately does NOT guess generic->specific variants (e.g. "onion" -> "Green
onions", "sugar" -> "Brown sugar") -- a wrong link is worse than none. Anything
not matched stays a shopping-list item.

--dry-run (default): report proposed links; writes nothing.
--apply: set recipe_ingredients.stock_item_id for matched, currently-unlinked
         rows (grouped PATCHes). Never overwrites an existing link.
"""
import os, sys, re, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

STOP = {"chopped", "diced", "sliced", "minced", "drained", "softened", "beaten",
        "grated", "cooked", "halved", "quartered", "peeled", "crumbled", "shredded",
        "melted", "husked", "cubed", "rinsed", "boiled", "fresh", "large", "small",
        "ripe", "whole", "dried", "frozen", "canned", "plain", "and", "or", "of",
        "for", "with", "into", "to", "taste", "a", "the", "pounded"}

# Hand-verified against the live pantry. Keys are natural text (normalized at
# load); values must match a stock item name exactly.
CURATED_RAW = {
    "salt": "Morton iodized salt", "sea salt": "Mediterranean sea salt, coarse",
    "pepper": "Black pepper", "butter": "Unsalted butter", "milk": "2% milk",
    "flour": "All-purpose flour", "cornstarch": "Corn starch",
    "chicken stock": "Chicken broth", "beef stock": "Beef broth",
    "spring onions": "Green onions", "scallions": "Green onions",
    "olive oil": "Virgin olive oil", "extra virgin olive oil": "Virgin olive oil",
    "coconut oil": "Virgin coconut oil", "soy sauce": "Less sodium soy sauce",
    "light soy sauce": "Less sodium soy sauce", "dark soy sauce": "Less sodium soy sauce",
    "cream cheese": "Philadelphia cream cheese", "peanut butter": "Jif peanut butter",
    "honey": "Local Texas honey", "panko": "Japanese-style breadcrumbs (panko)",
    "panko breadcrumbs": "Japanese-style breadcrumbs (panko)",
    "breadcrumbs": "Japanese-style breadcrumbs (panko)",
    "teriyaki sauce": "Less sodium teriyaki sauce", "rolled oats": "Old fashioned rolled oats",
    "oats": "Old fashioned rolled oats", "couscous": "Pearl couscous",
    "yeast": "Active dry yeast", "rice": "Basmati rice", "rosemary": "Rosemary leaves",
    "sesame seed oil": "Sesame oil", "spring onion": "Green onions",
}


def singular(w):
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def tokens(name):
    base = (name or "").split(",")[0].lower()
    base = re.sub(r"[^a-z0-9 ]+", " ", base)
    return [singular(t) for t in base.split() if t and t not in STOP]


def key_of(name):
    return " ".join(tokens(name))


def main():
    apply = "--apply" in sys.argv
    stock_rows = _db.get("stock_items", "select=id,name")
    stock = [(s["id"], s["name"], tokens(s["name"])) for s in stock_rows]
    by_name = {s["name"]: s["id"] for s in stock_rows}
    curated = {}
    for k, v in CURATED_RAW.items():
        if v in by_name:
            curated[key_of(k)] = (by_name[v], v)
        else:
            print("WARN curated target not in pantry: %r" % v)

    ings = _db.get("recipe_ingredients", "select=id,ingredient_name,stock_item_id")
    unlinked = [i for i in ings if not i["stock_item_id"]]

    matches, unmatched = [], []
    tier_c = {"exact": 0, "curated": 0}
    for i in unlinked:
        toks = tokens(i["ingredient_name"])
        k = " ".join(toks)
        hit = None
        if k in curated:
            hit = (curated[k][0], curated[k][1], "curated")
        elif toks:
            tset, head = set(toks), toks[-1]
            for sid, sname, s_toks in stock:
                if s_toks and s_toks[-1] == head and set(s_toks) == tset:
                    hit = (sid, sname, "exact")
                    break
        if hit:
            tier_c[hit[2]] += 1
            matches.append({"ing_id": i["id"], "ingredient": i["ingredient_name"],
                            "stock_id": hit[0], "stock_name": hit[1], "tier": hit[2]})
        else:
            unmatched.append(i["ingredient_name"])

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance", ts + "-stocklink")
    os.makedirs(outdir, exist_ok=True)
    json.dump(matches, open(os.path.join(outdir, "stock-link-matches.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    from collections import Counter
    recipes_touched = None
    print("MODE=%s" % ("apply" if apply else "dry-run"))
    print("unlinked ingredients: %d" % len(unlinked))
    print("  will link: %d  (exact=%d, curated=%d; %d distinct stock items)" % (
        len(matches), tier_c["exact"], tier_c["curated"], len(set(m["stock_id"] for m in matches))))
    print("  left unlinked (shopping-list): %d" % len(unmatched))
    print("\nsample links (ingredient -> stock item) [tier]:")
    for m in matches[:28]:
        print("  %-26s -> %-24s [%s]" % (m["ingredient"][:26], m["stock_name"][:24], m["tier"]))
    print("\ntop still-unlinked:")
    for name, c in Counter(n.lower() for n in unmatched).most_common(18):
        print("  %-28s x%d" % (name[:28], c))
    print("\nOUTDIR=%s" % outdir)

    if apply:
        by_stock = {}
        for m in matches:
            by_stock.setdefault(m["stock_id"], []).append(m["ing_id"])
        patched, failed = 0, 0
        for sid, ids in by_stock.items():
            for j in range(0, len(ids), 80):
                chunk = ids[j:j + 80]
                st, resp = _db.patch("recipe_ingredients", "id=in.(%s)" % ",".join(chunk), {"stock_item_id": sid})
                if st in (200, 204):
                    patched += len(chunk)
                else:
                    failed += len(chunk)
                    print("PATCH failed for stock %s: %s %r" % (sid, st, resp))
        now = len([i for i in _db.get("recipe_ingredients", "select=id,stock_item_id") if i["stock_item_id"]])
        print("\nAPPLIED: patched=%d failed=%d ; ingredients now linked=%d / %d" % (patched, failed, now, len(ings)))


if __name__ == "__main__":
    main()
