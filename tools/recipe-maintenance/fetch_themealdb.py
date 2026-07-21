"""Fetch TheMealDB via the official JSON API (first-letter search, a-z).

Saves each raw response verbatim plus a combined unique set (by idMeal) and a
fetch manifest under .local/MealDB/raw/<timestamp>/. Does NOT import anything.
"""
import os, sys, json, hashlib, time, string, datetime, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

BASE = "https://www.themealdb.com/api/json/v1/1/search.php?f="


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    raw = os.path.join(_db.ROOT, ".local", "MealDB", "raw", ts)
    os.makedirs(raw, exist_ok=True)
    manifest = {"timestamp": ts, "api": "themealdb v1 search.php?f=<letter>", "calls": []}
    seen = {}
    for letter in string.ascii_lowercase:
        url = BASE + letter
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "galleyquest-recipe-tool"})
            with urllib.request.urlopen(req, timeout=30) as r:
                status, body = r.status, r.read().decode("utf-8")
        except Exception as e:
            manifest["calls"].append({"endpoint": url, "error": str(e)})
            print("%s: ERROR %s" % (letter, e))
            continue
        with open(os.path.join(raw, "letter_%s.json" % letter), "w", encoding="utf-8") as f:
            f.write(body)
        meals = (json.loads(body).get("meals")) or []
        for m in meals:
            seen[m["idMeal"]] = m
        manifest["calls"].append({"endpoint": url, "http_status": status, "meals": len(meals),
                                  "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()})
        print("%s: %d meals" % (letter, len(meals)))
        time.sleep(0.25)
    allmeals = list(seen.values())
    with open(os.path.join(raw, "all-meals-unique.json"), "w", encoding="utf-8") as f:
        json.dump(allmeals, f, ensure_ascii=False, indent=2)
    manifest["unique_meals"] = len(allmeals)
    manifest["total_meals_fetched"] = sum(c.get("meals", 0) for c in manifest["calls"])
    with open(os.path.join(raw, "themealdb-fetch-manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("RAW_DIR=%s" % raw)
    print("unique_meals=%d total_fetched=%d" % (len(allmeals), manifest["total_meals_fetched"]))


if __name__ == "__main__":
    main()
