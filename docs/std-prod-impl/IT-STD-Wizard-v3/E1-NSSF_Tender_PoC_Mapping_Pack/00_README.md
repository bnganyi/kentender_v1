# NSSF Structured Extraction Fixture Pack v1.0

This replaces the earlier compressed NSSF packs.

It is a row-level proof-of-concept fixture for the KenTender IT Tender Configuration Wizard. It extracts the NSSF ERP tender into concrete data that Cursor can seed, validate, render, and use to generate an electronic bidder workspace.

## What changed

| Previous pack problem | This pack correction |
|---|---|
| Narrative summary only | Row-level fixture with TDS rows, evaluation rows, form fields, 190 Section VIII requirement rows, schedule rows, price lines, SCC records, and bidder submission schema. |
| First-pass seed was too summarized | New JSON fixture includes actual requirement records and response metadata. |
| Markdown had unnecessary code blocks | This pack uses normal Markdown prose and tables. |
| Bidder submission schema was broad only | New schema includes actual sections, fields, preliminary documents, qualification requirements, all requirement response rows, and price lines. |

## Source coverage

| Source area | Extracted into |
|---|---|
| Cover, Invitation, TDS | Tender profile and CFG-02 TDS records |
| Evaluation criteria | Preliminary, technical qualification, technical scoring, financial basis |
| Tendering forms | Structured e-form definitions |
| Background and objectives | CFG-05 bidder-facing context |
| Section VIII compliance matrix | 190 row-level requirement records |
| Schedule of requirements | CFG-04/CFG-06 delivery items |
| Price schedule | 22 electronic price lines |
| SCC | Contract carry-forward records |

## Non-negotiable production rule

NSSF is not the master STD. The official PPRA IT STD remains the legal source for locked ITT, GCC, standard forms, render order, and allowed configuration slots. This fixture tests whether a real tender instance can be represented without turning the wizard into a document editor.

## Files in this pack

| File | Purpose |
|---|---|
| 01_Source_Coverage_Audit.md | Coverage counts and source mapping. |
| 02_TDS_Profile_and_Invitation_Extraction.md | Tender profile, invitation, TDS, and SCC rows from TDS. |
| 03_Evaluation_and_Forms_Extraction.md | Preliminary checks, technical qualification, scoring, and forms. |
| 04_Requirement_Matrix_Full_Row_Extraction.md | Human-readable full requirement matrix. |
| 04_Requirement_Matrix_Full_Row_Extraction.csv | Importable requirement matrix rows. |
| 05_Schedule_and_Price_Schedule_Extraction.md | Schedule of requirements and price schedule. |
| 05_Price_Schedule_Lines.csv | Importable price schedule lines. |
| 06_Contract_Carry_Forward.md | SCC, SLA, payment, warranty, escrow, subcontracting, performance security. |
| 07_Wizard_Mapping_and_Gap_Register.md | Mapping decisions and gaps. |
| 08_Cursor_Implementation_Directive.md | Cursor-ready build directive. |
| 09_NSSF_Full_Structured_Fixture.json | Main implementation seed fixture. |
| 10_NSSF_Electronic_Bidder_Submission_Schema.json | Bidder workspace schema. |
| 11_Traceability_Index.csv | Source area to wizard/output traceability. |

## Extraction counts

| Area | Count |
|---|---:|
| TDS/SCC table rows | 17 |
| Preliminary mandatory requirements | 9 |
| Technical qualification requirements | 9 |
| Technical scoring criteria | 7 |
| Section VIII requirement rows | 190 |
| Schedule requirement rows | 6 |
| Price schedule lines | 22 |
| SCC carry-forward conditions | 8 |
