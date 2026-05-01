# kentender_procurement — internal subdomains (v3)

Aligned with [mono-repo-v2.md](../docs/architecture/mono-repo-v2.md). Each folder under `kentender_procurement/` is a **slice** with its own `doctype/`, `services/`, `api/`, `tests/`, `utils/`.

| Subdomain | Scope |
|-----------|--------|
| `demand_intake` | Demand Intake and Approval (DIA); handoff to planning |
| `procurement_planning` | Procurement planning after approved demand |
| `tender_management` | Tender Management: STD / tender configuration and (later) officer-facing tender lifecycle; v1 desk retired |
| *(tendering v1 retired)* | Heavy solicitation UI removed; v2 may extend this slice or integrate via hooks — see `release_procurement_package_to_tender` |
| `bid_submission_opening` | Bid submission and opening |
| `evaluation_award` | Evaluation and award |
| `contract_management` | Contract management |
| `inspection_acceptance` | Inspection and acceptance |

**Boundaries (v3):**

- This app owns the **procurement transaction lifecycle** only.
- **Suppliers:** `kentender_suppliers` owns registration, onboarding, performance, sanctions. Procurement references suppliers.
- **Public transparency:** `kentender_transparency` owns publication; procurement owns source transaction records.

**STD-WORKS-POC progress:** [Implementation tracker](../docs/prompts/std%20poc/IMPLEMENTATION_TRACKER.md) · [Issues log](../docs/prompts/std%20poc/ISSUES_LOG.md) · rules in tracker + [`.cursor/rules/kentender-std-poc-implementation.mdc`](../../../.cursor/rules/kentender-std-poc-implementation.mdc) (under `apps/kentender_v1/docs/prompts/std poc/`).
