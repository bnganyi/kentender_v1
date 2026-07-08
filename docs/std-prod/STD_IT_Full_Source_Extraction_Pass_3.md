# STD for Procurement of Information Technology - Full Source Extraction Pass 3

**Package:** `KE-PPRA-IT-2022-04`  
**Target engine:** Generalized STD Engine Core  
**Artifact status:** Draft extraction register - not activatable  
**Generated:** 2026-07-07 20:28 UTC  
**Pass focus:** Evaluation, qualification, tendering forms, and price schedule schemas

---

## 1. Purpose

This document is Pass 3 of the full source extraction for the official PPRA Standard Tender Document for Procurement of Information Technology. Pass 1 established source evidence, section anchors, locked ITT and GCC clause registers, and initial mutability classification. Pass 2 extracted the controlled TDS and SCC parameter surfaces.

Pass 3 converts the following portions of the official IT STD into implementation-ready engine structures:

1. **Section III - Evaluation and Qualification Criteria**
2. **Section IV - Tendering Forms**
3. **Price Schedule Forms**
4. **Qualification Forms**
5. **Form-to-rule bindings**
6. **Supplier response schema implications**
7. **Financial evaluation and recurrent-cost schema implications**

The result is not a final legal package. It is a structured extraction register that the engine can later convert into seed JSON files, database records, render blocks, validation contracts, and supplier submission screens.

The approach remains generalized. Although this pass is for the IT STD, the engine design must support equivalent constructs in WORKS, GOODS, CONSULTANCY, NON-CONSULTANCY SERVICES, SMALL WORKS, FRAMEWORK AGREEMENTS, and future STD families.

---

## 2. Source basis

| Source | Role in this pass | Handling |
| --- | --- | --- |
| Official PPRA IT STD, DOC 10 | Legal master source | Used for Section III, Section IV, price schedules, and qualification forms. |
| Rendered official source derivative | Page-anchor support | Used to stabilize section/page anchors. |
| Text extraction derivative | Extraction support | Used to identify evaluation/form/price boundaries. |
| NSSF SPS ERP tender | Calibration fixture | Used only to test whether the extracted model can represent a real ERP tender. It is not the legal master. |

### 2.1 Official source section anchors

| Official source area | Rendered page anchor | Engine section ID | Mutability | Extraction outcome |
| --- | ---: | --- | --- | --- |
| Section III - Evaluation and Qualification Criteria | 28-36 | `IT-STD-EVAL` | `CONTROLLED_CONFIG` | Evaluation stages, scoring criteria, qualification criteria, financial evaluation rules, preference rules, and post-qualification gates. |
| Section IV - Tendering Forms | 37-48 | `IT-STD-FORMS-MAIN` | `STRUCTURED_RESPONSE_SCHEMA` | Form of Tender, Confidential Business Questionnaire, Independent Tender Determination, Self-Declaration, Fraud and Corruption appendix. |
| Price Schedule Forms | 49-54 | `IT-STD-PRICE-SCHEDULES` | `STRUCTURED_PRICE_SCHEMA` | Grand Summary, Supply and Installation Summary, Recurrent Cost Summary, Supply and Installation Sub-Table, Recurrent Cost Sub-Table, Country of Origin Code table. |
| Qualification Forms | 55-66 | `IT-STD-QUAL-FORMS` | `STRUCTURED_RESPONSE_SCHEMA` | Foreign tenderers 40% rule, ELI, JV, CON, EXP, CCC, FIN, personnel, IP, and conformance forms. |

### 2.2 NSSF calibration anchors

The NSSF ERP tender provides a practical calibration sample:

| NSSF area | Page anchor | Observed behavior | Engine implication |
| --- | ---: | --- | --- |
| Evaluation and Qualification Criteria | 10-12 | Three-stage evaluation; mandatory requirements; technical qualification; 100-point technical scoring with 75-point pass mark. | Confirms need for configurable pass/fail + scored technical model. |
| Tendering Forms | 13-16 | Simplified Form of Tender, eligibility questionnaire, independent determination, self-declaration. | Confirms real tenders may simplify forms; the engine must preserve official master forms while allowing generated tender forms according to active STD package rules. |
| Price Schedule of Requirements | 54-55 | Flat module/item price schedule with phases, quantities, unit cost, total cost, VAT, and grand total. | Confirms the engine needs a profile that can render official summary/sub-table structure while also supporting PE-configured item rows for real ERP tenders. |

---

## 3. Extraction principle for Section III and Section IV

The official IT STD treats Section III as the only permitted place for evaluation and qualification criteria. The engine must therefore enforce these principles:

| Principle | Engine behavior |
| --- | --- |
| No evaluation criteria outside the approved STD schema | Hard blocker at tender validation. |
| PE may complete or omit permitted criteria only where the STD allows | Controlled configuration with omission reason. |
| Evaluation schema must generate both tender document text and evaluator workbench configuration | Same source records must drive publication and evaluation. |
| Forms must not be treated as static PDF pages | Forms become field schemas, evidence requirements, validation rules, and render blocks. |
| Price schedules must be structured data | Supplier prices must be captured as native rows, subtotals, VAT/tax fields, recurrent cost fields, and currency fields. |
| Supplier submissions must be validated against the published STD instance | No bidder-side field can be required or evaluated unless it was published in the tender document. |

---

## 4. Evaluation model overview

### 4.1 Evaluation stages

| Stage code | Stage name | Source basis | Result | Engine behavior |
| --- | --- | --- | --- | --- |
| `EVAL-STAGE-01` | Preliminary examination for responsiveness | Section III.3 | Pass/fail | Failure blocks further evaluation. |
| `EVAL-STAGE-02` | Technical evaluation | Section III.4 | Score or pass/fail + score | Technical threshold determines progression to financial evaluation. |
| `EVAL-STAGE-03` | Financial evaluation | Section III.5 | Evaluated price | Only technically qualified tenders continue. |
| `EVAL-STAGE-04` | Preference/reservation adjustment | Section III.7 and TDS controls | Adjusted evaluated price / eligibility outcome | Applied only when enabled in TDS and lawful. |
| `EVAL-STAGE-05` | Post-qualification / confirmation | Section III.8-11 | Qualified/not qualified | Required before contract award where post-qualification applies. |
| `EVAL-STAGE-06` | Award determination | Section III.2 and award clauses | Lowest evaluated responsive tender | Generates award recommendation basis. |

### 4.2 Evaluation entity model

The following generalized records are required.

| Entity | Purpose | Applies across STD families? |
| --- | --- | --- |
| `std_evaluation_profile` | Evaluation structure for a template version | Yes |
| `std_evaluation_stage` | Stage sequence and gating behavior | Yes |
| `std_evaluation_criterion` | Criterion, subcriterion, score range, mandatory flag | Yes |
| `std_evaluation_score_band` | Allowed score ranges and thresholds | Yes |
| `std_evaluation_method` | Lowest evaluated price, QCBS-like scoring, pass/fail, formula-based, lot-based, or preference-adjusted method | Yes |
| `std_evaluation_document_requirement` | Required supporting documents per criterion | Yes |
| `std_evaluation_formula` | Computed evaluation components such as recurrent cost adjustment or preference loading | Yes |
| `std_qualification_requirement` | Post-qualification and qualification criteria | Yes |
| `std_bidder_response_binding` | Maps forms and supplier response fields to evaluation criteria | Yes |
| `tender_evaluation_instance` | Tender-specific instantiated evaluation matrix | Yes |
| `tender_evaluation_result` | Actual evaluator decisions, scores, justifications, and audit | Yes |

---

## 5. Section III evaluation extraction register

### 5.1 General provision

