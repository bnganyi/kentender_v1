# BDS-CHG-001 v0.4 — Supplier and Electronic Bid Submission — tracker

**Authority:** `KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_4.md` (18 September 2026; status "Proposed for Project Owner review"; implementation authority "None until Project Owner approval and satisfaction of the production gates in §§5.10 and 15").
**Companions:** `BDS-CHG-001_Implementation_Plan.md` (decision register D1–D19, conflict register C1–C11, phase sequence, module layout, UI slice table, slice gate, owner questions OQ-1…OQ-10), `BDS-CHG-001_FOLLOW_UPS.md`, `design/*.dc.html` (16 boards + narrow-width duplicates), `evidence/v0_4/` (from Phase 9), `RUNBOOKS.md` (authored at Phase 9).
**Supersedes-in-tracking:** Nothing — no prior BDS-CHG-001 cycle exists. This tracker retires two **unrelated** legacy code bodies (`tender_configurations`'s bid-submission slice, `tender_management`/TM2) as Phase 1 work; see the plan's §3 Retirement register for their own history, which this tracker does not restate.
**Status:** Phase 0 substantively closed 21 September 2026 (gate BDS-G00 **Partial** — only two trivial file-hygiene actions remain, neither blocking). All ten owner questions resolved (plan §11). Two real findings from this pass changed scope: the `IT-EQUIPMENT-OPEN-V1` template bundle is document-rendering only and needs a new structured response-definition register authored before Phase 3's binding work (plan D7/D20, new row BDS-301); the portal architecture (plan D3) now reuses several genuine Frappe mechanisms (registration, auth-redirect, record scoping, the generator pattern for two screens) rather than building everything from scratch, narrowing — not eliminating — the net-new client runtime. No product code changed. Site untouched.
**Started:** 21 September 2026.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed. A row that is honestly incomplete is `Partial`, never `Done`.
3. A row touching a file that still references a prohibited concept is not `Done`. Prohibited here: `Electronic Bid Submission`, `IT Bid Opening Record`, `Electronic Bid Audit Event`, `tm2_bid_*`, `TM2 Tender`, any literal `Tender Configuration`/`IT Tender Publication Record` reference from new Bid Submission code (the retired slice, not the kept-but-out-of-scope BWMF system itself, which legitimately keeps its own name), a `KTSM Supplier Profile`/`Supplier` reference from `Bidder Account` code (D2/C10 — these are deliberately separate doctype families), `User Responsibility Assignment` used as the authority source for a bidder-side command (D16 — bidder authority is never resolved through the internal Assignment model), a raw Frappe Message/`frappe.msgprint` dialog for user-correctable portal input, `vue-router` or any client-side router dependency, a homemade certificate authority/signature/encryption/tender-box implementation, a hard-coded `bds_operating_profile_approved` truthy value outside the seed/test fixture path or `site_config.json`, a schema/digest/manifest/renderer key ever rendered to a bidder, `/desk/tender-security-receipts` (the corrected route is `/app/tender-security-receipts`, C8).
4. Spec §10 (boards + §10.1) governs visual/content fidelity; §11 governs behaviour; §8 governs error copy (re-extracted verbatim at Phase 0, OQ-10); §12 governs audit; §13 governs seeds. Board structure is literal per D19 (both 1440×1024 and 390×844); every literal the browser asserts comes from §10.1/§13, never from a board's placeholder data.
5. Every visible action maps to exactly one §7 command; no new command, status, role, queue or approval stage beyond §7/§6 plus this plan's own D-decisions (which are themselves recorded, not invented ad hoc).
6. Never run any Bid Submission or Bidder Accounts Python test module while a Bid Submission Playwright process is active on the site. After any Python run touching either app, repeat the canonical-seed repair sequence used by every prior module before reseeding.
7. The AC map closes a row only with the test/spec/observation that proves it; the one genuine owner-evidence row (§15.3's independent security review, and any representative-user sign-off) is closed only by the owner's recorded decision, never by code.
8. **Production-gate discipline**: no work register row may claim `Done` for `SubmitBid`/`SubmitReplacementBid` behaviour by exercising the production path — every proof in this tracker runs against `Bid Submission Settings.operating_profile_approved = 0` and the `Test Trust Service`/`Test Tender Box` doubles, and says so in its evidence.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-21 | D1–D19 recorded in the plan; OQ-1…OQ-10 defaults apply until vetoed. | Plan §4, §11. |
| 2026-09-21 | Identity (Bidder Account family) placed in `kentender_suppliers`; bid domain (Bid Workspace family) placed in a new `kentender_procurement.bid_submission` module. | CLAUDE.md app-ownership map; plan D1. |
| 2026-09-21 | Retirement scope bounded to `tender_configurations`'s bid-submission slice + all of `tender_management`/TM2; BWMF/STD-wizard machinery explicitly excluded. | Plan D4, C9; legacy-audit research recommendation. |
| 2026-09-21 | Portal built as Frappe Website pages with a new `kentender_core.bid_portal_page` shared runtime, no client router. | Plan D3; no existing finished public-frontend convention found in this repo. |
| 2026-09-21 | `BuildPublishedBidDefinition`/`MapBidDefinitionAddendum` do not exist in the current Tenders module and are added to it in Phase 3, not waited for as an external dependency. | Plan D7, C7; direct source inspection. |
| 2026-09-21 | **Owner**: production `Submit bid` gate simplified to one plain site-config flag reusing the spec's own `BDS_SUBMISSION_SERVICE_UNAVAILABLE` message — confirmed a deployment concern only, not a build-process gate. Old bid-submission records confirmed safe to delete outright. Template wizard confirmed already deprecated, left untouched. Portal to be built fresh, checking Frappe's own portal conventions first. All remaining open items delegated to plan-owner judgment after fresh code/requirements study. | Owner direction, this session; plan D15 (revised), retirement register (confirmed), D4/FU-05 (confirmed), D3 (revised). |
| 2026-09-21 | Follow-up research: `IT-EQUIPMENT-OPEN-V1` bundle confirmed document-rendering only, no structured response/evaluation/contract-mapping data. Frappe's own `sign_up()`, `has_website_permission`, the `redirect-to` login pattern, and the `WebsiteGenerator` list+detail mechanism confirmed reusable for parts of the portal (D3/D16 revised); confirmed nothing in Frappe/ERPNext mounts a JS framework into a public page, so the shared client runtime is still needed for the interactive bid-preparation flow specifically. Full 27-code `BDS_*` error contract extracted verbatim (below). | Three-agent research pass, this session (frappe-portal-patterns, std-tpl-bundle-content, spec-error-codes). |
| 2026-09-21 | **Owner**: the response-definition register is independent work, a bigger slice of scope than bid submission and not owned by this module. Checked STD-TPL-001 v0.6 §9-10 directly (not assumed) — confirmed no approved version defines this register either; this is genuinely new STD-TPL-001 scope, distinct from the already-complete Version 1.1 delta (gate `TPL-G07`). Spun out to STD-TPL-001's own tracker as a proposed "Version 1.2 delta" (new gate `TPL-G08`, `Blocked — owner`), with a full content proposal drafted and handed over. BDS-301 (below) revised from an authored work item to a cross-reference and blocking-dependency note; Phase 3's own gate `BDS-G03` is blocked on `TPL-G08`. | Owner direction, this session; STD-TPL-001's own plan/tracker now carry this work (`docs/mvp-1-r1/07_std_configuration/`). |

## Gate register

| Gate | Condition | Status | Evidence |
|---|---|---|---|
| BDS-G00 | Phase 0 docs, retirement inventory, design verification, owner questions | **Partial** | Plan/tracker/follow-ups authored and fully updated 2026-09-21 (BDS-001…BDS-004, BDS-006 Done). Only BDS-005 (physically relocating the stray design upload) remains an unexecuted mechanical action — decided, not blocking, not yet done. |
| BDS-G01 | Retirement complete: zero references outside retired history; migrate clean ×3; demo-seed dependency replaced | Planned | — |
| BDS-G02 | Bidder identity + authorization foundation | Planned | — |
| BDS-G03 | Tenders-side contracts + publication materialisation | **Blocked — external** | Cannot start until STD-TPL-001's own gate `TPL-G08` clears (see BDS-301) — that work is owned and tracked entirely outside this module. |
| BDS-G04 | Bid preparation services | Planned | — |
| BDS-G05 | Tender security, price & internal Desk slice | Planned | — |
| BDS-G06 | Signature, submission & custody services | Planned | — |
| BDS-G07 | Replacement, withdrawal, closing & Bid Opening handoff | Planned | — |
| BDS-G08 | Portal UI: every slice 8a–8p passes the slice gate; fidelity gate at both render sizes | Planned | — |
| BDS-G09 | Seeds, worlds & release evidence | Planned | — |

## Work register — Phase 0: docs, retirement inventory, design verification, owner questions

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-001 | Author plan (D1–D19, C1–C11, phase sequence, module layout, UI slice table, slice gate, OQ-1…OQ-10), this tracker (gates, work register, AC map, board map), follow-ups | Done | 2026-09-21. `BDS-CHG-001_Implementation_Plan.md`, `BDS-CHG-001_IMPLEMENTATION_TRACKER.md`, `BDS-CHG-001_FOLLOW_UPS.md` under `docs/mvp-1-r1/12_bid_submission/`. Preceded by a six-agent research pass covering the spec (full text), the design board (full file), a legacy-code audit, the current Tenders module's actual contracts, five sibling authority documents, and the sibling trackers' document format — findings folded directly into the plan's Baseline facts, Decision register and Conflict register. |
| BDS-002 | Verify `IT-EQUIPMENT-OPEN-V1` release 1.1 content against every §4.4.2 definition unit (task/group/response-row/evidence-rule/evaluation-mapping/contract-mapping, exact renderer version) | Done | 2026-09-21. Every file in the bundle read in full (`metadata.json`, `source_record.json`, `forms_register.csv`, `insertion_points.csv`, `coverage_register.csv`, `MANIFEST.sha256`, fixtures, `loader.py`/`registry.py`/`renderer.py`/`checks.py`). **Verdict: insufficient as-is** — the bundle is a document-rendering system only (requirement-level IDs and an `evidence_required` boolean exist; response-row identity, response types, applicability rules as data, declaration texts as entities, and every evaluation/contract mapping are absent, confirmed by grep and by reading the actual evaluation clause). Consequence: a new structured response-definition register must be authored inside `tender_templates` before Phase 3's binding work — new row BDS-301, plan D7/D20/C12. |
| BDS-003 | Re-extract spec §8 (error contract) verbatim | Done | 2026-09-21. Full §8 (spec lines 589–619) read and cross-checked against a whole-document grep for `BDS_` — one single canonical table, 27 codes, no others found anywhere else in the document. Complete table recorded below under "Error contract." |
| BDS-004 | Confirm design board labelling convention; decide `kt-notice is-info` disposition | Done | 2026-09-21. Labelling convention confirmed: no `data-screen-label` attribute exists anywhere in the file; screens are labelled by `id="desNN"` + a following `.text-muted` heading div — the Phase 8 fidelity spec must key on that pattern. `kt-notice is-info` (9 uses, no matching CSS rule, falls back to base `.kt-notice`) — **disposition decided: add the missing `.kt-notice.is-info` rule to `kt_industry_tokens.css`** (the design intent, not the accidental fallback, is authoritative). Not yet executed — a one-line CSS addition, tracked at Phase 8's start rather than blocking Phase 0. |
| BDS-005 | Relocate or flag the stray Departmental Needs design export nested at `design/uploads/design/` | Planned | Identified (2026-09-21): a complete, unrelated `Departmental Needs - Design Board.dc.html` export plus its own `_ds` bundle and two NDS spec markdown files sit three levels deep inside this module's design-upload folder. Disposition decided (delete/relocate); not yet executed — pure file hygiene, does not block Phase 1. |
| BDS-006 | Confirm legacy `Electronic Bid Submission`/`IT Bid Opening Record`/`tm2_bid_*` rows are safe to drop; record OQ-1…OQ-10 resolutions | Done | 2026-09-21. **Owner confirmed directly: delete outright, no migration path needed** — supersedes the originally-planned row-count check. OQ-1…OQ-10 all resolved, see plan §11. |

## Work register — Phase 1: retire legacy bid-submission surface

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-101 | Patch `bds_chg_001_retire_bid_configurations`: delete `Electronic Bid Submission`/`IT Bid Opening Record`/`Electronic Bid Audit Event` and the four `tm2_bid_*` doctypes (children before parents), Page `bid-submissions`, Page `it-electronic-bidder-workspace` | Planned | — |
| BDS-102 | Delete `tender_configurations/services/{electronic_bid,bid_submissions,bid_evidence,bidder_presentation,bid_issues,bidder_submission_schema,price_schedule_bidder,final_submission}.py` and their tests, after reading them once for Phase 4–7 design input (D5) | Planned | — |
| BDS-103 | Delete `www/tenders/{submit_bid,final_bid_review}` and the whole bidder-workspace route family; delete the whole `tender_management`/TM2 package and `www/supplier/tenders/`; remove all corresponding `hooks.py` `website_route_rules`/`page_js`/`app_include_js` entries | Planned | — |
| BDS-104 | Delete `public/js/{electronic_bid/bidder_workspace_renderer,bid_submissions_page,kt_bidder_countdown,it_electronic_bidder_workspace_page}.js`, `public/css/{bid_submissions_page,bidder_portal_forms}.css`, `templates/includes/{kt_bidder_workspace_sidebar,kt_bidder_portal_nav}.html` | Planned | — |
| BDS-105 | Replace `kentender_core/seeds/demo_platform_seed/{transitions,actionable}.py`'s direct import of `tender_configurations.services.bid_submissions` with a safe skip stub (matching the `demand_to_bidder_journey_sample.py` precedent) | Planned | — |
| BDS-106 | Update the `Bid Opening` Workspace placeholder tile's content (link deferred to Phase 5 once `/app/tender-security-receipts` exists) | Planned | — |
| BDS-107 | Exit: `bench migrate` clean ×3; repo-wide grep for the retired doctype/service names outside history returns zero; `bench console` confirms zero orphaned rows | Planned | — |

## Work register — Phase 2: bidder identity & external-actor foundation (`kentender_suppliers`)

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-201 | `kentender_suppliers` module "Bidder Accounts": `Bidder Account`, `Bidder User Assignment`, `Bidder Arrangement` doctypes (D2); schema test with planted-violation proof | Planned | — |
| BDS-202 | `services/registration.py`: `RegisterSupplierOrganisation`, `SendAccountVerification`, `VerifyAccountCommunication`, `UpdateSupplierOrganisation` — §5.2's 7 guard rules, §4.1's field set, "not qualification" disclosure text | Planned | — |
| BDS-203 | `services/assignment.py`: `AssignSupplierRepresentative`, `AssignAuthorisedSignatory` — authority evidence + effective window, active-organisation context for multi-org users | Planned | — |
| BDS-204 | `services/bidder_authorization.py` (D16): resolves active Bidder User Assignment + non-Suspended Account for the current Website User, independent of `User Responsibility Assignment` | Planned | — |
| BDS-205 | `services/bidder_identity_gateway.py` (D1, cross-app-facing) + `test_gateway_contracts.py` pinning its signature for `kentender_procurement.bid_submission` to consume | Planned | — |
| BDS-206 | `make bidder-accounts-schema-gate` (schema + registration + assignment + authorization) | Planned | — |

## Work register — Phase 3: STD response-definition authoring, Tenders-side contracts, publication materialisation

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-301 | **External dependency, not BDS-CHG-001-owned work**: confirm STD-TPL-001's "Version 1.2 delta" (its own tracker, gate `TPL-G08`) has shipped a released `IT-EQUIPMENT-OPEN-V1` response-definition register before any binding work below (BDS-302 onward) begins. | **Blocked — external** | 2026-09-21. Owner direction: this is independent work, tracked entirely in `STD-TPL-001_IMPLEMENTATION_TRACKER.md` (its own "Version 1.2 delta" block, work rows TPL-801…TPL-803). A complete content proposal was drafted directly from the approved bundle's own source and handed over as `docs/mvp-1-r1/07_std_configuration/STD-TPL-001_Bid_Response_Definition_Proposal_IT-EQUIPMENT-OPEN-V1.md` (9 declaration units, 11 technical rows, warranty/comparable-experience/evidence content, tender security, simplified price schedule, each with evaluation/contract mapping — three flagged decisions awaiting the STD-TPL-001 owner's confirmation). This row closes only when `TPL-G08` clears and the register is released — do not duplicate that work here. |
| BDS-302 | Add `BuildPublishedBidDefinition`/`MapBidDefinitionAddendum` to `kentender_procurement.tenders.services` (D7), binding BDS-301's new register; addendum rows filed in Tenders' own tracker (OQ-3) | Planned | — |
| BDS-303 | `bid_submission.services.tenders_gateway.py`: `GetPublishedTenderForBidder` (D8) — redacted read over Tenders' existing `get_submission_handoff()`; contract test pinning the redaction | Planned | — |
| BDS-304 | `services/product_profile.py`: `ResolveBidProductProfile` — code-owned registry, `IT-EQUIPMENT-OPEN-V1` only, fails closed on unknown input | Planned | — |
| BDS-305 | `Published Bid Definition` doctype + `services/definition.py` — the §4.4.4 nine-step publication-materialisation check, tested against the now-complete `IT-EQUIPMENT-OPEN-V1` release (BDS-301 + BDS-002) | Planned | — |
| BDS-306 | `CreateBidderArrangement`, `StartBid` — atomic arrangement + definition binding; §5.11 invariants 1 and 12 (one active workspace, concurrent-start safety) as named tests | Planned | — |
| BDS-307 | `make bid-submission-schema-gate` (schema + gateway contracts + product profile + definition materialisation) | Planned | — |

## Work register — Phase 4: bid preparation services

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-401 | `Bid Workspace`/`Bid Section Response`/`Bid Evidence` doctypes | Planned | — |
| BDS-402 | `SaveBidTask` — type/option/applicability/multiplicity/calculation/evidence/record-version enforcement; unknown/hidden/inapplicable rejection (§4.4.5) | Planned | — |
| BDS-403 | `UploadBidEvidence`, `LinkAccountEvidenceToBid` (delegates to `kentender_core.file_integrity`, D12) | Planned | — |
| BDS-404 | `AcknowledgeTenderDocument`, `RefreshBidForAddendum` — explicit unchanged/changed/removed/new identity map (§4.4.6), no text/position/similarity migration | Planned | — |
| BDS-405 | `ValidateBidResponses` — readiness derivation for the five-task Goods/IT composition, reused by task save, review and final submission (§5.3, §5.7 rule 1) | Planned | — |
| BDS-406 | `make bid-submission-services-gate` extended with Phase 4 modules | Planned | — |

## Work register — Phase 5: tender security, price & internal Desk slice

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-501 | `Tender Security Response` fields + validation (§4.8, §5.5) | Planned | — |
| BDS-502 | `RecordPhysicalTenderSecurityReceipt` — internal command, Head of Procurement Function + `tender_security_receipt` sod_tag (D10), no Draft/bid-content read | Planned | — |
| BDS-503 | `services/price.py` — server-side Decimal arithmetic/rounding/totals (§5.6), read-only quantity/unit/currency, Form of Tender total projection | Planned | — |
| BDS-504 | Page `tender-security-receipts` at `/app/tender-security-receipts` (C8) — standard `kentender_core.desk_page.register()` pattern, `ChannelTable`-equivalent read-only queue + `Record dialog` | Planned | — |
| BDS-505 | `make ui-tender-security-receipts-gate` | Planned | — |

## Work register — Phase 6: signature, submission & custody services

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-601 | `trust_service_gateway.py`/`custody_service_gateway.py` interfaces + `Test Trust Service`/`Test Tender Box` implementations (D6) | Planned | — |
| BDS-602 | One-line production-gate check in `SubmitBid`/`SubmitReplacementBid` reading `frappe.conf.get("bds_operating_profile_approved", False)` (D15, simplified); returns the spec's own `BDS_SUBMISSION_SERVICE_UNAVAILABLE` when False outside the seed/test fixture path — no new doctype, no new error code | Planned | — |
| BDS-603 | `BuildCanonicalBidPackage` — server-assembled only, no client-supplied package/schema/total trusted | Planned | — |
| BDS-604 | `PrepareBidSignature`, `SubmitBid` — server re-validation immediately before signing and before deposit; deadline check inside the committing transaction; idempotency-key replay handling | Planned | — |
| BDS-605 | `Bid Submission Version`/`Tender Box Envelope`/`Bid Receipt` doctypes; atomic Submitted-state + receipt commit only after custody acceptance | Planned | — |
| BDS-606 | Named tests for every integrity/concurrency case analogous to Tenders' own §15.3 register (committed-before-screen ordering; identical replay idempotent; changed-payload-same-key conflict; a definitive custody rejection leaves the Draft unchanged; an uncertain result shows Confirmation pending and reconciles to one outcome; two concurrent finals resolve to one Version) | Planned | — |

## Work register — Phase 7: replacement, withdrawal, closing & Bid Opening handoff

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-701 | `PrepareReplacementBid`/`SubmitReplacementBid` — predecessor supersession atomic with acceptance; abandoned replacement leaves the prior Version current | Planned | — |
| BDS-702 | `WithdrawBid` + `Submission Change` — active Authorised Signatory, exact current Version, reason 10–500 chars, trusted pre-deadline time, electronic acknowledgement | Planned | — |
| BDS-703 | `CloseBidSubmission` — system/tender-box-owner actor only, hourly scheduler job, idempotent per Tender, never-submitted Drafts → Closed without submission | Planned | — |
| BDS-704 | Bid Opening handoff contract — closed-box identity, sealed envelope identities, submission/withdrawal lineage, custody proofs; no content, no decrypt command; consumer contract pinned by test only (no real Bid Opening module exists yet) | Planned | — |
| BDS-705 | `make bid-submission-services-gate` full run (Phases 4–7 combined) | Planned | — |

## Work register — Phase 8: portal UI

| ID | Slice | Status | Evidence |
|---|---|---|---|
| BDS-801 | 8a — `kentender_core.bid_portal_page` shared runtime + BDS-DES-01 Available Tenders (incl. EMPTY variant, signed-out) | Planned | — |
| BDS-802 | 8b — BDS-DES-02 Published Tender overview (SIGNED-OUT/JV-START/DRAFT/SUBMITTED/CANCELLED) | Planned | — |
| BDS-803 | 8c — BDS-DES-03 Register supplier organisation (+ VERIFY) | Planned | — |
| BDS-804 | 8d — BDS-DES-04 Supplier/Bidder Account (+ ATTENTION/VERIFY) | Planned | — |
| BDS-805 | 8e — BDS-DES-05 My bids (SUBMITTED/WITHDRAWN/EMPTY) | Planned | — |
| BDS-806 | 8f — BDS-DES-06 Bid workspace (IN-PROGRESS/ADDENDUM/REPRESENTATIVE) | Planned | — |
| BDS-807 | 8g — BDS-DES-07 Tender documents and addenda (COMPLETE/NONE) | Planned | — |
| BDS-808 | 8h — BDS-DES-08 Company, declarations and tender security (SECURITY/JV) | Planned | — |
| BDS-809 | 8i — BDS-DES-09 Requirements and supporting evidence (response drawer, ATTENTION/ADDENDUM) | Planned | — |
| BDS-810 | 8j — BDS-DES-10 Price (INCOMPLETE) | Planned | — |
| BDS-811 | 8k — BDS-DES-11 Review bid (EVIDENCE-ATTENTION/ADDENDUM-ATTENTION/REPRESENTATIVE) | Planned | — |
| BDS-812 | 8l — BDS-DES-12 Submit bid (confirm dialog, PENDING/SIGNATURE/SERVICE unavailable) | Planned | — |
| BDS-813 | 8m — BDS-DES-13 Submission receipt (CLOSED) | Planned | — |
| BDS-814 | 8n — BDS-DES-14 Replacement and withdrawal (withdraw dialog, REPLACED/WITHDRAWN) | Planned | — |
| BDS-815 | 8o — BDS-DES-16 Common states (16-state catalogue, shared across all slices) | Planned | — |
| BDS-816 | 8p — Narrow-width (390×844) fidelity sweep across every slice (D19); `make ui-bid-submission-fidelity-gate` | Planned | — |

## Work register — Phase 9: seeds, worlds & release evidence

| ID | Item | Status | Evidence |
|---|---|---|---|
| BDS-901 | Canonical `bid_submission` seed stage (D18): `STAGES`/`BID_SUBMISSION_NS` in `canonical.py`; `upsert_bid_submission` through the full §13.3 timeline with an injected clock; `validate_bid_submission_seed()`; idempotent on a second run | Planned | — |
| BDS-902 | Playwright world: 20 §13.4 isolated fixture profiles, each built through real commands; `restore_site`/`globalTeardown` entries | Planned | — |
| BDS-903 | `bds-release-evidence.spec.ts` — the whole §13.3 lifecycle as David/Mary/Charles/Naomi, single-worker, against Test Trust Service/Test Tender Box | Planned | — |
| BDS-904 | Evidence pack: every board + named variant → PNG at both 1440×1024 and 390×844 in `evidence/v0_4/` | Planned | — |
| BDS-905 | Targeted asset build (`kentender_procurement` + `kentender_suppliers`), bundle-hash confirmation; `make ui-industry-design-gate`; prohibited-token scan (tracker rule 3) | Planned | — |
| BDS-906 | `RUNBOOKS.md` authored; AC map closed truthfully; `BDS-CHG-001_FOLLOW_UPS.md` updated; memory updated | Planned | — |
| BDS-907 | Owner evidence: §15.3 independent security/penetration review; any representative-user sign-off | Planned — owner | — |

## Board map

| Label | Slice | Notes |
|---|---|---|
| BDS-DES-01 Available Tenders | 8a | Public, unauthenticated |
| BDS-DES-02 Published Tender overview | 8b | Incl. JV-START dialog-card (560px, `.dialog-title`/`.dialog-actions` styling, not a real `.dialog`) |
| BDS-DES-03 Register supplier organisation | 8c | |
| BDS-DES-04 Supplier Account | 8d | |
| BDS-DES-05 My bids | 8e | |
| BDS-DES-06 Bid workspace | 8f | |
| BDS-DES-07 Tender documents and addenda | 8g | |
| BDS-DES-08 Company, declarations and tender security | 8h | |
| BDS-DES-09 Requirements and supporting evidence | 8i | Incl. response-drawer card (400px, `.dialog-title`/`.dialog-actions` styling, not a real `.dialog`) |
| BDS-DES-10 Price | 8j | |
| BDS-DES-11 Review bid | 8k | |
| BDS-DES-12 Submit bid | 8l | Real `.dialog`, 520px — "Submit this bid?" |
| BDS-DES-13 Submission receipt | 8m | |
| BDS-DES-14 Replacement and withdrawal | 8n | Real `.dialog`, 520px — "Withdraw this bid?" |
| BDS-DES-15 Record physical tender-security receipt | Phase 5 | Internal Desk shell, real `.dialog` 520px; the only board not in the portal |
| BDS-DES-16 Common states | 8o | 16-state catalogue, no persona |
| `#narrow` (390×844 derivatives) | 8p | Hand-built duplicate of all 16 screens, not a CSS breakpoint (D19) |

No rotation/mislabeling found in this board (unlike the Tenders precedent's C1) — every `id="desNN"` anchor is unique and matches its heading label. **No `data-screen-label` attribute exists** — the fidelity spec keys on the `id`+heading pattern (BDS-004).

## Error contract (spec §8, verbatim — extracted 2026-09-21)

All 27 codes, single canonical section (spec lines 589–619), confirmed complete by a whole-document grep for `BDS_` finding no code outside this table. Message text is the spec's own bolded sentence; treatment is the spec's own remaining clause where one exists.

| Code | Message | Treatment |
|---|---|---|
| `BDS_TENDER_NOT_FOUND` | Tender not found. | Return to Tenders. |
| `BDS_TENDER_NOT_OPEN` | This Tender is not accepting bids. | Show the truthful published/cancelled/closed status. |
| `BDS_SIGN_IN_REQUIRED` | Sign in to start or continue a bid. | Preserve the safe return destination. |
| `BDS_ACCOUNT_REQUIRED` | Set up your supplier account before starting a bid. | Link Account. |
| `BDS_ACCOUNT_SUSPENDED` | This supplier account cannot submit bids. | Show the configured support route. |
| `BDS_ARRANGEMENT_INVALID` | Check the supplier or joint-venture information. | Link exact field/member. |
| `BDS_RESPONSIBILITY_REQUIRED` | An Authorised Signatory must complete this action. | — |
| `BDS_DEFINITION_UNSUPPORTED` | This bid format is not available. | Do not create a partial workspace; contact support. Ties to `Start bid`/publication (§4.4.3). |
| `BDS_ADDENDUM_REVIEW_REQUIRED` | Review the latest addendum and the affected bid responses. | Link each affected task. |
| `BDS_FIELD_INVALID` | Check the highlighted value. | Bind each exact field error. |
| `BDS_UNKNOWN_RESPONSE` | This response is not part of the published Tender. | Reject without saving. |
| `BDS_EVIDENCE_REQUIRED` | Add the required supporting evidence. | Link the published requirement. |
| `BDS_EVIDENCE_REJECTED` | This file could not be accepted. | Show type/size/scan reason without internal details. |
| `BDS_SECURITY_PROOF_REQUIRED` | Add the required tender-security proof. | — |
| `BDS_SECURITY_ORIGINAL_OUTSTANDING` | The physical tender-security original has not been recorded as received. | Warns only, never blocks electronic receipt. |
| `BDS_MUST_FIX` | Fix the listed items before submitting. | Link every issue. |
| `BDS_STALE_VERSION` | Another person changed this bid. Reload before continuing. | — |
| `BDS_SIGNATORY_REQUIRED` | Only an active Authorised Signatory can submit this bid. | — |
| `BDS_SIGNATURE_UNAVAILABLE` | Digital signing is not available. | Keep the bid Draft; show the approved support route. |
| `BDS_SIGNATURE_INVALID` | The digital signature could not be verified for this bid. | Nothing is submitted. |
| `BDS_SUBMISSION_SERVICE_UNAVAILABLE` | Electronic submission is temporarily unavailable. Your bid remains saved. | Never imply receipt. **Reused for D15's production-gate check.** |
| `BDS_SUBMISSION_UNCERTAIN` | Submission confirmation is still pending. Do not submit again. | Show correlation/support route; no receipt or success claim. |
| `BDS_DEADLINE_PASSED` | The submission deadline has passed. This bid was not submitted. | Show authoritative deadline/time. |
| `BDS_ALREADY_SUBMITTED` | This bid Version has already been submitted. | Show its receipt. |
| `BDS_REPLACEMENT_CONFLICT` | A newer submitted bid already exists. | Show current receipt; do not change either Version. |
| `BDS_WITHDRAWAL_BLOCKED` | This bid can no longer be withdrawn because the deadline has passed. | — |
| `BDS_IDEMPOTENCY_CONFLICT` | This request was already used with different information. Stop and refresh. | — |

General conventions (spec, verbatim): "Record-existence masking prevents cross-organisation disclosure. A public not-found response never confirms whether another supplier has a Draft or submission." (§8). "Internal identifiers, digests, schemas, rule keys, storage locations and security metadata never appear in portal HTML, URLs, accessibility text, downloads or errors." (§3, governs every message above though stated outside §8).

## Acceptance criteria map

Opened 2026-09-21 at Phase 0. All 124 criteria below are copied verbatim (short form) from the spec's §14.1–§14.10. `Target phase` names the phase whose work is expected to close the row; `Done` rows will cite the exact test/spec/observation with counts; every row starts `Planned`.

### §14.1 Public access, Account and organisation scope (BDS01-AC-001…012)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-001 | View available Tenders/current Tender/documents/addenda/clarifications/cancellation without an Account | 8a/8b | Planned |
| BDS01-AC-002 | Public/portal DTOs omit internal package/schema/digest/config/db/security/audit metadata | 3 | Planned |
| BDS01-AC-003 | Start bid requires authentication; returns to the same Tender after sign-in | 2/8b | Planned |
| BDS01-AC-004 | Registration captures only §4.1 fields; states Account activation is not qualification/eligibility | 2 | Planned |
| BDS01-AC-005 | Communication verification displayed only as channel control | 2 | Planned |
| BDS01-AC-006 | Cross-organisation reads/commands denied and masked | 2 | Planned |
| BDS01-AC-007 | Supplier Representative can prepare but not submit/replace/withdraw | 2/6 | Planned |
| BDS01-AC-008 | Authorised Signatory command requires active assignment + evidence + window at command time | 2 | Planned |
| BDS01-AC-009 | One person acts for several orgs only via separate assignments + explicit active-org context | 2 | Planned |
| BDS01-AC-010 | Suspended Account blocked from start/edit/submit; receipts reachable via recovery route | 2/8m | Planned |
| BDS01-AC-011 | Joint venture available only when permitted; records lead/members/agreement/signatory | 3 | Planned |
| BDS01-AC-012 | One active workspace per Tender+arrangement under concurrent Start bid | 3 | Planned |

### §14.2 Published definition and bid preparation (BDS01-AC-013…028)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-013 | Start bid binds exact Tender/template release/addendum set/definition Version atomically | 3 | Planned |
| BDS01-AC-014 | Unsupported response definition creates no partial workspace | 3 | Planned |
| BDS01-AC-015 | `IT-EQUIPMENT-OPEN-V1` workspace presents exactly five tasks in §5.3 order | 4/8f | Planned |
| BDS01-AC-016 | Every response row traces to the Published Tender with stable mappings server-side | 3/4 | Planned |
| BDS01-AC-017 | Unknown/hidden/inapplicable/client-invented fields rejected and never stored | 4 | Planned |
| BDS01-AC-018 | Tender quantities/units/requirements/declarations/price rows/currency/tax read-only to bidder | 4 | Planned |
| BDS01-AC-019 | Draft saves accept incomplete valid work, derive status, never imply submission | 4 | Planned |
| BDS01-AC-020 | Concurrent Draft edits use record versions; stale save cannot overwrite | 4 | Planned |
| BDS01-AC-021 | All 11 technical + 6 warranty rows + 5 acceptance obligations accounted for in the chain | 3/4 | Planned |
| BDS01-AC-022 | Large requirement sets grouped without changing identity/order/wording/applicability | 4/8i | Planned |
| BDS01-AC-023 | Known organisation values reused once; changes require explicit Draft refresh | 4 | Planned |
| BDS01-AC-024 | Locked declaration text fully viewable, never preselected, explicitly confirmed against its Version | 4/8h | Planned |
| BDS01-AC-025 | Completing a declaration/task reversible in Draft; not an evaluation/legal decision | 4 | Planned |
| BDS01-AC-026 | PDFs are view/download references only; no filled PDF/ZIP/spreadsheet substitutes structured responses | 4 | Planned |
| BDS01-AC-027 | Bidder sees one plain next action, never a schema/renderer/manifest/status key | 4/8f | Planned |
| BDS01-AC-028 | Primary fixture completed through five tasks without duplicate entry | 4/9 | Planned |

### §14.3 Evidence, tender security and price (BDS01-AC-029…042)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-029 | Every evidence item links to one visible published requirement/declaration/form | 4 | Planned |
| BDS01-AC-030 | Uploaded file unusable until media/size/integrity/malware checks return Accepted | 4 | Planned |
| BDS01-AC-031 | Rejected evidence identifies the safe reason, blocks task completion, no criterion-failure claim | 4/8i | Planned |
| BDS01-AC-032 | Reusing Account evidence freezes an exact bid-bound copy; later replacement never alters a submitted bid | 4 | Planned |
| BDS01-AC-033 | Evidence metadata captured only when required; no storage path/digest bidder-visible | 4 | Planned |
| BDS01-AC-034 | Tender-security type/issuer/reference/amount/currency/validity/proof follow the published rule | 5 | Planned |
| BDS01-AC-035 | Procurement receipt owner records physical receipt without access to responses/price/Draft status | 5 | Planned |
| BDS01-AC-036 | Physical receipt records server actor/time, classifies before/after deadline immutably | 5 | Planned |
| BDS01-AC-037 | Outstanding physical original produces the exact warning, never blocks electronic submission or fabricates disqualification | 5/8h | Planned |
| BDS01-AC-038 | Quantity/unit/line identity/currency read-only in Price; only published bidder fields editable | 5 | Planned |
| BDS01-AC-039 | Decimal arithmetic/rounding deterministically produce the §10.1 subtotal/tax/total | 5 | Planned |
| BDS01-AC-040 | Form of Tender projection consumes the one current Price total without re-entry | 5 | Planned |
| BDS01-AC-041 | Bidder never sees authorised estimate/Budget/allocation/reservation value | 5 | Planned |
| BDS01-AC-042 | Other currency/alternative price/new line/discount/spreadsheet import rejected for this product | 5 | Planned |

### §14.4 Addenda, clarifications and readiness (BDS01-AC-043…053)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-043 | Portal displays every issued addendum and authoritative clarification answer | 3/8g | Planned |
| BDS01-AC-044 | New addendum creates a new immutable definition; never edits an earlier one | 3/4 | Planned |
| BDS01-AC-045 | Submission blocked until every current required addendum is acknowledged | 4/6 | Planned |
| BDS01-AC-046 | Stable unaffected responses copy forward; affected responses become Needs attention with an issue link | 4 | Planned |
| BDS01-AC-047 | A submitted bid stays sealed after an addendum; changing it requires a replacement | 6/7 | Planned |
| BDS01-AC-048 | Effective deadline shown/enforced is the latest lawfully issued Tender/addendum deadline | 4/6 | Planned |
| BDS01-AC-049 | BDS submits questions through the Tenders owner contract, no parallel clarification store | 3 | Planned |
| BDS01-AC-050 | A clarification affecting requirements is shown to all candidates without identifying the questioner | 3 | Planned |
| BDS01-AC-051 | Validation recomputes the exact current definition/arrangement/responses/evidence/acknowledgements/security/price | 4 | Planned |
| BDS01-AC-052 | Every Must fix blocks submission and links to the exact task/row; a Review note doesn't unless mandatory | 4/8k | Planned |
| BDS01-AC-053 | A Supplier Representative sees the same review but no Submit control; names the Authorised Signatory | 4/8k | Planned |

### §14.5 Digital signature, submission and receipt (BDS01-AC-054…068)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-054 | Production Submit bid unavailable until the §5.10 operating profile is approved/configured/healthy | 6 | Planned |
| BDS01-AC-055 | Final action is plain-language Submit bid; consequence states signature/locking/deposit/no opening | 6/8l | Planned |
| BDS01-AC-056 | Server rechecks readiness/authority/definition/deadline/totals/evidence immediately before signing and deposit | 6 | Planned |
| BDS01-AC-057 | Submission requires a valid licensed-trust-chain signature binding the exact canonical package | 6 | Planned |
| BDS01-AC-058 | Typed name/checkbox/image/password/staff override cannot satisfy signature | 6 | Planned |
| BDS01-AC-059 | A signature for another person/org/package/expired-or-revoked certificate is rejected, nothing submitted | 6 | Planned |
| BDS01-AC-060 | The complete signed request must reach the trusted server before the deadline; client time ignored | 6 | Planned |
| BDS01-AC-061 | All evidence Accepted before final submission; no hidden post-deadline upload | 6 | Planned |
| BDS01-AC-062 | Submitted state + receipt commit only after custody acceptance of the exact signed envelope | 6 | Planned |
| BDS01-AC-063 | A definite tender-box rejection leaves the Draft unchanged, creates no receipt | 6 | Planned |
| BDS01-AC-064 | An uncertain result shows Confirmation pending, prevents duplicate dispatch, reconciles to one outcome | 6/8o | Planned |
| BDS01-AC-065 | Identical replay returns the original receipt; changed content under the same key is rejected | 6 | Planned |
| BDS01-AC-066 | Receipt contains all §4.10 human-readable facts, omits hashes/keys/certificate internals/schemas | 6/8m | Planned |
| BDS01-AC-067 | Receipt explicitly says submission is not opening/evaluation/award | 6/8m | Planned |
| BDS01-AC-068 | Supplier-facing Submitted appears only from authoritative accepted custody evidence | 6 | Planned |

### §14.6 Replacement, withdrawal, closing and handoff (BDS01-AC-069…078)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-069 | Prepare replacement leaves the current submitted Version and receipt effective | 7 | Planned |
| BDS01-AC-070 | Replacement becomes current only on acceptance; predecessor Superseded + new receipt atomic | 7 | Planned |
| BDS01-AC-071 | Abandoned replacement or passed deadline leaves the prior Version current | 7 | Planned |
| BDS01-AC-072 | Withdrawal requires active Authorised Signatory, exact Version, reason, confirmation, trusted pre-deadline time | 7 | Planned |
| BDS01-AC-073 | Withdrawal produces electronic acknowledgement, retains full history | 7 | Planned |
| BDS01-AC-074 | Withdrawn arrangement may resubmit before deadline with new Version + receipt | 7 | Planned |
| BDS01-AC-075 | Submit/replace/withdraw after deadline rejected without status change or misleading acknowledgement | 7 | Planned |
| BDS01-AC-076 | Tender box closes automatically at deadline; no user can reopen/extend/backdate | 7 | Planned |
| BDS01-AC-077 | Unsubmitted Drafts become Closed without submission, never enter opening inventory | 7 | Planned |
| BDS01-AC-078 | Bid Opening handoff contains only closed-box/sealed-envelope/lineage/custody evidence, no open/decrypt command | 7 | Planned |

### §14.7 Confidentiality, usability, accessibility and audit (BDS01-AC-079…090)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS01-AC-079 | Before opening, PE business users see no identity/count/responses/evidence filenames/prices/content | 6/8 | Planned |
| BDS01-AC-080 | Technical/admin views expose only authorised service/custody metadata, cannot decrypt/preview/download/search | 6 (D17) | Planned |
| BDS01-AC-081 | Draft/submitted content never appears in logs/search/analytics/traces/errors | 6 | Planned |
| BDS01-AC-082 | Submitted content protected under approved custody design; no secrets/keys in app data/config/fixtures | 6 | Planned |
| BDS01-AC-083 | Every artboard producible from §10 + KT-STD-001 §2 without invented content/behaviour | 8 | Planned |
| BDS01-AC-084 | Every visible action has exactly one §11 mapping, absent when the server refuses it | 8 | Planned |
| BDS01-AC-085 | Public/supplier tasks use ordinary language, no internal workflow/schema/rendering/crypto terms | 8 | Planned |
| BDS01-AC-086 | A representative user can find a Tender, set up an Account, prepare five tasks, understand who submits | 9 | Planned |
| BDS01-AC-087 | An Authorised Signatory can review/submit/identify the receipt without confusing it with opening/award | 9 | Planned |
| BDS01-AC-088 | Portal/Desk receipt surfaces meet keyboard/focus/status-text/error-linking/responsive rules | 8 | Planned |
| BDS01-AC-089 | Every successful Account/response/evidence/ack/receipt/signature/submission/replacement/withdrawal/close fact records §12 minimum evidence | 2–7 | Planned |
| BDS01-AC-090 | §13 seed reruns idempotently, isolates opposing outcomes, never presents simulated evidence as production compliance | 9 | Planned |

### §14.8 STD-derived definition and rendering acceptance (BDS02-AC-001…010)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS02-AC-001 | Exact released bundle + Tender Version + source rows + addenda deterministically produce one immutable definition; repeated generation, no drift | 3 | Planned |
| BDS02-AC-002 | Every task/group/response/evidence/declaration/price row has one stable identity, source, supported treatment | 3 | Planned |
| BDS02-AC-003 | Publication fails if a required response lacks validation/mapping, schedules disagree, or an unpublished obligation is introduced | 3 | Planned |
| BDS02-AC-004 | Runtime resolves an exact code-owned profile/renderer Version; unknown input creates no partial workspace, no fallback | 3 | Planned |
| BDS02-AC-005 | Bidder client selects no template, executes no arbitrary logic, saves only typed values; server independently revalidates | 4 | Planned |
| BDS02-AC-006 | Every bidder-editable field has a current purpose + a validation/evidence/evaluation/calculation/contract consumer | 3/4 | Planned |
| BDS02-AC-007 | Conditional applicability via reviewed named rules; newly required work incomplete, inapplicable excluded without erasing audit history | 4 | Planned |
| BDS02-AC-008 | Addendum migration uses an explicit identity map; no label/position/similarity/inference copying | 4 | Planned |
| BDS02-AC-009 | Issued Tender PDF is reference/output only, never parsed at runtime | 3 | Planned |
| BDS02-AC-010 | `IT-EQUIPMENT-OPEN-V1` keeps its approved five-task Goods composition; Works/Services need their own release | 3 | Planned |

### §14.9 Artboard consistency and recovery acceptance (BDS03-AC-001…018)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS03-AC-001 | Every artboard fixture time is at/after every already-completed fact; the primary fixture is 10 Jun 2027 14:20 EAT | 9 | Planned |
| BDS03-AC-002 | Workspace/task badges use only exact §4.5/§4.6 status values; issue counts are supporting text only | 8 | Planned |
| BDS03-AC-003 | A recorded physical tender-security original displays as a satisfied fact; only outstanding = amber Review note | 5/8h | Planned |
| BDS03-AC-004 | Every common state mapping to a §8 error reproduces that text exactly before fixture-specific context | 8o | Planned |
| BDS03-AC-005 | Supplier artboards use the Website shell; BDS-DES-15 alone uses the internal Desk shell | 3(D3)/5 | Planned |
| BDS03-AC-006 | Registration creates an organisation Account only; an arrangement is created per-Tender at Start bid | 2/3 | Planned |
| BDS03-AC-007 | Submit page shows trusted current server time with EAT, never the browser clock as authority | 6/8l | Planned |
| BDS03-AC-008 | BDS-DES-13-CLOSED uses a dedicated already-submitted post-deadline fixture, never a never-submitted late attempt | 9 | Planned |
| BDS03-AC-009 | A new Account stays Pending verification until the challenge succeeds; registration/Account artboards cover the transition | 2/8c | Planned |
| BDS03-AC-010 | A Suspended Account cannot start/edit/submit/replace/withdraw; receipts stay reachable via recovery route | 2/8m | Planned |
| BDS03-AC-011 | `BDS_IDEMPOTENCY_CONFLICT`/`BDS_REPLACEMENT_CONFLICT` each have a deterministic state, message, safe action, isolated fixture | 6/7/8o | Planned |
| BDS03-AC-012 | Cross-org denial, definitive/uncertain custody failure, late submission each have exact actors/times/correlation facts | 6/8o | Planned |
| BDS03-AC-013 | Every supplier artboard/dialog has a 390×844 derivative where grids stack, rows become cards, no lost values/actions | 8p | Planned |
| BDS03-AC-014 | A receipt shows `received_at`/`accepted_at` as separately labelled EAT instants, never collapsed | 6/8m | Planned |
| BDS03-AC-015 | Every price row labels its pre-tax amount unambiguously; tax/Bid total separately labelled once | 5/8j | Planned |
| BDS03-AC-016 | Withdrawal dialog labels the required reason and states the 10–500 char rule before submission | 7/8n | Planned |
| BDS03-AC-017 | "Submit bid" is the single visible terminal action label on page and dialog; consequence explains signing | 6/8l | Planned |
| BDS03-AC-018 | Rejected-evidence and addendum-change review failures use separate isolated variants, never combined fixtures | 4/8i | Planned |

### §14.10 Residual artboard-boundary acceptance (BDS04-AC-001…006, new in v0.4)

| ID | Criterion | Target phase | Status |
|---|---|---|---|
| BDS04-AC-001 | Opening/viewing Review creates no business fact, never changes Updated/Last updated timestamps | 4/8k | Planned |
| BDS04-AC-002 | View receipts/Refresh/View current receipt/Choose another file/Back to Account each have exactly one §11 mapping; `/account/receipts` is the explicit read-only recovery route | 2/8d | Planned |
| BDS04-AC-003 | List/summary derive Submitted from `accepted_at`, omit seconds without rounding; the receipt shows both to the second | 6/8m | Planned |
| BDS04-AC-004 | Every §10.18 inventory row incomplete until base/variants/dialogs render at both sizes | 8p | Planned |
| BDS04-AC-005 | Both pending-verification surfaces use the exact label "Resend verification link"; "Back to Account" is a mapped navigation action | 2/8c | Planned |
| BDS04-AC-006 | Review and submit is Complete only when server-derived readiness has no Must fix; opening Review never changes status/time | 4/8k | Planned |

## Re-implementation register map (§19)

The spec's own §19 "Full reimplementation register" (124 `BDS0{1-4}-IMP-NNN` rows, grouped 90/10/18/6 across v0.1–v0.4 provenance) was not transcribed verbatim into this tracker — it maps conceptually 1:1 onto the AC groups above, section for section. Before Phase 6 closes any error-handling row, re-read spec §19 directly and add a literal `| IDs | Phase / rows |` cross-reference table here, in the same form Tenders' own tracker used, once the phase rows that close each group actually exist (BDS-003 in Phase 0 — re-extracting §8 — is the natural companion action to do this at the same time).
