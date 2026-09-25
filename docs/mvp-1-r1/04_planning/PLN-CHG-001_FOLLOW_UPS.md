# Procurement Planning — follow-ups (PLN-CHG-001 v1.18 cycle)

Items deliberately outside the v1.18 implementation cycle opened 12 September 2026 (`PLN-CHG-001_IMPLEMENTATION_TRACKER.md`), plus the disposition of every row still open in the retired v1.12–v1.16 register (`retired/FOLLOW_UPS.md`). Each row is an owner decision this cycle has no authority to make, a sibling document amendment the owner chose to log rather than author now (plan D17), a legal-verification prerequisite (v1.18 §15.2), or a future facility named in §15.3.

**Status:** opened 12 September 2026 with the plan. Nothing here blocks Phase 0–3; FU-20 (SEED-001 v1.3) and FU-21 (legal verification) are cited by Phase 4/5 rows where they bound what the seed and release evidence may claim.

## Carry-forward from the retired register

| Old ID | Item | Disposition under v1.18 |
|---|---|---|
| FU-02 | Budget/Strategy contracts expose no human business reference | **Closed** — `list_eligible_budget_lines` returns `reference` (`kentender_budget/services/budget_line_contracts.py:334-357`), consumed by the current screens; Strategy path labels come from `get_strategy_lineage`. |
| FU-03 | KENTENDER_MVP_V1 full-stack validator crashes on the retired `Strategy Programme` doctype | **Carried as FU-28** — the legacy multi-PE orchestrator is retired by SEED-OPS-001; the canonical validator (`make seed-canonical-validate`) is the live check. Owner may delete the legacy validator. |
| FU-04 | Dormant references to retired Planning doctypes in tender-management and legacy seed families | **Carried as FU-29** — no live caller; the tender-management rebuild owns them. Phase 2a's slug/removed-construct scans will list any that name doctypes this cycle renames (`Annual Plan Publication`). |
| FU-05 | Successor snapshot cannot distinguish carried-over from removed items | **Closed by this cycle** — v1.18 §9.2 Changes tab and `Plan Item.item_state` `Removed in successor` in the review pack (Phase 2e/3C/3F rows). |
| FU-06 / FU-18 | `RemovePlanItemInSuccessor`, `CancelPlanUpdate`, `RetryPublication`, `Withdraw departmental submission`, Finance-shortfall and No-validation-tasks states have no UI trigger | **Closed by this cycle** — v1.18 supplies the compositions (U21-cancel-update, U13-D retry, U02 withdraw, U10-scenarios excess, U21-empty "No departmental plans awaiting validation"); built in 3A/3B/3E/3G. |
| FU-08 | §14.5 illustrative dates implied a 31-day evaluation period | **Closed by the spec** — v1.18 §10.1 dates (1 May → 22 May → 21 Jun → 26 Jun → 28 Jun → 12 Jul → 31 Aug 2027) derive from 21/30/5/2/14 and the profile carries the 30-day maximum; the seed uses the same calculation (RI-056). |
| FU-09 | Peter/Julia register dates split between NDS and Planning | **Closed by this cycle** — plan D19 restores Julia 1 Oct–30 Nov 2026 acting and dates Peter's Digital Health authority from 1 Dec 2026 in `site_setup.py`; seeds run under the frozen clock so the windows are real at command time. |
| FU-12 | Partial rows: county fixture (AC-097), Project Name (AC-101), §7.5A field walk (AC-110) | Project name **closed by this cycle** (`Annual Plan Version.project_name`, PLN18-AC-100). County end-to-end fixture **carried as FU-26**. §7.5A reporting walk **replaced** by PLN18-AC-109 / RI-046 (field-ownership map), built in Phase 2f. |
| FU-13, FU-14, FU-15, FU-16 | Closed 7–11 September 2026 | Unchanged; their behaviours are re-expressed in v1.18 (§11.2 supporting lines, record-route task actions, Active copy for the Requisition contract) and covered by PLN18-AC-111 / RI-051 / RI-053 and `test_plan_requisition`. |
| FU-17 | §4 field-table drift (`indicative_amount_minor_units`, stored `source_line_id`, variance sign, governance `scope`) | **Closed by the spec** — v1.18 §4.1 Money in currency units, §4.3 `source_line_id` is a projection (`P`), §5.5.1A actual − baseline (positive late) matches `schedule.py`, §4.7 task carries `capacity` (plan C13). |
| FU-19 | Technical read stated once in KT-STD-001 v1.5 §3A.6 | **Carried as FU-27** — v1.18 §6 still carries its own Administrator/System Manager row; KT-STD v1.6 / PLN v1.19 citation clean-up. |

## Register

