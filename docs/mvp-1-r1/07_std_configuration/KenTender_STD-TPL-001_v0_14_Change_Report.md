# Change report — STD-TPL-001 v0.14 and the walkthrough change request (2 October 2026)

## 1. Files

| Input | Output | Version and status |
|---|---|---|
| `KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_13.md` | `KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_14.md` | v0.14, Proposed — v0.13 was Approved; re-approval required |
| `KenTender_STD-TPL-001_Change_Request_Template_Walkthrough_2026-10-02.md` (proposal) | Same file name (approved) | Change request, Approved 2 October 2026 |

Owner instruction applied: Project Owner, 2 October 2026: "This is approved, together with your recommendations. Update the documents appropriately with care".

## 2. Read list

- Read in full: STD-TPL-001 v0.13; STD-ST-001 v0.5; both change requests of 2 October 2026.
- Read in part: BDS-CHG-001 v0.10 and TPR-CHG-001 v0.15 (sections listed in the walkthrough change request §12).
- Not read: STD-TPL-IMP-001, AUTH-ADR-001, KT-STD-001, EVL-CHG-001, KT-DOC-CTRL-001.

## 3. Changes by section (STD-TPL-001 v0.14)

| Section | Operation | What changes |
|---|---|---|
| Control table | Replace, additive | Version, date, status, approval record, supersedes, template release; new change type; new "Version coordination (v0.14)" row; v0.13 change type retained |
| §3 | Extend | **STD Templates** also walks through a release |
| §3.1 | Insert row | `TemplateWalkthroughProjection v1` |
| §11 intro, §11.1, §11.3 | Insert | Walkthrough route, design input, link and **Walk through supplier bid** action |
| §11.4 | Replace, additive | Action list adds the walkthrough; v0.13 wording kept as "(v0.13 read: …)" |
| §11.6 | Insert paragraph | Walkthrough read and stateless rule evaluation |
| §11.7 | New | STD-DES-03 Template walkthrough: entry points, fixture scope (R1), shell, stages, answers (R2), field panel, variants, closed design fixture, interaction and security |
| §13.7 | Insert paragraph | Walkthrough compilation at installation, unpublished preview, published reading |
| §13.8 | Insert | Checks 22 and 23 (R3 severity), applying from Part A's release (R5) |
| §14.2 | Extend | Inspection gate names the walkthrough; records no gate result |
| §15 | Insert | TPL14-AC-001 to TPL14-AC-013 |
| §16 | Insert | Prohibitions 17 to 19 |
| §17 | Insert | v0.14 references |
| §18.6 | New | Decision basis, TPL14-CHG-001 to 005, decisions R1–R5, required corrections elsewhere |
| §19 | Insert, heading extended | v0.14 approval effect; v0.13 heading marked retained |

## 4. Preservation result

`preservation_check.py v0_13 v0_14 --allow-control-table` plus three allowances: **PASS**. Original 1219 lines, revised 1391; 11 lines extended in place; 1 changed (the control-table Version line, allowed); 0 deleted. Lines extended in place keep their original wording in full: the control-table rows, §3 owner cell, the §11.4 action list (v0.13 wording kept as "(v0.13 read: …)"), the §14.2 Inspection row and the §19 v0.13 heading.

Change request: **PASS**; 3 control-table rows extended, 0 changed, 0 deleted; §11 approval effect and new §13 added.

## 5. Consistency result

No ERROR. Three C7 warnings (one document cited at several versions), all pre-existing. Two are extended by v0.14: BDS-CHG-001 now also appears at v0.10 and TPR-CHG-001 at v0.15, intentionally, beside the existing v0.7/v0.8 and v0.10/v0.11 citations. A pre-existing mismatch is also noted: STD-TPL-001 cites STD-TPL-IMP-001 v1.0, while BDS-CHG-001 v0.10 and TPR-CHG-001 v0.15 cite v1.1.

`register_check.py` was not run: KT-DOC-CTRL-001 was not supplied. The register needs updating (§18.6).

## 6. New content for review

`TemplateWalkthroughProjection v1`; STD-DES-03; route `/app/std-templates/{release_id}/walkthrough`; action **Walk through supplier bid**; stage names; view switch **By stage** / **All supplier fields**; width selector; arrangement switch with **Member 1** and **Member 2**; supplied-value markers; **Not available in a walkthrough**; **Reset answers**; field-panel headings; variant copy in §11.7.5; validator checks 22 and 23; TPL14-AC-001 to 013; TPL14-CHG-001 to 005; prohibitions 17 to 19. The §11.7.6 fixture uses only facts from §§8.1, 11.5, 12 and the questionnaire change request §5.1; everything else is "Awaiting fixture".

