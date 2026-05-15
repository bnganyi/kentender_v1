# G0-001 — Repository inventory (PLC rectification)

**Parent gate:** [G0-001](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md)  
**Atomic tickets:** LV-G0-001-01 … LV-G0-001-08  
**Canonical catalog:** [module implementation catalog](../../audit/module_implementation_catalog/README.md), [doctypes_inventory.csv](../../audit/module_implementation_catalog/doctypes_inventory.csv)  
**Generated:** 2026-05-15 (bench: `apps/kentender_v1`)

---

## Evidence summary (§3.2 template)

```text
Implementation Evidence:
- Code path(s): see sections LV-G0-001-01 … LV-G0-001-08 below (repo-relative from apps/kentender_v1/).
- Migration/DocType path(s): see LV-G0-001-02.
- UI path(s): see LV-G0-001-07.

Test Evidence:
- Test path(s): N/A for G0-001 (documentation-only deliverable).
- Command(s) run: inventory produced via read-only repo inspection (list_dir, rg, read_file).
- Result: G0-001 and LV-G0-001-01–08 **Accepted** in [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) §5 / §18.1.

Review Notes:
- Decision: **Accepted** (repository inventory gate).
- Follow-up: G0-002 object map; G0-003 seed conflict matrix.
```

---

## LV-G0-001-01 — Frappe apps → repository roots

| App | Path (under `apps/kentender_v1/`) | PLC rectification relevance |
|-----|-------------------------------------|------------------------------|
| `kentender_core` | `kentender_core/` | Procuring entity, Audit Event, shared seeds |
| `kentender_strategy` | `kentender_strategy/` | Strategy spine; Desk workspace + builder page |
| `kentender_budget` | `kentender_budget/` | Budget spine; Desk workspace + builder page |
| `kentender_procurement` | `kentender_procurement/` | DIA, planning, STD, TM2, supplier portal, primary hooks |
| `kentender_suppliers` | `kentender_suppliers/` | Supplier registry seeds (adjacent to lifecycle) |
| `kentender_governance` | `kentender_governance/` | v3 app present; not in PLC six-module spine for this pack |
| `kentender_compliance` | `kentender_compliance/` | v3 app present |
| `kentender_integrations` | `kentender_integrations/` | v3 app present |
| `kentender_transparency` | `kentender_transparency/` | v3 app present |
| `kentender_stores` | `kentender_stores/` | v3 app present |
| `kentender_assets` | `kentender_assets/` | v3 app present |

**Procurement `required_apps`** (dependency direction for installs):

| Setting | Value | Source |
|---------|--------|--------|
| `required_apps` | `["kentender_core", "kentender_strategy", "kentender_budget"]` | [kentender_procurement/kentender_procurement/hooks.py](../../../kentender_procurement/kentender_procurement/hooks.py) line 33 |

---

## LV-G0-001-02 — DocType inventory cross-check

**Authoritative CSV:** [doctypes_inventory.csv](../../audit/module_implementation_catalog/doctypes_inventory.csv) (82 data rows; header + 81 rows in snapshot taken 2026-05-15).

**JSON path convention:** `apps/kentender_v1/<app>/<app>/doctype/<snake_case>/<snake_case>.json`  
Example TM2 audit row DocType: `kentender_procurement/kentender_procurement/doctype/tm2_tender_audit_event/tm2_tender_audit_event.json`  
Example core audit: `kentender_core/kentender_core/doctype/audit_event/audit_event.json`

### PLC relevance tags (by CSV row group)

| Tag | Apps / modules | Notes |
|-----|------------------|--------|
| `PLC-CORE` | `kentender_core` | Entity, departments, `Audit Event`, attachments |
| `PLC-STRATEGY` | `kentender_strategy` | Strategic Plan through Strategy Target, Navigation |
| `PLC-BUDGET` | `kentender_budget` | Budget through Funding Source, Navigation |
| `PLC-DIA` | `kentender_procurement` / Demand Intake | Demand, Demand Item |
| `PLC-PLANNING` | `kentender_procurement` / Procurement Planning | Plan, Package, Template, profiles |
| `PLC-STD-GOV` | `kentender_procurement` / Kentender Procurement | STD Template + governance + security registry |
| `PLC-TM2` | `kentender_procurement` / Kentender Procurement | TM2*, Tender*, publication, STD instance tree |
| `PLC-NAV` | `kentender_procurement` | `Procurement Navigation` |

