"""Read-only audit of existing recipes + recipe_ingredients.

Writes existing-recipe-audit.json (full per-recipe state + metrics) and
existing-recipe-audit.md (summary). Does NOT write to the database.
"""
import os, sys, json, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

STOP = set(("and or of the a an with to for fresh chopped diced sliced minced grated "
            "ground large small medium can cans package pkg cup cups tbsp tsp lb lbs oz "
            "optional divided drained softened cooked boneless skinless").split())


def norm(s):
    return (s or "").strip()


def keywords(name):
    n = re.sub(r"[^a-z ]", " ", (name or "").lower())
    return [w for w in n.split() if len(w) > 2 and w not in STOP]


def audit_rows():
    recs = _db.get("recipes",
                   "select=*,recipe_ingredients(id,ingredient_name,quantity,stock_item_id)&order=name")
    out = []
    for r in recs:
        ings = r.get("recipe_ingredients") or []
        instr = norm(r.get("instructions"))
        seen = {}
        for ing in ings:
            k = norm(ing.get("ingredient_name")).lower()
            seen[k] = seen.get(k, 0) + 1
        dup = sum(v - 1 for v in seen.values() if v > 1)
        miss_q = sum(1 for ing in ings if not norm(ing.get("quantity")))
        blank_n = sum(1 for ing in ings if not norm(ing.get("ingredient_name")))
        instr_missing = not instr
        instr_weak = (not instr_missing) and (len(instr) < 60 or
                                              instr.count(".") + instr.count("\n") < 1)
        itext = instr.lower()
        if instr:
            unused = [ing.get("ingredient_name") for ing in ings
                      if not any(kw in itext for kw in keywords(ing.get("ingredient_name")))]
        else:
            unused = [ing.get("ingredient_name") for ing in ings]
        linked = sum(1 for ing in ings if ing.get("stock_item_id"))
        problems = []
        if not ings:
            problems.append("no ingredients")
        if miss_q:
            problems.append("%d ingredient(s) missing quantity" % miss_q)
        if blank_n:
            problems.append("%d blank ingredient name(s)" % blank_n)
        if instr_missing:
            problems.append("instructions missing")
        elif instr_weak:
            problems.append("instructions weak/short")
        if dup:
            problems.append("%d duplicate ingredient row(s)" % dup)
        recon = instr_missing or len(ings) < 2 or (ings and miss_q == len(ings))
        out.append({
            "id": r["id"], "name": r.get("name"), "theme": r.get("theme"),
            "ingredient_count": len(ings), "missing_quantities": miss_q,
            "blank_names": blank_n, "instructions_missing": instr_missing,
            "instructions_weak": instr_weak, "unused_in_instructions": unused,
            "duplicate_ingredient_rows": dup, "stock_links": linked,
            "needs_substantial_reconstruction": recon, "problems": problems,
            "current": {
                "instructions": r.get("instructions"), "notes": r.get("notes"),
                "ingredients": [{"id": ing.get("id"), "name": ing.get("ingredient_name"),
                                 "quantity": ing.get("quantity"),
                                 "stock_item_id": ing.get("stock_item_id")} for ing in ings],
            },
        })
    return out


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    d = os.path.join(_db.ROOT, ".local", "recipe-maintenance", ts)
    os.makedirs(d, exist_ok=True)
    data = audit_rows()
    json.dump(data, open(os.path.join(d, "existing-recipe-audit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    tot = len(data)
    m = lambda pred: sum(1 for r in data if pred(r))
    miss_ing = m(lambda r: r["ingredient_count"] == 0)
    any_missq = m(lambda r: r["missing_quantities"])
    weak = m(lambda r: r["instructions_missing"] or r["instructions_weak"])
    dups = m(lambda r: r["duplicate_ingredient_rows"])
    recon = m(lambda r: r["needs_substantial_reconstruction"])
    ok = m(lambda r: not r["problems"])
    md = ["# Existing recipe audit (%s)\n" % ts,
          "- Total recipes: %d" % tot,
          "- Missing ingredients entirely: %d" % miss_ing,
          "- Recipes with any missing quantity: %d" % any_missq,
          "- Weak/missing instructions: %d" % weak,
          "- Duplicate ingredient rows: %d" % dups,
          "- Need substantial reconstruction: %d" % recon,
          "- Already acceptable: %d\n" % ok,
          "| Recipe | Theme | #Ing | MissQty | Instr | Problems |",
          "|---|---|---|---|---|---|"]
    for r in data:
        instr = "missing" if r["instructions_missing"] else ("weak" if r["instructions_weak"] else "ok")
        md.append("| %s | %s | %d | %d | %s | %s |" % (
            r["name"], r["theme"], r["ingredient_count"], r["missing_quantities"],
            instr, "; ".join(r["problems"]) or "none"))
    open(os.path.join(d, "existing-recipe-audit.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("AUDIT_DIR=%s" % d)
    print("total=%d miss_ing=%d any_missq=%d weak_instr=%d dup_ings=%d recon=%d acceptable=%d"
          % (tot, miss_ing, any_missq, weak, dups, recon, ok))


if __name__ == "__main__":
    main()
