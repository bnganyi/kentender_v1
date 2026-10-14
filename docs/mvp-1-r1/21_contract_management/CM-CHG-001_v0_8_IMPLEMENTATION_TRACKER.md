# CM-CHG-001 v0.8: Contract Management, tracker

| Control | Value |
|---|---|
| Version | 0.8-tracker.1 |
| Date | 14 October 2026 |
| Status | Phase 0 Done 14 Oct 2026 (CM-G00; CM8-009 and CM8-010 Partial); Phases 1–13 Planned. AC map: 0 of 71 Done. 0.8-tracker.1 read: Planned. Owner instruction 14 Oct 2026: "Proceed with the plan, implementation tracker, and follow-ups similar to other modules". |

**Authority:** `KenTender_CM-CHG-001_Contract_Management_v0_8.md`, *Approved — Project Owner, 14 October 2026* (requirements and artboard specification, §19 and CM-AC-65–71 included). Governing standard: KT-STD-001 — CM cites v1.25; the folder holds v1.27 (FU-CM-36, Phase 0 reads the latest).

**Plan:** `CM-CHG-001_v0_8_Implementation_Plan.md`. It holds owner decisions OD-A…OD-E, technical decisions D1–D20, the Finance test assumptions A1–A4, proof levels L1–L3 and conflicts C1–C12.

**Companions:** `CM-CHG-001_v0_8_FOLLOW_UPS.md`; Phase 0 `reconciliation/`; later `evidence/v0_8/` (spike evidence in `evidence/v0_8/spike/`) and `RUNBOOKS.md`.

**Design:** `design/CM Artboards.dc.html` + `cm-data-1…4.js` — 157 boards in 43 designs (extracted by script in Phase 0; the earlier count of 122 is superseded).

**Started:** 14 October 2026 (Phase 0).

## Tracker rules

1. **Rows are permanent.** Status vocabulary: `Planned` / `In progress` / `Blocked` / `Blocked — owner` / `Partial` / `Partial — synthetic` / `Done`. Reversed decisions are struck through in place, never deleted.
2. **`Done` needs the row's own evidence:** a command with result counts, a named test, a commit, or a described browser observation with literal rendered strings. Never record a result that was not observed. Reading source is never recorded as a pass.
3. **Proof levels (plan "Proof levels").** A row proved only against synthetic sources, a synthetic Award package or the simulation signing double is `Partial — synthetic` (L1) and says so. **An acceptance row or a package gate closes only at L2**: the real Award package through the real hook, the real Budget services, **real ERPNext documents**, the real core signing facade, the real supplier-account provider. L3 parts (legal profile, production Trust, real channels, Finance policy confirmation, release) are separate Phase 13 rows and stay `Blocked — owner`.
4. **Prohibited in new code** (CM §6.4, §9.2, §16 and the approved dispositions):
   - a duplicate invoice, stock or payable ledger; any direct ledger, stock-ledger, asset-ledger or Payment Ledger write; a second approval of a native transaction; a Stock Entry for an asset receipt;
   - a generic acceptance checkbox, an arbitrary approval chain, a hidden supplier score, a retrospective edit to a signed document, a waiver by comment, a generic **Override** or **Approve anyway**, a free-text outcome standing in for a typed one, unsupported actions disguised as **Record outcome**;
   - inferring "paid" from a zero balance or a queued entry, "cash paid" as total minus outstanding, publication completion from a queued job, receipt of an event as completion of its duty, **a security release from expiry**, completion from Stage 1 alone;
   - an acknowledgement task for a successful automatic check or handoff; a manual "accept handoff"; an extra confirmation page whose only job is to display success; re-entering a captured fact;
   - a routine redirect, iframe or launch button to a standard Frappe form for registration, receipt, inspection, claim, Finance preparation or approval, settlement or correction; a Desk fallback for an unsupported native field;
   - a hard-coded 14-day, 30-day, 60-day or other legal period; a Regulations-only deadline presented as verified law; an officer-editable rule, percentage or threshold; a legal hold cleared by an edit, a label or a UI choice;
   - a global weakening of Quality Inspection or receipt validation to process a return or rejection; rejected or uninspected units in a passing receipt; a native receipt draft created by arrival;
   - the acceptance signer certifying a claim that relies on that acceptance; a receiver signing acceptance of their own arrival; a Finance maker approving or confirming their own payment; a change requester recommending or deciding their own change;
   - any import of `kentender_procurement`, `kentender_budget` (except through the guarded adapter), `kentender_strategy` or any tendering module from `kentender_contracts` outside `adapters/`; a read of a tender, bid, evaluation or award table; a fabricated Award, Tender, Bid or Evaluation record for an imported contract;
   - expecting Award to hold an assembled eight-category agreement package; a CM read of tender, bid or template tables to fill a source gap; asking a user to re-upload a source KenTender already holds; declaring formation complete while a required §19.4 source is unavailable or unverified;
   - a new menu destination, per-persona route, per-stage module, dashboard metric, completion percentage or custom rule editor; a board number or task ID as a destination;
   - `kentender_core.cl_surface_registry.js`, Civic Ledger or Stitch Desk classes (Industry only); test banners or labels on a user-facing surface (DEC-044); stand-ins loading without `kt_bds_simulation_environment`.
