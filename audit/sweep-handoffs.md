# Sweep: handoff-contracts

Phase 2 cross-cutting sweep, READ-ONLY. Static reading only (Read, grep, sed). No bench command, no database, no test run was executed. Every statement below is from source I read; nothing was run, so runtime consequences are inferred and say so where it matters.

Scope: producer/consumer hand-off pairs across the chain NDS -> PLN -> REQ -> TPR -> BDS -> BOP -> EVL -> AWD, plus the BUD/STR/suppliers/core seams they use. Repo root `/home/midasuser/frappe-bench/apps/kentender_v1`; module root `kentender_procurement/kentender_procurement` is abbreviated `P/` below.

## 1. Method

Docs read (latest versions confirmed with `ls | sort -V`): AGENTS.md; PLN v1_29 §7.2, §7.3, §7.4, §7.6, §7.7, §5.1.2; NDS v1_16 §7.1-7.6, §8.1-8.3; REQ v1_14 §5.12-5.14, §7.4, §7.4A, §9.1C, §9.2, error table; TPR v0_17 (handoff v1.3 references, error table, §10.14 / correction route); BUD v1_12 §8.5, BUD21-AC-001/002; STR v1_9 §8 (`resolve_strategy_context`); OVS v0_6 §4.1; E2E-REQ-001 v0.2 §6, §9, §12.

Commands (reproducible):

```
grep -rhoE "get_hooks\(\s*[\"']kt_[a-z_]+[\"']" --include=*.py kentender_*/          # hook consumers
grep -rhoE "^\s*(kt_[a-z_]+)\s*(=|\.append|\[)" --include=hooks.py kentender_*/       # hook definitions
grep -rnoE "(snapshot|snap|payload|req)\.get\(\"[a-z_]+\"" P/tenders/services          # keys Tenders reads off the REQ handoff
grep -rnoE "(projection|proj)(\.get\(|\[)\"[a-z_]+\"" P/procurement_requisitions       # keys REQ reads off the PLN projection
grep -rnE "from kentender_(budget|strategy|suppliers)[a-z_.]* import" --include=*.py kentender_procurement/
grep -rnE "^\s*(from|import) kentender_(procurement|budget|strategy)" --include=*.py kentender_core/
grep -rnE "\"(Annual Plan[A-Za-z ]*|Plan Item|Plan Source Allocation|...)\"" P/procurement_requisitions
sed -n / grep -n on every producer builder and consumer reader listed in section 2
```

## 2. Coverage: hand-off inventory and classification

Classification key: CLEAN = producer and consumer read side by side, keys/types/enums/codes agree; FINDING = see section 3 (F-n); NOTE = checked, minor.

