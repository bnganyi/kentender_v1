# NSSF ERP Calibration Mapping

**Artifact:** NSSF ERP Calibration Mapping  
**Related STD Package:** `KE-PPRA-IT-2022-04`  
**Related Seed Package:** `KE-PPRA-IT-2022-04_Seed_Package_v0_2`  
**Status:** Draft calibration artifact  
**Activation Status:** Not activatable as an STD master package artifact  
**Prepared for:** KenTender e-Procurement System  

---

## 1. Purpose

This document maps the real-world NSSF Staff Pension Scheme ERP tender to the generalized STD Engine and to the official PPRA Standard Tender Document for Procurement of Information Technology.

The purpose is not to convert the NSSF tender into a new master STD. The purpose is to prove that a real ERP procurement can be represented as a tender-specific configuration instance derived from the official IT STD package.

The calibration answers four questions:

1. Can the NSSF ERP tender be represented by the generalized STD Engine without hard-coding ERP-specific behavior?
2. Which parts of the NSSF tender map cleanly to the official IT STD model?
3. Which parts require governance review, warning, or deviation handling?
4. What changes, if any, are needed before building the IT Tender Configuration Wizard?

---

## 2. Source Documents Used

| Source | Role in Calibration | Treatment |
|---|---|---|
| Official PPRA STD for Procurement of Information Technology, Doc. 10 | Legal master template | Authoritative source for structure, rules, forms, price schedules, GCC/SCC, and contract forms |
| NSSF SPS ERP Tender, Ref. `NSSFSPS/ICT/ERP/001/2025-2026` | Real-world calibration fixture | Tender instance example only; must not mutate the master STD |
| `KE-PPRA-IT-2022-04_Seed_Package_v0_2` | Draft package skeleton | Target structure for import and validation testing |
| Extraction Passes 1-5 | Source extraction artifacts | Used to reconcile IT STD sections, rules, parameters, requirements, evaluation, and contract carry-forward |

---

## 3. High-Level Calibration Result

The NSSF ERP tender can be represented by the generalized STD Engine, but only if the system supports five capabilities clearly:

1. **Tender-specific configuration values** must be separated from the STD master package.
2. **Requirement matrices** must be native structured data, not document uploads.
3. **Evaluation criteria** must support mandatory pass/fail checks, minimum qualification checks, and weighted scoring.
4. **IT price schedules** must support both official STD detailed price tables and simplified PE-specific price formats under governance.
5. **Deviation and compression detection** must flag when a real tender omits or modifies master STD sections, forms, schedules, or contract forms.

Overall result:

| Calibration Area | Result | Comment |
|---|---|---|
| Tender identity and invitation | Pass | Maps cleanly to invitation and TDS parameters |
| TDS values | Pass with warning | Most values map; professional indemnity handling needs policy treatment |
| ITT/GCC locked text | Warning | NSSF tender uses compressed/reworded text rather than full locked STD text |
| Technical requirements | Pass | Strong fit for requirement composer and compliance matrix |
| Implementation schedule | Pass | Two-phase model maps well to implementation milestones |
| System inventory | Partial | NSSF uses scope/schedule and price tables, but not full official system inventory tables |
| Evaluation | Pass with governance warnings | Strong evaluation model; some vendor-specific criteria require justification |
| Tendering forms | Partial | NSSF uses reduced form set compared with official STD |
| Price schedules | Partial | NSSF uses simplified price schedule; official STD expects supply/install and recurrent cost separation |
| SCC and contract terms | Pass with warning | Strong contract content, including escrow, SLA, performance security, warranty |
| Contract forms | Partial | NSSF includes reduced contract form set |
| Addendum readiness | Not tested | No addendum sample provided |

---

## 4. NSSF ERP Tender Profile

| Attribute | NSSF Tender Value | STD Engine Object |
|---|---|---|
| Procuring Entity | National Social Security Fund Staff Pension Scheme | `TenderSTDInstance.procuring_entity_name` |
| Tender Reference | `NSSFSPS/ICT/ERP/001/2025-2026` | `TenderSTDInstance.tender_number` |
| Contract Name | Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an ERP System | `TenderSTDInstance.contract_name` |
| Procurement Type | Information Technology / ERP System | `TenderSTDInstance.procurement_category` |
| Tendering Method | Open National Competitive Tendering | `TenderSTDConfigurationValue.procurement_method` |
| Currency | Kenya Shillings | `TenderSTDConfigurationValue.currency` |
| Tender Validity | 154 days | `TenderSTDConfigurationValue.tender_validity_days` |
| Alternative Tenders | Not permitted | `TenderSTDConfigurationValue.alternative_tenders_allowed` |
| Pre-Tender Meeting | N/A | `TenderSTDConfigurationValue.pre_tender_meeting_required` |
| Submission Deadline | 30 June 2026, 11:00 AM EAT | `TenderSTDConfigurationValue.submission_deadline` |
| Electronic Tenders | Not permitted | `TenderSTDConfigurationValue.electronic_tendering_allowed` |
| Performance Security | 10% of contract price | `SCCParameter.performance_security_percentage` |
| Warranty | 12 months per phase from acceptance | `SCCParameter.warranty_period` |
| Implementation Structure | Two financial-year phases | `ITImplementationMilestone.phase_group` |

