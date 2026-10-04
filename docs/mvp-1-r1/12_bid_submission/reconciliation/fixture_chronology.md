# BDS-CHG-001 v0.8: fixture chronology

| Control | Value |
|---|---|
| Version | 0.8-phase0.1 |
| Status | Phase 0 working document (plan BDS-CHG-001 v0.8) |
| Purpose | Phase 0 input for the canonical `bid_submission` seed stage (plan D19) and the Playwright worlds (plan Phase 12). It merges the Tenders canonical timeline with the Bid Submission timeline so each step runs at its real instant, as its named actor. |
| Sources | BDS-CHG-001 v0.8 §10.1 (fixture pack), BDS-CHG-001 §13.2–13.4 (seed contract), and the board captions (`artboard_inventory.md`). The canonical Tenders seed timeline is `kentender_procurement/tenders/seeds/kentender_mvp_v1.py` `CLOCK` (lines 82–106 as read on 26 Sep 2026). KT-STD-001 v1.9 §8.4A (fixture instants) and BDS-CHG-001 §8.7 (artboard-only facts). |
| Time rule | All instants are EAT, stored as naive site time (owner decision of 26 Sep 2026, AGENTS.md section 4.4). UTC appears only in serialized messages. |
| New content | The "Owner" column, the conflict dispositions and every "proposed" treatment are plan content for review. The instants themselves are quoted from the sources named. |

## 1. Canonical primary timeline (Tenders and Bid Submission interleaved)

"Tenders" rows are the existing canonical Tenders seed. "ACC" and "BDS" rows are new stage steps, quoted from BDS-CHG-001 §13.3 unless marked otherwise.

| Instant (EAT) | Owner | Actor | Event | Source |
|---|---|---|---|---|
| 20 Mar 2027 09:00 → 20 Apr 2027 10:00 | Tenders | Brian Wafula / Charles Mutiso | Tender prepared, returned, resubmitted and approved | Tenders `CLOCK` start…approve |
| 15 May 2027 07:55 | Tenders | Amina Hassan | Publication authorised; Published Bid Definition v1 frozen | Tenders `CLOCK["authorise"]` |
| 15 May 2027 08:00 | Tenders | Charles Mutiso | Published (availability 08:00; channel confirmations 08:03–08:07) | Tenders `AVAILABLE_AT`; BDS BDS-CHG-001 §10.1 "Published 15 May 2027, 08:00 EAT" |
| 18 May 2027 09:00 | ACC | Mary Wanjiku | `RegisterSupplierOrganisation` Afya Digital Supplies Limited → Pending verification; challenge sent | BDS BDS-CHG-001 §13.3; DES-03 |
| 18 May 2027 09:05 | ACC | Mary Wanjiku | (Isolated) Account Pending verification view | BDS BDS-CHG-001 §13.4 "Account pending verification"; DES-04-VERIFY caption |
| 18 May 2027 09:10 | ACC | Mary Wanjiku | `VerifyAccountCommunication` → Active | BDS BDS-CHG-001 §13.3 |
| 18 May 2027 09:20 | ACC | Mary Wanjiku (Account owner) | `AssignSupplierRepresentative` David Ouma | BDS BDS-CHG-001 §13.3 |
| 18 May 2027 09:30 | ACC | Mary Wanjiku (Account owner) | `AssignAuthorisedSignatory` Mary Wanjiku with authority evidence | BDS BDS-CHG-001 §13.3 (see conflict FX-2) |
| 18 May 2027 10:00 | ACC | Mary Wanjiku | Account read (DES-04 base) | DES-04 caption |
| 19 May 2027 09:20 | BDS | David Ouma | `StartBid` → `ARR-MOH-2027-033-001`, notice email `tenders@afyadigital.example`, `BID-MOH-2027-033-001` Draft Version 1 on definition Version 1. **Replaces** the Tenders stand-in step `CLOCK["candidate"]` (TPR FU-25). | BDS BDS-CHG-001 §13.3; Tenders `CLOCK["candidate"]` |
| 19–30 May 2027 | BDS | David Ouma | Initial task saves → Draft Versions 2 and 3 (see FX-1) | BDS BDS-CHG-001 §13.3 "Complete initial tasks"; DES-02-DRAFT "Draft Version 3" at 20 May 10:05 |
| 26 May 2027 09:00 | BDS → Tenders | David Ouma | `SubmitTenderClarification` → Tenders `receive_tender_clarification` | BDS BDS-CHG-001 §13.3; Tenders `CLOCK["clarification_received"]` |
| 26 May 2027 11:00 | Tenders | Brian Wafula | Answer to all registered candidates | Tenders `CLOCK["clarification_answered"]` |
| 26 May 2027 11:01 | Tenders | System | Candidate notice Delivered | Tenders `CLOCK["clarification_delivered"]`; BDS BDS-CHG-001 §10.1 |
| 27 May 2027 17:00 | Tenders | — | Clarification deadline | BDS BDS-CHG-001 §10.1 |
| 31 May 2027 08:30 → 09:07 | Tenders | Charles Mutiso | Addendum ADD-MOH-2027-033-001 issued and channels confirmed; effective 09:00; definition Version 2; deadline 12 Jun 2027 11:00 | Tenders `CLOCK` addendum_*; BDS BDS-CHG-001 §13.3 "31 May 2027 09:00" |
| 31 May 2027 09:08 | Tenders | System | Addendum candidate notice Delivered (canonical) | Tenders `CLOCK["addendum_delivered"]`; TPR FU-28 (see FX-3) |
| 1 Jun 2027 12:05 | BDS | David Ouma | Opens documents on Draft Version 4; read only (no mutation) | BDS BDS-CHG-001 §13.3 |
| 1 Jun 2027 12:10 | BDS | David Ouma | Acknowledges the addendum and confirms the delivery response → Draft Version 5 | BDS BDS-CHG-001 §13.3; DES-07-COMPLETE |
| 10 Jun 2027 10:00 | BDS | Charles Mutiso | Blind physical-security intake (owner decision OD-G). The intake reference is system-issued (see FX-4). Privately matched to Afya's bid (OD-H). | BDS BDS-CHG-001 §13.3 (as re-scoped by OD-G/H) |
| 10 Jun 2027 13:50 | BDS | David Ouma | Final save → Draft Version 7, all preparation tasks Complete | BDS BDS-CHG-001 §13.3 (see FX-1) |
| 10 Jun 2027 14:15 | BDS | Mary Wanjiku | Opens Review; read only | BDS BDS-CHG-001 §13.3 |
| 10 Jun 2027 14:20 | BDS | David / Mary | Primary workspace and My bids fixture instant | BDS BDS-CHG-001 §10.6–10.7, BDS03-AC-001 |
| 10 Jun 2027 14:31:58 → 14:32:01 | BDS | Mary Wanjiku | `SubmitBid`: received 14:31:58, accepted 14:32:01, receipt `RCPT-MOH-2027-033-001` (simulation) | BDS BDS-CHG-001 §13.3 |
| 12 Jun 2027 11:00 | Tenders → BDS | System | Tenders closes the submission period (`CLOCK["close"]`). BDS consumes `TenderSubmissionPeriodEnded`, closes the box and creates the Bid Opening hand-off. | BDS BDS-CHG-001 §13.3; Tenders `CLOCK["close"]` |

