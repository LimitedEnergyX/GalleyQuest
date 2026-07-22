"""Make every recipe ingredient trackable: canonicalize the still-unlinked
ingredients into proper pantry Stock items (with variant structure), add the
missing ones as status OUT, and link every ingredient to its stock item.

Canonicalization: strip prep words / parentheticals / comma-suffixes, then apply
a variant map (bare "onion" -> Yellow onion, "sugar" -> White sugar, "garlic" ->
Garlic cloves; "red onion"/"powdered sugar"/"garlic powder" stay distinct).
Everything else becomes a tidy Title-cased item. Non-items like "water" are
skipped. New items get a heuristic category from the existing pantry vocabulary.

--dry-run (default): show what would be added + linked; writes nothing.
--apply: insert the new OUT stock items, then link all unlinked ingredients.
"""
import os, sys, re, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

STOP = {"chopped", "diced", "sliced", "minced", "drained", "softened", "beaten",
        "grated", "cooked", "halved", "quartered", "peeled", "crumbled", "shredded",
        "melted", "husked", "cubed", "rinsed", "boiled", "fresh", "large", "small",
        "ripe", "whole", "dried", "frozen", "canned", "plain", "and", "or", "of",
        "for", "with", "into", "to", "taste", "a", "the", "pounded"}

SKIP = {"water", "ice", "salt and pepper", "salt pepper", "oil for frying",
        "oil for", "vegetable oil for frying"}

# Variant map (keys are normalized: lowercased, prep stripped, singularized).
CANON = {
    "onion": "Yellow onion", "yellow onion": "Yellow onion", "brown onion": "Yellow onion",
    "red onion": "Red onion", "white onion": "White onion",
    "sugar": "White sugar", "white sugar": "White sugar", "granulated sugar": "White sugar",
    "caster sugar": "White sugar", "powdered sugar": "Powdered sugar",
    "icing sugar": "Powdered sugar", "confectioner sugar": "Powdered sugar",
    "demerara sugar": "Raw sugar", "raw sugar": "Raw sugar",
    "garlic": "Garlic cloves", "garlic clove": "Garlic cloves",
    "oil": "Vegetable oil", "vegetable oil": "Vegetable oil", "cooking oil": "Vegetable oil",
    "high heat cooking oil": "Vegetable oil", "canola oil": "Vegetable oil",
    # map to existing pantry staples (these link, not add)
    "bicarbonate soda": "Baking soda", "bicarbonate of soda": "Baking soda",
    "plain flour": "All-purpose flour", "chicken stock": "Chicken broth",
    "egg": "Eggs", "bell pepper": "Bell pepper", "green bell pepper": "Bell pepper",
    "chicken breast": "Chicken breast", "boneless chicken breast": "Chicken breast",
    "skinless chicken breast": "Chicken breast", "chicken thigh": "Chicken thighs",
    "cooked chicken": "Cooked chicken",
}

# Categories = the app's 12 grocery departments (SECTIONS in index.html), which
# mirror a standard supermarket layout. categorize() below maps to them.


def singular(w):
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("oes"):
        return w[:-2]                     # potatoes->potato, tomatoes->tomato
    if len(w) > 4 and w.endswith("es") and w[-3] in "sxzh":
        return w[:-2]                     # dishes->dish, boxes->box
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def norm(name):
    base = re.sub(r"\([^)]*\)", " ", (name or "").lower())
    base = base.split(",")[0]
    base = re.split(r"\s+or\s+|/", base)[0]      # first option only
    base = re.sub(r"[^a-z0-9 ]+", " ", base)
    toks = [singular(t) for t in base.split() if t and t not in STOP]
    return toks


def canonical(name):
    toks = norm(name)
    if not toks:
        return None
    key = " ".join(toks)
    if key in SKIP:
        return None
    if key in CANON:
        return CANON[key]
    if any(ch.isdigit() for ch in key) or len(toks) > 4:
        return None                              # too messy to auto-add cleanly
    return key[:1].upper() + key[1:]


