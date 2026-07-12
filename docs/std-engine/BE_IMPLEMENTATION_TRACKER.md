# STD Engine Backend — Implementation Tracker

**Phase:** Milestone 1 — IT STD read model (import-first, immutable-first, read-only)  
**Module:** `apps/kentender_procurement/kentender_procurement/std_engine/` (Frappe module package: `kentender_procurement.std_engine`; new — **not** `tender_management`)  
**Companion docs:** `IMPORT_WIRING_PLAN.md`, `MILESTONE_1_VERTICAL_SLICE.md`  
**Source pack:** `docs/std-prod-impl/` (`Recommended development sequence…`, `KenTender_STD_Engine_Backend_Import_Wiring_Cursor_Pack.md`)  
**Decisions:** `docs/std-prod-impl/std backend answers.md`  
**Seed data:** `docs/std-prod-impl/data/`  
**UI tracker:** `docs/std-prod-impl/UI_IMPLEMENTATION_TRACKER.md`

## Goal

Load the official PPRA IT STD seed package (`KE-PPRA-IT-2022-04`) into Frappe as a normalized, source-traced, hash-verified read model; expose read-only APIs plus import HTTP scaffolding; wire UI screens to real data via iframe JS; persist validation findings and audit events. **No editing, approval workflow, supersession execution, or live tender generation in Milestone 1.**

Done looks like: bench or HTTP dry-run/commit imports the package as **DRAFT** with the official PDF registered → STD Library shows `KE-PPRA-IT` → vertical slice screens display real backend data → validation report and audit log are populated → version diff shows an explicit single-version stub. `DRAFT` is the persisted lifecycle state; the Milestone 1 UI still runs in **read-only inspection mode** because editing/workflow is intentionally out of scope.

## Locked product decisions

| Topic | Decision | Source |
|---|---|---|
| Module location | New `std_engine/` under `kentender_procurement`; Tender Management consumes STD outputs later | `std backend answers.md` |
| First import lifecycle | **DRAFT only** on commit; match v0.2 manifest; never promote to `ACTIVE` in M1 | Answers + prior session |
| Source PDF | Register `data/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf` as `STD Source Document` on import (filename, SHA-256, page/anchor refs, package link); zip metadata alone insufficient | Answers |
| UI version codes | Static HTML layout unchanged; iframe page JS binds all data-bearing identity fields from APIs (`KE-PPRA-IT-2022-04`); no visible `2024-04` mock identity after wiring | Prior session |
| Version diff (screen 21) | **Single-version stub** for M1; no fake second STD; real compare deferred until second fixture package exists | Answers |
| Usage bindings (screen 19) | Seed **minimal read-only** rows from `tender_binding_smoke_tests.json` expectations; `fixture_source = "SMOKE_TEST_EXPECTATION"` | Answers |
| Import UX | **Bench/CLI first** + HTTP scaffolding now: `POST /std-engine/import/dry-run`, `POST /std-engine/import/commit`, `GET /std-engine/import-runs/:id`; HTTP wraps the same services as CLI | Answers |
| Implementation start | Vertical slice after schema (see `MILESTONE_1_VERTICAL_SLICE.md`) | Answers + prior session |
| NSSF / fixtures in zip | Do not import NSSF ERP as STD master; skip `fixtures/nssf_erp/` by default | Pack + cursor rule 007 |

## Repo layout (Frappe)

| Concern | Path |
|---|---|
| Module root | `apps/kentender_procurement/kentender_procurement/std_engine/` |
| Dotted import path | `kentender_procurement.std_engine` |
| DocTypes | `std_engine/doctype/` |
| Import pipeline | `std_engine/package_import/` |
| Validation | `std_engine/validation/` |
| Audit | `std_engine/audit/` |
| Read APIs | `std_engine/api/` (`@frappe.whitelist`) |
| Import HTTP | `std_engine/api/import_api.py` (or Frappe API routes under `/api/method/...`) |
| Bench commands | `bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.<method>` |
| Tests | `std_engine/tests/` + `apps/kentender_v1/tests/ui/smoke/std-prod-impl/` |
| Seed zip | `docs/std-prod-impl/data/KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip` |
| Official PDF | `docs/std-prod-impl/data/DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf` |

