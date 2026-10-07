# Progress — WP1.1 Departmental Needs principal, projections and reads

| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| AUD-XC-001 | Green | departmental_needs/tests/test_departmental_needs_principal.py::TestEndpointsActAsTheSessionUser (6 tests); kentender_core/tests/test_whitelisted_principal_parameters.py (repo-wide guard) | 8bc76479 | test site | Endpoints now act as `frappe.session.user` only. |
| AUD-XC-016 | Green | test_departmental_needs_principal.py::TestPlanningProjectionsAreNotWebEndpoints::test_no_projection_command_is_reachable_over_http | 8bc76479 | test site | The three projection commands are no longer web endpoints. |
| AUD-XC-140 | Green | test_departmental_needs_principal.py::TestUnknownFieldsAreRefused (2 red tests) | 8bc76479 | test site | Unknown field -> typed `DepartmentalNeedError` (HTTP 417), not TypeError/500. Only the Needs part; see Follow-ups for the journey/search `limit` part. |
| AUD-NDS-011 | Green | test_departmental_needs_principal.py::TestWithdrawalDependencyRead::test_a_person_who_cannot_read_the_need_is_refused | 8bc76479 | test site | New reader service `lifecycle.read_withdrawal_dependency` (view-scope check); internal command callers keep `check_withdrawal_dependency`. |
| AUD-NDS-003 | Green | departmental_needs/tests/test_departmental_needs_unsent_draft.py::test_the_planner_and_the_oversight_offices_do_not_receive_the_draft | 9a28582c | test site | `get_departmental_need` and the register list show the accepted revision, not the author's Draft successor, to Planner / AO / HOPF. |

## What changed

- `departmental_needs/api.py`: every endpoint that was `frappe.whitelist()(service)` is now `_whitelisted(service)`: a wrapper whose public signature has no `user` parameter (Frappe therefore discards a `user=` request field) and which refuses a direct Python call that names one. The service is called without `user`, so it resolves the principal from `frappe.session.user` (idempotency digests are unchanged). The four `**kwargs` commands (`save_need_draft`, `return/accept/decline_need_revision`) now check the request fields against the target service's own signature: unknown field -> `NDS_FIELD_REQUIRED` "Unknown field: x."; a field naming the principal -> `NDS_SCOPE_DENIED`. `_TRANSPORT_FIELDS` stripping kept.
- The three Planning projection commands (`project_need_planning_usage`, `_disposition`, `_intake`) are removed from `api.py`. The services (`services/usage.py`) are unchanged and remain the in-process seam Planning, seeds and tests call with an explicit principal (Planning still passes `user="Administrator"`; no Planning edit was needed). No JS, Playwright or other caller used the HTTP routes.
- `services/lifecycle.py`: new `read_withdrawal_dependency(need, accepted_revision, user=None)` (actor + `require_view`); the whitelisted `check_accepted_need_withdrawal_dependency` points at it.
- `services/permissions.py` `can_read_unsent_draft`; `services/workspace.py` `_shown_revision` used by `get_need` (`current_revision`) and by the register rows (title/quantity/required-by).
- New repo-wide guard `kentender_core/kentender_core/tests/test_whitelisted_principal_parameters.py` (static AST scan of decorated functions in every `kentender_*` app + a scan of Frappe's `whitelisted` registry, which sees aliases/wrappers). Allow-list: the three `responsibility_api` `user` parameters (grantee, not actor). Retired Tender Management v2 (`kentender_procurement.tender_management`) is tolerated by prefix until it is deleted (AUD-XC-003 owner).
- `test_departmental_needs_contracts.py` updated: projection commands no longer in `COMMAND_CONTRACTS`; their idempotency-key exemption removed.

## Follow-ups

1. AUD-XC-140 second half (journey_api `limit`, `responsibility_api` `limit_page_length`, `technical_search` `limit`) is outside the Needs area and was not changed. Recommended default: a small shared `clamp_limit(value, default, maximum)` helper in `kentender_core` used by the three endpoints. Not started; row stays Green only for the Needs part.
2. Typed refusal code for an unknown field: NDS §9 is a closed set of fifteen codes with no "invalid request". I used `NDS_FIELD_REQUIRED` (unknown field) and `NDS_SCOPE_DENIED` (field naming the principal). Recommended: owner confirms, or the document adds an `NDS_INVALID_REQUEST` code.
3. The guard test tolerates `kentender_procurement.tender_management` (AUD-XC-003). Whoever deletes Tender Management v2 should delete the `RETIRED_TENDER_MANAGEMENT_V2` constant and its two uses from the guard test.
4. Residual, not fixed: the Home provider's "Records you oversee" row (`home_provider._oversight`) uses `facts.title(need)` (the current revision's title) for AO/HOPF on an Accepted Need whose update was *returned* to the author (the author then holds an edited Draft copy). `update_state` excludes a plain unsent Draft, so the AUD-NDS-003 case is covered, but a returned-and-being-corrected update can show the copy's title. Recommended default: use `_shown_revision` there too. Not changed (outside the finding's named read path); `my_work_provider` and `analytics_provider` were not examined for this.
5. The audit finding XC-016 wording "technical-principal-only" was not adopted: AUTH §8 says technical roles decide nothing and there is no registered-producer identity mechanism, so the safest reading of NDS §7.5 ("registered Planning producer only") is no web route at all.

