# Implementation Disposition — Executive Summary

**Document ID:** KENTENDER-ROIDA-00-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only — no implementation changes  
**Controlling drafts:** `KenTender_MVP_Cross_Module_Operating_Model_v1.0.md` (CMOM), `KenTender_MVP_Semantic_and_Workflow_Assurance_Audit_v1.1.md` (SWA)  
**Status note:** Both controlling documents are drafts pending product-owner approval. This disposition treats them as the proposed correction baseline (CMOM §15 / SWA §11), not as already-approved law.

---

## 1. Overall safety assessment

**Do not discard the platform.** Foundations that match CMOM/SWA “Keep” lists are substantially present and tested: PE/OU DocTypes + User Scope Assignment; versioned Strategy / Budget / Demand / Plan records; generated references in Strategy, Budget, Demands and Planning; Demand HoD approval; Budget Line + Reservation; Plan / Version / Item / Demand Allocation; Approved-plan Draft successor; one Demand → one Plan Item default; explicit Combine aggregation; Planning professional review/approve (PLN-UI-08).

**Highest risk is semantic drift, not missing infrastructure.** Several shipped Gate 05 Planning artefacts and several Budget/Demand “treatment” surfaces contradict CMOM §5.2 / §12 and SWA §7.3. Continuing feature expansion on those semantics will deepen migration cost.

**Immediate stop condition (recommended):** Do not expand Planning Gate 06+ or invent further contribution/treatment UI until CMOM is accepted or amended and the Remove/Correct waves below are sequenced.

---

## 2. Strongest foundations to preserve

| Foundation | Evidence (representative) |
|---|---|
| Shared PE/OU + USA | `kentender_core/.../doctype/procuring_entity`, `organisation_unit`, `user_scope_assignment`; `services/org_scope_access.py` |
| Strict Demand/Plan create scope (0/1/multi) | `demand_creation_scope.py`; `planning_permissions.resolve_pe_for_create`; tests deny Admin PE-MOH invent |
| Generated codes | `strategy_reference.py`, `budget_reference.py`, `demand_codes.py`, `_invariants.next_plan_code` |
| Demand → Plan Item formation | `add_demand_to_plan` default `one_plan_item`; `aggregate_plan_allocations` for explicit Combine |
| Approved-plan Draft successor | `open_or_create_plan_revision.py` used from `add_demand_to_plan` |
| Finance BO sign-off on Demand | `demand_lifecycle` Budget Confirmation + `Demand Funding Allocation.bo_confirmation_*` |
| Atomic plan approve + Effective allocations | `approve_plan_version.py` + Gate 05 tests |
| Canonical seed arithmetic validators | `kentender_mvp_v1/validate.py` (455m / 310m / 145m / 535m story) |

---

## 3. Highest-risk semantic defects

| Defect | CMOM/SWA rule | Runtime consequence |
|---|---|---|
| **Departmental Submission / PLN-UI-07 contribution** | CMOM §5.2, §12 — no routine OU contribution / planning-stage HoD sign-off | DocType + `submit_departmental_contribution` + builder drawer + **hard gate** in `submit_plan_for_review` (“all … contributions must be Submitted”) |
| **Generic treatment questionnaires** | CMOM §9.4, §12; SWA §7.3 | `Budget Line Value Treatment`, `Demand Value Treatment`, retired Plan Item statutory fields (tombstoned but still in schema); Demand `aggregation_treatment` |
| **Budget Admin / first-PE fallbacks** | CMOM §10; SWA §4.3 / §9 | `budget_permissions.entity_for_user` → PE-MOH for Admin/unrestricted; multi-PE → `sorted(pes)[0]` |
| **Strategy “Plan Value Commitment” naming** | SWA §7.2 Correct → Strategy Value Commitment | DocType `Plan Value Commitment`, APIs `list_plan_value_commitment*`, page `strategy-plan-value-commitments` |
| **Missing targeted HoD reapproval** | CMOM §5.3 | No Planning service routes material HoD-owned fact changes for reapproval (Demand only invalidates BO sign-off) |
| **Finance position vs Planning review order** | CMOM §4 sequence 4 then 5; SWA §6 | BO confirmation is on Demand (pre-plan); Planning review does not re-check live Finance task — open whether CMOM “after planned requirement” requires a second Finance step on the Plan Item |

---

## 4. Data-loss / migration risks

| Risk | Notes |
|---|---|
| Dropping `Departmental Submission` | Seed clears + Gate 05 fixtures create rows; production sites may have Submitted hashes — need rebuild vs migrate decision |
| Removing value-treatment children | Budget lines / Demands may store PVC snapshots in treatment rows — preserve Strategy lineage elsewhere before drop |
| Renaming Plan Value Commitment | Wide API/UI/seed/test surface; rename or alias carefully |
| Orphan statutory fields on Plan Item Version | Patch `clear_retired_statutory_questionnaire.py` already clears values; schema drop is separate |
| Dirty bench worktree | Bench root has **no commits yet on main** with large untracked tree — disposition must not rely on git SHA for rollback |

---

## 5. Recommended correction waves

(As required by audit prompt §10 — **do not implement in this pass**.)

1. **Shared PE/OU + task-surface authorisation** — remove Budget/Home PE-MOH and first-PE fallbacks; align Admin inflation; enforce task-route denial consistently.  
2. **Strategy semantics + generated references** — rename PVC → Strategy Value Commitment; tighten Active-plan overlap; Defer PVO engine / advanced CA / performance dashboards if admission fails.  
3. **Budget & Funding simplification** — remove Budget Line Value Treatment questionnaire; keep register/activate/reserve; Investigate commitment convert gap (XMOD-BUD-007).  
4. **Demand ownership and approval boundary** — remove/narrow Demand Value Treatment and Demand-side aggregation packaging; keep HoD + BO confirmation.  
5. **Procurement Planning journey** — **Remove** contribution DocType/services/UI-07/gate; rewire submit-for-review; finish statutory purge; add targeted HoD reapproval only if CMOM §5.3 admitted.  
6. **Canonical seed reconciliation** — strip contribution/treatment seed rows; keep arithmetic invariants.  
7. **Cross-module tests** — replace contribution gates; add Journeys A–F negatives (Admin fallback, unauthorised task routes, no second HoD).

---

## 6. Explicit stop conditions

Stop further MVP expansion when any of the following hold:

1. CMOM/SWA remain unaccepted **and** new work embeds contribution / generic treatment / silent PE fallbacks.  
2. A module pack (REQ/Stitch/Cursor) is treated as Approved/Locked without recorded product-owner acceptance (SWA §1 / §13).  
3. Migration deletes treatment/contribution data without a rebuild-or-migrate decision recorded in wave acceptance.  
4. Tests green only because they assert prohibited workflows (e.g. `make ui-planning-contribution-gate` as a Done criterion after CMOM acceptance).

---

## 7. Disposition volume (this audit)

| Output | Content |
|---|---|
| `01_…` | Shared scope/auth inventory + role/route matrix |
| `02`–`05` | Per-module disposition matrices |
| `06` | Journeys A–F code traces |
| `07` | Seed + test consistency |
| `08` | Open decisions / evidence gaps |

**Verdict:** Safe to preserve foundations; unsafe to continue Gate expansion on contribution + treatment semantics until waves 1 and 5 (at minimum) are planned against an accepted operating model.
