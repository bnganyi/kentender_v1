# Change report — STD-TPL-001 v0.14, release 1.3 content quality (Part A) (2 October 2026)

This report covers the **release 1.3 content-quality version** of STD-TPL-001. It is not the report for the template-walkthrough proposal, which also drafted a "v0.14" (`07_std_configuration/KenTender_STD-TPL-001_v0_14_Change_Report.md`, written by another session). §8 item 1 asks the owner to settle that numbering.

## 1. Files

| Input | Output | Version and status |
|---|---|---|
| `KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_13.md` | `KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_14.md` | v0.14, Proposed — v0.13 was Approved; re-approval required |

Edits were applied with `apply_edits.py` (21 anchored edits, each matched exactly once). The input file is unchanged.

## 2. Read list

- Read in full: STD-TPL-001 v0.13; the questionnaire change request of 2 October 2026; the other session's v0.14 change report; `open_issues.md` sections for releases 1.1 and 1.2.
- Read in part: the walkthrough change request (control table and the lines about R5 and the register only); the template pack JSON files and registers (the rules changed here); the bid-evaluation rules, Bid Submission, Tenders and std-templates source files that the release 1.3 change touched.
- Not read: STD-TPL-IMP-001, EVL-CHG-001, BDS-CHG-001, TPR-CHG-001, KT-STD-001, KT-DOC-CTRL-001 (the register was only grepped for STD-TPL-001), and the walkthrough change request outside the lines above.

## 3. Changes by section (STD-TPL-001 v0.14)

| Section | Operation | What changes |
|---|---|---|
| Control table | Replace, additive | Version, date, status, approved on, approval record ("None for v0.14", v0.13 record retained), supersedes, template release; new change type; new "Version coordination (v0.14)" row; v0.13 change type retained |
| §3.2 | Extend | `template_release` names `1.3` |
| §8.2 | Insert | The locked-declaration composition also permits integer and date controls |
| §8.3 | Insert | Three response-generation rows (questionnaire, independent tender determination, Form of Tender) and a paragraph on wording, one question per response and the interim tables |
| §9.1 | Insert | Yes/No reading, release-limited evaluation rules, committee reason names the question |
| §13 intro, §13.5 envelope | Extend | Release 1.3 beside 1.1 and 1.2 |
| §13.8 | Insert | Check 22, content quality |
| §13.12 | New | Content quality: seven checks, the quality register and its treatments |
| §14.2 | Insert | Gate row "Content quality" |
| §15 | Insert | TPL14-AC-001 to TPL14-AC-008 |
| §18.6 | New | Decision basis, TPL14-CHG-001 to 008, what v0.14 does not change |
| §19 | Insert | v0.14 (proposed) approval effect above the retained v0.13 section |

## 4. Preservation result

`preservation_check.py v0_13 v0_14 --allow-control-table`: **PASS**. Original lines 1219, revised 1284; 10 lines extended in place; 1 changed (control-table Version line, allowed); 0 deleted.

Changed original line, verbatim: `| Version | 0.13 |` (now `| Version | 0.14 |`). Reason: the consistency checker reads a Version cell as digits, so a "(v0.13 read: …)" suffix breaks it.

## 5. Consistency result

`consistency_check.py`: 0 errors, 3 warnings, all pre-existing (BDS-CHG-001, TPR-CHG-001 and STD-TPL-IMP-001 each cited at two versions) and 4 info lines about older citations. Nothing introduced.

`register_check.py` with the register: STD-TPL-001 reports R5 errors (the register says v0.13 approved; the file is proposed). Expected for a proposed successor. The register was **not** edited here: another session's uncommitted changes to it already describe a different "v0.14" (the walkthrough).

## 6. New content for review

- Identifiers: TPL14-AC-001 to 008; TPL14-CHG-001 to 008; gate name "Content quality"; validator check 22; register treatments `itemised`, `row-group`, `interim`, `excluded`, `deferred`, `open`; open issues 96 to 110.
- Wording: the three §8.3 rows, the §9.1 and §13.12 text, the "Version coordination (v0.14)" cell.
- Template content (release 1.3, in the pack, not in the document): the labels, help lines and field keys listed in `open_issues.md` items 96 to 102; the conflict labels are the official wording of the change request Appendix A, numbered 1 to 9.
- Operational statement in TPL14-CHG-008: installing release 1.3 requires switching release 1.2 Off; the seed and fixture helper does it, the deployment command does not.

## 7. Audit catalogue (what release 1.2 had)

Counts from the audit of 16 supplier forms, 25 response rules, 90 fields, run against the 1.2 pack. After the fixes, the content-quality check finds none of the failing classes in 1.3.

