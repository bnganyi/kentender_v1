# REQ-CHG-001 v1.6 — Procurement Requisitions implementation plan

| Control | Value |
|---|---|
| Authority | `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_6.md` (approved 4 September 2026; supersedes v1.5, v1.4, v1.3 (withdrawn), v1.2 and all earlier versions in full) |
| Sibling authorities consumed | KT-STD-001 v1.3, STD-STD-001 v1.1, AUTH-ADR-001 v1.6, CFG-CHG-002 v0.9, PLN-CHG-001 v1.14 (§4.14 projection), BUD-CHG-001 v1.6 (§8.2A, §9.1), TPR-CHG-001 v0.5 (§6.4, §7.3 consumer shape), STD-TPL-001 v0.4 (§6.1 reservation categories), SEED-001 v1.0 |
| Companions | `02_REQ_Gap_Analysis.md` (current-state facts), `IMPLEMENTATION_TRACKER.md` (evidence ledger), `FOLLOW_UPS.md` (deferred items) |
| Predecessor cycle | None — greenfield; v1.2 (approved 28 August 2026) was never built |
| Prepared | 6 September 2026 |
| Status | Approved by the Project Owner 6 September 2026 (decisions D1–D4 answered explicitly; "continue methodically until completion") |

## 1. Governing approach

**Greenfield build that mirrors Procurement Planning one-for-one.** Nothing exists to correct or demolish; the risk is invention. Every structural choice below is a copy of the Planning v1.12 build (`procurement_planning/`): the module layout, the `envelope` idempotency journal, the closed error set, the explicit-signature `api.py` with its AST guard, the verdict-first workspace read, the one-`register()` page controller, the shared route/rail adapters, the per-slice Make gate, the one-world Playwright fixture module with one reset function per spec file, and the design-fidelity spec against the artboard file.

**Done means all four roles finish the journey in a browser.** Departmental Author, Head of User Department, Head of Procurement Function and Auditor each complete their REQ-CHG-001 work on the Ministry of Health fixture as real actors (Playwright, single worker), with two Budget reservations, two Planning drawdown references and an immutable v1.3 handoff visible afterwards.

Non-negotiables inherited from AGENTS.md: business rules in services, never in Vue; every command re-checks responsibility, scope, state and record version on the server; no `frappe.db.commit()` in request services; artboards ported class-for-class; no Civic Ledger / Stitch surface; no `frappe.msgprint` for user-correctable errors; Python suite and Playwright never run concurrently on the site; TDD per behaviour.

## 2. Decision register

