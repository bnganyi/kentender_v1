# BDS-CHG-001 v0.8: legacy inventory (Phase 1 input)

| Control | Value |
|---|---|
| Version | 0.8-phase0.1 |
| Status | Phase 0 working document (plan BDS-CHG-001 v0.8) |
| Purpose | Exact scope for implementation plan Phase 1 ("Retire the legacy bid slice"). Owner decisions apply: legacy bid records deleted outright with no migration (21 Sep 2026); BWMF/STD-wizard machinery untouched (21 Sep 2026, follow-up FU-05); **OD-F (26 Sep 2026)**: retire only the bid slice and the route collisions now, and give the rest of TM2 its own later clean-up. |
| Evidence | Read-only repository scan on 26 Sep 2026: `kentender_procurement/hooks.py` (route rules lines 105–188, `app_include_js`, `page_js`), `www/`, `public/`, `templates/includes/`, `tender_configurations/{services,tests,seed,api.py,__init__.py}`, TM2 doctype importers, root `Makefile` (lines 922–1291). |
| Rule | Nothing below is deleted without its Phase 1 test (`bid_submission/tests/test_legacy_retirement.py`) and a clean `bench migrate`. A file is removed only after its importers are removed or re-pointed. |

## 1. Retire now (Phase 1): `tender_configurations` bidder workspace

The bid slice is the whole **bidder workspace** of `tender_configurations`, not only the eight bid services the 21 Sep plan listed. About 13 bidder "section" services import them, and so do the module's `__init__.py` and `api.py`.

| Kind | Items |
|---|---|
| Route rules (`hooks.py` 106–188) | `/supplier/tenders/<tender_code>` (TM2; see BDS-CHG-001 §2) and all 22 `/tenders/<publication_ref>[/…]` rules. The last, `/tenders/<publication_ref>` → `tenders/overview`, collides directly with BDS-CHG-001 §9 `/tenders/{tender_reference}`. |
| `www/` | All of `www/tenders/` (index, overview, workspace, documents, evidence, issues, section, submit_bid, final_bid_review, submission_receipt, review_and_validate, the form_of_tender / cbq / statutory / tender_security / preliminary / qualification / technical_proposal / requirements_compliance / price_schedule pages, `_final_submission_context.py`). `www/tenders/index.py` currently serves `/tenders` (Tenders FU-19). |
| Desk pages | `bid-submissions` (`kentender_procurement/page/bid_submissions`) and `it-electronic-bidder-workspace` (`page/it_electronic_bidder_workspace`), with their `page_js` entries. |
| Global JS (every Desk page) | `app_include_js` `electronic_bid/bidder_workspace_renderer.js`. |
| Public assets | `public/js/{bid_submissions_page, it_electronic_bidder_workspace_page, kt_bidder_countdown, final_submission_web, price_schedule_web, published_tender_overview_web}.js`, `public/js/electronic_bid/`, `public/css/{bid_submissions_page, bidder_portal_forms, final_submission_web, price_schedule_web}.css`. |
| Templates | `templates/includes/{kt_bidder_portal_nav, kt_bidder_workspace_sidebar}.html`, plus `templates/includes/{qualification, technical_proposal}/` if used only by the retired pages (confirm in Phase 1). |
| Bid services | `tender_configurations/services/{electronic_bid, bid_submissions, bid_evidence, bidder_presentation, bid_issues, bidder_submission_schema, price_schedule_bidder, final_submission}.py`. |
| Bidder section services (importers of the above) | `tender_configurations/services/{available_tenders, published_tender_overview, tender_documents_addenda, confidential_business_questionnaire, form_of_tender, statutory_declarations, tender_security, preliminary_requirements, qualification_and_capability, technical_proposal_and_implementation_plan, requirement_matrix, submission_checklist}.py`, plus `section_response_envelope.py` if nothing kept imports it (confirm in Phase 1). |
| Module surface | Bid and bidder endpoints in `tender_configurations/__init__.py` (lines ~32–43 import `get_electronic_bidder_workspace`, `create_electronic_bid_draft`, `save_electronic_bid_section`, `validate_electronic_bid`, `submit_and_seal_electronic_bid`, `get_electronic_bid_receipt`, `fill_electronic_bid_draft_for_tests`, `get_published_tender_overview`, `get_submission_checklist`, …) and in `tender_configurations/api.py` (119 whitelisted methods; only the bid and bidder ones are removed). |
| Tests | Every `tender_configurations/tests/*.py` that imports a retired service. The 26 Sep scan found about 30, including `test_bid_submissions_api`, `test_electronic_bid_submission`, `test_bidder_presentation_boundary`, `test_final_submission_readiness`, `test_available_tenders_api`, `test_published_tender_overview_api`, and the `test_lean_*` bidder-section tests. |
| Seed | `tender_configurations/seed/bid_submissions_officer_fixtures.py`, `seed/demand_to_bidder_journey_sample.py`. |
| Doctypes (patch `bds_chg_001_v08_retire_bid_slice`) | `Electronic Bid Submission`, `IT Bid Opening Record`, `Electronic Bid Audit Event`: rows deleted children first, then the doctypes. |
| Navigation | `workspace_sidebar/procurement.json` "Bid Submissions" (line 125) → removed. Desktop Icon "Tenders" keeps `/tenders`, which then serves the new BDS-DES-01. |
| Make targets (`Makefile` 922–1078) | `bid-submissions-domain-gate`, `ui-bid-submissions-gate`, `bw-domain-gate`, `bw-a0…a4-domain-gate`, `bw-x100`, `bw-s300`, `bw-fot`, `bw-statutory`, `bw-tender-security`, `bw-preliminary`, `bw-qualification`, `bw-technical-proposal`, `bw-requirements-compliance`, `bw-price-schedule`, `bw-final-submission` (+`-stitch-contract`) domain gates, every `ui-bidder-*-gate`, `seed-demand-to-bidder-journey`. |
| UI specs | `tests/ui/smoke/bid-submissions/`, `tests/ui/smoke/bidder-workspace/`. |
| Cross-app | `kentender_core/seeds/demo_platform_seed/{actionable, transitions, clear, load, validate}.py`: bid-scenario calls replaced by `{"ok": False, "skipped": True, "reason": "BID_SUBMISSION_MODULE_RETIRED"}`; imports of kept BWMF/wizard modules stay. |
| Empty scaffold | `kentender_procurement/bid_submission_opening/` (not in `modules.txt`; created in f39e5f09). |

