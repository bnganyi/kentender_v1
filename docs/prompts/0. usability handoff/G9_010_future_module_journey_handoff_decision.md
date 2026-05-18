<!--
  Evidence / decision artifact for Rectification Tracker §14 — G9-010 / LV-G9-010-01
-->

## Goal

Record **§14 G9-010**: the organization accepts **PLC-CURSOR-010** — greenfield **Bid Opening**, **Evaluation / Award**, and **Contract** capability must adopt the **Procurement Journey** and **Procurement Handoff Card** pattern **from first implementation**, consistent with **ADR-PLC-002** (journey/handoff remain non-authoritative aggregates; source modules retain legal/source-of-truth state).

**Done looks like:** a signed decision below plus tracker rows pointing here; implementation work on those modules does not start until this rule is acknowledged by product/architecture reviewers.

## Decision

1. **Bid Opening**, **Evaluation / Award**, and **Contract** modules (future tranches after TM2 publication readiness in the WORKS story) shall **not** ship as isolated Desk silos without journey spine alignment.

2. Each future stage shall expose **user-visible continuity** via:
   - **Journey steps** and lifecycle spine alignment with existing **`Procurement Journey`** conventions; and  
   - **Handoff certificates** where information passes between stages (**Procurement Handoff Card** services/APIs), mirroring Strategy→Tender patterns already accepted.

3. **Non‑negotiable constraints** (unchanged from rectification baseline):
   - Journey View and handoffs **do not** replace approvals or legal state in source DocTypes (**NG-001**, **NG-002**).
   - TM2 legal controls and sealed-bid rules remain authoritative where tender governance applies (**NG-003**, confidentiality **NG-006**).

4. **PLC-CURSOR-010** from [`1. procurement_lifecycle_usability_handoff_rectification_cursor_implementation_pack.md`](./1.%20procurement_lifecycle_usability_handoff_rectification_cursor_implementation_pack.md) is incorporated by reference.

## Out of scope for this artifact

- Detailed DocTypes/services for Bid Opening v2 / Evaluation v2 / Contract v2 — only the **pattern adoption rule** is decided here.

## Reviewer sign-off

| Field | Value |
|-------|--------|
| **Decision** | Accepted / Deferred / Rework — *(reviewer completes)* |
| **Accepted by** | *(name / role)* |
| **Date** | *(YYYY-MM-DD)* |
| **Conditions or notes** | *(optional)* |

Once completed, optionally copy these four lines into tracker **§14 — Final Acceptance Decision** (**G9-010** block).

---

*Once signed, update tracker **§14 G9-010** / **§18.10 LV-G9-010-01** to **Accepted** if your workflow distinguishes **Evidence Submitted** (artifact present) from **Accepted** (sign-off complete).*