| ID | Item | Severity | Owner |
|---|---|---|---|
| FU-20 | **SEED-001 v1.3** — adopt v1.18 §13.1 chronology (Julia certifies DHI 25 Nov 10:30, Peter HRMD 11:00, Mercy accepts 27 Nov 14:00/14:05), the laptop Plan boundary 31 Dec 2027 (REQ keeps 30 Sep 2027 as its operational date), the `Youth` planned designation on `PPI-MOH-2027-033` with `Fixture-verified — not production law` rules (plan D16), the HOPF signature, Treasury evidence `MOH/APP/2027/001` and the 10 Dec 2026 15:00 EAT acknowledgement; §6 naming note for `Annual Plan Publication` → `Plan Publication` | High — the canonical seed diverges from the written fixture until this lands | SEED / KT-STD owner |
| FU-21 | **Primary legal verification** (v1.18 §15.2 / §17.2) — method admissibility and thresholds, cumulative limits, schedule/counting rules, reservation eligibility/denominators/overlap, county basis, approval-route applicability, publication prerequisites and the prescribed Third Schedule layout. Until recorded, every seeded profile/rule stays `Production verification pending` (or fixture-verified in the canonical seed) and the C03/C04 screens say so | High — blocks any production-style approval claim; does not block the build | LAW / Configuration & Governance |
| FU-22 | **CFG-CHG-002 v0.10** — fifth System setup tab, method/schedule profiles and their maintenance, funding-source commands, `Regulatory Reference` verification status/supersession/applicability-date resolver, county/type consistency, DPP intake reason, reservation target no longer "advisory" (replaces §4.4A / CFG-AC-032), close-instant clarification, historical-register completeness (v1.18 §17.2 table) | Medium — code lands in Phase 1a/1b; document lags | Configuration & Governance |
| FU-23 | **BUD-CHG-001 v1.8** — `validate_plan_affordability_for_decision`, `get_annual_procurement_budget_basis`, decimal-string amounts and currency precision at the boundary, source-OU eligibility argument stated | Closed 24 Sep 2026 — BUD-CHG-001 v1.10 removed `get_annual_procurement_budget_basis` (the 30% measure is the plan's eligible value, PLN v1.25); `validate_plan_affordability_for_decision` remains | Budget & Funding |
| FU-24 | **NDS-CHG-001 v1.11** — `NeedPlanningDispositionChanged.v1` (separate from `NeedPlanningUsageChanged.v1`), disposition projection and "Planning information" display; header stays proposed until then | Medium | Departmental Needs |
| FU-25 | **REQ-CHG-001 v1.8 / TPR-CHG-001 v0.8** — `AuthoriseRequisitionDrawdown` name, `PLN_ITEM_SCOPE_LOCKED` / `PLN_ITEM_AUTHORISATION_HELD` handling, `PlanItemCorrectionOutcome.v1` and the requester follow-up after "Closed without change", removal of REQ §7.4A "open to correction"; TPR §4.8 event envelope and Planning-side never-overwrite guard (closes TPR FU-05) | Medium | Requisitions / Tender Preparation |
| FU-26 | **County-entity fixture** — a Playwright/Python world with `entity_is_county` set so PLN18-AC-097 / UX-24 county calculations are exercised end to end (the one-site model has no county entity) | Low | `kentender_procurement` (Planning) + fixture owner |
| FU-27 | **KT-STD-001 v1.6 / PLN v1.19 editorial** — cite §3A.6 for technical read instead of module prose; §8.3 note that the Head of Procurement Function also signs the Annual Plan preparation; §8.4A Planning window unchanged | Low | Document owner |
| FU-28 | Legacy `validate_kentender_mvp_v1` still crashes on `Strategy Programme` (retired FU-03); superseded by the canonical validator | Low | `kentender_core` seeds — delete or leave |
| FU-29 | Dormant retired-doctype references in tender-management and legacy seeds (retired FU-04) | Low — latent, no caller | `kentender_procurement` (tender-management rebuild) |
| FU-30 | **Cross-module Money precision** — BUD/NDS/REQ still compute in `flt()` with epsilons; Planning validates decimal strings at its boundary only (plan D3). Agreement "before release" per v1.18 §4.1 | Medium | Budget, Needs, Requisitions owners |
| FU-31 | **Future facilities named in v1.18 §15.3** — multi-year procurement, full OCDS publication, automated Treasury transmission, aggregate item-level actuals, the six remaining milestone integrations, fulfilment derivation, candidate-level preference entitlement, statutory returns, scope expansion via tender amendment; plus a real (non-sandbox) publication destination and State Portal evidence | Deferred by design | Product owner |

## Verifying a fix

- **FU-20:** SEED-001 v1.3 exists and `validate_planning_seed` facts match its §3.3/§3.6 tables; `make seed-canonical-validate` green.
- **FU-21:** rules and profiles carry `verification_status = Verified` with instrument/provision/document recorded; the C03/C04 screens and the review pack drop "Production verification pending"; the canonical seed may then drop the fixture-verified set.
- **FU-22–FU-25:** the named sibling version exists and its `FOLLOW_UPS`/tracker row cites the Phase 1 evidence rows (PLN18-101..110).
- **FU-26:** a county world drives `county_resident_reservation` in a browser spec and PLN18-AC-097 moves from `Partial` to `Done`.
- **FU-30:** one shared precision contract test passes in each of the three sibling suites.

## PLN-CHG-001 v1.23 — raised during the build (18 Sep 2026)

| # | What | Why it was not closed here | Where it bites |
|---|---|---|---|
| FU-V123-01 | §10.13's U14-ACTUALS artboard block still draws a **Forecast date** column; U14's BASE/PARTIAL cards still draw a **Completion** row reading "No completion evidence" / "Tracking is not yet available", and label the execution fact **Procurements started** rather than **Procurement stage**. | The prose of the same section forbids all three — PLN23-CHG-001 removed the forecast facility outright, PLN22-AC-009 forbids a completion placeholder, and §10.13's own column list names Procurement stage. The build follows the prose and the acceptance criterion. | The artboard file, not the product. The fidelity gate carries a named exemption (`U14_EXECUTION_COLUMNS` in `planning-fidelity.spec.ts`) that fails as stale the moment the artboard is regenerated. |
| FU-V123-02 | §10.7 U08-INCOMPATIBLE's copy says "These requirements use different budget lines and cannot be combined." | The rule the command enforces is the same **budget**, not the same budget line: two lines of one budget combine legitimately, and there is a test for it. The build uses §8's own governed sentence plus the difference that actually blocks it. | The variant's copy. §8's error table is already right. |
| FU-V123-03 | §10.11 U12's fixture states Revision 2 and 11:00/14:05 EAT; the canonical seed's own values are Revision 1 and 10:00/14:00. | Fixture values, not product behaviour — the fidelity gate deliberately never compares values. | Only the artboard's own fixture caption. |
| FU-V123-04 | `active_view` in `plan_read` is now rendered only as the approval/publication section of an Active plan; the item rows inside it are no longer read by any screen. | Trimming it means rewriting the seed validation and eight test assertions for no user-visible gain. | Dead weight in one projection. |
| FU-V123-05 | §10.10's U11-AO and U11-STATUTORY artboards still draw a **Decision / Outcome / Capacity / Person / Date/time** table between the current stage and the decision buttons. | §10.10's own prose replaced it: the Accountability section is two compact labelled rows (Funding, Preparation), and the immutable decision-history table moved into the collapsed **Changes and history** disclosure, which the same section says must not present a future decision as a synthetic history row. The build follows the prose. | The artboard file, not the product. The fidelity gate carries a named exemption (`U11_DECISION_TABLE` in `planning-fidelity.spec.ts`) that fails as stale the moment the artboard is regenerated. |
| FU-V123-06 | A purchase with no strategic objective shows Current work **Choose a strategic objective**, while the plan containing it passes every check and is offered for signature. Three gates agree the objective is optional — `readiness.item_blockers` is reached with `objective_eligible = (not item.strategic_objective) or …`, the submission gate uses the same predicate, and `plan_governance` fails only when a *set* objective has become ineligible. Only `plan_read._current_work` treats an unset one as outstanding work, and it labels it with `PLN_OBJECTIVE_INELIGIBLE`, whose own §8 message is "Choose a strategic objective currently available for this plan" — an ineligible choice, not a missing one. | Which way it should agree is a business decision, not a display one. Either Current work stops naming a field nothing requires, or Strategy → Plan traceability means the objective is mandatory and all three gates are too lax. The second is a domain change well outside a UI cycle. | Observed live: one purchase read "Choose a strategic objective" beside "Ready for the Head of Procurement Function to sign and submit". A Planner would chase a field that blocks nothing, and the column stops meaning "what stands between this purchase and readiness". |
| FU-V123-07 | §10.8's two U09 variant artboards carry pre-v1.23 wording. U09-INVALID-SCHEDULE draws **Estimated period**, **Estimated completion**, **Departmental required-by date** and **Review schedule**; §10.8's own Dates block names them Expected delivery period, Expected completion, Departmental deadline and Review dates. U09-REMOVE draws one action **Remove item and return requirements**; §10.8 heads that dialog **Remove this purchase?** and names its primary action **Remove purchase**. | The prose is unambiguous in both cases and the build follows it. Renaming four live labels and a dialog to match a lagging artboard would contradict the section that governs them. | The artboard files, not the product. The fidelity gate carries named exemptions (`U09_SCHEDULE_LABELS`, `U09_REMOVE_ACTION`) that fail as stale once the pack is regenerated, and asserts §10.8's own strings directly in the meantime so the panels are not left effectively ungated. |
| FU-V123-08 | §10.9 U10-HISTORY asks for two named blocks, **Funding checked at approval** and **Latest funding check**, each carrying Review; Budget version; Plan version; Outcome; Person; Date/time. The build renders one **Funding evidence history** table with Review; Basis; Outcome; Actor; Time, plus two status facts headed Funding evidence at approval and Current funding confirmation. | The block names are a copy change, but the columns are not: Plan version is not in the read at all, and Budget version is folded into Basis. Supplying them per review is a read change, not a relabel, and the current table already satisfies the rule that matters — a later review never overwrites an earlier one's outcome. Doing it properly is a scope decision rather than a fix. | The U10-HISTORY artboard carries no landmarks, so the fidelity gate cannot see this at all; it was found by reading §10.9 against the live page. The gate now asserts the history's structure behaviourally instead. |
| FU-V123-09 | The "Your actions" card's generic **Start departmental plan** button (§10.3, shown for an actor who is Author or HoD across two or more organisation units at once, with one not yet started) went through `frappe.set_route()` with no case for its own route shape, so the click silently re-rendered the same page. Fixed (`a8f77281`) by routing it through the same command the single-department card already used correctly. | Caught by tracing the code paths this session, not by a test — this cycle's fixtures give every actor exactly one departmental unit, so the multi-unit case that reaches this button has no fixture at all. | Anyone acting as Author or HoD for two or more departments in the same intake window, with at least one unstarted, could click the button and see nothing happen. |
| FU-V123-10 | Owner-driven design-fidelity sweep (19 Sep 2026), prompted by a side-by-side screenshot: the workspace's Financial year control was bare `<label>` + `<select>` + a separate Reset link, not U01's own `.tag.tag-neutral` chip; U08's "Keep separate / Combine into one purchase" choice was two bare radio labels, not U08's own `.seg`/`.seg-opt` bordered toggle. Both fixed (`1dfaa6b5`, `8d67ceeb`). | Nothing to log against — these were genuine misses, not defensible deviations, found precisely because the fidelity gate cannot see them: it does landmark-subsequence comparison over a fixed element whitelist (headings, `label`, `button`, table headers, `.kt-label`…), and a plain `.tag`/`.seg` wrapper is not one of those elements. All 5 U01 and the U08 fidelity assertions still pass unchanged after both fixes — proof the gate was blind to this class of defect, not that the screens were fine. | Swept every `.tag`/`.seg`/`.kt-kpi`/`.kt-record`/`.kt-steps` use across every Planning artboard against its live component. Everything else already matches: KPI tiles (`DppPlanScreen`, `DppValidationScreen`, `ReviewScreen`), the combined-purchase tag (`PlanItemEditorScreen`), notices, disclosures and timelines. Two smaller items intentionally left as-is: U12 draws "Accepted for planning" as a `.tag-accent`, but the shared token sheet's own rule is "decorative tags — labels only, never state (state is `.kt-status`)" — the live `.kt-status.is-live` is the more correct choice, not a miss. The KPI tiles' decorative SVG icons (list/wallet/circle-slash) are omitted everywhere consistently — a minor, low-priority polish gap, not a fidelity break. **Not yet swept:** dialogs and screens outside the 04_planning artboard pack proper (e.g. anything under `C01-C04`), and no other module has had this same `.tag`/`.seg` sweep run against it — Budget's own Financial year strip uses the identical bare `<label>`+`<select>` pattern and has not been checked against its own current artboard pack. |
| FU-V125-01 | Rule-driven exclusions from the 30% measure (by category, method or funding), each with its reason. | The verified rule names none, so every current purchase is Included; `readiness.item_applicability` is the one place to add them. Needs the rule payload to carry them first (System setup). | Only once a rule excludes something. |
| FU-V125-02 | System setup still offers **Annual procurement budget** as a denominator basis (`RuleEditor.vue`, `regulatory_reference` payload validator) and seeds a 10-entry category catalogue with `advantage_rank`. | Owner scoped this cycle to Budget and Planning; System setup v0.14 was in progress in the same tree. Planning ignores both (it reads only the four base designations and never the basis field). | Someone can still configure the old reading; it has no effect on Planning. |
| FU-V125-03 | County-residents treatment and the exact rule snapshot are not carried into the Requisition handoff (`plan_requisition.get_requisition_eligible_plan_item` passes `reservation_category` only). | REQ-CHG-001 v1.10 / TPR v0.9 are not yet controlling (RES-IMP-001 §8). | Tenders cannot show County treatment until this lands. |
| FU-V125-04 | U07's purchases table and the new reservation table overflow their container at 390 px (page does not scroll sideways, but the tables are clipped). | Pre-existing across U07's tables, not introduced here; a screen-wide narrow-layout decision. | Phone-width reading of U07. |
| FU-V125-05 | Drop the retired `reservation_category_reason` column. | Already on `RETIRED_COLUMNS_PENDING_DROP`; no longer read or copied. | Schema tidy only. |


## Accepting a Need starts the departmental plan (23 Sep 2026)

Owner instruction, raised while testing Needs and Planning together: a Head of
Department who has just accepted a Departmental Need should not then have to
press **Start departmental plan** for the same department. Accepting is the
decision that gives the department something to plan, so the Draft now exists
from that moment.

**What was built.** Planning subscribes to the published
`DepartmentalNeedAccepted.v2` outbox row (`hooks.py` `doc_events` →
`procurement_planning.services.dpp_autostart`) and calls
`dpp_lifecycle.ensure_departmental_plan`, which opens the department's root and
Draft Submission 1 and projects the accepted Need into it. The subscriber sits
on Planning's side, so Departmental Needs still knows nothing of Planning
(decision D5), and it runs inside the accepting command's own transaction:
creation from a command, never from a read, so §4.2's invariant 1 and §4.2's
"Initial reads create nothing" both stand unchanged. Starting the plan is a
consequence of acceptance and never a condition of it — the work runs in its
own savepoint and a failure is logged and dropped rather than losing the
acceptance. A department whose plan is already Submitted, Accepted or
Withdrawn is untouched; a Withdrawn initial Draft still reopens only through
its own §5.1.5 HoD decision. `patches/pln_start_plan_from_accepted_needs.py`
gives the same Draft to departments whose Needs were accepted before this
landed.

**Start departmental plan stays**, and is now reached only by a department with
no accepted Need at all — the direct-requirements-only case. Nothing about the
intake window changed: it still governs every submission, and a Draft started
outside it reads **Not submitted — window closed** exactly as one started by
hand would.

**Spec text to update at the next version (v1.25).**

| Where | Says now | Should say |
|---|---|---|
| §5.1.5 transitions, row 1 | "No DPP; permitted initial intake \| Start departmental plan \| Author or HoD" | Two rows: accepting a Need opens the root and Draft Submission 1 for its department; **Start departmental plan** remains the Author/HoD action for a department with no accepted Need. Keep "no creation from a read" — it is still true. |
| §8.2 command table | `OpenDepartmentalPlan — Author/HoD` | Add the system-initiated form: same root/Draft creation, triggered by `DepartmentalNeedAccepted.v2`, authority carried by the acceptance, recorded in the Planning Command Journal against the accepting actor. |
| §10.3 U01-DEPARTMENT-AUTHOR / §12.1 route table | "With no DPP and open intake: **No departmental plan yet** plus primary **Start departmental plan**"; "Explicit Start departmental plan or Prepare plan update" | Keep both, qualified: the empty state is what a department with nothing accepted sees. Once a Need is accepted the same actor arrives at **Continue departmental plan**. |
| §7.1 intake | Projection runs inside Planning commands | Add the subscriber as the first of those commands, and say a later acceptance joins the open Draft immediately rather than at the next Open command. |

**Watch item.** Any test or fixture that accepts a Need now also produces a
Departmental Plan for that department and year. The Python suites'
`test_departmental_needs_lifecycle._drop_plans_on` clears the disposable-year
case, `procurement_planning.seeds.playwright_ui_fixtures._wipe` clears the
fixture year, and `kentender_core.seeds.canonical` already treats a
Departmental Plan outside `PLANNING_NS` as non-canonical. The Departmental
Needs Playwright fixtures cannot clear one themselves — their `seeds/` module
is inside the D5 boundary scan — so a Needs UI world that accepts on a year
with no seeded plan leaves one behind for the canonical clear to remove.

## U09 purchase editor — layout audit and re-port (23 Sep 2026)

Raised by the owner from a live screenshot of PPI-MOH-2027-001: "improper
layout, duplicated sections, no padding, font mismatches, haphazard element
layout". Audited against `design/Artboards-U09.dc.html` and the rendered page,
with measurements, rather than patched from the screenshot. Everything below
was live, and every one of U09's three fidelity assertions passed throughout.

| # | Defect | Cause | Fixed |
|---|---|---|---|
| 1 | The same critical banner twice: "Complete the highlighted purchase details and required evidence." | `readiness.item_blockers` reports one blocker per incomplete field; several share one code and one message, and the editor rendered one banner per blocker (also a duplicate `v-for` key). | One banner per distinct sentence. |
| 2 | Nothing was highlighted, though the sentence says "the highlighted". | The blockers carry the field they are about; the form never used them. | The named fields carry `.pln-field-flagged` (critical border and label). |
| 3 | Estimated cost read as three ragged columns; the supporting-document input rendered in the heading typeface. | The amount, the basis textarea and the document input shared one `.kt-meta-row`, and the inputs sat inside `.kt-meta-value` (`.kt-input`'s `font: inherit` then picks up the heading family — measured: `Barlow Condensed` against `Barlow` everywhere else). | Amount is a `.pln-fact`; basis and document are `.kt-field`s in a `.pln-form-column`. |
| 4 | Procurement approach and Dates were full-width or content-width, at mixed baselines. | Both wrapped `.kt-field`s in a `.kt-meta-row`. | `.pln-field-grid` (the board's 320px pairs) and a dates grid of two fields plus two facts, top-aligned. |
| 5 | Fields touched each other with no separation. | `.kt-field` has no margin of its own; the board wraps them in a flex column with `gap: space-4`. | `.pln-form-column`. |
| 6 | The classification line and the combined-purchase reason floated loose. | `.pln-summary-line` was used in the template and defined in no stylesheet. | Defined as the board's quiet group with its link at the end of the line. |
| 7 | "Applicable rule evidence" stood over nothing once the method was cleared. | The heading was unconditional; its two facts were not. | The block renders only when a rule resolved; §10.16's missing-setting panel already carries the unresolved case. |
| 8 | The boundary sentence appeared twice when the schedule missed the deadline. | The critical notice and the line under the dates both rendered `boundaryText`. | The notice alone, as U09-INVALID-SCHEDULE draws it; the line returns with its tick when the deadline is met. |
| 9 | A milestone table of seven dashes before any invitation date was set. | The table rendered unconditionally. | It renders when a schedule exists; otherwise one line says what to enter. |
| 10 | The record context was a three-cell labelled strip the board never draws; Supporting details had no chevron and no contents chip. | Ported from the prose, not the board. | `.kt-page-scope` line; the board's chevron and chip. |

**Why the gate did not catch any of it.** `expectLandmarkSubsequence` compares
an ordered subsequence of landmark *texts* — headings, labels, buttons, table
headers. A duplicated banner adds a repeated text a subsequence check skips; a
field built out of `.kt-meta-value` has the same label text as one built out of
`.kt-field`; an orphaned label is still a label in the right order. The gate is
a copy-and-order check, not a layout check, and it never opened this screen in
its incomplete state at all.

**What now enforces it.** `expectLayoutSanity(page, where)`
(`tests/ui/helpers/designFidelity.ts`) asserts three structural rules against
the rendered DOM: no two sibling notices carrying the same sentence, no
editable control inside a `.kt-meta-value`, no label left standing alone in its
block. `pln-item.spec.ts` calls it on the editor in its incomplete state, and
AGENTS.md §6.6 carries the rule. Verified by reintroducing each defect in the
live DOM: clean page reports nothing, all three are reported the moment they
return.

## The same audit, five more screens (23 Sep 2026)

Offered after U09, not raised as a fresh complaint: the owner said "proceed"
to a sweep of every screen a first text scan flagged for the same class of
primitive misuse. Each one was re-diffed against its own literal artboard
section, not assumed guilty from the scan alone — two of the five it named
(`ClassificationEvidenceScreen.vue`, `departmental_needs/ReasonDialog.vue`,
`departmental_needs/NeedEditorScreen.vue`) had already been reconciled by
same-day earlier commits (`8dafe21e`, `99aa651d`) and needed nothing further.

| Screen | Found against the real board | Fixed |
|---|---|---|
| `ReviewScreen.vue` (U11) | The scope line was still a four-cell facts row (Plan/Plan reference/Version/Current stage) the board replaced with one `kt-page-scope` line in every U11-HOPF/-AO/-STATUTORY/-READER render; the actor's statement notice the board shows right under the header, before any evidence, was missing entirely; the statement and buttons were split across an unstyled `<p>` and a separately-bordered, space-between footer instead of one `kt-decision` block with both buttons clustered at its right edge; U11-COLLECTIVE's required resolution-reference input sat inside the same facts row as "Decision belongs to"/"Recorded by", and U11-LATE-ADOPTION's fact-then-field order was reversed. | `kt-page-scope` line (plus the financial year label, now returned by `get_plan_governance_task`, that no U11 board omits); the statement notice restored; one `kt-decision` block holding both required fields, the statement, the missing-setting panel and the right-clustered buttons. |
| `DppValidationScreen.vue` (U06) | Same split-footer defect as U11: the consequence line and the two decision buttons were a plain `<p>` plus a space-between `pln-footer`, where U06's own board wraps them in one `kt-decision` block, buttons right-clustered. | Same `kt-decision` regrouping. |
| `TreasurySubmissionDialog.vue` (U13) | The board draws U13-TREASURY-FORM and U13-CORRECT-EVIDENCE as full pages (`kt-page`/`kt-page-head`/`h1`), not dialogs — confirmed deliberate by contrast with the same file's own `U13-WITHDRAWAL-REQUEST-DIALOG`/`-DECISION-DIALOG` sections, which *are* drawn as dialogs and which `WithdrawalDialog.vue` correctly matches. Kept as a dialog anyway (every other publication-step action in this app is a dialog over the workspace, and nothing here asked for a navigation-pattern change), but its four core fields were stacked one-per-row where the board runs them on a two-column grid, and the "what's missing" hint sat on its own line below both buttons instead of stacked above the one it explains. | Widened the dialog (640→720px) and laid Date sent/Channel/Destination/Dispatch on a two-column grid; the hint now sits directly above the disabled submit button, both right-aligned. |

**Not fixed, flagged instead.** The same split `<p>` + space-between-`pln-footer`
pattern `kt-decision` now replaces on U06 and U11 still appears on at least
nine other screens (`SourceEvidenceScreen.vue`, `CorrectionRequestsScreen.vue`,
`FinanceTaskScreen.vue`, `PublicationResultScreen.vue`, `DppPlanScreen.vue`,
`EntryFundingPanel.vue`, `PlanItemEditorScreen.vue`, `DppEntryEditorScreen.vue`,
`AnnualPlanScreen.vue`). Each one needs the same treatment only if its *own*
literal board actually draws a `kt-decision` wrapper there — U06 and U11 both
did, but that was confirmed per-screen, not assumed. Worth the same sweep
before the next screen prompts it from a screenshot instead.

**Also found, unrelated, fixed in passing.** `planning-governance.spec.ts`'s
AO-return test still asserted the U11-RETURN lede text a same-day-earlier
commit (`plan_read.py`, "re-diffed 22 Sep 2026") had deliberately replaced;
the test was never updated to match. Corrected to the current, intentional
copy.

**Also found, not fixed — pre-existing, unrelated to this screen.** The
file's first test (Accounting Officer adopts, Statutory approver approves)
fails consistently, on a clean pre-sweep checkout as well as after these
changes: after the Accounting Officer's live adoption, the Statutory
approver's fresh workspace load doesn't show the resulting "Approve the
Annual Procurement Plan" action within the assertion's 5s window, though the
task is created correctly (confirmed directly against the database) and the
same workspace does render it correctly moments later. Bisected by stashing
every file this sweep touched and re-running the identical test against
`HEAD` — same failure, same locator, same line. A timing race in
`WorkspaceScreen`'s "actionable" read after a same-session actor handoff,
not a defect in any screen this pass touched.

## U09 purchase editor — a second pass, from live use (23 Sep 2026)

The owner kept using the screen after the layout re-port above and pointed
out seven more things, this time asking to see the exact artboard section
first. Each was checked against it, not assumed from the screenshots alone.

| # | Reported | Found against `Artboards-U09.dc.html` | Fixed |
|---|---|---|---|
| 1 | "View classification details" shows a different hover colour | Not a defect: `.kt-btn-ghost:hover` background is `--kt-color-accent-100`, `#e5e9fb`, byte-identical to the reference design system's own `.btn-ghost:hover`; text colour is unchanged in both. No code difference found. | Not changed. |
| 2 | Included requirements shows "richer" detail than expected | The board draws each row's need reference, revision and budget line beneath its title in every U09/-READY/-REMOVE section; the editor showed the title alone. The read model already carries `need_reference_line` and `budget_line_display` — nothing new to compute. | Sub-line added (`pln-row-ref`, already a defined class); title given the board's own `font-weight:600`. |
| 3 | "View calculated dates" looked like it did nothing | It is real in the board (`#U09` → `Read full basis`-style placeholder, an artboard-tool convention, not an instruction to make it inert) and already opened Supporting details — but never scrolled to it, so clicking it while the section was off-screen looked like a dead link. | Opens Supporting details and scrolls the calculated-dates table into view. |
| 4 | "Remove purchase" looked different from other destructive buttons | Confirmed, and isolated: the board's own footer button is `btn-danger` (solid fill, white text) exactly like `DissolveItemDialog.vue`'s already-correct confirm button; this screen's own button used the outlined `kt-btn-secondary kt-danger` instead — the treatment two other danger buttons in Needs/Planning correctly use for a *choice among options* (Decline vs Approve), not for a standalone action that opens its own confirmation. One misapplied instance, not a systemic gap. | `kt-btn-secondary` → `kt-btn-primary`. |
| 5 | "Supporting document" isn't in the design, meaning unclear | True — no generated U09 state draws it as an editable field, only the spec's own §12 prose ("Supporting document … only when an actual accessible record exists") and the required-before-submission contract table. Genuinely required (`estimate_basis_reference`, `PLN_PLAN_CONTENTS_INCOMPLETE` if empty), so removing it was not an option; its meaning was the actual gap. | Relabelled "Supporting document reference"; the spec's own words ("an identifiable market-survey document or working-paper reference — not a file upload") now sit in the placeholder, not a permanent line. |
| 6 | Field hints are inconsistent and make the form busy by default | Confirmed: no generated U09 state shows a hint under Estimate basis or Expected delivery period at all. | Estimate basis's generic hint removed outright. Expected delivery period's hint stayed — it disambiguates a bare number input, not a generic instruction, and the fidelity gate confirmed the alternative (folding the unit into the label text) breaks the board's own exact label landmark. |
| 7 | Mandatory fields keep their red border after the field is filled in | Confirmed, general: `flagged(field)` reads the server's `blockers` list, current only as of the last load; nothing cleared it before the next save re-derived it, so a field the Planner had just filled in still read as broken. Re-validating client-side was not an option (duplicates server business logic `AGENTS.md` already forbids — `procurement_method`'s own flag depends on a rule lookup no browser can do). | The flag now also requires the field's current draft value to still equal what was loaded; editing a flagged field drops the highlight immediately, and the next save is what actually confirms it. |

**Also acted on, raised as a follow-on to (7).** However many purchases and
rule kinds are unresolved at once, every `MissingSettingPanel` rendered
full-size, so two already read as a wall of amber and the owner asked what
five would look like — correctly: it would dominate the screen. No board
draws more than one C03/C04 panel at a time, so there was nothing to port
literally; `MissingSettingGroup.vue` is new — a single panel renders exactly
as before, two or more collapse to one closed-by-default summary line ("N
settings need administrator attention") that opens to the same panels.
Wired into both places this can happen: the item editor's own pair, and the
Annual Plan's per-purchase list (`AnnualPlanScreen.vue`), where several
purchases missing a rule is the more likely way to actually reach five.

Verified live on the reported purchase (PPI-MOH-2027-001), against
`PlanItemEditorScreen.spec.js` (27 tests), the new `MissingSettingGroup.spec.js`
(5), the full planning vitest suite (291), and live U07/U09/U09-INVALID-
SCHEDULE/U09-REMOVE fidelity plus the full `pln-item.spec.ts` browser suite (13
Playwright, all green).

## Annual Plan preparation: "the plan looks finished, what's next?" (23 Sep 2026)

Raised live, then followed up twice more as the story turned out to run
deeper than the first fix reached. A Planner looking at a two-purchase plan,
both purchases showing "Current work: Choose a strategic objective" and
every Plan check clear, saw no Send to Finance button and no explanation —
only Save draft. `Artboards-U07-U08.dc.html`'s own fixture note on the base
U07 board says plainly "Send to Finance is absent while a blocking check
fails," and that is correct, intended behaviour; the board's own answer to
"why" is the per-purchase Current work column plus Plan checks' own
notices, nothing more. Three real gaps sat underneath the report, found in
this order:

1. **No plan-level sentence ties "purchases still have current work" to "so
   Send to Finance is absent."** Reserved-procurement and schedule failures
   already get their own notice-and-action in Plan checks; an incomplete
   purchase's own gap (Strategy, method, dates, …) never did. First placed
   in the footer, next to the missing button — but a footer sentence that
   just said "shown above" needed the reader to scroll back up past
   Requirements, Plan checks and Changes and history to see what it meant,
   which is its own report ("I still don't understand — which work?").
   Moved beside the Purchases table itself, where its own Current work
   column is read from: "N of the purchases above must show Ready in
   Current work — open it from Action to complete it — before this plan can
   be sent to Finance for funding review."
2. **A real backend bug in `get_plan_item`, found while checking the
   first.** It read an unset Strategy as vacuously eligible
   (`objective_eligible = (not item.strategic_objective) or …`) — so a
   purchase actually missing it carried no blocker and no flagged field on
   its own editor page, though `plan_readiness` (the function
   `get_plan_item`'s own comment says it mirrors) already read the same
   unset value as *not* eligible. Both reads now use the same rule: unset
   is not eligible, only a chosen objective still in the eligible set (or
   any chosen one once the version is Active) is. `PlanItemEditorScreen.vue`'s
   Supporting details — the one place Strategy lives, closed by default —
   now opens by default too when this is what's blocking the purchase.
3. **The real bug, in `_item_rows` (`get_annual_plan`'s own item-list
   query), found from "why does it still say this for an item I just gave
   an objective to?"** `frappe.get_all`'s explicit `fields=[...]` list
   never included `strategic_objective`, `baseline_invitation_date` or
   `estimate_basis` — so `_current_work` (which checks exactly those three
   in sequence) read every one of them as unset regardless of the real
   value, for every purchase on every plan, the moment method and
   reservation were both chosen. That is why it never agreed with the
   editor, which reads the whole document: not "indirection" as a design
   choice, a missing-fields bug in one query. Fixed by adding the three
   fields. A save with every field complete now reads Ready in both places
   (new test), and the two purchases on the reported plan both correctly
   read Ready once this landed, with nothing further needed on either.

**Also fixed, self-inflicted.** Wrapping the table and item (2)'s notice
under one `v-if="items.length"` needs a `<template>`, not just the table —
`v-else` binds to the *nearest* preceding `v-if`, and putting the notice
between the table and the original `<div v-else>` silently re-paired that
`v-else` with the notice's own `v-if="incompleteItems.length"` instead. Two
Ready purchases then rendered correctly *and* "No purchases have been added
yet." underneath them, simultaneously — caught from a screenshot seconds
after building it, since no existing test asserted the empty-state message's
*absence*. Fixed, and a test now asserts both the table and its rows render
and the empty state does not, whenever there are items.

**Also found, unrelated — an environment note, not a defect.** Running
`pln-annual-plan.spec.ts` and `pln-item.spec.ts` together in one Playwright
invocation failed with the masked-NameError symptom
[[playwright-test-server-runs-unannounced]] already documents; each file
alone passed cleanly (6/6, then 7/7) both times. Not investigated further
per that memory's own guidance — logged there, not here.

Verified against `test_plan_workbench.py` (38, including a save-everything
regression for finding 3), the full planning vitest suite (294), live on
the reported plan and both its purchases (`current_work` now reads `Ready`
for both, `can_request_funding` is `True`, confirmed directly against the
database and in the browser), and U07/U09/U09-INVALID-SCHEDULE/U09-REMOVE
fidelity plus the full `pln-annual-plan.spec.ts` and `pln-item.spec.ts`
browser suites, each run alone (13 Playwright, all green).

## U09's missing-setting panel: named, ordered, and told apart (23 Sep 2026)

Raised live: a Planner picked Open Tender, saved, and on the next load found
the Procurement method dropdown empty and two identically-styled amber
panels. All three symptoms trace to one thing, none of them a code defect
in the choice itself — the applicability date the method-eligibility rule is
checked against comes from the purchase's own Target invitation date once
one is set, falling back to the plan's fiscal-year start until then; filling
in Dates *after* Procurement approach (the form's own field order) can
retroactively invalidate an already-saved, already-valid choice. That is
correct, load-bearing behaviour — a method genuinely can stop being
admissible when its applicable date changes — but the panel that explains it
was porting `C01`/`C02`/`C04` faithfully while missing what `C03-METHOD-
MISSING`'s own board draws differently:

| Found against the real C03 board | Fixed |
|---|---|
| No leading sentence. C03 alone opens with one naming the exact blocked choice ("Open Tender cannot be confirmed until the applicable method rule is verified in System setup."); `MissingSettingPanel.vue` had no such line for any variant. | Optional `lede`, rendered only when a caller sets it; `item_procurement_rules()` sets it for the method variant only, matching C03; C01/C02/C04 stay exactly as drawn. |
| Panel placement. The board states the blocked setting *before* the field it blocks; the editor rendered every missing-setting panel after the entire Procurement approach grid, including fields the panel had nothing to do with. | Moved directly under the section heading, before the field grid. |
| Stacked panels touch with no gap anywhere in the app — found here with two, but every `v-for` over `.kt-notice` (issues, corrections, missing settings) has the same gap. | One rule in the shared `kt-industry` tokens: adjacent `.kt-notice` siblings get `margin-top`. Fixes this for every screen that stacks notices, not only this one. |

Answers the "what if 5 issues occur" question the same way: each panel
already carries its own setting/purchase/action facts, so scaling was never
about consolidating them into one block — it was that two of them read as
one repeated block with no lede to tell them apart. With a name and a gap,
N of them read as N distinct things.

Verified live (`http://127.0.0.1:8000` — `kentender.midas.com` was not
resolving this session; the dev site's own `/etc/hosts` entry appears to
have been dropped, most likely by a WSL restart regenerating the file) as
Mercy Kilonzo on the actual purchase from the report, and against
`test_missing_setting.py` (13 Python), `MissingSettingPanel.spec.js` (6),
`PlanItemEditorScreen.spec.js` (24), and the live U09 fidelity and
`pln-item.spec.ts` suites (10 Playwright, including `expectLayoutSanity`).


## Correction, 24 September 2026 — the exemption constants named above no longer exist

FU-V123-01, FU-V123-05 and FU-V123-07 each point at a named landmark exemption in `planning-fidelity.spec.ts` as the mechanism keeping the departure honest: `U14_EXECUTION_COLUMNS`, `U11_DECISION_TABLE`, `U09_SCHEDULE_LABELS`, `U09_REMOVE_ACTION`. None of the four is in that file, or anywhere else in the repository. They were lost in the v1.23 to v1.24 rewrite of the spec, and the loss was not noticed because nothing checks that a register entry still has an implementation.

Departures are now recorded in `tests/ui/fidelity/departures/<module>.js`, where a stale entry fails the gate rather than sitting in a document. The rows above stand as history; the mechanism they describe does not.

## v1.27 workflow-guidance cycle (25 Sep 2026)

| ID | Follow-up | Owner decision needed |
|---|---|---|
| FU-V127-01 | **Planning instants display three hours ahead — closed 26 Sep 2026.** Planning's reads converted stored instants from UTC while its commands wrote site time, so every command-written time read +3h; seeded instants were UTC. A survey of every app found all other modules store and show site time (Frappe's own rule). **Owner decision 26 Sep 2026:** store instants in the site timezone, show them as stored, and use ISO-8601 UTC only in serialized messages between modules. **Built:** Planning's three formatters use core `display_datetime`; the budget-revision request stores site time and converts Budget's UTC outcome back; one pair of core helpers (`kentender_core.utils.instants.to_utc_iso` / `from_utc_iso`) replaces the hand-written conversions in Budget's outcome and Planning's REQ outcome, and now also serves the Tenders and Departmental Needs event payloads (Tenders' `occurred_at_utc` held site time); Tender Management's audit fallback no longer writes `utcnow()`; the Planning seed clock, the core DPP/disposal intake closing times and the Planning/Requisitions browser fixtures state site time; two one-off patches moved the already-stored UTC rows (exact seeded values only, and budget revision requests only where the stored time sits three hours behind the row's own creation). The rule is in AGENTS.md §4.4. | Yes, at KT-STD-001's next version: §3 "Service and audit instants remain UTC" to read "stored in the site timezone; ISO-8601 UTC in messages between modules" (and the same in PLN §4 / NDS / CFG / BUD §6 wording). |
| FU-V127-02 | Budget has no test module of its own for the revision request (BUD v1.11 §16.4) — **closed 26 Sep 2026**: `kentender_budget/tests/test_bud_chg_001_v111_revision_request.py`, 11 tests covering BUD21-AC-001 to 008 from Budget's side alone (receipt, not-required/stale, successor link, Revised on activation, decline/withdraw/closure, outbox retry and order, who sees the row). | No. |
| FU-V127-03 | **The holder of a budget revision request was told to wait for themselves (fixed; spec correction owed).** Found live 25 Sep 2026 by the owner: Josphat Mwangi (Finance Confirmation Officer *and* Budget Officer) opened PLN-MOH-2027-001 V2 while it waited on his own request and read "Waiting for Josphat Mwangi (Budget Officer) to revise the budget line", with no way to act, beside a tracker reading "Preparation — Blocked · Mercy Kilonzo". Two spec gaps: §5.7 (row "Open budget revision request; line still over") gives the Budget Officer's turn to BUD only and never considers a Budget Officer who can also read the plan; U07-WAITING-BUDGET-REVISION draws the tracker holder as the Planner although the line names the Budget Officer. **Built:** a Budget Officer reading the plan in that state gets *Your turn — Revise {line} for the plan update* with **Open the request in Budget & Funding** on the line (a route fix; `NextStep.vue` now draws a Your-turn route fix as a link on the head line); every reader's tracker names the Budget Officer(s) as holder of the blocked Preparation stage. Budget's Fiscal Year filter now honours a year passed in the link (`route_options.fiscal_year`), which Budget's own My Work row already sent but the workspace ignored. Guarded by two new dead-end matrix rules — *no reader is told to wait for themselves*; *a Your turn must offer an action or a way to act* (core `next_step.problems`) — and two dual-role matrix readers (Finance + Budget Officer; Planner + Finance). | Yes, at the next PLN version: amend §5.7 and U07-WAITING-BUDGET-REVISION (tracker holder = Budget Officer; the Budget Officer reading the plan = Your turn with the route to BUD). |
| FU-V127-04 | **A declined budget revision left the Planner with no explanation (fixed; spec correction owed).** Found live 25 Sep 2026 by the owner: after Josphat Mwangi declined Mercy's request, U07 and U01 read exactly as before she asked; the decline and its reason appeared only as the stage text of a "Continue plan update" My Work item (whose Received time was the Draft's last change, not the decline). The spec asks for no more — §4.7 keeps only the outcome instant, §7.7 says "Continue plan update, with the outcome", and no U07/U01 variant draws the declined state. **Built:** the over-budget blocker of a line whose latest request was declined carries two facts — *Budget revision: Declined by {name} on {instant}* and *Reason: {reason}* — leads with **Reduce a purchase** and offers **Request budget revision again from {name}**; the U01 row states *Budget revision declined by {name}: {reason}* under the blocked headline; the My Work item is received at the decline instant. `NextStep.vue` now keeps a blocker's facts in the several-blockers list too. A new request replaces the explanation with the Waiting line. | Yes, at the next PLN version: add a U07-BUDGET-REVISION-DECLINED variant (and the U01 row line) to §10 and the boards, and the reason to §4.7's record. |
| FU-V127-05 | **The departmental correction route replaces "Reduce a purchase" (built; spec correction owed).** Found live 26 Sep 2026 by the owner: "Reduce a purchase" pointed the Planner at the purchase editor, which locks the cost (a purchase's value is copied from the departments' accepted requirements, §4.6 "no source/quantity/value override"), and removing a purchase only leaves its requirement to be re-added. **Owner decision 26 Sep 2026 — built:** an over-budget line offers two recovery paths, **Request budget revision from {Budget Officer}** and **Request departmental plan update from {department}** (one per department whose requirements make up the line, named in a "Requirements on this line" fact). The new `Departmental Plan Update Request` record and `RequestDepartmentalPlanUpdate` command hand the line to the department: its authors and Head of Department get a My Work item and, on their accepted plan, *Your turn — Update this plan as Procurement asked* with a notice naming the line, the amount and the three choices (correct the estimate, change the requirement, or mark it Do not proceed this financial year), through the existing departmental update, certification and acceptance. The Planner waits on the department by name (tracker and My Work waiting item). Procurement's acceptance of the update answers the request; the existing source-correction rule then asks the Planner to rebuild the purchase. After Budget declines, its reason shows and the departmental path leads; a new budget request is offered and accepted only on a new basis (the line's approved or planned amount changed since the decline — `PLN_BUDGET_REVISION_ALREADY_DECLINED` otherwise). Sending the plan to Finance or cancelling the update withdraws open requests of both kinds (cancel did not withdraw a budget revision request before). New errors: `PLN_DEPARTMENTAL_UPDATE_NOT_REQUIRED`, `PLN_DEPARTMENTAL_UPDATE_ALREADY_REQUESTED`, `PLN_BUDGET_REVISION_ALREADY_DECLINED`. Supersedes the "Reduce a purchase" part of FU-V127-04. | Yes, at the next PLN version: §4 record, §7.2 command, §7.7 hand-off row, §8 errors, §5.7 rows for waiting on a department, §10 U07/U01/U02 variants (departmental fix, waiting on department, declined state, the department's request notice), §11.9 action map; and the matching NDS/DPP wording for the department's notice. |
| FU-V127-06 | **Named-user pass, 26 Sep 2026 (live PLN-MOH-2027-001 V2, stopped after Finance confirmation as the owner asked).** Mercy → Human Resources Management and Development asked to update its plan → Grace marked "testing requisitions" Do not proceed this financial year → Dr Peter Kimani certified and submitted → Mercy accepted, rebuilt the purchase and sent the update to Finance → Josphat Mwangi confirmed funding → Mercy now waits on Charles Mutiso to sign (not signed). Every screen's next step and tracker agreed; times read as Nairobi time; no console errors. **Fixed during the pass:** (a) every departmental holder lookup (`next_step.ou_holders`) matched no one — an SQL `NOT IN ('', NULL)` filter — so department steps named the role, never the people; (b) after the department's update was accepted, the over-budget block still offered requests to both departments while a purchase awaited rebuild — it now says "Rebuild the purchase first: the department's update changes this line's total", and the rebuild block names the purchase ("Rebuild testing requisitions from the department's updated plan"); (c) My Work "Received" showed raw timestamps for task items (Finance, signature, departmental review) — now formatted. **Still open:** (1) the Remove purchase dialog says the requirements "will return to this draft plan", untrue when the department has excluded one (needs a per-source fact from the server); (2) on a departmental update, Procurement must re-classify unchanged requirements from blank — the previous accepted classification is not offered; (3) with two departments behind one over line, asking one puts the Planner into Waiting and the other department's button disappears; (4) on the department's accepted plan with an open request, the tracker shows every stage Done beside "Your turn — Update this plan as Procurement asked". | (1)–(3) yes: small product decisions (is prefilling a prior classification allowed; may the Planner ask a second department while the first is working). (4) no — presentation only. |
