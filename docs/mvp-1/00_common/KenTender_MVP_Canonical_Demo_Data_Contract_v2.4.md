# KenTender MVP Canonical Demo Data Contract

**Fixture bundle:** `KENTENDER_MVP_V1`  
**Status:** Living contract — approved baseline for implementation  
**Version:** 2.4  
**Supersedes:** Version 2.3 and all Ministry-specific seed contracts  
**Compatibility:** Compatible fixture correction of version 2.3; legacy ownership fields remain prohibited  
**Fixture clock:** `2027-11-05T12:00:00+03:00`  
**Primary story:** Ministry of Health  
**Secondary entity:** County Government of Kisumu  
**Current module coverage:** Strategy Alignment, Budget & Funding, Demands and Procurement Planning

## 1. Purpose

This document defines the single repeatable cross-entity dataset used to develop, test and demonstrate KenTender MVP 1. It is the only current canonical seed-data contract.

Any earlier Ministry-specific ownership or single-entity contract is obsolete and shall not be used for implementation or planning.

It exists to ensure that every module extends one coherent procurement story instead of creating isolated page mocks or conflicting seed records.

Module requirements remain authoritative for business behaviour. This document is authoritative for shared fixture identities, dates, ownership, relationships and values. When a module needs new demo data, update this contract before changing the seed script.

## 2. Story in one paragraph

The Ministry of Health adopts a 2026–2030 strategic plan to improve the reliability of digital clinical services and strengthen health-workforce capability. The State Department for Medical Services, through the Directorate of Digital Health and Policy, owns the principal infrastructure outcome and receives KES 480 million in the FY 2027/28 procurement budget. An approved KES 455 million Demand reserves that funding and becomes an Active Plan Item in Approved Plan Version 1; its existing Tender later converts KES 310 million into a contract commitment, leaving KES 145 million reserved. A second Ministry Demand for technical-staff certification starts Returned after a KES 15 million funding shortfall. The Planning scenario corrects it to KES 80 million and adds it as a Proposed Plan Item through Draft Revision 2 while Approved Version 1 remains operational. A KES 180 million finance expenditure snapshot is stale and requires attention. Strategy performance moves from 99.82% availability in September 2027 to 99.96% in October after a verified corrective action. Separately, the County Government of Kisumu owns a minimal county-health strategy, a KES 24 million cold-chain Budget Line and a Draft Demand that has not yet been enriched with Strategy or funding. Unit-scoped users maintain only their own data, entity-level reviewers see their authorised consolidated position, and no user receives cross-entity access by default.

The system may show that procurement supports strategic outcomes. It must not claim that expenditure alone caused a performance result.

## 3. Fixture principles

The fixture shall be:

- deterministic and idempotent;
- safe to rerun in development, test and demo environments;
- unavailable in production unless explicitly enabled for a controlled demonstration;
- owned by the fixture namespace `KENTENDER_MVP_V1`;
- resettable without deleting unrelated records;
- free of random identities, amounts and dates;
- loaded in dependency order;
- shared across modules and browser tests;
- validated after every run;
- extended through this document rather than page-specific seed logic.

Stable fixture references are not user-maintained production codes. Production references remain generated server-side.

## 4. Organisation and data ownership

The canonical structure follows `KenTender_Procuring_Entity_and_Organisation_Scope_Model.md`.

### 4.1 Procuring entities

| Reference | Legal name | Entity type | Fixture depth | Purpose |
|---|---|---|---|---|
| `PE-MOH` | Ministry of Health | Ministry | Full | Principal end-to-end procurement story |
| `PE-CGKIS` | County Government of Kisumu | County Government | Minimal | Proves that the architecture is not Ministry-specific |

Neither entity is the organisational parent of the other. Cross-entity strategy alignment, when required, uses an explicit Strategic Framework assignment rather than an organisation hierarchy.

### 4.2 Organisation unit types

| Type reference | Display label | Used by |
|---|---|---|
| `OUT-STATE-DEPT` | State Department | `PE-MOH` |
| `OUT-DIRECTORATE` | Directorate | `PE-MOH` |
| `OUT-COUNTY-DEPT` | County Department | `PE-CGKIS` |

Unit types are fixture configuration. They are not dedicated schema fields.

### 4.3 Ministry of Health organisation units

| Organisation unit | Parent | Unit type | Name | Fixture depth | Purpose |
|---|---|---|---|---|---|
| `MOH-SDMS` | — | State Department | State Department for Medical Services | Full | Principal digital-health procurement story |
| `MOH-DIR-DHP` | `MOH-SDMS` | Directorate | Directorate of Digital Health and Policy | Full | Owns the principal Strategy, Budget and downstream records |
| `MOH-SDPHPS` | — | State Department | State Department for Public Health and Professional Standards | Minimal | Proves ownership isolation within one entity |
| `MOH-DIR-HRMD` | `MOH-SDPHPS` | Directorate | Human Resources Management and Development | Minimal | Owns the workforce-capability target and Budget line |

The State Department names reflect the Ministry's published structure. The operational ownership units are fixture simplifications and must not be presented as a complete official organisation chart.

### 4.4 County Government of Kisumu organisation unit

| Organisation unit | Parent | Unit type | Name | Fixture depth | Purpose |
|---|---|---|---|---|---|
| `CGK-DEPT-HEALTH` | — | County Department | Medical Services, Public Health and Sanitation | Minimal | Owns the county-health Strategy and Budget line |

The organisation-unit name reflects the County Government's published naming. The Strategy and Budget values below are deterministic demonstration data, not claims about the County's official approved plans or allocations.

### 4.5 Ownership rules

