# CM-CHG-001 v0.8: Contract Management, implementation plan

| Control | Value |
|---|---|
| Version | 0.8-plan.1 |
| Date | 14 October 2026 |
| Status | Draft for owner review. Nothing built. |
| Authority | `KenTender_CM-CHG-001_Contract_Management_v0_8.md`, *Approved — Project Owner, 14 October 2026* (requirements and artboard specification, including §19 and CM-AC-65–71). v0.7 is history. |
| Design | `design/CM Artboards.dc.html` + `cm-data-1…4.js` — **157 boards in 43 designs** (91 state variants, 23 dialog boards; extracted by script in Phase 0 and matching the design page's own header). The earlier count of 122 is superseded. |
| Companions | `CM-CHG-001_v0_8_IMPLEMENTATION_TRACKER.md`, `CM-CHG-001_v0_8_FOLLOW_UPS.md`; later `reconciliation/`, `evidence/v0_8/`, `RUNBOOKS.md`. |

This plan is a new implementation file. It changes no requirements document and records no approval. Anything marked **(proposed)** is new content for the owner to review: names, folders, hooks and targets that no approved document states.

## Context

**Why this module now.** Award is built and hands an eligible package to a synthetic "Contracting" receiver that creates a **Prepare contract** task and nothing more (Award plan D10, FU-AWD-12). Contract Management is the next link in the chain: Award → **Contract** → Inspection → Stores/Assets → Reporting.

**The MVP contract (CM v0.8 §§1–2).** One case carries prepare-and-sign → receive-and-inspect → accept → certify invoices and track payment → warranty, security and close-out. KenTender prepares the agreement, checks delivery evidence against its terms, generates findings and payment checks and tracks the contract to close-out. People establish physical facts, resolve exceptions and take personal responsibility. **ERPNext holds the operational stock, asset and accounting records.** KenTender never keeps a second stock, asset or payable ledger.

**What makes this module different from every earlier one.**

| Difference | Consequence for the plan |
|---|---|
| Largest scope yet: 83 named commands and reads (§7, counted by script), 71 acceptance scenarios, 157 boards in 43 designs, six delivery packages A–F | Package order and an early full-chain thread are fixed by the document (§14.4). |
| First module to write ERPNext Buying, Stock, Assets and Accounts records | The feasibility spike comes before any workflow screen. |
| Must install and run **without** the tendering apps (§3.1, CM-AC-25, CM-AC-32) | Dedicated app; a scratch site proves the boundary; an import-boundary test guards it. |
| Needs two-party and many-party signing over one frozen package | The signing facade must live in core, not in Proceedings. |
| Legal rules are specified (§19.3) but six named questions are external (LQ-01–06) | A code-owned rule register; holds scoped to the affected action only. |
| Several cross-owner effects can fail after real proof exists (§5.17) | One durable operation-intent model, designed in Package A, not retrofitted. |

**What slowed earlier modules, and the rule adopted here.**

| What slowed it | Evidence | Rule here |
|---|---|---|
| Verification left to the end | EVL: nine browser defects found late; Award rows closed only at release | The risky integrations are proved first (Phase 2); each phase closes with its own evidence. |
| Per-test world building | EVL suite 1,094 s → 444 s once worlds were shared (memory "shared test worlds") | CM tests build one synthetic world per module; per test only namespaced CM rows are wiped. |
| Upstream reruns with no changed dependency | EVL tracker lines 73–74 | An upstream rerun names the changed file that justifies it and runs one test module. |
| Gates and tooling left "owed" | EVL4-1104 | `cmKit`, `departures/contracts.js`, the vitest project and Make targets exist in Phases 0–1. |
| Demo profiles and the menu walk left to the end | EVL4-1304/1305 | The thread in Phase 4 is walked from the menu by its real personas. |
| A synthetic pass mistaken for proof | Award's "synthetic" rows | **Owner direction, 14 Oct 2026:** synthetic upstreams support development; package acceptance must include the actual relevant integrations (see "Proof levels"). |

## Current state (verified 14 October 2026 by reading the source)

Paths are relative to `apps/kentender_v1/` unless shown.

**Contract Management.** No code exists.
- `kentender_procurement/kentender_procurement/contract_management/` and `inspection_acceptance/` are empty skeletons (`__init__.py`, `api/`, `services/`, `tests/`, `utils/`, `doctype/.gitkeep`). Neither is in `modules.txt`. They sit inside the app that holds tenders and bids, so they cannot satisfy the independence requirement.
- `kentender_stores`, `kentender_assets`, `kentender_governance` and `kentender_integrations` are empty app shells. CM does not need them: native stock and assets are ERPNext's.
- The design folder `docs/mvp-1-r1/21_contract_management/design/` and both CM documents are untracked in git (`git status`, 14 Oct 2026).

**ERPNext on this bench.** ERPNext 16.10.1, Frappe 16.12.0. The test site `kentender-test.local` has one Company, **KenTender** (KES), and 5 Warehouses. Counts of Purchase Order, Receipt, Invoice, Payment Entry, Quality Inspection and Asset rows were not established. **No KenTender code reads or writes any ERPNext transaction today** (grep of all `kentender_*` apps for those doctypes returned nothing). Facts read in ERPNext source that the spike will exercise, not conclusions: Item has `auto_create_assets` and `inspection_required_before_purchase`; Purchase Receipt rows carry `rejected_qty` and `rejected_warehouse`; `buying_controller.py` creates assets from a receipt when an item auto-creates assets; `stock_controller.validate_inspection` reads the item's inspection flag.

**Award side.** `kt_award_contracting_receivers` (hook read by `award/services/contracting.py`) returns the first receiver that answers; the only provider is the simulation stand-in `award/test_services/contracting_receiver.py` (`receive_package`, `receive_decision_event`, `receive_update`). Award keeps a frozen `Award Contracting Package`. The Award document in the folder is **v0.6** (proposed, 10 Oct 2026: withdraws the test-environment notice); CM v0.8 cites AWD **v0.5**. Phase 0 reconciles which package contract is current.

**Signing.** `proceedings/services/signing.py` owns `attest(member, target_id, target_digest, minutes_version, action, correlation_id)` with outcomes Verified / Rejected / Unavailable / Indeterminate. Its provider hook is `kt_trust_signing_services` (declared in `kentender_procurement/hooks.py`) and the only provider is a test double inside Proceedings. `kentender_core` has no signing facade. **CM cannot import Proceedings**, so a core facade is required (D8).

**Suppliers.** `kentender_core/services/supplier_account_contract.py` already publishes a provider seam (`kt_supplier_account_provider`: `active_assignments`, `organisation_signatories`, `organisation_people`, `verified_contacts`, `business_profile` …). `kentender_suppliers` registers the real provider. CM uses this seam and never imports Bid Submission's `bid_authorization.py` or `supplier_gateway.py`.

**Budget.** `kentender_budget/services/budget_commitment_contracts.py` has `revalidate_reservations`, `release_reservation`, `convert_reservation` and `adjust_commitment`. **`close_commitment` does not exist** (CM §5.14.1 proposes it as a Budget-owned service). `budget_service_principal.py` exists.

**Shared facilities to reuse (no parallel versions).** `kentender_core/services/`: `my_work.py` (`kt_my_work_providers`), `next_step.py`, `support_issues.py`, `notification_service.py`, `business_role_registry.py` and `authorization*.py` (AUTH registry and resolver), `record_picker.py`, `paging.py`, `test_clock.py`, `portal_runtime.py` (`kt_portal_surfaces`), `technical_read.py`; the Desk runtime `kentender_core.desk_page.register`; industry `mountPageRail`, `mountGuidance`, `mountPager`, `mountRecordPicker`; `file_integrity`; Award's `records.py` / `errors.py` pattern (copied, not imported).

**Latest document versions in the repo versus CM's citations.** CM cites AUTH v1.11, CFG v0.18, KT-STD v1.25, BUD v1.12. The folder holds AUTH v1.15 and KT-STD v1.27 (BUD v1.12 is current). Phase 0 reads the latest of each before any code binds to them.

**Personas** (CM §13, from KT-STD §8): Charles Mutiso (HOP, invoice certifier, completion certificate), Amina Hassan (AO, entity signatory), Brian Wafula (procurement member), Julia Njeri (contract owner, inspection chair), Peter Mugo (technical member, technical certifier), Grace Wanjiku (receiver), Josphat Mwangi (Finance maker), Beatrice Kamau (Finance approver), Mary Wanjiku (supplier signatory), David Ouma (supplier representative), Daniel Otieno (technical read, recovery), Naomi Chebet (auditor). Grace Wambui is a distinct change reviewer. Which of these exist in the seeds today is a Phase 0 check; none is created without the owner.

**Done means:**
- Every §7 command and read is a server service with idempotency, expected revision, trusted time and audit.
- Every §5.10 next-step row has its holder, My Work item, clearing event and a named test.
- Every §10 board is a state of a shared surface; all 157 are compared by the fidelity gate or recorded as not compared with a reason.
- The ordinary ten-laptop journey and the existing-contract journey run in a browser from the menu, by their real personas, with no standard-Frappe-form redirect (§17.12 usability acceptance).
- Each package passes against its real integrations, not only synthetic ones. Formation is accepted only with proof that every CM §19.4 source is available through the versioned handoff.
- CM-AC-01…71 are marked honestly with a proof level. Production-only parts stay `Blocked — owner`.
- None of the prohibited shortcuts of CM §16 exists anywhere in the module.

## Owner decisions (14 October 2026)

| # | Decision |
|---|---|
| OD-A | **App home: a dedicated Contract Management app.** "Do **not** relax the independence requirement. CM must operate without the tendering modules, using the existing-contract intake route. Reuse core authority, signing, evidence and task services, plus ERPNext. Award integrates through an optional adapter; CM must not depend on tendering controllers or tables. This is a focused CM boundary, not permission to split every existing app." |
| OD-B | **Feasibility spike first, before the workflow screens.** "Treat 2–3 days as an initial timebox", evidence: agreement → native order → partial accepted receipt with serials; correct stock/asset and invoice postings; payment maker/approver separation and blocked direct-entry bypasses; both parties signing the same immutable agreement package; retry/recovery without duplicate signatures, transactions or funding effects. "A failed check should identify whether configuration, integration code or a reviewed requirements change is needed. ERPNext behaviour must not silently redefine the business requirements." |
| OD-C | **Finance: proceed with explicit test assumptions while obtaining targeted confirmation.** A1 ownership/recognition follows acceptance for the specified test contract (conditional on its terms and Finance policy; an earlier transfer needs a defined accounting treatment; recognition is not deferred to fit the workflow). A2 the payment approver may record settlement under CM-OD-08 with independent bank evidence, excluding the payment maker and procurement certifier; confirm whether institutional policy needs a separate reconciler. A3 serialised fixed assets for the demonstration, subject to Finance confirming capitalisation policy; real classification follows approved Finance configuration, not a procurement user's per-delivery choice. |
| OD-D | **Three tightenings.** (1) Synthetic upstreams support development; package acceptance includes the actual relevant integrations. (2) Design reversal, termination and recovery boundaries early, even if their complete screens come later. (3) Use CM's prescribed screen mapping; a count of screen families is not authority to introduce destinations. |
| OD-E | **Source handoff is required Package B work.** Owner, 14 Oct 2026: "The concern … is valid, but 'a follow-up' is too weak. This is a required integration dependency already identified in approved v0.8 §19.8. … Award supplies the authoritative source material; CM generates the agreement." Handling: "1. Check the current Award handoff against CM §19.4 … 2. Supply missing material through an explicit, versioned interface from its owning module. Immutable document references are acceptable if their exact contents remain retrievable and verifiable. 3. CM assembles the complete signing package, including its generated agreement, preserving source versions and hashes. 4. Close any interface gap within the formation package's implementation. It cannot remain an unspecified future task while formation is declared complete." |

Standing owner rules carried in and not re-asked: shared test worlds; targeted regression runs; walk from the menu; no test banners or labels on user-facing surfaces (DEC-044); store instants in site time with UTC only in serialized messages (AGENTS.md §4.4); always remove test data; fix the shared runtime, not each screen; when a defect is found, fix every instance and add a guard; plain-English replies.

## Key technical decisions (implementation authority unless the owner says otherwise)

| # | Decision |
|---|---|
| D1 | **App. (proposed name `kentender_contracts`; Module Def "Contract Management".)** `required_apps = ["erpnext", "kentender_core"]` (the same shape as `kentender_suppliers`). It sits after Award in the business chain but depends on nothing downstream or upstream of core except through published seams. Created with `bench new-app` under OD-A; AGENTS.md §2 (app list, dependency note) and CLAUDE.md's map gain one line each. The two empty skeletons in `kentender_procurement` are deleted (as Award deleted `evaluation_award/`). New-module procedure: migrate → clear cache → check the Module Def's `app_name` → migrate again. |
| D2 | **Boundary rules.** CM imports only `frappe`, `erpnext` and `kentender_core`. Optional adapters sit at the edge and are guarded by `frappe.get_installed_apps()`: **Award** → a receiver CM registers on Award's published hook `kt_award_contracting_receivers` that consumes the package *payload* only, never Award code or tables; **Budget** → `adapters/budget.py` calls Budget's published functions lazily, behind an installed-app guard, with a synthetic provider for development; **Suppliers** → core's `kt_supplier_account_provider` seam; **BDS/PRC** → optional navigation and projections only. Disabling any adapter leaves existing contracts readable and operable (CM-AC-32). Guarded by `test_cm_import_boundary` (static scan) and the `cm-independence-gate` (D12). |
| D3 | **Records (proposed names; reuse native fields where ERPNext already owns the fact; no field without a named rule or output).** `Contract Case` (one per source contract identity; lifecycle Preparing / Awaiting signatures / Active / Closed / Did not proceed / Terminated; hold fields are conditions, never stages); `Contract Agreement Version` + `Contract Package Entry` (manifest rows); `Contract Signature Request` + slots; `Contract Obligation`; `Contract Arrival` + units, `Contract Custody Movement`; `Contract Inspection` + observations; `Contract Acceptance Version`; `Contract Technical Certificate` and other generated outputs as `Contract Document Output`; `Contract Issue`; `Contract Change` (also termination); `Contract Invoice Submission` + lines; `Contract Certification`; `Contract Transaction Link` (unique native operation → document/row/version); `Contract Compliance Obligation`; `Contract Period Report Version`; `Contract Security Record`; `Contract Appointment` + members + declarations; `Contract Funding Link`; `Contract Correspondence`; `Contract Operation Intent`; `Contract Command Journal`; `Contract Settings`; `Contract Test Environment Controls`. All carry the flags guard (writes only through `records`), deny-by-default permissions and `fixture_namespace`. The rule profile is **code**, not a doctype (§4.1). |
| D4 | **Command envelope.** `services/records.py` and `errors.py` follow `award/services/records.py`: `command(name, *, case, idempotency_key, actor, payload, body)` journals the command, a replay returns the original result and a conflicting reuse is refused; `check_version` raises `CM_CHANGED` and returns the current record; `atomic`, `lock(case)`, `bump`, `digest`, `next_id`. The error set is the 17 codes of CM §8, verbatim, with separate detail, `Guards` that collect every reason together, `as_data` for refusals-as-data and `InputError` for field errors. The API never forwards `**kwargs` into a keyword-only service. |
| D5 | **One operation-intent model (designed in Package A — OD-D(2)).** Every cross-owner or uncertain effect is a `Contract Operation Intent`: purchase-order creation, funding convert / adjust / close, accepted-receipt posting, native invoice and payment save / approve, signing attempt, report dispatch, supplier notice dispatch. Identity = (subject, version, operation kind, key). States: Recorded → Attempting → Succeeded / Failed / Uncertain → Reconciled. Recovery order is fixed: read the owner's authoritative state first, link what exists, and only then retry; the same identity always returns the same native document. Each intent names its recovery owner and its truthful display state (§5.17). `Contract Transaction Link` is unique on the owner operation, so a retry cannot post twice. The matrix of §5.17 and §5.18 becomes `reconciliation/recovery_matrix.md` and a table-driven test (Phase 3). |
| D6 | **Hold engine.** `services/holds.py` evaluates every open hold independently. The permitted action set is the intersection of all applicable guards; each hold names its scope (line, quantity, amount, command), owner, reason and clearing evidence. Holds are derived from state (restriction, rule unverified, funding pending, order pending, native result pending, correction request, appointment missing, legal question LQ-n …), never stored as a stage. Factual and protective recording stays possible within the actor's authority (§5.17). |
| D7 | **Native adapter (the controlled façade of §9.1).** `native/` wraps ERPNext Purchase Order, Purchase Receipt, Purchase Invoice, Payment Entry, Quality Inspection and Asset through supported native methods only: save, submit, native workflow transition, cancel, return and credit note. Each operation re-checks authority, version, entitlement and holds inside its transaction, maps native validation errors to field errors for the KenTender screen, and records a `Contract Transaction Link`. No ledger write, no Stock Entry for an asset receipt, no iframe or redirect to a Desk form. **Bypass guards** (`doc_events` in CM's `hooks.py`, plus any supported native extension point the spike finds) enforce the payment hold, maker/approver separation and entitlement on every native path: direct Payment Entry, Journal Entry settlement, Payment Reconciliation / allocation, API, import and background jobs (CM-AC-17, 31). |
| D8 | **Signing.** A core facade `kentender_core/services/signing.py` takes over the `attest` function, outcomes and hook lookup from `proceedings/services/signing.py`; Proceedings keeps a thin delegating wrapper, so its callers and tests do not change (targeted Proceedings signing rerun, once). CM registers its own simulation provider on `kt_trust_signing_services` (loads only under the simulation flag) so a CM-only site can sign in tests. CM models a signature request per agreement version, amendment, report or certificate with ordered or unordered signer slots; **each signer attests the same full-package digest** (`target_digest` = digest of the frozen manifest and bytes, §19.4). An attempt is stored before the call; Indeterminate / Unavailable keeps the same attempt (correlation id) and shows **Signing is unavailable. Your work has been saved.** A changed version ends outstanding requests. Whether `attest` as it stands carries the witness evidence and capacity facts is spike item S6. Production signing, the witnessing method (LQ-05) and legal equivalence stay `Blocked — owner`. |
| D9 | **Agreement package and outputs (CM §19.4–19.5).** `documents/` builds the frozen manifest of the eight categories (`agreement`, `tender_form`, `price_schedule`, `requirements_schedule`, `technical_specifications`, `gcc`, `scc`, `award_notification`) plus addenda and any incorporated document, each entry with document ID/version, file digest, release/instance, locator, inclusion basis and access projection. The agreement text is the **issued** form's Form No. 4 body with its declared placeholders filled; the renderer uses versioned anchors and **fails visibly** when its source differs; no fallback to a current template. For a KenTender award the source material reaches CM through the versioned source handoff of D20 (CM never reads tender tables); CM generates the agreement and freezes the complete incorporated package. For an existing contract CM keeps the executed package and a reviewed mapping. Output generation reuses the existing wkhtmltopdf path and `file_integrity`; whether it is byte-deterministic enough to digest is spike item S8. Certificates and decisions of §19.5 are KenTender-authored documents on the shared preview/sign surface, not new destinations. |
| D10 | **Rule register.** `rules/` holds CM-R-01…18 as code: id, class (LAW / TERM / CONTROL), source edition and locator, applicability, inputs, calculation, affected commands. Original events are stored and results recomputed on an authoritative correction. A profile is Draft / Verified / Suspended; Draft or Suspended blocks only the consequential actions it governs (§4.1). LQ-01…06 each map to one named hold key with its approved interim treatment (§19.7). A labelled synthetic profile ("Illustrative test terms": the D34 mechanism, no-security setting, D36 percentage) loads only under the simulation flag and is stored as a classification, never drawn as a banner on a user-facing surface (DEC-044 — see C8). No 14-day, 60-day or Regulations-only deadline is hard-coded (CM-AC-30). |
| D11 | **Authority and reads.** New responsibilities are registered in `kentender_core/services/business_role_registry.py` (existing Site-wide and Organisation Unit scope types only; no Contract scope type): Contract preparation, Contract coordination, Receiving (Organisation Unit); Contract inspection, Technical certification, Entity contract signing, Finance preparation, Finance approval (Site-wide). The registry change is a core edit recorded in the AUTH owner follow-up. Appointments, signatory mandates and committee membership are CM-owned **subject bindings** checked in addition to AUTH. `services/segregation.py` evaluates the six separations of §6.1 from the **actual** signer and maker history at commit time. Read DTOs are per audience (§6.2 table), filtered before count and pagination, with the AO/HOP no-task read, Head-of-User-Department source participation and supplier projections. |
| D12 | **Independence proof.** A throwaway site `kentender-cm-only.local` (proposed) with only `erpnext`, `kentender_core`, `kentender_suppliers` and `kentender_contracts` installed. `make cm-independence-gate` creates or reuses it, migrates, and runs the existing-contract journey (register → partial receipt → invoice follow-up → close-out) through service calls with no tendering DocType present (CM-AC-25, 26, 32). Phase 0 checks that core and suppliers install on their own. Run at Phase 1 and at every package gate. |
| D13 | **Budget.** `adapters/budget.py` calls `revalidate_reservations`, `convert_reservation`, `adjust_commitment` and `release_reservation` as the contract service principal, with CM's idempotency keys. **`close_commitment` is built in `kentender_budget`** to CM §5.14.1 (including "Committed includes Active and Closed retained amounts" in positions) with the seven owner tests of §5.14.1; it is scheduled in Phase 3 because it is small and shapes the closure and termination boundaries (OD-D(2)). It records a BUD tracker addendum and a follow-up. A linked contract shows **Funding finalisation pending** until the owner acknowledgement exists. An external contract shows **Not linked to KenTender Budget**. |
| D14 | **Next steps and work items.** `services/next_steps.py` implements the §5.10 table, the §6.3 ordering (protective/legal/security deadline at risk → other verified overdue → earliest verified upcoming → undated by assignment instant and stable id) and the single-leading-task-plus-**Other work** rule with deduplication of command subject / version / holder. `services/tasks.py` registers on `kt_my_work_providers`. Technical recovery work uses core `Support Issue` rows (Daniel is a technical user whom My Work skips; Esther sees Support Issue rows — Award C9). Rows are derived from state and keyed by (case, subject, version, holder). Viewing never completes a task. |
| D15 | **UI and routes (CM §9, authoritative).** One Desk Page `contracts` (one `kentender_core.desk_page.register(...)`): `/app/contracts` (list; **My work** and **All contracts** are views), `/app/contracts/register`, `/app/contracts/{id}` with five tabs **Agreement / Deliveries / Invoices / Obligations / History** each with its own deep link, and `/app/contracts/{id}/invoices/{invoice_id}` and `/payments/{payment_id}` for the embedded Finance editors. Appointment, security, issue, change and report tasks open as focused records **inside** the same contract and return to the selected tab and filters. Supplier: `/supplier/contracts` and `/supplier/contracts/{id}` through `kt_portal_surfaces`, own small bundle, usable at 390 px. A standard Workspace and sidebar entry give the single menu item **Contract Management → Contracts**. **No other destination exists.** D-numbers are states of shared surfaces (§9.0 map below); a task ID or board number is never a menu item. One data-driven board renderer is ported class-for-class from the `<x-dc>` markup, as Award's `AwdBoard.vue` was; screen builders turn server reads into the block model. Industry only (never Civic Ledger, Stitch Desk or `cl_surface_registry.js`); lazy-loaded bundles (AGENTS.md §6.9); tables use `mountPager`; choosing a person uses `mountRecordPicker`; no browser alert for a correctable error (§6.10). Finance editors are KenTender components over the native adapter. |
| D16 | **Fidelity tooling.** `tests/ui/fidelity/board.js` gains a `cmKit` that evaluates the `cm-data-*.js` board definitions (`S`, `V` and `dlg` helpers) and renders each through the existing `renderTemplate`; `departures/contracts.js` (DEPARTURES, COVERED, NOT_COMPARED with reasons); vitest project `contracts`, added to `make ui-structure-gate` in Phase 0. The design folder is untracked, so the repo-wide provenance gate needs it committed (FU-CM-34). Board literals (dates, CM-MOH-2027-… references, serials) are fixture data; the runtime shows actual generated references and events. |
| D17 | **Seeds.** A canonical stage `contracts` after `award` in `kentender_core/seeds/canonical.py` (`STAGES`, `seed`, `validate`), implemented in `kentender_contracts/seeds/`, driven only through production commands. It starts from Award's actual generated package for TND-MOH-2027-002 (KES 46,400,000, delivered 2 Jul 2027 09:00 EAT under the test clock), deriving line values and terms from the package. The **ten-laptop demonstration** and the other scenario rows of §10.1B (thirteen named isolated contracts — `CM-MOH-2027-EXT-001`, `-EXTENSION-001`, `-SEC-RETURN-001`, `-SEC-VERIFY-001`, `-WAR-OPEN-001`, `-WAR-001`, `-TERM-001`, `-SVC-001`, `-QTY-001`, `-DELAY-001`, `-SEC-001`, `-CLOSE-001`, `-CLAIM-001` — plus the D28, D29 and D26 subjects; the base is `CM-MOH-2027-001`) use a separate synthetic source package (`CM-DEMO-AWD-01`, `CM-DEMO-TERMS-01`) and **never overwrite the canonical chain** (CM-AC-21). Demo profiles: `make seed-cm-profile PROFILE=…`. Reruns return the same identities. Production numbering is not constrained to board strings. |
| D18 | **Test base and test data.** Tests run on `kentender-test.local`, never on dev. `tests/support.py` provides `ContractCase`: a synthetic Award package and a synthetic native configuration built once per module; per test only `CM_TEST`-namespaced CM rows are wiped. **Native documents are never mocked in a test that claims native behaviour.** Test-created ERPNext documents are cancelled and deleted by a registered cleanup, and the test site is reset with `make test-site-rebuild` between phase gates, not per test (Python tests have no rollback on this bench). One test module at a time; never Python while a Playwright process is active (`cm-preflight`). Test years for native and Budget fixtures follow the module's existing "years ≥ 2100" practice where Budget is involved. |
| D19 | **Instants.** Stored in site time; UTC only in serialized messages and event payloads, through core instants helpers (AGENTS.md §4.4). A single `clock.now()` honours the trusted test clock for every actor, including supplier-side timeliness. Recording time is never back-dated to physical arrival (§12). |
| D20 | **Source handoff (CM §19.4, §19.8; owner direction 14 Oct 2026).** The owning modules supply the authoritative **source material**; **CM generates the agreement and assembles and freezes the complete package**. Award is not expected to hold an assembled eight-category package. Required handling: verify the current Award/source handoff against CM §19.4 (`reconciliation/package_gap.md`, S1–S12); identify and implement any missing owner-interface changes, updating the affected current documentation; CM freezes the complete incorporated package; **formation acceptance requires proof that every required source is available, and unresolved gaps block that acceptance**. **Interface (names confirmed by the owner, 14 Oct 2026):** a versioned `ContractSourceHandoff` carried with the Award package as references — per source: category, owning module, reference id and version, SHA-256, media type and size, locator (clause or section) and basis for inclusion. Contents must stay retrievable and verifiable, so owners register a provider on a core hook `kt_contract_source_provider` whose seam module `kentender_core/services/contract_source_contract.py` follows `supplier_account_contract.py` (functions `describe`, `fetch` returning bytes and digest, `verify`). CM resolves and verifies each reference at preparation, copies bytes and digests into its own manifest, and never imports an owner's code or reads its tables. Owners and sources: Tenders and the template release (issued instance, release, addenda, requirements and technical schedules, GCC/SCC with clause ids, Form No. 4 source), Bid Submission / Evaluation (accepted tender and clarifications), Award (award notification, signing-window result, decision), Budget via Award (funding lineage), site configuration (entity particulars once), supplier accounts (existing seam). Owner-side changes are additive seams with tracker addenda, as Award did for Evaluation, and their **document updates are proposed successors under the document-change protocol** (version numbers from the register, approval left to the owner), **written in Phase 5 with the code, not deferred to Phase 13**. A synthetic provider on the same interface serves Phases 3–4 at L1; Phase 5 proves the real providers on the canonical package (`test_cm_source_availability`). Users never re-upload what KenTender already holds (CM §9.1, §9.2). |

## Finance and native-posting test assumptions (OD-C) — what the build will and will not do

| # | Assumption in the build | Not done / still open |
|---|---|---|
| A1 | Receipt posting follows acceptance. Arrival creates segregated, **non-valued custody** and inspection work only; no Purchase Receipt is created for arrival (CM-OD-06, CM-AC-49). | A contract that transfers ownership earlier gets no silent delay of recognition; it is a named issue until Finance defines the treatment. |
| A2 | The current Finance approver may record settlement of the entry they approved, with independent bank or reconciliation evidence; the payment maker and procurement certifier are excluded (CM-OD-08). | **Open (FU-CM-24):** confirm with Finance whether institutional policy requires a separate reconciler; if so, a distinct capacity replaces this and the fixture changes by reviewed amendment. |
| A3 | Demonstration laptops are **serialised fixed assets** through the native receipt-to-asset path, configured at item and asset-category level by Finance configuration, not chosen by a user per delivery. Stock-classified items follow the stock path. | **Open (FU-CM-25):** Finance confirms the entity's capitalisation policy. Classification is never a per-delivery control. |
| A4 | Recognition of a liability before certification (early liability) is supported only with a server-enforced payment hold on every native path. | Policy confirmation and proof are CM-PROOF-02. |

## Proof levels

Every tracker row and every acceptance scenario states how it was proved.

| Level | Meaning | Closes |
|---|---|---|
| **L1 — Synthetic** | Services against synthetic sources, synthetic Award package, simulation signing double. Fast; builds in seconds. | Development progress only. A row proved only here is `Partial — synthetic`. |
| **L2 — Real integration** | The real Award package delivered by real Award code through the real hook (canonical TND-MOH-2027-002); the real Budget services on the canonical world; **real ERPNext documents** through the native adapter; the real core signing facade (with the simulation provider, the only provider that exists); the real supplier-account provider. | **Package acceptance** and an AC row's `Done`. |
| **L3 — Production-gated** | A verified legal profile (LQ-01…06), the production Trust provider and witnessing method, real notice and report channels, Finance policy confirmation and a release decision. | Never claimed here. `Blocked — owner`. |

## Screen mapping (CM §9.0 — the only destinations)

| Location | Boards that are states of it |
|---|---|
| Contracts list (`/app/contracts`) | D01, D01-S and variants, empty / filter / reader states |
| Agreement tab | D02, D03, D26; appointment and declaration tasks D23, D24 (focused records in the case) |
| Deliveries tab | D04–D07, D19, D31 and variants |
| Invoices tab | D08, D09, D17, D18, D28, D29, D33, D08-L, D09-F |
| Obligations tab | D13, D14, D16, D25, D27, D34–D37 (issue / change / security / warranty) and D10/D40 (remaining and simultaneous work), D11, D20, D22, D32, D38, D39 (completion, closure, termination) |
| Register form (`/app/contracts/register`) | D12, D21 |
| Report task (focused record) | D15 |
| History tab / evidence preview | shared View actions, no separate editing |
| Shared pages | D-ERR, D-DENIED; D30 is retired |

## Phases

**Loop for every phase:** red, then green, then refactor; run the module's tests once; run the phase gate; update the tracker row with its evidence in the same step. Phases 0–2 are horizontal; Phase 3 is foundations; from Phase 4 each phase is a vertical slice: service → API → screen → one Playwright spec on one fixture entity → a live click-through from the menu. Never run Python while a Playwright process is active. Each package gate has a synthetic part (L1) and a real part (L2); the gate is not passed on L1.

### Phase 0: Reconcile (documents and tooling)
- `reconciliation/artboard_inventory.md`: all board identifiers extracted **by script** from `cm-data-*.js`: id, name, design, actor, instant, variant kind (main / state / dialog), surface (the §9.0 location), spec §, slice, compare or not-compare. Confirms the 157 count.
- `reconciliation/error_contract.md`: CM §8, 17 codes, copied verbatim by script.
- `reconciliation/next_step_register.md`: every §5.10 row: situation, text, holder, My Work title, clearing event, named test.
- `reconciliation/command_map.md`: every §7 command, every §11 / §11.1 control and every board action → exactly one command or read (CM-AC-44).
- `reconciliation/fixture_chronology.md`: the ordinary ten-laptop path with instants, and every §10.1B identity with its synthetic entry point and isolation.
- `reconciliation/seam_register.md`: CM-IF-01…08 → the concrete function, hook or adapter, or the gap and its follow-up.
- `reconciliation/rule_register.md`: CM-R-01…18 and LQ-01…06 → rule module, input event, hold key, named test.
- `reconciliation/package_gap.md`: what Award's frozen package (v0.5 and v0.6 contract; the real `Award Contracting Package`) carries versus CM §19.4's eight categories and bindings, and §5.14's funding lineage; every gap → a required interface change in its owning module, scheduled in Phase 5 (D20). Award supplies source material; CM generates the agreement and assembles the package.
- Latest-version check: read the latest AUTH, CFG, KT-STD, AWD, BUD, STD-TPL, TPR, TRUST, SEED-OPS in the folder and register, and record each difference from CM's citations (see C1).
- Personas and registry: which §13 people and which AUTH registry entries exist today; the gap list.
- `cmKit` extractor, `departures/contracts.js`, vitest project `contracts`, added to `ui-structure-gate`.
- **Gate CM-G00:** inventory = 157 rows, each in exactly one slice and one §9.0 surface; every command and control mapped; `make artboard-provenance-gate` result recorded (needs the design folder committed, FU-CM-34); `npx vitest run --project contracts` runs (an empty compare list is allowed).

### Phase 1: App scaffold and the independence site
- `bench new-app` → `kentender_contracts/`; `hooks.py` with `required_apps = ["erpnext", "kentender_core"]`; module registered; install order in the Makefile; AGENTS.md and CLAUDE.md map lines; delete the two empty skeletons in `kentender_procurement`; new-module procedure (migrate, clear cache, check `app_name`, migrate).
- Minimal records for the spike (`Contract Case`, `Contract Operation Intent`, `Contract Command Journal`, `Contract Test Environment Controls`) with the flags guard.
- Install on `kentender-test.local` only. Installing on the dev site is announced to the owner and happens in Phase 4 (hidden side-effect rule).
- Makefile: `cm-preflight`, `cm-services-gate`, `cm-seams-gate`, `cm-native-gate`, `cm-independence-gate`, `cm-leakage-gate`, `cm-dead-end-gate`, `ui-cm-<slice>-gate`, `ui-cm-fidelity-gate`, `ui-cm-gate`, `ui-cm-release-evidence-gate`, `seed-cm-profile(s)`; all in `.PHONY`.
- `test_cm_import_boundary` (CM imports only frappe, erpnext, kentender_core).
- `kentender-cm-only.local`: erpnext + core + suppliers + contracts installs and migrates.
- **Gate CM-G01:** app installs on the test site and on the independence site; migrate twice clean; import-boundary test green.

### Phase 2: Feasibility spike (initial timebox 2–3 days; OD-B)
Isolated harness in `kentender_contracts/spike/` (never imported by product code), test site only, no real contract, signature, inventory or cash. Real native methods and real responsibilities, not database setup that bypasses the control being proved. Exact environment recorded: ERPNext 16.10.1, Frappe 16.12.0, app commits.

| Item | Concrete investigation | Result label |
|---|---|---|
| S0 Test world | Company, accounts, fiscal year, tax template, warehouses (accepted / custody / rejected as applicable), UOM, fixed-asset item and category, stock item, supplier, users and roles on the test site; what is configuration and what is code | one of the four labels below |
| S1 Order | Agreement fields → native Purchase Order, once, same identity on replay | |
| S2 Partial accepted receipt | Ten units with serials; eight accepted, two rejected stay out of the receipt; arrival creates no receipt; Quality Inspection split by accepted subset; rejected units never in a passing receipt; no global weakening of inspection settings | |
| S3 Asset and stock | Serialised fixed assets through the native receipt-to-asset path with no duplicate valuation or duplicate Stock Entry; the stock branch for contrast; item classification from configuration | |
| S4 Invoice | Purchase Invoice from the receipt for accepted quantity only; duplicate-invoice check behaviour; concurrent claims; early-liability posting with a credit later | |
| S5 Payment control | Maker/approver separation through the configured native transition invoked by a controlled server operation; own-entry approval refused; **every bypass**: direct Payment Entry, Journal Entry settlement, Payment Reconciliation / allocation, REST API, data import, background job; changed amount or beneficiary invalidating a pending approval | |
| S6 Signing | Core facade over the existing hook; two parties on one immutable package digest; supplier-first order; changed version ends the request; uncertain outcome keeps the same attempt; what `attest` carries for capacity and witness evidence | |
| S7 Recovery and reversal | Fail after native success but before the link is written; replay finds the same document; timeout/uncertain; funding convert replay through Budget's idempotency; cancel a posted receipt; return and credit note after payment; no duplicate signature, transaction or funding effect | |
| S8 Template and package | Does the installed STD-TPL release (1.5 on the test site, 1.4 on dev) hold Form No. 4 text, SCC clause locators and the eight-category manifest? Reproduce the Form No. 4 extraction (CM §19.2: paragraphs 2647–2667 of the retrieved DOCX, hash `ee081f60…f81`) if the file can be obtained; byte-determinism of the generated package | |
| S9 Independence | `kentender-cm-only.local` installs; supplier provider seam and Award adapter absent without error | |

**Result labels (OD-B):** *Verified* (reproduction and environment recorded); *Needs configuration*; *Needs integration code*; *Needs a reviewed requirements change*; *Not tested / Blocked* (missing fact and accountable owner). A failed item names which of the first three it is. ERPNext behaviour never silently redefines a requirement: a requirements-change result becomes a follow-up for the owner and holds only the affected behaviour. Source reading is never labelled a pass.
- Evidence in `evidence/v0_8/spike/` (commands, logs, before/after native documents and ledgers).
- **Gate CM-G02:** every S-item has a label and evidence; failures classified; the plan is amended in a dated "Spike findings" section (not rewritten above); no workflow screen is started before this gate. If the timebox is exceeded, stop and report.

### Phase 3: Package A — foundations, including the reversal and recovery boundary
- `records.py`, `errors.py` (17 codes), `clock.py`, `people.py`, command journal.
- Operation-intent model, `holds.py`, `reconciliation/recovery_matrix.md` and a table-driven test over §5.17 (eight operation rows) and §5.18 (nine correction rows): intent kind, owner, truthful state, blocked consequences, recovery order. Termination and closure boundaries included: the termination state, the Budget adjustment path and the settlement states exist as model and tests, with screens later.
- Core signing facade (D8) and Proceedings delegating wrapper; targeted Proceedings signing rerun; CM simulation provider.
- Native adapter productionised from the spike (D7) with bypass guards; Finance and stock configuration readiness check (named missing mapping and recovery owner, §17.10 CFG row).
- Rule register skeleton (D10): CM-R-01…18 as code, LQ hold keys, profile states, the synthetic profile under the flag (CM-AC-30, 36, 71 start).
- AUTH registry entries (D11), appointment subject bindings, `segregation.py`, read-DTO base and audience resolver.
- `next_steps.py` and `tasks.py` skeletons with the §6.3 ordering and deduplication (CM-AC-59 start).
- Budget owner work: `close_commitment` in `kentender_budget` with the seven §5.14.1 owner tests; BUD tracker addendum.
- Synthetic sources and `ContractCase` test base (D18).
- Page `contracts` shell, Workspace, sidebar item, Page.module collision check, shared D-ERR / D-DENIED pages.
- **Gate CM-G03:** schema, errors, holds, recovery-matrix, rules and segregation tests green; Budget owner tests green; core signing facade + Proceedings rerun green; `cm-native-gate` replays the spike's S5/S7 checks as tests on real ERPNext (L2); `/app/contracts` renders the empty shell with the rail from the sidebar.

### Phase 4: The ordinary thread (walking skeleton; CM §19.8 "next implementation step")
One frozen source-to-output thread, with deliberately thin screens, on the ten-laptop story, with the source material supplied through the D20 handoff interface by a synthetic provider (L1): package received → Prepare contract → CM generates the agreement and freezes the package → supplier signs, entity signs → Active + native order → appointment and declarations (minimal) → arrival → inspection → technical certificate → acceptance report and signatures → accepted-subset native receipt and asset → supplier invoice → certification → Finance draft, approval and payment → settlement → completion certificate → close-out.
- Boards: D01, D02, D03, D23/D24 (minimal), D04, D05, D19, D06, D07, D18, D08, D33, D09-F, D17, D09, D22, D11, D10/D40 (thin).
- Services thin but real: each command exists with its envelope and guards; rare branches are refusals-as-data, not absent.
- Install on the dev site, announced to the owner (hidden side-effect rule).
- Playwright `cm-ordinary-thread.spec.ts`: one browser session per person, walked from the menu, no Desk-form redirect, reload and back/forward keep the record.
- **Gate CM-G04:** the thread passes with real ERPNext and the real core facade with the simulation provider (L2), and the **source handoff at L1 on the synthetic provider, stated as such** — the thread is re-run against the real owner providers at CM-G05; rendered package and certificates with conformance results recorded (CM-AC-65 partial); live check recorded with literal strings.

**Phase 4 findings (15 October 2026; detail in the tracker, B16–B24).** The plan\'s Phase 4 is built and its gate CM-G04 met **for the ordinary thread only**. Differences from the plan as written: (1) the supplier\'s side is the shared supplier portal at `/supplier/contracts`, a surface on `kt_portal_surfaces`, not a Desk page; (2) the Finance steps are three (the accounting invoice, then the payment, then the settlement), as D33, D09-F and D17 draw them, with the native invoice a draft until certified; (3) native documents are created by a service principal, the Finance maker and approver act natively as themselves; (4) every choice of a person or a record uses the shared record picker; (5) the dev-site install is waiting for the owner (CM8-411). Rare branches are refusals as data or are absent and are not claimed.

### Phase 5: Package B — formation and both entry routes (CM-AC-01–05, 25–28, 32–34, 40, 65, 66)
- **Source handoff (D20; closes `package_gap.md` S1–S12).** Verify the current handoff against CM §19.4; add the core seam `contract_source_contract.py` and the versioned `ContractSourceHandoff`; implement each missing owner-interface change as an additive seam in its owning module with a tracker addendum — Tenders and the template release (issued instance, release, addenda, requirements and technical schedules, GCC/SCC with clause ids including payment, advance, security, remedies and change terms, Form No. 4 source with anchors), Bid Submission / Evaluation (accepted tender and clarifications), Award (notification identity, signing-window result with counting basis, funding lineage), site configuration (entity particulars read once); CM resolves and verifies each reference, generates the agreement, assembles the eight-category manifest plus addenda and freezes the package with source versions and hashes. **Update the affected current documentation** as proposed successors under the document-change protocol (AWD, TPR, STD-TPL, BDS and BUD as touched; register versions, owner approval). **Prove that every required source is available** for the canonical TND-MOH-2027-002 package (`test_cm_source_availability`); a gap that cannot be closed blocks formation acceptance and is reported to the owner as a reviewed requirements question, never worked around.
- Award adapter: `ReceiveAwardPackage` / `ReceiveAwardUpdate` / `ReceiveAwardPublicationEvent` (events before package, no-award events, corrections, source-version order, original trigger times); optional-adapter disablement.
- Preparation: particulars, source-and-terms mapping, signing-window and restriction rechecks at every commit, security evidence and verification (D25), outside signature (D26), refusal / expiry / Did not proceed, uncertain signing recovery, PO and funding failure recovery without fresh signatures.
- Funding: reservation revalidation and conversion with source allocations preserved (CM-AC-33, 34).
- Existing-contract route: `RegisterExistingContract`, `ReviseContractIntake`, `ConfirmOpeningPosition`, `StartContractManagement`; stable unique key, source history, reconciliation on conflict, unsupported-scope intake; imports post nothing (CM-AC-25–28, 40).
- Rules CM-R-01–04, 08, 17, 18 live; LQ-03 and LQ-05 holds.
- Boards: D01 variants, D02 (H, S, V), D03 (A, W), D12 (G), D21 (H), D25 (R, J), D26 (E, H).
- Playwright: `cm-formation.spec.ts`, `cm-existing-contract.spec.ts`.
- **Gate CM-G05:** services (L1) and `cm-seams-gate` on the real Award package, real owner source providers, real Budget and real native order (L2) green; **every required source available and verified for the canonical package, or formation is not accepted**; the Phase 4 thread re-run against the real providers; the affected owner documents updated as proposed successors; `cm-independence-gate` green.

### Phase 6: Package C — delivery, inspection, acceptance, native stock and assets (CM-AC-06–10, 38, 42, 49, 67, 70)
- Appointment, declaration, conflict and replacement (D23, D24 variants); receiver separation.
- Arrival and custody, returns before acceptance, replacement units linked to the original entitlement, excess/premature/ambiguous delivery.
- Inspection from frozen criteria, Needs review, coverage and sampling, technical certificate, acceptance report with every required current signer, dissent, correction and successor, authority-to-accept check (a committee report alone is a recommendation until the decision-maker's written authority is evidenced — §19.5).
- `PostAcceptedReceipt`: one accepted-subset receipt and asset operation through the intent model; related services without stock or asset (D31).
- Boards: D04, D05 (M), D06, D07 (P), D19, D23, D24 (C, S, X), D31 (A).
- Playwright: `cm-delivery-acceptance.spec.ts`.
- **Gate CM-G06:** L1 services; native stock and asset reconciliation to Finance at L2 (`cm-native-gate`).

### Phase 7: Package D — invoices, certification, embedded Finance, advances, settlement (CM-AC-11–14, 17, 31, 39, 41, 45–47, 52)
- Supplier claim once, matching, duplicate hold, correction-first policy, certification with the acceptance-signer exclusion, entitlement locked and consumed once.
- Finance maker and approver through KenTender editors over the native adapter; return for correction; invalidation on changed amount or beneficiary; settlement recording with independent evidence; partial instalments, reversal, credit/write-off kept out of Cash paid.
- Advances (D29): guarantee, approval, recovery.
- Boards: D08 (C, L), D18 (C, R), D33 (A, U, W), D09 (AUD, F, T), D17 (H, S), D28 (C, F, V), D29 (H, R).
- Playwright: `cm-invoice-finance.spec.ts`, `cm-payment-settlement.spec.ts`.
- **Gate CM-G07:** L1 services; `cm-native-gate` with the full bypass matrix and concurrency (CM-AC-31, 39) at L2; no routine step leaves KenTender.

### Phase 8: Package E — changes, delay, warranty, security, reporting, termination (CM-AC-15, 22, 35, 37, 51, 53–55, 68, 69)
- Issue / correspondence, change request → review → AO decision → executed amendment → activation (D13, D14, D27, D34 including **Change requires legal review**), delay adjustment (D36), paid-unit warranty replacement (D35), warranty claim and remedy verification, security actions and claims (D16, D37), termination request, decision, notice and effective consequence (D20).
- Compliance obligations and reports: publication and award reporting, monthly consolidated progress, quarterly variation, payment follow-up, termination record; cutoff, versions, Incomplete on failed reads, submission evidence (CM-R-13–15).
- Funding adjustments for effective variation and termination through `adjust_commitment`.
- Boards: D13 (C, S), D14 (P), D15 (L), D16 (P, W), D20 (P, T), D27 (A, R), D34 (A, H, L, P, R, X), D35 (C, H, V), D36 (A, E, H, S), D37 (A, P, X), D10/D40 (D, S) completed.
- Playwright: `cm-change.spec.ts`, `cm-warranty-security.spec.ts`, `cm-termination.spec.ts`, `cm-reports.spec.ts`.
- **Gate CM-G08:** L1 services; real Budget adjustments and real native credit/return/cancel at L2.

### Phase 9: Package F — completion, close-out and financial finalisation (CM-AC-16, 29, 35, 56–58, 69, 70)
- Final acceptance, completion certificate, close-out review with surviving obligations, close-out correction and reopening, termination settlement, `close_commitment` integration with **Funding finalisation pending** until acknowledged, security return clock from AO final acceptance (CM-R-09).
- Boards: D11 (B, C, T), D22 (P), D32 (H), D38 (P, R, T), D39 (C, H, P).
- Playwright: `cm-closeout.spec.ts`.
- **Gate CM-G09:** L1 services; real Budget closure and real native reconciliation at L2.

### Phase 10: Access, dead ends, reversal sweep and retries (CM-AC-19, 20, 43, 48, 50, 59, 60, 62, 71)
- Per-audience DTO filters for every reader of §6.2, supplier projections, technical read with no mutation, protected reads returning Not found and audited; `test_cm_leakage`.
- `test_cm_dead_end`: every stored state × hold × actor through `next_step.problems` (no disabled-action dead end).
- The §5.17 failures alone and in combination; the §5.18 corrections at each boundary (before proof, before posting, after receipt, after liability, after settlement); `test_cm_idempotency`.
- Expired authority, cross-supplier access, supplier self-acceptance, Finance self-approval, maker confirming settlement, acceptance signer certifying, technical business action.
- **Gate CM-G10:** `make cm-leakage-gate` and `make cm-dead-end-gate` green.

### Phase 11: Canonical seed stage and demo profiles (CM-AC-21)
- Stage `contracts` after `award`; isolated branches seeded through production commands and labelled synthetic Trust and Finance evidence; second run idempotent with no new audit transitions.
- Demo profiles, one per main stage; `cm-demo-walk.spec.ts` walked from the sidebar, My Work and the bell, one browser session per person.
- **Gate CM-G11:** `make seed-canonical SITE=… THROUGH=contracts` and `make seed-canonical-validate` green; demo walk green.

### Phase 12: Release evidence and whole-chain acceptance
- `ui-cm-fidelity-gate` over all 157 boards (compared or recorded as not compared with a reason).
- The eight whole-chain scenarios of §14.4 at **L2**: normal goods; mixed acceptance and replacement; multiple deliveries, invoices and instalments; quantity variation; disputed delay; paid-unit warranty; termination with advance; imported prior activity.
- CM-AC map closure with proof levels; persona browser pass as real users (Charles, Amina, Julia, Peter, Grace, Brian, Josphat, Beatrice, Mary, David, Naomi, Daniel); usability acceptance of §17.12 (one ordinary and one existing-contract journey without a native-form redirect).
- `RUNBOOKS.md` (simulation switches, fixture reset, uncertain-operation recovery, retry of order / receipt / invoice / payment / funding / report dispatch).
- One cross-module regression run, justified here because it is release time: Award, Budget, Proceedings signing, the supplier-account provider and the procurement UI smoke.
- **Gate CM-G12:** `ui-cm-release-evidence-gate`.

### Phase 13 (owner-gated; every row starts `Blocked — owner`)
- Owner approval of the proposed successor documents, and the remaining amendments of CM §17.10 and §19.8, each as a Proposed document under the document-change protocol: AUTH, CFG, BUD, PRC, KT-STD, TRUST, LAW, SEED-OPS, register and workbook. **The source-handoff amendments (AWD, TPR, STD-TPL, and BDS / BUD / CFG as touched) are written in Phase 5 (D20); only their approval is owner-gated.**
- LQ-01…06 decisions; CM-LEGAL-01 current-deployment clearance; a verified production rule profile.
- CM-PROOF-01/02 and CM-FUND-01 on the production-equivalent installed site; Finance policy confirmations A1–A3.
- Production Trust provider, the execution and witnessing method (LQ-05), real notice and report channels and evidence, official eGP/PPRA action ownership.
- A security review and production enablement.
- **No gate in this plan.**

## Conflicts and findings to log (Phase 0)

| # | Conflict or finding | Treatment |
|---|---|---|
| C1 | CM cites AUTH v1.11, CFG v0.18, KT-STD v1.25 and AWD v0.5; the folder holds AUTH v1.15, KT-STD v1.27 and AWD v0.6 (proposed). | Phase 0 reads the latest of each; register differences; build to the approved latest. FU-CM-36. |
| C2 | The signing facade and the signing hook's only provider live in Proceedings (procurement). | D8: core facade, Proceedings wrapper, CM-owned simulation provider. FU-CM-30. |
| C3 | The empty `contract_management` and `inspection_acceptance` skeletons are inside `kentender_procurement`. | D1: deleted. |
| C4 | The Award handoff does not yet carry the source material §19.4 needs: 12 sources, 5 absent, 5 partial, 0 unknown, 2 present (`reconciliation/package_gap.md`). | Verify the current Award/source handoff against CM §19.4. Identify and implement any missing owner-interface changes, updating the affected current documentation. CM generates the agreement and freezes the complete incorporated package. Formation acceptance requires proof that every required source is available; unresolved gaps block that acceptance. (Plan D20; tracker CM8-513…521.) |
| C5 | Both Award's simulation Contracting receiver and CM's real receiver answer `kt_award_contracting_receivers`; the hook takes the last provider that answers. | Phase 5 fixes the order so CM wins outside the simulation flag and the stand-in stays silent when CM is installed; guard test. |
| C6 | CM §10 draws **Illustrative test record** and "Not required under these test terms" labels; DEC-044 forbids test banners and labels on user-facing surfaces. | Runtime follows DEC-044: the synthetic profile is a stored classification, not a banner. The board literal is fixture data. FU-CM-31. |
| C7 | `close_commitment` does not exist in Budget. | D13: built in `kentender_budget` in Phase 3 with the seven owner tests. FU-CM-04. |
| C8 | The design folder and both CM documents are untracked; the provenance gate is repo-wide. | FU-CM-34: ask the owner to commit them. |
| C9 | CM §7 names AWD package contract identifiers that Award renamed or did not publish in v0.5/v0.6. | Phase 0 seam register; no deployed Award name is changed from a label (§17.10 AWD row). |
| C10 | Daniel Otieno is a technical user whom My Work skips; technical read has no business commands. | D14: Support Issue rows, as Award (C9). |
| C11 | A Page whose module names a real Module Def can swap the sidebar on record routes. | Phase 1 checks `/app/contracts/{id}` and sets Page.module as Award and Evaluation did. |
| C12 | CM-OD-08's separate-reconciler question remains with Finance. | A2; FU-CM-24. |

## Risks

- **Native bypass completeness.** Payment holds must hold on every native path. Mitigation: Phase 2 S5 tries each path; Phase 7 gate runs the full matrix; a path the spike cannot guard is a requirements-change result, not a UI-only safeguard (CM-AC-17).
- **Core signing change touches Proceedings.** Mitigation: a thin wrapper keeps its API; one targeted rerun of its signing tests (rule 12).
- **The agreement source may not be obtainable or reproducible.** The PPRA file is public but the issued release in STD-TPL may not hold Form No. 4. Mitigation: S8 decides early; a gap is a follow-up, and the formation package is held, not improvised (§19.1: implementation does not draft legal prose).
- **The source handoff touches several owner modules** (Tenders, the template release, Bid Submission / Evaluation, Award, Budget, site configuration). Mitigation: one versioned interface and one core seam (D20); additive owner seams with tracker addenda; the availability proof is a named test; a gap that cannot be closed blocks formation acceptance rather than being worked around.
- **ERPNext test data accumulating on the test site.** Mitigation: cancel-and-delete cleanup per module, `make test-site-rebuild` between gates.
- **Scale.** About three to four times Award by my estimate (not measured). Mitigation: the thread first, shared board renderer, table-driven recovery and rule tests, targeted reruns only.
- **A synthetic pass mistaken for acceptance.** Mitigation: proof levels in every row; gates require L2.
- **Independence erodes by accident.** Mitigation: import-boundary test and `cm-independence-gate` at every package.
- **Version drift between ERPNext and the spike.** Mitigation: exact versions recorded; a change of either re-runs `cm-native-gate`.
- **Legal holds mistaken for failures.** Mitigation: holds are per action with a named holder; a legal hold never disables unrelated factual recording (CM-AC-71).
- **Site-wide test mutation.** Mitigation: namespaced rows only, registered cleanup, one test module at a time, preflight before every Python run.

## Verification

```bash
cd /home/midasuser/frappe-bench
bench --site kentender-test.local run-tests --app kentender_contracts --module kentender_contracts.tests.<module>
./scripts/bench-with-node.sh build --app kentender_contracts
cd apps/kentender_v1
make cm-preflight
make cm-services-gate            # L1 synthetic; target under 3 minutes
make cm-seams-gate               # L2: real Award package, real Budget, real facade
make cm-native-gate              # L2: real ERPNext posting, bypass and concurrency matrix
make cm-independence-gate        # scratch site without the tendering apps
make cm-leakage-gate
make cm-dead-end-gate
make ui-queue-check
make ui-cm-<slice>-gate
npx vitest run --project contracts   # also inside make ui-structure-gate
make ui-cm-fidelity-gate
make ui-cm-release-evidence-gate
make seed-canonical SITE=kentender-test.local THROUGH=contracts
make seed-canonical-validate SITE=kentender-test.local
```

**Live browser walk (Phases 4, 11, 12), on the test site, from the menu, real personas:**
1. Charles opens **Contract Management → Contracts**, sees **Prepare contract** for the package Award delivered, reviews the generated agreement and sends it for signature.
2. Mary (390 px) signs first; Amina signs the same version second; the contract becomes Active and the native order exists.
3. Julia, Peter and Brian declare interest; Grace records the arrival of ten laptops with serials; nothing is posted to stock.
4. Peter records observations; Julia prepares the report; Julia, Peter and Brian each sign; eight units post as fixed assets; the two rejected units stay in custody.
5. David submits the invoice and corrects it; Charles certifies; Josphat prepares the native invoice and payment; Beatrice approves; settlement is confirmed with evidence and shows cash only for confirmed transfers.
6. The replacement units arrive, are inspected, accepted and posted without a second payable; Amina records final acceptance; Charles issues the completion certificate; Amina closes the contract; surviving obligations stay assigned.
7. A registered existing contract (`CM-MOH-2027-EXT-001`) goes through opening-position confirmation and start of management with no re-signing and no historical posting.
8. Naomi reads only; Daniel sees site-wide read without a business action; a cross-supplier link and a Finance self-approval fail with no side effect.
9. Repeat each isolated branch on its own fixture identity.

## Phase 0 findings (14 October 2026)

Recorded after Phase 0; the phase text above is not rewritten. Tracker rows CM8-001…011 and `reconciliation/` hold the evidence.

1. **157 boards in 43 designs, 83 named commands and reads** (the earlier 122 and "roughly 65" are superseded; tracker B1, B2).
2. **The current Award/source handoff does not yet carry the source material CM needs** (`reconciliation/package_gap.md`: of 12 sources, 5 absent, 5 partial, 0 unknown, 2 present). Award supplies source material; CM generates the agreement and freezes the package. **This is required Package B work, not a follow-up (owner direction 14 Oct 2026, OD-E; D20):** the missing owner-interface changes and the updates to the current documentation are implemented in Phase 5, and formation is not accepted until every required source is proved available. Phases 3–4 use a synthetic provider on the same interface at L1; CM-G05 requires the real providers on the canonical package.
3. **`bench run-tests` is blocked on `kentender-test.local`** by a fiscal-year overlap between ERPNext's test records and KenTender's `2040-2041` (FU-CM-43). Phase 1's first Python test and the spike's S0 need it cleared first.
4. **No owner document applies any CM amendment**; every §17.10 change is open and must be written against the current register versions, not the versions CM cites (`reconciliation/latest_versions.md`).
5. **Three command-map gaps and nine commands without a board** (FU-CM-42) and three fixtures without identities (FU-CM-41) are spec or design questions for the owner; the build does not invent them.
6. **The independence scan is clean** for `kentender_suppliers` and for `kentender_core` outside `seeds/`; the real proof is the scratch site in Phase 1.

## Phase 1 findings (14 October 2026)

Recorded after Phase 1; the phase text above is not rewritten. Tracker rows CM8-101…107 and B9–B12 hold the evidence.

1. **The independence site is SQLite** (no MariaDB root access exists). It proves that core, supplier accounts and Contract Management install, migrate and pass the app's tests with no tendering app present. It does not prove native-posting behaviour, which is proved on the MariaDB test site at L2 (D12, FU-CM-38).
2. **The record guard is core's `CommandWriteGuardMixin`**, not a copy of Award's flag pattern (D3): one shared mechanism, family `Contract Management`.
3. **Later `cm-*` gates are added with their phases**, not as empty targets (tracker rule 13); Phase 1 wires `cm-preflight`, `cm-services-gate` and `cm-independence-gate`.
4. **The dev site is untouched.** The app is installed on the test site and the independence site only; the dev install stays at Phase 4 (FU-CM-37).

## Phase 2 findings (15 October 2026)

Recorded after Phase 2; the phase text above is not rewritten. Evidence and the full table are in `evidence/v0_8/spike/README.md`; tracker rows CM8-201…211 and B13–B14.

**Result (qualified at the owner's review, 15 Oct 2026): every item is verified, or verified with a named need.** "No reviewed requirements change" holds for **Contract Management's business rules**; the spike found **implementation gaps in enforcing them**, and **signing, the template release and the source handoff still need changes to their owning services and documentation** (FU-CM-49 and FU-CM-30; FU-CM-50 and FU-CM-07; FU-CM-32, FU-CM-05 and FU-CM-06). **CM-G02 is the feasibility gate only: it does not establish formation, Finance or production acceptance.** The facts that change the build:

1. **A payment guard is mandatory and must sit on `before_submit` / `before_update_after_submit` of Payment Entry and Journal Entry.** Native submit rights, Administrator, the Desk save and a workflow button all post a Draft payment; native hold is not a payment hold; every route settles an uncertified invoice. One guard, opened only by the controlled KenTender operation, refuses every route. It also needs **the supplier-level rule** (any payment to a supplier with contract invoices, referenced or not), the **entitlement rule** (certified amount less settled), the **invalidation rule** (changed amount or beneficiary returns a pending payment to Draft) and a **row lock on the invoice**: without it two concurrent approvals both posted and the books disagreed with the cash. (D7 stands; its detail is now this.)
2. **The maker/approver mechanism is the native workflow** with a separate approver role and `allow_self_approval = 0`; it refuses own-entry approval even inside the controlled operation. D11's registry roles must map to ERPNext roles (FU-CM-48).
3. **The operation-intent model works** (D5): a hard crash after a native commit and before the link is recovered by identity without a second document; replays are no-ops.
4. **Serials are CM's to guard.** ERPNext invents a serial when none is supplied and the Asset record has none; CM refuses a serial-item receipt with an unidentified unit and assigns its unit reference to each asset inside the receipt's transaction.
5. **Reversal order is fixed by ERPNext:** inspection then receipt, invoice then receipt, asset then receipt; a paid return gives a stock return and a credit note and no automatic refund. The adapter carries this order (D7).
6. **Signing (D8) needs one addition:** a `reconcile(correlation_id)` on the core facade and an idempotent CM simulation provider; the seam alone is stateless (FU-CM-49).
7. **The agreement package (D9, D20):** generation is byte-reproducible for HTML and PDF; the installed release's assets are retrievable and digest-verifiable; but Form No. 4, the GCC and the SCC have no stable anchors and typed terms for advance, invoice process, change and termination do not exist (FU-CM-50). The owner provider of D20 therefore serves those fragments as separate digest-bound documents.
8. **Net payable is read from the ledger** after a credit note (FU-CM-53).

**Carry-over into Phase 3** (additions to the Phase 3 list above): promote `guards.py` to `services/`; the custom-field fixtures (FU-CM-48); the serial refusal and unit-reference assignment; the reversal-order table in `reconciliation/recovery_matrix.md`; the `reconcile` addition to the signing facade; the savepoint-and-commit test pattern and the registered teardown used by the harness (D18).

## Phase 3 findings (15 October 2026)

Package A foundations are built; the gate is the foundations gate only (tracker CM-G03). What running the code taught, beyond the plan:

1. **ERPNext creates a receipt's assets with `db_insert`, which fires no asset event.** The unit reference is therefore written from a Purchase Receipt `on_submit` event that runs after ERPNext's own, in the same transaction (D7 expected an asset event).
2. **Serial numbers survive a cancelled receipt** (as spike S7b2 recorded); the units leave stock and the serial records remain.
3. **A refused payment call records nothing and frees its key** in Budget's idempotency journal, so a replay check must use a key that completed.
4. **The Finance responsibilities project their own identically-named roles.** The Payment Entry workflow is allowed to those roles (readiness names any mismatch) rather than coupling the registry to ERPNext's broad Accounts roles, which could strip a role someone else relies on.
5. **Counting a Closed commitment** was a four-place change across three apps, found by a whole-repo search; one test now fails if any reader counts only Active.
6. **The module-sidebar collision does not break navigation**, but not for the reason first written here (that negative control was unreliable and is withdrawn). On a full site the module key and the route `contracts` both resolve to the shared Procurement rail; on a site without Procurement the page shows its own sidebar. Browser-verified on both: the rail is not rebuilt across 1-, 2- and 3-segment routes. The shared rail already reserved a Planned slot for this module; core's `kt_navigation_overrides` hook lets the installed app take it over without editing Procurement's file.
7. **Environment:** `sites/apps.txt` was rewritten on 14 October and lists `frontend`, which breaks Frappe's own build setup for every app (FU-CM-58). Two pre-existing test-site failures were found by a dependency rerun and are not Contract Management's (FU-CM-57).
8. **Method:** seen failing before the code existed: the operation intents, the core signing facade, authority and segregation, the readiness check, task ordering and the Budget `close_commitment` tests. Written with or after their code, and compensated by deliberate-defect (mutation) checks instead: holds, the recovery matrix, the signing simulation, the rules and profiles, the audience resolver and the readiness role mapping. The workspace read tests were written first but not run until the code existed, and the native tests replay behaviour the Phase 2 spike had already observed. Each tracker row says which applies.
9. **The standard asset build was broken by an uninstalled app** (`frontend`, in `apps.txt` but never pip-installed), fixed by installing it. The first standard build then replaced the `frontend` app's built stylesheets and left the Desk unstyled bench-wide until `frontend` and Budget were rebuilt: after any change to `apps.txt` or the app links, check every `assets.json` entry against the disk.
