# OVS-CHG-001 v0.6: System Usability and Decision Visibility, implementation plan

| Control | Value |
|---|---|
| Version | 0.6-plan.1 |
| Date | 4 October 2026 |
| Authority | `KenTender_OVS-CHG-001_System_Usability_and_Decision_Visibility_v0_6.md`, **"Approved — 3 October 2026"** (OVS v0.6 control table). Approval record: Project Owner, "Mark the documents as approved". The approval states: "Static design work and conformance matrices remain open; CM and the separate template walkthrough remain deferred. Approval does not establish implementation, seed execution, testing, legal clearance or production readiness." |
| Governing standard | KT-STD-001 v1.15, approved 3 October 2026 (`../00_common/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_15.md`). |
| Version set | `KenTender_OVS_Impact_and_Reconciliation_v0_6.md`, "Approved version set — 3 October 2026": STR 1.9, BUD 1.12, NDS 1.16, PLN 1.29, REQ 1.14, CFG 0.18, TPR 0.17, BDS 0.11, KT-STD 1.15, AUTH 1.11, SEED 1.4, SEED-OPS 1.22, KT-RCA 1.3, TRUST 0.2, BOP 0.11, PRC 0.11, EVL 0.5, AWD 0.5, OVS 0.6, CTX 1.1. |
| Design | `design/OVS First Slice Review.dc.html` (with `support.js` and `_ds/`). A **review board**, not a closed-input design: 17 views (one findings page, 4 Evaluation, 6 Tender, 6 Proceedings), several values shown as `[ … ]`. See Phase 1. |
| Companions | `OVS-CHG-001_v0_6_IMPLEMENTATION_TRACKER.md`; `OVS-CHG-001_v0_6_FOLLOW_UPS.md`. Phase 0 adds `reconciliation/`. Later: `evidence/v0_6/`. |
| Predecessor | None. An earlier OVS v0.1 draft, written the same day and never approved, is kept in `retired/`. Its acceptance IDs OVS-AC-001–024 mean different things from v0.6's OVS-AC-001–018. |
| Prepared | 4 October 2026 (current-state reading done 3 October 2026) |
| Status | Planned. No OVS code has been written. The approved package was filed into the project folders late on 3 October 2026 (tracker row OVS6-0000). |

## Context

**Why this change.** On 3 October 2026 the Project Owner, signed in as the Head of Procurement Function, found that the Bid Evaluation page for a delivered report showed only the committee list and the words "Report delivered". There was no decision and no report. An Accounting Officer had no way to count procurement meetings in a department, and the Tender page linked to later stages but showed nothing from them. Reading the code showed three separate causes: Evaluation gives only committee members, the secretary and auditors the bid-level read; the Tender record only carries link buttons; and nothing reads Proceedings across Tenders. OVS v0.6 turns this into a whole-system usability change.

**What OVS v0.6 requires, in one paragraph.** An authorised reader can always find a record again, see what was decided, by whom, when and why, see the supporting evidence and earlier versions, and see what is outstanding and who holds it. Each stage keeps its own disclosure rule. For Evaluation, the Accounting Officer and Head of Procurement Function see administrative facts only until the report is delivered and everything, read-only, after. Department heads see scoped progress and disclosed outcomes. One read-only register counts Opening and Evaluation meetings by type and by the Tender's owning department. Contract Management is in scope but deferred.

**What is not in the request.** No new approval layer, task, ledger, scoring scheme, meeting administration or unrestricted bid disclosure (OVS v0.6 §2). Reads create no business event.

### What slowed earlier modules, and the rule here

| Evidence | Rule here |
|---|---|
| Verification left to the end produced late rework (`feedback-rebuild-phase-sequencing`). | Phases 0–2 are horizontal; from Phase 2 every phase is a vertical slice that ends with a live check. |
| A green test missed a scope bug because fixtures mirrored the code's own persona assumptions (`playwright-fixture-realism-gaps`). | Disclosure is tested by driving the real endpoints as the real personas (Amina, Charles, Naomi, Peter), not only by calling a service. |
| Tests wrote real rows with no rollback and wiped site data. | Tests run on `kentender-test.local` only; shared test worlds per module; never run Python while Playwright is active. |
| A rewritten published contract left callers broken. | Before removing or reshaping any hook or read, grep the whole repository for callers (Phases 3, 10, 12). |
| A bug report on a spec-built screen was a signal to audit the whole screen. | Each UI slice compares every board and every variant, not only the one reported. |

## Current state (verified 3 October 2026 by reading the source; the live site was not run)

Paths are relative to `kentender_procurement/kentender_procurement/` unless stated.