| # | Decision | Why |
|---|---|---|
| D1 | **Budget changes in this cycle** (`kentender_budget/services/budget_check_reserve_contracts.py`, `funding_reservation.json` + index-dropping patch): caller gate admits Finance Confirmation Officer **or** Head of Procurement Function; new `calling_module` and `caller_reference` parameters; `finance_task` optional; `plan_source_allocation` no longer unique — conflict = an Active/Partially Converted reservation for the same allocation with the same `caller_reference`; same-correlation replay stays `reused`. Pinned by Budget tests. | REQ §9.1A and BUD §8.2A name Requisitions as the caller; the unique index makes §7.4 revoke-then-correct and a later Requisition on the same allocation impossible; the locked position check still stops oversubscription. Owner answered "change Budget in this cycle". |
| D2 | **`Delivery Location` master in `kentender_core`** (`location_name`, `address`, `status` Active/Retired, `fixture_namespace`), seeded by `site_setup` with "Ministry of Health Headquarters, Afya House, Nairobi". | No Location master exists; Needs forbids the field; Tender, Contract and Inspection will link the same row. Owner choice. |
| D3 | **Planning receives `Plan Item Correction Request`**: doctype `PCR-{#####}` (plan_item, requisition_reference, requisition_version, reason, requested_by, status Open/Resolved, resolution_note), inbound `receive_plan_item_correction_request` (idempotent), `resolve_plan_item_correction_request` (Planner; records resolution only) and a Procurement Planner My Work row. No Planning screen. | REQ §7.4A step 3 needs a receiver; §22 keeps the wider PLN correction open. Owner choice. |
| D4 | **Tender seam = published handoff only**: `get_authorised_requisition_handoff`, outbox event `ProcurementRequisitionAuthorised.v1.3`, inbound `record_handoff_consumption`, contract test pinning the payload to TPR v0.5 §6.4/§7.3. No Tender screen or creation. | "Done" is a tender-ready Requisition. Owner choice. |
| D5 | Rows (items, technical, service, acceptance, material) are child tables of `IT Equipment Requirement Package Version`; drawdown lines a child table of `Requisition Version`; `applies_to` = `applies_to_scope` (`Item`/`Service`/`All items`) + `applies_to_id` (stable row id); `required_value_json` canonical JSON validated by the catalogue; `linked_requirement_ids_json` on materials. | One `get_doc` is one atomic snapshot for lock, digest and copy-on-return; child rows cannot be Link targets; stable ids keep §4 lineage; typed columns fail the §2.2 field-purpose rule. |
| D6 | Authorise = external calls first (Budget check → Budget reserve → Planning drawdown per line), then every Requisition write inside `frappe.db.savepoint` with rollback-to-savepoint on any exception; no commit; sub-keys `{key}:budget`, `{key}:planning:{drawdown_line_id}`; revoke mirrors with `{key}:budget:{reservation}` / `{key}:planning:{pdr}`. | Direct Python callers (seeds, tests) get atomicity; retries replay in Budget (`reused`) and Planning (journal). |
| D7 | No canonical seed stage this cycle. The REQ seed chains after Planning in `make seed-kentender-mvp-v1`; Python tests build their world through Planning's `tests/fixtures.py` and commands; Playwright fixtures call Planning's `playwright_ui_fixtures` resets. `canonical.validate` and `collect_non_canonical` become namespace-aware for reservations. | Needs and Planning are not canonical stages (SEED-OPS-001 §2); promotion is one follow-up for all three. |
| D8 | Planning function names are kept (`record_requisition_drawdown`, `reverse_requisition_drawdown`); the Requisitions gateway maps the spec names. | No rename churn on a tested contract. |
| D9 | Immutability by digest: Version and Package Version controllers recompute `content_digest` in `validate` when the before-save status is not Draft and reject any difference beyond status/record_version/reference columns unless `flags.kt_lifecycle`; `on_trash` refuses unless `flags.kt_fixture_wipe`. Decisions and the handoff reject updates after insert except consumption columns. | §7.5 invariant 12 enforced below the service layer. |
| D10 | Warranty is a package field projected read-only into the technical table; never a stored characteristic row. `equipment_function` splits into `network_function` / `power_function` keys; `Other essential characteristic` is one repeatable key with reason. | §6.3 "not entered twice"; two catalogue rows share a label with different options. |
| D11 | Errors: `errors.py` = the sixteen §11 codes, `fail()` refuses others; AUTH_* remapped at the boundary; record-addressed reads outside authority raise the same not-found as a missing record; validation findings use a separate closed `FINDING_CODES` set and surface as `REQ_BLOCKING_FINDINGS` detail. | §11, AUTH-ADR-001 v1.6 non-disclosure; Planning D4 precedent. |
| D12 | Artboards are the literal build source, ported class-for-class from `REQ-CHG-001 Artboards.dc.html`; the fidelity helper gains an artboard-id scope so one file serves eleven screens; a fidelity assertion per artboard is a slice-gate condition. | AGENTS §6.6; owner-mandated gate. |
| D13 | Test isolation without PEs: Python world = Planning's `KENTENDER_TEST` world (FY 2101-2102, two OUs) extended with Requisitions actors (`reqt.author@`, `reqt.hod@`, `reqt.hopf@`, `reqt.auditor@`, `reqt.outsider@`, `reqt.nobody@` `example.test`); Playwright world = Planning's `KENTENDER_PLAYWRIGHT` world (FY 2098-2099) extended the same way, `--workers=1`, `serial`, one fixture-reset function per spec file, `restore_site` in `globalTeardown` and every gate. | Planning D13; one site, one PE. |
| D14 | Files: Frappe `File` `is_private=1` on the Package Version; `services/files.py` checks magic bytes, size ≤ 20 MB, readability (PDF header / Pillow decode) and computes SHA-256; malware scan is a `kt_file_scanners` hook — absence records "Not scanned — no scanner configured", visibly, never "clean". Download through a whitelisted endpoint under the registered predicate. | §5.10 with no scanner in the bench; REQ-AC-017/032. |
| D15 | Working context: no Procuring Entity switcher and no Financial Year selector; the workspace lists every eligible Plan Item the actor's OU assignments reach. | §1.1, §8: FY is inherited display data, never a scope. |

### 2.1 Cross-document conflicts (REQ v1.6 controls)

