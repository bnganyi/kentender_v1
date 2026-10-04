# REQ-CHG-001 v1.11 — gap analysis (current code against the approved spec)

| Control | Value |
|---|---|
| Authority | `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_11.md` (approved 24 September 2026) |
| Design authority | `design/Requisitions - Design Board v2.dc.html` (owner-updated 24 September 2026). The older `Requisitions - Design Board.dc.html` in the same folder is the superseded v1.9 board and is not an authority. |
| Code inspected | `kentender_procurement/procurement_requisitions/`, `public/js/procurement_requisitions/`, `tests/ui/smoke/requisitions/`, the Planning, Budget and Tenders seams |
| Prepared | 24 September 2026 |
| Supersedes | The v1.6 gap analysis (greenfield baseline, 6 September 2026) |

## 1. What the code implements today

The module was built for v1.6 (6–7 September 2026), then patched toward v1.8. The v1.9 spec landed in commit `a91e6706` but was never built.

- **Backend.** About 506 KB of Python:
  - 16 doctypes;
  - 21 service modules;
  - an explicit-signature `api.py` with 34 endpoints;
  - 184 Python tests in 19 modules;
  - a canonical seed and a Playwright world on FY 2099-2100.
- **UI.**
  - One Desk Page, `procurement-requisitions`, registered through `kentender_core.desk_page.register` with the shared rail. This is correct under AGENTS.md §6.1.
  - One root `ProcurementRequisitions.vue` using `useRouteState`, `createScreenCache` and `createSequenceGuard`. All six §12 routes are handled.
  - 21 components built around a **five-step editor** (StepDrawdown, StepItems, StepTechnical, StepServicesAcceptance, StepReview).
  - 141 vitest cases.
  - 10 Playwright specs (32 tests).
- **Fidelity.** `requisitions-fidelity.spec.ts` points at `REQ-CHG-001 Artboards.dc.html`, which no longer exists, and compares text landmarks only. There is no structural comparison, no departures registry, and the module is not in `make ui-structure-gate`.

## 2. Keep (proven, spec-conformant mechanics)

| Asset | Why it stays |
|---|---|
| `services/envelope.py` | Idempotency journal, row lock, record_version, a savepoint `atomic()` that re-raises. |
| `services/requisition_authorization.py` + hooks | The EXISTS-over-contributing-units predicate. Both permission hooks are registered for five doctypes. |
| `services/catalogue.py` | All 25 §6.3 characteristics and seven control types. Extended here, not replaced. |
| `services/digest.py`, `restrictive_terms.py`, `technical_read.py`, `references.py`, `events.py`, `files.py` | No v1.11 defect. |
| Page controller, bundle entry, root routing, `req_shared/` adapters | Already follow AGENTS.md §6.1 and §6.4. |

## 3. Gaps by concept

