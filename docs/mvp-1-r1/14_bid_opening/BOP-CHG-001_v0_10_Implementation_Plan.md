# BOP-CHG-001 v0.10: Electronic Bid Opening (with PRC-CHG-001 v0.9 Proceedings), implementation plan

| Control | Value |
|---|---|
| Version | 0.10-plan.2 (0.10-plan.1, 29 Sep 2026, retained below) |
| Date | 29 September 2026 |
| Authority | `KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_10.md`: "**Approved design and development contract**", "Approved on: 29 September 2026 — Project Owner" (BOP v0.10 as approved; the rebase is recorded in its Revision row as "approval references reconciled on admission"). (0.10-plan.1 read: "**Proposed design and development contract**" (BOP v0.10 line 7). Built to under owner decision OD-A.) Approved predecessor: `KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_9.md`, "**Approved design and development contract**", "Approved on: 29 September 2026 — Project Owner" (BOP v0.9 lines 7 and 9). |
| Shared service authority | `../13_proceedings/KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_9.md`: "**Approved detailed contract**", approved 29 September 2026 (PRC v0.9 lines 7 and 9). |
| Sibling authorities (as cited by BOP v0.10 line 14 and BOP v0.10 §17; register state in C3) | TPR-CHG-001 v0.13 (approved per BOP v0.10; register lists v0.12); TPR-CHG-001 v0.14 (proposed; no file in the repo); BDS-CHG-001 v0.8 (approved); BDS-CHG-001 v0.9 (proposed; no file in the repo); G1-REG-001 v1.1; KT-STD-001 v1.10 (approved per BOP v0.9 and PRC v0.9; the file is named `_v1_10_proposed.md`); TRUST-ADR-001 v0.1 (approved 27 Sep 2026; supplied 29 Sep 2026 as `../00_common/KenTender_TRUST-ADR-001_Shared_Signing_and_Sealed_Custody_v0_1.md`) (0.10-plan.1 read: cited as approved; no file in the repo); LAW-REG-001 v1.2 and LAW-V-001 (open). |
| Design | `design/Bid Opening Artboards v0.9.2.dc.html`. It has 52 registry entries: 50 drawn boards and 2 reviewer notes (`n00` Read me, `f00` Flags). The boards are labelled "BOP-CHG-001 v0.10 (proposed) · PRC v0.9 · KT-STD-001 v1.9" and carry the `_ds/kentender-industry-…` Industry design system bundle. |
| Companions | `BOP-CHG-001_v0_10_IMPLEMENTATION_TRACKER.md`; `BOP-CHG-001_v0_10_FOLLOW_UPS.md`; `reconciliation/artboard_inventory.md`; `reconciliation/v0_9_to_v0_10_diff.md`. Later: `evidence/v0_10/` and `RUNBOOKS.md`. |
| Predecessor | None. This is the first Bid Opening plan. |
| Prepared | 29 September 2026 |
| Status | Phase 0 closed except the provenance gate; Phase 1 in progress. (0.10-plan.1 read: Planned. No code has been written.) |

## Context

**Why this module now.** Bid Submission (BDS-CHG-001 v0.8) is built and gated (its tracker records BDS-G00…G13). At the effective deadline it closes the tender box and writes one `Bid Opening Handoff` per Tender, with `consumer = "bid-opening"` and `delivery_status = "Pending"`. Nothing reads it. Bid Opening is the next step in the traceability chain (Tender → Bid → **Opening** → Evaluation). It also brings the first user of the shared Proceedings record (PRC-CHG-001).

**Current state (verified 29 September 2026 by reading the source):**
- **Bid Opening.** It is only a placeholder workspace, `kentender_procurement/kentender_procurement/kentender_procurement/workspace/bid_opening/bid_opening.json`, with the text "This lifecycle step is not implemented yet". There is no sidebar entry in `workspace_sidebar/procurement.json`, and no `BOP_` identifier anywhere in the code.
- **Proceedings.** No code exists. `procurement_planning/doctype/proceeding_coverage` is unrelated.
- **What Bid Submission gives Bid Opening:**
  - `bid_submission/services/close.py::close_bid_submission` writes `Bid Opening Handoff` (`BOH-<ref>`). It carries `payload_json` and a sha256 `handoff_digest`, and every `Tender Box Envelope` gets `box_state = "Handed to Bid Opening"`. The payload (`handoff_payload`) holds `tender`, `closed_box`, `envelopes[]` (every version, with `status` Submitted, Superseded or Withdrawn, and `predecessor_submission_version`), `changes[]`, `unresolved_attempts[]` and `physical_tender_security {intakes[], matches[]}`. It carries no price and no content.
  - BDS has no published read or acknowledge service for this record, and nothing ever sets `Delivered`.
