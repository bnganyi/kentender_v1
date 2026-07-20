# 01 — Source Coverage Audit

## Coverage summary

| NSSF source area | Source pages | Extracted records | Target owner |
|---|---:|---:|---|
| Cover and invitation | 1, 5 | Tender profile and invitation values | CFG-01, CFG-02 |
| Tender Data Sheet | 9 | 17 rows | CFG-02 and CFG-09 split |
| Preliminary mandatory requirements | 10 | 9 rows | CFG-07, CFG-08 |
| Technical qualification criteria | 11 | 9 rows | CFG-07, CFG-08 |
| Technical scoring criteria | 12 | 7 criteria | CFG-07 |
| Tendering forms | 13-16 | 4 forms | CFG-08 |
| Background and objectives | 17 | 1 structured background record | CFG-05 |
| Scope and phases | 18 | 2 implementation phases | CFG-04 |
| Technical module summary | 19-21 | module summary in fixture | CFG-03 |
| Section VIII compliance matrix | 22-52 | 190 rows | CFG-03, CFG-04, CFG-09 |
| Schedule of requirements | 53 | 6 rows | CFG-04, CFG-06 |
| Price schedule | 54-55 | 22 lines | CFG-06 |
| GCC | 56-57 | locked-text strategy, not copied into wizard | STD Engine |
| SCC | 58 | 8 carry-forward records | CFG-09 |
| Contract forms | 59-61 | contract form outputs after award | Contract module |

## Quality control notes

1. The fixture contains 190 Section VIII requirement rows. This is the critical correction from the previous compressed pack.
2. NSSF ITT/GCC text is not treated as the legal master. Production rendering must use the official PPRA IT STD text in the STD Engine.
3. The NSSF source says electronic tenders are not permitted. KenTender's target process is electronic-only, so this is preserved as a source fact and handled as a platform-policy override.
4. Several NSSF values mix TDS and SCC concerns. The pack normalizes payment, performance security, SLA, warranty, escrow, and subcontracting into CFG-09.
