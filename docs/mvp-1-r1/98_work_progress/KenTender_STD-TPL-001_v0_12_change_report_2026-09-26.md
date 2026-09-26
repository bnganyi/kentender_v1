# STD-TPL-001 v0.12 change report (26 September 2026)

Prepared under the KenTender document change protocol for Project Owner review.

## 1. Files

| Item | Value |
|---|---|
| Input | `07_std_configuration/KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_11.md`, the committed proposed version (commit `765f0675`, owner decision OD5); unchanged |
| Output | `07_std_configuration/KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_12.md` |
| Version | 0.12 |
| Status | Proposed — v0.11 was also proposed and is not approved; approval of v0.12 is required |
| Edits | 9 anchored edits (`scripts/apply_edits.py`) |

**Process note.** A first draft was built from v0.10 because KT-DOC-CTRL-001 lists v0.10 as the current version. That draft was written to the v0.11 filename and overwrote the committed v0.11 in the working tree. The overwrite was found by `git status` before any commit. v0.11 was restored from git and verified unchanged, and the draft was discarded. Its TPL11-* identifiers would also have collided with v0.11's own TPL11-AC-001…008 and TPL11-CHG-001…007. v0.12 is built on the restored v0.11.

## 2. Read list

- **Read in full:** STD-TPL-001 v0.10 (1,085 lines) and every line v0.11 changes from it (the complete `diff`), which together cover all of v0.11.
- **Read in part:** BDS-CHG-001 v0.8 §1 item 4.1, §5.3 (the five-task table), §10.8 (BDS-DES-07 and its variants), §10.17, §10.19; KT-DOC-CTRL-001 (the STD-TPL-001 entry and the proposed-version pattern of the CFG-CHG-002 v0.16 entry); `12_bid_submission/reconciliation/definition_to_board_matrix.md` rows 1.1, 1.2, 3.6 and 5.1; the release 1.1 assets `06_runtime/response_rules.json`, `product_profile.json` and `moh_published_bid_definition_expected.json` (searched for the affected wording only).
- **Not read:** KT-STD-001 v1.9 beyond its use as the consistency checker's actor list; STD-TPL-IMP-001 v1.1; TPR-CHG-001 v0.12; the official PPRA source.

## 3. Changes by section

| Section | Operation | What changes | Source basis | New content? |
|---|---|---|---|---|
| Control table | Replace; add rows | Version 0.12; Status proposed with the v0.11 status kept as read; new rows Approved on, Approval record, Supersedes; Template release notes that the change applies from release 1.2; new Change type, with the v0.11 row kept as "Previous change type (v0.11, retained)" | Protocol; Project Owner decisions | Wording of the new rows |
| §8.1 | Replace one row; add a history table | Task 1 label **Tender documents, clarifications and addenda**; its purpose asks for an acknowledgement only when an addendum is effective, naming it; the earlier row is kept verbatim for release 1.1 | Project Owner: "2.1 Tender documents, clarifications and addenda"; "2.2 When there's something specific to acknowledge" | Purpose wording |
| §15 | Add two rows | TPL12-AC-001, TPL12-AC-002 | Same decisions | Yes: IDs and text |
| §18.4 | New subsection | Quoted decision basis; TPL12-CHG-001, TPL12-CHG-002 | Same decisions; BDS-CHG-001 v0.8 §5.3, §10.8 | Yes: IDs and text |
| §19 | Add 19.0; extend the 19.1 heading | v0.12 approval effect (proposed), newest first; v0.11's heading marked "retained, carried forward by v0.12" | Protocol | Wording; the "19.0" number avoids renumbering existing headings |

