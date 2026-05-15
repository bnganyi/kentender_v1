# G0-008 — WORKS master codes checklist (verbatim §4)

**Atomic ticket:** LV-G0-008-01 (parent [G0-008](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) — tracker **§5**).  
**Authoritative source:** [2. procurement_lifecycle_works_master_seed_data_specification.md](./2.%20procurement_lifecycle_works_master_seed_data_specification.md) **§4** (“Cursor must preserve these codes exactly”).  
**Depends on:** LV-G0-003-01 (**Accepted**) — seed conflict matrix uses the same registry.

**Rule:** Implementation, seeds, tests, and handoff JSON must use these strings **exactly** as below. If a code must change, update the **seed specification §4 first**, then re-run this gate.

---

## 4.1 Core Business Codes

| Object | Code |
|---|---|
| Procurement Journey | JRN-MOH-2026-001 |
| Procuring Entity | PE-MOH |
| Strategic Plan | STRAT-MOH-2026 |
| Strategy Programme | PROG-MOH-INFRA |
| Strategy Objective | OBJ-MOH-HOSP-RENOV |
| Strategy Target | TGT-MOH-HOSP-RENOV-2026 |
| Budget Cycle | BUDGET-MOH-2026 |
| Budget Line | BUD-MOH-INFRA-2026-001 |
| Demand | DEM-MOH-2026-001 |
| Demand Item | DEMITEM-MOH-2026-001-001 |
| Demand Approval | DEMAPPROVAL-MOH-2026-001 |
| Procurement Plan | PLAN-MOH-2026 |
| Procurement Package | PKG-MOH-2026-001 |
| Procurement Package Line | PKGLINE-MOH-2026-001-001 |
| STD Template | STD-WORKS |
| STD Template Version | STDTV-WORKS-BUILDING-CIVIL-APR2022 |
| STD Applicability Profile | WORKS-PROFILE-BUILDING-CIVIL |
| Tender STD Instance | STDINST-TND-MOH-2026-001 |
| TM2 Tender | TND-MOH-2026-001 |
| Tender STD Binding | TSB-TND-MOH-2026-001 |
| Bundle Output V2 | GB-TND-MOH-2026-001-V2 |
| DSM Output V2 | DSM-TND-MOH-2026-001-V2 |
| DOM Output V2 | DOM-TND-MOH-2026-001-V2 |
| DEM Output V2 | DEM-TND-MOH-2026-001-V2 |
| DCM Output V2 | DCM-TND-MOH-2026-001-V2 |
| Publication Snapshot V2 | PUBSNAP-TND-MOH-2026-001-V2 |
| Addendum 01 | ADD-TND-MOH-2026-001-01 |
| Publication Record | PUB-TND-MOH-2026-001-001 |
| Opening Readiness Record | ORR-TND-MOH-2026-001 |
| Closing Record | CLS-TND-MOH-2026-001 |

## 4.2 Handoff Codes

| Handoff | Code |
|---|---|
| Strategy Alignment Reference | STRATREF-MOH-2026-001 |
| Budget Funding Confirmation | BUDCONF-MOH-2026-001 |
| Demand Approval Certificate | DEMAPP-MOH-2026-001 |
| Planning Inclusion Record | PLANINCL-MOH-2026-001 |
| Planning Release Package | PKGREL-MOH-2026-001 |
| Tender Document Readiness Certificate | STDREADY-TND-MOH-2026-001 |
| Tender Publication Certificate | PUBCERT-TND-MOH-2026-001 |
| Tender Closing Certificate | CLOSECERT-TND-MOH-2026-001 |
| Opening Readiness Handoff | OPENREADY-TND-MOH-2026-001 |

## 4.3 User Codes

| User | Code | Role in Seed |
|---|---|---|
| Strategy Officer | USER-STRAT-001 | Creates/owns strategy alignment. |
| Budget Officer | USER-BUD-001 | Confirms budget line. |
| Requesting Officer | USER-REQ-001 | Raises demand. |
| Department Approver | USER-DA-001 | Approves demand. |
| Procurement Planner | USER-PLAN-001 | Includes demand in plan and releases package. |
| STD Administrator | USER-STDADMIN-001 | Ensures STD version active. |
| Procurement Officer | USER-PO-001 | Creates/prepares tender. |
| Procurement Manager | USER-PM-001 | Approves tender publication. |
| Auditor | USER-AUD-001 | Views evidence. |
| Supplier Alpha User | SUPUSER-ALPHA-BID | Supplier user, not internal journey access by default. |

---

## Acceptance

This checklist is **primary evidence** for **LV-G0-008-01**. Parent **G0-008** is tracked via [G0-008_master_works_codes_confirmation.md](./G0-008_master_works_codes_confirmation.md). **G0-008**, **LV-G0-008-01**, and the G0 exit item “Master WORKS codes confirmed” are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).