| Code | Source area | Extracted rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-EVAL-GEN-001` | Section III.1.1 | Monetary amounts stated by tenderers must be converted to Kenya Shilling equivalent according to exchange-rate rules. | Create `currency_conversion_rule` records tied to tender currency configuration. |
| `IT-EVAL-GEN-002` | Section III.1.1(a) | Financial data by year uses the exchange rate prevailing on the last day of the relevant calendar year. | Use date-scoped conversion for turnover/financial data. |
| `IT-EVAL-GEN-003` | Section III.1.1(b) | Value of a single contract uses the exchange rate on the contract signature date. | Use contract-date conversion for experience values. |
| `IT-EVAL-GEN-004` | Section III.1.1(c) | Exchange rates come from the publicly available source identified in the ITT/TDS. | Require TDS exchange-rate source where multi-currency evaluation is enabled. |
| `IT-EVAL-GEN-005` | Section III.1.2 | Section III contains all criteria used to evaluate and qualify tenderers; no other factors, methods, or criteria shall be used. | Hard blocker: evaluation matrix cannot contain criteria outside activated STD schema. |
| `IT-EVAL-GEN-006` | Section III.1.2 | Tenderer must provide requested information in Section IV forms. | Supplier portal must generate required form checklist from activated form schema. |

### 5.2 Multiple-contract / lot evaluation

| Code | Source option | Rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-EVAL-LOT-001` | Section III.1.3 | Multiple contracts/lots may be permitted according to TDS configuration. | Activate only if `IT-TDS-004` has lots/subsystems/slices. |
| `IT-EVAL-LOT-002` | Option 1 | Award won lots where tenderer meets eligibility and qualification criteria for each lot; if aggregate capacity is insufficient, unqualified lots move to next lowest tenderers. | Implement `LOT_BY_LOT_WITH_AGGREGATE_CAPACITY` algorithm. |
| `IT-EVAL-LOT-003` | Option 2 | Consider all possible combinations of won lots and award the combination with the lowest evaluated price where aggregate qualification is met. | Implement `LEAST_COST_COMBINATION` algorithm. |
| `IT-EVAL-LOT-004` | Cross-cutting | Lot evaluation must not be enabled unless price schedules, requirements, and award rules are all lot-aware. | Tender validation blocker if lot-aware schemas are incomplete. |

### 5.3 Award criterion

| Code | Source area | Rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-EVAL-AWARD-001` | Section III.2 | Award basis is lowest evaluated tender that meets qualification criteria and is substantially responsive. | Default award method: `LOWEST_EVALUATED_RESPONSIVE_TENDER`. |
| `IT-EVAL-AWARD-002` | Section III.2 | Technical qualification and responsiveness precede price comparison. | Financial evaluation stage locked until responsiveness/technical gates complete. |

### 5.4 Preliminary examination / responsiveness

| Code | Source area | Rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-EVAL-PRELIM-001` | Section III.3 | PE examines all tenders to ensure eligibility criteria, mandatory requirements, and completeness. | Generate mandatory checklist from TDS, Section III, and activated forms. |
| `IT-EVAL-PRELIM-002` | Section III.3 | Tenders that fail preliminary examination are non-responsive and not considered further. | Hard gate: failed tender cannot proceed to technical or financial scoring. |
| `IT-EVAL-PRELIM-003` | Section III.3 note | PE must provide preliminary evaluation criteria and documentation list. | Tender configuration must define mandatory document checklist before publication. |

### 5.5 Technical evaluation criteria

| Code | Criterion | Source points/range | Required configuration | Engine handling |
| --- | --- | ---: | --- | --- |
| `IT-TECH-001` | Specific experience of tenderer as a firm relevant to IT systems | 0-5 | Point value within range | Scored criterion; evidence from EXP forms and references. |
| `IT-TECH-002` | Adequacy and quality of methodology and work plan | 10-20 total | Subcriteria and points required | Parent criterion with subcriteria: technical approach, work plan, organization/staffing. |
| `IT-TECH-002-A` | Technical approach and methodology | PE inserts points | Point value required | Child scored criterion. |
| `IT-TECH-002-B` | Work plan | PE inserts points | Point value required | Child scored criterion. |
| `IT-TECH-002-C` | Organization and staffing | PE inserts points | Point value required | Child scored criterion. |
| `IT-TECH-003` | Conformity to Technical Specifications | 40-50 total | Subcriteria and points required | Parent criterion mapped to Part 2 requirements. |
| `IT-TECH-003-A` | Functional, architectural, and performance requirements | PE inserts points | Point value required | Map to requirements library and conformance matrix. |
| `IT-TECH-003-B` | Service specifications - supply and install items | PE inserts points | Point value required | Map to service specification items. |
| `IT-TECH-003-C` | Technology specifications - supply and install items | PE inserts points | Point value required | Map to technology specification items. |
| `IT-TECH-003-D` | Testing and quality assurance requirements | PE inserts points | Point value required | Map to testing and acceptance requirements. |
| `IT-TECH-003-E` | Service specifications - recurrent cost items | PE inserts points | Point value required | Map to recurrent service/support requirements. |
| `IT-TECH-003-F` | Implementation schedule | PE inserts points | Point value required | Map to milestone schedule. |
| `IT-TECH-003-G` | System inventory | PE inserts points | Point value required | Map to system inventory tables and price schedules. |
| `IT-TECH-004` | Supplier technical team | 20-30 total | Key positions and point values required | Parent criterion linked to personnel forms. |
| `IT-TECH-004-A` | Key position 1 - Team Leader | PE inserts points | Required unless omitted with justification | Candidate CV scoring. |
| `IT-TECH-004-B` | Key position 2 | PE inserts points | Conditional | Candidate CV scoring. |
| `IT-TECH-004-C` | Key position 3 and further key positions | PE inserts points | Conditional | Candidate CV scoring. |
| `IT-TECH-005` | Transfer of knowledge and training program | 0-5 normally | Optional; >10 requires justification/review | Parent criterion with training program subcriteria. |
| `IT-TECH-005-A` | Relevance of training program | PE inserts points | Conditional | Child scored criterion. |
| `IT-TECH-005-B` | Training approach and methodology | PE inserts points | Conditional | Child scored criterion. |
| `IT-TECH-005-C` | Qualifications of experts and trainers | PE inserts points | Conditional | Child scored criterion. |
| `IT-TECH-006` | Participation by Kenya citizens among proposed key experts | 0-5 | Optional score | Calculated ratio: Kenyan key expert time input / total key expert time input. |
| `IT-TECH-007` | Minimum technical score | 70-85 indicative | Required | Gate to financial evaluation. |

### 5.6 Technical scoring validation rules

| Rule code | Rule | Severity |
| --- | --- | --- |
| `IT-R-EVAL-001` | Total technical points must equal 100. | Blocker |
| `IT-R-EVAL-002` | Specific experience must not exceed 5 points. | Blocker |
| `IT-R-EVAL-003` | Methodology/work plan total must be between 10 and 20 points unless legal/procurement override is approved. | Blocker or override-controlled warning |
| `IT-R-EVAL-004` | Technical specification conformity total must be between 40 and 50 points unless override is approved. | Blocker or override-controlled warning |
| `IT-R-EVAL-005` | Supplier technical team total must be between 20 and 30 points unless override is approved. | Blocker or override-controlled warning |
| `IT-R-EVAL-006` | Training/knowledge transfer should normally not exceed 5 points; if greater than 10, require justification and approval. | Warning / approval required |
| `IT-R-EVAL-007` | Kenya citizen participation must not exceed 5 points. | Blocker |
| `IT-R-EVAL-008` | Minimum technical pass score must be set before publication. | Blocker |
| `IT-R-EVAL-009` | Minimum technical pass score should fall within 70-85 unless approved. | Warning / approval required |
| `IT-R-EVAL-010` | Every scored criterion must define scoring guide, evidence source, evaluator role, and maximum points. | Blocker |
| `IT-R-EVAL-011` | Every technical criterion that references Part 2 requirements must be traceable to requirement IDs. | Blocker |

### 5.7 Financial evaluation extraction

