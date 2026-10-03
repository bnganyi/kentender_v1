# Change report — STD-TPL-001 v0.15, release 1.4 (3 October 2026)

Release 1.4 holds a Tenderer's standing business facts once, on its supplier Account, and copies them into each bid per entity; it replaces four interim text fields with one bounded table control; and it corrects two wordings against the official form.

## 1. Files

| Input | Output | Version and status |
|---|---|---|
| `07_std_configuration/KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_14.md` | `07_std_configuration/KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_15.md` | v0.15, Proposed. v0.14 was itself Proposed (never approved); v0.15 carries it forward, so approving v0.15 also supersedes v0.13 |

Edits were applied with `apply_edits.py` (20 anchored edits, each matched exactly once). The input file is unchanged. The release itself is built and installed (§10); the document and the release are separate things and neither is approved by this report.

## 2. Read list

- Read in full: STD-TPL-001 v0.14 sections 1, 3.2, 8.2, 8.3, 13.5.1, 13.5.2, 13.6, 13.12, 15 (the end), 18.6 and 19; the questionnaire change request §3 and §12; `open_issues.md` items 96 to 110; the release 1.4 pack files that changed.
- Read in part: the rest of STD-TPL-001 v0.14 (outline and the sections above only); the BDS-CHG-001 follow-ups file (rows 104 to 110 and the closing-condition list).
- Not read: BDS-CHG-001 v0.8 and v0.10 (the v0.10 file is another session's untracked draft), EVL-CHG-001, STD-TPL-IMP-001, KT-STD-001, KT-DOC-CTRL-001 beyond the register check, and the template walkthrough change request.

## 3. Changes by section

| Section | Operation | What changes |
|---|---|---|
| Control table | Replace, additive | Version, date, status, approved on, approval record, supersedes, template release; new change type with the v0.14 one retained as "Previous change type (v0.14, retained)" |
| §3.2 | Extend | `template_release` names `1.4` |
| §8.2 | Insert | Table control, entity business profile composition, `per_entity`, `SV-ENTITY-PROFILE` and renderer 1.2.0 |
| §8.3 | Insert | Four response-generation rows (business profile; questionnaire and Form of Tender as read from release 1.4; year of registration) and a sentence on the tables |
| §13.5.1 | Insert | One table row (controls, validations, compositions, sources added) and a paragraph on `per_entity` and `SEL-ENTITIES` |
| §13.5.2 | Insert | A supplied value may be a list of rows, shown as a table |
| §13.6 | Insert | Identity of a `per_entity` group and what is copied and sealed |
| §13.12 | Insert | The four tables are `row-group` rows |
| §15 | Insert | TPL15-AC-001 to TPL15-AC-010 |
| §18.7 | New | Decision basis, TPL15-CHG-001 to 007, what v0.15 does not change |
| §19 | Insert | v0.15 (proposed) approval effect above the retained v0.14 text |

## 4. Preservation result

`preservation_check.py v0_14 v0_15 --allow-control-table`: **PASS**. Original lines 1285, revised 1337; 10 lines extended in place; 1 changed (the control-table Version line, allowed); 0 deleted.

Changed original line, verbatim: `| Version | 0.14 |` (now `| Version | 0.15 |`). Reason: the consistency checker reads a Version cell as digits.

## 5. Consistency result

`consistency_check.py` with the baseline register: 0 errors, 3 warnings and 4 info lines, identical to v0.14 (BDS-CHG-001, TPR-CHG-001 and STD-TPL-IMP-001 each cited at two versions; older citations). Nothing introduced.

`register_check.py`: 11 errors reported, none about STD-TPL-001 (delivery-item status values, a PLN-CHG-001 status); they are pre-existing. The register was **not** edited: another session's uncommitted changes to it already exist, and the STD-TPL-001 entry still describes v0.13 as current.

## 6. New content for review

- Identifiers: TPL15-AC-001 to 010; TPL15-CHG-001 to 007; `CTL-ROW-GROUP`, `VAL-ROW-GROUP`, `COMP-ENTITY-PROFILE`, `SV-ENTITY-PROFILE`, `SEL-ENTITIES`, repetition `per_entity`, mapping `DM-ENTITY-PROFILE`, rule `RR-ENTITY-PROFILE`; renderer version `1.2.0`; open issues 111 to 123.
- Wording: the §8.2, §8.3, §13.x and §18.7 text; the new commissions question ("Have you paid, or will you pay, any commissions, gratuities or fees with respect to the Tendering process or execution of the Contract?") — the official form has no such question; the table's column headings and the currency list **KES, USD, EUR, GBP**; the committee reason's added sentence about the Form of Tender's confirmation.
- Quotations: §18.7 quotes the 2 October working-session answers as recorded in the change request. The 3 October answers to the planning questions are recorded as the recommended option each time, **from the session summary, not as the exact words of the options**.
- Built behaviour that is not in any approved document (BDS-CHG-001 needs the amendments in §9): the Account business profile and its command, the per-entity profile in the bid snapshot, the table control's error keys, saved Account documents in a bid, the total in words on the printed receipt.

## 7. Decisions needed

1. **State-owned status moves to the entity's profile** (TPL15-CHG-004, open issue 118). Built as recommended: the question leaves the Form of Tender; the Form's locked text (k) is unchanged; evaluation reads every entity's answer. Recommendation: confirm.
2. **Form of Tender item (p)**: the official form asks for a website, the template prints the Procuring Entity's contact office. No website fact exists. Recommendation: the owner supplies the website as a constant, or accepts the contact office.
3. **Commissions question and currency list** (new wording). Recommendation: accept; the alternative is the official "or none" free text.
4. **Missing profile does not block starting a bid, but blocks submission** (built as written in the plan). Recommendation: accept.
5. **Per-entity evaluation display**: committee members see each entity's answer in one line ("Afya: No; Kisiwa: Yes"). Recommendation: accept for now; a block per entity is a larger change.
6. **Approve v0.15** (and so v0.14, which it carries). Recommendation: approve. Nothing in it changes releases 1.1 to 1.3 or a Tender bound to them.

## 8. Required corrections elsewhere

- **BDS-CHG-001** (successor to the version the register names current): §4.1 and §6 (profile facts), §4.4.3 (table control), §4.4.8 and §4.5 (per-entity snapshot, refresh listing every change), §5.5 (saved documents in a bid), §7.2 (`UpdateSupplierBusinessProfile`), §8 (field-error keys `handle.row.column`), §10.5 and the Account board (Business profile region), §10.9 and board BDS-DES-08 (profile rows, Open Account), §10.10 (table drawer), §10.14 (total in words). Recorded as follow-ups FU-V08-74 to 78 in `12_bid_submission/BDS-CHG-001_v0_8_FOLLOW_UPS.md`. The current BDS document is over 2,000 lines and has an untracked v0.10 draft from another session; a successor was not written here.
- **EVL-CHG-001:** an evaluation entry may name template releases; a response answered once per entity is read together; the conflict reason names the Form of Tender; the state-owned entry reads every entity.
- **KT-DOC-CTRL-001:** the `STD-TPL-001` entry's `proposed_revision` still describes v0.13/v0.14; reconcile with this version and release 1.4. Regenerate the register workbook afterwards.
- **STD-TPL-IMP-001:** the compiler loads the shared table checker without Frappe (a note, no rule change).
- **SEED-OPS-001:** seeded suppliers now carry a complete business profile (`canonical.AFYA_PROFILE`, `default_profile`).

## 9. Not verified

- Whether the PPRA form's Yes/No-less "or none" wording for commissions is meant to be answered as a table; the legal reading of the form is not verified against a primary source.
- Browser behaviour at 390 px of the Account's profile dialog (the owners table is checked as cards on the page; the dialog's rows stack at 800 px and below by CSS, not by a browser check); a keyboard-only pass of the table control.
- A full end-to-end pass as real actors starting from the menu on the **dev** site: the browser suites ran on the test site. The dev site was migrated, release 1.4 installed and the bid world recreated; a live walk is owed.
- A joint-venture bid was proven by Python tests (profile rows per member, a member without a profile), not in a browser.
- EVL-CHG-001, STD-TPL-IMP-001 and the template walkthrough draft were not read in full.