## 2. Isolated worlds (built by Playwright resets, never in the canonical chain)

Every row is quoted from BDS-CHG-001 §13.4, BDS-CHG-001 §10.1 "Isolated Tender and arrangement facts" or "Isolated variants". Per BDS-CHG-001 §13.4: "An isolated fixture never reuses one receipt, signature, envelope, evidence result or event time to prove opposite outcomes."

| World | Instant (EAT) | Actor | Key facts |
|---|---|---|---|
| Public signed out | 20 May 2027 10:00 (DES-01); 1 Jun 2027 12:15 (DES-02) | Guest | No identity |
| Kisiwa public base | 1 Jun 2027 12:15 | Peter Mwangi | Active Kisiwa representative; no workspace; not assigned to Afya |
| JV start | 20 May 2027 10:05 → 10:10 (start) → 10:15 (DES-08-JV) | Peter Mwangi | Kisiwa–Jua Technology JV; `ARR-MOH-2027-033-002`; `BID-MOH-2027-033-002` Draft Version 1; Grace Njeri signatory; `tenders@kisiwadigital.example` |
| Public Tender Draft | 20 May 2027 10:05 | David Ouma | Draft Version 3; 3 of 5 tasks Complete; original 5 Jun deadline |
| Candidate question | 26 May 2027 08:50 → 09:00 | David Ouma | Before the clarification deadline; no answer or addendum yet |
| Clarifications closed | 28 May 2027 12:00 | David Ouma | Answer readable; no addendum |
| Addendum notice Queued / Sent / Failed | 31 May 2027 09:01 / 09:02 / 09:15 | David Ouma | Isolated notice states (see FX-3) |
| Account incomplete | (no instant stated) | Mary Wanjiku | Official phone empty; no workspace |
| Account suspended | 10 Jun 2027 14:20 | David / Mary | Afya Suspended; receipt recoverable |
| Cross-organisation denial | 10 Jun 2027 14:20 | Peter Mwangi | Requests `BID-MOH-2027-033-001`; masked |
| Evidence rejected | (primary Draft) | David Ouma | Product datasheet fails the test malware scan |
| Security outstanding | (primary Draft) | David Ouma | Proof Accepted; no physical intake matched |
| Certificate required / signing unavailable / gate disabled / submission unavailable | 10 Jun 2027 14:20–14:30 | Mary Wanjiku | Via `BDS Test Environment Controls` (plan D5) |
| Custody definitely failed | 10 Jun 2027 14:30 | Mary Wanjiku | `TBX-REJECT-033-01`; Draft preserved |
| Custody uncertain | 10 Jun 2027 14:30 | Mary Wanjiku | `COR-BDS-2027-033-01`; `SUP-BDS-2027-033-01` |
| Late submission | 12 Jun 2027 11:00:01 | Mary Wanjiku | Rejected; no envelope or receipt |
| Submitted receipt after deadline | 12 Jun 2027 11:00:01 | Mary Wanjiku | Version 1 accepted 10 Jun 14:32:01 |
| Idempotency conflict | — | Mary Wanjiku | `COR-BDS-2027-033-02`; same key, changed price |
| Replacement | 11 Jun 2027 08:30 → 09:15 | Mary Wanjiku | Version 2 accepted; `RCPT-MOH-2027-033-002`; Version 1 Superseded |
| Replacement conflict | — | Mary Wanjiku | Stale Version 3 attempt after Version 2 is current |
| Withdrawal | 10 Jun 2027 14:41:58 / 14:42:01 → 15:00 | Mary Wanjiku | TND-MOH-2027-041; `RCPT-MOH-2027-041-001`; `WD-MOH-2027-041-001` |
| Cancelled Tender | — | Guest / supplier | TND-MOH-2027-034 |
| Receipt history | 12 Jun 2027 11:00:01 | David Ouma | `RCPT-MOH-2027-033-001` plus `WD-MOH-2027-041-001` (different Tenders) |