| Code | Source area | Rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-FIN-EVAL-001` | Section III.5 | Tenderers below technical pass mark are automatically disqualified. | Financial stage only visible for technically qualified tenderers. |
| `IT-FIN-EVAL-002` | Time schedule | No credit for earlier completion; tenders beyond maximum completion period are rejected. | Completion-period validation with rejection threshold. |
| `IT-FIN-EVAL-003` | Alternative technical solutions | Alternative solutions are evaluated only if permitted under TDS and official alternative rules. | Activate alternative evaluation workflow only when enabled. |
| `IT-FIN-EVAL-004` | Other specific additional criteria | Additional criteria allowed only if permitted under the relevant ITT/TDS control. | Prevent arbitrary additional financial criteria. |
| `IT-FIN-EVAL-005` | Recurrent costs | Recurrent costs form part of evaluation where operation and maintenance are material. | Compute evaluated price by adding recurrent costs for configured evaluation period. |
| `IT-FIN-EVAL-006` | Recurrent cost factors | Factors may include hardware maintenance, software licenses and updates, technical services, telecommunication services, and other services. | Recurrent cost item types and formula lines. |
| `IT-FIN-EVAL-007` | Post-warranty recurrent costs | If subject to evaluation, post-warranty service period recurrent costs are included in the main contract or a separate contract signed together with the main contract. | Contract-generation dependency: recurrent service contract or main contract schedule. |

### 5.8 Preference and reservation extraction

| Code | Source area | Rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-PREF-001` | Section III.7.1 | If TDS specifies, a 15% preference margin is loaded on evaluated prices of foreign tenderers where Kenyan citizen shareholding is below 51%. | Formula: `foreign_adjusted_price = evaluated_price * 1.15` for Group B when enabled. |
| `IT-PREF-002` | Section III.7.2 | Tenderers must provide ownership information to determine preference qualification. | Evidence requirement bound to ELI/ownership fields. |
| `IT-PREF-003` | Section III.7.3 | Responsive tenders are classified into Group A and Group B. | Evaluation grouping required before preference formula. |
| `IT-PREF-004` | Section III.7.4 | If Group A is lowest before preference, select Group A; if Group B is lowest, apply preference loading to Group B and compare again. | Implement `PREFERENCE_MARGIN_RECALCULATION` algorithm. |

### 5.9 Post-qualification extraction

| Code | Source area | Rule | Engine implementation |
| --- | --- | --- | --- |
| `IT-POSTQUAL-001` | Section III.8(a) | If prequalification was used, award is subject to confirmation/update of prequalification data. | Require prequalification data confirmation before award recommendation. |
| `IT-POSTQUAL-002` | Section III.8(b) | If not prequalified, lowest evaluated tenderer must meet post-qualification conditions. | Postqualification checklist mandatory before award. |
| `IT-POSTQUAL-003` | Financial resources | Tenderer must demonstrate sufficient liquid assets, unencumbered real assets, lines of credit, or other means. | FIN resource requirement; value configured by PE. |
| `IT-POSTQUAL-004` | Average annual turnover | Minimum average annual turnover amount and period must be configured. | FIN turnover requirement; amount and years configured. |
| `IT-POSTQUAL-005` | Similar contract experience | Number, geography, similarity, completion, and minimum value of similar contracts must be configured. | EXP specific-experience requirement. |
| `IT-POSTQUAL-006` | Contractor/Supplier representative and key personnel | Key personnel positions must be specified. | Personnel schema. |
| `IT-POSTQUAL-007` | Key equipment / resources | Major equipment or resources may be specified where relevant. | Resource/equipment schema; likely optional for pure software. |
| `IT-POSTQUAL-008` | Non-performing contracts | Non-performance history must be reviewed for configured period. | CON form binding. |
| `IT-POSTQUAL-009` | Pending litigation | Financial position must remain sound assuming pending litigation is resolved against tenderer. | CON + FIN binding. |
| `IT-POSTQUAL-010` | Litigation history | Consistent history of adverse awards may lead to rejection. | CON form binding; evaluator justification required. |

### 5.10 Official-source review flags in Section III

| Flag code | Issue | Treatment |
| --- | --- | --- |
| `IT-REVIEW-EVAL-001` | Some language appears inherited from works templates, including phrases such as construction turnover/cash flow or contractor/equipment references. | Preserve official source text but normalize engine labels as IT supplier/service-provider where safe. Legal/procurement review required before rendered wording is altered. |
| `IT-REVIEW-EVAL-002` | Section references contain minor numbering/wording inconsistencies. | Preserve source anchors and add normalized internal references. |
| `IT-REVIEW-EVAL-003` | Alternative tenders and additional financial criteria are permitted only through TDS controls. | Engine must block free-form alternatives unless TDS activates them. |
| `IT-REVIEW-EVAL-004` | Margin of preference formula depends on ownership data and tenderer classification. | Supplier eligibility forms must capture ownership details sufficient for evaluation. |

---

## 6. Qualification requirement register

| Code | Subject | Requirement source | Data required | Form binding | Engine behavior |
| --- | --- | --- | --- | --- | --- |
| `IT-QUAL-001` | Nationality | ITT eligibility | Tenderer nationality / registration country | `FORM-ELI-1`, `FORM-ELI-JV` | Eligibility check. |
| `IT-QUAL-002` | Kenyan tax obligations | ITT eligibility | Current tax clearance or exemption certificate | Form of Tender / evidence upload | Mandatory for Kenyan tenderers. |
| `IT-QUAL-003` | Conflict of interest | ITT 4.3 | Declaration and related-party information | Form of Tender / CBQ | Pass/fail. |
| `IT-QUAL-004` | Country ineligibility | ITT eligibility | Country of origin and sanctions eligibility | Form of Tender / price country codes | Pass/fail. |
| `IT-QUAL-005` | State-owned entity conditions | ITT state-owned entity rule | Legal/financial autonomy, commercial-law operation, no supervision by PE | `FORM-ELI-1` attachments | Conditional pass/fail. |
| `IT-QUAL-006` | UN resolution / Kenya law prohibition | ITT eligibility | Declaration | Form of Tender | Pass/fail. |
| `IT-QUAL-007` | History of non-performing contracts | Section III.8 and Qualification Form | Non-performance occurrence since configured date | `FORM-CON-1` | Postqualification risk check. |
| `IT-QUAL-008` | Suspension | Tender-securing declaration/debarment | Suspension status | Form of Tender | Pass/fail. |
| `IT-QUAL-009` | Pending litigation | Section III | Pending disputes and financial effect | `FORM-CON-1`, FIN forms | Evaluator must assess financial soundness. |
| `IT-QUAL-010` | Historical financial performance | Section III | Audited statements or equivalent for configured years | `FORM-FIN-1` | Pass/fail / review. |
| `IT-QUAL-011` | Average annual turnover | Section III | Certified payments / turnover over configured period | `FORM-FIN-2` | Numeric threshold. |
| `IT-QUAL-012` | Financial resources | Section III | Liquid assets, credit lines, other financial means | `FORM-FIN-3` | Numeric threshold. |
| `IT-QUAL-013` | General experience | Section III | Years under IT system contracts | `FORM-EXP-1` | Numeric threshold. |
| `IT-QUAL-014` | Specific experience | Section III | Number/value/similarity of completed IT system contracts | `FORM-EXP-2` | Numeric + qualitative threshold. |
| `IT-QUAL-015` | Personnel | Section III.10 | Key positions, CVs, experience | `FORM-PERSONNEL` | Technical/team scoring and postqualification. |
| `IT-QUAL-016` | Subcontractors/vendors/manufacturers | Section III.11 | Major items and minimum criteria | Subcontractor/manufacturer authorization forms | Conditional pass/fail. |
| `IT-QUAL-017` | Foreign tenderers 40% rule | Qualification Forms | Local labor, subcontract, materials, plant/equipment, local-content cost | `FORM-LOCAL-CONTENT-40` | Required for foreign tenderers where activated. |

---

## 7. Tendering forms extraction register

### 7.1 Form catalog

