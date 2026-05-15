# G0-012 — Procurement sidebar journey spine (evidence)

**Tracker:** G0-012 and LV-G0-012-01…10 are **Accepted** in [implementation tracker §5 / §18.0](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).

## Goal

Document where the **G0-012** lifecycle-first **Procurement** `Workspace Sidebar` spine is implemented, how it is verified (Python + Playwright), and how reviewers can capture **2+ role** screenshots on `kentender.midas.com`.

## Canonical fixtures (code)

| Area | Path |
|------|------|
| Procurement sidebar (ordered spine + Configuration) | `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json` |
| Boot fast-path keys (hard-refresh sidebar) | `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py` (`_KT_WORKSPACE_TO_SIDEBAR`) |
| Post-migrate sidebar re-sync | `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/after_migrate_navigation.py` |
| **Procurement Home** workspace (roles for module tile) | `apps/kentender_v1/kentender_procurement/kentender_procurement/kentender_procurement/workspace/procurement_home/procurement_home.json` |
| **My Work** workspace | `…/workspace/my_work/my_work.json` |
| Placeholder workspaces (**Bid Opening**, **Evaluation & Award**, **Contract Management**) | `…/workspace/bid_opening/bid_opening.json`, `…/workspace/evaluation_and_award/evaluation_and_award.json`, `…/workspace/contract_management/contract_management.json` |
| **Procurement Journeys** Desk Page (`procurement-journey`) | `…/page/procurement_journey/procurement_journey.json` + `public/js/procurement_journey_page.js` + `hooks.py` `page_js` |

## Spine row → mechanism

| G0-012 label | Mechanism | Target |
|--------------|-----------|--------|
| Procurement Home | Workspace link | `Procurement Home` |
| Procurement Journeys | Page link | `procurement-journey` (placeholder until R4) |
| My Work | Workspace + shortcuts | `My Work` → Demand / Procurement Plan / Package lists |
| Strategy Alignment | Workspace link | `Strategy Management` (Kentender Strategy) |
| Budget & Funding | Workspace link | `Budget Management` (Kentender Budget) |
| Demand Intake & Approval | Workspace link | `Demand Intake and Approval` |
| Procurement Planning | Workspace link | `Procurement Planning` |
| Tender Document Readiness | Page link | `tender-management-v2` (same workbench entry as TM2; distinct spine label) |
| Tender Management | Page link | `tender-management-v2` |
| Bid Opening / Evaluation & Award / Contract Management | Workspace stubs | Placeholder copy + `data-testid` markers |
| Supplier Management | Workspace link | `KTSM Supplier Registry` |
| Evidence & Audit | DocType link | `Audit Event` |
| **Configuration** (group) | Section + child links | Official STD Library (`std-engine`), Governance workspace, profiles/templates DocTypes (unchanged set) |

## Automated verification

1. **Export contract (no live site required for ordering)**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_procurement_sidebar_g0_012_contract`

2. **Boot sidebar fast-path**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_workspace_sidebar_fastpath`

3. **Playwright (sidebar order + Journeys placeholder, Administrator)**  
   From `apps/kentender_v1`:  
   `npx playwright test tests/ui/smoke/procurement/procurement-g3.spec.ts tests/ui/smoke/procurement/procurement-sidebar-g0-012.spec.ts --reporter=line`  
   (Requires Chromium + site per `playwright.config.ts` / `.env.ui`.)  
   Seeded non-admin roles do not reliably reach **Procurement Home** via the `/app` module launcher on all sites (tile / `Page` permission variance), so **second-role spine visibility** is asserted manually (§Role screenshots) rather than duplicated in CI.

## Build / cache (agent run)

- `./scripts/bench-with-node.sh build --app kentender_procurement` — **OK**
- `bench --site kentender.midas.com migrate` — **OK** (imports new workspaces / Page / sidebar)
- `bench --site kentender.midas.com clear-cache` — **OK**
- `bench restart` — **skipped / failed** in this WSL agent (no `supervisorctl` socket); run on a full bench host after deploy.

## Role screenshots (manual checklist)

On **`kentender.midas.com`**, after `bench migrate`, `./scripts/bench-with-node.sh build --app kentender_procurement`, `bench --site kentender.midas.com clear-cache`, and `bench restart`:

1. **Administrator** — open **Kentender Procurement** → **Procurement Home**; capture full left rail showing spine through **Evidence & Audit** and collapsed **Configuration**.
2. **Procurement Planner** (or **Planning Authority**) — same capture to prove non-admin roles still see the ordered spine (DocPerm may hide some targets on click; spine visibility is the contract here).

Attach PNGs to the ticket or paste paths beside this doc when archived.

## Notes

- Combined exit **G0-010–G0-017** is **closed** on the implementation tracker (**G0-017** **Accepted**); **G0-013** is **Accepted** separately ([G0-013_app_grid_deemphasis_evidence.md](./G0-013_app_grid_deemphasis_evidence.md)). This deliverable only closes **G0-012** implementation + evidence pointers.
- **G0-016** (rename Strategy/Budget workspace titles) is **not** done here: sidebar uses labels **Strategy Alignment** / **Budget & Funding** while target workspace titles remain **Strategy Management** / **Budget Management**.
