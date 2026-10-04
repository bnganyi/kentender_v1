# BDS-CHG-001 v0.8: Supplier Portal and Electronic Bid Submission, implementation plan

| Control | Value |
|---|---|
| Version | 0.8-plan.1 (implementation plan for BDS-CHG-001 v0.8) |
| Date | 26 September 2026 |
| Authority | `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_8.md`, **Approved** 26 Sep 2026 (control table lines 8–12). Its implementation authority, quoted: "Approved v0.8 requirements authorise implementation of the unconditional contract. Production submission remains disabled until the operating and release gates in BDS-CHG-001 §§5.10 and 15 pass. The published-Tender Superseded/Withdrawn branch remains conditional on TPR-CHG-001 v0.13 approval." |
| Sibling authorities | Status per the baseline register KT-DOC-CTRL-001 (`98_work_progress/KenTender_Baseline_Register.yaml`, as_of 2026-09-26).<br>**Approved:** KT-STD-001 v1.9; TPR-CHG-001 v0.12; STD-TPL-001 v0.10; STD-TPL-IMP-001 v1.1; REQ-CHG-001 v1.12; PLN-CHG-001 v1.27; BUD-CHG-001 v1.11; LAW-REG-001 v1.2; SEED-001 v1.3.<br>**Project Owner review:** CFG-CHG-002 v0.16 (built ahead of approval under OD-A); AUTH-ADR-001 v1.10; G1-REG-001 (the register lists v1.1; a v1.2 file exists; see follow-up FU-V08-19).<br>**Proposed:** TPR-CHG-001 v0.13 (gates Phase 13 only). |
| Design | `design/Bid Board v3 - A…E *.dc.html`: 79 labelled artboards, each at 1440×1024 and 390×844. The old board and its `_ds` bundle are in `retired/`. |
| Companions | `BDS-CHG-001_v0_8_IMPLEMENTATION_TRACKER.md`, `BDS-CHG-001_v0_8_FOLLOW_UPS.md`, `reconciliation/` (Phase 0 matrices). Later: `evidence/v0_8/` and `RUNBOOKS.md`. |
| Predecessor | `BDS-CHG-001_Implementation_Plan.md`, `BDS-CHG-001_IMPLEMENTATION_TRACKER.md` and `BDS-CHG-001_FOLLOW_UPS.md` (v0.4, 21 Sep 2026) are **retained unchanged as history**. This v0.8 set supersedes them for tracking. Their standing owner decisions are carried below. |
| Prepared | 26 September 2026. The plan was approved by the Project Owner on 26 Sep 2026 in the planning session, together with owner decisions OD-A…OD-H. |
| Status | Phase 0 in progress. No product code written. |


## Context

BDS-CHG-001 v0.8 (Supplier Portal and Electronic Bid Submission) was approved on 26 Sep 2026. It replaces v0.4, which the stale 21 Sep plan was written against. v0.8 adds:
- atomic **Start bid** (candidate registration, mandatory-notice contact and workspace in one step);
- supplier questions through Tenders;
- candidate notice states;
- System setup's public support and legal links;
- one default-off production switch with distinct outage codes;
- KT-STD-001 next-step, journey and hand-off guidance;
- receipt history.

The new design set is five "Bid Board v3" boards (`12_bid_submission/design/`): 79 labelled artboards, each drawn at 1440×1024 and at 390×844. The old boards are in `retired/`.

**Current state (verified 26 Sep):**
- No Bid Submission code exists (`bid_submission_opening/` is an empty scaffold).
- The old plan's Phase 3 blocker is gone. STD release 1.1 is installed and switched On, and Tenders v0.12 compiles and freezes the Published Bid Definition (`tenders/services/bid_definition.py`).
- Tenders built seams this module must plug into:
  - a temporary candidate stand-in (`candidate_gateway.py`, hook `kt_tender_candidate_registry`, TPR FU-25);
  - clarification intake (`clarifications.receive_tender_clarification`, producer identity);
  - candidate notices;
  - submission close, which emits `TenderSubmissionPeriodEnded` to consumer "bid-submission".
- The two legacy bid systems (`tender_configurations` bid slice and TM2) are still live, and they own the `/tenders/...` URL tree.
- Nothing mounts Vue on a public page yet.
- Frappe 16.12's Desk prefix is `/desk/`, so the spec's `/desk/tender-security-receipts` is literally right.

**Governing standard:** KT-STD-001 v1.9 (approved 26 Sep; presentation-only change to v1.8).

**Done means:**
- The BDS-CHG-001 §13.3 lifecycle runs end to end in a browser, as the named actors, on a labelled test environment with simulated signing and tender-box services, ending in a sealed Bid Opening hand-off.
- Every BDS-CHG-001 §13.4 isolated state is proven at both sizes.
- The dead-end matrix is clean.
- Production submission stays off. The BDS-CHG-001 §5.10/BDS-CHG-001 §15.3–15.6 operating-profile, security and legal evidence is recorded as owner-blocked and never claimed.

## Owner decisions (this session, 26 Sep 2026)

| # | Decision |
|---|---|
| OD-A | **Build System setup's Supplier portal piece here**, ahead of CFG-CHG-002 v0.16 approval and flagged as such. It comprises the `PublicPortalSettings` record, `UpdatePublicPortalSettings`, the public `GetPublicPortalInformation` projection, and the **Supplier portal** section after Reminders in Procurement settings. There is no artboard; it is built from CFG v0.16 BDS-CHG-001 §10.10A text and recorded as a departure. |
| OD-B | **One Vue portal.** One public page shell carrying the boards' header, skip link and footer, plus a new `kentender_core` portal runtime that mirrors `desk_page` (register / route adapter / screen cache / sequence guard / command runner / fetch-based call). No vue-router, no WebsiteGenerator. |
| OD-C | **Simulated services on test sites.** When site_config `kt_bds_simulation_environment: 1` is set, the Test Trust Service, Test Tender Box, Test Scanner and test clock register and `production_bid_submission_enabled` may be true. Every supplier page then shows a "Test environment" strip. Production defaults false and the simulations refuse to load. |
| OD-D | **Minimal suspend and restore.** A new internal responsibility, "Supplier Account Support Officer" (Amina Yusuf), gets Suspend and Restore access actions on a standard Frappe form. They create and clear the BDS-CHG-001 §5.14 item. Logged as a spec follow-up. |
| OD-E | **Reconcile the template before completing the bid journey.** The installed release 1.1 definition differs from the boards and BDS-CHG-001 §10.1: 4 generic warranty rows against 6, no security `valid_until`, free-text JV members, year of registration, 4 evidence items against 10, and CBQ against "Tenderer information". Treatment:<br>• Reconcile each difference against the approved template pack, source coverage, Published Tender and BDS contract.<br>• Correct the controlled template assets and rerun the definition, mapping and rendering checks.<br>• Install a **successor release** (1.2). Release 1.1 keeps its immutable identity and is switched **Off** (not Superseded, so no already-bound Tender enters the unapproved TPR v0.13 branch). No existing Published Bid Definition is changed.<br>• Never hard-code board rows, and never accept a missing obligation as a departure.<br>• **Hold completion of the Company, Requirements, Review and Submit journey until 1.2 passes.** |
| OD-F | **Legacy TM2:** retire only the bid slice and the route collisions now. The rest of TM2 (25 dependent files in `procurement_lifecycle`/`procurement_home`) gets its own later clean-up (follow-up, inventory produced in Phase 0). |
| OD-G | **DES-15 is not built as drawn.** Charles gets a **blind physical-original intake form**: Tender reference plus the instrument's own details. It issues an opaque intake receipt and shows no candidate list, no bid status and no indication of whether a matching bid exists. The intake record is protected. |
| OD-H | **Private match.** The server privately links an intake to a bid by exact instrument details. Only that supplier's own bid shows "Physical original recorded as received", with the intake reference and time. Charles's reads are identical whether or not a match exists. The sealed Bid Opening hand-off carries the intake inventory and the matches. |

