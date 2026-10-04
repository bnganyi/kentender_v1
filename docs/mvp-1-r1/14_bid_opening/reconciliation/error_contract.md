# BOP-CHG-001 v0.10: error contract

| Control | Value |
|---|---|
| Version | 0.10-errors.1 |
| Date | 29 September 2026 |
| Source | BOP-CHG-001 v0.10 §8 and §7.1 "Product vocabulary"; PRC-CHG-001 v0.9 §8 |
| Method | Rows copied verbatim by script from both spec tables; the code is `bid_opening/services/errors.py` and `proceedings/services/errors.py`, checked by `test_bop_gateways::TestErrorContract` and `test_prc_access::TestErrorContract` |

## 1. Bid Opening (BOP-CHG-001 v0.10 §8), verbatim

| Code | User message (verbatim) | In-product recovery (verbatim) | Source line |
|---|---|---|---|
| BOP_DEADLINE_NOT_REACHED | **Bids can be opened after submissions close at 12 Jun 2027, 11:00 EAT.** | Wait for system close; no manual override. | BOP v0.10 line 207 |
| BOP_CLOSE_MANIFEST_UNAVAILABLE | **We can’t confirm the bids received at the deadline yet. Opening cannot start.** | Opening access support checks the close record; the chair sees **View problem details** and a status update. | BOP v0.10 line 208 |
| BOP_COMMITTEE_INCOMPLETE | **Appoint at least three opening committee members before starting.** | AO appointment view. | BOP v0.10 line 209 |
| BOP_INDEPENDENT_MEMBER_REQUIRED | **Appoint a committee member who was not involved in processing this Tender and will not evaluate it.** | AO corrects appointment. | BOP v0.10 line 210 |
| BOP_MEMBER_ABSENT | Before Start: **Opening cannot start because [name] has not joined.** After Start: **Opening is paused because [name] is not present.** | Use the member’s full name in both message and button; show **Notify [name]** before Start or rejoin/replace route after Start. | BOP v0.10 line 211 |
| BOP_OPENING_PROFILE_UNAVAILABLE | **Bid opening isn’t available yet.** | Assign the issue to **Opening access support**; **View problem details** opens its incident, assigned holder and status. Show **Opening access support has been told.** only after the notification is committed; on delivery failure show **Support could not be notified. Try again.** with **Notify support** to retry the same incident notification, without creating another incident. Support coordinates any legal or configuration resolution; no chair override. | BOP v0.10 line 212 |
| BOP_CREDENTIAL_UNAVAILABLE | Before Start: **Opening access is not ready yet.** After Start: **Opening is paused because secure access is unavailable.** | Name Opening access support and show **View problem details**; no member proxy action. | BOP v0.10 line 213 |
| BOP_PACKAGE_MISMATCH | **Opening is paused while Opening access support checks this bid against the submissions received at the deadline.** | Chair and technical custodian investigate without substitution. | BOP v0.10 line 214 |
| BOP_PACKAGE_UNREADABLE | **This bid could not be opened. Opening access support is checking it; you can retry when they resolve it.** | Opening access support records the issue and resolution; chair sees **View problem details**, then **Retry opening** when enabled. No disqualification. | BOP v0.10 line 215 |
| BOP_READOUT_INCOMPLETE | **Read out and record every opened bid before ending the opening.** | Complete missing exact row(s). | BOP v0.10 line 216 |
| BOP_ATTESTATION_MISSING | **The opening record still needs signatures from the appointed members.** | Named member acts on the latest exact targets through the profile-specific route. The shared support method defines the signing and initial interactions; this integration condition is not user-facing copy. | BOP v0.10 line 217 |
| BOP_REGISTER_NOT_READY | **The opening register is still being prepared. You can check its status here.** | Bidder sees truthful request state. | BOP v0.10 line 218 |
| BOP_VERSION_CONFLICT | **Someone updated this opening record. Refresh the page before continuing.** | No partial effect. | BOP v0.10 line 219 |

