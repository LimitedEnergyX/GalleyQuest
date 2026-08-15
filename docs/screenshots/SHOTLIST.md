# Screenshot shot list

Fresh captures are produced with real Chrome (Playwright, `channel: chrome`) at a
1360-wide viewport, `deviceScaleFactor: 2`, scrolled to the top, and content-cropped
(clip height = min(viewport, actual content height)). Save with the exact filename
below into this folder (`docs/screenshots/`).

| Filename | Tab / state | What to show |
|----------|-------------|--------------|
| `recipes.png` | Recipes (default grid) — **hero** | The 3-column card grid: name + on-hand ratio, category · cuisine, rating + efficiency stars. |
| `cook-now.png` | Recipes → 🔥 Cook Now ON | The pressed toggle + the banner, filtered to recipes with ≥85% of ingredients in stock. |
| `cook-now-detail.png` | Recipes, first card expanded | Full ingredient list with per-item ✓/OUT status and the "+ Add N to cart" button. |
| `stock-overview.png` | Stock (aisles collapsed) | Food-only aisle roll-ups (`14/86 in stock`, `2 low`) — no household clutter. |
| `stock.png` | Stock, Produce expanded | The Uses / Aisle / Status / Expires / Qty columns + the ＋ cart button. |
| `meal-plan.png` | Meal Plan (a populated week) | The weekly grid: Slot/Theme/Recipe/Meal name/Notes/Status, days filled, readiness badges. |
| `grocery-cart.png` | Grocery Cart (populated) | Aisle-grouped list, the "Add from planned meals" horizon buttons, and the "Let Claude order it" workflow box. |

Note: Cook Now is now a **filter inside the Recipes tab**, not a separate tab. Stock
is **food-only** (no household category). ~1360px wide @2x, PNG.
