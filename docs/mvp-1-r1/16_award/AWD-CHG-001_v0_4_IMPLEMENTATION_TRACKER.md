# AWD-CHG-001 v0.4: Award, tracker

| Control | Value |
|---|---|
| Version | 0.4-tracker.2 |
| Date | 30 September 2026 |
| Status | Phases 0–12 Done (1 Oct 2026); Phase 13 owner-gated. Nothing committed (the owner did not ask for commits). AC map: 27 Done, 3 Partial (AC-010, 021, 026), 1 Blocked — owner (AC-027). (0.4-tracker.1 read: Planned.) Owner instruction 30 Sep 2026: "Build all phases nonstop as I will be unable to prompt you again. Record follow-ups if necessary." |

**Authority:** `KenTender_AWD-CHG-001_Award_v0_4.md`, *Proposed — Project Owner review* (built under OD-A). Governing standard: KT-STD-001 v1.12.

**Plan:** `AWD-CHG-001_v0_4_Implementation_Plan.md`. It holds owner decisions OD-A and OD-B, technical decisions D1–D16 and conflicts C1–C14.

**Companions:** `AWD-CHG-001_v0_4_FOLLOW_UPS.md`; Phase 0 `reconciliation/`; later `evidence/v0_4/` and `RUNBOOKS.md`.

**Design:** `design/Award Artboards.dc.html` — 47 boards (9 main, 27 variants, 11 dialogs).

**Started:** 30 September 2026.

## Tracker rules

1. **Rows are permanent.** Status vocabulary: `Planned` / `In progress` / `Blocked` / `Blocked — owner` / `Partial` / `Done`. Reversed decisions are struck through in place, never deleted.
2. **`Done` needs the row's own evidence:** a command with result counts, a named test, a commit, or a described browser observation with literal rendered strings. Never record a result that was not observed. An honestly incomplete row is `Partial`. A result proven only through a stand-in says so ("synthetic" or "simulation") and never closes a production part.
3. **Prohibited in new code** (AWD v0.4 §2, §5, §16):
   - a supplier picker, price or amount editor, ranking edit, supplier substitution, negotiation or revised-offer control;
   - a second notice approval, **Release notices**, a manual send-to-Contracting approval, an acknowledgement of the incoming report, an approval to start Award, a generic **Override**, a free-text issue outcome;
   - a contract, contract signature, performance-security demand, security forfeiture or automatic runner-up selection;
   - treating a queued email, send acceptance, portal creation or read receipt as proof of giving; showing **All bidders have been notified** before every required giving evidence;
   - inferring "no decision" or "no notification" from the absence of a case or a failed lookup;
   - clearing a hold by elapsed time; a hard-coded 14-day or other legal period; a browser clock authorising progress;
   - editing sent correspondence, signed opinions, decisions, notices or report bytes;
   - reading another module's doctypes from `award` code instead of `services/sources.py` and the published seams (D4, D5);
   - another bidder's facts reaching a supplier; bids, prices, opinions or decisions reaching a technical reader; the internal record reachable by a public URL;
   - `kentender_core.cl_surface_registry.js`, Civic Ledger or Stitch Desk classes (Industry only);
   - TRUST test labels drawn into ported board markup; stand-ins loading without `kt_bds_simulation_environment`.
4. **Governing sections:** AWD v0.4 §10 and the boards govern visual and content fidelity (ported class-for-class); §4, §5 and §7 govern behaviour; §5.9 governs stages, markers, next steps and work items; §8 governs error copy, verbatim; §10/§11 map each control to exactly one command or read. Board literals (033/036/037, instants) are fixture data; the runtime shows actual events.
5. **Mapping:** every visible action maps to exactly one §7 command or read (AC-023); every cross-module effect maps to one seam in D5.
6. **Site safety:** never run an `award` Python module while a Playwright process is active (`awd-preflight`); Award tests write only namespaced Award rows and clean them up; the integration module uses years ≥ 2100; browser-pass records count as test data.
7. **Production gate:** no production signing, notice channel, legal profile or Contracting receipt is claimed. Phase 13 rows stay `Blocked — owner`.
8. **Acceptance closure:** an AC row is `Done` only when every part it names is proven. Production-only parts are split into a Phase 13 row.
9. **Owner-document seams (OD-A):** every change to another owner's code records an addendum row in that owner's tracker in the same step, and keeps its follow-up open.
10. **No upstream world in Award tests (OD-B).** `AwardCase` uses the synthetic sources, built once per module; per test only Award rows are wiped.
11. **The real Evaluation → Award seam is proven only** by `test_awd_seams.py`, `test_awd_integration.py`, the canonical `award` stage and the demo walk.
12. **Upstream reruns are targeted.** Before rerunning another module's tests, name the changed file that justifies it, and run only that one test module. Full cross-module regression happens once, at Phase 12.
13. **Vertical slices from Phase 3:** service → API → screen → one Playwright spec with one fixture entity → a live click-through from the menu. The slice's tracker row is closed only after the live check.
14. **Gates are wired when created** (Make targets, vitest project in `ui-structure-gate`); none is left "owed".
15. **Rare branch boards** are compared where cheap; otherwise recorded in `departures/award.js` as not compared, with a reason.
16. **Update this tracker per proven piece**, with evidence, in the same step.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 30 Sep 2026 | OD-A: build now, amend later. Owner answer, verbatim: "Build now, amend later (Recommended)". | AWD v0.4 is Proposed; counterpart amendments are Phase 13 follow-ups (FU-AWD-01…08). |
| 30 Sep 2026 | OD-B: stand-in upstream, real seam proven separately. Owner answer, verbatim: "Stand-in upstream, real seam proven separately (Recommended)". | Evaluation's per-test world building and upstream reruns cost most of a day. |
| 30 Sep 2026 | Build all phases without further prompts. Owner, verbatim: "Build all phases nonstop as I will be unable to prompt you again. Record follow-ups if necessary." | Decisions that would normally be asked are taken under the plan's technical authority and logged here and in the follow-ups. |

