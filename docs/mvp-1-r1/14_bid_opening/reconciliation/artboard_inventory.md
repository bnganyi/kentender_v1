# BOP-CHG-001 v0.10: artboard inventory

| Control | Value |
|---|---|
| Version | 0.10-inventory.1 |
| Date | 29 September 2026 |
| Source | `../design/Bid Opening Artboards v0.9.2.dc.html`, board registry `const B = [...]` at line 1225 |
| Method | Script extraction of every registry entry. The actor, instant, spec reference and note columns are copied verbatim from the registry. Component#variant, slice and status are this plan's assignments. |

**Counts:** 52 registry entries. 50 are drawn boards (`st: "ready"`): 47 Covered and 3 Conditional. The other 2 are reviewer notes (`n00` Read me, `f00` Flags) and are not built. The board's own header reads "BOP-CHG-001 v0.10 (proposed) · PRC v0.9 · KT-STD-001 v1.9". Its Flags board lists four changes "Resolved in BOP v0.10" and says "Open: None from this review. BOP v0.10 is proposed and needs Project Owner approval."

**Statuses:**
- **Covered:** built class-for-class from the board.
- **Conditional:** built, but part of the pictured interaction depends on a provider that does not exist on this bench; the simulation stand-in is used and the dependency is named.
- **Replaced:** none.

**Components** are BOP-owned Vue roots:
- `PrepareOpening`, `OpenBids`, `OpeningRecord` and `CompletedRecord` are mounted under `/app/tenders/{tender}/opening…` (plan D9).
- `PublicOpening` is mounted in the BDS portal at `/tenders/{tender}` (plan D10).