1. Every owned Strategy node, measurement, Budget line and future downstream record shall carry `procuring_entity` and optional `owner_org_unit`.
2. `owner_org_unit`, when present, must belong to `procuring_entity`.
3. Entity-owned headers may have no `owner_org_unit`; their lines and children may retain unit ownership.
4. A unit-scoped officer may create, edit and submit records owned by their assigned unit and permitted descendants only.
5. A unit-scoped officer shall not read protected Draft records or mutate records owned by an unrelated unit.
6. Entity-level reviewers and authorities may act across assigned units, subject to role and segregation-of-duties controls.
7. Read-only management views may aggregate authorised unit data without transferring ownership.
8. No user receives cross-entity access by default.
9. Organisational ownership shall be enforced server-side. Filtering or hiding controls in the UI is insufficient.
10. Downstream records inherit the originating entity and organisation unit unless an authorised transfer is explicitly recorded.
11. Demand creation uses explicit active Demand Requester assignment pairs. A user with several pairs must choose one; Administrator status, assignment order and current list filters shall not supply a default.

### 4.6 Seeded access profiles

Use the repository's shared test-user and credential mechanism. Do not hardcode passwords in this contract or production code.

| Fixture user | Scope | Purpose |
|---|---|---|
| `moh.medicalservices.officer@example.test` | `PE-MOH` / `MOH-DIR-DHP` | Maintains the principal digital-health data |
| `moh.publichealth.officer@example.test` | `PE-MOH` / `MOH-DIR-HRMD` | Maintains the minimal workforce-development data |
| `moh.strategy.reviewer@example.test` | `PE-MOH`, all assigned units | Reviews Strategy submissions |
| `moh.budget.reviewer@example.test` | `PE-MOH`, all assigned units | Reviews Budget submissions and revisions |
| `moh.budget.authority@example.test` | `PE-MOH`, all assigned units | Activates Budgets and applies approved revisions |
| `moh.business.approver@example.test` | `PE-MOH`, assigned Ministry units | James Mwangi — supports, returns or rejects assigned business needs |
| `moh.procurement.authority@example.test` | `PE-MOH`, assigned Ministry units | Grace Wanjiku — performs Procurement enrichment and final Demand approval |
| `moh.budget.officer@example.test` | `PE-MOH`, assigned Ministry units | Peter Otieno — confirms every Demand funding assignment and resolves exceptions |
| `moh.planning.officer@example.test` | `PE-MOH`, assigned Ministry units | Mercy Kilonzo — prepares the consolidated Plan and Plan Items |
| `moh.planning.reviewer@example.test` | `PE-MOH`, all assigned units | David Kiptoo — performs professional Planning review and recommendation |
| `moh.accounting.officer@example.test` | `PE-MOH`, entity scope | Josephine Mburu — performs the configured Accounting Officer Planning action |
| `moh.plan.approver@example.test` | `PE-MOH`, entity scope | Performs the configured final annual-plan approval action |
| `moh.tender.initiator@example.test` | `PE-MOH`, assigned Ministry units | Starts Tender preparation from Active Plan Items |
| `moh.viewer@example.test` | `PE-MOH`, read-only Active data | Demonstrates consolidated entity access |
| `kisumu.health.officer@example.test` | `PE-CGKIS` / `CGK-DEPT-HEALTH` | Maintains the minimal county-health data and proves cross-entity denial |
| `kisumu.viewer@example.test` | `PE-CGKIS`, read-only Active data | Demonstrates county-level management access |
| `kentender.multiscope.admin@example.test` | Explicit Demand Requester assignments for `PE-MOH` / `MOH-DIR-DHP` and `PE-CGKIS` / `CGK-DEPT-HEALTH`; System Administrator role | Demonstrates explicit multi-entity creation selection; administration alone grants neither pair |
| `kentender.system.admin@example.test` | No operational Demand Requester assignment; System Administrator role only | Proves that administration does not authorise Demand creation or supply a fallback owner |

The multi-scope fixture is a deliberate exception created through two explicit operational assignments. It does not weaken the default cross-entity isolation rule.

## 5. Canonical Strategy data

### 5.1 Ministry of Health Strategic Plan

| Field | Value |
|---|---|
| Reference | `MOH-SP-2026-2030` |
| Title | Ministry of Health Strategic Plan 2026–2030 |
| Version | 1 |
| Period | 1 July 2026–30 June 2030 |
| Status | Active |
| Procuring Entity | `PE-MOH` |
| Owner Organisation Unit | Entity-owned — none |

Strategy scope assignments:

| Strategy scope | Assigned organisation unit | Include descendants | Applicability |
|---|---|---|---|
| Digital-health programme and related targets | `MOH-SDMS` | Yes | Required |
| Workforce-capability sub-programme and related targets | `MOH-SDPHPS` | Yes | Required |

### 5.2 Medical Services — Digital Health and Policy hierarchy

| Type | Reference | Name | Owner |
|---|---|---|---|
| Programme | `MOH-PROG-DH` | Digital Health Services | `MOH-DIR-DHP` |
| Sub-programme | `MOH-SUB-HIS` | Health Information Systems | `MOH-DIR-DHP` |
| Outcome | `MOH-OUT-RELIABILITY` | Reliable and accessible digital clinical services | `MOH-DIR-DHP` |
| Indicator | `MOH-IND-AVAIL-01` | Availability of core clinical information systems | `MOH-DIR-DHP` |
| Target | `MOH-TGT-AVAIL-2028` | At least 99.9% annual availability by 30 June 2028 | `MOH-DIR-DHP` |
| Indicator | `MOH-IND-RESTORE-01` | Average restoration time for critical services | `MOH-DIR-DHP` |
| Target | `MOH-TGT-RESTORE-2028` | Restore critical services within four hours by 30 June 2028 | `MOH-DIR-DHP` |

Baselines:

- Availability: 97.8% as at 30 June 2026.
- Average critical-service restoration time: 11.5 hours as at 30 June 2026.

Availability is measured monthly from an approved infrastructure-monitoring report. The restoration-time target is included to support Strategy linkage and Budget context; detailed measurement history is not required in the initial fixture.

### 5.3 Public Health and Professional Standards — workforce capability hierarchy

This is deliberately minimal but structurally complete.

