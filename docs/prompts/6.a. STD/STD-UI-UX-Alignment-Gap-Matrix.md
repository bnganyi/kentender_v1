# STD Engine — UI/UX alignment gap matrix

Maps [UI/UX model §3–9, §14–32](6.%20std_engine_works_configuration_ui_ux_model.md) and [PRD §32](2.%20std_engine_works_configuration_full_prd_execution_grade.md) to implementation surfaces and automated tests. Status: **aligned** (met), **partial** (subset), **deferred** (explicit follow-up).

| Doc ref | Requirement (summary) | UI location / API | Primary tests |
|--------|------------------------|-------------------|---------------|
| §3.1 | Procurement IA: Governance & Configuration subtree | `kentender_procurement/workspace_sidebar/procurement.json`, `workspace/governance_and_configuration/`, `workspace/std_engine/std_engine.json` (`parent_page`) | Playwright: `std-workbench-1001.spec.ts` (Governance nav) |
| §3.2 | Entry opens workbench, not raw DocType | `/app/std-engine` shell | `std-workbench-1001.spec.ts` |
| §3.3 | Deep / bookmarkable routes | Query params `std_scope`, `std_queue`, `std_code` in [std_engine_workspace.js](../../kentender_procurement/kentender_procurement/public/js/std_engine_workspace.js) | Playwright URL restore test |
| §4–7 | KPI / scope / queue chrome | `landing.py` + JS render | `test_std_phase10_kpi_strip.py`, `test_std_phase10_scope_queue.py` |
| §8.2.4 | Queue overflow on many chips | `renderQueueBar` + CSS | Playwright viewport / overflow |
| §5 | Global header CTAs | `get_std_workbench_kpi_strip` `header_actions` + JS | Playwright `std-header-*` |
| §9 | Search & filters | filter panel | `test_std_phase10_search_filters.py` |
| §14 | Template / instance tab sets | `injectTemplateVersionDetailTabs` / `injectStdInstanceDetailTabs` | `std-workbench-1001.spec.ts` |
| §15–23 | Template tab content | `std_engine_workspace.js` + template APIs | `test_std_phase10_template_version_*.py` |
| §24–32 | Instance tab content | instance panel services + JS | `test_std_phase11_*.py`, Playwright |
| §33 | Wizards | Not primary route in v1 shell | deferred |
| §38 | a11y (labels, keyboard, not color-only) | KPI `aria-label`, queue toolbar | partial — extend Playwright |
| PRD §32.3 / AC-003 | BOQ PE vs supplier clarity | BOQ panel columns / copy | `test_std_phase13_prd_boq_ux_labels.py` |
| PRD §32.1 / AC-001 | Readiness blockers plain language | readiness panel | covered by Phase 7/11; spot-check in matrix |
| §2.4 / roles doc | Role-scoped chrome | `landing.py` visibility | `test_std_phase13_workbench_chrome_visibility.py` |

Update this table when closing gaps or deferring scope.
