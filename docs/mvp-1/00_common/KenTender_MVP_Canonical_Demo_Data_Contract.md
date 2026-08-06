# KenTender MVP Canonical Demo Data Contract

**Fixture bundle:** `MOH_MVP_V1`  
**Status:** Living contract — approved baseline for implementation  
**Version:** 1.1  
**Fixture clock:** `2027-11-03T12:00:00+03:00`  
**Primary entity:** Ministry of Health  
**Current module coverage:** Strategy Alignment and Budget & Funding

## 1. Purpose

This document defines the single repeatable Ministry of Health dataset used to develop, test and demonstrate KenTender MVP 1.

It exists to ensure that every module extends one coherent procurement story instead of creating isolated page mocks or conflicting seed records.

Module requirements remain authoritative for business behaviour. This document is authoritative for shared fixture identities, dates, ownership, relationships and values. When a module needs new demo data, update this contract before changing the seed script.

## 2. Story in one paragraph

The Ministry of Health adopts a 2026–2030 strategic plan to improve the reliability of digital clinical services and strengthen health-workforce capability. The State Department for Medical Services, through the Directorate of Digital Health and Policy, owns the principal infrastructure outcome and receives KES 480 million in the FY 2027/28 procurement budget. An approved KES 455 million demand reserves that funding; KES 310 million is later converted into a contract commitment, leaving KES 145 million reserved. A KES 180 million finance expenditure snapshot is stale and requires attention. Strategy performance moves from 99.82% availability in September 2027 to 99.96% in October after a verified corrective action. The State Department for Public Health and Professional Standards, through its human-resources management and development function, owns a smaller capability target and an uncommitted KES 80 million Budget line. State-department users maintain only their own records, while authorised Ministry-level reviewers and authorities see the consolidated position.

The system may show that procurement supports strategic outcomes. It must not claim that expenditure alone caused a performance result.

## 3. Fixture principles

The fixture shall be:

- deterministic and idempotent;
- safe to rerun in development, test and demo environments;
- unavailable in production unless explicitly enabled for a controlled demonstration;
- owned by the fixture namespace `MOH_MVP_V1`;
- resettable without deleting unrelated records;
- free of random identities, amounts and dates;
- loaded in dependency order;
- shared across modules and browser tests;
- validated after every run;
- extended through this document rather than page-specific seed logic.

Stable fixture references are not user-maintained production codes. Production references remain generated server-side.

## 4. Organisation and data ownership

### 4.1 Procuring entity

| Reference | Name |
|---|---|
| `PE-MOH` | Ministry of Health |

### 4.2 State Departments and operational directorates

| Ownership reference | State Department | Operational directorate/function | Fixture depth | Purpose |
|---|---|---|---|---|
| `MOH-SDMS` | State Department for Medical Services | `MOH-DIR-DHP` — Directorate of Digital Health and Policy | Full | Principal end-to-end digital-health procurement story |
| `MOH-SDPHPS` | State Department for Public Health and Professional Standards | `MOH-DIR-HRMD` — Human Resources Management and Development | Minimal | Proves organisational ownership and isolation |

The two State Department names reflect the Ministry's published structure. The operational ownership references are fixture simplifications and must not be presented as a complete official Ministry organisation chart.

### 4.3 Ownership rules

1. Every owned Strategy node, measurement, Budget line and future downstream record shall carry `entity`, `owner_state_department` and, where applicable, `owner_directorate`.
2. A State Department officer may create, edit and submit records owned by their assigned State Department only.
3. A State Department officer shall not read protected Draft records or mutate records owned by another State Department.
4. Ministry-level Strategy and Budget reviewers may view and review all assigned State Departments.
5. Ministry-level authorities may activate or apply records across assigned State Departments, subject to segregation of duties.
6. Read-only management views may aggregate authorised State Department data without transferring ownership.
7. Organisational ownership shall be enforced server-side. Filtering or hiding controls in the UI is insufficient.
8. Downstream records inherit the originating State Department and directorate unless an authorised transfer is explicitly recorded.

### 4.4 Seeded access profiles

Use the repository's shared test-user and credential mechanism. Do not hardcode passwords in this contract or production code.