Full row list is omitted here; use the CSV for machine diff. Counts from CSV: `kentender_budget` 6, `kentender_core` 8, `kentender_procurement` 67, `kentender_strategy` 7.

---

## LV-G0-001-03 — `kentender_procurement` hooks integration (PLC-critical)

**Source file:** [kentender_procurement/kentender_procurement/hooks.py](../../../kentender_procurement/kentender_procurement/hooks.py)

| Concern | Hook key / symbol | Dotted callable or path | Notes |
|---------|-------------------|-------------------------|--------|
| Desk CSS bundles | `app_include_css` | `public/css/demand_intake_workspace.css`, `procurement_planning_workspace.css`, `procurement_home_workspace.css`, `procurement_package.css`, `std_library_shell.css` | Uses `_desk_asset_v` for cache-bust query on **URL** (allowed for `app_include_*`). |
| Desk JS bundles | `app_include_js` | `workspace_list_selection_utils.js`, `demand_intake_workspace.js`, `pp_template_selector.js`, `procurement_planning_workspace.js`, `procurement_home_workspace.js`, `std_engine_desk_boot.js` | Same `_desk_asset_v` pattern. |
| Form scripts | `doctype_js` | `Demand` → `public/js/demand_form.js`; `Procurement Package` → `public/js/procurement_package.js` | |
| Desk pages | `page_js` | `tender-management-v2` → single `public/js/tender_management_v2_workbench_page.js`; `std-engine` → ordered `public/js/std_library/*.js` + `std_engine_page.js` | **Invariant:** no `?v=` on `page_js` values (Frappe resolves as disk paths). |
| Website routes | `website_route_rules` | `/supplier/tenders/<tender_code>` → `supplier/tenders` | See LV-G0-001-06. |
| List query filters | `permission_query_conditions` | `Demand`, `Procurement Plan`, `Procurement Package` → `demand_intake.permissions.demand_permissions` / `procurement_planning.permissions.pp_record_permissions` | |
| Record auth | `has_permission` | Same DocTypes → `demand_has_permission`, `procurement_plan_has_permission`, `procurement_package_has_permission` | |
| Post-migrate | `after_migrate` | `kentender_procurement.setup.after_migrate_navigation.run`; `tender_management.seeds.std_template_governance_roles.run_after_migrate`; `std_template_governance_seed.run_after_migrate` | |
| Boot session | `boot_session` | `kentender_procurement.setup.workspace_permissions.patch_bootinfo` | |
| Planning → tender | `release_procurement_package_to_tender` | `kentender_procurement.tender_management.services.release_procurement_package_to_tender.hook_release_procurement_package_to_tender` | PLC handoff wiring target. |
| Fixtures | `fixtures` | Workspace names: Demand Intake and Approval, Governance & Configuration, Procurement Home, Procurement Planning; Sidebars: Procurement, Demand Intake, Planning module navigation; DocType filter `Procurement Navigation` | |

---

## LV-G0-001-04 — Seed entrypoints (`bench execute` style)

Pattern: `bench --site kentender.midas.com execute <dotted.module>.<callable>`

### `kentender_core` — `kentender_core/seeds/`

| Module path | Typical entry | Purpose (summary) |
|-------------|---------------|-------------------|
| `kentender_core.seeds.seed_core_minimal` | `run` | Minimal core |
| `kentender_core.seeds.dev_full_reseed` | `run` | Orchestrated reseed |
| `kentender_core.seeds.reset_core_seed` | `run` | Reset |
| `kentender_core.seeds.seed_strategy_basic` / `seed_strategy_extended` / `seed_strategy_empty` | `run` | Strategy fixtures |
| `kentender_core.seeds.seed_budget_basic` / `extended` / `empty` | `run` | Budget fixtures |
| `kentender_core.seeds.seed_budget_line_dia` | `run`, `verify_prerequisites_for_dia` | Budget line for DIA |
| `kentender_core.seeds.reset_strategy_seed` | `run` | Strategy reset |

