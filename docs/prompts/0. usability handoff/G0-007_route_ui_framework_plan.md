# G0-007 — Route and UI framework plan (LV-G0-007-01 + LV-G0-007-02)

**Parent gate:** [G0-007](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) (§5).  
**Inventory input:** [G0-001 §LV-G0-001-07](./G0-001_repository_inventory.md#lv-g0-001-07--desk-ui-surface-taxonomy) (Desk surface taxonomy).  
**Product URLs:** [Rectification pack §9.2](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md) (`/desk/procurement-journey`, `/desk/procurement-journey/<journey_code>`; user-facing title **Procurement Journey**).

This document is **design-only** (G0). R4 registers the Desk page and bundles per the tables below.

---

## LV-G0-007-01 — Procurement Journey: route registration

### Decision

**Use the same Frappe pattern as the existing TM2 workbench:** a **standard Desk `Page`** plus a **`page_js` hook** entry in `hooks.py`. Do **not** implement the full Journey UI only as a fragment inside `app_include_js` without a Page — the pack wireframe is a **full Desk surface** (timeline, header, evidence), analogous to [Tender Management v2 Page JSON](../../../kentender_procurement/kentender_procurement/kentender_procurement/page/tender_management_v2/tender_management_v2.json).

**Rationale:** `page_js` loads only when the Page is opened; it matches G0-001’s classification of TM2 as “Desk `page_js` only” and avoids loading a large journey bundle on every Desk session.

### Route / naming alignment

| Pack (canonical) | Frappe implementation (approved) |
|------------------|----------------------------------|
| `/desk/procurement-journey` | Desk **Page** `name` / `page_name`: **`procurement-journey`** (hyphenated slug aligns with pack path segment). Users reach it via Desk routing / sidebar link; exact hash vs path segment follows the site’s Frappe version and `desk` router — **user-visible title** remains **Procurement Journey** per pack §9.2. |
| `/desk/procurement-journey/<journey_code>` | **R4:** resolve `journey_code` via **approved equivalent** to pack literal: e.g. `frappe.route_options`, query string, or post-hash segment — chosen in R4 and documented in `LV-R4-005-01` evidence. |

**Anti-pattern:** Do **not** append `?v=` to `page_js` hook values (see [hooks.py](../../../kentender_procurement/kentender_procurement/hooks.py) comment — breaks file resolution).

### Registration matrix (LV-G0-007-01)

| Item | Mechanism | Path / key (planned) |
|------|-----------|----------------------|
| Desk Page record | `Page` JSON (standard) | `kentender_procurement/kentender_procurement/kentender_procurement/page/procurement_journey/procurement_journey.json` (module **Kentender Procurement**; roles aligned with who may open Journey — mirror TM2 page role pattern, refined in R4). |
| Page script | `page_js` in `hooks.py` | `"procurement-journey": "public/js/procurement_journey_page.js"` (file created in **R4**; name illustrative). |
| Selectors / tests | HTML + JS | Root container **`plc-journey-page`** per [pack §16.6](./0.%20procurement_lifecycle_usability_handoff_rectification_pack.md). |

### Downstream

| Tracker | Use |
|---------|-----|
| **LV-R4-005-01** | Register page + route + `plc-journey-page` per this plan. |
| **LV-G0-012-02** | Sidebar **Procurement Journeys** link targets this Page route (placeholder acceptable until R4). |
| **LV-R5-XAPP-01** | Cross-app calls depend on agreed Desk/API pattern; server entry remains in `kentender_procurement` per G0-001. |

---

## LV-G0-007-02 — Procurement Home: patch plan

### Decision

**Procurement Home** remains a **Workspace + workspace bundle** (not a separate Desk Page). Patches extend the **existing** workspace JSON and **`app_include_js` / `app_include_css`** bundle already used for Desk-wide procurement shell chrome.

### Artifact matrix

| Artifact | Role | Path |
|----------|------|------|
| Workspace definition | Sidebar shortcuts, blocks, links | `kentender_procurement/kentender_procurement/kentender_procurement/workspace/procurement_home/procurement_home.json` |
| Desk JS bundle | Active journeys / cards / `plc-*` hooks for Home | `kentender_procurement/kentender_procurement/public/js/procurement_home_workspace.js` |
| Desk CSS | Layout / cards | `kentender_procurement/kentender_procurement/public/css/procurement_home_workspace.css` |
| Hook registration | Globally include built assets on Desk (with safe `?v=` on **URL** hooks only) | [hooks.py](../../../kentender_procurement/kentender_procurement/hooks.py) — `app_include_js`, `app_include_css` |

### Build / deploy (mandatory on this bench)

After any edit to `public/js` or `public/css` under `kentender_procurement`:

1. From **bench root:** `./scripts/bench-with-node.sh build --app kentender_procurement` (Node 24 — see [AGENTS.md](../../../../../AGENTS.md) / frappe-bench-node rule).  
2. `bench --site kentender.midas.com clear-cache`  
3. `bench restart`  
4. Hard-refresh browser.

### Downstream

| Tracker | Use |
|---------|-----|
| **LV-R6-*** / **LV-R5-*** | Home cards and journey columns consume APIs; UI stays in workspace bundle above. |

---

## Acceptance

This file is **primary evidence** for **LV-G0-007-01** and **LV-G0-007-02**. Parent **G0-007** is tracked via [G0-007_route_ui_framework_confirmation.md](./G0-007_route_ui_framework_confirmation.md). **G0-007**, **LV-G0-007-01**, **LV-G0-007-02**, and the G0 exit item “UI route/framework plan approved” are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).
