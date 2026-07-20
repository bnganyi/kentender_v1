# 07 — Wizard Mapping and Gap Register

## Wizard mapping

| Wizard step | NSSF source | Mapped data | Status |
| --- | --- | --- | --- |
| CFG-01 Tender Profile | Cover, invitation, TDS identity | PE, tender ref, contract name, method, category, contact. | Ready |
| CFG-02 Tender Data Sheet | TDS rows | Deadlines, currency, validity, alternatives, JV limit, clarification, submission/opening, security instrument. | Needs instrument and electronic policy controls |
| CFG-03 IT Requirements | Section VII and VIII | Module summaries plus 190 detailed compliance rows. | Needs bulk import/review |
| CFG-04 Implementation Schedule | Scope, implementation phases, schedule, M/N/S/T/U requirements | Two-phase implementation, 24-month cap, training/testing/acceptance milestones. | Ready with phased-mode support |
| CFG-05 System Inventory & Bidder Background | Background/objectives/context | NSSF scheme context, objectives, expected outcomes, task context. | Needs disclosure status per item |
| CFG-06 Price Schedule | Section IX/X | Schedule requirements and 22 price lines. | Needs structured e-price form |
| CFG-07 Evaluation Setup | Section III | Preliminary, qualification, 100-point technical scoring, 75 pass mark, financial evaluation. | Ready |
| CFG-08 Forms & Evidence | Section IV plus evidence columns | Forms, declarations, uploads, professional indemnity evidence. | Needs e-form implementation |
| CFG-09 Contract Values | SCC and GCC-dependent values | Performance security, payment, warranty, SLA, escrow, subcontracting. | Ready with contract carry-forward |

## Gap register

| Gap | Severity | Source evidence | Required action |
| --- | --- | --- | --- |
| Locked ITT/GCC rendering | Critical | Preview must use official PPRA IT STD text, not NSSF shortened text. | Build STD clause library/render manifest before treating preview as legally complete. |
| Large requirement matrix import | Critical | NSSF has 190 Section VIII compliance rows. | Implement bulk import, review, grouping, and approval workflow. |
| Electronic-only contradiction | High | NSSF source says electronic tenders are not permitted. | Preserve source fact; apply KenTender electronic-only policy override. |
| Professional indemnity instrument | High | NSSF requires professional indemnity of KES 500,000. | Add governed security/evidence instrument model. |
| Vendor/platform specificity | High | Microsoft Dynamics 365 / Azure specificity appears throughout. | Add proprietary/vendor-specificity review flag. |
| TDS/SCC mixing | High | Performance security, payments, warranty appear in TDS table. | Normalize contract terms into CFG-09. |
| Price schedule normalization | High | 22 module/cloud/support/licensing lines. | Implement structured price schedule with calculated totals and VAT. |
| Contract carry-forward | High | SCC includes payment, SLA, escrow, warranty, subcontracting, security. | Generate contract carry-forward bundle from CFG-09. |
| Forms and e-declarations | Medium | Forms are paper-style with signatures/blanks. | Transform into e-forms while preserving legal declarations. |
| System inventory/background split | Medium | NSSF has rich background and objectives, not classic inventory tables. | Allow CFG-05 bidder-facing background plus inventory/N/A governance. |

## Decision

This fixture is suitable for Cursor implementation only if it is loaded together with the official PPRA IT STD package. It should not be used to create a standalone generated tender from NSSF text alone.
