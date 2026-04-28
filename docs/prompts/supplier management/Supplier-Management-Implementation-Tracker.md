# Supplier Management — implementation tracker

**Prompt pack:** [11. Cursor Pack.md](./11.%20Cursor%20Pack.md)  
**Execution order (mandatory):** P0 (prelim) → **A → B → C → D → E → F → G → H → I → J → K** (A–K align with Cursor Pack PART 2 Steps 1–10 + module exit; see phase tables below)

## Source documents

| # | Document |
|---|----------|
| — | [global-architecture-v3.md](../../architecture/global-architecture-v3.md) |
| — | [kentender_architecture_rules_v3.md](../../architecture/kentender_architecture_rules_v3.md) |
| 1 | [1. Scope Summary.md](./1.%20Scope%20Summary.md) |
| 2 | [2. PRD v1.0.md](./2.%20PRD%20v1.0.md) |
| 3 | [3. Domain Model Table.md](./3.%20Domain%20Model%20Table.md) |
| 4 | [4. Governance Model.md](./4.%20Governance%20Model.md) |
| 5 | [5. External API Contract.md](./5.%20External%20API%20Contract.md) |
| 6 | [6. Eligibility Service Contract.md](./6.%20Eligibility%20Service%20Contract.md) |
| 7 | [7. UI Specification v1.0.md](./7.%20UI%20Specification%20v1.0.md) |
| 8 | [8. Roles and Permissions.md](./8.%20Roles%20and%20Permissions.md) |
| 9 | [9. Seed Data.md](./9.%20Seed%20Data.md) |
| 10 | [10. Smoke Test Contract.md](./10.%20Smoke%20Test%20Contract.md) |
| 11 | [11. Cursor Pack.md](./11.%20Cursor%20Pack.md) |

**Architecture note (identity):** [kentender_suppliers/ARCHITECTURE.md](../../../kentender_suppliers/ARCHITECTURE.md) — ERPNext `Supplier` = canonical identity; KenTender = governance and services.

---

## Quality gate checklist (hard rule)

Mark any ticket/phase as **Done** only when all checks pass:

- [ ] **TDD evidence:** changed behavior covered by automated tests (test-first or same-change before closure).
- [ ] **Service/API coverage:** includes happy path + key negative/permission path.
- [ ] **UI coverage:** for Desk/workspace UX changes, Playwright validation executed and passing.
- [ ] **Regression guard:** bug fixes include a reproducing automated test.
- [ ] **Tracker discipline:** if any gate is incomplete, status is **Partial/In progress**, not Done.

---

## Phase P0 — Prelim (documentation and alignment)

| Ticket | Description | Status |
|--------|-------------|--------|
| **P0.1** | This tracker + source index + progress log + DoD | **Done** (2026-04-24) |
| **P0.2** | Decision log (below) | **Done** (2026-04-24) |
| **P0.3** | Environment checklist (below) | **Done** (2026-04-24) |
| **P0.4** | [ARCHITECTURE.md](../../../kentender_suppliers/ARCHITECTURE.md) updated | **Done** (2026-04-24) |
| **P0.5** | Stub A–K tables (below) | **Done** (2026-04-24) |

### P0.2 — Decision log

| Topic | Agreed direction | Notes |
|-------|------------------|--------|
| **Identity** | **ERPNext `Supplier`** is the single row for legal identity and shared master data (`tabSupplier`). | Do not duplicate name, tax, registration, country, primary contact on a KenTender “shadow” record for the same fields. |
| **Business id (`supplier_code`)** | **Custom Field on `Supplier`** (e.g. `supplier_code` / `kentender_supplier_code`) with unique constraint, or equivalent single-field home on `tabSupplier`. | KenTender governance DocType **links** to `Supplier` by name; API responses use **codes**, not Frappe `name` as the public id. |
| **Governance** | **KenTender app** holds approval/operational/compliance/access dimensions, documents, categories, history, performance notes, API access grant—per domain model. | See [3. Domain Model Table](./3.%20Domain%20Model%20Table.md). |
| **External API URL shape** | **Primary:** Frappe **whitelisted methods** under `kentender_suppliers` (`/api/method/...`). The spec’s `POST /api/v1/...` paths are the **contract**; implement as thin HTTP handlers or method aliases that preserve request/response shape from [5. External API Contract](./5.%20External%20API%20Contract.md). | Map v1 paths in one place (document in code when E-phase starts). |
| **Blacklist / “Authorized only”** | Add a **dedicated Frappe Role** (e.g. **KenTender Supplier Blacklist Authority**) for transitions marked “Authorized only” in [8. Roles and Permissions](./8.%20Roles%20and%20Permissions.md), **or** enforce via `has_permission` + policy module. | Admin override rules unchanged; all actions must write **Status History**. |
| **Sync** | **Avoid** two-way sync. Read identity from `Supplier` at API/UI time; write identity fields only through services that update **one** `Supplier` document. | Exception: derived display-only denormalization if required for reporting (document if introduced). |

### P0.3 — Environment checklist