| Form code | Official form | Section anchor | Respondent | Purpose | Engine type |
| --- | --- | ---: | --- | --- | --- |
| `IT-FORM-001` | Form of Tender | 37-39 | Tenderer | Tender offer, price, validity, declarations, discounts, binding commitments, beneficial ownership commitment | `BIDDER_SUBMISSION_FORM` |
| `IT-FORM-002` | Tenderer's Eligibility - Confidential Business Questionnaire | 40-42 | Tenderer | Legal identity, ownership, business details, eligibility disclosures | `BIDDER_ELIGIBILITY_FORM` |
| `IT-FORM-003` | Certificate of Independent Tender Determination | 43 | Tenderer | Anti-collusion declaration | `DECLARATION_FORM` |
| `IT-FORM-004` | Self-Declaration Form | 44-46 | Tenderer | Debarment, corruption, fraudulent/collusive/coercive/obstructive practice declaration | `DECLARATION_FORM` |
| `IT-FORM-005` | Appendix 1 - Fraud and Corruption | 47-48 | Tenderer / information | Definitions and anti-corruption obligations | `LEGAL_APPENDIX` |
| `IT-FORM-006` | Grand Summary Cost Table | 50 | Tenderer | Summarizes supply/install and recurrent cost totals | `PRICE_FORM` |
| `IT-FORM-007` | Supply and Installation Cost Summary Table | 50 | Tenderer | Summarizes supply/install cost sub-tables by subsystem/item | `PRICE_FORM` |
| `IT-FORM-008` | Recurrent Cost Summary Table | 51 | Tenderer | Summarizes recurrent cost sub-tables | `PRICE_FORM` |
| `IT-FORM-009` | Supply and Installation Cost Sub-Table | 52 | Tenderer | Detailed component pricing by origin/currency | `PRICE_FORM` |
| `IT-FORM-010` | Recurrent Cost Sub-Table | 53 | Tenderer | Detailed recurrent cost pricing, warranty/post-warranty where applicable | `PRICE_FORM` |
| `IT-FORM-011` | Country of Origin Code Table | 54 | Tenderer | Country of origin coding for priced items | `PRICE_FORM_REFERENCE` |
| `IT-FORM-012` | Foreign Tenderers 40% Rule | 55 | Foreign tenderer | Local-content demonstration | `QUALIFICATION_FORM` |
| `IT-FORM-013` | Form ELI-1 Tenderer Information Form | 56 | Tenderer | Tenderer legal identity and attachments | `QUALIFICATION_FORM` |
| `IT-FORM-014` | Form ELI-1 Tenderer's JV Members Information Form | 57 | JV member | JV member identity and attachments | `QUALIFICATION_FORM` |
| `IT-FORM-015` | Form CON-1 Historical Contract Non-Performance and Pending Litigation | 58 | Tenderer / JV member | Non-performance, pending litigation, litigation history | `QUALIFICATION_FORM` |
| `IT-FORM-016` | Form EXP-1 Experience - General Experience | 59 | Tenderer | General IT system contract experience | `QUALIFICATION_FORM` |
| `IT-FORM-017` | Form EXP-2 Specific Experience | 60 | Tenderer | Similar contract experience | `QUALIFICATION_FORM` |
| `IT-FORM-018` | Form EXP-2 cont. Specific Experience | 60 | Tenderer | Additional detail for specific experience | `QUALIFICATION_FORM` |
| `IT-FORM-019` | Form CCC-1 Current Contract Commitments / Work in Progress | 61 | Tenderer | Current commitments and workload | `QUALIFICATION_FORM` |
| `IT-FORM-020` | Form FIN-1 Financial Situation | 61 | Tenderer | Financial statements and financial health | `QUALIFICATION_FORM` |
| `IT-FORM-021` | Form FIN-2 Average Annual Turnover | 62 | Tenderer | Turnover computation | `QUALIFICATION_FORM` |
| `IT-FORM-022` | Form F-3 Financial Resources | 62 | Tenderer | Liquid assets, credit lines, other resources | `QUALIFICATION_FORM` |
| `IT-FORM-023` | Personnel Capabilities | 62 | Tenderer | Key personnel details | `TECHNICAL_FORM` |
| `IT-FORM-024` | Intellectual Property Forms | 63-65 | Tenderer | Software categories, custom materials, licenses, ownership/rights | `TECHNICAL_LEGAL_FORM` |
| `IT-FORM-025` | Conformance of Information System Materials | 66-70 | Tenderer | Requirement-by-requirement conformance response | `TECHNICAL_CONFORMANCE_FORM` |

### 7.2 Form object standard

Every form must be stored with this generalized structure:

```json
{
  "form_code": "IT-FORM-001",
  "template_family_code": "KE-PPRA-IT",
  "template_version_code": "KE-PPRA-IT-2022-04",
  "section_id": "IT-STD-FORMS-MAIN",
  "title": "Form of Tender",
  "form_type": "BIDDER_SUBMISSION_FORM",
  "respondent_type": "TENDERER",
  "activation_rule_code": "IT-R-FORM-001",
  "source_anchor_id": "SRC-KE-PPRA-IT-2022-04-FORM-OF-TENDER",
  "render_block_code": "R-FORM-OF-TENDER",
  "is_locked_text": false,
  "is_structured_schema": true,
  "requires_signature": true,
  "requires_attachments": true,
  "downstream_bindings": ["EVALUATION", "CONTRACT_FORMATION", "AUDIT"]
}
```

### 7.3 Form field categories

| Category | Examples | Engine behavior |
| --- | --- | --- |
| Identity fields | Tenderer legal name, country, registration year, address, authorized representative | Standardized across all STDs. |
| Tender reference fields | Tender name, ITT number, alternative number, lot number | Auto-filled where possible from tender instance. |
| Price fields | Total tender price, discounts, line-item prices, currencies, VAT/taxes | Native numeric/currency fields with formula validation. |
| Declarations | Eligibility, no conflict, anti-collusion, suspension/debarment, state-owned entity status | Must be signed; pass/fail evaluation binding. |
| Evidence attachments | Incorporation documents, JV agreement, tax evidence, audited statements, authorizations | Upload requirements with file metadata and reviewer status. |
| Experience records | Contract name, value, date, PE/client, role, completion status, similarity | Evaluation and qualification binding. |
| Financial records | Balance sheets, turnover, credit lines, liquid assets | Qualification thresholds and litigation stress test. |
| Technical proposal records | Methodology, work plan, organization/staffing, conformance responses | Technical scoring binding. |
| Personnel records | CVs, role, general qualifications, relevant experience, local experience | Personnel scoring binding. |
| IP/software records | Software categories, custom materials, licensing rights | Contract/IP clauses and appendices. |

---

## 8. Form-level schema extraction

### 8.1 Form of Tender schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `FOT-001` | Tender submission date | Date | Yes | Audit and validity. |
| `FOT-002` | Tender name and identification | Text / tender ref | Yes | Tender instance identity. |
| `FOT-003` | Alternative number | Text | Conditional | Required if alternative tender submitted. |
| `FOT-004` | Procuring Entity addressee | Entity / text | Yes | Render from PE profile. |
| `FOT-005` | No reservations declaration | Boolean declaration | Yes | Responsiveness. |
| `FOT-006` | Eligibility declaration | Boolean declaration | Yes | Eligibility gate. |
| `FOT-007` | Tender-securing declaration / debarment declaration | Boolean declaration | Conditional | Activated by TDS security model. |
| `FOT-008` | Description of IT design, supply and installation services offered | Long text | Yes | Technical proposal summary. |
| `FOT-009` | Total tender price - single lot | Money/multi-currency | Conditional | Price evaluation. |
| `FOT-010` | Lot prices | Structured list | Conditional | Lot evaluation. |
| `FOT-011` | Discounts offered | Structured list | Optional | Financial evaluation if unconditional/allowed. |
| `FOT-012` | Discount calculation method | Formula/text | Conditional | Required if discount offered. |
| `FOT-013` | Tender validity declaration | Duration/date | Yes | Must match TDS validity. |
| `FOT-014` | Performance security commitment | Boolean declaration | Yes | Contract award readiness. |
| `FOT-015` | One tender per tenderer declaration | Boolean declaration | Yes | Eligibility gate. |
| `FOT-016` | Suspension/debarment declaration | Boolean declaration | Yes | Eligibility gate. |
| `FOT-017` | State-owned enterprise/institution status | Enum | Yes | Conditional evidence. |
| `FOT-018` | Commissions/gratuities/fees table | Structured list | Yes | Audit/anti-corruption. |
| `FOT-019` | Binding contract acknowledgement | Boolean declaration | Yes | Legal commitment. |
| `FOT-020` | Not bound to accept acknowledgement | Boolean declaration | Yes | Legal acknowledgement. |
| `FOT-021` | Beneficial ownership disclosure undertaking | Boolean declaration | Yes | Contract publication/award compliance. |
| `FOT-022` | Signature block | Signature | Yes | Submission validity. |