- **Custody, trust and time.** They come through the `bid_submission/services/gateways.py` hooks (`kt_bds_custody_services`, `kt_bds_trust_services`, `kt_bds_time_services`). The only box is `bid_submission/test_services/tender_box.py::TestTenderBox`, which stores plain package bytes under `private/kt_test_tender_box/`. Its docstring says "There is no encryption here and none is claimed". `stored_package(correlation_id)` is test-only. **There is no decrypt, reveal, multi-person custody or attestation code anywhere.**
- **Package format.** The package is canonical JSON, `SCHEMA = "kt-bds-package/1"` (`bid_submission/services/package.py`). It carries `responses[]` (tender security under rule `RR-TENDER-SECURITY`), `evidence[]` with base64 files, and `price {currency, subtotal, tax, total, lines[]}`. **Nothing renders it to pages or counts pages.** `wkhtmltopdf` is installed at `/usr/local/bin/wkhtmltopdf`.
- **Tenders.** The doctype is `Tender`, with fields `submission_deadline` (effective, addenda-adjusted), `cancellation` and `submission_handoff`. `ConfirmTenderPublished` emits `TenderOpenForSubmission`, which BDS already consumes (`tenders/services/publication.py`). `cancel_tender` emits `TenderCancelled` with no consumer and no `Pending` status, so no outbox item reaches another module. The Desk page `tenders` owns `/app/tenders` and dispatches sub-segments inside `public/js/tenders/Tenders.vue` (`segments`, `sub`, `subId`).
- **Public pages.** The `/tenders` portal prefix belongs to BDS through `kt_portal_surfaces` (`bid_submission/portal.py::resolve`, `bid_portal.bundle.js`).
- **Shared runtime available:**
  - `kentender_core.desk_page` (`register`, `useRoute`, `createCommandRunner`, `createSequenceGuard`, `createScreenCache`);
  - `kentender_core.industry.mountPageRail` and `mountGuidance`;
  - `kentender_core/services/next_step.py` (`guard`, `blocker`, `holder`, `for_viewer`, `problems`, `journey`);
  - `kentender_core/services/my_work.py` (`kt_my_work_providers` hook);
  - `kentender_core/utils/instants.py`;
  - `kentender_core/services/audit_event_service.py`;
  - `kentender_core/services/notification_service.py`;
  - the BDS command envelope in `bid_submission/services/records.py` (`idempotent`, `check_version`, `atomic`, `emit`).
- **Personas.** Amina Hassan, Charles Mutiso, Brian Wafula, Beatrice Kamau and Naomi Chebet are in KT-STD-001 v1.10 §8.3 and the seeds. Beatrice's KT-STD-001 v1.10 §8.3 row reads "Beatrice Kamau | `beatrice.kamau@moh.example.test` | Budget Approver | Site-wide" (line 584). David Ouma exists as a BDS supplier user. **Jane Wanjiku does not exist anywhere.**
- **Baseline register** (`KenTender_Baseline_Register.yaml`, `as_of` 2026-09-26). It has no BOP, PRC or TRUST entry. Bid Opening appears only as future item `FW-001`, and IF-011 (BDS → Bid Opening) is "Future consumer boundary" / "Not started".

**Governing standard.** BOP v0.9 and PRC v0.9 name KT-STD-001 v1.10. BOP v0.10 names KT-STD-001 v1.9 (see C1). This plan follows KT-STD-001 v1.10 wherever the two differ, because v1.10 is the version the approved sibling contracts cite. The only v1.10 feature BOP depends on is the timed next-step kind (**Scheduled**).

**Done means:**
- Every BOP v0.10 §7 command and PRC v0.9 §7 command is built as a server service with idempotency, expected version, trusted time and audit.
- Every BOP v0.10 §7.1 binding row has its producer, consumer, failure and named test.
- All 50 drawn boards are ported class-for-class and pass the fidelity gate.
- The canonical Afya Tender can be opened end to end in a browser by its real personas, under the simulation flag, with the empty, not-held, paused and cancelled branches each proven on their own fixture.
- The acceptance map (BOP-A01–A21, PRC-A01–A13) is honestly marked. Production-only parts remain `Blocked — owner`.
- Real opening in production stays disabled.

## Owner decisions (this session, 29 September 2026)

| # | Decision |
|---|---|
| OD-A | **Build to BOP v0.10.** Owner answer, verbatim: "Build to v0.10 (Recommended)", choosing: "Treat v0.10's four changes as the build authority because the boards embody them. Log owner approval, and rebasing v0.10 onto approved v0.9, as a Phase 0 item that doesn't block backend work." |
| OD-B | **Proceedings location.** Owner answer, verbatim: "New module in procurement (Recommended)", choosing: "A 'proceedings' module in kentender_procurement, beside a new 'bid_opening' module. Its services are owner-independent and can be contract-tested against a simulated owner." |
| OD-C | **Where the stand-ins run.** Owner answer, verbatim: "Dev site, like Bid Submission (Recommended)", choosing: "Stand-ins run on kentender.midas.com only when the simulation flag is set, and the canonical Afya Tender can be opened end to end in the browser. Recorded as a departure from §13's isolation rule." |

## Key technical decisions (implementation authority unless the owner says otherwise)

