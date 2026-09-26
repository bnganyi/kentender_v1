# STD-TPL-IMP-001 v1.0 — STD Templates runtime — tracker

**Authority:** `KenTender_STD-TPL-IMP-001_Installed_STD_Template_Runtime_v1_0.md` and `KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_10.md`. Both are Proposed and in Project Owner review (KT-DOC-CTRL-001, as_of 2026-09-25).
**Companions:** `STD-TPL-IMP-001_v1_0_Implementation_Plan.md`, which holds the owner decisions OD1–OD4, rulings R1–R12, phases and owner questions Q1–Q4. Design is in `design/STD Templates Artboards.dc.html`.
**Supersedes-in-tracking:** gates TPL-G07 and TPL-G08 in `STD-TPL-001_IMPLEMENTATION_TRACKER.md`. Release 1.0 history stays there.
**Status:** Phase 0 Done 25 September 2026. Owner authorised the build against the proposed text on 25 September 2026 (Q2); Phases A and B are in progress.
**Started:** 25 September 2026.

## Tracker rules

1. Rows are permanent. The only status values are `Planned`, `In progress`, `Blocked`, `Partial` and `Done`. When a decision is reversed, strike it through in place; never delete it.
2. A row is `Done` only with its own evidence: a command with its result counts, a named test, a diff, or a described browser observation quoting the literal rendered strings. Never record a result that was not observed.
3. No editable template-content DocType, upload, activation, repair or site-adoption approval may be introduced (STD-TPL-IMP-001 §2.2, §4.4; STD-TPL-001 §16).
4. Pack assets are generated, never hand-corrected (STD-TPL-001 §13.1). A controlled byte change after the manifest is built invalidates it (§13.9).
5. Owner gates (Gate D, Gate E, Q1–Q4) are closed only by the owner's recorded words, never by code.
6. Never run a Python test module while a Playwright process is active on the site. Purge after every Python run.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-25 | OD2 "Install as Candidate", OD3 "In this cycle" (Tenders cutover), OD4 "Retire and archive" | Owner answers to the planning questions |
| 2026-09-25 | OD1: the owner answered "Check /docs/mvp-1-r1/07_tender_templates". The check found no `06_runtime` and no review JSON, so the plan builds them from the 01–05 candidate. Confirmation is pending (Q1) | Plan §2, §3.1 |
| 2026-09-26 | **OD5 — owner decision, overrides the approval model.** Owner, asked how Requisitions should treat a Candidate release: "I don't want this complicated admin overhead regarding approvals and commissioning of templates. It is unnecessary, adds no value and is vexing. Allow development work to contine without this friction. Template release is purely an on and off switch on an affected site. Update this decision as a follow up to reflect in affected documents if necessary". Built as: an installed release is Available and switched **On** by default; a deployment command switches it Off or On; gate results and any owner decision are displayed evidence only and never block use; there is no Candidate state and no exact-manifest approval step. Integrity checks, the release validator and Superseded/Withdrawn remain. Supersedes OD2 and rulings R2 and R5 (approval parts). Document updates are follow-up FU-01. | Owner instruction |
| 2026-09-26 | R13 (new, owner to confirm): golden vectors are compiled against the *input* bundle digest (every asset except generated outputs), because a vector cannot contain the digest of the bundle that contains it; published Tenders use the installed full bundle digest. | Circular digest otherwise (plan §4). |
| 2026-09-26 | The installer reads the pack directly (`docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1`) instead of a second in-app byte copy (plan B2 said copy): the pack is ~36 MB and a copy would duplicate it in git; installed private Files are the runtime source. | Avoids a duplicated, drift-prone copy. |
| 2026-09-25 | Owner answers to Q1–Q4, quoted. Q1 "Confirm the missing runtime files should be built from the existing folder contents. - Confirmed". Q2 "Approve the two documents, or authorise building against them as proposed. - Authorised". Q3 "Accept or change the proposed defaults for the document conflicts. - Accepted" (R1–R12 defaults now binding). Q4 "Confirm you are the named release owner for install and withdraw actions. - Confirmed" (bnganyi) | The build is authorised against the proposed text. This is not document approval; the register's requirement_status is unchanged |

## Gate register