## 3. Fixture conflicts found (for the tracker and follow-ups)

| ID | Conflict | Proposed treatment |
|---|---|---|
| FX-1 | DES-06 shows per-task Updated times of 10 Jun 10:05 (Company), 11:30 (Requirements), 12:15 (Price) and 13:50 (Review). That is four Draft saves after Version 5 (1 Jun 12:10). But BDS-CHG-001 §10.1 says "Draft Version 7 is the seventh saved working Draft revision" at 13:50, which leaves room for only two saves after Version 5. | Rule: `current_draft_version` +1 per committed Draft-mutating command (BDS-CHG-001 §4.5). The canonical seed keeps BDS-CHG-001 §13.3's version numbers. The DES-06 Updated column is declared an artboard-only fact under KT-STD-001 v1.9 §8.7. Logged as a spec follow-up. |
| FX-2 | DES-03 captures the registrant's "Your responsibility: Authorised Signatory" and authority evidence at registration, but BDS-CHG-001 §13.3 assigns Mary at 09:30, after David at 09:20. | Registration records the registrant's requested responsibility and evidence. The seed follows BDS-CHG-001 §13.3 (David 09:20, Mary 09:30, both by the Account owner). The live UI activates the registrant's signatory assignment at verification. Logged as a spec follow-up. |
| FX-3 | The BDS BDS-CHG-001 §10.1 addendum notice shows Queued 09:01 and Sent 09:02, but Tenders freezes the audience only at the final channel confirmation (09:07) and the canonical notice is Delivered at 09:08 (TPR FU-28). | The canonical chain uses the real Tenders instants. The Queued, Sent and Failed states are isolated worlds with injected transport outcomes and the board's times. |
| FX-4 | BDS-CHG-001 §10.1 shows the security receipt `MOH-SEC-2027-033-017` typed by the receipt owner. Owner decision OD-G makes the intake reference system-issued and opaque. | The intake reference is generated. DES-08/DES-11 supplier copy shows the generated reference, and `MOH-SEC-2027-033-017` becomes an artboard-only fact. Logged with OD-G. |
| FX-5 | BDS-CHG-001 §13.2 names Alice Njeri as Auditor; the KT-STD-001 v1.9 §8.3 register has Naomi Chebet. | The register wins (standing owner decision, 21 Sep 2026). |
| FX-6 | KT-STD-001 v1.9 §8.4A lists no Bid Submission window. | Bid Submission works in 15 May–12 Jun 2027, after the Requisition and Tender Preparation window ends on 15 May 2027. The KT-STD owner is asked to add the window. |
