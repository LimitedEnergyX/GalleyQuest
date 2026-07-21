"""Extract the live Pantry & Meal Tracker into a local dev project."""
import json, os, re, urllib.request

SRC = "http://aet-w11l.local:8000/"
ROOT = r"D:\DEV\GalleyQuest\.local\pantry-snapshot"
DATA = os.path.join(ROOT, "data")
TABLES = ["stock_items", "recipes", "recipe_ingredients",
          "meal_plan", "grocery_extra_items", "grocery_dismissed_items"]


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


html = get(SRC)
open(os.path.join(ROOT, "original.html"), "w", encoding="utf-8").write(html)
print("original.html", len(html))

styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)
open(os.path.join(ROOT, "styles.css"), "w", encoding="utf-8").write(
    "\n\n".join(s.strip() for s in styles))
print("styles.css", sum(len(s) for s in styles), "blocks:", len(styles))

inline = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
app_js = "\n\n".join(s.strip() for s in inline)
open(os.path.join(ROOT, "app.js"), "w", encoding="utf-8").write(app_js)
print("app.js", len(app_js), "blocks:", len(inline))

# Build index.html: styles -> link, inline script -> src, supabase CDN -> local shim
out = re.sub(r"<style[^>]*>.*?</style>",
             '<link rel="stylesheet" href="styles.css">', html, count=1, flags=re.S)
out = re.sub(r"<style[^>]*>.*?</style>", "", out, flags=re.S)
out = re.sub(r'<script[^>]*src="https://cdn\.jsdelivr\.net/[^"]*"[^>]*>\s*</script>',
             '<script src="seed.js"></script>\n<script src="local-db.js"></script>',
             out, flags=re.S)
out = re.sub(r"<script(?![^>]*\bsrc=)[^>]*>.*?</script>",
             '<script src="app.js"></script>', out, count=1, flags=re.S)
out = re.sub(r"<script(?![^>]*\bsrc=)[^>]*>.*?</script>", "", out, flags=re.S)
BADGE = ('<div style="background:#8a3d00;color:#fff;padding:6px 12px;'
         'font:600 13px system-ui,sans-serif">OFFLINE DEV COPY - local data only, '
         'nothing here touches the live app</div>')
out = re.sub(r"(<body[^>]*>)", r"\1\n" + BADGE, out, count=1)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
print("index.html", len(out))

# --- pull data straight from Supabase REST using creds embedded in the page ---
m_url = re.search(r"https://[a-z0-9]+\.supabase\.co", html)
m_key = re.search(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", html)
if not (m_url and m_key):
    raise SystemExit("could not locate supabase url/key in page")
base, key = m_url.group(0), m_key.group(0)
hdr = {"apikey": key, "Authorization": "Bearer " + key}

seed = {}
for t in TABLES:
    rows = json.loads(get(f"{base}/rest/v1/{t}?select=*", hdr))
    seed[t] = rows
    with open(os.path.join(DATA, t + ".json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"data/{t}.json", len(rows), "rows")

with open(os.path.join(ROOT, "seed.js"), "w", encoding="utf-8") as f:
    f.write("// Snapshot of the live database. Regenerate with tools/extract.py\n")
    f.write("window.__SEED__ = ")
    json.dump(seed, f, indent=1, ensure_ascii=False)
    f.write(";\n")
print("seed.js written")
