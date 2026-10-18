# Cancellation recovery — what was built, and what proves it

Built 17–18 October 2026 for the whole-Tender cancellation recovery (PLN v1.32, TPR v0.21 carried by v0.22, REQ v1.20, BUD v1.17). The four documents carry the same twelve acceptance rows, so this one table answers all four (`PLN-CR-AC-001` to `-012`, `TPR-…`, `REQ-…`, `BUD-…`).

This is **code complete, test-site evidence, and the development site migrated and recovered on 18 October 2026** (section "The development site" below). Nothing is released to production and nothing was pushed. Approval of the documents closed none of these rows.

## How to read the evidence

- **Real adapters** means the test ran the real Planning, Requisitions, Tenders and Budget code on `kentender-test.local`, not a stand-in for one of them. The two shared fixtures are CR-F01 (one source, 60 of 100 units, KES 6m of KES 10m) and CR-F02 (two source departments, 40 units / KES 4m and 60 units / KES 6m, two reservations on one Budget Line).
- **Met** only when the test or run named was seen to pass. **Partial** says exactly what was not shown. **Not run** means no run exists.
- The test site is `kentender-test.local`, one module at a time under the shared lock.

## Acceptance map

| Row | What it requires, shortly | Status | Where it is shown |
|---|---|---|---|
| 001 | A verified cancellation of a complete, unused source set restores the exact original quantities and values, releases every hold once, keeps the scope lock | **Met** | Integration, CR-F01 and CR-F02, the last test of each (`test_cancellation_recovery_integration`); Planning half `test_cr_f01_the_exact_draw_is_restored_and_the_lock_is_kept`; Budget half `test_both_reservations_on_one_line_release_exactly_once` |
| 002 | A recommendation, failed opening, missing answer, stale source, wrong Version, omitted or foreign reservation or surviving obligation produces no recovery effect; unavailable evidence stays Pending; a proved conflict is Needs attention | **Met**, one path shown by construction | Unavailable evidence stays Pending; an Award notice or package, a converted or other-reason reservation, and a different lineage each stop at Needs attention and move nothing (integration). A recommendation registers nothing (`test_open_period`). Budget refuses another requisition's reservation and a wrong line or amount (`test_budget_cancellation_release`). A failed opening has no path to the recovery: the only caller is the Accounting Officer's cancellation, and a test pins that only Tenders' gateway may call it. No test cancels a failed opening and looks |
| 003 | A crash before commit leaves both balances unchanged; after commit and before acknowledgement the same complete result comes back; cancellation stays committed | **Partial** | A failure on either owner leg commits neither effect, and Planning refusing after Budget ran undoes Budget (integration). The same key after commit returns the recorded result. The Tender stays Cancelled in every failure case. A killed process was not simulated; the failures are raised exceptions |
| 004 | Concurrent retry or new key cannot duplicate an effect; the same key with changed facts conflicts; two sequential draws restore only their own amounts | **Met** | Replay, new key and changed facts in Planning, Budget and Requisitions; two sequential draws (`test_two_sequential_draws_restore_only_their_own_amounts`); two workers on one recovery with two real connections (`TestTwoWorkersAtOnce`) |
| 005 | A notice, contract or conversion racing the cancellation or the recovery serialises on current evidence; one wins | **Partial** | Recovery against a Budget conversion, both orders, with two real connections (`TestRecoveryAheadOfConversion`, `TestConversionAheadOfRecovery`). Cancellation takes the Tender and then the Award case in the global lock order, and Award's guard re-reads under the lock (lock-order recorder). No two-connection test races the cancellation against Award issuing a notice |
| 006 | A partial legacy release or reversal, another release reason or a conversion blocks blanket recovery; nothing is guessed, compensated or restored by hand | **Met** | `test_cancellation_recovery_legacy` (inventory, dry run, other-reason, surviving obligation, unmapped, applied twice); no screen has a restore or release button (browser spec) |
| 007 | A pending or unresolved recovery blocks new authorisation only for the affected sources; completion creates no replacement | **Met** | `test_an_unrelated_item_is_still_usable`, `test_a_held_source_refuses_the_second_authorisation_and_names_why`, `test_a_needs_attention_recovery_refuses_it_with_the_invalid_code`; no requisition is created by completion |
| 008 | A fresh requisition uses the restored scope with fresh identities and ordinary approvals; new sources and bigger ceilings stay refused across Plan successors; the scope lock is never reset | **Met** | Integration (fresh Requisition, fresh handoff and reservation, old recovery replay leaves the new balances alone); Planning `test_a_successor_plan_version_remembers_what_was_drawn`, `test_the_ceiling_is_not_redrawn_after_a_successor`, `test_the_restoration_survives_a_plan_successor` |
| 009 | Notices, reporting and Bid Opening handling go on independently; recovery reads expose no sealed or unrelated evidence | **Met** | The cancellation's compliance task stays open and its notice obligations stay due while a recovery is Pending or Needs attention (`assert_nothing_moved` in the integration module, used by both); the cancellation compliance tasks and obligations behave as before (`test_open_period`); Bid Opening pre-session, dead end and leakage, and Award authority and cancellation suites pass unchanged; the recovery reads carry amounts, statuses and permitted source rows only (`test_a_departmental_reader_sees_only_the_permitted_rows`, `test_who_may_read_the_recovery`) |
| 010 | A closed-year recovery changes historical balances only | **Partial** | Budget records a closed Budget's context and gives no spending authority (`test_a_closed_budget_records_its_closure_and_gains_no_spending_authority`). No Requisitions-to-Planning run was made against a closed year |
| 011 | Every existing permitted owner screen shows Pending, Completed or Needs attention with exact amounts, a real next step and permitted links; no page claims restoration before the whole transaction commits | **Met** for the screens named below; two states not walked in a browser | Python reads for each owner (integration), component tests, and `tnd-cancel-recovery.spec.ts` (below). Not walked in a browser: the Budget line in Needs attention, and browser back and forward on these sections |
| 012 | Single-source and shared-Budget-Line fixtures pass the same transaction and replay checks against real adapters | **Met** | Integration, CR-F01 and CR-F02 |