### `kentender_procurement` — demand / planning / tender seeds

| Module path | Entry | Purpose |
|-------------|-------|---------|
| `kentender_procurement.demand_intake.seeds.seed_dia_basic` | `run` | DIA basic |
| `…seed_dia_extended` / `seed_dia_empty` / `seed_dia_exceptions` | `run` | DIA variants |
| `…seed_dia_planning_f1_prerequisites` | `run` | Planning F1 prereqs |
| `kentender_procurement.procurement_planning.seeds.seed_procurement_planning_f1` | `run` | F1 planning |
| `…seed_planning_pp3_slice` | `run` | PP3 slice |
| `…seed_works_stdint_s01` | `run` | WORKS STDINT-S01 chain |
| `…validate_planning_seed_dependencies` | `run`, `get_validation_report`, `assert_prerequisites` | Validation |
| `kentender_procurement.tender_management.seeds.seed_std_inst_1400` | (module) | STD instance fixture chain |
| `…tender_publication.seeds.seed_pub_moh_1100` | (module) | Publication MOH slice |
| `…derived_models.seeds.seed_derived_moh_1200` | (module) | Derived model golden |
| `…works_completion.seeds.works_completion_moh_fixture` | (module) | Works completion |

**After migrate (not `bench execute` but lifecycle):** see hooks `after_migrate` list in LV-G0-001-03.

**Historical / audit-only seeds (not default Frappe fixtures):** `apps/kentender_v1/docs/audit/planning_tender_handoff_2026-05-03/seeds/*.py` — document UAT parity only; confirm before treating as production entrypoints.

**WORKS master code collision analysis:** deferred to **G0-003** / `LV-G0-003-01` per tracker.

---

## LV-G0-001-05 — Audit and TM2 audit touchpoints

### Core — `Audit Event` DocType + service

| Artifact | Path |
|----------|------|
| DocType JSON | `kentender_core/kentender_core/doctype/audit_event/audit_event.json` |
| Insert API | `kentender_core/kentender_core/services/audit_event_service.py` — `log_audit_event` |
| Orchestration | `kentender_core/kentender_core/services/business_action_service.py` — calls `log_audit_event` after workflow guard |
| Tests | `kentender_core/kentender_core/tests/test_audit_event.py`, `test_wave0_smoke.py`, `test_business_action.py` |

### Procurement tender / security — unified `Audit Event` rows

| Artifact | Path |
|----------|------|
| Append-only façade (SEC-0520) | `kentender_procurement/kentender_procurement/tender_management/security/audit/event_service.py` — imports `log_audit_event`, validates metadata |
| Publication audits | `…/tender_management/tender_publication/audit/publication_audit.py` |
| Access denied audit | `…/tender_management/security/action_availability/access_denied_audit.py` |
| TM2-specific audit DocType (if used for structured TM2 rows) | `kentender_procurement/kentender_procurement/doctype/tm2_tender_audit_event/tm2_tender_audit_event.json` |

**Evidence timeline (R7) join hypothesis:** filter `Audit Event` by `document_type` / `document_name` / `metadata` JSON and optional linkage to `TM2 Tender`; confirm field names in `audit_event.json` and `event_service` when implementing R7.

---

## LV-G0-001-06 — Supplier portal

| Item | Detail |
|------|--------|
| Route rule | `website_route_rules` in hooks: `/supplier/tenders/<tender_code>` → `supplier/tenders` |
| Controller | `kentender_procurement/kentender_procurement/www/supplier/tenders/index.py` — `get_context` |
| Template | `kentender_procurement/kentender_procurement/www/supplier/tenders/index.html` |
| Guest behaviour | Redirect to `/login?redirect-to=…` when `frappe.session.user == "Guest"` |
| Data services | `tender_management.services.supplier_portal_tender_list.list_supplier_portal_tenders`; `supplier_portal_tender_detail.get_supplier_portal_tender_detail` |