| Gate | Condition | Status | Evidence |
|---|---|---|---|
| STI-G00 | Phase 0: plan, tracker, predecessor pointer, rulings register | Done | 2026-09-25. STI-001..003 |
| STI-G01 | Pack Phase A1–A6 built; validator green except for owner-gated checks | Partial | 2026-09-26. 21/21 checks green; County variant Incomplete and 6 coverage rows await review — both owner/legal items, recorded as blockers. |
| STI-G02 | Schema, installer and private assets (B1–B2); installer test matrix green | Done | 2026-09-26. `std_templates.tests.test_installer` 19/19 (traversal, symlink, duplicate, undeclared, each digest, idempotency, identity clash, rollback, switch On/Off). OD5: installs Available, switched On. |
| STI-G03 | Shared compiler golden vectors and CLI/production parity (B3) | Done | 2026-09-26. `test_compiler` 25/25; MoH and variant vectors byte-identical; no-`frappe`-import test; validator C20 parity. |
| STI-G04 | Renderer adapter registry and health checks (B4) | Done | 2026-09-26. `BDS-GOODS-IT-V1` 1.0.0 document + bid_workspace adapters; production render reproduces the MoH HTML (`test_services`). |
| STI-G05 | Owner: Gate D, then Gate E `APPROVE EXACT MANIFEST` (replaces TPL-G07/G08) | Superseded by OD5 | 2026-09-26. No review or owner decision blocks use; gate results and any decision are recorded evidence. Reviews still Pending are shown in Verification. |
| STI-G06 | Projections, permissions, concerns and audit (B5); access matrix green | Done | 2026-09-26. `test_services` 18/18 (PO/HOPF read; AO/Auditor masked; SysMgr technical; concerns change nothing; tamper fails closed; switched-off and switched-on projections). |
| STI-G07 | STD Templates UI (B6): structure gate, Playwright, fidelity, 390 px, keyboard | Done | 2026-09-26. vitest `std-templates` 23/23 incl. 4-board structural fidelity; Playwright `tests/ui/smoke/std_templates/std-templates.spec.ts` 10/10 as real personas (list, filters, detail, panels, Back/Forward, switch Off → Unavailable with one blocker → On, concern round trip, keyboard, auditor denied, read failure, 390 px); release left On, 0 concerns. |
| STI-G08 | Tenders cutover and lifecycle (B7–B8): binding matrix green; Tenders and REQ suites green | Partial | 2026-09-26. `test_binding` 9/9; REQ `test_compatibility` 9/9; Tenders: schema 6/6, envelope 10/10, documents 8/8, serializer 10/11, authorization 5/6, gateway contracts 4/7 — every remaining failure pre-existing (FU-11). `test_lifecycle`, `test_read`, `test_publication`, `test_open_period` cannot run: their fixtures call REQ `add_requisition_item`, removed on 24 Sep (FU-11). The full Tender lifecycle is instead proven through the real commands by the canonical seed (`TDR-150688`, validate OK). Technical-read conformance 3/3. Follow-ups 26 Sep 2026: handoff v1.4 translation fixed a real reservation/warranty loss (FU-11); contract 6/6, snapshot 5/5, bound-release notice 7/7; canonical rebuild from a consumed state works (`TDR-150730`, documents show Youth and 36 months). Still not run: the four site-wiping Tenders modules (safety check). |
| STI-G09 | Retirement (B9): zero references outside `archive/`; migrate clean; `validate-links` | Done | 2026-09-26. Migrate clean; patch `std_tpl_imp_001_retire_std_configuration` dropped 28 DocTypes and tables, 6 Pages, 9 roles, the workspace and Module Def. Remaining mentions are retirement guards/history only. `validate-links` fails on the pre-existing `apps/frontend` symlink (FU-07). 26 Sep 2026: `make validate-links` passes after creating the missing `apps/frontend` link (FU-07). |
| STI-G10 | Release evidence (B10): AC map closed truthfully; persona pass | Planned | — |

## Work register — Phase 0

| ID | Item | Status | Evidence |
|---|---|---|---|
| STI-001 | Author the implementation plan (OD1–OD4, R1–R12, phases, Q1–Q4) | Done | 2026-09-25. `STD-TPL-IMP-001_v1_0_Implementation_Plan.md` |
| STI-002 | Author this tracker | Done | 2026-09-25 |
| STI-003 | Add a pointer banner to `STD-TPL-001_IMPLEMENTATION_TRACKER.md`; TPL-G07/G08 superseded here | Done | 2026-09-25. Banner added above the Authority line; no existing line changed |
| STI-004 | Confirm personas in `.env.ui`: Procurement Officer, HOPF, System Manager and one denied user | Planned | — |

## Work register — Phase A: release 1.1 pack