## Needs browser check

- Needs workspace register, a Need's detail page, Save draft (first save and later save), Submit, Accept/Return/Decline from the review screen, withdrawal request/decision, and the "Planning status" panel: the Vue code sends no `user` and only service fields, but a live run after deploy is the only proof the stricter field check does not refuse a field the screen sends. As Planner / AO / HOPF open an Accepted Need that has an author's Draft update: the page should show the accepted requirement, not the draft title.

## Dev site actions needed

- None (no schema, DocPerm, patch or seed change). A normal restart/clear-cache is enough for the Python change.

## Document follow-ups

- NDS v1.16 §8.2 lists `project_need_planning_usage`, `_disposition`, `_intake` as commands "called through the endpoint"; they are now in-process service seams only (NDS §7.5 "registered Planning producer only"). Next NDS version should say so and drop "or administrative principal" (AUTH §8).
- NDS §9: add an invalid-request code (or say which existing code an unknown field uses).
- AUTH-ADR-001 §5.5 could state that no whitelisted function takes an acting-user parameter (now enforced by the repo-wide guard test).

## Commands run

- Red run: `bench --site kentender-test.local run-tests --app kentender_procurement --module kentender_procurement.departmental_needs.tests.test_departmental_needs_principal` -> 15 tests, 12 failures + 4 errors (before the fix); 3 tests that pin existing behaviour passed.
- Green: same module -> 13 tests OK; `...test_departmental_needs_unsent_draft` -> 2 OK (the NDS-003 test was red in the same first run: fail at `current_revision.title == private title`).
- `kentender_core.tests.test_whitelisted_principal_parameters` -> 4 tests OK.
- NDS module sweep on the test site (each module run once, after the change): analytics_provider 13 OK; audit_and_notifications 13 OK; dead_end_matrix 1 OK; domain_model 24 OK; events 18 OK; lifecycle 76 OK; my_work 13 OK; navigation 13 OK; permissions 42 OK; static_scan 12 OK; ovs_needs_reads 5 OK; contracts 51 OK (1 skipped) after one fix of my own (the static `**kwargs` forwarding test flagged my wrapper; fixed and re-run).
- Failures seen, NOT caused by my files, and NOT baseline-verified (I could not run HEAD-without-my-change; git stash is forbidden): `test_departmental_needs_architecture` 2 failures (both name `procurement_planning/seeds/kentender_mvp_v1.py`, a file I did not touch, importing Needs seeds / reading `Departmental Need`); `test_departmental_needs_seed::test_the_cleared_variant_supplies_no_plan_references` (usage "Fully included" vs "Not included", canonical seed world state); `test_home_provider` 3 failures, all about `julia.njeri` (Acting Head, window 1 Oct-30 Nov 2026) getting no `my_work` rows, i.e. assignment/clock data, none about revisions or endpoints.
- Final re-run after the last edit: principal 13 OK, contracts 51 OK, unsent_draft 2 OK, permissions 42 OK, ovs_needs_reads 5 OK, core guard 4 OK.
- Not run: Planning module tests (Planning still calls the unchanged services with `user="Administrator"`; no Planning file was edited), Playwright.