Carried from 21 Sep:
- Legacy bid records are deleted outright, with no migration.
- BWMF/STD-wizard machinery is untouched (FU-05).
- The KT-STD-001 §8.3 persona register wins where it already has the role.

## Key technical decisions (implementation authority unless the owner says otherwise)

| # | Decision |
|---|---|
| D1 | **App split.** Identity (Supplier Organisation, Supplier User Assignment, Account contacts and verification, Account evidence, access decisions) lives in `kentender_suppliers`, new module **Supplier Accounts** (`supplier_accounts/`). Everything Tender-bound (Bidder Arrangement/candidate, workspace, responses, evidence, security, submission, custody, close) lives in `kentender_procurement`, new module **Bid Submission** (`bid_submission/`). The cross-app seam is a core-declared hook, `kt_supplier_account_provider`; procurement never imports suppliers, because procurement installs first. |
| D2 | Spec model names verbatim: Supplier Organisation, Supplier User Assignment, Bidder Arrangement, Bid Workspace, Bid Section Response, Bid Evidence, Tender Security Response, Bid Submission Version, Tender Box Envelope, Bid Receipt, Bid Submission Change. There is no link to ERPNext `Supplier` or `KTSM Supplier Profile` (registration is not qualification). |
| D3 | **Tenders/STD published seams (additive; recorded as addendum rows in the Tenders tracker).**<br>• `tenders/services/bidder_projection.py`: allowlisted public list/detail, guest-safe document stream, anonymous public answers, a candidate view of own questions and notices.<br>• `bid_definition.definition_for(tender, version)`.<br>• `bid_definition.map_bid_definition_addendum(tender, from_v, to_v)` (= `MapBidDefinitionAddendum`), with the identity map stored immutably on successor rows at `store()`.<br>• `events.pending_for_consumer`.<br>• `std_templates/services/runtime.bid_work_status(release_id)`.<br>BDS reaches Tenders/STD only through `bid_submission/services/tenders_gateway.py`. |
| D4 | **Bound-release rule.** Available with the switch On or Off → permitted. Superseded or Withdrawn on a *published* Tender → fail closed with `BDS_DEFINITION_UNSUPPORTED`, preserving Drafts and receipts, until TPR v0.13 is approved (BDS-CHG-001 §18.1, BDS08-AC-008). Integrity or renderer failure → fail closed. |
| D5 | **Availability.** `production_bid_submission_enabled` comes from `frappe.conf`, default false, with no Desk, portal or API control. One `availability.get_submission_availability()` serves signature preparation, submission and replacement. It returns, in this order: `BDS_PRODUCTION_SUBMISSION_NOT_ENABLED`, `BDS_SIGNATURE_UNAVAILABLE` (trust), `BDS_SUBMISSION_SERVICE_UNAVAILABLE` (time/custody). A simulation-only Single, `BDS Test Environment Controls` (no permissions; fixture-written; ignored outside simulation), forces the GATE/OUTAGE/SIGNATURE worlds. |
| D6 | **Gateways.** `trust_gateway`, `custody_gateway`, `time_gateway` and `scan_gateway` are interfaces, each with one simulation double. Production adapters are unconfigured, which reports as unhealthy. No homemade CA, signature or encryption (BDS-CHG-001 §16). |
| D7 | **Honest custody minimum.** The Test Tender Box stores package bytes under `sites/<site>/private/kt_test_tender_box/`, outside every DocType and `File`, with no read API. BDS keeps only ids and digests. Every simulated receipt is labelled `simulation=1`. There is no encryption claim; the residual (Administrator DB bypass, working-copy rows) is recorded as a production-gate item. |
| D8 | **Submission is two-phase with a durable attempt.** An explicit, documented commit boundary, an exception to AGENTS.md section 4.4 required by the uncertain-result semantics:<br>1. Phase 1 locks, checks trusted `received_at` against the deadline (strict `<`), revalidates, builds the canonical package and persists a `Bid Submission Attempt` (correlation `COR-…`, key hash, package digest), then commits.<br>2. The custody deposit follows.<br>3. Phase 3 atomically commits one of: Version + Envelope + Receipt + audit; Rejected; or Uncertain.<br>A scheduler reconciler resolves Uncertain attempts from the same correlation, with no second dispatch. |
| D9 | **Close.** Every command carries an in-transaction deadline guard. BDS consumes `TenderSubmissionPeriodEnded` (consumer "bid-submission") and runs `CloseBidSubmission`:<br>• Drafts become Closed without submission and arrangements are Closed;<br>• the box closes;<br>• a `Bid Opening Handoff` is created (envelope ids, lineage, custody proofs, intake inventory and matches; no content);<br>• an outbox event goes to consumer "bid-opening".<br>It also consumes `TenderOpenForSubmission`, which closes TPR FU-13. |
| D10 | **Addendum refresh is supplier-initiated** (`RefreshBidForAddendum`, run inside the first named mutation after an addendum becomes effective). Reads derive Needs attention without mutating. The BDS-CHG-001 §5.14 review item is opened by the event consumer. This matches BDS-CHG-001 §13.3: a read on v4 at 12:05, then save v5 at 12:10. |
| D11 | **No identifiers leak.** Portal DTOs carry per-definition opaque field handles mapped back to `response_id` on the server, never `RSP-`/`COMP-`/`CTL-`/`RR-`/`EVG-` ids, digests, schemas or paths. A leakage test scans every read DTO and the rendered HTML. |
| D12 | **Authorisation.** Explicit services (`bid_authorization.py`, `account_authorization.py`), not `has_website_permission`. Both families of DocTypes have no role permissions, plus deny `has_permission` and `permission_query_conditions`. Cross-organisation reads mask as Not found. The active organisation for multi-org users is carried explicitly per request and revalidated each call, never a session default (KT-STD BDS-CHG-001 §10). |
| D13 | **Personas.**<br>• Auditor: Naomi Chebet, not the spec's Alice Njeri (follow-up).<br>• Receipt/intake owner: Charles Mutiso, HOPF, with new sod tag `tender_security_receipt`.<br>• Procurement Officer: Brian Wafula.<br>• New Website Users on the spec's domains: David Ouma, Mary Wanjiku, Peter Mwangi, Grace Njeri, and the Jua Technology registrant.<br>• New internal: Daniel Otieno (System Manager, technical operator, CFG holder; not the Administrator login), Amina Yusuf (Supplier Account Support Officer), Nadia Kamau (release operator).<br>A request goes to the KT-STD owner to add them to BDS-CHG-001 §8.3. |
| D14 | **Guidance.** The Account S/V/A and Bid P/S/R journeys, next steps and guards use `kentender_core/services/next_step.py`. The shared `NextStep`/`JourneyTracker` components are mounted on the portal through `kentender_core.industry.mountGuidance`. The reduced tracker uses the spec's stated form "Stage {label} of 3" (KT-STD BDS-CHG-001 §2.9.3.5: the change unit states it); the board's "· 2 of 3 ·" is logged. Technical readers get waiting, done or not involved only; sealed-bid content is never in their projection (a BDS domain rule, which prevails under KT-STD BDS-CHG-001 §1). |
| D15 | **Supplier hand-offs.** BDS-CHG-001 §5.14 items for Mary and David are persisted `Bid Hand-off` rows. They surface as the row action in My bids, the next-step block and an email transport (hook plus test double). My Work and Home are Desk-only, so this is logged as a follow-up. Amina's item is a Desk My Work item. Operational items for Daniel and Nadia are `Bid Submission Incident` rows with a Notification Log, never My Work. |
| D16 | **Evidence.** BDS/ACC upload endpoints take a multipart file, create a private File attached to the evidence record, then run `kentender_core/services/file_integrity.check_file`. **Accepted only with a real scanner verdict** from `scan_gateway` (the `kt_file_scanners` hook, or the Test Scanner in simulation). Account evidence linked into a bid is an exact byte copy with an equal digest. Downloads use short-lived tokens bound to user and record. |
| D17 | **Narrow layout.** A `useNarrow()` composable renders the boards' labelled-card lists at ≤600 px instead of tables, so the structure matches at 390 without horizontal scroll. |
| D18 | **Trusted time.** `bid_submission/services/clock.py` works like `tenders/services/clock.py`: `frappe.flags.kt_bds_clock` in tests and `kentender_core.seeds.clock.at` in seeds. A simulation-only persisted instant drives browser worlds (the "Current server time" and closed states). |
| D19 | **Seed interleaving.** The canonical Tenders stage is refactored into dated step functions. With `THROUGH>=bid_submission`, BDS steps interleave at their real BDS-CHG-001 §13.3 instants: registration 18 May, Start bid 19 May replacing the stand-in, question 26 May, addendum acknowledgement 1 Jun, submission 10 Jun, close 12 Jun. |