| # | Decision |
|---|---|
| D1 | **Modules.** Add two new modules to `kentender_procurement`: `bid_opening/` (the owner) and `proceedings/` (the shared record, OD-B). Each has `doctype/`, `services/`, `api.py`, `tests/` and `test_services/`. Add both to `modules.txt`. Follow the new-module procedure: after the first migrate, clear the cache, check that each Module Def has `app_name = kentender_procurement`, then migrate again. `proceedings` never imports `bid_opening`; it knows its owner only as `(owner_type, owner_id)` plus a registered owner-adapter hook, `kt_prc_owner_adapters`. |
| D2 | **Doctypes, using the spec model names:**<br>• **PRC (PRC v0.9 §4):** `Proceeding`, `Proceeding Member` (roster snapshot, child), `Proceeding Attendance`, `Proceeding Event`, `Proceeding Minutes Version`, `Proceeding Minutes Target` (child), `Proceeding Attestation`, `Proceeding Supplement`, `Proceeding Command Journal`.<br>• **BOP (BOP v0.10 §4):** `Bid Opening Case`, `Opening Committee Appointment` (+ `Opening Committee Member` child, with successor history), `Opening Arrangement` (versioned public projection), `Opening Presence`, `Opening Custody Participation`, `Opening Entry` (register row), `Opening Register` (frozen version and digest), `Opening Exception`, `Opening Access Incident`, `Opening Decision Item` (AO), `Opening Register Request`, `Evaluation Handoff` (consumer `evaluation`, `Pending`, once-only key), `Opening Command Journal`, and the Single `Bid Opening Settings` (operating-profile values, D7).<br>• **All of these, following BDS D12:** no role permissions; `validate()` refuses unless a command flag is set; `on_trash` refuses unless the fixture-wipe flag is set; `has_permission` and `permission_query_conditions` deny. Reads go only through explicit services. |
| D3 | **Command envelope.** Mirror the BDS `records.py` pattern in each module (`idempotent(key, command, payload, fn)`, `check_version`, `atomic`, `emit`), so that a replay returns the original result and a conflicting replay or stale write has no partial effect. Next steps use `kentender_core/services/next_step.py`, including `next_step.kind = timed` for **Scheduled** (BOP v0.10 §5). Time comes from a per-module `clock.py` modelled on `bid_submission/services/clock.py`. Values are stored in site time; UTC is used only in cross-module payloads, through `kentender_core/utils/instants.py` (AGENTS.md §4.4). Audit goes through `log_audit_event`. PRC errors map to BOP copy as BOP v0.10 §7.1 "Product vocabulary" requires (`PRC_VERSION_CONFLICT` → `BOP_VERSION_CONFLICT`). |
| D4 | **BDS published seam** (additive; one addendum row in the BDS v0.8 tracker). New file `bid_submission/services/opening_gateway.py`:<br>• `closed_manifest(tender) -> {handoff_id, digest, payload}` verifies the digest.<br>• `acknowledge_handoff(handoff_id)` sets `Delivered`, once.<br>• `confirm_custody_participation(*, tender, member_users, manifest_digest)` requires at least two distinct appointed members including the independent member, for empty and nonempty manifests alike. It returns an opaque participation reference, and a changed manifest or roster makes that reference stale.<br>• `reveal_envelope(*, envelope_id, participation_ref) -> bytes` works only for a current (`Submitted`) envelope after close. In simulation it reads through `TestTenderBox.stored_package`; with no production adapter it reports unhealthy.<br>BOP never reads a BDS doctype directly. The physical-security facts come from the manifest's `physical_tender_security.matches`. |
| D5 | **Renderer gateway** (hook `kt_bop_renderer_services`). The default renderer turns a `kt-bds-package/1` package into a fixed, versioned HTML template, then into PDF bytes with wkhtmltopdf. It returns:<br>• the page count;<br>• the price-page and change-page locations, found by embedded markers;<br>• the source-derived tenderer name, submitted total and currency, and tender security given;<br>• the render digest.<br>The same renderer produces the opening-record pages and the register copy. Bytes are handled through `kentender_core/services/file_integrity` (the save_file/get_file corruption lesson). A failure raises `BOP_PACKAGE_UNREADABLE` and opens an `Opening Access Incident`. Page 1 is only an editable proposal for the designated page (BOP v0.10 §7 SelectOpeningTargets). |
| D6 | **Signing gateway** (hook `kt_bop_signing_services`). The simulation double records an individually attributable attestation bound to the target digest, as PRC v0.9 §13 describes. The label "Test attestation — not an electronic signature" appears only in verification scripts and evidence, never in product copy (BOP v0.10 §7.1 "No verification label or proxy action is a production screen"). With no production adapter, `BOP_ATTESTATION_MISSING` stays blocking. There is no checkbox signature (BOP v0.10 §16). |
| D7 | **Presence.** Socket.io is not served on this bench, so presence is an authenticated `JoinOpening` / `LeaveOpening` pair plus a polling heartbeat. The lapse timeout is an operating-profile input (BOP v0.10 §5: "This exact mechanism and timeout are operating-profile inputs"). It is held in `Bid Opening Settings`, defaulting to 60 seconds in simulation and unset in production, which blocks Begin. Every material command (BeginOpening, OpenNextTender, RecordReadout, ResumeOpening, FinishCeremony) rechecks the full active roster on the server. A lapse is recorded at the next material attempt, or by a scheduler sweep, whichever comes first. |
| D8 | **Tenders seams** (additive; addendum rows in the Tenders tracker):<br>• BOP consumes `TenderOpenForSubmission` as a second consumer, `bid-opening`, and runs `PrepareOpeningCase`.<br>• `cancel_tender` gains a `Pending` outbox row for consumer `bid-opening`, so that `ConsumeTenderCancellation` receives an authoritative event. Until that lands, BOP reads `open_period_read.get_tender_cancellation`.<br>• Under TPR-CHG-001 v0.13, cancellation after close is unavailable (BOP v0.10 §10.7). The cancelled-after-start branch (BOP-N18, PRC-N09, board `c12`) is therefore exercised only through a simulation-only owner event until TPR-CHG-001 v0.14 is approved (FU-BOP-06). |
| D9 | **Desk route (BOP v0.10 §9, change 4).** The `tenders` Page keeps `/app/tenders`. Bid Opening views are sub-paths of the Tender record: `/app/tenders/{tender}/opening`, `…/opening/record`, `…/opening/correct` and `…/opening/decision`. `Tenders.vue` delegates `sub === "opening"` to a BOP-owned root component, exposed by a new `bid_opening.bundle.js` that is added to the `bundles` list in `public/js/tenders_page.js`. This is one additive Tenders seam. BOP reads the route only through its own `useRouteState()` adapter over `kentender_core.desk_page.useRoute`. It uses the shared `mountPageRail` and `mountGuidance`, the Industry design system only, and never `kentender_core.cl_surface_registry.js` (AGENTS.md §6.1–6.5). Exact sub-path names are locked in Phase 8 and recorded in the tracker. |
| D10 | **Public route.** BDS owns the `/tenders` portal prefix. BOP adds the public opening region and `/tenders/{tender}/opening` through a published BDS portal seam: a registered section resolver called from `bid_submission/portal.py::resolve`. The live readout polls announced facts only; a fact appears after the recorder's confirmation, never at reveal (BOP v0.10 §10). The register request and download are offered only to a verified submitting-supplier user. |
| D11 | **Work items.** A new `bid_opening/services/my_work_provider.py::my_work_rows` is registered in `kt_my_work_providers`. It covers every Desk title in the BOP v0.10 §5 handoff table: AO appoint, publish, replacement, decide, paused decision and register-copy tasks; member Join and Review-and-sign tasks; recorder Prepare; and chair Start, shown as upcoming until close. **Opening access support** incidents go to the Technical Operator (Daniel Otieno, BDS plan D13; not in KT-STD-001 §8.3, see FU-BOP-08) through a Notification Log, never My Work (BOP v0.10 §5). Delivery can fail and be retried for the same incident without creating another (branch 6). A fault switch in the simulation-only controls drives that failure. |
| D12 | **Placeholder retirement.** Delete the `bid_opening` placeholder workspace. There is no Bid Opening sidebar entry, because BOP v0.10 §9 reaches every view from the Tender record. Check `workspace_sidebar/*.json` for dangling links before migrating (the reverse-sync gotcha), and migrate twice. |
| D13 | **Personas.**<br>• Amina Hassan: Accounting Officer.<br>• Charles Mutiso: chair and recorder, a fixture appointment only.<br>• Brian Wafula: member.<br>• Beatrice Kamau: independent member.<br>• Naomi Chebet: Auditor.<br>• David Ouma: existing BDS supplier user, verified submitting representative.<br>• Daniel Otieno: technical operator.<br>• Administrator.<br>**Jane Wanjiku** (public observer) is new: a Website User with no supplier link. Request that she be added to KT-STD-001 §8.3 (FU-BOP-08). Amina's office alone does not make her a committee member (PRC v0.9 §13). |
| D14 | **Seed and fixtures.**<br>• **Canonical stage:** add `bid_opening` to `canonical.STAGES` after `bid_submission`. Its steps run at the BOP v0.10 §10 main-path instants: appoint 10 Jun 2027 10:15 EAT; publish 10:20; members join 12 Jun 10:55–10:57; David 10:58; Jane 10:59; Start 11:00:12; readout confirmed 11:01:45; End 11:04:00; freeze 11:07; member reviews 11:08–11:10; completion 11:10:30.<br>• **Browser fixtures:** each Playwright spec builds its own fixture entity in test years ≥ 2100, including the `-034` (empty), `-035` (not held) and BOP v0.10 §13 `TND-TEST-BOP-001/002/003` shapes.<br>• **Cleanup:** every test module registers purge cleanup (the always-remove-test-data rule).<br>• **Canonical site:** the site is reseeded to canonical after Python runs (bench run-tests has no rollback). |

