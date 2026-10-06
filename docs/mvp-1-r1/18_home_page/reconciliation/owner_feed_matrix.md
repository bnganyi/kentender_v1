# Owner feed matrix (row HOME6-0001)

Date: 4 October 2026. Read from source and from the approved owner documents; nothing was run. Provider code is in `kentender_procurement/kentender_procurement/` unless stated.

**How to read it.** Home needs, per entry: business title, action text, due, holder, since, reason, completed-action event, scheduled item and destination. "Today" is what the owner's existing My Work provider supplies. "Gap" is what Phase 3 must add by reshaping existing owner data. No gap is filled by adding an owner task, workflow step or stored field (tracker rule 6).

**Home action titles required by the spec** (HOME §10B): Authorise requisition; Prepare professional opinion; Resolve notice delivery; Appoint the evaluation committee; Consider cancellation; Authorise publication; Decide award; Decide whether this requirement is available to Procurement Planning; Respond to clarification; Record cancellation notices and PPRA report; Start opening; Evaluation deadline.

## 1. Provider today

| Owner | Provider | Module label today | Waiting today | Holder / since today | Due today | Title shape today |
|---|---|---|---|---|---|---|
| Strategy | **none** (only `strategy_ui_contracts._my_work_versions()` for its own page, `kentender_strategy/services/strategy_ui_contracts.py:414`) | n/a | no | label only | no | n/a |
| Budget | `kentender_budget/services/budget_my_work_provider.py::my_work_rows` (`budget.approve`, `budget.revision_request`) | "Budget & Funding" | no | no / `received_at` string | `""` | task-style |
| Needs | `departmental_needs/services/my_work_provider.py::my_work_rows` | varies | yes | `ns.holder` and since | `""` | task-style |
| Planning | `procurement_planning/services/my_work_provider.py::my_work_rows` | "Procurement Planning" | yes | yes | `""` | task-style |
| Requisitions | `procurement_requisitions/services/my_work_provider.py::my_work_rows` | "Procurement Requisitions" | **no** (hard-coded `[]`) | no / `received_at` only | `""` | "Decide whether to authorise — {ref}", "Review departmental requisition — {ref}" |
| Tenders | `tenders/services/my_work_provider.py::my_work_rows` | "Tenders" | yes | yes, `ns.holder`, `ns.since` | `""` (line 59) | includes reference ("Waiting for … to reopen Tender {ref}") |
| Bid Opening | `bid_opening/services/my_work_provider.py::my_work_rows` | "Bid Opening" | yes | yes | `""` (line 37) | "Start opening …" with `status: "Upcoming"` |
| Evaluation | `bid_evaluation/services/my_work_provider.py::my_work_rows` | "Bid Evaluation" | yes | **no holder object**; `received_at` only | `""` (line 32) | "Waiting for committee appointment", "Waiting for {bidder}'s reply" |
| Award | `award/services/tasks.py::my_work_rows` (line ~95) | "Award" | **no** (hard-coded `[]`, line 100) | internal item has `holder`; the row drops it | `""` | "{task} for {tender_reference}" |

## 2. Per-owner Home contract