## Phases

Every phase follows the same loop:
- TDD red → green → refactor per behaviour;
- then the containing module's tests;
- then the phase gate;
- then tracker and follow-up updates.

New `make` targets go beside the `tenders-*` block, with a `bds-preflight` that refuses to run while Playwright is running. Never run the Python suite and Playwright together; run `make ui-queue-check` before UI runs.

### Phase 0: Documents and reconciliation (no product code)
- Rewrite `12_bid_submission/BDS-CHG-001_Implementation_Plan.md`, `_IMPLEMENTATION_TRACKER.md` (gates BDS-G00…G13; the spec's native AC and IMP IDs) and `_FOLLOW_UPS.md` for v0.8, following the full-replacement precedent. Use the `kentender-document-change` skill protocol for every controlled-document edit.
- Write `12_bid_submission/reconciliation/`:
  - `definition_to_board_matrix.md`: every response, price and declaration row of the release 1.1 MOH definition (`07_tender_templates/it_equipment_open_v1/06_runtime/moh_published_bid_definition_expected.json`) against every board element and BDS-CHG-001 §10.1 fact, each classified. This feeds Phase 3.
  - `fixture_chronology.md`
  - `artboard_inventory.md`: 79 labels → `Component#variant`, both frames, with the conditional and OD-G-replaced labels marked.
  - `error_contract.md`: the BDS-CHG-001 §8 set verbatim.
  - `hand_off_register.md`
  - `legacy_inventory.md`: the 1A list, plus the TM2 remainder for the later clean-up.
- Add addendum rows to the Tenders and STD-TPL-IMP trackers for the D3 seams and FU-25.
- Log spec follow-ups: OD-D, OD-G/H (DES-15, BDS-CHG-001 §6, AC-035/036), Alice Njeri → Naomi, the reduced-tracker wording, supplier My Work (D15), BDS-CHG-001 §5.1 "Refresh bid".
- **Ask the user to commit** the untracked v3 boards, the `retired/` move and the approved v0.8 working copy. The artboard-provenance gate needs them in git.
- **Gate BDS-G00:** matrices reviewed; `make artboard-provenance-gate` green.

### Phase 1: Retire the legacy bid slice (must precede portal routes)
- `kentender_procurement/hooks.py`:
  - remove the 22 `/tenders/<publication_ref>/…` rules and the `/supplier/tenders/<code>` rule;
  - remove `app_include_js` `electronic_bid/bidder_workspace_renderer.js`;
  - remove `page_js` `bid-submissions` and `it-electronic-bidder-workspace`.
- Delete:
  - `www/tenders/**`, `www/supplier/**`;
  - pages `bid_submissions` and `it_electronic_bidder_workspace`;
  - their JS/CSS and `templates/includes/kt_bidder_*`;
  - `tender_configurations/services/{electronic_bid,bid_submissions,bid_evidence,bidder_presentation,bid_issues,bidder_submission_schema,price_schedule_bidder,final_submission}.py`, with their tests and seed fixtures;
  - the empty `bid_submission_opening/`.
- Patch `patches/bds_chg_001_v08_retire_bid_slice.py`: delete the Electronic Bid Submission, IT Bid Opening Record and Electronic Bid Audit Event rows (children first) and their doctypes; delete the TM2 *bid* doctypes (Bid Submission/Component/Receipt/Draft Metadata/Late Submission Attempt), subject to the inventory confirming no non-bid TM2 dependents.
- Remove the "Bid Submissions" sidebar entry. The Desktop Icon "Tenders" → `/tenders` now resolves to the new DES-01.
- `kentender_core/seeds/demo_platform_seed/*`: replace the bid-scenario calls with `{"ok": False, "skipped": True, "reason": "BID_SUBMISSION_MODULE_RETIRED"}`; BWMF imports stay.
- Makefile and `tests/ui/smoke`: drop the bid-facing legacy gates and specs listed in the inventory.
- **Tests:** `bid_submission/tests/test_legacy_retirement.py` (repository and schema scan).
- **Gate BDS-G01:** `make bds-retirement-gate`; `bench migrate` clean twice.
- **Closes:** BDS01-IMP-090, BDS07-IMP-010.

### Phase 2: Prerequisites

**2A. System setup Supplier portal (OD-A, `kentender_core`)**
- Doctypes: Single `Public Portal Settings`, holding:
  - support email, phone and hours;
  - the three HTTPS destinations;
  - `record_version` plus audit fields;
- and an append-only `Public Portal Settings Change`.
- `services/public_portal.py`:
  - `update_public_portal_settings` (Administrator/System Manager, atomic, version plus idempotency);
  - `get_public_portal_settings`;
  - `get_public_portal_information()`: labels, destinations, Complete/Incomplete with the missing categories, version; no audit.
- Add `CFG_*` codes in `services/configuration_errors.py`.
- Add `api/public_portal_api.py` and technical-read registration.
- UI: `public/js/system_setup/components/SupplierPortalSection.vue` inside the Procurement settings tab, covering the complete, incomplete, invalid-link and saved states.
- Seed through the command in `seeds/site_setup.py` with the BDS-CHG-001 §10.1 values.
- **Tests:** `tests/test_public_portal_settings.py`, plus a system_setup vitest.
- **Gate:** `make cfg-portal-settings-gate`.

**2B. Tenders/STD seams (D3)**
- `tenders/services/bidder_projection.py`:
  - `available_tenders(...)`;
  - `published_tender(ref, at)`: allowlist only, with addenda applied to the current delivery location and deadline;
  - `stream_public_document(ref, kind, addendum_ref)`: guest-safe bytes, no digest or file URL;
  - `public_answers(tender)`: no candidate id; changed-content answers withheld until the addendum is effective;
  - `candidate_view(tender, candidate_registration_id)`.
- `bid_definition.py`:
  - `definition_for`, `map_bid_definition_addendum`;
  - `identity_map_json` / `identity_map_digest` on Tender Bid Definition successor rows, with a backfill patch.
- `events.pending_for_consumer`.
- `candidate_gateway` gains a test-only provider override via `frappe.flags`.
- `std_templates/services/runtime.bid_work_status`.
- **Tests:** `tenders/tests/test_bidder_projection.py` (allowlist key scan, guest, cancelled, ended, anonymity), plus additions to `test_bid_definition.py`, `test_gateway_contracts.py` and `std_templates/tests/test_bid_work_status.py`.
- **Gate:** `make tenders-services-gate` and the STD gate stay green.

**2C. Portal runtime walking skeleton (OD-B)**
- `kentender_core/www/kt_portal.{html,py}` (`no_cache`), on its own base template `templates/kt_portal/base.html`:
  - links fonts and `kt_industry_tokens.css` explicitly;
  - loads `frappe-web.bundle.js` for `__`, `frappe.provide` and CSRF;
  - loads `kt_industry_guidance.bundle.js`, the runtime bundle and the surface bundle.
- Surface resolution: new hook `kt_portal_surfaces` (longest route prefix → the owning app's resolver plus bundle).
  - The resolver returns the verdict, any redirect, the active nav and the first payload (KT-STD BDS-CHG-001 §3A.1).
  - The shell renders the board header, skip link and footer server-side from `get_public_portal_information()`. The footer is omitted when Incomplete.
  - A "Test environment" strip shows in simulation.
- `public/js/kt_portal/kt_portal_runtime.bundle.js` → `kentender_core.portal_page`, with:
  - `register`;
  - `useRoute` (History API, popstate/pageshow epoch);
  - `createScreenCache`, `createSequenceGuard`, `createCommandRunner` (parity with `kt_desk_page.js`, enforced by a shared spec);
  - `call()`: fetch with `X-Frappe-CSRF-Token`, parses `kt_error_*`, never msgprint;
  - `upload()`, `leaveGuard`, dialog focus trap.
- `public/css/kt_portal_shell.css`, scoped `.kt-industry .kt-portal-*`.
- Vitest project `kt-portal-runtime`.
- `tests/ui/helpers/portal.ts`: `loginToPortal(page, user, returnTo)`, `expectNoFrappeDialog`, `expectNoHorizontalOverflow`, `atZoom200`.
- First surface: BDS `/tenders` (DES-01, guest, read-only).
- **Gate BDS-G02:** 2A and 2B green; `/tenders` renders at 1440 and 390 with zero console errors; computed-style proof that the website theme and Bootstrap do not bleed in; `make ui-industry-design-gate` and the translation-binding gate green for the new bundles.

### Phase 3: Template reconciliation → successor release 1.2 (OD-E; runs in parallel with Phases 4–5)
- Work each Phase 0 matrix difference against:
  - the official source coverage (`07_tender_templates/it_equipment_open_v1/03_registers/`);
  - the approved STD-TPL-001 v0.10 rules (BDS-CHG-001 §§7–10, BDS-CHG-001 §13.5–13.6);
  - the Published Tender;
  - the BDS contract (BDS-CHG-001 §4.4.8: Account-owned facts pre-fill from the snapshot and are not new bidder fields).
- Classify each difference as one of:
  - (a) a published obligation missing from the rules → correct the assets;
  - (b) Account/arrangement-owned → pre-filled from the snapshot or arrangement;
  - (c) board or BDS-CHG-001 §10.1 content with no source → spec or design follow-up, not built.
- Correct `06_runtime/{response_rules,downstream_rules,addendum_identity_rules,product_profile}.json` and the coverage registers. For example: specific warranty/support response rows, security `valid_until`, structured JV members sourced from the arrangement, and evidence requirements linked to their rows.
- Stop and raise to the document owner if a correction needs STD-TPL-001 text changes (that text is owner-authored).
- Rebuild with `make std-release-rebuild`: validator, fixtures, expected definition, manifest and change report.
- If new controls or compositions are needed, bump `supported_renderer_version` in `std_templates/renderers/registry.py` `bid_workspace_capabilities`.
- Install 1.2 (Available, On) and switch 1.1 **Off** with `make std-release-switch`. Tenders bound to 1.1 keep their frozen definitions.
- **Tests:** STD compiler and vector parity, `tenders/tests/test_bid_definition.py` against 1.2, and a canonical reseed binding 1.2.
- **Gate BDS-G03:** the validator passes on 1.2; the fixture and production adapters produce byte-identical definitions; every matrix row is closed; 1.1 is unchanged.
- **This gates** completion of the Company, Requirements, Review and Submit slices (Phases 5 and 11) only.

### Phase 4: Supplier identity and Account (`kentender_suppliers/supplier_accounts/`)
- Add "Supplier Accounts" to `modules.txt`.
- Doctypes (no role permissions; deny hooks):
  - `Supplier Organisation`: BDS-CHG-001 §4.1 fields, `account_status`, `status_since`, `record_version`; child `Supplier Account Contact` with verification state.
  - `Supplier Account Verification`: token hash, TTL, status.
  - `Supplier User Assignment`: immutable; responsibility, job title, authority evidence, effective window, assigner.
  - `Supplier Account Evidence`.
  - `Supplier Account Access Decision` (OD-D).
  - `Supplier Account Task`.
  - `Supplier Account Event` (audit, BDS-CHG-001 §12.1).
  - `Supplier Account Command Journal`.
- Services (`services/`):
  - `errors.py` (BDS codes), `clock.py`, `envelope.py` (mirrors `tenders/services/envelope.py`);
  - `account_authorization.py`;
  - `registration.py` (`RegisterSupplierOrganisation`; Frappe website sign-up enabled for the person's login);
  - `verification.py` (`SendAccountVerification` with a non-disclosing rate limit of 3 per hour and a 24 h TTL; `VerifyAccountCommunication`; transport hook `kt_supplier_account_message_transports` plus a test transport);
  - `organisation.py` (`UpdateSupplierOrganisation`, contacts);
  - `assignments.py` (`AssignSupplierRepresentative`, `AssignAuthorisedSignatory`);
  - `evidence.py`;
  - `access.py` (suspend/restore; Amina or System Manager; reason required);
  - `read.py` (`GetSupplierAccount`);
  - `guidance.py` (S/V/A);
  - `provider.py` (the `kt_supplier_account_provider` contract: active assignments, assignment, organisation facts plus version, verified contacts, Account evidence, account status, find an Active Account by country and registration number for a JV member, returning legal name only);
  - `my_work_provider.py`, `technical_read.py`;
  - `portal.py` (surface resolver for `/account`, `/account/register`, `/account/verify`).
- Core:
  - `services/business_role_registry.py` gains "Supplier Account Support Officer" (site scope, `sod_tags=("supplier_account_support",)`);
  - `services/supplier_account_contract.py` holds the hook name, resolver and contract-test helper.
- **Tests (`tests/`):** schema, registration, verification, assignments (window boundaries; a representative cannot sign; evidence required), authorisation masking, suspension, evidence, guidance, provider contract.
- **Gate BDS-G04:** `make supplier-accounts-schema-gate supplier-accounts-services-gate`.
- **Closes:** BDS01-IMP-004…008/010/011, BDS03-IMP-009/010, BDS01-AC-004…010, BDS03-AC-009/010.

### Phase 5: Definition binding, Start bid and candidate provider (`kentender_procurement/bid_submission/`)
- Add "Bid Submission" to `modules.txt`.
- Doctypes:
  - `Bidder Arrangement`: tender, reference, type, lead organisation, JV name, agreement evidence, signatory assignment, Tender contact, `candidate_registered_at`, status, version; child `Bidder Arrangement Member` with legal-name snapshots; append-only child `Bidder Arrangement Notice Contact` versions.
  - `Bid Workspace`: unique active (tender, arrangement); definition id, version and digest; organisation snapshot; derived status; `status_since`; `current_draft_version`; `current_submission_version`.
  - `Bid Organisation Snapshot` (immutable), `Bid Command Journal`, `Bid Submission Event`.
- Services:
  - `errors.py` (the BDS-CHG-001 §8 closed set; `fail()` like `tenders/services/errors.py`);
  - `clock.py`, `envelope.py`, `references.py` (named-lock minting of `ARR-`/`BID-`/`RCPT-`/`WD-`/`COR-BDS-`/`SUP-BDS-`);
  - `supplier_gateway.py` (fails closed without the provider), `tenders_gateway.py`;
  - `product_profile.py` (`ResolveBidProductProfile`: an exact family/renderer/version registry, no fallback);
  - `definition_runtime.py` (v1 field order, `verify_definition_digest`, the D4 rule, rejection of aliases and unknown rows);
  - `bid_authorization.py`;
  - `candidate_registry.py` (the `kt_tender_candidate_registry` provider);
  - `start_bid.py` (`StartBid`: arrangement, notice contact, snapshot and Draft v1 atomically, under a row lock and unique index, with idempotency-key replay; guards: Active Account, verified notice email, JV permitted, CFG Complete, definition supported);
  - `notice_contact.py` (`UpdateTenderNoticeContact`);
  - `clarification.py` (`SubmitTenderClarification` through the producer identity in site_config `kt_bds_clarification_producer`);
  - `snapshot.py` (`RefreshBidOrganisationSnapshot`);
  - `api.py`, with NOT_FOUND/FORBIDDEN returned as data like `tenders/api.py:_masked_read`.
- Hooks:
  - `kt_tender_candidate_registry`, the permission hooks, technical-read resolvers and probes;
  - `website_route_rules` for `/tenders`, `/tenders/<ref>`, `/tenders/<ref>/bid[/<task_key>|/receipt/<r>]`, `/my-bids`, `/account/receipts` → `kt_portal`;
  - `kt_portal_surfaces`.
- **FU-25:** patch `tpr_fu25_retire_candidate_stand_in.py` removes `Tender Candidate Registration`, `register_stand_in_candidate` and its API. Tenders tests switch to the flag-injected fake provider; the Tenders seed and Playwright steps go through BDS (D19).
- **Tests:**
  - `test_bds_schema.py`;
  - `test_definition_runtime.py` (On/Off permitted; published Superseded/Withdrawn and integrity failures fail closed; unknown family, renderer or control creates no partial workspace);
  - `test_product_profile_contract.py`;
  - `test_start_bid.py` (atomicity, concurrency, replay, rollback, JV, suspended, CFG incomplete);
  - `test_candidate_registry_contract.py`, `test_notice_contact.py`;
  - `test_clarification.py` (27 May 17:00:00 rejected; no BDS store);
  - `test_org_snapshot.py`.
- **Gate BDS-G05:** `make bds-schema-gate bds-services-gate`, plus `make tenders-services-gate` green after FU-25.

### Phase 6: Preparation services (definition-driven; the affected compositions finish on 1.2)
- Doctypes:
  - `Bid Section Response` (values keyed by response id, derived status and counts);
  - append-only `Bid Draft Change` (prior and new canonical value, actor, instant);
  - `Bid Evidence` (BDS-CHG-001 §4.7 plus the check result and Account source).
- Services:
  - `controls.py` (canonicalisers for every `CTL-*`, including controlled multi-select and the structured ports list);
  - `validation.py` (named `VAL-*`/`RQ-*` rules; `ValidateBidResponses`; Must fix versus Review note);
  - `handles.py` (D11);
  - `tasks.py` (`GetBidTask`);
  - `save.py` (`SaveBidTask`: version check, applicability recompute, the draft-version rule);
  - `evidence.py` (`UploadBidEvidence`, `LinkAccountEvidenceToBid`, replace, download tokens);
  - `scan_gateway.py` and `test_services/scanner.py`;
  - `addendum.py` (D10: five-value migration via `map_bid_definition_addendum`, acknowledgement, affected tasks);
  - `reads.py` (`GetMyBids`, `GetBidWorkspace`, `GetBidReview`; no side effects, never stamps `last_saved_at`);
  - `status.py` (Review and submit is Complete only with no Must fix).
- **Tests:**
  - `test_controls.py`, `test_validation_rules.py` (every declared capability is implemented);
  - `test_save_bid_task.py` (tampered, stale, hidden, inapplicable, invented options);
  - `test_evidence.py` (clean, infected, oversize, type, immutability);
  - `test_addendum_migration.py`, `test_reads_no_side_effects.py`;
  - `test_definition_fixture_roundtrip.py` (on 1.2: five tasks in order, 11 technical rows, reconciled counts);
  - `test_dto_leakage.py`.
- **Gate BDS-G06:** services green on 1.1 for unaffected compositions and on 1.2 for everything.

### Phase 7: Tender security, price and blind intake (OD-G/H)
- Doctypes:
  - `Tender Security Response` (kept in step by `SaveBidTask`; `physical_original_required`; derived receipt status visible only to the supplier);
  - `Tender Security Intake`: append-only; entered Tender reference, instrument type, issuer, instrument reference, amount and currency, received_at (not in the future), trusted `recorded_by`/`recorded_at`, before/after-deadline class, notes ≤500, confirmation, a system-issued **opaque** `intake_reference` (random, not a per-bid sequence), and `corrects` for append-only corrections;
  - `Tender Security Intake Match`: protected; no role permissions; never in any PE read.
- Services:
  - `price.py`: Decimal line and total calculations from the definition; rounding; rejects another currency, alternative prices, extra lines or discounts. The fixture 250 × 160,000 + 6,400,000 must equal 46,400,000.
  - `tender_security.py`: an outstanding original is a Review note, never a Must fix.
  - `security_intake.py`: `RecordPhysicalTenderSecurityReceipt` is re-scoped to blind intake. Only HOPF with the `tender_security_receipt` tag may record. It validates that the Tender exists and is published; the response shape is constant whether or not a bid matches.
  - `security_matching.py`: a private exact match on Tender + normalised instrument reference + issuer + amount. It runs on intake commit and on the supplier's security save. More than one match means no match, flagged for opening. Only the matched supplier's own reads show "recorded".
- Desk page `/desk/tender-security-receipts`:
  - `bid_submission/page/tender_security_receipts/…json`;
  - `public/js/tender_security_receipts_page.js` (one `kentender_core.desk_page.register(...)`, shared rail, `sidebarWorkspaceKey "procurement"`);
  - `public/js/tender_security_receipts/{bundle, TenderSecurityReceipts.vue, IntakeDialog.vue}`.
  - It shows the intake form plus Charles's own intake records, and nothing about bids.
  - It is not in `cl_surface_registry` (AGENTS.md section 6.5).
  - The three DES-15 labels are recorded as departures replaced by OD-G, with a design follow-up to redraw.
- **Tests:**
  - `test_price.py`, `test_tender_security.py`;
  - `test_security_intake.py`: HOPF only; others denied; boundary classes; immutable; identical response and timing shape with and without a match; no bidder facts in any PE DTO;
  - `test_security_matching.py`;
  - vitest `TenderSecurityReceipts.spec.js`;
  - Playwright `tests/ui/smoke/bid-submission/bds-security-intake.spec.ts`.
- **Gate BDS-G07:** `make ui-bds-security-intake-gate` and the services gate.

### Phase 8: Signature, submission, custody and availability
- Doctypes:
  - `Bid Submission Attempt`;
  - `Bid Submission Version` (immutable, BDS-CHG-001 §4.9);
  - `Tender Box Envelope` (non-content);
  - `Bid Receipt` (the BDS-CHG-001 §4.10 facts);
  - `Bid Submission Incident`;
  - Single `BDS Test Environment Controls`;
  - `Test Trust Certificate` (simulation).
- Services:
  - gateways (D6) and `availability.py` (D5);
  - `package.py` (`BuildCanonicalBidPackage`, deterministic canonical JSON);
  - `signature.py` (`PrepareBidSignature`; Check certificate);
  - `submission.py` (`SubmitBid` per D8; View status; `reconcile_uncertain_attempts` on `scheduler_events["all"]`);
  - `receipts.py` (print view and a PDF via `frappe.utils.pdf.get_pdf`);
  - `test_services/{trust,tender_box,time,controls}.py`.
- **Tests:**
  - `test_availability.py` (the flag × dependency matrix; nothing created; no API exposes the flag);
  - `test_signature.py` (valid, expired, revoked, wrong person, wrong organisation, wrong package, unavailable; typed name, image or checkbox rejected);
  - `test_submission.py`: before, at and after the deadline; accepted; definite rejection; uncertain then reconciled to one outcome; identical replay returns the same receipt; a changed payload under the same key gives `BDS_IDEMPOTENCY_CONFLICT`; concurrent submits give one Version;
  - `test_receipt.py`, `test_package_determinism.py`;
  - `test_confidentiality.py` (no values in logs or errors; package bytes never in the DB).
- **Gate BDS-G08.**

### Phase 9: Replacement, withdrawal, close and hand-off
- Doctypes: `Bid Submission Change`, `Bid Submission Close`, `Bid Opening Handoff`.
- Services:
  - `replacement.py` (`PrepareReplacementBid`; `SubmitReplacementBid` supersedes atomically; `BDS_REPLACEMENT_CONFLICT`);
  - `withdrawal.py` (reason of 10–500 characters, signatory only, `WD-…` acknowledgement, Start replacement from Withdrawn);
  - `close.py` (D9).
- **Tests:**
  - `test_replacement.py`;
  - `test_withdrawal.py` (9, 10, 500 and 501 characters; representative denied; `BDS_WITHDRAWAL_BLOCKED` after the deadline);
  - `test_close.py` (Drafts excluded; idempotent; no override path);
  - `test_opening_handoff_contract.py` (includes the intake inventory and matches; no content).
- **Gate BDS-G09.**

### Phase 10: Guidance, hand-offs, incidents and dead-end gate
- `bid_submission/services/`:
  - `guidance.py`: every BDS-CHG-001 §5.12 row; the BDS-CHG-001 §5.13 guards with figures and fixes; `since` from recorded instants; technical readers and cross-organisation masking;
  - `handoffs.py`: every BDS-CHG-001 §5.14 row, cleared on events and never on read;
  - `incidents.py`, `my_work_provider.py`.
- Wired into every read.
- **Tests:**
  - `test_guidance_rows.py` (exact headline, stage, markers, holder and primary action per BDS-CHG-001 §5.12 row);
  - `test_guards.py`;
  - `test_handoffs.py` (create and clear; optional replacement or withdrawal creates no My Work);
  - `test_dead_end_matrix.py` (states × {David, Mary, Peter, Grace, Guest, Charles, Brian, Naomi, Administrator, Daniel, Nadia, Amina} × reads) → `12_bid_submission/evidence/v0_8/dead_end_matrix.md`;
  - the Account-side matrix in ACC.
- **Gate BDS-G10:** `make bds-dead-end-gate`.

### Phase 11: Portal UI slices (vertical: API → screen → browser → fidelity at both sizes)
- Runtime completion:
  - the dialog and the 480 px response drawer (a full-width overlay at 390);
  - error summary, the "Leave without saving?" guard;
  - the CommonState view (copy from the server catalogue);
  - the test-environment strip.
- Frontend:
  - BDS: `kentender_procurement/public/js/bid_portal/{bid_portal.bundle.js, BidPortal.vue, screens/, components/, composables/{useRouteState,useGuidance,useNarrow,useLeaveGuard}.js, data/}`. The composition renderers are keyed on the definition's composition ids, never on board rows.
  - ACC: `kentender_suppliers/public/js/supplier_account_portal/{bundle, SupplierAccountPortal.vue, screens/{Register,Verify,Account}Screen.vue}`.
  - Vitest projects `bid-portal` and `supplier-account-portal`, added to `ui-structure-gate`.
- Fidelity infrastructure:
  - `tests/ui/fidelity/board.js` gains `bidSubmissionScope`: frame by width, strip captions and fold markers, map `.kt-guidance` to the journey and next-step markers.
  - `tests/ui/fidelity/departures/bid-submission.js` holds LABELS (including the odd combined, suffixed and dialog labels), DEPARTURES, COVERED and CONDITIONAL.
  - An inventory test: 79 = COVERED + CONDITIONAL (3) + REPLACED (DES-15 ×3).
  - Landmark spec: `tests/ui/smoke/design-fidelity/bid-submission-fidelity.spec.ts`.
- Slices, each with a `ui-bds-<slice>-gate`:

| Slice | Boards | Notes |
|---|---|---|
| 11.1 | DES-01 (+EMPTY) | Guest |
| 11.2 | DES-02 base, SIGNED-OUT, JV-START, DRAFT, SUBMITTED, CANCELLED, CANDIDATE-QUESTION | Guest, Peter, David, Mary; sign-in return-to-Tender |
| 11.3 | DES-03, -VERIFY | Mary (new) |
| 11.4 | DES-04, -ATTENTION, -VERIFY, -SUSPENDED | |
| 11.5 | DES-05 (+SUBMITTED, WITHDRAWN, EMPTY), DES-17 (+EMPTY, SUSPENDED) | |
| 11.6 | the 9 unconditional DES-06 labels | |
| 11.7 | DES-07 base, COMPLETE, QUESTION-OPEN/NONE, dialog and success, CLOSED, Queued, Sent, NOTICE | |
| 11.8 | DES-08 (+SECURITY, JV, ACCOUNT-UPDATE) | **after G03** |
| 11.9 | DES-09 (+ATTENTION, ADDENDUM, drawer) | **after G03** |
| 11.10 | DES-10 (+INCOMPLETE) | |
| 11.11 | the 6 DES-11 labels | **after G03** |
| 11.12 | the 9 DES-12 labels, including the confirmation dialog | **after G03** |
| 11.13 | DES-13 (+REPRESENTATIVE, CLOSED) | |
| 11.14 | DES-14 (+REPLACED, withdrawal dialog, WITHDRAWN) | |
| 11.15 | DES-16: every live common state against its catalogue cell | grows with each slice |

- **Slice definition of done (AGENTS.md sections 6.7 and 6.10, BDS BDS-CHG-001 §11):**
  - component structure tests at both sizes;
  - a single-worker Playwright journey per actor, including Peter's cross-organisation masking and absence assertions (no Submit for David);
  - direct load, reload and back/forward;
  - a forced 500 and a stale write;
  - inline errors with no Message dialog;
  - 390 px, 200% zoom, keyboard and focus;
  - the leakage scan;
  - zero console errors;
  - the bundle hash changed (touch `hooks.py` after CSS);
  - PNGs in `12_bid_submission/evidence/v0_8/`.
- **Gate BDS-G11:** every slice gate plus `make ui-bds-fidelity-gate`.

### Phase 12: Seeds, worlds and release evidence
- `kentender_core/seeds/canonical.py`:
  - add `"bid_submission"` to STAGES;
  - supplier register users;
  - `@afyadigital.example`, `@kisiwadigital.example` and the Jua domain added to the fixture domains;
  - clear hooks call `bid_submission/seeds/clear.py` and `supplier_accounts/seeds/clear.py` (via `kentender_core/utils/raw_delete.py`).
- `seeds/site_setup.py`: the new internal actors and assignments.
- The Tenders canonical fixture is refactored into dated steps (D19). Its validator facts are preserved and the candidate now comes from BDS.
- `supplier_accounts/seeds/kentender_mvp_v1.py` and `bid_submission/seeds/kentender_mvp_v1.py` (`upsert_…`, `validate_…`, `reset_…`) follow BDS-CHG-001 §13.3 exactly as the named actors under `clock.at`, with simulation labels.
- Playwright worlds: `playwright_ui_fixtures.py` in both modules (`ensure_world`, `restore_site`, a reset per BDS-CHG-001 §13.4 fixture, test clock), registered in `tests/ui/globalTeardown.ts`. TND-034 (cancelled) and TND-041 (withdrawal) are built through the Tenders resets.
- `tests/ui/smoke/bid-submission/bds-release-evidence.spec.ts`: the full BDS-CHG-001 §13.3 persona pass, with the Tenders steps driven by Brian and Charles in Desk, Peter's denial, Naomi's read and Administrator's technical read, at 1440, 390 and 200%.
- Deliverables: the evidence PNG pack, the AC traceability matrix, and `12_bid_submission/RUNBOOKS.md` (enabling simulation, scheduler dependence, uncertain-attempt reconciliation, the production-switch checklist).
- Owner-evidence rows (BDS01-IMP-053/054/055/076/086/087/089, BDS-CHG-001 §15.3–15.6) are recorded as "Blocked — owner".
- **Gate BDS-G12:**
  - `make seed-canonical SITE=kentender.midas.com THROUGH=bid_submission REBUILD=True` run twice, plus `seed-canonical-validate`;
  - `make ui-bds-release-evidence-gate`;
  - `make ui-industry-design-gate ui-structure-gate artboard-provenance-gate`.

### Phase 13 (gated): TPR v0.13 branch
- **Entry:** TPR v0.13 approved.
- Extend D4 to the full BDS-CHG-001 §4.4.4 matrix and add the Brian Wafula BDS-CHG-001 §5.12 row.
- Move DES-02-SUPERSEDED, DES-02-WITHDRAWN-RELEASE and DES-06-WITHDRAWN-RELEASE to COVERED.
- **Closes:** BDS08-IMP-006, BDS08-AC-008.

## Conflicts and follow-ups to log (Phase 0)

- **Spec vs owner decisions:**
  - BDS-CHG-001 §10.16/DES-15 and BDS-CHG-001 §6 versus OD-G/H (blind intake);
  - BDS-CHG-001 §7.2 has no suspend/restore command (OD-D);
  - BDS-CHG-001 §13.2 Alice Njeri → Naomi Chebet;
  - Daniel Otieno is not the Administrator login;
  - BDS-CHG-001 §5.14 supplier My Work versus Desk-only My Work (D15);
  - the reduced tracker's board wording.
- **Spec vs repo:** KT-STD BDS-CHG-001 §4's "register in `cl_surface_registry`" loses to AGENTS.md section 6.5; `/app/std-templates/…` should be `/desk/std-templates/…` on Frappe 16.
- **Fixtures:**
  - DES-06 Updated times versus the BDS-CHG-001 §13.3 draft-version count, and registration capturing Mary's signatory role before her 09:30 assignment. Treat these as artboard-only facts (KT-STD BDS-CHG-001 §8.7).
  - The Tenders notice times (TPR FU-28).
- **Residuals for the production gate:**
  - Administrator's DB bypass on Draft and working-copy rows (BDS-CHG-001 §12.3.2);
  - an approved malware scanner in the BDS-CHG-001 §5.10 profile;
  - per-Tender reference sequences revealing counts (BDS-CHG-001 §8/BDS-CHG-001 §12).
- **CFG:** the Supplier portal UI is built without an artboard, ahead of v0.16 approval.
- **TM2 remainder** clean-up (OD-F).

## Risks

- **The portal runtime is new platform code.** CSS isolation, translations without Desk boot, and bfcache all need proving. Mitigation: the 2C walking skeleton with computed-style and console gates before any slice.
- **Template reconciliation (Phase 3) may need owner-authored STD-TPL-001 text.** Mitigation: stop and raise it; unaffected slices continue.
- **Seed interleaving touches the approved Tenders world.** Mitigation: keep its validator facts; add Tenders tracker rows; a dry run first.
- **Confidentiality residuals could be misread as compliance.** Mitigation: simulation labels everywhere, and no claims in the release evidence.
- **Verification surface** (152 frames, ~30 worlds, queue overload). Mitigation: per-slice gates, `make ui-queue-check`, no concurrent Python and Playwright runs, and `bench run-tests` treated as persistent (purge after).

## Verification

```bash
cd /home/midasuser/frappe-bench/apps/kentender_v1 && make help            # confirm target names
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.bid_submission.tests.test_start_bid
bench --site kentender.midas.com run-tests --app kentender_suppliers --module kentender_suppliers.supplier_accounts.tests.test_verification
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tenders.tests.test_bidder_projection
bench --site kentender.midas.com run-tests --app kentender_core --module kentender_core.tests.test_public_portal_settings
bench --site kentender.midas.com migrate                                    # after any new DocType/Page JSON
./scripts/bench-with-node.sh build --apps kentender_core,kentender_procurement,kentender_suppliers   # confirm bundle hash changed
cd apps/kentender_v1
make bds-retirement-gate cfg-portal-settings-gate supplier-accounts-services-gate bds-services-gate bds-dead-end-gate SITE=kentender.midas.com
make tenders-services-gate artboard-provenance-gate ui-industry-design-gate ui-structure-gate
make ui-queue-check && npx playwright test --workers=1 tests/ui/smoke/bid-submission/<slice>.spec.ts
make ui-bds-fidelity-gate ui-bds-release-evidence-gate
make seed-canonical-dry-run SITE=kentender.midas.com
make seed-canonical SITE=kentender.midas.com THROUGH=bid_submission REBUILD=True && make seed-canonical-validate SITE=kentender.midas.com
```

The live check at close is a browser run of the BDS-CHG-001 §13.3 journey:
1. Mary registers and verifies.
2. David starts, asks a question, acknowledges the addendum and completes the five tasks.
3. Charles records the blind intake, and Mary's bid shows it recorded.
4. Mary submits and receives a receipt.
5. The bid is replaced, and a separate one withdrawn.
6. The scheduler closes the box, and the Bid Opening hand-off holds only envelope, lineage, custody and intake facts.
7. Peter is masked throughout.
8. Administrator sees metadata only.

## Phase 0 findings (26 Sep 2026)

These refine the phases above. They are recorded here, and the phase text is not rewritten.

- **Legacy scope** (`reconciliation/legacy_inventory.md`):
  - The `tender_configurations` bid slice is its whole bidder workspace: the eight bid services plus about 13 bidder-section services that import them, the bid endpoints in its `__init__.py`/`api.py`, and about 30 tests.
  - The TM2 **bid doctypes are not dropped in Phase 1**: TM2's officer workbench still reads them, so they go with the OD-F clean-up.
  - `e1-nssf-*` and `bw-manifest-*` gates exercise kept BWMF code and stay.
- **Template reconciliation** (`reconciliation/definition_to_board_matrix.md`):
  - Most board content traces to the release 1.1 definition, including the group `published_facts`.
  - Class A gaps for release 1.2: per-obligation warranty/support responses, a security `valid_until` response, and structured JV members.
  - Board omissions to build from the definition, with a design follow-up: CBQ, year of registration, experience reference and value, acceptance confirmations, Form of Tender responses.
  - Four decisions: the task-1 label (STD-TPL-001 v0.10 §8.1 against BDS-CHG-001 v0.8 §5.3), document acknowledgement, splitting the eligibility documents, and the final confirmation wording.
- **Fixtures** (`reconciliation/fixture_chronology.md`): conflicts FX-1…FX-6. The canonical Tenders timeline interleaves cleanly with the BDS BDS-CHG-001 §13.3 instants; the Tenders stand-in step `CLOCK["candidate"]` (19 May 09:20) is replaced by `StartBid`.
- **Error contract** (`reconciliation/error_contract.md`): 34 codes, which supersedes the v0.4 tracker's 27.
- **Artboards** (`reconciliation/artboard_inventory.md`): 73 Covered, 3 Conditional (TPR v0.13), 3 Replaced (DES-15, OD-G).