**Evaluation (the reported defect).**
- `bid_evaluation/services/reads.py` `access()` (lines 47–54): a "bids" reader is `(eligible or secretary or auditor) and not technical`. The Accounting Officer is never one. The Head of Procurement Function is a "report" reader only as the delivery recipient.
- `resolve()` (92–118) builds the comparison, attention items and outcome only for bids readers.
- `bid_evaluation/services/next_steps.py` Report-sent branch (152–171): the recipient gets "Review the committee's report" with `open_report` only while the review is Open. The Done line "The committee report was sent to …" carries no `primary_action`. The Accounting Officer and a non-recipient Head fall through to not-involved.
- `public/js/bid_evaluation/screens/index.js` `pick()` line 79: any reader without `bids` goes to `record.setupOnly()` (`screens/record.js` 150–158), which shows the roster and "Report delivered".
- The disclosure test is `bid_evaluation/tests/test_evl_reads.py::test_who_reads_what` (lines 40–71). It asserts that the AO and Head see no comparison, name or amount, in all states, so it must become state-aware.

**Tender record.** Hook `kt_tender_record_links` (`hooks.py:146`) with providers in `bid_opening/desk_links.py`, `bid_evaluation/desk_links.py` and `award/desk_links.py` returns only a label and a route. `tenders/services/read.py` `record_links()` (623–630) and `get_tender()` (633–690) compose them. The buttons are in `public/js/tenders/components/PublishedScreen.vue` (12–18). `get_tender` already has a `department` reader mode (line 637).

**Opening and Award.** The AO and HOPF already read both (`bid_opening/services/reads.py:26` `READER_ROLES`; `award/services/guards.py:17` `INTERNAL_READERS`). Neither admits a Head of User Department.

**Proceedings.** `proceedings/doctype/proceeding` has `owner_type`, `owner_id`, `proceeding_type`, `state`, `actual_start`, `actual_end` and no tender or department field. An opening starts **no** `Proceeding Session`; only the Proceeding row exists. Evaluation discussion sessions are `Proceeding Session` rows (`proceedings/services/sessions.py`, started from `bid_evaluation/services/discussion.py:89-105`). `Evaluation Case.proceeding` is a Data field, not a Link. The owner adapter's `allows()` works only inside `acting(case)` (`bid_opening|bid_evaluation/services/prc_owner.py`), so there is no row-level reader verdict yet. There is no register and no cross-Tender read.

**Department.** `tenders/doctype/tender/tender.json` holds `lead_org_unit` (Link, can be null, set in `tenders/services/draft_commands.py:109-118`) and `contributing_org_unit_ids` (JSON text). `tenders/services/tender_authorization.py` has `reader_mode`, `departmental_units` and `contributing_units_of`. The resolver is `kentender_core/kentender_core/services/authorization.py`: `permitted_ou_scopes` (212), `descendants_of` (239), `report_match_conditions` (495).

**Other owners' read gates.**

| Owner | Where the read is decided | AO / HOPF / HoD today |
|---|---|---|
| Strategy | `kentender_strategy/.../services/strategy_authorization.py:58` tuple, plus DocPerm rows | none of the three |
| Budget | `kentender_budget/.../services/budget_authorization.py:64` tuple, plus DocPerm rows | none of the three |
| Needs | `departmental_needs/services/permissions.py:115-135` `can_view` | HoD reads in its unit; AO and HOPF do not |
| Planning | `procurement_planning/services/planning_roles.py:31-39` | AO and HOPF read site-wide; HoD by unit |
| Requisitions | `procurement_requisitions/services/requisition_roles.py:26` | HOPF and HoD read; AO does not |
| Bid Submission | supplier-side only | no internal grant |
| Configuration | administrator-gated | no business-role read |

**Already built from absorbed versions.** TPR v0.16 work-summary cards, `ReturnApprovedTender` and the publication-period guard; NDS v1.15 `need_planning_intake_projection`. **Not yet verified in code:** REQ v1.13 (installed, switched-on template release), CFG v0.17 (separate 7-day minimum and 21-day default), PLN v1.28 position rules. Phase 0 audits them. They belong to the approved package but not to OVS itself.

**Design.** The review board lists its own gaps (findings page): no Evaluation oversight variants in the owner document; no Tender placement or copy for Decisions and progress; the Proceedings brief is incomplete; Award and Opening wording are `[ … ]`; EVL's design fixture has one bid while the canonical story has four.

**Not specified anywhere in the approved package.** The stage-summary field list and its Tender placement. OVS v0.6 §13: "A new summary structure must be incorporated into the canonical owner/interface definitions during reconciliation". The retired OVS v0.1 (OVS v0.1 §4.1 and OVS v0.1 §5.3) is a drafting reference only.

**Done means:** every Done row in the tracker has observed evidence; OVS-AC-001–018 each have a recorded result or an owner-gated reason; the first slice passes a live walk as the four personas; and no module is called complete while its coverage row is open (OVS v0.6 §17).

## Owner decisions (recorded, not re-asked)

