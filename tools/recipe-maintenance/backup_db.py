"""Timestamped read-only backup of all six tables under .local/backups/.

Usage:  python backup_db.py --label before-recipe-expansion
Credential-free; verifies every exported JSON parses.
"""
import os, sys, json, datetime, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db


def git(*a):
    try:
        return subprocess.check_output(["git", "-C", _db.ROOT] + list(a),
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def main():
    label = "manual"
    if "--label" in sys.argv:
        label = sys.argv[sys.argv.index("--label") + 1]
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(_db.ROOT, ".local", "backups", "%s-%s" % (ts, label))
    m = _db.backup(dest, "pre/post-operation backup: " + label,
                   git("rev-parse", "--abbrev-ref", "HEAD"),
                   git("rev-parse", "--short", "HEAD"))
    ok = True
    for fn in list(m["file_sha256"]) + ["backup-manifest.json"]:
        try:
            json.load(open(os.path.join(dest, fn), encoding="utf-8"))
        except Exception as e:
            ok = False
            print("PARSE_FAIL", fn, e)
    print("BACKUP_DIR=%s" % dest)
    for t, c in m["tables"].items():
        print("  %s=%s" % (t, c))
    print("ALL_PARSE_OK=%s" % ok)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
