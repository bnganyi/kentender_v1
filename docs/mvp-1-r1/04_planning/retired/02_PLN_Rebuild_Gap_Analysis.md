# PLN-CHG-001 v1.12 — Gap analysis against the live v1.2 module

| Control | Value |
|---|---|
| Authority | `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_12.md` |
| Companions | `03_PLN_Rebuild_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md` |
| Prepared | 5 September 2026, from a direct read of every module file named below (no inference rows) |
| Predecessor | `02_PLN_Rebuild_Gap_Analysis_v1_2.md` (the Demand-era → v1.2 analysis, closed 31 August 2026) |

## 1. What the code implements today

`kentender_procurement/kentender_procurement/procurement_planning/` is a complete PLN-CHG-001 **v1.2** build: 20 doctypes, 19 service modules (5,980 lines), 37 whitelisted endpoints, 14 test modules (138 tests), 4 Desk Pages, 11 Vue SFCs + 10 vitest specs, one Industry CSS file, the §14 seed (1,148 lines), Playwright fixtures (1,351 lines) and 8 Playwright specs (38 tests). The v1.2 tracker's 32 headline findings remain valid engineering facts (archived in `IMPLEMENTATION_TRACKER_v1_2_closed.md`).

The current baseline on `kentender.midas.com` (5 September 2026): `test_planning_v12_schema` Ran 6, FAILED (failures=2 — legacy tables and the single-root rule); `test_dpp_lifecycle` and `test_planning_workspace` error in `setUpClass` with *"Exactly one root organisation unit exists per site"* (the fixtures create per-test Procuring Entities and OU roots, which AUTH v1.6's one-site-one-PE model forbids) and run 0 tests. The Playwright suite cannot run: all seven fixture worlds are keyed on dedicated Procuring Entities. This is the expected consequence of the AUTH v1.6 cutover landing before Planning's own, not a regression.

## 2. What survives unchanged in mechanics (≈60%)

- `services/envelope.py` (idempotency key, expected version, row locks, journal), `references.py`, `planning_roles.py` constants, `my_work_provider.py` shape.
- DPP lifecycle command shape (`dpp_lifecycle.py`), validation decisions (`dpp_validation.py`) incl. the invariant-24 first-acceptance race, formation/dissolve (`plan_workbench.py`), the governance chain (`plan_governance.py`), publication attempt/acknowledge/retry and successor mechanics (`plan_publication.py`), requisition eligibility and drawdown ledger (`plan_requisition.py`).
- Doctype families: DPP root/version/entry/submission/validation task/decision, Annual Plan/Version/Item/Publication/Destination, Plan Source Allocation, Plan Governance Task/Decision, Plan Drawdown Reference, Planning Command Journal.
- The Vue page shell (`ProcurementPlanning.vue`, four `*_page.js` controllers on the Industry rail), `data/planningApi.js`, the vitest project, the Make gates.

## 3. What changes, by concern

| Concern | Today | v1.12 | Owning phase |
|---|---|---|---|
| Authorisation | `services/authority.py`: `frappe.get_roles` + `User Permission` rows; zero resolver calls; nothing in `kentender_scope_map` | `planning_authorization.py` on `authorise_record`; DPP family in the scope map; AUTH→PLN remap; assignment snapshot on every decision | 2 (D2–D5) |
| PE / context | `pe_fy_context` (18 files), `procuring_entity` (40 files), KenTender `Financial Year` (15 files), `planning_context.py` PE selection | one `fiscal_year` Link to ERPNext `Fiscal Year`; FY is a visible filter only | 2 (D7) |
| Submission window | `Departmental Plan Submission Window` doctype read in `dpp_lifecycle.py:93`, `dpp_read.py:113`, `workspace.py:47` | `kentender_dpp_submission_open/_closes_at` on Fiscal Year (absent in core today) | 1 (D8), 2 |
| Finance | per-item `Plan Finance Task`; `check_funding`→token→`reserve_funding`; `Plan Reservation Reference`; release/revalidate; `finance_state` on the item; role Budget Officer | one task per Version over `check_plan_affordability` (absent in Budget today); no reservation anywhere; Finance Confirmation Officer | 1 (D11), 2, 5 |
| Statutory route | `Procuring Entity.entity_type` (legacy doctype) | `Site Procuring Entity.statutory_approval_route` (absent today) | 1 (D10), 2 |
| Plan Item | title, description, objective lineage, type, method (catalogue of one), aggregation reason, seven flat dates | + category, eleven methods (admissible set), horizon, justification, aggregation, lotting, lot count, county reservation, reservation category + reason, exclusive preference, threshold band, baseline anchor + five periods, derived baseline, forecast, actual, variance, item status; new `Plan Item Forecast Revision` | 2, 4, 6 |
| Regulator references | none | `kentender_core` effective-dated register + read service (absent today) | 1 (D9) |
| Readiness | Objective/schedule/allocation blockers | + method admissibility (blocking), contents, delivery boundary, reservation share (advisory), county share, splitting advisory | 2, 4 |
| Needs contract | `Fully included` / `Not included` usage | + `Not proceeding` with reason (absent in NDS today) | 1 (D12), 3 |
| Publication payload | ad-hoc JSON | OCDS planning-stage releases; invitation-to-treat characterisation; forecast seeding on activation | 2, 6 |
| Scheduler | none (all `scheduler_events` commented out) | daily `CheckApproachingMilestones` via `emit_notification_log` | 2 |
| Catalogues | `Requirement Type`/`Procurement Method` rows exist only via test fixtures | seeded in core: four types incl. Works; eleven methods; ERPNext `UOM` replaces `Unit Of Measure` | 1 |
| Screens | 16 v1.2 compositions | DES-01 rebuilt, DES-07/09/09A/10/11/14 changed, DES-14A new, DES-13 built; verdict-before-render Forbidden panel | 3–6 |
| Test isolation | seven PE worlds (Playwright), per-test PE worlds (Python) | one Playwright world on FY 2098-2099 + dedicated OUs; Python on FY 2101-2102 / 2103-2104 | 2, 3–6 |
| Seed actors | `moh.plan.approver@example.test`, Budget Officer as Finance | KT-STD §8.3 register: Daniel Rotich statutory, Josphat as Finance Confirmation Officer, Julia acting 26–30 Nov, Peter's split DHI assignments | 7 |

## 4. Sibling-contract state (5 September 2026)

| Contract | State | Action |
|---|---|---|
| Strategy `resolve_strategy_context` / `list_strategy_objectives` / `create_strategy_snapshot` | Exists; PE accepted-and-ignored at the whitelist bridge only | Planning gateway drops the PE kwarg |
| Budget `list_eligible_budget_lines` | Exists; returns no human `reference` (FU-02) | Add `reference` (D11) |
| Budget `check_plan_affordability` | **Absent** (specified BUD v1.5 §8.2) | Build (D11) |
| Budget `check_funding` / `reserve_funding` / `release_reservation` / `revalidate_reservations` | Exist | Planning stops calling them |
| CFG DPP intake flags | **Absent** (specified CFG v0.9 §4.2) | Build (D8) |
| CFG `statutory_approval_route`, `entity_is_county` | **Absent** (specified CFG v0.9 §4.1) | Build (D10) |
| CFG regulator reference register | **Absent** (specified CFG v0.9 §4.4A) | Build (D9) |
| NDS events, `get_current_accepted_need`, `project_planning_usage` | Exist | Add `Not proceeding` (D12) |
| Core `emit_notification_log`, `kt_my_work_providers` | Exist | Reuse |
| Business-role registry | Cites PLN v1.4; has `Planning Auditor`, `Budget Officer` on Planning | D6 |
| OCDS serialiser | **Absent** | Build in Planning |

## 5. Files in scope

See `03_PLN_Rebuild_Implementation_Plan.md` §3 detail. Deleted outright: `doctype/departmental_plan_submission_window/`, `doctype/plan_reservation_reference/`, `services/authority.py`, the seven PE constant blocks and builders in `seeds/playwright_ui_fixtures.py`, `Unit Of Measure` links. Everything else is edited in place.
