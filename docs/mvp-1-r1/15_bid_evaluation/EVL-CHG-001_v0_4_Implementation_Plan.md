# EVL-CHG-001 v0.4: Bid Evaluation, implementation plan

| Control | Value |
|---|---|
| Version | 0.4-plan.1 |
| Date | 30 September 2026 |
| Authority | `KenTender_EVL-CHG-001_Bid_Evaluation_v0_4.md`: "**Approved by Project Owner — 30 September 2026**, including R1–R3 minor corrections" (EVL v0.4 line 6). "Implementation and verification remain Not started; release remains Not approved. Coordinated amendments to other owner documents remain outstanding" (EVL v0.4 line 752). |
| Governing standard | KT-STD-001 v1.12, approved 30 Sep 2026 (`../00_common/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_12.md`). |
| Upstream authorities (as cited by EVL v0.4 lines 8–9) | TPR-CHG-001 v0.13; STD-TPL-001 v0.10 (the latest approved is v0.13, see C17); BDS-CHG-001 v0.8; BOP-CHG-001 v0.10; PRC-CHG-001 v0.9; TRUST-ADR-001 v0.1. All approved. None yet carries the Evaluation amendments EVL v0.4 §6 and §12 require (C1). |
| Design | `design/Bid Evaluation Artboards.dc.html` with `design/evl/evl-kit.js`, `design/evl/boards-1.js` … `boards-5.js`, `design/support.js` and the `_ds/kentender-industry-…` Industry bundle. The registry `window.EVL.boards` holds **107 drawn boards and no note-only entries**: 76 carry a spec note and 6 draw a dialog. 99 are drawn at 1440×1024, 7 supplier boards at 390×844 and one comparison board (D03-TIE) at 1024×768. |
| Companions | `EVL-CHG-001_v0_4_IMPLEMENTATION_TRACKER.md`; `EVL-CHG-001_v0_4_FOLLOW_UPS.md`. Phase 0 adds `reconciliation/{artboard_inventory, error_contract, handoff_register, fixture_chronology, rule_reconciliation, scope_binding}.md`. Later: `evidence/v0_4/` and `RUNBOOKS.md`. |
| Predecessor | None. This is the first Bid Evaluation plan. |
| Prepared | 30 September 2026 |
| Status | Planned. No code has been written. |

## Context

**Why this module now.** Bid Opening (BOP-CHG-001 v0.10) is built and gated: its tracker records BOP-G00 to BOP-G11. On a completed nonempty opening it writes one `Evaluation Handoff` per Tender, with `consumer = "evaluation"` and `delivery_status = "Pending"`, and nothing reads it (FU-BOP-11, FU-BOP-12). Evaluation is the next step in the traceability chain: Tender → Bid → Opening → **Evaluation** → Head of Procurement review and Award, both downstream. It is also the second user of the shared Proceedings record. EVL v0.4 §6 requires a separate Evaluation profile with several discussion sessions and report signing targets.

**The MVP contract (EVL v0.4 §1).** "KenTender evaluates bids against the published rules automatically. Committee members resolve matters requiring judgment, review the conclusions and personally sign the report. They do not repeat completed automatic checks." The scope is Open Tender, IT Goods, one lot, KES, fixed price, lowest evaluated responsive. There are no weights, scores, editable criteria or AI decisions. Evaluation produces a recommendation, never an award.

### Current state (verified 30 September 2026 by reading the source)

**Evaluation.** No code exists.
- `kentender_procurement/kentender_procurement/evaluation_award/` is an empty package skeleton.
- The workspace `evaluation_and_award.json` ("Evaluation & Award") has no links.
- In `workspace_sidebar/procurement.json` (lines 120–143), "Evaluation" and "Awards" both route to page `coming-soon`.
- There are no `EVL_` codes, no `bid_evaluation` module and no `/app/bid-evaluation` route anywhere.
- The legacy TM2 records and the roles `Evaluation Committee Member` / `Evaluation Coordinator` are listed for removal in `kentender_core/seeds/mvp1_role_user_cleanup.py:69-70` and are not reused.

**What Bid Opening gives Evaluation.** The handoff is written in `bid_opening/services/completion.py:49-73`.
- The record is `Evaluation Handoff`, with ID `EV-IN-<reference without TND->-01`, unique per Tender.
- Its payload (`_handoff_payload`, lines 30–46) contains:
  - `packages[]`, each with `entry`, `number`, `envelope_id`, `receipt_reference`, `submission_version`, `package_digest`, `render_digest`, `bid_definition_id`, `definition_version`, `definition_digest`;
  - `register {register_id, digest}`;
  - `opening_record {minutes_version, digest}`;
  - `exceptions[]` (with `for_evaluation`).
  It carries no bidder name, total or security; those live on `Opening Entry`.
- **The digest does not verify as stored.** `payload_json` is compact JSON, but `handoff_digest = records.digest(payload)` uses the default separators, so `sha256(payload_json) ≠ handoff_digest` (C5).
- No handoff is written for **No bids** (`finish.end_with_no_bids`), **Not held** or **Cancelled after start**.
- Completed-record corrections (`services/correction.py`, four kinds) append a PRC supplement and notify no consumer.
- `appointment.is_excluded_from_evaluation(tender, user)` exists (`services/appointment.py:55-61`) and is not exposed through the API.

**Bid content.**
- The `kt-bds-package/1` package (`bid_submission/services/package.py:96-140`) holds:
  - `responses[{response_id, field_key, member, evaluation_mapping_id, value}]`;
  - `evidence[]` (files in base64);
  - `price {currency, subtotal, tax, total, lines[]}`;
  - `signatory`;
  - `organisation_snapshot`.
- Bid Submission never stores the bytes.
- They are released only through `bid_submission/services/opening_gateway.py::reveal_envelope`, which requires the opening custody release. In simulation they sit in `TestTenderBox` (`private/kt_test_tender_box/`).
- Bid Opening keeps only rendered PDFs (`private/kt_bop_renders/`).
- **No seam lets Evaluation read an opened package** (C4).

**Proceedings v0.9 code is opening-shaped** (C6).
- `proceeding_type` has the single option "Bid Opening", hard-coded in `create_proceeding`.
- `owner_key` is unique and the ID is `PRC-{owner}`. There is one `actual_start` and one `actual_end`, and the lifecycle runs Pending → In session → Session ended → Awaiting attestations → Finalized.
- `events.PRE_SESSION_TYPES` is fixed.
- Minutes require `register_reference`/`register_digest`.
- `minutes.TARGET_TYPES` lists only opening page types.
- The attendance capacities include tenderer representative and public observer.
- The error wording says "opening".
- Reusable as they stand:
  - the owner adapter hook `kt_prc_owner_adapters` (`exists`, `allows(owner_id, user, capacity)`);
  - the signing hook `kt_trust_signing_services`, whose generic `attest(member, target_id, target_digest, minutes_version, action, correlation_id)` has a test double in `proceedings/test_services/attestation.py`;
  - the command journal.

**Template rules** (`docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/06_runtime/`).
- `product_profile.json` defines:
  - the four `evaluation_groups`;
  - the validations catalogue (`VAL-INTEGER-RANGE`, `VAL-DECIMAL-RANGE`, `VAL-DATE-RANGE`, `VAL-OPTION-IN-LIST`, `VAL-PORTS`, `VAL-EVIDENCE-COUNT`, `VAL-CONFIRMED`, …);
  - the controls;
  - the calculations (`CALC-LINE-TOTAL`, `CALC-TENDER-TOTAL`, exact decimals at 2 places).