Deliberately not changed: §11.5 (the closed **release 1.1** design fixture, whose "Supplier tasks" row correctly keeps release 1.1's label); §8.2 (the "document/addendum acknowledgement" composition name still fits); §9.1 and §9.2 (the acknowledgement stays Not evaluated and Not carried forward); every OD5 change in v0.11.

## 4. Preservation result

`preservation_check.py v0.11 v0.12 --allow-control-table`: **PASS**. 1,135 original lines, 1,167 revised; 4 extended in place, 1 changed (allowed), 0 deleted.

Changed original line, verbatim, with reason:

- L6 `| Version | 0.11 |` — control table, new version (allowed).

Extended in place (original text kept, text added): the Status row, the Template release row, the Change type row (relabelled "Previous change type (v0.11, retained)") and the heading `### 19.1 v0.11 (proposed)`. The §8.1 row `| Tender documents and addenda | View and acknowledge the current published package |` is retained verbatim in the new history table.

## 5. Consistency result

`consistency_check.py` (actors: KT-STD-001 v1.9; registry: KT-DOC-CTRL-001): **0 errors**, 2 warnings, 4 information notes, identical to v0.11's own result. All are pre-existing: TPR-CHG-001 cited at v0.10 and v0.11; STD-TPL-IMP-001 cited at v0.2 and v1.0; BDS-CHG-001, TPR-CHG-001, KT-STD-001 and STD-TPL-IMP-001 cited below their current registered versions.

`register_check.py`: the STD-TPL-001 errors are expected and pre-existing. The register lists v0.10 as approved and lists neither v0.11 nor v0.12.

## 6. New content for review

- Task 1 purpose: "View the current published package. When an addendum is effective, acknowledge that addendum by name; when there is nothing specific to acknowledge, no acknowledgement is asked. The clarification questions and answers shown in this task remain owned by Tenders and Bid Submission (§10.1)."
- TPL12-AC-001, TPL12-AC-002, TPL12-CHG-001 and TPL12-CHG-002 (following the TPL11-* pattern).
- The control-table wording, the §18.4 introduction and the §19.0 approval-effect paragraph.

## 7. Decisions needed

1. **Approve STD-TPL-001 v0.12.** Recommendation: approve. It adds only your two decisions, applies them from release 1.2, carries v0.11 (OD5) forward unchanged, and leaves release 1.1 and every Tender bound to it unchanged. Approving v0.12 also approves the carried-forward v0.11 content.
2. **The version-status disagreement.** KT-DOC-CTRL-001 records v0.10 as approved on 26 September 2026 and does not list v0.11. v0.11 says v0.10 was never approved, and v0.10's own control table says "Proposed for approval". Recommendation: when v0.12 is approved, the register entry records v0.12 as approved and states which of these is right about v0.10.

## 8. Required corrections elsewhere

- **KT-DOC-CTRL-001:** list STD-TPL-001 v0.12 as proposed (the CFG-CHG-002 v0.16 entry shows the pattern), and v0.11 as proposed and superseded by v0.12 on approval. Not edited here: the register file carries other uncommitted edits that are not part of this change.
- **BDS-CHG-001 v0.8 §5.3:** the task-1 "Bidder work" cell reads "View and acknowledge the current set; ask a question before the clarification deadline." That now conflicts with the decision and with BDS-CHG-001 v0.8 §10.8. The next BDS-CHG-001 revision should say that an acknowledgement is asked only for an effective addendum, naming it.
- **Release 1.2 assets** (STD-TPL-IMP-001 tracker Phase C): the `product_profile.json` task label and purpose; a named, bounded required rule replacing `RQ-ALWAYS` on the document acknowledgement, with wording that names each effective addendum; the final confirmation sentence in `response_rules.json` (Project Owner decision "2.4 Bid spec", which needs no STD-TPL-001 text change); and the three Class A corrections in the reconciliation matrix.

## 9. Not verified

- Whether the official PPRA source requires a general acknowledgement of the tendering document; the Form of Tender text was not reread for this change.
- The effect on the **STD Templates** artboards: the release 1.1 fixture is unchanged, and no release 1.2 artboard exists.
- Legal review of the new purpose wording: not verified against the primary source.