| ID | Item | Status | Evidence |
|---|---|---|---|
| STI-A01 | Review record §13.1 preconditions; fix the opaque `release_id` | Done | 2026-09-26. `release_id` `stdr-0e81b40c-d548-498c-855a-d4f80764af40` in every runtime asset; §13.1 preconditions added to `05_review/review_record.md` (new section, earlier text untouched). |
| STI-A02 | Registers to the exact §13.3 columns; `structured_rule_id` on Supplier-response rows; 6 "Draft checked" rows closed or recorded as blockers | Partial | 2026-09-26. Exact §13.3 columns in all three registers; `structured_rule_id` on every Supplier-response row and every rule traced to a coverage or forms row (validator C03/C11 green). §6.2 boundary corrections recorded as open item 68. The 6 `Draft checked` coverage rows and FORM-TCR/RSC/ARC still need the named reviewer (Coverage gate Pending). |
| STI-A03 | `product_profile.json` | Done | 2026-09-26. `06_runtime/product_profile.json`: 5 tasks, 12 controls, 14 compositions, 11 validations, named rules, 4 `EVG-*` groups, 6 destinations; loaded and validated by `std_templates/compiler/assets.py`. |
| STI-A04 | `response_rules.json` | Done | 2026-09-26. `response_rules.json`: 24 rules; 7 locked declarations extracted from the anchored master (open items 64–65). |
| STI-A05 | `downstream_rules.json` (one mapping per rule; four `EVG-*` groups) | Done | 2026-09-26. `downstream_rules.json`: 24 mappings, exactly one per rule, no orphan (C08); no response maps to `EVG-AWARD`. |
| STI-A06 | `addendum_identity_rules.json` | Done | 2026-09-26. `addendum_identity_rules.json`: five classifications, 13 family rules, requiredness conversions; C14 proves label-only / material / removed / new. |
| STI-A07 | `build_definition_fixture.py` (thin adapter over B3); MoH expected definition | Done | 2026-09-26. `04_fixture/build_definition_fixture.py` delegates to `compile_published_bid_definition` (C20); `06_runtime/moh_published_bid_definition_expected.json` — 123 responses, reproduces byte for byte (C15). |
| STI-A08 | Five reservation variant fixture pairs | Partial | 2026-09-26. Five variant pairs; None/Women/PwD Publishable, unsupported overlap Blocking on `overlap_treatment`; County-residents **Incomplete** — no released wording/rule (open item 70; LAW-REG-001 LAW12-AC-005). |
| STI-A09 | MoH HTML/PDF re-rendered through the registered document adapter | Done | 2026-09-26. MoH HTML/PDF via the registered `BDS-GOODS-IT-V1` 1.0.0 document adapter (wkhtmltopdf 0.12.6.1 patched qt); issued Tender 38 pages with reference footer (C16). |
| STI-A10 | `validate_release.py` (21 checks), `validation_report.json`, `release_gates.json` (17 gates) | Done | 2026-09-26. `06_runtime/validate_release.py`: 21/21 checks Passed, exit 0, deterministic rerun; `release_gates.json` 17 gates — 6 Passed, 11 Pending, 0 Failed. |
| STI-A11 | `release_change_report.json` against release 1.0 | Done | 2026-09-26. Generated against `05_review/preceding_release.json` (release 1.0 from commit `74793a0d`): *Breaking — new release approval required*. |
| STI-A12 | `release_manifest.json`; bundle and manifest digests in the review record | Done | 2026-09-26. `06_runtime/release_manifest.json` (Candidate) via `docs/mvp-1-r1/07_tender_templates/tools/rebuild_release.py`; bundle digest per §13.9 with the manifest, review record and owner decision outside the inventory. |

## Work register — Phase B: runtime

