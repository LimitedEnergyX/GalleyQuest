"""Consolidate near-duplicate / variant stock_items into canonical ingredients.

Recipes keep their specific ingredient_name (e.g. "Granny smith apple"); only the
stock link is re-pointed to a generic canonical item (e.g. "Apple"). This kills
pantry bloat and stops variety-only items from dragging the efficiency metric.

For each group: re-point every recipe_ingredients row from a variant to the
canonical stock item, merge status (best of OK>LOW>OUT), then delete the variant.
If the canonical name doesn't exist yet, the first variant is renamed to it.

Usage:
  python consolidate_ingredients.py            # dry-run: show every planned merge
  python consolidate_ingredients.py --apply     # execute
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

# canonical name -> [variant names merged into it]
MAP = {
    # spelling / US-UK synonyms
    "Chili powder": ["Chilli powder"],
    "Red chilli": ["Red chilly"],
    "Red chilli flake": ["Chilli flake"],
    "Hot sauce": ["Hotsauce"],
    "Shallot": ["Challot"],
    "Eggplant": ["Aubergine"],
    "Shrimp": ["Prawn", "King prawn", "Raw king prawn", "Raw tiger prawn", "Tiger prawn"],
    # varieties -> generic
    "Apple": ["Braeburn apple", "Gala apple", "Granny smith apple"],
    "Carrot": ["Crinkle cut carrot"],
    "Broccoli": ["Broccoli florets", "Chinese broccoli"],
    "Green onions": ["Chive"],
    # cheese
    "Parmesan": ["Parmesan cheese", "Parmigiano reggiano"],
    "Mozzarella": ["Mozzarella ball"],
    "Feta cheese": ["Feta"],
    "Ricotta cheese": ["Ricotta"],
    "Mexican cheese blend": ["Mexican cheese"],
    "Processed cheese": ["Pasteurized processed cheese spread"],
    # dairy
    "Unsalted butter": ["Butter", "Chilled butter"],
    "2% milk": ["Cold milk", "Semi skimmed milk"],
    "Heavy cream": ["Heavy whipping cream", "Double cream"],
    "Sweetened condensed milk": ["Condensed milk"],
    # herbs / spices
    "Basil": ["Basil leave"],
    "Cilantro": ["Coriander leave"],
    "Minced ginger": ["Ginger"],
    "Cumin": ["Ground cumin"],
    "Cinnamon": ["Ground cinnamon"],
    "Cocoa powder": ["Cocoa"],
    "Makrut lime leave": ["Lime leave"],
    # produce
    "Potato": ["Floury potato", "Yukon gold potato"],
    "Romaine lettuce": ["Romaine", "Little gem lettuce"],
    "Cabbage": ["Savoy cabbage"],
    "Red pepper": ["Red bell pepper"],
    "Tomato": ["Vine tomato"],
    "Cherry tomato": ["Grape tomato", "Baby plum tomato"],
    # meat
    "Chicken breast": ["Chicken breast tender", "Chicken cutlet"],
    "Flank steak": ["Flank"],
    # grains / pantry
    "White rice": ["Rice", "Long grain rice", "Long grain white rice"],
    "Spaghetti": ["Barilla spaghetti"],
    "Penne": ["Penne rigate", "Barilla penne"],
    "Elbow macaroni": ["Barilla elbows"],
    "Old fashioned rolled oats": ["Quick cooking rolled oat"],
    "Bread flour": ["Strong white flour"],
    "Brown sugar": ["Light brown sugar", "Light brown soft sugar", "Muscovado sugar"],
    "Vanilla extract": ["Vanilla"],
    "Vegetable oil": ["Oil frying"],
    "Vegetable broth": ["Vegetable stock", "Vegetable stock cube"],
    "Beef broth": ["Hot beef stock"],
    "Kidney bean": ["Red kidney bean"],
    "Ketchup": ["Tomato ketchup"],
    "Mustard": ["Prepared mustard", "Yellow mustard"],
    "White vinegar": ["Vinegar"],
    "Taco shell": ["Hard taco shell"],
    "Tortilla chip": ["Crushed tortilla chip"],
    "Green enchilada sauce": ["Green chile enchilada sauce"],
    "Cashew": ["Cashew nut"],
}
RANK = {"OK": 2, "LOW": 1, "OUT": 0}


def main():
    apply = "--apply" in sys.argv
    stock = _db.get("stock_items", "select=id,name,status")
    by_name = {s["name"]: s for s in stock}
    # usage counts for reporting
    ings = _db.get("recipe_ingredients", "select=stock_item_id")
    uses = {}
    for i in ings:
        sid = i.get("stock_item_id")
        if sid:
            uses[sid] = uses.get(sid, 0) + 1

    planned, missing, removed = [], [], 0
    for canon_name, variant_names in MAP.items():
        canon = by_name.get(canon_name)
        variants = [by_name[n] for n in variant_names if n in by_name]
        for n in variant_names:
            if n not in by_name:
                missing.append("%s <- %s (variant not found)" % (canon_name, n))
        if not canon and not variants:
            missing.append("%s (no canonical, no variants)" % canon_name)
            continue

        rename = None
        if not canon:
            canon = variants.pop(0)
            rename = (canon["id"], canon_name, canon["name"])
        if not variants and not rename:
            continue

        best = canon["status"]
        for v in variants:
            if RANK[v["status"]] > RANK[best]:
                best = v["status"]

        moved = sum(uses.get(v["id"], 0) for v in variants)
        planned.append("  %-26s <- %-45s  (+%d links%s)" % (
            canon_name, ", ".join(v["name"] for v in variants) or "(rename only)",
            moved, "" if best == canon["status"] else ", status->" + best))

        if apply:
            if rename:
                st, body = _db.patch("stock_items", "id=eq.%s" % rename[0], {"name": rename[1]})
                if st >= 400:
                    print("  ! rename %r failed: %s %s" % (rename[1], st, body)); continue
            for v in variants:
                st, body = _db.patch("recipe_ingredients", "stock_item_id=eq.%s" % v["id"],
                                     {"stock_item_id": canon["id"]})
                if st >= 400:
                    print("  ! repoint %r failed: %s %s" % (v["name"], st, body)); continue
                st, body = _db.delete("stock_items", "id=eq.%s" % v["id"])
                if st >= 400:
                    print("  ! delete %r failed: %s %s" % (v["name"], st, body)); continue
                removed += 1
            if best != canon["status"]:
                _db.patch("stock_items", "id=eq.%s" % canon["id"], {"status": best})

    print("%s %d groups:" % ("APPLIED" if apply else "DRY-RUN", len(planned)))
    print("\n".join(planned))
    if missing:
        print("\nNot found (skipped):")
        for m in missing:
            print("  " + m)
    print("\nstock_items before: %d" % len(stock))
    if apply:
        print("stock_items now:    %d  (removed %d)" % (_db.count("stock_items"), removed))
    else:
        est = sum(len([n for n in vs if n in by_name]) - (0 if cn in by_name else 1)
                  for cn, vs in MAP.items())
        print("would remove ~%d items -> ~%d" % (est, len(stock) - est))


if __name__ == "__main__":
    main()