| # | Decision |
|---|---|
| OD-1 | 3 Oct 2026: "Mark the documents as approved." OVS v0.6 and the coordinated version set are approved, with OVS-P01–P05. |
| OD-2 | 3 Oct 2026, on Evaluation: "sees status only before delivery"; "all details after delivery"; "tender's owning department". "Delivery" is the committee report being sent to the Head of Procurement Function (Report sent), not Bid Opening. |
| OD-3 | 3 Oct 2026: Contract Management sources and the separate template walkthrough are deferred. "Do not request them again until that work resumes." |
| OD-4 | 3 Oct 2026: "Make a plan and a tracker to implement"; "Move the latest versions of the files to their respective project folders." |
| OD-5 | 3 Oct 2026, folder: new `17_oversight_visibility/`. |
| OD-6 | 3 Oct 2026, scope: "Full scope, phased". The first slice (Evaluation, Tender Decisions and progress, Procurement meetings, department-head reads) is active; other-module reads, register coverage and CTX v1.1 are planned phases; Contract Management stays deferred. |
| OD-7 | 3 Oct 2026, old draft: move OVS v0.1 to `retired/`. |
| OD-8 | 3 Oct 2026, move handling: move files unchanged, empty `working_files`, log the stale rows, commit nothing. |
| OD-9 | 4 Oct 2026: "OVS6-0213: Yes". Store an evidence manifest beside the report content at freeze, with a labelled backfill for versions already delivered. |
| OD-10 | 4 Oct 2026: "OVS6-0311:  Yes". Fix the Tender lead department at its source and patch existing Tenders. |
| OD-11 | 4 Oct 2026: "FU-OVS-40: a department-level view". The Evaluation and Award routes render a department-level view for a Head of User Department. |

## Key technical decisions (implementation authority unless the owner says otherwise)

| # | Decision |
|---|---|
| D1 | **The Evaluation oversight projection is built from the frozen delivered Report Version content, never from live case data.** A return or correction therefore cannot leak unfinished findings (OVS-AC-006, OVS v0.6 §7). New `bid_evaluation/services/oversight.py` reads `Evaluation Report Version.content_json`. |
| D2 | **The delivery point is "a Delivered report version exists", not the case state.** A case sent back to Reviewing still shows the earlier delivered version, labelled **Returned for correction** with the return reason and **A corrected report is being prepared** (OVS v0.6 §7). |
| D3 | **Verify before adding storage.** OVS v0.6 §3 allows the smallest owner-owned association "where immutable evidence associations are missing"; the impact schedule says EVL-CHG-001 §5.5 may already freeze them. Phase 0 checks whether the frozen annex set includes every evaluated submission version and all its documents, cited or not. If it does not, add the smallest association to Evaluation and log it as a follow-up with owner sign-off. |
| D4 | **Stage summaries use a new hook, `kt_tender_stage_summaries`.** The name is proposed (OVS v0.6 §3: names "describe proposed contracts, not confirmed installed APIs"). Providers sit in the existing `desk_links.py` modules. `kt_tender_record_links` stays until the header buttons are replaced "only when their equivalent authorised navigation works" (OVS v0.6 §8). |
| D5 | **Department is read, not stored.** Grouping uses the Tender's lead department; the filter matches the lead or any contributor, resolved through case → Tender (OVS v0.6 §11). Phase 0 checks whether the lead can be reassigned or is null; if it can be reassigned, attribution uses owner history at the meeting date. A missing value shows **Department not recorded**. |
| D6 | **Meetings come from two sources.** An opening is its Proceeding (start, end, state, Not held); an Evaluation meeting is each `Proceeding Session`. "Held" means a session with an actual start, including aborted-after-start and ongoing. |
| D7 | **Add a row-level owner verdict to each PRC owner adapter** (`can_read_row`), usable without `acting(case)`. The register never decides who may see an owner's row (PRC v0.11, OVS v0.6 §13). |
| D8 | **The register uses the shared authorisation resolver, never raw SQL** (AUTH-ADR-001 v1.11 §5.4: "a report that cannot apply the shared conditions is prohibited"). Permission, owner verdict and filters apply before aggregation and pagination. A row that cannot be verified is hidden and the page says **Some meeting records could not be loaded. Totals are incomplete.** |
| D9 | **Evaluation's pointer to Award goes through an existing downstream seam**, not a deep import (dependency direction: Award depends on Evaluation). It names the person preparing the opinion only when Award supplies it (OVS v0.6 §8). |
| D10 | **UI follows the repository's AGENTS.md, section 6.** Vue 3 in a Desk Page; one `kentender_core.desk_page.register` call; no `cl_surface_registry`; the bundle binds `__` and `frappe`; route identifiers in the path; revalidate in place. The new page is `procurement-meetings`; the slug is free in code and must be confirmed on the live site (`frappe.db.exists("DocType", "Procurement Meeting")` and `"Procurement Meetings"`). Add the sidebar item after Awards and a `_KT_ROUTE_TO_SIDEBAR` entry; a new Page and sidebar JSON need `bench migrate`. |
| D11 | **Technical-reader reconciliation (OVS-P05, OVS v0.6 §4.2).** Administrator and System Manager read ordinary business records after governed release and read the meetings register (safe metadata); a limited technical operator does not; sealed content, keys and signing credentials are never ordinary data. This changes today's Evaluation behaviour (status only for technical readers), so Phase 2 ships explicit leak tests. |
| D12 | **Verification discipline (CLAUDE.md).** Red then green on one test; module tests once; broaden only at a checkpoint; test site only; shared test worlds built once per module; fidelity gates once per slice. |
| D13 | **The oversight view reuses the committee screen builders** (`screens/common.js` `comparisonTable`, `signaturesTable`, `summaryBlock`) fed from the frozen projection, with command controls absent. It does not fork them. |
| D14 | **Hand-offs and tasks:** none are added. Opening an oversight view clears no task (OVS-AC-011). |