## 2. Retire now (Phase 1): TM2 supplier-facing routes only

| Kind | Items |
|---|---|
| Route | `/supplier/tenders/<tender_code>` → `www/supplier/tenders/index.{py,html}` (login required; resolves the supplier through `KTSM Supplier Profile`). |
| Supplier-portal API | `tender_management/api/supplier_portal.py` and the `supplier_portal_*` services that only it uses (confirm importers in Phase 1). |

**Refinement of the Phase 1 plan text, recorded here:** the TM2 *bid* doctypes (TM2 Bid Submission, TM2 Bid Submission Component, TM2 Bid Receipt, TM2 Bid Draft Metadata, TM2 Late Submission Attempt) are **not** dropped in Phase 1. The 26 Sep scan shows TM2's officer workbench still reads them: `tender_management/services/{close_tender, complete_evaluation_handoff, export_tender_evidence, get_bid_content, prepare_opening_readiness, tm2_workbench_tender_detail}.py`. That workbench stays live until the OD-F clean-up, so the doctypes and their records go with it (BDS-CHG-001 §4).

## 3. Kept (not this module's work)

| Item | Why |
|---|---|
| `tender_configurations/bidder_workspace_manifest/` (BWMF, ~35 doctypes), `Tender Configuration`, `IT Tender Publication Record`, the "IT Tender Configuration" wizard pages and their `page_js` | Owner, 21 Sep 2026: already deprecated, left untouched (FU-05). `bidder_workspace_manifest/nssf_fixture_errata.py` names section keys as strings only; it imports no retired service. |
| `doc_events["File"]["on_trash"]` → BWMF CAS guard | BWMF-owned. |
| `bw-manifest-phase1…5-gate`, `e1-nssf-seed-gate`, `e1-nssf-poc-gate` | They exercise BWMF/schema-compiler tests, not the bid slice. (The 21 Sep plan listed `e1-nssf-*` for removal; that is corrected here.) Phase 1 confirms that none of their test modules imports a retired service. |
| `page_js` `publications`, `publication-setup`, `published-tender-overview`, `it-tender-package-review` | Officer publication surfaces, not bidder-facing. Belong to the TM2/legacy publication clean-up. |

## 4. Deferred to the OD-F TM2 clean-up (follow-up, not this cycle)