## Phases

**Loop for every phase:** red, then green, then refactor; run the module tests once; run the phase gate; update the tracker row with evidence. Phases 1–3 are horizontal. From Phase 4 each phase is vertical: service, then API, then (in Phase 8) screen and browser. Never run the Python suite while a Playwright process is active.

### Phase 0: Reconcile (documents only)
- `reconciliation/artboard_inventory.md`: the 50 drawn boards, each mapped to `Component#variant`, slice and status (Covered or Conditional). Extracted by script from the board registry (`const B = […]`, design file line 1225).
- `reconciliation/v0_9_to_v0_10_diff.md`: the four changes, and the approval-state reversions that block v0.10's approval as written (C1).
- Commit the design folder. Extend `make artboard-provenance-gate` to cover `14_bid_opening/design`.
- Log C1–C10 in the tracker and FU-BOP-01… in the follow-ups file.
- Owner items (these do not block Phase 1): rebase and approve v0.10; register entries for BOP, PRC, TRUST and KT-STD-001 v1.10; provide TRUST-ADR-001.
- **Gate BOP-G00:** inventory row count = 50; every board is in exactly one slice; provenance gate passes.

### Phase 1: Scaffolding
- Add the `bid_opening` and `proceedings` modules and every doctype in D2, with the flags guard, deny permissions and schema contract tests (`test_schema_contract.py` in each module).
- Retire the placeholder workspace (D12). Run `make validate-links`; migrate clean twice.
- **Gate BOP-G01.**

