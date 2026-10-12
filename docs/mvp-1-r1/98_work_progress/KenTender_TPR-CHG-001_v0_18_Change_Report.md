# TPR-CHG-001 v0.18 — change report

Written for: the Project Owner, to review before approving v0.18.

## 1. Files
- Input: `11_tenders/KenTender_TPR-CHG-001_Tenders_v0_17.md` (Approved — 3 October 2026), unmodified.
- Output: `11_tenders/KenTender_TPR-CHG-001_Tenders_v0_18.md` — **Proposed — 10 October 2026**. 9 anchored edits, each matched once.

## 2. Read list
Read in full: the head and control table (lines 1–40), §10.6 (the Review screen, lines 1116–1134), the FU-36 row of the follow-ups file, the §21 findings that mention digests, the last lines of the document. Read in part: §§10.8–10.9 (only the lines naming digests). Not read: the rest of the document.

## 3. Changes by section
| Section | Operation | What changed | New content? |
|---|---|---|---|
| Head | Insert | “Proposed successor v0.18” paragraph with the Owner's “Option 1” | Yes (wording) |
| Control table | Replace | Version 0.18; Date; Status Proposed (v0.17 approved); Approved on “Not yet approved”; each keeps the v0.17 wording inside | Yes (wording) |
| Control table | Insert | v0.18 change type; v0.18 owner decision | Yes (wording) |
| §10.6 item 7 | Replace | Digests only for a technical reader or an Auditor; heading line names the template and version. The v0.17 sentence is kept inside as “(v0.17 read: …)” | Yes |
| §15 acceptance table | Insert | TPR18-AC-001 | Yes (new identifier) |
| New §22 | Insert | v0.18 change account: finding, decision, what was built, what was not changed, required corrections | Yes (wording) |

## 4. Preservation
PASS. 2,258 → 2,280 lines, net +22; 1 line changed, allowed: `| Version | 0.17 |` (the new version). 0 deleted. The Date, Status and Approved on rows were extended in place (their v0.17 wording is kept inside).

## 5. Consistency
v0.17: 1 error, 3 warnings, 11 info. v0.18: the same. The one error (C3, `TND_CANCEL_TOO_LATE` not defined in the error table) is pre-existing. A first attempt that left “Approved on: 3 October 2026” beside a Proposed status raised a C1 error; I reworded the row so it carries no stand-alone date.
The register still shows v0.17 as TPR-CHG-001's approved version, which is right while v0.18 is only proposed.

## 6. New content for review
- TPR18-AC-001 (identifier and wording).
- The statement that the Accounting Officer's authorisation screen follows the same rule: this describes the build (it reuses the same sections) and the Owner's option 1 did not name that screen.
- “Auditors included”: I read option 1's “technical readers and auditors” that way.

## 7. Decisions needed
1. Approve v0.18 (separate, explicit step). Recommend yes.
2. Should the publication decision's Technical details (the package digest shown to the Head of Procurement Function and the Accounting Officer under the 2 October rule) follow the same technical-reader and Auditor limit? Recommend yes, for one rule across the module; not changed here.

## 8. Required corrections elsewhere
- Register entry for TPR-CHG-001: show v0.18 as proposed while v0.17 is approved.
- No board change: the TPR-DES-05 board never drew digests.

## 9. Not verified
Preview complete Tender and History views; the other places a digest might render to a business reader; production data (only the test and dev sites were used).