| Type | Reference | Name | Owner |
|---|---|---|---|
| Sub-programme | `MOH-SUB-DHC` | Digital Health Workforce Capability | `MOH-DIR-HRMD` |
| Outcome | `MOH-OUT-CAPABILITY` | Sustainable digital-health workforce capability | `MOH-DIR-HRMD` |
| Indicator | `MOH-IND-SKILLS-01` | Number of trained and certified digital-health technical staff | `MOH-DIR-HRMD` |
| Target | `MOH-TGT-SKILLS-2029` | Train and certify 150 digital-health technical staff by 30 June 2029 | `MOH-DIR-HRMD` |

Baseline: 35 trained and certified staff as at 30 June 2026.

### 5.4 Successor targets for the Draft FY 2028/29 Budget

The Draft FY 2028/29 Budget shall not reference targets whose period ended on 30 June 2028.

| Reference | Target | Owner |
|---|---|---|
| `MOH-TGT-AVAIL-2029` | Maintain at least 99.95% annual availability by 30 June 2029 | `MOH-DIR-DHP` |
| `MOH-TGT-RESTORE-2029` | Restore critical services within two hours by 30 June 2029 | `MOH-DIR-DHP` |
| `MOH-TGT-SKILLS-2030` | Train and certify 220 digital-health technical staff by 30 June 2030 | `MOH-DIR-HRMD` |

### 5.5 Public Value Objectives

| PVO reference | Pillar | Objective |
|---|---|---|
| `PVO-EFT-01` | Strategic and service outcomes | Improve availability of critical health services |
| `PVO-ECO-01` | Economy and whole-life value | Reduce whole-life infrastructure cost |
| `PVO-EFY-01` | Process efficiency | Reduce implementation and service-restoration time |
| `PVO-RES-01` | Contract performance and resilience | Improve continuity of critical services |
| `PVO-LOC-01` | Inclusion and economic development | Develop internal and local technical capability |
| `PVO-SUS-01` | Sustainability and asset stewardship | Reduce infrastructure energy consumption |
| `PVO-SUS-02` | Sustainability and asset stewardship | Ensure compliant handling of replaced ICT equipment |
| `PVO-INT-01` | Integrity and accountability | Minimise uncontrolled contract changes |

### 5.6 Plan Value Commitments

Plan Value Commitments are separate records that adopt catalogue PVOs into the Active Plan. Budget and downstream modules reference the commitment identity, not the PVO identity alone.

| Commitment reference | PVO | Consideration | Principal applicability |
|---|---|---|---|
| `MOH-PVC-EFT-01` | `PVO-EFT-01` | Required | Critical health-service procurements |
| `MOH-PVC-ECO-01` | `PVO-ECO-01` | Required | Infrastructure and material whole-life-cost procurements |
| `MOH-PVC-EFY-01` | `PVO-EFY-01` | Recommended | Implementation and service-restoration procurements |
| `MOH-PVC-RES-01` | `PVO-RES-01` | Recommended | Critical or continuity-dependent services |
| `MOH-PVC-LOC-01` | `PVO-LOC-01` | Required | Training and capability-development procurements |
| `MOH-PVC-SUS-01` | `PVO-SUS-01` | Recommended | Energy-consuming infrastructure or equipment |
| `MOH-PVC-SUS-02` | `PVO-SUS-02` | Required | Procurements replacing or disposing of ICT assets |
| `MOH-PVC-INT-01` | `PVO-INT-01` | Required | Material contracts with controlled variation exposure |

Applicability shall be resolved from structured context. An Organisation Unit may not modify the catalogue objective through its funding treatment.

### 5.7 Strategy measurements

| Period | Indicator | Actual | Workflow | Result |
|---|---|---:|---|---|
| September 2027 | `MOH-IND-AVAIL-01` | 99.82% | Submitted, then Verified | At risk |
| October 2027 | `MOH-IND-AVAIL-01` | 99.96% | Submitted, then Verified | On track |

Corrective action: resolve storage-controller instability. Status: Completed and verified. Owner: `PE-MOH` / `MOH-DIR-DHP`.

These are illustrative management values, not statutory thresholds.

### 5.8 County Government of Kisumu Strategy data

This is deliberately minimal. It proves a different Procuring Entity type and a one-level organisation hierarchy without creating a second full procurement story.

| Field | Value |
|---|---|
| Reference | `CGK-SP-HEALTH-2027-2028` |
| Title | Kisumu County Health Services Operational Plan FY 2027/28 |
| Version | 1 |
| Period | 1 July 2027–30 June 2028 |
| Status | Active |
| Procuring Entity | `PE-CGKIS` |
| Owner Organisation Unit | `CGK-DEPT-HEALTH` |

The Plan title and content are fixture data written in a realistic public-sector form. They shall not be presented as an official County Government publication.

| Type | Reference | Name | Owner |
|---|---|---|---|
| Outcome | `CGK-OUT-COLDCHAIN` | Reliable vaccine cold-chain services at county health facilities | `CGK-DEPT-HEALTH` |
| Indicator | `CGK-IND-COLDCHAIN-01` | Percentage of supported facilities meeting the cold-chain uptime standard | `CGK-DEPT-HEALTH` |
| Target | `CGK-TGT-COLDCHAIN-2028` | At least 95% of supported facilities meet the uptime standard by 30 June 2028 | `CGK-DEPT-HEALTH` |

Baseline: 82% as at 30 June 2027.

### 5.9 County Strategy scope and value commitments

| Strategy scope | Assigned organisation unit | Include descendants | Applicability |
|---|---|---|---|
| Cold-chain outcome, indicator and target | `CGK-DEPT-HEALTH` | Yes | Required |

| Commitment reference | PVO | Consideration | Principal applicability |
|---|---|---|---|
| `CGK-PVC-EFT-01` | `PVO-EFT-01` | Required | Equipment supporting essential county health services |
| `CGK-PVC-ECO-01` | `PVO-ECO-01` | Required | Whole-life equipment and maintenance cost |
| `CGK-PVC-SUS-01` | `PVO-SUS-01` | Recommended | Energy-consuming cold-chain equipment |