## Phases

**Loop for every phase:** red, then green, then refactor; run the module tests once; run the phase gate; update the tracker row with its evidence in the same step. Phases 0–1 are horizontal. From Phase 2 each phase is a **vertical slice**: service → API → screen (where the phase has one) → one Playwright spec with one fixture entity → a live click-through from the menu. Never run Python while a Playwright process is active. Never run Python tests on `kentender.midas.com`.

### Phase 0: Reconcile and audit the baseline (documents and tooling)
- `reconciliation/version_set.md`: the 20 approved documents, each with source, successor, folder, register entry, and whether a predecessor stays in place.
- `reconciliation/read_grant_matrix.md`: every OVS v0.6 §4.1 read, the owner file and function that decides it, today's behaviour, the change, and the test.
- `reconciliation/stage_summary_contract.md`: the field list for Opening, Evaluation and Award summaries (status, disclosure level, labelled facts, outcome, actor, date, reason, outstanding matter, links), the status-only subset per owner, and the failure contract. Reconcile it with the review board.
- `reconciliation/seam_register.md`: Tenders → owner summaries; Evaluation → Award pointer; PRC register → owner row verdicts.
- `reconciliation/ac_map.md`: OVS-AC-001–018 verbatim, with the phase that proves each.
- Audit which absorbed versions are in code: REQ v1.13, CFG v0.17, PLN v1.28 (TPR v0.16 and NDS v1.15 are present).
- Verify D3 (frozen evidence associations) and D5 (lead department reassignment and null cases) against the code and the live data model.
- Check the canonical Tender: four bids, one completed evaluation, against EVL's one-bid design fixture, and plan Tender A and Tender B (OVS v0.6 §14 counting test).
- Run `consistency_check.py`, `preservation_check.py` and `register_check.py` over the filed package and log what they report (the new register reports 13 errors, all status values outside `workflow_states`).
- **Gate OVS-G00:** all reconciliation files exist; every OVS v0.6 §4.1 row has an owner function and a test name; D3 and D5 have written answers; the AC map covers 18 rows; every finding is in the follow-ups file.

### Phase 1: Design completion (author and owner; rows start `Blocked — owner`)
OVS v0.6 §14.1: "Do not pass it to Claude Design as KT-STD §2 plus a design section." The first slice needs static design sections in the existing owner documents, then conformance matrices.
- EVL: oversight variants (Report sent, with Award, status only, returned, cancelled, no bids) with exact labels and actions.
- TPR: placement, block content and copy for **Decisions and progress**.
- PRC: the populated Procurement meetings brief (title, description, empty and error copy, fixture rows).
- Award and Opening: status, outcome and opening-metric wording now shown as `[ … ]`.
- Each owner section: artboard ID, archetype, actor and task, Level 1/2/3, ordered composition, exact labels and values, exhaustive visible and absent actions, loading/empty/error/denied variants, first-view comprehension tests, next-step and journey content or an explicit absence; the actor/state/event conformance matrix.
- Fixture binding: exact dates, attendance, duration, outcomes and a stable display reference per isolated fixture (OVS v0.6 §14.1).
- **Server phases do not wait for this phase. UI phases 6–8 do.**
- **Gate OVS-G01:** the owner's recorded approval of the three design sections and the fixture values; any `[ … ]` left in a board is an explicit, owner-accepted omission.

### Phase 2: Evaluation disclosure (server)
- Red: a state-by-state leakage test, driven through every endpoint (`get_evaluation`, `get_report`, `get_bid`, `get_evidence`, `get_committee_record`, `list_work`, My Work) and the evidence download, as the Accounting Officer, the Head of Procurement Function (not secretary, not recipient) and Naomi Chebet.
- `access()`: add oversight classification and the delivery point (D2). Committee, secretary and recipient access do not change.
- `oversight.py`: the projection from the frozen delivered version (D1), with the bidder inventory, per-bid findings, financial comparison, clarifications, committee record, due diligence, recommendation and reasons, signatures, versions, correction notices, and the evaluated submissions' documents (D3).
- Rules per state: Preparing, Reviewing and Signing are status only; Report sent is full; returned keeps the delivered version; cancelled before delivery is status plus the cancellation facts; cancelled after delivery is full; no-bids is full; expiry shows **No current recommendation — tender validity expired** and implies no winner; suspension adds the instruction.
- `next_steps.py`: candidates for AO and HOPF at Report sent with a `view_report` action; the Award pointer through the seam (D9); no task, no new kind.
- Evidence and download: recheck the delivered-version association and current permission at every read, including a direct file URL.
- Head of User Department: administrative progress before delivery; scoped outcome, reasons and correction/expiry status after; no full report, bids or committee notes (OVS-P02).
- Technical read per D11, with explicit leak tests (no sealed content, no keys).
- Rewrite `test_who_reads_what` to be state-aware, and add the committee/secretary regression.
- **Gate OVS-G02:** the leakage test and the new service tests pass on the test site; `test_evl_reads` passes; module tests once; OVS-AC-004–007, 009 and 017 have evidence.