5. **Governing sections:** CM v0.8 §10 and the boards govern visual and content fidelity (ported class-for-class); §4, §5 and §7 govern behaviour; §5.10 and §6.3 govern next steps, work items and ordering; §5.17 and §5.18 govern failure and correction; §6 governs authority and reads; §8 governs error copy verbatim; §9 and §9.0 govern routes and screen mapping; §19 governs rules, the agreement package and the certificate outputs; §10/§11 map each control to one command or read. Board literals (dates, `CM-MOH-2027-…` references, serials) are fixture data; the runtime shows actual generated references and events.
6. **Mapping:** every visible action maps to exactly one §7 command or read (CM-AC-44); every cross-owner effect is one `Contract Operation Intent` kind (plan D5).
7. **Site safety:** run CM tests on `kentender-test.local`, never on dev; never run a CM Python module while a Playwright process is active (`cm-preflight`); one `run-tests` at a time; CM tests write only `CM_TEST`-namespaced rows and register cleanup; test-created ERPNext documents are cancelled and deleted by that cleanup and the site is reset with `make test-site-rebuild` between phase gates; browser-pass records count as test data; never reset credentials or force a logout on a live site.
8. **No workflow screen before CM-G02** (the spike gate). Phases 0–2 build tooling, scaffold and the spike harness only.
9. **Owner-document seams:** every change to another owner's code records an addendum row in that owner's tracker in the same step and keeps its follow-up open. Changes planned outside `kentender_contracts`: `kentender_core` (registry entries, signing facade, canonical stage, Makefile), `kentender_budget` (`close_commitment`), `kentender_procurement` (Proceedings signing wrapper, skeleton removal, Award-receiver precedence), `tests/ui/fidelity`.
10. **Synthetic worlds are built once per module** (`ContractCase`); no upstream world is rebuilt per test. The real seams are proven only by `test_cm_seams.py`, `test_cm_integration.py`, `cm-native-gate`, the canonical `contracts` stage and the demo walk.
11. **Upstream reruns are targeted.** Before rerunning another module's tests, name the changed file that justifies it and run only that one test module. Full cross-module regression happens once, at Phase 12.
12. **Vertical slices from Phase 4:** service → API → screen → one Playwright spec with one fixture entity → a live click-through from the menu. The slice's row is closed only after the live check.
13. **Gates are wired when created** (Make targets, vitest project in `ui-structure-gate`); none is left "owed".
14. **Rare branch boards** are compared where cheap; otherwise recorded in `departures/contracts.js` as not compared, with a reason. Do not chase an exact match on a rare board.
15. **Failed spike items** carry one of: Needs configuration / Needs integration code / Needs a reviewed requirements change / Blocked. ERPNext behaviour never silently redefines a requirement; a requirements-change result opens a follow-up and holds only the affected behaviour.
16. **A defect found** is fixed in every instance and its shared cause, with a guard added in the same turn.
17. **Update this tracker per proven piece**, with evidence, in the same step.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 14 Oct 2026 | OD-A: dedicated Contract Management app. Owner, verbatim: "Do **not** relax the independence requirement. CM must operate without the tendering modules, using the existing-contract intake route. Reuse core authority, signing, evidence and task services, plus ERPNext. Award integrates through an optional adapter; CM must not depend on tendering controllers or tables. This is a focused CM boundary, not permission to split every existing app." | CM-AC-25 and CM-AC-32; the empty skeletons sit inside the tendering app. App name `kentender_contracts` is the plan's proposal. |
| 14 Oct 2026 | OD-B: feasibility spike first. Owner, verbatim: "Feasibility spike: yes, before building the workflow screens." Initial timebox 2–3 days; five evidence items; failures classified as configuration, integration code or a reviewed requirements change. | The module's main risk is native posting, payment control, signing and recovery. |
| 14 Oct 2026 | OD-C: Finance, proceed with explicit test assumptions and obtain targeted confirmation: acceptance-based receipt posting for the specified test contract; CM-OD-08 settlement recorder with independent evidence (confirm whether a separate reconciler is required); serialised fixed assets for the demonstration subject to capitalisation policy. | Plan A1–A4; FU-CM-24, 25, 26. |
| 14 Oct 2026 | OD-D: three tightenings. (1) "Synthetic upstreams support development; package acceptance must include the actual relevant integrations." (2) "Design reversal, termination and recovery boundaries early, even if their complete screens come later." (3) "Use CM's prescribed screen mapping; 'roughly 30 screen families' is not authority to introduce 30 destinations." | Proof levels L1–L3; Phase 3 recovery matrix; plan "Screen mapping". |
| 14 Oct 2026 | OD-E: the source handoff is required Package B work. Owner, verbatim: "The concern \"Award may not carry the full agreement package\" is valid, but \"a follow-up\" is too weak. This is a required integration dependency already identified in approved v0.8 §19.8. One distinction matters: **Award supplies the authoritative source material; CM generates the agreement.** Award should not be expected to hold a completed eight-category agreement package before CM prepares it." Handling (verbatim): "1. **Check the current Award handoff** against CM §19.4 … 2. **Supply missing material through an explicit, versioned interface** from its owning module. Immutable document references are acceptable if their exact contents remain retrievable and verifiable. 3. **CM assembles the complete signing package**, including its generated agreement, preserving source versions and hashes. 4. **Close any interface gap within the formation package's implementation.** It cannot remain an unspecified future task while formation is declared complete." Replacement wording: "Verify the current Award/source handoff against CM §19.4. Identify and implement any missing owner-interface changes, updating the affected current documentation. CM generates the agreement and freezes the complete incorporated package. Formation acceptance requires proof that every required source is available; unresolved gaps block that acceptance." | Plan D20 and C4; Phase 5 rows CM8-513…521; CM-G05; FU-CM-32 re-scoped, FU-CM-40 decided. Corrects the Phase 0 framing in `package_gap.md` (version 0.8-package-gap.2). |
| 14 Oct 2026 | v0.8 supersedes the "legal and templates are unverified" caveat of the earlier strategy: content and mappings are now specified; named legal questions (LQ-01–06) and actual implementation proof remain. | CM v0.8 §19.8. |
| 14 Oct 2026 | Owner, verbatim: "Proceed with the plan, implementation tracker, and follow-ups similar to other modules". | Authorises these three files only; no code, install or site change is authorised by it. |

## Work items

