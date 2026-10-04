# Review — AWD-CHG-001 v0.2 (Award)

Review only. No edit was made to the requirements document.

## 1. Files

- Input: `uploads/KenTender_AWD-CHG-001_Award_v0_2.md` — v0.2, "Proposed requirements — Project Owner review", 30 September 2026.
- Predecessor: `uploads/KenTender_AWD-CHG-001_Award_v0_1.md`. Its SHA-256 as held in this project is `95149a1ce07eea8b7191515af3c43c12588da62424403fe82c0ba4a8d3886b82`, which matches the value stated in v0.2 §18.1.
- Prior review: `reviews/AWD-CHG-001_v0_1_review.md`.

## 2. Read list

- Read in full: AWD-CHG-001 v0.2; the v0.1 review. The Act (Revised Edition 2022) was read in full during the v0.1 review. New legal wording in v0.2 was checked against that reading.
- Not read (not supplied): the baseline register, KT-STD-001, EVL, STD-TPL, TPR, BDS, PRC, TRUST, AUTH, LAW documents and the fixture register.
- Scripts: could not be run in this environment. There was no line-by-line preservation check; changes were checked manually against the §18.1 record.

## 3. Disposition of v0.1 findings

| Finding | Status in v0.2 | Evidence |
|---|---|---|
| F1 marker mapping | Resolved | §5.9 "Tracker mapping"; AC-028. D05 and V10 are consistent with it. |
| F2 correction-cycle stages | Resolved | §5.9 "Correction-cycle mapping" table; V19–V25. |
| F3 after No award | Resolved | §5.7: "There is no successor case"; §4 Decision cycle record; V21. |
| F4 restriction basis | Resolved | §5.10 **Basis for hold**; dialog in §10.3; §4 Review/order basis. |
| F5 outcome options | Partly resolved | §5.10 fixed outcomes; V08/V09/V21 choice lists. See N1 for **Record next action**. |
| F6 issue type | Resolved | §4 adds "Rules and notice audience". |
| F7 disposition owner | Resolved | §5.5, §6, §8 `AWD_VALIDITY_EXPIRED`. |
| F8 D06 label | Resolved | D06 "**Contracting owner: Charles Mutiso**". |
| F9 receiver message | Resolved | §5.9 and §8 now match. |
| F10 given vs delivered | Resolved | §5.4 labels; D05 "**All bidders have been notified**"; §8 `AWD_NOTICE_FAILED`. |
| F11 task names | Resolved | §5.9 splits HOP "Resolve notice delivery" from technical "Restore notice delivery". |
| F12 status vocabulary | Resolved | §7 canonical fields. |
| F13 corrected decision notices | Resolved | §5.7, §7, AC-031. |
| F14 late acceptance | Resolved | §5.5; §8 `AWD_RESPONSE_LATE`; V22. |
| F15 AO correction next step | Resolved | §5.9 row "AO correction decision". |
| F16 V07 instant | Accepted as dispositioned | §18.1 treats row instants as overriding the default. V19–V25 follow the same pattern. |
| F17 V18 header | Resolved | §10.3 intro. Introduces AWD-MOH-2027-036; see §6 below. |
| F18 AC-022 reference | Resolved | AC-022 now cites §5.9. |
| F19 versioning | Resolved | v0.2 with the §18.1 change record; the predecessor hash is verified above. |
| L1–L5 | Resolved | §2 (§131(a)); §5.8 (§136, §138); §5.4 (§63 cut-off); §5.5 (§88). The wording of §88 matches the Act: before expiry, once only, "not more than thirty days", written notice to every tenderer. |

## 4. New findings in v0.2