### Phase 3: Tender stage summaries (server)
- Define the hook `kt_tender_stage_summaries` and the summary read model from Phase 0; providers for Opening, Evaluation and Award, each deciding its own disclosure (status only or full).
- `get_tender()` returns the summaries beside `record_links`; TPR exposes the certified lead and contributor identifiers from the exact consumed source version (OVS v0.6 §4.1, AUTH-ADR-001 v1.11 §5.3), not an editable copy.
- Department-head scope uses the existing `department` reader mode; AO also receives the explicit contextual Opening read after reveal (OVS-P01).
- Failure contract: an authorised stage that fails returns `OVS_STAGE_UNAVAILABLE` (**We could not load this stage**, **Try again**); a denied stage is omitted; the two cannot be told apart by an unauthorised reader.
- Repo-wide grep for every consumer of `kt_tender_record_links` and `record_links` before changing its use.
- **Gate OVS-G03:** provider tests per owner; a Tender with lead and contributor departments shows the right stages to the right readers; OVS-AC-008, 010 and 011 have evidence.

### Phase 4: Procurement meetings register (server)
- Add `can_read_row` to each owner adapter (D7); add `proceedings/services/register.py` and a whitelisted GET API (the Proceedings module has no `api.py` yet).
- Rows, held totals, department grouping (**Grouped by lead department**), filters (Type, Department, State, From, To, Find a tender), inclusive site dates of actual start (Not held uses the recorded scheduled date, labelled Scheduled), distinct-people attendance, duration, totals before pagination, and the incomplete-totals failure (D5–D8).
- The counting test: Tender A (lead A, contributor B, one Opening and two Evaluation sessions started) and Tender B (lead B, one Not held opening) give four rows and three held; filtering contributor B returns the same four and three; pagination does not change totals.
- Readers: AO, HOPF, authorised auditor, Head of User Department within scope, Administrator and System Manager (D11).
- **Gate OVS-G04:** the counting test and the leakage test (no subject, notes, bidder name, bid count or finding in any state) pass; OVS-AC-012 has evidence for the server side.

### Phase 5: Seeds and fixtures
SEED-OPS-001 v1.22 and OVS v0.6 §14: add isolated branches on the canonical four-bid story. Delivered and returned report; Tender A and Tender B as above (department A Digital Health, department B Human Resources Management and Development; resolve real identities under SEED-OPS decision D3); a Not held opening; ongoing and aborted sessions; pagination volume; Dr Peter Kimani's HRMD assignment as the positive department persona; Julia Njeri's expired 2026 acting term as a negative persona. Extend each module's `playwright_ui_fixtures`.
- **Gate OVS-G05:** `make seed-canonical-validate` still passes with the canonical story unchanged; each isolated branch loads and unloads cleanly; the branches are registered with the purge cleanups.

### Phase 6: UI slice A, Evaluation oversight screens (needs Gate OVS-G01)
Vue screens for the oversight variants from the frozen projection (D13): Report sent, with Award, status only, returned (with a labelled version selector that preserves the selected version and return path), cancelled, no bids. Fidelity departures; one Playwright spec; live walk as Amina Hassan, Charles Mutiso and Naomi Chebet.
- **Gate OVS-G06:** the leakage test still passes; the board comparison is recorded; the live check is recorded.

### Phase 7: UI slice B, Tender **Decisions and progress** (needs Gate OVS-G01)
The section on the Tender record from the summaries: status, latest disclosed outcome, actor, date, reason, outstanding matter, one primary **View record** plus **View report** or **View supporting records**. It replaces the three header buttons only when each equivalent authorised link works. Partial failure leaves other blocks usable.
- **Gate OVS-G07:** the variants from OVS v0.6 §14 are exercised (Opening only, Evaluation protected, delivered outcome, corrected version pending, Award decision, partial failure); a live check as each persona.

### Phase 8: UI slice C, Procurement meetings page (needs Gate OVS-G01)
Page record, one `desk_page.register` call, Vue register with totals, filters, **Clear filters**, filtered result count, and states (populated, contributors, ongoing, Not held, scoped, incomplete, no matches). Sidebar item after Awards, `_KT_ROUTE_TO_SIDEBAR`, `bench migrate`, `make validate-links`, route-slug check.
- **Gate OVS-G08:** the page loads by direct URL, refresh and back/forward with filters preserved; keyboard and zoom checked; the sidebar item is live after migrate.