**PLC confidentiality:** internal journey / handoff APIs must not reuse supplier session; enforce same role model as **G0-006** (threat model follows this inventory).

---

## LV-G0-001-07 — Desk UI surface taxonomy

| Surface | Mechanism | Key files |
|---------|-----------|-----------|
| Procurement Home | Workspace + bundle JS | `kentender_procurement/kentender_procurement/kentender_procurement/workspace/procurement_home/procurement_home.json`; `public/js/procurement_home_workspace.js`; CSS in hooks |
| Demand Intake and Approval | Workspace + JS | `…/workspace/demand_intake_and_approval/demand_intake_and_approval.json`; `public/js/demand_intake_workspace.js` |
| Procurement Planning | Workspace + JS | `…/workspace/procurement_planning/procurement_planning.json`; `public/js/procurement_planning_workspace.js`; `public/js/pp_template_selector.js` |
| Governance & Configuration (STD admin) | Workspace + `page_js` std-engine | `…/workspace/governance_and_configuration/governance_and_configuration.json`; `page_js` std-engine chain in hooks |
| TM2 workbench | Desk `page_js` only | `tender-management-v2` → `public/js/tender_management_v2_workbench_page.js` |
| Demand form | `doctype_js` | `public/js/demand_form.js` |
| Procurement Package form | `doctype_js` | `public/js/procurement_package.js` |
| Strategy (current app) | Workspace + builder page | `kentender_strategy/kentender_strategy/workspace/strategy_management/strategy_management.json`; hooks `page_js` `strategy-builder`; `doctype_js` Strategic Plan |
| Budget (current app) | Workspace + builder page | `kentender_budget/kentender_budget/workspace/budget_management/budget_management.json`; hooks `page_js` `budget-builder`; `doctype_js` Budget |

**Future `plc-*` selectors:** attach on Journey page shell (R4), Procurement Home cards, handoff panels, and module context headers (R5) — see Cursor pack §16.6; implement in `kentender_procurement/public/js` (or shared test IDs in HTML templates for `www` if ever needed for supplier-negative tests).

---

## LV-G0-001-08 — ADR-PLC-001: `procurement_lifecycle` package (stub)

**Decision (recommended):** introduce Python package:

`kentender_procurement/kentender_procurement/procurement_lifecycle/`

with subpackages as in Cursor implementation pack:

- `constants.py`, `journey.py`, `handoff.py`
- `services/` — journey aggregation, handoff cards, seed orchestration, evidence
- `api/` — whitelisted methods for Desk / future REST adapters
- `seeds/` — `seed_procurement_lifecycle_works_master.py` (per WORKS master seed spec)
- `tests/`

**Import rules:**

1. **Inbound:** other subdomains call `procurement_lifecycle` only through **document hooks / explicit services**, not circular imports from `procurement_lifecycle` back into DocType class bodies at import time.
2. **Outbound:** `procurement_lifecycle` may call **`demand_intake`**, **`procurement_planning`**, **`tender_management`** `services/` modules; avoid importing UI or `hooks.py`.
3. **Data:** new DocTypes for Journey / Handoff live under `kentender_procurement` (same app as fixtures today) unless architecture review moves them.
4. **API surface:** Frappe `@frappe.whitelist()` in `procurement_lifecycle/api/` with permission checks mirroring G0-006 / R3-019.

**Status:** ADR stub recorded; implementation deferred to R1–R3.

---

## Appendix A — Related bench commands (reference only)

Site per project rules: `kentender.midas.com`.

```bash
bench --site kentender.midas.com execute kentender_core.seeds.seed_core_minimal.run
bench --site kentender.midas.com execute kentender_procurement.demand_intake.seeds.seed_dia_basic.run
```

(Exact callables vary; use `bench execute` with kwargs per seed module docstrings.)

---

## Appendix B — Design reference assets (optional)

Screenshots and IA discussion images may be stored under the Cursor project assets path used in session; not required for G0-001 technical completeness.