---

## 5. Mapping to STD Engine Layers

### 5.1 Master STD Layer

The NSSF tender must not create or modify master STD records.

| Master Object | Treatment |
|---|---|
| `STDTemplateFamily` | Use existing family `KE-PPRA-IT` |
| `STDTemplateVersion` | Use `KE-PPRA-IT-2022-04` once legally activated |
| `STDSourceDocument` | Official PPRA IT STD only |
| `STDSection` | Official IT STD section structure only |
| `STDClause` | Official locked clauses only |
| `STDParameter` | Official TDS/SCC/configurable fields only |
| `STDRule` | Official rule dictionary plus approved generalized engine rules |
| `STDFormSchema` | Official form schemas only |
| `STDRenderBlock` | Official rendering map only |

### 5.2 Tender Instance Layer

The NSSF tender maps here.

| Tender Instance Object | NSSF Data |
|---|---|
| `TenderSTDInstance` | NSSF ERP tender identity and active IT STD binding |
| `TenderSTDConfigurationValue` | TDS/SCC values, procurement method, deadlines, validity, security, currency, alternatives |
| `TenderRequirementSet` | ERP functional, technical, system, project, training, testing, warranty, and support requirements |
| `TenderRequirementItem` | Individual compliance matrix rows, e.g. General Requirement 1, Pension Requirement B1, etc. |
| `TenderEvaluationSchemaInstance` | Mandatory, qualification, scored technical, financial evaluation setup |
| `TenderPriceScheduleInstance` | NSSF price schedule structure |
| `TenderContractCarryForward` | Payment milestones, SLA, warranty, escrow, performance security, acceptance certificates |
| `TenderGeneratedBundle` | Published NSSF tender document output, if generated from engine |
| `TenderValidationFinding` | Warnings/deviations detected against official IT STD |

---

## 6. Section Mapping

| NSSF Section | NSSF Content | Official IT STD Target | Engine Handling | Calibration Result |
|---|---|---|---|---|
| Invitation to Tender | PE identity, contract name, tender number, method, indemnity, deadline, address | Invitation to Tender | Generated render block populated from TDS values | Pass |
| Section I - ITT | Compressed instructions | Section I - ITT | Locked official text should be rendered, not rewritten | Warning |
| Section II - TDS | Table of tender data and SCC-like fields | Section II - TDS | Structured parameter values | Pass with normalization |
| Section III - Evaluation | Mandatory, qualification, scored technical criteria | Section III - Evaluation and Qualification Criteria | Evaluation schema instance | Pass with review flags |
| Section IV - Tendering Forms | Form of Tender, Confidential Business Questionnaire, Independent Tender Determination, Self-Declaration | Section IV - Tendering Forms | Form schema subset | Partial |
| Part 2 - Requirements | Background, objectives, scope, phases, technical requirements, compliance matrix | Sections V-IX | Requirement composer, implementation schedule, system inventory, background material | Pass with system inventory gap |
| Section VIII - Compliance Requirements | Requirement rows with M and yes/no/reference page columns | Technical Requirements / Conformance Matrix | Native requirement conformance model | Pass |
| Section IX - Schedule of Requirements | Deliverable/scope schedule | Implementation Schedule / System Inventory | Milestone and deliverable schema | Partial |
| Section X - Price Schedule | Price structure | Price Schedule Forms | Price schedule instance | Partial |
| Section XI - GCC | Short contract conditions | GCC | Locked official GCC should be rendered | Warning |
| Section XII - SCC | Governing law, scope, payment, IP/escrow, subcontracting, SLA, performance security | SCC | SCC parameters and contract carry-forward | Pass |
| Section XIII - Contract Forms | Contract agreement, performance security, notification of intention to award | Contract Forms | Contract form subset | Partial |

---

## 7. TDS Calibration

### 7.1 Cleanly Mapped TDS Parameters

