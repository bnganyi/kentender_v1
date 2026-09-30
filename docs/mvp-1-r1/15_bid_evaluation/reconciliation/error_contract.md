# EVL-CHG-001 v0.4: error contract

| Control | Value |
|---|---|
| Version | 0.4-errors.1 |
| Date | 30 September 2026 |
| Source | EVL v0.4 §8, copied verbatim by `tools/build_contracts.py` |

**Counts:** 15 blocking codes and 2 nonblocking conditions. `bid_evaluation/services/errors.py` must hold exactly these codes and messages, and `test_evl_errors` compares them with this file.

**Rules** (EVL v0.4 §8 opening paragraph, verbatim): "These are the canonical guard/failure messages. Render the exact message with separate contextual detail (names, dates, reasons and recovery). A next-step sentence may describe the actor’s task; it does not replace or contradict the guard message. Return every applicable guard reason together, with its owner and recovery; do not stack serial blockers. Unaffected work stays available."

## Blocking codes

| Code | Message | Recovery | Source line |
|---|---|---|---|
| `EVL_SOURCE_INCOMPLETE` | Some opened bid information could not be loaded. | System creates one support issue automatically; secretary sees View issue and Try again. Support repairs; reconciliation retries the same intake identity and clears waiting only on success. | EVL v0.4 line 298 |
| `EVL_RULE_UNAVAILABLE` | This requirement needs review because its evaluation rule is unavailable. | Chair: Report issue; retain the issued requirement and other results. | EVL v0.4 line 299 |
| `EVL_MEMBER_INELIGIBLE` | This person cannot serve on this evaluation committee. | AO sees the specific eligibility reason beside the selected person; choose an eligible member. | EVL v0.4 line 300 |
| `EVL_DECLARATION_REQUIRED` | Complete your declaration before viewing bids. | Member: Complete declaration. | EVL v0.4 line 301 |
| `EVL_MEMBERS_ABSENT` | All members of the current eligible committee must be present to record this conclusion. | Chair sees absent names; members Join discussion or chair End discussion without a conclusion. | EVL v0.4 line 302 |
| `EVL_REPORT_INCOMPLETE` | Review the listed issues before sending the report for signing. | Secretary sees every unresolved item and the appointed member who recorded the finding or the chair; Open issue. | EVL v0.4 line 303 |
| `EVL_TARGET_CHANGED` | The report changed. Review the latest version before signing. | Member: Review latest report. | EVL v0.4 line 304 |
| `EVL_SIGNATURE_UNCONFIRMED` | Your signature has not been confirmed. Check its status before trying again. | Member: Check signature status; same shared operation, no duplicate proof. | EVL v0.4 line 305 |
| `EVL_VERSION_CONFLICT` | This record changed while you were working. Refresh it and try again. | Refresh; retain unsent text for comparison, never overwrite newer data. | EVL v0.4 line 306 |
| `EVL_REPLY_CLOSED` | This clarification is closed. Your saved reply has not been sent. | Supplier: Back to bid; show final-disposition, withdrawal or cancellation closure and preserve draft privately; no internal findings are disclosed. | EVL v0.4 line 307 |
| `EVL_SUSPENDED` | Evaluation is paused by the recorded instruction. | Read instruction and named authority; no local Resume button. | EVL v0.4 line 308 |
| `EVL_CANCELLED` | Evaluation ended | Read cancellation notice and retained record. | EVL v0.4 line 309 |
| `EVL_REPORT_DELIVERY_FAILED` | The signed report could not be delivered. | Secretary retries the same delivery; preserve signatures and do not show Report sent. | EVL v0.4 line 310 |
| `EVL_CLARIFICATION_NOTICE_FAILED` | The clarification notice could not be delivered. | Secretary retries the same notice; the request remains available to the supplier. | EVL v0.4 line 311 |
| `EVL_DECISION_STATUS_UNKNOWN` | The later decision could not be checked. | Chair/Head of Procurement: Report issue; correction notice remains available, no blind reopen. | EVL v0.4 line 312 |

## Nonblocking conditions

EVL v0.4 line 314, verbatim:

> Nonblocking conditions use the same server guidance contract: `EVL_REPLY_OVERDUE` — **The reply deadline has passed.** The supplier may send one late reply while the request is open; the committee must record disposition. `EVL_EVALUATION_OVERDUE` — **The evaluation deadline has passed.** Show the authoritative deadline and responsible holder; work and truthful reporting continue. These conditions create no new lifecycle state or automatic rejection.

| Code | Message |
|---|---|
| `EVL_REPLY_OVERDUE` | The reply deadline has passed. |
| `EVL_EVALUATION_OVERDUE` | The evaluation deadline has passed. |

## Proceedings mapping

Proceedings errors reached inside an Evaluation command are shown with Evaluation copy (plan D3 `from_prc`):

| PRC code (PRC v0.9 §8) | Evaluation code shown |
|---|---|
| `PRC_VERSION_CONFLICT` | `EVL_VERSION_CONFLICT` |
| `PRC_TARGET_CHANGED` | `EVL_TARGET_CHANGED` |
| `PRC_PROOF_UNVERIFIED` | `EVL_SIGNATURE_UNCONFIRMED` |
| `PRC_EVIDENCE_INCOMPLETE` (roster presence missing) | `EVL_MEMBERS_ABSENT` |
| `PRC_EVIDENCE_INCOMPLETE` (other) | `EVL_REPORT_INCOMPLETE` |
| `PRC_START_BLOCKED` | `EVL_MEMBERS_ABSENT` when the roster is incomplete, else `EVL_VERSION_CONFLICT` |
| `PRC_MEMBER_REQUIRED` | `EVL_DECLARATION_REQUIRED` for an undeclared member; otherwise the read is Not found |
| `PRC_OWNER_UNAVAILABLE`, `PRC_ALREADY_FINALIZED` | Not reachable from an Evaluation command: Evaluation checks its own state first. If one occurs it is returned as `EVL_VERSION_CONFLICT` and audited. |

Evaluation guards its own state before calling Proceedings, so the PRC wording ("opening record") never reaches an Evaluation screen. The Evaluation profile gets its own PRC wording (plan D4).
