# PANTRY Retirement Manifest

Consolidation of `D:\DEV\PANTRY` into `D:\DEV\GalleyQuest` on **2026-07-20**.
GalleyQuest is the sole operational repository. This manifest records the
disposition of every meaningful PANTRY artifact.

## Recovery archive

- **Path:** `D:\DEV\_archives\PANTRY-pre-consolidation-20260720-203016.zip`
- **Contents:** the complete PANTRY directory **including full `.git` history**
  (278 entries; 236 under `.git/`, incl. `.git/HEAD`).
- **Size:** 464,084 bytes
- **SHA-256:** `4A47C5386A5909B9CE250434A49CF09D3AB3D0748890673A1479FC851647EC7E`
- **Verified:** opens and lists; SHA-256 re-checked after migration — unchanged.

PANTRY had **no git remote** (branch `tweaks`, HEAD `2cc162a`); this archive is
the **sole preservation** of its history.

## Dispositions

**MIGRATED-TRACKED** = committed to GalleyQuest · **LOCAL-ONLY** = git-ignored
under `.local/` · **ARCHIVE-ONLY** = preserved only in the ZIP.

### Reusable offline-harness tooling → MIGRATED-TRACKED

| PANTRY path | New path | Reason |
| --- | --- | --- |
| `tools/extract.py` | `tools/offline-harness/extract.py` (ROOT repointed to `.local/pantry-snapshot`) | Reusable — regenerates the harness from the live app. |
| `local-db.js` | `tools/offline-harness/local-db.js` | Reusable offline Supabase shim. |
| `serve.py` | `tools/offline-harness/serve.py` | Reusable static server (self-locating, port 8001). |
| `schema.sql` | `tools/offline-harness/schema.sql` | Inferred schema reference. |

### Runnable harness + household data → LOCAL-ONLY (git-ignored)

| PANTRY path | New path | Reason |
| --- | --- | --- |
| `index.html` (offline) | `.local/pantry-snapshot/index.html` | Offline app copy; needed to run the harness. |
| `app.js` | `.local/pantry-snapshot/app.js` | Offline app source — **contains anon key**; regenerable via extract.py. |
| `styles.css` | `.local/pantry-snapshot/styles.css` | Offline app copy. |
| `ui-cards.js` | `.local/pantry-snapshot/ui-cards.js` | Bundled so the snapshot runs self-contained. |
| `local-db.js`, `serve.py`, `schema.sql` | `.local/pantry-snapshot/` | Bundled runnable copies (canonical tracked copies live in `tools/offline-harness/`). |
| `seed.js` | `.local/pantry-snapshot/seed.js` | Household data snapshot. |
| `data/*.json` (6) | `.local/pantry-snapshot/data/` | Household stock / recipe / meal-plan / grocery data. |
| `original.html` | `.local/pantry-snapshot/original.html` | Raw live page — **contains anon key**. |
| `README.md` | `.local/pantry-snapshot/PANTRY-README.md` | Prior harness README, kept for reference; operational content superseded by `docs/OPERATIONAL_HANDOFF.md`. |

### Not migrated → ARCHIVE-ONLY

| PANTRY path | Reason |
| --- | --- |
| `ui-cards.js` (tracked copy) | Byte-identical duplicate of GalleyQuest's authoritative `ui-cards.js`. |
| `.gitignore` | Repo-specific; GalleyQuest has its own. |
| `tools/cw-*` (plan packets, reconciliations, envelope, excerpts, impl-diff, request/result/verify) | ClearWright governance history — not operationally useful going forward. |
| `tools/make_excerpts.py`, `tools/scan_check.py` | ClearWright support scripts. |
| `tools/verify_readme.py` | Ad-hoc, trivial theme-reference dumper (hardcoded path); regenerable. |

All ARCHIVE-ONLY items are fully preserved in the recovery ZIP (including `.git`).

## New GalleyQuest additions (tracked)

- `docs/OPERATIONAL_HANDOFF.md` — operational handoff.
- `docs/PANTRY_RETIREMENT_MANIFEST.md` — this manifest.
- `tools/offline-harness/` — the reusable tooling above + `README.md`.
- `.gitignore` — added `.local/`.
- `README.md` — added a pointer to the handoff.
- `.local/MealDB/.gitkeep` — reserved (git-ignored) placeholder; no TheMealDB work started.

## Verification summary (all passed)

- Archive created, opens, includes `.git` + HEAD, SHA-256 verified unchanged.
- GalleyQuest app source unchanged (empty `git diff`); no PANTRY copy overwrote it.
- GalleyQuest app starts on `:8000`, no console errors, `config.js` loads, 28 recipes render, 10 themes present.
- Offline harness serves from `.local/pantry-snapshot` on `:8011` (offline banner, local-db shim), then stopped.
- Secret scan of tracked/committable files: clean (no key / JWT / password / token).
- `git status`: only intentional changes; `.local/` and `config.js` git-ignored.

**PANTRY directory:** removed after this manifest is committed and a final
re-verification passes (deletion status recorded in the session report).