| STD Parameter | NSSF Value | Validation |
|---|---|---|
| `tender_name` | Supply, Installation, Configuration, Customization, Testing, Commissioning and Maintenance of an ERP System | Pass |
| `tender_number` | `NSSFSPS/ICT/ERP/001/2025-2026` | Pass |
| `procurement_method` | Open National Competitive Tendering | Pass |
| `currency` | KES | Pass |
| `alternative_tenders_allowed` | No | Pass |
| `price_adjustment_allowed` | No | Pass |
| `tender_validity_days` | 154 | Pass |
| `submission_deadline` | 30 June 2026, 11:00 AM EAT | Pass |
| `pre_tender_meeting_required` | No | Pass |
| `jv_max_members` | Three | Pass |
| `tender_opening_location` | NSSF SPS offices, Hazina Trade Centre, Nairobi | Pass |
| `performance_security_percentage` | 10% | Pass |
| `warranty_period` | 12 months per phase | Pass |

### 7.2 TDS Governance Warnings

| Issue | NSSF Treatment | Engine Finding | Recommended Handling |
|---|---|---|---|
| Professional indemnity used where official STD commonly expects tender security / tender-securing declaration options | Professional indemnity of KES 500,000 required | `WARNING_SECURITY_INSTRUMENT_VARIANT` | Allow only if parameterized as PE-specific security/evidence requirement and reviewed |
| Electronic tendering disabled | Not permitted | No issue | Standard configurable value |
| Tender documents shared to invited bidders, while method says open national competitive tendering | Tender document says open national, but also says documents shared to invited bidders | `WARNING_METHOD_DISTRIBUTION_INCONSISTENCY` | Require procurement review clarification |
| Some SCC values are placed inside TDS table | Payment milestones and warranty appear in TDS table | `WARNING_TDS_SCC_MIXED_CONTENT` | Normalize into SCC/contract carry-forward fields |

---

## 8. Evaluation Calibration

### 8.1 NSSF Evaluation Stages

NSSF uses a three-stage model:

1. Preliminary examination for responsiveness
2. Technical evaluation
3. Financial evaluation for lowest evaluated price

This maps cleanly to the official IT STD evaluation model and the generalized engine.

| NSSF Stage | Engine Object | Result |
|---|---|---|
| Preliminary mandatory requirements | `EvaluationStage.PRELIMINARY_RESPONSIVENESS` | Pass |
| Technical qualification criteria | `EvaluationStage.TECHNICAL_QUALIFICATION` | Pass |
| Technical scoring criteria | `EvaluationStage.TECHNICAL_SCORING` | Pass |
| Minimum technical pass mark | `EvaluationThreshold.minimum_score` | Pass |
| Financial evaluation | `EvaluationStage.FINANCIAL_EVALUATION` | Pass |
| Award | `AwardRule.lowest_evaluated_responsive_tender` | Pass |

### 8.2 Mandatory Requirements Mapping

| NSSF Mandatory Requirement | Engine Schema Type | Calibration Result |
|---|---|---|
| Certificate of Incorporation/Registration in Kenya | Eligibility evidence | Pass |
| Tax Compliance Certificate | Statutory compliance evidence | Pass |
| NSSF Compliance Certificate | Statutory compliance evidence | Pass |
| CR12 or equivalent | Ownership/control evidence | Pass |
| Professional Indemnity KES 500,000 | Security/evidence requirement | Warning: instrument classification needed |
| Signed Form of Tender | Required form | Pass |
| Certificate of Independent Tender Determination | Required declaration | Pass |
| Self-Declaration Form | Required declaration | Pass |
| Microsoft Dynamics 365 Business Central authorization | Product/vendor-specific qualification | Governance warning |

### 8.3 Qualification Criteria Mapping

| NSSF Qualification Criterion | Engine Type | Calibration Result |
|---|---|---|
| Minimum five years ERP implementation experience | Qualification rule | Pass |
| At least three Dynamics 365 Business Central implementations in Kenya | Specific experience | Pass with vendor-specific warning |
| At least two post-implementation support projects for pension/retirement fund | Specific experience | Pass |
| Average turnover of KES 50 million over three audited years | Financial qualification | Pass |
| Project Manager qualifications | Key personnel rule | Pass |
| Technical Lead qualifications | Key personnel rule | Pass |
| Pension Administration Functional Consultant | Key personnel rule | Pass |
| Finance Functional Consultant | Key personnel rule | Pass |
| Local presence in Kenya | Support capability rule | Governance warning if applied restrictively |

### 8.4 Scored Technical Evaluation Mapping

