# KenTender Workbench Typography v1.0

## Goal

Operational workbench surfaces (Planning Workbench, Budget workbench, DIA hub, etc.) must share one **compact enterprise type scale** so users see consistent hierarchy across modules. Hero-scale typography (32px titles plus 28px KPI values on the same screen) is reserved for **detail/review identity headers**, not queue workbenches.

**Canonical reference implementation:** [budget_workbench_page.css](../../kentender_budget/kentender_budget/public/css/budget_workbench_page.css).

**Shared CSS tokens:** [kt_workbench_typography.css](../../kentender_core/kentender_core/public/css/kt_workbench_typography.css).

## Page-type rules

| Page type (UI System Pattern §2) | Typography profile | Example |
|----------------------------------|-------------------|---------|
| **2.1 Landing / Workbench** | Operational scale (`--kt-wb-*`) | Budget workbench, Planning Workbench |
| **2.2 Builder / Editor** | Operational title + section scale | Package wizard steps |
| **2.3 Review / Detail** | Identity header (`--kt-wb-identity`) for record title only | Package Detail page title |

On workbench surfaces, **only one element** may use the largest size (page title at 24px). KPI values, list titles, and table primary text must stay at or below the metric/item scale.

## Token scale (operational)

| Role | CSS variable | Size | Weight | Font |
|------|--------------|------|--------|------|
| Base body | `--kt-wb-font-body` | 14px | 400 | Inter |
| Page title | `--kt-wb-title-size` | 24px | 700 | Manrope / Hanken Grotesk |
| KPI / summary value | `--kt-wb-metric-size` | 20px | 600 | mono or headline |
| Section title | `--kt-wb-section-size` | 16px | 700 | headline |
| List/card primary | `--kt-wb-item-title-size` | 15px | 700 | body |
| Table body | `--kt-wb-table-size` | 13px | 400–500 | Inter |
| Label (caps) | `--kt-wb-label-size` | 10–11px | 600–700 | Inter / mono |
| Detail identity only | `--kt-wb-identity-size` | 32px | 700 | headline |

Line-height companions: `--kt-wb-title-line-height` (32px), `--kt-wb-metric-line-height` (26px), `--kt-wb-item-title-line-height` (22px).

## Anti-patterns (disallowed on workbench)

- Stacking multiple 24px+ elements on one screen (title + KPI + row titles all hero-scale).
- Using PP4 `display-hero` (32px) for KPI card values on operational workbenches.
- Ad-hoc literals (`38px`, `28px` toolbar titles) instead of `--kt-wb-*` tokens.
- Porting `code.html` Tailwind `text-display-hero` into deployed workbench without a harmonization CSS layer.

## PP4 mockup supersession

Procurement Planning v4 pixel mockups (`docs/prompts/procurement planning v4/workbench/*/DESIGN.md`) still list `display-hero: 32px` for design-tool export. **Deployed operational workbench** uses this document's operational scale via CSS override (see WORKBENCH_WIRING_TRACKER typography harmonization pass). Structure/layout guards remain verbatim; typography may be harmonized like the prior UI consistency pass (title link color, category chips).

## Phase 2 rollout (shipped)

| Surface | CSS file | Changes |
|---------|----------|---------|
| Planning Hub | `planning_hub_page.css` | Page title 24px, stat values 20px |
| Package Detail | `package_detail_page.css` | Keep `--kt-wb-identity` for record title; sidebar metrics 28px→20px; section cards 20px→16px |
| Package Wizard | `create_package_wizard_page.css` | Step title 28px→24px, success hero 26px→24px |
| PP4 workbench DESIGN.md files | `workbench/*/DESIGN.md` | Operational workbench uses v1.0 scale note |

Regression: `test_procurement_typography_phase2_harmony.py`.

## Phase 3 (shipped)

Refactored `budget_workbench_page.css` to consume `--kt-wb-*` for typography roles
(font aliases + title/metric/section/item/body scales). Module-local `--ktw-*`
colors, spacing, and shadows unchanged. No visual change expected.

Regression: `kentender_budget/tests/test_budget_workbench_typography_phase3.py`.

## Enforcement

- Cursor rule: `.cursor/rules/kentender-workbench-typography-harmony.mdc`
- Unit tests: `kentender_core/tests/test_workbench_typography_contract.py`, `test_pp4_workbench_typography_harmony.py`, `test_procurement_typography_phase2_harmony.py`, `kentender_budget/tests/test_budget_workbench_typography_phase3.py`
- UX: Playwright/MCP visual check when changing workbench CSS

## Related docs

- [Kentender UI System Pattern v1.0.md](./Kentender%20UI%20System%20Pattern%20v1.0.md) §12 Visual Language
- [WORKBENCH_WIRING_TRACKER.md](../procurement%20planning%20v4/workbench/WORKBENCH_WIRING_TRACKER.md) — typography harmonization pass
