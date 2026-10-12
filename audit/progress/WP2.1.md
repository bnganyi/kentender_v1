# Progress — WP2.1 + WP2.7 (command-only write guard; Audit Event immutability pilot)
| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| AUD-XC-010 | Green | kentender_core/tests/test_audit_event.py::TestAuditEventIsAppendOnly (update, delete, insert refused for System Manager and Administrator; confirmed failing with the controller reverted to `pass`: 3 failures); kentender_core/tests/test_command_write_guard.py (13 tests; red = ImportError before the helper existed) | 701a2edf | test site kentender-test.local, module tests (see Commands run) | Helper `kentender_core/services/command_write_guard.py`. Audit Event controller = `CommandWriteGuardMixin`, family "Audit Event", no editable fields. DocPerm: System Manager and Administrator read/report/export/print/email only (write/create/delete/share removed); track_changes 0. Only writer: `log_audit_event` (opens `command_write("Audit Event")`). Only deleter: `purge_audit_events(filters, reason=)` (dev/test site, refused inside an HTTP request). |

## Adoption API for other work packages (WP2.2 onward)
```python
from kentender_core.services.command_write_guard import (
    CommandWriteGuardMixin, command_write, maintenance_write,
    guard_command_write, guard_command_delete, CommandWriteError)

class StrategicPlanVersion(CommandWriteGuardMixin, Document):   # 1. controller
    command_write_family = "Strategy"                 # shared by every doctype one service owns
    command_user_editable_fields = ("title", "summary")   # optional Draft allow-list
    command_user_insert = True                        # optional: users may create a Draft (other fields must be at default)
    def user_editable_when(self, before): return before.status == "Draft"   # optional
    def user_deletable_when(self): return self.status == "Draft"             # optional (Draft discard)
# 2. services: wrap every insert/save/delete of the family in `with command_write("Strategy"):`
# 3. remove write/create/delete DocPerm on lifecycle fields (keep read); migrate
# 4. tests: user save -> COMMAND_ONLY_WRITE; non-allow-listed field -> COMMAND_ONLY_FIELD (fields named);
#    delete -> COMMAND_ONLY_DELETE; service command still works; clean-up via maintenance_write(family, reason=...)
```
Error codes (`CommandWriteError.code`, a `frappe.PermissionError`): COMMAND_ONLY_WRITE, COMMAND_ONLY_FIELD, COMMAND_ONLY_DELETE, COMMAND_MAINTENANCE_REFUSED. Authorisation is held on `frappe.local` only; `doc.flags`, request params and posted `flags` keys are ignored (tested). A controller overriding `validate`/`on_trash` must call `super()`. The guard runs in the document controller, so `frappe.db.set_value/delete/sql`, `doc.db_set/db_insert/db_update` are not covered (in-process server code only). Full adoption steps are in the module docstring.

## Follow-ups
1. (Low, recommend later) Raw SQL (`frappe.db.delete`, `frappe.db.set_value`) bypasses any controller guard. Remaining raw Audit Event writers, all in-process dev/test/seed code, left as they were: `frappe.db.set_value("Audit Event", ..., "timestamp", ...)` in kentender_core/seeds/kentender_mvp_v1/reference_data.py:167 and kentender_strategy/seeds/kentender_mvp_v1_strategy.py:114 and kentender_strategy/tests/test_home_provider.py (seed re-dating of event times); `frappe.db.delete("Audit Event", ...)` in kentender_procurement bid_opening/seeds/clear.py, bid_opening/tests/support.py, std_templates/tests/support.py and playwright_fixtures.py, kentender_suppliers supplier_accounts/seeds/canonical.py and tests/support.py, kentender_core tests test_public_portal_settings.py and test_cfg_idempotency.py. Option: route them through `purge_audit_events` (owners of those areas, to avoid cross-WP edits now); a database trigger is the only real defence against SQL. Recommended default: leave.
2. (Test-site hygiene, not my change) Several Strategy modules cannot set up on the test site because ERPNext's `_Test Fiscal Year 2040` overlaps the FY 2040 the Strategy test base creates (NameError "Year start date or end date is overlapping"): test_str_chg_001_v1_8_usability (18 errors, includes test_self_approval_is_named_not_hidden) and test_str_discard_draft (5 errors). Not run to green, so those two modules are unverified against this change; the self-approval path itself is covered by test_str_chg_001_phase2_lifecycle (author cannot approve own version; reads Audit Event) which passes.
3. (Not mine) Pre-existing failures seen: kentender_core test_business_action and test_wave0_smoke::test_smoke_procuring_entity_exception_workflow_guard (Procuring Entity `reporting_currency` mandatory), test_authorization_gate04::test_generated_pages_are_bound_to_protected_live_services (Page rows absent on test site), test_canonical_seed (8 errors: stray fiscal years, org units, Budget on test site), kentender_strategy test_strategy_canonical_seed (extra "Approve successor" event dated now on the canonical version). None touches Audit Event writes.
4. `kentender_core/tests/test_reference_data_api.py` carries another agent's uncommitted edits (AUD-XC-017); my part of that file is committed in 701a2edf, theirs is left in the working tree.
5. Whole-app `run-tests --app kentender_core` cannot discover tests: "No module named 'kentender_procurement.procurement_lifecycle.seeds'" (another area; modules were run one by one instead).

