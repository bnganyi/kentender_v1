# H2 — Procurement Planning UI alignment review

**Date:** 2026-04-24  
**References:** [5. UI Specification v1.0.md](./5.%20UI%20Specification%20v1.0.md), [Kentender UI System Pattern v1.0.md](../architecture/Kentender%20UI%20System%20Pattern%20v1.0.md), current `procurement_planning_workspace.js` / `.css`, `procurement_package.js` / `.css`, `pp_template_selector.js`, `landing.py`.

---

## Checklist (Cursor Pack H2)

### 1. Workbench feels like a planning workbench, not a DocType list

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | Injected shell replaces empty workspace: plan context bar, **Plan summary** KPI belt, **Package work** master–detail (`kt-pp-*`), queue pills + search, role-aware CTAs (`show_new_plan`, `show_submit_plan`, etc.). Route `/desk/procurement-planning` per spec §2.1. |

### 2. Package list is compact and scannable

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | Rows use spec §4.2 layering: **primary** `package_name`, **secondary** `package_code · procurement_method`, **tertiary** value · `template_name`, optional **badges** (`buildBadgeChips`). Selected row `is-active`. Empty states queue-specific (`emptyMessageForQueue`). |

### 3. Detail panel is review-ready

| Verdict | **Matches** (minor deltas noted below) |
|---------|-------------|
| **Evidence** | Identity header (title, meta line, badges, status), **sectioned** blocks (definition, financial, demand lines, risk, KPI, decision, vendor, workflow), **actions** in a dedicated bar (sticky pattern aligned with DIA). Data from `get_pp_package_detail`. |

### 4. Builder is compact and sectioned

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | `Procurement Package` form uses **tabs** + two-column field groups per DocType JSON; guided progression / tab states in `procurement_package.js`. Not a single long one-column scroll. **Demand assignment** tab defers line editing to workbench per Package Form Restructure v2 — intentional divergence from older spec wording that implied in-form demand table editing. |

### 5. Template selection is understandable

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | Shared `pp_template_selector.js` modal (list + preview + apply); workbench **Apply template** and form **Choose template…**; APIs `list_pp_templates` / `get_pp_template_preview`. Meets spec §1.3 “modal … enough for v1”. |

### 6. No raw IDs displayed

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | List rows show `package_code` and **name** is internal routing only (`data-pp-package-name`). Package DocType `autoname: field:package_code`. Detail API resolves **business** `demand_id` and **Budget Line** `code — name` for `budget_line` (`package_detail.py`). Profile blocks use names / bounded JSON, not internal hashes in primary UI. |

### 7. Action placement is correct

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | Workbench detail: workflow + **Edit** / **Add Demand Lines** in header action cluster; plan workflow on plan bar. Aligns with UI System Pattern §2.3 / §3.3 (“actions close to context”). |

### 8. Risk / emergency / override signals visible without clutter

| Verdict | **Matches** |
|---------|-------------|
| **Evidence** | List badges from `row.badges`; detail header badges; definition section shows **Method override** Yes/No. At most a small set of chips per row. |

---

## What matches (summary)

- Master–detail workbench layout and KPI strip under header narrative  
- Four primary KPIs scoped to current plan (`landing._kpis_for_plan`)  
- Top tabs (My Work / All / Approved / Ready) + secondary queue pills per spec §3  
- Full approver / handoff queue set in `landing._pick_queues` for relevant roles  
- Package row visual hierarchy and template/value line  
- Detail panel as governed **review** surface with section titles  
- Template modal path and planning read gates  
- Business identifiers for Demand and Budget Line in detail API  
- Sticky / prominent action treatment consistent with DIA polish work  

---

## What is missing or drifts from locked spec

| Item | Spec reference | Current behaviour | Severity |
|------|------------------|-------------------|----------|
| **Workbench subtitle copy** | §2.2 | Was: “Complete draft packages…”. Now matches locked §2.2. | **Resolved** in this H2 pass (`procurement_planning_workspace.js`). |
| **Demand title in review table** | §5.2 / §6.3 columns | API already returned `demand_title`; table omitted it. | **Resolved** — column added in this H2 pass. |
| **Queue label “Structured”** | §3.2 “Structured Packages” | Label **“Completed Packages”** (product rename after workflow copy change). | **Accepted product language** — document here; not reverted unless PM reverses rename. |
| **Optional KPI cards** | §2.3 optional | Emergency / extra KPIs not in default four-card strip (only the four defaults). | **OK for v1** — spec marks optional. |
| **Builder §3 demand table** | §6.3 | Demand lines editing moved to **workbench** + **Demand assignment** summary on form per Restructure v2. | **By design** — superseded by later prompt pack; UI spec §6.3 partially legacy for review mode. |

---

## What must be fixed before signoff

**None** blocking, after this H2 pass:

- Subtitle aligned to locked §2.2 wording.  
- Demand title column visible in workbench detail demand-lines table (API already supplied the field).

Remaining items are **PM choices** (Completed vs Structured label) or **deferred optional** KPIs.

---

## Sign-off recommendation

- **H2 (UI alignment review):** **Pass** with documented intentional deltas (queue rename, demand assignment split from legacy builder table).  
- **Next:** **H3** — module exit checklist.

---

## Files touched for alignment (this H2 implementation)

- `kentender_procurement/public/js/procurement_planning_workspace.js` — subtitle + demand lines table column.  
- This document + `Procurement-Planning-Implementation-Tracker.md`.