- `downstream_rules.json` maps the 25 `RR-*` rules to `DM-*` mappings:
  - `EVG-ELIGIBILITY` has 13 rules;
  - `EVG-FINANCIAL` has `RR-PRICE-GOODS` and `RR-PRICE-SERVICE`;
  - `EVG-AWARD` has none;
  - "Not evaluated" covers `DM-DOC-ACK`, `DM-SUPPLIER-DETAILS` and `DM-JV-MEMBER`.
- `evaluation_result_rule` is a sentence only. **No executable rule file exists.**
- The published `Tender Bid Definition.definition_json` (read with `tenders/services/bid_definition.py::definition_for(tender, version)`, line 450) carries `response_rows`, `evaluation_mappings`, `price_rows` and group `published_facts` with `comparison`, `control`, `required_value` and `unit`. Examples:
  - TECH-003: Minimum, INTEGER 16 GB;
  - WS-RESPONSE-TIME: Maximum 8 hours;
  - TECH-011: Required ports;
  - TECH-008: free text "minimum 10 cores or equivalent" (C13).

**Tenders.**
- `TenderOpenForSubmission` (`tenders/services/publication.py:174-181`) is an outbox event for consumer `bidder-service`.
- `TenderCancelled` has no consumer. `_require_open` (`cancellation.py:52`) allows no cancellation after close.
- There is no suspension, validity-extension or award-decision fact.
- `bid_definition.projection()` (lines 182–280) hard-codes `procurement_method: "Open Tender"`, `currency: "KES"` and a single lot.
- Tender validity comes from the officer's `tender_validity_days` through `serializer.derived_dates()`. The evaluation period is the core procurement setting `evaluation_period_days` (30; milestone `evaluation_completion`).
- The read-seam precedent is `tenders/services/opening_seam.py`.
- `public/js/tenders/Tenders.vue` delegates `sub === "opening"` to `bid_opening.bundle.js` (`frappe.kt_mount_bid_opening`), and `public/js/tenders_page.js` lists that bundle.
- The Tender record takes links from the `kt_tender_record_links` hook.

**Budget.** There is no published contract for evaluation funding. `kentender_budget/services/budget_downstream_contracts.py:43 get_funding_lineage(reservation=…)` returns each reservation's original and remaining amounts. The Tender's reservations come from `tenders/services/snapshot.internal_context(snapshot).reservation_ids` (C11).

**Shared runtime available:**
- `kentender_core.desk_page` (`register`, `useRoute`, `createCommandRunner`, `createSequenceGuard`, `createScreenCache`, `addLeaveGuard`);
- `kentender_core.industry` (`mountPageRail`, `mountGuidance`, `mountJourney`);
- `kentender_core/services/next_step.py` (`answer`, `guard`, `blocker`, `holder`, `since`, `for_viewer`, `problems`, `journey`, kinds `your_turn`, `your_turn_blocked`, `waiting`, `timed`, `done`, `not_involved`);
- `kentender_core/services/my_work.py` (`kt_my_work_providers`);
- `kentender_core/utils/instants.py`;
- `audit_event_service.log_audit_event`;
- `notification_service.emit_notification_log`;
- `file_integrity` (20 MB; pdf/png/jpg; magic-byte sniffing);
- supplier authority `bid_submission/services/bid_authorization.py::acting_assignment`;
- portal surfaces `kt_portal_surfaces` (`bid_submission/portal.py::resolve`), with the BOP public-opening section resolver as precedent;
- supplier message transports `kt_bds_supplier_message_transports`;
- the BOP command envelope `bid_opening/services/records.py`.

**There is no platform support-issue record** (C2). Bid Submission and Bid Opening each have their own incident record (`Bid Submission Incident`, `Opening Access Incident`). The Technical Operator role is registered (`business_role_registry.py:226`) and held by Daniel Otieno.

**Personas** (KT-STD-001 v1.12 §8.3 and seeds; C3):

| Person | Registered in §8.3 | Seeded | Note |
|---|---|---|---|
| Amina Hassan | Yes, Accounting Officer | Yes | |
| Charles Mutiso | Yes, Head of Procurement Function | Yes | |
| Naomi Chebet | Yes, Auditor | Yes | |
| Brian Wafula | Yes, as "Procurement Officer, site-wide — Tender Preparation only" | Yes | |
| Samuel Otieno | Yes, as "Head of User Department, expired" | Yes | |
| David Ouma | No (supplier person) | Yes, for Afya Digital Supplies Limited | |
| Grace Wambui, Peter Mugo, Ruth Achieng, Esther Njeri | No | No | |
| Jirani Office Supplies Limited | n/a (supplier) | No | |

**Seeds.** `kentender_core/seeds/canonical.py:49` `STAGES` ends at `bid_opening`. The canonical opening's handoff is left `Pending` (`bid_opening/seeds/kentender_mvp_v1.py:241`).

**Done means:**
- Every EVL v0.4 §7.2 command and §7 read is built as a server service with idempotency, expected version, trusted time and audit.
- The Proceedings Evaluation profile (§6) is built without changing Bid Opening behaviour.
- Every §7.3 hand-off row has its My Work item, notification and clearing event, each with a named test.
- All 107 boards are ported class-for-class and pass the fidelity gate.
- The canonical Afya tender (TND-MOH-2027-033) is evaluated end to end in a browser by its real personas under the simulation flag, to **Report sent**. The §11.2 branches are each proven on their own fixture.
- EVL-A01 to EVL-A17 are honestly marked. Production-only parts stay `Blocked — owner`.
- No award, supplier notification or contract action exists anywhere in the module.

## Owner decisions (this session, 30 September 2026)

| # | Decision |
|---|---|
| OD-A | **Build first, amend later.** Owner answer, verbatim: "Build first, amend later". The option chosen read: "Build to the Evaluation spec only, and log the other documents' amendments as follow-ups to write after the build. This is fastest, but the other documents lag behind the code." The Proceedings v0.10, Tenders, Bid Submission, STD-TPL, BOP cross-reference, Budget and KT-STD v1.13 amendments are follow-ups written in Phase 15. They block no phase. Every seam added to another owner's code is recorded as an addendum row in that owner's tracker when built. |
| OD-B | **Support issues.** Owner answer, verbatim: "New shared core record (Recommended)". The option chosen read: "Add a small Support Issue record and assignment route to kentender_core, used first by Evaluation. Bid Opening and Bid Submission move to it later, logged as a follow-up rather than done now. This matches the spec's wording." |
| OD-C | **Rule meaning.** Owner answer, verbatim: "Versioned file in the template pack (Recommended)". The option chosen read: "Add an evaluation-rules file to the IT-EQUIPMENT-OPEN-V1 release, one entry per mapping, installed with the release. Evaluation reads it together with the published tender's values. Needs an STD-TPL amendment; the rules become part of the curated template, as the spec says." |
| OD-D | **Where the stand-ins run.** Owner answer, verbatim: "Yes, same as Bid Opening (Recommended)". The option chosen read: "The stand-ins load only with kt_bds_simulation_environment set. Real signing stays deferred under TRUST-ADR-001, and test proofs are labelled as test proofs only under that flag." |

## Key technical decisions (implementation authority unless the owner says otherwise)

