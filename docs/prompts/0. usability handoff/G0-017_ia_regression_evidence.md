# G0-017 — IA regression tests (evidence)

## Goal

Close **G0-017** with **automated proof** for the procurement shell IA: **(a)** general roles see **Procurement-first** home (no Strategy/Budget peer tiles), **(b)** **G0-012** spine **ordering** in the Procurement rail (full spine for Administrator; **visible subset** ordering for roles where Desk hides many workspace rows), **(c)** **internal** authorization negatives (engine + enforcement helpers + role smoke). Tracker: **G0-017**, **LV-G0-017-02**, and sibling **LV-G0-017-01** / **LV-G0-017-03** are **Accepted**; **§5** combined **G0-010–G0-017** checkbox is **checked** (**closed**).

## Mapping (G0-017 clauses)

| Clause | LV / parent | Primary automation | Notes |
|--------|-------------|-------------------|--------|
| **(a)** Procurement-first shell | **LV-G0-017-01** (Accepted) | [apps/kentender_v1/tests/ui/smoke/procurement/g0-013-app-grid-deemphasis.spec.ts](apps/kentender_v1/tests/ui/smoke/procurement/g0-013-app-grid-deemphasis.spec.ts) | Requisitioner + Procurement Planner: no Strategy/Budget desktop tiles; Procurement tile visible. |
| **(b)** G0-012 sidebar spine order | **LV-G0-017-02** (Accepted) | [apps/kentender_v1/tests/ui/smoke/procurement/procurement-sidebar-g0-012.spec.ts](apps/kentender_v1/tests/ui/smoke/procurement/procurement-sidebar-g0-012.spec.ts) + [apps/kentender_v1/tests/ui/helpers/procurement.ts](apps/kentender_v1/tests/ui/helpers/procurement.ts) | **Administrator:** full spine + **Configuration** (strict). **Requisitioner / Planner:** `expectProcurementSidebarSpineG012(..., { omitMyWork: true, onlyVisibleSpineLinks: true })` — requires **Procurement Home** + **Procurement Journeys**, then monotonic **y** order among any other visible spine links in G0-012 order; **My Work** omitted (module gate); **Configuration** only if present. |
| **(c)** Supplier / session negatives (internal APIs) | **G0-017** (parent) | Python modules below | Portal / Website User denial path + enforcement + role matrix smoke. |

## Playwright (site: default `UI_BASE_URL` / `kentender.midas.com`)

**Command:**

```bash
cd apps/kentender_v1
npx playwright test \
  tests/ui/smoke/procurement/g0-013-app-grid-deemphasis.spec.ts \
  tests/ui/smoke/procurement/procurement-sidebar-g0-012.spec.ts \
  tests/ui/smoke/procurement/g0-014-configuration-specialist-links.spec.ts \
  --project=chromium
```

**Outcome (2026-05-15, this bench):** `12 passed` (no skips in this run).

**Credentials:** align [apps/kentender_v1/.env.ui](apps/kentender_v1/.env.ui) with [apps/kentender_v1/kentender_core/kentender_core/seeds/constants.py](apps/kentender_v1/kentender_core/kentender_core/seeds/constants.py) (`UI_REQUISITIONER_*`, `UI_PLANNER_*`, `UI_ADMIN_*`).

## Python — authorization / internal negatives (site: `kentender.midas.com`)

| Module | Command | Outcome |
|--------|---------|---------|
| `test_sec_authorization_decision_engine_0300` | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_sec_authorization_decision_engine_0300` | **9 tests OK** (includes `test_sec_0300_website_user_context_grants_for_portal`). **Note:** first run hit a **MariaDB deadlock** on cleanup; **re-run OK** — treat rare flake as environmental. |
| `test_sec_integration_authorization_1000` | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_sec_integration_authorization_1000` | **3 tests OK** |
| `test_sec_smoke_role_permissions_0800` | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_sec_smoke_role_permissions_0800` | **9 tests OK** |

## Related (already Accepted under G0-017 children)

- **LV-G0-017-03:** [apps/kentender_v1/tests/ui/smoke/procurement/g0-014-configuration-specialist-links.spec.ts](apps/kentender_v1/tests/ui/smoke/procurement/g0-014-configuration-specialist-links.spec.ts) (included in the Playwright command above).

## Out of scope

- **LV-G0-011-03** (per-role forbidden surfaces matrix) remains under **G0-011**, not **G0-017**.