### Phase 2: PRC core (owner-independent)
- **Services** (`proceedings/services/`):
  - `lifecycle.py`: CreateProceeding, StartProceeding, EndProceeding, MarkNotHeld, CloseAbortedProceeding.
  - `attendance.py`: RecordAttendance, with pre-session flag and arrivals snapshot at Start.
  - `events.py`: AppendProceedingEvent, with a unique owner event ID, replay and conflict handling, and trusted time kept separate from reported speech time.
  - `minutes.py`: FreezeMinutes, SupersedeFrozenMinutes and digest.
  - `attestation.py`: AttestTarget, through the D6 gateway.
  - `finalize.py`: FinalizeProceeding, AppendSupplement.
  - `reads.py`: ReadProceeding, ExportProceeding.
  - `errors.py`: PRC v0.9 §8 codes.
- **Simulated owner:** `proceedings/test_services/owner.py` implements `kt_prc_owner_adapters` for tests only.
- **Tests:** one module per group, covering PRC-S01, S02 and N01–N12 by name.
- **Gate PRC-G02:** `make prc-services-gate`.
- **Closes:** PRC-A01, A05, A09, and the shared parts of A02 and A10–A13, all as shared-service evidence only (PRC v0.9 §15).

### Phase 3: Gateways and simulation
- The D4 BDS seam (`opening_gateway.py`) with tests, and one BDS tracker addendum row.
- The D5 renderer, with a determinism test: the same package gives the same page count and digest twice.
- The D6 signing double.
- The D7 `Bid Opening Settings` Single.
- The D11 incident transport with the failure switch.
- `bid_opening/services/availability.py::get_opening_availability()`. It checks, in order: `BOP_OPENING_PROFILE_UNAVAILABLE` (profile or production switch), `BOP_CREDENTIAL_UNAVAILABLE` (custody or credential health), then service health. `production_bid_opening_enabled` is read only here, from `frappe.conf`, defaulting to false.
- The simulation doubles load only under `kt_bds_simulation_environment` (OD-C).
- **Gate BOP-G03.**
- **Closes:** the gateway parts of BOP-S01T, N06 and N13.

### Phase 4: Pre-session owner services
- **Services:**
  - `case.py`: PrepareOpeningCase, as the `TenderOpenForSubmission` consumer (D8), creating the PRC Pending session.
  - `appointment.py`: AppointOpeningCommittee, requiring at least three members including an independent one, keeping successor history, with the published read `is_excluded_from_evaluation(tender, user)` (BOP-A17).
  - `arrangements.py`: PublishOpeningArrangements.
  - `presence.py`: JoinOpening, LeaveOpening and heartbeat, with PRC pre-session attendance.
  - `close_intake.py`: ReceiveClosedBox, with manifest reconciliation of current, withdrawn and superseded envelopes; drafts and late attempts are excluded.
  - `custody.py`: ConfirmOpeningCustody.
  - `not_held.py`: RecordOpeningNotHeld, and pre-Start ConsumeTenderCancellation.
  - `reads.py::get_opening`: next step per BOP v0.10 §5 and BOP v0.10 §8 guards.
  - `my_work_provider.py`.
- **Tests:** BOP-N01, N02, N10, N14 and N17; the pre-session handoff-table rows; a count-neutral test showing the pre-Start DTO, errors and step list are identical for an empty and a nonempty manifest.
- **Gate BOP-G04.**
- **Closes:** BOP-A01, A04 (intake part), A11 (pre-session rows), A13 (application part), A17 and A18 (Not held part).