The County adopts catalogue PVOs through its own Plan Value Commitments. It does not reuse or mutate the Ministry's Plan Value Commitments.

## 6. Canonical Budget data

### 6.1 Active FY 2027/28 Budget

| Field | Value |
|---|---|
| Reference | `MOH-BUD-2027-2028` |
| Title | Ministry of Health Procurement Budget FY 2027/28 |
| Registration source | Direct capture |
| External approval reference | `MOH-FIN-BUD-2027-01` |
| Currency | KES |
| Status | Active |
| Approved total | KES 560,000,000 |

The Budget header is owned by `PE-MOH`. Its lines retain Organisation Unit ownership.

### 6.2 Medical Services — Digital Health and Policy line

| Field | Value |
|---|---|
| Reference | `MOH-BL-DHI-2027` |
| Title | Digital clinical systems infrastructure |
| Procuring Entity | `PE-MOH` |
| Owner Organisation Unit | `MOH-DIR-DHP` |
| Approved | KES 480,000,000 |
| Remaining reserved | KES 145,000,000 |
| Committed | KES 310,000,000 |
| Available | KES 25,000,000 |
| Actual expenditure | KES 180,000,000 |
| Primary target | `MOH-TGT-AVAIL-2028` |
| Supporting target | `MOH-TGT-RESTORE-2028` |

Funding treatments:

| Plan Value Commitment | Treatment | Amount/rationale |
|---|---|---|
| `MOH-PVC-EFT-01` | Embedded in line | Infrastructure supports reliable critical health services |
| `MOH-PVC-ECO-01` | Dedicated allocation | KES 40,000,000 for whole-life costing, energy efficiency and lifecycle optimisation |
| `MOH-PVC-RES-01` | Embedded in line | Redundancy, continuity and support requirements are included |
| `MOH-PVC-SUS-02` | No direct allocation required | Disposal cost is included in funded asset-replacement activities |

### 6.3 Public Health and Professional Standards — workforce capability line

This line proves that a second Organisation Unit owns data within the same Ministry Budget.

| Field | Value |
|---|---|
| Reference | `MOH-BL-HWD-2027` |
| Title | Digital Health Workforce Capacity Development |
| Procuring Entity | `PE-MOH` |
| Owner Organisation Unit | `MOH-DIR-HRMD` |
| Approved | KES 80,000,000 |
| Reserved | KES 0 |
| Committed | KES 0 |
| Available | KES 80,000,000 |
| Actual expenditure | Unknown |
| Primary target | `MOH-TGT-SKILLS-2029` |

Funding treatments:

| Plan Value Commitment | Treatment | Amount/rationale |
|---|---|---|
| `MOH-PVC-LOC-01` | Embedded in line | Training and certification build internal technical capability |
| `MOH-PVC-EFT-01` | Embedded in line | Capability supports continuity of digital clinical services |
| `MOH-PVC-ECO-01` | Embedded in line | Training and certification costs are included in the line amount |
| `MOH-PVC-RES-01` | Embedded in line | Continuity capability is included in the training programme |

`MOH-PVC-SUS-02` shall not be returned as applicable because this line does not acquire, replace or dispose of physical assets.

### 6.4 Derived Active Budget totals

| Measure | Amount |
|---|---:|
| Approved | KES 560,000,000 |
| Remaining reserved | KES 145,000,000 |
| Committed | KES 310,000,000 |
| Available | KES 105,000,000 |
| Actual expenditure | KES 180,000,000 |
| Outstanding commitment | KES 130,000,000 |

Actual expenditure is utilisation of the commitment and shall not be deducted again when calculating Available.

### 6.5 Draft FY 2028/29 Budget

| Field | Value |
|---|---|
| Reference | `MOH-BUD-2028-2029` |
| Title | Ministry of Health Procurement Budget FY 2028/29 |
| External approval reference | `MOH-FIN-BUD-2028-01` |
| Status | Draft |
| External approved total | KES 600,000,000 |

| Line | Owner | Approved | Primary target |
|---|---|---:|---|
| `MOH-BL-DHI-2028` — Digital clinical systems infrastructure | `MOH-DIR-DHP` | KES 480,000,000 | `MOH-TGT-AVAIL-2029` |
| `MOH-BL-HWD-2028` — Digital-health workforce capability | `MOH-DIR-HRMD` | KES 120,000,000 | `MOH-TGT-SKILLS-2030` |

The infrastructure line may use `MOH-TGT-RESTORE-2029` as a supporting target. Treatments follow the applicable FY 2028/29 Strategy context and must be independently stored, not copied by reference from the prior Budget.

### 6.6 Closed FY 2026/27 Budget

| Field | Value |
|---|---|
| Reference | `MOH-BUD-2026-2027` |
| Status | Closed |
| Approved | KES 520,000,000 |
| Open reservations | None |

Only the minimum data required for portfolio and status filtering is necessary.

### 6.7 County Government of Kisumu Active FY 2027/28 Budget

| Field | Value |
|---|---|
| Reference | `CGK-BUD-2027-2028` |
| Title | County Government of Kisumu Procurement Budget FY 2027/28 |
| Registration source | Direct capture |
| External approval reference | `CGK-FIN-BUD-2027-01` |
| Currency | KES |
| Status | Active |
| Approved total | KES 24,000,000 |
| Procuring Entity | `PE-CGKIS` |

| Field | Value |
|---|---|
| Line reference | `CGK-BL-COLDCHAIN-2027` |
| Title | Solar-powered vaccine refrigerators and temperature monitoring |
| Procuring Entity | `PE-CGKIS` |
| Owner Organisation Unit | `CGK-DEPT-HEALTH` |
| Approved | KES 24,000,000 |
| Reserved | KES 0 |
| Committed | KES 0 |
| Available | KES 24,000,000 |
| Actual expenditure | Unknown |
| Primary target | `CGK-TGT-COLDCHAIN-2028` |