| Criterion | Points | Engine Object | Result |
|---|---:|---|---|
| Company profile, experience, and past performance | 20 | `ScoredCriterion` | Pass |
| Technical solution proposal | 25 | `ScoredCriterion` | Pass |
| Implementation methodology | 15 | `ScoredCriterion` | Pass |
| Key personnel | 15 | `ScoredCriterion` | Pass |
| Post-implementation support and maintenance plan | 10 | `ScoredCriterion` | Pass |
| Data migration and integration approach | 10 | `ScoredCriterion` | Pass |
| Training plan | 5 | `ScoredCriterion` | Pass |
| Total | 100 | `EvaluationScoreTotal` | Pass |
| Minimum pass mark | 75 | `EvaluationThreshold` | Pass |

### 8.5 Evaluation Warnings

| Warning Code | Trigger | Reason | Required Action |
|---|---|---|---|
| `WARNING_VENDOR_SPECIFIC_REQUIREMENT` | Microsoft Dynamics 365 Business Central authorization is mandatory | May be valid if procurement is for that platform, but needs justification | Require procurement/legal review note |
| `WARNING_LOCAL_PRESENCE_REQUIREMENT` | Proof of Kenya office and local support contacts | Could be legitimate for support; may be restrictive if overused | Require support justification |
| `WARNING_SECTOR_SPECIFIC_EXPERIENCE` | Pension/RBA-regulated implementation experience | Strong relevance, but may narrow competition | Require proportionality review |
| `WARNING_REFERENCE_LETTER_ADDRESSEE` | References addressed specifically to Trust Secretary | May be administratively restrictive | Recommend accepting verifiable equivalent references unless legally justified |

---

## 9. Requirements Composer Calibration

The NSSF tender is a strong proof that the Requirements Composer must support hierarchical, requirement-row based configuration.

### 9.1 Requirement Groups

| NSSF Requirement Group | Engine Requirement Category | Result |
|---|---|---|
| General Requirements | `GENERAL` | Pass |
| Pension Management | `FUNCTIONAL` | Pass |
| General Ledger | `FUNCTIONAL` | Pass |
| Procurement Module | `FUNCTIONAL` | Pass |
| HR & Payroll | `FUNCTIONAL` | Pass |
| Customer Care / CRM | `FUNCTIONAL` | Pass |
| EDMS via SharePoint | `FUNCTIONAL` / `INTEGRATION` | Pass with platform-specific warning |
| E-Board | `FUNCTIONAL` | Pass |
| Business Intelligence | `REPORTING_ANALYTICS` | Pass |
| Liveness Certification | `SECURITY_IDENTITY` | Pass |
| Member Self-Service Portals | `CHANNELS` | Pass |
| System Requirements | `ARCHITECTURE` / `NON_FUNCTIONAL` | Pass |
| Project Management | `SERVICE_SPECIFICATION` | Pass |
| Data Migration | `DATA_MIGRATION` | Pass |
| Database Analysis | `DATA_ANALYSIS` | Pass |
| Business Value Enhancements | `OPTIONAL_OR_ENHANCEMENT` | Pass with scoring policy review |
| Integration Requirements | `INTEGRATION` | Pass |
| Documentation Standards | `DOCUMENTATION` | Pass |
| Training and Knowledge Transfer | `TRAINING` | Pass |
| Testing and Acceptance | `TESTING_ACCEPTANCE` | Pass |
| Implementation Schedule and Location | `IMPLEMENTATION` | Pass |
| Hardware and Cloud Infrastructure | `INFRASTRUCTURE` | Pass |
| Warranty, Support, and Maintenance | `SUPPORT_MAINTENANCE` | Pass |

### 9.2 Requirement Row Model

Each NSSF compliance row should map to this object pattern:

```json
{
  "requirement_id": "NSSF-ERP-GEN-002",
  "source_section": "Section VIII - Technical Specifications and Compliance Requirements",
  "category": "ARCHITECTURE",
  "subsystem": "General Requirements",
  "requirement_text": "The ERP system shall be built on Microsoft Dynamics 365 Business Central, deployed as a fully cloud-based solution on Microsoft Azure...",
  "criticality": "MANDATORY",
  "response_type": "YES_NO_WITH_REFERENCE",
  "requires_bidder_commentary": true,
  "requires_reference_pages": true,
  "requires_evidence": false,
  "governance_flags": ["VENDOR_SPECIFIC", "CLOUD_PLATFORM_SPECIFIC"]
}
```

### 9.3 Requirement Governance Findings

