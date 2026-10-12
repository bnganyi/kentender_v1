# REQ-CHG-001 v1.11 — Procurement Requisitions build — tracker

**Authority:** `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_11.md` (approved 24 September 2026). **Design authority:** `design/Requisitions - Design Board v2.dc.html`.
**Companions:** `02_REQ_Gap_Analysis.md`, `03_REQ_Implementation_Plan.md` (decisions D1–D14, board findings B1–B3, gates, slice map), `FOLLOW_UPS.md`.
**Supersedes-in-tracking:** the REQ-CHG-001 v1.6 tracker (closed 7 September 2026, 48/56 acceptance rows Done; recoverable from git at `f5c3f649`).
**Status:** Phases 0–1 Done; Phase 2 substantively Done (seeds pending); Phase 3 next. Started 24 September 2026.

## v1.19 Record details (proposed 9 October 2026, built, not yet approved)

Display change directed by the Project Owner (REQ-CHG-001 v1.19 §13.7A; REQ119-CHG-001; REQ119-AC-001..005). v1.18 remains the approved text.

| Item | State | Evidence |
|---|---|---|
| One label pattern; Handoff display reference removed; Departmental need references | Built | `test_read` (record details tests), board REQ-DES-10 artboard |
| Strategic objective reference = Strategy Node reference (was its database name; also fixes the Strategic objective line in Purchase and source details) | Built | `test_read` |
| Digests for the Technical and Auditor reads only | Built | `test_read` |
| Approval of v1.19 | Not given | register untouched |

## v1.18 requirements follow the items (proposed 9 October 2026, built, not yet approved)

Built ahead of approval at the Project Owner's direction (REQ-CHG-001 v1.18 §5.7A, §6.4A, §6.5A, §13.6A, §5.12; change rows REQ118-CHG-001..005; statements REQ118-AC-001..010). v1.16 remains the approved text.

| Item | State | Evidence |
|---|---|---|
| Exact item ids on each requirement row (`Items` scope, `applies_to_item_ids_json`), frozen at lock, digest unchanged for earlier Versions | Built | `test_requirement_scope` 12/12 |
| Proposal generated per item and category (monitor defaults Full HD / 24 in), never `All items` for a mixed request; Laptop-only digest identical | Built | `test_catalogue`, `test_requirement_scope` |
| Customise for one item; reconcile on add/remove/recategorise; **Needs review**; per-item completeness | Built | `test_requirement_scope`, `test_maker_checker`, `test_draft_commands` |
| Handoff 1.5 (`applies_to_item_ids`); Tenders accepts 1.4 and 1.5 | Built | `test_authorise`, `test_gateway_contracts`, `test_snapshot_contract` |
| Tender goods lines, STD projection (incl. Service-scoped acceptance), evaluation labels | Built | `test_requirement_item_scope` 8/8, `test_serializer`, `test_bid_definition`, `test_compiler`, frozen release vectors 1.2–1.4 unchanged |
| End to end: 100 laptops + 50 monitors → Tender, two goods lines with their own technical rows | Built | `tenders.tests.test_mixed_requisition_to_tender` |
| Requirements by target, Customise dialog, Applies-to on service/acceptance, board REQ-DES-05-MIXED | Built | vitest 149/149; fidelity registries |
| Per-item warranty | Deferred (owner) | one shared package-level set kept |
| `bench migrate` on dev | **Not run** | schema: new field on three child doctypes, new Select options |
| Approval of v1.18; TPR / STD-TPL wording for handoff 1.5 | Not given | register untouched |

## v1.17 presentation change (proposed 9 October 2026, built, not yet approved)

Built ahead of approval at the Project Owner's request; v1.16 remains the approved text until v1.17 is approved (REQ-CHG-001 v1.17 §13.4A–C, change rows REQ117-CHG-001..003, statements REQ117-AC-001..005).

| Item | State | Evidence |
|---|---|---|
| One attention panel per task, each finding once, row/section markers, no red strips, one footer status line | Built | Vitest `procurement-requisitions` 144/144; Playwright request-details 8/8, requirements-review, decisions, fidelity pass on the test site |
| Numbered steps row (design-system journey), current step marked | Built | `EditorSteps.spec.js`; browser check at 1280 and 390 wide |
| Items grouped by specification, Edit shared details per group (mixed requests editable) | Built | `test_items_entered_once.TestMixedRequestKeepsEachKindEditable`; Playwright "two kinds of item" |
| Design board REQ-DES-03-MIXED, board steps/panel/footer | Built | `ui-req-fidelity-gate` 5/5 |
| Mixed-category proposal ("All equipment") | On hold (owner) | Not built |
| Approval of v1.17 | Not given | Register not changed |

## v1.15 delta (approved 9 October 2026)

**Authority:** `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_15.md` (supersedes v1.14); support notes and the full change report: `REQ-CHG-001_v1_15_change_manifest.md` (non-normative). Scope: items typed once, requested quantity derived, one estimated total cost per source, unused sources omitted at submission, frozen evidence, Goods template boundary, review of Drafts carried over from v1.14. Automatic estimation is deferred.
**Status (9 October 2026):** document, backend, UI, board, fixtures and canonical seed done and verified on the test site; **dev migration and reseed not done** (see change report §12 for results and what was not verified).

| Item | Status | Evidence |
|---|---|---|
| REQ v1.15 written, checked, approved, register entry updated | Done | preservation PASS; consistency 0 errors; register R5 errors for REQ cleared |
| Backend (commands, validation, lock/omission, read model, handoff departments, error codes) | Done | new tests 16/16 and 1/1; Requisitions suite 316/319 (3 seeded-world failures named in §12) |
| Downstream Tenders and Evaluation | Done with 2 modules failing, not baseline-verified | §12 |
| UI, design board v2, fidelity registries | Done | vitest 128/128; `ui-req-fidelity-gate` 5/5; request-details browser spec 6/6 |
| Canonical seed on the test site | Done | `validate: ok, failures: []` |
| Dev site: migrate (two Version columns + review patch), reseed | **Not done** | needs the owner's go-ahead |
| Browser spec for a carried-over Draft | Planned | no fixture state exists yet |
| Reconcile approved REQ/TPR handoff label (v1.3) with the build (v1.4); KT-STD v1.7 citation; companion workbook | Planned | change report §11 |

## Tracker rules