| # | Decision |
|---|---|
| D1 | **Module.** Add a new `bid_evaluation` module to `kentender_procurement`, with `doctype/`, `services/`, `api.py`, `tests/`, `test_services/` and `seeds/`, and add it to `modules.txt`. Follow the new-module procedure: after the first migrate, clear the cache, check that the Module Def has `app_name = kentender_procurement`, then migrate again. The empty `evaluation_award` skeleton stays for Award. `bid_evaluation` never imports internals of `bid_opening`, `bid_submission`, `tenders` or `kentender_budget`. It uses only their published seams (D5, D6, D8, D9). `proceedings` never imports `bid_evaluation`. |
| D2 | **Doctypes (EVL v0.4 §6.1 names).**<br>• `Evaluation Case`: one per Tender, with state Preparing / Reviewing / Signing / Report sent / No evaluation required / Cancelled. Conditions are fields, never states: suspended, overdue, validity expired, checking.<br>• `Evaluation Appointment`, with child `Evaluation Committee Member` (person, department, designation, capacity Chair/Member, status Current/Replaced/Ended, successor, reason, appointment reference).<br>• `Evaluation Secretary Appointment`, `Evaluation Declaration`, `Evaluation Member Unavailability`.<br>• `Evaluation Source Intake` and `Evaluation Bid` (one per opened bid; references and digests only).<br>• `Evaluation Check Run` and `Evaluation Check Result` (one result per run, bid and requirement).<br>• `Evaluation Finding` (finding or concern; `prior_finding`; never overwritten), `Evaluation Discussion Item`, `Evaluation Conclusion`, `Evaluation Disagreement`.<br>• `Evaluation Clarification` and `Evaluation Clarification Reply` (draft or sent; one sent reply per request).<br>• `Evaluation Verification Plan`, `Evaluation Verification Observation`.<br>• `Evaluation Report Version` (narrative, frozen content, digest, outcome, supersession), `Evaluation Report Delivery` (delivery key = evaluation + version).<br>• `Evaluation Source Event` (opening supplement, suspension, resumption, cancellation, validity extension, award decision), `Evaluation Correction Notice`.<br>• `Evaluation Command Journal`, and the Single `Bid Evaluation Settings` (presence lapse, a technical value).<br>**All of them follow BDS D12 / BOP D2:** `validate()` refuses unless `flags.kt_evl_command` is set; `on_trash` refuses unless `flags.kt_fixture_wipe` is set; `has_permission` and `permission_query_conditions` deny. System Manager has technical read only (KT-STD-001 §3A.6). The journal and Settings have no role. Reads go only through services. |
| D3 | **Command envelope.** `bid_evaluation/services/records.py` mirrors `bid_opening/services/records.py`:<br>• `command(name, *, tender, idempotency_key, actor, payload, body)` journals the command; a replay returns the original result and a conflicting replay has no effect;<br>• `check_version` raises `EVL_VERSION_CONFLICT`;<br>• also `atomic`, `lock(tender)`, `bump`, `digest`, and `prc_owner.acting(case)`.<br>`errors.py` holds the closed EVL v0.4 §8 set verbatim: 15 blocking codes plus `EVL_REPLY_OVERDUE` and `EVL_EVALUATION_OVERDUE` as nonblocking conditions. Messages come with separate `detail` (names, dates, reasons, recovery), and every applicable guard is returned together, never serial blockers (EVL v0.4 §8 opening paragraph). `from_prc` maps Proceedings errors to Evaluation copy.<br>`clock.py` reads `frappe.flags.kt_evl_clock`, then the core test clock, then now. Instants are stored in site time; UTC is used only in cross-module payloads through `instants.py` (AGENTS.md §4.4). Audit goes through `log_audit_event`. |
| D4 | **Proceedings Evaluation profile** (EVL v0.4 §6 "PRC change is explicit"). The change is additive, and Bid Opening behaviour and tests stay unchanged.<br>• `proceeding_type` gains the option "Bid Evaluation", supplied by the owner adapter instead of hard-coded.<br>• A new `Proceeding Session` doctype (session number, started by, actual start and end, state), with attendance and events linked to a session. The Opening profile keeps one implicit session.<br>• Profile rules move into `proceedings/services/profiles.py`, keyed by type: pre-session event types, whether a register reference is required, allowed target types, the event-reference completeness rule, the attendance capacities, and the wording.<br>• New target types: `Report signature`, `Verification report page`, `Verification report signature`.<br>• Logical operations (EVL v0.4 §6): `CreateEvaluationProceeding`, `StartEvaluationDiscussion`, `JoinEvaluationDiscussion`, `LeaveEvaluationDiscussion`, `RecordEvaluationConclusion`, `EndEvaluationDiscussion`, `FreezeEvaluationReport`, `RecordEvaluationProof`, `SupersedeEvaluationReport`, `CompleteEvaluationRecord`, `AppendEvaluationCorrection`, and scoped read and export.<br>• There is one Proceeding per Evaluation Case. The due-diligence report is a second record-version kind in the same Proceeding.<br>• Only one session may be active per evaluation, and there is no group attendance action (§6 owner-event table).<br>Proceedings stores evidence and checks owner bindings. It cannot rank, approve findings or supply signatures (§6). |
| D5 | **Opening intake binding.** A new seam, `bid_opening/services/evaluation_seam.py`, provides:<br>• `completion(tender)`, which returns the handoff with its digest verified by recomputation from the parsed payload (fixes C5 without rewriting stored handoffs);<br>• `acknowledge(handoff_id)`, which sets `Delivered` once;<br>• `final_outcome(tender)`: Bids opened / No bids / Not held / Cancelled / Incomplete;<br>• `register_rows(tender)`, for cross-checking only;<br>• `supplements(tender, after)`;<br>• `is_excluded_from_evaluation(tender, user)` (closes FU-BOP-11).<br>Bid Opening completion calls a new hook, `kt_opening_completion_consumers`, which is enqueued after commit, on both the nonempty handoff and the final no-bids outcome. A scheduler sweep, `bid_evaluation/services/sweep.py` (every minute), recovers a missed intake or publication preparation and marks the overdue and expiry conditions. The sweep and the hook use the same operation identity. BOP tracker addendum rows record each addition. |
| D6 | **Opened-package seam.** A new `bid_submission/services/evaluation_gateway.py::released_package(tender, envelope_id, completion_ref, correlation_id)`.<br>• It releases a package only after a verified Bid Opening completion names that envelope, and verifies the package digest against the handoff.<br>• It returns exactly one TRUST-ADR-001 §4 outcome (`Unavailable`, `Rejected`, `Indeterminate`, `Accepted/Verified`) with one correlation identity.<br>• In simulation it reads `TestTenderBox`. With no production adapter it returns `Unavailable`, which becomes `EVL_SOURCE_INCOMPLETE` plus an automatic Support Issue (§5.1).<br>Evaluation stores no package bytes. A check run keeps, immutably, the input values it compared as calculation detail. Evidence files stream through the scoped `ReadEvaluationEvidence` read and never become a File URL; bytes are handled through `file_integrity`, not `save_file`/`get_file`. BDS tracker addendum row. |
| D7 | **Executable rules (OD-C).**<br>• Add `06_runtime/evaluation_rules.json` to the IT-EQUIPMENT-OPEN-V1 pack, with `rules_version`, `template_key`, `applies_to_release_ids` and one entry per evaluated mapping and response identity. Each entry gives:<br>  – the kind: presence, declared boolean, permitted choice, numeric minimum/maximum, date condition, published calculation, evidence assessment, or manual;<br>  – the unit, rounding and inclusive boundary;<br>  – the date anchor;<br>  – any explicit published alternatives;<br>  – whether an evidence assessment is also required.<br>• It is installed as an `Installed STD Release Asset` without changing any published definition digest, and is checked by `validate_release.py` and by `std_templates/tests/vectors`.<br>• The engine `bid_evaluation/services/rules.py` is pure functions. Comparison values come only from the published `definition_json`, never from the rules file.<br>• A missing or conflicting rule gives **Needs review** with `EVL_RULE_UNAVAILABLE` and no default. Free text and "or equivalent" become an evidence check (§4.1).<br>• `aggregate.py` implements §4.2: group result, combined requirement (a response comparison can read Meets while its evidence assessment is unresolved), and bid Responsive / Not responsive / Needs review.<br>• A rule-implementation correction reruns every affected bid and keeps the prior run (§4.1, §7.2 `RunEvaluationChecks`). |
| D8 | **Tenders seam.** A new `tenders/services/evaluation_seam.py`:<br>• `evaluation_candidates()` and `publication_fact(tender)`: publication identity and version, tender reference, publication time, and definition reference;<br>• `scope_facts(tender)`: one value per §5.1 predicate with its published source (C7);<br>• `dated_rules(tender)`: evaluation deadline and validity end, each with its source, counting rule and timezone (§5.7, C10);<br>• `status_events(tender, after)`: cancellation, plus suspension, validity extension and award decision once Tenders can produce them;<br>• `award_decision_status(tender)`: an authoritative "No award decision recorded" read from Tender status, or `Unknown` when the read fails. It is never inferred from an absent consumer (§6).<br>Branches Tenders cannot produce under TPR v0.13 (post-close cancellation, suspension, validity extension, award recorded) use simulation-only owner events, as in BOP D8. The Tenders tracker gets an addendum row. |
| D9 | **Financial comparison.**<br>• Amounts are exact `Decimal` KES. The submitted total comes from the package price and is never written back.<br>• Evaluation adjustments come only from a published rule. This template has none, so they show as **None**.<br>• No preference margin is applied: the site's MSME 15% regulatory reference is not a published rule of this tender (C12).<br>• Only responsive bids with resolved financial checks are ranked, and equal evaluated totals share a rank.<br>• With no published tie-break the outcome is **No single recommendation — equal evaluated totals**. **Provisional comparison** labels the table while unresolved bids could change the outcome. A nonresponsive bid shows **Not assessed — mandatory requirement not met** and **Not ranked**.<br>• Funding is a read-only comparison through `get_funding_lineage` over the tender's reservations. A shortfall only qualifies the report (§4.4, C11). |
| D10 | **Next steps and journey.** `bid_evaluation/services/next_steps.py` uses core `answer`, `guard`, `blocker`, `holder` and `journey` with stages Prepare / Review / Report. The per-actor tracker codes are those of §9.1, including blocked markers for suspension and cancellation. There is no tracker on the workspace, dialogs, supplier pages or the standalone declaration. KT-STD-001 §3B precedence applies: actionable work before waiting, all genuine blockers together with their named fix, and a system job is not "waiting on a person" (§7.1). |
| D11 | **Work items.** `bid_evaluation/services/my_work_provider.py` is registered in `kt_my_work_providers`. Its rows are derived purely from state for every internal row of the §7.3 hand-off table, keyed by (evaluation, source event, recipient responsibility), so that concurrent supplement and correction tasks never collide or clear each other (§5.6). Opening or reading never clears an item. Replaced members' unperformed tasks close as replaced (§7.3). Suppliers have no Desk task: the Bid Submission bid overview shows the request through `kt_tender_portal_links`, and the courtesy email goes through `kt_bds_supplier_message_transports` with truthful delivery status and retry (§5.3). Internal courtesy notices use `emit_notification_log` with correlation keys. |
| D12 | **Core Support Issue (OD-B).**<br>• A new `kentender_core` doctype `Support Issue` with these fields: `issue_key` (unique: module + operation correlation), module, operation, safe reference, safe detail, holder role (Technical Operator), holder users, status Open/Resolved, opened_at, resolved_at, notification state and attempts.<br>• `kentender_core/services/support_issues.py` provides `open_issue` (idempotent on its key), `resolve_on_success` and `for_holder`, plus a core My Work provider row, **Resolve evaluation issue for {tender}**.<br>• The record never carries bids or findings (§6). The technician repairs the service and cannot decide a result. The waiting task clears only when the failed operation succeeds.<br>• Esther Njeri holds Technical Operator (C18).<br>• Moving the Bid Opening and Bid Submission incidents onto this record is FU-EVL-12. |
| D13 | **Desk routes (EVL v0.4 §10).**<br>• The workspace (D01) is a new Desk Page `bid-evaluation` at `/app/bid-evaluation`: one `kentender_core.desk_page.register(...)` call. No DocType has the slug, and `Page.module` avoids the module-sidebar collision.<br>• Record screens are Tender sub-routes, `/app/tenders/{tender}/evaluation[/…]`. `Tenders.vue` delegates `sub === "evaluation"` to a new `bid_evaluation.bundle.js` (`frappe.kt_mount_bid_evaluation`), added to the `tenders_page.js` bundles list. The exact sub-paths are locked in Phase 11 and recorded in the tracker.<br>• The Tender record links through `kt_tender_record_links`.<br>• The sidebar "Evaluation" coming-soon entry is replaced by the Page link. Check `workspace_sidebar/*.json` for dangling links first (the reverse-sync gotcha) and migrate twice. "Awards" is untouched.<br>• The route is read only through a `useRouteState()` adapter over `desk_page.useRoute`. The UI uses the shared `mountPageRail` and `mountGuidance` and the Industry design system only, never `kentender_core.cl_surface_registry.js` (AGENTS.md §6.1–6.5). |
| D14 | **Supplier portal.** The spec's `/bid/{bid_id}/evaluation-clarifications/{request_id}` "under the existing supplier portal base" becomes `/tenders/{ref}/bid/evaluation-clarifications/{request_id}?organisation=` (C16). It is served through a BDS portal section-resolver seam, as BOP's public opening region is. Draft and reply commands authorise through `acting_assignment` (Supplier Representative or Authorised Signatory of the bidding organisation). Uploads use the shared `file_integrity` limits. The supplier DTO is an allowlist: the own request, own reply, deadline and closure. It never shows findings, ranking, committee notes or another bidder. |
| D15 | **Participation.** Socket.io is not served on this bench. Start, Join and Leave are authenticated commands, with a polling heartbeat. The lapse is a technical setting in `Bid Evaluation Settings`, not a business timeout (§5.2). Every collective command rechecks that the complete current eligible roster is present: `RecordCommitteeConclusion`, `AuthoriseClarification`, `RecordReplyDisposition`, `RecordVerificationPlan`. A lapse is recorded at the next attempt or by the sweep. The secretary cannot record anyone's attendance. |
| D16 | **Simulation controls (OD-D).** `bid_evaluation/services/simulation.py` and `test_services/` provide fault switches: intake failure, clarification notice failure, report delivery failure, signing outcome, award decision recorded, and the suspension, resumption, cancellation and validity-extension owner events. They load only when `kt_bds_simulation_environment` is set. The TRUST-ADR-001 §2 labels render at runtime only under the flag and are never drawn into ported board markup (BOP D15). An `Indeterminate` proof never satisfies a target and gives `EVL_SIGNATURE_UNCONFIRMED`. |
| D17 | **Personas and fixtures.**<br>• The EVL v0.4 §9.1 cast: Amina Hassan (Accounting Officer), Charles Mutiso (Head of Procurement), Brian Wafula (secretary), Grace Wambui (chair), Peter Mugo and Ruth Achieng (members), Samuel Otieno (replacement, D02-REPLACE only), David Ouma (supplier), Naomi Chebet (auditor) and Esther Njeri (Technical Operator). Jirani Office Supplies Limited appears on tender 036 only.<br>• Grace, Peter, Ruth and Esther are added to `site_setup.ACTORS` under the spec's own naming ("new module fixture actors", EVL v0.4 lines 336 and 340). Their KT-STD-001 §8.3 registration and the correction of Brian's "Tender Preparation only" scope are owed under OD-A (FU-EVL-07).<br>• Committee membership and the secretary are appointments, never responsibilities.<br>• Python fixtures use years ≥ 2100 and one fixture entity per test file, and every test module registers purge cleanup. |
| D18 | **Seed and demo profiles.**<br>• A new canonical stage `bid_evaluation` after `bid_opening` (`kentender_core/seeds/canonical.py` `STAGES`, `seed()`, `validate()`). It drives the §11.1 ordinary path at its instants: appointment 11 Jun 2027 09:00, secretary 09:05, declarations 09:10–09:14, intake 12 Jun 11:10:31, clarification 14 Jun 09:05–09:10, reply 15 Jun 10:00, disposition 16 Jun 09:05, signing 14:05–14:07, delivery 14:07:01. The stage ends at **Report sent**.<br>• Demo profiles in `bid_evaluation/seeds/profiles.py` (`make seed-evl-profile PROFILE=`) cover each lifecycle moment and the main branches: appoint, declare, checks running, concern, discussion, clarification sent and replied, signing, sent, tie on tender 036, funding shortfall, no responsive bids, paused, cancelled, and no bids.<br>• The walk-from-the-menu rule applies.<br>• The SEED-OPS-001 runbook gets its new version as a named correction. |
| D19 | **Report.** `bid_evaluation/services/report.py` generates the report continuously from the authoritative record, in the §9.12 section order: summary first, signatures last. The sections are Tender and committee, Bid findings, Financial comparison, Clarifications and committee record, Recommendation and reasons. Only the narrative is editable (`SaveReportNarrative`). `SendReportForSigning` freezes the content and material annexes as one digest. The PDF goes through the existing wkhtmltopdf path, with bytes handled through `file_integrity`. Export follows `ExportEvaluationRecord`. The outcome vocabulary is fixed: recommendation, **No responsive bids**, **No single recommendation — equal evaluated totals**, **No agreed recommendation**, **No current recommendation — tender validity expired**, and the funding qualification. |
| D20 | **Disclosure.** There are per-actor DTO filters for the Accounting Officer, Head of Procurement, chair, member, undeclared or conflicted member, secretary, auditor, technical reader, supplier and any other user. A protected read returns Not found (§7.2 reads). No bid fact reaches the Accounting Officer, an unappointed user or an undeclared member, before or after intake (§7.1, EVL-A16). Public tender pages receive no evaluation projection. |