Funding treatments:

| Plan Value Commitment | Treatment | Amount/rationale |
|---|---|---|
| `CGK-PVC-EFT-01` | Embedded in line | Equipment supports reliable vaccine services |
| `CGK-PVC-ECO-01` | Embedded in line | Acquisition, maintenance and operating cost are considered together |
| `CGK-PVC-SUS-01` | Embedded in line | Solar power reduces reliance on unstable grid supply and operating energy |

The county Draft Demand is defined in section 7.3. It has no Strategy assignment, funding allocation, reservation, commitment or expenditure at the Draft stage.

## 7. Canonical Demand and downstream funding story

### 7.1 Principal approved Ministry Demand

| Field | Value |
|---|---|
| Reference | `DMD-MOH-2027-014` |
| Title | National digital health infrastructure upgrade |
| Procuring Entity | `PE-MOH` |
| Owner Organisation Unit | `MOH-DIR-DHP` |
| Requester | Dr Miriam Njeri — `moh.medicalservices.officer@example.test` |
| Business Approver | James Mwangi — `moh.business.approver@example.test` |
| Procurement Approval Authority | Grace Wanjiku — `moh.procurement.authority@example.test` |
| Budget Officer | Peter Otieno — `moh.budget.officer@example.test` |
| Route | Standard |
| Required by | 31 March 2028 |
| Delivery location | National Data Centre and designated health facilities |
| Requester estimate | KES 455,000,000 |
| Confirmed estimate | KES 455,000,000 |
| Currency | KES |
| Procurement category | ICT infrastructure and services |
| Estimate basis | Market research and infrastructure assessment |
| Final status/stage | Approved / Complete |
| Planning readiness | Ready, derived from Approved status |
| Planning usage at the Demands seed boundary | Not taken up |

Need Items:

| Item | Quantity | Unit | Confirmed estimate |
|---|---:|---|---:|
| Resilient compute and storage platform | 1 | Lot | KES 300,000,000 |
| Network, monitoring and implementation services | 1 | Lot | KES 155,000,000 |

Strategy alignment:

| Type | Reference | Reason |
|---|---|---|
| Primary | `MOH-TGT-AVAIL-2028` | The infrastructure directly supports availability of core clinical information systems |
| Supporting | `MOH-TGT-RESTORE-2028` | Resilient infrastructure and monitoring support faster restoration of critical services |

The Demand retains an immutable Strategy snapshot containing the plan/version, complete hierarchy path and human-readable target text.

Public-value treatments:

| Plan Value Commitment | Treatment | Rationale |
|---|---|---|
| `MOH-PVC-EFT-01` | Embedded in specification | Infrastructure supports reliable critical health services |
| `MOH-PVC-ECO-01` | To be determined in Planning | Whole-life costing, energy use and lifecycle optimisation must be resolved during plan preparation |
| `MOH-PVC-RES-01` | Contract obligation | Redundancy, continuity and support requirements must carry forward |
| `MOH-PVC-SUS-02` | Delivery or disposal obligation | Replaced ICT equipment requires controlled end-of-life handling |

Funding and decisions:

| Control | Canonical value |
|---|---|
| Budget Line | `MOH-BL-DHI-2027` |
| Budget Officer-confirmed allocation | KES 455,000,000 |
| Reservation | `RSV-MOH-0001` |
| Business support | James Mwangi — 12 August 2027 |
| Procurement enrichment | Grace Wanjiku — 14 August 2027 |
| Budget confirmation | Peter Otieno — 15 August 2027 |
| Final approval and reservation | Grace Wanjiku — 16 August 2027 |

All decision times shall be fixed values in East Africa Time and preserve this order. Budget confirmation does not create the reservation. Final approval creates or resolves exactly one `RSV-MOH-0001` atomically and idempotently.

### 7.2 Returned Ministry Demand with a funding shortfall

| Field | Value |
|---|---|
| Reference | `DMD-MOH-2027-019` |
| Title | Digital health technical staff certification programme |
| Procuring Entity | `PE-MOH` |
| Owner Organisation Unit | `MOH-DIR-HRMD` |
| Requester/current owner | Anne Achieng — `moh.publichealth.officer@example.test` |
| Route | Standard |
| Required by | 31 December 2027 |
| Confirmed estimate | KES 95,000,000 |
| Currency | KES |
| Primary Strategy target | `MOH-TGT-SKILLS-2029` |
| Relevant Budget Line | `MOH-BL-HWD-2027` |
| Available funding | KES 80,000,000 |
| Funding shortfall | KES 15,000,000 |
| Final status/stage | Returned / Request preparation |

Return reason:

> The proposed scope exceeds available funding by KES 15,000,000. Revise the number of participants or provide a phased delivery approach.

The audit history shall show that Procurement enrichment was completed, the funding exception was detected and the Demand was returned to Anne Achieng. There is no Budget Officer confirmation, reservation, commitment or expenditure. The fixture shall not create negative availability or a funding override.

### 7.3 Minimal County Draft Demand

| Field | Value |
|---|---|
| Reference | `DMD-CGK-2027-006` |
| Title | Solar-powered vaccine refrigerators for rural health facilities |
| Procuring Entity | `PE-CGKIS` |
| Owner Organisation Unit | `CGK-DEPT-HEALTH` |
| Requester | `kisumu.health.officer@example.test` |
| Route | Standard |
| Requester estimate | KES 24,000,000 |
| Currency | KES |
| Status/stage | Draft / Request preparation |
| Strategy assignment | None |
| Budget assignment | None |

This record proves progressive enrichment and cross-entity isolation. The Requester does not select `CGK-TGT-COLDCHAIN-2028` or `CGK-BL-COLDCHAIN-2027`; responsible specialist stages may assign them later.

### 7.4 Downstream continuation of the principal Demand