### 8.2 Confidential Business Questionnaire schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `CBQ-001` | Full legal name | Text | Yes | Tenderer identity. |
| `CBQ-002` | Business registration/incorporation number | Text | Yes | Eligibility. |
| `CBQ-003` | Country of incorporation/registration | Country | Yes | Nationality/preference. |
| `CBQ-004` | Year of establishment | Year | Yes | General experience check. |
| `CBQ-005` | Registered office address | Address | Yes | Eligibility/contact. |
| `CBQ-006` | Local/Kenya office address | Address | Conditional | Local presence criteria where used. |
| `CBQ-007` | Contact person and contact details | Person/contact | Yes | Notices. |
| `CBQ-008` | KRA PIN / tax registration | Text | Conditional | Kenyan tenderers. |
| `CBQ-009` | Ownership / shareholding information | Structured ownership table | Conditional | Preference, conflict, beneficial ownership. |
| `CBQ-010` | Directors/partners/proprietors | Structured list | Conditional | Conflict and beneficial ownership. |
| `CBQ-011` | Pending litigation indicator/details | Boolean + details | Yes | Qualification. |
| `CBQ-012` | Relationships/conflict disclosures | Structured declaration | Yes | Conflict checks. |

### 8.3 Certificate of Independent Tender Determination schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `CITD-001` | Declaration that prices were determined independently | Boolean declaration | Yes | Anti-collusion gate. |
| `CITD-002` | Declaration of no disclosure of quoted prices before award | Boolean declaration | Yes | Anti-collusion gate. |
| `CITD-003` | Declaration of no attempt to induce another tenderer | Boolean declaration | Yes | Anti-collusion gate. |
| `CITD-004` | Authority to sign on behalf of corporation | Boolean declaration | Yes | Validity. |
| `CITD-005` | Signature block | Signature | Yes | Submission validity. |

### 8.4 Self-declaration schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `SELF-001` | Declaration of no fraudulent practice | Boolean declaration | Yes | Eligibility/responsiveness. |
| `SELF-002` | Declaration of no corrupt practice | Boolean declaration | Yes | Eligibility/responsiveness. |
| `SELF-003` | Declaration of no coercive practice | Boolean declaration | Yes | Eligibility/responsiveness. |
| `SELF-004` | Declaration of no collusive practice | Boolean declaration | Yes | Eligibility/responsiveness. |
| `SELF-005` | Declaration of no obstructive practice | Boolean declaration | Yes | Eligibility/responsiveness. |
| `SELF-006` | Declaration of not being debarred by PPRA | Boolean declaration | Yes | Eligibility/responsiveness. |
| `SELF-007` | Signature block | Signature | Yes | Submission validity. |

### 8.5 Foreign tenderers 40% rule schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `LC40-001` | Local labor items | Structured cost rows | Conditional | Required for foreign tenderers where rule active. |
| `LC40-002` | Local subcontract items | Structured cost rows | Conditional | Local content calculation. |
| `LC40-003` | Local material items | Structured cost rows | Conditional | Local content calculation. |
| `LC40-004` | Local plant/equipment items | Structured cost rows | Conditional | Local content calculation. |
| `LC40-005` | Other local content items | Structured cost rows | Optional | Local content calculation. |
| `LC40-006` | Total local content cost | Money | Computed | Numerator for percentage. |
| `LC40-007` | Percentage of contract price | Percentage | Computed | Must meet configured threshold. |

---

## 9. Qualification form schemas

### 9.1 ELI forms

| Form | Field group | Required fields | Binding |
| --- | --- | --- | --- |
| `FORM-ELI-1` | Tenderer identity | Legal name, JV members, country/year of registration, address, authorized representative, documents attached | Nationality, SOE, JV, registration, ownership. |
| `FORM-ELI-JV` | JV member identity | JV member name, country/year of registration, address, representative, attachments | JV eligibility and joint/several liability review. |

### 9.2 CON form

| Field group | Required fields | Binding |
| --- | --- | --- |
| Non-performing contracts | Occurrence flag, year, non-performed portion, contract ID, PE/client, reason, amount | Non-performance qualification check. |
| Pending litigation | Dispute year, amount, contract ID, PE/client, matter, initiating party, status | Financial soundness stress test. |
| Litigation history | Award/case details, year, amount, outcome | Rejection risk if consistent adverse history. |

### 9.3 EXP forms

| Form | Field group | Required fields | Binding |
| --- | --- | --- | --- |
| `FORM-EXP-1` | General experience | Start/end dates, contract type, role, client, value, country | Minimum years of IT system contract experience. |
| `FORM-EXP-2` | Specific experience | Similar contract description, scope, value, completion, role, technology, complexity, client contact | Similar-contract threshold and technical scoring. |

### 9.4 Financial forms

| Form | Required fields | Binding |
| --- | --- | --- |
| `FORM-FIN-1` | Audited balance sheets/financial statements, current soundness indicators, profitability notes | Historical financial performance. |
| `FORM-FIN-2` | Annual turnover by year, currency, exchange rate, KES equivalent, average | Average annual turnover threshold. |
| `FORM-FIN-3` | Liquid assets, credit lines, unencumbered assets, other resources, evidence | Financial resources / cash-flow threshold. |

### 9.5 Personnel capabilities schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `PER-001` | Position code | Text | Yes | Evaluation criterion. |
| `PER-002` | Proposed person name | Text | Yes | CV record. |
| `PER-003` | General qualifications | Long text / attachment | Yes | Scoring subcriterion. |
| `PER-004` | Relevant qualifications and certifications | Structured list | Conditional | Role-specific requirements. |
| `PER-005` | Relevant IT system experience | Structured experience rows | Yes | Scoring subcriterion. |
| `PER-006` | Kenya/local experience | Structured experience rows | Optional | Local experience/citizen participation criteria. |
| `PER-007` | Time input | Person-months / percentage | Conditional | Kenya citizen participation ratio. |
| `PER-008` | CV attachment | File | Yes | Evidence. |

### 9.6 Intellectual property forms schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `IP-001` | Software category | Enum | Yes | Contract appendices and license clauses. |
| `IP-002` | Standard software item | Structured row | Conditional | License appendix. |
| `IP-003` | Custom software/material item | Structured row | Conditional | Ownership/transfer clauses. |
| `IP-004` | Third-party software item | Structured row | Conditional | Third-party license obligations. |
| `IP-005` | License model | Enum/text | Conditional | Contract/SCC IP terms. |
| `IP-006` | Source code / escrow / transfer statement | Text / declaration | Conditional | Custom material treatment. |
| `IP-007` | Restrictions on PE use | Text | Conditional | Legal review. |
| `IP-008` | Warranty of IP rights | Declaration | Yes | IPR warranty and indemnity. |

### 9.7 Conformance of Information System Materials schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `CONF-001` | Requirement ID | Requirement reference | Yes | Links to Part 2 requirement. |
| `CONF-002` | Requirement description | Locked text / generated | Yes | From PE requirement composer. |
| `CONF-003` | Tenderer conformance status | Enum | Yes | Values: `COMPLY`, `PARTIALLY_COMPLY`, `DO_NOT_COMPLY`, `ALTERNATIVE`, where alternatives allowed. |
| `CONF-004` | Tenderer response/commentary | Long text | Yes | Technical evaluation. |
| `CONF-005` | Reference page/document | Text / file reference | Conditional | Evidence navigation. |
| `CONF-006` | Supporting attachment | File | Optional/conditional | Technical evidence. |
| `CONF-007` | Evaluator determination | Enum | Evaluation stage | Meets/does not meet/clarification. |
| `CONF-008` | Evaluator notes | Long text | Evaluation stage | Audit. |

---

## 10. Price schedule extraction

### 10.1 Official price schedule structure

The official IT STD price schedules are not a single flat BoQ. They are a linked set of summary and sub-table structures:

| Official price schedule | Engine schema | Purpose |
| --- | --- | --- |
| Grand Summary Cost Table | `price_grand_summary` | Rolls up supply/install and recurrent cost totals into tender submission amount. |
| Supply and Installation Cost Summary Table | `price_supply_install_summary` | Summarizes supply/install cost sub-tables by subsystem/item. |
| Recurrent Cost Summary Table | `price_recurrent_summary` | Summarizes recurrent cost sub-tables. |
| Supply and Installation Cost Sub-Table | `price_supply_install_line` | Captures itemized local/foreign supplied components, quantities, unit rates, and totals. |
| Recurrent Cost Sub-Table | `price_recurrent_line` | Captures warranty/post-warranty recurrent costs such as support, licenses, updates, maintenance, telecom services. |
| Country of Origin Code Table | `price_country_origin_code` | Maps country code references used in cost sub-tables. |

### 10.2 General pricing rules

| Rule code | Rule | Engine behavior |
| --- | --- | --- |
| `IT-R-PRICE-001` | Price schedules must be completed using structured rows. | Supplier cannot submit only a PDF/Excel without row capture unless importer maps it to rows. |
| `IT-R-PRICE-002` | Quoted rates and prices cover full scope of technical requirements, overhead, and profit. | Render official note; do not separately score unpriced scope unless tender states treatment. |
| `IT-R-PRICE-003` | Unclear scope must be clarified before tender submission. | Clarification period workflow. |
| `IT-R-PRICE-004` | Prices must be entered in indelible/unaltered manner in paper context; digital equivalent is locked submission after deadline. | Supplier submission locks at deadline. |
| `IT-R-PRICE-005` | Price adjustment depends on TDS configuration. | If fixed prices, block price-adjustment formulas. |
| `IT-R-PRICE-006` | Price currencies must match ITT/TDS currency controls. | Block unsupported currency entries. |
| `IT-R-PRICE-007` | Arithmetic errors are corrected under ITT correction rules. | Evaluation arithmetic-correction workflow with audit. |
| `IT-R-PRICE-008` | No more than the permitted number of foreign currencies may be used where foreign currency is allowed. | Currency count validation. |
| `IT-R-PRICE-009` | Grand summary total must equal sum of supply/install and recurrent summaries. | Computed-field validation. |
| `IT-R-PRICE-010` | Form of Tender total must equal Grand Summary total after allowed discounts/tax treatment. | Cross-form validation. |

### 10.3 Grand Summary Cost Table schema

| Field code | Field | Type | Required | Formula/binding |
| --- | --- | --- | --- | --- |
| `PGS-001` | Tenderer name | Text | Yes | Supplier profile. |
| `PGS-002` | Currency columns | Currency set | Yes | From TDS currency rules. |
| `PGS-003` | Supply and installation total | Money by currency | Computed | From Supply and Installation Cost Summary. |
| `PGS-004` | Recurrent cost total | Money by currency | Computed | From Recurrent Cost Summary. |
| `PGS-005` | Grand total | Money by currency | Computed | `PGS-003 + PGS-004`. |
| `PGS-006` | Authorized signature | Signature | Yes | Submission validity. |

### 10.4 Supply and Installation Cost Summary schema

| Field code | Field | Type | Required | Formula/binding |
| --- | --- | --- | --- | --- |
| `SIS-001` | Line item number | Sequence | Yes | Links to sub-table. |
| `SIS-002` | Subsystem/item name | Text / requirement ref | Yes | From system inventory / PE requirements. |
| `SIS-003` | Supply/install cost sub-table number | Text/ref | Yes | Links to `price_supply_install_line`. |
| `SIS-004` | Local currency price | Money | Conditional | Required if local supply/cost exists. |
| `SIS-005` | Foreign currency A price | Money | Conditional | Required if foreign currency A used. |
| `SIS-006` | Foreign currency B price | Money | Conditional | Required if foreign currency B used. |
| `SIS-007` | Subtotal | Money | Computed | Sum of sub-table totals. |
| `SIS-008` | Total to grand summary | Money | Computed | Rolls up to `PGS-003`. |

### 10.5 Recurrent Cost Summary schema

| Field code | Field | Type | Required | Formula/binding |
| --- | --- | --- | --- | --- |
| `RCS-001` | Line item number | Sequence | Yes | Links to recurrent sub-table. |
| `RCS-002` | Subsystem/item name | Text / requirement ref | Yes | From recurrent service/support requirements. |
| `RCS-003` | Recurrent cost sub-table number | Text/ref | Yes | Links to recurrent line table. |
| `RCS-004` | Local currency recurrent price | Money | Conditional | Required for local recurrent cost. |
| `RCS-005` | Foreign currency A recurrent price | Money | Conditional | Required if used. |
| `RCS-006` | Foreign currency B recurrent price | Money | Conditional | Required if used. |
| `RCS-007` | Recurrent subtotal | Money | Computed | Sum of recurrent sub-table totals. |
| `RCS-008` | Total to grand summary | Money | Computed | Rolls up to `PGS-004`. |

### 10.6 Supply and Installation Cost Sub-Table schema

| Field code | Field | Type | Required | Formula/binding |
| --- | --- | --- | --- | --- |
| `SIL-001` | Parent line item number | Ref | Yes | Must match summary line. |
| `SIL-002` | Component number | Sequence | Yes | Unique within sub-table. |
| `SIL-003` | Component description | Text | Yes | From system inventory / bidder breakdown. |
| `SIL-004` | Country of origin code | Country code | Conditional | Required for supplied components. |
| `SIL-005` | Quantity | Decimal | Yes | From PE inventory or tenderer where allowed. |
| `SIL-006` | Unit price supplied locally | Money | Conditional | Local component price. |
| `SIL-007` | Unit price supplied from outside Kenya - local currency | Money | Conditional | Import/local currency. |
| `SIL-008` | Unit price foreign currency A | Money | Conditional | Foreign currency A. |
| `SIL-009` | Unit price foreign currency B | Money | Conditional | Foreign currency B. |
| `SIL-010` | Total price supplied locally | Money | Computed | `quantity * local unit price`. |
| `SIL-011` | Total price supplied from outside Kenya | Money | Computed | `quantity * applicable foreign/import unit price`. |
| `SIL-012` | Subtotal to summary | Money | Computed | Rolls up to summary line. |

### 10.7 Recurrent Cost Sub-Table schema

| Field code | Field | Type | Required | Formula/binding |
| --- | --- | --- | --- | --- |
| `RCL-001` | Parent recurrent line item number | Ref | Yes | Must match recurrent summary line. |
| `RCL-002` | Recurrent cost type | Enum | Yes | Hardware maintenance, software licenses/updates, technical services, telecom services, other. |
| `RCL-003` | Warranty/post-warranty period | Enum/date range | Yes | Warranty, year 1, year 2, year N, post-warranty, etc. |
| `RCL-004` | Component/service description | Text | Yes | From recurrent requirements. |
| `RCL-005` | Quantity / unit basis | Decimal/text | Conditional | Users, devices, month, GB/month, annual, lump sum, etc. |
| `RCL-006` | Unit rate | Money | Conditional | Required unless lump sum. |
| `RCL-007` | Period multiplier | Decimal | Conditional | Months/years used in evaluation. |
| `RCL-008` | Total recurrent cost | Money | Computed | Rate * quantity * period or lump sum. |
| `RCL-009` | Included in evaluated price | Boolean | Yes | Controlled by Section III/TDS recurrent cost rules. |
| `RCL-010` | Included in contract price | Boolean | Yes | Controls contract appendices. |

### 10.8 Country of Origin Code schema

| Field code | Field | Type | Required | Binding |
| --- | --- | --- | --- | --- |
| `COO-001` | Country code | Text / ISO | Yes | Used in price sub-tables. |
| `COO-002` | Country name | Country | Yes | Eligibility and origin checks. |
| `COO-003` | Eligible origin flag | Boolean | Computed/validated | Blocker if country is ineligible. |
| `COO-004` | Notes | Text | Optional | Audit/support. |

---

## 11. NSSF ERP calibration findings

The NSSF ERP tender shows how a real PE has simplified or specialized the official IT STD structure. The engine should support these cases, but it must not treat the NSSF structure as the legal master.

### 11.1 Evaluation calibration