## Canonical seed identity

| Field | Value |
|---|---|
| Family code | `KE-PPRA-IT` |
| Package / version code | `KE-PPRA-IT-2022-04` |
| Source authority | PPRA (DOC. 10) |
| Package quality | `RECONCILED_DRAFT_NOT_ACTIVATABLE` (`activation_allowed: false`) |
| Commit target state | **DRAFT** |

## Milestone 1 runtime guardrails

| Guardrail | Required behavior |
|---|---|
| Persisted lifecycle | `DRAFT` exactly as the v0.2 manifest requires |
| Activation flag | `activation_allowed = false`; importer must persist blockers as validation findings |
| UI mode | `READ_ONLY_INSPECTION`; DRAFT does **not** imply editable UI in Milestone 1 |
| Edit/mutation APIs | Not implemented; any accidental write endpoint must return an explicit not-implemented/forbidden response |
| Active protection | Importer must never create or mutate `ACTIVE` records in M1 |
| Identity source of truth | API/database values override every static mock identity shown in HTML |
| Missing data | Show empty state or validation finding; never silently fabricate legal content |

## Core lifecycle enum for M1

Use exact uppercase lifecycle values in the backend and API envelope:

```text
DRAFT
STRUCTURING
INTERNAL_REVIEW
LEGAL_REVIEW
PROCUREMENT_REVIEW
APPROVED
ACTIVE
SUPERSEDED
ARCHIVED
```

M1 commits only `DRAFT`. Other states are reserved for later workflow milestones.

## Milestone 1 tracker

