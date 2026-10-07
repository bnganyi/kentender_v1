# Progress — WP1.2 Budget service principals (AUD-XC-002, AUD-XC-012, AUD-BUD-012, AUD-BUD-013)

| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| AUD-XC-002 | Green | kentender_budget/tests/test_budget_service_principal.py::TestPrincipalMatrix, ::TestNoWebSurface, ::TestRequisitionsRelease, ::TestContractPrincipal | 94f1c9ba (dia_budget_control.py deletion landed in 9c7c9a6d, a concurrent session's commit swept my staged `git rm`) | test site: new module 29/29; kentender_budget app 175/176 (the 1 failure is unrelated, see Notes); REQ authorise/lifecycle/gateway + Planning gateway tests green | Whitelist removed from the 4 wrappers (+ check/reserve); dia_budget_control module deleted (no caller). Allow-list matrix + idempotency journal implemented. |
| AUD-XC-012 | Green | same file::TestCheckReserveCaller | 94f1c9ba | same | FCO/HOPF session path removed; calling_module comes from the principal; caller_reference must equal the principal's requisition. Inverted the old `test_finance_confirmation_officer_still_permitted`. |
| AUD-BUD-012 | Green | same file (TestPrincipalMatrix::test_a_caller_cannot_be_forged, ::test_only_the_owning_gateways_and_seeds_mint_principals) | 94f1c9ba | same | Mechanism: `kentender_budget/services/budget_service_principal.py` — a `ServiceCaller` object only `service_caller()` can mint (not constructible from a web request), checked against an allow-list of (principal, action); error `BUDGET_DOWNSTREAM_FORBIDDEN`. Repo test fails if any non-seed, non-test file other than Requisitions' funding_gateway mints a principal. |
| AUD-BUD-013 | Green | same file::TestCheckReserveCaller::test_the_token_is_bound_to_the_actor_who_checked, ::test_the_token_is_bound_to_the_requisition_that_checked, ::test_a_budget_revision_between_check_and_reserve_makes_the_check_stale | 94f1c9ba | same | Token now carries actor, requisition and per-line Budget Version; a real governed revision (successor, submit, approve) between check and reserve gives BUDGET_CHECK_STALE. |

Red run (before the fix): 29 tests, 9 failures + 88 errors (TypeError on the new `caller` argument; endpoints still published; no-principal calls succeeded).

## Step 0 — caller inventory (WP0.3)
Searched every Python, JS, Vue, TS, JSON and HTML file in all kentender_* apps (excluding docs/, audit/, archive/, node_modules, dist). JS/Vue/TS callers: none (no browser caller of any of these routes exists).

| Function | Caller (file:line at HEAD before the change) | Kind | Principal now |
|---|---|---|---|
| check_funding | procurement_requisitions/services/funding_gateway.py:45 (via authorise.py:112; seeds/profiles.py:480) | production + seed | Requisitions |
| reserve_funding | funding_gateway.py:54 (authorise.py:118; seeds/profiles.py:485) | production + seed | Requisitions |
| release_reservation | funding_gateway.py:60 (authorise.py:192 revoke_unconsumed_authorisation; seeds/profiles.py:174 demo clean-up) | production + seed | Requisitions (own whole unconverted reservation) |
| release_reservation | api/dia_budget_control.py (whitelisted `release_reservation(reservation_id, reason)`) | no in-repo caller (only an archived docs/audit seed that imports names that no longer exist) | module deleted |
| convert_reservation / release / revalidate / check / reserve | budget seeds: seeds/kentender_mvp_v1_portfolio.py (7 sites), seeds/playwright_ui_fixtures.py (6 sites) | seeds | Requisitions for holds; Contract for conversion/unused release; Budget-internal for revalidate (seed-minted, repository test allows seed files) |
| all six | budget tests: test_bud_chg_001_phase3_check_reserve, test_check_reserve_requisition_caller, test_check_reserve_v110_requisition_array, test_bud_chg_001_v19_usability, test_analytics_provider | tests | updated to pass principals |
| all six (HTTP) | api/budget_api.py wrappers (whitelisted) | web | removed |
| contract inspection only | procurement_requisitions/tests/test_gateway_contracts.py:43 (asserts check_funding parameter names); planning tests/test_gateway_contracts.py:49 (asserts Planning no longer imports them) | tests | param list updated (`calling_module` -> `caller`) |
No production caller exists for convert_reservation, adjust_commitment, or revalidate_reservations (Contract Management has no module; revalidation has no trigger yet).

## Follow-ups
1. **Contract principal has no production caller** (no Contract Management module). Capability is allow-listed and tested directly; Budget checks the caller's contract equals the conversion/adjustment contract and that a commitment for that contract exists before releasing, but cannot verify the contract event or "exact allocation" against a Contract record. Recommended: when Contract Management is built, mint the principal only in its gateway and add its event validation. Done instead: tests + repository mint guard.
2. **"Only before Tender Preparation consumed the handoff"** cannot be checked inside Budget (Budget may not read Requisitions/Tenders records; dependency direction). Enforced where it already lived — `revoke_unconsumed_authorisation` under the handoff row lock — plus, in Budget, only the creating requisition may release, only the whole reservation, only if nothing was converted. Recommended default: keep as is.
3. **Principal minting is a convention, not a security boundary**: any Python in-process code can call `service_caller()`. Mitigated by (a) no whitelisted surface can supply one, (b) a repository test that fails on any unexpected mint site. Alternative (owner choice): frame inspection or a signed token; not done (judged over-engineering).
4. **Planning's budget-revision principal still uses a different mechanism** (`frappe.flags["kt_budget_service_principal"]` in budget_revision_request_contracts.py, BUD-BR-027). Recommended: later move it onto `ServiceCaller` for one mechanism. Not changed (outside these findings).
5. **Ledger wording**: release/convert/adjust ledger rows now record `calling_module` = the principal's label ("Procurement Requisitions", "Contract Management") instead of the free-text event type; the event type is no longer on the ledger row (it is part of the idempotency payload digest only), the event id stays in `downstream_reference`. Owner may want the event type back on the row (`reason`) — I held back because the funding-activity UI shows `reason`.
6. **Concurrency (AUD-XC-101..104) not touched**, not worsened. The idempotency journal is a read-then-insert (same family as XC-101..104); the later locking work package should cover it.
7. Seeded `BUD-SC-*` holds now read as Requisitions-created (`calling_module` "Procurement Requisitions", caller_reference `BUD-SC-*-HOLD`) instead of Planning-era with a blank caller; no UI/code keyed on the old value was found.
8. New typed codes used that are not in BUD §13: `BUDGET_RELEASE_EXCEEDS_REMAINDER` (release larger than the remainder is now refused instead of silently clamped), `BUDGET_IDEMPOTENCY_CONFLICT` on convert of an existing (reservation, contract) with a different amount; a missing downstream event or idempotency key uses `BUDGET_DOWNSTREAM_FORBIDDEN`. Needs a document decision.
9. `test_budget_canonical_seed::test_the_seeded_world_validates` fails on the test site ("year2 version list ['Draft','Active']") — test-site data state (next-year Draft present), unrelated to this change; not investigated.

## Needs browser check
None required: no screen calls these functions. Funding Activity ledger labels change for newly created release/convert/adjust events (see follow-up 5) — worth one look at Budget > Funding Activity after the next seed.

## Dev site actions needed
No migrate or patch (no schema change). `make seed-canonical` / Budget Playwright fixture resets on dev will use the updated seed callers; old rows are unaffected. The `/api/method/kentender_budget.api.budget_api.{check_funding,reserve_funding,release_reservation,convert_reservation,adjust_commitment,revalidate_reservations}` and `kentender_budget.api.dia_budget_control.release_reservation` routes disappear on the next dev restart/reload.

## Document follow-ups
- BUD §7 / BUD-BR-015 / §12.6: record the mechanism (a minted `ServiceCaller` validated against a (principal, action) allow-list; refusal `BUDGET_DOWNSTREAM_FORBIDDEN`), the Requisitions/Contract matrix, that check/reserve are Requisitions-only, and that revalidation is Budget-internal.
- BUD §13 error vocabulary: add `BUDGET_RELEASE_EXCEEDS_REMAINDER`; decide the code for "missing event/key".
- BUD §8.3: token binds actor, requisition and line Budget Versions (implemented).
- docs/mvp-1 teardown inventories still list `dia_budget_control.py` (historical).

## Commands run
- Red: `flock /tmp/kt-test-site.lock bench --site kentender-test.local run-tests --app kentender_budget --module kentender_budget.tests.test_budget_service_principal` — 29 run, 9 failures, 88 errors (expected).
- Green: same command — 29 run, OK.
- `... run-tests --app kentender_budget` (whole app) — integration category 3 run, 1 failure (test_budget_canonical_seed::test_the_seeded_world_validates, pre-existing data state); unspecified category 164 OK; old-style category 12 OK.
- `... run-tests --app kentender_procurement --module kentender_procurement.procurement_requisitions.tests.test_authorise` — 9 OK; `...test_gateway_contracts` — 5 OK; `...test_lifecycle` — 12 OK; `kentender_procurement.procurement_planning.tests.test_gateway_contracts` — 3 OK.
- Probe: unauthenticated POST to the removed routes on the test server returns 417 (not exposed); an authenticated browser/session probe was not run.
- Not run: Playwright; Requisitions/Planning full suites; the dev site.
