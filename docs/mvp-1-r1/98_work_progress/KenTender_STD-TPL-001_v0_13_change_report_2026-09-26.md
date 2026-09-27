# STD-TPL-001 v0.13 change report (26 September 2026)

Prepared under the KenTender document change protocol for Project Owner review.

## 1. Files

| Item | Value |
|---|---|
| Input | `07_std_configuration/KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_12.md`, approved 26 September 2026 (commit `5f7f521d`); unchanged |
| Output | `07_std_configuration/KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_13.md` |
| Version | 0.13 |
| Status | Proposed — v0.12 was Approved; re-approval required |
| Edits | 21 anchored edits (`scripts/apply_edits.py`) |

**Step 0.** The folder and `git log` for STD-TPL-001 show v0.12 as the newest version (approved, commit `5f7f521d`); no later file exists. KT-DOC-CTRL-001 (working copy) listed v0.12 as approved. The next free identifier series is TPL13-*.

## 2. Read list

- **Read in full:** STD-TPL-001 v0.12 (1,167 lines).
- **Read in part:**
  - BDS-CHG-001 v0.8: §4.3 (line 184, joint-venture membership frozen for a submitted Version); §4.4.8 (the supplier fact and form ownership table); §4.8 (the TenderSecurityResponse field table); §5.6 item 6; BDS01-AC-021; the BDS-DES-08-JV variant (line 1254).
  - PPRA Goods STD source text (`01_source/ppra_goods_std_official.txt`): ITT 13.4, ITT 18.1–18.5, the Tenderer Information Form and the Tenderer's JV Members Information Form.
  - Release pack: the release 1.2 runtime assets and the release 1.1 test vectors (compared by script); coverage rows COV-207…COV-218; forms FORM-TIF and FORM-JV.
  - KT-DOC-CTRL-001: the STD-TPL-001 and CFG-CHG-002 entries.
  - `12_bid_submission/reconciliation/definition_to_board_matrix.md` in full (the OD-E quotation).
- **Not read:** KT-STD-001 v1.9, beyond its use as the consistency checker's actor list; STD-TPL-IMP-001 v1.1; TPR-CHG-001 v0.12; LAW-REG-001.

## 3. Changes by section

| Section | Operation | What changes | Source basis | New content? |
|---|---|---|---|---|
| Control table | Replace; extend; add a row | Version 0.13; Status Proposed; Approved on and Approval record keep the v0.12 values as read; Supersedes; Template release notes that v0.13 applies from release 1.2; new Change type, with the v0.12 row kept as "Previous change type (v0.12, retained)" | Protocol; OD-E; the joint-venture decision | Wording of the new rows |
| §3.2 | Extend in place | `template_release` also names `1.2` | Release 1.2 assets | Wording |
| §8.2 | Add a paragraph | The joint-venture member composition; renderer 1.1.0 supports the new vocabulary and 1.0.0 refuses it | Joint-venture decision; release 1.2 renderer registry | Yes |
| §8.3 | Add three rows and a paragraph | Rows for supplied Account/arrangement/signatory facts, the joint-venture member, and tender security; a paragraph on per-obligation warranty/support rows, the per-addendum acknowledgement and label parameters | BDS-CHG-001 v0.8 §4.4.8 and §4.8; source ITT 18.1 and the two forms; STD-TPL-001 v0.12 §8.1 and §8.3 | Yes |
| §9.2 | Add a paragraph | Supplied facts and joint-venture member details are Not evaluated and Not carried forward | Release 1.1 and 1.2 mappings `DM-SUPPLIER-DETAILS`, `DM-JV-MEMBER` | Wording |
| §13 | Extend in place | The procedure also covers release 1.2 | OD-E | Wording |
| §13.5 | Extend in place | Envelope `template_release` also allows `1.2` | Release 1.2 assets | Wording |
| §13.5.1 | Add two rows and a paragraph | `supplied_value_sources`, `label_parameters`; the `per_arrangement_member` repetition; three named selectors | Release 1.2 profile | Yes: identifiers from the build |
| §13.5.2 | Add a paragraph | Optional field keys `supplied_value` and `label_parameters` | Release 1.2 compiler contract | Yes |
| §13.6 | Add a paragraph | Per-member identity: published identity plus the member's Supplier Organisation identity | BDS-CHG-001 v0.8 §4.3 | Yes |
| §15 | Add six rows | TPL13-AC-001…006 | As above | Yes: IDs and text |
| §17 | Add a bullet | BDS-CHG-001 v0.8 (approved) for §4.4.8, §4.3 and §4.8 | KT-DOC-CTRL-001 | Wording |
| §18.5 | New subsection | Quoted decisions; TPL13-CHG-001…006 | OD-E; the joint-venture decision; the sources above | Yes: IDs and text |
| §19 | Add a subsection; extend a heading | "v0.13 (proposed)" approval effect, newest first; the v0.12 heading marked "retained, carried forward by v0.13" | Protocol | Wording. The new heading is unnumbered because "19.0" is taken and renumbering would change approved lines |

