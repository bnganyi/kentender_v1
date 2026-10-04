# BDS-CHG-001 v0.8 — design-readiness review

Review only. No document edited. Date 26 Sep 2026.

## 0. Re-review — updated file `…v0_8-99a33eae.md`

Line-diff against the first v0.8 file: 61 lines replaced, 106 added (2419 → 2484). No approved content was dropped without a replacement line. All `BDS_*` codes, including the new `BDS_SIGNATORY_CERTIFICATE_REQUIRED` and `BDS_CUSTODY_REJECTED`, are defined in §8.

**Resolved:** A1 (inventory now lists every §10.19 state; the 10.19 intro makes each row "a required variant of its §10.18 artboard"), A3, A4, A5, B1 (explicit precedence, line 1488), B2 (line 837), B3, B4, B5, B6, C1 (new BDS-DES-17 Receipt history, §10.20), C2, C3 (for DES-02 only), C4, C5, C6, D1, D2, D3, D5.

**Still open or new:**

R1. **Control table not updated.** Version, date and revision record (lines 6–9) are unchanged even though the content changed materially: a new artboard, two new error codes, three new actors and new variants. The protocol expects a new versioned file (e.g. v0.9, or a dated revision note) so the earlier v0.8 stays as evidence. Owner decision.

R2. **Signing-service and custody-service outages share one code.** BDS08-AC-010 (2062) requires "distinct reason codes" for the missing certificate, signing-service outage, custody-service outage and definitive rejection. §5.13 line 650 still maps "Enabled trust, time or custody service unhealthy" to `BDS_SUBMISSION_SERVICE_UNAVAILABLE`, and §5.12 has no signing-service row (only "Enabled service unhealthy; Mary", 622, "restoring electronic submission").

R3. **Draft numbering terms drift.** DES-05 row (1149) and DES-06 fixture (1163) now say "Working draft revision 7". §10.1 Bid (919), DES-05 fixture (1141), DES-07 (1202), DES-11 (1304), DES-12 (1333) and §13.3 (1767) still say "Draft Version 7". DES-13 says "Submitted bid Version 1" (1374). Pick one term.

R4. **DES-02 variants without fixture instants** (conflicts with BDS08-AC-009, "No designer invents a time"). DES-02-DRAFT: "its isolated in-progress fixture" (1085), with no time given. DES-02-SUBMITTED (1086): viewer and time not stated, and the base viewer is now Peter, who can't see Afya's receipt. The "candidate/general question" variant in §10.18 (1467) has no ID or fixture. It must fall before 27 May to show **Ask a question**.

R5. **DES-08-JV has no fixture.** The only JV fixture (875) is Kisiwa–Jua on 20 May and "creates no Afya workspace", while DES-08 is David/Afya at 10 Jun. The JV variant has no bid, declarations or signatory to show.

R6. **DES-07 notice states have no instants.** Queued, Sent and Delivery problem (1222–1224) reuse "the same current Tender facts", but it isn't stated which notice (addendum of 31 May, or clarification answer of 26 May) or at what time.

R7. **DES-06 gate, outage and CFG variants: viewer unstated.** The §5.12 rows for gate, outage and CFG-ready name Mary or "signatory". DES-06's default viewer is David, and §10.19 has no DES-06 row for gate or outage (1505 and 1508 name DES-12 only). The next-step line for David in these states is undefined.

R8. **Brian Wafula** (1747) is described as "from the coordinated Tender fixture". TPR wasn't supplied, so I couldn't verify this.

R9. **KT-STD-001 v1.8 §2.9** is still not supplied (A2). The tracker and next-step block can't be drawn to the standard without it.

**Design impact now:** 17 artboards. DES-17 is new, and the inventory has grown by about 25 variants. All of them are required at both sizes, and none has a desktop-only exemption.

## 1. Files
- Reviewed: `uploads/KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_8.md` — v0.8, Proposed, not approved (control table lines 7–11).
- Compared against: v0.4 in `uploads/` (the predecessor v0.7 was **not supplied**, so no preservation check against it was possible).

## 2. Read list
- Read in full: control table and §1 (1–48); §§5.10–5.14 (563–672); §9 (796–815); §10.1–10.19 (816–1482); §13.2–13.4 (1678–1742); §14.15 (1988–1999); §18.1–18.2 (2157–2184); §19.13 (2409–2419).
- Read in part: §8 (error codes only, scripted check).
- Not read: §§2–4, 5.1–5.9, 6–7, 11, 12, 14.1–14.14, 15–17, 19.1–19.12.
- Not supplied: KT-STD-001 v1.8 (esp. §2 and §2.9, which §10 line 818 says must accompany this section), baseline register KT-DOC-CTRL-001, TPR-CHG-001 v0.12/v0.13, CFG-CHG-002 v0.16, v0.7 of this document.