## Screens (row 011)

Four owner screens carry one labelled section, **Unused allowance and funding**, in each owner's own words; Planning shows it on two screens. Nothing on any of them restores, releases or edits anything.

| Owner | Screen | Component test | Server read test |
|---|---|---|---|
| Tenders | Cancel Tender / cancelled detail | `OpenPeriodScreens.spec.js` | integration |
| Requisitions | Authorised requisition | `AuthorisedRecovery.spec.js` (4) | integration |
| Planning | Procurement progress; Plan Item | `ProgressScreen.spec.js` (4 new), `PlanItemEditorScreen.spec.js` (4 new) | integration |
| Budget | Budget line detail | none (the screen has no component test file) | integration |

The browser spec is `tests/ui/smoke/tenders/tnd-cancel-recovery.spec.ts`. It ran on the test site against the rebuilt bundles and **passed, 2 of 2 (5.2 minutes), with no page console errors on any screen**.

- **Test 1.** The Accounting Officer cancels a published Tender through the screen. The screen re-renders in place as "Cancelled" and shows **Restoring unused allowance and funding** (Pending), with no "start again" link and the identifiers collapsed under Technical details; a reload keeps it. The Budget line shows the reservation as **Being released after tender cancellation** and "Nothing is released from this screen.", and no release table yet. The Requisition (as the Head of Procurement Function) and Planning's Procurement progress (as the Planner) say Pending in their own words. The worker is then run the way the scheduler runs it (the test site has no scheduler). Every screen then reads Completed: the Tender screen lists both source rows with KES amounts, the Requisition says "Unused allowance and funding restored" with its next step, Planning's progress row says "Unused allowance restored after tender cancellation", and the Budget line lists the release.
- **Test 2.** A reservation is released for another reason first. The recovery stops at **Needs attention** with that real reason on the Tender screen (which has no button at all in the section), the Requisition, Planning's progress and the Plan Item itself, and none of them offers a next step.

## Design-match gates and the existing screen specs