## Work items

### Phase 0 — Reconcile

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-001 | `reconciliation/artboard_inventory.md` (47 boards by script) | Done | `reconciliation/artboard_inventory.md`, extracted by script: 47 rows (9 main, 27 variants, 11 dialogs), each in one slice, 0 unassigned |
| AWD4-002 | `reconciliation/error_contract.md` (13 codes verbatim) | Done | `reconciliation/error_contract.md`, copied by script (13 codes); `test_awd_errors` checks `errors.MESSAGES` against it (3/3) |
| AWD4-003 | `reconciliation/next_step_register.md` (§5.9 rows → holder, task, clearing event, test) | Done | `reconciliation/next_step_register.md`: 29 §5.9 rows + the correction-cycle table, each with holder, task, clearing event and test |
| AWD4-004 | `reconciliation/command_map.md` (§10/§11 controls → §7) | Done | `reconciliation/command_map.md`: every §10/§11 control → one §7 command or read and its endpoint |
| AWD4-005 | `reconciliation/fixture_chronology.md` (ordinary path + §13 branches) | Done | `reconciliation/fixture_chronology.md`: ordinary path + the §13 branches, each with its synthetic stage |
| AWD4-006 | `reconciliation/seam_register.md` (AWD-IF-01…07) | Done | `reconciliation/seam_register.md`: AWD-IF-01…07 → built function or gap + follow-up |
| AWD4-007 | Canonical Report sent facts on TND-MOH-2027-002 checked against §10.1 | Done | Checked by `test_awd_seams` against the canonical report of TND-MOH-2027-002: Afya Digital Supplies Limited, KES 46,400,000 submitted and evaluated, 250 Each, 36 months, 3 of 3 signatures, valid until 10 Oct 2027 11:00, delivered 16 Jun 2027 14:07 — all §10.1 facts present in the real source (no placeholder gap, unlike EVL C22) |
| AWD4-008 | `awardKit` extractor, `departures/award.js`, vitest project `award` in `ui-structure-gate` | Done | `tests/ui/fidelity/board.js` `awardKit`/`awardSkeleton`/`awardDialogSkeleton`; `departures/award.js`; vitest project `award` in `vitest.config.ts` and in `make ui-structure-gate` (bid-evaluation added there too, closing EVL4-1104's wiring gap) |
| AWD-G00 | Gate: 47 rows, one slice each; controls mapped; provenance gate green | Done | 47 inventory rows, each in one slice; every §10/§11 control mapped; the fidelity project runs (48/48 now) |

### Phase 1 — Scaffolding

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-101 | `award` module, `modules.txt`, new-module procedure; `evaluation_award/` removed | Done | `award` module in `modules.txt`; migrate → clear-cache → migrate: Module Def app `kentender_procurement`, 17 doctypes, Page `award`; empty `evaluation_award/` skeleton removed |
| AWD4-102 | D2 doctypes with flags guard and deny permissions | Done | 17 doctypes generated with the flags guard, System Manager read-only; `test_awd_schema` 5/5 (facts, vocabularies, no Desk write, Desk save refused) |
| AWD4-103 | `records.py`, `errors.py`, `clock.py` | Done | `services/records.py`, `errors.py`, `clock.py`, `people.py`; `test_awd_errors` 3/3 |
| AWD4-104 | Page `award` shell, sidebar link, planned-label update, Page.module collision check | Done | Page `award` + `award_page.js` (one `desk_page.register`); sidebar Awards → `award` (planned label removed); route key `award` mapped to the Procurement rail; `test_procurement_sidebar_g0_012_contract` 6/6 (its stale "Evaluation is planned" expectation corrected). Browser: /app/award/AWD-MOH-2027-033 shows the Procurement rail with Awards active |
| AWD4-105 | Makefile targets (`awd-*`, `ui-awd-*`, `seed-awd-*`) | Done | Makefile `awd-preflight`, `awd-services-gate`, `awd-seams-gate`, `awd-leakage-gate`, `awd-dead-end-gate`, `ui-awd-*`, `seed-awd-profile*`, all in `.PHONY` |
| AWD4-106 | `test_awd_schema.py`, `test_awd_errors.py` | Done | `test_awd_schema` 5/5, `test_awd_errors` 3/3 |
| AWD-G01 | Gate: schema/errors green; migrate twice; `/app/award` shell from the sidebar | Done | schema/errors green; migrate twice clean; `/app/award` reached from the sidebar in `awd-opinion.spec.ts` |

### Phase 2 — Sources, seams, test base

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-201 | `services/sources.py` interface + real provider | Done | `services/sources.py` (`EvaluationSource` over the three seams); hook `kt_award_source_providers` |
| AWD4-202 | Synthetic provider `test_services/sources.py` (033, 036, 037 fixtures) | Done | `test_services/sources.py` (033, 036 tie, 037 two-bid; live facts kept in the simulation controls' synthetic state); answers only under `kt_bds_simulation_environment` |
| AWD4-203 | `tests/support.py` `AwardCase` (shared synthetic world, namespaced wipe) | Done | `tests/support.py` `AwardCase`: a synthetic delivery per test, namespace `AWD_TEST` wiped per test; `make awd-services-gate` 93 tests / 16 modules in 59 s wall (EVL: 8½ min) |
| AWD4-204 | `bid_evaluation/services/award_seam.py` + `kt_evaluation_report_consumers` hook call; EVL tracker addendum | Done | `bid_evaluation/services/award_seam.py` + the three hooks + `return_for_authorised_correction` + review-state "With Award". Real delivery → Award: `test_awd_integration` 2/2 (35 s); `test_awd_seams` 3/3 (the seam first failed on its own digest rule — Evaluation hashes the frozen JSON text — and on a missing `responsiveness` field; both fixed in the seam). EVL tracker addendum EVL4-1516 |
| AWD4-205 | `tenders/services/award_seam.py`, `kt_tender_cancellation_guards`, `award_decision_status` delegation; TPR tracker addendum | Done | `tenders/services/award_seam.py`; `cancel_tender` asks `kt_tender_cancellation_guards`; `award_decision_status` delegates. `test_awd_authority` 4/4, `test_awd_seams` 3/3; upstream `tenders.tests.test_open_period` 9/9, `bid_evaluation.tests.test_evl_seams` 6/6. TPR tracker addendum TND12-C05 |
| AWD4-206 | `bid_submission/services/award_gateway.py`; BDS tracker addendum | Done | `bid_submission/services/award_gateway.py`; `test_awd_seams::test_the_bidder_audience_and_authority` on the canonical Tender (Afya Submitted, contact tenders@afyadigital.example; Mary signatory, David representative). BDS tracker addendum BDS8-B08 |
| AWD4-207 | `test_awd_seams.py` (read-only against canonical) | Done | `test_awd_seams.py` 3/3, read-only against the canonical report |
| AWD4-208 | `test_awd_integration.py` (one real EVL world) | Done | `test_awd_integration.py` 2/2 on one real Evaluation world (Evaluation's shared test world): one case, one HOP task, EVL row taken up, retry no duplicate, Award's Return report goes back through Evaluation |
| AWD4-209 | Targeted upstream reruns (named modules only) | Done | Justified by the changed files, once each: `bid_evaluation.tests.test_evl_report` 8/8 (its HOP-row assertions now expect Award's task — §3), `test_evl_seams` 6/6, `tenders.tests.test_open_period` 9/9; browser `evl-demo-walk` 3/3 and `evl-ordinary-path` 1/1 (1.6 min) after updating their HOP expectations (FU-AWD-21). BOP and BDS suites not re-run: no file they depend on changed |
| AWD-G02 | Gate: `awd-seams-gate` + named upstream modules green | Done | `make awd-seams-gate` green (5 tests); named upstream modules green |

### Phase 3 — Receive and opinion

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-301 | `ReceiveEvaluationReport` + source checks + automatic issues | Done | `services/intake.py` + `checks.py`; `test_awd_intake` 6/6 (one case/cycle/task; retry no duplicate; missing annex / signature → exact source issue owned by HOP; expired validity; unreadable status is Unknown and clears on recovery) |
| AWD4-302 | `SaveProfessionalOpinion`, `SignProfessionalOpinion` (D6) | Done | `services/opinion.py` via `proceedings.services.signing.attest`; `test_awd_opinion` 9/9 (sign → Decide award; AO refused AWD_AUTHORITY_REQUIRED; stale revision; conclusion + reason required; signing unavailable keeps the draft and the same attempt, opens then resolves a Support Issue; incomplete source blocks signing; expired report signs; tie cannot recommend) |
| AWD4-303 | `ReturnEvaluationReport` via seam | Done | `opinion.return_report` → EVL `ReturnEvaluationReport`; `TestReturn` (cycle waits, prior versions kept, successor report attaches to the same cycle, an out-of-date draft must be re-saved) |
| AWD4-304 | `next_steps.py`, `my_work_provider.py` (opinion rows) | Done | `services/next_steps.py` (§5.9 wording and marker mapping), `services/tasks.py` (My Work on `kt_my_work_providers`); `test_awd_reads` 16/16 (D02–D07, V01–V12, V17–V19 headlines, journey codes, task lists) |
| AWD4-305 | Reads `GetAwardWorkspace`, `GetAwardRecord`; API | Done | `services/reads.py`, `award/api.py`; `TestReads` (HOP/AO/auditor actions; technical view without business facts; Not found for suppliers and guests; workspace rows) |
| AWD4-306 | Screens D01, D01e, D02, V01, V02, V03, V12, V18, X07 | Done | `AwdBoard.vue` (one port of the board template), `screens/record.js`, `workspace.js`, `dialogs.js`, `views.js`; fidelity D01, D01e, D02, V01, V02, V03, V12, V18, X07 match (`npx vitest run --project award`) |
| AWD4-307 | `awd-opinion.spec.ts` + live check from the sidebar | Done | `tests/ui/smoke/award/awd-opinion.spec.ts` 1/1 (13 s): Charles from Procurement → Tender Management → Awards, task row, record, draft survives reload, signed, back/forward keep the record. First run showed the page matching the board (screenshot checked); the only failure was the test clicking a hidden radio input |
| AWD-G03 | Gate | Done | `test_awd_intake` 6/6, `test_awd_opinion` 9/9, `ui-awd-opinion-gate` 1/1, boards compared |

### Phase 4 — Decision and decision event

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-401 | `RecordAwardDecision` (Award / No award / Return) | Done | `services/decision.py`; `test_awd_decision` 8/8 (award queues and issues the batch; AO only; no award names a concrete next action and closes the cycle; return creates one task and no event; tie and expired validity block the positive action but allow no award; retry returns the first result) |
| AWD4-402 | `AwardDecisionRecorded v1` event + delivery to the receiver | Done | `services/events.py`, `services/contracting.py`, `test_services/contracting_receiver.py`; one event per committed decision, none for a return; a failed delivery keeps the event and is retried (`test_event_delivery_failure_keeps_the_event_for_retry`); No award creates no publication obligation |
| AWD4-403 | Screens D03, V04, X08, X09 | Done | Fidelity D03, V04, X08, X09 match |
| AWD4-404 | `awd-decision.spec.ts` + live check | Done | `awd-decision.spec.ts` 3/3 (28 s): Amina from the menu task awards in one action; return reaches Charles as "Resolve returned decision"; Record no award keeps the typed reason and names the missing next action |
| AWD-G04 | Gate | Done | service and browser checks above |

### Phase 5 — Notices and authority status

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-501 | Audience reconciliation | Done | `notices.audience` (submitted only; withdrawn none; missing contact stops issue naming HOP); two-bid world gives each bidder their own result (`test_two_bidders_each_get_their_own_result`) |
| AWD4-502 | Batch generation, `IssueAwardNotices`, giving evidence | Done | `notices.prepare_batch/issue`, `letters.py`: one serialised issue under the case lock; portal publish is recorded but is not giving; email delivery evidence gives; reply deadline 24 Jun 2027 17:00 and minimum wait 2 Jul 2027 09:00 from the test profile (`test_awd_notices` 6/6) |
| AWD4-503 | `RetryNoticeDelivery`, Correct contact, Support Issue | Done | `notices.retry`, `recovery.correct_contact`, `recovery.retry_operation`; the same notice identity and letter digest after a corrected contact; service failure → Support Issue for the technical operator, cleared on success |
| AWD4-504 | `GetAwardAuthorityStatus` + Tenders/EVL delegation; cancel/issue serialisation | Done | `services/authority.py` (`status`, `tender_status`, `cancellation_guard`); `test_awd_authority` 4/4 (Issued / Issue in progress / Unknown all refuse cancellation; no case is not a negative from Award) |
| AWD4-505 | Screens V05, V15, V15s, V16 | Done | Fidelity V05, V15, V15s, V16 match |
| AWD4-506 | `awd-notices.spec.ts` + live check | Done | `awd-notices.spec.ts` 2/2: rejected address → Correct contact refused until the owner corrects, then the same notice is given; Daniel's technical view shows no supplier or price and Retry operation resolves |
| AWD-G05 | Gate | Done | service and browser checks above |

### Phase 6 — Supplier portal

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-601 | `/supplier/awards/{id}` surface and resolver | Done | Portal surface `/supplier/awards` (route rules + `kt_portal_surfaces`), `award/portal.py`, bid-overview link through `kt_tender_portal_links` |
| AWD4-602 | `GetSupplierAwardNotice`, `RespondToAward`, `RequestAwardExplanation` | Done | `services/supplier.py`; `test_awd_supplier` 7/7 (accept; representative refused AWD_AUTHORITY_REQUIRED; outsiders Not found; stale notice AWD_NOTICE_CHANGED; revoked signatory; decline needs a reason; late response kept and labelled; request explanation) |
| AWD4-603 | Screens D04, V13, V14, V22, X01, X02, X11 (390 px) | Done | Fidelity D04, V13, V14, V22, X01, X02, X11 match |
| AWD4-604 | `awd-supplier.spec.ts` + live check | Done | `awd-supplier.spec.ts` 3/3 at 390 px (no horizontal overflow): David can only read and request; Mary accepts the exact notice; the unsuccessful bidder sees only her result and gets Not found for the other letter; the late response is labelled |
| AWD-G06 | Gate | Done | service and browser checks above |

### Phase 7 — Clocks, eligibility, Contracting

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-701 | Clocks and the legal/test profile | Done | `services/clocks.py`, `profile.py`; boundaries tested (`test_wait_boundary` 08:59:59 waits, 09:00:00 delivers; reply deadline 17:00 vs 17:01) |
| AWD4-702 | `RefreshAwardEligibility` + sweep | Done | `eligibility.conditions/refresh/sweep` (the seven §5.8 conditions together, text keys); `test_awd_eligibility` 4/4 |
| AWD4-703 | `DeliverAwardPackage` + synthetic Contracting receiver | Done | `eligibility.deliver`; `test_awd_delivery` 3/3 (package terms carry quantity/warranty/amount; receiver down → Failed + Support Issue; a restriction during the outage keeps it held after service returns; a later restriction reaches Contracting as an update without changing the package digest) |
| AWD4-704 | Record next action (V06/V07) | Done | V06/V07 **Record next action** saves Request decision review with the response or deadline evidence attached by the server (`test_no_response_task`) |
| AWD4-705 | Screens D05, D06, V06, V07, V10, X10 | Done | Fidelity D05, D06, V06, V07, V10, X10 match |
| AWD4-706 | `awd-wait-deliver.spec.ts` + live check | Done | `awd-wait-deliver.spec.ts` 2/2: the wait (2 Jul 2027 09:00 shown) then "Contracting has received the award." with Next: Prepare contract; receiver down shows the named technical operator |
| AWD-G07 | Gate | Done | service and browser checks above |

### Phase 8 — Debrief, restrictions, cancellation

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-801 | `SaveAwardExplanation`, `SendAwardExplanation` | Done | `services/explanation.py`; `test_awd_explanation` 3/3 (send and close; failed dispatch leaves it open and resends the frozen reply; a later request is linked) |
| AWD4-802 | `RecordExternalAwardRestriction`, `ReceiveAwardRestriction`, `RecordAwardIssueDisposition` | Done | `services/restrictions.py`; `test_awd_restrictions` 5/5 (order hold; only the applicable §5.10 outcomes; order needs evidence; a reported challenge clears only itself; an order cannot end while another continues; no timer clears a hold) |
| AWD4-803 | Tender events: cancellation, suspension, validity extension | Done | `services/tender_events.py`; `test_awd_cancellation` 4/4 (valid cancellation closes and marks Decision Blocked; unconfirmed or unreadable status never closes; after notice it becomes a restriction; suspension is an authoritative hold). Real post-close cancellation/suspension events do not exist in Tenders (simulated owner events; FU-AWD-02) |
| AWD4-804 | Screens D07, D07c, V08, V11, X03, X04, X05 | Done | Fidelity D07, D07c, V08, V11, X03, X04, X05 match |
| AWD4-805 | `awd-debrief-hold.spec.ts` + live check | Done | `awd-debrief-hold.spec.ts` 3/3: the reply draft survives reload and Send and close closes it (a defect found here — the closed request page carried the open request's screen name — fixed in `recordBoard`); an authoritative order holds until Restriction ended with evidence; Record restriction from Outstanding issues |
| AWD-G08 | Gate | Done | service and browser checks above |

### Phase 9 — Corrections and cycles

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-901 | Post-decision correction review and hold | Done | `corrections.pull`; `test_awd_corrections` 4/4 (the review item holds; No material effect closes only it; the AO's Request corrected evaluation opens cycle 2 on the same case with the original decision kept and no new event; Decline reconsideration) |
| AWD4-902 | `RecordAwardCorrectionDecision`, successor cycle, revised notices | Done | `corrections.record`; `test_awd_cycles` 6/6 (successor cycle to a corrected No award with one event per committed decision; revised notices held while the treatment is unverified; Authorise revised notices later creates no second decision; corrected award and notify in one action; returned successor opinion; correction after a closed No award is review only) |
| AWD4-903 | Screens V09, V17, V19, V20, V21, V23, V23p, V24, V25, X06 | Done | Fidelity V09, V17, V19, V20, V21, V23, V23p (one registered departure: the Decision reason field, FU-AWD-16), V24, V25, X06 match |
| AWD4-904 | `awd-correction.spec.ts` + live check | Done | `awd-correction.spec.ts` 1/1: review → propose → Amina authorises → cycle 2 waits for the corrected report (Opinion Blocked) |
| AWD-G09 | Gate | Done | service and browser checks above |

### Phase 10 — Access, dead ends, retries

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-1001 | Per-actor DTO filters; Not found for protected reads | Done | `reads.py` per-actor projections; `test_awd_leakage` 7/7 (technical reader and support issues carry no business facts; auditor reads with no action and is refused commands; outsiders, suppliers and guests get Not found; a supplier sees only their own letter; the portal asks guests to sign in; task titles carry no amounts or names; refusals disclose nothing else) |
| AWD4-1002 | My Work matrix vs `next_step_register.md`; technical-read resolver | Done | My Work matrix via `tasks.py` checked in `test_awd_reads`; technical-read resolver and probes (`award/services/technical_read.py`) conform to the core rule (checked directly; the core conformance module itself fails on Bid Opening and Tenders entries, FU-AWD-14) |
| AWD4-1003 | `test_awd_leakage.py`, `test_awd_dead_end.py`, `test_awd_idempotency.py` | Done | `test_awd_dead_end` 1/1 (34 stages × HOP, AO, auditor, technical: no dead end, no technical turn); `test_awd_idempotency` 4/4 |
| AWD-G10 | Gate | Done | `make awd-leakage-gate` and `make awd-dead-end-gate` green |

### Phase 11 — Canonical stage and demo

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-1101 | Canonical `award` stage (seed + validate) | Done | `award/seeds/kentender_mvp_v1.py`; `canonical.STAGES` ends with `award`; `make seed-canonical THROUGH=award` 12.6 s, validate ok (10 checks); second run `idempotent: true`, nothing removed |
| AWD4-1102 | Demo profiles + make targets | Done | `award/seeds/profiles.py`: AWD-DEMO-OPINION, -DECISION, -NOTICE, -WAIT, -DELIVERED; `make seed-awd-profile(s)`, `seed-awd-profile-restore` |
| AWD4-1103 | `awd-demo-walk.spec.ts` from the menu and the bell | Done | `awd-demo-walk.spec.ts` 4/4 (34 s) on the canonical Tender: Charles from the menu, Amina from the bell, David then Mary from their Tender page in the portal at 390 px, the wait, Contracting receipt; the profile restored and `seed-canonical-validate` green afterwards |
| AWD-G11 | Gate | Done | seed + validate green, second run idempotent, demo walk green |

### Phase 12 — Release evidence

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-1201 | Fidelity over 47 boards | Done | `npx vitest run --project award` 48/48: all 47 boards compared (page for page; dialogs dialog for dialog), one registered departure (V23p Decision reason, FU-AWD-16); also inside `make ui-structure-gate` (45 + 1,558 green) |
| AWD4-1202 | Ordinary path + branch matrix | Done | Ordinary path: canonical stage + `awd-demo-walk.spec.ts`. Branches: every §13 branch has a synthetic stage (`fixture_chronology.md`) exercised by the service tests; 34 stages × 4 viewers in the dead-end matrix; the browser specs cover D01–D07c, V01, V04, V05, V08, V09, V10, V13, V14, V16, V17, V19, V22, X01, X03, X04, X06, X08, X09 |
| AWD4-1203 | Persona pass | Done | Charles, Amina (`awd-opinion`, `awd-decision`, `awd-demo-walk`), Mary and David (`awd-supplier`, demo walk, 390 px), Daniel (`awd-notices` technical view), Naomi, Daniel and Administrator on the canonical award (`awd-personas.spec.ts` 3/3: auditor reads with no action; technical readers see no report, supplier, price, opinion or decision). Esther Njeri holds the same Technical Operator role; not walked separately |
| AWD4-1204 | AC map closure; `RUNBOOKS.md` | Done | AC map below (31 rows: 27 Done, 3 Partial, 1 Blocked — owner); `RUNBOOKS.md` written |
| AWD4-1205 | One cross-module regression run | Done | 1 Oct 2026, justified by the upstream files changed (Evaluation and Tenders): `make evl-services-gate` 83/83 and `make tenders-services-gate` 124/124, 15¾ min, green. BOP/BDS not re-run (no dependency changed). Canonical reseeded after (`seed-canonical THROUGH=award` validate ok). Pre-existing failures outside Award found on the way: core technical-read conformance (FU-AWD-14) and the Industry design gate on BidEvaluation.vue (FU-AWD-22) |
| AWD-G12 | Gate | Done | `make ui-awd-release-evidence-gate` 1 Oct 2026: fidelity 48/48 + 22 browser tests in 9 specs, 3 min 21 s, all passed; Python: `awd-services-gate` 95 tests / 64 s, `awd-seams-gate` 6, `awd-leakage-gate` 7, `awd-dead-end-gate` 1 + 4; `seed-canonical-validate THROUGH=award` ok |

### Phase 13 — Owner-gated

| ID | Item | Status | Evidence |
|---|---|---|---|
| AWD4-1301 | Owner-document amendments (FU-AWD-01…08) | Blocked — owner | |
| AWD4-1302 | AWD v0.4 approval | Blocked — owner | |
| AWD4-1303 | Verified legal operating profile (LAW-V-001) | Blocked — owner | |
| AWD4-1304 | Real signing, notice channels, Contracting receiver | Blocked — owner | |
| AWD4-1305 | Security review, production enablement | Blocked — owner | |

## Acceptance map

| AC | Phase | Status | Evidence |
|---|---|---|---|
| AWD-AC-001 | 2, 3, 11 | Done | Real delivery → one case and one HOP task, EVL row taken up, retry no duplicate (`test_awd_integration`); synthetic receipt/retry (`test_awd_intake`); canonical stage. An empty opening delivers no Evaluation report, so Award has nothing to receive (EVL's no-bids path never calls the consumer) |
| AWD-AC-002 | 3 | Done | `test_awd_intake` (missing annex, missing signature, unverifiable digest → exact source issue owned by HOP); signing refused AWD_SOURCE_INCOMPLETE (`test_awd_opinion`) |
| AWD-AC-003 | 3 | Done | Exact frozen opinion/report digest signed; signed opinion and AO task in one transaction; unavailable/uncertain proof keeps the draft and resolves through the same attempt (`test_awd_opinion`). Through the test attestation (simulation); real signing is AWD4-1304 |
| AWD-AC-004 | 4 | Done | Supplier, bid and amounts come only from the signed report (no picker or editor exists); submitted and evaluated amounts shown distinctly (D03, `test_awd_reads`); recorded dissent shown to the AO in the Evaluation report disclosure (`TestDissent`) |
| AWD-AC-005 | 3, 4 | Done | Expired/qualified report: signed factual opinion and No award allowed, positive decision refused AWD_VALIDITY_EXPIRED / AWD_NO_SUPPORTED_AWARD (`test_awd_opinion`, `test_awd_decision`) |
| AWD-AC-006 | 3 | Done | Return needs no signed opinion, keeps prior versions, supersedes drafts, waits for the successor report and requires a fresh opinion (`TestReturn`, `test_awd_integration::test_return_report_goes_back_through_evaluation`) |
| AWD-AC-007 | 4, 5 | Done | One AO action authorises and issues the exact batch; no notice approval control exists (`test_award_queues_batch`, `awd-decision.spec.ts`). No verified form requires an extra signature in the test profile |
| AWD-AC-008 | 5 | Done | Audience from BDS's sealed submission history: one notice per arrangement for its final version, replaced versions listed once, withdrawn not Submitted (`test_awd_seams::TestAudienceRule` over Bid Submission's own `award_gateway`), own result per letter (`test_awd_notices`), real audience on the canonical Tender (`test_awd_seams`). The verified legal audience rule itself is a production gate (FU-AWD-09) |
| AWD-AC-009 | 5 | Done | Coordinated issue; partial giving keeps the stage at Notices; corrected contact and retries keep notice identity and letter digest with every attempt and address retained (`test_failed_address_task`, `awd-notices.spec.ts`) |
| AWD-AC-010 | 5 | Partial | Serialised boundary: Tenders' `cancel_tender` asks Award's guard under the case lock; Issued, Issue in progress and Unknown refuse (`test_awd_authority`). A true concurrent cancel/issue interleaving test is not built, and Tenders has no post-close cancellation to race (FU-AWD-02) |
| AWD-AC-011 | 6 | Done | Mary accepts; David refused; cross-supplier Not found; revoked authority and stale notice refused with no response recorded (`test_awd_supplier`, `awd-supplier.spec.ts`) |
| AWD-AC-012 | 6, 7 | Done | Timely acceptance, late acceptance (kept, not operative, HOP issue), decline and no response are distinct; Record next action saves Request decision review with server-attached evidence; no runner-up or security action exists (`test_awd_supplier`, `test_awd_eligibility`) |
| AWD-AC-013 | 7 | Done | Before/at/after boundaries, profile counting and timezone, the latest wait over all recipients, and a lawful revision kept beside the earlier calculation (`test_awd_eligibility` incl. `TestClockRevision`); no browser clock is used. Statutory counting is a production gate (FU-AWD-09) |
| AWD-AC-014 | 5, 7 | Done | Validity checked at decision (`test_expired_validity_blocks_award_but_allows_no_award`), at issue (`test_validity_expiring_before_issue_stops_the_batch`) and at delivery (`TestValidity.test_expiry_holds`) |
| AWD-AC-015 | 8 | Done | `test_awd_explanation` (frozen reply, failed dispatch keeps it open and resends the same reply, later request linked); the request is labelled as not a Review Board filing in the letter's review information; the test profile's debrief rule sets no waiting effect |
| AWD-AC-016 | 8 | Done | `test_awd_restrictions` (order vs reported challenge distinct, evidence-backed resolution clears only its own issue, no timer clears) |
| AWD-AC-017 | 9 | Done | `test_awd_corrections`, `test_awd_cycles` (hold without approval, original decision/notices kept, corrected report needs a fresh opinion and Decide correction; the ordinary return is refused after a decision) |
| AWD-AC-018 | 8 | Done | `test_awd_cancellation` (valid cancellation closes and keeps history; unconfirmed or unavailable status never closes; after notice it becomes a restriction; No award is a separate outcome) |
| AWD-AC-019 | 7 | Done | `test_awd_delivery` (all §5.8 conditions, durable receipt and Prepare contract task; outage keeps the package and names the technical owner; a new restriction blocks the retry after service returns) |
| AWD-AC-020 | 8 | Done | `test_later_restriction_reaches_contracting_without_rewriting_the_package` |
| AWD-AC-021 | 7 | Partial | The package carries quantity, warranty, amounts and the published-terms references (`test_delivered`); the full contract mappings, reservation lineage and security terms are referenced, not re-read from the issued tender (no Contracting counterpart yet, FU-AWD-05) |
| AWD-AC-022 | 3–10 | Done | `test_awd_reads` (§5.9 headlines, markers and tasks), `test_awd_dead_end` (34 stages × 4 viewers), browser specs assert the journey markers; unrelated work stays visible (debrief leads the running wait) |
| AWD-AC-023 | 0, 12 | Done | `reconciliation/command_map.md`; all 47 boards compared (`npx vitest run --project award` 48/48, one registered departure) |
| AWD-AC-024 | 10 | Done | `test_awd_leakage` 7/7 and `awd-personas.spec.ts` (see AWD4-1203) |
| AWD-AC-025 | 10 | Done | `test_awd_idempotency` 4/4, `test_awd_decision` retry, `test_awd_intake` retry, uncertain signing (`test_awd_opinion`) |
| AWD-AC-026 | 7, 13 | Partial | Without the simulation flag no profile is verified and every positive advance is refused (`profile.verified`); test labels render only on a test environment. Production enablement is owner-gated (AWD4-1303/1304) |
| AWD-AC-027 | 13 | Blocked — owner | Register and owner contracts are owner work |
| AWD-AC-028 | 7 | Done | `test_awd_reads` (DDDCN wait, DDDDB receiver down, DDDBN restriction, DDDDD delivered) |
| AWD-AC-029 | 9 | Done | `test_awd_cycles` (correction to a closed cycle is review only; successor on the same case with a new number; returned successor opinion → Decide correction; prior decisions and events unchanged; authority status keeps history) |
| AWD-AC-030 | 8 | Done | `test_awd_restrictions` (only defined bases and outcomes; HOP cannot end another order, change a decision or make a late acceptance timely) |
| AWD-AC-031 | 4, 9 | Done | `test_awd_cycles` (revised notices held then authorised without a second decision; one event per committed decision; returns, instructions and notice-only authorisations create none) and `test_awd_decision` (retry reuses the event; failed delivery keeps it; No award creates no publication obligation). Contracting's own obligation handling is the test receiver only (FU-AWD-05) |