### Phase 9: First-slice live walk and release evidence
Walk the whole first slice in a browser as Amina, Charles, Naomi and Dr Peter Kimani: first paint and at least one interactive re-render on each surface; the negative personas; write `evidence/v0_6/`.
- **Gate OVS-G09:** all first-slice AC rows have recorded results; the owner is told exactly what was and was not run. "Earlier verified improvements may be released independently" (OVS v0.6 §17).

### Phase 10: Other-module read grants
Strategy and Budget (tuple plus DocPerm rows, then the scope hooks); Needs (AO/HOPF branch in `can_view` and the review-task reads); Requisitions (add the Accounting Officer to `requisition_roles.py` and check `TENDER_SEAM_READER_ROLES`); Planning (verify only); Bid Submission and Configuration (navigation and history only; no new audience). Each: the HoD grant is by authoritative source relationship; a shared budget line does not establish ownership; repo-wide caller grep first; one module test run each.
- **Gate OVS-G10:** each OVS v0.6 §4.1 row has a passing test and a recorded negative case (unrelated department, drafts, revoked responsibility).

### Phase 11: Register and record usability coverage (OVS v0.6 §§5, 6, 12)
Per module, a coverage row: Active and All records, search by reference and title, supported filters, **Clear filters**, filter/sort/page preserved on return, completed/cancelled/returned records findable, a record view with identity, current disclosed decision, supporting information and history, honest empty and error states. Modules: Configuration, Strategy, Budget, Needs, Planning, Requisitions, Tenders, Bid Submission, Opening, Evaluation, Award, Proceedings.
- **Gate OVS-G11:** every module has a recorded coverage result or an exclusion with a specific reason and owner (OVS-AC-018).

### Phase 12: CTX v1.1 refactor (breaking)
Retire the global PE selector and preference, the PE Fiscal Year Context gate, and User Permission / User Scope Assignment as authority in `kentender_core`; keep reversible module-local filters (`get_module_fy`, `select_module_fy`, `get_module_ou`, `select_module_ou`) where they satisfy CTX v1.1. Repo-wide caller audit first; remove only what has no live caller; CTX v1.1 says "No installed implementation was inspected", so this phase starts by inspecting it.
- **Gate OVS-G12:** no route requires PE selection; a direct link works despite a different saved filter; callers audited and listed.

### Phase 13: Owner-gated and deferred (every row `Blocked — owner` or `Deferred`)
Contract Management stages 1–3 and their ERPNext accounting views (OVS-AC-013, 014), the separate template walkthrough, supplier contract/delivery/payment designs. **No gate in this plan.** Nothing in this phase counts toward a readiness claim.

## Conflicts and follow-ups to log (Phase 0)

| # | Conflict | Treatment |
|---|---|---|
| C1 | EVL v0.5 §3 still reads "Appointment access contains no automatic right to read bids or alter findings", while OVS v0.6 §4.1 gives the AO and HOPF a delivered-version read. | Read as appointment-based; the right here comes from delivery. Log for an EVL wording clarification. |
| C2 | KT-STD v1.15 §3A.6 body does not yet carry the OVS v0.6 §4.2 carve-out (sealed content, limited operators), and §8.3 still calls Daniel Otieno a technical reader. | D11 follows OVS v0.6 §4.2; log for KT-STD. |
| C3 | EVL's design fixture is a single bid; the canonical story and OVS v0.6 §14 use four. | Build to the four-bid canonical story; log for EVL design. |
| C4 | TPR v0.17 §10.10 gives no placement or copy for Decisions and progress. | Phase 1 owner deliverable. |
| C5 | The retired OVS v0.1 reuses OVS-AC-001–024 with different meanings. | It is in `retired/`; only v0.6's IDs are used. |
| C6 | Stale control text in the filed package: EVL v0.5 "Version / date 0.4"; Roadmap v1.3 date; TPR v0.17 §18.0A and CFG v0.18 "proposed / None"; AUTH, BOP, AWD, PRC preambles call the §4.2 rule "proposed"; BOP and PRC cite KT-STD v1.10. | Not edited (approved documents). Logged. Treat each document's top "Controlling approval" paragraph as winning. |
| C7 | SEED-001 v1.4 names v1.2 as its predecessor; v1_3 also exists in `00_common`. | Logged. |
| C8 | The filed register reports 13 `register_check` errors (status values outside `workflow_states` for CTX, OVS, PLN and several delivery items). | Logged for the documentation owner. |
| C9 | `Makefile:1365` and `kentender_core/kentender_core/seeds/README.md:33` name SEED-OPS v1_21 as the maintained runbook. | Still valid (v1_21 is kept). Advance to v1_22 as a follow-up. |

## Risks

