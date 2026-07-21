# Recipe maintenance toolkit

Reusable, credential-free scripts for safely backing up, cleaning, and growing
the GalleyQuest recipe database. Standard-library Python 3 only.

## How it stays safe

- **No credentials in the repo.** Every script reads the Supabase URL + anon key
  from the app's local `config.js` at runtime (via `_db.py`) and never prints or
  logs them. `config.js` and the whole `.local/` tree are git-ignored.
- **CRUD only.** These use the anon REST role (PostgREST). They insert/update/
  delete rows; they never run DDL or touch schema.
- **Back up before you change anything.** `backup_db.py` exports all six tables +
  a SHA-256 manifest to `.local/backups/`.
- **Verify + roll back.** Writes are read back and checked per recipe; any
  failure rolls that recipe back and is logged. Nothing is left half-imported.
- **Household data stays local.** Raw source data, curation picks, reports, and
  backups all live under `.local/` (never committed). Only the scripts here are
  tracked.

## Scripts

| Script | What it does | Writes to DB? |
|---|---|---|
| `_db.py` | Shared PostgREST helpers + `backup()`. Reads `config.js`. | — |
| `backup_db.py --label <name>` | Snapshot all six tables to `.local/backups/`. | no |
| `audit_existing_recipes.py` | Report every recipe's gaps (missing quantities, weak instructions, etc.). | no |
| `improve_existing.py [--apply]` | Fill quantities + write instructions for existing recipes, one at a time, with verify + rollback. Needs an improvements file under `.local/`. | with `--apply` |
| `fetch_themealdb.py` | Fetch TheMealDB (a–z) to `.local/MealDB/raw/`. | no |
| `curate_themealdb.py` | Normalize + classify + dedup TheMealDB into Tex-Mex / Southwest / Mediterranean candidates. | no |
| `build_import_set.py` | Combine curated + household supplemental recipes, dedup vs the live DB, validate, emit `final-import.json`. | no |
| `import_recipes.py [--apply]` | Import `final-import.json` in batches of 10 with per-recipe verify + rollback. | with `--apply` |
| `verify_recipe_database.py [--baseline <recipes.json>]` | Integrity check: quantities, instructions, no dupes/orphans, links resolve, baseline IDs preserved. Exit 0 = PASS. | no |

## Typical run (grow the library)

```
python backup_db.py --label before-change
python fetch_themealdb.py
python curate_themealdb.py
python build_import_set.py
python import_recipes.py            # dry-run (default)
python import_recipes.py --apply    # writes, batched, with rollback
python verify_recipe_database.py --baseline .local/backups/<ts>-before-change/recipes.json
python backup_db.py --label after-change
```

`improve_existing.py` and `build_import_set.py` read curation/content files from
`.local/recipe-maintenance/` (git-ignored). Keep those there — never in `tools/`.