### Phase 0 — Reconcile

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-001 | `reconciliation/artboard_inventory.md` (all board identifiers by script, classified, one slice and one §9.0 surface each) | Done | `reconciliation/artboard_inventory.md`, extracted by script (`tools/extract_boards.mjs` → `tools/build_inventory.py`): **157 boards in 43 designs** = 43 main, 91 state variants, 23 dialog boards; slices 3:2, 4:24, 5:23, 6:11, 7:27, 8:52, 9:18; 9 surfaces; the count matches the design page's own header. **Corrects the earlier count of 122** (a text search that missed ids such as `D17 · Posted` and the dialog boards) |
| CM8-002 | `reconciliation/error_contract.md` (17 codes verbatim by script; `errors.MESSAGES` test later) | Done | `reconciliation/error_contract.md`: 17 codes copied verbatim from §8 by script, each with its source line; `test_cm_errors` compares `errors.MESSAGES` with it from Phase 3 |
| CM8-003 | `reconciliation/next_step_register.md` (§5.10 rows → holder, task, clearing event, test) | Done | `reconciliation/next_step_register.md`: 32 §5.10 rows verbatim with holder, clearing event and a proposed test name each, plus the §6.3 ordering rules |
| CM8-004 | `reconciliation/command_map.md` (§7 commands, §11/§11.1 controls, board actions → one command or read) | Done | `reconciliation/command_map.md`: 83 commands and reads named in §7 (script count); 273 (design, control) pairs from the 157 boards = 187 Named, 83 Inferred, 3 Gap; 61 commands or reads have a board control, 22 have none (9 of them flagged as design gaps). The script fails on any unmapped control and on any command name not in §7. Gaps logged as FU-CM-42 |
| CM8-005 | `reconciliation/fixture_chronology.md` (ordinary ten-laptop path + §10.1B identities, isolation) | Done | `reconciliation/fixture_chronology.md`: 15 §10.1B rows and the chronology paragraphs verbatim, boards per identity from the design, 78 base-reference boards sorted by instant. **Finding:** D26, D28 and D29 have no identity in the spec and every board header shows the base reference; three ids proposed (FU-CM-41) |
| CM8-006 | `reconciliation/seam_register.md` (CM-IF-01…08 → function, hook, adapter or gap) | Done | `reconciliation/seam_register.md`: CM-IF-01…08 → planned function, what exists today, gap and follow-up. Searching AUTH v1.15, CFG v0.19, KT-STD v1.29, TRUST v0.6 and TPR v0.20 for `CM-CHG` / `Contract Management` / `close_commitment` found no application of any §17.10 amendment |
| CM8-007 | `reconciliation/rule_register.md` (CM-R-01…18, LQ-01…06 → module, event, hold key, test) | Done | `reconciliation/rule_register.md` (`tools/build_rules.py`): CM-R-01…18 and LQ-01…06 with verbatim class, source and question; authored module, hold key, affected commands, phase and test name marked proposed |
| CM8-008 | `reconciliation/package_gap.md` (current Award/source handoff vs §19.4 and §5.14; gaps → Phase 5 interface work, D20) | Done | `reconciliation/package_gap.md` version 0.8-package-gap.2 (re-framed 14 Oct 2026 after owner direction OD-E): 12 sources the owning modules must supply — 5 absent, 4 partial, 1 unknown, 2 present — against what `award/services/eligibility.py::_content` freezes and release 1.5's `downstream_rules.json`; CM-produced items listed separately (generated agreement, eight-category manifest, frozen package). **Required Package B work (D20; CM8-513…521), not a follow-up.** Version 0.8-package-gap.1 had counted 16 rows and treated the eight-category package as something Award should carry; superseded |
| CM8-009 | Latest-version check of AUTH, CFG, KT-STD, AWD, BUD, STD-TPL, TPR, TRUST, SEED-OPS and the register; differences from CM's citations (FU-CM-36) | Partial | `reconciliation/latest_versions.md`: 22 documents compared with the register (`as_of` 12 Oct 2026) and the folder; every CM citation except BUD, AWD (approved v0.5) and LAW/OVS is older than the register. **Bodies of the newer versions were not read** except TRUST v0.6 §§1–4 and the headers of KT-STD v1.29, AUTH v1.15 and AWD v0.6; each is read in the phase that depends on it. FU-CM-36 |
| CM8-010 | Personas and registry check: which §13 people and AUTH entries exist; gap list; check that core and suppliers install without procurement (D12) | Partial | `reconciliation/personas_and_registry.md`: all 12 §13 people exist as enabled users on the test site; Peter Mugo holds no responsibility; none of CM's 8 responsibilities is in the 18-entry registry. Static scan: `kentender_suppliers` 0 and `kentender_core` 0 (outside `seeds/`) imports of procurement, budget or strategy. **The check that core and suppliers install without procurement is deferred to CM8-107** |
| CM8-011 | `cmKit` extractor, `departures/contracts.js`, vitest project `contracts` in `ui-structure-gate` | Done | `cmKit`, `cmBoardIds`, `cmScope`, `cmSkeleton`, `cmDialogSkeleton` in `tests/ui/fidelity/board.js`; `tests/ui/fidelity/departures/contracts.js`; vitest project `contracts` (also in `make ui-structure-gate`; `design-fidelity` excludes `tests/ui/fidelity/contracts/**`). `npx vitest run --project contracts` 5/5 in 3.6 s; red proof: renaming one inventory id made the stale-inventory test fail, restored → 5/5 |
| CM-G00 | Gate: inventory rows each in one slice and one surface; every command and control mapped; provenance gate result recorded; fidelity project runs | Done | 157 inventory rows, each in one slice and one surface (checked by `cm-boards.spec.js`); every control mapped (script exits non-zero otherwise); `kentender_core.tests.test_artboard_provenance_gate` 3/3 via the site console (`bench run-tests` is blocked on the test site, FU-CM-43); `npx vitest run --project contracts` 5/5. Not run: `make ui-structure-gate` as a whole |

### Phase 1 — App scaffold and independence site

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-101 | `kentender_contracts` created; `required_apps = ["erpnext", "kentender_core"]`; module registered; Makefile install order; AGENTS.md and CLAUDE.md map lines | Planned | |
| CM8-102 | Empty `contract_management/` and `inspection_acceptance/` removed from `kentender_procurement` (FU-CM-35) | Planned | |
| CM8-103 | Spike records (`Contract Case`, `Contract Operation Intent`, `Contract Command Journal`, `Contract Test Environment Controls`) with the flags guard and deny permissions | Planned | |
| CM8-104 | New-module procedure on the test site (migrate, clear cache, `app_name` check, migrate); Page.module collision check prepared | Planned | |
| CM8-105 | Makefile targets (`cm-*`, `ui-cm-*`, `seed-cm-*`) in `.PHONY` | Planned | |
| CM8-106 | `test_cm_import_boundary` (static scan of `kentender_contracts`) | Planned | |
| CM8-107 | `kentender-cm-only.local` created and migrated; `make cm-independence-gate` wired (FU-CM-38) | Planned | |
| CM-G01 | Gate: installs on the test site and the independence site; migrate twice clean; import-boundary test green | Planned | |

### Phase 2 — Feasibility spike (initial timebox 2–3 days; OD-B)

