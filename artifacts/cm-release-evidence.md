# Contract Management release evidence

| | |
|---|---|
| Commit | `2b401fe1` (287 uncommitted paths at the start of the run) |
| Site | `kentender-test.local` (the test site; never the dev site) |
| Started | 2026-10-16 22:49:40 +0300 |
| Finished | 2026-10-17 00:33:18 +0300 |
| Gates failed | 1 of 11 |
| Shared test-site lock | held for the whole run (`/tmp/kt-test-site.lock`) |
| Preflight | run first by every gate (`cm-preflight`: refuses a live Playwright run and the development site) |

| Gate | Result | Took | Proof level | What it covers |
|---|---|---|---|---|
| `make cm-services-gate` | Passed | 58 min 11 s | L1 synthetic upstreams, real ERPNext where the module says so | every service and board module, then the shared signing facade |
| `make cm-seams-gate` | Passed | 2 min 2 s | L2 real owners | Award's source material, the core seams, Budget's funding provider and its principal guard |
| `make cm-native-gate` | Passed | 2 min 41 s | L2 real ERPNext | the native adapter, the payment bypass guards, a two-process claim race, the readiness check |
| `make cm-leakage-gate` | Passed | 3 min 15 s | L1 + L2 | who may read what; the technical and audit readers can never act; adversarial authority |
| `make cm-dead-end-gate` | Passed | 2 min 15 s | L1 | no reader stranded on any stage; every command safe to send twice; holds and recovery |
| `make cm-regression-gate` | **FAILED** (exit 2) | 9 min 48 s | L2 regression | Award's seams, Budget's funding provider, the signing facade, the supplier-account provider and Home's structural comparison |
| `make ui-cm-fidelity-gate` | Passed | 0 min 13 s | structural | every board of the design compared with its artboard, or recorded as not compared with its reason |
| `make cm-ui-gate` | Passed | 17 min 1 s | L2 browser | the shell, the ordinary thread, formation, an existing contract, delivery and acceptance, finance, changes, close-out; then the world is cleaned |
| `make cm-demo-gate` | Passed | 2 min 44 s | L2 browser | the demonstration profiles walked as real people from the sidebar, My work and the bell |
| `make cm-persona-gate` | Passed | 2 min 5 s | L2 browser | each named person on the accepted contract, as that person, with no native-form redirect |
| `make cm-independence-gate` | Passed | 3 min 23 s | L2 independence site | the service modules on a site that holds only ERPNext, core, supplier accounts and the app |

## Platform

| | |
|---|---|
| Taken | 2026-10-17 00:33:22 +0300 |
| Repository commit | `2b401fe1` on `mvp1/dev` (287 uncommitted paths) |
| frappe | 16.12.0 |
| erpnext | 16.10.1 |
| kentender_core | 0.0.1 |
| kentender_suppliers | 0.0.1 |
| kentender_budget | 0.0.1 |
| kentender_procurement | 0.0.1 |
| kentender_contracts | 0.0.1 |
| frappe commit | none: installed as a release, not a checkout; the version above is the pin |
| erpnext commit | none: installed as a release, not a checkout; the version above is the pin |
| Python | Python 3.14.6 |
| Node | v24.15.0 |
| Database server | mariadb  Ver 15.1 Distrib 10.6.23-MariaDB, for debian-linux-gnu (x86_64) |

A change to any line above makes the earlier native, seams and release-evidence results stale for that line: run `make cm-native-gate` and `make cm-seams-gate` (and the whole `make ui-cm-release-evidence-gate` before a release) again, and say which line changed.

## Rerun of the failed gate (added by hand after the run)

`make cm-regression-gate` failed once in the run above: a Home vitest (`Home.fidelity.spec.js`, "are the sixteen the page compares, no more and no fewer") timed out at its 5-second default, and passes alone in 0.3 s. The gate was run again on the same commit `2b401fe1` with the same tree (287 uncommitted paths, unchanged) at 00:3x on 17 October 2026 under the same lock: it passed (Award 3, 1, 2 and 7 tests; Budget 13, 36 and 12; suppliers 10; signing facade 11; Home vitest 72 tests). The run above is therefore 10 of 11 gates passed, and the eleventh passed on its rerun; it is not one clean run.

What this evidence run led to before it passed (all committed): the service-module sweep and the first runs found 14 test expectations made stale by the publication tasks, the ordering rule (work that blocks leads the standing duty), Award's S9 and a paged picker, and one defect of mine (a made-up supplier number on the Debit Note, FU-CM-132).

## Not run, and why

* **Phase 13** is owner-gated and has no gate: the approval of the proposed successor documents, the legal questions (LQ-01 to LQ-06), the production rule profile, the production Trust provider, the execution and witnessing method, real notice and report channels, Finance policy confirmations, and a security review. Until they are done, the proofs above are development proofs: the signing provider, the rule profile, the Award source provider and the funding owner may be simulated, and no screen says so.
* **A contract closed against the real Budget on the canonical award** is not proved (FU-CM-118): Budget's own provider is proved and Contract Management's close-out is proved against the simulated funding owner.
* **The canonical seed world** carries no contract (FU-CM-122); the demonstration profiles stand in for it.
* **Home's browser specs** (`make ui-home-gate`) are not run as evidence: they read the canonical world as it was seeded on 5 October, and the test site's canonical world has drifted from it (the head of procurement's Home reads 2 actions, 1 waiting item and 2 oversight records where the specs expect 9, 2 and 6, because Tenders, Bid opening and Requisitions rows are missing; none of that is Contract Management's). Contract work on Home is proved by `test_cm_home_provider` and the demonstration walk. Rebuilding the world with `make seed-canonical SITE=kentender-test.local REBUILD=True` makes them an oracle again.
* **The rest of the platform's gates** (each other module's own services and browser gates) are not re-run: the regression gate above covers what Contract Management reaches into or changed in another app's world, and nothing else.