def categorize(name):
    """Map a stock item name to one of the app's grocery-department categories.
    Ordered rules (first match wins). The top block handles substring traps
    (soup->canned not meat/dairy, bun->bakery not "ham" meat, corn chip->snacks
    not produce, seasonings->condiments not produce)."""
    n = name.lower()
    def has(*kw):
        return any(k in n for k in kw)

    # --- overrides for substring traps ---
    if has("soup"):                                              # canned/boxed soups
        return "canned_goods"
    if has("peanut butter", "almond butter", "nut butter", "cashew butter", "sunflower butter"):
        return "condiments_spices"
    if has("baking powder", "baking soda", "bicarbonate"):
        return "pantry_dry_goods"
    if has("breadcrumb", "bread crumb", "panko"):
        return "pantry_dry_goods"
    if has("cornstarch", "corn starch", "cornmeal", "corn meal", "cornflour", "corn flour"):
        return "pantry_dry_goods"
    if has("sugar") and not has("syrup"):                        # incl. powdered sugar
        return "pantry_dry_goods"
    if has("eggplant", "aubergine", "squash", "butternut", "courgette"):
        return "produce"
    if has("lemon juice", "lime juice"):                         # cooking acids, not drinks
        return "condiments_spices"
    if has("black pepper", "white pepper", "peppercorn"):
        return "condiments_spices"
    if has("chocolate", "cocoa"):                                # baking staple ("cola" is a substring!)
        return "pantry_dry_goods"
    if has("clam juice", "fish stock", "seafood stock"):
        return "canned_goods"

    # --- ordered grocery departments ---
    if has("chip", "cracker", "pretzel", "popcorn", "trail mix"):
        return "snacks"
    if has("bun", "tortilla", "bagel", "baguette", "croissant", "pita", "naan", "brioche",
           "dinner roll", "bread", "pie crust", "pastry", "dough", "flatbread", "muffin",
           "biscuit", "focaccia", "crumpet"):
        return "bakery"
    if has("juice", "soda", "lemonade", " ale", "root beer", "ginger beer", "ginger ale",
           "coffee", " tea", "kombucha", "seltzer", "sparkling water"):
        return "beverages"
    if has("frozen", "ice cream", "popsicle", "sorbet"):
        return "frozen"
    if has("oil", "vinegar", "sauce", "dressing", "zest", "chilli flake", "chili flake",
           "chile flake", "pepper flake", "seasoning", "salt", "spice",
           "powder", "cumin", "paprika", "oregano", "cinnamon", "nutmeg", "allspice", "cayenne",
           "turmeric", "curry", "syrup", "honey", "jam", "jelly", "ketchup", "mustard",
           "mayonnaise", "salsa", "relish", "pesto", "sriracha", "gochujang", "hoisin", "soy sauce", "soya sauce",
           "teriyaki", "caper", "marinade", " rub", "extract", "paste", "tahini", "miso",
           "sherry", "wine", "mirin", "bouillon", "vanilla", "gelatin", "molasses"):
        return "condiments_spices"
    if has("broth", "stock", "puree", "bean", "hominy", "chickpea", "lentil", "coconut milk",
           "refried", "diced tomato", "crushed tomato", "stewed tomato", "whole tomato",
           "tomato paste", "artichoke", "olive"):
        return "canned_goods"
    if has("beef", "chicken", "pork", "turkey", "lamb", "veal", "shrimp", "prawn", "fish",
           "salmon", "tuna", "cod", "tilapia", "halibut", "bacon", "sausage", "steak", "chorizo",
           "ham", "duck", "crab", "lobster", "clam", "mussel", "scallop", "anchovy", "sardine",
           "pepperoni", "salami", "meatball", "seafood", "squid", "calamari", "octopus"):
        return "meat_seafood"
    if has("milk", "cheese", "butter", "cream", "egg", "yogurt", "ricotta", "mozzarella",
           "parmesan", "feta", "provolone", "custard", "mascarpone", "half and half"):
        return "dairy_eggs"
    if has("onion", "garlic", "tomato", "lettuce", "carrot", "celery", "potato", "avocado",
           "lime", "lemon", "pepper", "cilantro", "parsley", "spinach", "cabbage", "cucumber",
           "mushroom", "broccoli", "zucchini", "corn", "apple", "banana", "berry", "kale",
           "ginger", "chile", "chilli", "jalapeno", "poblano", "tomatillo", "scallion",
           "shallot", "leek", "fennel", "romaine", "beet", "orange", "mango", "pineapple",
           "peach", "pear", "plum", "fig", "grape", "cherry", "cauliflower", "pumpkin",
           "radish", "asparagus", "okra", "plantain", "sprout", "herb", "mint", "dill", "sage",
           "chive", "cranberry", "coriander", "watercress", "arugula", "rocket"):
        return "produce"
    return "pantry_dry_goods"


def recategorize():
    """Re-apply categorize() to the auto-added items (fixes systematic mis-cats)."""
    auto = [s for s in _db.get("stock_items", "select=id,name,category,notes")
            if (s.get("notes") or "").startswith("auto-added from recipes")]
    changed = 0
    for s in auto:
        newcat = categorize(s["name"])
        if newcat != s["category"]:
            st, _ = _db.patch("stock_items", "id=eq.%s" % s["id"], {"category": newcat})
            if st in (200, 204):
                changed += 1
                print("  %-30s %s -> %s" % (s["name"][:30], s["category"], newcat))
    print("recategorized %d of %d auto-added items" % (changed, len(auto)))


