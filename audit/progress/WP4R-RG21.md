# Progress — WP4R RG-21 (reference allocators deadlock under two connections) + RG-19 lock order
| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| RG-21 | Green | kentender_procurement/tests/test_reference_allocator_deadlock.py::TestAllocatorsDoNotDeadlock (4 allocator tests: Requisition, Tender, Plan Source Allocation, Departmental Plan) | see git log "RG-21" | test site, 10 + 3 new/edited tests | Red on old code: all four failed with MariaDB 1213 (QueryDeadlockError) on one connection. |
| RG-19 (lock order) | Green | ...::TestOneLockOrderForEveryAllocator | same commit | test site | every allocator and the `services/sequence.py` helpers take `allocation_lock(<table>)` after the case lock; a sweep fails on any `get_lock`/`release_lock` outside `utils/series.py`. |

## Design (the mechanism)
`kentender_core.utils.series.allocation_lock(table)`: one `tabSeries` row per table (`kt:alloc:<Doctype>`) locked by an atomic upsert, held to commit/rollback, 10 s wait then the caller's typed error (`busy`). Order for every allocator: case/parent row lock, then `allocation_lock(table)`, then the probe/count, then the insert. `allocation_lock_all` takes several tables in sorted order. `next_free_reference` and `sequence.locked_names/next_after` and Bid Submission `_committed_count` take it themselves, so a caller cannot forget it.
Replaced: prefix-named `GET_LOCK` in Requisitions, Tenders, Planning `_next`, NDS create (which also released it before commit - now not needed), DPP root creation (`pln:dpp:ou:fy`, which locked an absent key outside the allocation lock). Also `raise_series_to(prefix, 0)` now creates the counter row so Frappe's `make_autoname` never reads an absent `tabSeries` key `for update` (same gap-lock deadlock for two first allocations in Budget/Strategy).
Why a row lock and not GET_LOCK: GET_LOCK lives until the connection closes - in tests and any long-lived worker it would block every later allocator of that table and outlive the commit.

## Follow-ups
1. Mutexes of two different tables taken in opposite order by two different commands can still deadlock (InnoDB detects it: 1213 on one request). No such command found; the rule (parent lock, then allocation lock, tables sorted when taken together) is documented in `utils/series.py`. Not audited command by command.
2. `test_pln_idempotency_envelope::test_every_command_that_replays_a_key_also_records_it` fails on `publication_pipeline.py::_publish` is not a planning_command - not caused by this change (Planning publication, another lane's file).
3. Budget/Strategy allocators still use plain `exists` probes after `make_autoname`; no lock needed there (no gap-locking read). Not changed.
4. Canonical-seed test module and Playwright not run (shared test site).

## Needs browser check
None.

## Dev site actions needed
None (no schema change; new `kt:alloc:*` rows are created on first use in `tabSeries`).

## Document follow-ups
None.

## Commands run
- `bench --site kentender-test.local run-tests --app kentender_procurement --module kentender_procurement.tests.test_reference_allocator_deadlock` : Red first (4 failed, 1213); then 10 tests OK.
- `... --app kentender_core --module kentender_core.tests.test_series_race` : 3 OK.
- Regression modules OK: bid_submission.tests.test_reference_allocation (6), tenders.tests.test_tnd_idempotency_envelope (8), tests.test_sequence (3), procurement_requisitions tests test_req_idempotency_envelope (7) + test_references (3), departmental_needs test_nds_idempotency_envelope (9). procurement_planning test_pln_idempotency_envelope: 9 OK, 1 FAIL (follow-up 2).