| Fixture user | Scope | Purpose |
|---|---|---|
| `moh.medicalservices.officer@example.test` | `PE-MOH` / `MOH-SDMS` / `MOH-DIR-DHP` | Maintains the principal digital-health data |
| `moh.publichealth.officer@example.test` | `PE-MOH` / `MOH-SDPHPS` / `MOH-DIR-HRMD` | Maintains the minimal workforce-development data |
| `moh.strategy.reviewer@example.test` | `PE-MOH`, all assigned State Departments | Reviews Strategy submissions |
| `moh.budget.reviewer@example.test` | `PE-MOH`, all assigned State Departments | Reviews Budget submissions and revisions |
| `moh.budget.authority@example.test` | `PE-MOH`, all assigned State Departments | Activates Budgets and applies approved revisions |
| `moh.viewer@example.test` | `PE-MOH`, read-only Active data | Demonstrates consolidated management access |
| `other.entity.officer@example.test` | Another fixture entity | Proves cross-entity denial |

## 5. Canonical Strategy data

### 5.1 Strategic Plan

| Field | Value |
|---|---|
| Reference | `MOH-SP-2026-2030` |
| Title | Ministry of Health Strategic Plan 2026–2030 |
| Version | 1 |
| Period | 1 July 2026–30 June 2030 |
| Status | Active |
| Entity | `PE-MOH` |

### 5.2 Medical Services — Digital Health and Policy hierarchy

| Type | Reference | Name | Owner |
|---|---|---|---|
| Programme | `MOH-PROG-DH` | Digital Health Services | `MOH-SDMS` / `MOH-DIR-DHP` |
| Sub-programme | `MOH-SUB-HIS` | Health Information Systems | `MOH-SDMS` / `MOH-DIR-DHP` |
| Outcome | `MOH-OUT-RELIABILITY` | Reliable and accessible digital clinical services | `MOH-SDMS` / `MOH-DIR-DHP` |
| Indicator | `MOH-IND-AVAIL-01` | Availability of core clinical information systems | `MOH-SDMS` / `MOH-DIR-DHP` |
| Target | `MOH-TGT-AVAIL-2028` | At least 99.9% annual availability by 30 June 2028 | `MOH-SDMS` / `MOH-DIR-DHP` |
| Indicator | `MOH-IND-RESTORE-01` | Average restoration time for critical services | `MOH-SDMS` / `MOH-DIR-DHP` |
| Target | `MOH-TGT-RESTORE-2028` | Restore critical services within four hours by 30 June 2028 | `MOH-SDMS` / `MOH-DIR-DHP` |

Baselines:

- Availability: 97.8% as at 30 June 2026.
- Average critical-service restoration time: 11.5 hours as at 30 June 2026.

Availability is measured monthly from an approved infrastructure-monitoring report. The restoration-time target is included to support Strategy linkage and Budget context; detailed measurement history is not required in the initial fixture.

### 5.3 Public Health and Professional Standards — workforce capability hierarchy

This is deliberately minimal but structurally complete.

| Type | Reference | Name | Owner |
|---|---|---|---|
| Sub-programme | `MOH-SUB-DHC` | Digital Health Workforce Capability | `MOH-SDPHPS` / `MOH-DIR-HRMD` |
| Outcome | `MOH-OUT-CAPABILITY` | Sustainable digital-health workforce capability | `MOH-SDPHPS` / `MOH-DIR-HRMD` |
| Indicator | `MOH-IND-SKILLS-01` | Number of trained and certified digital-health technical staff | `MOH-SDPHPS` / `MOH-DIR-HRMD` |
| Target | `MOH-TGT-SKILLS-2029` | Train and certify 150 digital-health technical staff by 30 June 2029 | `MOH-SDPHPS` / `MOH-DIR-HRMD` |

Baseline: 35 trained and certified staff as at 30 June 2026.

### 5.4 Successor targets for the Draft FY 2028/29 Budget

The Draft FY 2028/29 Budget shall not reference targets whose period ended on 30 June 2028.

| Reference | Target | Owner |
|---|---|---|
| `MOH-TGT-AVAIL-2029` | Maintain at least 99.95% annual availability by 30 June 2029 | `MOH-SDMS` / `MOH-DIR-DHP` |
| `MOH-TGT-RESTORE-2029` | Restore critical services within two hours by 30 June 2029 | `MOH-SDMS` / `MOH-DIR-DHP` |
| `MOH-TGT-SKILLS-2030` | Train and certify 220 digital-health technical staff by 30 June 2030 | `MOH-SDPHPS` / `MOH-DIR-HRMD` |

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

