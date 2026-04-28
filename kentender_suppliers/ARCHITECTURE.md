# kentender_suppliers

This app **owns** supplier onboarding, classification, qualification, performance, sanctions/blacklisting, and **computed eligibility** for procurement per [global-architecture-v3.md](../docs/architecture/global-architecture-v3.md) and the [Supplier Management prompt pack](../docs/prompts/supplier%20management/).

**Implementation tracker:** [Supplier-Management-Implementation-Tracker.md](../docs/prompts/supplier%20management/Supplier-Management-Implementation-Tracker.md)

## Identity vs governance (single source of truth)

| Concern | Owner | Notes |
|--------|--------|--------|
| **Legal / master identity** | **ERPNext `Supplier`** (`tabSupplier`) | One row per supplier. Name, tax id, country, company/contact fields used as defined on that doctype. **Extend with Custom Field(s)** when the PRD needs a stable business id (e.g. `SUP-KE-YYYY-####`) and ensure uniqueness. |
| **Governance and compliance** | **KenTender** (this app) | Link field(s) to `Supplier` + child DocTypes: documents, categories, approval/operational/compliance states, status history, performance notes, API access. **No duplicate** of identity fields for the same meaning—read from the linked `Supplier` for display and external APIs. |
| **Eligibility** | **Services in this app** | `check_supplier_eligibility` (and batch) per the eligibility contract. Downstream procurement/tendering modules call this; they do not re-derive rules ad hoc. |

```text
ERPNext Supplier (identity)
        │
        │ Link
        ▼
KenTender profile / governance graph  ──►  documents, categories, history, eligibility
```

- **DocTypes** stay **thin**; orchestration and transitions live under `kentender_suppliers/kentender_suppliers/services/`.
- **`kentender_procurement`** **references** suppliers; it does **not** own supplier lifecycle.

## Dependencies

- **`erpnext`**: required on the site so `Supplier` exists. Declare in this app’s `required_apps` in `hooks.py` when implementation begins.
- **Desk UI assets** (when added): build with `./scripts/bench-with-node.sh` from the bench root; see repo `AGENTS.md`.

## Cross-app reference

- Procurement and other transaction apps use **governed** supplier records and the **eligibility** API, not uncontrolled free-text or duplicate masters.
