# STD-WORKS-POC Acceptance Evidence Pack

**Evidence location:** `kentender_procurement/.../tender_management/std_templates/ke_ppra_works_building_2022_04_poc/evidence/` (stable path per **STD-POC-003**; differs from Step 17 spec literal `procurement/std_templates/...`).

**Primary automation:** Step 16 integration tests + Step 16 Playwright smoke. Manual Desk screenshots are optional under `evidence/screenshots/` (see `screenshots/README.md`).

---

## 1. Acceptance Summary

| Field | Value |
|---|---|
| **Overall outcome** | **Accepted with Limitations** |
| **Rationale** | Core Step 16 primary path and required negative blocking behaviours are evidenced by automated tests. Formal reviewer sign-off (§18) is still outstanding. Known POC limitations (§16) are explicit and non-blocking for POC closure. |
| **Blockers** | None identified in automated smoke (see `issue_log.md`). |

---

## 2. POC Identity

| Field | Value |
|---|---|
| POC name | `STD-WORKS-POC` |
| Template code | `KE-PPRA-WORKS-BLDG-2022-04-POC` |
| Template short name | `PPRA Works STD — Building and Civil Works` (from `manifest.json`) |
| Package version | `0.1.0-poc` |
| Source document code | `DOC. 1` |
| Procurement category | `WORKS` |
| Template family | `BUILDING_AND_ASSOCIATED_CIVIL_ENGINEERING_WORKS` |
| Frappe site (reference) | `kentender.midas.com` (used in tracker evidence commands) |
| App branch/commit | `e286b3e` (`apps/kentender_v1` git root). Bench root may not be a git repo. |
| Date executed | `2026-05-01` (aligned with Step 16 tracker evidence) |
| Executed by | Automated CI / developer runs (`Administrator` in integration tests; Step 16 Playwright uses configured Desk users per `.env.ui`) |

---

## 3. Package Artefacts Reviewed

All files live under `.../ke_ppra_works_building_2022_04_poc/`.

| File | Exists | JSON parses | In package hash | Notes |
|---|---|---:|---:|---|
| `manifest.json` | Yes | Yes | Yes | STEP2–3 structural tests + loader |
| `sections.json` | Yes | Yes | Yes | Package skeleton tests |
| `fields.json` | Yes | Yes | Yes | |
| `rules.json` | Yes | Yes | Yes | |
| `forms.json` | Yes | Yes | Yes | |
| `render_map.json` | Yes | Yes | Yes | |
| `sample_tender.json` | Yes | Yes | Yes | |
| `README.md` | Yes | n/a | **No** | Required by loader; excluded from SHA-256 digest per Step 10 hash policy |

---

## 4. Environment and Execution Context

| Field | Content |
|---|---|
| Frappe version | Not captured in this artefact generation run — obtain via `bench version` or site **About** on the target environment. |
| ERPNext version | Not captured — include if installed. |
| Custom app name | `kentender_procurement` (KenTender v1 app path `apps/kentender_v1/kentender_procurement`) |
| Site name | `kentender.midas.com` (reference site from implementation tracker) |
| User role | Integration tests: `Administrator`. Playwright Step 16: role per smoke spec (e.g. governance user with Procurement Tender access). |
| Browser | Playwright: Chromium (see `apps/kentender_v1/playwright.config.ts`). |
| Execution mode | **Mixed:** `bench run-tests`, optional `bench execute ... import_std_works_poc_template`, Desk UI via Playwright. |
| Data isolation | Integration tests run in Frappe test transaction where applicable; avoid relying on production data deletion without site policy. |

---

## 5. End-to-End Smoke Result

Summary of Step 16 primary smoke path (STEP16-AC-001..013).

