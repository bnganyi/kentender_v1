# BDS-CHG-001 v0.8: artboard inventory

| Control | Value |
|---|---|
| Version | 0.8-phase0.1 |
| Status | Phase 0 working document (plan BDS-CHG-001 v0.8) |
| Purpose | Phase 0 reconciliation input (plan Phase 0; spec BDS-CHG-001 v0.8 §10.18 and BDS04-AC-004). Maps every design-board artboard to its implementing screen, slice and status. |
| Source | `design/Bid Board v3 - A…E *.dc.html`, extracted by script on 26 Sep 2026 from every `data-screen-label` attribute and its caption span. Captions are quoted from the boards; they are fixture context outside the artboard frame. |
| Frames | Every label below holds a 1440 × 1024 desktop frame and a 390 × 844 narrow frame (BDS-CHG-001 §10.1; BDS-CHG-001 §10.18 "Required render sizes"). An inventory row is complete only when both frames are proven (BDS04-AC-004). |
| Totals | 79 labels: 73 Covered, 3 Conditional, 3 Replaced. |
| New content | The "Screen component", "Owner" and "Slice" columns are plan proposals (implementation plan Phase 11), not spec content. |

Board files: A = `Bid Board v3 - A Public and Account.dc.html`; B = `Bid Board v3 - B Workspace and documents.dc.html`; C = `Bid Board v3 - C Company requirements and price.dc.html`; D = `Bid Board v3 - D Review and submission.dc.html`; E = `Bid Board v3 - E Desk and common states.dc.html`.

Status meanings:
- **Covered**: built and compared structurally at both sizes.
- **Conditional**: the spec makes the variant conditional on approval of proposed TPR-CHG-001 v0.13 (BDS-CHG-001 v0.8 §18.1, BDS08-AC-008). It is not built until then.
- **Replaced**: owner decision OD-G of 26 Sep 2026 replaces the drawn DES-15 composition with a blind physical-original intake. There is no board for the replacement; a redraw is a design follow-up.

Label forms the fidelity tooling must map to canonical IDs:
- **Combined:** `BDS-DES-06 / BDS-DES-06-REPRESENTATIVE`, `BDS-DES-07-QUESTION-OPEN / BDS-DES-07-NONE`. The spec allows both merges (BDS-CHG-001 §10.7 "Do not produce a second identical artboard"; BDS-CHG-001 §10.8 "(also BDS-DES-07-NONE)").
- **Suffixed:** `· in preparation`, `· ready`, `· success`, `notice pending · Queued`, `notice pending · Sent`.
- **Dialog:** `confirmation dialog`, `response drawer`, `withdrawal dialog`, `record dialog`.
- **DES-16:** one catalogue artboard of the BDS-CHG-001 §10.17 rows, drawn as cells. Each live common state is compared with its cell.