## 10. Build and test evidence (observed 3 October 2026)

- Release 1.4: `rebuild_release.py --pdf`, validator 22 of 22 passed (including content quality), bundle digest `0c63ab3b…1a1e`, release id `stdr-c25e6578-3700-4df8-bbaa-8c2041be2f01`. Releases 1.2, 1.3 and 1.4 are frozen as test vectors (`std_templates/tests/vectors/release_1_2`, `_1_3`, `_1_4`) and compile byte for byte.
- Python on the test site: the new and changed modules and every bid-submission, std-templates, tenders (documents, lifecycle), bid-opening, bid-evaluation and award module run, all passing; 8 evaluation tests of the new vocabulary, 12 profile tests on the Account, 11 table-control tests, a populated-tables bid through submission, opening and evaluation, and a joint-venture profile test.
- Vitest: bid-portal (357 tests) and supplier-account-portal (33) pass; one parallel run of eight projects timed out five fidelity files under load, and those files pass when their projects run alone.
- Playwright on the test site: all 62 tests of `tests/ui/smoke/bid-submission` pass, including the new Account profile, business-profile row, commission-table and persons-table tests. Four existing expectations the earlier bid-wizard work had made stale were updated, and two real 390 px overflow defects (the task stepper and the requirements section nav) were fixed.
- Dev site: migrated, release 1.4 installed On, release 1.3 switched Off, bid world recreated on 1.4 (Tender TND-MOH-2099-001, bid BID-MOH-2099-001-002, David `pw.bds.david@afya-pw.example`), supplier Accounts given profiles. Not driven in a browser.