All current Planning, Tender, Contract and expenditure records below belong to `PE-MOH` / `MOH-DIR-DHP` and extend `DMD-MOH-2027-014`.

| Stage | Reference | Description/amount |
|---|---|---|
| Demand | `DMD-MOH-2027-014` | National digital health infrastructure upgrade — approved KES 455,000,000 |
| Reservation | `RSV-MOH-0001` | Original KES 455,000,000; remaining KES 145,000,000; Partially converted |
| Logical Procurement Plan | `PLN-MOH-2027-001` | Open Ministry FY 2027/28 annual Plan |
| Procurement Plan Version | `PLN-MOH-2027-001-V1` | Current Approved Version 1; value KES 455,000,000 |
| Procurement Plan Item | `PPI-MOH-2027-021` | Active; inherits the reservation and current Approved Plan Item Version |
| Tender | `TND-MOH-2027-008` | Carries and revalidates the same reservation |
| Contract | `CTR-MOH-2027-005` | Commitment KES 310,000,000 |
| Expenditure snapshot | `EXP-MOH-2027-005-01` | KES 180,000,000; Stale |

The reservation identity remains unchanged through Demand, Planning and Tender. The commitment converts part of that reservation:

`KES 455,000,000 original = KES 310,000,000 committed + KES 145,000,000 remaining reserved`

Outstanding commitment:

`KES 310,000,000 commitment − KES 180,000,000 expenditure = KES 130,000,000`

The expenditure snapshot source time shall be derived from the fixed fixture clock and shall exceed the configured freshness threshold. The UI must show Stale rather than zero.

At the base seed boundary, no reservation, Plan Item, Tender or Contract exists for `DMD-MOH-2027-019`, and the related KES 80 million workforce Budget Line remains fully available. `SCN-PLN-ADD-001` changes that state only through the controlled correction and approval sequence in section 7.6. `DMD-CGK-2027-006` has no reservation or downstream records, and the county Budget Line remains fully available.

At a Demands-only seed boundary, `DMD-MOH-2027-014` has Planning usage **Not taken up**. A full canonical bundle run derives its later Planning usage from Active `PPI-MOH-2027-021` and other downstream records. It shall never hardcode or duplicate that usage on the Demand.

### 7.5 Demand-creation scope states

The seed shall support three deterministic creation states without creating extra Demand records:

| User | Eligible Demand Requester pairs | Expected create state |
|---|---|---|
| `moh.medicalservices.officer@example.test` | `PE-MOH` / `MOH-DIR-DHP` | The single pair is visibly preselected and read-only |
| `kentender.multiscope.admin@example.test` | `PE-MOH` / `MOH-DIR-DHP`; `PE-CGKIS` / `CGK-DEPT-HEALTH` | No default; the user must explicitly select one exact pair |
| `kentender.system.admin@example.test` | None | Demand creation is blocked; no Administrator or local-development fallback |

The creator identity remains separate from the selected Demand owner. The multi-scope user may create for either listed pair only; any omitted, mixed or third pair shall be rejected server-side.

### 7.6 Planning status and post-approval addition scenario

Base Planning state:

| Record | State | Meaning |
|---|---|---|
| `PLN-MOH-2027-001` | Open | Stable logical Plan for `PE-MOH`, FY 2027/28 |
| `PLN-MOH-2027-001-V1` | Approved | Current immutable approval baseline |
| `PPI-MOH-2027-021` | Active | Operational item present in Approved Version 1 |
| `PPI-MOH-2027-021` Tender take-up | Tender active | Linked to `TND-MOH-2027-008` |

The deterministic scenario `SCN-PLN-ADD-001` shall then demonstrate adding a common post-approval requirement:

1. `DMD-MOH-2027-019` starts Returned at KES 95,000,000 with a KES 15,000,000 funding shortfall.
2. Anne Achieng reduces the certification scope to KES 80,000,000 and resubmits it through the existing business, Procurement, mandatory Budget Officer and final approval route.
3. Final Demand approval creates `RSV-MOH-0002` for KES 80,000,000 exactly once.
4. Mercy Kilonzo selects **Add Plan Item** on `PLN-MOH-2027-001`.
5. The system creates `PLN-MOH-2027-001-V2` as the single Draft successor and creates Proposed `PPI-MOH-2027-022` for the Digital health technical staff certification programme.
6. Version 1 remains current Approved; `PPI-MOH-2027-021` remains Active and `TND-MOH-2027-008` remains valid.
7. The added Organisation Unit contribution is signed off and the revised consolidated totals, funding and statutory allocations are revalidated.
8. Approval makes Version 2 current Approved, Version 1 Superseded and `PPI-MOH-2027-022` Active.
9. The unchanged `PPI-MOH-2027-021` retains the same stable identity, handoff and Tender linkage.

Draft and Approved Version 2 values:

| Item | Owner | Value | Version 2 treatment |
|---|---|---:|---|
| `PPI-MOH-2027-021` National digital health infrastructure upgrade | `MOH-DIR-DHP` | KES 455,000,000 | Carried forward unchanged |
| `PPI-MOH-2027-022` Digital health technical staff certification programme | `MOH-DIR-HRMD` | KES 80,000,000 | Added; Open tender; single year |
| **Consolidated Plan** | — | **KES 535,000,000** | Revised approval baseline |

The applicable 30% plan-allocation basis becomes KES 160,500,000. The fixture records planned treatment only; it must not present the allocation as an award, expenditure or realised result.

After Demand approval in the scenario, Ministry Budget arithmetic becomes:

`KES 560,000,000 Budget = KES 310,000,000 committed + KES 225,000,000 remaining reserved + KES 25,000,000 available`

Running `SCN-PLN-ADD-001` a second time shall not create another revision, Plan Item, reservation, decision or audit event. Reset returns the bundle to the base Planning state above.

## 8. Seed implementation contract

### 8.1 Orchestration

Provide one repository-conformant documented command that seeds or resets `KENTENDER_MVP_V1`.

