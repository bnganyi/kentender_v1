# 08 — Cursor Implementation Directive

## Objective

Implement the NSSF ERP tender proof-of-concept as a structured tender configuration fixture for the KenTender IT Tender Configuration Wizard.

Use `09_NSSF_Full_Structured_Fixture.json` as the seed source and `10_NSSF_Electronic_Bidder_Submission_Schema.json` as the bidder workspace target.

## Non-negotiable rules

1. Do not treat NSSF as the master STD.
2. Do not copy NSSF ITT/GCC as the legal source of locked clauses.
3. Render official locked ITT and GCC from the active PPRA IT STD package.
4. Store NSSF content as tender-specific configuration values, requirements, evidence requirements, price lines, evaluation records, and contract carry-forward records.
5. Preserve the original NSSF fact that electronic tenders were not permitted, but apply KenTender's electronic-only submission policy in the generated bidder workspace.
6. Do not render internal field names, fixture warnings, validation errors, or debug content into bidder-facing PDFs.
7. The 190 Section VIII requirement rows must generate bidder response controls.
8. The 22 price lines must generate electronic price-entry controls.
9. Preliminary and technical qualification records must generate mandatory document/evidence checks.
10. SCC records must generate contract carry-forward output.

## Build sequence

1. Import fixture metadata and tender profile.
2. Create CFG-01 and CFG-02 values.
3. Import Section VIII requirement rows with source trace.
4. Generate requirement response schema per row.
5. Import preliminary and technical qualification criteria.
6. Configure 100-point technical scoring with 75-point pass mark.
7. Import schedule requirements and price lines.
8. Import forms and evidence fields.
9. Import SCC contract carry-forward records.
10. Generate preview with official locked STD text plus NSSF configured values.
11. Generate electronic bidder submission workspace from schema.
12. Run validation: no missing mandatory fields, no raw source errors in preview, all row counts match fixture.

## Acceptance tests

| Test | Expected result |
|---|---|
| Requirement row count | 190 Section VIII records imported. |
| Price row count | 22 price lines imported. |
| Evaluation setup | Preliminary, technical qualification, 100-point scoring, 75 pass mark, financial lowest evaluated price. |
| Legal text | ITT and GCC come from STD Engine, not fixture prose. |
| Bidder workspace | Electronic forms, uploads, requirement response matrix, price fields, declarations, final sealed submission. |
| Contract carry-forward | Payment, security, SLA, warranty, escrow, subcontracting available after award. |
