"""Read / update the GalleyQuest grocery list. Used by the order-groceries skill.

Usage:
  python grocery_cli.py list                 # id<TAB>status<TAB>name<TAB>note (current week)
  python grocery_cli.py mark <status> <id...># set those items to a status
Statuses: on_list, ordered, pending_pickup.
"""
import os, sys, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db

STATUSES = ("on_list", "ordered", "pending_pickup")


def week_start():
    d = datetime.date.today()
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def parse_status(notes):
    m = re.match(r"^\[(\w+)\]\s*([\s\S]*)$", notes or "")
    if m and m.group(1) in STATUSES:
        return m.group(1), m.group(2)
    return "on_list", (notes or "")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("list", "mark"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "list":
        rows = _db.get("grocery_extra_items", "week_start_date=eq.%s&order=item_name" % week_start())
        for r in rows:
            st, txt = parse_status(r.get("notes"))
            print("%s\t%s\t%s\t%s" % (r["id"], st, r["item_name"], txt.replace("\n", " ")))
        return
    # mark
    status = sys.argv[2]
    if status not in STATUSES:
        print("status must be one of %s" % (STATUSES,))
        sys.exit(1)
    ids = sys.argv[3:]
    rows = {r["id"]: r for r in _db.get("grocery_extra_items", "week_start_date=eq.%s" % week_start())}
    n = 0
    for i in ids:
        r = rows.get(i)
        if not r:
            print("skip (not found): %s" % i)
            continue
        _, txt = parse_status(r.get("notes"))
        st, _b = _db.patch("grocery_extra_items", "id=eq.%s" % i, {"notes": "[%s]%s" % (status, (" " + txt) if txt else "")})
        if st in (200, 204):
            n += 1
    print("marked %d item(s) as %s" % (n, status))


if __name__ == "__main__":
    main()
