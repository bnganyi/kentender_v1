# Contract Management runbooks

Companion to `CM-CHG-001_v0_8_IMPLEMENTATION_TRACKER.md` (plan Phase 12, tracker CM8-1205). Every command and function named here is checked against the code by `test_cm_runbook`, so a rename fails a test instead of leaving a stale instruction. The audience is whoever runs, tests or recovers Contract Management: a developer on the test site, the Technical Operator on a live site, and the head of procurement who is told something is pending.

Contract Management never writes another app's records. It asks the owner (Budget for funding, ERPNext for orders, receipts, invoices and payments, the shared signing facade for proof) through its published interface, **reads the owner first** by the operation's identity, links what already exists and creates only what is missing. That one rule is what makes every recovery below safe to repeat.

## 1. Environments and switches

| Switch | Where | What it does |
|---|---|---|
| `kt_cm_simulation_environment` (site config) or the platform's `kt_bds_simulation_environment` | test and demonstration sites; never a live site | Lets the simulation stand-ins answer: the signing provider, the synthetic rule profile, the synthetic award source provider, the simulated funding owner. On a live site neither is set and the synthetic profile is refused (`CM_RULE`). Nothing is ever drawn on a screen as a test label. |
| `kt_cm_clock` (a flag, set in code) | tests and profile builders | An injected instant that every recorded time and every deadline reads. The live pages of a test site read the site's test clock instead (`kentender_core.services.test_clock`). |
| `kt_cm_dispatch_fault = "fail"` (a flag) | tests | Makes the message channel fail, so a notice stays Unsent and is retried. |
| `kt_cm_funding_fault = "fail"` (a flag) | tests | Makes the simulated funding owner refuse, so the conversion, adjustment or closure stays pending. |
| `kt_cm_deduction_account` (site config) | any site | The native account a delay deduction is posted against. Without it a delay adjustment's application is held (the "adjustment mapping" hold) and Finance is told. |

Tests write real rows and have no rollback on this bench. **Run them on `kentender-test.local` only**, through `scripts/test-site.sh run …`, one module at a time, never while a Playwright run is active (`make cm-preflight` refuses). The dev site is never a test target.

## 2. Resetting fixtures

* The whole test site: `make test-site-rebuild` (copies the dev site over the test site).
* The browser world the Playwright specs walk: `make cm-ui-world` builds it and `make cm-ui-world-clean` removes it; always clean before running Python gates.
* A demonstration profile: `make seed-cm-profile SITE=kentender-test.local PROFILE=ACCEPTED` (profiles: RECEIVED, SIGNING, ACTIVE, ACCEPTED, PAID, CHANGE, WARRANTY, TERMINATION, CLOSED); the profile already in place is left exactly as it is, another replaces it, and `make seed-cm-clean` removes the contract, its native documents and the responsibilities granted for it and puts the clock back. `make seed-cm-profiles` builds and checks all nine once and cleans up. (17 October 2026) The nine profiles are documented in SEED-002 v0.10 §B6.1 and stay beside the canonical `contracts` stage of the seed (§A8.1), which carries the closed year's three awards through Contract Management; a profile suspends the canonical Finance workflow `KenTender Payment Approval` while it runs and `clean` puts it back.
* Passwords: a browser or demonstration world signs the seed world's own people in with a password it knows, keeps the password each had in `artifacts/cm-original-passwords.json`, and puts it back when the world is cleaned (`make cm-ui-world-clean`, `make seed-cm-clean`). A run killed before its clean leaves those people with the world's password, so every other module's browser specs fail with "Invalid Login" until the clean is run.
* A world also removes only the responsibilities it granted itself (its own namespace), never one a person already held: `test_cm_world_hygiene`.
* Python-level: `kentender_contracts.services.records.wipe` deletes every Contract Management row of one fixture namespace and the bell alerts for its contracts.

## 3. The gates, in the order they are run

| Target | What it proves | Roughly |
|---|---|---|
| `make cm-services-gate` | every service and board module on the test site | 25 to 35 minutes |
| `make cm-seams-gate` | the real owners: Award's source material, the core seams, Budget's funding provider | 3 minutes |
| `make cm-native-gate` | real ERPNext documents: the adapter, the payment guards, a two-process claim race | 2 minutes |
| `make cm-leakage-gate` | who may read what; the technical and audit readers can never act | 5 minutes |
| `make cm-dead-end-gate` | no reader is left on a screen with no way forward; every command is safe to send twice | 8 minutes |
| `make cm-ui-gate` | the structural fidelity of the boards, then every browser walk, then the world is cleaned | 12 to 35 minutes |
| `make cm-demo-gate` | the demonstration profiles walked as real people from the sidebar, My work and the bell | 3 minutes |
| `make cm-independence-gate` | the app on a site that holds only ERPNext, core, supplier accounts and itself | 6 minutes |
| `make ui-cm-fidelity-gate` | every board of the design compared with its artboard, or recorded as not compared with its reason | 1 minute |
| `make cm-persona-gate` | each named person on the accepted contract, in a real browser, with no native-form redirect | 3 minutes |
| `make cm-regression-gate` | what Contract Management reaches into in other apps: Award's seams, Budget's funding provider, the signing facade, the supplier-account provider and Home's structural comparison | 10 to 20 minutes |
| `make cm-platform-manifest` | the versions of Frappe, ERPNext, the KenTender apps, Python, Node and the database server and the repository commit, written to `artifacts/cm-platform-manifest.md` (the evidence report carries the same table); after any change to one of them the native and seams gates are run again | under 1 second |
| `make ui-cm-release-evidence-gate` | all of the above, once, in the order that keeps one gate's leftovers out of the next; writes `artifacts/cm-release-evidence.md` with each result and its proof level; it does not cover the owner-gated Phase 13; it holds the shared test-site lock (`/tmp/kt-test-site.lock`) and serves the site without the file watcher | about 70 minutes |