| Smoke step | Expected result | Observed result | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Seed loader import | Template imported | `import_std_works_poc_template()` returns `ok`, `template_code`, `package_hash` | Pass | `test_step16_primary_smoke_ac001_to_ac013` |
| STD Template verification | Record populated | `STD Template` exists for `KE-PPRA-WORKS-BLDG-2022-04-POC` with `package_json`, `manifest_json`, `package_hash` | Pass | Same |
| Procurement Tender creation | Tender saved and linked | Tender created with `std_template` set | Pass | Same (`setUp` + assertions) |
| Load sample tender | Configuration/lots/BoQ populated | Title/reference match sample; 2 lots; 9 BoQ rows; `configuration_json` set | Pass | Same |
| Validate configuration | Passed without blockers | `validation_status == Passed`; no BLOCKER/ERROR messages | Pass | Same |
| Generate required forms | Expected forms generated | 15 forms in `PRIMARY_SAMPLE_ACTIVATED_FORMS` order | Pass | Same |
| Generate tender-pack preview | Preview generated | `generate_tender_pack_preview` ok; HTML shell + headings | Pass | Same |
| Audit summary | Hashes/status visible | Package Hash, Configuration Hash, Validation Status, template code, version, DOC. 1 in HTML | Pass | Same |

**Automated module:** `kentender_procurement.tender_management.tests.test_std_works_poc_step16_end_to_end_smoke`

**Desk UI:** `apps/kentender_v1/tests/ui/smoke/procurement/std-poc-step16-e2e-smoke.spec.ts`

---

## 6. Template Import Evidence

1. **Loader entrypoint (repo actual path — STD-POC-017):**  
   `kentender_procurement.tender_management.services.std_template_loader.import_std_works_poc_template`

2. **Bench execute (reference):**  
   `bench --site kentender.midas.com execute kentender_procurement.tender_management.services.std_template_loader.import_std_works_poc_template`

3. **Result summary:** Tests assert `ok`, `template_code == KE-PPRA-WORKS-BLDG-2022-04-POC`, non-empty `package_hash`.

4. **STD Template name:** Resolved via `frappe.db.get_value("STD Template", {"template_code": TEMPLATE_CODE}, "name")`.

5. **STD Template record screenshot:** Optional — `evidence/screenshots/16_std_template_record.png` (not required when automation passes).

| Check | Expected | Observed | Pass/Fail |
|---|---|---|---|
| Loader completed | Yes | `import` returns `ok` | Pass |
| One STD Template record exists | Yes | DB lookup succeeds | Pass |
| Template code correct | Yes | Matches `KE-PPRA-WORKS-BLDG-2022-04-POC` | Pass |
| Package JSON populated | Yes | `package_json` parses; payload keys ⊇ expected set | Pass |
| Manifest JSON populated | Yes | `manifest_json` present | Pass |
| Package hash populated | Yes | On document and in import result | Pass |
| No duplicate template record | Yes | Idempotent upsert (Step 10 design) | Pass |

---

## 7. Tender Creation and Sample Load Evidence

| Check | Expected | Observed | Pass/Fail |
|---|---|---|---|
| Tender saved | Yes | Created in test `setUp` | Pass |
| Linked template | `KE-PPRA-WORKS-BLDG-2022-04-POC` | Asserted | Pass |
| Sample tender title loaded | `Construction of Ward Administration Block` | Asserted | Pass |
| Sample reference loaded | `CGK/WKS/OT/001/2026` | Asserted | Pass |
| Configuration JSON populated | Yes | Asserted | Pass |
| Lots populated | 2 rows | `len(tender.lots) == 2` | Pass |
| BoQ populated | 9 rows after load | `len(tender.boq_items) == 9` | Pass |

**Evidence:** `test_step16_primary_smoke_ac001_to_ac013` (STEP16-AC-004..006).

---

## 8. Validation Evidence

| Check | Expected | Observed | Pass/Fail |
|---|---|---|---|
| Validation status | `Passed` | `tender.validation_status == Passed` | Pass |
| Blocks generation | False | Primary sample allows preview | Pass |
| Configuration hash populated | Yes | Via validate/generate pipeline | Pass |
| Tender security amount rule | Pass | Within 2% for primary sample | Pass |
| Date ordering rules | Pass | No blockers on primary | Pass |
| BoQ row rules | Pass | No duplicate `item_code` | Pass |
| Required-field rules | Pass | No ERROR/BLOCKER messages | Pass |

**Evidence:** `test_step16_primary_smoke_ac001_to_ac013` (STEP16-AC-007).

---

## 9. Required Forms Evidence

### Primary sample form table