- **Evidence associations may be missing (D3).** Mitigation: Phase 0 verifies; an addition needs owner sign-off.
- **`lead_org_unit` can be null or reassigned (D5).** Mitigation: show **Department not recorded**; use owner history for attribution when reassignment exists.
- **Opening has no session row (D6).** Mitigation: two row sources, one counting test that includes both.
- **UI built before the design closes.** Mitigation: Gate OVS-G01 blocks Phases 6–8.
- **Changing Evaluation reads leaks bids.** Mitigation: the projection comes from the frozen version (D1); the leakage test drives every endpoint and download as the real personas.
- **CTX v1.1 breaks callers.** Mitigation: Phase 12 starts with a repo-wide caller audit and removes nothing with a live caller.
- **A Python test run during Playwright corrupts state.** Mitigation: `ovs-preflight` refuses to run while a Playwright run is active (modelled on `evl-preflight`).
- **`bench migrate` overwrites sidebar JSON.** Mitigation: edit once, migrate twice, run `make validate-links`, and check the live sidebar.
- **A Playwright run can be mutating the dev site unannounced.** Mitigation: use the test site; check `make ui-queue-check` before reading code on odd UI failures.

## Verification

```bash
# per phase: one focused test first (red, then green), on the test site
cd /home/midasuser/frappe-bench
bench --site kentender-test.local run-tests --app kentender_procurement \
  --module kentender_procurement.bid_evaluation.tests.test_evl_reads

# then the module tests once
make ovs-services-gate          # to be added in Phase 0, modelled on evl-services-gate / awd-services-gate
make ovs-leakage-gate           # AO/HOPF/auditor/department-head negative reads across endpoints
make ovs-dead-end-gate          # every OVS state resolves to a screen with a way out

# UI, test site only
scripts/test-site.sh run npx playwright test tests/ui/smoke/oversight/<spec>.spec.ts --workers=1
make ui-structure-gate          # includes a new vitest project if a board is comparable
make ui-queue-check             # before reading code on odd UI failures
make validate-links             # after the sidebar change
make artboard-provenance-gate   # the filed board must still pass (passed 3 Oct 2026)
```

New `ovs-*` targets are added to `.PHONY` (Makefile line 9). No target is added until it has a test to run.

**Live browser walk (Phase 9), on the canonical site with the test profiles:**
1. Amina Hassan (Accounting Officer): open the Tender, see **Decisions and progress**; open Evaluation before delivery and see status only; open it after delivery and see the report, recommendation, reasons and signatures; open the evidence for an uncited submission.
2. Charles Mutiso (Head of Procurement Function): the same, plus the state after Award takes the review; confirm no sign, return or finding action appears except his own review actions.
3. Naomi Chebet (Auditor): read-only everywhere; the register.
4. Dr Peter Kimani (Head of User Department): scoped progress for Tender A and B; nothing from unrelated departments; no full report.
5. Julia Njeri on the dates her term has expired: nothing.
6. Procurement meetings: apply each filter; confirm totals do not change with pagination; confirm **Grouped by lead department**; trigger the incomplete-totals state with a denied row.
7. Returned report: the earlier version stays readable, labelled **Returned for correction**; the corrected version replaces it as current once delivered, and the selector keeps the earlier one.
8. Refresh and browser back/forward on every surface; keyboard-only pass on the register.

## Build findings (4 October 2026)

These are recorded here; the phase text above is not rewritten.

