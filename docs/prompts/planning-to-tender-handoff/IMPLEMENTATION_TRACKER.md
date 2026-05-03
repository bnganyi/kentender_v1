# Planning → Tender handoff — implementation tracker

**Purpose:** Single place to record status, evidence (tests, migrations, Playwright), acceptance criteria, blockers, and pointers to issues for the **STD-Driven Tender Creation Integration** workstream (planning-to-tender handoff + integrated WORKS seed + tender-stage hardening).

**Workstream docs (source of truth):**

| # | Document |
|---|----------|
| 1 | [`1. std_driven_tender_creation_integration_scope_document.md`](1.%20std_driven_tender_creation_integration_scope_document.md) |
| 2 | [`2. planning_to_tender_handoff_specification.md`](2.%20planning_to_tender_handoff_specification.md) |
| 3 | [`3. works_seed_scenario_refactor_specification.md`](3.%20works_seed_scenario_refactor_specification.md) |
| 4 | [`4. works_tender_stage_hardening_specification.md`](4.%20works_tender_stage_hardening_specification.md) |
| 5 | [`5. works_tender_stage_hardening_cursor_implementation_pack.md`](5.%20works_tender_stage_hardening_cursor_implementation_pack.md) |

**Related audit snapshot:** [`docs/audit/planning_tender_handoff_2026-05-03/AUDIT_SNAPSHOT.md`](../../audit/planning_tender_handoff_2026-05-03/AUDIT_SNAPSHOT.md)

**Upstream POC trackers (completed context):** [`../std poc/IMPLEMENTATION_TRACKER.md`](../std%20poc/IMPLEMENTATION_TRACKER.md) · [`../std poc/tender configuration/IMPLEMENTATION_TRACKER.md`](../std%20poc/tender%20configuration/IMPLEMENTATION_TRACKER.md)

**Issues log (canonical for this workstream):** [`ISSUES_LOG.md`](ISSUES_LOG.md) — prefix **`STD-INT-*`** / **`STD-INT-SEED-*`**. Cross-post to [`../std poc/ISSUES_LOG.md`](../std%20poc/ISSUES_LOG.md) only when an item is shared with STD-WORKS-POC governance (`STD-POC-*` / `STD-ADMIN-*`).

---

## Rules of engagement

1. **Spec is law** — Each row maps to acceptance criteria / exit language in docs 1–5. Do not mark **Done** without evidence that those criteria are met (or an explicit **deviation** logged with approval). **§A design sign-off:** Evidence may be a dated AC checklist in **Notes** plus [`ISSUES_LOG.md`](ISSUES_LOG.md) for deferrals (`STD-INT-*`); no `bench`/Playwright required for A1–A5 alone.
2. **TDD; Playwright for Desk** — Follow workspace rules ([`.cursor/rules/kentender-tdd-playwright-quality-gate.mdc`](../../../../../.cursor/rules/kentender-tdd-playwright-quality-gate.mdc), [`.cursor/rules/frappe-desk-playwright-patterns.mdc`](../../../../../.cursor/rules/frappe-desk-playwright-patterns.mdc)). Desk/UI changes need Playwright evidence or a logged environment blocker.
3. **Bench / Node** — Use [`./scripts/bench-with-node.sh`](../../../../../scripts/bench-with-node.sh) from bench root for any `bench build` / asset work touching `public/js` or `public/css`.
4. **Non-scope (all docs)** — Do not implement or claim done: public publication, final certified PDF, bidder portal, bid submission, bid opening execution, evaluation execution, award, contract execution, production bidder BoQ pricing, full addenda lifecycle, external integrations, manual submission/opening/evaluation/contract rule builders, or document-upload-as-source for tender truth.

**Status values:** `Not started` | `In progress` | `Partial` | `Blocked` | `Done`

**Evidence column:** Commands (`bench run-tests`, `bench migrate`), test module paths, Playwright spec paths, PR links, or artefact paths.

**Notes column:** AC ids (e.g. `PT-HANDOFF-AC-003`), spec § references, `STD-INT-*` issue ids, assumptions.

---

## Workstream health

