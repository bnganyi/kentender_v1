# Progress — WP3.6 residual (Strategy idempotency, typed stale-version errors and reference generators, replay-before-authorisation in Award/Evaluation/Strategy)

| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| AUD-XC-120 | Green | kentender_strategy/tests/test_str_idempotency_envelope.py::test_same_key_with_another_payload_is_a_typed_conflict, ::test_same_key_for_another_command_is_a_typed_conflict, ::test_another_actor_replaying_a_key_is_refused_and_sees_no_result, ::test_concurrent_same_key_creates_one_plan_and_both_get_its_identity (real two-connection), ::test_a_command_without_a_key_or_expected_version_is_refused | 8753be14 | test site, module tests + Strategy app suite | Journal row now carries actor + payload hash; unique-insert claim inside the command transaction; typed STRATEGY_IDEMPOTENCY_CONFLICT / _REQUIRED / STRATEGY_VERSION_REQUIRED. Existing code also caught the wrong exception (a unique-index violation is `UniqueValidationError`, not `DuplicateEntryError`), so the old race branch never ran. |
| AUD-XC-131 (Strategy, Award, Evaluation only) | Green | Strategy: ::test_a_caller_without_the_responsibility_gets_no_replay; Award: award/tests/test_awd_command_envelope.py::test_a_replay_is_refused_when_the_actor_no_longer_holds_the_authority; Evaluation: bid_evaluation/tests/test_evl_command_envelope.py::test_a_replay_is_refused_when_the_actor_no_longer_has_the_standing_they_acted_with | 8753be14 (Strategy), a394d872 (Award), 2e1721eb (Evaluation) | test site, module tests | Needs, Planning, Requisition, Tenders envelopes left to the later pass: see Follow-ups. |
| AUD-XC-130 (Award, Evaluation, Budget references, shared series helper) | Green | award/tests/test_awd_command_envelope.py::test_two_requests_with_one_key_execute_once_and_both_get_the_result and ::test_a_stale_revision_is_the_typed_refusal_not_a_save_timestamp_error; bid_evaluation/tests/test_evl_command_envelope.py (same two names); kentender_core/tests/test_series_race.py::test_two_allocators_on_a_prefix_with_no_counter_take_different_numbers | a394d872 (Award), 2e1721eb (Evaluation), 641b6cc6 (reference allocators) | test site, module tests | Planning, Needs, Requisition, Tenders, Opening and Proceedings lock helpers and reference generators: see Follow-ups. |

## What changed

* Strategy (`strategy_idempotency.py`, `strategy_consumer_api.py`, `strategy_transitions.authorise_action`, Strategy Command Journal gains `actor` and `payload_hash`): authorise, then claim the key with a unique insert, then run; a replay needs the same actor, command and payload hash. The whitelisted commands now require an idempotency key (KT-STD-001 §11) and, on an existing version, the expected version (STR §8: "Every write command requires the expected record version"). The service functions (used by seeds and in-process callers) still accept an optional token.
* Award (`records.command`, `records.lock`): every user command passes its role check as `authorise=`; case lock, then unique-insert claim, then body; `lock` is a locking read (`get_doc(..., for_update=True)`). The supplier commands now pass the notice's case so they lock it.
* Evaluation (`records.command`, `records.lock`, journal gains `standing`): same envelope. The 47 commands authorise inside their bodies in many different ways, so instead of 47 hooks the journal records the actor's standing (active responsibilities plus chair / secretary / member of this case) when it claims the key and a replay is answered only while the actor still holds all of it.
* Budget and Strategy reference allocators: the series raise is now one atomic upsert (`kentender_core.utils.series.raise_series_to`).

## Follow-ups

1. **Other envelopes (AUD-XC-131, handled in the later pass, owned by other agents now).** Same defect shape, file:line at HEAD:
   * Needs: `departmental_needs/services/lifecycle.py` replay lookups before `actor(...)` at `:541, :609, :660, :734, :848, :893, :946` (`if replay := _existing(idempotency_key, payload)`), `_fingerprint :127` excludes the user, `_existing :141` is a key-only lookup.
   * Planning: `procurement_planning/services/envelope.py:28-61` (`fingerprint`, global key lookup in `replay_or_none`, mismatch raises `PLN_STALE_WRITE` at `:56` instead of the registered `PLN_IDEMPOTENCY_CONFLICT`), `locked :91-100` (select-for-update then plain read), `check_record_version :103`.
   * Requisitions: `procurement_requisitions/services/envelope.py:37-66` (`fingerprint`, `replay_or_none`), `locked :94-103`; replay precedes the role check at `procurement_requisitions/services/authorise.py:84` (authorise) and `:172` (revoke); the revoke / withdraw / request-correction commands share a `{requisition, reason}` payload with no command name in the fingerprint.
   * Tenders: `tenders/services/envelope.py:39-61` (`fingerprint`, `replay_or_none` with a key-only `get_value`), `locked :92-98`; `tender_command_journal.json` has no `unique` on `idempotency_key`.
   The pattern to copy is the Award envelope (`award/services/records.py::command`): authorise first, lock the root with a locking read, claim the key with a unique insert, replay only for the same actor, command and payload (typed `*_IDEMPOTENCY_CONFLICT` otherwise). The two-connection helper is `kentender_procurement/tests/two_connections.py`.
