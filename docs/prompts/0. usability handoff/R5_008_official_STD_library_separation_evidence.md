<!--
  Evidence for Rectification Tracker §10 — R5-008 / LV-R5-008-01
-->
# Goal

Keep **Official STD Library** administration **governance-first** and **structurally separated** from **Tender Management** runtime workflows: librarians and approvers reach the **`std-engine`** library shell directly, while **`Governance & Configuration`** stays a complementary workspace with catalogue/import shortcuts—not a merger with TM2 Tender operations.

# Scope reviewed (2026-05-16)

| Surface | Purpose | Separation note |
|---------|---------|-----------------|
| **Procurement Workspace Sidebar → Configuration → Official STD Library** | Opens Desk **Page** `std-engine` (Official STD Library shell) | `link_type`: **Page**, not Workspace; avoids loading Tender Management chrome as the primary path. |
| **Configuration → Governance & Configuration** | Workspace with catalogue/validation-queue shortcuts (`governance_and_configuration.json`) | Complements **`std-engine`** via separate **`Workspace`** rows; catalogue/import wording stays governance-first in workspace header. |
| **Tender Management / Tender Document Readiness** (sidebar spine) | Pages `tender-management-v2` | Distinct **`link_to`** from **`std-engine`** — tender runtime/readiness stays off the Official STD Library page. |
| **`std-library` shell (`std_library_shell.js`)** | Region A headline “Official STD Library”, governance guidance strip, catalogue queues | Primary actions: **Import / Register source / Validate library** — no “create tender instance” as a primary hero CTA (absence marker retained in markup). |

# Acceptance criteria (R5-008)

1. Sidebar row **Official STD Library** resolves to **Page `std-engine`** (`procurement.json`), not **`tender-management-v2`**.
2. **Governance & Configuration** remains its own **Workspace** entry (separate **`link_to`**) beside the library page—not merged into **`std-engine`**.
3. Library Desk page presents **Official STD Library** framing and governance copy on first paint (validated in Playwright).  
4. **Automated regressions**: Python sidebar contract (`test_r5_008_*`) + Playwright PLC-R5-008-01 (this pack).

# Screenshot / review baseline

- **Manual QA** (when needed for PM sign-off): capture **Official STD Library** header + summary cards (`data-testid="std-library-page"`) after **Administrator** navigates `#` → Procurement → Configuration → Official STD Library.  
- Screenshots may be attached under `apps/kentender_v1/docs/prompts/0. usability handoff/screenshots/` when the reviewer runs a visual diff; tracker references this document as the textual baseline.

# Related references

- Module catalog: `docs/audit/module_implementation_catalog/05_std_admin.md`  
- Sidebar export: `kentender_procurement/workspace_sidebar/procurement.json`  
- Workspace content: `kentender_procurement/kentender_procurement/workspace/governance_and_configuration/governance_and_configuration.json`  
- Smoke / shell tests: `tests/ui/smoke/procurement/std-engine-route.spec.ts`, `tests/ui/smoke/procurement/std-library-shell.spec.ts`

# Evidence submitted (automated)

- Python: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_r5_008_official_std_library_separation` — see tracker §10 row.  
- Playwright (from `apps/kentender_v1`): `npx playwright test tests/ui/smoke/procurement/official_std_library_separation_r5_008.spec.ts --workers=1` — PLC-R5-008-01.