| Expected order | Form code | Expected included? | Observed included? | Activation source | Evidence reference |
|---:|---|---:|---:|---|---|
| 10 | `FORM_OF_TENDER` | Yes | Yes | DEFAULT (+ rules where applicable) | `PRIMARY_SAMPLE_ACTIVATED_FORMS` vs tender rows |
| 20 | `FORM_CONFIDENTIAL_BUSINESS_QUESTIONNAIRE` | Yes | Yes | | Step 16 primary test |
| 30 | `FORM_CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION` | Yes | Yes | | |
| 40 | `FORM_SELF_DECLARATION` | Yes | Yes | | |
| 50 | `FORM_TENDER_SECURITY` | Yes | Yes | | |
| 70 | `FORM_JV_INFORMATION` | Yes | Yes | | |
| 90 | `FORM_ALTERNATIVE_TECHNICAL_PROPOSAL` | Yes | Yes | | |
| 100 | `FORM_TECHNICAL_PROPOSAL` | Yes | Yes | | |
| 110 | `FORM_SIMILAR_EXPERIENCE` | Yes | Yes | | |
| 120 | `FORM_FINANCIAL_CAPACITY` | Yes | Yes | | |
| 130 | `FORM_PERSONNEL_SCHEDULE` | Yes | Yes | | |
| 140 | `FORM_EQUIPMENT_SCHEDULE` | Yes | Yes | | |
| 150 | `FORM_BENEFICIAL_OWNERSHIP_DISCLOSURE` | Yes | Yes | | |
| 160 | `FORM_PERFORMANCE_SECURITY` | Yes | Yes | | |
| 170 | `FORM_ADVANCE_PAYMENT_SECURITY` | Yes | Yes | | |

### Exclusion table (primary sample)

| Form code | Expected excluded? | Observed excluded? | Reason |
|---|---:|---:|---|
| `FORM_TENDER_SECURING_DECLARATION` | Yes | Yes | Tender security mode is `TENDER_SECURITY` |
| `FORM_FOREIGN_TENDERER_LOCAL_INPUT` | Yes | Yes | Primary sample is national tender |
| `FORM_RETENTION_MONEY_SECURITY` | Yes | Yes | Retention money security is false |

### Checks

| Check | Expected | Observed | Pass/Fail |
|---|---|---|---|
| Required form count | 15 | 15 | Pass |
| Duplicate form codes | 0 | 0 | Pass |
| Activation source populated | Yes | Rows persisted after `generate_required_forms` | Pass |
| Evidence policy populated | Yes | Covered by Step 14 module | Pass |
| Display order stable | Yes | Exact list match `PRIMARY_SAMPLE_ACTIVATED_FORMS` | Pass |

---

## 10. Sample BoQ Evidence

| Expected row | Item category | Expected present? | Observed present? | Evidence reference |
|---:|---|---:|---:|---|
| 1 | `PRELIMINARIES` | Yes | Yes | Step 16 + Step 15 tests |
| 2 | `SUBSTRUCTURE` | Yes | Yes | |
| 3 | `SUPERSTRUCTURE` | Yes | Yes | |
| 4 | `ROOFING` | Yes | Yes | |
| 5 | `FINISHES` | Yes | Yes | |
| 6 | `EXTERNAL_WORKS` | Yes | Yes | |
| 7 | `DAYWORKS` | Yes | Yes | |
| 8 | `PROVISIONAL_SUMS` | Yes | Yes | |
| 9 | `GRAND_SUMMARY` | Yes | Yes | |

| Check | Expected | Observed | Pass/Fail |
|---|---|---|---|
| BoQ row count | 9 | 9 | Pass |
| Duplicate item codes | 0 | 0 | Pass |
| Dayworks row present | Yes | Yes | Pass |
| Provisional sums row present | Yes | Yes | Pass |
| Lot references valid | Yes | Asserted in Step 16 | Pass |
| BoQ preview warning present | Yes | POC / disclaimer path in `boq_summary.html` + Step 13 tests | Pass |

---

## 11. Tender-Pack Preview Evidence