If a UI run fails oddly (a teardown that fails, later specs failing against state an earlier one left behind), check `make ui-queue-check` before reading any application code.

## 4. Uncertain operations: what the screen says and who acts

An operation that crosses to another owner is stored as a **Contract Operation Intent** with an identity (case, subject, version, kind, key) and a state: Recorded, Attempting, Failed or Uncertain are pending; Succeeded and Reconciled are settled. A definitive refusal by the owner is Failed; an unexpected error or a timeout is **Uncertain**, because the owner may or may not have acted. `kentender_contracts.services.intents.pending` lists a case's pending operations, and the Obligations tab shows them to the Technical Operator ("Restore contract operation").

* The case never changes lifecycle because an operation is pending, and nothing asks for a repeat signature: a signature proves the exact version, and the retry carries on from the original operation.
* What is held while an operation is pending is named on the screen with its reason and its holder; it is read fresh every time (`kentender_contracts.services.holds.open_holds`), so a cleared cause releases it without anyone editing a hold.
* An attempt that was left Attempting belongs to its worker for two minutes; after that a retry reads the owner first and carries on.
* **Recovery** is the Technical Operator's `RestoreContractOperation` task, which runs `kentender_contracts.services.formation.restore_operations`. It is the only technical action and it only reads and links.

## 5. Retrying each kind of operation

| Operation | Recovered by | How it is made safe |
|---|---|---|
| Native purchase order and funding conversion at signing, a variation's order update and funding adjustment, a termination's adjustment | `kentender_contracts.services.formation.carry_out_effects`, `kentender_contracts.services.change.carry_out_effects`, `kentender_contracts.services.termination.carry_out_effects` | the owner is read by identity first; a second attempt links the first's document |
| Funding closure of a closed contract or a completed settlement | `kentender_contracts.services.funding_closure.carry_out` | the owner answers by identity (`recall`); the contract stays Closed and shows **Funding finalisation pending** until the owner acknowledges |
| Native receipt of accepted goods | `kentender_contracts.services.delivery.restore_receipts` | a replacement's receipt waits for the native return that makes room for it |
| Native invoice (liability) for a claim | on the claim's own state change; a corrected claim after Finance posted the original is held until the credit stands (`kentender_contracts.services.payment.reconcile_liability` names it) | one liability, never two |
| A payment | **not retried by the system.** Finance prepares, a Finance approver approves, and the settlement is confirmed by a Finance approver, never the maker; a pending native payment holds further payment and a business user cannot repeat one by refreshing | the payment guards of the native adapter |
| A report to its recipient | `kentender_contracts.services.reporting.retry_dispatches` | the same dispatch identity: the recipient is sent it once |
| A message to the supplier | `kentender_contracts.services.issues.retry_dispatches` | the same message, delivered only with evidence |

## 6. Things not to do

* Do not edit a Contract Management record, or an ERPNext document the contract made, by hand to "fix" a state. The history is append-only; a correction is a later fact (a correction request, a reopening, a credit note).
* Do not delete a native document the contract is linked to: the link stops the document's name from being reused until the contract's own record says what happened.
* Do not reuse an idempotency key for anything but the exact same command: another payload, person or command with the same key is refused as a conflict, on purpose.
* Do not turn on the simulation switches on a live site to "get past" a refused action. A refusal with `CM_RULE` means the production rule profile has not been verified (LQ-01), which is a decision for the legal and procurement owners, not a setting.

## 7. Installing on the dev site (done 17 October 2026; receipt in `evidence/dev_install_2026-10-17/receipt.md`)

The Project Owner authorised it on 17 October 2026 and it was run that day: backup, `install-app kentender_contracts`, the app build, cache clear, canonical-seed validation and a read-only smoke (9 s to install, no rows created, no restart needed). The text below is what installing it does, kept as it was written before the go-ahead; the rollback it mentions is still written and not tried.

* It adds the module and its record types, custom fields on native documents (`native/fields.py`), the payment guards on Payment Entry and Journal Entry for suppliers that have contract invoices, and takes over the Contract Management rail slot.
* **It also switches the simulation stand-ins on there**, because the dev site carries the platform's `kt_bds_simulation_environment`: the signing provider, the synthetic rule profile, the synthetic Award source provider and the simulated funding owner would answer on dev, and a production site must never carry that flag.
* The demonstration profiles (`make seed-cm-profile`) refuse the dev site without `CM_ALLOW_DEV_SITE`, and one of them activates a Payment Entry workflow, which Frappe makes the only active one for that document (FU-CM-124): it must restore the one it replaced before it is run on a site that has its own. Since 17 October 2026 the test helpers do: `native_world.ensure_workflow` suspends the site's own workflow and `drop_workflow` puts it back, and the canonical validation fails a site that has none active.
* The command when approved is in the implementation tracker, CM8-411. A rollback has not been written or tried; prove it on the test site first. The receipt to keep: migrate, build and smoke output, and the native configuration before and after.

