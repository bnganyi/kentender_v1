# Document corrections owed (approved documents are changed only through the document-change protocol)

Merged 07 Oct 2026 from audit/progress/*.md.

## INT-A

None.

## INT-B

None.

## REGRESS

- D-2 (PLN): add RG-01 (Annual Plan publication D4) to the triggers.
- RG-35: owner to say whether TM2 mentions in `docs/` and `archive/` and the sidebar label "Tender Management" count against decision D1.
- RG-28: BUD should record the float-JSON deviation and the 12 versus 18 digit decision.

## WP1.1

- NDS v1.16 §8.2 lists `project_need_planning_usage`, `_disposition`, `_intake` as commands "called through the endpoint"; they are now in-process service seams only (NDS §7.5 "registered Planning producer only"). Next NDS version should say so and drop "or administrative principal" (AUTH §8).
- NDS §9: add an invalid-request code (or say which existing code an unknown field uses).
- AUTH-ADR-001 §5.5 could state that no whitelisted function takes an acting-user parameter (now enforced by the repo-wide guard test).

## WP1.2

- BUD §7 / BUD-BR-015 / §12.6: record the mechanism (a minted `ServiceCaller` validated against a (principal, action) allow-list; refusal `BUDGET_DOWNSTREAM_FORBIDDEN`), the Requisitions/Contract matrix, that check/reserve are Requisitions-only, and that revalidation is Budget-internal.
- BUD §13 error vocabulary: add `BUDGET_RELEASE_EXCEEDS_REMAINDER`; decide the code for "missing event/key".
- BUD §8.3: token binds actor, requisition and line Budget Versions (implemented).
- docs/mvp-1 teardown inventories still list `dia_budget_control.py` (historical).

## WP1.3

- Docs under `docs/mvp-1-r1` that still mention TM2 (not edited): 26 files, notably `11_tenders/TPR-CHG-001_FOLLOW_UPS.md` (FU-08, "inverted Administrator authority" debt now closed by deletion), `12_bid_submission/reconciliation/legacy_inventory.md` §4 (the OD-F TM2 clean-up is now done; this was the owner-endorsed plan I followed), `12_bid_submission/BDS-CHG-001*` trackers/plans, `18_home_page/reconciliation/hook_inventory.md`, `17_oversight_visibility/reconciliation/baseline_audit.md`, and the plans for EVL/AWD/ANL/PLN.
- Outside `docs/mvp-1-r1`: I deleted the wholly-TM2 documents (`docs/prompts/tender management/`, `docs/tender-management-v2/`, `docs/audit/module_implementation_catalog/06_tender_management.md`, `docs/audit/seed_data_bundle/fixtures/tm2_seed_works_open_tender.json`). 49 other superseded prompt packs / audits mention TM2 in passing (list below); recommend moving them to `archive/` rather than editing.

- docs/audit/module_implementation_catalog/04_procurement_planning.md
- docs/audit/module_implementation_catalog/05_std_admin.md
- docs/audit/module_implementation_catalog/README.md
- docs/audit/module_implementation_catalog/doctypes_inventory.csv
- docs/audit/planning_tender_handoff_2026-05-03/AUDIT_SNAPSHOT.md
- docs/audit/planning_tender_handoff_2026-05-03/officer_tender_config.py
- docs/audit/seed_data_bundle/README.md
- docs/audit/seed_data_bundle/frozen/bench_execute_catalog.json
- docs/audit/seed_data_bundle/frozen/stdinst_1400_stable_ids.json
- docs/audit/seed_data_bundle/packages/ke-ppra-works-building-2022-04-poc/evidence/acceptance_pack.md
- docs/mvp-1/04_planning/04_Procurement_Planning_MVP1_Implementation_Tracker.md
- docs/mvp-1/04_planning/05_Procurement_Planning_MVP1_Gap_Rectification_Tracker.md
- docs/procurement-home/DELIVERY_REPORT.md
- docs/prompts/0. usability handoff/1. procurement_lifecycle_usability_handoff_rectification_pack.md
- docs/prompts/0. usability handoff/2. procurement_lifecycle_usability_handoff_rectification_cursor_implementation_pack.md
- docs/prompts/0. usability handoff/3. procurement_lifecycle_works_master_seed_data_specification.md
- docs/prompts/0. usability handoff/4. procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md
- docs/prompts/architecture/Kentender Workbench Typography v1.0.md
- docs/prompts/planning-to-tender-handoff/2. planning_to_tender_handoff_specification.md
- docs/prompts/planning-to-tender-handoff/3. works_seed_scenario_refactor_specification.md
- docs/prompts/planning-to-tender-handoff/4. works_tender_stage_hardening_specification.md
- docs/prompts/planning-to-tender-handoff/5. works_tender_stage_hardening_cursor_implementation_pack.md
- docs/prompts/planning-to-tender-handoff/IMPLEMENTATION_TRACKER.md
- docs/prompts/procurement planning v2/0.1. procurement_planning_v_2_baseline_audit_gap_analysis_and_revamp_pre_prd.md
- docs/prompts/procurement planning v2/0.2. procurement_planning_v_2_full_prd.md
- docs/prompts/procurement planning v2/1. procurement_planning_v_2_cursor_implementation_control_protocol.md
- docs/prompts/procurement planning v2/2. procurement_planning_v_2_cursor_implementation_pack.md
- docs/prompts/procurement planning v2/3.1 procurement_planning_v_2_implementation_tracker.md
- docs/prompts/procurement planning v2/4. procurement_planning_v_2_smoke_contract.md
- docs/prompts/procurement planning v2/5. procurement_planning_v_2_works_seed_data_specification.md
- docs/prompts/procurement planning v2/7. procurement_planning_v_2_governance_state_and_approval_model.md
- docs/prompts/procurement planning v2/8. procurement_planning_v_2_strict_domain_model.md
- docs/prompts/procurement planning v2/9. procurement_planning_v_2_roles_and_permissions_matrix.md
- docs/prompts/procurement planning v2/P0-repository-inventory.md
- docs/prompts/procurement planning v2/reset/2.procurement_planning_v_2_p_5_ux_reset_implementation_tracker.md
- "docs/prompts/procurement planning v3/3. Procurement Planning v3 \342\200\224 Cursor Implementation Contract and Tracker.md"
- docs/prompts/procurement planning v4/package wizard/PACKAGE_WIZARD_WIRING_TRACKER.md
- docs/prompts/ui refactor/ken_tender_tender_management_ui_refactor_notes.md
- docs/std-engine/BE-00_REPO_AUDIT.md
- docs/std-engine/BE_IMPLEMENTATION_TRACKER.md
- docs/std-engine/IMPORT_WIRING_PLAN.md
- docs/std-prod-impl/IT-STD-Wizard-v3/B-Components/COMPONENTS.md
- docs/std-prod-impl/IT-STD-Wizard/00 Correct Next Sequence After STD Engine.md
- docs/std-prod-impl/IT-STD-Wizard/99 IT_Tender_Wizard_Screen_Ownership_Matrix.md
- docs/std-prod-impl/cursor/README.md
- docs/std-prod-impl/std backend answers.md
- docs/tender-publications/IMPLEMENTATION_TRACKER.md
- docs/tender-publications/README.md
- docs/test-contracts/workspace-pattern-rollout-matrix.md

## WP1.4-1.6

- KTSM registry has no approved document (BDS FU-06); docs/prompts/supplier management/4 and 8 name "Admin" as an actor, which AUTH §8 contradicts.
- STR §9 defines STRATEGY_DOWNSTREAM_FORBIDDEN; now implemented as the title of a PermissionError.

## WP2.1

- STR v1_9 line 161/636 and AUTH-ADR-001 §8 can cite the guard as the enforcement of "append-only; Administrator and System Manager read-only".

## WP2.2-4.5

- STR v1_9 STR-BR-006 / STR-AC-010 / STR-AC-032 can cite the command-only guard as the enforcement of "Active content is immutable" and "every Strategy write goes through the commands".
- STR §4.2 / §12.4: state that "Use until" blank means open-ended for overlap and resolution, and that approval is refused once applicability has ended (now enforced).
- STR §5.1/§6.1/STR-AC-010: define "author" (follow-up 1).

## WP2.3-3.5-3.6-budget

- BUD §4.8 / BUD18-AC-051: record that the editor's JSON numbers are accepted when they are plain decimals of at most 15 significant digits (Follow-up 1), and the 12-integral-digit storage ceiling until the storage decision (Follow-up 2).
- BUD §13: add `BUDGET_CURRENCY_PRECISION_UNSUPPORTED` (missing/disabled/unsupported currency blocks monetary writes), and say that a command with no expected record version is answered `BUDGET_STALE_WRITE`.
- BUD §4.1/§4.8: CurrencyBasis retained on the Budget root is described but not stored (Follow-up 3).
- BUD §6/§9.2: say whether successor creation needs a stamp (Follow-up 4).

## WP2.6-2.8

- AUTH-ADR-001 §4.4 / §8: record which registered responsibilities a technical account may hold (`technical_holder`: Technical Operator, Release Operator, Evaluation Technical Support), and add the rule that an administrator cannot assign a responsibility to themselves (AUD-XC-136 owner decision still open: the code now refuses both).
- AUTH-ADR-001 §15 and REQ v1_14 invariant 12 / TPR §12.3 rule 1 can cite `CommandWriteGuardMixin` as the enforcement; TPR's text about `flags.kt_lifecycle` is out of date.
- AUTH-ADR-001 §11.3 step 9 is done in code; step 11 (remove obsolete reads, clean rows) is open.

## WP3.1-3.3

- BUD v1.12 §4.6/§6: record the Budget Submission Attempt record, the `BUDGET_CLOSED` refusal when approving a successor of a Closed Budget, the (contract, reservation) commitment key, and decide the Close-with-open-successor rule (follow-up 2).
- BUD §13: `BUDGET_SOURCE_OU_REQUIRED` and `BUDGET_CLOSED` as approval outcomes.

## WP3.2-4.3

- REQ-CHG-001 §5.2 should list the "sent for approval by / at" evidence; §7.3 should say whether the preparer or sender may authorise (F2) and what "preparing directly" requires on the Draft path (F1); §7.2 should say whether a hold blocks routing (F3); §6.3 should say how brand wording is excused where a row has no reason column (F4) and how `All items` applies in mixed-category packages (F5).
- REQ §9.2 / §10.2: state that `RecordHandoffConsumption` is an in-process owner call inside Tenders' start commands with no public endpoint, and the published lock order (Requisition root, then handoff).
- AWD v0.5 §5.4: note that the cancellation guard reads as last committed after the case lock.

## WP3.4-4.1-award

- AWD-CHG-001 v0_5 §6/§7: record owner decision D2 (HOP-only opinion, correspondence and restrictions; AO-only decision) and the Q3 segregation rule once confirmed.
- AWD §5.1/§5.5/AWD-IF-07: state that an unavailable funding read refuses a positive award, issue and delivery with `AWD_STATUS_UNAVAILABLE`, and a shortfall holds with `AWD_ON_HOLD`. §8 has no funding-specific code (the closed set of 13 was kept).
- AWD §5.10: say what counts as "operative authority evidence" for an order recorded by hand (follow-up 3), and that a Funding issue is cleared by Budget's own read.
- AWD §6 says the technical operator retries operations. D2 says "no other roles", so confirm the wording that the technical operator stays outside the business chain.

## WP3.5-2.4-2.5

- PLN v1_29 §5.5.3.1: state the rounding rule of the required amount (XC-132); §4.1 / BUD §4.8: Budget to publish the CurrencyBasis contract incl. precision on the display read.
- NDS v1_16 §4.9 / §9: record that unit/quantity are rechecked at acceptance only when the code does it (Follow-ups 2d); the CFG UOM adapter's precision/whole-number result is the native `must_be_whole_number` only today.
- AUTH-ADR-001 §9 / NDS §6: cite `need_authorization` as the Needs read predicate; NDS §8.2 and §16.1 can cite the command-write guard as the enforcement of "projection written only by the projection command" and "no writable DocType endpoints".

## WP3.6-needs-planning

* NDS v1.16 section 9 and PLN v1.29 section 8: state that an idempotency key is bound to the actor, the command and the payload; the same key from anyone else, for another command or with another payload is `NDS_IDEMPOTENCY_CONFLICT` / `PLN_IDEMPOTENCY_CONFLICT`; a replay is answered only after authorisation (Needs) or only to an actor who still holds the standing recorded with it (Planning); a duplicate that arrives while the first is running waits and returns the original result.
* PLN section 8 error list: `PLN_STALE_WRITE` is no longer used for key reuse.

## WP3.6-req-tenders

* REQ v1.14 section 10 and TPR v0.17 section 11.1: state the order of the envelope (authorise, claim the key, check the version under the row lock, run) and that a key is bound to the actor, the command and the payload (`REQ_IDEMPOTENCY_CONFLICT`, `TND_IDEMPOTENCY_CONFLICT` for any other use, never a replay of someone else's result), and that a key that recorded nothing may be reused by the same actor.
* TPR09-AC-007 / AC-025: the concurrent same-key StartTender and the stale-version refusal under a snapshot race are now covered by real two-connection tests; the acceptance tables can cite them.

## WP3.6-residual

* STR v1.9 §8.2 says the idempotency identity is "a stable command idempotency identity under KT-STD §11"; it should now also say that a key is bound to the actor, the command and the payload and that the conflict code is `STRATEGY_IDEMPOTENCY_CONFLICT` (plus `STRATEGY_IDEMPOTENCY_REQUIRED`, `STRATEGY_VERSION_REQUIRED`) in the Strategy error list.
* EVL v0.4 section 7.2 / AWD v0.5 section 7: add the order of the envelope (authorise, lock, claim, run) and, for Evaluation, the standing rule for replays.

## WP4.2-eval

- EVL v0.5 §3: state whether the secretary must declare/accept confidentiality and whether a conflicted secretary is replaced (AUD-EVL-016).
- EVL v0.5 §3 line 65 / BOP-A17: the symmetric exclusion is now implemented (an Evaluation member cannot be named independent opening member, and vice versa); the documents should say so (AUD-EVL-013).
- EVL v0.5 §4.4 / §5.5: say explicitly that a member finding or committee conclusion cannot resolve an arithmetic discrepancy or missing rule and that a qualified outcome is the only record (AUD-EVL-003/002).
- EVL v0.5 §5.5: delivery retry rechecks as the last signature does; a Finalized-but-undelivered Proceedings record is left as signed history when the report is returned for validity (AUD-EVL-004).

## WP4.4-tenders

- TPR-CHG-001 §5.5(6) / §7.3: define the command that issues a revised deadline inside the same publication package, and its effect on the package digest and prior channel confirmations (F-1).
- TPR-CHG-001 §4.8 / §5.6: state what happens to an addendum still awaiting channel confirmation when the submission period ends (F-2); state that issue and effectiveness are possible only before the submission deadline.
- TPR-CHG-001 §6: define "prepared" for segregation. Implemented as everyone who saved a value or evidence requirement on any Version of the Tender, so the owner should confirm or narrow it.
- TPR-CHG-001 §4.8: a clarification-deadline row's revised value must be a date before the submission deadline; a submission-deadline row's revised value is the revised deadline (implemented that way).

## WP4.6-planning-needs

- NDS v1_16 §4.9 / §7.1: record the actual wire change (quantity as an exact decimal string on `DepartmentalNeedAccepted.v2`, `DepartmentalNeedSuperseded.v1.successor_accepted_payload` and the §8.1 read; replay normalises pre-cutover numeric rows; hash unchanged) as the cutover evidence the document asks for, or decide on a new event version.
- NDS v1_16 §8.2: acceptance recheck is now implemented as unit active, quantity valid for the unit, hash equals the stored digest; error codes `NDS_UNIT_INELIGIBLE`, `NDS_QUANTITY_PRECISION_INVALID`, `NDS_STATE_CONFLICT`.
- PLN v1_29 §6.4: say whether "Withdraw for correction" is a statutory decision for segregation purposes (AUD-PLN-021) and whether `CancelPlanUpdate` counts as authoring; list `SavePlanVersionDetails` and the funding-reuse request explicitly among the Planner-side actions.