def main():
    if "--recat" in sys.argv:
        recategorize()
        return
    apply = "--apply" in sys.argv
    stock_rows = _db.get("stock_items", "select=id,name")
    by_name = {s["name"]: s["id"] for s in stock_rows}
    existing_names_lc = {n.lower() for n in by_name}
    ings = _db.get("recipe_ingredients", "select=id,ingredient_name,stock_item_id")
    unlinked = [i for i in ings if not i["stock_item_id"]]

    min_freq = int(sys.argv[sys.argv.index("--min-freq") + 1]) if "--min-freq" in sys.argv else 1

    from collections import Counter
    allplan, skipped = [], 0
    freq = Counter()
    for i in unlinked:
        c = canonical(i["ingredient_name"])
        if not c:
            skipped += 1
            continue
        allplan.append((i["id"], i["ingredient_name"], c))
        if c.lower() not in existing_names_lc:
            freq[c] += 1

    needed = {c: categorize(c) for c, n in freq.items() if n >= min_freq}
    # keep links only where the canonical exists already or will be added
    plan = [p for p in allplan if p[2].lower() in existing_names_lc or p[2] in needed]
    cat_c = Counter(needed.values())

    print("MODE=%s   min-freq=%d" % ("apply" if apply else "dry-run", min_freq))
    print("unlinked ingredients: %d  (skipped as non-items/too-messy: %d)" % (len(unlinked), skipped))
    print("distinct new candidates: %d   ->  add at freq>=1:%d  >=2:%d  >=3:%d  >=5:%d" % (
        len(freq),
        sum(1 for v in freq.values() if v >= 1), sum(1 for v in freq.values() if v >= 2),
        sum(1 for v in freq.values() if v >= 3), sum(1 for v in freq.values() if v >= 5)))
    print("NEW stock items to add now (freq>=%d): %d" % (min_freq, len(needed)))
    print("new items by category:", dict(cat_c))
    print("\nvariant examples:")
    for probe in ["onion", "onion, chopped", "red onion", "sugar", "caster sugar",
                  "powdered sugar", "garlic", "garlic, minced", "garlic powder", "ground beef"]:
        print("  %-22s -> %s" % (probe, canonical(probe)))
    print("\nmost-used new items (x = how many recipes):")
    for c, n in freq.most_common(28):
        print("  %-28s x%-3d [%s]%s" % (c, n, categorize(c), "" if c in needed else "  (below cut)"))
    print("\ningredient links that will result: %d" % len(plan))

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance", ts + "-pantry-build")
    os.makedirs(outdir, exist_ok=True)
    json.dump({"new_items": needed, "links": [{"ing": p[1], "canonical": p[2]} for p in plan]},
              open(os.path.join(outdir, "pantry-build-plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("OUTDIR=%s" % outdir)

    if apply:
        # 1) insert new items (status OUT)
        rows = [{"name": c, "category": cat, "status": "OUT",
                 "notes": "auto-added from recipes; set to OK once confirmed in pantry"}
                for c, cat in needed.items()]
        added = 0
        for k in range(0, len(rows), 50):
            st, resp = _db.insert("stock_items", rows[k:k + 50])
            if st in (200, 201) and resp:
                for r in resp:
                    by_name[r["name"]] = r["id"]
                added += len(resp)
            else:
                print("INSERT failed: %s %r" % (st, resp))
        # 2) link every planned ingredient
        by_stock = {}
        for ing_id, _, c in plan:
            sid = by_name.get(c)
            if sid:
                by_stock.setdefault(sid, []).append(ing_id)
        patched = 0
        for sid, ids in by_stock.items():
            for k in range(0, len(ids), 80):
                chunk = ids[k:k + 80]
                st, resp = _db.patch("recipe_ingredients", "id=in.(%s)" % ",".join(chunk), {"stock_item_id": sid})
                if st in (200, 204):
                    patched += len(chunk)
                else:
                    print("PATCH failed stock %s: %s %r" % (sid, st, resp))
        now = len([i for i in _db.get("recipe_ingredients", "select=id,stock_item_id") if i["stock_item_id"]])
        print("\nAPPLIED: stock items added=%d, ingredient links set=%d ; ingredients now linked=%d / %d" % (
            added, patched, now, len(ings)))


if __name__ == "__main__":
    main()
