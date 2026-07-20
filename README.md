# Pantry & Meal Tracker

A small self-hosted app for tracking pantry stock, recipes, and a weekly meal
plan, with a derived grocery list. Static HTML/JS frontend, backed by
Supabase (Postgres), served by a tiny dependency-free Node static file server.

## Running it

1. `npm` isn't needed — there are no dependencies.
2. Create a Supabase project with `stock_items`, `recipes`,
   `recipe_ingredients`, `meal_plan`, `grocery_extra_items`, and
   `grocery_dismissed_items` tables.
3. Copy `config.example.js` to `config.js` and fill in your project's URL
   and anon key.
4. `node server.js` (serves on port 8000).

`config.js` is git-ignored — never commit real credentials to this repo.
