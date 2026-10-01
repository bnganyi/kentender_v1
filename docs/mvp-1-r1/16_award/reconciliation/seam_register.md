# AWD-CHG-001 v0.4 — seam register

Tracker AWD4-006. Each §17.2 counterpart contract → the concrete function built in this repository, or the gap and its follow-up. Award code reads upstream only through `award/services/sources.py` (plan D4); the `real` provider calls the functions below.

| ID | Owner | Built here | Gap / follow-up |
|---|---|---|---|
| AWD-IF-01 | EVL + Award | `bid_evaluation/services/award_seam.py`: `delivered_report`, `take_up`, `return_report`, `corrections_after`; hook `kt_evaluation_report_consumers` called at the end of `signing.deliver`; EVL's `correction.decision_status` reads Award through `tenders.evaluation_seam.award_decision_status` → hook `kt_award_authority_status` | EVL document amendment FU-AWD-01 |
| AWD-IF-02 | Tenders + Award | `tenders/services/award_seam.py`: `tender_facts`, `validity`, `status_events`; hook `kt_tender_cancellation_guards` called by `cancel_tender`; `evaluation_seam.award_decision_status` delegates to `kt_award_authority_status` | Post-close cancellation, suspension and validity-extension events do not exist in Tenders; simulated owner events under the flag. FU-AWD-02 |
| AWD-IF-03 | BDS + Award | `bid_submission/services/award_gateway.py`: `audience`, `notice_contact`, `signatory`, `acting_for` (at the trusted instant) | Contact correction receipts to Award; supplier route in BDS docs. FU-AWD-03 |
| AWD-IF-04 | PRC | none (no PRC change; plan D6) | FU-AWD-04 |
| AWD-IF-05 | Contracting | hook `kt_award_contracting_receivers`; only provider `award/test_services/contracting_receiver.py` (simulation) | FU-AWD-05, FU-AWD-12 |
| AWD-IF-06 | Legal/rules + Trust/notifications | `Award Settings` test profile (simulation); `proceedings.services.signing.attest`; `kt_bds_supplier_message_transports` | FU-AWD-09, FU-AWD-10, FU-AWD-11 |
| AWD-IF-07 | AUTH + Budget | AUTH through `kentender_core.services.authorization` (`people.holds`); Budget read through the frozen report's funding and `bid_evaluation.services.funding` via the EVL seam | Budget contract FU-EVL-06 (inherited) |