The implementation should use one central orchestrator with module-owned seed functions. Module functions must not independently invent or mutate shared fixture values.

### 8.2 Dependency order

1. Procuring entities and Organisation Unit Types
2. Organisation Units
3. Users, roles and User Scope Assignments
4. Public Value Objective catalogue
5. Strategic Plans and versions
6. Strategy hierarchies, indicators and targets
7. Strategy Scope Assignments
8. Plan Value Commitments and applicability
9. Strategy measurements and corrective action
10. Budget headers
11. Budget lines, Strategy references and funding treatments
12. Demand and reservation
13. Logical Procurement Plan and Approved Version 1
14. Stable Plan Item, Plan Item Version and Demand Allocations
15. Departmental submissions, Planning decisions and publication evidence
16. Planning handoff and Tender
17. Contract and commitment
18. Expenditure snapshot
19. Audit and lifecycle events

Only implemented modules need live records. Until a downstream module is available, its references may be declared in this contract but shall not be represented by misleading production records.

### 8.3 Reset behaviour

The reset process shall:

- identify exact records through fixture ownership, not broad entity deletion;
- delete fixture records in reverse dependency order;
- preserve unrelated Ministry, county and other-entity records;
- run transactionally where supported;
- fail clearly if a non-fixture record depends on a fixture record;
- recreate the same identities and values;
- leave no duplicate relationships, reservations, commitments or audit events.

### 8.4 Time and freshness

All fixture dates shall derive from `2027-11-05T12:00:00+03:00`. Do not use the runtime current date.

The script shall explicitly configure or reference the finance-source freshness threshold used to classify the seeded snapshot as Stale.

## 9. Required verification report

After seeding, print a concise PASS/FAIL report and return a failing exit status when an invariant fails.

Verify at minimum:

### Identity and repeatability

- fixture namespace is present on every owned record;
- both Procuring Entities resolve once;
- every Organisation Unit belongs to exactly one Procuring Entity;
- every parent Organisation Unit belongs to the same Procuring Entity as its child;
- all canonical references resolve once;
- a second execution creates no duplicates;
- record identities and counts remain unchanged after rerun.

### Strategy

- both Active Plans and versions resolve correctly;
- every target has a valid hierarchy, Procuring Entity and owning Organisation Unit;
- Strategy Scope Assignments return the correct items for each permitted unit;
- Ministry Strategy items are not returned to the county merely because they share a health subject;
- every Budget target exists and is valid for the Budget period;
- Plan Value Commitments reference active catalogue objectives;
- applicability returns the correct commitments for infrastructure and training contexts.

### Budget

- lines total KES 560,000,000;
- remaining reservations total KES 145,000,000;
- commitments total KES 310,000,000;
- Available totals KES 105,000,000;
- Actual Expenditure is not double-counted;
- Required applicable commitments have complete treatments;
- the Draft FY 2028/29 Budget uses valid successor targets;
- the county Budget totals KES 24,000,000 and remains fully available;
- the county line references only its assigned Strategy target and county Plan Value Commitments.

### Demands

- all three Demand references resolve exactly once;
- `DMD-MOH-2027-014` Need Items, confirmed estimate, allocation and original reservation each total KES 455,000,000;
- `DMD-MOH-2027-014` references `MOH-TGT-AVAIL-2028`, `MOH-TGT-RESTORE-2028`, `MOH-BL-DHI-2027` and exactly one `RSV-MOH-0001`;
- the principal Demand contains ordered Business, Procurement, Budget and Final approval decisions by the named actors;
- at the base boundary, `DMD-MOH-2027-019` has a KES 15,000,000 funding shortfall, a preserved return reason and no confirmation or reservation;
- `DMD-CGK-2027-006` is Draft and has no Strategy target, Budget Line, funding allocation or reservation;
- the Requester accounts cannot mutate specialist Strategy, value-treatment or funding fields;
- the Budget Officer is required for routine and exception funding assignments;
- a Demands-only seed run shows the principal Demand as Not taken up; a full bundle derives downstream usage from actual Planning records;
- rerunning the seed creates no duplicate Demands, decisions, allocations, exceptions, reservations or audit events.
- the single-scope Requester resolves exactly one visible creation pair;
- the multi-scope Administrator resolves exactly two eligible Demand Requester pairs and no default pair;
- the no-scope Administrator resolves no eligible creation pair and cannot create a Demand;
- an omitted, mixed or unauthorised PE/OU pair is rejected server-side.

### Procurement Planning

- `PLN-MOH-2027-001` resolves once as the Open logical FY 2027/28 Plan;
- Version 1 resolves once as the current Approved immutable baseline;
- `PPI-MOH-2027-021` is Active, totals KES 455,000,000 and retains `RSV-MOH-0001` and `TND-MOH-2027-008` lineage;
- the logical Plan can hold one current Approved version and at most one open Draft successor;
- before `SCN-PLN-ADD-001`, `DMD-MOH-2027-019` is ineligible for Planning;
- the scenario creates or resolves exactly one `RSV-MOH-0002`, Draft Version 2 and Proposed `PPI-MOH-2027-022`;
- while Version 2 is Draft, Version 1 remains current Approved and `PPI-MOH-2027-021` remains operational;
- Draft Version 2 totals KES 535,000,000 and recalculates the 30% allocation basis to KES 160,500,000;
- after Demand approval in the scenario, Ministry Budget totals reconcile to KES 310,000,000 committed, KES 225,000,000 remaining reserved and KES 25,000,000 available;
- Proposed `PPI-MOH-2027-022` cannot be taken up by Tender Management;
- approving Version 2 makes it current Approved, makes Version 1 Superseded and activates `PPI-MOH-2027-022`;
- supersession does not alter the existing handoff or Tender link for unchanged `PPI-MOH-2027-021`;
- rerunning the scenario creates no duplicate version, item, allocation, reservation, decision, handoff or audit event; and
- resetting the scenario restores the base Planning state without deleting unrelated fixture data.

### Organisation ownership and isolation