`make fidelity-affected` named four design-match gates as due. They were run directly with Playwright against the test site (the make targets' own restore step points at the development site, so they were not used).

| Gate | Result |
|---|---|
| Tenders: `tenders-fidelity.spec.ts` (14 boards) with `tnd-cancel.spec.ts` (4, carrying the new warning wording) | 18 of 18 |
| Planning: `planning-fidelity.spec.ts`, `pln-item.spec.ts`, `planning-publication.spec.ts` | 42 passed, 2 skipped, 3 failed — all three failures are on the publication form (see the owner list), none on a screen this work changed |
| Requisitions: `requisitions-fidelity.spec.ts` | 5 of 5 |
| Budget: `budget-fidelity.spec.ts` | 12 of 12, after the line-detail check failed first on the commitments card built on 16 October and never registered as a departure; I registered it |

The new section has no design board. It is built from the specification's own wording, so it is registered nowhere as a departure; the fidelity fixtures do not render it (no recovery exists in them), which is why no gate noticed it.

## Legacy reconciliation on the real canonical data

Run on 18 October 2026 against `kentender-test.local` (a copy of the development site), inside one database transaction that was **rolled back at the end** so nothing was kept (a check afterwards confirmed every count was back to its starting value). The script is the same code the two make targets call: `make cancellation-recovery-inventory` and `make cancellation-recovery-reconcile` (dry run unless `APPLY=1`).

| Step | Result |
|---|---|
| Inventory | 2 cancelled Tenders, both **eligible**: TND-MOH-2026-007 (10 units, KES 25,000,000) and TND-MOH-2026-012 (80 units, KES 12,000,000). None already registered, partial, converted, released for another reason, unmapped or ambiguous |
| Dry run | "would register" for both; no row written |
| Apply, first run | Both registered (Origin "Legacy reconciliation", version `CR-LEGACY-1`), with a hold on each source |
| Worker | Both **Completed**: both drawdowns Reversed, both reservations Released, both holds removed |
| Apply, second run | Both skipped ("already registered"); the worker did nothing (`acted` false); every row count and balance unchanged |

What this meant for the development site is in the next section.

## The development site (18 October 2026)

Done on the Project Owner's instruction "Migrate now", recorded in his words in the owner list.

| Step | Result |
|---|---|
| `bench migrate` | One pending patch (`pln_chg_001_v132_drawdown_allocation_id`, mine) and the four new records (Cancellation Resource Recovery with its source rows, Plan Cancellation Recovery Hold, Reservation Cancellation Release) created. No other patch was pending. No tracked file changed |
| Inventory | Same as the test site: 2 cancelled Tenders, both eligible |
| Reconciliation, applied | CRR-308860 (TND-MOH-2026-007) and CRR-308863 (TND-MOH-2026-012) registered, origin "Legacy reconciliation". A second run skipped both |
| Worker, run once by hand (the Technical Operator's job, per the owner's decision) | Both Completed: both drawdowns Reversed, both reservations Released |
| Effect on the two Budget lines | MOH-BL-0005: reserved KES 52,000,000 to 27,000,000, available 28,000,000 to 53,000,000. MOH-BL-0006: reserved 23,000,000 to 11,000,000, available 7,000,000 to 19,000,000 |
| The test site afterwards | It had been brought to the same recovered state to see what the tests make of it; that made its own canonical check fail on the same line for everyone, so it was reseeded (`make seed-canonical SITE=kentender-test.local REBUILD=True`, ok, validates). The reseed cancels the two demo Tenders through the real command and leaves their recoveries Pending, as designed |
| Canonical world check on dev | One line now fails: "a recorded event is later than the anchor" (the recovery's Budget events are dated 18 October, the anchor is 16 October 10:00). Every other check passes. Any real action on the seeded world does the same; a reseed takes a new anchor |

## Test runs

All on `kentender-test.local`, one module at a time under the shared lock, 18 October 2026. Pass counts are as printed by the runner.

| Module | Result |
|---|---|
| Planning `test_cancellation_recovery` | 20 of 20 |
| Budget `test_budget_cancellation_release` | 15 of 15 |
| Budget `test_budget_service_principal` | 36 of 36 |
| Requisitions `test_cancellation_recovery_integration` (CR-F01, CR-F02 on the real adapters) | 20 of 20 |
| Requisitions `test_cancellation_recovery_concurrency` | 8 of 8 |
| Requisitions `test_cancellation_recovery_legacy` | 6 of 6 |
| Tenders `test_open_period` | 14 of 14 |
| Tenders `test_tender_schema` | 6 of 6 |
| Tenders `test_partial_requisition_remainder` | 1 of 1 |
| Requisitions `test_authorise` | 10 of 10 |
| Planning `test_plan_progress` | 16 of 16 |
| Budget `test_bud_chg_001_v19_usability`, `test_budget_retained_commitments`, `test_ovs_budget_reads`, `test_bud_chg_001_phase3_check_reserve`, `test_budget_funding_read` | 20, 13, 5, 8, 2 — all pass |
| Component tests (vitest) for Requisitions, Tenders, Planning and Budget | 697 of 697 (50 files) |
| Playwright `tnd-cancel-recovery.spec.ts` | 2 of 2 |

Earlier phases also ran, and passed, Planning `test_drawdown_races`, `test_rest_bypass_guard`, `test_planning_v123_schema`, `test_plan_requisition` and `test_plan_requisition_v111`; Requisitions gateway, command-only, schema, idempotency and API-request modules; Tenders gateway, command-only, fixture-scope, seed-clear, snapshot, handoff-consumption and dead-end modules; Award authority and cancellation; Bid Opening pre-session and dead end.

**Failing, and not caused by this work** (details in `CANCELLATION_RECOVERY_OWNER_ATTENTION.md`): Requisitions `test_read` (1 of 15) and Tenders `test_read` (5 of 11).
