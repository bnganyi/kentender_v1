# REQ-CHG-001 v1.6 — Gap analysis against the live repository

| Control | Value |
|---|---|
| Authority | `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_6.md` (approved 4 September 2026; supersedes v1.5, v1.4, v1.3 (withdrawn) and v1.2 in full) |
| Companions | `03_REQ_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md`, `FOLLOW_UPS.md` |
| Prepared | 6 September 2026, from a direct read of every file named below (no inference rows) |
| Predecessor | None — no Requisitions cycle has run; v1.2 was approved on 28 August 2026 but never built |

## 1. What the code implements today

**Nothing.** There is no `procurement_requisitions` module, doctype, Page, route, service, seed or test in any `kentender_*` app. Every REQ-CHG-001 name (`PrepareITEquipmentRequisition`, `AuthorisedRequisitionHandoff`, `PlanItemCorrectionRequest`, `RecordHandoffConsumption`, `REQ_*` error codes, `IT-EQUIPMENT-OPEN-V1`) occurs only in `docs/`. The slug `procurement-requisitions` collides with no Page, Workspace or DocType (57 Pages and every `Procurement *` DocType checked).

The only traces of the module are:

- v1.2-era role names in `kentender_procurement/kentender_procurement/setup/procurement_home_page.py:78-85` (`Requisitioner`, `Requester`, `Business Approver`, `Department Approver`, `Designated Approver`, `Procurement Approval Authority`) with a comment deferring their rename to the approved REQ document, plus the legacy `requisitioner@moh.test` user in `kentender_core/kentender_core/seeds/constants.py:20-32` and passive `Requisitioner` rows in ~14 Page/Workspace fixtures.
- `kentender_core/kentender_core/services/business_role_registry.py:34-37` deliberately omits `Head of Procurement Function` ("registered in the cutover slice of the document that owns it") — this cycle is that slice.
- Cosmetic strings in the retired STD Configuration module (`std_manifest.py:88` "Requisition Requirements Composer", `std_cfg_output_mapping.json:68`) — retired surface, untouched.

## 2. What exists upstream and downstream for this module to consume