| ID | Item | Status | Evidence |
|---|---|---|---|
| STI-B01 | Module `STD Templates` and three DocTypes; immutability; purge cleanup | Done | 2026-09-26. `Installed STD Release` (+ asset child), `STD Template Concern`; flag-guarded controllers; `support.purge`. |
| STI-B02 | Installer: fail-closed, Candidate/Available decision (R2), private Files, idempotent; `make std-release-install`; remove the `after_migrate` auto-install | Done | 2026-09-26. As changed by OD5: Available + switch On (or `SWITCH=Off`); `make std-release-switch`; auto-install removed from `hooks.py`. Dev site: release 1.1 installed, 142 assets, On. |
| STI-B03 | Shared pure compiler and canonical JSON; golden vectors; parity; no-`frappe`-import test | Done | 2026-09-26. See STI-G03. |
| STI-B04 | Renderer adapter registry: document and bid_workspace kinds (R8); health check | Done | 2026-09-26. See STI-G04. |
| STI-B05 | Read services and projections; coverage paging and filters; change report; preview and review pack | Done | 2026-09-26. `services/read.py`, `documents.py`; blockers derived live from switch, integrity and renderer (OD5). |
| STI-B06 | Concerns: create and list; resolve by command (R5); no lifecycle effect | Done | 2026-09-26. `services/concerns.py`; tested in `test_services`. |
| STI-B07 | Permissions (AUTH v1.10 §8.1, R4); audit; §12 error codes; whitelisted API | Done | 2026-09-26. `services/access.py`, `api.py`; technical-read resolvers and probes registered (replacing STD Configuration's). |
| STI-B08 | Page `std-templates`, controller, bundle, rail, sidebar row, workspace maps | Done | 2026-09-26. One `desk_page.register` call; sidebar row for the four roles. |
| STI-B09 | List screen (01, 01F, 01E, 01R) and 390 px cards | Done | 2026-09-26. Browser-verified before OD5; spec updated, rerun owed (STI-G07). |
| STI-B10 | Detail screen (02, 02A, 02F, 02S, 02W, 02R), coverage and change panels, technical details | Done | 2026-09-26. OD5: 02A's "Exact manifest approval" replaced by a live "Site switch" verification row; owner decision moved to Technical details (FU-01). |
| STI-B11 | Report concern dialog (02C) | Done | 2026-09-26. |
| STI-B12 | Tenders binding cutover; new Tender and Tender Version fields; compatibility services; View STD Template link | Done | 2026-09-26. `tenders/services/template_binding.py` over STD Templates binding (new Tender: switched-on Available; later actions: the bound release, never rebinds; `TND_TEMPLATE_RELEASE_WITHDRAWN` / `_INTEGRITY_FAILED`); renders through the bound release's masters; 5 new fields on Tender and Tender Version; REQ `template_support()` switched over; Start-screen **View STD Template**. Proven end to end by the canonical seed (STI-B13). Link on later action errors: FU-10. |
| STI-B13 | `TDR-138016` legacy patch (R9); canonical `tenders` stage behaviour while Candidate | Done | 2026-09-26. No legacy patch needed: the dev site was rebuilt (owner: "You may reseed data as you see fit since this is a dev site") with `make seed-canonical THROUGH=tenders REBUILD=True` — validate OK. New canonical Tender `TDR-150128` ran its full lifecycle (start, return, approve, authorise, publish, addendum, close) bound to release `stdr-0e81b40c…` 1.1 / `BDS-GOODS-IT-V1` 1.0.0, documents rendered from the release's masters; Requisition `PRQ-150116` passed the compatibility check against the switched-on release. OD5 removed the Candidate stop. |
| STI-B14 | Supersede and withdraw commands; affected-Tender projection | Done | 2026-09-26. `services/lifecycle.py` supersede/withdraw/switch; `test_binding` 9/9. |
| STI-B15 | Retire `std_configuration/`, `Supported Tender Template`, old `tender_templates/`, 9 roles and the stale workspace; archive | Done | 2026-09-26. Archived to `archive/std-configuration-retired-2026-09/`; drop patch applied on the dev site (STI-G09). |
| STI-B16 | Close CFG FU-18; record required corrections (R10, R11) | Done | 2026-09-26. CFG FU-18 closed as superseded by CFG v0.15 CFG15-CHG-001 / STD Templates. OD5 document revisions done (FU-01): STD-TPL-001 v0.11, STD-TPL-IMP-001 v1.1, TPR v0.12, REQ v1.13, BDS v0.8, G1-REG v1.2; register updated (DEC-024). |
| STI-B17 | Release evidence and runbook | Planned | — |

## Acceptance map

Every row is Planned until its evidence exists.

| AC | Row(s) |
|---|---|
| STI10-AC-001, 002 | STI-B02 |
| STI10-AC-003 | STI-B01, B02 |
| STI10-AC-004 | STI-B01, B15 |
| STI10-AC-005 | STI-B05, B09, B10 |
| STI10-AC-006 | STI-B07 |
| STI10-AC-007 | STI-B06 |
| STI10-AC-008 | STI-B03, A07 |
| STI10-AC-009 | STI-B03, B04 |
| STI10-AC-010, 011, 012, 013 | STI-B12, B13, B14 |
| STI10-AC-014 | STI-B02 |
| STI10-AC-015 | STI-B04 |
| STI10-AC-016 | STI-B09, B10, B11 |
| TPL10-AC-001 | STI-A11, B10 |
| TPL10-AC-002 | STI-B06, B11 |
| TPL10-AC-003 | STI-A10, B02 |
| TPL10-AC-004 | STI-B03 |
| TPL10-AC-005 | STI-B04 |
| TPL10-AC-006, 007, 008 | STI-B12, B14 |
| TPL10-AC-009 | STI-B02 |
| TPL10-AC-010 | STI-G10 |
| TPL08-AC-003..013 | STI-A01..A12 |
| TPL08-AC-016, 021, 023 | STI-B03 (TPR v0.11 owns publication wiring) |
| TPL08-AC-017, 018 | STI-A03, A05 |
| TPL08-AC-019, 020, 022 | STI-B05, B09, B10 |
| TPL07-AC-013 | STI-B02 |
| TPL07-AC-014, 015 | STI-B07, B09, B10, B12 |