## 3. Mechanical checks (scripted)
- Every `BDS_*` code used anywhere appears in §8. No orphan codes.
- Owner-document versions are internally consistent (KT-STD-001 v1.8 ×11, CFG v0.16, TPR v0.12 approved / v0.13 proposed). No stale v1.7 / v0.15 references outside "read:" notes.
- All §13.2 actors used in §§5.12–5.14 and §10.19 (Nadia Kamau, Amina Yusuf, Daniel Otieno) are defined at 1686–1688.

## 4. Findings — verified in the text

Marked **[new in v0.8]** or **[pre-existing]** (present in v0.4).

### A. Blocking for design

A1. **§10.19 requires variants §10.18 does not list** [new in v0.8]. BDS08-AC-004 (1995) says "All §10.19 variants render at the §10.18 sizes", but these §10.19 rows have no inventory row or defined composition:
- "DES-04 Suspended" (1459) — §10.5 defines only ATTENTION and VERIFY; §10.18 DES-04 lists "Incomplete Account; Pending verification".
- "DES-06/11 CFG information incomplete" (1468), "DES-11/12 CFG information incomplete" (1469).
- "DES-12 definitive rejection" (1472) — §10.13 folds it into SERVICE ("Try confirmation again only when the server says the earlier attempt definitely failed").
- "DES-13 accepted receipt, David" (1474).
- "DES-06 unsubmitted Draft after deadline" (1477).
- "DES-06 existing Draft bound to Withdrawn release" (1478).
- "DES-06 production gate / outage" (§10.7 line 1161 describes it; no variant ID).

A2. **KT-STD-001 v1.8 §2.9 not supplied.** §10.19 (1450) makes the next-step block and tracker "the shared KT-STD-001 v1.8 §2.9 components". Their anatomy, marker rendering (C/D/N/B) and reduced-tracker form can't be drawn faithfully without it.

A3. **DES-02 base fixture time contradicts its content** [pre-existing]. Fixture is 20 May 2027, 10:05 (1051), yet the deadline strip says "Clarifications closed 27 May 2027, 17:00 EAT" (1057), and the page shows ADD-MOH-2027-033-001 (issued 31 May), the clarification answer (26 May) and deadline 12 Jun (set by the addendum; original 5 Jun, line 853). On 20 May none of these exist and the clarification period is open.

A4. **DES-07 base fixture vs. Ask-a-question** [partly new]. Fixture is 1 Jun 2027, 12:05 (1175), after the 27 May clarification deadline, so per 1184 "Ask a question" is absent and "Clarifications closed" shows — making base and BDS-DES-07-CLOSED (1193) the same state. The dialog success "Question received 26 May 2027, 09:00 EAT" (1187) needs a pre-deadline fixture in which the addendum does not yet exist. BDS-DES-07-NONE (1191) keeps "Ask a question… while the clarification period is open" but no time is given.

A5. **Signature-unavailable holder conflict** [new in v0.8]. §10.19 (1470) says "Technical operator Daniel Otieno is restoring … digital signing". The fixture is Mary's own certificate: "no approved certificate is available for Mary" (1013) / "Mary has authority but no valid approved test certificate" (1729). §5.12 and §5.13 have no signature-unavailable row or guard, so the holder, headline and reason code aren't defined anywhere authoritative.

### B. Conflicts the design must resolve one way

B1. **§10.19 "replace" instructions vs. page-header specs.** §10.19 replaces "Ready-to-submit narrative/badge" (1464), "Ready badge" (1467, 1469, 1470), "duplicate attention banner" (1462) and the DES-13 "Before the deadline status line" (1473). The page specs still require: DES-06 badge Ready to submit (1145); DES-06-ADDENDUM amber panel (1166); DES-11 badge + green result Ready to submit (1277, 1282); DES-12 badge Ready to submit (1304); DES-13 section "Before the deadline" with its text (1340). No precedence rule is stated. Recommendation: §10.19 wins; keep factual task/receipt states.

B2. **Tracker on task pages** [new in v0.8]. §10.19 (1461) places the P/S/R tracker on DES-08–10; §10.1 (833) says "task pages do not repeat a large progress stepper". Reconcilable (3-stage journey ≠ 5-task stepper) but worth stating, since the earlier board review removed steppers from DES-06.

B3. **DES-13 David / closed headline** [new in v0.8]. §10.19 row 1474 joins "David; deadline passed" under "Done: Bid Version 1 was accepted on …", but §5.12 gives the after-deadline state a different headline: "Done: Bid Version 1 remains submitted; submission changes closed at 12 Jun 2027, 11:00 EAT." DES-13-CLOSED's viewer isn't stated.