| ID | Workstream | Description | Depends on | Tests | Status | Evidence |
|---|---|---|---|---|---|---|
| **BE-00** | Repo audit | Confirm Frappe module scaffold, DocType naming, API routing, test patterns; report before coding | — | `test_be_00_module_scaffold` | Done | `BE-00_REPO_AUDIT.md`; `std_engine/` scaffold; `modules.txt` + `STD Engine`; `constants.py` + `paths.py`; 9/9 unit on `kentender.midas.com` |
| **BE-01** | Core DocTypes | Family, Version, Source Document, Source Anchor, Section, Clause, Parameter, Rule, Form Schema, Form Field, Requirement Schema, Price Schedule Schema, Evaluation Schema, Render Block, Validation Run, Validation Finding, Audit Event, Usage Binding, **Import Run** (for HTTP `import-runs/:id`). Include package context, source/hash fields, `activation_allowed`, exact lifecycle enum, and `ui_mode`. | BE-00 | `test_be_01_core_doctypes` | Done | 19 DocTypes migrated; `doctype_schema.py` + `validators.py`; 15/15 integration on `kentender.midas.com` |
| **BE-02** | Package reader | Read zip; parse manifest/checksums; map nested JSON folders; classify required/optional files; no DB writes | BE-00 | `test_be_02_package_reader` | Done | `package_import/package_reader.py`, `manifest_validator.py`, `checksum_verifier.py`; 12/12 unit on `kentender.midas.com` |
| **BE-03** | Dry-run importer | Planned insert/skip/fail; missing files/anchors; deterministic report; package/source checksums; CLI + feeds HTTP dry-run | BE-02 | `test_be_03_dry_run_importer` | Done | `package_import/import_planner.py`, `dry_run_importer.py`, `import_report_writer.py`, `hash_utils.py`, `dry_run.py`; 16/16 on `kentender.midas.com` |
| **BE-04** | Commit importer | Transactional import as **DRAFT**; idempotent when `package_id + package_sha256` match; fail on same package ID with different hash unless an explicit future replace-draft workflow exists; register **official PDF**; skip NSSF fixtures; audit events | BE-01, BE-03 | `test_be_04_commit_importer` | Done | `package_import/record_mapper.py`, `commit_persister.py`, `commit_importer.py`, `commit.py`, `audit/event_service.py`; 8/8 integration on `kentender.midas.com` |
| **BE-04a** | Import HTTP scaffold | `POST dry-run`, `POST commit` (DRAFT only), `GET import-runs/:id`; wraps same services as CLI | BE-03, BE-04 | `test_be_04a_import_api` | Done | `api/import_api.py`, `services/import_run_service.py`; 9/10 integration (1 skipped auditor user) on `kentender.midas.com` |
| **BE-05** | Validation engine | Persistent validators + findings from package blockers and structural checks | BE-04 | `test_be_05_validation_engine` | Done | `validation/validation_engine.py`, validators (activation, integrity, source, clause); `validation/run.py`; 8/8 on `kentender.midas.com` |
| **BE-06** | Read APIs (core) | Families, family, version, source traceability, sections, clauses; all endpoints return standard envelope with `packageContext`, `uiMode`, validation summary, and audit snapshot | BE-04 | `test_be_06_read_api` | Done | `api/read.py`, `services/envelope.py`, `services/read_service.py`; 8/8 integration on `kentender.midas.com` |
| **BE-07** | Read APIs (schemas) | Parameters, rules, forms, requirements, price schedules, evaluation, render blocks | BE-04 | API contract tests | Done | `test_be_07_read_api.py` 6/6 pass; `schema_read_service.py` + 10 whitelisted GET endpoints in `api/read.py` |
| **BE-08** | Read APIs (governance) | Validation report, audit log, usage bindings, import run report; **version diff stub** (single-version message) | BE-05, BE-04a | API contract tests | Done | `test_be_08_read_api.py` 6/6 pass; `governance_read_service.py` + 7 whitelisted GET endpoints in `api/read.py` |
| **BE-08a** | Usage binding seed | Minimal rows from `tender_binding_smoke_tests.json`; `fixture_source = SMOKE_TEST_EXPECTATION` | BE-04 | Seed + API tests | Done | `usage_binding_seeder.py`, `map_usage_binding_record`; commit seeds 3 bindings; `test_be_08a_usage_binding_seed.py` 6/6 pass |
| **BE-09** | UI wiring (vertical slice) | Screens 01–06, 17, 22 via iframe JS → read APIs; static HTML unchanged | BE-06, BE-08 | Playwright | Done | `std_prod_engine.js` + page shells; `test_std_prod_vertical_slice_desk_wiring.py` 5/5; `std-vertical-slice.spec.ts` 4/4 pass on `kentender.midas.com` |
| **BE-10** | UI wiring (schemas) | Screens 07–16 | BE-07, BE-09 | Playwright | Done | `std_prod_schema_pages.js` + engine hydrators; `test_std_prod_schema_desk_wiring.py` 6/6; `std-schema-slice.spec.ts` 4/4 pass |
| **BE-11** | UI wiring (placeholders) | 18 Review (composite read); 19 Usage (seeded fixtures); 20 Import Review (dry-run report); **21 Version Diff (single-version stub)** | BE-08, BE-10 | Playwright | Done | `std_prod_governance_pages.js` + engine hydrators; `test_std_prod_governance_desk_wiring.py` 6/6; `std-governance-slice.spec.ts` 4/4 pass; `std-vertical-slice.spec.ts` 5/5 pass |
| **BE-12** | Smoke contracts | Package/family/version DRAFT; PDF registered; sections/clauses; findings; audit; no ACTIVE mutation | BE-04–BE-08 | `STD-SMOKE-001..015` via `test_be_12_smoke_contracts` | Done | 15/15 integration on `kentender.midas.com`; v1_0 package `FULL_EXTRACTION_CANDIDATE` |
| **BE-14** | FULL_VERBATIM_SOURCE_EXTRACTION_V1_1 | PDF verbatim clauses + TDS/SCC parameter source text; reconciliation JSON; legal review gate; v1_1 zip | BE-04, BE-05, BE-12 | `STD-SMOKE-016..020` via `test_be_14_verbatim_smoke_contracts`; `make std-verbatim-gate` | Done | 94/94 clauses + 155/155 params extracted; `KE-PPRA-IT-2022-04_Seed_Package_v1_1.zip`; import + smoke on `kentender.midas.com` |
| **BE-15** | Step 1 closure — activation, consumption, render | Activation readiness + legal gate sync; `activate_std_version` workflow; tender binding (ACTIVE + dev test-mode); package-level render API; NSSF calibration fixture + golden bind | BE-14 | `STD-SMOKE-021..028` + `CAL-NSSF-001..003,012,013` via `test_be_15_step1_activation_consumption`; `make std-step1-gate`; `make nssf-calibration-gate`; `std-step1-activation.spec.ts` | Done | 15/15 BE-15 integration; `std-step1-gate` + `nssf-calibration-gate` pass on `kentender.midas.com`; `CAL-NSSF-002` golden bind; Playwright `std-step1-activation.spec.ts` 1/1 |
| **BE-DOC** | Tracker docs | This file + `IMPORT_WIRING_PLAN.md` + `MILESTONE_1_VERTICAL_SLICE.md` + `BE-00_REPO_AUDIT.md` committed | — | — | In progress | Tracker trio + audit report written; git commit pending |

