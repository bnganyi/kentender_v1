# Change report — test notices withdrawn (10 October 2026)

Project Owner instruction, 10 October 2026, verbatim: “I am continuously discovering the highlighted throughout the app. I did not ask for them and if they exist in the documentation then that is wrong. The problem is the decision to put them in various places is opaque and they might eventually leak into production code. Remove these, including on forms, and summarize”; then: “"Simulation" checkbox: remove” and “Documentation: update all affected and the document control too”. Recorded in the register as DEC-044 and delivery item TNW-001.

## 1. Files

| Document | Input (unchanged) | Output | Status |
|---|---|---|---|
| TRUST-ADR-001 | v0.2 | v0.3 | Proposed — v0.2 stays the approved baseline |
| PRC-CHG-001 | v0.12 | v0.13 | Proposed — v0.12 stays the approved baseline |
| BOP-CHG-001 | v0.11 | v0.12 | Proposed — v0.11 stays the approved baseline |
| AWD-CHG-001 | v0.5 | v0.6 | Proposed — v0.5 stays the approved baseline |
| BDS-CHG-001 | v0.12 (itself Proposed) | v0.13 | Proposed — supersedes the v0.12 proposal; v0.11 stays the approved baseline |
| KT-DOC-CTRL-001 register | as_of 2026-10-09 | as_of 2026-10-10 | Edited in place (a register, not a versioned requirement document) |

Not changed, with the reason: EVL-CHG-001 v0.8 (its two matches, lines 735 and 781, say development test attestations cannot satisfy production signatures and record a past change; neither requires a notice); SEED-002 v0.4 (no notice requirement); KT-STD-001 v1.29 (no match); SEED-001 v1.4 and SEED-OPS-001 (retired as history on 8 October 2026).

## 2. Read list

Read in full: TRUST-ADR-001 v0.2. Read in part, by the matching sections and their control tables: PRC v0.12 (§§1, 13, 18, 20.2, control table), BOP v0.11 (header, control table, §§13, 17, 18, 19 excerpts), AWD v0.5 (header, control table, §§10, 13, 18), BDS v0.12 (header, control table, §§5.10, 13.1, 15.1, 18), EVL v0.8 and SEED-002 v0.4 (matching lines only), the register (all document, decision and delivery-item entries touched). Not read in full: the four larger specifications and KT-STD-001 v1.29.

## 3. Changes by section

| Document | Section | Operation |
|---|---|---|
| TRUST-ADR-001 v0.3 | top; control table; §2 introduction; §2 table (two cells); new “No test notices” paragraph; new Approval effect; change record | Extension, each with its v0.2 wording beside it |
| PRC-CHG-001 v0.13 | top; control table; §1 interim test binding; §13 first paragraph; §18; change record | Extension, v0.12 wording beside it |
| BOP-CHG-001 v0.12 | top; control table; deferral paragraph (two phrases); §13 verification-deployment sentence; §17 TRUST row; §18; change record | Extension |
| AWD-CHG-001 v0.6 | top; control table; §10 closed input; §13 adapter sentence; §18; change record | Extension |
| BDS-CHG-001 v0.13 | top; control table; §5.10; §15.1; §18; change record | Extension |

The rule they carry: no screen, Desk form, receipt, print view, PDF, export, message or portal shell shows a test-environment notice, a simulation or test-attestation label, or a record flag marking a record as simulated; a stand-in is recognised only through the site's simulation setting and its test-control records. Production gates and guards that stop a stand-in acting outside a test site stay.

Working documents annotated in place (dated notes beside the superseded text, nothing deleted except the stale validate item in the Bid Submission runbook): BDS v0.8 implementation plan (OD-C, D7, two list items), Bid Submission RUNBOOKS (three places), BOP v0.10 plan (D15) and tracker (two places), EVL v0.4 plan (one risk line), AWD v0.4 plan and tracker (one line each).

## 4. Preservation result

`preservation_check.py` against each input with `--allow-control-table`: PASS for all five. Changed original lines: 0. Deleted original lines: 0. Every replaced sentence keeps its previous wording inside a “v0.x read” note. The first BOP run failed on one table row that I had reworded; I rebuilt that edit so the row keeps its original text and adds a v0.12 sentence.

## 5. Consistency result

`consistency_check.py` against KT-STD-001 v1.29 and the register. No error is introduced. Errors that exist in the inputs and remain, at shifted line numbers: PRC (two §10.6 references that do not resolve), BOP (§18.1), BDS (§2.9). Pre-existing warnings, such as older versions cited in the text, are untouched. The “approval effect does not mention the current version” warnings on PRC, BOP, AWD, BDS and TRUST are cleared by the new Approval effect text.

`register_check.py` on the register alone: 0 errors. Supplied with the five new files it reports R5 errors, because the register keeps recording the approved baseline version and carries each new version as a proposal in `approval_history`, which is how it already records BDS v0.12. One new R4 warning is the TNW-001 item (implementation “Implemented” with its evidence stated in the entry).

## 6. New content for owner review

Everything in the five documents is the owner's instruction applied to places the old text named. These items are mine and need confirming: (a) the sentence in TRUST-ADR-001 v0.3 that a stored record naming the service that produced a proof or receipt is an audit fact and stays; (b) the AWD v0.6 statement that the Award operating profile's Simulation only setting stays as a guard; (c) BDS v0.13 §15.1, where a prototype is now required only to omit production Submit bid; (d) the DEC-044 and TNW-001 wording in the register.

## 7. Decisions needed

1. **Test attestation now reads as signing.** With the label gone, a member's test attestation shows as “Signed by …” on the Award opinion and elsewhere. Production signing stays disabled by the BDS production flag and the Award profile guard. Recommendation: accept, since the guards, not screen text, are what stop production use.
2. **Retained on purpose, not removed:** the Award Settings Simulation only setting (it stops a test profile counting as verified on a site that is not a test site); the Award Case source kind “Synthetic” (a stored classification that selects the source); the method recorded on a Proceeding Attestation (“Test attestation (simulation)”), which is audit attribution. Recommendation: keep all three; say if you want any hidden on forms.
3. **Approval:** all five documents are Proposed. Marking them approved is your instruction to give.

## 8. Required corrections elsewhere

None in controlled specifications. The Documentation Control Register workbook (`KenTender_Documentation_Control_Register.xlsx`) was last updated on 5 October 2026 and does not match the register for 8–10 October either; I did not regenerate it because the generator is not in the repository and no spreadsheet library is installed.

## 9. Not verified

I did not verify the five new files against the primary text of any law. I did not read the documents that cite these five at older versions (for example TPR, EVL, SEED-002); their version citations are unchanged. No browser walk was done.
