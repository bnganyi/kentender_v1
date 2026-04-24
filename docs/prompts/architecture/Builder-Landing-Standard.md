# Builder landing — look & feel standard (KenTender workbenches)

**Status:** working standard (2026-04-23)  
**Related:** [Builder Landing Page Refactor .md](./Builder%20Landing%20Page%20Refactor%20.md) (DIA compression spec and acceptance criteria; implementation record for all workbenches)

## Purpose

Workspace-injected **builder** UIs — **Procurement Home**, **Demand Intake & Approval**, **Procurement Planning**, **Strategy Management**, and **Budget Management** — should feel like one family: **dense above the fold**, with the **master–detail work area** starting high on the page, without hiding primary actions or changing domain logic.

## Layout stack (top → bottom)

1. **Page header (compact)** — title, one-line intro, primary CTA (e.g. New Demand / header actions). **No** large vertical padding; title one step below page `h4` scale (~1.2rem).
2. **Context bar (if any)** — e.g. current plan (PP). Tight padding.
3. **KPI strip (compact)** — same row height per card; **numeric values** show **full thousands separators**; **do not** prefix every card with the same currency. Assert currency **once** under the strip, e.g. *“All monetary figures in KES”* (`data-testid` values: `ph-kpi-currency-context` / `dia-kpi-currency-context` / `pp-kpi-currency-context` / `budget-kpi-currency-context`; Strategy is count-only).
4. **Control band** — work tabs; **queue chips + search on one row** where search exists (DIA); scope/helper text **one short line** if needed, not a tall block; **Filters** in `<details>`, **collapsed** by default, compact padding.
5. **Active filter chips** (if any) — single shallow row.
6. **Master–detail** — reduced top margin; list and detail columns use **taller** `max-height` (e.g. `min(78vh, 40rem)`) so first paint shows real content.

## CSS / JS conventions

- **Namespace:** app-specific shell (e.g. `.kt-dia-injected-shell`, `.kt-pp-injected-shell`) to avoid polluting the global desk.
- **Modifier classes:** `*-workspace-header--compact`, `*-control-surface` (tighter padding on the control `kt-surface` block), `*-master-detail--tight`, `*-queue-search-line` + `*-search-compact` (DIA).
- **Sticky detail actions:** follow DIA/PP pattern — first sticky section in the detail scrollport (`dia-detail-section-f` / `kt-pp-detail-section--sticky-actions`); keep in sync when adding new workbenches.
- **KPI value element:** no `text-overflow: ellipsis` on money; allow wrap or full line; prefer **number-only** in the card + single currency legend.

## When adding a new builder

1. Copy the **structural** order above (not necessarily every control).  
2. Reuse tokens: compact KPI card padding (~0.45rem × 0.6rem), compact title scale, single currency line.  
3. Add a short note in the implementation PR: **which** standard items apply (e.g. no search row yet → skip queue+search line).  
4. Link back to this file and the **Refactor** doc if you change density or KPI rules.

## Non-goals

- Replacing Frappe Workspaces or Form/List primitives.  
- Hiding **New** / **Apply** / **workflow** actions in overflow menus to save space.  
- Removing KPIs, tabs, or master–detail for density alone.
