# G0-011 — Role matrix for Procurement shell visibility

**Parent gate:** [G0-011](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) (§5).  
**Policy:** [ADR-PLC-003](./ADR-PLC-003_desktop_procurement_shell_two_layer_ia.md); [Rectification pack §15.5](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md).  
**Role inventory source:** [G0-001 §LV-G0-001-01](./G0-001_repository_inventory.md#lv-g0-001-01--frappe-apps--repository-roots) (apps) + seed role constants in [core_constants.json](../../audit/seed_data_bundle/frozen/core_constants.json) (`BUSINESS_ROLES`).

This artifact is a **target IA contract** for G0-012+ implementation and Playwright (G0-017). It is not a claim that Desk already matches every cell.

---

## LV-G0-011-01 — KenTender Desk roles enumerated

| # | Role | Typical persona | Primary workstream |
|---|------|-----------------|---------------------|
| R0 | **System Manager** | Platform admin | Break-glass / setup |
| R1 | **Administrator** | Full admin | Break-glass / setup |
| R2 | **Strategy Manager** | Strategy owner | Strategy spine |
| R3 | **Planning Authority** | Planning / finance gate | Planning / budget context |
| R4 | **Requisitioner** | Demand author | Demand intake |
| R5 | **Procurement Planner** | Plans & packages | Procurement planning |
| R6 | **Procurement Officer** | Tender / execution | TM2 / STD operational |
| R7 | **Finance Reviewer** | Budget / funds check | Budget / finance |
| R8 | **Department Approver** | Line manager approval | Demand approval |
| R9 | **Auditor** | Read-heavy oversight | Evidence / audit |

*Additional roles (e.g. supplier portal users) are out of scope for this **Desk shell** matrix; supplier confidentiality remains under **G0-006**.*

---

## LV-G0-011-02 — Role × surface matrix (target)

**Columns**

| Column | Meaning |
|--------|--------|
| **App switcher** | Which **top-level Desk apps** the role should see as **primary** (`P` = Procurement, `S` = Strategy, `B` = Budget). **`—`** = must not be promoted as a peer “front door” for this role. |
| **Procurement sidebar** | Access to the **Procurement** workspace ordered spine (**G0-012**): `Full` = all entries subject to DocPerm; `Core` = lifecycle core without specialist Configuration blocks; `Read` = read-only where DocPerm allows. |
| **Configuration** | **Configuration / Governance** group inside Procurement (STD Library, templates, profiles, specialist links): `Full` / `Limited` / `None` (policy intent). |
| **Specialist Strategy** | Direct entry to **full Strategy Management** (own app workspace), not only “Strategy Alignment” wrapper: `Yes` only for roles that own strategy configuration. |
| **Specialist Budget** | Direct entry to **full Budget Management**: `Yes` for finance/strategy specialists; otherwise **`—`**. |

### Matrix

| Role | App switcher | Procurement sidebar | Configuration | Specialist Strategy | Specialist Budget |
|------|--------------|---------------------|---------------|----------------------|-------------------|
| System Manager | P, S, B | Full | Full | Yes | Yes |
| Administrator | P, S, B | Full | Full | Yes | Yes |
| Strategy Manager | **P** primary; S via specialist path | Full | Full | Yes | `—` (unless dual-role) |
| Planning Authority | **P** primary; B via sidebar / config as needed | Full | Limited → Full per DocPerm | `—` | Yes |
| Requisitioner | **P** only (`S`/`B` **—**) | Core | None or Limited (org choice) | `—` | `—` |
| Procurement Planner | **P** only (`S`/`B` **—**) | Full | Limited | `—` | `—` |
| Procurement Officer | **P** only (`S`/`B` **—**) | Full | Limited | `—` | `—` |
| Finance Reviewer | **P** primary; budget context via **Budget & Funding** | Full | Limited | `—` | Yes (or via wrapper only — pick one implementation; default **Yes** if role owns budget lines) |
| Department Approver | **P** only | Core | None | `—` | `—` |
| Auditor | **P** primary (evidence spine) | Full (read where permitted) | Limited (audit exports) | `—` | `—` |

**Notes**

1. **`P` only** for general procurement roles implements ADR-PLC-003 / pack §15.5: Strategy and Budget are **lifecycle capabilities** inside Procurement (`Strategy Alignment`, `Budget & Funding`), not peer app tiles.
2. **System Manager / Administrator** retain all apps for break-glass and module maintenance.
3. **LV-G0-011-03** (automated forbidden-surface checks) is **deferred** to implementation + **G0-017** Playwright; this document supplies the **expected** matrix for those tests.

---

## Acceptance

This file is **primary evidence** for **LV-G0-011-01** and **LV-G0-011-02**. Parent **G0-011** is tracked via [G0-011_role_matrix_confirmation.md](./G0-011_role_matrix_confirmation.md). **G0-011**, **LV-G0-011-01**, and **LV-G0-011-02** are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md). **LV-G0-011-03** is still **Not Started**.

The G0 exit item that bundles **G0-010–G0-017** is **checked** (**closed**) on the implementation tracker (**G0-017** **Accepted**).
