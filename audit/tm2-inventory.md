# TM2 inventory (WP0.2) — written before any deletion, 6 Oct 2026

Owner decision D1: Tender Management v2 (TM2) is permanently retired, no reference left. Findings: AUD-XC-003, XC-011, XC-126 (+ XC-143).
Gate pattern used throughout: `git grep -i -E 'tm2|tender[_ -]management[_ -]v2|tender_management|tender-management'` excluding `.git`, `node_modules`, `archive/`, `docs/mvp-1-r1/**`, `audit/`.
Baseline at HEAD: 414 files hit (62 under docs/ outside mvp-1-r1, 352 elsewhere).

## 1. What TM2 is in this repo

| Area | Path | Size |
|---|---|---|
| Python package | `kentender_procurement/kentender_procurement/tender_management/` (api, audit, constants, fixtures, scenarios, security, seeds, services, tender_publication, tests) | 422 files on disk, 228 tracked (rest is `__pycache__`) |
| Doctypes (23 `TM2 *`) | `kentender_procurement/.../kentender_procurement/doctype/tm2_*` (Addendum, Addendum Acknowledgement, Addendum Impact Record, Bid Draft Metadata, Bid Receipt, Bid Submission, Bid Submission Component, Clarification Request/Response, Contract Handoff Reference, Evaluation Handoff Record, Late Submission Attempt, Notification Record, Opening Readiness Record, Publication Readiness, Publication Record, Supplier Participation, Tender, Tender Access Rule, Tender Audit Event, Tender Closing Record, Tender Invitation, Tender Timeline) | 23 dirs (the finding's "56" counts files) |
| TM2 companion doctypes (module Kentender Procurement) | `tender_publication_approval_decision`, `tender_publication_snapshot` (both Link to `TM2 Tender`, and to dropped `Tender STD Instance`/`Procurement Package`); `security_permission`, `security_role`, `security_role_permission` (the TM2 permission catalogue, consumed only by `tender_management/security/permissions`) | 5 dirs |
| Desk Page | `kentender_procurement/page/tender_management_v2/` (route `tender-management-v2`) | 1 |
| Assets | `public/js/tender_management_v2_workbench_page.js` (556 hits), `public/js/tm2_workbench_lifecycle.js`, `public/js/tm2_tender_handoff_panel.js`, `public/css/tender_management_v2_workbench.css`, `public/css/tm2_tender_handoff_panel.css` | 5 |
| hooks.py | lines 65, 67, 86, 89 (app_include css/js), 251 (page_js `tender-management-v2`) | 5 |
| Workspace / sidebar | Sidebar item "Tender Management" is a *section break* over the live Tenders/Evaluation/Awards pages: KEEP (it is not TM2). `setup/workspace_permissions.py:157`, `setup/tests/test_workspace_sidebar_fastpath.py:168` map route `tender-management-v2` | 2 lines |
| kentender_core | `kt_cl_surface_registry.js:23` crumb for `tender-management-v2`; `kt_desk_document_title.js:15`; `tests/test_kt_cl_surface_registry_contract.py:88`; `seeds/stable_platform_seed/purge.py` (TM2 tender purge, 40 hits); `seeds/demo_platform_seed/pe_cleanup.py:51`; `seeds/kentender_mvp_v1/users.py:30` (comment) | 6 files |
| Makefile | targets `tm2-v1-contamination-audit`, `p11-04-tm2-surface-gate`, `p11-05-tm2-surface-legacy-literal-gate`, `p12-01-tm2-works-scenario-harness` (script outside repo), `x-01-planning-std-poc-gate`, `x-02-no-plain-bench-build-gate`, `x-03-doc9-acceptance-sequence-gate` (tender-management prompt docs gates) and their `.PHONY`/help lines | ~14 lines |
| scripts/ | `archive-std-module-git-mv.sh`, `archive-std-module-inventory.sh`, `verify-std-archived.sh`, `run-std-library-regression.sh` (one-off STD-archival scripts and a runner that name `tender_management/...` paths) | 4 |
| `.cursor/rules/kentender-officer-guided-surface-gate.mdc` | globs on `tender_management/services/officer_*.py` | 1 |
| Browser tests | `tests/ui/helpers/tm2Workbench.ts`, `tests/ui/tm2_*.spec.ts` (2), `tests/ui/smoke/procurement/tender-management-v2-*.spec.ts` (14), `tm2-workbench-*.spec.ts` (4) | 21 |
| Patches | `patches.txt:37` `remove_tender_management_v1_desk_artifacts` (one-shot, long applied); `patches/retire_it_std_wizard_cleanup.py` (`_purge_tm2_std_bindings`); docstring mentions in `patches/bds_chg_001_v08_retire_bid_slice.py`; commented-out lines 43-44 | 4 |
| Other tests | `bid_submission/tests/test_legacy_retirement.py` (docstring), `setup/tests/test_workspace_sidebar_fastpath.py` | 2 |

## 2. Live code that depends on TM2 (shared, needs surgery, not deletion)

| Consumer | Dependency | Plan |
|---|---|---|
| `procurement_lifecycle/api/journey_api.py` | imports `tender_management.services.tm2_handoff_panel` (module-level) -> whole journey API would fail to import | remove `get_tm2_handoff_panel` + import |
| `procurement_lifecycle/{tender_publication,tender_closing,opening_readiness,std_readiness}_handoff.py` | build handoff cards from TM2 Tender/Closing/Opening records | TM2-only: delete |
| `procurement_lifecycle/{business_readiness_summary.py, api/readiness_api.py}` + `public/js/business_readiness_summary.js/css` | supports only `TM2 Tender` | TM2-only: delete |
| `procurement_lifecycle/{evidence_timeline,handoff_freshness,journey_aggregate,journey_by_object,journey_object_lookup,source_module_authority,constants,api/handoff_api}.py` | TM2 object types / `tm2_tender_ref` / TM2 Tender Audit Event | strip TM2 branches |
| Doctype `Procurement Journey` (field `tm2_tender_ref`, search field), `Procurement Handoff Card` (description text) | field to a retired object | remove field/text |
| `procurement_lifecycle/seeds/works_master_*` | "WORKS master seed" world is built around a TM2 tender (`works_master_tender_seed`, `works_master_std_seed`, counts `tm2_reference_records`) and handoff payloads | TM2-bound: strip |
| `kentender_core/seeds/stable_platform_seed/{purge,load}.py`, `demo_platform_seed/*` | import `tender_management.seeds.purge_smoke_test_tenders`, purge TM2 doctypes | strip TM2 branches |
| `procurement_home/services/{home_pipeline,home_deadlines,home_actions,home_portfolio}.py`, `seed/seed_home_demo.py`, `SOURCE_MAP.md` | `if db.exists("DocType","TM2 Tender")` guarded counts | remove branches |
| Other module tests that name TM2 | `procurement_lifecycle/tests/test_r*_tm2*`, `test_g9_007`, `test_r8_012`, `test_r3_016`, `test_r5_011`... | delete TM2-only, trim the rest |

## 3. Non-TM2 (decided: KEEP, not part of D1)

- **Tender Configurations (legacy IT-wizard + BWMF)**: `kentender_procurement/tender_configurations/` including `Confirmed Tender Document Package` and `IT Tender Publication Record` (AUD-XC-011) and the services with `frappe.db.commit()` (AUD-XC-143). Own module (Module Def `Tender Configurations`, modules.txt, own Desk pages `it-tender-configuration-*`, `publication-setup`, `publications`, own Makefile BWMF/E1 gates, used by `kentender_core` demo seed). Not imported by any TM2 file and imports nothing from it. -> XC-011 is fixed in place (drop role `All` permission); XC-143 does NOT close with TM2 (follow-up, outside this WP's deletion remit).
- Sidebar section "Tender Management" label and the live Tenders module (`kentender_procurement/tenders/`, Module Def `Tenders`, Doctype `Tender Publication` in module Tenders).
- `Tender BoQ Item`, `Tender Lot`, `Tender Works Requirement`, `Tender Required Form`, `Tender Section Attachment`, `Tender Validation Message`, `Tender Hardening Finding`, `Tender Derived Model Readiness`: v1 (`Procurement Tender`-era) child tables, no TM2 link; nothing references them. Orphaned, follow-up (not TM2).
- `Procurement Navigation`: hooks fixture, shared.

## 4. Site state (read-only SELECT counts, 6 Oct 2026)

| Site | TM2 doctype rows in `tabDocType` | rows in any `tabTM2 *` table | `Procurement Journey` / `Procurement Handoff Card` rows | Tender Publication Approval Decision / Snapshot rows | Page `tender-management-v2` |
|---|---|---|---|---|---|
| kentender-test.local | 23 | 0 in all 23 | 0 / 0 | 0 / 0 | present |
| kentender.midas.com (dev, read-only) | 23 | 0 in all 23 | 0 / 0 | 0 / 0 | present |

No data to preserve. Module Def "Tender Management" does not exist (tender_management is only a Python package under module `Kentender Procurement`). No Workspace named like `Tender Management` exists.

## 5. Finding ownership

| Finding | Belongs to | Resolution |
|---|---|---|
| XC-003 | TM2 (`tender_management/tender_publication/api/handlers.py`) | closes by deletion |
| XC-011 | Tender Configurations (not TM2) | fix in place: remove the `All` DocPerm on both doctypes |
| XC-126 | half TM2 (`export_tender_evidence`, closes by deletion); half Planning post-sync patches without `table_exists` | TM2 half by deletion; patch half fixed with guards |
| XC-143 | Tender Configurations / Tenders | not TM2; stays open |

## 6. Delete list / keep list summary

Delete: everything in section 1; TM2-only parts in section 2. Drop patch `drop_retired_tm2_doctypes` (single place the TM2 doctype names may appear) removes the 23 `TM2 *` + 5 companion DocType records, tables, Page `tender-management-v2`, DocPerm/custom rows, with existence guards.
Docs outside docs/mvp-1-r1 and archive: delete the wholly-TM2 documents (`docs/prompts/tender management/`, `docs/tender-management-v2/`, `docs/audit/module_implementation_catalog/06_tender_management.md`, `docs/audit/seed_data_bundle/fixtures/tm2_seed_works_open_tender.json`); about 50 other superseded planning/handoff prompt packs mention TM2 in passing: listed as document follow-ups (recommend moving to archive/), not edited.

## 7. Risks

- Dev site keeps orphan DB rows/tables until the owner runs the drop patch (harmless: sites already empty).
- `hooks.py`, `patches.txt` are shared with concurrent agents: small targeted edits only.
- Lifecycle layer (Journey/Handoff cards) loses its TM2 source types; the layer is already empty on both sites and has no menu entry.
