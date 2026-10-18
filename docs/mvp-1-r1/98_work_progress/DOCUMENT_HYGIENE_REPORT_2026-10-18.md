# Document hygiene, 18 October 2026 — what was changed and how it was checked

Written for the Project Owner. It follows the change report the document-change protocol asks for. It answers your instruction of 18 October 2026 on `SYSTEM_CHECK_2026-10-18.md`: “1. All are approved. Harmonize 2. Approved. Mark them as such 3. Fix them now as part of document hygiene 4. Update the cancellation documents”.

Nothing here is pushed. Approval is not evidence of code, tests or release, so no implementation, verification or release field of an approved document was changed because it was approved.

## 1. What changed

| Group | Files | What was done |
|---|---|---|
| Seven versions marked approved (18 October 2026, quoting “2. Approved. Mark them as such”) | Strategy v1.11, Seed runbook v1.25 (`KenTender_SEED-OPS-001_Canonical_Site_Seed_Runbook_v1_25.md` in `00_common`), Procurement Proceedings v0.13, Bid Evaluation v0.9, Award v0.8, Contract Management v0.12, Gate 1 handoff v1.2 | The control table (status, approved on, approval record, supersedes) and the approval-effect paragraph were changed. The proposed wording was kept beside the new wording and labelled as retained. Nothing else in the body changed. |
| Two files brought into line with the register (quoting “1. All are approved. Harmonize”) | Installed STD Template Runtime v1.1, Statutory Correction Register v1.2 | The header now states the approval the register already recorded, with the register's dates (26 September and 23 September 2026). No wording about the original approval was invented. |
| Four correction versions, **Proposed, awaiting your approval** (quoting “3. Fix them now as part of document hygiene”) | Planning v1.33, Requisitions v1.21, Budget v1.18, Tenders v0.23 | Editorial only; see section 3. |
| The register | `KenTender_Baseline_Register.yaml` | The seven approvals, the two harmonisations, the four cancellation documents' implementation and verification status, and a pointer from each to the evidence map. The four correction versions are listed beside their entries as proposals. |
| Pages | `SYSTEM_CHECK_2026-10-18.md`, `CANCELLATION_RECOVERY_OWNER_ATTENTION.md` | Your answers recorded; the Roadmap Coverage Assessment mistake corrected. |

**Roadmap Coverage Assessment v1.3 (KT-RCA-001) needed no change.** Its file says “Approved — 3 October 2026”. The document checker could not read that header, and I wrongly reported it as unapproved.

## 2. Preservation and consistency

- **The four correction versions against the approved version before each:** Requisitions v1.21, Budget v1.18 and Tenders v0.23 pass with nothing changed and nothing deleted (7, 8 and 7 lines extended). Planning v1.33 passes only with one allowed change, below.
- **The one original line changed (Planning v1.33, §10.9).** The U10-CHANGED row had six cells under a seven-cell heading; one cell was split into two. Original, verbatim (v1.32 line 1948):

  `| U10-CHANGED | Replacement supplied: Your turn, **Open the updated funding review**. Otherwise: Waiting on someone, **Waiting for the Procurement Planner to request a new funding check** | Mercy Kilonzo, or the role where none resolves; since **Awaiting fixture** | Existing link when supplied | The Responsible role field | As U10 |`

  Corrected (v1.33 line 1960):

  `| U10-CHANGED | Replacement supplied: Your turn. Otherwise: Waiting on someone | Replacement supplied: **Open the updated funding review**. Otherwise: **Waiting for the Procurement Planner to request a new funding check** | Mercy Kilonzo, or the role where none resolves; since **Awaiting fixture** | Existing link when supplied | The Responsible role field | As U10 |`

  No words were removed; the same words sit in two cells. Which of the two cells was meant to hold which words is my reading of the table's heading; please check it when you read v1.33.
- **Document checker (errors, predecessor then successor):** Planning 5 → 2, Requisitions 2 → 0, Budget 3 → 0, Tenders 1 → 0. The two that remain in Planning are older wrong cross-references (“§8.3”) that existed in v1.32 and are not part of what you asked.
- **The seven approvals and two harmonisations:** the checker's error count is unchanged in each (nothing new), and the line-level changes are in the control tables and approval paragraphs only (checked in the diff for Award and Procurement Proceedings; the others are of the same size, 9 to 15 lines added).
- **The register:** its errors fell from 17 to 4. The four left were already there and are not caused by this change: Roadmap Coverage Assessment (the checker cannot read its header, see above) and three documents the register deliberately labels “Historical provenance” while their files say “Approved” (the Planning journey reference, SEED-001 and the Seed runbook).
- **Preservation of the register against its previous content** passes (the lines allowed to change were only version, approval date, supersedes, filename, scope, action, source hash, approval record, implementation and verification status, the date the register is current to, and the proposal status). One block in the Requisitions entry had irregular indentation; rewriting it moved seven lines two spaces to the right. The words are the same.

## 3. The four correction versions

| Version | What it adds | New content for you to read |
|---|---|---|
| Planning v1.33 | `PLN_CANCELLATION_RECOVERY_PENDING` and `PLN_CANCELLATION_RECOVERY_CONFLICT` in the §8 error table, with the wording already stated in §8.1; the §10.9 row split above | none beyond the row split |
| Requisitions v1.21 | `REQ_CANCELLATION_RECOVERY_INVALID` and `REQ_CANCELLATION_RECOVERY_PENDING` in the §11 error table | none |
| Budget v1.18 | `BUDGET_CANCELLATION_RECOVERY_INVALID` and `BUDGET_CANCELLATION_RECOVERY_CONFLICT` in the error table; the second BUD24-XD-002 row relabelled “BUD24-XD-002 (status)” | none |
| Tenders v0.23 | `TND_CANCEL_TOO_LATE` in the §8 error table | **The message wording is new.** The software does not have this message, because cancelling after the submission period has closed is not built |

Each version states in its own header that it is Proposed and not approved, and each has an approval-effect paragraph that becomes declarative only if you approve.

## 4. Things for you to know or decide

1. **Strategy v1.11, §18.6** is headed “Defaults taken by v1.11 for the Project Owner to confirm”. Your blanket approval settles them as taken. If you want to look at any of them separately, say so.
2. **Seed runbook v1.25** is approved, but the register still labels the runbook “Historical provenance” because the seed specification retired it as a live rule document on 8 October. If you want it live again, that is a separate decision.
3. **Gate 1 handoff v1.1 was already approved (1 October 2026).** v1.2 replaces it. Some sentences in the v1.2 body still read as if it were waiting; they were left alone.
4. **Approved bodies still carry sentences written while they were proposed**, kept as history. Rewriting them is an optional later tidy-up.
5. **Approve or change the four correction versions** (Planning v1.33, Requisitions v1.21, Budget v1.18, Tenders v0.23).

## 5. Not verified

- The nine in-place edits and four new versions were drafted by helper agents under my instructions. I checked them with the scripts and by reading the diffs of two of the approvals and the Planning row; I did not re-read every changed line of every document.
- I did not re-read the other documents the seven approved versions refer to.
- Nothing in this change was run against the software.
- The register's recorded hash for Roadmap Coverage Assessment v1.3 does not match the file on disk. I did not change that entry, and git shows the file unmodified; I did not look into why.
