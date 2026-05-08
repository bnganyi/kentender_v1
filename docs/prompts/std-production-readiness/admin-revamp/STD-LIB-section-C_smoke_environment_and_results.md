# Section C smoke — environment and results (admin revamp)

**Tracker:** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) §C (gates C1–C7)  
**Pattern:** Same capture shape as [`../workstream-1/STD-GOV-doc8_smoke_environment_and_results.md`](../workstream-1/STD-GOV-doc8_smoke_environment_and_results.md)

## 1. Environment

| Field | Captured value |
|-------|----------------|
| Test date | 2026-05-08 |
| Tester | Automated (`bench run-tests`; Playwright evidence recorded in tracker §C C1–C6) |
| Frappe site | `kentender.midas.com` |
| Custom app | `kentender_procurement` |
| WORKS POC reference template | `KE-PPRA-WORKS-BLDG-2022-04-POC` |

## 2. UI smoke / acceptance (C1–C6)

| Gate | Automated evidence | Command (from `apps/kentender_v1`) |
|------|-------------------|-------------------------------------|
| C1–C4, C6 | Playwright specs listed in tracker §C | `npm run test:ui:smoke:std-lib-0600` |
| C5 | A11y + server-policy alignment | `npm run test:ui:smoke:std-lib-0610` |

Supporting specs: `std-library-shell.spec.ts`, `std-engine-route.spec.ts`, `std-governance-workspace-nav.spec.ts` (see tracker rows).

## 3. Regression bench (C7)

| Module | Tests | Result (2026-05-08) |
|--------|-------|----------------------|
| `kentender_procurement.tender_management.tests.test_std_works_poc_step9_doctypes` | 9 | OK |
| `kentender_procurement.tender_management.tests.test_std_works_poc_step10_loader` | 16 | OK |
| `kentender_procurement.tender_management.tests.test_std_works_poc_step11_engine` | 26 | OK |
| `kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8` | 12 | OK |

**Operational note:** If two bench modules run concurrently against the same site, tests that mutate `STD Template` can hit InnoDB lock wait timeout or `TimestampMismatchError`. Re-run failing modules **sequentially** (single `--module` invocation at a time), or run **[`scripts/run-std-library-regression.sh`](../../../../scripts/run-std-library-regression.sh)** from the `kentender_v1` app tree (runs the four C7 modules in order; `STD_LIB_REGRESSION_SITE` overrides the default site). The bench checkout may also expose `./scripts/run-std-library-regression.sh` delegating to the same script.

## 4. Commands (copy-paste)

```bash
cd /home/midasuser/frappe-bench

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_std_works_poc_step9_doctypes

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_std_works_poc_step10_loader

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_std_works_poc_step11_engine

bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8
```

```bash
cd apps/kentender_v1
npm run test:ui:smoke:std-lib-0600
npm run test:ui:smoke:std-lib-0610
```

**One-shot sequential C7 regression** (from Frappe bench root, if `apps/kentender_v1` is present):

```bash
cd /path/to/frappe-bench
./apps/kentender_v1/scripts/run-std-library-regression.sh
# or: ./scripts/run-std-library-regression.sh  (wrapper in bench repo checkout)
```