1. Rows are permanent. Status is one of `Planned`, `In progress`, `Blocked` or `Done`. A reversed decision is struck through in place, not deleted.
2. `Done` needs the row's own evidence: a command with its result counts, a named test, a diff, or a browser observation quoting the literal rendered strings. Never record a result that was not observed.
3. A row is not `Done` while a file it touches still references a prohibited concept:
   - `pe_fy_context`, or a PE/FY scope argument;
   - `User Permission` or a native Role used as authority;
   - STD manifest, composer, capability profile or schema objects;
   - an attachment-primary specification;
   - a technical-review, Finance, Accounting Officer or committee stage;
   - Civic Ledger or Stitch markup, or a `kt_cl_surface_registry.js` entry;
   - a sidebar work-queue entry;
   - `record_requisition_drawdown`;
   - `release_handoff_consumption`;
   - `confirm_proposed_requirement`;
   - float or `flt()` arithmetic on Money or Quantity;
   - the APP-wide 30% denominator, target or shortfall.
4. No alias, redirect, dual-write, compatibility shim or parallel legacy and new surface. A deletion lands in the same change as its replacement.
5. Screens are ported class-for-class from the v2 board. Behaviour comes from §14, never from board content. Reusing a component on a changed board means re-porting it.
6. Slice gates follow plan §3 Phase 4 exactly.
7. A static or architecture guard is `Done` only once a planted violation has proven it fails.
8. Fixture instants are pinned, never relative to now. The Python suite and Playwright never run at the same time. Purge test data after every run.
9. Diagnosis follows the KT-STD-001 test ladder. A full-suite run is never the first diagnostic step.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-24 | D1–D4 answered by the Project Owner: sibling changes this cycle; board extras built as drawn; v2 board only (updated same day); handoff v1.4 with the Tenders reader updated. | Plan approval, 24 Sep 2026. |
| 2026-09-24 | D5–D14 applied as plan defaults, derived from the gap analysis. | Plan §2. |

## Baseline (2026-09-24, before any change)

- Python: 184 tests in 19 modules under `procurement_requisitions/tests/`.
- Vitest: 141 cases in 21 spec files (`--project procurement-requisitions`).
- Playwright: 10 spec files in `tests/ui/smoke/requisitions/`.
- `requisitions-fidelity.spec.ts` references `design/REQ-CHG-001 Artboards.dc.html`, which does not exist, so the gate has no working artboard.
- No structural fidelity comparison, no departures registry, and the module is not in `make ui-structure-gate`.

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| REQ-G00 | Docs rewritten for v1.11; no product code changed | Done | 2026-09-24. REQ11-001 Done. |
| REQ-G01 | Owner contracts in Budget, Planning, Core and Tenders (plan §3) | Done | 2026-09-24. REQ11-101..105 and 107 Done; 106 superseded by D15. |
| REQ-G02 | Requisitions domain: schema, precision, nine checks, every §10 command and read, §11 errors, one-transaction authorisation | Done | 2026-09-24. All 19 REQ test modules green (163 tests) after the seed rewrite. |
| REQ-G03 | UI foundation: fidelity harness, registry, structure gate, shared components | Done | 2026-09-24. REQ11-301..303 Done. |
| REQ-G04a | Slice 4a Workspace (DES-01, DES-12 workspace states) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04b | Slice 4b Start (DES-02, DES-12 purchase states) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04c | Slice 4c Request details (DES-03, DES-04) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04d | Slice 4d Requirements (DES-05) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04e | Slice 4e Review and submit (DES-06) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04f | Slice 4f HoD review (DES-07) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04g | Slice 4g Procurement authorisation (DES-08, DES-09) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04h | Slice 4h Authorised (DES-10) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G04i | Slice 4i Returned and stopped (DES-11) | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ-G05 | §16 seed world and profiles; validated green twice | Done (through requisitions) | 2026-09-24. `canonical.run(rebuild)` then `make seed-canonical THROUGH=requisitions` twice: CANONICAL_SEED_OK, reruns idempotent, validate ok. THROUGH=tenders not attempted — Tenders is knowingly broken (D15, FU-30). |
| REQ-G06 | Release evidence; acceptance map closed | Planned | |

## Work register — Phase 0

| ID | Item | Change rows | Status | Evidence / gap |
|---|---|---|---|---|
| REQ11-001 | Rewrite gap analysis, plan, tracker and follow-ups for v1.11 | REQ19-CHG-032, REQ111-CHG-001 | Done | 2026-09-24. `02_REQ_Gap_Analysis.md` and `03_REQ_Implementation_Plan.md` rewritten for v1.11. This tracker's acceptance map has 135 rows, generated from spec §17 (`grep -c '^| REQ1[0-9]*-AC'` → 135). `FOLLOW_UPS.md`: FU-24 superseded, FU-25..29 added. `git status` shows only docs changed by this row. |

## Work register — Phase 1: owner contracts