**Deliberately not changed:**

- §8.1, as approved in v0.12.
- §11.5: the closed release 1.1 design fixture.
- §12: the MoH fixture. Its "six warranty/support facts" still holds.
- §9.1: the per-obligation warranty rows already map to `EVG-TECHNICAL-COMPLIANCE`.
- The "Current consumers" row and the §17 bullets that still name BDS-CHG-001 v0.7 and TPR-CHG-001 v0.11 (pre-existing; see §5).

## 4. Preservation result

`preservation_check.py v0.12 v0.13 --allow-control-table`: **PASS**.

- 1,167 original lines, 1,219 revised.
- 10 extended in place; 1 changed (allowed); 0 deleted.

Changed original line, verbatim, with reason:

- L6 `| Version | 0.12 |`: control table, new version (allowed).

Extended in place (original text kept, text added):

- the Status, Approved on, Approval record, Supersedes and Template release rows;
- the v0.12 Change type row, relabelled "Previous change type (v0.12, retained)";
- the §3.2 `template_release` row;
- the §13 opening sentence;
- the §13.5 `template_release` row;
- the heading `### 19.0 v0.12 (approved)`.

## 5. Consistency result

`consistency_check.py` (actors: KT-STD-001 v1.9; registry: KT-DOC-CTRL-001): **0 errors**, 3 warnings and 3 information notes.

