# OVS-CHG-001 v0.6: version set (Phase 0, OVS6-0001)

Generated 4 October 2026 from the filed folders, the approved version set in `KenTender_OVS_Impact_and_Reconciliation_v0_6.md` ("Approved version set — 3 October 2026") and the filed baseline register `98_work_progress/KenTender_Baseline_Register.yaml` (`as_of` 2026-10-03). Predecessors stay beside their successors; none was moved or deleted.

| Document | Approved version | Folder | Filed file | Latest earlier version kept | Register version | Register requirement status |
|---|---|---|---|---|---|---|
| STR-CHG-001 | 1.9 | `02_strategy` | `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md` | 1.8 | 1.9 | Approved requirement |
| BUD-CHG-001 | 1.12 | `03_budget` | `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md` | 1.11 | 1.12 | Approved requirement |
| NDS-CHG-001 | 1.16 | `01_departmental_needs` | `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md` | 1.15 | 1.16 | Approved requirement |
| PLN-CHG-001 | 1.29 | `04_planning` | `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md` | 1.28 | 1.29 | Approved requirement |
| REQ-CHG-001 | 1.14 | `06_requisitions` | `KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md` | 1.13 | 1.14 | Approved requirement |
| CFG-CHG-002 | 0.18 | `09_unified_system_setup` | `KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_18.md` | 0.17 | 0.18 | Approved requirement |
| TPR-CHG-001 | 0.17 | `11_tenders` | `KenTender_TPR-CHG-001_Tenders_v0_17.md` | 0.16 | 0.17 | Approved requirement |
| BDS-CHG-001 | 0.11 | `12_bid_submission` | `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_11.md` | 0.10 | 0.11 | Approved requirement |
| KT-STD-001 | 1.15 | `00_common` | `KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_15.md` | 1.14 | 1.15 | Approved requirement |
| AUTH-ADR-001 | 1.11 | `00_common` | `KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_11.md` | 1.10 | 1.11 | Approved requirement |
| SEED-001 | 1.4 | `00_common` | `KenTender_SEED-001_Harmonized_End_to_End_Fixture_v1_4.md` | 1.3 | 1.4 | Approved requirement |
| SEED-OPS-001 | 1.22 | `00_common` | `KenTender_SEED-OPS-001_Canonical_Site_Seed_Runbook_v1_22.md` | 1.21 | 1.22 | Approved requirement |
| KT-RCA-001 | 1.3 | `98_work_progress` | `KenTender_Roadmap_Coverage_Assessment_v1_3.md` | 1.2 | 1.3 | Approved requirement |
| TRUST-ADR-001 | 0.2 | `00_common` | `KenTender_TRUST-ADR-001_Shared_Signing_and_Sealed_Custody_v0_2.md` | 0.1 | 0.2 | Approved requirement |
| BOP-CHG-001 | 0.11 | `14_bid_opening` | `KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md` | 0.10 | 0.11 | Approved requirement |
| PRC-CHG-001 | 0.11 | `13_proceedings` | `KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_11.md` | 0.10 | 0.11 | Approved requirement |
| EVL-CHG-001 | 0.5 | `15_bid_evaluation` | `KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md` | 0.4 | 0.5 | Approved requirement |
| AWD-CHG-001 | 0.5 | `16_award` | `KenTender_AWD-CHG-001_Award_v0_5.md` | 0.4 | 0.5 | Approved requirement |
| OVS-CHG-001 | 0.6 | `17_oversight_visibility` | `KenTender_OVS-CHG-001_System_Usability_and_Decision_Visibility_v0_6.md` | — | 0.6 | Approved requirement |
| CTX-CHG-001 | 1.1 | `00_common` | `KenTender_CTX-CHG-001_Working_Context_v1_1.md` | 1.0 (dotted name `…v1.0.md`) | 1.1 | Approved requirement |

## Findings

- All 20 filed documents match the approved version set. The register lists the same version for each and the status "Approved requirement".
- STD-TPL-001 v0.15 is approved and already registered. It was not moved because the staging copy was byte-identical to `07_std_configuration/`.
- The register was replaced by the working copy. Before the replacement it listed 30 documents and 20 interfaces, 38 decisions, 50 delivery items and 24 findings; it now lists 32, 24, 40, 57 and 31.
- `register_check.py` reports 13 errors on the filed register, all status values outside `workflow_states` (FU-OVS-24).
- SEED-001 v1.4 names v1.2 as its predecessor; v1_3 also exists (FU-OVS-23).
- TPR v0.16 and REQ v1.13, CFG v0.17 are intermediate versions folded into TPR v0.17, REQ v1.14 and CFG v0.18. They were never separately approved (OVS v0.6 control paragraph); their files stay in their folders as history.
- The Documentation Control Register workbook (`.xlsx`) was replaced the same way. It was not opened or compared cell by cell; it is binary and the YAML is the canonical source (register governance: "This file is the canonical source for the companion Documentation Control Register workbook").
