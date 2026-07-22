"""Recipe coverage calculator: how many recipes are FULLY makeable from a set of
ingredients, and — greedily — which few additions unlock the most more recipes.

A recipe counts as makeable when every tracked ingredient it needs is in the
"have" set. (Untracked odds-and-ends like water aren't counted as blockers.)

Usage:
  python coverage.py staples [N] [--add K]   # start from your top-N most-used (default 30)
  python coverage.py stock   [--add K]       # start from what's currently OK in Stock
  python coverage.py all     [--add K]       # start from everything you track
K = how many "best next additions" to suggest (default 12).
"""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db


def load():
    recs = _db.get("recipes", "select=id,name,recipe_ingredients(stock_item_id)")
    recipes = [(r["name"], set(i["stock_item_id"] for i in (r.get("recipe_ingredients") or []) if i["stock_item_id"]))
               for r in recs]
    stock = {s["id"]: s["name"] for s in _db.get("stock_items", "select=id,name")}
    return recipes, stock


def top_staples(recipes, n):
    cnt = Counter()
    for _, req in recipes:
        for sid in req:
            cnt[sid] += 1
    return set(k for k, _ in cnt.most_common(n))


def makeable(recipes, have):
    return sum(1 for _, req in recipes if req <= have)


def greedy(recipes, have, stock, k):
    have = set(have)
    out = []
    for _ in range(k):
        unlock = Counter()
        for _, req in recipes:
            missing = req - have
            if len(missing) == 1:
                unlock[next(iter(missing))] += 1
        if not unlock:
            break
        best, gain = unlock.most_common(1)[0]
        have.add(best)
        out.append((stock.get(best, "?"), gain, makeable(recipes, have)))
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "staples"
    k = int(sys.argv[sys.argv.index("--add") + 1]) if "--add" in sys.argv else 12
    recipes, stock = load()
    if mode == "leverage":
        cnt = Counter()
        for _, req in recipes:
            for sid in req:
                cnt[sid] += 1
        dist = Counter()
        for _, c in cnt.items():
            b = "1" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6-10" if c <= 10 else "11+"
            dist[b] += 1
        print("Ingredient leverage - how many recipes each tracked ingredient serves:")
        for b in ["1", "2", "3-5", "6-10", "11+"]:
            print("  in %-5s recipe(s): %3d ingredients" % (b, dist[b]))
        oneoff = set(sid for sid, c in cnt.items() if c == 1)
        print("  single-use ingredients (waste risk): %d of %d tracked" % (len(oneoff), len(cnt)))
        scored = sorted(((name, len(req & oneoff), len(req)) for name, req in recipes), key=lambda x: -x[1])
        print("\nRecipes that lean hardest on single-use ingredients (least pantry-efficient):")
        for name, oo, tot in scored[:12]:
            if oo == 0:
                break
            print("  %-30s %d/%d ingredients used in no other recipe" % (name[:30], oo, tot))
        return
    if mode == "stock":
        okids = set(s["id"] for s in _db.get("stock_items", "select=id,status") if s["status"] == "OK")
        have = okids
        print("From what's currently OK in Stock (%d items):" % len(have))
    elif mode == "all":
        have = set(stock.keys())
        print("From everything you track (%d items):" % len(have))
    else:
        n = next((int(a) for a in sys.argv[2:] if a.isdigit()), 30)
        have = top_staples(recipes, n)
        print("From your top %d most-used ingredients:" % n)
    base = makeable(recipes, have)
    print("  fully makeable now: %d / %d recipes" % (base, len(recipes)))
    print("  best ingredients to add next:")
    for name, gain, total in greedy(recipes, have, stock, k):
        print("    + %-26s unlocks %2d more  (=> %3d makeable)" % (name[:26], gain, total))


if __name__ == "__main__":
    main()