| Field | Value |
|-------|--------|
| Primary scenario | `STDINT-WORKS-S01` — District Hospital Renovation Works |
| Primary package / tender (target codes) | `PKG-MOH-2026-001` / `TND-MOH-2026-001` |
| Primary STD template | `KE-PPRA-WORKS-BLDG-2022-04-POC` |
| Canonical handoff object | `Procurement Package` |
| Last tracker update | 2026-05-03 — **B10** release integration tests (doc 2 sec. 21) |

---

## A. Design artefacts — acceptance / sign-off

Use this section to record **product / architecture sign-off** on the written specs before or while implementation proceeds.

| Artefact | Document | Sign-off status | Evidence | Notes |
|----------|----------|-----------------|----------|-------|
| A1 Integration scope | Doc 1 | Done | Design sign-off 2026-05-03; [`ISSUES_LOG.md`](ISSUES_LOG.md) `STD-INT-SIGNOFF-001` | **§9 Non-scope:** Pass — 15 exclusions consistent with docs 2–5. **INT-SCOPE-AC-001–010:** Pass — (001) `Procurement Package` canonical §6; (002) persistent plan/package links specified doc §12.1 + doc 2 §11; (003) roles separated doc §16; (004) mapping doc §14 + doc 2 §13–14; (005) hook + service doc §5.3 + doc 2 §16; (006) seed chain doc §17 + doc 3; (007) BoQ hardening doc §18 + doc 4; (008) refactor allowed doc §11; (009) exclusions doc §9; (010) downstream deferred doc §8.10 + doc 2 §5. |
| A2 Handoff specification | Doc 2 | Done | Same | **PT-HANDOFF-AC-001–012:** Pass — canonical source §6–8; links §11; gated release §9–10; boundary `XMV-BND-001` §17; STD order §12.1–12.2; Works STD §12.2; no silent demo §14–15; duplicate guard §16.3; status ordering §10; audit §18; BoQ boundary §20; non-scope §5. **§25 exit:** Pass as specification. **Naming:** Implement `procurement_plan`, `procurement_package`, `procurement_template` (doc 2 §11.2); optional counts/hash per doc 1 §12.1 — repo may adjust spelling if DocType naming differs, relationships unchanged. |
| A3 WORKS seed specification | Doc 3 | Done | Same | **WORKS-SEED-AC-001–014:** Pass — chain §7, scenario `STDINT-WORKS-S01` §6, codes §8, service-preferred release §18.1 vs transitional §18.2 flagged, verification §28–29, non-scope §5. **§33 exit:** Pass — deterministic integrated fixture through preview; boundary before publication/downstream. **Governance:** If `release_procurement_package_to_tender` lags, transitional seed allowed per §18.2 with explicit note (track in §C4). |
| A4 Tender-stage hardening design | Doc 4 | Done | Same | **WORKS-HARDEN-AC-001–015:** Pass — structured Works requirements, section-bound attachments, BoQ bill/item direction, lot linkage, forms↔submission, derived-model readiness placeholders, no false publication readiness, validation/audit/legacy lockout, seed expectations, non-scope §5. **§25 exit:** Pass as design. **Reconciliation with doc 2 §20:** BoQ remains tender-stage only; bidder pricing/downstream arithmetic explicitly deferred in both docs. |
| A5 Cursor implementation pack | Doc 5 | Done | Same | **WH-AC-001–016:** Pass as **executable plan** (not implementation): DocTypes/fields §6–14, services §16, validation codes §18, snapshot §23, UI §24, seed §25, tests §26, tickets WH-001–015 §27, non-negotiables §3. **§30 exit:** Pass — sequence and scope bounded; JSON fallback on tender permitted per §6.3/§7 if child tables deferred. **Contradiction check:** Doc 5 implements doc 4; no open conflict requiring doc revision. |

---

## B. Planning → tender handoff foundation (doc 2 + doc 1 §12–16)

Implement per **doc 2** (`release_procurement_package_to_tender`, links, validation boundary `XMV-BND-001`, STD resolution, audit, duplicate guard). Align field names with repo conventions where doc uses placeholders.