| Concept (v1.11) | State | Evidence | Required change |
|---|---|---|---|
| Three visible tasks over five validation groups (§6.1) | Absent | `validation.py:217-231` five steps; `ProcurementRequisitions.vue:414` five labels | Reads roll the groups up into three task statuses. The UI is re-ported. |
| Grouped standard package `LAPTOP-REQUIREMENTS-V1` (§5.5, §6.4) | Absent | `draft_commands.py:384-432` auto-creates baseline rows per item; `confirm_proposed_requirement` confirms one row at a time (`:462-508`) | `ApplySelectedRequirementPackage`, `SaveRequirementProposalDraft`, Reset standard values; `row_state` on technical and acceptance rows; `standard_profile_key/version`; `standard_package_review_state`. |
| Same-specification items (§5.6, §10.2) | Absent | Items are added one at a time | `AddSameSpecificationItems`, `UpdateSharedItemDetails`, both atomic, plus `REQ_BATCH_ITEM_INVALID`. |
| Exact Money/Quantity (§5.14) | Absent | Drawdown quantity and value are Float/Currency; `flt()` at `draft_commands.py:156,256-260`, `read.py:41,184,302,546`; `1e-6` tolerances in `authorise.py:99` and `validation.py:108,139` | Store exact decimal strings; add `precision.py`; add the `REQ_MONEY_/QUANTITY_PRECISION_INVALID` codes. |
| Single atomic authorisation (§7.2, §9.1A) | Partial | Budget and Planning calls commit before REQ writes (`authorise.py:7-16`); Planning is called once per unit (`:121-135`); revoke reads `Plan Drawdown Reference` directly (`:210`) | One transaction with no inner owner commits, one Planning call for every line, reversal through Planning's published service. |
| Shared-line funding + one reservation per drawdown line (§9.1A) | Partial (Budget side) | `check_funding` checks each row separately (`budget_check_reserve_contracts.py:~136-140`); reservations are keyed per allocation | Budget totals by line and reserves per drawdown line. |
| Nine compatibility checks (§5A) | Partial (6/9) | `compatibility.py:42-53`; the accepted list contains "Other disadvantaged group"; horizon is deliberately skipped (`:9`) | Add the rule snapshot, County, Open Tender and Single year checks; limit categories to the four base ones; add `REQ_RESERVATION_RULE_UNAVAILABLE`. |
| Planning projection facts (§9.1) | Partial | `plan_requisition.py:120` has no plan_item_version, County, rule snapshots, scope lock or hold evidence; numbers are floats | Planning publishes them (closes PLN FU-V125-03). |
| Lead change as return + recertification (§7.3A) | Wrong model | `lifecycle.py:409-435` changes the lead in place | `ChangeRequisitionLeadDepartment` returns and copies; `certified_lead_org_unit_id` frozen per Version. |
| Return affected section (§5.11) | Absent | Decision has only `return_reason` | `affected_section` Select; the copied Draft opens at that section. |
| Upstream correction (§7.4A–B, §9.1B) | Partial | The request does not close tasks; Planning calls `receive_plan_item_correction_outcome` directly (`plan_requisition.py:682,731`) with no event identity or ordering | `PlanItemCorrectionOutcome.v1`, `RecordPlanItemCorrectionOutcome`, outcome projection, `PrepareRequisitionAfterPlanCorrection`, `CreateRequisitionCorrectionDraft`, `GetStoppedRequisition`. |
| Handoff consumption guard (§9.2, §5.13) | Partial | `record_handoff_consumption` does not recheck Authorised; `release_handoff_consumption` exists; Tenders reads REQ tables directly (`tenders/services/handoff_gateway.py:45-61`, `correction.py:74`) | Guarded consumption with `REQ_HANDOFF_CONFLICT`; release removed; handoff v1.4 (owner D4). |
| Error set (§11) | Partial | 12 codes missing; `REQ_PLAN_ITEM_SCOPE_LOCKED`/`REQ_PLAN_ITEM_HELD` extra | Exact §11 set; pass `PLN_ITEM_*` through unchanged. |
| Lineage fields (§5.1) | Partial | Missing `strategic_objective_id`, `plan_item_version_id`, rule snapshots, County, `prior_requisition_id`, `planning_correction_request_id` | Add them. `multi_year_justification` becomes history only. |
| UI v2 board (§13) | Absent | Every component cites v1.6 DES numbering; the classes used omit `kt-meta-row`, `kt-notice`, `kt-timeline` and most `kt-disclosure` | Full re-port, module by module, class-for-class. |

## 4. Cross-module callers affected

- **Tenders:**
  - `tenders/services/handoff_gateway.py:21-92`
  - `draft_commands.py:138`
  - `correction.py:59,74,130`
  - `serializer.py:29,133,138,275`
  - `seeds/kentender_mvp_v1.py:134,319-373`
  - `seeds/playwright_ui_fixtures.py:30`
  - `tests/fixtures.py`
  - `tests/test_gateway_contracts.py`
- **Planning:** `procurement_planning/services/plan_requisition.py:682,731`.
- **Core seeds:**
  - `kentender_core/seeds/canonical.py:49,367,482,561,734,825`
  - `seeds/kentender_mvp_v1/{clear,orchestrator,validate}.py`
- **Hooks** (`kentender_procurement/hooks.py`): permission hooks `:386-401`, My Work `:575`, technical read `:586,594`, page and CSS `:73,231`.
- **UI tests:**
  - `tests/ui/smoke/requisitions/*`
  - `tests/ui/globalTeardown.ts:23`
  - `tests/ui/smoke/core/technical-read.spec.ts`
- **Informational gate:** `kentender_core/tests/test_artboard_provenance_gate.py:141` names the Requisitions board provenance finding.
