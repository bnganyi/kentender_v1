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

## Version 1.1 — delta review record (prepared 2026-09-08; decision pending)

**Authority:** STD-TPL-001 v0.5 (approved 7 September 2026) — the Version 1.1 correction TPR-CHG-001 v0.6 §6.2 depends on. Prepared under TPR-CHG-001 v0.6 Phase 1 as a bounded delta on the locked Version 1.0 artefacts above; the Version 1.0 record and its manifest are unchanged history.

**What changed from Version 1.0** (full detail in `open_issues.md` items 53–63):

1. Section V's technical specification is generated from the structured technical requirement rows inherited from the authorised Requisition handoff v1.3 (`technical_requirements[]`, V.3), the package-level warranty and support values (V.4), supporting materials (V.5) and acceptance requirements (V.6); the Version 1.0 controlled-PDF cover sheet, its five `technical_specification.*` keys, the fixture PDF and the package-index entry are retired.
2. Section III renders one fixed eligibility clause per reservation category, citing regulation 149, only when `reservation.category` is not `None`; the Invitation carries the matching eligibility sentence.
3. Section IV gains three KenTender supplier-response schedules — Technical Compliance Response (one row per `technical_requirement_id`), Related Services Confirmation (conditional) and Acceptance Requirements Confirmation.
4. Goods lines are inherited and grouped per specification with every contributing Requisition item ID shown; related-service rows take the handoff shape with stable IDs.
5. The golden fixture is the Ministry of Health scenario (`TND-MOH-2027-033`, `REQ-MOH-2027-033-001`, `PPI-MOH-2027-033`; Brian Wafula prepares, Charles Mutiso approves) — `moh_input.json` replaces `kebs_input.json`, and the `kebs_*` fixture files are removed from the workspace (retained in git history and in the Version 1.0 manifest above).

**Confirmations for Gate TPL-G07** (to be completed by the reviewer):

| Item | Confirmed by | Basis |
|---|---|---|
| Official source and digest | — | Unchanged: `01_source/ppra_goods_std_official.pdf`, SHA-256 `95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee`. |
| Coverage | — | `coverage_register.csv` 296 rows: 290 Version 1.0 rows (`Reviewed`; COV-160, 236–241 re-treated for 1.1) + COV-291..296 (`Draft checked`). |
| Legal text and fixed-alternative treatment | — | Open item 53 (reservation clause wording) requires procurement/legal confirmation. |
| Five-task usability | — | Walkthrough with `moh_input.json` owed at this gate. |
| Structured Section V treatment | — | `package_index.md` "Section V structured-content confirmation": eleven TECH rows, five ACC rows, one grouped goods line, no specification file. |

**Unresolved blockers:** open item 53 (decision required); otherwise none.

**Output boundary confirmation (re-run 2026-09-08):** `moh_expected.html` contains no Invitation notice (its two case-insensitive "invitation to tender" phrases are locked ITT text, identical in count to Version 1.0); `moh_invitation_expected.html` is a standalone notice; shared values (reference, title, Procuring Entity, clarification and submission deadlines, submission channel, Tender-security amount) present in both; unresolved-content scan returns nothing in either output; Strategic Objective and plan horizon are absent from both outputs.

**Decision:** PENDING — Gate TPL-G07 (owner). Options: APPROVE FOR IMPLEMENTATION PACK v1.1 / CORRECT AND RE-REVIEW / REJECT.

## Candidate bundle digest — Version 1.1 (computed 2026-09-08, not yet locked)

Becomes the released Version 1.1 manifest only on an APPROVE decision above; any correction before then recomputes it.

```
95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee  01_source/ppra_goods_std_official.pdf
a53609f746ffdf7f0808fba2577ebcdb4241ac760168a463c8c68d3bfe9f32fb  02_master/invitation_to_tender.html
026c21b0174317546a5a3b429dac8ca4f82e0f5ada72ca7769174820fddc9f51  02_master/complete_tender.html
7a753ed264a586d0654249aaad573bae65ad5067e11184d947a55999cb80a4d4  02_master/print.css
5ea3b424d678551b2bff9b0145cc2f2587b506fd19284da22e84050637d33a91  03_registers/coverage_register.csv
b94c7217c9fddee6342b7ac9fbe86c01585f404f8c6639d14489da4ec048207a  03_registers/insertion_points.csv
5ed01e1fcc2c6ff200025340b2fcb8fc279efb2f01f26f0f96bbd5d1427c82d9  03_registers/forms_register.csv
86c823ad790f20f7100f015b31de4218bfa758e53c7bfc68f4d479c274b46206  04_fixture/moh_input.json
232b1c526e9d7645f3e97638198c6d94039fe8f25d972e3f873b6d42981e23f4  04_fixture/render_fixture.py
e00450fc8753f2a4d3038cab81a4f5fc95522ea04f2eeb8b87b5781b888ee297  04_fixture/moh_invitation_expected.html
2ac542561b61f7f4bdf0a184a07a3b95751d7d25dd6e67a805444ecb6f767a3a  04_fixture/moh_invitation_expected.pdf
d6a13535d118a8f64132fffaf275a397514065f3960076c8ffcb17e143691af5  04_fixture/moh_expected.html
d3ad2bdabf1f5ca2d57a94010cb3d99f1c16a378e844f56da553f6d815808f84  04_fixture/moh_expected.pdf
1d4adcae7047fff4e9937f4ecdb5d5f3e76e7e7268f4614de1624a35994f40b4  04_fixture/package_index.md
```