Applicability shall be resolved from structured context. A department may not modify the catalogue objective through its funding treatment.

### 5.7 Strategy measurements

| Period | Indicator | Actual | Workflow | Result |
|---|---|---:|---|---|
| September 2027 | `MOH-IND-AVAIL-01` | 99.82% | Submitted, then Verified | At risk |
| October 2027 | `MOH-IND-AVAIL-01` | 99.96% | Submitted, then Verified | On track |

Corrective action: resolve storage-controller instability. Status: Completed and verified. Owner: `MOH-SDMS` / `MOH-DIR-DHP`.

These are illustrative management values, not statutory thresholds.

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

The Budget header is Ministry-owned. Its lines retain State Department and directorate ownership.

### 6.2 Medical Services — Digital Health and Policy line

| Field | Value |
|---|---|
| Reference | `MOH-BL-DHI-2027` |
| Title | Digital clinical systems infrastructure |
| Owner | `MOH-SDMS` / `MOH-DIR-DHP` |
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

This line proves that the second State Department owns data within the same Ministry Budget.

| Field | Value |
|---|---|
| Reference | `MOH-BL-HWD-2027` |
| Title | Digital Health Workforce Capacity Development |
| Owner | `MOH-SDPHPS` / `MOH-DIR-HRMD` |
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
| `MOH-BL-DHI-2028` — Digital clinical systems infrastructure | `MOH-SDMS` / `MOH-DIR-DHP` | KES 480,000,000 | `MOH-TGT-AVAIL-2029` |
| `MOH-BL-HWD-2028` — Digital-health workforce capability | `MOH-SDPHPS` / `MOH-DIR-HRMD` | KES 120,000,000 | `MOH-TGT-SKILLS-2030` |

The infrastructure line may use `MOH-TGT-RESTORE-2029` as a supporting target. Treatments follow the applicable FY 2028/29 Strategy context and must be independently stored, not copied by reference from the prior Budget.

### 6.6 Closed FY 2026/27 Budget

| Field | Value |
|---|---|
| Reference | `MOH-BUD-2026-2027` |
| Status | Closed |
| Approved | KES 520,000,000 |
| Open reservations | None |

Only the minimum data required for portfolio and status filtering is necessary.

## 7. Downstream funding story

All current downstream records belong to `MOH-SDMS` / `MOH-DIR-DHP`.

| Stage | Reference | Description/amount |
|---|---|---|
| Demand | `DMD-MOH-2027-014` | National digital health infrastructure upgrade — approved KES 455,000,000 |
| Reservation | `RSV-MOH-0001` | Original KES 455,000,000; remaining KES 145,000,000; Partially converted |
| Procurement Plan item | `PPI-MOH-2027-021` | Inherits the reservation |
| Tender | `TND-MOH-2027-008` | Carries and revalidates the same reservation |
| Contract | `CTR-MOH-2027-005` | Commitment KES 310,000,000 |
| Expenditure snapshot | `EXP-MOH-2027-005-01` | KES 180,000,000; Stale |

The reservation identity remains unchanged through Demand, Planning and Tender. The commitment converts part of that reservation:

`KES 455,000,000 original = KES 310,000,000 committed + KES 145,000,000 remaining reserved`

Outstanding commitment:

`KES 310,000,000 commitment − KES 180,000,000 expenditure = KES 130,000,000`

The expenditure snapshot source time shall be derived from the fixed fixture clock and shall exceed the configured freshness threshold. The UI must show Stale rather than zero.

No Demand, reservation, Tender or Contract is initially required for `MOH-SDPHPS` / `MOH-DIR-HRMD`. Its KES 80 million remains fully available.

## 8. Seed implementation contract

### 8.1 Orchestration

Provide one repository-conformant documented command that seeds or resets `MOH_MVP_V1`.

The implementation should use one central orchestrator with module-owned seed functions. Module functions must not independently invent or mutate shared fixture values.

### 8.2 Dependency order

