# AWD-CHG-001 v0.4: Award, implementation plan

| Control | Value |
|---|---|
| Version | 0.4-plan.1 |
| Date | 30 September 2026 |
| Authority | `KenTender_AWD-CHG-001_Award_v0_4.md`, **"Proposed requirements — Project Owner review"** (AWD v0.4 line 7). "Implementation / verification / release: Not started / Not started / Not approved" (line 15). Built under owner decision OD-A below; approval is recorded separately and is not claimed by this plan. |
| Governing standard | KT-STD-001 v1.12, approved (`../00_common/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_12.md`). |
| Upstream authorities (AWD v0.4 §17.1) | EVL-CHG-001 v0.4 (approved 30 Sep 2026; built, tracker 0.4-tracker.9); STD-TPL-001 v0.10; TPR-CHG-001 v0.13; BDS-CHG-001 v0.8; PRC-CHG-001 v0.9; TRUST-ADR-001 v0.1; AUTH-ADR-001 effective version. None carries the Award counterpart contracts AWD-IF-01…07 (C1). |
| Design | `design/Award Artboards.dc.html`, with `design/support.js` and the `_ds/kentender-industry-…` Industry bundle (both byte-identical to Evaluation's). One self-contained file: an inline `BOARDS` array of **47 boards** (9 main, 27 variants, 11 dialogs) rendered by one data-driven `<x-dc>` template. A `viewport` prop switches Desktop (1120 px sheet) and Mobile 390. Reviews: `design/reviews/AWD-CHG-001_v0_{1,2,3}_review.md`. |
| Companions | `AWD-CHG-001_v0_4_IMPLEMENTATION_TRACKER.md`; `AWD-CHG-001_v0_4_FOLLOW_UPS.md`. Phase 0 adds `reconciliation/{artboard_inventory, error_contract, next_step_register, command_map, fixture_chronology, seam_register}.md`. Later: `evidence/v0_4/` and `RUNBOOKS.md`. |
| Predecessor | None. This is the first Award plan. |
| Prepared | 30 September 2026 |
| Status | Built 1 Oct 2026 through Phase 12 (see tracker 0.4-tracker.2); Phase 13 owner-gated; uncommitted. (0.4-plan.1 read: Planned. No code has been written.) |

## Context

**Why this module now.** Bid Evaluation (EVL-CHG-001 v0.4) is built. It ends by delivering a signed report to the Head of Procurement, and nothing reads that delivery (FU-EVL-15). Award is the next step in the traceability chain: Evaluation → **Award** → Contracting.

**The MVP contract (AWD v0.4 §1).** "Receive Evaluation report → sign professional opinion → record award decision and issue notices → record supplier acceptance and complete the required wait → send to Contracting." Receipt, checks, preparation, tracking and final delivery are automatic. There is no separate acceptance of the incoming report, no approval to start, no approval per notice and no approval to send an eligible package to Contracting. The award notice and the supplier's acceptance do not create a contract.

**Why this plan is shaped the way it is.** The Evaluation build took most of a day. The recorded causes, with the rule this plan adopts for each:

| What slowed Evaluation | Evidence | Rule here |
|---|---|---|
| Every Python test rebuilt tender → bid → opening (20–40 s each) until the owner stopped it | EVL suite 1,094 s → 444 s after sharing worlds (EVL tracker line 65); memory "shared test worlds" | Award tests do not build any upstream world at all (OD-B, D4). One integration module builds one real world. |
| Bid Opening suites re-run with no changed dependency; a 25-minute rerun blocked the site | EVL tracker lines 73–74 ("stopped at 71/71 as redundant") | An upstream rerun names the changed file that justifies it and runs only that one test module. |
| All services built before any screen; nine defects surfaced in the browser late (no pick lists, wrong guidance precedence, wrong version on first save, "Decision unknown" with no action, "Late" vs "Received late", supplier check on the real date instead of the trusted clock) | commits `bfbfc43e`, `944c16f0`, `0ac585da`, `d5690dbc` | Vertical slices from Phase 3: service → API → screen → one Playwright spec → live click-through, per slice. |
| Browser worlds rebuilt BDS → BOP → EVL per spec (committee spec alone built 4) | `evlWorld.ts`, `playwright_ui_fixtures._start` | Browser worlds use the synthetic sources and build in seconds. |
| UI gates never wired: no `ui-evl-*` targets; `bid-evaluation` vitest project not in `ui-structure-gate` | Makefile; EVL4-1104 Partial | Make targets and the vitest project exist from Phases 0–1. |
| Demo profiles and the menu walk left to the end, still open | EVL4-1304/1305 | The first screen slice already walks from the sidebar and My Work. |
| Placeholder canonical bid found in Phase 0 but fixed in Phase 13, forcing a reseed through `bid_opening` | C22, EVL4-1306 | Phase 0 checks the canonical Report sent facts Award will read; any gap is fixed or logged before code. |

## Current state (verified 30 September 2026 by reading the source)

Paths are relative to `kentender_procurement/kentender_procurement/` unless shown otherwise.

**Award.** No code exists.
- `evaluation_award/` is an empty skeleton (`__init__.py`, `api/`, `services/`, `tests/`, `utils/` with docstrings only; `doctype/.gitkeep`). It is not in `modules.txt`.
- Workspace `evaluation_and_award` is a placeholder ("This lifecycle step is not implemented yet"), referenced by `setup/workspace_permissions.py:104–105` and `setup/tests/test_procurement_sidebar_g0_012_contract.py:167`.
- `workspace_sidebar/procurement.json:136–141`: "Awards" → Page `coming-soon`. `setup/sidebar_availability.py:26` lists "Awards" in `PLANNED_SIDEBAR_LABELS`.
- No DocType, Page, route or role named `award` exists in any app on the bench. No `/supplier` portal prefix exists (`kentender_core/hooks.py:95–101` route rules cover `/tenders`, `/my-bids`, `/account`).
- Legacy TM2 references (`tender_management/enums.py:32` "Awarded", `create_contract_handoff_reference.py`, `PERM_AWARD_APPROVE`) are not reused.

**What Evaluation gives Award.**
- `bid_evaluation/services/signing.py:189 deliver(doc, version, key)` runs when the last committee signature lands. It writes one `Evaluation Report Delivery` per report version: `delivery_key = "{case}:{version}"`, `recipient_user` (the Head of Procurement, `_recipient()` l.159), `status` Pending/Delivered/Failed, `review_state` Open/Reviewed/Returned, `downstream_status`. It sets the case to **Report sent**, appends a PRC `ReportDelivered` event and notifies "Review evaluation report for {ref}". Retry: `retry_delivery` (l.214).
- There is no outbox. The payload is the frozen `Evaluation Report Version`: `content_json` (`report.build`: summary, tender and committee, bid findings, financial comparison, clarifications and record, recommendation), `content_digest`, `outcome`, `recommended_bid`, `recommended_total` (decimal string, "46400000" canonically), `qualifications_json`, `source_versions_json`, `record_version_reference` (a PRC `Proceeding Minutes Version`). Signatures: `signing.signatures(version)` (l.275), stored as PRC targets and attestations.
- Outcomes (`services/report.py:130`): Recommendation; No agreed recommendation; No current recommendation — tender validity expired; Qualified report; No responsive bids; No single recommendation — equal evaluated totals ("The published tender has no tie-break rule."); funding qualification "Funding needs resolution before award.".
- Comparison rows (`services/comparison.py:47`): `bid, bidder, submitted_total, adjustments, evaluated_total, position` (shared on ties).
- The Head of Procurement's task (`services/my_work_provider.py:188–192`): "Review evaluation report for {ref}", key `review-report:{delivery}`, route `tenders/{ref}/evaluation/report`, shown while `review_state == "Open"`. Nothing sets it to Reviewed today.
- Return before a decision: `services/correction.py:89 return_report` (`ReturnEvaluationReport`, recipient only). It refuses on `EVL_DECISION_STATUS_UNKNOWN` or when a decision is recorded.
- After delivery: `record_correction_notice` (l.119, `Evaluation Correction Notice` with `head_review_state`), `assess_supplement` (l.199), `head_review` (l.226).
- EVL reads the award decision through `correction.decision_status` (l.42) → simulation override → an `Evaluation Source Event` of kind "Award decision" → `tenders/services/evaluation_seam.py:183 award_decision_status(tender)`, a stub that always returns "No award decision recorded" (or "Unknown" on error). `status_events` (l.171) returns cancellation only.
- Canonical stage `bid_evaluation` (`bid_evaluation/seeds/kentender_mvp_v1.py:199/229`): Report sent on **TND-MOH-2027-002**, delivered to `charles.mutiso@moh.example.test` on 16 Jun 2027 at 14:07, recommending Afya at KES 46,400,000.00.

**Shared facilities to reuse (no parallel versions, AWD v0.4 §15).**
- **Signing.** `proceedings/services/signing.py:33 attest(*, member, target_id, target_digest, minutes_version, action, correlation_id)` with outcomes `Accepted/Verified`, `Rejected`, `Unavailable`, `Indeterminate`. The test double (`proceedings/test_services/attestation.py`) loads only under `kt_bds_simulation_environment`; `frappe.flags.kt_prc_signing_outcome` forces an outcome in tests. PRC `record_versions.freeze_record` requires every signer on a proceeding roster and a profile in `profiles.PROFILES`, which the single-signer opinion does not have (C4).
- **Support issues.** `kentender_core/services/support_issues.py`: `open_issue(...)` (l.115, idempotent on `module:operation_correlation`), `resolve_on_success` (l.148), `my_work_rows` (l.178).
- **Guidance and work.** `kentender_core/services/next_step.py` (`answer`, `guard`, `combine`, `blocker`, `holder`, `since`, `journey`, `for_viewer`, `problems`; kinds `your_turn`, `your_turn_blocked`, `waiting`, `timed`, `done`, `not_involved`). `kentender_core/services/my_work.py` (`kt_my_work_providers`, returns `{assigned, claimable, waiting}`; skips technical users, l.139).
- **Notifications.** `kentender_core/services/notification_service.py:19 emit_notification_log(..., correlation_key)` (idempotent).
- **Supplier messages.** `kt_bds_supplier_message_transports` → `bid_submission/test_services/mailbox.deliver` (JSONL test mailbox, test sites only). Evaluation's pattern: `clarification.py:130 _deliver`, `:148 _notice` ("Delivered" / "Delivery problem").
- **Delivery attempts.** `tenders/services/candidate_notices.py`: `freeze` (l.82) snapshots destinations; `dispatch` (l.123) appends one attempt per try; "Sent" is never shown as "Delivered" without provider evidence. No "giving evidence" concept exists yet.
- **Supplier authority.** `bid_submission/services/bid_authorization.py`: `acting_assignment` (l.31, representative or signatory), `active_signatory` (l.58, signatory only). `supplier_gateway.py`: `verified_contacts` (l.38), `organisation_signatories` (l.59).
- **Notice contacts.** `Bidder Arrangement.mandatory_notice_email` with `notice_contacts` history; correction command `notice_contact.update_tender_notice_contact(...)` (l.25), the contact owner's command.
- **Bidder audience.** `bid_submission/services/opening_gateway.py:29 closed_manifest(tender)`: `envelopes[]` with `status` Submitted / Superseded / Withdrawn, `bidder_arrangement`, `predecessor_submission_version`, `changes[]`.
- **Tender facts.** `tenders/services/evaluation_seam.py:150 dated_rules(tender)` (validity end from `RR-TENDER-SECURITY.validity_date` at the deadline's time of day); `:195 funding_reservations`. Cancellation: `tenders/services/cancellation.py:112 cancel_tender`, guarded by `_require_open` (l.52, "Published — open" only). Event outbox `tenders/services/events.py`. Record links hook `kt_tender_record_links`.
- **Funding.** `kentender_budget/services/budget_downstream_contracts.py:43 get_funding_lineage`, as used by `bid_evaluation/services/funding.py`.
- **Clocks.** `kentender_core/services/test_clock.py` (`current_instant`, `set_instant`), `kentender_core/utils/instants.py`; module pattern `bid_evaluation/services/clock.py::now()`.
- **Desk runtime.** `kentender_core.desk_page.register` (`kt_desk_page.js:156`), `useRoute`, command runner, sequence guard, screen cache; industry `mountPageRail`, `mountGuidance`, `mountJourney`.
- **Portal.** `kentender_core/services/portal_runtime.py:73 resolve_surface(path)` (longest owned prefix), surfaces registered through `kt_portal_surfaces` (`kentender_procurement/hooks.py:113–128`); `bid_submission/portal.py::resolve`; `public/js/bid_portal/BidPortal.vue`.

**Personas** (`kentender_core/seeds/site_setup.py`, supplier seeds):

| Person | Role | Seeded | Note |
|---|---|---|---|
| Charles Mutiso | Head of Procurement Function, site-wide | Yes (:154, :249) | Also the illustrative Contracting owner (§13) |
| Amina Hassan | Accounting Officer | Yes (:162, :256) | |
| Mary Wanjiku | Afya Authorised Signatory (registrant) | Yes (`kentender_suppliers/.../seeds/canonical.py`) | |
| David Ouma | Afya Supplier Representative | Yes | |
| Daniel Otieno | Technical Operator + technical reader (System Manager) | Yes (:169, :260, `TECHNICAL_ACTORS` :187) | My Work skips him (C9) |
| Esther Njeri | Technical Operator | Yes (:182, :273) | Sees Support Issue rows |
| Naomi Chebet | Auditor | Yes | |
| Jirani Office Supplies Limited | Supplier | **No** | Synthetic recipient only (§13; C8) |

**Done means:**
- Every AWD v0.4 §7 command and read is a server service with idempotency, expected revision, trusted time and audit.
- Every §5.9 next-step row has its holder, My Work item, clearing event and a named test.
- All 47 boards are ported class-for-class; each is compared by the fidelity gate or recorded as not compared with a reason.
- The canonical tender (TND-MOH-2027-002) goes from the real Evaluation delivery to **Contracting has received the award.** in a browser, driven from the menu by its real personas under the simulation flag. The §13 branches are each proven on their own synthetic fixture.
- AWD-AC-001…031 are honestly marked. Production-only parts stay `Blocked — owner`.
- No contract, contract signature, performance-security verification, supplier substitution, price edit, negotiation or second approval exists anywhere in the module.

## Owner decisions (this session, 30 September 2026)

| # | Decision |
|---|---|
| OD-A | **Build now, amend later.** Owner answer, verbatim: "Build now, amend later (Recommended)". The option chosen read: "Same approach as Evaluation: build to v0.4 as written, log the changes other modules' documents need as follow-ups, and record approval separately." AWD v0.4 remains *Proposed* until the owner approves it. The counterpart amendments (EVL, TPR, BDS, PRC, KT-STD, SEED-OPS, Contracting) are Phase 13 follow-ups and block no phase. Every seam added to another owner's code records an addendum row in that owner's tracker. If approval changes v0.4, the change is handled as a delta against this build. |
| OD-B | **Stand-in upstream, real seam proven separately.** Owner answer, verbatim: "Stand-in upstream, real seam proven separately (Recommended)". The option chosen read: "Service and browser tests start from a signed report in seconds. The real Evaluation→Award hand-off is proven by one integration test module (built once) plus the canonical 'award' seed stage and the demo walk." |

Standing owner rules carried in from earlier modules and not re-asked: dev-site stand-ins behind `kt_bds_simulation_environment` (EVL OD-D); shared test worlds; targeted regression runs; walk from the menu; stop chasing exact matches on rare branch screens (record them as not compared); plain-English replies; store instants in site time, UTC only in serialized messages (AGENTS.md §4.4 overrides AWD §15's "Persist timestamps in UTC").

## Key technical decisions (implementation authority unless the owner says otherwise)

| # | Decision |
|---|---|
| D1 | **Module.** Add a new `award` module (Module Def "Award") to `kentender_procurement`, with `doctype/`, `services/`, `api.py`, `portal.py`, `desk_links.py`, `page/`, `tests/`, `test_services/` and `seeds/`, and add it to `modules.txt`. Follow the new-module procedure: after the first migrate, clear the cache, check that the Module Def has `app_name = kentender_procurement`, then migrate again. Delete the empty `evaluation_award/` skeleton (docstring-only files). Leave the "Evaluation and Award" workspace untouched (the G0-012 sidebar contract test references it). `award` never imports internals of `bid_evaluation`, `bid_submission`, `tenders`, `proceedings` or `kentender_budget`; it reaches them only through `services/sources.py` (D4) and the published seams (D5). |
| D2 | **Doctypes (AWD v0.4 §4 names; no field without a named rule or output).**<br>• `Award Case`: one per tender/lot, ID `AWD-<tender reference without TND->`; tender, lot, `source_kind` (Evaluation / Synthetic), frozen source snapshot (report identity, version, content digest, signature set digest, outcome, recommendation, comparison, qualifications), received time, current cycle number, stored stage (Opinion / Decision / Notices / Waiting to proceed / Sent to Contracting / Closed), terminal outcome, `record_version`, `fixture_namespace`. Conditions (held, overdue, suspended, awaiting correction) are fields or open issues, never stages (§5.9).<br>• `Award Decision Cycle`: number, predecessor, authorising correction decision, report/opinion/decision references, stage, terminal outcome; immutable once complete.<br>• `Award Professional Opinion`: version, exact report reference and digest, HOP, conclusion (Recommend award / No current recommendation), reason, addressed issues, frozen document digest, signing attempt, proof reference, outcome, signed time. Immutable once signed.<br>• `Award Decision`: version, cycle, AO, time, exact opinion and report, outcome (Award / No award / Return for correction), reasons, next action and owner (No award), supplier, bid, submitted and evaluated amounts (Award only), authorised batch reference.<br>• `Award Decision Event` (`AwardDecisionRecorded v1`): stable event ID, payload per §5.8, recipient, child `Award Delivery Attempt` rows, receipt.<br>• `Award Notice Batch` and `Award Notice`: one logical notice per decision and bidder; generated bytes and version, recipient bid and organisation, contact snapshot, required channels, issue identity and time, child attempt rows, giving evidence per channel, notification status.<br>• `Award Supplier Response`: notice and version, Accept / Decline, person, authority evidence, exact wording, received time, late flag.<br>• `Award Issue`: source event identity, type (Source correction, Funding, Validity, Delivery, Debrief, Review/order, Supplier response, Service failure, Rules and notice audience), basis for hold (Authoritative order / Reported challenge), scope, evidence, effective and received times, owner, state, disposition (§5.10 outcomes only), reason, next action.<br>• `Award Correspondence`: bidder, request and reply, attachments, times, closure, immutable once sent.<br>• `Award Clock`: rule and profile version, trigger evidence, timezone, calendar treatment, deadline, revision.<br>• `Award Contracting Package`: version, digest, frozen references, check results, receipt.<br>• `Award Command Journal`; `Award Settings` (single: the versioned legal/test profile, D8); `Award Test Environment Controls` (single: fault switches, D16).<br>All doctypes carry the flags guard (writes only through `records`), deny-by-default permissions and `fixture_namespace`. |
| D3 | **Command envelope.** `award/services/records.py` mirrors `bid_evaluation/services/records.py`: `command(name, *, case, idempotency_key, actor, payload, body)` journals the command, a replay returns the original result and a conflicting reuse is refused; `check_version` raises `AWD_RECORD_CHANGED` and returns the current record; `atomic`, `lock(case)`, `bump`, `digest`, `next_id`. `errors.py` holds the closed AWD v0.4 §8 set verbatim (13 codes) with a separate detail, `Guards` that collect every reason together, `as_data` for refusals-as-data and `InputError` for field errors. The API never forwards `**kwargs` into a keyword-only service (transport-field trap). |
| D4 | **Source layer (OD-B).** `award/services/sources.py` is the only place Award reads upstream facts. One interface: `delivered_report(delivery)`, `signatures(report)`, `tender_facts(tender)` (reference, title, lot, currency, published award method, acceptance/reply terms), `validity(tender)`, `status_events(tender, after)` (cancellation, suspension, validity extension), `audience(tender)`, `notice_contact(bidder)`, `is_active_signatory(user, organisation, at)`, `acting_for(user, organisation, at)`, `funding(tender, amount)`, `status_available()`. Providers are registered through the hook `kt_award_source_providers`:<br>• `real` wraps the published seams (D5);<br>• `synthetic` (`award/test_services/sources.py`) serves a deterministic fixture dictionary of the AWD v0.4 §10.1/§13 facts (report 1, Afya, 250 Each, KES 46,400,000, 36 months, three signatures, validity 10 Oct 2027 11:00 EAT, the two-bid 037 and tie 036 fixtures, a synthetic Jirani recipient). It loads only under `kt_bds_simulation_environment`, and an `Award Case` created from it carries `source_kind = "Synthetic"` visibly.<br>After receipt the case reads its own frozen snapshot; live source calls happen only in the guard checks (validity, cancellation, funding, authority, contacts, status). This keeps upstream reads few, deterministic and testable. |
| D5 | **Upstream seams (additive: new files plus one-line hook calls; no rewrites).**<br>• `bid_evaluation/services/award_seam.py`: `delivered_report(delivery)` (report version, digest, outcome, recommendation, comparison, qualifications, signature set, verified by recomputing the digest); `take_up(delivery, award_case)` (sets `review_state` to a new value "With Award" so EVL's "Review evaluation report" row stops and Award's "Prepare professional opinion" is the same work item, AWD §3 entry contract); `return_report(delivery, comment, actor)` (wraps `correction.return_report`); `corrections_after(case, after)` (correction notices and opening supplements after delivery).<br>• One call to the new hook `kt_evaluation_report_consumers` at the end of `signing.deliver` after a successful delivery. Award's consumer calls `ReceiveEvaluationReport`; a consumer failure never fails EVL's delivery and leaves an Award Support Issue plus retry (§3 "durable delivery retry").<br>• `tenders/services/award_seam.py`: `validity(tender)` (from `dated_rules`), `status_events(tender, after)`, `acceptance_terms(tender)`. `cancel_tender` gains one call to a new hook `kt_tender_cancellation_guards`; Award's guard refuses when notification status is not "Not issued" (serialised under the Award case lock, AC-010). `evaluation_seam.award_decision_status` delegates to the hook `kt_award_authority_status` when one is registered, so EVL's existing return guard sees real decisions.<br>• `bid_submission/services/award_gateway.py`: `audience(tender)` from `closed_manifest` (Submitted only; Superseded and Withdrawn per the verified audience rule, no duplicates), `notice_contact(bidder_arrangement)`, `is_active_signatory`, `acting_for`.<br>• Each seam gets an addendum row in the owner's tracker (EVL, TPR, BDS) in the same commit, and a Phase 13 follow-up. Each upstream edit names the single upstream test module to rerun once (tracker rule 12). |
| D6 | **Signing.** HOP signs the frozen opinion through `proceedings.services.signing.attest(member=HOP, target_id=opinion ID, target_digest=frozen digest, minutes_version="", action="Sign", correlation_id=attempt ID)`. The attempt is stored before the call. `Accepted/Verified` commits the signed opinion and creates the AO task atomically (AC-003). `Indeterminate`/`Unavailable`/`Rejected` keeps the draft, shows **Signing is unavailable. Your draft has been saved.** (V12) and resolves through the same attempt ID. A changed draft invalidates the frozen target. Test proofs are labelled at runtime only under the flag. No PRC profile change. |
| D7 | **Notices.** Letter bytes are generated deterministically per recipient from the decision, signed findings and the issued form fields, through the existing wkhtmltopdf path and `file_integrity`. `IssueAwardNotices` runs as one serialised operation under the case lock and re-checks cancellation, validity and restrictions before the first outward effect. The portal notices are published atomically for every recipient, then the email jobs are dispatched together (`kt_bds_supplier_message_transports`). Each attempt is a retained row. Whether a notice has been **given** is decided by the channel rule in the profile (D8), never by a send status. Case notification status: Not issued / Issue in progress / Issued / Unknown; it never returns to Not issued after any issue. **Correct contact** invokes `notice_contact.update_tender_notice_contact` and returns its receipt; only the route changes, and every old address and attempt is kept. |
| D8 | **Legal/test profile.** `Award Settings` holds a versioned operating profile: profile ID and version, verified flag, reviewer and date, reply window source (the issued notice term), minimum waiting rule, counting, timezone and calendar treatment, lawful channels and what counts as giving evidence, debrief effect, revised-notice treatment. The only verified profile on this bench is the simulation test profile, loaded under the flag, whose delivery date term reproduces §13 (**2 Jul 2027, 09:00 EAT**). Without a verified profile every positive advance fails with `AWD_RULE_UNVERIFIED` (V15) and a Rules and notice audience issue. No 14-day or other time is hard-coded (§5.5, §15). |
| D9 | **Clocks and eligibility.** `Award Clock` rows record each calculation. `RefreshAwardEligibility` runs after every accepted command or event, and from a scheduler sweep for deadlines (reply deadline, waiting period, validity expiry). It evaluates the seven §5.8 conditions together and returns every unmet one. It is rechecked at decision, at actual issue and before every delivery attempt; a delayed worker cannot send a positive notice after expiry (AC-014). `award/services/clock.py::now()` honours the trusted test clock for every actor, including supplier-side timeliness (the EVL "real date" defect). |
| D10 | **Contracting.** `DeliverAwardPackage` and the decision-event delivery go through the hook `kt_award_contracting_receivers`. The only provider is `award/test_services/contracting_receiver.py`: a test inbox with `receive_package` (durable receipt plus one **Prepare contract** row for Charles in a Contracting capacity), `receive_decision_event` (`ReceiveAwardPublicationEvent`: one receipt per event, a publication obligation only for Award events) and a failure switch. It loads only under the flag. With no receiver the case stays **Waiting to proceed**, shows **Contracting is unavailable. KenTender will check that the award can still proceed before sending it.** (V10) and opens a Support Issue; it never asks HOP to approve transmission. **Open Contracting** is shown only after a durable destination exists. |
| D11 | **Next steps and journey.** `award/services/next_steps.py` implements the §5.9 tables: the five journey labels **Opinion / Decision / Notices / Acceptance and wait / Send to Contracting**, markers Done / Current / Blocked / Not started, the tracker mapping for Waiting to proceed (conditions 1–6 vs 7), the correction-cycle mapping and every next-step text verbatim. It uses core `answer`, `guard`, `holder`, `journey` and `problems`. Precedence: cancellation or a restriction that stops the actor's action first, then the actor's available work, then the next scheduled event. Every outstanding issue and its owner is returned, not just the headline. Viewing never completes a task. No tracker on the workspace, supplier pages or dialogs. |
| D12 | **Work items.** `award/services/my_work_provider.py` registered in `kt_my_work_providers`. Rows are derived purely from state and keyed by (case, cycle, source event, responsibility), so retries cannot duplicate them and resolving one issue never clears another. Titles come from §5.9: Prepare professional opinion, Decide award, Resolve returned decision, Resolve notice delivery, Respond to request, Review restriction, Resolve expired validity, Resolve supplier response, Review report correction, Review opening update, Decide correction, Resolve revised notice treatment. Technical work (Restore notice delivery, Restore Contracting delivery, Restore signing) uses core `Support Issue` rows; Esther sees them in My Work, and Daniel (a technical user whom My Work skips) sees them in the technical work view (V16, C9). Suppliers have no Desk task; the portal shows their notice. |
| D13 | **Desk routes.** A new Desk Page `award` (one `kentender_core.desk_page.register(...)` call) serves `/app/award` (D01 workspace) and `/app/award/{award_id}` (record, with sections, not sub-pages). Bundles: `award.bundle.js`, `award_page.bundle.css`, lazy-loaded (AGENTS.md §6.9). The sidebar "Awards" item moves from `coming-soon` to Page `award`, and "Awards" leaves `PLANNED_SIDEBAR_LABELS`. The Tender record links to its award through `kt_tender_record_links`. Phase 1 checks the Page.module collision on `/app/award/{id}` (memory: module-sidebar route collision) and sets `Page.module` to avoid it, as Evaluation did. |
| D14 | **Supplier portal.** A new portal surface `/supplier/awards/{notice_id}` registered through `kt_portal_surfaces`, with its own small bundle, served at 390 px. Reads use `GetSupplierAwardNotice` (own notice only; never another recipient's letter). **Accept award** / **Decline award** require `is_active_signatory` at the action; **Request explanation** needs `acting_for` (representative or signatory). The supplier's bid overview links to the notice through `kt_tender_portal_links`. |
| D15 | **UI port.** The 47 boards are all rendered by one data-driven template, so the port is one Vue block renderer, `public/js/award/board/AwdBoard.vue`, ported class-for-class from the `<x-dc>` markup (page head, journey, next-step block, sections with facts/paragraphs/definitions/tables/fields/notes, decision bar, action row, disclosures, dialogs). Screen builders (`public/js/award/screens/*.js`) turn server reads into that block model. The shared Industry rail and guidance are mounted as the other Industry pages do. Never Civic Ledger or Stitch Desk classes, never `cl_surface_registry.js`. |
| D16 | **Fidelity tooling and simulation controls.** `tests/ui/fidelity/board.js` gains an `awardKit` that evaluates the inline `BOARDS` script with stubs for `DCLogic`, `React.createRef` and `localStorage`, and renders each board through the existing `renderTemplate`. A `departures/award.js` registry (DEPARTURES, COVERED, NOT_COMPARED with reasons) and a vitest project `award` are added, and `award` joins `make ui-structure-gate` in Phase 0. Fixtures for the fidelity spec are captured from synthetic stages (`capture_all` in seconds). `Award Test Environment Controls` holds fault switches (signing outcome, notice channel failure, status service down, Contracting receiver down, rule profile unverified, simulated Tenders owner events: cancellation, suspension, validity extension) and loads only under the flag. TRUST test labels render at runtime only, never in ported markup. |

## Phases

**Loop for every phase:** red, then green, then refactor; run the module tests once; run the phase gate; update the tracker row with its evidence in the same step. Phases 0–2 are horizontal. From Phase 3 each phase is a **vertical slice**: service → API → screen → one Playwright spec with one fixture entity → a live click-through from the menu. Never run Python while a Playwright process is active.

### Phase 0: Reconcile (documents and tooling)
- `reconciliation/artboard_inventory.md`: all 47 boards extracted by script from the inline `BOARDS` array: id, name, group, actor, instant, viewport, spec § / variant, slice, compare or not-compare.
- `reconciliation/error_contract.md`: AWD v0.4 §8, 13 codes, copied verbatim by script.
- `reconciliation/next_step_register.md`: every §5.9 next-step row and correction-cycle row: situation, text, holder, My Work title, clearing event, named test.
- `reconciliation/command_map.md`: every §10/§11 control → exactly one §7 command or read (AC-023).
- `reconciliation/fixture_chronology.md`: the §13 ordinary path with instants, and the 24 isolated branches, each with its synthetic entry point.
- `reconciliation/seam_register.md`: AWD-IF-01…07 → the concrete function built here, or the gap and its follow-up.
- Check the canonical Report sent facts on TND-MOH-2027-002 against §10.1 (supplier, amount, quantity, warranty, signatures, validity). Fix or log any gap now, not in Phase 11.
- `awardKit` extractor, `departures/award.js`, vitest project `award`, added to `ui-structure-gate`.
- Commit the spec and design folder if the owner permits (the provenance gate is repo-wide).
- **Gate AWD-G00:** inventory = 47 rows, each in exactly one slice; every §10/§11 control mapped; `make artboard-provenance-gate` green; `npx vitest run --project award` runs (empty compare list allowed).

### Phase 1: Scaffolding
- `award` module, every D2 doctype with the flags guard and deny permissions, `Award Settings`, `Award Test Environment Controls`, `Award Command Journal`; delete `evaluation_award/`.
- `records.py`, `errors.py`, `clock.py`.
- Page `award` shell with the register call, sidebar link, `PLANNED_SIDEBAR_LABELS` update; check the Page.module collision.
- Makefile: `awd-preflight`, `awd-services-gate`, `awd-seams-gate`, `awd-leakage-gate`, `awd-dead-end-gate`, `ui-awd-fidelity-gate`, `ui-awd-<slice>-gate` (one per slice), `ui-awd-gate`, `seed-awd-profile(s)`, added to `.PHONY`.
- Schema tests `award/tests/test_awd_schema.py`, `test_awd_errors.py`.
- `make validate-links`, migrate clean twice.
- **Gate AWD-G01:** schema and errors tests green; migrate twice clean; `/app/award` renders the empty shell with the rail from the sidebar.

### Phase 2: Sources, seams and the test base
- `services/sources.py`, `test_services/sources.py` (synthetic provider), `award/tests/support.py` (`AwardCase`: synthetic world built once per module; per test only Award rows of the `AWD_TEST` namespace are wiped; flags handled as in EVL's support).
- The D5 seam files and hook calls in `bid_evaluation`, `tenders` and `bid_submission`, each with an addendum row in its owner's tracker.
- `test_awd_seams.py`: seam contract tests, read-only, against the canonical Report sent on TND-MOH-2027-002 (shape, digest recomputation, audience, validity).
- `test_awd_integration.py`: one real EVL Report sent world per module (years ≥ 2100, EVL `EvaluationCase` machinery), proving delivery → one case and one HOP task, retry without duplicates, EVL row taken up.
- Upstream reruns, once each, justified by the files touched: `bid_evaluation.tests.test_evl_report` (delivery hook), the Tenders cancellation test module (guard hook), the Tenders seam test (`award_decision_status` delegation).
- **Gate AWD-G02:** `make awd-seams-gate` green; the named upstream modules green; `make awd-services-gate` builds the synthetic world in under 5 s.

### Phase 3: Receive and professional opinion (AC-001, 002, 003, 006)
- Services: `intake.py` `ReceiveEvaluationReport` (one case/cycle 1/HOP task; source completeness and signature checks → automatic Source correction issue with named owner, `AWD_SOURCE_INCOMPLETE`; empty opening → nothing; failure → Support Issue and same-identity retry); `opinion.py` `SaveProfessionalOpinion`, `SignProfessionalOpinion` (D6), `ReturnEvaluationReport` (via seam; closes superseded tasks; a successor report makes drafts out of date and requires a fresh opinion); `checks.py` read-only checks (source, tender status, validity, funding, award-method consistency, open corrections, supplier identity; established restriction vs unavailable check); `next_steps.py` and `my_work_provider.py` first rows; reads `GetAwardWorkspace`, `GetAwardRecord`.
- API endpoints for these, refusals as data.
- Screens: D01, D01e (workspace), D02 (opinion), V01 (returned), V02 (source problem), V03 (expired report), V12 (signing unavailable), V18 (tie, synthetic tender 036), X07 (Return report dialog).
- Playwright: `awd-opinion.spec.ts` (from the sidebar and My Work to a signed opinion; reload and back/forward keep the record).
- **Gate AWD-G03:** `test_awd_intake.py`, `test_awd_opinion.py` green; `ui-awd-opinion-gate` green; slice boards compared; live check recorded.

### Phase 4: Accounting Officer decision and decision event (AC-004, 005, 007, part of 031)
- Services: `decision.py` `RecordAwardDecision` (Award / No award / Return for correction; only in Decision with the current signed opinion; positive action blocked by tie, unresolved discrepancy, unsupported funding or no current recommendation; supplier/bid/amount taken from the signed report, no picker or editor; submitted and evaluated amounts distinct; No award needs a concrete next action and owner; Return creates one **Resolve returned decision**); `decision_events.py` (`AwardDecisionRecorded v1` retained atomically per committed Award/No award; delivery to the receiver with retry; a return creates no event); notice preview set generated for the AO.
- Screens: D03 (decision), V04 (no award), X08 (Return for correction), X09 (Record no award).
- Playwright: `awd-decision.spec.ts`.
- **Gate AWD-G04:** `test_awd_decision.py`, `test_awd_decision_event.py` green; `ui-awd-decision-gate` green.

### Phase 5: Notices and authority status (AC-008, 009, 010, 014)
- Services: `audience.py` (reconcile every submitted tenderer; withdrawn/replaced treatment; no draft-only candidates; missing contact or unresolved treatment blocks issue with HOP as owner); `notices.py` batch generation and `IssueAwardNotices` (serialised with the cancellation guard, validity rechecked at issue); channel attempts and giving evidence; `RetryNoticeDelivery`; Correct contact via the owner command; `authority.py` `GetAwardAuthorityStatus` (decision status and notification status, historical references, Unknown on failure, never a fabricated negative) registered for `kt_award_authority_status`; Support Issue for service failure.
- Screens: V05 (delivery failure), V15 (rules unavailable), V15s (status service unavailable), V16 (technical incident: technical work view, no business data).
- Playwright: `awd-notices.spec.ts` (Award and notify → notices given → **All bidders have been notified**; the failure branch shows **A required notice is not yet confirmed.**).
- **Gate AWD-G05:** `test_awd_notices.py`, `test_awd_authority.py` (both interleavings of cancel and issue) green; `ui-awd-notices-gate` green.

### Phase 6: Supplier portal (AC-011, part of 012)
- The D14 surface and resolver; `supplier.py` `GetSupplierAwardNotice`, `RespondToAward` (signatory only; exact current notice version, `AWD_NOTICE_CHANGED` for a stale one; late responses stored as **Received after the deadline** with a HOP review; one operative acceptance per notice), `RequestAwardExplanation`.
- Screens at 390 px: D04 (successful notice), V13 (representative), V14 (unsuccessful, synthetic two-bid tender 037), V22 (late response), X01 (Accept award), X02 (Decline award), X11 (Request explanation).
- Playwright: `awd-supplier.spec.ts` (Mary accepts; David cannot; cross-supplier access fails without side effect).
- **Gate AWD-G06:** `test_awd_supplier.py` green; `ui-awd-supplier-gate` green.

### Phase 7: Clocks, eligibility and Contracting (AC-012, 013, 019, 021, 028)
- Services: `clocks.py` (reply deadline from the issued notice term, minimum wait from giving evidence per recipient, validity; before/at/after boundaries; delayed giving to a second bidder; lawful revision); `eligibility.py` `RefreshAwardEligibility` and the scheduler sweep; `delivery.py` `DeliverAwardPackage` (frozen package of exact versions, contract mappings, security terms and reservation lineage; eligibility-only declarations excluded; retry with the same package identity; a restriction arising during an outage blocks the retry); the V06/V07 **Record next action** path through `RecordAwardIssueDisposition` fixed to **Request decision review**.
- Screens: D05 (wait), D06 (delivered), V06 (declined), V07 (no response), V10 (receiver failure), X10 (Record next action).
- Playwright: `awd-wait-deliver.spec.ts` (the test clock moves to 2 Jul 09:00 → **Contracting has received the award.**).
- **Gate AWD-G07:** `test_awd_clocks.py`, `test_awd_eligibility.py`, `test_awd_delivery.py` green; `ui-awd-wait-gate` green.

### Phase 8: Debrief, restrictions and cancellation (AC-015, 016, 018, 020, 030)
- Services: `explanation.py` `SaveAwardExplanation`, `SendAwardExplanation` (closes only after dispatch evidence; a failure leaves it open and retries the same reply; a later request is a new linked record); `restrictions.py` `RecordExternalAwardRestriction` (Basis for hold: Authoritative order / Reported challenge), `ReceiveAwardRestriction`, `RecordAwardIssueDisposition` (only the §5.10 outcomes applicable to the issue; no free-text outcome or Override); a later restriction reaches the Contracting receiver as a separate update; `tender_events.py` consumes valid cancellation, suspension and validity-extension events (simulated owner events under the flag, as EVL did).
- Screens: D07 (explanation), D07c (closed), V08 (review hold), V11 (cancelled), X03 (Record restriction), X04 (Record outcome — order), X05 (Record outcome — reported challenge).
- Playwright: `awd-debrief-hold.spec.ts`.
- **Gate AWD-G08:** `test_awd_explanation.py`, `test_awd_restrictions.py`, `test_awd_cancellation.py` green; `ui-awd-debrief-gate` green.

### Phase 9: Corrections and decision cycles (AC-017, 029, 031)
- Services: `corrections.py` (post-decision correction or opening supplement → **Review report correction** / **Review opening update** plus an immediate hold; HOP's §5.10 outcomes); `RecordAwardCorrectionDecision` (Request corrected evaluation, Authorise reconsideration, Record corrected award, Record no award, Return for correction, Decline reconsideration, Authorise revised notices; successor cycle on the same case; corrected decisions send nothing until the exact revised batch is authorised; the combined **Record corrected award and notify bidders** records one decision and the batch; one decision event per new committed decision; correction after a Closed cycle creates review only).
- Screens: V09, V17, V19, V20, V21, V23, V23p, V24, V25, X06.
- Playwright: `awd-correction.spec.ts` (one cycle-2 path).
- **Gate AWD-G09:** `test_awd_corrections.py`, `test_awd_cycles.py` green; `ui-awd-correction-gate` green.

### Phase 10: Access, dead ends and retries (AC-022, 024, 025)
- Per-actor DTO filters: HOP, AO, supplier signatory, supplier representative, other supplier, auditor (Naomi, read only, no unrestricted export), technical reader (safe operation identifiers only), public (nothing; no public URL for the internal record). Protected reads return Not found and are audited.
- The full My Work matrix checked against `next_step_register.md`; technical-read resolver and probe (`kt_technical_reference_resolvers`, `kt_technical_read_probes`).
- `test_awd_leakage.py`, `test_awd_dead_end.py` (every stored stage × condition × actor through `next_step.problems`), `test_awd_idempotency.py` (repeated commands, out-of-order events, stale revisions, uncertain signing).
- **Gate AWD-G10:** `make awd-leakage-gate` and `make awd-dead-end-gate` green.

### Phase 11: Canonical seed stage and demo profiles
- Stage `award` after `bid_evaluation` in `kentender_core/seeds/canonical.py` (`STAGES`, `seed()`, `validate()`), in `award/seeds/kentender_mvp_v1.py`. It drives the §13 ordinary path through the real commands on the real EVL delivery of TND-MOH-2027-002: receipt 16 Jun 14:07:01, opinion signed 17 Jun 09:10, decision and test notices 10:00, Mary accepts 18 Jun 09:00, delivery at 2 Jul 09:00 on the test instant. A second run returns the same identities without new audit transitions.
- Demo profiles in `award/seeds/profiles.py` (`make seed-awd-profile PROFILE=`, `seed-awd-profiles`, `seed-awd-profile-restore`), one per main stage.
- `tests/ui/smoke/award/awd-demo-walk.spec.ts`: walked from the sidebar, My Work and the bell, one browser session per person.
- **Gate AWD-G11:** `make seed-canonical SITE=kentender.midas.com THROUGH=award` and `make seed-canonical-validate` green; the second run idempotent; the demo walk green.

### Phase 12: Release evidence
- `ui-awd-fidelity-gate` over all 47 boards (compared or recorded as not compared with a reason).
- The ordinary path and the §13 branch matrix: for each row, compare the visible control, server command, event, My Work item, disclosure and clearing transition.
- A persona browser pass as real users: Charles, Amina, Mary, David, Esther/Daniel, Naomi, Administrator.
- AC map closure; `RUNBOOKS.md` (simulation switches, fixture reset, source-issue recovery, notice retry, Contracting receiver retry).
- One cross-module regression run (EVL, Tenders, BDS services and the procurement UI smoke), justified here because it is release time.
- **Gate AWD-G12:** `ui-awd-release-evidence-gate`.

### Phase 13 (owner-gated; every row starts `Blocked — owner`)
- Owner-document amendments owed under OD-A, each written as a Proposed document under the document-change protocol: EVL (award seam, take-up, decision-status source), TPR (post-close cancellation, tender-level decision/notification status, serialised guard, validity extension event), BDS (audience, signatory action, contact correction receipt, supplier award route), PRC (indexing of Award records), KT-STD-001 v1.13 (Mary Wanjiku, Daniel Otieno as technical operator, Jirani as synthetic), SEED-OPS-001 (`award` stage), a Contracting counterpart document (AWD-IF-05 operations), register interface rows IF-017/018/019.
- AWD v0.4 approval by the Project Owner, and any delta it brings.
- LAW-V-001 and the verified legal operating profile (§15 production gates).
- Real signing (TRUST-ADR-001), real notice channels and giving evidence, a real Contracting receiver.
- A security review and production enablement.
- **No gate in this plan.**

## Conflicts and follow-ups to log (Phase 0)

| # | Conflict | Treatment |
|---|---|---|
| C1 | AWD v0.4 is *Proposed*; the counterpart contracts AWD-IF-01…07 exist in no owner document. | OD-A. Build to v0.4; FU-AWD-01…08; addendum rows in the EVL, TPR and BDS trackers. |
| C2 | The canonical tender is TND-MOH-2027-002; the boards and §10.1 use TND-MOH-2027-033/036/037 and AWD-MOH-2027-033. | Board literals are fixture data (as EVL C21). The canonical stage uses the actual source facts; synthetic fixtures reproduce 033/036/037 for the fidelity capture. |
| C3 | Tenders has no post-close cancellation, suspension, validity-extension event or tender-level decision/notification status (`_require_open`). | D5 guard hook and status delegation; simulated owner events under the flag (as EVL D16). FU-AWD-02. |
| C4 | PRC `record_versions` needs a proceeding roster and profile; the opinion has one signer and no proceeding. | D6: `signing.attest` directly; no PRC change. PRC indexing of Award records is FU-AWD-04. |
| C5 | AWD §9 names `/supplier/awards/{notice_id}`; no `/supplier` portal prefix exists. | D14: new surface registered through `kt_portal_surfaces`. FU-AWD-03 records it in BDS. |
| C6 | No Contracting module exists. | D10: synthetic receiver under the flag; production shows Waiting to proceed. FU-AWD-05. |
| C7 | No verified legal operating profile exists (§15). | D8: simulation test profile only; production gives `AWD_RULE_UNVERIFIED`. FU-AWD-09. |
| C8 | Jirani Office Supplies Limited is not seeded. | Synthetic recipient with seeded contact evidence (§13 says exactly this); no new human actor. |
| C9 | Daniel Otieno is a technical user; My Work skips technical users. Esther Njeri also holds Technical Operator. | D12: Support Issue rows (Esther in My Work, Daniel in the technical work view, V16). FU-AWD-06 (KT-STD actor note). |
| C10 | EVL already creates "Review evaluation report for {ref}"; AWD §3 says it becomes the same work item. | D5 `take_up`: EVL's row stops when Award receives the report. |
| C11 | A Page whose module names a real Module Def can swap the sidebar on record routes. | D13: check in Phase 1; set Page.module as EVL did. |
| C12 | EVL stores amounts as decimal strings; §15 requires exact published precision. | `Decimal` KES from the frozen report; never recomputed or written back; submitted and evaluated shown distinctly. |
| C13 | AWD §15 says "Persist timestamps in UTC"; the owner's standing rule (AGENTS.md §4.4) is site time with UTC only in serialized messages. | Follow AGENTS.md §4.4; `AwardDecisionRecorded v1` payload times in UTC via core instants helpers. FU-AWD-07. |
| C14 | The "Evaluation and Award" workspace and the `evaluation_award` skeleton are placeholders. | D1: skeleton deleted; workspace left alone. |

## Risks

- **Stand-in drift from the real Evaluation output (OD-B).** Mitigation: the synthetic provider implements the same `sources.py` interface; `test_awd_seams.py` checks the real seam's shape against the synthetic one field by field; the canonical stage and demo walk run on the real delivery.
- **Upstream regression from the seam hooks.** Mitigation: additive files and one-line hook calls only; each upstream edit reruns exactly its one affected test module; full cross-module run only at release.
- **Legal-rule overreach.** Mitigation: every time and channel rule comes from the profile; no hard-coded periods; production shows `AWD_RULE_UNVERIFIED`.
- **Double approvals creeping in.** Mitigation: the tracker's prohibited-controls rule and the command map (every control → one command).
- **Leakage** of other bidders' facts to suppliers, or business facts to technical readers. Mitigation: per-actor DTOs and the Phase 10 leakage gate.
- **Site-wide test mutation.** Mitigation: Award tests write only namespaced Award rows and clean up; the integration module uses years ≥ 2100; never run Python and Playwright together.
- **A stand-in mistaken for production.** Mitigation: stand-ins load only under the simulation flag; `source_kind` and test labels are visible at runtime.

## Verification

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.award.tests.<module>
./scripts/bench-with-node.sh build --app kentender_procurement
cd apps/kentender_v1
make awd-services-gate            # synthetic sources; target under 3 minutes
make awd-seams-gate               # seam contracts + integration on real EVL output; phase gates only
make awd-leakage-gate
make awd-dead-end-gate
make ui-queue-check
make ui-awd-<slice>-gate
npx vitest run --project award    # also inside make ui-structure-gate
make ui-awd-fidelity-gate
make ui-awd-release-evidence-gate
make seed-canonical SITE=kentender.midas.com THROUGH=award
make seed-canonical-validate SITE=kentender.midas.com
```

**Live browser walk (Phases 11–12), under the simulation flag, on the canonical tender:**
1. Charles opens **Awards** from the sidebar, sees **Prepare professional opinion**, and signs **Professional opinion 1**. EVL's "Review evaluation report" row is gone.
2. Amina opens **Decide award** from My Work, sees the submitted and evaluated amounts, and chooses **Award and notify bidders**. There is no separate notice approval.
3. Mary, at 390 px, opens her notice from the portal and accepts. David sees **Mary Wanjiku must respond for Afya Digital Supplies Limited.** and cannot accept.
4. Charles sees **The required waiting period is still running.** and **All bidders have been notified**.
5. The test clock moves to 2 Jul 2027 09:00; Charles sees **Contracting has received the award.** and **Next: Prepare contract**.
6. Naomi reads the record only. The technical operator sees operation status only, with no tender, supplier or price.
7. Repeat the §13 branches on their own synthetic fixtures: source problem, return, expired validity, tie, delivery failure, decline, no response, late response, debrief, hold, cancellation, correction cycle, receiver failure.

## Build findings (1 October 2026)

These are recorded here; the phase text above is not rewritten.

| # | Decision | Why |
|---|---|---|
| D17 | **Award rows inherit the Evaluation case's fixture namespace** (the canonical award is stamped `KENTENDER_MVP_1_R1_EVL`; a test world's award is stamped with that test world's namespace). Evaluation's `clear.wipe` calls `kt_evaluation_removal_consumers`, so an award is removed with its evaluation. | An award exists only because of its evaluation; the Evaluation test suites and browser worlds, which now trigger Award automatically, leave no Award rows behind (checked after `evl-ordinary-path`). |
| D18 | **The report digest is verified the owner's way**: Evaluation's `content_digest` is `records.digest` over the frozen JSON text, not the parsed object. | `test_awd_seams` failed on the real report until the seam used Evaluation's own rule. |
| D19 | **Receipt time is never before the delivery it receives** (the later of the trusted clock and the delivery instant). | Seeds replay 2027 fixture instants while the real clock is 2026; an automatic receipt must not predate the delivery. |
| D20 | **The Head's Evaluation review row ends when Award receives the report** (§3 "one work item"); Evaluation's record then shows its existing line "The committee report was sent to … on …" to the Head. `test_evl_report` and the `evl-ordinary-path` / `evl-demo-walk` browser specs were updated to expect this. | The spec forbids two acknowledgements of one report. |
| D21 | **The controlled post-decision correction route** is `correction.return_for_authorised_correction` in Evaluation: allowed only when Award's authority status names the AO's recorded correction instruction; it reuses the ordinary return's effect (`_apply_return`). | EVL-CHG-001 names the route but has no command for it; the ordinary return is rightly refused after a decision. FU-AWD-15. |
| D22 | **A No award decision closes the issues it answers** (validity, funding, supplier response, incomplete source); restrictions stay with their own authority. | Found by `test_awd_reads`: the "Resolve expired validity" task outlived the AO's No award. |
| D23 | **Notices are HTML letters**, deterministic and digest-bound; no PDF. **Correct contact** reads the contact owner's corrected address and retries the same notice; Award has no contact editor (§10.3). | FU-AWD-13, FU-AWD-19. |
| D24 | **Dialog boards (X01–X11) are compared dialog for dialog**; the live dialog opens over the page the user was on, not over the board's bare header. | Keeps the comparison strict where the board is specific, without registering 11 identical departures. |
| D25 | **Browser slices followed the service phases instead of interleaving with them**: all services were built and unit-tested on the synthetic sources first (93 tests in about a minute), then one board renderer and the seven slice specs. The renderer is shared by all 47 boards, so a slice-by-slice UI would have rebuilt the same component seven times. The first browser run found one real UI defect (the closed request's screen name), fixed the same hour. | A deliberate change from rule 13 of the tracker, recorded here. |
