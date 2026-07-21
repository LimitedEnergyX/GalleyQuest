"""Normalize + curate TheMealDB meals into Tex-Mex / Southwest / Mediterranean.

Converts strIngredient/strMeasure pairs to ordered ingredient objects, splits
instructions into steps, classifies by area/keyword, dedups against the live DB
and within candidates, excludes desserts/weak recipes. Writes curated JSON sets,
a rejected list, and a report. No database writes.
"""
import os, sys, json, re, glob, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

MED_AREAS = {"greek", "italian", "spanish", "turkish", "moroccan", "tunisian",
             "croatian", "portuguese"}
TEXMEX_KW = ["taco", "burrito", "enchilada", "fajita", "nacho", "quesadilla",
             "chili", "chile", "tortilla", "queso", "chimichanga", "taquito"]
SW_KW = ["santa fe", "green chile", "chile verde", "poblano", "hominy",
         "posole", "pozole", "new mexico"]
CUISINE = {"tex-mex": "Tex-Mex", "southwest": "Southwest", "mediterranean": "Mediterranean"}


def norm_name(n):
    return re.sub(r"\s+", " ", (n or "").strip().lower())


def normalize(m):
    ings = []
    for i in range(1, 21):
        nm = (m.get("strIngredient%d" % i) or "").strip()
        me = (m.get("strMeasure%d" % i) or "").strip()
        if not nm:
            continue
        ings.append({"name": nm, "quantity": me if me else "to taste"})
    instr = (m.get("strInstructions") or "").strip()
    steps = [s.strip() for s in re.split(r"\r?\n+", instr) if s.strip()]
    if len(steps) <= 1:
        steps = [s.strip() for s in re.split(r"(?<=[.!?])\s+", instr) if s.strip()]
    return {"name": (m.get("strMeal") or "").strip(), "instructions": "\n".join(steps),
            "ingredients": ings, "idMeal": m.get("idMeal"), "area": m.get("strArea"),
            "category": m.get("strCategory"), "source": (m.get("strSource") or "").strip()}


def classify(nm, area, cat):
    a = (area or "").lower()
    c = (cat or "").lower()
    n = nm.lower()
    if c == "dessert":
        return None
    if any(k in n for k in SW_KW):
        return "southwest"
    if a in MED_AREAS:
        return "mediterranean"
    if a == "mexican" and any(k in n for k in TEXMEX_KW):
        return "tex-mex"
    return None


def main():
    rawdirs = sorted(glob.glob(os.path.join(_db.ROOT, ".local", "MealDB", "raw", "*")))
    allmeals = json.load(open(os.path.join(rawdirs[-1], "all-meals-unique.json"), encoding="utf-8"))
    existing = set(norm_name(r["name"]) for r in _db.get("recipes", "select=name"))
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(_db.ROOT, ".local", "recipe-maintenance", ts + "-curation")
    os.makedirs(outdir, exist_ok=True)
    buckets = {"tex-mex": [], "southwest": [], "mediterranean": []}
    rejected, seen, normalized_all = [], set(), []
    for m in allmeals:
        r = normalize(m)
        normalized_all.append(r)
        b = classify(r["name"], r["area"], r["category"])
        reason = None
        if not b:
            reason = "cuisine not targeted"
        elif len(r["instructions"]) < 40:
            reason = "instructions too short"
        elif len(r["ingredients"]) < 3:
            reason = "too few ingredients"
        elif norm_name(r["name"]) in existing:
            reason = "duplicate of existing recipe"
        elif norm_name(r["name"]) in seen:
            reason = "duplicate within candidates"
        if reason:
            rejected.append({"name": r["name"], "area": r["area"], "bucket": b, "reason": reason})
            continue
        seen.add(norm_name(r["name"]))
        notes = "Cuisine: %s\nSource: TheMealDB\nMealDB ID: %s\nOriginal area: %s\nOriginal category: %s" % (
            CUISINE[b], r["idMeal"], r["area"] or "", r["category"] or "")
        if r["source"]:
            notes += "\nSource URL: %s" % r["source"]
        buckets[b].append({"name": r["name"], "theme": "Open" if b == "mediterranean" else "Mexican",
                           "instructions": r["instructions"], "notes": notes, "ingredients": r["ingredients"]})
    curated_all = buckets["tex-mex"] + buckets["southwest"] + buckets["mediterranean"]
    dump = lambda fn, obj: json.dump(obj, open(os.path.join(outdir, fn), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    dump("themealdb-normalized-all.json", normalized_all)
    dump("themealdb-curated-tex-mex.json", buckets["tex-mex"])
    dump("themealdb-curated-southwest.json", buckets["southwest"])
    dump("themealdb-curated-mediterranean.json", buckets["mediterranean"])
    dump("themealdb-curated-all.json", curated_all)
    dump("themealdb-rejected.json", rejected)
    md = ["# TheMealDB curation report (%s)\n" % ts,
          "- Raw unique meals: %d" % len(allmeals),
          "- Tex-Mex candidates: %d" % len(buckets["tex-mex"]),
          "- Southwest candidates: %d" % len(buckets["southwest"]),
          "- Mediterranean candidates: %d" % len(buckets["mediterranean"]),
          "- Total curated: %d" % len(curated_all),
          "- Rejected: %d\n" % len(rejected),
          "## Curated names",
          "### Tex-Mex\n" + "\n".join("- " + c["name"] for c in buckets["tex-mex"]),
          "\n### Southwest\n" + "\n".join("- " + c["name"] for c in buckets["southwest"]),
          "\n### Mediterranean\n" + "\n".join("- " + c["name"] for c in buckets["mediterranean"])]
    open(os.path.join(outdir, "themealdb-curation-report.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("OUTDIR=%s" % outdir)
    for b in ("tex-mex", "southwest", "mediterranean"):
        print("%s=%d" % (b, len(buckets[b])))
    print("curated_all=%d rejected=%d" % (len(curated_all), len(rejected)))


if __name__ == "__main__":
    main()