| Board id | Code | Label | Actor | Pictured instant | Spec reference | Component#variant | Slice | Status | Note |
|---|---|---|---|---|---|---|---|---|---|
| a1 | 01 · APPOINT | Appoint committee | Amina Hassan, Accounting Officer | 10 Jun 2027, before 10:15 EAT | BOP v0.10 §10.2, §20 row 1 | PrepareOpening#APPOINT | 8.1 | Covered |  |
| a2 | 01 · INCOMPLETE | Needs an independent member | Amina Hassan | Before appointment, two members named | BOP v0.10 §10.2, §8 | PrepareOpening#INCOMPLETE | 8.1 | Covered | Appoint committee is omitted; the blocked block carries the fix. |
| a3 | 01 · APPOINTED | Appointed, publish next | Amina Hassan | 10 Jun 2027, 10:15 EAT | BOP v0.10 §10.2, §5 row 2 | PrepareOpening#APPOINTED | 8.1 | Covered |  |
| a4 | 01 · HOW TO ATTEND | Publish how to attend | Amina Hassan | 10 Jun 2027, 10:18 EAT | BOP v0.10 §10.2, §20 row 2 | PrepareOpening#HOW TO ATTEND | 8.1 | Covered | “What attendees can do” is my wording from the §10 fixture. |
| a5 | 01 · PUBLISHED | Attendance published | Amina Hassan | 10 Jun 2027, 10:20 EAT | BOP v0.10 §10.2 | PrepareOpening#PUBLISHED | 8.1 | Covered |  |
| p0 | 04 · DETAILS COMING | Before details are published | Visitor, signed out | Before 10 Jun 10:20 EAT | BOP v0.10 §5 row 2 | PublicOpening#DETAILS COMING | 9 | Covered |  |
| p1a | 04 · BEFORE JOIN OPENS | Published, join not open yet | Jane Wanjiku | 12 Jun 2027, 10:40 EAT | BOP v0.10 §10.5 | PublicOpening#BEFORE JOIN OPENS | 9 | Covered |  |
| p1 | 04 · JOIN | Join public opening | Jane Wanjiku | 12 Jun 2027, 10:58 EAT | BOP v0.10 §10.5 | PublicOpening#JOIN | 9 | Conditional | Join public opening hands the visitor to a configured attendance service (BOP v0.10 §10.5); no provider exists; an attendance-channel stand-in is used in simulation (plan D10). |
| p2 | 04 · READOUT | Readout in session | Jane Wanjiku | 12 Jun 2027, 11:02:30 EAT | BOP v0.10 §10.5, §10 completion row | PublicOpening#READOUT | 9 | Covered | Readout appears only after Charles’s 11:01:45 record. |
| p3 | 04 · REQUEST | Request register | David Ouma, verified submitting supplier | 12 Jun 2027, 11:11 EAT | BOP v0.10 §10.5 | PublicOpening#REQUEST | 9 | Covered |  |
| p4 | 04 · PREPARING | Register being prepared | David Ouma | 12 Jun 2027, 11:12 EAT | BOP v0.10 §10.5 | PublicOpening#PREPARING | 9 | Covered |  |
| p5 | 04 · READY | Download register | David Ouma | 12 Jun 2027, 11:13 EAT | BOP v0.10 §10.5 | PublicOpening#READY | 9 | Covered |  |
| p6 | 04 · NOT A SUBMITTER | No register request | Jane Wanjiku | After 11:10:30 EAT | BOP v0.10 §10.5 | PublicOpening#NOT A SUBMITTER | 9 | Covered | The “denied” variant: no request control, plain reason. |
| c1 | 02 · WAIT | Scheduled | Charles Mutiso, chair and recorder | 12 Jun 2027, 10:58:30 EAT | BOP v0.10 §10.3 WAIT, §5 timed kind | OpenBids#WAIT | 8.2 | Covered |  |
| c2 | 02 · WAITING TO JOIN | Member not joined | Charles Mutiso | 11:00:05 EAT, branch | BOP v0.10 §10.3 READY, §8 BOP_MEMBER_ABSENT | OpenBids#WAITING TO JOIN | 8.2 | Covered |  |
| c2b | 02 · ACCESS NOT READY | Secure access being checked | Charles Mutiso | 11:00:05 EAT, branch | BOP v0.10 §10.3 READY, §8 BOP_CREDENTIAL_UNAVAILABLE | OpenBids#ACCESS NOT READY | 8.2 | Conditional | BOP_CREDENTIAL_UNAVAILABLE depends on the custody/credential gateway health (plan D4); reachable only through the simulation control. |
| c2c | 02 · NOT AVAILABLE | Bid opening not available | Charles Mutiso | 12 Jun 2027, 11:00:41 EAT (branch 6) | BOP v0.10 §10 negative branch (6); §8 BOP_OPENING_PROFILE_UNAVAILABLE | OpenBids#NOT AVAILABLE | 8.2 | Covered | Shown only after the retried notification is committed. Support resolves at 11:06:00; Start opening at 11:06:20. |
| c2d | 02 · SUPPORT NOT NOTIFIED | Notification failed | Charles Mutiso | 12 Jun 2027, 11:00:05–11:00:40 EAT (branch 6) | BOP v0.10 §10 negative branch (6); §11 Notify support | OpenBids#SUPPORT NOT NOTIFIED | 8.2 | Covered | Charles uses Notify support at 11:00:40. Same incident, no new one. |
| c3 | 02 · READY | Ready to start | Charles Mutiso | 12 Jun 2027, 11:00:05 EAT | BOP v0.10 §10.3 READY, §20 row 4 | OpenBids#READY | 8.2 | Covered |  |
| c4 | 02 · OPEN NEXT BID | Started, open first bid | Charles Mutiso | 12 Jun 2027, 11:00:30 EAT | BOP v0.10 §10.3 ATTENDANCE, §11 | OpenBids#OPEN NEXT BID | 8.3 | Covered |  |
| c5 | 02 · READ ALOUD | Read these details aloud | Brian Wafula, member | 12 Jun 2027, 11:01:20 EAT | BOP v0.10 §10.3 OPEN / READOUT | OpenBids#READ ALOUD | 8.3 | Covered | 12 pages and price page 4 are §10 illustrative values. |
| c6 | 02 · RECORD READOUT | Record what was read aloud and pages | Charles Mutiso, recorder | 12 Jun 2027, 11:01:40 EAT | BOP v0.10 §10.3 OPEN / READOUT, §11 | OpenBids#RECORD READOUT | 8.3 | Covered | Page 1 is a proposal Charles can change. One action records the readout and the pages together. |
| c7 | 02 · REQUEST | Record request as answered | Charles Mutiso | 12 Jun 2027, 11:02:18 EAT | BOP v0.10 §10 procedural exchange | OpenBids#REQUEST | 8.3 | Covered |  |
| c8 | 02 · MEMBER’S ACCOUNT | Beatrice records her own account | Beatrice Kamau, Independent member | 12 Jun 2027, before 11:02:25 EAT (separate branch) | BOP v0.10 §10.3 OBSERVATION / DIFFERING ACCOUNT, §11 | OpenBids#MEMBER'S ACCOUNT | 8.3 | Covered |  |
| c8b | 02 · RESPONSE | Response to member’s account | Charles Mutiso | 12 Jun 2027, 11:02:40 EAT (separate branch) | BOP v0.10 §10.3 OBSERVATION / DIFFERING ACCOUNT | OpenBids#RESPONSE | 8.3 | Covered |  |
| c13 | 02 · COMMENT FOR EVALUATION | Record comment for Evaluation | Charles Mutiso | 12 Jun 2027, before 11:02:40 EAT (separate branch) | BOP v0.10 §10.3 FACTUAL EXCEPTION, §5.1 | OpenBids#COMMENT FOR EVALUATION | 8.3 | Covered |  |
| c13b | 02 · RECORDED FOR EVALUATION | Comment recorded | Charles Mutiso | 12 Jun 2027, 11:02:40 EAT (separate branch) | BOP v0.10 §10.3 FACTUAL EXCEPTION | OpenBids#RECORDED FOR EVALUATION | 8.3 | Covered |  |
| c9 | 02 · END OPENING | Readout complete, end | Charles Mutiso | 12 Jun 2027, 11:03:30 EAT | BOP v0.10 §10.3, §11 End opening | OpenBids#END OPENING | 8.3 | Covered |  |
| c10 | 02 · MEMBER LEFT | Paused, member left | Charles Mutiso | 11:02:10 EAT, branch 1 | BOP v0.10 §10 branch 1 | OpenBids#MEMBER LEFT | 8.4 | Covered |  |
| c10b | 02 · MEMBER REJOINED | Resumed after rejoin | Charles Mutiso | 11:05:10 EAT, branch 1 | BOP v0.10 §10 branch 1 | OpenBids#MEMBER REJOINED | 8.4 | Replaced | 30 Sep 2026 (Phase 8): resumption returns to the ordinary in-session view; no pending attendee request exists server-side (FU-BOP-21). |
| c11 | 02 · CANNOT OPEN | Bid pages cannot be shown | Charles Mutiso | 11:01:10 EAT, branch 2 | BOP v0.10 §10.3 UNREADABLE | OpenBids#CANNOT OPEN | 8.4 | Covered | Retry is disabled with its condition beside it. |
| c11b | 02 · RESOLVED | Retry opening | Charles Mutiso | 11:05:05 EAT, branch 2 | BOP v0.10 §10 branch 2 | OpenBids#RESOLVED | 8.4 | Covered |  |
| c11c | 02 · NOT RESOLVED | Waiting for Amina Hassan | Charles Mutiso | Branch 2, support cannot fix | BOP v0.10 §10.3 UNREADABLE, §5 row 6 | OpenBids#NOT RESOLVED | 8.4 | Covered |  |
| c11e | 02 · PAUSED, AO DECISION | Decide how to proceed | Amina Hassan, Accounting Officer | 12 Jun 2027, after 11:05 EAT (separate branch) | BOP v0.10 §10.7, §5 hand-off table | OpenBids#PAUSED, AO DECISION | 8.4 | Covered | Last recorded step (Opening started, 11:00:12) is inferred from the branch. No Cancel Tender button under TPR v0.13. Dependency (not on screen): KenTender Project Owner approves TPR v0.14; Tenders development owner implements the post-close route. |
| c11d | 02 · NOT MATCHED | Bid not matched to deadline record | Charles Mutiso | 11:01:10 EAT, branch 3 | BOP v0.10 §10.3 MISMATCH | OpenBids#NOT MATCHED | 8.4 | Covered | See flag 4. |
| c12 | 02 · CANCELLED | Ended by Tender cancellation | Charles Mutiso | 11:03:10 EAT, branch 5 | BOP v0.10 §10 branch 5 | OpenBids#CANCELLED | 8.4 | Covered | Not involved after cancellation, so no next-step block. |
| z1 | 02 · NO BIDS | No bids to open | Charles Mutiso | 19 Jun 2027, 11:00:30 EAT, TND-MOH-2027-034 | BOP v0.10 §10 empty-outcome fixture | OpenBids#NO BIDS | 8.5 | Covered |  |
| n1 | 02 · DID NOT TAKE PLACE | Record what happened | Amina Hassan | 26 Jun 2027, 11:10 EAT, TND-MOH-2027-035 | BOP v0.10 §10 branch 4 | OpenBids#DID NOT TAKE PLACE | 8.5 | Covered |  |
| n2 | 02 · DID NOT TAKE PLACE (after) | Decide what happens next | Amina Hassan | 26 Jun 2027, after 11:10 EAT | BOP v0.10 §10.7, §10.3 NOT HELD | OpenBids#DID NOT TAKE PLACE (after) | 8.5 | Covered | No Cancel Tender button under TPR v0.13. Dependency (not on screen): KenTender Project Owner approves TPR v0.14; Tenders development owner implements the post-close route. |
| r1 | 03 · PREPARE | Prepare opening record | Charles Mutiso, recorder | 12 Jun 2027, 11:04:30 EAT | BOP v0.10 §10.4, §5 row 8 | OpeningRecord#PREPARE | 8.6 | Covered |  |
| r2 | 03 · FINISH | Check draft and finish | Charles Mutiso | 12 Jun 2027, 11:06 EAT | BOP v0.10 §10.4 | OpeningRecord#FINISH | 8.6 | Covered | Page thumbnails are placeholders for the generated record. |
| r3 | 03 · SIGN | Review and sign | Beatrice Kamau | 12 Jun 2027, 11:08:30 EAT | BOP v0.10 §10.4, §5 row 9 | OpeningRecord#SIGN | 8.6 | Conditional | Signing interaction belongs to the deferred support module (BOP v0.10 §10.4); built against the D6 signing stand-in in simulation only. |
| r4 | 03 · WAITING | Waiting for signatures | Brian Wafula | 12 Jun 2027, 11:08:30 EAT | BOP v0.10 §10.4 WAITING | OpeningRecord#WAITING | 8.6 | Covered |  |
| r5 | 03 · CHANGED | Record changed, version 2 | Brian Wafula | 11:08:45 EAT, independent branch | BOP v0.10 §10.4 STALE | OpeningRecord#CHANGED | 8.6 | Covered |  |
| r6 | 03 · COMPLETE | Opening complete | Charles Mutiso | 12 Jun 2027, 11:10:30 EAT | BOP v0.10 §10.4, §20 row 8 | OpeningRecord#COMPLETE | 8.6 | Covered | Correct opening record opens board h4. |
| h1 | 05 · AUDIT | Completed record, read only | Naomi Chebet, Auditor | After 11:10:30 EAT | BOP v0.10 §10.6 | CompletedRecord#AUDIT | 8.7 | Covered | Not involved, so no next-step block. |
| h2 | 05 · NO BIDS COMPLETE | No bids to evaluate | Charles Mutiso | 19 Jun 2027, 11:06:30 EAT, TND-MOH-2027-034 | BOP v0.10 §10 empty-outcome fixture | CompletedRecord#NO BIDS COMPLETE | 8.7 | Covered |  |
| h4 | 05 · CORRECT | Correct completed record | Charles Mutiso | 12 Jun 2027, 11:15 EAT (separate branch) | BOP v0.10 §10.6 CORRECT COMPLETED RECORD | CompletedRecord#CORRECT | 8.7 | Covered | What needs correcting? is a choice of four kinds (BOP v0.10). |
| h5 | 05 · CORRECTION ADDED | Correction added | Charles Mutiso | 12 Jun 2027, after 11:15 EAT (separate branch) | BOP v0.10 §10.6 | CompletedRecord#CORRECTION ADDED | 8.7 | Covered | The red notice shows the denied message for reference only. |
| h3 | 05 · ADMINISTRATOR | Technical status only | Administrator | 12 Jun 2027, after 11:10:30 EAT | BOP v0.10 §10.6, §6 | CompletedRecord#ADMINISTRATOR | 8.7 | Covered | Not involved, so no next-step block. No incidents in the main fixture. |