1. Procuring entity and departments
2. Users, roles and organisational assignments
3. Public Value Objective catalogue
4. Strategic Plan and version
5. Strategy hierarchy, indicators and targets
6. Plan Value Commitments and applicability
7. Strategy measurements and corrective action
8. Budget headers
9. Budget lines, Strategy references and funding treatments
10. Demand and reservation
11. Procurement Plan item
12. Tender
13. Contract and commitment
14. Expenditure snapshot
15. Audit and lifecycle events

Only implemented modules need live records. Until a downstream module is available, its references may be declared in this contract but shall not be represented by misleading production records.

### 8.3 Reset behaviour

The reset process shall:

- identify exact records through fixture ownership, not broad entity deletion;
- delete fixture records in reverse dependency order;
- preserve unrelated Ministry and other-entity records;
- run transactionally where supported;
- fail clearly if a non-fixture record depends on a fixture record;
- recreate the same identities and values;
- leave no duplicate relationships, reservations, commitments or audit events.

### 8.4 Time and freshness

All fixture dates shall derive from `2027-11-03T12:00:00+03:00`. Do not use the runtime current date.

The script shall explicitly configure or reference the finance-source freshness threshold used to classify the seeded snapshot as Stale.

## 9. Required verification report

After seeding, print a concise PASS/FAIL report and return a failing exit status when an invariant fails.

Verify at minimum:

### Identity and repeatability

- fixture namespace is present on every owned record;
- all canonical references resolve once;
- a second execution creates no duplicates;
- record identities and counts remain unchanged after rerun.

### Strategy

- the Active Plan and version resolve correctly;
- every target has a valid hierarchy and owner department;
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
- the Draft FY 2028/29 Budget uses valid successor targets.

### State Department ownership

- the Medical Services officer may maintain Draft records owned by `MOH-SDMS` / `MOH-DIR-DHP`;
- the Medical Services officer cannot read protected Public Health Draft data or mutate Public Health records;
- the Public Health and Professional Standards officer may maintain Draft records owned by `MOH-SDPHPS` / `MOH-DIR-HRMD`;
- the Public Health and Professional Standards officer cannot read protected Medical Services Draft data or mutate Medical Services records;
- Ministry reviewers and authorities can access assigned data across both State Departments;
- the management viewer receives only authorised read-only consolidated information;
- the other-entity officer cannot access Ministry records through either UI or API.

### Downstream lifecycle

- one reservation identity links Demand, Planning and Tender;
- reservation and commitment are not double-counted;
- original reservation equals converted plus remaining reservation;
- expenditure is read-only and linked to the commitment;
- stale finance data is never displayed as zero;
- all lifecycle records retain `PE-MOH`, `MOH-SDMS` and `MOH-DIR-DHP` ownership.

## 10. Demonstration path

1. Sign in as the State Department for Medical Services officer and show the Digital Health and Policy-owned Strategy targets and Draft Budget line.
2. Attempt to open or mutate the Public Health and Professional Standards Draft line and show that access is denied.
3. Sign in as the State Department for Public Health and Professional Standards officer and show its minimal workforce-capability target and Budget line.
4. Sign in as a Ministry reviewer or authority and show the consolidated Ministry Budget and both State Department contributions.
5. Open the Medical Services digital-health infrastructure line and trace Strategy target, value treatments, reservation, commitment and stale expenditure.
6. Open Strategy Performance and show September At risk, the verified corrective action and October On track.
7. Explain that KenTender preserves ownership while providing authorised institutional oversight and traceability.

## 11. Extension rules for subsequent modules

When Demand, Planning, Tender, Evaluation, Award, Contract, Stores, Assets, Disposal or Analytics is added:

1. Extend the same narrative and identifiers where the business lifecycle continues.
2. Add only the smallest data needed to demonstrate the new module's value and exceptions.
3. Assign every record to the correct entity, State Department and operational directorate where applicable.
4. Preserve upstream identities rather than creating look-alike records.
5. Add the new invariants to the verification report.
6. Update the version and change log below before changing the script.

## 12. Change log

| Version | Date | Modules | Change |
|---|---|---|---|
| 1.0 | 6 August 2026 | Strategy Alignment; Budget & Funding | Established the canonical Ministry story and reconciled Strategy/Budget references |
| 1.1 | 6 August 2026 | Strategy Alignment; Budget & Funding | Replaced illustrative department names with the State Department for Medical Services and the State Department for Public Health and Professional Standards, with realistic operational ownership functions |
