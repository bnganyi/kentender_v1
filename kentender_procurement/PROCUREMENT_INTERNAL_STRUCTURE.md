# kentender_procurement — internal subdomains (v3)

Aligned with [mono-repo-v2.md](../docs/architecture/mono-repo-v2.md). Each folder under `kentender_procurement/` is a **slice** with its own `doctype/`, `services/`, `api/`, `tests/`, `utils/`.

| Subdomain | Scope |
|-----------|--------|
| `demand_intake` | Demand Intake and Approval (DIA); handoff to planning |
| `procurement_planning` | Procurement planning after approved demand |
| *(tendering v1 retired)* | Solicitation / tendering ships as a separate v2 slice or app — not present in this tree |
| `bid_submission_opening` | Bid submission and opening |
| `evaluation_award` | Evaluation and award |
| `contract_management` | Contract management |
| `inspection_acceptance` | Inspection and acceptance |

**Boundaries (v3):**

- This app owns the **procurement transaction lifecycle** only.
- **Suppliers:** `kentender_suppliers` owns registration, onboarding, performance, sanctions. Procurement references suppliers.
- **Public transparency:** `kentender_transparency` owns publication; procurement owns source transaction records.