| Preview section | Expected present? | Observed present? | Evidence reference |
|---|---:|---:|---|
| POC warning | Yes | Yes | `POC_WARNING_KEY_PHRASE` in HTML |
| Tender Cover and Identity | Yes | Yes | `REQUIRED_PREVIEW_HEADINGS` |
| Invitation to Tender summary | Yes | Yes | Heading `Invitation to Tender` |
| Active STD Sections | Yes | Yes | |
| Locked STD Sections Notice | Yes | Yes | |
| Tender Data Sheet Summary | Yes | Yes | |
| Evaluation and Qualification Criteria Summary | Yes | Yes | |
| Required Bidder Forms Checklist | Yes | Yes | |
| Bills of Quantities Summary | Yes | Yes | |
| Specifications and Works Requirements Summary | Yes | Yes | |
| Drawings Summary | Yes | Yes | |
| Special Conditions of Contract Summary | Yes | Yes | |
| Contract Forms Checklist | Yes | Yes | |
| Template and Configuration Audit Summary | Yes | Yes | |

**Outcome checks**

1. `generated_tender_pack_html` populated — **Pass** (Step 16).
2. Preview readable on tender record — **Pass** (Playwright Step 16 + manual policy).
3. Preview does not claim legal certification — **Pass** (warning phrases asserted).
4. Preview does not render full PPRA legal text — **Pass** (POC scope; representative summaries only).

---

## 12. Audit and Reproducibility Evidence

| Audit item | Expected | Observed | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Template code | `KE-PPRA-WORKS-BLDG-2022-04-POC` | In HTML | Pass | Step 16 AC-013 |
| Package version | `0.1.0-poc` | In HTML | Pass | |
| Source document code | `DOC. 1` | In HTML | Pass | |
| Package hash | Matches `STD Template.package_hash` | Asserted substring | Pass | |
| Configuration hash | Matches tender / result | Asserted in HTML | Pass | |
| Validation status | `Passed` (primary) | In audit section | Pass | |
| Last generated timestamp | Present | Render context / audit partial | Pass | |

---

## 13. Negative Scenario Evidence

### 13.1 Missing Site Visit Date/Location (`VARIANT-MISSING-SITE-VISIT-DATE`)

| Check | Expected | Observed | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Variant loaded | Yes | `load_sample_variant` | Pass | `test_step16_ac014_site_visit_variant_blocks_preview` |
| Validation status | `Blocked` | Pipeline blocks preview | Pass | |
| Missing site visit message | Present | Via validation messages (detail in Step 11/16) | Pass | |
| Preview generation | Blocked | `ok` false, `blocks_generation` true, HTML cleared | Pass | |

### 13.2 Missing Alternative Scope (`VARIANT-MISSING-ALTERNATIVE-SCOPE`)

| Check | Expected | Observed | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Variant loaded | Yes | | Pass | `test_step16_ac015_alternative_scope_variant_blocks_preview` |
| Validation status | `Blocked` | | Pass | |
| Missing alternative scope message | Present | | Pass | |
| Preview generation | Blocked | | Pass | |

### 13.3 Tender Security Amount Above 2 Percent

| Check | Expected | Observed | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Tender security amount changed | Above 2% of estimated cost | Set to 3,000,000 vs 100,000,000 estimated | Pass | `test_step16_ac016_excessive_tender_security_blocks_preview` |
| Validation status | `Blocked` | BLOCKER includes `RULE_TENDER_SECURITY_AMOUNT_LIMIT_2_PERCENT` | Pass | |
| Security amount limit message | Present | Rule fires | Pass | |
| Preview generation | Blocked | | Pass | |

---

## 14. Positive Variant Evidence

### 14.1 Tender-Securing Declaration (`VARIANT-TENDER-SECURING-DECLARATION`)

| Check | Expected | Observed | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Variant loaded | Yes | | Pass | `test_step16_ac017_tender_securing_declaration_variant` |
| Tender-securing declaration form | Included | `FORM_TENDER_SECURING_DECLARATION` in set | Pass | |
| Tender security form | Excluded | `FORM_TENDER_SECURITY` not in set | Pass | |
| Duplicate security forms | None | | Pass | |

### 14.2 International Variant (`VARIANT-INTERNATIONAL`)

