# Demand Intake and Approval (DIA)

**Home for the next procurement slice** inside `kentender_procurement` (KenTender global architecture v3).

This subdomain will own:

- demand capture (intake)
- classification / routing metadata as defined in the DIA PRD
- approval workflow and governance hooks
- budget reservation / commitment handoff to `kentender_budget` (via services — no direct cross-app DB writes)
- outputs that are **planning-ready** for the `procurement_planning` subdomain

Do **not** place supplier lifecycle here — that belongs to `kentender_suppliers`.  
Do **not** place public publication here — that belongs to `kentender_transparency`.

Implementation status: **structure only** — no business logic until the DIA phase starts.