2. **Same lock helpers still read plain after the lock (AUD-XC-130, Opening and Proceedings, not assigned to this package):** `bid_opening/services/records.py:77-84` (`lock`, `for update` at `:83`) and `:100-113` (`command` reads the journal before any lock), `proceedings/services/records.py:86-93` (`lock`) and `:118-126` (`command`), `bid_submission/services/records.py:99`. Apply the Award change (`get_doc(..., for_update=True)`; claim-first journal).
3. **Reference generators still racing (AUD-XC-130):** `procurement_planning/services/references.py:64-70`, `procurement_requisitions/services/references.py:54-56`, `tenders/services/references.py:42-44` and `departmental_needs/services/lifecycle.py:345-354` take a `get_lock` and then compute `max+1` from a plain read; under REPEATABLE READ the plain read can miss a number another request just committed, so they fail on the unique index instead of taking the next number. Fix: read the maximum with a locking read after the named lock, or move them to `make_autoname` + `kentender_core.utils.series.raise_series_to` as Budget and Strategy now do.
4. **Service-level mandatory token/key (STR §8):** the Strategy service functions (`strategy_writes.*`, `strategy_transitions.transition_plan_version`) still treat `expected_version` as optional because the canonical seed and in-process tests call them directly. The whitelisted endpoints are strict. Recommended default: leave as is; making the services strict means the seeds must read the token first. No owner decision needed unless the seeds are to be strict too.
5. **Legacy journal rows.** Strategy Command Journal rows written before this change have no actor or payload hash, so a replay of an old key is now a conflict (never a silent replay of someone else's result). Evaluation rows without `standing` replay as before. Both are bounded to in-flight retries across the deploy.
6. **Snapshot create (`create_strategy_snapshot`)**: the journal key is now bound to the calling user as well; if two different downstream service users ever replay one correlation key through the whitelisted endpoint they will get a conflict. In-process callers (Planning's `strategy_gateway`) call the service directly and are unaffected.

## Needs browser check

* Strategy screens that call the commands (plan details save, structure save, submit, discard, successor, return, approve): the Vue pages already send an idempotency key and the expected version on every call (`strategyApi.js`, `runAttempt`), so no front-end change was needed, but a retry after an unknown outcome and a double-clicked Approve are worth one manual pass on the test site.

## Dev site actions needed

* `bench --site kentender.midas.com migrate` (owner, later): Strategy Command Journal gains `actor` and `payload_hash`; Evaluation Command Journal gains `standing`. No patch, no data change.

## Document follow-ups

* STR v1.9 §8.2 says the idempotency identity is "a stable command idempotency identity under KT-STD §11"; it should now also say that a key is bound to the actor, the command and the payload and that the conflict code is `STRATEGY_IDEMPOTENCY_CONFLICT` (plus `STRATEGY_IDEMPOTENCY_REQUIRED`, `STRATEGY_VERSION_REQUIRED`) in the Strategy error list.
* EVL v0.4 section 7.2 / AWD v0.5 section 7: add the order of the envelope (authorise, lock, claim, run) and, for Evaluation, the standing rule for replays.

## Commands run

All on the test site (`kentender-test.local`), each wrapped in `flock /tmp/kt-test-site.lock`; after the two JSON changes `bench --site kentender-test.local migrate` was run on the test site only.

Red runs (each failed for the stated reason before the fix):
* `bench --site kentender-test.local run-tests --app kentender_strategy --module kentender_strategy.tests.test_str_idempotency_envelope` -> 7 failed (no conflict raised; the race raised `UniqueValidationError` on the journal key).
* `... --app kentender_procurement --module kentender_procurement.award.tests.test_awd_command_envelope` -> 3 of 5 failed (duplicate-key error on the opinion row; `TimestampMismatchError` instead of `AWD_RECORD_CHANGED`; replay answered after authority was lost).
* `... --module kentender_procurement.bid_evaluation.tests.test_evl_command_envelope` -> 3 of 4 failed (same three reasons).
* `... --app kentender_core --module kentender_core.tests.test_series_race` against the old read-then-insert logic restored for one run -> `IntegrityError 1062 Duplicate entry 'ZZRACE-REF-' for key 'PRIMARY'`.

Green runs after the fix:
* Strategy app, whole: 4 + 137 + 46 tests, OK (includes the 7 new). Four existing tests that called the whitelisted submit/approve without a key or version were updated to send them.
* Award, every module under `award/tests` (27 modules, 1 skipped): all OK (includes 5 new).
* Evaluation, every module under `bid_evaluation/tests`: all OK except 5 tests in 4 modules that fail identically with the pre-change `records.py` restored (checked by swapping HEAD's file in for one run): `test_evl_canonical_seed::test_the_canonical_evaluation_is_told_with_the_default_presence_lapse` (2 errors), `test_evl_intake::test_a_final_no_bids_opening_closes_the_preparation`, `test_evl_meetings::test_a_reader_with_no_responsibility_and_no_row_gets_the_forbidden_verdict_and_a_department_head_does_not`, `test_home_provider::test_only_an_oversight_capable_responsibility_has_the_region` and `::test_the_technical_reader_and_an_unrelated_internal_user_get_nothing`. They concern reader/responsibility visibility and the canonical world, not the journal; not caused by this package. The 4 new Evaluation tests pass.
* `kentender_core.tests.test_series_race` 2 OK; `kentender_budget.tests.test_bud_chg_001_phase3_lifecycle` 19 OK; `kentender_budget.tests.test_budget_locking_races` 9 OK.

Not run: Playwright / browser (not permitted), the other modules' suites (Needs, Planning, Requisitions, Tenders, Opening, Proceedings: untouched), anything on the dev site.

Test-site residue checked after the runs: no leftover Strategic Plans, Strategy journal rows, ZZRACE series row or test users from this package.
