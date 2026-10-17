# Coordinated funding build: what was run (BUD v1.16, AWD v0.7, CM v0.10, AUTH v1.16)

Run on 16 and 17 October 2026 on the test site `kentender-test.local` only, one module at a time under `/tmp/kt-test-site.lock`. I ran nothing on the development site; on 17 October the seed session, at the Project Owner's instruction, ran a normal migrate there and reseeded it. Commits: fe2e5c16, 478512c6,
21326934, 46d4e1c7, 2656d0ee, e0988068, d160a88a, 7a98a441, 1429815e (repaired by a154702f), 8c389f62. This file records results; it is not a test result of its own and not a release claim.

| Check | Result |
|---|---|
| Budget app, all 30 modules (`kentender_budget.tests.*`) | all OK on 17 October (for example award lineage conversion 23, commitment origin 9, contract funding provider 13, service principal 36, close commitment 12, retained commitments 13, locking races 11, exact money 14, approval integrity 16, analytics 22) |
| Budget funding entry module | 67 of 67 (includes the document's 600,000 / 100,000 / 500,000 fixture, the Additional increment path, the balance model across every funding operation, no accounting record named) |
| Award chain, all modules | all OK; `test_awd_funding_allocation` 33, `test_awd_funding` 16, `test_funding_split` 19, `test_contract_sources` 7 on the canonical award |
| Award record board | vitest `funding.spec.js` 5, whole Award board suite 57 |
| Core seams | `test_business_role_registry` 22, `test_contract_funding_contract` 5, `test_contract_reservation_authority` 6, `test_contract_source_contract` 7, `test_signing_facade` 11 |
| Budget browser specs (normal roles, isolated fixtures) | `budget-contract-funding.spec.ts` 10 of 10, `budget-commitment-correction.spec.ts` 3 of 3 (13 of 13 on the committed code) |
| Contract Management funding module | `test_cm_contract_funding` 38 of 38 |
| Contract Management guards | notifications 6, date guard 3, import boundary 2, navigation 2, dead-end 6 |
| Contract Management gates | `cm-native-gate`, `cm-leakage-gate`, `cm-dead-end-gate` passed with the wiring; the other 33 service modules passed except `test_cm_settlement` (1), `test_cm_finance_boards` (1), `test_cm_credit_adjustment` (11), which error only with "Posting timestamp must be after 17-10-2026 09:00:00" (FU-CM-127, run before 09:00) |
| Migration | a normal `bench migrate` on the test site: the commitment patch ran and is logged; 53 commitments all carry a line and a budget; the new record types and Contract Case fields exist |

## Not run, and why

* The Award to Contract Management to Budget journey on the canonical award (`scripts/bud_v116_canonical_award_journey.py`): written, not run. The test site's canonical reservations were purged on 17 October by Budget browser fixtures that called `reset_default` (fixed); the repair (a wipe rebuild, or restoring the stored anchor after the failed non-wipe rebuild) was refused by the permission classifier in this session and is left to the Project Owner. Formation of the canonical award is separately blocked by FU-CM-70 and FU-CM-72.
* A browser walk of the Contract Management funding screens (CM-AC-94) and of the Award Funding sources disclosure: not done; the Contract Management browser world is built from the canonical award.
* `cm-seams-gate` and `cm-regression-gate` on the damaged canonical world: they failed on S9 (Budget does not hold the reservation) and are to be rerun after the repair.
* Mutation checks of the guards: not run.