| Owner | Action titles in the owner document | Business title available | Scheduled / deadline source | Completed-action source | Gap for Home |
|---|---|---|---|---|---|
| **TPR v0.17** | §5.11: "Authorise publication of Tender {ref}", "Consider cancellation", "Record cancellation notices and PPRA report", "Respond to clarification", "Waiting for … to decide publication"; §8: block text "Issue an addendum before sending this answer." (`TND_CLARIFICATION_ADDENDUM_REQUIRED`) | Tender title on the record; row titles embed the reference | `ppra_report_due_by`, `candidate_notice_due_by` (§4.10) are recorded facts; no deadline feed | submission and approval events exist as record history; no actor-event read | split title from action; expose due; blocker reason as a row field; completed events; Coming up deadlines |
| **BOP v0.11** | §5 hand-off table: "Start opening for {ref} at {time}" (chair sees Scheduled, `next_step.kind=timed`) | Tender title | **defined**: `next_steps._timed_close`, `_join_answer` return `KIND_SCHEDULED` | Opening ceremony events on the record | Scheduled to Coming up entry with instant; business title; no completed read |
| **EVL v0.5** | §7.1 "Appoint the evaluation committee" (prose); §7.3 register "Appoint evaluation committee for {tender}"; §5.7 evaluation deadline displayed from "authoritative dated rules" | Tender title | `reads.py:101` `evaluation_deadline`, `overdue`; dated rule still missing (FU-EVL-18); one Scheduled answer ("Opening is scheduled for …") | delivery and signing events on the report | holder object; since; the deadline as an owner fact; completed events; wording reconciliation (FU-HOME-03) |
| **AWD v0.5** | §5.9: "Prepare professional opinion", "Resolve notice delivery", "Decide award"; reason "A required notice is not yet confirmed." (§5.9) | Tender title | none beyond "System / scheduled eligibility check" | award decision, opinion signing events on the record | stop dropping `holder`; waiting item; reason as a row field; since; completed events (e.g. "You recorded the award decision") |
| **REQ v1.14** | §7.1, §12.1: "Authorise requisition" (REQ-DES-08); hand-off register §9.1C is only "Purchase ready for requisition" | Requisition title | none | decision rows (`requisition_decision`) | HoPF authorisation item contract missing (FU-HOME-02); waiting; holder/since; completed events |
| **NDS v1.16** | §5.5 headline "Decide whether this requirement is available to Procurement Planning"; §7.6 register "Review need" | Need title | `closes_at` on the fiscal-year flag (§4) | review decisions | wording reconciliation; deadline framing optional |
| **PLN v1.29** | §7.7 register: "Review {department}'s departmental plan", "Sign and submit the annual plan", "Adopt the annual plan" | Plan title | **none by rule** (PLN23-AC-001, §5.5.1B: no scheduled checks or reminders) | plan transitions | no Scheduled items; reshape rows only |
| **BUD v1.12** | none (native Role tasks; no Budget-owned Finance task) | Budget title | none | approval records | no Scheduled items; waiting absent; title/action split |
| **STR v1.9** | none (My work tab selects existing tasks; no hand-off register) | Plan title | none (no scheduled activation) | approval records | **new provider** needed; nothing scheduled |

## 3. Records you oversee

No cross-record projection exists. Per-Tender summaries exist behind the `kt_tender_stage_summaries` hook (`tenders/services/stage_summary.py::summary`, with `outstanding`; Opening, Evaluation and Award providers `…/services/stage_summary.py::for_tender`). Read grants for Strategy, Budget, Needs and Requisitions are scope helpers (`kentender_budget/services/budget_read_scope.py`, `strategy_authorization.py`, NDS and REQ permissions), not feeds. OVS itself is not marked implemented (its tracker, rule 14); its screens' gate is open. Phase 3A reuses the stage summaries read-only; HOME-AC-07 stays blocked.

## 4. Spec rows that need a source before they can be built

| Spec row | Source needed | Status |
|---|---|---|
| "Authorise requisition" (H10) | REQ HoPF authorisation item | provider has "Decide whether to authorise — {ref}"; reword by title/action split, FU-HOME-02 |
| "Appoint the evaluation committee" (H12) | EVL appointment row | exists as "Waiting for committee appointment" for the waiting side; assigned side to confirm in Phase 3A |
| "Consider cancellation", "Authorise publication" (H12) | TPR §5.11 hand-offs | exist; reference embedded in title |
| "Decide award" (H12) | AWD decision task | exists |
| "Respond to clarification" with blocked reason | TPR §8 guard | guard exists; no row reason field |
| Coming up: "Start opening" | BOP Scheduled | exists |
| Coming up: "Evaluation deadline" | EVL `evaluation_deadline` | exists on read; dated rule missing |
| Recently completed actions (all rows) | each owner's own decision rows (decided 4 Oct 2026, HOME6-0307) | Audit Event and Business Action rejected (FU-HOME-13); no owner source today for Strategy and Budget |
