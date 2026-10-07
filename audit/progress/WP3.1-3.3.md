# Progress — WP3.1 + WP3.3 (Budget locking/races and approval integrity)

Commits: 6a88d4fc (AUD-BUD-004), dfb23492 (all other findings; the services were edited in the same files so they are one commit).

| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| AUD-XC-101 | Green | tests/test_budget_locking_races.py::test_two_80m_reservations_on_a_100m_line_cannot_both_succeed (+ ::test_a_reservation_waiting_on_a_reservation_decides_on_the_committed_position) | dfb23492 | test site, module + app tests | Real two-connection test (threads, own frappe.init/connect, REPEATABLE-READ). All 9 race tests FAILED on the pre-fix services (HEAD copies swapped in temporarily) and pass now. |
| AUD-XC-102 | Green | ::test_two_commitment_increases_of_20m_cannot_both_succeed, ::test_a_commitment_increase_waits_for_a_reservation_on_the_same_line | dfb23492 | test site | |
| AUD-XC-103 | Green | ::test_approval_waits_for_a_racing_reservation_and_rechecks_the_floor, ::test_a_reservation_waits_for_an_approval_and_uses_the_new_basis, ::test_closure_waits_for_a_racing_reservation, ::test_a_reservation_waits_for_a_closure_and_is_refused | dfb23492 | test site | Both orderings of approve-vs-reserve and close-vs-reserve. |
| AUD-XC-104 | Green | ::test_decision_basis_waits_for_an_approval_and_fails_stale | dfb23492 | test site, plus Planning test_plan_finance (15 OK) | Raises BUD_BASIS_STALE after waiting behind an approval. |
| AUD-BUD-003 | Green | tests/test_budget_approval_integrity.py::TestClosedBudgetStaysClosed | dfb23492 | test site | Approving an open successor of a Closed Budget returns BUDGET_CLOSED; successor creation is lock-serialised (no DB constraint, see follow-ups). |
| AUD-BUD-004 | Green | ::TestOneContractOnSeveralReservations (three tests incl. patch double-run) | 6a88d4fc | test site (migrated) | Key is now (contract, reservation). |
| AUD-XC-105 | Green | ::TestNoSelfApprovalOfTheCurrentAttempt (4 tests) | dfb23492 | test site | Latest submit event; fail closed while Submitted for approval; submit audit write not swallowed (savepoint); locked row's submitted_by rechecked after the lock. |
| AUD-BUD-001 | Green | ::TestOwnerScopeAndSourceUnit (3 tests) | dfb23492 | test site, REQ test_authorise + test_gateway_contracts OK | BUDGET_SOURCE_OU_REQUIRED / BUDGET_LINE_NOT_ELIGIBLE in check and reserve. Funding-source half only when the caller supplies one (follow-up 1). |
| AUD-BUD-002 | Green | ::TestSubmissionAttemptSnapshot (2 tests) | dfb23492 | test site (migrated) | New doctype Budget Submission Attempt; exposed as `attempts` in get_budget_version_history. |
| AUD-BUD-010 | Green | ::TestCatalogueStateOfNewLines (2 tests) | dfb23492 | test site | New lines only (see follow-up 3). |

## Follow-ups
1. BUD-BR-008 (funding source): Planning's requisition projection (`plan_requisition.py` sources) carries no `funding_source`, so Requisitions cannot send one and Budget can compare only when it is supplied. Options: Planning adds the allocation's funding source to the projection and REQ passes it (then Budget can require it); or Budget treats the line's own source as authoritative. Recommended: the first. Done meanwhile: nothing beyond the existing "compare when supplied".
2. Spec gap (BUD-003): the document is silent on Close while a Draft/Submitted successor is open. Done: an open successor can no longer be approved or submitted on a Closed Budget (BUDGET_CLOSED). Owner to decide whether Close should be refused or should decline the open successor.
3. BUD-010 scope: only NEW lines (not carried from the prior Active Version, and every line of an initial baseline) must name an Active unit and an Available funding source. Carried lines keep their frozen identity, otherwise a retired department would block every future revision. Owner to confirm. Reserve/convert/adjust do not recheck catalogue state.
4. At-most-one open successor is enforced by the Version-row lock and a locking re-read, not by a database constraint (existing dev data may hold more than one open version, which would make a unique marker column fail to migrate).
5. Cross-WP: the command-only write guard (commit 701a2edf) made every test cleanup that deletes a User Responsibility Assignment fail in tearDownClass. Fixed here only for the Budget tests (they now use `command_write_guard.purge_doc`); other apps' test bases may have the same problem.
6. `run_idempotent` still looks the key up with a plain read before running (a same-key replay racing the first call is not serialised). Not in this WP's findings.
7. Funding Source status: "Available" is treated as usable; "Draft" and "Retired" are refused for new lines.

## Needs browser check
- Approval screen: a version resubmitted by a dual-role user shows no Approve action for that user; Approve refused on a Closed Budget now returns code BUDGET_CLOSED (check the screen shows a sensible message, it uses the generic errors.status text).
- Version History tab: the API now returns `attempts`; the Vue tab does not render them yet (no UI change was made).

## Dev site actions needed
- `bench --site kentender.midas.com migrate` (new doctype Budget Submission Attempt; patch `bud_chg_001_v1_12_commitment_contract_unique_per_reservation` drops the table-wide unique index on Procurement Commitment.contract and adds unique (contract, reservation)). Applied to the test site (before its rebuild from dev, and again by the rebuild); verified table and indexes on the test site.
- After migrating dev, re-run the canonical seed validation (`make seed-canonical-validate SITE=...`): the budget seeds now pass the line's owner as the source unit; not run by me.

## Document follow-ups
- BUD v1.12 §4.6/§6: record the Budget Submission Attempt record, the `BUDGET_CLOSED` refusal when approving a successor of a Closed Budget, the (contract, reservation) commitment key, and decide the Close-with-open-successor rule (follow-up 2).
- BUD §13: `BUDGET_SOURCE_OU_REQUIRED` and `BUDGET_CLOSED` as approval outcomes.

## Commands run
- `flock /tmp/kt-test-site.lock bench --site kentender-test.local migrate` — completed; table `tabBudget Submission Attempt` present, commitment indexes as intended (re-checked after the lead's rebuild).
- `... run-tests --app kentender_budget --module kentender_budget.tests.test_budget_locking_races` — 9/9 OK after the fix. With the previous service files from HEAD temporarily swapped back in: 9 failures (all for the intended reasons); my files were then restored (git diff confirmed).
- `... --module kentender_budget.tests.test_budget_approval_integrity` — 16/16 OK.
- `... run-tests --app kentender_budget` (whole app) — all groups OK except two tearDownClass errors from the URA guard (test_bud_chg_001_phase4_scope_map, test_ovs_budget_reads); after fixing those teardowns both modules pass (4 and 5 tests OK). I did not re-run the whole app a second time.
- `... --app kentender_procurement` modules procurement_requisitions.tests.test_authorise (9 OK), test_gateway_contracts (5 OK), procurement_planning.tests.test_plan_finance (15 OK).
- Not run: seeds (seed-canonical), Playwright, dev site anything.
