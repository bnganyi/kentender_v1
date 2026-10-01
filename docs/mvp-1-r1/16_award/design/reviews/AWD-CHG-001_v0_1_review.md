# Review — AWD-CHG-001 v0.1 (Award)

Review only. No edit was made to the requirements document.

## 1. Files

- Input: `uploads/KenTender_AWD-CHG-001_Award_v0_1.md` — v0.1, "Proposed requirements — Project Owner review", dated 30 September 2026, including the 30 September review amendment.
- Output: this report. No new version created.

## 2. Read list

- Read in full: AWD-CHG-001 v0.1; Public Procurement and Asset Disposal Act No. 33 of 2015, Revised Edition 2022 (the PDF linked in §17.1).
- Not read (not supplied): baseline register KT-DOC-CTRL-001; KT-STD-001 v1.12 / v1.13; EVL-CHG-001 v0.4; STD-TPL-001 v0.10; TPR-CHG-001 v0.13 / v0.15; BDS-CHG-001 v0.8 / v0.10; PRC-CHG-001 v0.9 / v0.10; TRUST-ADR-001; AUTH-ADR-001; LAW-REG-001; LAW-V-001; 2020 Regulations; the fixture register.
- Scripts: `preservation_check.py`, `consistency_check.py` and `register_check.py` could not be run in this environment. All checks below are manual.

## 3. Findings verified in the text (internal consistency)

Severity: **A** = would force a designer or developer to invent behaviour; **B** = contradiction or wording drift; **C** = editorial.