## Phases

**Loop for every phase:** red, then green, then refactor; run the module tests once; run the phase gate; update the tracker row with evidence. Phases 1–3 are horizontal. From Phase 4 each phase is vertical (service, then API, then screen in Phase 11). Never run the Python suite while a Playwright process is active, and reseed to canonical after Python runs (bench run-tests has no rollback).

### Phase 0: Reconcile (documents only)
- `reconciliation/artboard_inventory.md`: all 107 boards, extracted by script from `window.EVL.boards` (node, running `evl-kit.js` and `boards-1…5.js`). Each row gives id, name, actor, group, size, dialog flag, spec § / variant, slice, and Covered or Conditional. The 18 boards without a spec ID are mapped to the spec prose they depict (C15).
- `reconciliation/error_contract.md`: EVL v0.4 §8, 15 codes plus the 2 nonblocking conditions, copied verbatim by script.
- `reconciliation/handoff_register.md`: the §7.3 rows, each with holder, My Work title, waiting item, notification and clearing event, plus the named test that will prove it.
- `reconciliation/fixture_chronology.md`: the §11.1 ordinary path and the §11.2 branches, each with its entry point and reset state.
- `reconciliation/rule_reconciliation.md`: every `RR-*` / `DM-*` / response identity in the published definition of TND-MOH-2027-033, classified as automatic, automatic plus evidence, evidence only, manual, or not evaluated. Each row also gives its published fact, unit and boundary, and its expected ordinary result from §9.12.
- `reconciliation/scope_binding.md`: the six §5.1 predicates, each mapped to its actual published field and value, or to a gap (C7).
- Commit the design folder and the spec. The provenance gate is repo-wide.
- Log C1–C20 here and FU-EVL-01… in the follow-ups.
- **Gate EVL-G00:** inventory row count = 107 and each board in exactly one slice; every response identity classified; `make artboard-provenance-gate` green.

