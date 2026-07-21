# Offline harness

Reusable tooling to run the GalleyQuest app **offline**, against a local
snapshot of the database, without touching Supabase or the network. Migrated
from the retired `D:\DEV\PANTRY` project on 2026-07-20.

## What's here (tracked, no secrets)

| File | Purpose |
| --- | --- |
| `extract.py` | Re-downloads the live app page and dumps all six Supabase tables into the local snapshot. |
| `local-db.js` | Offline stand-in for `window.supabase.createClient` — implements the query-builder surface the app uses, against local seed data. |
| `serve.py` | Dependency-free localhost static server (default port **8001**; serves its own directory). |
| `schema.sql` | Inferred Postgres schema (evidence-based, **not** an authoritative `pg_dump`). |

## Run the offline harness

The runnable snapshot (offline `index.html`, `app.js`, `styles.css`,
`local-db.js`, `serve.py`, `seed.js`, `data/`) lives **git-ignored** under:

    D:\DEV\GalleyQuest\.local\pantry-snapshot\

Start it:

    cd D:\DEV\GalleyQuest\.local\pantry-snapshot
    python serve.py            # http://localhost:8001

Port 8001 avoids clashing with the app / live server on 8000.

## Regenerate the snapshot from the live app

`extract.py` is hardcoded to write into `.local\pantry-snapshot\`:

    python D:\DEV\GalleyQuest\tools\offline-harness\extract.py

It downloads the live page from `http://aet-w11l.local:8000/`, splits the
inline `<style>`/`<script>`, rewires the Supabase CDN tag to load `seed.js` +
`local-db.js`, and pulls all six tables from Supabase REST using the anon key
embedded in the live page. Requires network access to the live app. Its output
(including `original.html`, which contains the anon key) is git-ignored.

## Shim limitations (`local-db.js`)

Implements only what the app calls: `select` (incl. embedded relations,
`count`, `head`), `insert`, `update`, `upsert` (with `onConflict`), `delete`,
`eq`, `in`, `order`, `single`. Relations resolve from a hardcoded FK map at the
top of the file — add new tables/joins there. No auth, realtime, RPC, or
`.or()`/`.gt()`/`.like()` filters.