| # | Hand-off (version tag in code) | Producer | Consumer | Result |
|---|---|---|---|---|
| 1 | `DepartmentalNeedAccepted.v2` outbox event (NDS -> PLN) | `P/departmental_needs/services/events.py:68-86` `accepted_payload` | `P/procurement_planning/services/needs_intake.py:97-105` `_facts`, `dpp_autostart.py:48-60` | FINDING F-5, F-10 (key sets differ between event and read; float quantity) |
| 2 | `DepartmentalNeedSuperseded.v1` / `Withdrawn.v1` events | `events.py` `publish_superseded/withdrawn` | none (only `Accepted` is subscribed) | FINDING F-5, F-18 |
| 3 | `get_current_accepted_need` read (NDS -> PLN) | `P/departmental_needs/services/workspace.py:466-519` | `needs_intake.py:65-90` | FINDING F-10 |
| 4 | `NeedPlanningDispositionChanged.v1` (PLN -> NDS) | `P/procurement_planning/services/dpp_validation.py:236-262` | `P/departmental_needs/services/usage.py:303-368` | FINDING F-7 |
| 5 | `NeedPlanningUsageChanged.v1` (PLN -> NDS) | `P/procurement_planning/services/plan_publication.py:32-65` | `usage.py:164-250` | NOTE F-7 (event-id/payload conflict) |
| 6 | `project_need_planning_intake` position (PLN -> NDS) | `needs_intake.py:305-345` | `usage.py:430-489` | CLEAN on keys/enums; FINDING F-5 (trigger gap) |
| 7 | NDS withdrawal dependency / PLN activation source check | `lifecycle.py:966-996` (local projection) | n/a (no Planning provider) | FINDING F-11 |
| 8 | BUD `list_eligible_budget_lines` | `kentender_budget/.../budget_line_contracts.py:364-414` | `P/procurement_planning/services/budget_gateway.py:67-92` | CLEAN (keys `id`, `reference`, `title`, `funding_source`, `approved`) |
| 9 | BUD `check_plan_affordability` / `validate_plan_affordability_for_decision` | `budget_line_contracts.py:428-700` | `budget_gateway.py:95-161`, `financial_basis.py`, `plan_finance.py` | FINDING F-12, F-17 |
| 10 | BUD `receive/withdraw_budget_revision_request` + `BudgetRevisionRequestOutcome.v1` | `kentender_budget/.../budget_revision_request_contracts.py` | `P/procurement_planning/services/budget_revision.py` | FINDING F-8; outcome event CLEAN |
| 11 | STR `resolve_strategy_context` / `list_strategy_objectives` / `create_strategy_snapshot` | `kentender_strategy/.../strategy_consumer.py:76-336` | `P/procurement_planning/services/strategy_gateway.py` | FINDING F-9 |
| 12 | PLN `GetRequisitionEligiblePlanItem.v2` projection (PLN -> REQ) | `P/procurement_planning/services/plan_requisition.py:190-335` | `P/procurement_requisitions/services/*` (38 keys read) | CLEAN (every key REQ reads exists) |
| 13 | `AuthoriseRequisitionDrawdown` / reverse (REQ -> PLN) | `plan_requisition.py:449-560` | `P/procurement_requisitions/services/eligibility_gateway.py`, `authorise.py` | CLEAN on keys/codes |
| 14 | BUD `check_funding` / `reserve_funding` / `release_reservation` (REQ -> BUD) | `kentender_budget/.../budget_check_reserve_contracts.py` | `P/procurement_requisitions/services/funding_gateway.py` | CLEAN on shapes; FINDING F-15, F-19 |
| 15 | `PlanItemCorrectionOutcome.v1` (PLN -> REQ) | `P/procurement_planning/services/outcome_event.py:61-107` | `P/procurement_requisitions/services/correction.py:62-150` | CLEAN (13 required keys, schema_version, producer, hook name `kt_plan_item_correction_outcome_consumers`) |
| 16 | `AuthorisedRequisitionHandoff` payload (code tag `1.4`) REQ -> TPR | `P/procurement_requisitions/services/handoff.py:41-92` | `P/tenders/services/snapshot.py:34-72`, `handoff_gateway.py` | FINDING F-3, F-4, F-6, F-13 |
| 17 | `RecordHandoffConsumption` | `handoff.py:101-136` | `P/tenders/services/handoff_gateway.py:80-93` | FINDING F-2 |
| 18 | `ProcurementRequisitionAuthorised.v1.4` / Revoked / CorrectionRequested outbox | `P/procurement_requisitions/services/events.py` | none | FINDING F-18 |
| 19 | Handoff release / re-authorise for Tender correction | none (removed in REQ v1.11) | `P/tenders/services/correction.py` | FINDING F-1 |
| 20 | `RecordTenderMilestoneActual` + coverage (TPR -> PLN) | `P/tenders/services/planning_gateway.py:36-81` | `P/procurement_planning/services/schedule.py:137-230`, `actuals.py:73-109` | FINDING F-14 |
| 21 | `TenderSubmissionPeriodEnded` / `TenderOpenForSubmission` (TPR -> BDS) | `P/tenders/services/submission_close.py:26-28,112`, `publication.py:176` | `P/bid_submission/services/close.py:46-47,226-250` | CLEAN on names/consumers; NOTE F-18 (payload unread) |
| 22 | `TenderVersionProjection v1` -> STD compiler -> Published Bid Definition (TPR -> STD -> BDS) | `P/tenders/services/bid_definition.py`, `P/std_templates/compiler/definition.py:30-70,255-330` | `P/bid_submission/services/definition_model.py` | CLEAN (sections/groups/response_rows/`repetition` values) |
| 23 | Supplier account provider (suppliers -> BDS) | `kentender_suppliers/.../provider.py` | `P/bid_submission/services/supplier_gateway.py`, `snapshot.py` | CLEAN (contract list `FUNCTIONS` with producer test `missing_functions`) |
| 24 | Tender candidate registry (BDS -> TPR) | `P/bid_submission/services/candidate_registry.py` | `P/tenders/services/candidate_gateway.py` | CLEAN (hook name matches) |
| 25 | `Bid Opening Handoff` v1.0 (BDS -> BOP) | `P/bid_submission/services/close.py:140-205` | `P/bid_submission/services/opening_gateway.py`, `P/bid_opening/services/custody.py:26-33` | CLEAN |
| 26 | `Evaluation Handoff` v1.0 (BOP -> EVL) | `P/bid_opening/services/completion.py:24-43` | `P/bid_opening/services/evaluation_seam.py:49-65`, `P/bid_evaluation/services/intake.py` | CLEAN on keys; NOTE F-20 |
| 27 | Released package (BDS -> EVL) | `P/bid_submission/services/package.py:100-150`, `evaluation_gateway.py` | `P/bid_evaluation/services/sources.py`, `intake.py:100-120` | CLEAN |
| 28 | TPR read seam (TPR -> EVL/BOP/AWD) | `P/tenders/services/evaluation_seam.py`, `opening_seam.py`, `award_seam.py` | EVL/BOP/AWD | CLEAN (NOTE F-6: `award_decision_status` default) |
| 29 | `kt_evaluation_report_consumers` (+ `_failed`), `kt_evaluation_correction_consumers` (EVL -> AWD) | `P/bid_evaluation/services/award_seam.py:32-52`, `signing.py:217` | `P/award/services/intake.py:134-160`, `corrections.py:46` | CLEAN (hook names, `delivery=`/`tender=` kwargs) |
| 30 | `delivered_report` snapshot (EVL -> AWD) | `award_seam.py:93-140` | `P/award/services/intake.py`, `sources.py:57-72` | CLEAN |
| 31 | BDS audience / notice contact (BDS -> AWD) | `P/bid_submission/services/award_gateway.py` | `P/award/services/sources.py:130-185` | NOTE F-21 |
| 32 | AWD -> Contracting (`AwardDecisionRecorded v1`, package, update) | `P/award/services/contracting.py` | none in production (simulation stand-in only) | FINDING F-16 |
| 33 | TPR -> EVL funding reservations -> BUD lineage | `P/tenders/services/evaluation_seam.py:205-212` | `P/bid_evaluation/services/funding.py` | FINDING F-15 |
| 34 | OVS v0.6 §4.1 reads (REQ/TPR lead + contributors) | `P/tenders/services/snapshot.py:116-125` | OVS readers | FINDING F-6 (lead fallback) |
| 35 | analytics/home/my_work/technical hooks (core <-> modules) | owners | `kentender_core` | CLEAN: `analytics_contract.record()` validates types at construction; all 23 `kt_*` hook names defined in hooks.py resolve to a consumer (`_failed` derived by `f"{hook}_failed"` in `award_seam.py:43`) |
| 36 | E2E-REQ-001 v0.2 §6 identifiers (`source_line_id`, `plan_item_line_id`, `requisition_item_id`, technical/service/acceptance ids) | REQ handoff rows | TPR `snapshot.VISIBLE_TYPES`, `bid_definition._items` | CLEAN (ids carried; `drawdown_line_id` join used) |

Totals enumerated: 36 pairs or seams; 21 contain at least one finding or note below.

Dependency direction and imports checked:

| Check | Result |
|---|---|
| Reverse imports into `kentender_core` from procurement/budget/strategy | 112 import lines, all under `kentender_core/kentender_core/seeds/` (seed orchestration only); no non-seed reverse import. Clean. |
| `kentender_budget` -> strategy import | 1 (allowed direction strategy -> budget). Clean. |
| `kentender_procurement` -> budget/strategy | Via `budget_api` (Planning), via `services/*_contracts` modules (REQ, EVL). See F-19. |
| NDS reading Planning tables | `grep -rn "procurement_planning\|Annual Plan\|Departmental Plan" departmental_needs` returns nothing. Clean. |
| Direct writes into another module's tables | None found: the producers' writes go through the owner functions listed above. |

## 3. Candidate findings (most severe first)