| Contract | Where | State |
|---|---|---|
| `GetRequisitionEligiblePlanItem.v2` | `procurement_planning/services/plan_requisition.py:67`, whitelisted at `procurement_planning/api.py:356` | Live, tested (`test_plan_requisition.py`, 466 lines), caller-less. Returns plan/version/item ids, `fiscal_year`, `requirement_type`, `procurement_category`, `procurement_method`, `strategic_objective`, `objective_path`, planned/forecast dates, funding references and state, total/remaining quantity and value, `sources[]` per `plan_source_allocation_id` (origin, dpp_entry, need, organisation_unit, title, description, expected_operational_result, approved/remaining quantity, unit, required_by_date, budget_line, allocated/remaining amount), `evaluated_at`. **Missing vs REQ §5.1/§5A and PLN §4.14:** `reservation_category`, `lotting_indicator`, `plan_horizon`, `multi_year_justification` (all present on `Annual Plan Item`), a `contributing_org_unit_ids` aggregate, `currency`, award-package count, per-source `source_line_id` / `plan_item_line_id`. Read gate is Procurement Planner / Auditor only. |
| `record_requisition_drawdown` / `reverse_requisition_drawdown` | `plan_requisition.py:174, 270` | Live, tested. Two-phase lock-then-insert on `Plan Drawdown Reference` (one per `requesting_org_unit`), idempotent through `Planning Command Journal`. Gated `require_technical` (System Manager) — Planning FU-07 names the Requisitions module as the closer. Spec names them `AuthoriseRequisitionDrawdown` / `ReverseRequisitionDrawdown`. |
| Planning identifiers | `plan_source_allocation.json`, `annual_plan_item.json` | There is no "Plan Item Line"; the line grain is `Plan Source Allocation.allocation_id`. `source_line_id` exists only inside DPP submission snapshots (`dpp_lifecycle.py:455`: need id, else entry id). |
| `PlanItemCorrectionRequest` inbound | — | Does not exist. Inbound-only precedent: `procurement_planning/services/schedule.py:390 record_tender_milestone_actual`. |
| `check_funding` / `reserve_funding` | `kentender_budget/kentender_budget/services/budget_check_reserve_contracts.py:76, 171`; whitelisted in `api/budget_api.py` | Live, tested (`test_bud_chg_001_phase3_check_reserve.py`), **zero production callers** (Planning's gateway is forbidden from importing them by `test_gateway_contracts.py:49` and `test_planning_v12_schema.py:174-178`). Token TTL 300 s; idempotent by `correlation_id = idempotency_key`; lines locked in stable order; errors `BUDGET_CHECK_STALE`, `BUDGET_INSUFFICIENT_FUNDS`, `BUDGET_RESERVATION_CONFLICT`, `BUDGET_LINE_NOT_ELIGIBLE`. **Blockers:** `_require_finance_capability()` (line 31) admits only Finance Confirmation Officer; `calling_module` hard-coded "Procurement Planning" (line 157); `finance_task` is a required Planning-era argument; `Funding Reservation.plan_source_allocation` is `unique` (`funding_reservation.json:98`), so an allocation can hold one reservation ever — revoke-then-correct and a later Requisition on the same allocation are impossible. |
| `release_reservation` | `kentender_budget/kentender_budget/services/budget_commitment_contracts.py:119` | Live; `amount=None` releases the remainder; idempotent replay on Released. Usable as-is for revocation. |
| Reservation record | `Funding Reservation` (`autoname: hash`; `generated_reference` `RSV-{SITE}-####`, `plan_item` Data, `plan_source_allocation` Data unique, `correlation_id`, `fixture_namespace`) | No requisition reference column; traceability is by `correlation_id`. |
| Tender Preparation consumer | `tender_configurations/services/eligibility.py:33` (`return []`, "empty until MVP-1 Plan Item handoff"), `create_configuration.py:15` (`TCFG_PACKAGE_RETIRED`) | Stubbed; TPR-CHG-001 v0.5 is not built. TPR §6.4 accepts handoff "v1.2 or its corrected successor"; §7.3 lists the snapshot rows it stores. |
| Reservation-category vocabulary | `kentender_core/kentender_core/seeds/site_setup.py:94-105` (10 governed values) vs `tender_configurations/services/tds.py:43-49` (legacy 5 values, different casing) | REQ §5A requires one list shared with Tender Preparation; none is published today. STD-TPL-001 v0.4 §6.1 renders `None`, `Youth`, `Women`, `Persons with disabilities`, `Other disadvantaged group`. |
| Outbox | `departmental_needs/services/events.py` + `Departmental Need Event` | The only transactional-outbox precedent (publish inside the transaction, `consume_events`, `acknowledge`). No core outbox. |
| Location master | — | None in KenTender. Needs forbids `delivery_location` fields (`test_departmental_needs_static_scan.py:64-68`). ERPNext `Location` (assets tree) is the only doctype of that name. |
| Private-file digest / scan | — | None. `Typed Attachment` (core) has no digest; `tender_management/services/planning_tender_handoff_audit.py` has the sha256 idiom. No malware scanner in the bench. |
| Authorisation | `kentender_core/kentender_core/services/authorization.py` (`require_responsibility`, `authorise_record`, `permitted_ou_scopes`, `assignment_snapshot`, hook targets), `business_role_registry.py`, `responsibility_errors.py` | Live and used by Strategy, Budget, Needs, Planning. Registered roles this module needs: Departmental Author (OU), Head of User Department (OU), Procurement Planner (Site-wide), Auditor (Site-wide). **Not registered:** Head of Procurement Function. |
| Vue-in-Desk runtime | `kentender_core/kentender_core/public/js/kt_desk_page.js` (`register`, `useRoute`, `createScreenCache`, `ownsRoute`), `kt_industry_page_rail.bundle.js`, `kt_industry_tokens.css` | Live; Planning is the reference consumer (`procurement_planning_page.js`, `ProcurementPlanning.vue`, `pln_shared/`). |
| Seed world | `kentender_core/kentender_core/seeds/site_setup.py`, `seeds/canonical.py` (`STAGES = site, strategy, budget`) | Grace Wanjiku (Departmental Author DHI + HRMD, HoD HRMD), Dr Peter Kimani (HoD HRMD + DHI), Naomi Chebet (Auditor), FY 2027-2028, UOM `Each`, `MOH-BL-HWD-2027` (KES 60,000,000, Entity-wide) exist. **Charles Mutiso does not exist** (no user, no assignment). The Afya House delivery location does not exist. Needs and Planning are not canonical stages; the Planning legacy seed forms the combined laptops item with a server-issued id (`PPI-MOH-2027-001/-002` observed, Budget FU-10), not the documented `-033`. `canonical.validate` asserts `count("Funding Reservation") == 0` and `collect_non_canonical` deletes every reservation. |
| Playwright / vitest / gates | `tests/ui/smoke/planning/*`, `tests/ui/helpers/designFidelity.ts`, `vitest.config.ts`, `Makefile` `ui-planning-*-gate` | Live patterns. `globalTeardown.ts` restores Planning only; `purge_kentender_playwright_data` has no requisitions branch; the fidelity helper opens one artboard file per screen, whereas REQ ships one file with 11 `<sc-if>` artboards. |

## 3. What the specification requires, by concern

| Concern | Today | REQ v1.6 | Owning phase |
|---|---|---|---|
| Module, doctypes, hooks, navigation | none | root/version/package/package-version + five row tables, task, decision, handoff, journal, event; `modules.txt`; `kentender_scope_map`, permission hooks; sidebar + workspace-permission entries; one Page `procurement-requisitions` | 1 |
| Roles | HoPF unregistered; v1.2 names in landing gate | Departmental Author, Head of User Department (OU); Head of Procurement Function, Procurement Planner, Procurement Officer, Auditor (Site-wide); Charles Mutiso seeded | 1 |
| Planning projection | eight fields missing | §5.1 fields, `contributing_org_unit_ids`, `source_line_id`/`plan_item_line_id`; Requisitions read gate; HoPF drawdown gate | 1 |
| Budget reservation | caller-blocked, unique allocation | HoPF caller, `calling_module`/`caller_reference`, optional `finance_task`, one non-Released reservation per allocation | 1 |
| Delivery location | none | core `Delivery Location` master, Afya House seeded | 1 |
| Category list | two divergent lists | `TENDER_RENDERABLE_RESERVATION_CATEGORIES` in core | 1 |
| Catalogue, validation, digest, files, compatibility | none | §6.3 catalogue, §6.4 baselines, §6.5 findings/steps, §5A tests, canonical digests, file checks | 2 |
| Commands and reads | none | §10.1 seven reads, §10.2 twenty-three commands, §11 sixteen codes, outbox event, handoff v1.3, consumption inbound | 2 |
| Screens | none | REQ-DES-01..10 + §13.13 dialogs, six routes under one Page | 3 |
| Seed | none | §16 six lifecycle fixtures + stopped version + correction request, idempotent, command-driven | 4 |
| Evidence | none | §18.3 pack | 5 |

## 4. Facts that shape the design

1. Planning issues **one `Plan Drawdown Reference` per requesting Organisation Unit**, so a two-department Requisition records two drawdown references; the spec's single `planning_drawdown_reference` is projected as a list.
2. Budget creates **one reservation per source allocation** (BUD §8.2A step 5); with two drawdown lines the authorised fixture carries two reservations (`RSV-MOH-2027-033-001/-002` in REQ §16.4), not the one SEED-001 §4.3 names.
3. `record_requisition_drawdown` documents that it cannot rely on `frappe.handler` rollback for direct Python callers and locks-then-inserts explicitly; Requisition authorisation must give the same guarantee to seeds and tests (savepoint).
4. Child rows cannot be Frappe Link targets; `applies_to` and `linked_requirement_ids` must be modelled as stable-id references validated server-side.
5. The artboards define the Forbidden copy, the six common-state messages and every label; the single `.dc.html` carries all eleven artboards under `<sc-if value="{{ is.desNN }}">` blocks.