## Needs browser check
None: no screen writes Audit Event; Home/analytics/evidence timeline only read it.
## Dev site actions needed
- `bench --site kentender.midas.com migrate` (Audit Event DocPerm becomes read-only for System Manager and Administrator; track_changes 0). The controller guard is live on dev as soon as the code is, before migrate; dev seed or Playwright clean-up helpers that called `frappe.delete_doc("Audit Event")` now use `purge_audit_events` (works on dev because `developer_mode` is on, refused over HTTP).
- Test site: migrated already (DocPerm check: 0 write/create/delete rows for Audit Event).
## Document follow-ups
- STR v1_9 line 161/636 and AUTH-ADR-001 §8 can cite the guard as the enforcement of "append-only; Administrator and System Manager read-only".
## Commands run
All on kentender-test.local, wrapped in `flock /tmp/kt-test-site.lock`, `bench --site kentender-test.local run-tests --app <app> --module <module>`:
- migrate (flock): ok.
- kentender_core.tests.test_command_write_guard: 13 tests OK (final run). test_audit_event: 7 OK. Red check with controller reverted to `pass`: 3 failed, 4 passed.
- kentender_core: test_analytics_reads_create_nothing 2 OK; test_auth_migration_inventory 7 OK; test_authorization 30 OK; test_authorization_gate02 7 OK; test_authorization_gate04 5 OK / 1 FAIL (unrelated, follow-up 3); test_business_action 1 ERROR (unrelated); test_canonical_seed 8 ERRORS of 36 (unrelated); test_cfg_chg_002_v11_business_day_calendar 10 OK; test_cfg_chg_002_v11_intake_control 19 OK; test_cfg_idempotency 4 OK; test_cfg_preview 9 OK; test_cfg_resolver 8 OK; test_procurement_settings 18 OK; test_public_portal_settings 10 OK; test_reference_data_pe_lifecycle 13 OK; test_reference_data_fy_lifecycle 7 OK; test_reference_data_context_lifecycle 20 OK; test_regulatory_reference 29 OK; test_site_configuration 35 OK; test_responsibility_administration 36 OK; test_wave0_smoke 4 OK / 1 ERROR (unrelated). test_reference_data_api 8 OK (final run). Modules not reached (loop stopped for time): test_cfg_rule_details, test_cfg_schedule_calendar_versions, test_cfg_supersession, test_cfg_technical_read, test_reference_data_seed_mvp1, test_reference_data_workspace, and the rest of the alphabet in the first loop.
- kentender_strategy: phase1_domain_model 18 OK; phase2_lifecycle 9 OK; phase3_governance 5 OK; phase4_contracts 17 OK; phase6_consumers 5 OK; test_home_provider 26 OK; v1_8_usability 18 ERRORS and discard_draft 5 ERRORS (FY overlap, follow-up 2); strategy_canonical_seed 1 FAIL (unrelated, follow-up 3).
- Whole-app kentender_core run: discovery error (follow-up 5).