| Track | Deliverable | Status | Evidence | Notes |
|-------|-------------|--------|----------|-------|
| B1 | `Procurement Tender`: persistent links to `Procurement Plan`, `Procurement Package`; optional `procurement_template`, snapshot/hash fields as spec | Done | `bench --site kentender.midas.com migrate` (2026-05-03) · `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_planning_tender_linkage_b1` (4/4 OK) · regression `test_std_works_poc_step9_doctypes` (9/9 OK) · [`procurement_tender.json`](../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_tender/procurement_tender.json) · [`procurement_tender.py`](../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_tender/procurement_tender.py) · [`test_planning_tender_linkage_b1.py`](../../../kentender_procurement/kentender_procurement/tender_management/tests/test_planning_tender_linkage_b1.py) | Doc 2 §11.2: Links + `source_package_code` / `source_package_hash` / `source_package_snapshot_json`; doc 1 §12.1: `source_demand_count`, `source_budget_line_count`. `ProcurementTender.validate`: auto-fill `procurement_plan` from package `plan_id`; throw on plan/package mismatch. |
| B2 | `Procurement Template.default_std_template` Link (or documented mapping alternative) | Done | `bench --site kentender.midas.com migrate` (2026-05-03) · `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_planning.tests.test_procurement_template_default_std_b2` (4/4 OK) · regression `test_procurement_planning_smoke_g1` (14 ran, OK) · [`procurement_template.json`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_template/procurement_template.json) · [`procurement_template.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/doctype/procurement_template/procurement_template.py) · [`test_procurement_template_default_std_b2.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/tests/test_procurement_template_default_std_b2.py) | Doc 1 §16; doc 2 §12.1 resolution step 1. Optional Link + section **STD template mapping**; `ProcurementTemplate._validate_default_std_template` rejects non-existent STD. **B6/B3** consume field when wired. |
| B3 | `release_procurement_package_to_tender` service + register `release_procurement_package_to_tender` hook | Done | See B4 row for current test evidence (same module). · [`release_procurement_package_to_tender.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/release_procurement_package_to_tender.py) · [`hooks.py`](../../../kentender_procurement/kentender_procurement/hooks.py) · [`test_release_procurement_package_to_tender_b3.py`](../../../kentender_procurement/kentender_procurement/tender_management/tests/test_release_procurement_package_to_tender_b3.py) | Doc 2 §16.1 service + hook wired to [`deliver_procurement_package_release`](../../../kentender_procurement/kentender_procurement/procurement_planning/services/tendering_handoff.py). **B4** extended service + workflow (see B4). |
| B4 | Preconditions + state transition (`Ready for Tender` → `Released to Tender`); tender initial `Draft` / `Configured` | Done | `bench --site kentender.midas.com migrate` (2026-05-03) · `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3` (7/7 OK) · regressions `test_planning_tender_linkage_b1` (4/4), `test_std_works_poc_step9_doctypes` (9/9) · [`release_procurement_package_to_tender.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/release_procurement_package_to_tender.py) · [`workflow.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py) (`release_package_to_tender`) | Doc 2 §9: new-create path requires **Approved** plan + package **currency** (now enforced via **B5** XMV + completeness overlap). §10: [`release_package_to_tender`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py) calls `package_has_release_tender` after hooks — **PT-HANDOFF-AC-009** fail-closed (package stays Ready if no linked tender). §10.2: new tender `tender_status` **Configured** + handoff `configuration_json` (**B7**). Hook remains fail-open; workflow blocks bad release. **§16.3 duplicate guard:** **B9** (`Procurement Tender` validate). |
| B5 | Cross-module validation checks `XMV-PT-001` … `011` (or subset + deferrals logged) | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_planning_tender_handoff_xmv_b5` (6/6 OK) · `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3` (7/7) · `test_planning_tender_linkage_b1` (4/4) · `test_std_works_poc_step10_loader` (16/16) · [`planning_tender_handoff_xmv.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/planning_tender_handoff_xmv.py) · [`release_procurement_package_to_tender.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/release_procurement_package_to_tender.py) · [`workflow.py`](../../../kentender_procurement/kentender_procurement/procurement_planning/api/workflow.py) | Doc 2 §17 / `XMV-BND-001`: [`validate_package_for_release_xmv`](../../../kentender_procurement/kentender_procurement/tender_management/services/planning_tender_handoff_xmv.py) returns coded **critical** / **warning** findings; **007** delegates to `get_package_completeness_blockers` when `template_id` set. **005:** `estimated_value` ≤0 → **warning** only (POC). **010:** Works + competitive method → **warning** (full BoQ deferred B7/WH per doc §19). **011:** JSON snapshot build — failure **critical**; persisted snapshot/hash on tender + audit **Comment** in **B8**. **009:** >1 non-cancelled tender → **critical** (legacy corruption / import; **B9** prevents new duplicates at validate). **Seed alignment:** POC `manifest.json` now `IMPORTED` + `allowed_for_tender_creation: true` so **008** matches release path (`test_std_works_poc_step10_loader`, STEP3-AC-009 assertions updated). |
| B6 | STD template resolution order + fail-closed ambiguity | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_std_template_handoff_resolution_b6` (6/6 OK) · regressions `test_release_procurement_package_to_tender_b3` (7/7), `test_planning_tender_handoff_xmv_b5` (6/6), `test_planning_tender_linkage_b1` (4/4) · [`std_template_handoff_resolution.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_handoff_resolution.py) · [`planning_tender_handoff_xmv.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/planning_tender_handoff_xmv.py) (`XMV-PT-008`) · [`release_procurement_package_to_tender.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/release_procurement_package_to_tender.py) | Doc 2 **§12.1** order: (1) `Procurement Template.default_std_template` when valid row; (2) mapping pass = eligible STDs (`allowed_for_tender_creation`, status **Imported**/**POC Approved**) filtered by planning template **category** vs `STD Template.procurement_category` — **>1 match → ambiguous, no guess** (§12.1 / §21); (3) **§12.2** Works POC fallback only when mapping empty: Works + **Open Tender** + package contract type set. **PT-HANDOFF-AC-005** deterministic fail-closed. B3 fixtures set `default_std_template` to POC code for Goods packages without Works POC. |
| B7 | Pre-populate `configuration_json` / officer fields from package; no silent demo merge on release | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_planning_tender_handoff_configuration_b7` (5/5 OK) · regressions `test_release_procurement_package_to_tender_b3` (7/7), `test_planning_tender_handoff_xmv_b5` (6/6), `test_std_template_handoff_resolution_b6` (6/6) · [`planning_tender_handoff_configuration.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/planning_tender_handoff_configuration.py) · [`release_procurement_package_to_tender.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/release_procurement_package_to_tender.py) | Doc 2 **§14–15**: safe defaults from bundled ``fields.json`` only (no ``sample_tender.json``); inherited package/plan onto guided columns + flat overlay; ``merge_officer_overlay_into_configuration``; ``validation_status`` **Not Validated**, empty preview HTML; ``procurement_category`` from planning template. **Deferrals:** §14.3–14.4 lots/BoQ/works summaries not populated (WH/B10); child-table stale flags unchanged. |
| B8 | Handoff audit event + optional `source_package_snapshot_json` | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_planning_tender_handoff_audit_b8` (2/2 OK) · regressions `test_release_procurement_package_to_tender_b3` (7/7), `test_planning_tender_handoff_configuration_b7` (5/5), `test_planning_tender_handoff_xmv_b5` (6/6), `test_std_template_handoff_resolution_b6` (6/6) · [`planning_tender_handoff_audit.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/planning_tender_handoff_audit.py) · [`release_procurement_package_to_tender.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/release_procurement_package_to_tender.py) | Doc 2 **§18**: snapshot schema `kentender.planning_to_tender.handoff_snapshot/v1` on `source_package_snapshot_json`; SHA-256 `source_package_hash`; `configuration_hash` from merged `configuration_json`; demand/budget **distinct** counts from active package lines; **Comment** JSON payload (actor, roles, package/plan/status before+after read, STD, XMV warnings, hashes). **§21 fail-closed:** if `add_comment` fails, tender is **deleted** and `frappe.throw` (**ValidationError**). Package **status after** in the comment is DB value immediately after tender insert (workflow may set **Released to Tender** afterward). |
| B9 | Duplicate active tender guard | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_planning_tender_handoff_duplicate_b9` (2/2 OK) · regressions `test_planning_tender_linkage_b1` (4/4), `test_release_procurement_package_to_tender_b3` (7/7), `test_planning_tender_handoff_configuration_b7` (5/5), `test_planning_tender_handoff_audit_b8` (2/2), `test_planning_tender_handoff_xmv_b5` (6/6) · [`planning_tender_handoff_duplicates.py`](../../../kentender_procurement/kentender_procurement/tender_management/services/planning_tender_handoff_duplicates.py) · [`procurement_tender.py`](../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/procurement_tender/procurement_tender.py) | Doc 2 **§16.3**: `ProcurementTender.validate` — at most one **non-cancelled** tender per `procurement_package`; clear error pointing at peer tender. After cancelling the prior tender, a new handoff/release may create a replacement. **`XMV-PT-009`** test uses `ignore_validate` on the second insert to simulate pre-B9 DB state. |
| B10 | Integration tests for release path (happy + negative cases from doc 2 §21) | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_planning_tender_handoff_release_integration_b10` (12/12 OK) · regression `test_release_procurement_package_to_tender_b3` (7/7 OK) · [`test_planning_tender_handoff_release_integration_b10.py`](../../../kentender_procurement/kentender_procurement/tender_management/tests/test_planning_tender_handoff_release_integration_b10.py) | Doc 2 **§21** matrix: not found / blank id; **read** + **create** permission denials; non-releasable status; **STD** unresolved + ambiguous (patched resolution); existing tender idempotent; **audit** fail-closed (no active tender, ``ValidationError``); **configuration** prep failure (no persist); **XMV** raises → propagate, no tender. Happy path asserts structured keys + **PT-HANDOFF-AC-002** lineage + snapshot hash present. |

---

## C. WORKS integrated seed (doc 3)

| Track | Deliverable | Status | Evidence | Notes |
|-------|-------------|--------|----------|-------|
| C1 | Deterministic seed chain through package lines (codes per doc 3 §8) | Not started | | Idempotent loader |
| C2 | STD template present via **existing** loader import | Not started | | Doc 3 §16 |
| C3 | Package `Ready for Tender`; release via **service** (preferred) | Not started | | Doc 3 §18.1 |
| C4 | Transitional direct-tender path only if B3 not ready — **flagged** in seed/README | Not started | | Doc 3 §18.2 |
| C5 | Officer completion step clearly labelled (sample only) | Not started | | Doc 3 §20 |
| C6 | Verification script / tests per doc 3 §28–29 (smoke path) | Not started | | Forms count, BoQ, preview, hashes |
| C7 | Issue log updates `STD-INT-SEED-001` … `005` as applicable | Not started | | Doc 3 §30 |

---

## D. WORKS tender-stage hardening — tickets WH-001 … WH-015 (doc 5)

Execute in order unless dependencies clearly allow parallel prep (e.g. DocType JSON before services).

| Ticket | Title (summary) | Status | Evidence | Notes |
|--------|-----------------|--------|----------|-------|
| WH-001 | Hardening fields on `Procurement Tender` | Not started | | Doc 5 §7 |
| WH-002 | Child DocType `Tender Works Requirement` | Not started | | Doc 5 §8 |
| WH-003 | Child DocType `Tender Section Attachment` | Not started | | Doc 5 §9 |
| WH-004 | Child DocType `Tender Derived Model Readiness` | Not started | | Doc 5 §10 |
| WH-005 | Child DocType `Tender Hardening Finding` | Not started | | Doc 5 §11 |
| WH-006 | Extend `Tender Lot` (package line traceability) | Not started | | Doc 5 §12 |
| WH-007 | Extend `Tender BoQ Item` (bill/item, formula, locks) | Not started | | Doc 5 §13 |
| WH-008 | Extend `Tender Required Form` (submission placeholder) | Not started | | Doc 5 §14 |
| WH-009 | Services: `works_tender_hardening*.py` + orchestration | Not started | | Doc 5 §16 |
| WH-010 | Validation service + all finding codes §18 | Not started | | Doc 5 §18 |
| WH-011 | Snapshot JSON + SHA-256 hash | Not started | | Doc 5 §23 |
| WH-012 | Desk: Works Hardening button group + dialogs | Not started | | Doc 5 §24; Playwright |
| WH-013 | Integrated Works seed runs hardening sequence | Not started | | Doc 5 §25 |
| WH-014 | `test_works_tender_hardening.py` (required cases §26) | Not started | | |
| WH-015 | Exit review: assumptions, remaining findings, blockers | Not started | | Doc 5 §27 ticket WH-015 |

**Expected primary outcome (doc 5 §25):** hardening status may be **Warning** (derived model placeholders); **no Critical** findings for primary seed; publication must not be claimed.

---

## E. Cross-cutting verification (run before marking workstream milestone)

| Check | Status | Evidence | Notes |
|-------|--------|----------|-------|
| E1 Tender links package + plan after release | Not started | | PT-HANDOFF-AC-002 |
| E2 STD resolution deterministic for Works POC path | Not started | | PT-HANDOFF-AC-005 |
| E3 No plain `bench build` in CI/docs instructions for this work | Not started | | Repo rule |
| E4 Regression: existing STD POC tests still green | Not started | | `kentender_procurement` tender_management tests |
| E5 Playwright slice for new Desk buttons (if WH-012) | Not started | | Or logged blocker |

---

## F. Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-05-03 | — | Tracker created. All implementation rows initialised to **Not started**. |
| 2026-05-03 | — | **§A Design artefacts:** A1–A5 signed off at specification level; [`ISSUES_LOG.md`](ISSUES_LOG.md) added (`STD-INT-SIGNOFF-001`); rules clarified for §A evidence. |
| 2026-05-03 | — | **§B1:** Planning lineage fields on `Procurement Tender` + validate + tests (`test_planning_tender_linkage_b1`). |
| 2026-05-03 | — | **§B2:** `Procurement Template.default_std_template` Link + validate + tests (`test_procurement_template_default_std_b2`). |
| 2026-05-03 | — | **§B3:** `release_procurement_package_to_tender` service + `hook_release_procurement_package_to_tender` in `hooks.py` + tests (`test_release_procurement_package_to_tender_b3`). |
| 2026-05-03 | — | **§B4:** Release preconditions on service; `release_package_to_tender` handoff guard; initial tender **Configured** + merged `configuration_json`. |
| 2026-05-03 | — | **§B5:** `planning_tender_handoff_xmv` (`XMV-PT-001`–`011`) + wire to release service + `release_package_to_tender`; B3/B5 tests; STD POC `manifest.json` status flags aligned with **008**; STEP3/STEP10 test expectations updated. |
| 2026-05-03 | — | **§B6:** `std_template_handoff_resolution` (doc 2 sec. 12.1–12.2) + `XMV-PT-008` ambiguity/invalid-default messages + release `std_resolution_path`; B3 template `default_std_template` for Goods handoff; `test_std_template_handoff_resolution_b6`. |
| 2026-05-03 | — | **§B7:** `planning_tender_handoff_configuration` — handoff ``configuration_json`` (safe ``fields.json`` defaults + inherited overlay + officer merge); no ``sample_tender`` loaders on release path; `test_planning_tender_handoff_configuration_b7`. |
| 2026-05-03 | — | **§B8:** `planning_tender_handoff_audit` — persisted snapshot + hashes/counts on new tender; structured audit **Comment**; fail-closed delete+tender throw on audit write failure; `test_planning_tender_handoff_audit_b8`; B3/B7/B5/B6 regressions re-run. |
| 2026-05-03 | — | **§B9:** `planning_tender_handoff_duplicates` + `ProcurementTender` validate — one active tender per package; `test_planning_tender_handoff_duplicate_b9`; B5 PT-009 test inserts second tender with `ignore_validate`; B1/B3/B7/B8/B5 regressions re-run. |
| 2026-05-03 | — | **§B10:** `test_planning_tender_handoff_release_integration_b10` — 12 integration cases for doc 2 **§21** + happy path / AC-002; B3 regression re-run. |

---

## How to use

1. Move a row from **Not started** → **In progress** when work begins.
2. Set **Done** only with **Evidence** (commands + paths) and brief **Notes** tying to AC ids or spec sections.
3. Use **Partial** when some ACs remain; **Blocked** when waiting on dependency or decision — log `STD-INT-*` (or chosen prefix).
4. After each merge or milestone, append a row to **§F Changelog** and update **Workstream health → Last tracker update**.