| # | Conflict | Disposition |
|---|---|---|
| C1 | SEED-001 §4.3 / SEED-AC-003: one reservation; REQ §5.3/§13.12/§16.4 + BUD §8.2A: one per drawdown line | Two. SEED-001 correction → FU-01. |
| C2 | PLN §7.4: one open Requisition per plan item + requesting OU; REQ §5.1: one per plan item | One per Plan Item. PLN text correction → FU-02. |
| C3 | Spec `AuthoriseRequisitionDrawdown` vs code `record_requisition_drawdown` | D8. |
| C4 | PLN §4.14 fields missing from the live projection; no `plan_item_line_id`/`source_line_id` in Planning | Phase 1 extends the projection; `plan_item_line_id := plan_source_allocation_id`, `source_line_id := need id, else dpp_entry id`. |
| C5 | TPR v0.5 §16.1 fixture (1 item, 0 acceptance rows) vs REQ §13.6–13.8 (2 items, 5 rows); TPR §6.4 accepts "v1.2 or its corrected successor" | Build REQ's fixture; handoff version `AuthorisedRequisitionHandoff v1.3`. TPR fixture correction → FU-03. |
| C6 | Budget FU-10: the live Planning seed issues `PPI-MOH-2027-001/-002`, not `-033` | Reference derived from Planning's id; specs read ids from fixture results; fidelity exempts data values. |
| C7 | E2E-REQ-001 v0.2 predates §2.1 and §9.1A | Carried open per REQ §21 → FU-04. |
| C8 | Core governed reservation list (10) vs legacy `tds.py` list | `TENDER_RENDERABLE_RESERVATION_CATEGORIES` in core; legacy `tds.py` untouched. |
| C9 | KT-STD-001 §8.4A lacks the Requisition fixture-instant row | Added in Phase 0 (1 Mar – 15 May 2027 EAT, per SEED-001 §7). |

## 3. Phase sequence

| Phase | Name | Exit condition |
|---|---|---|
| 0 | Plan, tracker, gap analysis, follow-ups, env personas, KT-STD row | Docs written; AC map holds 56 `Planned` rows; no product code changed. |
| 1 | Sibling contracts + Requisitions schema (horizontal) | Core, Budget and Planning owning-app tests green; every Requisitions doctype migrates; hooks, navigation and roles registered; `test_requisitions_schema` planted-violation-proven; `test_gateway_contracts` green; `bench migrate` clean. |
| 2 | Core services (Python only) | Every §10 read/command implemented behind `api.py`; §18.1 layers 1–6 green module by module; REQ-SMK-04/09/10/11 proven at service level; savepoint atomicity proven by a forced Planning failure. |
| 3a | Workspace (REQ-DES-01) | Slice gate (§4). |
| 3b | Start Requisition (REQ-DES-02) | Slice gate. |
| 3c-i | Editor steps 1–2 (REQ-DES-03, 04, 13.6A) | Slice gate. |
| 3c-ii | Editor steps 3–5 (REQ-DES-05, 06, 07) + upstream-correction dialog | Slice gate. |
| 3d | Department approval task (REQ-DES-08) | Slice gate. |
| 3e | Procurement authorisation task (REQ-DES-09) + authorise/return/lead-unit dialogs | Slice gate. |
| 3f | Authorised Requisition (REQ-DES-10) + revoke dialog + consumed state | Slice gate. |
| 4 | §16 seed + Playwright fixture world | `make seed-kentender-mvp-v1` + validate green twice; two reservations exist only after authorisation; purge/teardown branches. |
| 5 | Release evidence | §18.3 pack; persona pass REQ-SMK-01/02/07/08 as real actors; build hash; industry and translation-binding gates; prohibited-token search; AC map closed truthfully; FOLLOW_UPS updated. |

### Phase 1 detail
- `kentender_core`: registry entry `Head of Procurement Function` (Site-wide, REQ-CHG-001 v1.6 §8); `site_setup` ACTORS/ASSIGNMENTS + Charles Mutiso; `Delivery Location` doctype + seed row + `canonical.validate` fact; `regulatory_reference.TENDER_RENDERABLE_RESERVATION_CATEGORIES`; `canonical.validate`/`collect_non_canonical` reservation rules namespace-aware; `kentender_mvp_v1/clear.py` requisitions branch (stub until Phase 4).
- `kentender_budget`: D1 with tests `test_check_reserve_requisition_caller.py` (HoPF permitted, Finance still permitted, Budget Officer refused; reserve after release; two reservations on one allocation from different `caller_reference`; same `caller_reference` conflict; `finance_task` omitted; audit event carries `calling_module`).
- `kentender_procurement/procurement_planning`: projection fields (C4); `planning_roles.REQUISITION_CALLER_ROLES`; read gate widened; drawdown/reverse gate = HoPF (closes FU-07); `Plan Item Correction Request` + services + My Work row (D3); `test_plan_requisition.py` updated.
- `kentender_procurement/procurement_requisitions`: `modules.txt`; all doctypes; `errors.py`; `envelope.py`; `catalogue.py`; `requisition_roles.py`; `requisition_authorization.py`; hooks (`kentender_scope_map`, `permission_query_conditions`, `has_permission`, `kt_my_work_providers` placeholder, `page_js`, `app_include_css`); `workspace_sidebar/procurement.json`; `setup/workspace_permissions.py`; `setup/procurement_home_page.py` roles; `tests/test_requisitions_schema.py`, `tests/test_gateway_contracts.py`, `tests/test_catalogue.py`.

