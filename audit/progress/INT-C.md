# Progress — INT-C second integration gate (core, budget, strategy, suppliers)

Site: kentender-test.local only, every run under `flock /tmp/kt-test-site.lock`, one module per call. HEAD at start afdeac99. Status: IN PROGRESS (first write, after a machine restart at 19:32 killed the session and wiped the scratchpad logs).

## Scope

156 test modules: kentender_core 101, kentender_budget 23, kentender_strategy 18, kentender_suppliers 14. Module name = path under the app directory, without the app prefix (for example `kentender_core.tests.test_audit_event`).

## Run 1 (killed by the restart): first 28 modules of kentender_core

Ran in path order, from `doctype/authorization_delegation` through `tests/test_cfg_preview`. Their logs were lost with the scratchpad, so only what was observed before the restart is recorded:

| Result | Modules |
|---|---|
| Passed (rc 0) | the 8 doctype stubs, `services.test_clock`, `test_analytics_*` (4), `test_artboard_provenance_gate`, `test_assignment_command_only`, `test_audit_event`, `test_auth_migration_inventory`, `test_authorization`, `test_authorization_native`, `test_authorization_role_registry`, `test_business_role_registry`, `test_cfg_chg_002_v11_business_day_calendar`, `test_cfg_chg_002_v11_intake_control` |
| Failed (rc 1) | `test_backfill_pe_fy_context_links` (4 errors), `test_business_action` (1 error), `test_canonical_seed` (details lost) |
| Result not seen | `test_cfg_idempotency`, `test_cfg_preview` |

Run 2 therefore restarts at `kentender_core.tests.test_canonical_seed` and covers every module after it (133 modules). Modules before it are counted from run 1 as above.

Failures seen in run 1 (triage pending confirmation in run 2):

- `test_backfill_pe_fy_context_links` (4 errors): `IndexError: list index out of range` in setUp. Looks like the same site-data cause INT-A recorded (setUp expects an Organisation Unit with a procuring entity). Unconfirmed on this rebuilt site.
- `test_business_action` (1 error): `MandatoryError [Procuring Entity, KT-TEST-BA-001]: reporting_currency` — the same fixture gap as INT-A D-1.
- Canonical validate after the first 8 modules already listed 6 Organisation Units (4 expected) and extra Fiscal Years `2101-2102` and `2103-2104`, i.e. residue from the early modules (test years >= 2100 are Tenders/Planning-style test years; which module left them was not isolated).

## Results

(to be completed after run 2)

## Follow-ups

## Commands run

- Driver: `flock /tmp/kt-test-site.lock timeout 1500 bench --site kentender-test.local run-tests --app <app> --module <module>`, one module at a time; canonical validate probe every 10 modules.