### Phase 5: Ceremony
- **Services** (`ceremony.py`, `readout.py`, `interventions.py`, `exceptions.py`, `interruptions.py`, `incidents.py`, `cancellation.py`):
  - BeginOpening, calling PRC StartProceeding with the arrivals snapshot.
  - OpenNextTender: reveal through D4, render through D5, assign a number, count pages.
  - RecordReadout + SelectOpeningTargets, committed atomically, with a named speaker, trusted confirmation time and an optional attributed speech time.
  - RecordAttendance, RecordIntervention and RecordMemberAccount (member authorship only).
  - DisposeOpeningException: **Record comment for Evaluation**; identity, integrity and unreadable problems cannot be disposed of this way.
  - RecordInterruption, ResumeOpening and the paused-opening AO item.
  - Incidents for unreadable, mismatch, credential and profile-unavailable problems, with **Notify support** retry and **Retry opening**.
  - RecordZeroBidOutcome + FinishCeremony, committed atomically.
  - FinishCeremony, with the full-roster and inventory recheck.
  - CloseCancelledOpening, calling PRC CloseAbortedProceeding.
- **Tests:** BOP-N02A, N03, N04, N05, N06, N12, N15, N16 and N18; the v0.10 branch (6) timeline.
- **Gate BOP-G05.**
- **Closes:** BOP-A02, A04, A05 and A06 (application parts), A09 (simulation part), A14, A18 and A20; PRC-A10, A12 and A13 (integrated).

### Phase 6: Opening record and completion
- **Services** (`record.py`, `signing.py`, `completion.py`, `correction.py`, `register_copy.py`, `export.py`):
  - Generated opening-record draft, through D5.
  - FreezeOpeningMinutes, which fails if any page selection or owner event is missing.
  - SupersedeFrozenMinutes.
  - Per-member, per-roster-segment target enumeration.
  - AttestOpeningTarget.
  - Internal CompleteOpening: PRC FinalizeProceeding, then BOP completion, then a once-only `Evaluation Handoff` for a nonempty opening only. A failed finalization leaves BOP awaiting attestations.
  - The completed-record correction, limited to the four v0.10 kinds (Attendance note, Procedural note, Typographical error in a note, Observer name or organisation). Any other kind, or any change to bid facts, amounts or signed targets, is denied with "This correction cannot change a bid or replace the signed opening record."
  - RequestOpeningRegister and GetOpeningRegisterCopy, with digest and delivery audit, or the AO task path when self-service is not authorised.
  - Audit export.
- **Tests:** BOP-N07, N08, N09 (service part) and N11; PRC-N05 and N06 through the real owner.
- **Gate BOP-G06.**
- **Closes:** BOP-A07 and A08 (application parts), A10 and A19; PRC-A03, A04, A06 and A07 (integrated, simulation).

### Phase 7: API and disclosure
- `bid_opening/api.py` and `proceedings/api.py`: whitelisted endpoints with explicit arguments, never forwarding `**kwargs` into a keyword-only service (the transport-field trap).
- Per-actor DTO filters: chair, recorder, member, AO, HOPF or Procurement Officer outside the appointment, auditor, technical reader, submitting supplier, public observer. Cross-scope requests return protected Not found.
- A leakage gate that scans every pre-Start DTO, error and next-step payload for bid count or identity.
- A dead-end matrix over every state × actor through `next_step.problems`.
- Technical-read resolvers (`kt_technical_reference_resolvers`).
- **Gate BOP-G07:** `make bop-dead-end-gate` and `make bop-leakage-gate`.
- **Closes:** BOP-A11, A13, A15 and A21 (matrix part); PRC-A06.

### Phase 8: Desk UI (vertical slices)
- Tenders seam first (D9). Afterwards run the existing `ui-tenders-*` gates once to prove no regression.
- **Each slice:** API read, then screen ported class-for-class from its boards, then one Playwright spec with one fixture entity, then `ui-bop-<slice>-gate`. Evidence PNGs go to `evidence/v0_10/`.
- **Departures file:** `tests/ui/fidelity/departures/bid-opening.js` (LABELS, DEPARTURES, COVERED, CONDITIONAL), with an inventory-count test fixed at 50.

| Slice | Boards | Notes |
|---|---|---|
| 8.1 Prepare opening | a1, a2, a3, a4, a5 | AO appointment, independent-member block, publish how to attend |
| 8.2 Before Start | c1, c2, c2b, c2c, c2d, c3 | Timed **Scheduled**; member not joined; access not ready; v0.10 branch (6) |
| 8.3 Ceremony | c4, c5, c6, c7, c8, c8b, c13, c13b, c9 | One bid at a time; atomic readout and pages; member's own account |
| 8.4 Pauses and cancellation | c10, c10b, c11, c11b, c11c, c11e, c11d, c12 | c12 through the simulation-only TPR event (D8) |
| 8.5 No bids and not held | z1, n1, n2 | Separate `-034` and `-035` fixture entities; v0.10 **Your turn** kind on n2 |
| 8.6 Opening record and signing | r1, r2, r3, r4, r5, r6 | r3 Conditional (D6) |
| 8.7 Completed record | h1, h2, h4, h5, h3 | v0.10 four correction kinds on h4 and h5 |

- **Gate:** each slice gate; `make ui-structure-gate` extended with a `bid-opening` project.
- **Closes:** BOP-A12 and A16 (UI parts).