| # | Decision | Why |
|---|---|---|
| D15 | **The Tender's lead department is corrected at its source before anything reads it.** `Tender.lead_org_unit` is today the alphabetically first contributing unit, not the certified lead (`tenders/services/draft_commands.py:111`, `tenders/services/snapshot.py:116-118`). Phase 3 reads the certified lead from the consumed handoff (`departmental_certification.lead_org_unit_id`), exposes it through the Tender read, patches existing Tenders from their handoff and fixes the same stale read in `tenders/services/correction.py:82,97`. | OVS-DEC-3 and OVS v0.6 §4.1 require the "certified lead and contributing OU identifiers from the exact consumed REQ Version". Reading the stored field would attribute meetings to the wrong department whenever the certified lead is not first alphabetically. `baseline_audit.md` section 4. The change touches Tenders data and code, so the owner is told (FU-OVS-36) before it is built. |
| D16 | **Phase 2 is split.** Part A builds the AO and HOPF oversight view from the frozen report content: report text, findings, comparison, clarifications (Sent replies), sessions, disagreements, recommendation, reasons and signatures. It needs no stored addition. Part B, the evaluated bid versions, "all submitted documents … even if not individually cited" and the committee-record items not frozen today, needs an evidence manifest stored beside `content_json` and a backfill for delivered versions, and is **Blocked — owner** (OVS6-0213, FU-OVS-11). | The frozen version carries no submission version, receipt or document list (`baseline_audit.md` section 3). OVS v0.6 §3 allows only "the smallest owner-owned addition", and tracker rule 6 requires the owner's sign-off first. The manifest sits beside the content, not inside it, because `content_json` is hashed and signed and existing delivered reports cannot change without breaking their signatures. |
| D17 | **Attribution is by Organisation Unit code, display by current name.** The Tender stores the code; the lead is never reassigned; units can be renamed and moved with only the Frappe Version log as history. | OVS v0.6 §11 asks for owner history "if reassignment is supported". Reassignment is not supported (`baseline_audit.md` section 4). Moving a unit changes scope by the descendant rule but not grouped totals. |
| D18 | **Evidence reads gain a version.** `reads.evidence` takes an optional report version; with one, a (bid, digest) pair is allowed only if it is in that version's manifest, and the recipient and the AO are admitted through that path. A successful read is audited. | Today `evidence()` is bound to the case, not to a delivery, and the delivered recipient cannot reach any bid document (`baseline_audit.md` section 3.3). The audit question is open to the owner (FU-OVS-37). |
| D19 | **The canonical Tender is Tender A.** It already has lead Digital Health, contributor Human Resources Management and Development, a finalized opening with no session row, two ended Evaluation sessions, four bids, a delivered report with review state With Award and an Award case at the Opinion stage. Only Tender B (lead Human Resources Management and Development, one Not held opening) is a new isolated branch. | Observed on the dev site, 4 October 2026 (`baseline_audit.md` section 2). Whether the certified lead is Digital Health is checked first in Phase 3 (OVS6-0310). |
| D20 | **Peter Kimani's cases run under a stated clock.** On the real date his Digital Health assignment has not started (it begins 1 December 2026) and Julia Njeri holds Digital Health. He reaches Digital Health today through the Directorate assignment (from 1 September 2026) by the descendant rule, and the Tender through his permanent HRMD assignment. Phase 5 states the clock for each persona case. | `baseline_audit.md` section 2.2–2.3; AUTH-ADR-001 v1.11 §4.3. |
| D21 | **Read probes use the wrapped form** `PYTHONPATH=<scratchpad> bench --site kentender.midas.com execute "__import__('<module>').run"`. | The dotted form fails with "App … is not installed" and a NameError naming the scratch module, which is not queue overload (`baseline_audit.md` section 6). |
| D22 | **Strategy: an approved-only read at the contract layer.** `read_scope(user)` returns `full` (existing readers), `approved` (AO, HOPF, a Head of User Department in any unit) or nothing; the portfolio, plan workspace, tree and history contracts filter to Active and Superseded versions for `approved`; the approval task and the comparison stay `full` only. | Strategy's reads are gated in its service contracts, not by DocPerm, so the filter belongs there. Strategy has no department attribution, so the department head's read is of approved versions (FU-OVS-30). Built 4 Oct 2026; tracker OVS6-1001. |
| D23 | **Budget: a hook wrapper, not new core code.** `budget_read_scope.py` wraps the core `permission_query_conditions` and `has_permission` for the four Budget doctypes: a reader of approved versions only (AO or HOPF holding no Budget responsibility) sees a Budget, its lines and line versions only through an Active, Superseded or Closed version. DocPerm read rows added; the contracts answer Not found to that reader for a version not yet approved. | Budget reads go through DocPerm and the scope hooks, so the state limit must be there too; the existing pending-version summary already falls back to `has_permission`, so a pending version is hidden without a second rule. Tracker OVS6-1002. |
| D24 | **Requisitions: the state is in the permission query.** The Accounting Officer reads a Requisition whose state is Authorised or Revoked (permission query condition, record `has_permission`, `_reader` with the state, workspace gate, DocPerm rows). `require_requisition_reader` takes the state as an optional argument; callers that pass none are unchanged. | One rule at the framework hooks and in the record read the screen uses. Tracker OVS6-1004. |
| D25 | **Needs: an observer profile.** `can_view` returns `oversight` for AO and HOPF on a Submitted, Accepted for planning or Not taken forward Need; `require_review_read` and `viewing_contexts` follow. A Returned Need is excluded: its revision is the author's again. | NDS v1.16 §6 allows only the neutral read. Tracker OVS6-1003; FU-OVS-52. |
| D26 | **Home shows the site's one entity.** `list_available_entities` returns the entity named by `Site Procuring Entity`; an explicit request for another is refused; the global working-entity preference is neither read nor written. The PageRail switcher and `working_context_api.py` are removed. | CTX-CHG-001 v1.1 §2 and AUTH-ADR-001 v1.11. The authority code is left for a later phase (FU-OVS-56). Tracker OVS6-1203. |
| D27 | **Tender B is the Bid Opening browser-test world, loaded on request.** `ovs_register_branch.load()` runs `reset_opening_fixture(stage="not-held")`; `unload()` runs `restore_site`. Its lead department is a Playwright unit, not Human Resources Management and Development. | It reuses a fixture that already tells a Not held opening through the real commands, and leaves the canonical rows alone. Building a Human Resources Management and Development-led Tender needs a certified requisition walked through the Tenders chain (FU-OVS-47). SEED-OPS-001 v1.23 §9C. |