| Requirement Pattern | Finding | Required Engine Behavior |
|---|---|---|
| Product-specific platform requirement | Microsoft Dynamics 365 Business Central / Azure | Must trigger `VENDOR_SPECIFIC_REQUIREMENT` review |
| Proprietary EDMS platform requirement | SharePoint | Must trigger platform-specific justification |
| API/protocol requirements | SOAP, OData, REST/JSON | Normal technical requirement |
| Data Protection Act compliance | Security/legal compliance | Normal statutory/regulatory requirement |
| Source code / customization ownership | Contract/IP requirement | Carry forward to SCC and contract appendices |
| Liveness/biometric proof of life | Sensitive data processing | Must require privacy/security review in platform design |

---

## 10. Implementation Schedule Calibration

The NSSF tender uses a two-phase implementation structure across two financial years.

| NSSF Phase | Modules | Engine Object |
|---|---|---|
| Phase 1 - FY 2026/2027 | Pension Administration, Finance, HR & Payroll, Procurement, CRM | `ITImplementationPhase` |
| Phase 2 - FY 2027/2028 | E-Board, EDMS, Member Self-Service, BI, Liveness Certification | `ITImplementationPhase` |
| Cross-phase integration | Phase 1 must interface with Phase 2 without re-implementation | `ITIntegrationDependency` |
| Maximum duration | 24 months | `ImplementationConstraint.maximum_duration_months` |
| Acceptance | Acceptance certificate per phase | `AcceptanceMilestone` |
| Warranty | 12 months per phase from acceptance | `WarrantyPeriod` |

### 10.1 Engine Implication

The wizard must support phased implementation without converting the tender into multiple separate tenders. The contract may remain a single award while delivery, acceptance, payment, and warranty are milestone-driven.

Required fields:

| Field | Required |
|---|---|
| `phase_code` | Yes |
| `phase_name` | Yes |
| `financial_year` | Optional but useful |
| `module_scope` | Yes |
| `dependency_notes` | Yes |
| `acceptance_required` | Yes |
| `payment_trigger` | Optional; if payment milestone exists |
| `warranty_start_trigger` | Yes |

---

## 11. System Inventory Calibration

The NSSF tender demonstrates a common real-world pattern: PEs often describe modules and price schedules, but do not fully produce official STD-style system inventory tables.

| Official IT STD Expectation | NSSF Treatment | Calibration Result |
|---|---|---|
| Implementation Schedule | Two-phase scope and maximum timeline | Partial pass |
| System Inventory Table - Supply and Installation Cost Items | Not fully expressed as official inventory rows | Gap |
| System Inventory Table - Recurrent Cost Items | Warranty/support/maintenance stated, but not full recurrent inventory table | Gap |
| Price Schedule linked to inventory | Simplified schedule | Gap |
| Technical requirement cross-references | Compliance matrix has requirement IDs/sections | Pass |

### 11.1 Required Engine Finding

The engine should produce this warning when a tender has technical requirements and price schedules but no corresponding system inventory structure:

```json
{
  "finding_code": "WARNING_SYSTEM_INVENTORY_PRICE_LINK_MISSING",
  "severity": "WARNING",
  "message": "The tender contains technical requirements and price schedules, but not all priced items are linked to implementation schedule and system inventory records.",
  "blocking": false,
  "requires_reviewer_acknowledgement": true
}
```

This should be a warning in early system rollout. Later, once the platform enforces full digital STDs, it should become a blocker before publication unless explicitly waived by an authorized reviewer.

---

## 12. Price Schedule Calibration

The official IT STD expects detailed supply/install and recurrent cost structures. NSSF uses a simpler ERP pricing approach.

### 12.1 Required Price Model Support

The engine must support at least three price schedule profiles:

| Price Profile | Description | Use Case |
|---|---|---|
| `IT_STD_FULL` | Official detailed IT STD price schedules | Production default |
| `IT_SIMPLIFIED_ERP` | Simplified ERP implementation/license/support cost table | Calibration / transitional use |
| `IT_HYBRID` | Official summary tables plus PE-defined module-level pricing | Practical rollout mode |

### 12.2 NSSF Price Schedule Treatment

| Price Area | Engine Mapping | Finding |
|---|---|---|
| Total tender price excluding VAT | `PriceSummary.exclusive_tax_total` | Pass |
| VAT | `TaxLine.vat_amount` | Pass |
| Grand total inclusive of VAT | `PriceSummary.inclusive_tax_total` | Pass |
| Implementation cost by phase/module | `SupplyInstallCostLine` | Requires extraction |
| License/subscription costs | `RecurrentCostLine` | Requires extraction |
| Support/maintenance | `RecurrentCostLine` | Requires extraction |
| Warranty cost treatment | `WarrantyCostPolicy` | Requires explicit rule |
| Escrow cost borne by vendor | `ContractCostResponsibility` | Contract carry-forward |

### 12.3 Validation Rule