| # | Sev | Where | Finding |
|---|---|---|---|
| F1 | A | §5.9 journey vs stored stages; D05, V10 | Five journey labels, six stored stages. No mapping says when stored stage **Waiting to proceed** shows journey stage "Acceptance and wait" versus "Send to Contracting". D05 shows Acceptance and wait Current; V10 (still Waiting to proceed, receiver down) shows "first four Done; Send to Contracting Blocked". The rule that moves the marker is not stated. |
| F2 | A | §5.9 transition table; §5.2, §5.7, §7 | The table has no rows for the post-decision correction cycle (Review report correction → Decide correction → corrected report → fresh opinion → further AO decision). V09/V17 give markers, but the stage the case sits in during that cycle is undefined. |
| F3 | A | §5.9 "**Closed** is a terminal outcome" vs §5.7 | §5.7 says a correction "After an Award or No award decision" creates HOP's Review report correction task, and "A later lawful reconsideration is a linked successor decision cycle". After No award the case is Closed and terminal. It is not stated whether a correction reopens the case, creates a successor case or only a linked cycle. |
| F4 | A | §10.3 Record restriction dialog; §5.6; AWD-AC-016 | §5.6 requires an authoritative suspension and a "reported challenge awaiting verification" (precautionary hold) to be "clearly distinguished". The dialog fields (Source, Received at, Effective from, Scope, Evidence, Reason) have no field that records which of the two it is. |
| F5 | A | §10.3 Record outcome / Review correction dialog; AWD-AC-023 | Field **Outcome** has no stated options. §5.7 needs at least: close as non-material with evidence, or propose a change / corrected evaluation (which creates AO's Decide correction). A designer would have to invent the options. |
| F6 | A | §4 Issue types | "Types: Source correction, Funding, Validity, Delivery, Debrief, Review/order, Supplier response, Service failure." V15's unverified-rule issue (`AWD_RULE_UNVERIFIED`, "View outstanding issue") and the unresolved-audience case in §5.4 have no type. §4 also says "Do not add fields without a named rule or output". |
| F7 | B | §6 vs §8, §5.5 | §6: "AO makes decisions and owns lawful procurement dispositions." §8 `AWD_VALIDITY_EXPIRED` resolution: "HOP records lawful disposition." §5.5: already given notices "require a recorded legal disposition" with no owner. Who records it is contradictory. |
| F8 | B | D06 vs §13, §5.9 | D06 shows "**Head of Procurement: Charles Mutiso**" beside "**Next: Prepare contract**". §5.9 names the holder as "Contracting owner / Prepare contract" and §13 says Charles acts "in a separately authorised Contracting capacity; the Award role alone does not grant that future capability". The D06 label attributes the Contracting task to the HOP role. |
| F9 | B | §5.9 vs §8 | Same condition, two texts. §5.9: "Contracting is unavailable. KenTender will check that the award can still proceed before sending it." `AWD_CONTRACTING_UNAVAILABLE`: "Contracting is unavailable. KenTender will retry and check that the award can still proceed." |
| F10 | B | §5.4, §5.9 vs D05, §8 | §5.4 distinguishes legal "giving" from delivery ("A queued job, email service acceptance, portal creation or read receipt is not automatically legal proof of giving"). D05 says "**All required notices delivered**"; `AWD_NOTICE_FAILED` and the §5.9 row say "has not been delivered". The Act's §135(3) term is "giving of that notification". |
| F11 | B | §5.9 table vs V16 | Technical task for notice failure is "Resolve notice delivery" in §5.9 and "**Restore notice delivery**" on V16. The receiver case uses "Restore Contracting delivery". One name per task is needed. |
| F12 | B | §5.4 vs §7 | Notification status values "Not issued / Issue in progress / Issued / Unknown" (§5.4) vs "No decision recorded / No notification issued" (§7 authority-status service). Two vocabularies for one fact. |
| F13 | B | §7 `RecordAwardCorrectionDecision` | It may produce "a new linked decision", but unlike `RecordAwardDecision` it does not authorise a notice batch. A changed award would need revised notices; §5.7 defers these to "a verified legal treatment". The command contract should say the new decision issues nothing until then. |
| F14 | B | §5.5, §5.8 condition 3 | Condition 3 requires "timely, valid written acceptance". A late acceptance "does not silently revive eligibility" and creates HOP review, but no outcome of that review can satisfy condition 3. Either late acceptance can never proceed in MVP 1 (state it), or the disposition route is missing. |
| F15 | B | §5.9 next-step table | No row for the AO's Decide correction. V17 uses "**Decide the reported correction.**"; the table only has HOP's "Review the report correction before this award proceeds." |
| F16 | C | §10.1 fixture instants | The exception list names V03/V04, V08, V10, V11 but omits V07, which states its own instant (24 Jun 17:01) in the §10.3 row. |
| F17 | C | §10.3 intro vs V18 | "Each internal variant retains D02's tender/record header", but V18 uses tender TND-MOH-2027-036. V18 should be named as the exception. |
| F18 | C | AWD-AC-022 | "Stage transitions, labels and task closure match §10": the transitions are defined in §5.9. |
| F19 | C | Control table | The "Review amendment" changed content while keeping v0.1. The protocol requires a version bump for revisions and a change register. The document has neither a change register nor a preservation record for the amendment. |

Fixture arithmetic checked: D03 decision 17 Jun 10:00 + 14 days = 1 Jul 10:00; the test term 2 Jul 09:00 is later, as §13 states. V03/V04 (11 Oct 09:00) fall after validity (10 Oct 11:00). V07 (24 Jun 17:01) falls after the reply deadline (24 Jun 17:00). V11 (17 Jun 09:30) falls after the opinion signature (09:10) and before the decision (10:00), consistent with "Opinion Done; Decision Blocked". No arithmetic errors found.

## 4. Legal cross-check (Act, Revised Edition 2022, read in full)

Consistent with the Act as read:

- §84(1) HOP "review the tender evaluation report and provide a signed professional opinion to the accounting officer"; §84(3) AO "shall take into account the views of the head of procurement".
- §87(1) notification "Before the expiry of the period during which tenders must remain valid"; §87(2) acceptance "in writing within the time frame specified in the notification"; §87(3) unsuccessful notices at the same time, "disclosing the successful tenderer as appropriate and reasons thereof"; §87(4) notification "does not form a contract".
- §135(3) "not before fourteen days have elapsed following the giving of that notification provided that a contract shall be signed within the tender validity period".
- §63(1) AO may terminate "prior to notification of tender award".
- §168: on a request for review, the Review Board Secretary notifies the AO of "the suspension of the procurement proceedings".
- §142(1) performance security is submitted "before signing of the contract".
- Page citations in §17.1 (pp. 48–50, 66–69, 77–78) match the printed pages.

Points for the owner:

- L1 — **Ties (V18).** §131(a) allows competitive negotiations where "there is a tie in the lowest evaluated price by two or more tenderers". The document excludes negotiation from MVP 1. V18 is correct for MVP 1, but the record should name §131 as the lawful route outside scope, as §2 requires ("A lawful route outside this scope requires a separately controlled process").
- L2 — **Decline and refusal (V06).** §136(1): if the successful tenderer refuses to sign, "the procurement process shall proceed with the next lowest evaluated tenderer", and §136(2) disapplies this once validity has expired. §5.8 leaves §136 with the owner. V06's **Record next action** gives no pointer to it. Whether a §87(2) decline is treated as a §136 refusal is a legal question the document does not answer.
- L3 — **§138 ownership.** §138(1) requires the AO to "publish and publicise all contract awards". The document assigns §138 to Contracting (§5.8, AWD-IF-05). Whether publication follows award or contract signature is an interpretation that should be recorded in the legal operating profile.
- L4 — **Cancellation cut-off.** §63(1) uses "notification of tender award". The document closes the route "Once any required notice is given", which is the more conservative reading. Record it as a chosen interpretation.
- L5 — **Extension.** §88(1) and (3): the AO may extend before expiry, "not more than thirty days and may only be done once", with written notice to every tenderer (§88(2)). §5.5 says only "within the applicable limit". Quoting the limit would help Tenders' interface (AWD-IF-02).

Not verified: amendments after the 2022 revision, the 2020 Regulations, court orders, and whether the 2022 edition is current on 30 September 2026. The document says the same in §15.

## 5. Cross-document statements not verified

Every claim about another document's content or version is unverified in this review, including: the KT-STD-001 §8 actors (Charles Mutiso, Amina Hassan, Daniel Otieno); BDS v0.8's Mary Wanjiku and David Ouma; EVL v0.4's report 1 fixture (14:07:01 EAT, three signatures) and tender 036 tie fixture; STD-TPL-001 v0.10's template key `IT-EQUIPMENT-OPEN-V1` and profile `GOODS-IT-SIMPLE-V1`; all approval dates and versions in §17.1; and the register entry claimed in §17.2.

## 6. New content in the document to flag for owner review

The document's §10 fixtures are self-declared synthetic. Values not traceable to a supplied source: tender 037 and Jirani's KES 45,900,000; V18's title "Supply and delivery of office laptops"; the reply deadline 24 Jun 17:00; the test contracting instant 2 Jul 09:00; the 36-month warranty; validity 10 Oct 2027 11:00.

## 7. Decisions needed (with recommendation)

1. **F1 marker rule.** Recommend: Acceptance and wait is Current until every §5.8 condition 1–6 holds; Send to Contracting becomes Current (or Blocked) only while delivery is being attempted.
2. **F3 after No award.** Recommend: a post-No-award correction opens a linked successor decision cycle on the same case and records "Closed" as the prior cycle's outcome.
3. **F4/F5 dialog fields.** Recommend adding a **Type** choice (Authoritative order / Reported challenge) to Record restriction and fixed **Outcome** options to Record outcome.
4. **F7 disposition owner.** Recommend: HOP records; AO decides where the disposition changes a decision.
5. **F14 late acceptance.** Recommend: state that late acceptance cannot satisfy condition 3 in MVP 1 and routes to Record next action.
6. **L1/L2.** Owner and legal reviewer to decide how §131 and §136 are referenced.

## 8. Required corrections elsewhere

None asserted. Sibling documents were not read.

## 9. Design impact

F1, F4, F5, F8, F9, F10 and F11 change artboard content (markers, dialog fields, labels, copy). Resolve them before building D05, D06, V08–V10, V16, V17 and the dialogs. The remaining boards (D01–D04, D07, V01–V07, V11–V15, V18) can be designed from §10 as written.
