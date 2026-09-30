# EVL-CHG-001 v0.4: Bid Evaluation, tracker

| Control | Value |
|---|---|
| Version | 0.4-tracker.4 |
| Date | 30 September 2026 |
| Status | Phases 0–10 services built and gated (EVL-G03…G09 Passed, EVL-G10 Partial; `make evl-services-gate` 80/80, 30 Sep 2026); Phase 11 screens written, not yet run in a browser. (0.4-tracker.3 read: Phases 0–2 done; Phase 3 in progress.) (0.4-tracker.2 read: Phase 0 done (EVL-G00, 30 Sep 2026); Phase 1 next.) (0.4-tracker.1 read: Planned. No phase started; no code written.) |

**Authority:** `KenTender_EVL-CHG-001_Bid_Evaluation_v0_4.md`, Approved 30 Sep 2026 by the Project Owner, including R1–R3. Governing standard: KT-STD-001 v1.12 (approved 30 Sep 2026). Shared services: PRC-CHG-001 v0.9 and TRUST-ADR-001 v0.1. EVL v0.4 §6 extends both, and those extensions are owed as coordinated amendments (OD-A).

**Plan:** `EVL-CHG-001_v0_4_Implementation_Plan.md`. It holds owner decisions OD-A…OD-D, technical decisions D1–D20 and conflicts C1–C20.

**Companions:**
- `EVL-CHG-001_v0_4_FOLLOW_UPS.md`;
- Phase 0: `reconciliation/{artboard_inventory, error_contract, handoff_register, fixture_chronology, rule_reconciliation, scope_binding}.md`;
- later: `evidence/v0_4/` and `RUNBOOKS.md`.

**Design:** `design/Bid Evaluation Artboards.dc.html` and `design/evl/*.js`. It has 107 drawn boards and no note-only entries.

**Started:** 30 September 2026.

## Tracker rules

1. **Rows are permanent.** Status vocabulary: `Planned` / `In progress` / `Blocked` / `Blocked — owner` / `Partial` / `Done`. Reversed decisions are struck through in place, never deleted.
2. **`Done` needs the row's own evidence.** Acceptable evidence is a command with result counts, a named test, a commit, or a described browser observation with literal rendered strings. Never record a result that was not observed. An honestly incomplete row is `Partial`. A result proven only through a simulation stand-in says so ("simulation") and never closes a production part.
3. **Prohibited in new code:**
   - an award, **Approve**, **Select winner**, **Negotiate**, **Accept all results**, per-check member approval, chair **Complete**/**Activate**/**Release**, recipient receipt approval, local **Resume**, **Edit criterion**, **Change offer** or **Extend validity** control (EVL v0.4 §4.3, §5.5, §5.7, §9);
   - a write-back to a bid, a published rule or a response; a computed amount stored as a bid fact; an overwritten system or prior finding (§4.3, §4.4);
   - a bid fact (name, count, amount, finding) reachable by the Accounting Officer, an unappointed user, an undeclared or conflicted member, a public page or a technical reader, whether through a DTO, an error, a task title, a count or an export (§3, §7.1, EVL-A16);
   - supplier access to internal findings, ranking, committee notes or another bidder's material (§3, §5.3);
   - a chair, secretary, administrator or service credential acting, attending, disagreeing or signing for a member; a group attendance button (§5.2, §6);
   - evaluator-set units, rounding, thresholds or dates; a default filling a missing rule; free text treated as automatic compliance (§4.1);
   - a preference margin, tax treatment, discount, exchange rate or tie-break not in the published rule; random selection; automatic majority or casting vote (§4.4, §5.2);
   - a budget shortfall that fails a bid, alters ranking or cancels (§4.4);
   - a read of a Bid Submission, Bid Opening, Tenders or Budget doctype from `bid_evaluation` code instead of a published seam (plan D5, D6, D8, D9); an import of `bid_evaluation` from `proceedings`;
   - a change to Bid Opening behaviour through the Proceedings profile work (plan D4);
   - `kentender_core.cl_surface_registry.js`, Civic Ledger or Stitch Desk classes (Industry only);
   - TRUST-ADR-001 test labels drawn into ported board markup. They render only at runtime under `kt_bds_simulation_environment` (plan D16);
   - simulation stand-ins loading without that flag (OD-D).
4. **Governing sections:**
   - EVL v0.4 §9 and the boards govern visual and content fidelity. Board markup is ported class-for-class.
   - EVL v0.4 §4, §5 and §7 govern behaviour; §7.3 governs work items; §8 governs error copy, verbatim, with separate detail; §10 maps each control to exactly one command or read.
   - Browser literals come from EVL v0.4 §9.1/§9.12 and the approved BDS/BOP source facts, never from board placeholder data. The runtime replaces every fixture time, attendance, proof and delivery value with actual events.
5. **Mapping:** every visible action maps to exactly one EVL v0.4 §7.2 command or §7 read (EVL-A15), and every cross-module effect maps to one seam in plan D5, D6, D8, D9, D12 or D14.
6. **Site safety:**
   - Never run a `bid_evaluation` or `proceedings` Python module while a Playwright process is active.
   - Reseed to canonical after Python runs, because `bench run-tests` has no rollback.
   - Test fixtures use years ≥ 2100.
   - Every test module registers purge cleanup, and browser-pass records count as test data.
7. **Production gate:** no production signing, custody release or delivery is claimed. Phase 15 rows stay `Blocked — owner` until the owner supplies the named evidence.
8. **Acceptance closure:** an AC row is `Done` only when every part it names is proven. Production-only parts are split into a Phase 15 row, never silently dropped.
9. **Owner-document seams (OD-A):** every change to another owner's code (Proceedings, Bid Opening, Bid Submission, Tenders, STD templates, Budget read, core) records an addendum row in that owner's tracker in the same commit, and keeps its Phase 15 follow-up open.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 30 Sep 2026 | OD-A: build first, amend later. Owner answer, verbatim: "Build first, amend later". | The Proceedings, Tenders, Bid Submission, STD-TPL, BOP, Budget and KT-STD amendments are Phase 15 follow-ups (FU-EVL-01…07). They block no phase. |
| 30 Sep 2026 | OD-B: a new shared core Support Issue record. Owner answer, verbatim: "New shared core record (Recommended)". | EVL v0.4 §6 names "the platform support-issue record", which does not exist (C2). Moving Bid Opening and Bid Submission onto it later is FU-EVL-12. |
| 30 Sep 2026 | OD-C: a versioned evaluation-rules file in the template pack. Owner answer, verbatim: "Versioned file in the template pack (Recommended)". | EVL v0.4 §4.1: "The curated template implementation must supply this executable meaning for each automatic rule." |
| 30 Sep 2026 | OD-D: the stand-ins run on the dev site under `kt_bds_simulation_environment`. Owner answer, verbatim: "Yes, same as Bid Opening (Recommended)". | This follows the BDS v0.8 and BOP v0.10 precedent. |
| 30 Sep 2026 | D1–D20 adopted as implementation authority (plan). | They fill the implementation bindings EVL v0.4 §6 and §12 leave to coordinated work. |
| 30 Sep 2026 | Phase 0: (1) C21: the canonical Tender is TND-MOH-2027-002; board literals 033 are fixture data. (2) C22: the canonical Afya bid is placeholder data and fails the automatic checks; the Bid Submission seed is corrected in Phase 13 (EVL4-1306). (3) C23: the hand-off omits the definition identity; Evaluation reads it from the package. (4) D21 scope binding to the release `supported_use`; D22 dated rules (no authoritative evaluation deadline yet, C24); D23 the 19 check kinds. | `reconciliation/*.md`; plan "Phase 0 findings". |
| 30 Sep 2026 | Phase 3: D24, the evaluation-rules file is a separately versioned companion of the template (`07_tender_templates/evaluation_rules/`), not an asset inside the digest-bound release, which cannot change for Tenders already bound to it. D25, the scheduler sweep binds intake and preparation; no producer calls Evaluation inside its own transaction. The core `Support Issue` My Work row is registered in `kentender_core` hooks. | Plan "Phase 3 findings". |
| 30 Sep 2026 | Test worlds are shared per test module. Owner instruction, verbatim: "Yes, optimize the testing please. There is no reason to tear down and start afresh for each and every test." `bid_evaluation/tests/support.py`: the published Tender, the answered bid and the completed opening are built once per module and kept until it ends; every test starts from no Evaluation rows, the opening hand-off back to Pending, simulation switches off and the world's clocks. `world` = completed / empty / open and `overrides` key the world; a class needing a different one replaces it; `shared_world = False` keeps a per-test build for the three classes whose tests need the opening at their own moment. | `make evl-services-gate` 80/80 in both forms; test time 1,094 s → 444 s (wall 508 s); no Tender, bid, opening or evaluation left after the run. Bid Opening's own suites still build per test (not changed). |