| ID | Item | Change rows | Status | Evidence / gap |
|---|---|---|---|---|
| REQ11-101 | Budget: shared-line aggregation in `check_funding`/`reserve_funding`; `drawdown_line_id` per row; one reservation per drawdown line; exact Money strings; no inner commit; same-key replay and changed-payload refusal | REQ19-CHG-014–017 | Done | 2026-09-24. `budget_check_reserve_contracts.py`: `check_funding` normalises the complete array, totals rows per Budget Line before testing availability, and returns per-row plus per-line results (`lines[]`: required/available/after/shortfall as exact strings) and one token bound to a payload digest. `reserve_funding` replays same key + same payload, refuses same key + changed payload (`BUDGET_IDEMPOTENCY_CONFLICT`), refuses a second reservation for a drawdown line (`BUDGET_RESERVATION_CONFLICT`), rechecks the line totals under the stable-order lock, and creates one reservation per drawdown line; no commit. Money in: exact string, int or Decimal; float, exponent, excess scale and more than 18 integral digits → `BUDGET_MONEY_PRECISION_INVALID`. `Funding Reservation` gains `drawdown_line_id` (unique), `source_organisation_unit`, `payload_digest`; migrate clean. New `test_check_reserve_v110_requisition_array` Ran 11 OK, including 20m + 30m against 40m → one line, 10m shortfall, no reservation. Against HEAD's service it ran 11 with 6 failures and 2 errors, so the tests were genuinely red. Owner suites: `test_bud_chg_001_phase3_check_reserve` 8 OK (two assertions moved to exact strings), `test_check_reserve_requisition_caller` 8 OK, `test_bud_chg_001_v19_usability` 18 OK. Residual: Budget's own Currency storage is its FU-30; stored positions are read back exactly at 2 dp. |
| REQ11-102 | Planning projection: `plan_item_version_id`, County treatment, rule snapshot IDs and availability, scope lock, hold and unresolved requests, source boundary vs estimated date, exact strings (closes PLN FU-V125-03) | REQ19-CHG-003–005, 018, 029 | Done | 2026-09-24. `get_requisition_eligible_plan_item` adds `plan_id`, `plan_version_id`, `plan_item_version_id`, `strategic_objective_id`, `county_resident_reservation`, `reservation_rule` (snapshot_id, version_number, verification_status, applies_to_designation, available), `county_rule`, `scope` (locked, since, first requisition), `hold` (held plus every Open/In-progress request), `plan_completion_boundary` (latest source required-by) and `estimated_completion_date`. Every Money/Quantity is an exact string; totals use Decimal (no `flt`/epsilon remains in `plan_requisition.py`). No APP-wide denominator/target/shortfall exposed. Closes PLN FU-V125-03. `test_plan_requisition_v111::TestProjectionCarriesV111Facts` 3 OK. The Planning seed validator's projection checks moved to exact strings. |
| REQ11-103 | Planning: `authorise_requisition_drawdown` takes every allocation in one call with REQ context and no commit; published reversal; REQ stops reading `Plan Drawdown Reference` directly | REQ19-CHG-001, 015 | Done | 2026-09-24. `authorise_requisition_drawdown` takes every allocation in one call with `requisition_version`/`correlation_id`, records each row against its own allocation's department, returns a `drawdowns[]` allocation→reference mapping, refuses float quantity/amount (`PLN_MONEY_PRECISION_INVALID`), compares in Decimal, and never commits (proven by patching `frappe.db.commit`). The `requesting_org_unit` parameter is removed with no alias; api.py follows. New `list_requisition_drawdowns` (HoPF-only published read) with endpoint. `Plan Drawdown Reference` gains `requisition_version` and `correlation_id`. `TestOneCallDrawdown` 4 OK; `test_plan_requisition` 38 OK, `test_plan_progress` 16 OK, `test_planning_api_requests` 7 OK after call sites moved to exact strings. |
| REQ11-104 | Planning: correction request plus hold made atomic with the REQ stop; terminal dispositions emit the `PlanItemCorrectionOutcome.v1` payload with producer_sequence | REQ19-CHG-006–013 | Done (Planning side) | 2026-09-24. New `services/outcome_event.py` builds `PlanItemCorrectionOutcome.v1` (every §9.1B field; `producer_sequence` = position in the request's disposition stream; UTC `decision_at`; Resolved carries the exact replacement item/version/allocation lineage, Closed without change carries the reason and null lineage). Delivery is to consumers registered under the `kt_plan_item_correction_outcome_consumers` hook, in the disposition transaction. `plan_requisition.py` no longer imports the Requisitions lifecycle (AST-checked). `TestCorrectionOutcomeEvent` 4 OK. The Planning test base stubs delivery, so Planning's suite never drives REQ records. Recording a request and making the hold effective were already atomic under `scope_lock.guard`. The REQ consumer and hook registration land in REQ11-209. |
| REQ11-105 | Core/Planning: REQ product gate limited to None, Youth, Women and Persons with disabilities | REQ110-CHG-008 | Done (no code needed in core) | 2026-09-24. The four base categories are Planning's `readiness.BASE_RESERVATION_CATEGORIES`; REQ's compatibility check (REQ11-203) reads that list, not core's `TENDER_RENDERABLE_RESERVATION_CATEGORIES`. |
| REQ11-106 | Tenders: handoff v1.4 reader; consumption only through the guarded `record_handoff_consumption`; release removed; no direct REQ table reads | REQ19-CHG-023 | Superseded by D15 | 2026-09-24. The owner ruled that Tenders will be revamped next: build REQ literally even if it breaks Tenders. Tenders is only kept importable and migratable (FU-30). |
| REQ11-107 | REQ `test_gateway_contracts` pins every new owner signature | REQ19-CHG-031 | Done | 2026-09-24. `test_gateway_contracts` rewritten: pins `authorise_requisition_drawdown` (whole context, no `requesting_org_unit`, no `record_requisition_drawdown`), `list_requisition_drawdowns`, `correction_request_facts`, the §9.1B event fields and hook name, Budget `check_funding` parameters and the reservation result keys (incl. `drawdown_line_id`). Ran 5 OK. |

## Work register — Phase 2: Requisitions domain

| ID | Item | Change rows | Status | Evidence / gap |
|---|---|---|---|---|
| REQ11-201 | `precision.py` plus exact Money/Quantity storage and arithmetic across the module | REQ19-CHG-017 | Done | 2026-09-24. New `services/precision.py` (exact KES scale 2, 18 integral digits, whole-number Each; float/exponent/NaN/excess scale refused) — `test_precision` 7 OK. Drawdown Money/Quantity columns are `Data` strings; every total and comparison is `Decimal`. The schema test's prohibited-token scan now includes `flt(` and `1e-6`; none remain in services or api. |
| REQ11-202 | Schema additions: lineage, County, rule snapshots, lead fields, affected_section, row_state, standard profile and review state, outcome projection doctype; `multi_year_justification` kept as history only | REQ19-CHG-018, 019, 021, 044 | Done | 2026-09-24. Added pinned `plan_item_version_id`, `strategic_objective_id`, `lead_org_unit_id`, unique `open_slot_key`, prior/correction lineage (root); lead directive, certified lead, preparation and submission authority, basis snapshot (Version); County + rule snapshot IDs (Package); profile key/version, proposal digest, review state (Package Version); `drawdown_line_id` (Item); `row_state` (technical, acceptance); `reason`/`affected_section`/`new_lead_org_unit_id`/`resulting_state` (Decision, task now optional); new `Requisition Correction Outcome`. Removed `multi_year_justification` and the four `upstream_correction_*` fields. Migrate clean. `test_requisitions_schema` allow-list regenerated from the JSON; 4/5 OK — the prohibited-token scan fails only on `seeds/kentender_mvp_v1.py` and `seeds/playwright_ui_fixtures.py` (still call removed commands; rewritten in REQ11-501/502). |
| REQ11-203 | Nine independent §5A checks at Prepare and Authorise | REQ19-CHG-019, 020; REQ111-CHG-004 | Done | 2026-09-24. `compatibility.py`: nine named checks in §13.1 order (designation against the installed template's declared categories plus Planning's verified rule → `REQ_RESERVATION_RULE_UNAVAILABLE` or `REQ_PRODUCT_UNSUPPORTED`; County needs template support then a verified County rule; Open Tender; Single year with no justification bypass). `test_compatibility` 9 OK; Prepare and Authorise both call `require_compatible`. |
| REQ11-204 | Standard package: `LAPTOP-REQUIREMENTS-V1` constant, `SaveRequirementProposalDraft`, `ApplySelectedRequirementPackage`, Reset standard values; `confirm_proposed_requirement` deleted | REQ19-CHG-038, 039, 041 | Done | 2026-09-24. `catalogue.LAPTOP-REQUIREMENTS-V1` (exact §13.1 rows, board groups, exact decimals) and catalogue-driven proposals — `test_catalogue` 15 OK. `SaveRequirementProposalDraft`, `ApplySelectedRequirementPackage` (stale digest → `REQ_STANDARD_PROPOSAL_STALE`; at least one acceptance check; all-or-nothing), `ResetStandardValues`; `confirm_proposed_requirement` deleted. `test_draft_commands::TestStandardPackage` 5 OK. |
| REQ11-205 | `AddSameSpecificationItems` and `UpdateSharedItemDetails`, atomic, with `REQ_BATCH_ITEM_INVALID` | REQ19-CHG-037 | Done | 2026-09-24. `add_same_specification_items` / `update_shared_item_details` atomic; a bad row → `REQ_BATCH_ITEM_INVALID` naming the row, nothing created; category change regenerates a Review-required proposal keeping confirmed history. `TestSameSpecificationItems` 3 OK. |
| REQ11-206 | Returns carry `affected_section`; the copied Draft opens there | REQ19-CHG-044 | Done | 2026-09-24. Both returns take `affected_section`; the copied Draft is Review required and the editor's `returned` block names the task/section. `TestReturns` 2 OK. |
| REQ11-207 | `ChangeRequisitionLeadDepartment` as return plus copy; frozen certified lead | REQ19-CHG-021, 022 | Done | 2026-09-24. `change_requisition_lead_department`: HOPF-only at Submitted, different contributing OU, 20–500 reason; returns and copies with a lead directive; the old Version keeps its certified lead; only the new lead's HoD can certify. `TestLeadChange` 2 OK. |
| REQ11-208 | One-transaction `AuthoriseRequisition` and `RevokeUnconsumedAuthorisation` through owner services only; handoff v1.4 | REQ19-CHG-014, 015, 023; D4 | Done | 2026-09-24. `authorise.py`: Budget complete-array check + one reservation per drawdown line + Planning one-call drawdown + decision + v1.4 handoff + outbox, all inside one savepoint with no owner commit. `TestAuthorise` 5 OK, including a forced handoff failure leaving 0 reservations, 0 drawdowns, no scope marker; insufficient funding creates nothing; SoD; Planning hold passes through as `PLN_ITEM_AUTHORISATION_HELD`. Revoke reverses through Planning's published read + reversal and Budget release in one savepoint; scope marker stays. |
| REQ11-209 | Upstream correction: close tasks, `RecordPlanItemCorrectionOutcome`, outcome projection, `PrepareRequisitionAfterPlanCorrection`, `CreateRequisitionCorrectionDraft`, `GetStoppedRequisition` | REQ19-CHG-006–013, 024, 025 | Done | 2026-09-24. `RequestUpstreamPlanCorrection` freezes, cancels tasks and records Planning's request/hold in one savepoint (owner refusal leaves everything unchanged). `correction.py`: the registered `PlanItemCorrectionOutcome.v1` consumer authenticates against Planning's published `correction_request_facts`, deduplicates, quarantines conflicts without raising (so an invalid event never undoes Planning's disposition), orders by producer_sequence and notifies the requester; `PrepareRequisitionAfterPlanCorrection` and `CreateRequisitionCorrectionDraft`. `test_correction` 5 OK; `test_lifecycle::TestStops` 3 OK; `test_authorise` corrected-draft 1 OK. |
| REQ11-210 | Guarded `RecordHandoffConsumption` with `REQ_HANDOFF_CONFLICT` | REQ19-CHG-023 | Done | 2026-09-24. Consumption locks the handoff and root, replays the same Tender, refuses another Tender or a revoked handoff (`REQ_HANDOFF_CONFLICT`), frees the open slot; release deleted. `TestRevokeAndConsume` 4 OK. |
| REQ11-211 | Exact §11 error set; `PLN_ITEM_*` passed through; `REQ_PLAN_ITEM_*` deleted | REQ19-CHG-005 | Done | 2026-09-24. `errors.py` = the 29 §11 codes (count asserted by script); `REQ_PLAN_ITEM_*` deleted. |
| REQ11-212 | Reads: three-task progress over five groups; workspace Your work / Ready / register; editor projection with proposal; decision and correction chains; EAT datetimes | REQ19-CHG-033, 034, 042, 043; REQ110-CHG-002–006 | Done | 2026-09-24. `read.py` + `presenters.py`: workspace (Your work / Ready to start / register, technical mode, inline Forbidden with the §13.13 text), start preview with every DES-02/12 purchase state, record dispatcher (editor, locked, version, authorised, stopped), editor (three tasks, footer hints, returned panel, contributor mode), HoD and HOPF tasks (question, certification, decision chain, nine checks, funding totalled per line via Budget's non-mutating position read), authorised and stopped views; EAT times rendered without conversion (closes FU-22's display defect). `test_read` 8 OK. |
| REQ11-213 | One open root per stable item, across departments, under serialized Prepare; fresh-start and corrected-Draft competing for the same slot | REQ19-CHG-002, 026 | Done | 2026-09-24. Unique `open_slot_key` is the authoritative guard; a second Prepare returns the existing route; a Prepare that loses the race creates nothing (savepoint). `TestPrepare` 5 OK. |
| REQ11-214 | Module suite, sibling suites, clean `bench migrate` | — | Done | 2026-09-24. 19 REQ modules / 163 tests green; Budget, Planning v1.11 (11) green; migrate clean earlier this cycle. |

## Work register — Phase 3: UI foundation

| ID | Item | Change rows | Status | Evidence / gap |
|---|---|---|---|---|
| REQ11-301 | `requisitionsScope` in `tests/ui/fidelity/board.js`; `departures/procurement-requisitions.js`; `ui-structure-gate` includes the module; browser fidelity spec rewritten for the v2 board | REQ110-CHG-007 | Done | 2026-09-24. `requisitionsScope` (div#desNN frames and `.sub` variants, annotations stripped, dialogs kept as self); `departures/procurement-requisitions.js` (DEPARTURES + COVERED, checked by `covered.spec.js`); `make ui-structure-gate` includes the project. Component fidelity spec `requisitions.fidelity.spec.js` compares every covered variant. Browser text-landmark spec still to repoint (REQ11-603). |
| REQ11-302 | Tokens: promote `kt-seg`/`kt-date-field` into `kt_industry_tokens.css`; trim `procurement_requisitions_industry.css` | REQ110-CHG-007 | Done | 2026-09-24. `.kt-seg.kt-seg-inline` added to `kt_industry_tokens.css` (the admin stylesheet's segmented control left untouched); module stylesheet rewritten to board compositions only, scoped under `.kt-req`. Core asset rebuild still owed (deferred while the System Setup session runs its gates). |
| REQ11-303 | Shared module components (ProgressRow, ReviewSection, Notice, MetaRow, DecisionChain, CommonState, ReasonDialog); switch mutations to `createCommandRunner` | REQ19-CHG-042 | Done | 2026-09-24. `components/shared/` (Icon, CardTitle, Notice, MetaFacts, DecisionChain, ProgressRow, Disclosure on native details/summary, DialogFrame, ReasonDialog, SegYesNo, DateField, ActionsMenu, CommonState). Root rewritten as a thin router; every mutation goes through `createCommandRunner` via one injected context; a failed background refresh keeps the screen and offers a retry (found live). |

## Work register — Phase 4: vertical slices

| ID | Item | Change rows | Status | Evidence / gap |
|---|---|---|---|---|
| REQ11-401 | 4a Workspace | REQ110-CHG-002 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-402 | 4b Start dialog and purchase states | REQ19-CHG-035; REQ111-CHG-006 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-403 | 4c Request details and Add laptop request | REQ19-CHG-036, 037; REQ110-CHG-003 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-404 | 4d Requirements | REQ19-CHG-038–041; REQ110-CHG-004 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-405 | 4e Review and submit | REQ19-CHG-042, 046; REQ110-CHG-005 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-406 | 4f HoD review | REQ19-CHG-045; REQ110-CHG-005 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-407 | 4g Procurement authorisation and confirmation | REQ19-CHG-043; REQ110-CHG-005 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-408 | 4h Authorised | REQ110-CHG-006 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |
| REQ11-409 | 4i Returned and stopped | REQ19-CHG-025, 047; REQ110-CHG-006 | Done | 2026-09-24. Browser: 21/21 slice specs + 6-frame board-v2 fidelity gate (structure + text) green; 108 component/fidelity vitest, full vitest 834 green. |

## Work register — Phases 5–6

| ID | Item | Change rows | Status | Evidence / gap |
|---|---|---|---|---|
| REQ11-501 | §16 canonical world, six lifecycle profiles and the 16.4A isolated profiles through real commands | REQ19-CHG-030 | Done | 2026-09-24. `seeds/kentender_mvp_v1.py` on the v1.11 commands (one same-specification add + one package apply, clock in site-local EAT); lifecycle profiles restore the namespace when the item is locked, held or changed. The thirteen §16.4A profiles are REQ11-504. `test_requisitions_seed` 12/12. |
| REQ11-502 | Playwright world (FY 2099-2100) updated; one reset per spec | — | Done | 2026-09-24. Playwright world resets for every drawn state incl. `reset_stopped`, `reset_stopped_closed`, `reset_revoked`, `reset_consumed`, `reset_direct_hod_draft`. |
| REQ11-503 | `make seed-canonical THROUGH=tenders` validated green twice | — | Partial | 2026-09-24. Green twice THROUGH=requisitions; THROUGH=tenders blocked by D15 (Tenders revamp). |
| REQ11-504 | §16.4A isolated profiles as named demo data (D16–D18) | REQ19-CHG-030 | Done | 2026-09-24. `seeds/profiles.py`: all thirteen profiles on the canonical item through real commands, each returning an observed created/refused report; `make seed-req-profiles` / `seed-req-profile PROFILE=…` / `seed-req-profile-restore`; `canonical.run()` releases a loaded profile first; `make seed-canonical` gains `REBUILD=True`. Proof: each loaded live with every result `[ok]`; `test_requisitions_profiles` 17/17; a loaded SHARED-LINE-SHORT then `make seed-canonical` released it, reseeded and validated with no hold left. Documented in SEED-OPS-001 v1.9 §9. Limits recorded per profile (FU-35–FU-38). |
| REQ11-601 | Persona pass SMK-01..15 as the real actors | REQ19-CHG-049 | Planned | |
| REQ11-602 | Evidence pack `evidence/v1_11/`; handoff v1.4 plus digest; all-or-none proofs | — | Planned | |
| REQ11-603 | Prohibited-token search; acceptance map closed; follow-ups updated | REQ19-CHG-050 | Planned | |

## Acceptance map (135 rows)

Status stays `Planned` until a named test or observation is cited in Evidence.

| ID | Required result (abridged; the spec text governs) | Status | Evidence |
|---|---|---|---|
| REQ19-AC-001 | Starting from a currently preparation-eligible item serializes one stable-item open slot; create a Draft or return an authorized existing open-record route,… | Planned | |
| REQ19-AC-002 | A page read creates no record or task. | Planned | |
| REQ19-AC-003 | Planning and inherited departmental facts are read-only. | Planned | |
| REQ19-AC-004 | The Draft contains one fixed IT Equipment package without profile or schema selection. | Planned | |
| REQ19-AC-005 | Each drawdown retains canonical exact Planning allocation and tagged stable source plus exact source/DPP/item revisions; each item links explicitly to a… | Planned | |
| REQ19-AC-006 | Requested Money/Quantity are exact positive strings within current remaining original Planning allowance; copied APP Versions cannot reset prior consumption. | Planned | |
| REQ19-AC-007 | Every item links to one REQ drawdown line, which links to one exact eligible Planning allocation; display PIL/SRC labels are not command identity keys. | Planned | |
| REQ19-AC-008 | Item quantities reconcile exactly to requested source quantities. | Planned | |
| REQ19-AC-009 | Only category-applicable characteristics and their released controls are accepted. | Planned | |
| REQ19-AC-010 | Unknown Select values and free-text substitutes are rejected server-side. | Planned | |
| REQ19-AC-011 | Every standard suggestion is visible and editable before one deliberate grouped confirmation; no generated value is silently confirmed. | Planned | |
| REQ19-AC-012 | Warranty and conditional support fields enforce their ranges and visibility. | Planned | |
| REQ19-AC-013 | Complex software, integration or migration produces a Blocking unsupported-product finding. | Planned | |
| REQ19-AC-014 | At least one observable acceptance row is required. | Planned | |
| REQ19-AC-015 | "Satisfactory" alone is rejected as a pass condition. | Planned | |
| REQ19-AC-016 | A supporting file cannot create an unstructured obligation. | Planned | |
| REQ19-AC-017 | An operative file links to at least one structured requirement and retains a digest. | Planned | |
| REQ19-AC-018 | Brand/restrictive wording without permitted equivalence treatment blocks submission. | Planned | |
| REQ19-AC-019 | A Departmental Author routes one complete locked Version to the HoD. | Planned | |
| REQ19-AC-020 | A Head of User Department sees the complete Version and may return or submit it. | Planned | |
| REQ19-AC-021 | A HoD preparing directly may submit without an invented departmental-review task. | Planned | |
| REQ19-AC-022 | HOPF sees the complete immutable Version, independent current original allowance/scope/hold evidence and full-array Budget availability, all nine… | Planned | |
| REQ19-AC-023 | No technical reviewer, Finance approver, Accounting Officer or committee stage exists in the Requisition chain. | Planned | |
| REQ19-AC-024 | Procurement return creates a copied Draft successor and preserves the submitted Version. | Planned | |
| REQ19-AC-025 | REQ authorisation, Planning drawdown/permanent first-authorisation scope marker, every Budget reservation, decision, handoff and outbox commit together or… | Planned | |
| REQ19-AC-026 | Failed authorisation creates none of those effects. | Planned | |
| REQ19-AC-027 | The handoff contains all inherited facts and every structured row with stable IDs. | Planned | |
| REQ19-AC-028 | Authorisation creates no Tender and binds no Tender template. | Planned | |
| REQ19-AC-029 | TPR consumes exact handoff once through REQ owner validation in the same transaction as Tender creation; retains every source/item/requirement ID and groups… | Planned | |
| REQ19-AC-030 | Unconsumed revocation serializes against consumption, reverses exact drawdown and every Budget reservation once, preserves historical approvals and never… | Planned | |
| REQ19-AC-031 | Revocation after consumption is blocked. | Planned | |
| REQ19-AC-032 | Role-bound `User Responsibility Assignment`, resolved through the registered permission hooks, protects rows, counts, routes, files and commands… | Planned | |
| REQ19-AC-033 | An acting HoD uses a time-bound assignment; no delegate role or second permission system exists. | Planned | |
| REQ19-AC-034 | The complete Ministry of Health package renders with zero missing values or anonymous requirement text. | Planned | |
| REQ19-AC-035 | Repeated seed and command execution remains idempotent. | Planned | |
| REQ19-AC-036 | No STD Configuration, manifest, composer profile or generic schema object exists. | Planned | |
| REQ19-AC-037 | No attachment-only specification can reach authorisation. | Planned | |
| REQ19-AC-038 | TPR receives all structured items and technical/service/acceptance rows; TPR v0.9 matching precision/single-year/consumption contracts require actual… | Planned | |
| REQ19-AC-039 | A drawdown line's Organisation Unit must be among the Plan Item's contributing departments; any other value is rejected with `REQ_DEPARTMENT_NOT_CONTRIBUTING`. | Planned | |
| REQ19-AC-040 | Budget’s complete-array funding check/locked reservation rejects any per-line aggregate shortfall; exact shared-line requirement/availability/shortfall are… | Planned | |
| REQ19-AC-041 | Every authorised Requisition's Budget position change is visible in BUD-CHG-001's own reservation records, matching this module's reservation IDs exactly. | Planned | |
| REQ19-AC-042 | No pe_fy_context_id, PE/FY user-permission scope argument or authority bypass exists. Record FY and source OU remain required eligibility facts, not… | Planned | |
| REQ19-AC-043 | Planned designation (`reservation_category`) and lotting indicator are read-only throughout, and an unsupported value is rejected at product-suitability… | Planned | |
| REQ19-AC-044 | RequestUpstreamPlanCorrection atomically preserves/stops the exact pre-authorisation Version, cancels its tasks, records the owner request and makes item… | Planned | |
| REQ19-AC-045 | HOPF cannot authorise a Version they submitted departmentally; HOPF alone cannot prepare a departmental Draft. Dual-role actors exercise exact current… | Planned | |
| REQ19-AC-046 | Every field in this document passes the field-purpose rule in §2.2; no field exists without a stated decision, control and downstream effect. | Planned | |
| REQ19-AC-047 | The lead department's Head of User Department certifies on behalf of every contributing department in one submission, never one certification per department. | Planned | |
| REQ19-AC-048 | An item links to exactly one drawdown line; a Requisition with two contributing departments and one shared specification produces two item rows, never one… | Planned | |
| REQ19-AC-049 | A standard package renders as **Review required**, distinct from **Reviewed**, and blocks Requirements and Review-and-submit completion until the selected… | Planned | |
| REQ19-AC-050 | HOPF can request lead change only at Submitted to Procurement with reason; command returns/copies for new lead certification, preserves original… | Planned | |
| REQ19-AC-051 | Each drawdown line's requested quantity and value default to its full remaining balance; a user may still enter a smaller amount. | Planned | |
| REQ19-AC-052 | A Plan Item whose `procurement_category` is not `Goods` is rejected at `PrepareITEquipmentRequisition`, before any Draft is created, with… | Planned | |
| REQ19-AC-053 | Every row in §5A's compatibility test is independently checked and independently named on failure; no test is folded into a single generic suitability flag. | Planned | |
| REQ19-AC-054 | The Strategic Objective and its full path are visible in Request details, both decision tasks and the authorised handoff, traceable without a second query… | Planned | |
| REQ19-AC-055 | Only fixed Single year is operative. Multi-year and non-Open-Tender method fail product compatibility before preparation and again at authorisation; no… | Planned | |
| REQ19-AC-056 | PLN/REQ provider schemas explicitly map every consumed stable/exact source, financial, date, scope/hold and eligibility fact; actual wire and precision… | Planned | |
| REQ19-AC-057 | AuthoriseRequisitionDrawdown is the sole canonical Planning drawdown command; no RecordRequisitionDrawdown alias remains in active provider/caller code or… | Planned | |
| REQ19-AC-058 | Request recording/hold and new authorisation use the same stable-item guard; both race orderings preserve one valid outcome and no acknowledged hold can be… | Planned | |
| REQ19-AC-059 | Hold is derived while any relevant request is Open/In progress; one request’s closure, Draft correction or stale terminal snapshot cannot clear another… | Planned | |
| REQ19-AC-060 | Correction request/hold leaves existing authorised REQs, Budget reservations and published Tenders unchanged; no automatic revoke/release/cancel or APP-wide… | Planned | |
| REQ19-AC-061 | First authorised REQ permanently fixes stable-item procurement scope through APP copies, new source revisions, revocation and cancellation; new Needs use a… | Planned | |
| REQ19-AC-062 | A consumed original proceeding can be followed by a REQ drawing remaining original scope; permanent scope lock alone is not a blanket authorisation… | Planned | |
| REQ19-AC-063 | Planning-owned defect uses governed Plan successor; Need/DPP source defects begin with their owners; warranty/technical REQ facts use ordinary REQ… | Planned | |
| REQ19-AC-064 | PlanItemCorrectionOutcome.v1 validates exact request/stopped REQ/item/baseline lineage, terminal outcome, actor/time, required no-change reason and… | Planned | |
| REQ19-AC-065 | Closed without change displays the reason and unchanged-facts warning; old Version remains stopped. An explicit fresh-start can create a new linked Draft… | Planned | |
| REQ19-AC-066 | Resolved does not resurrect the stopped Version or carry approvals/funds. Explicit fresh start binds current corrected exact lineage, fresh root/row IDs and… | Planned | |
| REQ19-AC-067 | Same event/payload no-op; conflicting duplicate/schema/producer rejected; gaps/out-of-order/missing identities reconciled with pending state. Event receipt… | Planned | |
| REQ19-AC-068 | Fresh-start and normal Prepare against one stable item yield one open root across departments; exact retries return the same result, and unauthorized… | Planned | |
| REQ19-AC-069 | REQ sends one complete array and receives one bound expiring Budget token; independent per-row tokens/subsets, Finance task arguments and changed-payload… | Planned | |
| REQ19-AC-070 | Two 20m/30m rows against 40m available produce 10m aggregate shortfall and no effects; a successful 50m draw produces two distinct reservations, not a… | Planned | |
| REQ19-AC-071 | Money/Quantity round-trip exactly through BUD/PLN/NDS/REQ/TPR contracts and persistence; at least 18 integral digits plus supported decimals; reject floats,… | Planned | |
| REQ19-AC-072 | PSA allocation IDs, stable Need/direct source IDs, Need -V revision IDs, REQ drawdown/item IDs and human PIL/SRC labels retain distinct meanings. Legacy… | Planned | |
| REQ19-AC-073 | HOPF lead change cannot relabel previous certification; copied Draft and new lead submission precede authorisation. Deterministic default/tie and current… | Planned | |
| REQ19-AC-074 | RecordHandoffConsumption/TPR creation and REQ revocation share the owner guard; no delayed projection admits revoked consumption or released funds behind a… | Planned | |
| REQ19-AC-075 | Create corrected Draft is explicit and uses current eligibility/open-slot guard; no event automatically recreates a hold, decision or Draft. Changed… | Planned | |
| REQ19-AC-076 | Stopped detail renders the full structured package, original reason, each outcome, older/new lineage, remaining hold and exact fresh-start actions; no… | Planned | |
| REQ19-AC-077 | Authorisation displays temporary hold, permanent scope lock and per-source remaining allowance separately; held and shared-line-shortfall states block… | Planned | |
| REQ19-AC-078 | Administrator/System Manager have full technical read without business decisions; queues/routes/files share AUTH checks and ordinary Forbidden paints no… | Planned | |
| REQ19-AC-079 | All nine product gates are named independently. Network connectivity uses Required multi-select consistently; all 11 fixture technical rows apply to both… | Planned | |
| REQ19-AC-080 | Plan/source boundary 31 Dec 2027, estimated completion 24 Sep 2027 and REQ operational date 30 Sep 2027 remain distinct; REQ does not overwrite Plan dates… | Planned | |
| REQ19-AC-081 | BASE remains blocked Draft; positive REQ uses conditional READY/Youth plus the exact verified reservation rule and owner prerequisites. Lifecycle fixtures… | Planned | |
| REQ19-AC-082 | Shared HOPF is Charles Mutiso with exact login; Peter’s March DHI authority is valid from 1 Dec; Budget owns reservations and CFG catalogue; no new Charles… | Planned | |
| REQ19-AC-083 | Only current owner evidence can close contract/precision/transaction/seed claims; LAW/CFG applicability and unprovided STD/E2E documents remain explicit,… | Planned | |
| REQ19-AC-084 | All 84 v1.8 results and the complete 25-row characteristic catalogue are retained or explicitly reconciled; five validation groups map to three visible… | Planned | |
| REQ19-AC-085 | The Draft presents exactly three user tasks while retaining and reporting all five internal validation groups. | Planned | |
| REQ19-AC-086 | Request details contains approved-plan amounts and equipment without requiring a separate saved page transition between them. | Planned | |
| REQ19-AC-087 | Requirements contains all technical, warranty/support, service, acceptance and supporting-material fields with no deleted catalogue option. | Planned | |
| REQ19-AC-088 | The start dialog creates nothing until Start requisition succeeds; reload, Cancel and opening the dialog create no root. | Planned | |
| REQ19-AC-089 | All eleven suggested technical rows, five suggested acceptance checks and six warranty/support defaults are visible before grouped confirmation; one… | Planned | |
| REQ19-AC-090 | Copied or changed-category packages remain Review required until the user uses Use selected requirements; confirmed history is not overwritten. | Planned | |
| REQ19-AC-091 | Ordinary preparation uses the approved business labels; exact identities and machine terminology remain available in supporting evidence and unchanged… | Planned | |
| REQ19-AC-092 | Every returned Draft opens the governed affected section with the exact correction comment visible; the reviewed Version remains immutable in History. | Planned | |
| REQ19-AC-093 | HoD and HOPF see the complete request in the same stable order, with role-specific result, statement and actions only. | Planned | |
| REQ19-AC-094 | HOPF sees current funding, available-after amount, Planning availability and every material blocking exception before Authorise requisition. | Planned | |
| REQ19-AC-095 | All nine compatibility checks remain independently visible and enforced; their lower placement does not reduce the gate. | Planned | |
| REQ19-AC-096 | Authorisation confirmation states quantity, value, Budget Line, available-after amount and the plain-language consequence. | Planned | |
| REQ19-AC-097 | Authorised view contains every item, requirement, support value, acceptance check and reservation; counts never replace content. | Planned | |
| REQ19-AC-098 | Continue to Tender Preparation performs navigation only; Tender creation remains an explicit TPR command. | Planned | |
| REQ19-AC-099 | Planning-correction pages clearly distinguish waiting, in progress, resolved, closed without change, unavailable and another-request-open states. | Planned | |
| REQ19-AC-100 | No stopped Version displays Resume, Clear hold, edit, approve or authorise controls. | Planned | |
| REQ19-AC-101 | Author, direct HoD, reviewing HoD, HOPF, Procurement Officer, Planner, Auditor and technical-reader journeys have exact action sets without role switching. | Planned | |
| REQ19-AC-102 | Technical readers can open every record state site-wide and see no business command; ordinary masked records remain Requisition not found. | Planned | |
| REQ19-AC-103 | Save/validation failure retains still-authorised input and points to the affected section/control; no unsupported autosave is claimed. | Planned | |
| REQ19-AC-104 | Uncertain command outcomes resolve the original idempotency identity before another decision is offered. | Planned | |
| REQ19-AC-105 | Desktop and narrow layouts retain every decision-critical quantity, value, requirement, result and action. | Planned | |
| REQ19-AC-106 | Keyboard, focus, contrast, long-text wrapping and dialog return comply with KT-STD-001 v1.7. | Planned | |
| REQ19-AC-107 | Representative Departmental Author, HoD and HOPF users complete ordinary and correction tasks without button coaching and correctly explain scope,… | Planned | |
| REQ19-AC-108 | Misunderstanding that an APP update expands an authorised package, authorisation creates a Tender, or a supporting file replaces structured requirements… | Planned | |
| REQ19-AC-109 | KT-STD-001 v1.7 §2 plus §13 alone supplies every exact value, control, actor/state premise and action required to render every artboard; no operative phrase… | Planned | |
| REQ19-AC-110 | Every artboard and reset variant represents one internally possible state; incomplete and complete values, progress labels, issue summaries and enabled… | Planned | |
| REQ19-AC-111 | Every actor in §8 maps to at least one explicit §13 artboard or named actor variant, including the isolated contributing-department Author. | Planned | |
| REQ19-AC-112 | Every §13 business control appears in §14.1, belongs to an actor/state permitted by the lifecycle and has its exact destination or committed result stated.… | Planned | |
| REQ19-AC-113 | In the two-department same-specification fixture, the user enters category, item name, delivery location and date once; one atomic command creates exactly… | Planned | |
| REQ19-AC-114 | Removing or editing one source-linked item never silently changes the other item’s source-specific quantity or intended use; editing shared details names… | Planned | |
| REQ19-AC-115 | The routine Laptop package requires no row-by-row creation of the eleven technical requirements or five acceptance checks. Every selected row remains… | Planned | |
| REQ19-AC-116 | Author, HoD, HOPF, Procurement Officer and authorised readers receive the same ordered section summaries and can reveal every exact row without leaving the… | Planned | |
| REQ19-AC-117 | Sections with a blocker, warning or requested correction start open and focus the exact affected content; complete non-exception sections may start closed. | Planned | |
| REQ19-AC-118 | A collapsed summary never replaces, truncates or changes the complete record, export, digest, decision payload or accessible detail. | Planned | |
| REQ110-AC-001 | No field, state, role, permission, command, validation, event, integration, governance, audit or evidence requirement changes solely because of this… | Planned | |
| REQ110-AC-002 | Every REQ-DES family implements its assigned archetype, primary question and Level 1–3 hierarchy from §13. | Planned | |
| REQ110-AC-003 | REQ-DES-01 leads with the actor’s exact work or one purchase ready to start; zero-count metrics and the historical register never dominate the workspace. | Planned | |
| REQ110-AC-004 | REQ-DES-03 and REQ-DES-05 expose the current completion gap and one next action before source provenance or proposal/version evidence. | Planned | |
| REQ110-AC-005 | REQ-DES-06 puts readiness, warning, scope, quantity/value and next responsible person in the first view while keeping every structured requirement reachable. | Planned | |
| REQ110-AC-006 | REQ-DES-07 and REQ-DES-08 put the actual decision, consequence and material blocker before expanded evidence; HoD certification and HOPF authorisation… | Planned | |
| REQ110-AC-007 | REQ-DES-10 makes authorised scope and the next lawful stage immediately clear; REQ-DES-11 makes stopped ownership and fresh-start eligibility immediately… | Planned | |
| REQ110-AC-008 | Common/access states inherit their parent orientation and replace stale task/decision content; no generic state panel exposes protected facts or ambiguous… | Planned | |
| REQ110-AC-009 | Colour, containers, tables, borders, badges, uppercase labels and repeated metadata are restrained; emphasis communicates task, issue, state or consequence… | Planned | |
| REQ110-AC-010 | At 1440 × 1024 and the prescribed narrow layout, a representative actor identifies what the page is, what matters now, what they can do and the consequence… | Planned | |
| REQ110-AC-011 | `IT-EQUIPMENT-OPEN-V1` accepts `None`, `Youth`, `Women` and `Persons with disabilities`, plus an independently applicable County-residents restriction, only… | Planned | |
| REQ111-AC-001 | REQ accepts only the exact item-level planned designation, separate County treatment and verified rule/overlap snapshots from PLN v1.25. It neither receives… | Planned | |
| REQ111-AC-002 | A Budget funding reservation created at authorisation is labelled and treated only as a financial hold. It is never used as statutory-reservation allocation… | Planned | |
| REQ111-AC-003 | Ordinary user screens label `reservation_category` as **Reserved for** and show **County requirement** only when applicable. Exact internal field and rule… | Planned | |
| REQ111-AC-004 | The supported start, Draft, review, HoD, HOPF and authorised compositions carry the same inherited item treatment without adding a task or exposing APP-wide… | Planned | |
| REQ111-AC-005 | Every product-compatibility composition, criterion and isolated failure profile consistently contains nine independent checks. No screen or test reports eight. | Planned | |
| REQ111-AC-006 | Active cross-document references use approved LAW v1.2, BUD v1.10, PLN v1.25, NDS v1.14, CFG v0.14, AUTH v1.9, KT-STD v1.7 and STR v1.8; TPR v0.9 and… | Planned | |