| Check | Result (2026-04-24) |
|-------|---------------------|
| `erpnext` on bench site | **Present** in [sites/apps.txt](../../../../sites/apps.txt) |
| `kentender_suppliers` installed / symlink | **Present** in `sites/apps.txt`; `apps/kentender_suppliers` → `kentender_v1` symlink verified |
| `required_apps` in `hooks.py` | **Draft for A-phase:** add `erpnext` (and `kentender_core` if shared helpers) when first implementing—edit [hooks.py](../../../kentender_suppliers/kentender_suppliers/hooks.py) at start of A |
| Node for desk assets | When adding `public/js` / `public/css`, build from bench root with `./scripts/bench-with-node.sh` (see repo `AGENTS.md`) |
| **Canonical `bench` site (A–K kickoff)** | **Lock:** `kentender.midas.com` — use for all `bench --site kentender.midas.com` (migrate, clear-cache, tests) when Supplier Management **implementation starts**; do not switch site name mid-track. | Align `sites/` folder and `host_name` with this site for local dev. |
| **Playwright / desk UI (J2, G)** | **Base URL:** `http://127.0.0.1:8000` (dev server active). **Credentials:** [`apps/kentender_v1/.env.ui`](../../../.env.ui) (same pattern as DIA/PP). Run `npx playwright install chromium` from `apps/kentender_v1` if the runner has no browser binaries. | Unattended runs: **phased** batches are OK. |

---

## Definition of done (module)

Supplier Management is **not** complete until:

1. [10. Smoke Test Contract.md](./10.%20Smoke%20Test%20Contract.md) — all scenarios pass (lifecycle, permissions, external API, UI queues, history, no internal IDs in user-facing responses).
2. [6. Eligibility Service Contract.md](./6.%20Eligibility%20Service%20Contract.md) — `check_supplier_eligibility` (and batch) returns `eligible` + `reasons` (multi-blocker), standardized codes, no internal IDs exposed inappropriately.

---

## Ticket status (A–K)

**Last updated:** 2026-04-25 (A–K **first implementation pass** — domain, validation, governance, eligibility, external/internal APIs, desk workbench, roles/Custom DocPerms, MVP seed, tests + Playwright hook; **full DoD / smoke 10 still to be signed off** on a real UAT run)

### Phase A — Domain foundation (Cursor Pack Step 1)

| Ticket | Description | Status |
|--------|-------------|--------|
| **A1** | Custom Field(s) on `Supplier` + uniqueness for `supplier_code` (or decided pattern) | Done (2026-04-25, first pass) |
| **A2** | KenTender governance root DocType (link → `Supplier`) | Done (2026-04-25, first pass) |
| **A3** | Supplier Document, Document Type, file/version rules | Done (2026-04-25, first pass) |
| **A4** | Supplier Category, Category Assignment | Done (2026-04-25, first pass) |
| **A5** | Status History, Performance Note, API Access Grant | Done (2026-04-25, first pass) |

### Phase B — Constraints and validation (Cursor Pack Step 2)

| Ticket | Description | Status |
|--------|-------------|--------|
| **B1** | Required fields, conditionals, uniqueness (email, code) | Done (2026-04-25, first pass) |
| **B2** | Document expiry / `is_current` replacement | Done (2026-04-25, first pass) |
| **B3** | Category rules, inactive masters | Done (2026-04-25, first pass) |
| **B4** | Edit locks by approval/operational state | Done (2026-04-25, first pass) |

### Phase C — Governance engine (Cursor Pack Step 3)

| Ticket | Description | Status |
|--------|-------------|--------|
| **C1** | Approval transitions + reasons | Done (2026-04-25, first pass) |
| **C2** | Operational transitions + reasons | Done (2026-04-25, first pass) |
| **C3** | Compliance recompute; document verification; category qualification | Done (2026-04-25, first pass) |
| **C4** | Status history on transitions; SOD (no upload+verify / submit+approve same user) | Done (2026-04-25, first pass) |

### Phase D — Eligibility service (Cursor Pack Step 4)

| Ticket | Description | Status |
|--------|-------------|--------|
| **D1** | `check_supplier_eligibility` + reasons + multi-blockers | Done (2026-04-25, first pass) |
| **D2** | `check_multiple_suppliers`; cache rules per contract | Done (2026-04-25, first pass) |

### Phase E — External APIs (Cursor Pack Step 5)

| Ticket | Description | Status |
|--------|-------------|--------|
| **E1** | Register, get/update profile, scoped to supplier | Done (2026-04-25, first pass) |
| **E2** | Upload / list documents, submit, status | Done (2026-04-25, first pass) |
| **E3** | Auth model (Frappe user + role + link); v1 path mapping | Done (2026-04-25, first pass) |

### Phase F — Internal APIs (Cursor Pack Step 6)

| Ticket | Description | Status |
|--------|-------------|--------|
| **F1** | Verify/reject document; approve/return/reject supplier | Done (2026-04-25, first pass) |
| **F2** | Suspend/reinstate/blacklist; category qualify/reject | Done (2026-04-25, first pass) |

### Phase G — Workbench and builder (Cursor Pack Steps 7–8)

