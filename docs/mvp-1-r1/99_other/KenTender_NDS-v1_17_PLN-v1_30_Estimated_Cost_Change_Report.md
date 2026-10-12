# Change report — NDS-CHG-001 v1.17 and PLN-CHG-001 v1.30 (estimated total cost on the Need)

Prepared 9 October 2026 under the KenTender document-change protocol. Both new documents are **Proposed**. Nothing is approved and the register is not updated.

## 1. Files

| Input (unchanged) | Output (new) | Version and status |
|---|---|---|
| `01_departmental_needs/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md` | `01_departmental_needs/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_17.md` | 1.17, Proposed — v1.16 was Approved; re-approval required |
| `04_planning/KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md` | `04_planning/KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_30.md` | 1.30, Proposed — v1.29 was Approved; re-approval required |

Edit lists (56 and 24 anchored edits) were applied with `apply_edits.py`; every anchor matched exactly once.

## 2. Read list

- **Read in full:** NDS-CHG-001 v1.16 (all 2,000 lines).
- **Read in part:** PLN-CHG-001 v1.29: §§1–5.3, §6.4–6.5 (part), §§7.1–8, §§10.4–10.5, §11.9 (first rows), §13, §§14.11–14.13, §15, §§17.1–17.2, the head and tail of §17.4, and §18.0–18.3.
- **Not read for this change:** PLN v1.29 §5.3.3 to §6.4 (rest), §§9, 10.1–10.3, 10.6–10.18, 11.1–11.8, 12, 14.1–14.10, most of 17.3 and 17.4. KT-STD-001 v1.27, BUD-CHG-001 v1.12, SEED-002 v0.3, the baseline register content and the NDS and PLN implementation plans and trackers were read only through the consistency scripts and earlier research summaries.

## 3. Changes by section

**NDS v1.17:** control table; status paragraph; §1.1 row corrected beside the original; new §1.2 (the Project Owner decisions); §2.1 carve-out; §2.2 gate and row; §3 ownership; §4.3 field and paragraph; §4.9 money boundary corrected, new rows for the exact value and the hash; §4.10 label and count; §5.4 NDS-BR-004, 007, 008 extended and NDS-BR-022 to 025 added; new §7.1A (`DepartmentalNeedAccepted.v3`); §§7.1, 7.2, 7.3, 8.1, 8.2, 9 (two new codes), 10, 11.1, new §11.19 (placement on every screen), §§12.3, 12.5, 12.10; new §14.3A (fixtures); acceptance rows corrected beside the original and new §15.6 (NDS17-AC-001–010); §§17, 18.1–18.3 (six change rows, six dependencies), 19; new §20.0.

**PLN v1.30:** control table; status paragraph; §1.2 and §3 rows; §4.3 entry reference and eight prefill and change rules; §7.3 `.v3` row; §10.4 variants U03-FUNDING-PREFILLED and U03-FUNDING-CHANGED, U03-REINCLUDE, U05 and U06 estimate-change lines; §11.9 row; §13.3 profile; new §14.14 (PLN30-AC-001–009); §§15.2, 17.1, 17.4 (four rows); new §18.0A.

## 4. Preservation

Both pass. NDS: 2,001 → 2,123 lines, **0 changed, 0 deleted**, 36 lines extended in place. PLN: 3,181 → 3,243 lines, **0 changed, 0 deleted**, 8 lines extended in place. Control-table rows were allowed to change; each previous value is kept as a "(retained)" row. No original line is altered or removed, so there is nothing to list verbatim.

## 5. Consistency

- NDS: no ERROR. WARN C5 (the retained §20.1 still says 132 criteria and 56 rows, and the document now defines 142 and 62 — historical text, correct under v1.15) and C7 (several versions cited: provenance). The C2 warning on "§3A.6" and the other C7 warnings were already in v1.16.
- PLN: 3 ERROR (C9, table rows with 6 cells under a 7-column header) **pre-existing** in v1.29 (same count before and after). The C7 warnings are provenance.
- Counts stated in the new text were recomputed by the script: 142 acceptance criteria and 62 change rows. 23 dependencies counted by hand (17 + 6).
- `register_check.py`: only pre-existing warnings. The register is **not** updated, because the documents are not approved.

## 6. New content for owner review

Everything below has no source in an approved document.

- Field `estimated_total_cost` and the Planning reference `need_estimated_total_cost`; the label **Estimated cost**; placement after the Quantity and Unit row; the currency shown read-only beside the label.
- Error codes `NDS_ESTIMATE_PRECISION_INVALID` and `NDS_ESTIMATE_CURRENCY_UNAVAILABLE`, with their user messages.
- Event `DepartmentalNeedAccepted.v3` and the proposal that `DepartmentalNeedSuperseded` moves to `.v2`.
- Bold wording in NDS §§9 and 11.19 and PLN §§10.4 and 10.5 (for example **Accepted requirement estimate: KES 80,000,000. Change: +KES 5,000,000.**).
- Fixture values: KES 20,000,000 for NDS-MOH-2027-0003 Revision 2 (derived from KES 130,000,000 minus KES 110,000,000 in PLN v1.29 §§13.2 and 10.4), KES 85,000,000 as the revised planning amount, and KES 35,000,000 for the deployment laptops in the PLN §13.3 profile.
- The rule that the content hash includes the estimate only when present.

## 7. Decisions needed

1. **Is the requester the Project Owner for §1.2?** I recorded the two answers given in this session as Project Owner decisions of 9 October 2026, quoting them. Correct this if they were not.
2. **`DepartmentalNeedSuperseded.v1`:** it embeds the accepted payload. Recommendation: move it to `.v2` in the same cutover (as drafted).
3. **Currency mismatch:** if the selected Budget Line's currency differs from the Fiscal Year currency used for the Need, should the prefill still apply? Drafted as: it applies as a number and the line's precision rules validate it. Recommendation: confirm that the site has one currency per Fiscal Year so the case cannot arise.
4. **Estimates for NDS-MOH-2027-0002 and 0003 Revision 1:** no document states them (marked Awaiting fixture).
5. **Workspace registers:** drafted with no estimate column. Recommendation: keep it out until users ask.

## 8. Required corrections elsewhere

- SEED-002: a v0.4 carrying the §14.3A estimates (NDS §A4.2 lists the Need facts).
- BUD-CHG-001 v1.12: check its wording on the Need's source facts against seven facts.
- Baseline register: on approval, update NDS and PLN entries and interface IF-003 (its `owner_doc` is stale at NDS v1.14 and PLN v1.27).
- NDS and PLN implementation plans and trackers (they lag their approved versions: v1.14 and v1.23).
- Design boards: NDS-DES-03, 04, 05, 06, 07, 08, 09, 12, 15, TERMINAL; Planning U03, U05, U06.
- Pre-existing, not changed: PLN v1.29 §1.2 cites NDS v1.14 and v1.15 as current, while the register current version is v1.16; the register says NDS v1.16 supersedes v1.14, the control table says v1.15.

## 9. Not verified

Anything about Budget's currency contract (that it returns precision without a Budget Line); BUD and SEED wording; the unread PLN sections; the existing code; the artboards. No legal proposition is made.