- the Medical Services officer may maintain Draft records owned by `PE-MOH` / `MOH-DIR-DHP`;
- the Medical Services officer cannot read protected `MOH-DIR-HRMD` Draft data or mutate its records;
- the Public Health and Professional Standards officer may maintain Draft records owned by `PE-MOH` / `MOH-DIR-HRMD`;
- the Public Health and Professional Standards officer cannot read protected `MOH-DIR-DHP` Draft data or mutate its records;
- Ministry reviewers and authorities can access assigned data across both Ministry branches;
- the Ministry viewer receives only authorised read-only consolidated Ministry information;
- the Kisumu health officer may maintain Draft records owned by `PE-CGKIS` / `CGK-DEPT-HEALTH`;
- the Kisumu viewer receives only authorised read-only county information;
- Ministry users cannot access county records and county users cannot access Ministry records through either UI or API.
- the Medical Services Requester can access `DMD-MOH-2027-014` but not the protected County Draft;
- the Public Health and Professional Standards Requester can correct `DMD-MOH-2027-019` but cannot mutate `DMD-MOH-2027-014`;
- the Kisumu health officer can maintain `DMD-CGK-2027-006` but cannot read or mutate either Ministry Demand.

### Downstream lifecycle

- one reservation identity links Demand, Planning and Tender;
- reservation and commitment are not double-counted;
- original reservation equals converted plus remaining reservation;
- expenditure is read-only and linked to the commitment;
- stale finance data is never displayed as zero;
- all Ministry lifecycle records retain `PE-MOH` and `MOH-DIR-DHP` ownership.

## 10. Demonstration path

1. Sign in as `kentender.multiscope.admin@example.test`, start Create demand and show that no Procuring Entity / Organisation Unit pair is silently selected; choose the Ministry pair explicitly.
2. Sign in as Dr Miriam Njeri and show her single authorised ownership pair, then show that Request preparation asks for the business need but not Strategy, Budget, Planning or procurement-method codes.
3. Trace `DMD-MOH-2027-014` through Business support, Procurement Strategy assignment, mandatory Budget Officer confirmation and final approval/reservation.
4. Open the approved Demand and trace `MOH-TGT-AVAIL-2028`, the value treatments, `MOH-BL-DHI-2027` and `RSV-MOH-0001`.
5. Open `DMD-MOH-2027-019` and show the KES 15 million shortfall, named correction owner and controlled return without a reservation.
6. Open the consolidated Ministry Budget and show the principal infrastructure line and the separate workforce-capability line owned by different Organisation Units.
7. Open `PLN-MOH-2027-001` and show Approved Version 1, Active `PPI-MOH-2027-021` and the existing Tender take-up.
8. Run `SCN-PLN-ADD-001`: correct and approve `DMD-MOH-2027-019`, then select Add Plan Item on the Approved Plan.
9. Show Draft Version 2 and Proposed `PPI-MOH-2027-022` while Version 1 and `TND-MOH-2027-008` remain operational.
10. Approve Version 2 and show Version 1 Superseded, both Plan Items Active and unchanged Tender lineage preserved.
11. Trace the principal reservation into Tender, the KES 310 million commitment and the stale KES 180 million expenditure snapshot.
12. Open Strategy Performance and show September At risk, the verified corrective action and October On track.
13. Sign in as the Kisumu health officer and show `DMD-CGK-2027-006` as a county-owned Draft without Strategy or Budget assignment.
14. Attempt to open a Ministry Demand from the county account and show that access is denied.
15. Sign in as `kentender.system.admin@example.test` and show that Demand creation is blocked because no operational Requester assignment exists.
16. Explain that the same KenTender ownership model supports different public-entity structures without hardcoded hierarchy levels.

## 11. Extension rules for subsequent modules

When Planning, Tender, Evaluation, Award, Contract, Stores, Assets, Disposal or Analytics is added or extended:

1. Extend the same narrative and identifiers where the business lifecycle continues.
2. Add only the smallest data needed to demonstrate the new module's value and exceptions.
3. Assign every owned record to the correct `procuring_entity` and optional `owner_org_unit`.
4. Preserve upstream identities rather than creating look-alike records.
5. Add the new invariants to the verification report.
6. Update the version and change log below before changing the script.

## 12. Change log

| Version | Date | Modules | Change |
|---|---|---|---|
| 1.0 | 6 August 2026 | Strategy Alignment; Budget & Funding | Established the canonical Ministry story and reconciled Strategy/Budget references |
| 1.1 | 6 August 2026 | Strategy Alignment; Budget & Funding | Replaced illustrative department names with the State Department for Medical Services and the State Department for Public Health and Professional Standards, with realistic operational ownership functions |
| 2.0 | 6 August 2026 | Cross-module foundation; Strategy Alignment; Budget & Funding | Breaking replacement of Ministry-specific ownership with generic Procuring Entity and Organisation Unit scope; added explicit Strategy Scope Assignments and a minimal County Government of Kisumu fixture |
| 2.1 | 7 August 2026 | Demands | Added the principal approved Ministry Demand, a returned Ministry funding-shortfall Demand, a minimal County Draft Demand, named Demand actors, lifecycle decisions and Demand-specific repeatability and isolation invariants |
| 2.2 | 7 August 2026 | Demands; access scope | Added deterministic zero-, single- and multi-scope Demand-creation fixtures; prohibited assignment-order, workspace-filter and Administrator ownership fallbacks; added verification and demonstration steps |
| 2.3 | 8 August 2026 | Procurement Planning | Added the logical Plan, version and stable Plan Item model; Approved Version 1 baseline; deterministic post-approval Plan Item addition through Draft Revision 2; Planning actors, status invariants and preserved Tender lineage |
| 2.4 | 9 August 2026 | Demands; Procurement Planning | Corrected the principal Demand required-by date to 31 March 2028 so the approved need and planned delivery schedule reconcile; clarified downstream design-field semantics without changing fixture identities or amounts |