```json
{
  "rule_code": "PRICE_TOTALS_RECONCILE_WITH_FORM_OF_TENDER",
  "severity": "BLOCKER",
  "scope": "TENDER_SUBMISSION",
  "condition": "form_of_tender.grand_total == price_schedule.grand_total",
  "message": "The Form of Tender grand total must reconcile with the price schedule grand total."
}
```

---

## 13. Contract Carry-Forward Calibration

The NSSF tender contains strong contract-specific material. This proves the engine must not stop at tender publication. It must carry award and contract data into contract formation and execution.

| NSSF Contract Term | Engine Object | Result |
|---|---|---|
| Governing law: Kenya | `SCCParameter.governing_law` | Pass |
| Scope includes all modules, no exclusions | `ContractScopeConstraint` | Pass |
| Commencement within 14 days | `CommencementRule` | Pass |
| Maximum implementation period 24 months | `ImplementationTimeGuarantee` | Pass |
| Phase-based payment schedule | `PaymentMilestone` | Pass |
| Customization source code and configuration transfer | `IPCarryForward` | Pass |
| Software escrow arrangement | `EscrowRequirement` | Pass |
| Subcontracting requires prior approval | `SubcontractingApprovalRule` | Pass |
| SLA P1/P2/P3 response and resolution targets | `ServiceLevelAgreement` | Pass |
| Uptime 99.5% monthly | `ServiceAvailabilityMetric` | Pass |
| Performance security 10% | `PerformanceSecurityRequirement` | Pass |
| Acceptance certificate per phase | `AcceptanceCertificateRequirement` | Pass |

### 13.1 Contract Carry-Forward Object Pattern

```json
{
  "carry_forward_id": "NSSF-ERP-CF-IP-001",
  "source": "Tender SCC / Technical Requirements",
  "target_contract_section": "SCC - Intellectual Property",
  "target_contract_appendix": "Custom Materials / Software Categories",
  "value_type": "ESCROW_REQUIREMENT",
  "value": {
    "applies_to": "customizations, configurations, bespoke development",
    "escrow_required": true,
    "escrow_setup_deadline_days_after_signing": 30,
    "release_triggers": ["vendor insolvency", "cessation of business", "material breach"],
    "cost_responsibility": "supplier"
  }
}
```

---

## 14. Forms Calibration

NSSF uses a reduced form set compared with the official IT STD.

| Official IT STD Form Area | NSSF Equivalent | Result |
|---|---|---|
| Form of Tender | Present | Pass |
| Confidential Business Questionnaire | Present | Pass |
| Certificate of Independent Tender Determination | Present | Pass |
| Self-Declaration / Fraud and Corruption | Present | Pass |
| Price Schedule Forms | Present but simplified | Partial |
| Foreign Tenderers 40% Rule | Referenced in ITT but not fully in forms | Gap |
| ELI-1 Tenderer Information | Simplified via questionnaire | Partial |
| JV Members Form | Not visible in reduced form set | Gap if JVs allowed |
| Historical Contract Non-Performance | Not visible in reduced form set | Gap |
| Experience Forms | Captured through criteria/evidence, not official forms | Partial |
| Financial Situation / Turnover / Resources | Captured through audited statements, not official forms | Partial |
| Personnel Capabilities | Captured through CV/certification requirements | Partial |
| IP Forms | Mentioned in documents comprising tender; not full official form set | Gap |
| Conformance of Information System Materials | Implemented via compliance matrix | Pass conceptually |

### 14.1 Required Engine Finding

```json
{
  "finding_code": "WARNING_OFFICIAL_FORM_SET_COMPRESSED",
  "severity": "WARNING",
  "message": "The tender uses a reduced or compressed form set compared with the official IT STD form catalog.",
  "requires_reviewer_acknowledgement": true
}
```

---

## 15. Deviation and Governance Register

