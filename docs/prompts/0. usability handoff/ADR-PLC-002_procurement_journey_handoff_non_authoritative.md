# ADR-PLC-002 — Procurement Journey and Handoff layer are non-authoritative

| Field | Value |
|-------|--------|
| **Status** | Accepted (with **G0-005** / **LV-G0-005-01** on the implementation tracker) |
| **Date** | 2026-05-15 |
| **Scope** | Procurement lifecycle rectification — Journey View, handoff cards, cross-module navigation |
| **Supersedes** | — |
| **Related** | [ADR-PLC-001](./G0-001_repository_inventory.md#lv-g0-001-08--adr-plc-001-procurement_lifecycle-package-stub) (`procurement_lifecycle` package boundaries, [G0-001](./G0-001_repository_inventory.md)); [Rectification pack §9.3](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md) |

---

## Context

The [Procurement Lifecycle Usability & Handoff Rectification Pack](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md) introduces **Procurement Journey** and visible **handoff cards** so users can see cross-module progress, evidence, and next actions. Source modules (Demand Intake, Procurement Planning, Tender Management / TM2, Budget, Strategy, etc.) remain the **owners** of workflow state, approvals, and legal record.

Without an explicit boundary, implementers or users could treat the journey aggregate or a handoff card as an additional place to **approve**, **mutate legal state**, or **override** module truth — violating the product architecture and audit model.

---

## Decision

1. **Non-authority:** The **Procurement Journey** object (whether implemented as a DocType, query-backed view, or other aggregate) and **handoff card** artefacts are **navigation and evidence presentation only**. They **do not** constitute a second source of truth for:
   - workflow state (submitted, approved, published, closed, etc.),
   - legal or regulatory status,
   - financial commitment,
   - or any action that changes binding module state.

2. **Read model:** Journey and handoffs **read** from source modules (and linked audit/evidence) and **display** mapped status categories (per pack §6.3). They may cache or denormalise for performance only if **reconciliation** with source remains the contract and stale views are tolerable or clearly labelled.

3. **Conflict resolution:** If any handoff or journey presentation **disagrees** with the owning source DocType (or TM2 legal surface), **the source module wins**. The journey layer must **not** overwrite source records; it must **refresh**, mark stale, or surface a conflict for humans — with enforcement and tests deferred to **R1-010** / **LV-R1-010-01** (see [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md)).

4. **Admin / power-user UX:** User-visible copy (especially for admins) must state that **Journey is not an approval authority** and that **handoff cards do not replace** module workflows. Concrete strings and placement are **R5/R6** implementation; this ADR records the requirement.

---

## Consequences

- **Positive:** Clear separation between usability aggregation and module legal ownership; aligns with TM2-only legal controls (**G0-004**) and rectification no-go rules **NG-001**, **NG-002** in the tracker.
- **Negative / cost:** Journey and handoff APIs must be designed read-only or append-only for evidence metadata; any “action” from the journey UI must **delegate** to whitelisted source-module APIs (already the pattern for PR/tender actions elsewhere on the bench).

---

## Compliance and tracker mapping

| Tracker id | Relevance |
|------------|-----------|
| **NG-001** | Journey View must not become a source of approval or legal state. |
| **NG-002** | Handoff cards must not override source module status. |
| **R1-010** | Implementation: validation/tests that handoff upsert cannot change source workflow state. |

---

## Acceptance

This ADR is **primary evidence** for **LV-G0-005-01**. Parent **G0-005** is satisfied together with the gate note [G0-005_source_of_truth_approval.md](./G0-005_source_of_truth_approval.md). **G0-005**, **LV-G0-005-01**, and the G0 exit item “Journey/Handoff source-of-truth boundary approved” are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).