B4. **Definitive rejection wording.** §10.17 "Definitive custody failure" heading reads "Electronic submission is temporarily unavailable" (1416) while §5.12/10.19 say "The tender box rejected this attempt; no bid was submitted." §5.13 also gives definite rejection the same code as an unhealthy service, `BDS_SUBMISSION_SERVICE_UNAVAILABLE` (647–649), while the next-step holder differs (Mary vs Daniel).

B5. **Addendum-attention action label.** DES-11-ADDENDUM-ATTENTION primary is "Fix item" (1294); §5.12/§10.19 name the fix "Review addendum" (1462).

B6. **DES-06 base = DES-06-REPRESENTATIVE** [pre-existing]. Base fixture is already David viewing the Ready Draft (1143); the variant is "same Ready fixture for David" (1168).

### C. Missing facts (designer would have to invent)

C1. **Receipt history** `/account/receipts` (§9, 806) has no artboard, yet "View receipts" is the action in DES-04 Suspended, DES-16 Suspended and the submitted-bidder CFG variant [pre-existing route; actions partly new].
C2. **TND-MOH-2027-041** (withdrawal fixture) has no deadline or title, yet DES-14-WITHDRAWN says "start a new bid before the deadline" (1476) and the withdrawal dialog shows "deadline" (1365).
C3. **Joint venture**: Tender fixture never says JVs are permitted (condition at 1068); no JV name, lead, members or agreement file for DES-02-JV-START / DES-08-JV [pre-existing].
C4. **"View question"** after question success (1187) and **"View notice"** (Cancelled) have no destination.
C5. **Notice contacts** section on DES-04 (1111): only one verified email exists in fixtures; verification status wording not given.
C6. **Response drawer** (DES-09) has no size; §10.1 sizes dialogs only (531).

### D. Minor / judgement

D1. §5.14 "Account access suspended" row: next holder Amina Yusuf, but Notification "Yes, Daniel" (663) [new in v0.8]. Likely should be Amina.
D2. "2 days remaining" at 10 Jun 14:20 → 12 Jun 11:00 is 1 d 20 h 40 m (1151) [pre-existing]. Rounding rule not stated.
D3. DES-11 "seven declarations confirmed" (1289) while two fixture rows read "Complete", not "Confirmed" (918, 924).
D4. Two version counters (Draft Version 7 → Submission Version 1; Replacement Version 2/3) sit side by side on DES-06/12/13; wording is correct but easy to misread.
D5. §10.1 "warm-white background" (826) differs from the bound design system ground (`--color-bg`); design follows the design system.

## 5. Design impact on the current board
- Shell chrome is now mandatory: public header (Tenders / My bids / Account) and a quiet footer with Supplier support, Privacy and data use, Terms of portal use, Accessibility (828–829); DES-15 needs the Desk header and breadcrumb **Tender-security receipts** (837). The board currently has no shell chrome.
- Next-step block + P/S/R or S/V/A tracker on DES-03, 04, 06, 07–14 per §10.19; absent on DES-01, 02 public, 05, 15, 16 and dialogs.
- New variants to draw: DES-02 JV-START (+notice email), SUPERSEDED, WITHDRAWN-RELEASE, question-before-start helper; DES-04 notice-contacts section; DES-06 gate/outage; DES-07 dialog/success, NONE, CLOSED, NOTICE, Queued, Sent; DES-08 Tender notice email + ACCOUNT-UPDATE; DES-12 GATE; DES-16 six new rows (1408–1414, 1417).
- §10.18 still requires every variant and dialog at 390 × 844 (1447). Currently those are desktop-only.

## 6. Decisions needed (owner)
1. Precedence: does §10.19 override conflicting header/badge/banner text in §§10.7–10.14 (B1)? Recommend yes.
2. Add the A1 variants to §10.18, or treat §10.19 rows as content-only (no extra artboards)? Recommend adding the ones with distinct screens (DES-04 Suspended, DES-06 deadline-passed, DES-06 withdrawn-release, DES-06 gate) and treating the rest as copy variants of existing artboards.
3. Signature-unavailable holder: Mary (obtain certificate) or technical operator (A5)? Recommend Mary, add §5.12/§5.13 rows.
4. Re-time DES-02 base (e.g. 1 Jun 2027) or strip post-20-May content (A3); give DES-07 dialog/NONE a pre-deadline fixture (A4).
5. Supply C1–C3 fixture facts or approve placeholders.
6. Confirm D1 (Amina vs Daniel).

## 7. Required corrections elsewhere
- None identified in owner documents from this read; KT-STD-001 v1.8 §2.9 and TPR v0.13 not read.

## 8. Not verified
- Anything in KT-STD-001 v1.8, TPR, CFG, STD-TPL, the baseline register.
- Preservation against v0.7 (not supplied).
- Sections listed as not read in §2.
- `consistency_check.py` / `register_check.py` were not run; checks above are scripted equivalents on this file only.