Calibration status for the known defects in this domain (stated in section 5 too):
* REQ handoff v1.4 renamed fields / TPR kept old names: FIXED in `P/tenders/services/snapshot.py:34-57` (`_handoff_v14_names`) and pinned by `P/tenders/tests/test_snapshot_contract.py`; silent-default residue remains (F-6) and the pin is weak (F-13).
* Late-accepted Need dead end: FIXED for first acceptance (`dpp_autostart.py:48-60`, `needs_intake.py:305-345`); STILL PRESENT for an accepted successor revision (F-5).
* Reservation denominator: not a hand-off; the REQ handoff correctly carries no denominator (`handoff.py:41-92` has no APP-wide key), matching REQ §5.12.

---

### F-1 (High, CODE DEFECT + SPEC DEFECT): The Tender "Requisition correction" route has no producer; a consumed handoff can never be re-authorised, and the test fabricates the missing state

Evidence:
* Consumer: `P/tenders/services/correction.py:34-66` stops the Tender Version and opens a task for the Departmental Author; `start_corrected_tender_version` (`correction.py:110-150`) needs "a newly authorised successor handoff on the same Plan Item" via `handoff_gateway.successors`.
* Producer side removed: `P/tenders/services/handoff_gateway.py:96-103`:
  `def release(...): ... fail("TND_HANDOFF_INVALID", "A consumed requisition handoff can no longer be released. The Tender correction route is being revised.", ...)`
* REQ refuses to revoke after consumption: `P/procurement_requisitions/services/authorise.py:184-185`: `if handoff_doc.consumed_at: fail("REQ_HANDOFF_CONSUMED", ...)`.
* Successor needs remaining allowance: `P/procurement_planning/services/plan_requisition.py:280-285` `eligible = (... and total_remaining_qty > 0 and total_remaining_value > 0)`, and a consumed authorisation keeps its drawdown (REQ v1.14 §7.4 "after handoff consumption ... cannot revoke or edit").
* The only test of the route fabricates the producer: `P/tenders/tests/test_lifecycle.py:331-333`:
  `# Owner-contract stand-in (§15.1 step 2): ... (REQ FOLLOW_UPS FU-30 owns the real route).`
  `frappe.db.set_value("Authorised Requisition Handoff", authorised["handoff"], {"consumed_at": None, "tender": None, "tender_version": None}, update_modified=False)`

Governing rule: REQ v1_14 §7.4 line "after handoff consumption, Requisitions cannot revoke or edit the authorised package; Tender Preparation uses its own upstream-correction route, per TPR-CHG-001 §10.4". TPR v0_17 §10.4 is "TPR-DES-03 — Draft: Tender details" (heading at line 1067); the correction route is §10.14 and TPR09-AC-010 (line 1712) says it "can continue only from a newly authorised successor handoff". E2E-REQ-001 v0.2 §12 row 5 still says "release the handoff, correct and reauthorise". The three approved documents disagree and REQ offers no command that yields the successor handoff TPR requires. AGENTS.md §5: "A stub that blocks completion is a defect."

Reproduction: authorise a requisition that draws 100% of the Plan Item allowance; `StartTender`; `RequestRequisitionCorrection` (HOPF). The Tender sits in `Requisition correction requested`; the author's task says "Correct Requisition ..."; no REQ command (`RevokeUnconsumedAuthorisation` fails `REQ_HANDOFF_CONSUMED`; `CreateRequisitionCorrectionDraft` needs `Revoked`; `PrepareITEquipmentRequisition` needs remaining allowance) can produce a handoff for `successors()`. Failing-test sketch: replace the `db.set_value` in `test_correction_stops_the_version...` with real REQ calls; it cannot pass.

### F-2 (Medium, CODE DEFECT): Tenders maps the wrong REQ error code, so a concurrent start gets `TND_HANDOFF_INVALID` instead of `TND_HANDOFF_CONFLICT`

* Producer `P/procurement_requisitions/services/handoff.py:122` `fail("REQ_HANDOFF_CONFLICT", detail={"tender": cstr(doc.tender)})` (consumed by another Tender) and `:124` `fail("REQ_HANDOFF_CONFLICT", detail={"state": root.current_state})` (revoked / not current).
* Consumer `P/tenders/services/handoff_gateway.py:88-91`:
  `if exc.code == "REQ_HANDOFF_CONSUMED": fail("TND_HANDOFF_CONFLICT", ...)` then `fail("TND_HANDOFF_INVALID", detail={"requisition_error": exc.code})`.
  `REQ_HANDOFF_CONSUMED` is only raised by revocation (`authorise.py:185`), never by `record_handoff_consumption`. So the conflict branch is unreachable.
* Rule: TPR v0_17 error table: `TND_HANDOFF_CONFLICT` "A Tender has already been started for this requisition" with Open Tender; REQ error table `REQ_HANDOFF_CONFLICT` "already consumed by another Tender or has been revoked". The pre-check at `P/tenders/services/draft_commands.py:100-101` only covers the non-concurrent case.
* Repro: two officers call `StartTender` on the same handoff in parallel; the second gets "no longer available" with no Tender link. Both codes are also folded into one REQ code so the consumer cannot tell consumed from revoked without reading `detail.state`/`detail.tender`.

### F-3 (Medium, CODE DEFECT): Tender stores the Annual Plan Version id in `plan_item_version_id`

* Producer: handoff carries both `"plan_version_id": root.plan_version_id` and `"plan_item_version_id": root.plan_item_version_id` (`P/procurement_requisitions/services/handoff.py:59-60`); Planning's `plan_item_version_id` is the Annual Plan Item name (`plan_requisition.py:300`), `plan_version_id` is the Annual Plan Version name.
* Consumer `P/tenders/services/draft_commands.py:117`: `"plan_item_version_id": snapshot.get("plan_version_id")`.
* Rule: TPR v0_17 line 163 "`plan_item_id`, `plan_item_version_id` | Stable item and exact approved content identities"; field label "Plan Item version" (`P/tenders/doctype/tender/tender.json:93-96`).
* Effect: the exact item content identity is lost on every Tender (the field holds a different record type). No Python reader found yet, so impact is evidence/lineage, not behaviour. Failing-test sketch: start a Tender from a handoff and assert `root.plan_item_version_id == payload["plan_item_version_id"]`.

### F-4 (Medium, SPEC DEFECT / SPEC GAP): handoff and outbox event are tagged `1.4` in code; approved REQ v1.14 and TPR v0.17 still say `1.3`; stored v1.3 handoffs silently drop out