| # | Sev | Where | Finding |
|---|---|---|---|
| N1 | A | §10.3 Record next action (V06, V07); §7 `RecordAwardIssueDisposition`; §11 | The command now requires "one §5.10 outcome". The **Record next action** dialog has only **Reason** and **Next action**, with no Outcome, and §11 routes it to the same command. It is not stated which §5.10 outcome a decline (V06) or silence (V07) records. V06's note says "The Accounting Officer must decide the next procurement action", which points to **Request decision review**, but the dialog does not show it. |
| N2 | A | V25 journey vs §5.9 correction-cycle table | The table says "Notices Blocked until exact revised-notice authorisation exists, then Current during issue". V25 is the board where the AO has not yet authorised ("**Authorise the revised notices.**"), yet it shows "Notices Current". By the table it should be Blocked. Otherwise the table needs a third state for "ready, awaiting AO". |
| N3 | B | V25 "Earliest permitted date and time: 4 Jul 2027, 10:00 EAT" vs §4 clocks | §4: "Clocks are derived from retained authoritative events". Before authorisation no revised notice has been given, so there is no triggering event. The date can only be a projection. It should be labelled as one (for example "if notices are given on 19 Jun 2027, 10:00 EAT") or removed. The arithmetic itself holds: 19 Jun 10:00 + 14 days = 3 Jul 10:00, and 4 Jul 10:00 is later. |
| N4 | A | §4 domain model vs §5.8, AC-031 | §5.8 introduces "a durable publication obligation for that owner". §4 says "These records are the complete MVP 1 write model". No record, command or event in §4/§7 creates, holds or discharges that obligation, and nothing says whether Award or Contracting creates it. AC-031 tests it. |
| N5 | B | §5.9 next-step table vs V18, V21, V22, V24, V25 | Next-step texts used on boards have no row in the authoritative table: "Review the equal-price outcome." (V18, pre-existing in v0.1), "Review the correction to the closed award record." (V21), "Confirm the required notice treatment before this award proceeds." (V24), "Authorise the revised notices." (V25). V22 is supplier-facing. AC-022 requires every condition to yield an owner and explanation. |
| N6 | C | V17 vs V19 | The same correction instruction reason is worded two ways: "The reported calculation issue may affect the recommendation." (V17) and "The calculation issue may affect the recommendation." (V19). A recorded reason should read identically. |
| N7 | C | §5.10 AO list vs V23 positive alternative | §5.10 lists "Record corrected award" and "Authorise revised notices" separately. The V23 alternative uses a combined label, **Record corrected award and notify bidders**, which is allowed by §5.7 ("in the same action ... when all inputs are ready") but is not in the §5.10 list. |
| N8 | C | §2 | "HOP refers that route to AO outside MVP 1" (the §131 tie route). No board, dialog or outcome shows the referral. V18 ends at signing an opinion with No current recommendation. If the referral is the AO's Record no award next action, say so. |

## 5. Fixture checks (new boards)

- V17 (18 Jun 10:00) → V19 (18 Jun 10:05) → V20 (report 2 received 19 Jun 09:00; board 09:05) → V23 (opinion 2 signed 09:10; board 09:15): the sequence is consistent.
- V19 "Opinion Blocked" and V20 "Opinion Current" match the correction-cycle table.
- V21 (11 Oct 2027 10:00) follows V04's expired-validity No award (11 Oct 09:00). Its dialog offers Request corrected evaluation and Request decision review. §5.7 says a successor cycle "does not revive validity ... or permit an award", so both remain possible but cannot produce an award. That is consistent.
- V22 (24 Jun 17:01) and V07 (24 Jun 17:01) are isolated branches; no conflict.
- V24/V25 at 19 Jun 10:00 follow opinion 2 at 09:10; "Corrected award decision 2" is recorded at an unstated time in between. That is acceptable for an isolated branch.

## 6. New content for owner review

Identifiers and values in v0.2 that are not traceable to a supplied source: award record AWD-MOH-2027-036; "Decision cycle 2"; "Evaluation report 2" received 19 Jun 2027 09:00; "Professional opinion 2" signed 19 Jun 2027 09:10; "Corrected award decision 2"; "Revised notice 2"; reply by 26 Jun 2027 17:00; earliest 4 Jul 2027 10:00; issue type "Rules and notice audience"; the seven §5.10 outcome names; AC-028–031.

## 7. Not verified

- The register entry claimed in §17.2 ("admit AWD v0.2 as Project Owner review").
- All sibling-document versions and fixtures, as in the v0.1 review.
- Whether EVL v0.4 supports an "authorised corrected report" delivered into a successor cycle (AWD-IF-01).
- Amendments after the 2022 Act revision.

## 8. Decisions needed (with recommendation)

1. **N1.** Add an **Outcome** field to Record next action, limited to **Request decision review** and **Further action required**.
2. **N2.** Show V25 as Notices Current, and amend the table to "Blocked while treatment is unverified; Current once the exact batch is ready for AO authorisation and during issue".
3. **N3.** Label V25's date as a projection from the proposed giving time.
4. **N4.** Name the publication obligation as an owner-contract item under AWD-IF-05, created by Contracting from the Award decision event, so the Award write model stays closed.
5. **N5.** Add the four missing next-step rows.

## 9. Design readiness

- **Ready to design from §10 as written:** D01–D07 and V01–V05, V08–V20, V22 and V23.
- **Blocked by N1:** V06 and V07, because their Record next action dialog has no Outcome field.
- **Blocked by N2 and N3:** V25.
- **Buildable now, but copy may change when N5 is resolved:** V21 and V24. Their next-step text has no row in the §5.9 table yet.
