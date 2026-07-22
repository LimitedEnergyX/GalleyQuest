# 🍽️ GalleyQuest

**A household pantry, recipe, and meal-planning app that tells you what you can cook right now — and shops for the rest.**

GalleyQuest tracks what's in your pantry, what you can make with it, and turns your weekly meal plan into a smart grocery list. It's a dependency-free static frontend backed by Supabase (Postgres). No build step, no framework.

<!-- Replace with a real screenshot: docs/screenshots/cook-now.png -->
![Cook Now](docs/screenshots/cook-now.png)

---

## What it does

### 🔥 Cook Now
See every recipe you can make from what's currently in stock, ranked by readiness. Each card shows a readiness bar, a plain-English summary ("You have everything" / "3 items to buy"), and the full ingredient list with per-item status. Filter by category or cuisine, or flip on **Show Fully Stocked** to see only what needs zero shopping. One click adds anything missing to the cart.

![Cook Now — expanded ingredient list](docs/screenshots/cook-now-detail.png)

### 🥫 Stock
Your pantry, grouped into the 12 aisles of a real supermarket. Each aisle header shows an at-a-glance count (`7/74 in stock · 1 low`) and an ⏰ expiring flag. Every item has:
- **Status** — OK / LOW / OUT
- **Inline expiration date** — click the cell, pick a date, done
- **Uses** — how many recipes rely on it (⭐ staple, ⚠ rarely used), with one-click **Staples** / **Low-use** filters
- **General quantity** — sensible shopping units (eggs → dozen, milk → gallon, meat → lb)
- **＋ to cart** — add straight to your grocery list

Update your whole pantry by **voice** through Claude Dispatch — just talk, no typing.

![Stock — aisle overview](docs/screenshots/stock-overview.png)

![Stock — expanded aisle with Uses, quantities, and add-to-cart](docs/screenshots/stock.png)

### 📖 Recipes
200+ recipes in a clean, consistent card layout. Every card shows the same three rows: **name + on-hand ratio**, **category · cuisine**, and **ratings**. Rate what you've tried (1–5 ⭐), and see each recipe's computed **efficiency rating** — a 🌿 score based on how many ingredients it needs and how many are rarely used elsewhere. Filter by category, cuisine, search, or "🌿 Efficient" to favor lean, pantry-friendly meals.

![Recipes](docs/screenshots/recipes.png)

### 📅 Meal Plan
A weekly grid — pick a theme and a recipe per day. Themes cross-reference cuisines (choose "Mexican" and the recipe list narrows to Tex-Mex / Southwest), each day shows live readiness ("✓ ready" / "3 to buy"), and one button pulls the whole week's missing ingredients into the cart.

![Meal Plan](docs/screenshots/meal-plan.png)

### 🛒 Grocery Cart
A real shopping list with a lifecycle: **on list → ordered → picked up**. Add missing ingredients from your planned meals across a horizon you choose — **this week, next 2 weeks, 3 weeks, or all planned**. Perishables needed too far out are **held back with a warning** so you don't buy milk three weeks early. When you mark items picked up, the pantry restocks itself.

![Grocery Cart](docs/screenshots/grocery-cart.png)

---

## Highlights

- **Efficiency-first pantry** — a usage-based star rating on every recipe, single-use ingredient flags, and a staples view help keep a lean pantry and cut waste.
- **AKA / interchangeable ingredients** — call for lard, have shortening? You're covered. Substitutes count toward readiness and never get double-bought.
- **Expiration-aware shopping** — buy non-perishables ahead for several weeks; perishables get held for a closer trip.
- **Zero build, zero deps** — a single `index.html` + `ui-cards.js`, served by a ~60-line Node static server.
- **No schema gymnastics** — cuisine/category/tags/ratings ride in a recipe's notes field, so the app runs against a plain Supabase project with anon-role CRUD.

---

## Quick start

No `npm install` — there are no dependencies.

1. **Create a Supabase project** with these tables: `stock_items`, `recipes`, `recipe_ingredients`, `meal_plan`, `grocery_extra_items`, `grocery_dismissed_items`.
2. **Configure credentials:** copy `config.example.js` to `config.js` and fill in your project URL + anon key.
   ```bash
   cp config.example.js config.js
   # then edit config.js
   ```
   `config.js` is git-ignored — **never commit real credentials.**
3. **Run it:**
   ```bash
   node server.js      # serves on http://localhost:8000
   ```

---

## Architecture

| Layer | Choice |
|-------|--------|
| Frontend | Static `index.html` + `ui-cards.js`, vanilla JS, no framework |
| Backend | Supabase (Postgres) via PostgREST, anon-role CRUD |
| Server | Dependency-free Node static file server (`server.js`) |
| Taxonomy/ratings | Stored as lines in `recipes.notes` (`Cuisine:` / `Category:` / `Tags:` / `Rating:`) — no schema changes needed |

## Recipe-maintenance toolkit

`tools/recipe-maintenance/` holds a small, credential-free Python toolkit (reads `config.js` at runtime, standard library only) for data upkeep:

- `backup_db.py` — read-only export of all tables + a manifest
- `verify_recipe_database.py` — integrity checks (no orphans, every ingredient has a quantity, etc.)
- `consolidate_ingredients.py` — merge duplicate/variant stock items into canonical ones
- `coverage.py` — how many recipes are makeable from a set of ingredients, and the best next additions
- `link_stock.py` / `stock_from_recipes.py` — link recipe ingredients to pantry items and build out stock
- `stock_cli.py` / `grocery_cli.py` — voice-pantry ingest and grocery list operations

Run any of them with `python <script>.py` from `tools/recipe-maintenance/`.

---

## Operations

Full operational details — database/connection specifics, data procedures, and history — live in [`docs/OPERATIONAL_HANDOFF.md`](docs/OPERATIONAL_HANDOFF.md).