| Board:line | Label | Board caption (fixture context) | Screen component | Owner | Slice | Status | Prerequisite |
|---|---|---|---|---|---|---|---|
| A:29 | `BDS-DES-01` | Signed-out public visitor · 20 May 2027, 10:00 EAT | AvailableTendersScreen | BDS | 11.1 | Covered | — |
| A:30 | `BDS-DES-01-EMPTY` | Filtered empty · header and filters kept | AvailableTendersScreen | BDS | 11.1 | Covered | — |
| A:34 | `BDS-DES-02` | Peter Mwangi, Supplier Representative, Kisiwa Digital Limited · no workspace · 1 Jun 2027, 12:15 EAT | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:35 | `BDS-DES-02-SIGNED-OUT` | Public visitor · 1 Jun 2027, 12:15 EAT | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:36 | `BDS-DES-02-JV-START` | Peter Mwangi · 20 May 2027, 10:05 EAT · original deadline · Who is bidding? step | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:37 | `BDS-DES-02-DRAFT` | David Ouma · 20 May 2027, 10:05 EAT · Afya Draft Version 3 | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:38 | `BDS-DES-02-SUBMITTED` | Mary Wanjiku · 10 Jun 2027, 14:33 EAT · Afya receipt RCPT-MOH-2027-033-001 | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:39 | `BDS-DES-02-CANDIDATE-QUESTION` | David Ouma · 26 May 2027, 08:50 EAT · before the clarification deadline | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:40 | `BDS-DES-02-CANCELLED` | Cancelled Tender TND-MOH-2027-034 | TenderOverviewScreen | BDS | 11.2 | Covered | — |
| A:41 | `BDS-DES-02-SUPERSEDED` | Conditional on TPR-CHG-001 v0.13 approval · Peter Mwangi · 1 Jun 2027 | TenderOverviewScreen | BDS | 11.2 | Conditional — TPR-CHG-001 v0.13 approval (Phase 13) | — |
| A:42 | `BDS-DES-02-WITHDRAWN-RELEASE` | Conditional on TPR-CHG-001 v0.13 approval · Mary Wanjiku with a current Submitted bid | TenderOverviewScreen | BDS | 11.2 | Conditional — TPR-CHG-001 v0.13 approval (Phase 13) | — |
| A:46 | `BDS-DES-03` | Mary Wanjiku · New Account · 18 May 2027, 09:00 EAT | RegisterScreen / VerifyScreen | ACC | 11.3 | Covered | — |
| A:47 | `BDS-DES-03-VERIFY` | After Create account · challenge sent to tenders@afyadigital.example | RegisterScreen / VerifyScreen | ACC | 11.3 | Covered | — |
| A:51 | `BDS-DES-04` | Mary Wanjiku, Authorised Signatory · Active · 18 May 2027, 10:00 EAT | AccountScreen | ACC | 11.4 | Covered | — |
| A:52 | `BDS-DES-04-ATTENTION` | Organisation incomplete · official phone empty | AccountScreen | ACC | 11.4 | Covered | — |
| A:53 | `BDS-DES-04-VERIFY` | Pending verification · 18 May 2027, 09:05 EAT | AccountScreen | ACC | 11.4 | Covered | — |
| A:54 | `BDS-DES-04-SUSPENDED` | Account suspended · 10 Jun 2027, 14:20 EAT | AccountScreen | ACC | 11.4 | Covered | — |
| A:58 | `BDS-DES-05` | David Ouma · 10 Jun 2027, 14:20 EAT · Draft Version 7 Ready to submit | MyBidsScreen | BDS | 11.5 | Covered | — |
| A:59 | `BDS-DES-05-SUBMITTED` | Submitted bid Version 1 · 10 Jun 2027, 14:32 EAT | MyBidsScreen | BDS | 11.5 | Covered | — |
| A:60 | `BDS-DES-05-WITHDRAWN` | Withdrawal fixture · TND-MOH-2027-041 | MyBidsScreen | BDS | 11.5 | Covered | — |
| A:61 | `BDS-DES-05-EMPTY` | No bids | MyBidsScreen | BDS | 11.5 | Covered | — |
| A:65 | `BDS-DES-17` | David Ouma · 12 Jun 2027, 11:00:01 EAT · /account/receipts | ReceiptHistoryScreen | BDS | 11.5 | Covered | — |
| A:66 | `BDS-DES-17-EMPTY` | No receipts | ReceiptHistoryScreen | BDS | 11.5 | Covered | — |
| A:67 | `BDS-DES-17-SUSPENDED` | Suspended Account · read-only | ReceiptHistoryScreen | BDS | 11.5 | Covered | — |
| B:29 | `BDS-DES-06 / BDS-DES-06-REPRESENTATIVE` | David Ouma · Draft Version 7 · 10 Jun 2027, 14:20 EAT · all preparation complete | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:30 | `BDS-DES-06-SIGNATORY` | Mary Wanjiku · same Ready Draft · 10 Jun 2027, 14:20 EAT | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:31 | `BDS-DES-06-IN-PROGRESS` | David Ouma · isolated in-progress fixture | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:32 | `BDS-DES-06-ADDENDUM` | David Ouma · 1 Jun 2027, 12:05 EAT · Draft Version 4 · addendum review | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:33 | `BDS-DES-06-GATE` | Mary Wanjiku · 10 Jun 2027, 14:20 EAT · production gate disabled | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:34 | `BDS-DES-06-OUTAGE` | Mary Wanjiku · 10 Jun 2027, 14:20 EAT · enabled custody-service outage | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:35 | `BDS-DES-06-CFG-INCOMPLETE · in preparation` | David Ouma · in-progress Draft · 10 Jun 2027, 14:20 EAT | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:36 | `BDS-DES-06-CFG-INCOMPLETE · ready` | Mary Wanjiku · otherwise Ready · 10 Jun 2027, 14:20 EAT | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:37 | `BDS-DES-06-CLOSED-UNSUBMITTED` | Unsubmitted Draft · trusted time 12 Jun 2027, 11:00:01 EAT | BidWorkspaceScreen | BDS | 11.6 | Covered | — |
| B:38 | `BDS-DES-06-WITHDRAWN-RELEASE` | Conditional on TPR-CHG-001 v0.13 approval · existing Draft, bound release Withdrawn | BidWorkspaceScreen | BDS | 11.6 | Conditional — TPR-CHG-001 v0.13 approval (Phase 13) | — |
| B:42 | `BDS-DES-07` | David Ouma · 1 Jun 2027, 12:05 EAT · Draft Version 4 · addendum effective, not acknowledged · clarification closed | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:43 | `BDS-DES-07-COMPLETE` | 1 Jun 2027, 12:10 EAT · Draft Version 5 · acknowledged | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:44 | `BDS-DES-07-QUESTION-OPEN / BDS-DES-07-NONE` | David Ouma · 26 May 2027, 08:50 EAT · original deadline · no addendum | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:45 | `BDS-DES-07-QUESTION-OPEN-DIALOG` | Ask-a-question dialog · 26 May 2027 | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:46 | `BDS-DES-07-QUESTION-OPEN-DIALOG · success` | Question sent · 26 May 2027, 09:00 EAT | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:47 | `BDS-DES-07-CLOSED` | 28 May 2027, 12:00 EAT · before the addendum | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:48 | `BDS-DES-07 notice pending · Queued` | Addendum notice Queued · 31 May 2027, 09:01 EAT | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:49 | `BDS-DES-07 notice pending · Sent` | Addendum notice Sent without delivery proof · 31 May 2027, 09:02 EAT | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| B:50 | `BDS-DES-07-NOTICE` | Addendum notice Failed · 31 May 2027, 09:15 EAT | DocumentsTaskScreen | BDS | 11.7 | Covered | — |
| C:29 | `BDS-DES-08` | David Ouma · 10 Jun 2027, 10:05 EAT · complete | CompanyTaskScreen | BDS | 11.8 | Covered | BDS-G03 (release 1.2) first |
| C:30 | `BDS-DES-08-SECURITY` | Physical original not recorded · Review note | CompanyTaskScreen | BDS | 11.8 | Covered | BDS-G03 (release 1.2) first |
| C:31 | `BDS-DES-08-JV` | Peter Mwangi · 20 May 2027, 10:15 EAT · BID-MOH-2027-033-002 Draft Version 1 | CompanyTaskScreen | BDS | 11.8 | Covered | BDS-G03 (release 1.2) first |
| C:32 | `BDS-DES-08-ACCOUNT-UPDATE` | Account address changed after bid start | CompanyTaskScreen | BDS | 11.8 | Covered | BDS-G03 (release 1.2) first |
| C:36 | `BDS-DES-09` | David Ouma · 10 Jun 2027, 11:30 EAT · complete | RequirementsTaskScreen | BDS | 11.9 | Covered | BDS-G03 (release 1.2) first |
| C:37 | `BDS-DES-09 response drawer` | Opened from the Battery runtime row | RequirementsTaskScreen | BDS | 11.9 | Covered | BDS-G03 (release 1.2) first |
| C:38 | `BDS-DES-09-ATTENTION` | Product datasheet rejected after malware scan | RequirementsTaskScreen | BDS | 11.9 | Covered | BDS-G03 (release 1.2) first |
| C:39 | `BDS-DES-09-ADDENDUM` | Addendum review · changed delivery response | RequirementsTaskScreen | BDS | 11.9 | Covered | BDS-G03 (release 1.2) first |
| C:43 | `BDS-DES-10` | David Ouma · 10 Jun 2027, 12:15 EAT · complete | PriceTaskScreen | BDS | 11.10 | Covered | — |
| C:44 | `BDS-DES-10-INCOMPLETE` | Unit price empty | PriceTaskScreen | BDS | 11.10 | Covered | — |
| D:29 | `BDS-DES-11` | Mary Wanjiku · Draft Version 7 · 10 Jun 2027, 14:15 EAT | ReviewScreen | BDS | 11.11 | Covered | BDS-G03 (release 1.2) first |
| D:30 | `BDS-DES-11-EVIDENCE-ATTENTION` | Evidence rejected fixture only | ReviewScreen | BDS | 11.11 | Covered | BDS-G03 (release 1.2) first |
| D:31 | `BDS-DES-11-ADDENDUM-ATTENTION` | Addendum review fixture only | ReviewScreen | BDS | 11.11 | Covered | BDS-G03 (release 1.2) first |
| D:32 | `BDS-DES-11-REPRESENTATIVE` | David Ouma · same complete review | ReviewScreen | BDS | 11.11 | Covered | BDS-G03 (release 1.2) first |
| D:33 | `BDS-DES-11-CFG · in preparation` | David Ouma · Draft still in preparation | ReviewScreen | BDS | 11.11 | Covered | BDS-G03 (release 1.2) first |
| D:34 | `BDS-DES-11-CFG · ready` | Mary Wanjiku · otherwise Ready | ReviewScreen | BDS | 11.11 | Covered | BDS-G03 (release 1.2) first |
| D:38 | `BDS-DES-12` | Mary Wanjiku · 10 Jun 2027, 14:30 EAT · approved certificate available | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:39 | `BDS-DES-12 confirmation dialog` | Mary Wanjiku · final confirmation checked | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:40 | `BDS-DES-12-PENDING` | Submission attempt pending · correlation recorded | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:41 | `BDS-DES-12-CERTIFICATE` | Mary has no valid approved certificate | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:42 | `BDS-DES-12-SIGNATURE` | Valid certificate · signing service unhealthy | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:43 | `BDS-DES-12-SERVICE` | Enabled custody service unhealthy before deposit | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:44 | `BDS-DES-12-REJECTED` | Definitive rejection TBX-REJECT-033-01 | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:45 | `BDS-DES-12-CFG` | CFG information incomplete · otherwise Ready | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:46 | `BDS-DES-12-GATE` | Production gate disabled | SubmitScreen | BDS | 11.12 | Covered | BDS-G03 (release 1.2) first |
| D:50 | `BDS-DES-13` | Mary Wanjiku · Submitted bid Version 1 · 10 Jun 2027, 14:33 EAT | ReceiptScreen | BDS | 11.13 | Covered | — |
| D:51 | `BDS-DES-13-REPRESENTATIVE` | David Ouma · before deadline | ReceiptScreen | BDS | 11.13 | Covered | — |
| D:52 | `BDS-DES-13-CLOSED` | Mary Wanjiku · trusted time 12 Jun 2027, 11:00:01 EAT | ReceiptScreen | BDS | 11.13 | Covered | — |
| D:56 | `BDS-DES-14` | Mary Wanjiku · Replacement fixture · 11 Jun 2027, 08:30 EAT | ReplacementScreen | BDS | 11.14 | Covered | — |
| D:57 | `BDS-DES-14-REPLACED` | Submitted bid Version 2 accepted 11 Jun 2027, 09:15 EAT | ReplacementScreen | BDS | 11.14 | Covered | — |
| D:58 | `BDS-DES-14 withdrawal dialog` | Mary Wanjiku · TND-MOH-2027-041 receipt · 10 Jun 2027, before 15:00 EAT | ReplacementScreen | BDS | 11.14 | Covered | — |
| D:59 | `BDS-DES-14-WITHDRAWN` | Withdrawal acknowledgement WD-MOH-2027-041-001 | ReplacementScreen | BDS | 11.14 | Covered | — |
| E:29 | `BDS-DES-15` | Charles Mutiso, Procurement receipt owner · 10 Jun 2027, 10:00 EAT · internal Desk shell | TenderSecurityReceipts (Desk) | BDS | Phase 7 | Replaced — owner decision OD-G (blind intake); design follow-up | — |
| E:30 | `BDS-DES-15 record dialog` | Charles Mutiso · 10 Jun 2027, 10:00 EAT | TenderSecurityReceipts (Desk) | BDS | Phase 7 | Replaced — owner decision OD-G (blind intake); design follow-up | — |
| E:31 | `BDS-DES-15-RECORDED` | Recorded before deadline | TenderSecurityReceipts (Desk) | BDS | Phase 7 | Replaced — owner decision OD-G (blind intake); design follow-up | — |
| E:35 | `BDS-DES-16` | All BDS-CHG-001 §10.17 variants | CommonState | core portal runtime | 11.15 | Covered | — |