| Item | Dependents found 26 Sep 2026 |
|---|---|
| All of `kentender_procurement/tender_management/` and the 23 `tm2_*` doctypes (module "Kentender Procurement") | 25 files in `procurement_lifecycle/` (e.g. `journey_object_lookup.py`, `tender_publication_handoff.py`, `opening_readiness_handoff.py`, `tender_closing_handoff.py`, `journey_aggregate.py`, `api/journey_api.py:66`, `seeds/works_master_*`, tests `test_g9_007_*`, `test_r8_012_*`, `test_r1_009_*`) and `procurement_home/` (`services/home_deadlines.py`, `seed/seed_home_demo.py`, links to `/desk/tender-management-v2` and `/desk/publications`). |
| `app_include_js` `tm2_tender_handoff_panel.js`, `tm2_workbench_lifecycle.js`, `it_tender_configuration_create_modal.js`; `app_include_css` `tm2_tender_handoff_panel.css`, `tender_management_v2_workbench.css`; `page_js` `tender-management-v2` | TM2 officer workbench. |
| `kentender_core/seeds/stable_platform_seed/purge.py` (imports `tender_management.seeds.purge_smoke_test_tenders`; lists a non-existent "TM2 Tender STD Binding") | Stable-platform seed. |

## 5. Phase 1 as built (26 Sep 2026)

This section adds to the inventory above, which is left as written.

The Phase 1 build found more to retire than §1 listed. Each item has the same basis: it served only the retired bidder surfaces.

| Addition | Why |
|---|---|
| Desk page `published-tender-overview` (`kentender_procurement/page/published_tender_overview`, `public/js/published_tender_overview_page.js`) and its shared surface-registry entry "BW-A1" (`kentender_core/public/js/kt_cl_surface_registry.js` and its contract test) | §3 listed it as a kept officer surface. It is bidder-facing: it calls `get_published_tender_overview`, `start_or_get_bid_workspace` and `download_published_tender_document_pdf`. |
| Bidder web scripts `public/js/{qualification_and_capability_web, requirement_matrix_web, technical_proposal_web, tender_documents_addenda_web, requirements_compliance_review}.js` and the bidder `*_web.css` styles | Used only by the retired `www/tenders` pages. |
| `tender_configurations/services/{section_response_envelope, section_status}.py` | Imported only by retired services. |
| 34 more `tender_configurations/__init__.py` wrappers that import removed `api` functions inside their bodies | Found by an inner-import scan after the first pass. |
| TM2 supplier portal: `tender_management/api/supplier_portal.py`, `services/supplier_portal_*.py` (7), `tests/test_p10_01_supplier_portal_routes.py` | Used only by the retired `/supplier/tenders` page. |
| UI specs `tests/ui/smoke/it-std-wizard/e1-bidder-workspace.spec.ts`, `tests/ui/smoke/supplier/supplier-portal.spec.ts`, `tests/ui/tm2_supplier_{submission,boq}.spec.ts`, `tests/ui/smoke/procurement/tender-management-v2-supplier-{detail-p10-03,routes-p10-01,boq-p10-06}.spec.ts` | They open retired routes. |
| Six bidder layout/web tests (`test_submission_checklist_web` and five `*_stitch_layout_guard`) plus the bidder method of `test_cfg_drawer_dismiss_guard` | They read retired files by path. |
| `e1-nssf-poc-gate` recipe: removed its `test_electronic_bid_submission` and `e1-bidder-workspace.spec.ts` lines; the rest of the gate is kept | Those two steps tested the retired slice. |
| Cleanup blocks naming `Electronic Bid Submission` in the kept seeds `ui00_seed`, `lean_synthetic_it_seed`, `lean_price_schedule`, `lean_requirements_compliance`, `e1_nssf_seed` | A dropped table turns such calls into crash sites. |
| `setup/workspace_permissions.py` "bid-submissions" mapping; the sidebar contract test's "Bid Submissions" expectations | Pointed at the retired page. |

Findings recorded for the OD-F TM2 clean-up (not caused by Phase 1):
- 262 imports in `tender_management` (and a few elsewhere) already point at modules removed by earlier cycles (`std_instance`, `derived_models`, `works_completion`, …). None was caused by this retirement: a scan of imports against the modules deleted today finds zero.
- `tender_management/tests/tm2_works_boq_supplier_fixture.py` is now referenced only by a docstring.

Observation: `/supplier/<name>` and any `/<doctype>/<name>` path returns 500 through Frappe's built-in print-view resolver. `/customer/X` and `/item/X` do the same. This is framework behaviour, previously hidden for `/supplier/tenders/…` by the retired route rule. The v0.8 portal does not use `/supplier`.