### Phase 1: Scaffolding
- Add the `bid_evaluation` module and every D2 doctype, with the flags guard and deny permissions.
- Add the core `Support Issue` doctype.
- Add the Proceedings schema changes (D4): the `Proceeding Session` doctype, the `proceeding_type` option and the new target types, schema only.
- Schema contract tests: `bid_evaluation/tests/test_evl_schema.py`, `kentender_core/tests/test_support_issue_schema.py`, and additions to `proceedings/tests/test_prc_schema.py`.
- Makefile targets `evl-preflight` and `evl-services-gate`.
- Sidebar replacement (D13), then `make validate-links`, then migrate clean twice.
- **Gate EVL-G01.**

### Phase 2: Proceedings Evaluation profile (owner-independent)
- `proceedings/services/profiles.py` and the profile-aware versions of `lifecycle`, `attendance`, `events`, `minutes`, `attestation`, `finalize`, `errors` and `reads`, covering the D4 operations.
- Tests against the simulated owner (`proceedings/test_services/owner.py`), with the type Bid Evaluation:
  - several sessions, with only one active at a time;
  - personal join and leave per session;
  - conclusion events carrying the participating roster;
  - report and verification targets;
  - proofs bound to targets, with stale ones failing;
  - supersede, complete, and correction append.
- **Gate PRC-G02E:** `make prc-services-gate` including the new evaluation-profile tests, and `make bop-services-gate` unchanged and green.
- **Closes:** the shared parts of EVL-A05 and EVL-A10.

### Phase 3: Seams and gateways
- The D5 Bid Opening seam, including the digest verification and the completion hook, with tests.
- The D6 Bid Submission package seam, with all four trust outcomes.
- The D8 Tenders seam.
- The D7 rules file, installer, validator extension and vectors.
- The D12 Support Issue service.
- Signing through `kt_trust_signing_services`, the D16 simulation controls, and `Bid Evaluation Settings`.
- One addendum row in each of the BOP, BDS and Tenders trackers.
- **Gate EVL-G03:** `make evl-services-gate` (schema and seams). The `bop-services-gate`, the affected Bid Submission suites and the Tenders seam tests are rerun green.
- **Closes:** the intake-binding part of EVL-A02.

### Phase 4: Preparation and committee
- Services:
  - `preparation.py`: `EnsureEvaluationPreparation`, from the publication consumer and the sweep. It applies the scope gate, records the named Tenders-owner issue on missing or conflicting scope, and lets a terminal no-bids or cancellation outcome take precedence.
  - `appointment.py`: `AppointEvaluationCommittee` and `ReplaceEvaluationMember`. The roster is 3–5 members. The same-tender independent opening member is excluded through the D5 seam. `EVL_MEMBER_INELIGIBLE` is returned with the specific reason beside the person.
  - `secretary.py`: `AssignEvaluationSecretary`.
  - `declaration.py`: `DeclareEvaluationInterest`. A conflict means immediate recusal and a task for the Accounting Officer.
  - `unavailability.py`: `RecordMemberUnavailability`.
  - The suspension scope for administrative actions (§5.7).
  - `roster.py`: current roster, eligible member and complete current eligible roster (§3 roster terminology).
  - The first rows of `my_work_provider.py`.