| Defect class | Instances in 1.2 | Treatment in 1.3 |
|---|---|---|
| Label that is only an ordinal | 10 (nine conflict items and the independent-determination paragraph 5) | Official wording; conflict items numbered |
| Yes/No with no declared reading | 11 | Declared in the evaluation rules |
| Evaluated response with no evaluation rule | 6 (Related Service ×3, Additional Evidence, Related Service price ×2) | Rules added |
| Evaluator text naming an item by number | 5 | Reworded |
| Locked text losing list numbers | 4 (independent determination, SD1, SD2, questionnaire) | Flattener keeps numbers; digests regenerated |
| Compound or shared response | `ownership_details`, shared conflict details, trade licence, discounts, consultation details, others | Split or itemised (open issues 96 to 102) |
| Official table collapsed to text | partners, directors, persons with an interest, commission recipients | **Not fixed in 1.3**; interim text with column help; replaced in release 1.4 |
| Price-schedule columns not captured | goods schedule (10 official columns, 2 electronic) and related-service schedule | **Deferred** by the owner on 2 October 2026 |
| Inverted Yes/No (item 9) | 1 | Decision D2(a) applied |

## 8. Decisions needed

1. **Version number.** The walkthrough proposal also drafted "v0.14". This file takes v0.14 for release 1.3, as that draft's own report invited. Recommendation: keep it, and rebase the walkthrough on this version as v0.15 with its validator checks 23 and later; Part B (repeating rows) follows after.
2. **Approve v0.14.** Recommendation: approve. Nothing in it changes release 1.1, release 1.2 or a Tender bound to them.
3. **Vocabulary note.** The locked-declaration composition now permits integer and date controls (open issue 98). Recommendation: accept; the alternative is two free-text fields for age and licence expiry.
4. **Trade licence expiry has no bound** (open issue 100): the declaration source publishes no submission-deadline fact. Recommendation: accept; the committee sees the date.
5. **Item 9 follows the form literally**: its details response is asked for a Yes (how it was resolved), not for a No. **Decided by the owner, 2 October 2026: "Item 9 details: Confirmed as is".**
6. **Signature blocks** (open issue 108): the electronic confirmation replaces the printed name, title, signature and date. **Decided by the owner, 2 October 2026: "Signature blocks: Confirmed (though the actual implementation of electronic signatures is deferred)".** The pack's `open_issues.md` items 97 and 108 still read "for review"; they are updated at the next release rebuild, because editing the pack now would change the installed release's digest.
7. **Version number and vocabulary note**: settled by the owner's replies the same day (the walkthrough "v0.14" was removed, so this v0.14 stands; the vocabulary note was noted; the plan deviations stay open).

## 9. Required corrections elsewhere

- **KT-DOC-CTRL-001:** the `STD-TPL-001` entry's `proposed_revision` currently describes the walkthrough as v0.14; reconcile it with item 1 above. Add release 1.3 and the new gate to the entries that name release 1.2. (Not edited here.)
- **EVL-CHG-001:** record that an evaluation rule may name template releases, that a Yes/No rule declares its reading, and that conflict item 9 is Not applicable when not asked.
- **BDS-CHG-001 and TPR-CHG-001:** no change is required by Part A (labels and fields flow through the published definition). Part B (release 1.4) needs the repeating-row control in BDS-CHG-001.
- **STD-TPL-IMP-001:** note that the seed and fixture helper switches older releases of one format Off.
- **Documentation control register workbook:** regenerate after the register is updated.

## 10. Not verified

- Nothing further on the dev site is unverified beyond §11.
- The questionnaire read through a keyboard-only or 390 px pass, and the Certificate of independent tender determination and Form of Tender drawers in a browser (only the questionnaire drawer was walked, on the test site).
- Whether the legal reading of conflict item 9 (decision D2) is correct against a primary source; the change request records it as unverified.
- The 12 official tables are not all in the quality register: the joint-venture form items 7 and 8 and the manufacturer authorisation form are not listed.
- `Make` targets `std-release-switch` and the dev-site install were not run.
- EVL-CHG-001, STD-TPL-IMP-001 and the walkthrough draft were not read in full.

## 11. Dev-site install (2 October 2026, after the owner's request)

- Backup taken first (`kentender_midas_com-database.sql.gz`, 18:50).
- Release 1.3 installed and switched On (`make std-release-install`; bundle digest `33c5cb0f…b9247`, 142 assets, matches the pack). Release 1.2 switched Off (`make std-release-switch`). Release 1.1 was already Off.
- The platform has no rebind path, so Tender TDR-304178 (release 1.2, Published — open, one started bid) could not be moved to 1.3. With the owner's acceptance of data loss, the canonical world was reseeded through the Tenders stage (`make seed-canonical THROUGH=tenders REBUILD=True`) and the Bid Submission fixture world was recreated (`reset_my_bids_fixture state=started`).
- Result: TDR-304178 no longer exists. **TDR-304255**, reference **TND-MOH-2099-001**, Published — open, release 1.3, with started bid BID-MOH-2099-001-002 (Afya, `pw.bds.david@afya-pw.example`, fixture test password). The canonical **TDR-304219** (TND-MOH-2027-002) is also on release 1.3 but reads "Submission period ended", because the canonical seed runs on a 2027 timeline.
- Verified by reading the dev database: both Tenders and their published definitions carry release id `stdr-9b953bcf-…`, and the questionnaire rows of the new definition include the new fields. Not driven in a browser on the dev site.
