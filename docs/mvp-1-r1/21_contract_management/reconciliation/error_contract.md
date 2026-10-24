# CM-CHG-001 v0.8: error contract

| Control | Value |
|---|---|
| Version | 0.8-errors.1 |
| Date | 14 October 2026 |
| Source | CM v0.8 §8, copied verbatim by `tools/build_contracts.py` (tracker CM8-002) |

**Count:** 17 codes. `kentender_contracts/services/errors.py` must hold exactly these codes and messages, and `test_cm_errors` compares them with this file.

**Rule** (CM v0.8 §8, verbatim): "No internal tables, hashes or stack traces in business messages. Pending, rejected and unavailable are distinct. Read-only/denied pages follow KT-STD §3A, not a modal or an invitation to obtain unsafe privilege."

| Code | User-visible message | Fix / holder | Source line |
|---|---|---|---|
| CM_SOURCE | The contract details do not match the source record. | HOP reviews source issue; View issue | CM v0.8 line 587 |
| CM_CHANGED | This record has changed. Review the latest version before continuing. | Reload current comparison; retain unsaved text | CM v0.8 line 588 |
| CM_AUTHORITY | You are not authorised to take this action. | Shared access page; current holder where disclosure permits | CM v0.8 line 589 |
| CM_RULE | The applicable requirement has not been confirmed. | HOP/legal owner; View issue | CM v0.8 line 590 |
| CM_HOLD | This action is on hold. | Show specific reason and holder; View issue | CM v0.8 line 591 |
| CM_SIGNING | Signing is unavailable. Your work has been saved. | Technical recovery of original attempt | CM v0.8 line 592 |
| CM_INCOMPLETE | Some required observations are missing. | Inspector; Review missing observations | CM v0.8 line 593 |
| CM_QUANTITY | These quantities do not match the delivery record. | Chair/receiver; View quantity comparison | CM v0.8 line 594 |
| CM_POSTING | The record is signed. The stock update is still pending. | Technical owner; View update status | CM v0.8 line 595 |
| CM_INVOICE | This invoice needs review before certification. | Finance/HOP issue owner; Review differences | CM v0.8 line 596 |
| CM_DUPLICATE | This submission may already be recorded. | View existing submission; Finance reviews ambiguity | CM v0.8 line 597 |
| CM_CLOSURE | The contract still has obligations that prevent close-out. | View remaining obligations; named holder per item | CM v0.8 line 598 |
| CM_FUNDING | The contract funding update needs attention. | HOP/Budget owner; View funding issue; do not ask for new signatures | CM v0.8 line 599 |
| CM_APPOINTMENT | The inspectors are not ready to act on this contract. | AO/HOP/missing declarer; show missing appointment or declarations | CM v0.8 line 600 |
| CM_SEGREGATION | Another authorised person must take this action. | Name eligible capacity without revealing protected assignments | CM v0.8 line 601 |
| CM_RECONCILE | The correction must be reconciled before this action can proceed. | Current Finance/stock/Budget owner; View affected records | CM v0.8 line 602 |
| CM_REPORT | This report is incomplete because a source could not be read. | Daniel; View update status; submission absent | CM v0.8 line 603 |