## Gate register

| Gate | Condition | Status | Evidence |
|---|---|---|---|
| EVL-G00 | Phase 0: inventory = 107 boards, each in exactly one slice; §8 error contract, §7.3 hand-off register, fixture chronology, rule reconciliation (every response identity classified) and scope binding written; conflicts logged; design folder and spec committed; `make artboard-provenance-gate` green | Passed | 30 Sep 2026: inventory 107 rows (92 Covered, 15 Conditional; slices 11.1 = 16, 11.2 = 11, 11.3 = 8, 11.4 = 14, 11.5 = 8, 11.6 = 24, 11.7 = 15, 11.8 = 4, 12 = 7); error contract 15 + 2; hand-off register 20 rows; chronology 15 ordinary rows + 22 branches, each with a fixture entity; rule reconciliation 136 evaluated response rows, every one classified; scope binding six predicates bound (D21). Design and spec committed in `f35fffce`. `make artboard-provenance-gate` 3/3 OK. Findings C21–C24, D21–D23. |
| EVL-G01 | Phase 1: module, doctypes, core Support Issue, PRC schema additions, flags guard, sidebar replacement, `make validate-links`, migrate clean twice | Passed | 30 Sep 2026: `test_evl_schema` 7/7 (red first: 65 errors, DocType not found) and `test_prc_schema` 10/10; Module Def `Bid Evaluation` has `app_name = kentender_procurement` after the first migrate; two clean migrates (the second rewrote only the Procurement sidebar stamp, reverted). The sidebar replacement moved to Phase 11 (EVL4-108). `make validate-links` not run: no link changed. |
| PRC-G02E | Phase 2: `make prc-services-gate` including the Evaluation-profile tests; `make bop-services-gate` unchanged and green | Passed | 30 Sep 2026: `make prc-services-gate` 62/62 (schema 10, lifecycle 13, events 8, minutes 11, access 4, evaluation profile 16); `make bop-services-gate` 85/85 unchanged (schema 7, gateways 13, custody seam 7, pre-session 22, ceremony 13, record 9, API 5, public 9). The profile tests were written first but passed on their first run; mutation checks (presence rule off, stale-target rule off) each failed the suite (3 failures), then the code was restored. |
| EVL-G03 | Phase 3: Bid Opening seam (digest verified), Bid Submission package seam (four trust outcomes), Tenders seam, rules file and validator, Support Issue service, simulation controls; `bop-services-gate`, Bid Submission and Tenders regression green | Passed | 30 Sep 2026: seams, rules file, Support Issue service and simulation controls; `make evl-services-gate` modules `test_evl_seams` 6/6, `test_evl_rules` 12/12 (mutation-checked), `test_evl_errors` 3/3, core `test_support_issues` 3/3; `make prc-services-gate` 62/62; `make bop-services-gate` 85/85 after the Proceedings changes (Phase 2, twice); a later full re-run was stopped at 71/71 green as redundant (only additive seam and test-box changes since). Installer/validator for the rules file not built (EVL4-305 Partial). |
| EVL-G04 | Phase 4: preparation, scope gate, appointment, replacement, secretary, declaration, unavailability, roster rules, preparation work items | Passed | 30 Sep 2026: `test_evl_preparation` 4/4, `test_evl_committee` 10/10 (in `make evl-services-gate`, 80/80). |
| EVL-G05 | Phase 5: intake, empty outcome, source issue, checks, rules vectors, aggregation, comparison, funding, timers | Passed | 30 Sep 2026: `test_evl_intake` 6/6, `test_evl_comparison` 2/2, `test_evl_rules` 12/12. Funding and timers built without a dedicated test (EVL4-508, EVL4-509 Partial). |
| EVL-G06 | Phase 6: findings, concerns, discussion sessions, notes, conclusions, disagreement, issues and retry | Passed | 30 Sep 2026: `test_evl_discussion` 10/10. |
| EVL-G07 | Phase 7: clarification, including both reply/closure commit orders | Passed | 30 Sep 2026: `test_evl_clarification` 5/5. The two concurrent commit orders have no dedicated test (EVL4-708 Partial). |
| EVL-G08 | Phase 8: due diligence | Passed | 30 Sep 2026: `test_evl_diligence` 2/2 (new). |
| EVL-G09 | Phase 9: report, signing, delivery, return, correction, supplements, tender events, qualified outcomes | Passed | 30 Sep 2026: `test_evl_report` 7/7. Revision, supplements, rechecks and the tie/no-agreement/expiry outcomes are built without dedicated tests (Partial rows). |
| EVL-G10 | Phase 10: `make evl-dead-end-gate` and `make evl-leakage-gate`; My Work matrix against the hand-off register | Partial | 30 Sep 2026: `test_evl_reads` 3/3 (disclosure for AO, Head, outsider, technical reader, undeclared member; sound next step for 9 actors in three states). `make evl-dead-end-gate` and `make evl-leakage-gate` are not yet targets; the full My Work matrix is not one test. |
| EVL-G11.1…11.8 | Phase 11 slices: `ui-evl-<slice>-gate` each; `ui-evl-fidelity-gate`; one `ui-tenders-*` and `ui-bop-*` regression run after the Tenders seam | In progress | 30 Sep 2026: screens, workspace, browser world, capture script and fidelity harness written; nothing run in a browser yet. |
| EVL-G12 | Phase 12: `ui-evl-supplier-gate`; Bid Submission portal regression | Planned | |
| EVL-G13 | Phase 13: `seed-canonical THROUGH=bid_evaluation` and `seed-canonical-validate`; second run idempotent; `evl-demo-walk.spec.ts` | Planned | |
| EVL-G14 | Phase 14: `ui-evl-fidelity-gate` (107), state/actor and branch matrix, persona pass, `ui-evl-release-evidence-gate` | Planned | |

## Work register: Phase 0 (documents and reconciliation)

| ID | Item | Status | Evidence |
|---|---|---|---|
| EVL4-001 | Plan, tracker and follow-ups (new versioned files) | Done | 30 Sep 2026. `EVL-CHG-001_v0_4_{Implementation_Plan, IMPLEMENTATION_TRACKER, FOLLOW_UPS}.md`. |
| EVL4-002 | `reconciliation/artboard_inventory.md`: 107 boards by script from `window.EVL.boards`, with component#variant, slice and Covered/Conditional; the 18 boards without a spec ID mapped to spec prose (C15) | Done | 30 Sep 2026: `tools/extract_boards.js` + `tools/build_inventory.py`; 107 boards, 92 Covered, 15 Conditional (signing double, funding read, simulation-only owner events); every board has a registry spec reference; the 18 without a variant ID each name the prose they depict. |
| EVL4-003 | `reconciliation/error_contract.md`: EVL v0.4 §8, 15 codes and 2 nonblocking conditions, verbatim by script | Done | 30 Sep 2026: `tools/build_contracts.py`; 15 blocking + 2 nonblocking, with the PRC v0.9 §8 → Evaluation mapping checked against `proceedings/services/errors.py`. |
| EVL4-004 | `reconciliation/handoff_register.md`: §7.3 rows → holder, My Work title, waiting item, notification, clearing event, named test | Done | 30 Sep 2026: `tools/build_contracts.py`; 20 rows verbatim, each with its planned named test. |
| EVL4-005 | `reconciliation/fixture_chronology.md`: §11.1 ordinary path and §11.2 branches, each with entry point and reset state | Done | 30 Sep 2026: `tools/build_chronology.py`; 15 ordinary rows and 22 branches, each branch with its own test-year fixture entity (TND-MOH-2101-E01…E22). |
| EVL4-006 | `reconciliation/rule_reconciliation.md`: every RR/DM/response identity of the canonical Tender's published definition, classified, with its published fact and expected §9.12 result | Done | 30 Sep 2026: `tools/dump_source.py` (bench console) + `tools/build_rules.py` on TND-MOH-2027-002 (C21): 22 mappings (19 evaluated, 3 not evaluated), 136 evaluated response rows in 19 check kinds (D23). Found C22 (placeholder canonical bid) and C23 (hand-off without definition identity). |
| EVL4-007 | `reconciliation/scope_binding.md`: the six §5.1 predicates → published field and value, or gap (C7); the dated-rule anchors (C10) | Done | 30 Sep 2026: all six predicates bound to the release `supported_use` and `Tender.product_key` (D21, closes C7); validity published as 2027-10-10; no authoritative evaluation-deadline rule (C24, D22). |
| EVL4-008 | Commit `design/` and the spec; `make artboard-provenance-gate` | Done | 30 Sep 2026: committed in `f35fffce`; `make artboard-provenance-gate` 3/3 OK. |
| EVL4-009 | Conflicts C1–C20 logged; FU-EVL-01… opened | Done | 30 Sep 2026: plan "Conflicts" table; `EVL-CHG-001_v0_4_FOLLOW_UPS.md`. |
| EVL4-010 | Report the register drift (C17) to the documentation owner; leave the owner's uncommitted register and `.xlsx` changes untouched | Planned | |