- **Tests:** `test_evl_preparation.py` and `test_evl_committee.py`.
- **Gate EVL-G04.**
- **Closes:** EVL-A01, A06 and A16 (service parts).

### Phase 5: Intake and automatic checks
- Services:
  - `intake.py`: `ReceiveOpeningPackage` (once only; on failure an automatic Support Issue, and retry with the same operation identity) and `ReceiveEmptyOpeningOutcome` (**No evaluation required**, clearing preparation tasks and creating no case when none exists).
  - `checks.py`: `RunEvaluationChecks` (reruns only affected checks and keeps prior runs).
  - `rules.py` and `aggregate.py` (D7).
  - `comparison.py` (D9: ranking, ties, Provisional comparison, funding).
  - `timers.py`: evaluation deadline, validity end, overdue and expiry conditions.
  - Entering Reviewing.
  - Member review tasks, created once when a member becomes eligible, with no second check run.
- **Tests:** `test_evl_intake.py`; `test_evl_rules.py` (boundary, unit, precision and alternative vectors, plus presence not implying validity); `test_evl_comparison.py` (the §9.12 ordinary results, tie, funding, no responsive bids).
- **Gate EVL-G05.**
- **Closes:** EVL-A02, A03, A04 and A09.

### Phase 6: Findings and discussion
- Services:
  - `findings.py`: `RecordEvidenceFinding` and `RaiseFindingConcern`. A Needs review finding, a concern or a contrary finding creates or updates one chair item per bid and requirement.
  - `discussion.py`: `StartDiscussion` (records the chair's attendance in the same action), `JoinDiscussion`, `LeaveDiscussion`, `EndDiscussion`, and `RecordDiscussionNote`.
  - `conclusion.py`: `RecordCommitteeConclusion`, resolved or qualified, with the complete current eligible roster present and `EVL_MEMBERS_ABSENT` naming who is missing.
  - `RecordDisagreement`, in the member's own words.
  - `issues.py`: `ReportEvaluationIssue` and `RetryEvaluationOperation`.
  - Recalculation when a finding is resolved.
- **Tests:** `test_evl_findings.py` and `test_evl_discussion.py`.
- **Gate EVL-G06.**
- **Closes:** EVL-A05 and A17.

### Phase 7: Written clarification
- Services, in `clarification.py`:
  - `AuthoriseClarification`: atomic with its committee conclusion; the chair sees any date conflict first.
  - `SendClarification`, `WithdrawClarification` and `RetryClarificationNotice` (truthful **Delivery problem**; same request identity).
  - `SaveClarificationDraft` and `SubmitClarificationReply`: timeliness taken from the trusted received instant, **Received late** labelling, one sent reply.
  - `RecordReplyDisposition`: atomic closure; an attempted change to the offer is kept as correspondence but excluded.
- **Tests:** `test_evl_clarification.py`, including both reply-versus-closure commit orders, closure with no reply, and a reply denied during signing without changing the frozen report (EVL-A07).
- **Gate EVL-G07.**
- **Closes:** EVL-A07 (service part).

### Phase 8: Due diligence
- Services, in `diligence.py`:
  - `RecordVerificationPlan`: recorded in session; participants and one lead drawn from the current eligible roster; a revision with a reason supersedes a frozen verification report.
  - `RecordDueDiligence`: each participant records their own observations.
  - `SendDueDiligenceForSigning` (the lead) and `SignDueDiligenceReport` (page-initial and final-signature targets).
  - The outcome conclusion. After a negative outcome with a recorded conclusion, the service proposes the next eligible ranked bidder and never substitutes silently.
- **Tests:** `test_evl_diligence.py`.
- **Gate EVL-G08.**
- **Closes:** EVL-A08.

### Phase 9: Report, signing, delivery and correction
- Services:
  - `report.py` (D19) and `SaveReportNarrative`.
  - `signing.py`:
    - `SendReportForSigning`, with every guard returned together; `EVL_REPORT_INCOMPLETE` lists every unresolved item and its holder;
    - `SignEvaluationReport`, with the stale case (`EVL_TARGET_CHANGED`) and the unconfirmed case (`EVL_SIGNATURE_UNCONFIRMED`);
    - `RaiseReportConcern` and `ReviseEvaluationReport`.
  - `delivery.py`: `DeliverEvaluationReport`, triggered by the final proof, with `EVL_REPORT_DELIVERY_FAILED` and a retry under the same delivery identity.
  - `correction.py`:
    - `ReturnEvaluationReport`, which checks the authoritative downstream status (`EVL_DECISION_STATUS_UNKNOWN`);
    - `RecordCorrectionNotice`;
    - `AssessOpeningSupplement`, with separate tasks before and after delivery.
  - `tender_events.py`: `ReceiveTenderEvent`, for pause, resume, cancel and extension.
  - Rechecks before freezing and before delivery.
  - The qualified outcomes, including an expired-validity report that can be frozen, signed and delivered without an expiry loop.
- **Tests:** `test_evl_report.py`, `test_evl_signing.py` and `test_evl_correction.py`.
- **Gate EVL-G09.**
- **Closes:** EVL-A10, A11, A12 and A13.

### Phase 10: API, disclosure and work
- `bid_evaluation/api.py`: whitelisted endpoints with explicit arguments. They never forward `**kwargs` into a keyword-only service (the transport-field trap). Refusals are data carrying the §8 code, and refusals and not-found reads are audited.
- Reads: `ResolveEvaluation`, `ListEvaluationWork`, `ReadEvaluationEvidence`, `ReadEvaluationReport`, `ReadOwnClarification`, `ExportEvaluationRecord`.
- The per-actor DTO filters (D20).
- The full My Work matrix, checked against `handoff_register.md`.
- The technical-read resolver and probe (`kt_technical_reference_resolvers`, `kt_technical_read_probes`).
- **Tests:** `test_evl_api.py`, `test_evl_my_work.py`, `test_evl_dead_end.py` and `test_evl_leakage.py`.
- **Gate EVL-G10:** `make evl-dead-end-gate` (every state × actor through `next_step.problems`) and `make evl-leakage-gate` (Accounting Officer, unappointed, undeclared, conflicted, supplier, public and technical readers; counts, errors, task titles and exports).
- **Closes:** EVL-A14.

### Phase 11: Desk UI (vertical slices)
- The Tenders seam comes first (D13). Afterwards run the existing `ui-tenders-*` and `ui-bop-*` gates once to prove there is no regression.
- **Each slice:** API read, then the screen ported class-for-class from its boards (with the `evl-kit.js` compositions mapped to Vue components once), then one Playwright spec with one fixture entity, then `ui-evl-<slice>-gate`. Evidence PNGs go to `evidence/v0_4/`.
- **Departures file:** `tests/ui/fidelity/departures/bid-evaluation.js` (DEPARTURES, COVERED, CONDITIONAL, SUPPLIER_*), with an inventory-count test fixed at 107.

| Slice | Boards | Notes |
|---|---|---|
| 11.1 Workspace and shared states | D01, D01-EMPTY, D01-FILTERED, D01-APPOINT, D01-APPOINT-HOP; S-LOADING, S-ERROR, S-NOT-FOUND, S-FORBIDDEN, S-CHECKS, S-OPENING-AWAITED, S-SOURCE-OPEN, S-STALE-RECORD, S-STALE-REPORT, S-UNCONFIRMED, S-AUDITOR | The `/app/bid-evaluation` Page; the local register filter changes no state |
| 11.2 Committee and declaration | D02-A, D02-S, D02-D, D02-CONFLICT, D02-REPLACE, D02-INELIGIBLE, D02-INTAKE-FIRST, D02-INTAKE-FIRST-HOP, D02-DECLARE-FIRST, D02-UNABLE, D02-NO-BIDS | No bid facts before declaration; no tracker on D02-D |
| 11.3 Record and requirement | D03, D03-READY, D03-FUNDING, D03-TIE (1024×768), D04, D04-AUTO, D04-FAIL, D04-CONCERN | Tender 036 is its own fixture entity |
| 11.4 Committee discussion | D05, D05-CHAIR, D05-START, D05-JOIN, D05-MEMBER, D05-DISAGREE, D05-ABSENT, D05-ABSENT-CHAIR, D05-ABSENT-MEMBER, D05-CONCLUSION, D05-CONCLUSION-Q, D05-RECORD, D05-RECORD-MEMBER, D05-RECORD-AUDITOR | Personal join and leave per browser session |
| 11.5 Clarification (internal) | D06-SEND, D06-DELIVERY, D06-OUTCOME, D06-NO-REPLY, D06-LATE-REVIEW, D06-CHANGED-OFFER, D06-WITHDRAW, D06-WITHDRAW-DLG | Notice failure through the D16 switch |
| 11.6 Report and signing | D07-DRAFT, D07-PREVIEW, D07-SIGN, D07-WAIT, D07-CONCERN, D07-SENT, D07-HOP, D07-HOP-RETURN, D07-RETURNED, D07-NO-RESPONSIVE, D07-NO-AGREEMENT, D07-REVISE, D07-REVISE-DLG, D07-DELIVERY, D07-OVERDUE, D07-OVERDUE-SEC, D07-EXPIRED, D07-EXPIRED-SIGN, D07-EXPIRED-SENT, D07-INCOMPLETE, D07-DECISION-UNKNOWN, D07-DECISION-UNKNOWN-CHAIR, D07-TIE, D07-FUNDING | Signing through the test double under the flag |
| 11.7 Issues, verification and correction | D08-SOURCE, D08-RULE, D08-VERIFY-PLAN, D08-DD, D08-DD-FREEZE, D08-DD-SIGN, D08-VERIFY-OUTCOME, D08-VERIFY-NEG, D08-SUPPLEMENT, D08-SUPPLEMENT-SENT, D08-SUPPLEMENT-HOP, D08-CORRECTION-HOP, D08-CORRECTION, D08-PAUSED, D08-CANCELLED | Paused and cancelled through the D8 simulation owner events |
| 11.8 Pause and cancellation | P-PREP, P-SIGN, C-PREP, C-SIGN | Cancellation after delivery is Conditional (C15) |

- **Gate:** each slice gate, plus `ui-evl-fidelity-gate` (vitest project `bid-evaluation`, added to `ui-structure-gate`).
- **Closes:** the Desk part of EVL-A15.

### Phase 12: Supplier portal
- The D14 portal seam, then the 7 supplier boards at 390×844: D06-SUPPLIER, D06-RECEIVED, D06-LATE, D06-LATE-RECEIVED, D06-CLOSED, D06-FINAL-CLOSED, D06-FINAL-CLOSED-NR.
- **Tests:**
  - no finding, ranking or other bidder is ever disclosed;
  - a saved draft is not a sent reply;
  - closure rejects writes with `EVL_REPLY_CLOSED` and keeps the draft private;
  - a late reply is labelled, not accepted.
- Bid Submission portal regression.
- **Gate:** `ui-evl-supplier-gate`.
- **Closes:** the browser parts of EVL-A07 and A14.

### Phase 13: Canonical seed stage and demo profiles
- The D18 `bid_evaluation` stage and its `seed-canonical-validate` coverage.
- The four new actors in `site_setup.ACTORS` and `ASSIGNMENTS` (D17).
- The demo profiles and `make seed-evl-profile`, `seed-evl-profiles`, `seed-evl-profile-restore`.
- `tests/ui/smoke/bid-evaluation/evl-demo-walk.spec.ts`, walked from the menu and the bell with one browser session per person.
- **Gate EVL-G13:** `make seed-canonical SITE=kentender.midas.com THROUGH=bid_evaluation` and `make seed-canonical-validate`, both green; a second run is idempotent.

### Phase 14: Release evidence
- `ui-evl-fidelity-gate` over all 107 boards.
- The §11.1 ordinary path and the §11.2 branch matrix. For each row, compare the visible control, server command, PRC event, My Work item, disclosure and clearing transition.
- A persona browser pass as real users: Amina, Charles, Brian, Grace, Peter, Ruth, Samuel, David, Naomi, Esther and Administrator.
- AC map closure, and `RUNBOOKS.md` (simulation switches, fixture reset, source-issue recovery, delivery retry).
- **Gate EVL-G14:** `ui-evl-release-evidence-gate`.

### Phase 15 (owner-gated; every row starts `Blocked — owner`)
- **Owner-document amendments owed under OD-A**, each written as a Proposed document under the document-change protocol, then approved by the owner:
  - PRC-CHG-001 v0.10 (Evaluation profile);
  - TPR-CHG-001 (publication binding and scope fields, post-close cancellation, suspension, validity extension, award-decision status);
  - BDS-CHG-001 (supplier evaluation correspondence view, released-package seam);
  - STD-TPL-001 (evaluation-rules asset);
  - BOP-CHG-001 (automatic take-up, completion consumer, digest note);
  - BUD-CHG-001 (evaluation funding read);
  - KT-STD-001 v1.13 (Grace Wambui, Peter Mugo, Ruth Achieng, Esther Njeri; Brian's scope);
  - SEED-OPS-001 (the `bid_evaluation` stage);
  - register rows (a BOP → Evaluation interface row; the STD-TPL version cited).
- LAW-V-001 current-law verification and the PPRA evaluation-report format reconciliation (EVL v0.4 §2.1, §12).
- Real signing and custody (TRUST-ADR-001).
- A security review.
- Production enablement.
- The downstream Award consumer of the delivered report.
- Moving the Bid Opening and Bid Submission incidents onto Support Issue.
- **No gate in this plan.**

## Conflicts and follow-ups to log (Phase 0)

| # | Conflict | Treatment |
|---|---|---|
| C1 | EVL v0.4 requires coordinated amendments to PRC, TPR, BDS, STD-TPL and BOP (EVL v0.4 §12 lines 680–683; line 752 "Coordinated amendments to other owner documents remain outstanding"). None exists in the repository. | OD-A: build to EVL v0.4, with each amendment a Phase 15 follow-up (FU-EVL-01…06). Every seam gets an addendum row in its owner's tracker. |
| C2 | EVL v0.4 §6: "Technical issues reuse the platform support-issue record and assignment route." No platform record exists. | OD-B and D12. |
| C3 | Grace Wambui, Peter Mugo, Ruth Achieng and Esther Njeri are not in KT-STD-001 v1.12 §8.3 or the seeds.<br>• Brian Wafula is registered as "Procurement Officer, site-wide — Tender Preparation only".<br>• Samuel Otieno is registered as "Head of User Department, expired". He is still usable as a replacement member, because membership is an appointment and not a responsibility.<br>• Jirani Office Supplies Limited is not seeded, and David Ouma is not in §8.3. | D17; FU-EVL-07. |
| C4 | No seam releases an opened package to Evaluation. | D6. |
| C5 | `Evaluation Handoff.handoff_digest` ≠ sha256(`payload_json`): the payload is serialised compactly, but the digest uses the default separators. | D5: the seam verifies by recomputation. Add a BOP addendum row and FU-EVL-05. |
| C6 | The Proceedings v0.9 code allows one session, is opening-only and hard-codes the type (EVL v0.4 §12 line 681). | D4. |
| C7 | The §5.1 scope gate requires Open Tender, IT Goods (`product_key = IT-EQUIPMENT-OPEN-V1`), one lot, KES, fixed price, and lowest evaluated responsive. `product_key` is a stored field, but method, currency and lot are hard-coded in `bid_definition.projection()`, and fixed price and evaluation method have no explicit published field. | Phase 0 `scope_binding.md`. Bind each predicate to a published definition fact or a template-release product-profile fact, never to a title or a default. A predicate that is truly absent produces the named Tenders-owner issue (§5.1). FU-EVL-02. |
| C8 | The handoff has no bidder name, submitted total or security. | Take them from the released package (the source), and use `register_rows` only for cross-checking. |
| C9 | Under TPR v0.13 there is no post-close cancellation, suspension, validity extension or award-decision fact. `TenderCancelled` has no consumer. | D8: seam reads, plus simulation-only owner events for these branches. FU-EVL-02. |
| C10 | Dated rules. The evaluation period is `evaluation_period_days` (30) and validity is the officer's `tender_validity_days`. The spec's fixtures, 12 Jul 2027 11:00 and 10 Oct 2027 11:00, are 30 and 120 days after the 12 Jun 2027 11:00 opening. EVL v0.4 §5.7 requires the computation, source and timezone to be inspectable. | `dated_rules` exposes the counting rule, anchor, source and timezone. Phase 0 confirms the anchor against TPR. |
| C11 | No Budget contract gives evaluation funding. The D03-FUNDING board cites "Budget confirmation, 16 Jun 2027, 09:50 EAT". | D9: a read through `get_funding_lineage`. FU-EVL-06. |
| C12 | The site's `PREFERENCE-MARGINS/MSME` 15% regulatory reference (`site_setup.py:1102-1145`) is applied at financial evaluation elsewhere. EVL v0.4 §4.4 says "do not introduce a preference margin … after closing". | Apply it only when the tender's published rule carries it. It does not for this template. |
| C13 | TECH-008 is a "Minimum" on free text ("minimum 10 cores or equivalent benchmark"). | An evidence check, never automatic (§4.1). The §9.12 final result is Meets after member review. |
| C14 | Legacy placeholders: the `evaluation_award` skeleton, the "Evaluation & Award" workspace, the coming-soon sidebar entries, the TM2 records and the legacy roles. | D1 and D13. TM2 and the roles stay untouched. |
| C15 | 18 boards have no spec variant ID (D01-APPOINT-HOP, D02-INTAKE-FIRST-HOP, D05-DISAGREE, D05-ABSENT-CHAIR, D05-ABSENT-MEMBER, D05-CONCLUSION-Q, D05-RECORD-MEMBER, D05-RECORD-AUDITOR, D06-LATE-RECEIVED, D06-WITHDRAW-DLG, D06-FINAL-CLOSED-NR, D07-REVISE-DLG, D07-OVERDUE-SEC, D07-DECISION-UNKNOWN-CHAIR, D07-PREVIEW, D08-VERIFY-NEG, D08-SUPPLEMENT-HOP, D08-CORRECTION-HOP). Cancellation after delivery (§9.13 line 546) is prose only. D05-CONCERN is an alias of D03 (§9.13, N1). | The inventory maps each board to the spec prose it depicts. The after-delivery cancelled view is built from the rules and marked Conditional. |
| C16 | The supplier route `/bid/{bid_id}/evaluation-clarifications/{request_id}` "under the existing supplier portal base". The existing base is `/tenders/{ref}/bid`. | D14. |
| C17 | Register drift:<br>• the new EVL entry cites STD-TPL v0.10, while v0.13 is the latest approved;<br>• LAW-REG-001 v1.2 is "Proposed" in its file but "Approved" in the register;<br>• the SEED-OPS-001 file is named `v1_0` but its content is v1.15, and it has no register entry.<br>The register and `.xlsx` changes in the working tree are the owner's own and are not touched. | Report to the documentation owner (FU-EVL-09). This plan does not edit the register. |
| C18 | EVL v0.4 names a "Technical support" holder, and the registered role is Technical Operator. | Esther Njeri holds Technical Operator (D12). |
| C19 | Participation needs a live session, and socket.io is not served on this bench. | D15. |
| C20 | The PPRA evaluation-report format and LAW-V-001 are open (EVL v0.4 §2.1, §12). | Phase 15. Neither is claimed. |

## Risks

- **Scale.** 107 boards, 17 acceptance criteria, about 40 commands and 20 hand-off rows. Mitigation: horizontal Phases 1–3, then vertical phases, and one fixture entity per browser spec.
- **Proceedings regression** from generalising a service Bid Opening depends on. Mitigation: the PRC and BOP gates run on every Phase 2 red/green cycle, and profile rules are isolated in `profiles.py`.
- **Rule semantics drift** from the issued tender. Mitigation: the Phase 0 rule reconciliation, and vectors asserting the §9.12 ordinary results; missing rules become Needs review, never defaults.
- **Leakage of bid facts** through counts, errors, task titles or exports before declaration, or to the Accounting Officer. Mitigation: named leakage tests in Phase 4 and the Phase 10 leakage gate.
- **Code running ahead of the owner documents** (OD-A). Mitigation: an addendum row in each owner's tracker for every seam, and a Phase 15 follow-up for each document with the exact change needed.
- **Site-wide test mutation.** Mitigation: fixture years ≥ 2100, purge registration, reseed to canonical after runs, and never run Python and Playwright together.
- **A stand-in mistaken for production.** Mitigation: the stand-ins load only under the simulation flag, and the verification labels appear only at runtime under that flag.

## Verification

```bash
cd /home/midasuser/frappe-bench
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.bid_evaluation.tests.<module>
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.proceedings.tests.<module>
./scripts/bench-with-node.sh build --app kentender_procurement
cd apps/kentender_v1
make artboard-provenance-gate
make evl-services-gate
make prc-services-gate
make bop-services-gate
make evl-dead-end-gate
make evl-leakage-gate
make ui-queue-check
make ui-evl-<slice>-gate
make ui-evl-supplier-gate
make ui-evl-fidelity-gate
make ui-evl-release-evidence-gate
make seed-canonical SITE=kentender.midas.com THROUGH=bid_evaluation
make seed-canonical-validate SITE=kentender.midas.com
```

**Live browser walk (Phase 14), under the simulation flag, on the canonical Afya tender:**
1. Amina opens **Appoint evaluation committee for TND-MOH-2027-033** from My Work and appoints Grace, Peter and Ruth. Charles assigns Brian as secretary.
2. Each member declares with no conflict. Before the opening, Grace sees the committee but no bidder.
3. After the opening completes, the checks run with no click. Peter reviews the service-location evidence and saves it as Needs review.
4. Grace starts a discussion, and Peter and Ruth join. Brian records the note. Grace authorises the clarification, and Brian sends it.
5. David replies from the supplier portal on a phone-sized screen.
6. The committee records the reply outcome. The comparison refreshes to position 1.
7. Brian sends the report for signing. Grace, Peter and Ruth each sign.
8. Charles receives **Review evaluation report for TND-MOH-2027-033**. There is no award button.
9. Naomi reads the record read-only, and Administrator sees technical status only.
10. Repeat the §11.2 branches on their own fixtures: tie (tender 036), no responsive bids, funding, paused, cancelled, no bids, source issue (Esther), and return for correction.