| Check | Expected | Observed | Pass/Fail | Evidence reference |
|---|---|---|---|---|
| Variant loaded | Yes | | Pass | `test_step16_international_variant_foreign_form` |
| Foreign tenderer local input form | Included | `FORM_FOREIGN_TENDERER_LOCAL_INPUT` | Pass | |
| Default core forms | Still included | All `DEFAULT_REQUIRED_FORM_CODES` present | Pass | |

---

## 15. Known Issues and Dispositions

Cross-reference: `issue_log.md` (no SMOKE-NNN entries filed).

| Issue ID | Severity | Area | Description | Status | Decision | Owner |
|---|---|---|---|---|---|---|
| — | — | — | No Step 16 smoke issues filed | Closed | N/A | Engineering |

Tracker-level deviations (paths, tests): see **`STD-POC-001` … `STD-POC-017`** in `apps/kentender_v1/docs/prompts/std poc/ISSUES_LOG.md`.

---

## 16. Explicit POC Limitations

1. The POC does not reproduce the full PPRA Works STD legal text.
2. The POC does not generate a legally certified final tender PDF.
3. The POC does not implement bidder portal submission.
4. The POC does not implement electronic bid sealing or opening.
5. The POC does not implement evaluation committee workflow.
6. The POC does not implement award workflow.
7. The POC does not implement contract execution workflow.
8. The POC does not implement production-grade template lifecycle governance.
9. The POC does not implement production permission hardening.
10. The POC does not implement external registry verification.
11. The BoQ is representative and not a production-grade BoQ module.
12. Structured bidder form schemas are minimal and do not yet represent full bidder submission screens.
13. Source STD change management remains developer-controlled in the POC.

---

## 17. Acceptance Checklist

| ID | Acceptance item | Required result | Observed result | Pass/Fail | Evidence reference |
|---|---|---|---|---|---|
| ACC-001 | Package imports successfully | Pass | Pass | Pass | Step 16 primary test |
| ACC-002 | `STD Template` stores package JSON and hash | Pass | Pass | Pass | |
| ACC-003 | Tender can link to STD template | Pass | Pass | Pass | |
| ACC-004 | Sample tender loads controlled configuration | Pass | Pass | Pass | |
| ACC-005 | Lots are structured child rows | 2 rows | 2 | Pass | |
| ACC-006 | BoQ is structured child data | 9 rows | 9 | Pass | |
| ACC-007 | Primary validation passes | Pass | Pass | Pass | |
| ACC-008 | Required forms generated correctly | 15 forms | 15 | Pass | |
| ACC-009 | Conditional form variants behave correctly | Pass | Pass | `test_step16_ac017_*`, international |
| ACC-010 | Negative scenarios block generation | Pass | Pass | AC-014..016 tests |
| ACC-011 | Tender-pack preview generated | Pass | Pass | |
| ACC-012 | Preview includes POC warning | Pass | Pass | |
| ACC-013 | Preview includes audit summary | Pass | Pass | |
| ACC-014 | Package hash visible and consistent | Pass | Pass | |
| ACC-015 | Configuration hash visible and consistent | Pass | Pass | |
| ACC-016 | No out-of-scope production workflows introduced | Pass | Pass | Scope boundaries in Steps 9–16 |

---

## 18. Reviewer Sign-Off

| Reviewer role | Name | Decision | Comments | Date |
|---|---|---|---|---|
| Product Owner |  | *Pending* |  |  |
| Procurement SME |  | *Pending* |  |  |
| Legal/Compliance Reviewer |  | *Pending* |  |  |
| Technical Lead |  | *Pending* |  |  |
| QA Reviewer |  | *Pending* |  |  |

---

## 19. Acceptance Decision

1. **Final outcome:** **Accepted with Limitations** (pending human sign-off in §18).
2. **Decision rationale:** Step 16 automated evidence satisfies ACC-001..016 for engineering verification; limitations §16 are acknowledged and match POC scope.
3. **Conditions:** Reviewers complete §18; optional screenshots added if procurement/legal require Desk-visible artefacts beyond automation.
4. **Known limitations accepted:** As listed in §16.
5. **Required next step:** **Step 18** — production gap analysis per `apps/kentender_v1/docs/prompts/std poc/18. std_works_poc_production_gap_analysis_specification.md`.