In code, `[name]` and the deadline are template facts (`{name}`, `{deadline}`); `BOP_MEMBER_ABSENT` and `BOP_CREDENTIAL_UNAVAILABLE` use their after-Start sentence when the ceremony has started.

## 2. Proceedings (PRC-CHG-001 v0.9 §8), verbatim

| Code | User-visible message (verbatim) | Result and recovery owner (verbatim) | Source line |
|---|---|---|---|
| `PRC_OWNER_UNAVAILABLE` | **This opening record is not available.** | No disclosure; Bid Opening repairs/authorizes reference. | PRC v0.9 line 137 |
| `PRC_START_BLOCKED` | **The opening session cannot start yet. Review the opening requirement shown here.** | Owner supplies specific blocker and in-product fix in its next-step contract. | PRC v0.9 line 138 |
| `PRC_MEMBER_REQUIRED` | **You are not an appointed member for this opening.** | No attestation; accounting officer/Bid Opening manages appointment. | PRC v0.9 line 139 |
| `PRC_TARGET_CHANGED` | **The opening record changed. Review the latest version before signing.** | No stale proof; member reviews new frozen version. | PRC v0.9 line 140 |
| `PRC_PROOF_UNVERIFIED` | **We could not verify your signature. Follow the steps shown here.** | No completion; the shared support method supplies the precise recovery interaction. This integration requirement is not user-facing copy. | PRC v0.9 line 141 |
| `PRC_EVIDENCE_INCOMPLETE` | **Some opening details are still missing. Review the items shown here.** | No finalization; owner supplies all missing facts and holders. | PRC v0.9 line 142 |
| `PRC_VERSION_CONFLICT` | **This record changed while you were working. Refresh it and try again.** | No partial effect. | PRC v0.9 line 143 |
| `PRC_ALREADY_FINALIZED` | **This record is final. Add a correction if a fact needs to change.** | Original immutable; owner-authorized supplement route. In BOP use **This opening record is final. Add a correction if a fact needs to change.** and BOP §10.6 **Correct opening record**. | PRC v0.9 line 144 |

## 3. Proceedings codes as Bid Opening shows them (BOP-CHG-001 v0.10 §7.1)

| Proceedings code | Shown in Bid Opening as | Basis |
|---|---|---|
| `PRC_VERSION_CONFLICT` | `BOP_VERSION_CONFLICT`: "Someone updated this opening record. Refresh the page before continuing." | BOP v0.10 §7.1: "`PRC_VERSION_CONFLICT` maps to `BOP_VERSION_CONFLICT` and its exact §8 message" |
| `PRC_ALREADY_FINALIZED` | "This opening record is final. Add a correction if a fact needs to change." | BOP v0.10 §7.1 and PRC v0.9 §8 |
| `PRC_TARGET_CHANGED`, `PRC_MEMBER_REQUIRED`, `PRC_PROOF_UNVERIFIED`, `PRC_EVIDENCE_INCOMPLETE`, `PRC_START_BLOCKED`, `PRC_OWNER_UNAVAILABLE` | Their own PRC v0.9 §8 sentence | No Bid Opening replacement is specified; each already names the opening record. The concrete reasons, holder and fix come from Bid Opening's next step (BOP v0.10 §8 closing rule). |

## 4. Other fixed wording used by errors

| Situation | Wording (verbatim) | Source |
|---|---|---|
| A correction tries to change a bid fact, amount or signed target | "This correction cannot change a bid or replace the signed opening record." | BOP v0.10 §10.6 |
| Support notification committed | "Opening access support has been told." | BOP v0.10 §8 BOP_OPENING_PROFILE_UNAVAILABLE |
| Support notification failed | "Support could not be notified. Try again." | BOP v0.10 §8 BOP_OPENING_PROFILE_UNAVAILABLE |