## 7. Decisions needed

1. **Approve v0.14.** Recommendation: approve once its number is settled against the Part A and Part B versions.
2. **Version number.** If Claude Code's Part A version takes v0.14 first, this version is renumbered and rebased with its content unchanged (control table, "Version coordination").

## 8. Required corrections elsewhere

Named in STD-TPL-001 v0.14 §18.6: TPR-CHG-001, BDS-CHG-001, STD-TPL-IMP-001, AUTH-ADR-001, KT-DOC-CTRL-001 and the Part A/B versions. TPR-CHG-001 and BDS-CHG-001 successors were not drafted in this session: each is over 2,000 lines and must be read in full before it is edited.

## 9. Not verified

- Whether a Part A or Part B version has already taken v0.14.
- Whether STD-TPL-IMP-001 already stores the compiled fixture definition, and its exact version (v1.0 or v1.1).
- The §11.7 next-step statement ("none") against KT-STD-001 v1.8 §2.9, which was not read.
- Whether the BDS renderer can run inside the Desk shell unchanged.

## 10. Register update — KT-DOC-CTRL-001, 2 October 2026

Inputs: `KenTender_Baseline_Register.yaml` (as of 2026-10-01) and `KenTender_Documentation_Control_Register.xlsx`, supplied 2 October 2026. Outputs: the same file names, register as of 2026-10-02.

| Entry | Change |
|---|---|
| `as_of` | 2026-10-01 → 2026-10-02 |
| documents/STD-TPL-001 | v0.10 → v0.13, approved 2026-09-27; v0.13 filename; `library_file_id` blank (not known); `proposed_revision` v0.14; `prior_approved_baseline` v0.10 with its library file ID. Implementation, verification and release statuses unchanged. Previous action kept as "(Before 2 October 2026 read: …)" |
| documents/STD-ST-001 | Referenced—unresolved → Approved reference, approved 2026-09-11, file named, normative Yes. Implementation, verification and release statuses unchanged |
| documents/IT-EQUIPMENT-OPEN-V1 | Action records the 2 October QA observation on release 1.2; statuses unchanged |
| interfaces IF-007, IF-015; delivery items G1-002–005, 007, 015, 019, 020, 026–030 | `owner_doc` STD-TPL-001 v0.10 → v0.13; IF-007 status text likewise |
| delivery_items/G1-023 | 'Blocked by unresolved standard' → 'Approved requirement' (the unresolved standard is now resolved) |
| interfaces/IF-020 | New: template walkthrough interface (Proposed interface) |
| decisions/DEC-035, DEC-036 | New: questionnaire D1/D2/D3/D5 (D4 open); template walkthrough S1–S3 and R1–R5 |
| delivery_items/G1-032, G1-033, G1-034 | New: Part A release with checks 22–23; Part B repeating rows; template walkthrough |
| audit_findings/AUD-011 | Open → Resolved (file supplied); library admission remains |
| audit_findings/AUD-021–AUD-024 | New: register lag (Resolved); stale STD-TPL/IMP/KT-STD citations; STD-ST-001 §13 walkthrough condition; v0.14 numbering |

`register_check.py`: errors 13 → 9. Removed: both STD-TPL-001 R5 errors, the STD-ST-001 R5 error and the G1-023 vocabulary error. The 9 remaining are all pre-existing vocabulary errors ('Mixed approved/proposed' ×7, 'Needs reconciliation', PLN 'Not implemented'). Warnings 96 → 117. The new warnings are stale citations that the correction to v0.13 now exposes, mostly documents still citing STD-TPL-001 v0.10, plus the new findings' own quoted citations and two R7 names (STD-ADR-002, TND-MOH-2027-002) that the register does not list. Decisions DEC-021 to DEC-024 still cite STD-TPL-001 v0.10 as the version in which they were made; they were left unchanged as history.

Workbook: regenerated from the register. All six data sheets were rewritten in register order with their table, conditional-format and validation ranges extended. This also brings in DEC-030 to DEC-034, which were missing, and fixes the Future Work table range. On Overview, the date is updated, the count formulas are extended to the new rows, the AUD-011 row is refreshed and AUD-022 to AUD-024 are added under "Immediate attention". Recalculation: 4 formulas, 0 errors.

Not done: the 1 October `approval_record` block is unchanged, because the two change requests are not controlled document versions; the library file IDs for STD-TPL-001 v0.13 and STD-ST-001 v0.5 are unknown.