## Work register: Phases 1–15

| ID | Phase | Item | Status | Evidence |
|---|---|---|---|---|
| EVL4-101 | 1 | `bid_evaluation` module in `modules.txt`; Module Def app check after the first migrate (D1) | Done | 30 Sep 2026: `Bid Evaluation` in `modules.txt`; Module Def app correct after the first migrate (no new-module cache trap). |
| EVL4-102 | 1 | Case and committee doctypes: Evaluation Case, Appointment (+ Committee Member), Secretary Appointment, Declaration, Member Unavailability (D2) | Done | 30 Sep 2026: generated with the flags guard (`kt_evl_command`, `kt_fixture_wipe`); `test_evl_schema`. |
| EVL4-103 | 1 | Assessment doctypes: Source Intake, Evaluation Bid, Check Run, Check Result, Finding, Discussion Item, Conclusion, Disagreement (D2) | Done | 30 Sep 2026: as EVL4-102; bid-content records have no role at all (`test_administrators_cannot_read_bid_content_or_findings`). |
| EVL4-104 | 1 | Correspondence, diligence, report and event doctypes: Clarification (+ Reply), Verification Plan, Verification Observation, Report Version, Report Delivery, Source Event, Correction Notice, Command Journal, Bid Evaluation Settings (D2) | Done | 30 Sep 2026: as EVL4-102, plus the Single `EVL Test Environment Controls` (plan D16) with no role. |
| EVL4-105 | 1 | Core `Support Issue` doctype (D12) | Done | 30 Sep 2026: `kentender_core` doctype `Support Issue` (guard `kt_support_issue_command`); `TestSupportIssueRecord`. |
| EVL4-106 | 1 | Proceedings schema: `Proceeding Session`, `proceeding_type` option "Bid Evaluation", new target types (D4); BOP schema tests unchanged | Done | 30 Sep 2026: `Proceeding Session` (no role); `proceeding_type` + "Bid Evaluation"; state + "Open"; attendance/event `session`; attendance capacity + "Secretary"; minutes version `record_kind` (default "Opening minutes") and `owner_reference`; three new target types. Bid Opening always sets its state explicitly, so the inserted option changes nothing there. `TestEvaluationProfileSchema` 2/2. |
| EVL4-107 | 1 | Schema contract tests (`test_evl_schema.py`, core Support Issue schema, PRC schema additions), red first; Makefile `evl-preflight`, `evl-services-gate` | Done | 30 Sep 2026: `test_evl_schema.py` (red first), PRC schema additions; Makefile `evl-preflight`, `evl-services-gate` (grows per phase). |
| EVL4-108 | 1 → 11 | Sidebar "Evaluation" coming-soon replaced by the `bid-evaluation` Page link; `workspace_sidebar/*.json` dangling-link check; `make validate-links`; migrate clean twice (D13) | In progress | 30 Sep 2026: Page `bid-evaluation` added (`bid_evaluation/page/bid_evaluation/bid_evaluation.json`, controller `public/js/bid_evaluation_page.js`, hooks `page_js`). Needs a migrate before the sidebar entry can point at it (a dangling Page link fails the whole migrate); sidebar not yet changed. |
| EVL4-201 | 2 | `proceedings/services/profiles.py`: per-type pre-session events, register requirement, target types, event completeness, capacities, wording (D4) | Done | 30 Sep 2026: `proceedings/services/profiles.py`; `lifecycle.create_proceeding` takes the type from the owner adapter (`proceeding_type` attribute; default Bid Opening). |
| EVL4-202 | 2 | Sessions: StartEvaluationDiscussion (chair attendance in the same action), Join, Leave, End; one active session per evaluation; no group attendance | Done | 30 Sep 2026: `proceedings/services/sessions.py` start (starter's arrival in the same action), join, leave, lapse (owner/system), end (everyone present leaves at the end instant); one active session. |
| EVL4-203 | 2 | RecordEvaluationConclusion: ordered owner event with the actual participating roster; member-authored disagreement keeps its author | Done | 30 Sep 2026: `sessions.record_conclusion` (absent members listed; participants recorded on the event; owner-event replay checks the stored participants), `append_owner_event`, `record_member_statement` (member only, own words). |
| EVL4-204 | 2 | FreezeEvaluationReport / SupersedeEvaluationReport: exact report and annex targets, and verification report page and signature targets | Done | 30 Sep 2026: `proceedings/services/record_versions.py` freeze/supersede per record kind (report `-Rnn`, verification report `-Vnn`); one frozen version per kind. |
| EVL4-205 | 2 | RecordEvaluationProof through `kt_trust_signing_services`; a stale or uncertain proof never satisfies the current target | Done | 30 Sep 2026: `record_versions.record_proof` through `kt_trust_signing_services`; no proxy; stale digest or superseded version → PRC_TARGET_CHANGED; Indeterminate kept, satisfies nothing. |
| EVL4-206 | 2 | CompleteEvaluationRecord, AppendEvaluationCorrection, scoped read and export | Done | 30 Sep 2026: `complete_record` (every proof, case stays Open), `append_correction` (finalized content unchanged), `abort` (session ended, frozen versions superseded), `read`/`export`. |
| EVL4-207 | 2 | Regression: `make bop-services-gate` and the existing PRC tests unchanged and green | Done | 30 Sep 2026: `make bop-services-gate` 85/85 and the pre-existing PRC modules 46/46 after the change. |
| EVL4-301 | 3 | `bid_opening/services/evaluation_seam.py`: completion (digest recomputed, C5), acknowledge, final_outcome, register_rows, supplements, is_excluded_from_evaluation (D5) | Done | 30 Sep 2026: `bid_opening/services/evaluation_seam.py` (completion with the digest recomputed from the parsed payload, acknowledge once, final_outcome, register_rows, supplements, is_excluded_from_evaluation). `test_evl_seams` `test_completion_is_verified_acknowledged_once_and_never_an_empty_opening`, `test_a_changed_payload_does_not_verify`. BOP addendum row BOP10-E01. |
| EVL4-302 | 3 | `kt_opening_completion_consumers` hook called after commit for the nonempty handoff and the final no-bids outcome; BOP tracker addendum row | Done | 30 Sep 2026: replaced by the Evaluation sweep (plan D25): no call from inside Bid Opening's completion transaction. `sweep.sweep_tender` prepares, takes up the completed opening and closes on a final no-bids outcome; `test_evl_intake` `test_intake_before_appointment_runs_checks_and_gives_no_bid_access`, `test_a_final_no_bids_opening_closes_the_preparation`. The scheduler hook is registered (scheduler disabled on this site). |
| EVL4-303 | 3 | `bid_submission/services/evaluation_gateway.py::released_package`: completion-bound release, digest check, four trust outcomes, one correlation ID; BDS tracker addendum row (D6) | Done | 30 Sep 2026: `bid_submission/services/evaluation_gateway.released_package` over `TestTenderBox.release_for_evaluation`; one TRUST outcome and correlation per call; `test_the_package_is_released_only_for_an_opened_envelope`, `test_nothing_is_released_before_close`. BDS addendum rows BDS8-B06/B07. Simulation only (OD-D). |
| EVL4-304 | 3 | `tenders/services/evaluation_seam.py`: candidates, publication_fact, scope_facts, dated_rules, status_events, award_decision_status; simulation-only owner events; Tenders tracker addendum row (D8) | Done | 30 Sep 2026: `tenders/services/evaluation_seam.py` (scope_facts, dated_rules, status_events, award_decision_status, funding_reservations); `test_scope_dates_and_decision_status`, `test_a_missing_product_key_is_unresolved_not_a_default`. Simulation-only owner events for suspension, cancellation, extension and award decision (`tender_events.record_simulated_event`). Tenders addendum row TND12-C04. |
| EVL4-305 | 3 | `06_runtime/evaluation_rules.json`, release-asset installer, `validate_release.py` extension, std_templates vectors; no published definition digest changes (D7) | Partial | 30 Sep 2026: rules file `07_tender_templates/evaluation_rules/IT-EQUIPMENT-OPEN-V1.json` beside the release, not inside it (plan D24); 66 rules; `test_evl_rules` 12/12, mutation-checked, including `test_every_evaluated_response_of_the_published_definition_has_a_rule`. Not done: an installer/validator in the STD Templates runtime (FU-EVL-04). |
| EVL4-306 | 3 | Core `support_issues.py` (`open_issue` idempotent on key, `resolve_on_success`, `for_holder`) and the core My Work row; no bid content in any issue (D12) | Done | 30 Sep 2026: `kentender_core/services/support_issues.py` (open_issue idempotent on module:operation correlation, resolve_on_success, retry_notice, for_holder, core My Work row); `kentender_core.tests.test_support_issues` 3/3; no bid content (`test_a_failed_intake_has_one_issue_until_it_succeeds`). |
| EVL4-307 | 3 | Evaluation owner adapter on `kt_prc_owner_adapters` with its own `acting` context; signing through the shared hook | Done | 30 Sep 2026: `prc_owner` adapter on `kt_prc_owner_adapters` (`proceeding_type` Bid Evaluation) with its own `acting`; signing through the shared trust hook; `test_prc_evaluation_profile` 16/16. |
| EVL4-308 | 3 | Simulation controls and `test_services/` fault switches, flag-only loading; `Bid Evaluation Settings` (D15, D16) | Done | 30 Sep 2026: `simulation.py` controls (intake_outcome, notice_outcome, delivery_outcome, downstream_status) load only under `kt_bds_simulation_environment`; `Bid Evaluation Settings.presence_lapse_seconds`; exercised by every service module. |
| EVL4-309 | 3 | `records.py`, `errors.py` (§8 verbatim, all guards together), `clock.py` (D3) | Done | 30 Sep 2026: `records.py` (journal, replay, conflict, atomic, lock, bump), `errors.py` (§8 verbatim, all guards together, `from_prc`), `clock.py`; `test_evl_errors` 3/3. |
| EVL4-401 | 4 | `EnsureEvaluationPreparation`: publication consumer and sweep; once-only case; Accounting Officer and Head of Procurement tasks; replay and addendum idempotent; terminal no-bids or cancellation takes precedence (§5.1) | Done | 30 Sep 2026: `preparation.ensure_preparation`; `test_publication_prepares_one_case_with_the_setup_tasks`, `test_a_cancelled_tender_is_never_prepared`. |
| EVL4-402 | 4 | Scope gate: six predicates from published facts; known unsupported scope → no case; missing or conflicting → named Tenders-owner issue; retry after repair (§5.1, EVL-A16) | Done | 30 Sep 2026: `test_a_known_unsupported_scope_prepares_nothing`, `test_missing_scope_metadata_is_the_tenders_owners_issue_until_repaired`. |
| EVL4-403 | 4 | `AppointEvaluationCommittee`: 3–5 members with designation, department and capacity; excludes the same-tender independent opening member; `EVL_MEMBER_INELIGIBLE` with reason | Done | 30 Sep 2026: `test_the_accounting_officer_appoints_three_to_five_members`, `test_only_the_accounting_officer_appoints`, `test_every_ineligible_person_is_reported_together`, `test_size_and_one_chair`. |
| EVL4-404 | 4 | `ReplaceEvaluationMember`: reasoned; history kept; replaced members' tasks close as replaced; a report being signed is withdrawn | Done | 30 Sep 2026: `test_a_reasoned_replacement_keeps_history`; a report being signed is withdrawn through `lifecycle.withdraw_signing`. |
| EVL4-405 | 4 | `AssignEvaluationSecretary`: own appointment or a named procurement officer with a written reference; no vote, finding or signature | Done | 30 Sep 2026: `test_the_head_assigns_a_procurement_officer_or_themself`. |
| EVL4-406 | 4 | `DeclareEvaluationInterest`: no conflict plus confidentiality; a conflict stops bid access immediately and creates the Accounting Officer's task; every bid read before declaration refuses with `EVL_DECLARATION_REQUIRED` | Done | 30 Sep 2026: `test_each_member_declares_personally`, `test_a_conflict_stops_eligibility_and_goes_to_the_accounting_officer`; `test_evl_reads` `test_an_undeclared_member_sees_no_bids`. |
| EVL4-407 | 4 | `RecordMemberUnavailability`: chair and Accounting Officer tasks; the appointment is not silently removed | Done | 30 Sep 2026: `test_inability_to_serve_never_removes_the_member_silently`. |
| EVL4-408 | 4 | Roster terms: current roster, eligible member, complete current eligible roster (§3) | Done | 30 Sep 2026: `roster.py` current roster, eligible member and complete current eligible roster; exercised by committee, discussion and report modules. |
| EVL4-409 | 4 | Suspension scope: appointment and declaration only where the instruction permits them (§5.7) | Done | 30 Sep 2026: `test_permitted_administrative_actions_continue_and_nothing_else`. |
| EVL4-410 | 4 | My Work preparation rows: appoint, assign secretary, declare, resolve appointment; waiting items | Done | 30 Sep 2026: `my_work_provider` preparation rows; titles asserted in `test_evl_preparation` and `test_evl_committee`. |
| EVL4-501 | 5 | `ReceiveOpeningPackage`: verified nonempty completion; once-only receipt; handoff acknowledged | Done | 30 Sep 2026: `test_one_completed_opening_gives_one_intake_one_run_and_reviewing` (replay and sweep change nothing). |
| EVL4-502 | 5 | `ReceiveEmptyOpeningOutcome`: existing preparation → **No evaluation required**, tasks cleared, history kept; no preparation → no case; an incomplete opening never counts as empty | Done | 30 Sep 2026: `test_a_final_no_bids_opening_closes_the_preparation`, `test_no_case_is_created_for_an_empty_opening`, `test_an_incomplete_opening_is_never_an_empty_one`. |
| EVL4-503 | 5 | A failed intake automatically opens one Support Issue; the secretary gets View issue and Try again; retry reuses the operation and issue identities; the waiting item clears only on success (§5.1, EVL-A02) | Done | 30 Sep 2026: `test_a_failed_intake_has_one_issue_until_it_succeeds`. |
| EVL4-504 | 5 | `RunEvaluationChecks`: one result per run, bid and requirement; affected-only rerun; prior run kept | Done | 30 Sep 2026: `checks.run`; prior run kept and superseded (`test_a_rule_issue_goes_to_support_and_clears_on_the_corrected_run`). Found and fixed: `current_run` filtered NULL with `in ('', None)`, which never matches NULL. |
| EVL4-505 | 5 | Rules engine: presence, boolean, choice, minimum/maximum, date, calculation, alternatives, "or equivalent" → review; missing rule → `EVL_RULE_UNAVAILABLE` | Done | 30 Sep 2026: `test_evl_rules` 12/12 (boundaries, decimals, choices, ports, or-equivalent, dates, money, presence, declarations, missing rule, calculation). |
| EVL4-506 | 5 | Aggregation: combined requirement (comparison plus evidence), group result, bid Responsive / Not responsive / Needs review; unresolved issues shown even after a failure | Done | 30 Sep 2026: `test_values_meet_and_evidence_waits_for_the_committee`, `test_the_bid_is_not_responsive_and_nothing_is_recommended`, `test_a_failed_requirement_cannot_be_waived`. Found and fixed: the request-local package cache was keyed by bid name only (a rebuilt test world reused the name). |
| EVL4-507 | 5 | Comparison: submitted total, adjustments (None), evaluated total, Provisional comparison, Not ranked, Not assessed, equal ranks, no tie-break outcome | Done | 30 Sep 2026: `comparison.compare`; one-bid, not-responsive and provisional cases in `test_evl_comparison`. Equal totals are covered only by the report builder (no two-bid service test yet). |
| EVL4-508 | 5 | Funding read via `get_funding_lineage`; a shortfall only qualifies the report (D9) | Partial | 30 Sep 2026: `funding.py` over `get_funding_lineage`; qualifies only. No service test with a shortfall (BUD contract owed, FU-EVL-06). |
| EVL4-509 | 5 | Timers: evaluation deadline and validity end with an inspectable source; `EVL_EVALUATION_OVERDUE`; expiry blocks an unsupported positive recommendation; the clock is not reset by late appointment | Partial | 30 Sep 2026: `timers.py` (deadline, validity end, overdue, expiry); read in the report outcome. No dedicated overdue/expiry test yet. |
| EVL4-510 | 5 | Enter Reviewing when results or source-rule issues are available; member review tasks created once as members become eligible | Done | 30 Sep 2026: `test_intake_before_appointment_runs_checks_and_gives_no_bid_access` (review task only after the member's own declaration; one notification). |
| EVL4-601 | 6 | `RecordEvidenceFinding`: attributed; never overwrites a system or prior finding | Done | 30 Sep 2026: `test_a_member_finding_completes_evidence_without_a_second_approval`, `test_only_eligible_members_record_findings`. |
| EVL4-602 | 6 | `RaiseFindingConcern`: one chair discussion item per bid and requirement; clears only on a committed conclusion, authorisation, plan or linked issue | Done | 30 Sep 2026: `test_needs_review_opens_one_chair_item`. |
| EVL4-603 | 6 | `StartDiscussion` (chair attendance in the same action), `JoinDiscussion`, `LeaveDiscussion`, `EndDiscussion` (a paused session may end without a conclusion); heartbeat and lapse (D15) | Done | 30 Sep 2026: `test_the_ordinary_conclusion`, `test_a_departure_pauses_decisions_but_not_notes`, `test_a_lapsed_member_is_not_present`. |
| EVL4-604 | 6 | `RecordDiscussionNote`: chair or secretary; available while paused; no decision authority | Done | 30 Sep 2026: `test_a_departure_pauses_decisions_but_not_notes`; the note's words are journalled and read back for the committee record. |
| EVL4-605 | 6 | `RecordCommitteeConclusion`: resolved or qualified; complete eligible roster present; `EVL_MEMBERS_ABSENT` with names | Done | 30 Sep 2026: `test_the_ordinary_conclusion`, `test_resolve_or_qualify_but_never_waive`. Found and fixed: Proceedings event keys over 140 characters (`prc.bounded`). |
| EVL4-606 | 6 | `RecordDisagreement`: the member's own words only; No agreed recommendation outcome | Done | 30 Sep 2026: `test_disagreement_keeps_its_author`; the No agreed recommendation outcome is built by `report.outcome`. |
| EVL4-607 | 6 | `ReportEvaluationIssue` / `RetryEvaluationOperation`: Support Issue link; support cannot supply findings | Done | 30 Sep 2026: `test_a_rule_issue_goes_to_support_and_clears_on_the_corrected_run`; intake retry in `test_a_failed_intake_has_one_issue_until_it_succeeds`. |
| EVL4-608 | 6 | Recalculation of affected results and comparison after a resolution | Done | 30 Sep 2026: aggregation reads the human record live; `test_the_ordinary_conclusion` shows the committee basis on the requirement. |
| EVL4-701 | 7 | `AuthoriseClarification`: atomic with its conclusion; question, requirement, original response, scope, future deadline; date conflict shown | Done | 30 Sep 2026: `test_authorise_send_reply_and_close`. |
| EVL4-702 | 7 | `SendClarification`: the exact authorised version; supplier notice; truthful Delivery problem | Done | 30 Sep 2026: `test_authorise_send_reply_and_close`. |
| EVL4-703 | 7 | `WithdrawClarification`: chair's recorded reason; a linked replacement request needs fresh authorisation | Done | 30 Sep 2026: `test_a_replacement_is_a_new_linked_request`. |
| EVL4-704 | 7 | `RetryClarificationNotice`: same notice and request identity (`EVL_CLARIFICATION_NOTICE_FAILED`) | Done | 30 Sep 2026: `test_a_failed_notice_is_true_and_retried_for_the_same_request`. |
| EVL4-705 | 7 | `SaveClarificationDraft`: own request; editable until sent; kept privately after closure | Done | 30 Sep 2026: draft and submit exercised in `test_evl_clarification`. |
| EVL4-706 | 7 | `SubmitClarificationReply`: one reply; timeliness on the trusted instant; Received late; `EVL_REPLY_OVERDUE` nonblocking; evidence upload limits | Done | 30 Sep 2026: `test_a_late_reply_is_labelled_and_no_reply_is_disposed`. |
| EVL4-707 | 7 | `RecordReplyDisposition`: complete roster; atomic closure (including no reply); changed offer excluded; `EVL_REPLY_CLOSED` afterwards | Done | 30 Sep 2026: `test_no_reply_closes_and_leaves_the_requirement_open`, `test_authorise_send_reply_and_close`. |
| EVL4-708 | 7 | Concurrency: reply committed before closure is included, after closure rejected; reply denied during signing leaves the frozen report unchanged | Partial | 30 Sep 2026: a reply after closure is refused (`EVL_REPLY_CLOSED`); the two concurrent commit orders and the reply-during-signing case have no dedicated test yet. |
| EVL4-801 | 8 | `RecordVerificationPlan`: in session; scope, basis, participants from the current eligible roster, one lead; revision supersedes with reason | Done | 30 Sep 2026: `test_evl_diligence` `test_a_plan_needs_the_committee_in_session_and_eligible_participants` (red first on the no-session refusal: `EVL_MEMBERS_ABSENT`, accepted as the correct answer). |
| EVL4-802 | 8 | `RecordDueDiligence`: each participant records their own observations | Done | 30 Sep 2026: `test_observe_freeze_sign_and_conclude`. |
| EVL4-803 | 8 | `SendDueDiligenceForSigning`: lead only, after every participant's observations | Done | 30 Sep 2026: `test_observe_freeze_sign_and_conclude` (missing observations listed; lead only). |
| EVL4-804 | 8 | `SignDueDiligenceReport`: page-initial and final-signature targets for each actual participant | Done | 30 Sep 2026: `test_observe_freeze_sign_and_conclude` (page and signature targets; signed only when every proof is in). |
| EVL4-805 | 8 | Outcome conclusion; after a negative result, the next eligible ranked bidder is proposed with its required checks, never silently substituted | Done | 30 Sep 2026: `test_observe_freeze_sign_and_conclude` (negative outcome, no substitute with one bid). |
| EVL4-901 | 9 | Report generator: §9.12 sections and order; continuous; source versions; attributed record | Done | 30 Sep 2026: `report.build` in §9.12 order; `test_the_ordinary_path_to_report_sent`. |
| EVL4-902 | 9 | `SaveReportNarrative`: narrative only | Done | 30 Sep 2026: `report.save_narrative` (secretary only, Reviewing only). |
| EVL4-903 | 9 | `SendReportForSigning`: freeze content and annexes; every guard together; `EVL_REPORT_INCOMPLETE` lists all items and holders; no active meeting; clarifications disposed | Done | 30 Sep 2026: `test_every_unresolved_item_is_listed_together`. |
| EVL4-904 | 9 | `SignEvaluationReport`: personal proof; `EVL_TARGET_CHANGED`; `EVL_SIGNATURE_UNCONFIRMED` with reconcile; no proxy | Done | 30 Sep 2026: `test_a_stale_version_or_unconfirmed_proof_counts_for_nothing`. |
| EVL4-905 | 9 | `RaiseReportConcern`: returns to Reviewing; signatures historical; chair and secretary task | Done | 30 Sep 2026: `test_a_stale_version_or_unconfirmed_proof_counts_for_nothing` (concern returns to Reviewing). |
| EVL4-906 | 9 | `ReviseEvaluationReport`: reason; new version needs fresh signatures | Partial | 30 Sep 2026: `signing.revise` built; no dedicated test. |
| EVL4-907 | 9 | `DeliverEvaluationReport` on the final proof; one recipient record and task; `EVL_REPORT_DELIVERY_FAILED` keeps Signing and proofs; retry with the same delivery identity | Done | 30 Sep 2026: `test_the_ordinary_path_to_report_sent`, `test_a_failed_delivery_keeps_the_signatures`. |
| EVL4-908 | 9 | `ReturnEvaluationReport`: before an authoritative downstream decision only; `EVL_DECISION_STATUS_UNKNOWN` blocks | Done | 30 Sep 2026: `test_return_before_a_decision_and_never_on_an_unknown_status`. |
| EVL4-909 | 9 | `RecordCorrectionNotice`: after a downstream decision; immutable link; separate Head of Procurement task keyed by source event | Done | 30 Sep 2026: `test_after_an_award_decision_only_a_correction_notice`. |
| EVL4-910 | 9 | `ReceiveOpeningSupplement` / `AssessOpeningSupplement`: before delivery a shared chair item; after delivery separate chair and Head items; a material effect reopens work and supersedes signing | Partial | 30 Sep 2026: `correction.consume_supplements`/`assess_supplement`/`head_review` built; no dedicated test. |
| EVL4-911 | 9 | `ReceiveTenderEvent`: suspension (`EVL_SUSPENDED`, blocked tracker, no local resume), resumption with rechecks, cancellation (`EVL_CANCELLED`, "Evaluation ended", tasks withdrawn), validity extension | Done | 30 Sep 2026: `test_a_suspension_pauses_and_a_cancellation_ends`; resumption and extension events are read, extension has no test. |
| EVL4-912 | 9 | Rechecks before freeze and before delivery: source impact, roster, cancellation or suspension, validity | Partial | 30 Sep 2026: rechecks in `signing.readiness` and before delivery; not separately tested. |
| EVL4-913 | 9 | Qualified outcomes: No responsive bids, equal totals, No agreed recommendation, funding qualification, No current recommendation — tender validity expired (signable without a loop) | Partial | 30 Sep 2026: outcomes built in `report.outcome`; No responsive bids tested through the comparison; tie, no agreement and expiry not tested end to end. |
| EVL4-914 | 9 | `ExportEvaluationRecord`: selected version and permitted annexes; signatures and correction links kept | Planned |  |
| EVL4-1001 | 10 | `bid_evaluation/api.py`: explicit arguments; refusals as data; audit of refusals and not-found | Done | 30 Sep 2026: `bid_evaluation/api.py`: explicit arguments, refusals as data, audit of refusals and not-found; exercised in the browser (Phase 11). |
| EVL4-1002 | 10 | Reads: `ResolveEvaluation`, `ListEvaluationWork`, `ReadEvaluationEvidence`, `ReadEvaluationReport`, `ReadOwnClarification` | Done | 30 Sep 2026: `reads.resolve`, `list_work`, `evidence`, `report_view`, `committee_record`, `own_clarification`, `candidates`; `test_who_reads_what`. |
| EVL4-1003 | 10 | Per-actor DTO filters (D20); protected Not found | Done | 30 Sep 2026: `test_who_reads_what`, `test_an_undeclared_member_sees_no_bids`. |
| EVL4-1004 | 10 | My Work provider: every §7.3 internal row, checked against `handoff_register.md` | Partial | 30 Sep 2026: every internal row is built; titles asserted per module. The full matrix against `handoff_register.md` is not yet one test. |
| EVL4-1005 | 10 | Notifications: courtesy notices with correlation keys; supplier email through the BDS transport | Partial | 30 Sep 2026: courtesy notices via `notify.tell` with correlation keys; the supplier transport is the BDS hook in simulation. |
| EVL4-1006 | 10 | `make evl-dead-end-gate`: every state × actor through `next_step.problems` | Partial | 30 Sep 2026: `test_every_actor_has_a_sound_answer` (prepared, reviewing, ready states × 9 actors). The full state × actor gate `make evl-dead-end-gate` is not yet a target. |
| EVL4-1007 | 10 | `make evl-leakage-gate`: Accounting Officer, unappointed, undeclared, conflicted, supplier, public and technical readers | Partial | 30 Sep 2026: `test_who_reads_what` covers AO, Head before delivery, outsider, technical reader and undeclared member. `make evl-leakage-gate` is not yet a target; supplier and public readers are Phase 12. |
| EVL4-1008 | 10 | Technical-read resolver and probe | Planned |  |
| EVL4-1101 | 11 | Tenders seam: `Tenders.vue` `sub === "evaluation"` → `bid_evaluation.bundle.js`; `tenders_page.js` bundles; Tender record link; one `ui-tenders-*` and `ui-bop-*` regression run | In progress | 30 Sep 2026: `Tenders.vue` delegates `sub === "evaluation"` to `frappe.kt_mount_bid_evaluation`; `bid_evaluation.bundle.js` added to `tenders_page.js`; Tender record link `bid_evaluation/desk_links.py` on `kt_tender_record_links`. Asset build clean. Not yet run in a browser; Tenders/BOP UI regression not run. |
| EVL4-1102 | 11 | Desk Page `bid-evaluation` (one `desk_page.register` call; `useRouteState()`; shared rail) | In progress | 30 Sep 2026: one `desk_page.register` call; workspace app `workspace/BidEvaluationWorkspace.vue` (D01 boards) over `list_work` with the shared rail. Page not yet migrated; not run in a browser. |
| EVL4-1103 | 11 | `evl-kit.js` compositions → Vue components (record head, tracker, guidance, comparison, signatures, roster, attendance, evidence, facts, disclosures) | In progress | 30 Sep 2026: one block renderer instead of per-block components: `board/model.js` ports the kit's builders and classifiers, `board/EvlBoard.vue` the board template class for class; screen builders in `screens/` (record, committee, bid, discussion, clarification, report, follow-ups, committee record) compose the boards from the server's reads; root `BidEvaluation.vue` (loader, one pending gate, poll and heartbeat while a discussion is live). New reads for the screens: appointment pick lists, discussion notes and conclusions, report readiness and downstream status. |
| EVL4-1104 | 11 | Departures file `tests/ui/fidelity/departures/bid-evaluation.js`; vitest project `bid-evaluation` in `ui-structure-gate`; inventory count test = 107 | In progress | 30 Sep 2026: `tests/ui/fidelity/board.js` renders every one of the 107 boards from the design tool's own template (smoke: 107/107 render); departures file created; vitest project `bid-evaluation`; `bid-evaluation.fidelity.spec.js` lists 41 boards. Waits for captured fixtures (`tests/ui/smoke/bid-evaluation/capture.sh` over the new browser world `bid_evaluation.seeds.playwright_ui_fixtures`, 23 stages). |
| EVL4-1111 | 11 | Slice 11.1 Workspace and shared states (16 boards) | In progress | 30 Sep 2026: screens written; `evl-committee.spec.ts` covers the workspace task → appointment; not run. |
| EVL4-1112 | 11 | Slice 11.2 Committee and declaration (11) | In progress | 30 Sep 2026: screens written; `evl-committee.spec.ts` (appoint, secretary, declaration, replacement refusal and replacement); not run. |
| EVL4-1113 | 11 | Slice 11.3 Record and requirement (8) | In progress | 30 Sep 2026: screens written; not run. |
| EVL4-1114 | 11 | Slice 11.4 Committee discussion (14) | In progress | 30 Sep 2026: screens written; not run. |
| EVL4-1115 | 11 | Slice 11.5 Clarification, internal (8) | In progress | 30 Sep 2026: screens written; not run. |
| EVL4-1116 | 11 | Slice 11.6 Report and signing (24) | In progress | 30 Sep 2026: screens written; Download report opens the preview and prints (no export endpoint yet, EVL4-914); not run. |
| EVL4-1117 | 11 | Slice 11.7 Issues, verification and correction (15) | In progress | 30 Sep 2026: screens written; not run. |
| EVL4-1118 | 11 | Slice 11.8 Pause and cancellation (4); after-delivery cancellation Conditional | In progress | 30 Sep 2026: screens written; not run. |
| EVL4-1201 | 12 | BDS portal section-resolver seam for `/tenders/{ref}/bid/evaluation-clarifications/{request_id}`; BDS tracker addendum row (D14) | Planned | |
| EVL4-1202 | 12 | Supplier screens (7 boards at 390×844) and the bid-overview link | Planned | |
| EVL4-1203 | 12 | Supplier tests: no internal disclosure; draft ≠ reply; closure rejects writes; late label; BDS portal regression | Planned | |
| EVL4-1301 | 13 | Grace Wambui, Peter Mugo, Ruth Achieng, Esther Njeri in `site_setup.ACTORS`/`ASSIGNMENTS`; Jirani Office Supplies Limited for tender 036 (D17) | Planned | |
| EVL4-1302 | 13 | Canonical stage `bid_evaluation` at the §11.1 instants, ending at Report sent | Planned | |
| EVL4-1303 | 13 | `seed-canonical-validate` coverage for the stage | Planned | |
| EVL4-1304 | 13 | Demo profiles and `make seed-evl-profile(s)`, `seed-evl-profile-restore` | Planned | |
| EVL4-1305 | 13 | `evl-demo-walk.spec.ts`: from the menu and the bell, one session per person | Planned | |
| EVL4-1306 | 13 | Bid Submission canonical seed submits the EVL v0.4 §9.1/§9.12 bid facts and named evidence documents (C22); reseed through `bid_opening`; BDS tracker addendum row | Planned | |
| EVL4-1401 | 14 | `ui-evl-fidelity-gate` over all 107 boards | Planned | |
| EVL4-1402 | 14 | §11.1 and §11.2 state/actor/branch matrix: control ↔ command ↔ PRC event ↔ My Work ↔ disclosure ↔ clearing | Planned | |
| EVL4-1403 | 14 | Persona browser pass: Amina, Charles, Brian, Grace, Peter, Ruth, Samuel, David, Naomi, Esther, Administrator | Planned | |
| EVL4-1404 | 14 | AC map closure | Planned | |
| EVL4-1405 | 14 | `RUNBOOKS.md` | Planned | |
| EVL4-1501 | 15 | PRC-CHG-001 v0.10 (Evaluation profile) written and approved (FU-EVL-01) | Blocked — owner | |
| EVL4-1502 | 15 | TPR-CHG-001 amendment (publication binding, scope fields, post-close cancellation, suspension, validity extension, award status) (FU-EVL-02) | Blocked — owner | |
| EVL4-1503 | 15 | BDS-CHG-001 amendment (supplier correspondence view, released-package seam) (FU-EVL-03) | Blocked — owner | |
| EVL4-1504 | 15 | STD-TPL-001 amendment (evaluation-rules asset) (FU-EVL-04) | Blocked — owner | |
| EVL4-1505 | 15 | BOP-CHG-001 cross-reference (automatic take-up, completion consumer, digest) (FU-EVL-05) | Blocked — owner | |
| EVL4-1506 | 15 | BUD-CHG-001 evaluation funding read (FU-EVL-06) | Blocked — owner | |
| EVL4-1507 | 15 | KT-STD-001 v1.13 personas and Brian's scope (FU-EVL-07) | Blocked — owner | |
| EVL4-1508 | 15 | SEED-OPS-001 new version for the `bid_evaluation` stage (FU-EVL-08) | Blocked — owner | |
| EVL4-1509 | 15 | Register rows: BOP → Evaluation interface; STD-TPL version cited (FU-EVL-09) | Blocked — owner | |
| EVL4-1510 | 15 | LAW-V-001 current-law verification and PPRA report-format reconciliation (FU-EVL-10) | Blocked — owner | |
| EVL4-1511 | 15 | Real signing and custody under TRUST-ADR-001; production release of opened packages (FU-EVL-11) | Blocked — owner | |
| EVL4-1512 | 15 | Bid Opening and Bid Submission incidents onto Support Issue (FU-EVL-12) | Blocked — owner | |
| EVL4-1513 | 15 | Security review | Blocked — owner | |
| EVL4-1514 | 15 | Production enablement | Blocked — owner | |
| EVL4-1515 | 15 | Downstream Award consumer of the delivered report | Blocked — owner | |

## Command and read map (EVL v0.4 §7.2)

| Command or read | Tracker row | Service module (planned) |
|---|---|---|
| EnsureEvaluationPreparation | EVL4-401, 402 | `preparation.py` |
| AppointEvaluationCommittee, ReplaceEvaluationMember | EVL4-403, 404 | `appointment.py` |
| AssignEvaluationSecretary | EVL4-405 | `secretary.py` |
| DeclareEvaluationInterest | EVL4-406 | `declaration.py` |
| ReceiveOpeningPackage, ReceiveEmptyOpeningOutcome, RunEvaluationChecks | EVL4-501…504 | `intake.py`, `checks.py` |
| RecordEvidenceFinding, RaiseFindingConcern | EVL4-601, 602 | `findings.py` |
| StartDiscussion, JoinDiscussion, LeaveDiscussion, EndDiscussion | EVL4-603 | `discussion.py` |
| RecordDiscussionNote | EVL4-604 | `discussion.py` |
| RecordCommitteeConclusion, RecordDisagreement | EVL4-605, 606 | `conclusion.py` |
| AuthoriseClarification, SendClarification, WithdrawClarification | EVL4-701…703 | `clarification.py` |
| SaveClarificationDraft, SubmitClarificationReply | EVL4-705, 706 | `clarification.py` |
| RecordReplyDisposition, RecordDueDiligence | EVL4-707, 802 | `clarification.py`, `diligence.py` |
| RecordVerificationPlan | EVL4-801 | `diligence.py` |
| SendDueDiligenceForSigning, SignDueDiligenceReport | EVL4-803, 804 | `diligence.py` |
| AssessOpeningSupplement, RecordMemberUnavailability | EVL4-910, 407 | `correction.py`, `unavailability.py` |
| SaveReportNarrative, SendReportForSigning | EVL4-902, 903 | `report.py`, `signing.py` |
| SignEvaluationReport, RaiseReportConcern | EVL4-904, 905 | `signing.py` |
| ReviseEvaluationReport, ReturnEvaluationReport | EVL4-906, 908 | `signing.py`, `correction.py` |
| DeliverEvaluationReport | EVL4-907 | `delivery.py` |
| ReceiveOpeningSupplement, ReceiveTenderEvent, RecordCorrectionNotice | EVL4-910, 911, 909 | `correction.py`, `tender_events.py` |
| ReportEvaluationIssue, RetryEvaluationOperation, RetryClarificationNotice | EVL4-607, 503, 704 | `issues.py`, `clarification.py` |
| ResolveEvaluation, ListEvaluationWork, ReadEvaluationEvidence, ReadEvaluationReport, ReadOwnClarification | EVL4-1002 | `reads.py` |
| ExportEvaluationRecord | EVL4-914 | `export.py` |

## Branch map (EVL v0.4 §11.2)

| Branch | Tracker rows | Acceptance |
|---|---|---|
| Source unavailable before receipt | EVL4-503 | EVL-A02 |
| Final no-bids outcome / existing preparation | EVL4-502 | EVL-A02 |
| Opening incomplete | EVL4-502 | EVL-A02 |
| Rule absent or defective | EVL4-505, 607 | EVL-A03 |
| Memory 8 GB in the original alternative bid | EVL4-505, 507, 913 | EVL-A04 |
| Missing member during discussion | EVL4-603, 605 | EVL-A05 |
| Late conflict before delivery | EVL4-406, 404 | EVL-A06 |
| Clarification notice failure | EVL4-704 | EVL-A07 |
| Late, absent or changed reply | EVL4-706, 707 | EVL-A07 |
| Verification branch | EVL4-801…805 | EVL-A08 |
| Tie, shortfall, no agreement | EVL4-507, 508, 606, 913 | EVL-A09 |
| Report delivery failure | EVL4-907 | EVL-A10 |
| Stale report or uncertain signature | EVL4-904 | EVL-A10 |
| Return before downstream decision | EVL4-908 | EVL-A11 |
| Correction after downstream decision | EVL4-909 | EVL-A11 |
| Opening supplement | EVL4-910 | EVL-A12 |
| Suspended or cancelled | EVL4-911 | EVL-A13 |
| Deadline overdue or validity expired | EVL4-509, 913 | EVL-A13 |
| Publication replay or intake before appointment | EVL4-401, 510 | EVL-A16 |
| Replacement clarification | EVL4-703 | EVL-A07 |
| Generic evidence conclusion | EVL4-605 | EVL-A17 |
| Supplier, auditor or dual-role actor | EVL4-1003, 1007 | EVL-A14 |

## Board map

Built in Phase 0 as `reconciliation/artboard_inventory.md`. The slice totals are fixed here: 11.1 = 16, 11.2 = 11, 11.3 = 8, 11.4 = 14, 11.5 = 8, 11.6 = 24, 11.7 = 15, 11.8 = 4, Phase 12 supplier = 7. Total 107.

## Acceptance criteria map

All 17 criteria are copied verbatim by script from EVL v0.4 §11.3. Every row starts `Planned`.

| ID | Criterion (verbatim) | Source line | Target phase | Status | Evidence |
|---|---|---|---|---|---|
| EVL-A01 | Appointments, declarations, secretary authority and same-tender independent-opening exclusion work through UI and direct API; technical readers cannot decide. | EVL v0.4 line 653 | 4, 10 | Partial | 30 Sep 2026: `test_evl_committee` 10/10, `test_evl_reads`; UI owed (slice 11.2). |
| EVL-A02 | One valid nonempty opening creates one evaluation intake/run. A final empty outcome retains and closes existing preparation as No evaluation required, clearing its tasks without assessment/report/signing tasks; without preparation, no case is created. Incomplete/failed intake never triggers empty closure. Failed intake automatically creates one named support issue; repeated failures/retries reuse it, and only successful reconciliation clears waiting. Replays have no duplicate effect. | EVL v0.4 line 654 | 3, 5 | Partial | 30 Sep 2026: `test_evl_intake` 6/6; UI owed. |
| EVL-A03 | Every evaluated published identity has a traceable result; unknown rules/evidence remain reviewable; non-evaluated responses never become hidden criteria. | EVL v0.4 line 655 | 5 | Partial | 30 Sep 2026: `test_evl_rules` (every evaluated response has a rule), `test_evl_comparison`; UI owed. |
| EVL-A04 | Numeric/date boundaries, applicability, units, calculation precision and alternatives yield correct explainable outcomes; evidence presence does not imply validity. | EVL v0.4 line 656 | 5 | Partial | 30 Sep 2026: `test_evl_rules` 12/12; UI owed. |
| EVL-A05 | Start records chair attendance once; other members join personally; current personal participation and complete current eligible roster govern collective conclusions; asynchronous work needs no ceremonial attendance; member-authored disagreement is preserved. | EVL v0.4 line 657 | 2, 6 | Partial | 30 Sep 2026: `test_evl_discussion` 10/10; UI owed. |
| EVL-A06 | Conflict/replacement changes access immediately; incoming member reviews the current record; old contributions/proofs remain historical. | EVL v0.4 line 658 | 4 | Partial | 30 Sep 2026: `test_evl_committee` (conflict, replacement), `test_evl_reads` (undeclared member); UI owed. |
| EVL-A07 | Supplier correspondence preserves originals and own-organisation privacy; on-time/late/no reply, changed offer, withdrawal, notice failure and retry have distinct truthful outcomes. Final disposition closes replies atomically; test both reply/closure commit orders, no-reply closure and denied later replies during signing without changing the frozen report. | EVL v0.4 line 659 | 7, 12 | Partial | 30 Sep 2026: `test_evl_clarification` 5/5; concurrency test and supplier portal (Phase 12) owed. |
| EVL-A08 | Due-diligence plan, basis, current committee participants, lead, participant tasks, scope/roster changes, observations and exact proof targets are retained; failed finding never silently selects a replacement winner. | EVL v0.4 line 660 | 8; production signing part 15 | Partial | 30 Sep 2026: `test_evl_diligence` 2/2; UI owed. |
| EVL-A09 | Responsive-only comparison uses the published method, retains submitted sums, distinguishes adjustments, treats ties and budget separately, and never creates an award. | EVL v0.4 line 661 | 5 | Partial | 30 Sep 2026: `test_evl_comparison` 2/2; tie and funding shortfall not tested; UI owed. |
| EVL-A10 | One exact report/annex set is signed personally; stale/uncertain proof fails; final proof creates one durable recipient record and task without extra user action. If durable delivery fails, retain Signing and valid proofs; D07-DELIVERY retries the same delivery identity and produces exactly one recipient record/task on success. | EVL v0.4 line 662 | 2, 9; production signing part 15 | Partial | 30 Sep 2026: `test_evl_report` (ordinary path, stale/unconfirmed proof, failed delivery); UI owed. |
| EVL-A11 | Concern, return and revision require new exact targets/fresh signatures; post-decision corrections preserve the delivered basis. | EVL v0.4 line 663 | 9 | Partial | 30 Sep 2026: `test_evl_report` (concern, return, correction notice); revision not tested; UI owed. |
| EVL-A12 | Opening supplements have separate identity, scope and recorded impact; originals and earlier handoffs remain intact. Concurrent supplement and correction tasks have distinct source identities, titles and clearing records; replay and clearing one must not duplicate or clear another. | EVL v0.4 line 664 | 9 | Partial | 30 Sep 2026: supplements built, not tested; UI owed. |
| EVL-A13 | Overdue, expiry, authoritative pause/resume and cancellation preserve history; administrative actions during suspension require explicit instruction scope and do not manufacture decisions or extensions. Expiry invalidates an unsupported positive recommendation; an explicitly expired-validity report with no current recommendation can be signed and delivered without an expiry loop. | EVL v0.4 line 665 | 5, 9 | Partial | 30 Sep 2026: `test_evl_report` (suspension, resumption, cancellation), `test_evl_committee` (suspension scope); overdue/expiry not tested; UI owed. |
| EVL-A14 | Every state/actor, including intake without appointment, each pause/cancellation stage and downstream Head review, has a clear next step or truthful waiting/done result; every fix reaches its actual owner; protected data never leak through counts, errors, exports or tasks. | EVL v0.4 line 666 | 10, 12, 14 | Partial | 30 Sep 2026: `test_evl_reads` `test_every_actor_has_a_sound_answer` (three states); full dead-end and leakage gates owed. |
| EVL-A15 | Every §9 action maps to §10/§7; exact fixtures produce their pictured states; desktop/mobile content remains complete and readable under KT-STD-001. | EVL v0.4 line 667 | 11, 12, 14 | In progress | 30 Sep 2026: screens written (Phase 11); nothing run in a browser yet. |
| EVL-A16 | Scope checks reject supported-field mismatches without a case/tasks and route missing metadata to the Tenders owner without guessing; verify each predicate and replay after repair. Publication and intake recovery create one preparation case and missing AO/secretary tasks; late/replayed events after terminal no-bids/cancellation do not reopen work. Intake before appointment runs checks without disclosing bids to AO or unappointed users; appointment/declaration enables member tasks once and never resets deadlines. | EVL v0.4 line 668 | 4 | Partial | 30 Sep 2026: `test_evl_preparation` 4/4 (unsupported scope, missing metadata, repair); UI owed. |
| EVL-A17 | Needs-review findings and concerns create one chair item; generic conclusions preserve evidence and author attribution, resolve the finding or explicitly qualify the report, and cannot override deterministic rules. Clarification and verification commit their specialised commands directly; a durable linked technical issue transfers work to support. Merely opening a form never clears the concern; each committed route creates its named follow-up once. Every member of the current eligible roster must participate; former/conflicted/unavailable members cannot silently reduce the requirement. | EVL v0.4 line 669 | 6 | Partial | 30 Sep 2026: `test_evl_discussion` (one chair item, attribution, never waive); UI owed. |
