# EVL-CHG-001 v0.4: hand-off register

| Control | Value |
|---|---|
| Version | 0.4-handoff.1 |
| Date | 30 September 2026 |
| Source | EVL v0.4 §7.3, copied verbatim by `tools/build_contracts.py`; the last two columns are this plan's assignments |

**Rules** (EVL v0.4 §7.3, verbatim):

> Cancellation clears all outstanding Evaluation and supplier-reply work without claiming it was performed. A verified final no-bids outcome clears preparation work. Replaced members’ unperformed personal tasks close as replaced, preserving history; current members receive any required fresh tasks.
>
> Notification means in-product task plus a courtesy notice; notice delivery does not prove task completion.
>

**Counts:** 20 rows. Internal rows become My Work items from `bid_evaluation/services/my_work_provider.py` (plan D11). The supplier row is shown in the Bid Submission bid overview and sent as a courtesy email, never a Desk task (plan D11, D14). The support row is a core Support Issue item (plan D12).

| Event | Next holder | Their My Work item | Sender's waiting-on item | Notification | Clears when | Source line | Named test (planned) |
|---|---|---|---|---|---|---|---|
| First in-scope publication / recovery on valid nonempty intake | AO | Appoint evaluation committee for {tender} | Head of Procurement: Waiting for committee appointment | AO | Valid appointment, final no-bids closure or cancellation | EVL v0.4 line 271 | `test_evl_preparation::test_publication_creates_ao_task_once` |
| Same preparation event | Head of Procurement | Assign evaluation secretary for {tender} | AO: Waiting for secretary appointment | Head of Procurement | Valid secretary appointment, final no-bids closure or cancellation | EVL v0.4 line 272 | `test_evl_preparation::test_publication_creates_secretary_task_once` |
| Appointment | Each member | Declare interests for {tender} | AO: Waiting for committee declarations | Members | Personal declaration, valid replacement or verified no-bids closure | EVL v0.4 line 273 | `test_evl_committee::test_appointment_creates_declaration_tasks` |
| Conflict / member unable to serve | AO | Resolve committee appointment for {tender} | Chair: Waiting for committee appointment | AO | Reasoned replacement/appointment resolves eligibility, or verified no-bids closure | EVL v0.4 line 274 | `test_evl_committee::test_conflict_and_unavailability_route_to_ao` |
| Valid intake and member eligible, or member becomes eligible after intake | Each member | Review bids for {tender} | None | Members | Report enters Signing or case cancelled; separate concerns persist | EVL v0.4 line 275 | `test_evl_intake::test_review_tasks_once_member_eligible` |
| Needs-review finding / finding concern | Chair | Resolve evaluation concern for {tender} | Author: Waiting for committee response | Chair | Committed attributed resolved/qualified conclusion, specialised clarification authorisation or verification plan, or durable linked support issue; author-visible response and named next task under §4.3. Opening a form or reading never clears it. | EVL v0.4 line 276 | `test_evl_findings::test_needs_review_creates_one_chair_item` |
| Authorised clarification | Secretary | Send clarification for {supplier} | Chair: Waiting for clarification to be sent | Secretary | Request sent or authorisation withdrawn | EVL v0.4 line 277 | `test_evl_clarification::test_authorised_creates_send_task` |
| Clarification sent | Supplier's authorised users | Reply to clarification for {tender} | Committee: Waiting for {supplier}'s reply | Supplier contact | Reply, final disposition, withdrawal or cancellation; overdue item persists until disposition | EVL v0.4 line 278 | `test_evl_clarification::test_sent_creates_supplier_reply_request` |
| Reply / deadline without reply | Chair / committee | Review clarification outcome for {supplier} | Supplier: Reply received (receipt, not a work item) | Chair/secretary | Recorded disposition; original and reply retained | EVL v0.4 line 279 | `test_evl_clarification::test_reply_or_deadline_creates_outcome_task` |
| Verification plan recorded | Named participants; named lead | Participants: Record verification findings for {tender}; lead: Prepare verification report for {tender} | Chair: Waiting for verification findings | Participants and lead | Participant observation recorded; lead item clears when report frozen or plan superseded | EVL v0.4 line 280 | `test_evl_diligence::test_plan_creates_participant_and_lead_tasks` |
| Verification report frozen | Each named participant | Review and sign verification report for {tender} | Lead: Waiting for verification signatures | Participants | Own current proof, superseded report or cancellation | EVL v0.4 line 281 | `test_evl_diligence::test_frozen_report_creates_participant_sign_tasks` |
| All verification proofs recorded | Chair | Review verification outcome for {tender} | Lead: Waiting for committee conclusion | Chair | Collective conclusion records effect on recommendation | EVL v0.4 line 282 | `test_evl_diligence::test_all_proofs_create_chair_outcome_task` |
| Report frozen | Each member | Review and sign report for {tender} | Secretary: Waiting for committee signatures | Members | Personal signature, superseded report or cancellation | EVL v0.4 line 283 | `test_evl_signing::test_freeze_creates_member_sign_tasks` |
| Report concern / refusal | Chair and secretary | Resolve report concern for {tender} | Member: Waiting for report correction | Chair/secretary | New report or recorded resolution; no implied signature | EVL v0.4 line 284 | `test_evl_signing::test_concern_creates_chair_and_secretary_task` |
| Final delivery | Head of Procurement | Review evaluation report for {tender} | None; committee sees Done | Head of Procurement | Downstream review recorded or report returned/superseded | EVL v0.4 line 285 | `test_evl_signing::test_final_proof_delivers_one_hop_task` |
| Return | Chair/secretary | Correct evaluation report for {tender}: {comment} | Head of Procurement: Waiting for corrected report | Chair/secretary | New report delivered | EVL v0.4 line 286 | `test_evl_correction::test_return_creates_correction_task` |
| Opening supplement before delivery | Chair; any eligible member may record impact | Review opening update for {tender} | None | Chair | Attributed impact committed; material effects create affected review tasks | EVL v0.4 line 287 | `test_evl_correction::test_supplement_before_delivery_shared_chair_item` |
| Opening supplement after delivery | Chair and Head of Procurement, separate items | Chair: Review opening update for {tender}; Head: Review opening update for {tender} | None | Both | Each item clears on its own recorded action under §5.6 | EVL v0.4 line 288 | `test_evl_correction::test_supplement_after_delivery_separate_items` |
| Post-delivery correction notice | Head of Procurement | Review report correction for {tender} | Chair: Waiting for correction review | Head of Procurement | Recorded downstream review or correction/return action | EVL v0.4 line 289 | `test_evl_correction::test_correction_notice_task_keyed_by_source_event` |
| Source/rule/service issue | Named technical support owner | Resolve evaluation issue for {tender} | Reporter: Waiting for technical support | Support | Repair and successful reconciliation; no “mark read” clearance | EVL v0.4 line 290 | `test_evl_intake::test_source_issue_task_clears_on_reconciliation` |
