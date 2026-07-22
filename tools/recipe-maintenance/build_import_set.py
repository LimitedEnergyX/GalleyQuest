"""Assemble the final recipe import set.

Combines the selected TheMealDB Mediterranean + Tex-Mex candidates with the
household supplemental Tex-Mex/Southwest recipes (from .local), dedups against
the live DB and within the set, validates every recipe (name, accepted theme,
useful instructions, >=3 ingredients, every ingredient with a nonempty
quantity), and writes final-import.json plus a build report. No DB writes.

Reads household curation data from .local (git-ignored); writes nothing tracked.
"""
import os, sys, json, re, glob, datetime, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

THEMES = {"Mexican", "Thai", "Asian", "Crock Pot", "Grab Night", "Invention", "Open"}
CUISINE_THEME = {"Tex-Mex": "Mexican", "Southwest": "Mexican", "Mediterranean": "Open",
                 "American": "Open", "Italian": "Open"}


def norm_name(n):
    return re.sub(r"\s+", " ", (n or "").strip().lower())


def load_local(fname):
    path = os.path.join(_db.ROOT, ".local", "recipe-maintenance", fname)
    spec = importlib.util.spec_from_file_location(fname.replace(".py", ""), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def expand_supplemental(tup):
    name, cuisine, ings, steps = tup
    return {
        "name": name,
        "theme": CUISINE_THEME[cuisine],
        "instructions": "\n".join(steps),
        "notes": "Cuisine: %s\nSource: household culinary reconstruction" % cuisine,
        "ingredients": [{"name": nm, "quantity": q} for (q, nm) in ings],
    }


def expand_rich(tup):
    name, cuisine, category, tags, ings, steps = tup
    return {
        "name": name,
        "theme": CUISINE_THEME[cuisine],
        "instructions": "\n".join(steps),
        "notes": "Cuisine: %s\nCategory: %s\nTags: %s\nSource: household culinary reconstruction" % (
            cuisine, category, tags),
        "ingredients": [{"name": nm, "quantity": q} for (q, nm) in ings],
    }


def validate(r):
    problems = []
    if not (r.get("name") or "").strip():
        problems.append("blank name")
    if r.get("theme") not in THEMES:
        problems.append("theme not accepted: %r" % r.get("theme"))
    if len((r.get("instructions") or "").strip()) < 40:
        problems.append("instructions too short")
    ings = r.get("ingredients") or []
    if len(ings) < 3:
        problems.append("fewer than 3 ingredients")
    for i in ings:
        if not (i.get("name") or "").strip():
            problems.append("ingredient with blank name")
        if not (i.get("quantity") or "").strip():
            problems.append("ingredient %r missing quantity" % i.get("name"))
    return problems


def main():
    curdirs = sorted(glob.glob(os.path.join(_db.ROOT, ".local", "recipe-maintenance", "*-curation")))
    curdir = curdirs[-1]
    med = json.load(open(os.path.join(curdir, "themealdb-curated-mediterranean.json"), encoding="utf-8"))
    texmex_db = json.load(open(os.path.join(curdir, "themealdb-curated-tex-mex.json"), encoding="utf-8"))
    supp = load_local("supplemental_recipes.py")
    med_keep = set(norm_name(n) for n in supp.MED_KEEP)
    med_sel = [r for r in med if norm_name(r["name"]) in med_keep]

    candidates = med_sel + texmex_db + [expand_supplemental(t) for t in supp.SUPPLEMENTAL]

    rich_path = os.path.join(_db.ROOT, ".local", "recipe-maintenance", "supplemental_american_italian.py")
    if os.path.exists(rich_path):
        rich = load_local("supplemental_american_italian.py")
        candidates += [expand_rich(t) for t in rich.SUPPLEMENTAL_RICH]

    staples_path = os.path.join(_db.ROOT, ".local", "recipe-maintenance", "supplemental_staples.py")
    if os.path.exists(staples_path):
        st = load_local("supplemental_staples.py")
        candidates += [expand_rich(t) for t in st.SUPPLEMENTAL_STAPLES]

    existing = set(norm_name(r["name"]) for r in _db.get("recipes", "select=name"))
    final, skipped, seen = [], [], set()
    for r in candidates:
        nn = norm_name(r["name"])
        if nn in existing:
            skipped.append({"name": r["name"], "reason": "duplicate of existing recipe"})
            continue
        if nn in seen:
            skipped.append({"name": r["name"], "reason": "duplicate within set"})
            continue
        probs = validate(r)
        if probs:
            skipped.append({"name": r["name"], "reason": "; ".join(probs)})
            continue
        seen.add(nn)
        final.append(r)

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance", ts + "-import-build")
    os.makedirs(outdir, exist_ok=True)
    json.dump(final, open(os.path.join(outdir, "final-import.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(skipped, open(os.path.join(outdir, "final-import-skipped.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def cuisine_of(r):
        m = re.search(r"Cuisine:\s*(.+)", r.get("notes") or "")
        return m.group(1).splitlines()[0].strip() if m else "?"
    counts = {}
    for r in final:
        counts[cuisine_of(r)] = counts.get(cuisine_of(r), 0) + 1

    print("OUTDIR=%s" % outdir)
    print("final=%d skipped=%d" % (len(final), len(skipped)))
    print("by_cuisine=%s" % counts)
    print("total_ingredients=%d" % sum(len(r["ingredients"]) for r in final))


if __name__ == "__main__":
    main()
