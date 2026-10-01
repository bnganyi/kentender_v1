# AWD-CHG-001 v0.4 — control → command map

Tracker AWD4-004; AWD-AC-023. Every visible control on a board maps to exactly one §7 command or read. "Read" controls open retained versions read-only (§11). API endpoint names are in `award/api.py`.

| Control (boards) | §7 command / read | Endpoint |
|---|---|---|
| Open award (D01) | `GetAwardRecord` (navigation) | `get_award` |
| Save draft (D02, V01, V03, V12, V18, V20) | `SaveProfessionalOpinion` | `save_opinion` |
| Sign opinion (D02, V01, V03, V18, V20) | `SignProfessionalOpinion` | `sign_opinion` |
| Return report (D02, V01, V02; X07 Return report) | `ReturnEvaluationReport` | `return_report` |
| Award and notify bidders (D03) | `RecordAwardDecision` outcome Award (+ batch authorisation) | `record_decision` |
| Return for correction (D03; X08) | `RecordAwardDecision` outcome Return for correction | `record_decision` |
| Record no award (D03; X09) | `RecordAwardDecision` outcome No award | `record_decision` |
| Record no award / Return for correction (V23) | `RecordAwardCorrectionDecision` | `record_correction_decision` |
| Record corrected award and notify bidders (V23p) | `RecordAwardCorrectionDecision` Record corrected award + exact batch | `record_correction_decision` |
| Authorise revised notices (V25) | `RecordAwardCorrectionDecision` Authorise revised notices | `record_correction_decision` |
| Request corrected evaluation (V17) | `RecordAwardCorrectionDecision` Request corrected evaluation | `record_correction_decision` |
| View notice (D04, V05, V07, V13, V14, V22) | `GetSupplierAwardNotice` / `GetAwardRecord` notice section (read) | `get_notice`, `get_supplier_notice` |
| Accept award (D04; X01) | `RespondToAward` Accept | `respond` (portal) |
| Decline award (D04; X02) | `RespondToAward` Decline | `respond` (portal) |
| Request explanation (D04, V13, V14; X11 Send request) | `RequestAwardExplanation` | `request_explanation` (portal) |
| Save reply (D07) | `SaveAwardExplanation` | `save_explanation` |
| Send and close (D07) | `SendAwardExplanation` | `send_explanation` |
| View correspondence (D07c) | `GetAwardRecord` correspondence section (read) | `get_award` |
| Correct contact (V05) | `RetryNoticeDelivery` after the contact owner's correction (plan D7; FU-AWD-13) | `correct_contact` |
| View delivery history (V05) | `GetAwardRecord` notices section (read) | `get_award` |
| Retry operation (V16) | `RetryNoticeDelivery` / `DeliverAwardPackage` retry through technical recovery | `retry_operation` |
| View service history (V16) | technical read of the Support Issue (read) | core Support Issue view |
| Record next action (V06, V07; X10 Save) | `RecordAwardIssueDisposition` fixed outcome Request decision review | `record_disposition` |
| Record outcome (V08; X04, X05 Save outcome) | `RecordAwardIssueDisposition` | `record_disposition` |
| Review correction (V09, V21; X06 Save outcome) | `RecordAwardIssueDisposition` | `record_disposition` |
| Record restriction (Outstanding issues; X03 Save restriction) | `RecordExternalAwardRestriction` | `record_restriction` |
| View source issue, View outstanding issue, View restriction (V02, V08, V15, V15s, V24) | `GetAwardRecord` issues section (read) | `get_award` |
| View decision, View notices, View acceptance, View original/prior/corrected decision, View correction, View correction instruction, View cancellation, View history, View opinion, View evaluation report, View notice preview, View response (D05, V04, V06, V09, V11, V12, V17, V19–V25) | `GetAwardRecord` disclosures (read) | `get_award` |
| View award package (D06, V10) | `GetAwardRecord` package section (read) | `get_award` |
| Open Contracting (D06) | navigation to the durable destination (shown only after receipt) | — |
| Back (all dialogs) | closes the dialog; no command | — |
| System: receipt, issue, refresh, delivery | `ReceiveEvaluationReport`, `IssueAwardNotices`, `RefreshAwardEligibility`, `DeliverAwardPackage`, `ReceiveAwardRestriction` | hooks and scheduler |
| Tenders / EVL / Contracting consumers | `GetAwardAuthorityStatus` | `kt_award_authority_status` hook |