* Code: `P/procurement_requisitions/services/handoff.py:31` `HANDOFF_VERSION = "1.4"`; `P/procurement_requisitions/services/events.py:19` `EVENT_AUTHORISED = "ProcurementRequisitionAuthorised.v1.4"`.
* Docs: REQ v1_14 §5.12 "AuthorisedRequisitionHandoff v1.3", §9.2 "publishes `ProcurementRequisitionAuthorised.v1.3`", §9.1 read "Exact immutable v1.3 handoff"; TPR v0_17 lines 32, 1823, 2024, 2143 "`AuthorisedRequisitionHandoff v1.3`". REQ §5.14 last row: "an incompatible wire change requires an explicit agreed version/cutover, never two undocumented shapes under one name".
* Consumer is exact-match: `P/tenders/services/handoff_gateway.py:69` `if cstr(handoff_doc.handoff_version) != req_handoff.HANDOFF_VERSION: fail("TND_HANDOFF_INVALID", ...)` and the producer's list filter `P/procurement_requisitions/services/read.py:897` `filters={... "handoff_version": handoff_service.HANDOFF_VERSION}`. An Authorised, unconsumed v1.3 handoff therefore disappears from the eligible list and cannot start a Tender; `patches/` has no migration of handoffs (only `ovs_chg_001_v06_tender_lead_from_certification.py` touches them). The v1.4 shape is documented only in code docstrings ("owner D4, 24 Sep 2026"), not in an approved REQ/TPR version.
* Also: both gateway docstrings still cite v1.3 (`handoff_gateway.py:5`).
* Repro: insert an Authorised requisition with a `handoff_version="1.3"` handoff; `list_eligible_handoffs` omits it; `StartTender` returns `TND_HANDOFF_INVALID`.

### F-5 (Medium, CODE DEFECT): a successor Need revision's acceptance never triggers Planning's position projection or departmental-plan autostart

* Producer `P/departmental_needs/services/lifecycle.py:806-811`: `if superseded: event = publish_superseded(...) else: event = publish_accepted(...)` - a successor acceptance publishes only `DepartmentalNeedSuperseded.v1`.
* Consumer `P/procurement_planning/services/dpp_autostart.py:57`: `if cstr(doc.get("event_type")) != EVENT_ACCEPTED: return`; it also reads `org_unit_id`/`financial_year_id` from the top level (`:60-61`), which in the superseded payload are nested under `successor_accepted_payload` (`events.py:167`). `publish_need_positions` is called only from here and from DPP commands.
* Rule: PLN v1_29 §5.1.2 "Planning publishes the positions to Departmental Needs (§7.3) after every departmental-plan command ... and after every Need acceptance", §7.3 row "after every departmental-plan command and every Need acceptance"; the position table includes "Update required (with the earlier revision it carries, if any)", which exists only for successor revisions.
* Effect: after a successor is accepted on a department whose plan is already Accepted, NDS `planning_intake_detail` returns None (`usage.py` `cstr(row.need_revision) != cstr(current_accepted_revision)`), so the Need's page does not tell the department to **Update** the departmental plan until some unrelated DPP command runs. This is the late-accepted-Need dead end re-opened for revisions. `test_late_accepted_need.py` covers the first-acceptance case only (no "Superseded" in `test_late_accepted_need.py`/`test_dpp_autostart.py`).
* Repro: Accept Need, accept DPP, accept successor revision of the Need; call `get_need_planning_status` -> no intake position; expected `Update required` with carried revision.

### F-6 (Medium, CODE DEFECT): silent permissive defaults on keys of the REQ handoff, with a test that pins the permissive value

Side by side (producer / consumer):

