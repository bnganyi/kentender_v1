# ADR-PLC-003 — Desktop Procurement shell: two-layer information architecture

| Field | Value |
|-------|--------|
| **Status** | Accepted (with **G0-010** / **LV-G0-010-01** / **LV-G0-010-02** on the implementation tracker) |
| **Date** | 2026-05-15 |
| **Scope** | Frappe Desk IA for KenTender procurement lifecycle rectification — Procurement shell vs technical apps |
| **Supersedes** | — |
| **Related** | [ADR-PLC-001](./G0-001_repository_inventory.md#lv-g0-001-08--adr-plc-001-procurement_lifecycle-package-stub) (technical `procurement_lifecycle` package / app boundaries); [ADR-PLC-002](./ADR-PLC-002_procurement_journey_handoff_non_authoritative.md) (Journey/handoff non-authority — consistent with lifecycle-first navigation); [Rectification pack §15.5](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md) |

---

## Context

The [rectification pack §15.5](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md) states that end users should experience **one public-sector procurement lifecycle** inside a **single Desk shell (“Procurement”)**, with **Procurement Home** as the **canonical entry point** for ordinary procurement work.

Technically, KenTender remains implemented as **separate Frappe apps** (`kentender_strategy`, `kentender_budget`, `kentender_procurement`, …) for permissions, tests, governance, and data ownership ([ADR-PLC-001](./G0-001_repository_inventory.md#lv-g0-001-08--adr-plc-001-procurement_lifecycle-package-stub)). Without an explicit IA rule, Desk can still present **Strategy** and **Budget** as peer top-level products alongside **Procurement**, recreating the “three-tile” fragmentation the pack rejects.

---

## Decision

### 1. Two-layer rule (non-negotiable)

| Layer | What it is | Rule |
|-------|-------------|------|
| **Technical / code** | Separate Frappe apps, services, DocType ownership, hooks | **Keep** strong boundaries — unchanged from ADR-PLC-001. |
| **User-facing Desk IA** | App switcher, module tiles, workspace sidebars, primary labels | **Do not** present **Strategy** and **Budget** as independent **front-door** apps for **general procurement users**. Surface them as **lifecycle capabilities** inside the **Procurement** shell (aligned names: **Strategy Alignment**, **Budget & Funding** per pack). |

### 2. Procurement shell

- **Procurement** is the primary Desk navigation context for requisitioners, planners, procurement officers, and similar lifecycle roles.
- **Procurement Home** remains the **canonical landing** for lifecycle work (see pack §15.5).
- **Procurement Journey** and related surfaces sit inside this mental model ([ADR-PLC-002](./ADR-PLC-002_procurement_journey_handoff_non_authoritative.md)).

### 3. Specialist / admin access

Full **Strategy Management** and **Budget Management** workspaces may remain available for **specialist and admin** roles, reached via **Configuration / Governance** (or equivalent grouped entry) and **role gates** — not as the default path for general procurement roles (pack §15.5 “Role-based presentation”).

---

## Consequences

- **Positive:** Clear product story (“one lifecycle”); reduces duplicate navigation and role confusion.
- **Implementation split:** This ADR does **not** implement concrete Desk files. Execution belongs to **G0-011** (role matrix), **G0-012** (sidebar spine), **G0-013** / **G0-014** (app grid / specialist surfaces), **G0-015** (cross-app links), **G0-016** (labels), **G0-017** (Playwright). **LV-G0-015-01** consumes this decision plus **LV-G0-010-01** for supported cross-app navigation patterns.

---

## Acceptance

This ADR is **primary evidence** for **LV-G0-010-01**. Parent **G0-010** and **LV-G0-010-02** are tracked via [G0-010_desktop_ia_two_layer_confirmation.md](./G0-010_desktop_ia_two_layer_confirmation.md). **G0-010**, **LV-G0-010-01**, and **LV-G0-010-02** are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).

The G0 exit item that bundles **G0-010–G0-017** is **checked** (**closed**) on the implementation tracker (**G0-017** + **LV-G0-017-01…03** **Accepted**).
