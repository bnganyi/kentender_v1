# KenTender Architecture Rules v3

## 1. Service Layer Rule

All business logic must live in:

services/

NOT:
- DocTypes
- controllers
- UI handlers

---

## 2. Module Completion Rule (NEW)

No module is considered complete unless it includes:

- Pre-PRD
- Full PRD
- Domain model (tables)
- Governance/state model
- Role/permission matrices (tabular)
- UI specification
- Seed data
- Smoke contracts

---

## 3. Governance Rule (CRITICAL)

No module proceeds without:

- states defined
- transitions defined
- approvals defined
- rejection/return defined
- edit locks defined
- downstream trust defined

---

## 4. Permission Rule

Permissions must be:

- enforced server-side
- explicitly defined per role
- mapped to:
  - actions
  - visibility
  - transitions

---

## 5. UI Rule

All modules must follow:

Workspace (Landing)
→ Queue (role-based)
→ Detail panel
→ Builder

NOT:
- form-first design
- tab overload
- search-first workflows

---

## 6. Data Integrity Rule

- derived fields must not be manually editable
- totals must always reconcile
- no silent overrides

---

## 7. Integration Rule

Apps communicate via:
- services
- APIs

NOT:
- direct table writes

---

## 8. Procurement Boundary Rule

`kentender_procurement` must NOT:
- manage suppliers
- publish to public portal
- manage payments

It only manages the procurement transaction lifecycle.

---

## 9. Supplier Boundary Rule

`kentender_suppliers` owns:
- supplier identity
- qualification
- performance

Procurement only references suppliers.

---

## 10. Transparency Rule

`kentender_transparency` is:
- read-only
- publish-only

It does NOT influence transactions.