| Finding Code | Severity | NSSF Trigger | Recommended Decision |
|---|---|---|---|
| `WARNING_LOCKED_ITT_TEXT_COMPRESSED` | Warning | NSSF Section I appears shortened | Official locked ITT should be rendered by engine |
| `WARNING_LOCKED_GCC_TEXT_COMPRESSED` | Warning | NSSF GCC is short-form | Official locked GCC should be rendered by engine |
| `WARNING_TDS_SCC_MIXED_CONTENT` | Warning | Payment milestones and warranty appear in TDS | Normalize into SCC/carry-forward |
| `WARNING_VENDOR_SPECIFIC_REQUIREMENT` | Warning / Review | Microsoft Dynamics 365 Business Central mandatory | Require justification and approval |
| `WARNING_CLOUD_PLATFORM_SPECIFIC_REQUIREMENT` | Warning / Review | Microsoft Azure required | Require justification and approval |
| `WARNING_OFFICIAL_FORM_SET_COMPRESSED` | Warning | Reduced tendering forms | Procurement/legal review |
| `WARNING_SYSTEM_INVENTORY_PRICE_LINK_MISSING` | Warning | Price schedule not fully linked to inventory | Require inventory completion in future wizard |
| `WARNING_REFERENCES_ADDRESSEE_RESTRICTIVE` | Warning | Client reference letters addressed specifically to NSSF Trust Secretary | Review proportionality |
| `WARNING_METHOD_DISTRIBUTION_INCONSISTENCY` | Warning | Open tendering plus documents shared to invited bidders | Clarify method and document access |
| `INFO_PHASED_SINGLE_AWARD` | Info | Two-phase implementation under one contract | Supported |
| `INFO_ESCROW_REQUIRED` | Info | Escrow for customizations/configurations | Supported contract carry-forward |
| `INFO_ACCEPTANCE_CERTIFICATE_PER_PHASE` | Info | Acceptance certificate per phase | Supported |

---

## 16. Import Simulation Model

The NSSF calibration should be imported only as a fixture, not as STD master data.

### 16.1 Suggested Fixture Directory

```text
fixtures/
  nssf-erp-2025-2026/
    fixture_manifest.json
    tender_identity.json
    tds_values.json
    scc_values.json
    requirement_groups.json
    requirement_items.json
    evaluation_schema_instance.json
    price_schedule_instance.json
    implementation_schedule_instance.json
    contract_carry_forward.json
    validation_expected_findings.json
```

### 16.2 Fixture Manifest

```json
{
  "fixture_code": "NSSF-SPS-ERP-2025-2026",
  "fixture_type": "REAL_WORLD_CALIBRATION",
  "do_not_import_by_default": true,
  "master_std_family_code": "KE-PPRA-IT",
  "master_std_version_code": "KE-PPRA-IT-2022-04",
  "expected_result": "IMPORT_AS_TENDER_INSTANCE_FIXTURE_ONLY",
  "activation_allowed": false
}
```

---

## 17. Required Updates to v0.2 Package Based on Calibration

The calibration does not require structural redesign of the STD Engine, but it does require several additions before the IT wizard PRD.

### 17.1 Add Validation Codes

Add to `rules/validation_findings.json` or equivalent:

```json
[
  "WARNING_VENDOR_SPECIFIC_REQUIREMENT",
  "WARNING_CLOUD_PLATFORM_SPECIFIC_REQUIREMENT",
  "WARNING_SYSTEM_INVENTORY_PRICE_LINK_MISSING",
  "WARNING_OFFICIAL_FORM_SET_COMPRESSED",
  "WARNING_TDS_SCC_MIXED_CONTENT",
  "WARNING_METHOD_DISTRIBUTION_INCONSISTENCY",
  "WARNING_LOCKED_ITT_TEXT_COMPRESSED",
  "WARNING_LOCKED_GCC_TEXT_COMPRESSED",
  "WARNING_REFERENCES_ADDRESSEE_RESTRICTIVE",
  "INFO_PHASED_SINGLE_AWARD",
  "INFO_ESCROW_REQUIRED",
  "INFO_ACCEPTANCE_CERTIFICATE_PER_PHASE"
]
```

### 17.2 Add Requirement Governance Flags

Add to requirement item enum set:

```json
[
  "VENDOR_SPECIFIC",
  "PRODUCT_SPECIFIC",
  "CLOUD_PLATFORM_SPECIFIC",
  "LOCAL_PRESENCE_REQUIRED",
  "SECTOR_SPECIFIC_EXPERIENCE",
  "SENSITIVE_PERSONAL_DATA_PROCESSING",
  "BIOMETRIC_DATA_PROCESSING",
  "IP_TRANSFER_REQUIRED",
  "ESCROW_REQUIRED",
  "INTEGRATION_CRITICAL"
]
```

### 17.3 Add Price Schedule Profiles

Add to price schedule schema:

```json
[
  "IT_STD_FULL",
  "IT_SIMPLIFIED_ERP",
  "IT_HYBRID"
]
```

### 17.4 Add Contract Carry-Forward Types

Add to contract carry-forward schema:

```json
[
  "PAYMENT_MILESTONE",
  "PERFORMANCE_SECURITY",
  "WARRANTY_PERIOD",
  "SLA_RESPONSE_RESOLUTION",
  "UPTIME_COMMITMENT",
  "IP_TRANSFER",
  "ESCROW_REQUIREMENT",
  "SUBCONTRACTING_APPROVAL",
  "ACCEPTANCE_CERTIFICATE",
  "PHASED_IMPLEMENTATION"
]
```

