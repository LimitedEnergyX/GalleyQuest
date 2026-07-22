"""Backfill first-class taxonomy columns (cuisine / category / tags) for every
recipe. Parses the Cuisine/Category/Tags lines already in notes where present,
and infers the rest from the recipe name + ingredients.

--dry-run (default): compute + report only (works before the migration is run).
--apply: PATCH the cuisine/category/tags columns (requires the migration from
         .local/recipe-maintenance/migrations/ to have been applied).

Reads notes but does not modify them.
"""
import os, sys, json, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

CATEGORIES = ["Main", "Handheld", "Pasta", "Salad", "Soup", "Side", "Breakfast", "Bread", "Appetizer", "Dessert", "Drink"]


def parse_notes(notes):
    notes = notes or ""
    def line(key):
        # [ \t]* (not \s*) so a blank "Cuisine:" line does not swallow the next line
        m = re.search(r"^%s:[ \t]*(.+)$" % key, notes, re.M)
        return m.group(1).strip() if m else None
    cuisine = line("Cuisine")
    category = line("Category")
    tags = line("Tags")
    taglist = [t.strip() for t in (tags.split(",") if tags else []) if t.strip()]
    return cuisine, category, taglist


def infer_category(name):
    n = name.lower()
    def has(*kw): return any(k in n for k in kw)
    if has("salad"): return "Salad"
    if has("taco", "burrito", "burger", "sandwich", "wrap", "quesadilla", "sloppy joe", "blt", "grilled cheese", "sub", "gyro", "souvlaki"): return "Handheld"
    if has("soup", "stew", "chowder", "chili", "posole", "pozole", "gazpacho", "bisque", "corba", "ribollita", "broth", "pho", "tom kha", "tom yum"): return "Soup"
    if has("dip", "hummus", "salsa", "guacamole", "queso", "caviar", "nachos", "croquetas", "bruschetta", "wings", "deviled", "calamari", "squid", "fritter", "dumpling"): return "Appetizer"
    if has("shortbread", "cookie", "cake", "brownie", "cobbler", "torrijas", "pudding", "tart", "doughnut", "pie ", "cheesecake", "souffle", "crumble", "churros", "mess", "buns"): return "Dessert"
    if has("biscuit", "cornbread", "flatbread", "garlic bread", "focaccia") or n.endswith("bread"): return "Bread"
    if has("breakfast", "omelette", "scramble", "migas", "pancake", "waffle", "frittata", "benedict", "grits", "kedgeree") or n.startswith("eggs"): return "Breakfast"
    if has("pasta", "spaghetti", "fettuccine", "fettucine", "penne", "linguine", "lasagne", "lasagna", "cannelloni", "carbonara", "alfredo", "rigatoni", "macaroni", "gnocchi", "ziti", "vodka", "marinara", "scampi", "shells"): return "Pasta"
    if has("coleslaw", "baked beans", "refried beans", "rice", "gratin"): return "Side"
    return "Main"


def build_notes(old, cuisine, category, tags):
    """Rebuild notes with canonical Cuisine/Category/Tags lines on top, keeping
    any other existing note text (Source lines, descriptions) below."""
    rest = [l for l in (old or "").split("\n")
            if not re.match(r"^\s*(Cuisine|Category|Tags)\s*:", l)]
    rest = "\n".join(rest).strip()
    head = []
    if cuisine:
        head.append("Cuisine: %s" % cuisine)
    head.append("Category: %s" % category)
    if tags:
        head.append("Tags: %s" % ", ".join(tags))
    out = "\n".join(head)
    if rest:
        out += "\n" + rest
    return out


def infer_tags(name, ings):
    text = (name + " " + " ".join(i.get("ingredient_name", "") for i in (ings or []))).lower()
    tags = []
    if re.search(r"\bchicken\b", text): tags.append("chicken")
    if re.search(r"\bbeef|steak\b", text): tags.append("beef")
    if re.search(r"\bpork|chorizo|bacon|ham|sausage\b", text): tags.append("pork")
    if re.search(r"\bturkey\b", text): tags.append("turkey")
    if re.search(r"\blamb\b", text): tags.append("lamb")
    if re.search(r"prawn|shrimp|salmon|tuna|fish|squid|calamari|sardine|clam|seafood|cod|haddock", text): tags.append("seafood")
    if re.search(r"\btofu\b", text): tags.append("tofu")
    if not any(t in tags for t in ("chicken", "beef", "pork", "turkey", "lamb", "seafood")): tags.append("vegetarian")
    return tags


def main():
    apply = "--apply" in sys.argv
    to_notes = "--to-notes" in sys.argv
    if apply and not to_notes:
        try:
            _db.get("recipes", "select=cuisine,category,tags&limit=1")
        except Exception as e:
            print("PREFLIGHT FAILED: the taxonomy columns don't exist yet.")
            print("Run .local/recipe-maintenance/migrations/2026-07-21-add-recipe-taxonomy.sql in Supabase first,")
            print("or use --to-notes to store the taxonomy in the notes field instead (no schema change).")
            print("(%s)" % e)
            sys.exit(1)

    recs = _db.get("recipes", "select=id,name,theme,notes,recipe_ingredients(ingredient_name)")
    from collections import Counter
    cat_c, cui_c = Counter(), Counter()
    plan, changed = [], 0
    for r in recs:
        cuisine, category, tags = parse_notes(r.get("notes"))
        src_cat = "notes" if category else "inferred"
        src_tags = "notes" if tags else "inferred"
        if not category:
            category = infer_category(r["name"])
        if not tags:
            tags = infer_tags(r["name"], r.get("recipe_ingredients"))
        if not cuisine and r.get("theme") in ("Mexican", "Thai", "Asian"):
            cuisine = r["theme"]
        cat_c[category] += 1
        cui_c[cuisine or "(none)"] += 1
        plan.append({"id": r["id"], "name": r["name"], "cuisine": cuisine,
                     "category": category, "category_src": src_cat, "tags": tags, "tags_src": src_tags})
        if apply:
            if to_notes:
                body = {"notes": build_notes(r.get("notes"), cuisine, category, tags)}
            else:
                body = {"cuisine": cuisine, "category": category, "tags": tags}
            st, resp = _db.patch("recipes", "id=eq.%s" % r["id"], body)
            if st not in (200, 204):
                print("PATCH failed for %s: %s %r" % (r["name"], st, resp))
            else:
                changed += 1

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance", ts + "-taxonomy")
    os.makedirs(outdir, exist_ok=True)
    json.dump(plan, open(os.path.join(outdir, "taxonomy-plan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("MODE=%s recipes=%d %s" % ("apply" if apply else "dry-run", len(recs), "patched=%d" % changed if apply else ""))
    print("category:", dict(cat_c.most_common()))
    print("cuisine:", dict(cui_c.most_common()))
    print("OUTDIR=%s" % outdir)


if __name__ == "__main__":
    main()
