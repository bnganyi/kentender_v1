# Review record — IT-EQUIPMENT-OPEN-V1

**Authority:** STD-TPL-001 v0.3, Pass 6 (§14)
**Review date:** 2026-08-28
**Decision:** **APPROVE FOR IMPLEMENTATION PACK**

## Confirmations

| Item | Confirmed by | Basis |
|---|---|---|
| Official source and digest | bnganyi (product owner) | Gate A, 2026-08-28: `01_source/ppra_goods_std_official.pdf`, SHA-256 `95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee`, matches the originally supplied `STD-FOR-PROCUREMENT-OF-GOODS.pdf` byte-for-byte. See `01_source/source_record.md`. |
| Coverage | bnganyi (product owner) | Gate B, 2026-08-28 (initial two-output reclassification per v0.3); Gate D, 2026-08-28 (two remediation rounds, all 45 open_issues.md items 1-45 resolved). `coverage_register.csv` — 290/290 rows `Reviewed`, zero discrepancies outstanding. |
| Legal text and fixed-alternative treatment | bnganyi (product owner) | Gate D decisions on items 20-23 (blanket rules) and 36-45 (ten named judgement calls: JV cap, GCC 28.3 warranty default, ITT 13.5 rejection rule, ITT 24.6 PPADA-cited electronic opening-authentication rewrite, unified Price Schedule design, Tenderer Information Form restoration, CBQ repeatable tables, Section V renumbering, Form No. 5 Beneficiary address); Gate E items 46-52 (Tender Security expiry calculation, internal-note removal, ITT 23.3 electronic withdrawal, Advance Payment Security removal, debriefing-period citation, 12 bracketed drafting-note placeholders, Tender-reference/page-number footer). All decisions recorded with reasoning in `open_issues.md`. |
| Five-task usability | bnganyi (product owner) | Gate E walkthrough, 2026-08-28, using `04_fixture/kebs_input.json`. First walkthrough returned CORRECT AND RE-REVIEW (7 defects, see `open_issues.md` items 46-52); all corrected same day and re-presented. Second walkthrough: APPROVE FOR IMPLEMENTATION PACK. |
| Technical-specification package treatment | bnganyi (product owner) | Confirmed via `04_fixture/package_index.md` — the controlled technical specification is published as a separate file within the issued Tender package (title, version, approval date, publication filename and SHA-256 digest recorded in `kebs_input.json`), not embedded in or retyped into `complete_tender.html`. |

## Unresolved blockers

None. All 52 items in `05_review/open_issues.md` are resolved. `coverage_register.csv` is 290/290 `Reviewed`; `forms_register.csv` is 25/25 `Reviewed` or `Reviewed - confirmed excluded` (20 included, 5 excluded).

## Output boundary confirmation

`kebs_expected.html` (the issued Tender) contains zero occurrences of Invitation content; `kebs_invitation_expected.html` is a separate, standalone publication notice. Cross-output shared values (Tender reference, title, Procuring Entity, clarification deadline, submission deadline, electronic submission channel, Tender-security treatment) are consistent between both outputs. Unresolved-content scan (`{{`, `{%`, `[insert`, `[Not applicable`, etc.) returns zero matches in both rendered outputs.

## Released bundle digest — Version 1.0

Locked 2026-08-28. These are the final, reviewed artifacts for IT-EQUIPMENT-OPEN-V1 Version 1.0. Any further change is a new version, subject to its own gate sequence, not an edit to this record.

```
95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee  01_source/ppra_goods_std_official.pdf
4d058a3c2ad4af8bc8bb9e0c32fdbba11333620219a353d1109d59f01e74eb53  02_master/invitation_to_tender.html
56584474813c5532c4dac82d958e7de2582cbeebd2853b1666517817a68dbb6a  02_master/complete_tender.html
7a753ed264a586d0654249aaad573bae65ad5067e11184d947a55999cb80a4d4  02_master/print.css
b827a18bdaa6e6468d5e80506f9ba99a6f91ae634ef4f931f8bdbc4c84ff65ae  03_registers/coverage_register.csv
886ce58b3630f5ef3d1a92a44b055ac5d0a5ea7526b0f3d100a2eabcc2caee09  03_registers/insertion_points.csv
2f2716e0c6f6677c5f78babbf8b3853089297ae7667809cde437120837f2071d  03_registers/forms_register.csv
e2269202cbc0429dd76022c473faaf7909b7aecba0154d8c45ec95f76557a9ca  04_fixture/kebs_input.json
9272954f50c5f0208c019e5878fca0f338e23ed6912d48ce3ab804e4a02647a5  04_fixture/render_fixture.py
7debf3804e33da3056175907fa8cb9d14fa5261381e357e37bc2bd4f26e2af7b  04_fixture/kebs_invitation_expected.html
e2a3cdbc1c278c442adfc332b401d5bdfcfe5b094e04155200692fad240422f5  04_fixture/kebs_invitation_expected.pdf
cbba367c9dc6793a0520a7f3f7e4119fa3b2e8ce7871b907f3a225f024a0ceaa  04_fixture/kebs_expected.html
4f978b534d950e093173b13071706eb06f223fc317154865dc1fa9749a5b78f8  04_fixture/kebs_expected.pdf
f3556acf6d3809a981bc625082fd12eb63b13a06d541f6a231db66918b8d5326  04_fixture/kebs_technical_specification.pdf
57219b24d478837117c93f77553ecb4ba7158419efa60a0d70763818b3b1dda4  04_fixture/package_index.md
```

Computed via `sha256sum` on 2026-08-28, immediately after the final Gate E re-verification and the coverage-register CSV-quoting fix on COV-225 (a formatting-only correction, not a content change — see `open_issues.md`).

## Scope carried into the implementation pack

Per STD-TPL-001 v0.3 §14, no DocType, hook, route, service, permission, patch, seed or runtime template code has been created or modified under this curation instruction. `render_fixture.py` is curation-only tooling and must not be imported or installed by KenTender. A later, separately authorized implementation pack must state exactly how this reviewed master and these registers are encoded in `kentender_procurement`, and must carry forward the 14 release-evidence items listed in STD-TPL-001 v0.3 §15, all of which are satisfied by this curation pack as of this record.