| NSSF observation | Engine interpretation | Risk/control |
| --- | --- | --- |
| Evaluation has three stages: preliminary, technical, financial. | Directly maps to official evaluation stages. | Good calibration. |
| Mandatory requirements include incorporation, tax compliance, NSSF compliance, CR12, professional indemnity, signed forms, independent tender determination, self-declaration, and Microsoft authorization. | Maps to preliminary checklist and evidence requirements. | Product/vendor-specific Microsoft requirement should require justification and legal/procurement review to avoid improper restriction unless the procurement is intentionally for a Microsoft Dynamics platform. |
| Technical qualification includes minimum five years ERP experience, three D365 Business Central implementations, pension/RBA-sector experience, post-go-live support experience, KES 50M turnover, key staff, and local presence. | Maps to qualification criteria and evidence requirements. | Sector/platform specificity must be traceable to PE requirements and procurement plan. |
| Technical scoring totals 100 points with 75-point pass mark. | Maps cleanly to the official 100-point model and pass-score configuration. | Pass mark of 75 sits within the official indicative 70-85 range. |
| Scoring criteria include company experience 20, solution proposal 25, implementation methodology 15, key personnel 15, support plan 10, data migration/integration 10, training 5. | Fits generalized scored criteria but differs from official suggested range distribution. | Engine should warn if official criterion range boundaries are exceeded or criterion labels drift too far from official model. |

### 11.2 Price schedule calibration

| NSSF observation | Engine interpretation | Risk/control |
| --- | --- | --- |
| NSSF uses a flat module/item price schedule instead of the official Grand Summary + supply/install + recurrent sub-table structure. | Treat as PE-specific simplified `price_schedule_profile = FLAT_ITEM_PHASED`. | Legal/procurement review needed to confirm simplification is acceptable under active STD. |
| Price rows include module/item, phase, users/quantity, unit cost, total cost. | Good fit for `price_line_item` records with phase and quantity basis. | Must still roll up to official grand total and Form of Tender totals. |
| Cloud infrastructure is priced per month / per GB-month, while annual maintenance and license renewal are annual. | Confirms need for unit-basis and recurrent period fields. | Recurrent costs must be included or excluded from evaluated price according to published rules. |
| VAT and grand total are separately stated. | Engine should support tax breakdown and grand-total computation. | VAT/tax treatment must match TDS/invitation/SCC. |

### 11.3 Form calibration

| NSSF observation | Engine interpretation | Risk/control |
| --- | --- | --- |
| NSSF includes simplified Form of Tender and selected declaration forms. | Engine can generate simplified form variants only if the active STD package permits them. | Avoid losing official form obligations such as discounts, commissions/gratuities, lot pricing, beneficial ownership, and complete declarations. |
| NSSF includes Microsoft partner designation in business questionnaire/eligibility. | Treat as tender-specific evidence criterion, not a template-level field. | Requires review for brand-specific restriction. |

---

## 12. Seed package updates required by Pass 3

The package skeleton should be updated with the following new or expanded module files.

### 12.1 Evaluation modules

| File | Required status | Contents |
| --- | --- | --- |
| `evaluation/profile.json` | Required | Evaluation profile metadata, stages, award method, pass thresholds. |
| `evaluation/stages.json` | Required | Preliminary, technical, financial, preference, postqualification, award stages. |
| `evaluation/criteria.json` | Required | Technical criteria and subcriteria with ranges and point values. |
| `evaluation/qualification_requirements.json` | Required | Qualification matrix, thresholds, form bindings. |
| `evaluation/form_bindings.json` | Required | Mapping from forms/fields to criteria. |
| `evaluation/financial_evaluation_rules.json` | Required | Price, currency, recurrent cost, alternative, and time-schedule rules. |
| `evaluation/preference_rules.json` | Conditional | Margin of preference group classification and formula. |
| `evaluation/lot_evaluation_rules.json` | Conditional | Option 1/Option 2 lot-combination logic. |

### 12.2 Form modules

| File | Required status | Contents |
| --- | --- | --- |
| `forms/form_catalog.json` | Required | All forms listed in this pass. |
| `forms/form_fields.json` | Required | Field dictionary for forms. |
| `forms/form_validation_rules.json` | Required | Required fields, conditional fields, signature rules. |
| `forms/evidence_requirements.json` | Required | Attachments and evidence requirements. |
| `forms/declaration_forms.json` | Required | Anti-collusion, self-declaration, conflict, debarment declarations. |
| `forms/qualification_forms.json` | Required | ELI, JV, CON, EXP, FIN, personnel, IP, conformance forms. |

### 12.3 Price modules

| File | Required status | Contents |
| --- | --- | --- |
| `pricing/price_schedule_profile.json` | Required | Official price schedule profile. |
| `pricing/grand_summary_schema.json` | Required | Grand summary fields and formulas. |
| `pricing/supply_install_summary_schema.json` | Required | Supply/install summary structure. |
| `pricing/supply_install_subtable_schema.json` | Required | Component-level supply/install pricing. |
| `pricing/recurrent_summary_schema.json` | Required | Recurrent cost summary. |
| `pricing/recurrent_subtable_schema.json` | Required | Recurrent item, warranty/post-warranty, maintenance/license/service pricing. |
| `pricing/country_origin_code_schema.json` | Required | Country code/origin schema. |
| `pricing/tax_schema.json` | Required | VAT/tax treatment and grand-total formulas. |

---

## 13. Import order impact

The seed package import order should be updated as follows:

```text
01_source_documents
02_template_family
03_template_version
04_sections
05_clauses
06_mutability
07_parameters_tds
08_parameters_scc
09_rules_core
10_forms_catalog
11_forms_fields
12_evidence_requirements
13_price_schedule_schemas
14_evaluation_profile
15_evaluation_criteria
16_qualification_requirements
17_form_bindings
18_render_blocks
19_workflow_bindings
20_smoke_tests
21_calibration_fixtures
```

Pass 3 specifically populates import groups 10 through 17 and adds smoke tests to group 20.

---

## 14. Render block implications

| Render block | Source | Purpose |
| --- | --- | --- |
| `R-EVAL-GENERAL-PROVISION` | Section III.1 | Render general evaluation rules. |
| `R-EVAL-MULTIPLE-CONTRACTS` | Section III.1.3 | Render selected lot-award option. |
| `R-EVAL-PRELIMINARY` | Section III.3 | Render preliminary examination criteria and document checklist. |
| `R-EVAL-TECHNICAL` | Section III.4 | Render technical criteria, points, pass mark, subcriteria. |
| `R-EVAL-FINANCIAL` | Section III.5 | Render price/recurrent cost/time schedule criteria. |
| `R-EVAL-PREFERENCE` | Section III.7 | Render preference margin only when enabled. |
| `R-EVAL-POSTQUAL` | Section III.8-11 | Render qualification and postqualification requirements. |
| `R-FORM-CATALOG` | Section IV | Render selected/required forms in correct order. |
| `R-PRICE-SCHEDULES` | Price Schedule Forms | Render price forms and supplier input tables. |
| `R-QUAL-FORMS` | Qualification Forms | Render eligibility, experience, financial, personnel, IP, and conformance forms. |

---

## 15. Smoke contracts from Pass 3

### 15.1 Evaluation smoke contracts

| Smoke ID | Scenario | Expected result |
| --- | --- | --- |
| `SMOKE-IT-EVAL-001` | Technical criteria total points = 99. | Block publication. |
| `SMOKE-IT-EVAL-002` | Technical criteria total points = 100 but pass mark missing. | Block publication. |
| `SMOKE-IT-EVAL-003` | Pass mark set to 75. | Pass normal validation. |
| `SMOKE-IT-EVAL-004` | Pass mark set to 90. | Require override/legal-procurement approval because outside indicative 70-85. |
| `SMOKE-IT-EVAL-005` | Financial evaluation attempted before technical pass/fail complete. | Block evaluation action. |
| `SMOKE-IT-EVAL-006` | Additional criterion added outside Section III schema. | Block publication. |
| `SMOKE-IT-EVAL-007` | Lot evaluation enabled without lot-aware price schedule. | Block publication. |
| `SMOKE-IT-EVAL-008` | Margin of preference enabled without ownership data fields/evidence. | Block publication. |