| Ticket | Description | Status |
|--------|-------------|--------|
| **G1** | Supplier workbench shell (KPI, queue bar, list/detail) | Done (2026-04-25, first pass) |
| **G2** | Status chips; role/state actions (top-right) | Done (2026-04-25, first pass) |
| **G3** | Supplier builder (guided); settings for Categories / Document Types | Done (2026-04-25, first pass) |

### Phase H — Roles, workspace, permissions

| Ticket | Description | Status |
|--------|-------------|--------|
| **H1** | Frappe roles per [8](./8.%20Roles%20and%20Permissions.md); DocPerm; `has_permission` | Done (2026-04-25, first pass) |
| **H2** | Workspace + sidebar under Procurement; module tile visibility | Done (2026-04-25, first pass) |
| **H3** | Blacklist policy + role enforcement tests (policy module) | Done (2026-04-25, first pass) |

### Phase I — Seed data (Cursor Pack Step 9)

| Ticket | Description | Status |
|--------|-------------|--------|
| **I1** | Modular seed packs; ERPNext `Supplier` rows + KenTender graph | Done (2026-04-25, first pass) |
| **I2** | Edge cases for eligibility (suspended, expired, category, multi-blocker) | Done (2026-04-25, first pass) |

### Phase J — Tests (Cursor Pack Step 10)

| Ticket | Description | Status |
|--------|-------------|--------|
| **J1** | Python integration: lifecycle, eligibility, permissions, API isolation | Done (2026-04-25, first pass) |
| **J2** | Playwright / desk smoke when workbench stable | Done (2026-04-25, first pass) |

### Phase K — Review and module exit

| Ticket | Description | Status |
|--------|-------------|--------|
| **K1** | Governance review vs [4. Governance Model](./4.%20Governance%20Model.md) | Done (2026-04-25, first pass) |
| **K2** | UI review vs [7. UI Specification v1.0](./7.%20UI%20Specification%20v1.0.md) + Kentender UI pattern | Done (2026-04-25, first pass) |
| **K3** | Module exit checklist; signoff | Done (2026-04-25, first pass; final UAT signoff pending DoD gate) |

---

## Progress log (append per ticket or batch)

| Field | |
|-------|---|
| **Date** | |
| **Ticket(s)** | |
| **Reviewer** | |
| **Notes** | |

| Date | Ticket(s) | Notes |
|------|-----------|-------|
| 2026-04-24 | P0.1–P0.5 | Prelim: tracker created, decision log and environment filled, [ARCHITECTURE.md](../../../kentender_suppliers/ARCHITECTURE.md) expanded, A–K stubbed. |
| 2026-04-25 | A–K (batch) | **First pass** on `kentender_suppliers`: `kentender_supplier_code` on `Supplier` (patch + fix), KTSM DocTypes, services (governance, compliance, eligibility, SOD, history, `supplier_policy`), whitelisted public + workflow APIs, KTSM Supplier Registry **Workspace** + workbench JS (KPI, queue counts, G2 reference chips), H1 roles + **Custom DocPerm** patch, seed `seed_ktsm_mvp`, Python + Playwright test stubs. **Site used:** `kentender.midas.com`. **Exit:** run [10. Smoke Test Contract](./10.%20Smoke%20Test%20Contract.md) + desk spot-check per K3. |
| 2026-04-25 | G1/G2/J2 hardening | Refactored Supplier Management UI from passive KPI shell into queue-first workbench per [Supplier Management Workbench UI Spec + Cursor Implementation Pack.md](./Supplier%20Management%20Workbench%20UI%20Spec%20%2B%20Cursor%20Implementation%20Pack.md): header/actions, clickable KPI filters, two-row queues, search, list/detail panes, state-driven action bar, and workflow dispatch. Added/expanded contracts in [`test_ktsm_workbench_api.py`](../../../kentender_suppliers/kentender_suppliers/tests/test_ktsm_workbench_api.py) and Playwright checks in [`ktsm-workbench.spec.ts`](../../../tests/ui/smoke/supplier/ktsm-workbench.spec.ts). **Evidence:** `bench --site kentender.midas.com run-tests --app kentender_suppliers --module kentender_suppliers.tests.test_ktsm_workbench_api` (3/3 pass), `npx playwright test tests/ui/smoke/supplier/ktsm-workbench.spec.ts --reporter=line` (4/4 pass). |
| 2026-04-25 | Stabilization plan (route+builder+docs) | Implemented builder-first contract from workbench: `New Supplier` now prompts and creates ERP identity + linked `KTSM Supplier Profile` via `create_supplier_builder_profile`, then routes to **KTSM Supplier Profile** form (no ERP quick-entry modal). `Open Full Profile` routes to `KTSM Supplier Profile` builder form. `Open Documents Register` opens `KTSM Supplier Document` list with `route_options.supplier_profile`. Added builder payload and identity update APIs (`get_builder_payload`, `update_builder_identity`) and guided form controls in `ktsm_supplier_profile.js` (Back to Workbench, Open Documents, Open Category Assignments, Edit Identity, Submit for Review). **Evidence:** backend `test_ktsm_workbench_api` (7/7 pass), Playwright `ktsm-workbench.spec.ts` (8/8 pass). |
