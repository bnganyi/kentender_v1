# CM-CHG-001 v0.8: fixture chronology

| Control | Value |
|---|---|
| Version | 0.8-chronology.1 |
| Date | 14 October 2026 |
| Source | CM v0.8 §10.1B (verbatim) and the board dump, built by `tools/build_chronology.py` (tracker CM8-005) |

The board literals are fixture data (plan D17). The ordinary ten-laptop story and every isolated identity use a separate synthetic source (`CM-DEMO-AWD-01`, `CM-DEMO-TERMS-01`) and **never overwrite the canonical chain** (Award's TND-MOH-2027-002 package, KES 46,400,000, delivered 2 Jul 2027 09:00 EAT; CM v0.8 §13). Each isolated branch has its own source and operation identities and inherits nothing from another branch.

## Scenario table (CM v0.8 §10.1B, verbatim)

| Scenario | Resolved contract | Task families / fact boundary | Boards in the design | Entry point (proposed) | Spec line |
|---|---|---|---|---|---|
| Ordinary ten-laptop delivery | CM-MOH-2027-001 | Formation, eight accepted/two rejected, replacement, invoices and later completed branch. | D01, D01-E, D01-F, D01-T, D01-AUD, D01-S, D01-S-E, D02, D02-H, D02-S, D02-V, D03, D03-W, D03-A, D26, D26-H, D26-E, D23, D23 · Appoint, D23 · Return, D23-R, D23-P, D24, D24-C, D24-S, D24-X, D04, D04 · Units, D05, D05 · Record, D05 · All, D05-M, D19, D06, D07, D07 · Correction, D07-P, D18, D18-R, D18-C, D08, D08 · Correction, D08-C, D33, D33-U, D33-W, D33-A, D33-A · Return, D33-A · Posted, D09, D09-F, D09-F · Submitted, D09-T, D09-AUD, D09-F · Stale, D17, D17 · Return, D17 · Posted, D17 · Pending, D17-H, D17-S, D28, D28-F, D28-F · Editor, D28-C, D28-V, D29, D29-H, D29-R, D13, D13-S, D13-C, D10, D40, D40-AO, D40-HOD, D40-D, D40-F, D40-T, D40-AUD, D40-S, D32, D32 · Return, D22, D22-P, D11, D11 · Return, D11-C, D15, D15-L, D15-L · Evidence, D-ERR, D-DENIED | Synthetic Award package `CM-DEMO-AWD-01` delivered through the receiver hook → `ReceiveAwardPackage` → the ordinary commands in order (plan Phase 4). | CM v0.8 line 678 |
| Existing signed contract | CM-MOH-2027-EXT-001 | D12/D21; imported opening position; no re-signing or historic reposting. | D12, D12-G, D21, D21-H | `RegisterExistingContract` → `ConfirmOpeningPosition` → `StartContractManagement` (no package, no signature). | CM v0.8 line 679 |
| Delivery extension | CM-MOH-2027-EXTENSION-001 | D14/D27; no base delivery history; due date changes only after effective amendment. | D27, D27-R, D27-A, D27 · Blocked, D14, D14 · Approve, D14 · Decline, D14-P | Package `EXTENSION-TERMS-01` → signed and Active 2 Jul 10:30 → `RequestContractChange` 18 Jul → review → `DecideContractChange` 19 Jul → amendment signatures → `ActivateContractChange`. | CM v0.8 line 680 |
| Security return | CM-MOH-2027-SEC-RETURN-001 | D16; TEST-G-RETURN-001, distinct verification/signing/return history. | D16 | Package with performance security `TEST-G-RETURN-001` verified 3 Jul → signed → delivery and acceptance → `SignFinalContractAcceptance` → `RecordSecurityAction` (Return). | CM v0.8 line 681 |
| Security verification | CM-MOH-2027-SEC-VERIFY-001 | D25; TEST-G-001, no D16 discharge. | D25, D25 · Verify, D25 · Reject, D25-R, D25-J | Package with security `TEST-G-001` received → `VerifyContractSecurity` or `RejectContractSecurity` (no discharge). | CM v0.8 line 682 |
| Open warranty claim | CM-MOH-2027-WAR-OPEN-001 | D16-W/P, D11-B, D32-H; claim remains open on 21/28 Jul 2028. | D16-W, D16-P, D32-H, D11-B | Completed delivery → warranty claim on `CM-WAR-OPEN-004` 10 Jul 2028 → remedy pending 21 and 28 Jul. | CM v0.8 line 683 |
| Resolved paid-unit warranty | CM-MOH-2027-WAR-001 | D35; replacement/native corrections reconciled, claim closed 15 Jul. | D35, D35 · Return, D35-V, D35-C, D35-H | Completed and paid delivery → warranty claim on `CM-WAR-004` → `RecordAcceptanceCorrection` return and replacement → `VerifyContractRemedy`; resolved 15 Jul. | CM v0.8 line 684 |
| Termination/settlement | CM-MOH-2027-TERM-001 | D20, D11-T, D39; eight accepted units only; no base replacements/invoice 2. | D20, D20 · Decline, D20-P, D20-T, D39-P, D39, D39 · Complete, D39-C, D39-H, D11-T | Eight units accepted 20 Jul and paid 600,000 + 200,000 → `DecideContractTermination` → `RecordTerminationNotice` 10 Aug → `PrepareTerminationSettlement` → `CompleteTerminationSettlement`. | CM v0.8 line 685 |
| Related service | CM-MOH-2027-SVC-001 | D31; ten laptops plus training; no training in base D22. | D31, D31-A | Ten laptops plus training service → `PrepareAcceptanceReport` for the service subject (no stock or asset). | CM v0.8 line 686 |
| Quantity change | CM-MOH-2027-QTY-001 | D34; source limits and funding; no base changes. | D34, D34-R, D34-A, D34-A · Decide, D34-P, D34-H, D34-L, D34-X | Active contract → `RequestContractChange` quantity 10 → 11 (and a 12-unit refusal) with synthetic source and funding evidence. | CM v0.8 line 687 |
| Delay adjustment | CM-MOH-2027-DELAY-001 | D36; its own delivery/extension facts and calculations. | D36, D36-A, D36-A · Decide, D36-S, D36-H, D36-E | Ten goods accepted 25 Jul after a 20 Jul due date → `PrepareContractAdjustment` → `DecideContractAdjustment`. | CM v0.8 line 688 |
| Security claim | CM-MOH-2027-SEC-001 | D37; TEST-SG instruments; decision is not cash recovery. | D37, D37-A, D37-P, D37-P · Outcome, D37-X | Verified instruments `TEST-SG` → `RequestSecurityClaim` → `DecideSecurityClaim` → `RecordSecurityClaimOutcome`. | CM v0.8 line 689 |
| Close-out correction | CM-MOH-2027-CLOSE-001 | D38; retained original closure and correction. | D38-P, D38, D38 · Reopen, D38-R, D38-T | Closed 28 Jul 2028 → `PrepareContractClosureCorrection` → `ReopenContractCloseout`. | CM v0.8 line 690 |
| Posted-liability correction | CM-MOH-2027-CLAIM-001 | D08-L; Finance correction required before certification. | D08-L | Early liability recognised by Finance for invoice v1 → corrected claim v2 at 10:00 → native credit before certification. | CM v0.8 line 691 |
| Partial payment / advance / outside signing | Explicitly isolated subject identities in D28 / D29 / D26 | Use their own records and evidence; never import the ordinary branch’s settlement/signature outcomes. | — (see Findings) | **Identity not named by the spec** (see Findings). | CM v0.8 line 692 |

## Source chronology paragraphs (CM v0.8 §10.1B, verbatim)

> **Line 694.** The following source chronology is fixture metadata. Task cards resolve their visible content and controls locally; this table does not add screen fields.

> **Line 696.** All dates without a year in §§10.2–10.5 are in 2027 unless a brief explicitly says 2028. In §10.8 each variant inherits its base branch year, contract/subject/version, EAT timezone and selected tab unless explicitly replaced; waiting lines use the stated event/assignment instant. Base managing unit **Digital Health** (`OU-MOH-DHI`); source kind **KenTender award — illustrative package CM-DEMO-AWD-01**, distinct from Award’s canonical source. The synthetic rule profile is labelled **Illustrative test terms**; it supplies the stated 30-day contractual invoice term and unit-based warranty without claiming statutory validity. Issued source **CM-DEMO-TERMS-01** has the 10 laptops/rates/criteria in §10.1; agreement becomes effective at **2 Jul 2027, 10:30 EAT** after Mary signs at 10:05 and Amina at 10:30. Request sent 09:20; the main no-security branch does not borrow D16’s guarantee.

> **Line 698.** Base accepted receipt and asset/stock classification are a labelled test configuration; posting occurs once at **20 Jul 2027, 14:31 EAT**, after the report’s last required signature. INV-01 v1 is received **21 Jul 2027, 08:05 EAT**, corrected v2 received **21 Jul 2027, 10:00 EAT**, with original receipt retained. Charles signs certification at 10:15; Josphat submits the accounting invoice at 11:00 and Beatrice posts it at 11:30 through D33; Josphat prepares the payment entry **22 Jul 2027, 13:00**; Beatrice approves the native entry **22 Jul 2027, 14:15**. Settlement confirmation **23 Jul 2027, 10:00** gives KES 800,000 cash. Replacement units 011/012 arrive **27 Jul 2027, 09:00**, are accepted **27 Jul 2027, 15:30**, and posted 15:31, linked to original rejected units 009/010; source quantity remains 10. A separate eligible invoice INV-02 for KES 200,000 remains unpaid in D15. The completed branch confirms it at **2 Aug 2027, 10:00**, giving total cash KES 1,000,000. The ordinary branch’s final acceptance is recorded by Amina **28 Jul 2028, 08:30**, completion certificate signed/delivered **09:00/09:05**, closure **10:00**. The timing is fixture data, not a legal deadline.

> **Line 700.** **Isolated identity overrides.** D20/P/T, D11-T and D39-P/D39/C use CM-MOH-2027-TERM-001. The first eight units were accepted 20 Jul 2027; their supported KES 800,000 is settled by KES 600,000 confirmed 2 Aug and KES 200,000 confirmed 19 Aug. Units 9/10 were never delivered or accepted; no base replacement receipts or INV-02 are inherited. Default notice/cure evidence is complete before the 10 Aug review; notice delivered/effective 10 Aug 11:00. The final unperformed KES 200,000 is extinguished under the reviewed termination outcome, with Budget adjustment/reconciliation evidenced by 20 Aug. D20-P is the 10:15 pre-delivery state; D20-T/D11-T are the 11:00 effective state. D16 uses SEC-RETURN-001, D16-W/P and D11-B WAR-OPEN-001; D35/V/C/H WAR-001, and D25 SEC-VERIFY-001; these cases never import base security, warranty, acceptance or cash facts. All D37 variants retain SEC-001 and its distinct TEST-SG instruments. Every inherited header uses the brief’s resolved contract identity rather than the global base reference.

> **Line 702.** **Extension identity and chronology.** D27/R/A and D14/P share **CM-MOH-2027-EXTENSION-001**, issued source **EXTENSION-TERMS-01**, agreement 1 and change 1. Source terms are 10 laptops / KES 1,000,000 / delivery due 20 Jul 2027; no advance or performance security. Mary signs agreement 1 on 2 Jul at 10:05 EAT and Amina at 10:30; it is Active from 10:30. No delivery or acceptance has occurred at the 18 Jul request or 19 Jul decision/signing views. D27 is the request at 18 Jul 10:00; D27-R follows the current reviewers’ recommendation at 11:00; D14 is AO review at 19 Jul 10:00; approval is recorded at 10:15, yielding D14-P. D27-A is Mary’s amendment 1 signing task at 11:00; Mary signs at 11:05 and Amina at 11:30. Only both required signatures make amendment 1 effective at 11:30 and change the due date to 27 Jul; approval alone leaves 20 Jul operative. This successful fixture later records delivery of all 10 units on 27 Jul at 09:00, with acceptance not yet established at that instant. It never inherits the base 20 Jul delivery, rejection/replacement history, invoices, cash settlements, final acceptance or closure. Declined/returned variants do not inherit the successful approval/signature/effectiveness events.

> **Line 704.** **Open warranty identity.** D16-W/P, D11-B and D32-H share **CM-MOH-2027-WAR-OPEN-001**, source **WAR-OPEN-TERMS-01**, agreement 1 / claim 1, unit **CM-WAR-OPEN-004**. The defect notice is timely on 10 Jul 2028; the remedy remains pending on 21 and 28 Jul. These branches never inherit D35’s 15 Jul remedy or the base completed story. D35/V/C/H retain **CM-MOH-2027-WAR-001**, unit **CM-WAR-004**, and its distinct resolved-remedy chronology. D16 uses **TEST-G-RETURN-001**; D25/R/J retains **TEST-G-001** on SEC-VERIFY-001, with its own confirmation/expiry and no D16 discharge.

> **Line 706.** **Expanded Evidence and history** shows only the named links and the exact events supplied for that brief/branch. Default is closed; material reasons and quantity/financial differences are never hidden in it. Common tabs are Agreement, Deliveries, Invoices, Obligations, History; selected tab: D02/D03/D12 Agreement; D04–D07/D19 Deliveries; D08/D09/D17/D18/D21/D33 Invoices; D10/D11/D13–D16/D20/D22 Obligations. D01 is a workspace and has no case tabs. D21’s selected Invoices tab is a cutover financial comparison, not a new accounting screen.

## Ordinary path as drawn (boards whose header is CM-MOH-2027-001, sorted by their instant)

78 boards carry a parseable instant; boards of the isolated D26, D28 and D29 branches are listed separately below. Display instants are EAT.

| Instant | Board | Design | State | Actor |
|---|---|---|---|---|
| 2 Jul 2027, 09:01 EAT | D01 | D01 | Base — My work | Charles Mutiso · HOP |
| 2 Jul 2027, 09:01 EAT | D01-E | D01 | Empty register | Charles Mutiso · HOP |
| 2 Jul 2027, 09:01 EAT | D01-F | D01 | No search results | Charles Mutiso · HOP |
| 2 Jul 2027, 09:15 EAT | D02 | D02 | Base — Preparing | Brian Wafula · authorised preparer |
| 2 Jul 2027, 09:15 EAT | D02-H | D02 | Signing on hold | Charles Mutiso · HOP |
| 2 Jul 2027, 09:15 EAT | D02-V | D02 | View agreement 1 — source-layout prototype | Brian Wafula · authorised preparer |
| 2 Jul 2027, 09:20 EAT | D02-S | D02 | Signing unavailable | Brian Wafula · authorised preparer |
| 2 Jul 2027, 10:00 EAT | D01-S | D01-S | Base | Mary Wanjiku · Afya supplier signatory |
| 2 Jul 2027, 10:00 EAT | D01-S-E | D01-S | Empty | Mary Wanjiku · Afya supplier signatory |
| 2 Jul 2027, 10:00 EAT | D03 | D03 | Base — Mary signs | Mary Wanjiku · Afya authorised signatory |
| 2 Jul 2027, 10:05 EAT | D03-W | D03 | Supplier signed — entity pending | Mary Wanjiku · Afya authorised signatory |
| 2 Jul 2027, 11:00 EAT | D15-L | D15 | Publication requirement — blocked | Charles Mutiso · HOP |
| 2 Jul 2027, 11:00 EAT | D15-L · Evidence | D15 | Record source evidence dialog | Charles Mutiso · HOP |
| 3 Jul 2027, 09:00 EAT | D23-R | D23 | Recommend (HOP draft) | Charles Mutiso · HOP |
| 3 Jul 2027, 10:00 EAT | D23 | D23 | Base — AO review | Amina Hassan · Accounting Officer |
| 3 Jul 2027, 10:00 EAT | D23 · Appoint | D23 | Appointment dialog | Amina Hassan · Accounting Officer |
| 3 Jul 2027, 10:00 EAT | D23 · Return | D23 | Return dialog | Amina Hassan · Accounting Officer |
| 3 Jul 2027, 10:05 EAT | D23-P | D23 | Declaration pending | Charles Mutiso · HOP |
| 3 Jul 2027, 10:10 EAT | D24 | D24 | Base — not yet declared | Peter Mugo · appointed member |
| 3 Jul 2027, 10:10 EAT | D24-C | D24 | Conflict selected | Peter Mugo · appointed member |
| 3 Jul 2027, 10:11 EAT | D24-S | D24 | Saved — no conflict | Peter Mugo · appointed member |
| 3 Jul 2027, 10:12 EAT | D24-X | D24 | Conflict — replacement needed | Charles Mutiso · HOP |
| 20 Jul 2027, 09:00 EAT | D04 | D04 | Base | Grace Wanjiku · authorised receiver |
| 20 Jul 2027, 09:00 EAT | D04 · Units | D04 | Unit references dialog | Grace Wanjiku · authorised receiver |
| 20 Jul 2027, 11:00 EAT | D05 | D05 | Base — Your turn | Peter Mugo · appointed inspector |
| 20 Jul 2027, 11:00 EAT | D05 · Record | D05 | Record observations dialog | Peter Mugo · appointed inspector |
| 20 Jul 2027, 11:00 EAT | D05 · All | D05 | All observations detail | Peter Mugo · appointed inspector |
| 20 Jul 2027, 11:00 EAT | D05-M | D05 | Evidence unreadable — blocked | Peter Mugo · appointed inspector |
| 20 Jul 2027, 13:30 EAT | D19 | D19 | Base | Peter Mugo · appointed technical member/certifier |
| 20 Jul 2027, 14:00 EAT | D06 | D06 | Base | Julia Njeri · appointed chair |
| 20 Jul 2027, 14:30 EAT | D07 | D07 | Base — Brian signs | Brian Wafula · appointed procurement member |
| 20 Jul 2027, 14:30 EAT | D07 · Correction | D07 | Request correction dialog | Brian Wafula · appointed procurement member |
| 20 Jul 2027, 14:31 EAT | D07-P | D07 | Signed — stock update pending | Brian Wafula · appointed procurement member |
| 20 Jul 2027, 15:00 EAT | D13 | D13 | Base — send findings | Julia Njeri · contract owner |
| 21 Jul 2027, 08:00 EAT | D18 | D18 | Base — submit | David Ouma · Afya supplier representative |
| 21 Jul 2027, 08:05 EAT | D18-R | D18 | Needs review — waiting | David Ouma · Afya supplier representative |
| 21 Jul 2027, 09:00 EAT | D08 | D08 | Base — quantity difference | Charles Mutiso · authorised certifier |
| 21 Jul 2027, 09:00 EAT | D08 · Correction | D08 | Request correction dialog | Charles Mutiso · authorised certifier |
| 21 Jul 2027, 09:00 EAT | D13-S | D13 | Supplier reply | David Ouma · Afya supplier representative |
| 21 Jul 2027, 11:00 EAT | D33 | D33 | Base — Finance maker | Josphat Mwangi · Finance maker |
| 21 Jul 2027, 11:00 EAT | D33-U | D33 | Accounting setup needs review | Josphat Mwangi · Finance maker |
| 21 Jul 2027, 11:00 EAT | D33-W | D33 | Submitted — waiting | Josphat Mwangi · Finance maker |
| 21 Jul 2027, 11:30 EAT | D33-A | D33 | Finance approver review | Beatrice Kamau · Finance approver |
| 21 Jul 2027, 11:30 EAT | D33-A · Return | D33 | Return dialog | Beatrice Kamau · Finance approver |
| 21 Jul 2027, 11:30 EAT | D33-A · Posted | D33 | Posted | Beatrice Kamau · Finance approver |
| 22 Jul 2027, 13:00 EAT | D09-F | D09 | Finance maker — payment editor | Josphat Mwangi · Finance maker |
| 22 Jul 2027, 13:00 EAT | D09-F · Submitted | D09 | Submitted — waiting | Josphat Mwangi · Finance maker |
| 22 Jul 2027, 13:00 EAT | D09-F · Stale | D09 | Changed since review | Josphat Mwangi · Finance maker |
| 22 Jul 2027, 14:00 EAT | D17 | D17 | Base — approver review | Beatrice Kamau · Finance approver |
| 22 Jul 2027, 14:00 EAT | D17 · Return | D17 | Return dialog | Beatrice Kamau · Finance approver |
| 22 Jul 2027, 14:00 EAT | D17 · Pending | D17 | Approval pending | Beatrice Kamau · Finance approver |
| 22 Jul 2027, 14:00 EAT | D17-H | D17 | Payment on hold | Beatrice Kamau · Finance approver |
| 22 Jul 2027, 14:15 EAT | D17 · Posted | D17 | Approved — posted | Beatrice Kamau · Finance approver |
| 23 Jul 2027, 09:00 EAT | D09 | D09 | Base — contract owner | Julia Njeri · contract owner |
| 23 Jul 2027, 09:00 EAT | D09-T | D09 | Technical reader | Daniel Otieno · Technical operator (site-wide read) |
| 23 Jul 2027, 09:00 EAT | D09-AUD | D09 | Auditor | Naomi · Site-wide auditor |
| 23 Jul 2027, 09:15 EAT | D10 | D10 | Base | Julia Njeri · contract owner |
| 23 Jul 2027, 09:15 EAT | D40 | D40 | Base — identical to D10 | Julia Njeri · contract owner |
| 23 Jul 2027, 09:15 EAT | D40-AO | D40 | Accounting Officer read | Amina Hassan · Accounting Officer |
| 23 Jul 2027, 09:15 EAT | D40-HOD | D40 | Head of User Department read | Julia Njeri · Head of User Department (Digital Health only) |
| 23 Jul 2027, 09:15 EAT | D40-D | D40 | Departmental Author — denied | Grace Wanjiku · Departmental Author only |
| 23 Jul 2027, 09:15 EAT | D40-F | D40 | Finance maker read | Josphat Mwangi · Finance maker |
| 23 Jul 2027, 09:15 EAT | D40-T | D40 | Technical reader | Daniel Otieno · Technical operator (site-wide read) |
| 23 Jul 2027, 09:15 EAT | D40-AUD | D40 | Auditor | Naomi · Site-wide auditor |
| 23 Jul 2027, 09:15 EAT | D40-S | D40 | Supplier representative | David Ouma · Afya supplier representative |
| 23 Jul 2027, 10:00 EAT | D17-S | D17 | Record settlement | Beatrice Kamau · Finance approver |
| 27 Jul 2027, 16:00 EAT | D13-C | D13 | Issue closed | Julia Njeri · contract owner |
| 1 Aug 2027, 09:00 EAT | D15 | D15 | Base — July report | Charles Mutiso · HOP |
| 3 Aug 2027, 12:00 EAT | D01-T | D01 | Technical reader — All contracts | Daniel Otieno · Technical operator (site-wide read) |
| 3 Aug 2027, 12:00 EAT | D01-AUD | D01 | Auditor — All contracts | Naomi · Site-wide auditor |
| 3 Aug 2027, 12:00 EAT | D-DENIED | D-DENIED | Shared denial page | Grace Wanjiku · Departmental Author only |
| 28 Jul 2028, 08:30 EAT | D32 | D32 | Base — completed branch | Amina Hassan · AO acceptance authority |
| 28 Jul 2028, 08:30 EAT | D32 · Return | D32 | Return dialog | Amina Hassan · AO acceptance authority |
| 28 Jul 2028, 09:00 EAT | D22 | D22 | Base | Charles Mutiso · HOP |
| 28 Jul 2028, 09:00 EAT | D22-P | D22 | Issued — delivery pending | Charles Mutiso · HOP |
| 28 Jul 2028, 10:00 EAT | D11 | D11 | Base — completed branch | Amina Hassan · Accounting Officer |
| 28 Jul 2028, 10:00 EAT | D11 · Return | D11 | Return dialog | Amina Hassan · Accounting Officer |
| 28 Jul 2028, 10:00 EAT | D11-C | D11 | Closed | Amina Hassan · Accounting Officer |

## Base-reference boards without a parseable instant

| Board | Stated | Reason |
|---|---|---|
| D03-A | 2 Jul 2027, before 10:30 EAT | The board states no single instant; the instant is read from the task card. |
| D18-C | 21 Jul 2027, before 10:00 EAT | The board states no single instant; the instant is read from the task card. |
| D08-C | 21 Jul 2027, before 10:15 EAT | The board states no single instant; the instant is read from the task card. |
| D-ERR | (empty) | The board states no single instant; the instant is read from the task card. |

## Isolated D26, D28 and D29 boards

| Board | Subject | Header reference | Instant |
|---|---|---|---|
| D26 | Isolated permitted outside-signing branch | CM-MOH-2027-001 | 2 Jul 2027, 10:10 EAT |
| D26-H | Isolated permitted outside-signing branch | CM-MOH-2027-001 | 2 Jul 2027, 10:10 EAT |
| D26-E | Isolated permitted outside-signing branch | CM-MOH-2027-001 | 2 Jul 2027, 10:35 EAT |
| D28 | Isolated partial-payment branch · INV-01 version 2 | CM-MOH-2027-001 | 23 Jul 2027, 11:00 EAT |
| D28-F | Isolated partial-payment branch · INV-01 version 2 | CM-MOH-2027-001 | 24 Jul 2027, 09:00 EAT |
| D28-F · Editor | Payment Entry TEST-PE-PART-02 draft | CM-MOH-2027-001 | 24 Jul 2027, 09:00 EAT |
| D28-C | Isolated partial-payment branch · INV-01 version 2 | CM-MOH-2027-001 | 25 Jul 2027, 10:00 EAT |
| D28-V | Isolated partial-payment branch · INV-01 version 2 | CM-MOH-2027-001 | 26 Jul 2027, 10:00 EAT |
| D29 | Isolated advance branch | CM-MOH-2027-001 | 5 Jul 2027, 09:00 EAT |
| D29-H | Isolated advance branch | CM-MOH-2027-001 | 5 Jul 2027, 09:00 EAT |
| D29-R | Isolated advance branch | CM-MOH-2027-001 | Not stated |

## Findings

1. **D26, D28 and D29 have no identity.** CM v0.8 §10.1B names them "explicitly isolated subject identities" and the D28 / D29 briefs say "Explicit variant contract identities replace this normal fixture", but no identity is given and every board header shows `CM-MOH-2027-001`. The seeds need three identities. **Proposed (new content, for the owner):** `CM-MOH-2027-PART-001` (D28, payments TEST-PE-PART-01/02), `CM-MOH-2027-ADV-001` (D29, ADV-01 / TEST-AG-01) and `CM-MOH-2027-OUTSIDE-001` (D26). Logged as a follow-up.
2. **Boards of the base contract:** 82 of 157 boards carry `CM-MOH-2027-001` outside D26, D28 and D29. Boards for every other §10.1B identity are listed in the scenario table.
3. **Dates are 2027 unless a brief says 2028** (CM v0.8 §10.1B). The ordinary branch's final acceptance, completion certificate and closure are 28 Jul 2028; warranty ends 20 Jul 2028 for the first eight units and 27 Jul 2028 for the two replacements.
4. **Test clock.** The canonical Award delivery to Contract Management is at 2 Jul 2027 09:00 EAT on the trusted test clock; every CM seed drives the same clock and never uses the real date.