### Phase 9: Public portal
- The D10 BDS portal seam, then the public opening region.
- **Slice 9 boards:** p0, p1a, p1, p2, p3, p4, p5, p6. p1 is Conditional (no attendance-service provider).
- **Tests:** the readout appears only after the recorder's confirmation; Jane has no request control; David goes from request to preparing to download; before the deadline, nothing reveals a bid count (BOP-N01, browser part).
- **Gate:** `ui-bop-public-gate`.
- **Closes:** BOP-A08 and N09 (browser parts).

### Phase 10: Canonical seed stage
- The D14 `bid_opening` stage, `seed-canonical-validate` coverage, and the SEED-OPS-001 runbook addition (named as a required correction; the runbook is not edited without its own change step).
- **Gate BOP-G10:** `make seed-canonical SITE=kentender.midas.com THROUGH=bid_opening` and `make seed-canonical-validate`, both green.

### Phase 11: Release evidence
- `ui-bop-fidelity-gate` over all 50 boards.
- The BOP v0.10 §15 state/actor matrix: nonempty, empty, not held, interrupted, missing member, unreadable. For each it compares the visible control, server command, PRC event, My Work item, public disclosure and clearing transition.
- A persona browser pass as real users: Amina, Charles, Brian, Beatrice, David, Jane, Naomi and Administrator.
- PRC-INT-01 through the real owner.
- AC map closure, and `RUNBOOKS.md` (simulation switch, fixture reset, incident recovery).
- **Gate BOP-G11:** `ui-bop-release-evidence-gate`.

### Phase 12 (owner-gated; every row starts `Blocked — owner`)
- LAW-V-001 legal trace of Act section 78(1)–(11), section 67 and section 82 (BOP v0.10 §15).
- Operating profile: presence timeout, custody threshold and key holders, page and initial equivalence, attendee authentication, recovery.
- TRUST-ADR-001 support-module integration (real signing and custody).
- Security review (BOP v0.10 §15 list).
- Production enablement.
- The Evaluation intake of `Evaluation Handoff`.
- The TPR-CHG-001 v0.14 post-close decision route (BOP v0.10 §10.7).
- **No gate in this plan.**

## Conflicts and follow-ups to log (Phase 0)

| # | Conflict | Treatment |
|---|---|---|
| C1 | BOP v0.10 is "Proposed" (line 7), yet the boards are drawn against it. v0.10 also reverts approved v0.9 text: "Governing standard: KT-STD-001 v1.9" (v0.10) against "KT-STD-001 v1.10" (v0.9); "v0.9 proposed coordinated contract" against "v0.9 approved coordinated contract"; the timed kind is "proposed for KT-STD-001 v1.10 §2.9.1" against "approved KT-STD-001 v1.10 §2.9.1". | OD-A: build to v0.10's four changes. The owner rebases v0.10 onto approved v0.9 and approves it (FU-BOP-01). |
| C2 | TRUST-ADR-001 v0.1 is cited as approved (BOP v0.10 line 7; PRC v0.9 line 24), but no file exists in the repo. | D5/D6/D4 build to the cited semantics only. FU-BOP-02. |
| C3 | The baseline register (as_of 2026-09-26) has no BOP, PRC or TRUST entries. It lists KT-STD-001 at v1.9 and TPR-CHG-001 at v0.12, and gives BDS-CHG-001 implementation status "Planned" although its tracker shows G00–G13 passed. The KT-STD-001 v1.10 file is named `_proposed` while its content says Approved. | Report to the documentation owner (FU-BOP-03). This plan does not edit the register. |
| C4 | BOP needs page count, price page and pages to initial, but no renderer exists. | D5. |
| C5 | The BDS handoff has no read or acknowledge service. | D4 (BDS addendum). |
| C6 | `TenderCancelled` has no outbox consumer, and TPR-CHG-001 v0.13 has no post-close cancellation. | D8; FU-BOP-06. |
| C7 | The physical-security visibility exception depends on BDS-CHG-001 v0.9, which is proposed (BOP v0.10 §3: "must be approved before treating that exception as a reconciled production contract"). | Build no pre-opening physical-security disclosure to PE opening users. FU-BOP-07. |
| C8 | BOP v0.10 §13 and BOP-A16 require an isolated verification deployment; OD-C runs the stand-ins on the dev site. | A recorded departure. The production switch stays false, and stand-ins refuse to load without the simulation flag. |
| C9 | Jane Wanjiku is not in KT-STD-001 §8.3. | D13; FU-BOP-08. |
| C10 | Presence needs a live session, but socket.io is not served on this bench. | D7 polling heartbeat; the timeout is an operating-profile value. |

## Risks

