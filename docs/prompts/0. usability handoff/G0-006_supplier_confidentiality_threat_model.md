# G0-006 — Supplier confidentiality: permission design and threat model

**Parent gate:** [G0-006](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) (§5).  
**Atomic ticket:** LV-G0-006-01  
**Depends on:** [G0-001 §LV-G0-001-06](./G0-001_repository_inventory.md#lv-g0-001-06--supplier-portal) (supplier portal inventory; **must not** reuse supplier session for internal PLC aggregates).

---

## 1. Scope

**In scope:** Planned read-side **Procurement Lifecycle** HTTP contract from the [rectification pack §16.4](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md):

| Operation group | Pack path (logical) |
|-----------------|---------------------|
| List / search journeys | `GET /api/procurement-lifecycle/journeys` |
| Journey detail | `GET /api/procurement-lifecycle/journeys/<journey_code>` |
| Resolve journey by source object | `GET /api/procurement-lifecycle/journeys/by-object?object_type=&object_code=` |
| Internal evidence timeline | `GET /api/procurement-lifecycle/journeys/<journey_code>/evidence` |
| Handoff card detail | `GET /api/procurement-lifecycle/handoff-cards/<handoff_code>` |

**Assumption:** Frappe may expose these as `@frappe.whitelist()` methods or registered REST handlers; the **permission contract** below applies to the logical operations regardless of URL prefix.

**Out of scope for this note:** Write/mutate services from pack §16.3 (certificates, handoff upsert) — they remain **internal Desk** only unless a separate gate extends them. Any future **supplier-intentional** read API (e.g. redacted “my tender context”) is **not** defined here; default remains **deny** until product and security sign a dedicated contract (**PLC-NB-005**).

---

## 2. Actor definitions

| Actor | Typical session | Notes |
|-------|-----------------|-------|
| **Supplier / Guest** | Supplier portal user or `Guest` on `www` routes | Per [§LV-G0-001-06](./G0-001_repository_inventory.md#lv-g0-001-06--supplier-portal); must not inherit Desk roles. |
| **Internal Desk** | Logged-in Frappe Desk user with procurement / planning / DIA / TM2-related roles | Row-level access must follow **source DocTypes** (Demand, Package, TM2 Tender, etc.) as today — see [G0-002](./G0-002_existing_module_object_map.md) and `permission_query_conditions` / `has_permission` hooks referenced in G0-001. |
| **Auditor / elevated read** | Roles explicitly allowed to read audit-heavy or cross-entity evidence (e.g. auditor, compliance, System Manager as policy allows) | **Allow** only where organisation policy permits; implementation still **filters** technical refs per field rules in the pack. |

---

## 3. Access matrix (default policy)

Rationale summary: internal journey and handoff surfaces aggregate **strategy, budget, demand, planning, STD, publication, and audit** metadata. That is **internal procurement intelligence** — **not** supplier portal data.

| API / operation | Supplier / Guest | Internal Desk | Auditor / elevated read |
|-----------------|------------------|----------------|-------------------------|
| `GET …/journeys` | **Deny** — list would leak existence/titles of internal programmes and works. | **Allow** with role + **entity-scoped** query (same visibility as underlying journeys the user may already see via module lists). | **Allow** if policy grants cross-org read; else same as internal. |
| `GET …/journeys/<journey_code>` | **Deny** — full spine exposes cross-module state. | **Allow** only if caller has read on **linked root entities** for that journey (enforce via resolver, not only role name). | **Allow** with policy; optional extra redaction of names/codes is a product choice, not weaker than Deny for supplier. |
| `GET …/journeys/by-object?…` | **Deny** — bypass risk (object enumeration). | **Allow** only if caller has read on the **named** `object_type` / `object_code` (mirror module permission). | Same as internal unless policy widens. |
| `GET …/journeys/<journey_code>/evidence` | **Deny** — internal timeline, handoff payloads, audit joins (**NG-006**, **PLC-NB-005**). | **Allow** with same journey read gate + per-linked-document checks on evidence rows. | **Allow** / **Redacted subset** — auditors read evidence classes policy allows; technical refs may stay visible for true audit roles per pack “Legal Basis / Evidence” pattern. |
| `GET …/handoff-cards/<handoff_code>` | **Deny** — handoff cards carry internal handoff narrative + evidence links. | **Allow** only if caller may read the **handoff’s journey** and underlying **source** records. | **Allow** with policy + field-level rules. |

**PLC-SMOKE-014:** Supplier-facing tender flows must continue to satisfy “supplier does not see internal journey/audit-only information” — this matrix is the design backing that smoke expectation.

---

## 4. Mitigations (implementation must-haves)

1. **Separate permission paths:** PLC read APIs run in **Desk auth context** with explicit `frappe.only_for` / role checks **and** document-level checks; they **do not** reuse supplier portal controllers or “same code path” as `www/supplier/tenders` without a separate, reviewed, deny-by-default branch.
2. **Default deny for Guest** on all five operations unless a future signed API explicitly documents supplier read (none in v1 rectification default).
3. **No privilege expansion:** Journey aggregation must not return rows the user could not obtain by opening the source module (respect `permission_query_conditions` and `get_doc` permission outcomes on linked DocTypes).
4. **Evidence endpoint is highest risk:** `…/evidence` joins handoffs, audit metadata, and internal refs — treat as **strictest** internal gate; supplier denial is non-negotiable unless **PLC-NB-005** “explicitly permitted” is designed and accepted elsewhere.
5. **Auditor column** is “allow with policy”, not “public”: still authenticated, still logged, still subject to org rules.

---

## 5. Risk and downstream work

| Tracker | Relationship |
|---------|----------------|
| **NG-006** | Mitigated by **Deny** rows for supplier/guest on all five operations. |
| **R3-019** / **LV-R3-019-01** | Implement role + entity matrix tests for each whitelisted method. |
| **R3-020** | Supplier confidentiality guard + negative test at API boundary. |
| **R7-007** | Supplier users do not see internal journey evidence by default (negative permission test). |
| **LV-R8-REG-04** | Regression `NEG-SUP-EVIDENCE-ACCESS-001` — encodes this design in CI. |

---

## 6. Acceptance

This file is **primary evidence** for **LV-G0-006-01**. Parent **G0-006** is tracked via [G0-006_supplier_confidentiality_approval.md](./G0-006_supplier_confidentiality_approval.md). **G0-006**, **LV-G0-006-01**, and the G0 exit item “Supplier confidentiality boundary approved” are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).