Each row ends in one of: Verified / Needs configuration / Needs integration code / Needs a reviewed requirements change / Blocked. Evidence in `evidence/v0_8/spike/`.

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-201 | S0 test world: Company, accounts, fiscal year, taxes, warehouses, UOM, fixed-asset item and category, stock item, supplier, users and roles | Planned | |
| CM8-202 | S1 agreement → native Purchase Order, once; replay returns the same document | Planned | |
| CM8-203 | S2 ten units with serials; eight accepted, two rejected outside the receipt; arrival creates no receipt; inspection split by accepted subset; no global weakening | Planned | |
| CM8-204 | S3 serialised fixed assets through native receipt-to-asset, no duplicate valuation or Stock Entry; stock branch for contrast | Planned | |
| CM8-205 | S4 Purchase Invoice for accepted quantity only; duplicate check; concurrent claims; early liability then credit | Planned | |
| CM8-206 | S5 payment maker/approver through the native transition by a controlled server operation; own-entry refused; bypasses: direct Payment Entry, Journal Entry, Payment Reconciliation, API, import, background job; changed amount or beneficiary invalidates approval | Planned | |
| CM8-207 | S6 core signing facade; two parties on one immutable package digest; changed version ends the request; uncertain outcome keeps the attempt; capacity and witness evidence carried | Planned | |
| CM8-208 | S7 fail after native success before link; replay; timeout; funding convert replay; cancel a posted receipt; return and credit after payment; no duplicate signature, transaction or funding effect | Planned | |
| CM8-209 | S8 installed STD-TPL release vs §19.4; Form No. 4 extraction reproduced if the source file can be obtained; byte-determinism of the generated package | Planned | |
| CM8-210 | S9 independence site installs; supplier seam and Award adapter absent without error | Planned | |
| CM8-211 | Dated "Spike findings" section in the plan; follow-ups for every requirements-change or blocked result | Planned | |
| CM-G02 | Gate: every S-item labelled with evidence; failures classified; no workflow screen started before this row is Done | Planned | |

### Phase 3 — Package A: foundations, reversal and recovery

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-301 | `records.py`, `errors.py` (17 codes), `clock.py`, `people.py`, command journal | Planned | |
| CM8-302 | Operation-intent model and states; transaction links unique on the owner operation | Planned | |
| CM8-303 | `holds.py` (intersection of independent holds; scope, owner, clearing evidence) | Planned | |
| CM8-304 | `reconciliation/recovery_matrix.md` + table-driven test over the eight §5.17 rows and nine §5.18 rows; termination and closure boundaries modelled | Planned | |
| CM8-305 | Core signing facade `kentender_core/services/signing.py`; Proceedings delegating wrapper; targeted Proceedings signing rerun; CM simulation provider (FU-CM-30) | Planned | |
| CM8-306 | Native adapter (`native/`) productionised from the spike | Planned | |
| CM8-307 | Bypass guards on every native payment-capable path | Planned | |
| CM8-308 | Finance and stock configuration readiness check naming missing mapping and owner | Planned | |
| CM8-309 | Rule register: CM-R-01…18 as code, profile states, LQ hold keys, synthetic profile under the flag | Planned | |
| CM8-310 | AUTH registry entries, appointment and mandate subject bindings, `segregation.py` | Planned | |
| CM8-311 | Read-DTO base and audience resolver | Planned | |
| CM8-312 | `next_steps.py` and `tasks.py` skeletons; §6.3 ordering and deduplication | Planned | |
| CM8-313 | Budget `close_commitment` + Closed-amount position semantics + the seven owner tests; BUD tracker addendum (FU-CM-04) | Planned | |
| CM8-314 | Synthetic sources and `ContractCase` test base | Planned | |
| CM8-315 | Page `contracts` shell, Workspace, sidebar item, D-ERR and D-DENIED, Page.module collision check | Planned | |
| CM-G03 | Gate: schema, errors, holds, recovery-matrix, rules, segregation tests green; Budget owner tests green; signing facade and Proceedings rerun green; `cm-native-gate` replays S5/S7 at L2; `/app/contracts` shell from the sidebar | Planned | |

### Phase 4 — The ordinary thread (walking skeleton)

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-401 | Package received through the receiver hook (synthetic source provider on the D20 interface, L1) → Prepare contract (D01, D02) | Planned | |
| CM8-402 | CM generates the agreement and freezes the package from the supplied sources; certificate previews (CM-AC-65 partial) | Planned | |
| CM8-403 | Supplier then entity signature on one version → Active + native order (D03) | Planned | |
| CM8-404 | Appointment and declarations, minimal (D23, D24) | Planned | |
| CM8-405 | Arrival and custody (D04); inspection (D05); technical certificate (D19) | Planned | |
| CM8-406 | Acceptance report and signatures (D06, D07); accepted-subset receipt and asset | Planned | |
| CM8-407 | Supplier invoice, matching, certification (D18, D08) | Planned | |
| CM8-408 | Finance invoice, payment preparation, approval, settlement (D33, D09-F, D17, D09) | Planned | |
| CM8-409 | Completion certificate and close-out (D22, D11); Obligations presentation thin (D10/D40) | Planned | |
| CM8-410 | `cm-ordinary-thread.spec.ts` and live check from the menu, one session per person | Planned | |
| CM8-411 | Dev-site install announced and done (FU-CM-37) | Planned | |
| CM-G04 | Gate: the thread passes with real ERPNext and the real core facade (L2), the source handoff at L1 stated as such; rendered outputs and conformance recorded; live check with literal strings | Planned | |