- **Scale.** 50 boards, 34 acceptance criteria, 36 named fixtures and 20 binding rows. Mitigation: horizontal Phases 1–3, then vertical slices, with one fixture entity per browser spec.
- **Tenders routing regression** from the D9 seam. Mitigation: the seam is the first Phase 8 task, followed by one run of the Tenders UI gates.
- **Bid-count leakage** before Start, through timing, step presence or error wording (BOP-A13). Mitigation: a named leakage gate in Phase 4 and Phase 7, not a UI afterthought.
- **Site-wide test mutation.** `bench run-tests` persists writes. Mitigation: fixture years ≥ 2100, purge registration, reseed to canonical after runs, and never run Python and Playwright together.
- **Renderer determinism.** Mitigation: a pinned template and fonts, and the digest asserted twice in one test.
- **Proxy mistaken for production.** Mitigation: `production_bid_opening_enabled` is read in one place; verification labels live only in tests; a tracker rule prohibits them in product copy.

## Verification

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.proceedings.tests.<module>
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.bid_opening.tests.<module>
./scripts/bench-with-node.sh build --app kentender_procurement
cd apps/kentender_v1
make prc-services-gate
make bop-services-gate
make bop-dead-end-gate
make bop-leakage-gate
make ui-queue-check
make ui-bop-<slice>-gate
make ui-bop-public-gate
make ui-bop-fidelity-gate
make ui-bop-release-evidence-gate
make seed-canonical SITE=kentender.midas.com THROUGH=bid_opening
make seed-canonical-validate SITE=kentender.midas.com
```

**Live browser walk (Phase 11), under the simulation flag, on the canonical Afya Tender:**
1. Amina appoints Charles, Brian and Beatrice, then publishes how to attend.
2. Jane sees the join window.
3. Each member joins, and David's and Jane's arrivals are recorded.
4. After close, Charles sees **Start opening**, with no bid count shown beforehand.
5. Brian's readout, confirmed by Charles, appears on Jane's public view only after confirmation.
6. Charles uses **End opening**, **Prepare opening record** and **Finish opening record**.
7. Each member signs their own targets, and completion follows with no chair click.
8. David requests and downloads the register.
9. Naomi reads the completed record; Administrator sees technical status only.
10. Repeat for the `-034` empty, `-035` not-held and paused branches on their own fixtures.

## Phase 0 findings and owner answers (29 September 2026)

These are recorded here; the phase text above is not rewritten.

**Owner answers**, verbatim: "v0.10 is now approved"; "Register Daniel Otieno"; "Add Jane Wanjiku"; "Register updated"; "Commit and proceed to Phase 1".

| Item | Effect on this plan |
|---|---|
| BOP-CHG-001 v0.10 approved 29 Sep 2026, with the approval references reconciled | C1 is closed. The authority is now approved v0.10; OD-A stands with no approval dependency. |
| TRUST-ADR-001 v0.1 supplied | C2 is closed. It confirms D4 and D6 and adds three requirements, listed below as D15–D17. |
| KT-STD-001 v1.11 drafted: two §8.3 actors (Daniel Otieno, Jane Wanjiku) | It is Proposed and needs the Project Owner's approval before Phase 10 seeds either persona (FU-BOP-08). D13 uses the logins in that draft: `daniel.otieno@moh.example.test` and `jane.wanjiku@observer.example`. |
| Register refreshed (`as_of` 2026-09-28) with BOP v0.10, PRC v0.9, TRUST v0.1 and KT-STD-001 v1.10 entries | C3 is closed except the note in FU-BOP-03. |

**New technical decisions, from TRUST-ADR-001 v0.1:**

| # | Decision |
|---|---|
| D15 | **Test-environment labels at runtime.** TRUST-ADR-001 v0.1 §2 requires, in the test proxy, the UI and export label "Test attestation — not an electronic signature" on a member's test proof, and "Prominent **Test environment — bids are not submitted/opened under the production procedure** on all affected screens, receipts and exports". Under the simulation flag (OD-C), the Bid Opening runtime therefore shows that strip on every Bid Opening screen, public opening view and export, and labels each test proof, in the same way as the BDS simulation strip. The boards picture production and do not draw the strip. The "Shared infrastructure deferral" paragraph of BOP-CHG-001 v0.10 (line 20) already says proxy demonstrations "use explicit non-production labels outside the product design contract", so they are recorded as a Conditional runtime addition in the fidelity departures file, not as a board departure. With the simulation flag off, neither label renders. This refines D6 and tracker rule 3. |
| D16 | **Trust-interface outcomes.** Every call through the custody, signing or renderer gateway returns exactly one of `Unavailable`, `Rejected`, `Indeterminate` or `Accepted/Verified`, carries one correlation identity, and is safe to retry (TRUST-ADR-001 v0.1 §4). Bid Opening never records a successful reveal, proof or render on timeout; `Indeterminate` pauses the ceremony with an incident. This refines D4 to D6. |
| D17 | **Proxy negative paths.** The Phase 3 and Phase 5 gates include every negative path TRUST-ADR-001 v0.1 §2 lists for the proxy: early attempt, one-member or absent-member attempt, stale member, invalid package, duplicate receipt, interrupted session, stale target, administrator attempt, and recovery without rewriting history. The release confirmation follows TRUST-ADR-001 v0.1 §2: at least two distinct committee members, including the independent member, confirm once, and all appointed members stay present before each reveal. |

