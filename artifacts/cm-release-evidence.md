# Contract Management release evidence

| | |
|---|---|
| Commit | `02c15f1a` (25 uncommitted paths at the start of the run) |
| Site | `kentender-test.local` (the test site; never the dev site) |
| Started | 2026-10-17 11:01:54 +0300 |
| Finished | 2026-10-17 12:25:16 +0300 |
| Gates failed | 0 of 11 |
| Shared test-site lock | held for the whole run (`/tmp/kt-test-site.lock`) |
| Preflight | run first by every gate (`cm-preflight`: refuses a live Playwright run and the development site) |

| Gate | Result | Took | Proof level | What it covers |
|---|---|---|---|---|
| `make cm-services-gate` | Passed | 50 min 4 s | L1 synthetic upstreams, real ERPNext where the module says so | every service and board module, then the shared signing facade |
| `make cm-seams-gate` | Passed | 1 min 27 s | L2 real owners | Award's source material, the core seams, Budget's funding provider and its principal guard |
| `make cm-native-gate` | Passed | 1 min 55 s | L2 real ERPNext | the native adapter, the payment bypass guards, a two-process claim race, the readiness check |
| `make cm-leakage-gate` | Passed | 2 min 9 s | L1 + L2 | who may read what; the technical and audit readers can never act; adversarial authority |
| `make cm-dead-end-gate` | Passed | 1 min 31 s | L1 | no reader stranded on any stage; every command safe to send twice; holds and recovery |
| `make cm-regression-gate` | Passed | 7 min 32 s | L2 regression | Award's seams, Budget's funding provider, the signing facade, the supplier-account provider and Home's structural comparison |
| `make ui-cm-fidelity-gate` | Passed | 0 min 5 s | structural | every board of the design compared with its artboard, or recorded as not compared with its reason |
| `make cm-ui-gate` | Passed | 12 min 42 s | L2 browser | the shell, the ordinary thread, formation, an existing contract, delivery and acceptance, finance, changes, close-out; then the world is cleaned |
| `make cm-demo-gate` | Passed | 2 min 5 s | L2 browser | the demonstration profiles walked as real people from the sidebar, My work and the bell |
| `make cm-persona-gate` | Passed | 1 min 26 s | L2 browser | each named person on the accepted contract, as that person, with no native-form redirect |
| `make cm-independence-gate` | Passed | 2 min 26 s | L2 independence site | the service modules on a site that holds only ERPNext, core, supplier accounts and the app |

## Platform

| | |
|---|---|
| Taken | 2026-10-17 12:25:17 +0300 |
| Repository commit | `64ff61e2` on `mvp1/dev` (33 uncommitted paths) |
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

## Not run, and why

* **Phase 13** is owner-gated and has no gate: the approval of the proposed successor documents, the legal questions (LQ-01 to LQ-06), the production rule profile, the production Trust provider, the execution and witnessing method, real notice and report channels, Finance policy confirmations, and a security review. Until they are done, the proofs above are development proofs: the signing provider, the rule profile, the Award source provider and the funding owner may be simulated, and no screen says so.
* **A contract closed against the real Budget on the canonical award** is not proved (FU-CM-118): Budget's own provider is proved and Contract Management's close-out is proved against the simulated funding owner.
* **The canonical seed world** carries no contract (FU-CM-122); the demonstration profiles stand in for it.
* **Home's browser specs** (`make ui-home-gate`) are not run as evidence: they read the canonical world as it was seeded on 5 October, and the test site's canonical world has drifted from it (the head of procurement's Home reads 2 actions, 1 waiting item and 2 oversight records where the specs expect 9, 2 and 6, because Tenders, Bid opening and Requisitions rows are missing; none of that is Contract Management's). Contract work on Home is proved by `test_cm_home_provider` and the demonstration walk. Rebuilding the world with `make seed-canonical SITE=kentender-test.local REBUILD=True` makes them an oracle again.
* **The rest of the platform's gates** (each other module's own services and browser gates) are not re-run: the regression gate above covers what Contract Management reaches into or changed in another app's world, and nothing else.