### 15.2 Forms smoke contracts

| Smoke ID | Scenario | Expected result |
| --- | --- | --- |
| `SMOKE-IT-FORM-001` | Form of Tender missing signature. | Supplier submission blocked. |
| `SMOKE-IT-FORM-002` | Certificate of Independent Tender Determination missing. | Preliminary responsiveness fail. |
| `SMOKE-IT-FORM-003` | Self-declaration missing. | Preliminary responsiveness fail. |
| `SMOKE-IT-FORM-004` | Foreign tenderer submits no 40% local content form when rule active. | Preliminary/qualification fail. |
| `SMOKE-IT-FORM-005` | JV tender without JV member ELI forms. | Preliminary/qualification fail. |
| `SMOKE-IT-FORM-006` | Specific experience criterion active but EXP-2 form omitted. | Publication blocked or supplier submission blocked depending stage. |
| `SMOKE-IT-FORM-007` | Personnel scoring active but no personnel form required. | Publication blocked. |
| `SMOKE-IT-FORM-008` | IP forms omitted for software procurement. | Publication warning/blocker depending package setting. |

### 15.3 Price schedule smoke contracts

| Smoke ID | Scenario | Expected result |
| --- | --- | --- |
| `SMOKE-IT-PRICE-001` | Grand Summary total does not equal supply/install + recurrent totals. | Supplier submission blocked or arithmetic correction workflow triggered. |
| `SMOKE-IT-PRICE-002` | Recurrent costs activated in evaluation but recurrent cost table missing. | Publication blocked. |
| `SMOKE-IT-PRICE-003` | Supplier uses unsupported foreign currency. | Supplier submission blocked. |
| `SMOKE-IT-PRICE-004` | Form of Tender total differs from Grand Summary total. | Supplier submission blocked or evaluator correction workflow triggered, depending submission stage. |
| `SMOKE-IT-PRICE-005` | Price adjustment disabled but supplier enters adjustment formula. | Supplier submission blocked. |
| `SMOKE-IT-PRICE-006` | VAT/tax total not arithmetically consistent with net total. | Supplier submission blocked or correction workflow triggered. |
| `SMOKE-IT-PRICE-007` | NSSF-style flat schedule imported with rows and totals. | Import allowed only if mapped to official roll-up and flagged as PE-specific schedule profile. |

---

## 16. Database/domain model additions from Pass 3

The existing STD Engine Core domain model should be extended or confirmed to include the following tables/DocTypes.

| Domain object | Key fields | Notes |
| --- | --- | --- |
| `STD Evaluation Profile` | template_version, award_method, technical_scoring_enabled, pass_mark, lot_evaluation_mode | One per STD version or tender instance override. |
| `STD Evaluation Stage` | profile, sequence, stage_type, gate_behavior | Preliminary/technical/financial/postqual. |
| `STD Evaluation Criterion` | stage, code, label, max_points, min_points, range_min, range_max, required, parent_criterion | Supports nested criteria. |
| `STD Evaluation Formula` | criterion/stage, formula_type, expression, inputs, output | Recurrent cost, preference margin, totals. |
| `STD Qualification Requirement` | code, subject, threshold_type, threshold_value, evidence_required, form_binding | Postqualification and eligibility. |
| `STD Form` | code, title, form_type, respondent_type, render_order, activation_rule | Form catalog. |
| `STD Form Field` | form, field_code, label, data_type, required, conditional_rule, evidence_rule | Supplier response schema. |
| `STD Evidence Requirement` | form/field/criterion, evidence_type, required, file_rules, verification_owner | Evidence uploads. |
| `STD Price Schedule Profile` | code, profile_type, currency_policy, tax_policy, recurrent_cost_policy | Official vs PE-specific profiles. |
| `STD Price Schedule Table` | profile, table_type, render_order, rollup_target | Grand, summary, sub-table. |
| `STD Price Field` | table, field_code, type, formula, editable_by_supplier | Structured price input. |
| `Tender Supplier Response` | tender, supplier, form_instance, status, submitted_at, hash | Supplier submission. |
| `Tender Supplier Price Row` | response, table, line_no, item, qty, unit_rate, totals, currency | Price schedule response. |
| `Tender Evaluation Score` | tender, supplier, criterion, evaluator, score, justification, status | Evaluation workbench. |
| `Tender Qualification Finding` | tender, supplier, requirement, finding, notes, evidence_refs | Postqualification. |

---

## 17. Governance and approval impact

Before this package can be activated, the following approvals must be completed:

| Approval item | Required approver | Reason |
| --- | --- | --- |
| Evaluation stage and scoring schema | Procurement/legal reviewer | Evaluation criteria determine award legality. |
| Technical criterion ranges and pass mark rules | Procurement/legal reviewer | Prevents arbitrary or discriminatory scoring. |
| Form catalog and required/optional activation rules | Procurement/legal reviewer | Supplier obligations must match published tender. |
| Price schedule formulas | Procurement + finance reviewer | Evaluated price must be deterministic and auditable. |
| Recurrent cost inclusion/exclusion | Procurement + technical reviewer | IT costs may materially change evaluated price. |
| Preference/reservation formula | Procurement/legal reviewer | Must align with statutory and TDS configuration. |
| Brand-specific criteria controls | Procurement/legal/technical reviewer | Real tenders may include platform-specific requirements; misuse is high-risk. |

No approval/state-transition gap is acceptable at this stage. The extraction from Pass 3 affects award outcomes directly; therefore the package must remain non-activatable until evaluation, form, and price schedule governance is complete.

---

## 18. Acceptance criteria for Pass 3 completion

Pass 3 is complete when the following conditions are met:

| Acceptance ID | Criterion | Status expected now |
| --- | --- | --- |
| `AC-P3-001` | Section III evaluation stages are represented as structured records. | Met in this document. |
| `AC-P3-002` | Technical criteria and point ranges are extracted. | Met in this document. |
| `AC-P3-003` | Financial evaluation, recurrent cost, preference, and lot rules are identified. | Met in this document. |
| `AC-P3-004` | Qualification requirements are mapped to forms. | Met in this document. |
| `AC-P3-005` | Tendering forms catalog is extracted. | Met in this document. |
| `AC-P3-006` | Price schedule schemas are defined. | Met in this document. |
| `AC-P3-007` | NSSF ERP tender calibration findings are captured. | Met in this document. |
| `AC-P3-008` | Seed package file updates are identified. | Met in this document. |
| `AC-P3-009` | Smoke contracts are defined. | Met in this document. |
| `AC-P3-010` | Full field-level legal text hashing is complete. | Not yet; future pass. |
| `AC-P3-011` | Final render templates are complete. | Not yet; future pass. |
| `AC-P3-012` | Legal/procurement approval is complete. | Not yet; future governance step. |

---

## 19. Next recommended artifact

The next artifact should be:

**IT STD Full Source Extraction Pass 4 - Procuring Entity Requirements, Technical Requirements, Implementation Schedule, and System Inventory Schemas**

That pass should extract Part 2 of the official IT STD and convert it into the structured IT Requirements Composer:

1. Functional, architectural, and performance requirements
2. Service specifications - supply and install items
3. Technology specifications - supply and install items
4. Testing and quality assurance requirements
5. Service specifications - recurrent cost items
6. Implementation schedule
7. System inventory tables
8. Background and informational materials
9. Bidder conformance matrix bindings
10. NSSF ERP requirement calibration

The reason to do Pass 4 next is simple: Section III evaluation references Part 2 technical requirements directly. The evaluation model is not complete until the technical requirement records exist and can be linked to evaluation criteria, conformance forms, price schedules, and acceptance tests.

---

## 20. Non-activation statement

This extraction pass is **not activatable**. It is a draft source extraction and schema-design artifact. The IT STD package must remain in `DRAFT` or `STRUCTURING` state until at least the following are completed:

1. Full clause and form text extraction with source anchors and hashes.
2. Full Part 2 technical requirement extraction.
3. Render template implementation.
4. Evaluation and price formula implementation.
5. Smoke-test execution.
6. Legal/procurement review.
7. Approval and activation under STD Engine governance.