## API ↔ UI map (summary)

Full mapping in `IMPORT_WIRING_PLAN.md`.

| Screen | Milestone 1 behavior |
|---|---|
| 01–06, 17, 22 | Real data (vertical slice first) |
| 07–16 | Real data (after slice green) |
| 18 Review | Read-only composite placeholder |
| 19 Usage | Seeded smoke-test bindings (fixture-tagged) |
| 20 Import Review | Dry-run / import-run report via HTTP |
| 21 Version Diff | **Single-version stub** — no compare until second package |
| 22 Audit Log | Import + validation events |

## Import endpoints (Milestone 1)

| Method | Route | Behavior |
|---|---|---|
| `POST` | `/std-engine/import/dry-run` | Parse zip + PDF path; no DB commit; returns `import_run` id + report |
| `POST` | `/std-engine/import/commit` | Transactional import; **target state DRAFT only**; registers PDF |
| `GET` | `/std-engine/import-runs/:id` | Dry-run or commit report by id |

Bench equivalents remain the primary operator path for CI and local dev.

## Exit criteria (Milestone 1)

- [x] `std_engine` module exists separately from `tender_management`
- [x] Core STD DocTypes registered under `STD Engine` module (BE-01)
- [ ] IT STD imports as DRAFT from zip + official PDF registered with hash
- [ ] `activation_allowed=false`, `ui_mode=READ_ONLY_INSPECTION`, and no `ACTIVE` promotion
- [ ] Dry-run deterministic; commit idempotent
- [x] HTTP import scaffold returns import-run reports
- [ ] Vertical slice screens show API-driven data (no silent fake rows; no visible `2024-04` mock package identity in data-bearing regions)
- [x] Usage bindings seeded with `fixture_source = SMOKE_TEST_EXPECTATION`
- [ ] Version diff returns single-version stub (no fabricated second STD)
- [ ] Validation findings + audit events persisted and visible
- [ ] Smoke + Playwright evidence on `kentender.midas.com`

## Explicitly deferred

- Second STD package / real version diff compare
- Full approval workflow chains beyond legal gate (INTERNAL_REVIEW, PROCUREMENT_REVIEW)
- Editing, addendum generation, live tender generation
- NSSF as STD master; importing `fixtures/nssf_erp/` by default
- IT Tender Configuration Wizard DocTypes and instance-level preview POST (Step 2)

## BE-00 start instruction (when approved)

Begin repo audit and `std_engine` module scaffold only. Register official PDF on import design. Implement CLI import plus dry-run/commit HTTP scaffolding. Keep version diff single-version. Seed minimal smoke-test usage bindings. Do not extend `tender_management`.