### Phase 2 detail
`references.py`, `eligibility_gateway.py`, `funding_gateway.py`, `compatibility.py`, `restrictive_terms.py`, `validation.py`, `digest.py`, `files.py`, `draft_commands.py`, `lifecycle.py`, `authorise.py`, `handoff.py`, `events.py`, `read.py`, `my_work_provider.py`, `api.py`; tests `test_compatibility.py`, `test_validation.py`, `test_digest.py`, `test_draft_commands.py`, `test_lifecycle.py`, `test_authorise.py`, `test_handoff.py`, `test_requisition_authorization.py`, `test_requisitions_api_requests.py`, `test_envelope.py`, `test_funding_gateway.py`; `tests/fixtures.py`.

### Phase 3 detail (per slice)
`api.py` methods already exist from Phase 2; each slice adds Vue components ported from the artboard, co-located `*.spec.js`, the Playwright spec with one fixture-reset function in `seeds/playwright_ui_fixtures.py`, the fidelity assertions for its artboards, and a Make gate `ui-req-<slice>-gate`.

## 4. Slice gate

A slice is `Done` only on all of: component tests green; Playwright spec green single-worker with per-role logins (each §8 actor served plus one outsider and one unassigned user); absence assertions on refusal paths (no Procuring Entity control, no STD/template selector, no create-without-Plan-Item action); first paint **and** one interactive re-render observed; direct load, reload and back/forward on every route-addressable state; a forced 500 error state; the inline-error-not-Message-dialog check; fidelity assertions for the slice's artboards; zero page-specific console errors; bundle hash changed; screenshot(s) in `evidence/v1_6/`.

## 5. Verification commands

```bash
# Focused Python (one module per run, sequential) — from /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_requisitions.tests.<module>
# Owner-side pins
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_planning.tests.test_plan_requisition
bench --site kentender.midas.com run-tests --app kentender_budget --module kentender_budget.tests.test_check_reserve_requisition_caller
bench --site kentender.midas.com run-tests --app kentender_core --module kentender_core.tests.test_business_role_registry
# Component / browser — from apps/kentender_v1
npx vitest run --project procurement-requisitions
npx playwright test --workers=1 tests/ui/smoke/requisitions/<spec>.spec.ts
npx playwright test --workers=1 tests/ui/smoke/design-fidelity/requisitions-fidelity.spec.ts
# Assets (never plain bench build); touch hooks.py + clear cache after CSS edits
cd /home/midasuser/frappe-bench && ./scripts/bench-with-node.sh build --app kentender_procurement
# Seed
make seed-kentender-mvp-v1 SITE=kentender.midas.com && make seed-kentender-mvp-v1-validate SITE=kentender.midas.com
# Gates
make requisitions-schema-gate requisitions-services-gate ui-req-<slice>-gate ui-req-fidelity-gate ui-req-release-evidence-gate
```

## 6. Non-goals

Tender creation or any Tender Preparation screen; a Planning-side correction-resolution screen; canonical seed stage promotion; STD manifest/schema/composer objects; multiple currencies, lots or award packages; Works or Services Plan Items; a malware-scan provider; migration of any v1.2-era data; a Procuring Entity or Financial Year control anywhere.

## 7. Risks

| Risk | Mitigation |
|---|---|
| D1 changes Budget's reservation-uniqueness semantics | Budget-side tests for reserve-after-release, two reservations on one allocation, same-caller conflict; recorded in Budget FOLLOW_UPS. |
| `PPI-MOH-2027-033` is not a stable live id | Nothing hardcodes it; fixture specs read ids from fixture results; tracker cites the observed id. |
| Heuristic validators false-positive on real text | The §16.3 fixture text is the first test case; lists are code-owned and listed in the tracker. |
| Savepoint semantics inside `IntegrationTestCase` | The first Phase 2 authorisation test forces a Planning failure and asserts no decision/handoff/event survived. |
| One artboard file, per-file fidelity helper | Extend `designFidelity.ts` with an artboard-id scope in slice 3a, before any screen relies on it. |
| Editor is the largest single UI slice so far | Split into 3c-i / 3c-ii with separate gates and fixture resets; stop and record if a slice overruns by half. |