### Phase 5 — Package B: formation and both entry routes

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-501 | `ReceiveAwardPackage` / `ReceiveAwardUpdate`; replay, ordering, no overwrite of a signed version | Planned | |
| CM8-502 | `ReceiveAwardPublicationEvent` / `RecordContractAwardPublication`; events before package, no-award, corrections, original trigger time | Planned | |
| CM8-503 | Preparation, particulars, signing-window and restriction rechecks at every commit | Planned | |
| CM8-504 | Security record, verification, rejection, replacement (D25) | Planned | |
| CM8-505 | Outside signature (D26); refusal, expiry, Did not proceed | Planned | |
| CM8-506 | Uncertain signing recovery; PO and funding failure recovery without fresh signatures | Planned | |
| CM8-507 | Funding revalidation and conversion; source allocations preserved; shared reservation | Planned | |
| CM8-508 | Existing-contract route: register, revise, opening position, start management; unique key; reconciliation | Planned | |
| CM8-509 | Rules CM-R-01–04, 08, 17, 18; LQ-03 and LQ-05 holds | Planned | |
| CM8-510 | Award-receiver precedence guard (FU-CM-33); optional-adapter disablement test | Planned | |
| CM8-511 | Boards: D01 variants, D02 (H, S, V), D03 (A, W), D12 (G), D21 (H), D25 (R, J), D26 (E, H) | Planned | |
| CM8-512 | `cm-formation.spec.ts`, `cm-existing-contract.spec.ts` + live check | Planned | |
| CM8-513 | Verify the current Award/source handoff against CM §19.4 on the canonical package: re-read `_content`, the Tenders issued-instance records through their published surface, the template release and the accepted-tender record; update `package_gap.md` with results | Planned | |
| CM8-514 | Core seam `kentender_core/services/contract_source_contract.py` (`describe`, `fetch`, `verify`; hook `kt_contract_source_provider`) and the versioned `ContractSourceHandoff` structure (category, owner, reference, version, digest, media type, size, locator, basis) | Planned | |
| CM8-515 | Owner-interface change: Tenders and the template release — issued instance, release, addenda, requirements and technical schedules, GCC/SCC with clause ids (payment, advance, security, remedies, change terms), Form No. 4 source with anchors; additive seam, tracker addendum | Planned | |
| CM8-516 | Owner-interface change: Bid Submission / Evaluation — accepted tender and clarifications; additive seam, tracker addendum | Planned | |
| CM8-517 | Owner-interface change: Award — notification identity and digest, signing-window result with counting basis, award package carrying the handoff references and funding lineage (via Budget's existing reader); additive, AWD tracker addendum | Planned | |
| CM8-518 | Entity particulars read once from site configuration (no retyping); supplier identity through the existing supplier-account seam | Planned | |
| CM8-519 | CM generates the agreement from the issued Form No. 4 and freezes the complete incorporated package (eight categories plus addenda), preserving source versions and hashes; coverage result before **Send for signature** (CM-R-04) | Planned | |
| CM8-520 | `test_cm_source_availability`: every §19.4 source available and verified for the canonical TND-MOH-2027-002 package through the real providers; an absent or unverifiable source blocks formation acceptance | Planned | |
| CM8-521 | Documentation: proposed successors under the document-change protocol for each owner document the handoff touches (AWD, TPR, STD-TPL; BDS, BUD, CFG as touched), version numbers from the register, owner approval left open (FU-CM-05, 06, 07) | Planned | |
| CM-G05 | Gate: L1 services; `cm-seams-gate` on real Award, real owner source providers, Budget and native order at L2; **every required source available and verified for the canonical package (CM8-520), or formation is not accepted**; the Phase 4 thread re-run against the real providers; `cm-independence-gate` green | Planned | |

### Phase 6 — Package C: delivery, inspection, acceptance, native stock and assets

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-601 | Appointment, declaration, conflict, replacement; receiver separation (D23, D24 variants) | Planned | |
| CM8-602 | Arrival and custody; returns before acceptance; replacement linked to original entitlement; excess, premature, ambiguous | Planned | |
| CM8-603 | Inspection from frozen criteria; Needs review; coverage and sampling | Planned | |
| CM8-604 | Technical certificate; acceptance report; every required current signer; dissent; correction and successor; authority-to-accept check | Planned | |
| CM8-605 | `PostAcceptedReceipt` via the intent model; stock and asset reconcile to Finance; related services without stock (D31) | Planned | |
| CM8-606 | Boards: D04, D05 (M), D06, D07 (P), D19, D23, D24 (C, S, X), D31 (A) | Planned | |
| CM8-607 | `cm-delivery-acceptance.spec.ts` + live check | Planned | |
| CM-G06 | Gate: L1 services; native stock and asset reconciliation at L2 | Planned | |

### Phase 7 — Package D: invoices, certification, Finance, advances, settlement

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-701 | Supplier claim once; matching; duplicate hold; correction-first policy; entitlement locked and consumed once | Planned | |
| CM8-702 | Certification with the acceptance-signer exclusion | Planned | |
| CM8-703 | Finance maker and approver editors over the native adapter; return; invalidation on changed amount or beneficiary | Planned | |
| CM8-704 | Settlement recording with independent evidence; instalments; reversal; credit and write-off kept out of Cash paid | Planned | |
| CM8-705 | Advances (D29) | Planned | |
| CM8-706 | Boards: D08 (C, L), D18 (C, R), D33 (A, U, W), D09 (AUD, F, T), D17 (H, S), D28 (C, F, V), D29 (H, R) | Planned | |
| CM8-707 | `cm-invoice-finance.spec.ts`, `cm-payment-settlement.spec.ts` + live check | Planned | |
| CM-G07 | Gate: L1 services; `cm-native-gate` bypass matrix and concurrency at L2; no routine step leaves KenTender | Planned | |

### Phase 8 — Package E: changes, delay, warranty, security, reporting, termination

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-801 | Issues and correspondence (D13) | Planned | |
| CM8-802 | Change request → review → AO decision → amendment → activation (D14, D27, D34 incl. **Change requires legal review**) | Planned | |
| CM8-803 | Delay adjustment (D36); paid-unit warranty replacement (D35); remedy verification | Planned | |
| CM8-804 | Security actions and claims (D16, D37) | Planned | |
| CM8-805 | Termination request, decision, notice, effective consequence (D20) | Planned | |
| CM8-806 | Compliance obligations and period reports: monthly, quarterly, publication, payment follow-up, termination record (D15) | Planned | |
| CM8-807 | Funding adjustments for variation and termination | Planned | |
| CM8-808 | Boards: D13 (C, S), D14 (P), D15 (L), D16 (P, W), D20 (P, T), D27 (A, R), D34 (A, H, L, P, R, X), D35 (C, H, V), D36 (A, E, H, S), D37 (A, P, X), D10/D40 (D, S) | Planned | |
| CM8-809 | `cm-change.spec.ts`, `cm-warranty-security.spec.ts`, `cm-termination.spec.ts`, `cm-reports.spec.ts` + live check | Planned | |
| CM-G08 | Gate: L1 services; real Budget adjustments and real native credit, return and cancel at L2 | Planned | |

### Phase 9 — Package F: completion, close-out, financial finalisation

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-901 | Final acceptance; completion certificate; close-out review with surviving obligations | Planned | |
| CM8-902 | Close-out correction and reopening (D38) | Planned | |
| CM8-903 | Termination settlement (D39) | Planned | |
| CM8-904 | `close_commitment` integration; **Funding finalisation pending** until acknowledged | Planned | |
| CM8-905 | Security return clock from AO final acceptance (CM-R-09) | Planned | |
| CM8-906 | Boards: D11 (B, C, T), D22 (P), D32 (H), D38 (P, R, T), D39 (C, H, P) | Planned | |
| CM8-907 | `cm-closeout.spec.ts` + live check | Planned | |
| CM-G09 | Gate: L1 services; real Budget closure and real native reconciliation at L2 | Planned | |

### Phase 10 — Access, dead ends, reversal sweep, retries

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-1001 | Per-audience DTO filters for every §6.2 reader; supplier projections; technical read without mutation; `test_cm_leakage` | Planned | |
| CM8-1002 | `test_cm_dead_end` (state × hold × actor through `next_step.problems`) | Planned | |
| CM8-1003 | §5.17 failures alone and in combination; §5.18 corrections at each boundary; `test_cm_idempotency` | Planned | |
| CM8-1004 | Adversarial authority scenarios (CM-AC-20) | Planned | |
| CM-G10 | Gate: `make cm-leakage-gate` and `make cm-dead-end-gate` green | Planned | |

### Phase 11 — Canonical seed stage and demo profiles

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-1101 | Stage `contracts` after `award` on the canonical package; isolated branches; idempotent second run | Planned | |
| CM8-1102 | Demo profiles (`make seed-cm-profile PROFILE=`), one per main stage | Planned | |
| CM8-1103 | `cm-demo-walk.spec.ts` from the sidebar, My Work and the bell | Planned | |
| CM-G11 | Gate: `seed-canonical THROUGH=contracts` and `seed-canonical-validate` green; second run idempotent; demo walk green | Planned | |

### Phase 12 — Release evidence and whole-chain acceptance

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-1201 | `ui-cm-fidelity-gate` over all boards (compared or not compared with a reason) | Planned | |
| CM8-1202 | The eight whole-chain scenarios of §14.4 at L2 | Planned | |
| CM8-1203 | AC map closure with proof levels | Planned | |
| CM8-1204 | Persona browser pass as real users; §17.12 usability acceptance (ordinary and existing-contract journeys without a native-form redirect) | Planned | |
| CM8-1205 | `RUNBOOKS.md` | Planned | |
| CM8-1206 | One cross-module regression run (Award, Budget, Proceedings signing, supplier provider, procurement UI smoke) | Planned | |
| CM-G12 | Gate: `ui-cm-release-evidence-gate` | Planned | |

### Phase 13 — Owner-gated

| ID | Item | Status | Evidence |
|---|---|---|---|
| CM8-1301 | Owner approval of the proposed successor documents and the remaining amendments FU-CM-01…13 (the source-handoff amendments FU-CM-05, 06, 07 are written in Phase 5, CM8-521; only approval is owner-gated) | Blocked — owner | |
| CM8-1302 | LQ-01…06 decisions (FU-CM-14…19) | Blocked — owner | |
| CM8-1303 | CM-LEGAL-01 deployment clearance; verified production profile (FU-CM-20) | Blocked — owner | |
| CM8-1304 | Installed-site proof: CM-TPL-01, CM-PROOF-01/02, CM-FUND-01 (FU-CM-21, 22, 23) | Blocked — owner | |
| CM8-1305 | Finance confirmations A1–A3 (FU-CM-24, 25, 26) | Blocked — owner | |
| CM8-1306 | Production Trust provider, execution and witnessing method, real channels, official actions (FU-CM-18, 27, 28) | Blocked — owner | |
| CM8-1307 | Security review and production enablement | Blocked — owner | |

## Acceptance map (CM-AC-01…71)

`Phase` is where the row is first built; `Proof` is what closes it. Every row is `Planned`. A row needing a native, Award, Budget or signing effect closes at L2; an L3 part is split into a Phase 13 row when the row is closed.

| ID | Requirement (short) | Phase | Proof | Status |
|---|---|---|---|---|
| CM-AC-01 | Replayed Award package: one case and task; earlier publication event survives; no-award creates no publication duty | 5 | L2 real Award | Planned |
| CM-AC-02 | Later restriction blocks only affected positive actions; arrival and evidence stay recordable | 5, 10 | L1 + L2 | Planned |
| CM-AC-03 | Exact source and terms persist; Item or template edits cannot change agreement or criteria | 5 | L2 real source providers | Planned |
| CM-AC-04 | Both parties sign the same version; changed content or expired authority cannot complete the old request; unknown outcome reconciles | 4, 5 | L2 facade | Planned |
| CM-AC-05 | Signed agreement with order failure: true partial state, recovers once, no fresh signatures | 5 | L2 native | Planned |
| CM-AC-06 | Arrival creates no usable stock; excess and premature goods are attributable exceptions | 6 | L2 native | Planned |
| CM-AC-07 | Empty, unreadable or unavailable observations give Needs review | 6 | L1 | Planned |
| CM-AC-08 | Serial and unit coverage, sampling authority, partial quantities reconcile; no duplicate acceptance | 6 | L1 + L2 | Planned |
| CM-AC-09 | Report signatures bind exact conclusions; correction keeps prior proof; all required signatures precede posting | 6 | L2 facade | Planned |
| CM-AC-10 | Mixed accepted and rejected goods, segregated custody, returns; stock and asset reconcile to Finance | 6 | L2 native | Planned |
| CM-AC-11 | Partial invoice and replacement claims consume entitlement once; no over-certify or overpay | 7 | L2 native | Planned |
| CM-AC-12 | Price, tax and quantity differences show reason and holder; original receipt time survives correction | 7 | L1 + L2 | Planned |
| CM-AC-13 | Certification, liability, payment entry and settlement stay distinct; credit not shown as cash | 7 | L2 native | Planned |
| CM-AC-14 | Advances follow their own guarantee and recovery route | 7 | L2 native | Planned |
| CM-AC-15 | Effective changes preserve prior terms; pending requests alter none; termination leaves settlement visible | 8 | L2 | Planned |
| CM-AC-16 | Security and warranty expiry release nothing; close-out respects the verified completion rule | 8, 9 | L1 + L2 | Planned |
| CM-AC-17 | Direct ERPNext, API, import and background routes enforce the same authority, quantity and source controls | 2, 3, 7, 10 | L2 native | Planned |
| CM-AC-18 | Native timeout, cancellation, reversal, changed downstream records reconcile without duplicate ledger effects | 3, 6, 7 | L2 native | Planned |
| CM-AC-19 | Every §5.10 and §10.3 condition shows the correct holder, fix or wait; no dead end | 10 | L1 | Planned |
| CM-AC-20 | Cross-supplier, expired appointment, supplier self-acceptance, Finance self-approval, maker confirming settlement, acceptance signer certifying, technical business action all fail without side effects | 10 | L2 | Planned |
| CM-AC-21 | Canonical and isolated fixtures separate, rerunnable, no live external side effects | 11 | L2 | Planned |
| CM-AC-22 | Publication and reporting due dates preserve trigger times; correction and failed dispatch never complete the duty | 8 | L1 + L2 | Planned |
| CM-AC-23 | Contract, stock, asset, payable, cash and credit totals reconcile across partial delivery, replacement, reversal | 7, 12 | L2 native | Planned |
| CM-AC-24 | Requirements approval, feasibility, package acceptance and production release kept distinct; source review is not installed verification | 12, 13 | Document + L3 | Planned |
| CM-AC-25 | Install without tendering apps; register, receive, invoice, close out; no absent-DocType errors | 1, 5 | L2 independence site | Planned |
| CM-AC-26 | Import 4 accepted, 2 in custody, KES 400,000 invoiced, 300,000 cash, 100,000 outstanding; import posts nothing; no double claim | 5 | L2 native links | Planned |
| CM-AC-27 | Repeat registration, changed source file, later KenTender package: one live case, reconciliation on conflict | 5 | L1 + L2 | Planned |
| CM-AC-28 | Missing signatures, unreadable schedule, unsupported product, unknown balance or unconfirmed action owner prevent activation with a named issue | 5 | L1 | Planned |
| CM-AC-29 | Legitimate surviving warranty or payment stays assigned after close-out; unresolved defect blocks it; timer never records release | 9 | L1 + L2 | Planned |
| CM-AC-30 | An invalidated Regulations-only deadline cannot appear as verified law | 3 | L1 | Planned |
| CM-AC-31 | Changed beneficiary, Journal Entry settlement, direct reconciliation cannot bypass hold or separation; credits never inflate Cash paid | 3, 7 | L2 native | Planned |
| CM-AC-32 | Disabling optional BDS, PRC or Award adapters leaves CM functional | 5, 10 | L2 independence site | Planned |
| CM-AC-33 | Shared reservation funds two commitments; forming one cannot release the other | 5 | L2 real Budget | Planned |
| CM-AC-34 | Signing succeeds but funding or order fails: proof retained, spending held, original intent reconciled once | 5 | L2 | Planned |
| CM-AC-35 | Variation and termination adjustments account for supported obligations; missing closure never writes state directly | 8, 9 | L2 real Budget | Planned |
| CM-AC-36 | Each rule has classification, parameters, calendar, evidence; unverified rules block affected actions only | 3 | L1 | Planned |
| CM-AC-37 | Period reports use exact cutoff and versions; failed reads give Incomplete | 8 | L1 + L2 | Planned |
| CM-AC-38 | Appointment, declaration, conflict, replacement, receiver separation, report reconstitution preserve attribution | 6 | L2 facade | Planned |
| CM-AC-39 | Payments of KES 500,000 and 300,000 settle one 800,000 entitlement once; concurrent excess refused; reversal reopens 300,000 | 7 | L2 native | Planned |
| CM-AC-40 | Source-signed imports keep actual effective dates and versions; outside copies not mixed or labelled Trust proof | 5 | L1 | Planned |
| CM-AC-41 | Advance KES 100,000, recoveries 80,000 and 20,000, cash 100,000 + 720,000 + 180,000 = 1,000,000 | 7 | L2 native | Planned |
| CM-AC-42 | Related-service acceptance and invoice create no stock or asset; 1,000,000 + 50,000 reconcile | 6, 7 | L2 native | Planned |
| CM-AC-43 | Technical readers site-wide read without mutation; supplier powers exactly as CM grants, no bid authority inherited | 10 | L2 | Planned |
| CM-AC-44 | Every action and variant resolves to one command or read, fixture identity and next-step kind | 0, 12 | Document + L1 | Partial — Phase 0 map built (273 pairs, 3 gaps); closes at Phase 12 |
| CM-AC-45 | Supplier claim, Finance preparation, approval and settlement entirely in KenTender; no standard-form step | 7 | L2 browser | Planned |
| CM-AC-46 | Tax, account, dimension requirements and native errors surface in KenTender; unsupported configuration blocks with a named owner | 7 | L2 native | Planned |
| CM-AC-47 | Native change, reversal, stale projection, concurrent approval or uncertain posting update the view truthfully; retries create no duplicate | 7, 10 | L2 native | Planned |
| CM-AC-48 | Every §6.2 reader opens list, counts, tabs, focused record, evidence and API without task-dependent denial | 10 | L2 | Planned |
| CM-AC-49 | Arrival produces custody and inspection only, zero receipt drafts; effective acceptance makes one accepted-subset draft | 6 | L2 native | Planned |
| CM-AC-50 | Each §5.17 failure alone and in combination keeps true state, permitted work and visible incidents | 3, 10 | L2 | Planned |
| CM-AC-51 | D34: early upward-total change held pending LQ-02; synthetic mechanism tests for 10 → 11, 12-unit refusal, replay | 8 | L1 + L2 | Planned |
| CM-AC-52 | D08-L: original receipt 08:05 and correction 10:00 kept; liability 1,000,000 + credit 200,000 = 800,000 | 7 | L2 native | Planned |
| CM-AC-53 | D35 paid-unit return and replacement preserve entitlement; no new cash or payable | 8 | L2 native | Planned |
| CM-AC-54 | D36 five-day 5,000 and three-day 3,000 calculations preserve inputs; missing mapping holds payment | 8 | L1 + L2 | Planned |
| CM-AC-55 | D37 request and decision do not mark KES 40,000 recovered; expiry releases nothing | 8 | L2 | Planned |
| CM-AC-56 | D38 preserves closure 1 and reopening 1; no automatic rollback; termination cannot become Active | 9 | L1 + L2 | Planned |
| CM-AC-57 | D39 settlement of KES 800,000 keeps Terminated, separate completion instant, true Budget pending | 9 | L2 real Budget | Planned |
| CM-AC-58 | Budget closure retains 1,000,000 charge; approved decrease to 800,000 adjusts once; replay, stale, race, closed FY | 3, 9 | L2 real Budget | Planned |
| CM-AC-59 | Multiple tasks obey §6.3 ordering, discoverable and deduplicated; surviving tasks stay in My Work | 3, 10 | L1 | Planned |
| CM-AC-60 | §5.18 corrections at each boundary keep history, invalidate future support, hold only affected scope | 3, 10 | L2 native | Planned |
| CM-AC-61 | Journeys stay within list, five-tab case and contextual tasks; no new menu destination or per-persona route | 4, 12 | L2 browser | Planned |
| CM-AC-62 | Every state names task or obstacle, quantity or amount and holder on first view; neutral reader has no personal block | 10 | L1 + browser | Planned |
| CM-AC-63 | Facts entered once and reused; no acknowledgement of successful checks; posting failure triggers no fresh signatures or Desk redirect | 7, 12 | L2 browser | Planned |
| CM-AC-64 | Each state resolvable from its card plus the shared shell; build agrees with D05, evidence order, Finance fields, D10/D40 | 12 | Fidelity gate | Planned |
| CM-AC-65 | Normal agreement resolves eight categories plus addenda; preview, download and both proofs bind one manifest and digests | 4, 5 | L2 render + facade + real source providers (CM8-520) | Planned |
| CM-AC-66 | Each Form No. 4 binding against its exact supported source; older release keeps its mapping; unsupported form gives a named issue | 5 | L2 render | Planned |
| CM-AC-67 | Eight accepted, two rejected: technical, committee and invoice records with non-overlapping coverage and correct recipients | 6, 7 | L2 | Planned |
| CM-AC-68 | Monthly HOP→AO and quarterly AO→PPRA reports with period, omissions and actual submission evidence | 8 | L1 + L2 | Planned |
| CM-AC-69 | Security-return clock starts only on evidenced AO final acceptance; low-value no-security case not signable without a lawful exemption; D34 held | 8, 9 | L1 + L2 | Planned |
| CM-AC-70 | Each certificate has the §19.5 assertion, scope, exceptions, issuer, recipient, evidence and proof; delivery failure stays pending | 6, 9 | L2 render | Planned |
| CM-AC-71 | Legal response and execution method bind affected actions only; a legal hold cannot be edited into a pass | 3, 10 | L1 | Planned |

## Follow-up map

| Follow-up | Closes with |
|---|---|
| FU-CM-01…04, 08…13 (owner documents) | CM8-1301 (FU-CM-04 built in CM8-313) |
| FU-CM-05, 06, 07 (AWD, TPR, STD-TPL) | CM8-521 written in Phase 5; approval CM8-1301 |
| FU-CM-14…19 (LQ-01…06) | CM8-1302 |
| FU-CM-20 | CM8-1303 |
| FU-CM-21, 22, 23 | CM8-1304 |
| FU-CM-24, 25, 26 | CM8-1305 |
| FU-CM-18, 27, 28 | CM8-1306 |
| FU-CM-29 | CM8-009, CM8-1301 |
| FU-CM-30 | CM8-305 |
| FU-CM-31 | owner revision of CM §10 / §17.12 |
| FU-CM-32 | CM8-008 (comparison built); closes with CM8-513…520 |
| FU-CM-33 | CM8-510 |
| FU-CM-34 | owner commit |
| FU-CM-35 | CM8-102 |
| FU-CM-36 | CM8-009 |
| FU-CM-37 | CM8-411 |
| FU-CM-38 | CM8-107 |
| FU-CM-39 | each `cm-native-gate` run |
| FU-CM-40 | Decided 14 Oct 2026 (OD-E): built within Package B |
| FU-CM-41 | owner confirms identities (before Phase 11) |
| FU-CM-42 | owner / designer (before Phase 5 and Phase 9 boards) |
| FU-CM-43 | before Phase 1's first Python test |
| FU-CM-44 | Planning owner |
| FU-CM-45 | Phase 4 |
| FU-CM-46 | KT-STD fixture owner |

## Build findings

Findings are recorded here as dated rows; the phase text of the plan is not rewritten.

| # | Date | Finding | Effect |
|---|---|---|---|
| B1 | 14 Oct 2026 | **Board count corrected: 157, not 122.** The earlier figure came from a text search for `id: 'D…'` and missed ids written with a label (`D17 · Posted`) and the dialog boards. `cmKit` now runs the design's own code and the design page's header agrees (43 designs, 157 artboards). | Plan header, Phase 0 gate, Phase 12 and the tracker header corrected in place; slice sizes in `artboard_inventory.md` (slice 8 is the largest at 52). |
| B2 | 14 Oct 2026 | **Command count: 83 named commands and reads in §7**, not "roughly 65". | Plan context corrected. |
| B3 | 14 Oct 2026 | **`bench run-tests` fails on `kentender-test.local` before any test runs.** Frappe's `compat_preload_test_records_upfront` creates ERPNext's `_Test Fiscal Year` records and one overlaps the KenTender fiscal year `2040-2041` already on the site (`NameError: Year start date or end date is overlapping`). `--skip-before-tests` does not help. It does not depend on CM; the same failure stops any module run through the runner. Documented remedy: `make purge-erpnext-test-fixtures` or `make test-site-rebuild` (about 9 minutes; also overwrites anything else on the test site, and a VS Code Playwright test-server was running during Phase 0). **Not done.** | FU-CM-43. Must be cleared before Phase 1's tests and the spike's S0 (which needs its own fiscal-year configuration). The provenance gate was run through the site console instead (3/3). |
| B4 | 14 Oct 2026 | **Award's frozen package carries descriptive sentences, not terms.** `contract_terms.delivery_and_warranty`, `reservation_treatment`, `performance_security` and `tender_security` are fixed strings; there is no issued release, addenda, price schedule lines, GCC/SCC, signing-window result or funding allocation. Release 1.5 has no contract destination for payment, advance, security, remedies or change terms. | Superseded by B8: the handoff is required Package B work (OD-E, D20); Phase 4 uses a synthetic provider on the same interface at L1; CM-G05 requires the real providers. |
| B5 | 14 Oct 2026 | **Pre-existing, not CM:** `npx vitest run --project design-fidelity` fails 1 of 51 (`covered.spec.js`: `procurement-planning.js` names `PublicationResultScreen#U13` in COVERED with no comparing spec). Identical with the CM changes stashed (1 failed of 50). | FU-CM-44. |
| B6 | 14 Oct 2026 | **Spec gaps found by the command map:** D32 and D39 draw **Return for correction** with no §7 command; nine required commands have no control on any board. | FU-CM-42. |
| B7 | 14 Oct 2026 | **Personas:** Peter Mugo has no responsibility; Josphat holds Budget's Finance Confirmation Officer (not a CM Finance role); Beatrice holds Budget Approver. | FU-CM-03 (fixtures) and FU-CM-46. |
| B8 | 14 Oct 2026 | **Owner correction of the Phase 0 handling of the Award package gap (OD-E).** The gap is a required integration dependency already identified in CM v0.8 §19.8, not a follow-up; Award supplies the authoritative source material and CM generates the agreement and assembles and freezes the package. My Phase 0 write-up (`package_gap.md` version 0.8-package-gap.1, plan C4 and findings item 2, FU-CM-32 / FU-CM-40) treated the eight-category package as something Award should carry and left the extension as an open owner decision. | `package_gap.md` rewritten (version 0.8-package-gap.2: 12 sources, who produces what); plan D20, OD-E, C4, Phases 4, 5, 13, findings item 2 and risks patched in place; Phase 5 rows CM8-513…521 and CM-G05 added; FU-CM-32 re-scoped, FU-CM-40 decided. |