- **Introduced (1 warning):** BDS-CHG-001 is now cited at v0.7 and v0.8. The new text cites v0.8, the approved version, for the facts release 1.2 implements. The existing v0.7 references are retained as read (v0.12's own result listed them as an information note).
- **Pre-existing (2 warnings, 3 notes):**
  - TPR-CHG-001 is cited at v0.10 and v0.11, and STD-TPL-IMP-001 at v0.2 and v1.0.
  - TPR-CHG-001, KT-STD-001 and STD-TPL-IMP-001 are cited below their current registered versions.

`register_check.py`: no STD-TPL-001 error once the register entry was updated (§8). The other 11 errors concern other entries; this change did not touch them.

## 6. New content for review

- TPL13-AC-001…006 and TPL13-CHG-001…006, following the TPL12-* pattern.
- The §18.5 heading and the unnumbered "v0.13 (proposed)" heading.
- Identifiers authored during the release 1.2 build and now named in the document:
  - supplied-value sources: `SV-ORGANISATION`, `SV-ARRANGEMENT`, `SV-ARRANGEMENT-MEMBER`, `SV-SIGNATORY`;
  - label parameters: `bidder_name`, `addendum_reference`;
  - repetition: `per_arrangement_member`;
  - selectors: `SEL-EFFECTIVE-ADDENDA`, `SEL-WARRANTY-OBLIGATIONS`, `SEL-ARRANGEMENT-MEMBERS`;
  - the fixed `immutable_source_id` `JV-MEMBER`;
  - renderer version 1.1.0.
- "A composition's repetition rule is `one` or `per_source`." This is taken from the release 1.1 profile; the document did not state it before.
- All other new wording in the §8.2, §8.3, §9.2, §13.5.1, §13.5.2, §13.6 and §19 additions.

## 7. Decisions needed

1. **Approve STD-TPL-001 v0.13.** Recommendation: approve. It adds only what release 1.2 already uses, following OD-E and your joint-venture decision. It leaves release 1.1 and every Tender bound to it unchanged.
2. **Tender security amount: exactly the published amount, or at least it?**
   - The build requires exactly the published amount. ITT 18.1 says "in the amount and currency specified in the TDS", and BDS-CHG-001 v0.8 §4.8 says the amount and currency "Must match the published requirement".
   - A bidder holding a guarantee for more than the required amount cannot enter it truthfully.
   - Recommendation: keep exact. Change it to "not below" only if you want the portal to accept larger guarantees and leave their sufficiency to evaluation.
3. **Who is the form's "Authorized Representative"?**
   - The build supplies the tenderer's authorised representative name, email and telephone from the bid's Tender contact (BDS-CHG-001 v0.8 §4.3), as the Phase 0 matrix classified it. The bidder types the representative's address.
   - The alternative reading is the Authorised Signatory.
   - Recommendation: keep the Tender contact, and confirm it at the next BDS-CHG-001 revision (follow-up FU-V08-31).

## 8. Required corrections elsewhere

- **KT-DOC-CTRL-001.** The working copy's STD-TPL-001 entry now follows the CFG-CHG-002 v0.16 pattern:
  - version 0.13 and the v0.13 filename;
  - `requirement_status` "Project Owner review" and `normative` "Proposed";
  - `approval_date` empty;
  - supersedes "v0.12 on approval; approved baseline v0.12 … remains effective until then";
  - an added action.

  Implementation, verification and release statuses are unchanged. The file is not committed, because it carries other uncommitted edits. The companion workbook needs regenerating.
- **BDS-CHG-001, next revision.** The §10.1 and DES-08/DES-08-JV fixtures do not show:
  - the authorised representative's address;
  - each joint-venture member's year of registration and representative (FU-V08-31).
- **BDS-CHG-001 §5.3.** The task-1 "Bidder work" cell remains as reported for v0.12.

## 9. Not verified

- Legal review of the new wording, and whether evaluation would treat a larger-value guarantee as responsive: not verified against the primary source beyond ITT 18.1.
- Whether the PPRA forms' "Authorized Representative" means the Tender contact or the signatory: not verified against the primary source's guidance notes.
- The effect on the **STD Templates** artboards. No release 1.2 artboard exists; the release 1.1 fixture is unchanged.
- Usability of the new bidder entries: they have no artboard yet (FU-V08-31).

## 10. Approval (added 27 September 2026)

The Project Owner answered the three decisions in §7 on 27 September 2026: "1. Approved 2. Exact published amount 3. Tender contact Proceed".

- **Decision 1.** v0.13 is approved.
- **Decision 2.** The tender security instrument amount stays exactly the published amount, in the published currency.
- **Decision 3.** The tenderer's authorised representative is read as the bid's Tender contact. Name, email and telephone are supplied from it; the bidder types the address.

**Document.** Changed only as the approval step allows:

- Status **Approved**; Approved on 27 September 2026.
- The Approval record quotes the instruction and keeps the earlier status and record wording as read.
- Supersedes: v0.12 (approved) from 27 September 2026.
- The v0.13 approval-effect heading and first sentence now say approved.

`preservation_check.py` (against the committed proposed v0.13): PASS, with `--allow-control-table` and two `--allow` patterns for that heading and sentence. `consistency_check.py`: 0 errors, and the same 3 warnings and 3 information notes as before.

**Register (KT-DOC-CTRL-001), working copy.**

- The STD-TPL-001 entry is now `requirement_status` "Approved requirement", `approval_date` 2026-09-27, `normative` "Yes", and supersedes v0.12.
- AUD-019 records the approval, Resolved.
- `register_check.py` shows no STD-TPL-001 error.
- Implementation, verification and release statuses are unchanged.
- The register file is still not committed, because it carries other uncommitted edits; the workbook still needs regenerating.

**Follow-ups.**

- The BDS-CHG-001 fixture and board redraw for the representative's address and the per-member entries remains open (FU-V08-31).
- Decisions 2 and 3 need no text change here: the v0.13 text already states the exact amount, and decision 3 concerns the release assets and BDS-CHG-001.
