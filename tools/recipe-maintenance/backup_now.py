# -*- coding: utf-8 -*-
"""Full read-only snapshot of the live DB (all tables + sha256 manifest) into
.local/backups/<UTC-timestamp>-<label>. Pass an optional label:
    python backup_now.py "before-big-change"
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _db
from datetime import datetime, timezone

label = (sys.argv[1] if len(sys.argv) > 1 else "manual-snapshot").strip().replace(" ", "-")
ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
dest = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".local", "backups", ts + "-" + label))
m = _db.backup(dest, purpose=label)
print("project_ref :", m["supabase_project_ref"])
print("backup dir  :", dest)
for t, n in m["tables"].items():
    print("  %-24s %5d rows" % (t, n))
print("manifest files:", list(m["file_sha256"].keys()))