| Key | Producer | Consumer default |
|---|---|---|
| reservation category | `handoff.py:70` `"reservation_category": package.reservation_category` | `snapshot.py:47` `out["reservation_category_value"] = payload.get("reservation_category") or "None"`; `compatibility.py:97` `payload.get("reservation_category_value") or payload.get("reservation_category") or "None"`; `bid_definition.py:222`, `serializer.py:375`, `read.py:559-617` `... or "None"` |
| award packages | not emitted (`handoff.py:41-92`; Planning's projection has it `plan_requisition.py` `"award_packages": 1` but REQ does not copy it) | `compatibility.py:123` `packages = payload.get("award_packages") or 1` -> the check "Award package: One" can never fail; `bid_definition.py:201` `_int(snapshot.get("award_packages") or 1)` |
| warranty months | `warranty_support` group | `bid_definition.py` `_int(snapshot.get("minimum_warranty_months"))`, `_int` returns 0 on any error (`bid_definition.py:91-95`) |
| fiscal year | `projection.get("fiscal_year")` | `draft_commands.py:117` `... if frappe.db.exists("Fiscal Year", ...) else None` |
| certified lead | `departmental_certification.lead_org_unit_id` | `snapshot.py:116-125` falls back to `units[0]` (the first contributing unit, which `snapshot.py` itself says "is not the lead") |

* Pinned by test: `P/tenders/tests/test_snapshot_contract.py:59-62` `test_an_unreserved_requisition_stays_none` sets `reservation_category=None` and expects `"None"`; `...first_contributing_unit_stands` pins the lead fallback.
* Rule: REQ v1_14 §5.12 (reservation category and County treatment are exact item-level handoff facts); OVS v0_6 §4.1 and plan D15 (lead is the certified lead, not the first contributor); AGENTS.md §4.3 predictable failure; this is exactly the Requisition-v1.4 failure class (a missing key becomes a permissive value). A handoff missing `reservation_category` would produce an unreserved Tender with no error.
* Repro: delete the key from a handoff payload (or rename it again) and `snap.build(...)`; result carries `"None"` and the Tender starts.

### F-7 (Medium, CODE DEFECT): disposition event deviates from the approved wire contract

* Enum: code `P/departmental_needs/services/usage.py:256` `DISPOSITION_NOT_PROCEEDING = "Not proceeding"` and doctype options `Proceeding\nNot proceeding` (`need_planning_disposition_projection.json:18`); producer `dpp_validation.py:254` passes the same constant. Approved: NDS v1_16 §7.4 "`disposition` | Exact enum `Proceeding` or `Not proceeding this financial year`" and PLN v1_29 §7.6 last paragraph "disposition is exactly `Proceeding` or `Not proceeding this financial year`".
* `schema_version` (integer 1; "Unknown versions are rejected/quarantined") is neither emitted (`dpp_validation.py:249-259`) nor accepted/validated (`usage.py:303-345` has no parameter for it).
* Duplicate id with different payload: NDS v1_16 §7.5 "Different payload under the same ID/sequence conflicts; preserve evidence and reject". Consumer `usage.py:348` `if frappe.db.exists(DISPOSITION_DOCTYPE, {"source_event_id": event_id}): return {... "idempotent": True ...}` and the usage consumer `usage.py:205` return idempotent on equal id regardless of payload.
* `producer_sequence` is `submission_number` of the departmental submission (`dpp_validation.py:244`), not "allocated transactionally per stable Need's disposition stream" (§7.4). Monotonic in practice; not the specified stream.
* Both sides agree with each other, so there is no runtime mismatch today; any external consumer or the spec's enum would fail.

### F-8 (Medium, CODE DEFECT): the budget-revision request omits `expected_line_revision`, so Budget's stale-line check is dead

* Producer `P/procurement_planning/services/budget_revision.py:110-121` sends `planning_request_id, idempotency_key, fiscal_year, budget_line, planned_amount, over_amount, plan_version_reference, plan_label, requested_by, fixture_namespace` (floats via `flt`); no line revision, no approved amount.
* Consumer `kentender_budget/.../budget_revision_request_contracts.py:125-127`: `expected = cstr(payload.get("expected_line_revision")); if expected and expected != line_version.name: return _error("BUDGET_DECISION_BASIS_STALE", ...)`.
* Rule: PLN v1_29 §7.3 row "BUD ReceiveBudgetRevisionRequest ... exact Budget Line and revision, approved, planned and over Money amounts"; BUD v1_12 §8.5 item 1 "Budget Line and expected line revision" and BUD21-AC-002 "a stale line revision fails with `BUDGET_DECISION_BASIS_STALE`". Planning's mapping `BUDGET_DECISION_BASIS_STALE -> PLN_FINANCE_STALE` (`budget_revision.py:126`) is unreachable.
* Also: planned/over amounts cross as floats with a `1e-9` epsilon on both sides (`budget_revision.py:72` `flt(line.get("planned")) <= flt(line.get("approved")) + 1e-9`; Budget `budget_revision_request_contracts.py:130` `planned <= approved + 1e-9`) against PLN §4.1 "Money ... decimal strings" (see F-12).

### F-9 (Medium, CODE DEFECT): Strategy snapshot is taken at Plan Item save, not at final approval; objective eligibility ignores the Plan's Fiscal Year

* Snapshot timing: `P/procurement_planning/services/plan_workbench.py:516` `snapshot = strategy_gateway.snapshot_objective(objective_id=objective_id, correlation_key=f"{item.plan_item_id}:{idempotency_key}")` inside `SavePlanItem`. `create_strategy_snapshot` is called nowhere else (`grep` of `snapshot_objective|create_strategy_snapshot`); final approval only runs `_require_positive_predicates` (`plan_governance.py:418-433`), which re-lists eligible objectives and fails `PLN_STRATEGY_REVIEW_CHANGED`.
* Rule: PLN v1_29 §7.4 "At final statutory approval, call STR `create_strategy_snapshot` ... Store its deterministic returned lineage only if it agrees with the reviewed selection ... The snapshot call belongs to final Plan approval, not item formation ... It must not append duplicate Strategy snapshot evidence on retry." STR's function writes an audit event on every call (`strategy_consumer.py:325-335` `record_event(... "Strategy Snapshot Created" ...)`, with idempotency documented as "wired at the API layer, not here"), so each changed-objective save appends evidence.
* Fiscal Year: `P/procurement_planning/services/strategy_gateway.py:32` `resolve_strategy_context(as_of_date=frappe.utils.today())`, with the comment "Planning selects Objectives for the plan being authored now". PLN §7.3 row lists "FY/Plan period" as the input and STR v1_9 offers `fiscal_year`. When a plan for next year is drafted while a different Primary Strategy is Active today, eligible objectives come from the wrong Strategy version; `_active_plan_version` also swallows every exception into `""` (`strategy_gateway.py:33-34`), which presents as "no objectives".
* Repro: draft the FY N+1 plan after the Strategic Plan for N+1 becomes Active only at year start; the objective list is still N's.

### F-10 (Medium, CODE DEFECT / SPEC GAP): two key shapes under one name for NDS's accepted-Need contract; quantity travels as float

* Event payload `events.py:68-86` (Need id key `need_id`, `accepted_version_id`, `version_number`, `org_unit_id`, `financial_year_id`, `unit_id`, `unit_display_value`).
* Read `workspace.py:503-516` returns `"contract": "DepartmentalNeedAccepted.v2"` with `need`, `accepted_revision`, `revision_number`, `organisation_unit`, `financial_year`, `unit`, `unit_label`.
* Rule: NDS v1_16 §7.1 "Wire keys are unchanged ...: the accepted revision travels as `accepted_version_id` and `version_number`, and the contract stays at `.v2`. Consumers read the keys, not the word"; §8.1 `get_current_accepted_need` is "the typed accepted source contract". Planning reads only `accepted_revision` from the read (`needs_intake.py:90`) so it works today, but two shapes carry the same contract tag.
* Quantity: `events.py:83` and `workspace.py:514` emit `flt(version.indicative_quantity)` (JSON float); PLN v1_29 §4.1 "Quantity | Exact positive decimal string ... Need quantities are copied exactly"; Planning re-reads with `flt` (`needs_intake.py:_facts`). Storage is Float(3) on both sides (`departmental_need_revision.json:94-97`, `departmental_plan_entry.json:103-105`).

### F-11 (Medium, divergence from spec-flagged owner dependency): withdrawal and activation do not use a Planning owner contract

* `P/departmental_needs/services/lifecycle.py:966-996` `check_withdrawal_dependency` answers from NDS's local usage projection for the single named revision; no function `validate_accepted_need_withdrawal_for_decision` exists anywhere (`grep` returns none).
* Planning's approval/activation does not revalidate NDS eligibility: `needs_intake.current_accepted_revision_of` is called only from `dpp_validation.py:197`, `dpp_lifecycle.py:352,412` (departmental plan stage), never from `plan_governance`/`plan_publication` activation (`grep` of callers).
* Rule: NDS v1_16 §8.1 `check_accepted_need_withdrawal_dependency` "across all revisions of the stable Need", §8.3 rows "validate_accepted_need_withdrawal_for_decision" and "Current-source validation at Planning activation", and "matching Planning implementation is required before claiming that race is closed". The spec itself marks these as owed, so this is a divergence from a proposed owner contract rather than an undetected regression; a Need withdrawn between approval and activation can still activate.

### F-12 (Medium, CODE DEFECT): Planning <-> Budget affordability uses floats and an epsilon; two statement shapes for one contract family

* `kentender_budget/.../budget_line_contracts.py:496` `within_approved = planned <= pos["approved"] + 1e-9` (also `:646`), `:456` `totals = {str(k): flt(v) ...}`; the display statement returns floats (`"approved": pos["approved"]`, lines 343/408/512), the decision statement returns strings (`:663` `"approved": money(pos["approved"])`), the decision statement returns strings (`:663`). Planning sends `planned_totals: dict[str, float]` (`budget_gateway.py:95`).
* Rule: BUD v1_12 (BUD-CHG-001 v1.10 §4.8, applied by `budget_check_reserve_contracts._exact_money`) and PLN v1_29 §4.1 "Money ... never binary float ... APIs use decimal strings". `_exact_money` in the same app refuses floats, but the affordability contracts accept them.
* Effect: statement fields change type between `check_plan_affordability` (float) and `validate_plan_affordability_for_decision` (decimal string); `financial_basis._rows_from_decision_statement` normalises both through `money_text`, hiding the difference.

### F-13 (Medium, TEST GAP): the Tenders-side contract test pins substrings of producer source, from a hand-written fixture, and omits keys the consumer reads

* `P/tenders/tests/test_gateway_contracts.py:46-60` asserts `self.assertIn(f'"{key}"', source, key)` against `inspect.getsource(handoff.build_payload)`; any quoted occurrence anywhere in the function passes (e.g. `"quantity"`, `"unit"` appear in several places).
* `HANDOFF_KEYS` (`:30-37`) omits keys Tenders reads: `county_resident_reservation` (`compatibility.py:108`, `bid_definition.py:188`), `reservation_rule_snapshot_ids` (`compatibility.py:91`), `plan_item_version_id`, `currency` (`compatibility.py:122`), `award_packages` (read, never produced - F-6).
* `P/tenders/tests/test_snapshot_contract.py:25-45` reads a hand-written `V14_PAYLOAD`, not the shape `build_payload` returns, so a producer rename passes both tests unless the key literally disappears from the source text.
* Producer side: no REQ test pins the key set of the payload against Tenders' reads (REQ `test_gateway_contracts.py` pins the Planning/Budget signatures only). Net: one-sided, weak.

### F-14 (Medium-High, CODE DEFECT): Tenders' coverage rows never reach Planning (identity mismatch hidden by a silent skip)

* Producer `P/tenders/services/planning_gateway.py:68-72`:
  `allocation = cstr(line.get("plan_item_line_id"))`
  `if not allocation or not frappe.db.exists("Plan Source Allocation", allocation): continue`
  `plan_item_line_id` is the Planning `allocation_id` (`plan_requisition.py` sources: `"plan_item_line_id": a.allocation_id`, format `PSA-...`, `references.py:112-115`), whereas `frappe.db.exists(doctype, name)` tests the document name, which is `PSAR-{#####}` (`plan_source_allocation.json` autoname `format:PSAR-{#####}`).
* Consumer `P/procurement_planning/services/actuals.py:73-109` `upsert_coverage(allocation=...)` stores a Link to `Plan Source Allocation` (`proceeding_coverage.json` `allocation` Link), i.e. expects the document name. Planning's own test supplies the name: `P/procurement_planning/tests/test_plan_progress.py:134-140` `frappe.db.get_value("Plan Source Allocation", {...}, "name")`.
* Rule: PLN v1_29 §7.3 row "TPR/TPUB invitation actual ... exact proceeding/REQ/Plan/allocation coverage" and §4.8 ProceedingCoverage; Planning's progress screen builds its proceeding rows only from `Proceeding Coverage` (`progress_read.py:176-200`).
* Effect (inferred, not run): every Tender publication delivers its date but an empty coverage list, so Planning's U14 "procurement progress" shows no proceeding rows/stage for the item. No Tenders test covers coverage (`grep -n coverage tenders/tests` shows only home-provider unrelated hits).
* Repro: publish a Tender; `frappe.get_all("Proceeding Coverage", filters={"proceeding_id": tender_reference})` is empty.

### F-15 (Low-Medium, CODE DEFECT): Evaluation's funding read runs as the session user and swallows every failure

* `P/bid_evaluation/services/funding.py:34-43` calls `kentender_budget.services.budget_downstream_contracts.get_funding_lineage(...)` inside `try ... except Exception: ... return None` ("no funding fact is shown"). `get_funding_lineage` calls `require_budget_version_read_scope(...)` (`budget_downstream_contracts.py:61`) which runs `frappe.has_permission(..., user=frappe.session.user, throw=True)` (`budget_authorization.py:180-184`); Budget read roles are Budget governance roles, Auditor, AO and HOPF only (`budget_authorization.py:57-71`). Planning's equivalent reads run under `_system_principal()` (`budget_gateway.py:36-58`).
* Rule: EVL v0_5 §4.4 / funding beside the comparison; `funding.py` docstring "When that read is unavailable no funding fact is shown; nothing is guessed". A committee actor without a Budget role gets "no funding fact" with only a log entry, indistinguishable from "no reservations". Not verified at runtime.

### F-16 (Low, SPEC-ACCEPTED GAP): Award -> Contracting has no production consumer

* `P/hooks.py:173` `kt_award_contracting_receivers = ["...award.test_services.contracting_receiver.receiver"]`; `P/award/test_services/contracting_receiver.py:49-50` returns a receiver only when `simulation.enabled()`; `P/contract_management/` contains empty packages. `P/award/services/contracting.py:1-14` documents it. Produced `AwardDecisionRecorded v1`, package and update have no real consumer. Listed so Phase 3 can distinguish "documented absent" from "unexamined".

### F-17 (Low, CODE DEFECT): the capture digest and the current-state digest disagree when the Plan has a line that is not Active in Budget

* Capture rows for unknown lines carry `"planned": ""` (`P/procurement_planning/services/financial_basis.py:50`), and `digest(..., operative_only=True)` filters `flt(r["planned"]) > 0` (`:62`) so they are excluded; `current_digest` builds the same rows with `"planned": money.money_text(totals.get(key, 0))` (`:140`) so they are included. Same contract, two digests; the basis reads as perpetually stale in that case. Also `_rows_from_decision_statement` defaults `"eligible": bool(line.get("eligible", True))` (`:45`) (permissive default; Budget always sends it today).

### F-18 (Low, produced hand-off with no consumer / unconsumed payload)

* No consumer, never acknowledged: `ProcurementRequisitionAuthorised.v1.4`, `...Revoked.v1`, `ProcurementRequisitionCorrectionRequested`, `PlanItemCorrectionOutcomeReceived` (`P/procurement_requisitions/services/events.py:19-24`; `events.acknowledge` has no caller; only read for history at `read.py:920`). `EVENT_WITHDRAWN` is declared and registered but never published (`grep events.publish` shows no withdraw call). The authorised event body is only `{"handoff", "handoff_digest"}` (`authorise.py:145`), not the "exact handoff" REQ v1_14 §9.2 implies; Tenders consumes by reading the handoff table instead.
* NDS: `DepartmentalNeedSuperseded.v1` and `...Withdrawn.v1` have no subscriber; `consume_events`/`acknowledge` (`events.py:184-250`) have no caller in Planning (events stay `Pending` forever).
* Tenders -> BDS: Bid Submission uses only the event's `subject_id` (`close.py:237` `tenders_handoff=cstr(event.subject_id)`); the whole `Tender Submission Handoff` payload (`submission_close.py:36-60`) is never read by BDS, which reads deadline from the Tender root (`close.py:57-58`). The Tenders docstring still says the consumer "does not exist in this release" (`submission_close.py:11-13`).

### F-19 (Low, SPEC GAP): inconsistent definition of a "published surface" for cross-app imports

* Planning's test treats `kentender_budget.api.budget_api` and `kentender_strategy.services.strategy_consumer` as the only allowed prefixes (`P/procurement_planning/tests/test_gateway_contracts.py:81-93`). REQ imports Budget internals `services.budget_check_reserve_contracts`, `services.budget_commitment_contracts`, `services.budget_contracts` (`P/procurement_requisitions/services/funding_gateway.py:46,53,60,70`) and EVL imports `services.budget_downstream_contracts` (`P/bid_evaluation/services/funding.py:34`); REQ also imports Planning's `_system_principal` private helper (`funding_gateway.py:76-79`). `budget_api` exposes the same functions as whitelisted wrappers. AGENTS.md §2 says cross-app access uses the owner's "published service or API"; no document names which modules are published.
* Also `funding_gateway._call` catches only `frappe.ValidationError` (`:35`) while Budget raises `PermissionError` for `BUDGET_FINANCE_TASK_DENIED` (`budget_check_reserve_contracts.py:122-126`) and authorises `frappe.session.user` (`:118`) although `authorise_requisition(user=...)` resolves the actor from its own argument (`authorise.py:82`): a call with `user` different from the session produces an unmapped `PermissionError`, not `REQ_OWNER_VALIDATION_UNAVAILABLE`.

### F-20 (Low, informational): EVL/BOP comment contradicts the producer

* `P/bid_evaluation/services/sources.py:7-9` "the opening hand-off does not carry it, C23" while `P/bid_opening/services/completion.py:36-38` writes `bid_definition_id`, `definition_version`, `definition_digest` per package (from `cstr(sealed.get(...))`, silent blank if the envelope is missing). EVL ignores those fields and records the definition of the first package for the whole case (`intake.py:95` `first_definition = loaded[0][1]["definition"]`).

### F-21 (Low): supplier-provider failures become silent empties in Award's gateway

* `P/bid_submission/services/award_gateway.py` `organisation_users` returns `[]`, `organisations_of` returns `[]`, `signatory`/`acting_for` return `None` on any `Exception` (`:68-100`). Fails closed for authority, but the notice audience is silently empty during a provider outage. Also `P/bid_submission/services/snapshot.py:_pick` blanks missing Account facts (`.get(k) or ""`).

### F-22 (Low): REQ/TPR money and currency handling at the boundary

* REQ hard-codes `CURRENCY = "KES"`, scale 2 (`precision.py:20-23`) and writes `"currency": precision.CURRENCY` (`handoff.py:68`) even though Budget returns the reservation's own `currency` (`budget_check_reserve_contracts.py:447`) which REQ ignores. REQ §5.14 "Basis snapshot ... retains BUD currency/precision evidence".
* Tenders reads REQ's decimal strings through `float`: `P/tenders/services/snapshot.py:109-113` `float(sum(float(row.get("requested_value") or 0) ...))` and `compatibility.py:120` `float(row.get("quantity") ...)`; the result feeds `authorised_value` into EVL (`evaluation_seam.py:212`). REQ v1_14 §5.14 forbids `flt()`/float on owner boundaries.

## 4. Contract-test presence, both sides

| Pair | Producer shape pinned | Consumer reads pinned fixture | Note |
|---|---|---|---|
| NDS event -> PLN | yes (`departmental_needs/tests/test_departmental_needs_events.py:149-161`, `..._contracts.py:342-363`) | PLN fixtures call the real producer (`procurement_planning/tests/fixtures.py`) | both sides; F-5/F-10 untested |
| PLN dispositions -> NDS | partial | partial | enum not checked against spec (F-7) |
| PLN -> BUD gateways | n/a (Budget side) | signatures only (`procurement_planning/tests/test_gateway_contracts.py`); `validate_plan_affordability_for_decision`, `receive/withdraw_budget_revision_request` parameters and return keys not pinned | one side, weak |
| PLN projection -> REQ | `procurement_planning/tests/test_plan_requisition*.py` | REQ tests use real projection | both sides |
| REQ -> BUD | n/a | `procurement_requisitions/tests/test_gateway_contracts.py:42-` signatures | consumer side only |
| REQ handoff -> TPR | none that compares keys to consumer | substring pins + hand-written fixture (F-13) | one side, weak |
| TPR -> PLN milestone | signature only (`tenders/tests/test_gateway_contracts.py:64-69`) | none for coverage | F-14 undetected |
| BDS -> BOP -> EVL -> AWD | each module's own tests build the real producer in shared worlds | yes | no finding |
| suppliers provider | yes (`kentender_suppliers/.../test_account_read_and_contract.py:148`) | BDS tests use the provider | both sides |
| Producer version bumps | handoff 1.3 -> 1.4 bumped with no cutover test | `test_gateway_contracts.py` asserts `handoff.HANDOFF_VERSION == "1.4"` | F-4 |

## 5. Checked and clean

* PLN projection `GetRequisitionEligiblePlanItem.v2` (`plan_requisition.py` return dict) vs every key REQ reads (`projection.get(...)` list, 38 keys in `P/procurement_requisitions/services/`): all present; per-source keys `plan_item_line_id`, `source_line_id`, `source_origin`, `dpp_entry`, `need_revision`, `budget_line`, `remaining_quantity/amount`, `approved_quantity`, `allocated_amount` match consumers (`handoff.py:41-60`, `authorise.py:60-70`).
* `AuthoriseRequisitionDrawdown` request/response keys (`plan_source_allocation_id`, `quantity`, `amount` -> `drawdowns[].plan_source_allocation_id/drawdown_reference/record_version`) and error mapping (`PLN_ALLOWANCE_EXCEEDED`, `PLN_ITEM_AUTHORISATION_HELD`, `PLN_ITEM_SCOPE_LOCKED`, `PLN_MONEY_PRECISION_INVALID`) match `eligibility_gateway.py:25-45`. REQ stores money/quantity as strings (`requisition_drawdown_line.json`) so Planning's float refusal (`plan_requisition.py:440-446`) is not triggered.
* BUD `check_funding` returns `token`, `all_sufficient`, `lines[].sufficient`; `reserve_funding` returns `reservations[].reservation_id/reservation_code/drawdown_line_id`, as REQ reads (`authorise.py:104-116`, `handoff.py:46-48`). Amounts are exact strings (`_exact_money`). Budget error titles `BUDGET_INSUFFICIENT_FUNDS`, `BUDGET_MONEY_PRECISION_INVALID` match REQ's mapping (`funding_gateway.py:35-44`). `reserve_funding` is idempotent per correlation id (`budget_check_reserve_contracts.py:314`).
* Budget `BUD_BASIS_STALE` / `BUD_BASIS_UNAVAILABLE` titles (`budget_line_contracts.py:605-630`) match Planning's reader (`budget_gateway.py:150-158`).
* `PlanItemCorrectionOutcome.v1`: producer (`outcome_event.py:61-107`) emits all 13 keys REQ requires (`correction.py:34-40`), `schema_version=1`, `producer="Procurement Planning"`, dedupe by event id + digest (`correction.py:81-86`), hook name identical on both sides.
* `BudgetRevisionRequestOutcome.v1`: keys `planning_request_id`, `outcome`, `sequence`, `decided_at` (UTC ISO), `decided_by(_name)`, `reason`, `resulting_line_version`, `resulting_approved_amount` all read by `budget_revision.py:185-210`; hook `kt_budget_revision_outcome_consumers` defined (`hooks.py:731`) and read via `CONSUMERS_HOOK`; hourly retry registered (`kentender_budget/hooks.py:111-114`); `_site_instant` converts UTC to site time per AGENTS.md §4.4.
* NDS disposition/usage/intake hand-offs conform to AGENTS.md §4.4 (in-process calls pass site time; serialized event body uses `to_utc_iso`, `events.py:104-107`).
* Planning->NDS `project_need_planning_intake` keys and enum strings (`No update needed`, `Update required`, `After current submission`) match on both sides (`needs_intake.py:287-289`, `usage.py:418-421`).
* REQ -> TPR consumption is idempotent and race-safe: `record_handoff_consumption` replays by key, locks handoff and root, and rejects a different Tender (`handoff.py:101-136`); revocation takes the same lock (`authorise.py:183-186`). TPR rolls back with the Tender creation in `envelope.atomic`.
* Tenders -> STD -> BDS: `DefinitionModel` reads `definition_digest`, `sections[].section_id/label/purpose/order/groups[]`, `groups[].group_key/rule_id/composition_id/published_facts/response_ids/repetition`, `response_rows[].response_id/field/required/visibility/validation/evidence/sequence`; the compiler emits exactly these (`std_templates/compiler/definition.py:30-70,255-300`), including the `per_arrangement_member`/`per_entity` repetition literals.
* TPR -> BDS events: `TenderSubmissionPeriodEnded` / consumer `bid-submission` and `TenderOpenForSubmission` / `bidder-service` identical in producer and consumer (`submission_close.py:27-28`, `close.py:46-47`); one close per Tender (idempotent `close_bid_submission`).
* BDS -> BOP -> EVL: manifest keys (`closed_box.custody_inventory`, `envelopes[].envelope_id/status/accepted_at/package_digest/...`) read exactly as produced (`close.py:140-205` vs `custody.py:26-33`, `opening_gateway.py`, `ceremony.py`); Evaluation Handoff `packages[]` keys read in `intake.py`; digest recomputation modes documented and consistent (`evaluation_seam.py:36-47`).
* EVL -> AWD: hook names and kwargs, `delivered_report` keys (`outcome`, `recommended`, `comparison`, `signatures`, `content_digest`, `digest_verified`, `delivered_at`, `tender`, `tender_reference`, ...) all read by `award/services/intake.py` / `sources.py`.
* Hook registry: every `kt_*` hook that a module declares has a consumer in code; `kt_evaluation_report_consumers_failed` is consumed through `f"{hook}_failed"` (`award_seam.py:43`).
* Supplier account provider: `FUNCTIONS` in `kentender_core/.../supplier_account_contract.py` is implemented by `kentender_suppliers/.../provider.py`; `business_profile` keys cover BDS's `PROFILE_FACTS` plus `year_of_registration`.
* Dependency direction: no non-seed import from `kentender_core` into procurement/budget/strategy; NDS reads no Planning table; no direct writes into another module's tables found in any producer examined.
* Idempotency keys on replay: REQ `record_handoff_consumption` (same Tender returns `already_consumed`), Planning `record_tender_milestone_actual` (dedupe on `(producer, event_id)`, `schedule.py:184`), Tenders milestone event id `<publication>:invitation` (`planning_gateway.py:36`), Budget revision request (digest conflict `BUDGET_IDEMPOTENCY_CONFLICT`), NDS events (unique `event_id` + per-Need sequence).

## 6. Limits of this sweep

Not examined: contract sections of NDS/PLN/REQ that are internal to one module; the contents of every Vue/JS consumer; STD template asset content; `kentender_stores`/`kentender_assets`/`kentender_contracts` (no producer/consumer code exists for them in this repo). All runtime effects named above are inferred from source and were not reproduced on a site.
