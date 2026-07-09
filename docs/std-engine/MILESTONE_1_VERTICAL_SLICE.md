# Milestone 1 — Vertical Slice Definition

**Tracker:** `BE_IMPLEMENTATION_TRACKER.md`  
**Wiring plan:** `IMPORT_WIRING_PLAN.md`  
**Decisions:** `docs/std-prod-impl/std backend answers.md`

## Goal

Prove one end-to-end path from **package import** to **read-only UI** before wiring the remaining schema screens. Success means a user can load the IT STD as DRAFT, open the library, drill into a clause, and see validation + audit evidence — all from real backend data. The UI remains read-only even though the persisted lifecycle is `DRAFT`.

## Scope

### In scope (this slice)

| Step | Backend | UI screen | Desk route |
|---|---|---|---|
| Import commit | `std_engine` commit importer (`DRAFT`, `activation_allowed=false`, `ui_mode=READ_ONLY_INSPECTION`) + PDF registration | — | bench / HTTP |
| Family list | `get_std_families` | 01 STD Library | `/app/std-library` |
| Version list | `get_std_family` | 02 Family Detail | `/app/std-family-detail` |
| Version metadata | `get_std_version` | 03 Version Detail | `/app/std-version-detail` |
| Source trace | `get_std_version_source_traceability` | 04 Source Doc | TBD page route |
| Section tree | `get_std_version_sections` | 05 Section/Clause Map | TBD |
| Clause body | `get_std_clause` | 06 Clause Detail | TBD |
| Findings | `get_std_version_validation_report` | 17 Validation Report | TBD |
| Audit trail | `get_std_version_audit_log` | 22 Audit Log | TBD |

### Out of scope (defer to BE-10 / BE-11)

- Screens 07–16 (parameters through render blocks)
- Screen 18 (review workflow)
- Screen 19 (usage bindings — separate seed ticket BE-08a)
- Screen 20 (import review UI — needs BE-04a HTTP scaffold)
- Screen 21 (version diff stub only in BE-11)

## User journey (acceptance narrative)

```text
1. Operator runs dry-run then commit (CLI or HTTP).
   → Package KE-PPRA-IT-2022-04 imported as DRAFT.
   → Official PDF registered with SHA-256 on STD Source Document.
   → Audit events: STD_PACKAGE_IMPORTED, SOURCE_DOCUMENT_REGISTERED, …

2. User opens STD Library (Desk).
   → Sees KE-PPRA-IT family from API (not static table rows).

3. User opens family → version list.
   → Sees KE-PPRA-IT-2022-04 with lifecycle DRAFT.

4. User opens version detail.
   → Integrity summary reflects validation_summary from API.

5. User opens source traceability.
   → Official PDF listed with hash; anchors from import.

6. User opens section/clause map → selects a clause.
   → Clause detail shows imported text/metadata.

7. User opens validation report.
   → Persisted blockers/warnings from v0.2 manifest + structural validators.

8. User opens audit log.
   → Import and validation events visible.
```

## Technical constraints

- **Static HTML unchanged** — layout guards remain valid; iframe `page.js` replaces data bindings only
- **Default package id** in JS: `KE-PPRA-IT-2022-04` (not UI mock `2024-04`)
- **Read-only** — no save/edit/approve/activate buttons enabled, even though the backend lifecycle is `DRAFT`
- **Missing data** — show validation finding or empty state; never hide gaps
- **Identity hydration** — data-bearing package/version labels must show `KE-PPRA-IT-2022-04`, not static `2024-04` mock values
- **Source traceability** — PDF hash and clause/source anchors are part of the slice, not a later enhancement

## Slice anti-goals

Do not use the vertical slice to introduce any of the following:

```text
editing
approval decisions
activation
supersession execution
fake second version compare
NSSF-as-master import
manual patching of static HTML mock values as the source of truth
```

If a screen needs one of these, render a disabled action or explicit placeholder.

## Prerequisites (must be green before BE-09)

| ID | Deliverable |
|---|---|
| BE-00 | `std_engine` module scaffold |
| BE-01 | Core DocTypes including Source Document, Import Run |
| BE-02–BE-04 | Package reader, dry-run, commit (DRAFT + PDF) |
| BE-05 | At least post-import validation run |
| BE-06 | Read APIs for slice endpoints |
| BE-08 | Validation report + audit log APIs |

BE-04a (HTTP import) can run in parallel; not blocking slice UI except screen 20.

## Tests (slice DoD)

| Layer | Check |
|---|---|
| Unit | Package reader; PDF hash registration; DRAFT commit idempotency |
| Integration | Import creates family/version/sections/clauses/source doc |
| API | Each slice endpoint returns envelope with `packageContext.lifecycleState = DRAFT`, `activationAllowed=false`, `uiMode=READ_ONLY_INSPECTION`, and `canEdit=false` |
| Playwright | Library → family → version navigation still works; slice screens show API-sourced labels; no visible `2024-04` mock identity in data-bearing regions |
| Smoke | `STD-SMOKE-BE-001` package exists; `STD-SMOKE-BE-002` PDF registered; `STD-SMOKE-BE-003` clause queryable |

## After slice is green

Expand in order:

1. BE-10 — wire screens 07–16  
2. BE-08a — usage binding seed  
3. BE-11 — placeholders 18–21 (import review HTTP, version diff stub)  
4. BE-12 — full smoke contract suite  