---

## 18. Wizard Requirements Proven by NSSF Calibration

The IT Tender Configuration Wizard must include at least the following tabs:

| Wizard Tab | NSSF Proof |
|---|---|
| Tender Identity | PE name, tender number, contract name |
| Procurement Method | Open national competitive tendering |
| Dates and Addresses | Closing date, opening venue, clarification address |
| Security / Indemnity | Professional indemnity and performance security |
| Participation Rules | JV max members, alternative tenders, local support |
| Product / Platform Justification | Dynamics 365, Azure, SharePoint |
| Requirements Builder | ERP modules and technical compliance matrix |
| Requirement Governance Review | Vendor-specific and biometric/privacy flags |
| Implementation Phases | FY2026/2027 and FY2027/2028 phases |
| System Inventory | Missing/partial in NSSF; must be guided |
| Price Schedule | Simplified ERP pricing vs full STD pricing |
| Evaluation Setup | Mandatory, qualification, scoring, pass mark |
| Forms Selection | Official vs compressed form set |
| SCC / Contract Terms | Payment, warranty, SLA, escrow, subcontracting |
| Contract Carry-Forward | Acceptance certificates, IP, performance security |
| Validation Findings | Warnings and blockers before publication |
| Preview and Approval | Generated tender bundle review |

---

## 19. Calibration Acceptance Criteria

The calibration should be considered successful only if the following tests pass.

| Test ID | Test | Expected Result |
|---|---|---|
| `CAL-NSSF-001` | Import NSSF as tender instance fixture | Fixture imports without creating master STD records |
| `CAL-NSSF-002` | Bind fixture to `KE-PPRA-IT-2022-04` | Binding succeeds only if STD version is active or simulated as active in test mode |
| `CAL-NSSF-003` | Validate TDS values | Pass with warnings for mixed TDS/SCC content |
| `CAL-NSSF-004` | Validate evaluation schema | Pass; total score equals 100 and pass mark equals 75 |
| `CAL-NSSF-005` | Validate mandatory criteria | Pass; vendor-specific warning triggered |
| `CAL-NSSF-006` | Validate requirements matrix | Pass; product/cloud/biometric flags triggered |
| `CAL-NSSF-007` | Validate implementation phases | Pass; two phases under one contract allowed |
| `CAL-NSSF-008` | Validate system inventory linkage | Warning triggered for incomplete inventory-price linkage |
| `CAL-NSSF-009` | Validate price summary | Pass if Form of Tender totals reconcile with price schedule |
| `CAL-NSSF-010` | Validate contract carry-forward | Pass; payment, warranty, SLA, escrow, performance security captured |
| `CAL-NSSF-011` | Validate forms | Warning for compressed official form set |
| `CAL-NSSF-012` | Render tender preview | Render succeeds only using official locked ITT/GCC text, not compressed NSSF text |
| `CAL-NSSF-013` | Activation attempt | Must be blocked because this is a fixture, not master STD |

---

## 20. Conclusion

The NSSF ERP tender is a strong calibration fixture because it exercises the hard parts of the IT STD Engine:

1. Highly structured IT requirements.
2. Product and platform specificity requiring governance review.
3. Phased implementation under a single contract.
4. Technical scoring plus qualification gates.
5. Contract carry-forward for acceptance, warranty, SLA, IP, escrow, and performance security.
6. Real-world compression of official STD forms and clauses.
7. Price schedule simplification compared with official STD expectations.

The generalized STD Engine design remains valid. The key adjustment is not architectural. The key adjustment is stricter validation and governance around real-world deviations.

The next implementation artifact should be:

**IT Tender Configuration Wizard PRD**

That PRD should be based on the official IT STD package and informed by the NSSF ERP calibration findings, especially around requirement composition, platform-specific justifications, system inventory linkage, evaluation setup, and contract carry-forward.

---

## 21. Recommended Next Artifact

Create:

```text
STD_IT_Tender_Configuration_Wizard_PRD.md
```

The PRD should define:

1. Wizard user roles.
2. Wizard state model.
3. Tab-by-tab UI requirements.
4. Parameter binding behavior.
5. Requirements composer UX.
6. Evaluation builder UX.
7. Price schedule UX.
8. System inventory UX.
9. Contract carry-forward UX.
10. Validation warning/blocker model.
11. Review and approval workflow.
12. Tender bundle preview behavior.
13. Publication and addendum behavior.
14. NSSF ERP fixture acceptance tests.

