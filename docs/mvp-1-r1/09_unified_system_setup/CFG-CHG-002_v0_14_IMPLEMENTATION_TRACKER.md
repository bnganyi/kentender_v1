# CFG-CHG-002 v0.14 — System setup — tracker

**Authority:** `KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_14.md` (approved 24 September 2026; supersedes v0.13 in full). Shared standard KT-STD-001 v1.7; authority baseline AUTH-ADR-001 v1.9.
**Companions:** `CFG-CHG-002_v0_14_Implementation_Plan.md` (rules, phases, verification), `FOLLOW_UPS.md`, design `design/*.dc.html`.
**Predecessor:** `CFG-CHG-002_IMPLEMENTATION_TRACKER.md` (v0.11 cycle, 16 September 2026), kept as history. Its decisions D1–D10 stand. Its acceptance claims are **not** carried forward as Done: every one is re-audited against v0.14 and the stronger UI definition of done in the plan.
**Status:** Phases 0–3 done 24 September 2026 (two owner questions open, Q1–Q2); Phase 4 next.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done` / `Re-audit` / `Deferred`. Reversed decisions are struck through in place.
2. `Done` needs the row's own evidence: a command with result counts, a named test, or a browser observation with the literal rendered strings. Never record a result that was not observed.
3. A screen row is `Done` only when every item of the plan's UI definition of done is green: component tests, structural fidelity (listed in `COVERED`, component fidelity spec, `ui-structure-gate`), browser journey, browser fidelity, accessibility evidence, live click-through as Administrator and System Manager.
4. `Re-audit` means the v0.11 cycle claimed it; the claim is proved again under v0.14 before it becomes `Done`.
5. No alias, redirect, dual-write, compatibility shim or parallel surface. No setup approval stage.
6. Never run the Python suite while a System setup Playwright process is active on the site.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-16 | D1–D10 (v0.11 tracker) | Retained unchanged: generic Set/Version/VerificationEvent envelope, JSON-validated typed payloads, Method eligibility delegated to `Procedure Method Profile`, no data migration. |
| 2026-09-24 | **D11 Tender formats deferred.** Nothing Tender-format related is built this cycle: no `/tender-formats` route, no §4.11 projection, no change to `TENDER_RENDERABLE_RESERVATION_CATEGORIES`. The "Tender formats" link drawn in every board's section row is a registered departure, not built. | Owner choice. The Tender-template owner has no read projection, review pack, blockers or approval facts, and STD-TPL-001 v0.7 / TPR-CHG-001 v0.9 are not in the repo. Prerequisites in `FOLLOW_UPS.md` FU-18. |
| 2026-09-24 | **D12 Routing: hash-aware shared adapter.** Keep the spec's `#tab/section/id[/versions/id]` links; read them through a `useRouteState` adapter over `kentender_core.desk_page.useRoute`; delete `SystemSetup.vue`'s own `hashchange` listener. | Owner choice. Satisfies spec §9 exactly while removing the hand-rolled routing behind the flash and stale-screen defects (AGENTS.md §6.4). |
| 2026-09-24 | **D13 Re-port every screen from its board.** No component is kept because it "works"; each is re-derived class-for-class from the current board and gated structurally. Keeping one unchanged is a recorded departure. | Owner choice. The v0.11 screens were only ever checked by the text-order gate, which cannot see containers. |
| 2026-09-24 | **D14 Boards completed before code.** Missing states in the spec's artboard inventory are authored into the CFG boards (Phase 0); AUTH-owned boards are not edited here. | A design-tool export can drop states; closed-input rule forbids inventing them in Vue. AUTH owns its compositions (spec §10.1 exception). |
| 2026-09-24 | **D15 In-place correction kept** (answers Q1). An unused, unchecked, not-yet-effective version may be corrected in place through its command (owner decision 23 Sep 2026, `configuration_versions.version_editable`); anything used, source-checked or in force needs a new version. A named exception to v0.14 §4.6 "every saved version is immutable". | Owner choice, 24 Sep 2026. |
| 2026-09-24 | **D16 Undeclared overlaps refused** (answers Q2). Saving any rule, method, schedule or calendar version — new or corrected in place — whose dates overlap an Active version of the same record must name it; otherwise `CFG_SUPERSESSION_INVALID`, checked before any write. A declared version must actually overlap. | Owner choice, 24 Sep 2026; follows v0.14 §5. |

## Risks

| # | Risk | Handling |
|---|---|---|
| R1 | Structural gate on System setup turns up many failures at once. | Expected — that list *is* the Phase 5 work queue (plan Phase 1). |
| R2 | Changing the reservation `denominator_basis` vocabulary breaks a consumer. | Grep all callers first; Planning's `readiness.reservation_allocations` ignores the field today. Run Planning's focused tests after 3a. |
| R3 | Making idempotency keys required breaks callers that omit them. | Grep every caller of `run_idempotent` and the CFG APIs (UI, seeds, fixtures, other apps) before 3b. |
| R4 | Porting the `.kt-meta-row` grid fix into shared tokens changes other modules. | Run the other modules' structure and fidelity gates after the change; Planning has local overrides to reconcile. |
| R5 | `ui-industry-design-gate` Python half fails on the site's fiscal-year overlap (pre-existing). | Record, don't chase; purge `_Test Fiscal Year` residue. |
| R6 | AUTH v1.9 boards (Scheduled edit, missing-root variants) are not in the repo. | 5H verifies against AUTH v1.9 §13 text plus the existing AUTH boards; gap recorded as FU-19. |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| CFG14-G00 | Plan, tracker, follow-ups; boards diffed and completed; committed | **Done** 2026-09-24 | CFG14-001–006 |
| CFG14-G01 | Enforcement wired; red list recorded; other modules' gates still green | **Done** 2026-09-24 | CFG14-101–109; `ui-structure-gate` 595 passed; System setup fidelity 17, access 5, fiscal years 3, entity 1 passed; procurement-settings 3 of 4 — the 4th is pre-existing finding F2 |
| CFG14-G02 | Shared routing runtime; route specs green | **Done** 2026-09-24 | CFG14-201–204. System setup component suite 189; structure gate 609 + 35; browser: routing 5, access 5, fiscal years 3, entity 1, fidelity 17 (after rebuild), procurement settings 3 of 4 (F2, pre-existing) |
| CFG14-G03 | Domain deltas 3a–3f green; cross-app callers green; canonical seed validates | **Done except canonical validation** 2026-09-24 | 3a–3f green; Planning callers green; structure gate 617 + 35; System setup browser fidelity 17, routing 5, procurement settings 3 of 4 (F2). Canonical validation fails for pre-existing reasons (FU-23), not from this phase |
| CFG14-G04 | Fixture worlds idempotent and purge clean | Planned | |
| CFG14-G05 | Every screen meets the UI definition of done; per-screen gates green | Planned | |
| CFG14-G06 | Release evidence; acceptance map complete with evidence or named gap | Planned | |

## Phase rows

### Phase 0 — docs and boards

| ID | Item | Status | Evidence |
|---|---|---|---|
| CFG14-001 | v0.14 plan + this tracker in repo | Done | `CFG-CHG-002_v0_14_Implementation_Plan.md`, this document |
| CFG14-002 | Record D11–D14 | Done | Decision log above |
| CFG14-003 | `FOLLOW_UPS.md` updated (FU-18 Tender formats, FU-19 AUTH v1.9 boards, FU-20 LAW v1.2 status, FU-21 resolver-caller migration) | Done | `FOLLOW_UPS.md` |
| CFG14-004 | Diff the refreshed boards against HEAD for dropped states | Done | Every removed line was a replacement, not a dropped state: reservation "Annual procurement budget/value" → Measure + fixed "Eligible value of the current Annual Plan"; published-prices placeholder → table; schedule list and interval table reformatted (Minimum/Maximum days columns added); funding disabled specimen moved into its own table beside a new Edit dialog. |
| CFG14-005 | Audit boards against the spec's artboard inventory; author missing CFG states | Done | See "Board audit" below |
| CFG14-006 | Commit docs and boards | Done | Commit "docs(system-setup): CFG-CHG-002 v0.14 plan, tracker and completed boards" |

#### Board audit (CFG14-005)

| Board | Gap found | Change |
|---|---|---|
| C01 | "Site details saved" / "Site configured" notices carried prose annotations inside the notice body | Annotation moved to a kicker; notice bodies now carry only the spec copy |
| C02 | "No closing date" and scheduled-expiry rows were prose only; no disabled-year list row; no narrow-width year card | Added `#detail-row-variants` (two rendered rows), `#overview-disabled` (Include disabled years ticked, disabled FY row), `#narrow` (390 px year card with all three activities) |
| C03BC | Exclusive preference, Preference margins, Approval applicability and Publication obligations drew merged read-only summaries (`.kt-meta-row`) instead of editors; several spec fields absent (Comparison, origin conditions, bound-included flags, Due rule, Days, date basis, integration requirement, source references) | All four rebuilt field-by-field in `.field` controls with every §10.7 label; notices as `.kt-notice` with icon |
| C04 | Working-day calendar merged the unsaved editor with saved-detail actions; no saved detail, successor or history state | Split into `#calendar` (editor with holiday table + Add row), `#calendar-detail` (read-only, Create new version / Check sources / View usage and history), `#calendar-version` (Earlier versions this replaces + Reason for change), `#calendar-history` (version, source-check and usage tables) |
| Common | No CFG board for Loading, Forbidden or Load error | New `Common-States.dc.html` (`#loading`, `#denied`, `#load-error`); nothing of the page paints behind them |
| C03A, C03D, Reminders | None | — |
| AUTH-owned | No v1.9 board for Edit scheduled assignment or missing-root variants | Not edited (AUTH owns them) — FU-19 |

### Phase 1 — enforcement first

| ID | Item | Status | Evidence |
|---|---|---|---|
| CFG14-101 | `tests/ui/fidelity/departures/system-setup.js` | Done | `DEPARTURES` (empty), `COVERED` (empty — nothing re-ported yet), `REBUILD_QUEUE` (all 46 artboards), `LANDMARK_DRIFT` (3). Keys are `Board#artboard`. |
| CFG14-102 | Board scope/resolver for id'd `div` artboards in `tests/ui/fidelity/board.js` | Done | `setupSkeleton(file, selector, {self})` (a dialog artboard keeps itself as a landmark) and `setupArtboardIds(file)` (every id except `aria-labelledby`/`label[for]` targets). No resolver needed: no CFG board uses `sc-if`/`sc-for`. C03A and Reminders boards given stable artboard ids. |
| CFG14-103 | Component `system-setup.fidelity.spec.js`, one case per artboard | Done | 48 tests: an inventory test (every drawn artboard has an entry; none extra), a COVERED/queue completeness test, and one comparison per artboard. 6 artboards mountable from props today (C01 configured/first-run, C02 add-year, C03A add/edit, Reminders unchanged) — all 6 differ from their boards; 40 have no props-driven component yet. Rot rule: a queued artboard that matches FAILS. |
| CFG14-104 | `ui-structure-gate` runs `--project system-setup` | Done | `make ui-structure-gate`: 35 + 560 passed. |
| CFG14-105 | Test that every board-backed component is in its module's `COVERED` | Done — reversed direction | `tests/ui/fidelity/covered.spec.js`: every `COVERED` entry in every registry must be named by a spec that imports that registry AND runs a structural comparison. Found Budget's three screens named by board label (`BUD-DES-02/03/06`) — made explicit via `COVERED_AS` in `departures/budget.js`. The "every board-backed component is listed" direction is enforced for System setup by its inventory test; other modules' component headers are too inconsistent to derive it (recorded, not claimed). |
| CFG14-106 | Browser fidelity spec: `expectStructure` + `expectLayoutSanity`; remove false geometry claim | Done | All 17 browser tests now compare structure (live `.kt-setup-panel` / `.kt-dialog` vs the board scope) with the same queue rule, and 9 editor states call `expectLayoutSanity`. Header no longer claims geometry. `make ui-system-setup-fidelity-gate`: 17 passed. |
| CFG14-107 | `system-setup-pe-stale-save.spec.ts` in a gate | Done | New `make ui-system-setup-entity-gate`. **Found:** the spec renamed the live entity and never restored it — it now reads the original name first and restores it through the UI; verified the site ends as "Ministry of Health". |
| CFG14-108 | `.kt-meta-row` grid + `.is-tight` in shared tokens; other modules re-checked | Done — scoped | Only 3 of 11 design bundles carry the grid (Departmental Needs, Planning, System setup); 8 (Budget, Strategy, Tenders…) still draw flex, so a global change would move their screens off their boards unasked. Grid applied under `.kt-setup-root` in `kt_admin_configuration.css`; `.is-tight` added globally (no-op today). Verified live: computed `display: grid`, stylesheet `?v=` refreshed. Global adoption is FU-22. |
| CFG14-109 | Record the red list | Done | All 46 CFG artboards queued (0 covered). Structural drift seen at component level, e.g. C01: page content wrapped in an extra `card+blueprint`, `h3`/`field`/`card-title`/`meta-row`/`notice.is-live` missing; C03A editors render a card, not a dialog; dialogs add `corner`s and an `h2`. Words drift (`LANDMARK_DRIFT`): C04 calendar Holidays table, C04 interval Minimum/Maximum days columns, and C02 detail (fixture — see findings). |

#### Phase 1 findings

| # | Finding | Disposition |
|---|---|---|
| F1 | The Procuring entity approval status used invented labels ("No rule in force", "Rule in force, not source-checked") and explanations, added by the seed fix `e2831468`; its own component test had been red since. | Fixed test-first to the spec wording: "Source check needed" for a rule in force but unchecked, "No rule covers this date" for none, and the §10.2 sentence for both. System setup component suite 145 passed. |
| F2 | `format.js` maps the fixture-verification status to an invented label "Fixture data — not law"; on the canonical (fixture-verified) site `procurement-settings.spec.ts` expects "Source check needed" and fails. Pre-existing; not caused by this cycle. | Phase 5D: status labels come only from spec §8.1; the spec's state world comes from the Phase 4 fixtures, not the canonical seed. |
| F3 | `system-setup-pe-stale-save.spec.ts` was in no gate and left the live entity renamed. | Fixed (CFG14-107). |
| F4 | The canonical seed opens disposal-plan submissions (SEED-OPS v1.8), while the CONFIG world draws them closed, so the C02 detail's words differ on the canonical site. | `LANDMARK_DRIFT["C02#detail"]` until the Phase 4 CONFIG world is used. |

### Phase 2 — shared routing runtime

| ID | Item | Status | Evidence |
|---|---|---|---|
| CFG14-201 | Hash-aware `useRouteState` over `desk_page.useRoute` | Done | The shared runtime gained an opt-in hash mode (`useRoute(vue, slug, {hash:true})` → `hash`, `goHash(fragment, {replace})`), so the fragment is followed by the one core listener with the same pause/resume rules; path-routed pages unchanged. First tests for the runtime itself: `kt_desk_page.spec.js` (5, new `desk-runtime` vitest project, in `ui-structure-gate`). `system_setup/composables/useRouteState.js` maps it onto the §9 grammar; `onSetupRevalidate` gives tabs quiet re-reads on return. Budget workspace + access browser specs re-run green (8) as a regression check on the changed runtime. |
| CFG14-202 | `SystemSetup.vue` rewired | Done | No `hashchange` listener; tabs in `KeepAlive` via one dynamic component; skeleton only while there is no site yet; every read sequence-guarded; the address corrected in place (replace, no Back step) when a link names a missing or refused tab. `SystemSetup.spec.js` (9) mounts the root on the REAL runtime. Quiet revalidation on Financial years, Procurement settings and Responsibilities; Organisation structure still reloads visibly (its `load` has no quiet mode) — left to its 5H re-port. |
| CFG14-203 | Spec §9 section keys replace ad hoc sub-paths; first-incomplete-tab default; dead `navigate("procurement-rules")` fixed | Done | `data/routes.js` (34 tests): `#procurement-settings/{funding-sources,procurement-rules,schedule-profiles,reminders,calendars}/{id}[/versions/{vid}][/new-version\|edit\|check-sources]`, `…/new`, `#fiscal-years/{fy}`; per-segment encoding. Tabs keep their older view names through a tested translator until Phase 5. Default: first run → entity, missing root → organisation structure. "View procurement rules" now opens the list at that section. Browser specs moved to the new links; cross-app links use tab anchors only (Planning `missing_setting.py`) — unaffected. |
| CFG14-204 | Route vitest + Playwright route spec | Done | `system-setup-routing.spec.ts` 5 passed: all five tabs survive direct load + reload with the address naming the tab; no-link lands on entity with no Back step; Back/Forward walk tab clicks and a MutationObserver counts **0** skeleton insertions on return; a rule link survives reload and Back returns to the list; the section link scrolls into view. Added to `ui-system-setup-access-gate`. |

#### Phase 2 findings

| # | Finding | Disposition |
|---|---|---|
| F5 | Two regressions this phase introduced were caught before commit: (a) routing every tab's `navigate` to the current tab broke the Procuring entity's cross-tab "View procurement rules" (caught by the new browser spec); (b) on a direct load of a method rule's new-version link, the tab treated the rule as a reference rule before its list arrived and the server refused the lookup (caught by the fidelity spec's console check). | Both fixed test-first with component regression tests. |
| F6 | `FIXTURE_PENDING` added to the System setup registry: C02 detail's words depend on whichever seed or spec last touched disposal-plan submissions, so it can neither be required to match nor to differ. Text comparison skipped; structure still compared. | Removed when the Phase 4 CONFIG world exists (CFG14-401). |
| F7 | The dev site is not canonical, independently of this cycle: `make seed-canonical THROUGH=tenders` fails validation (NDS-MOH-2027-0002 is "Accepted for planning", expected Submitted; Requisition reservations 0), and a `rebuild` fails on a missing Budget reservation (`Reservation 4pfc7sdk5g not found`). Both runs rolled back; nothing changed. The site also carries Tenders/Planning/test-suite residue. | Not CFG's to fix; FOLLOW_UPS FU-23. System setup's own spec runs were purged after each run. |

### Phase 3 — domain deltas

| ID | Item | Status | Evidence |
|---|---|---|---|
| CFG14-301 | 3a Reservation `measure_stage` + new `denominator_basis`; old values refused; seed updated | Done — `570b6cdc` | Validator requires `measure_stage` (PlanningAllocation / ImplementationAchievement) and derives the denominator (EligibleCurrentAPPValue / ApplicableActualProcurementValue); retired budget-based values and mismatched pairs refused (CFG_SCHEMA_UNSUPPORTED). Planning read selects the planning-stage rule and returns measure + basis. Seed writes the measure and replaces an old-shape rule with a corrected successor; editor asks for Measure and shows Measured against read-only. test_regulatory_reference 29 OK; Planning test_plan_workbench 45 + test_plan_governance 38 OK; vitest 190. |
| CFG14-302 | 3b Idempotency payload hash → `CFG_IDEMPOTENCY_CONFLICT` | Done — `6eed5e1f` | Journal gains `payload_hash`; `run_idempotent(..., payload=)` refuses same key/different content; all 14 CFG commands pass `request_payload(locals())`; legacy reference-data and STD-configuration callers unchanged. test_cfg_idempotency 4 OK. **Not done:** making the key required at the API layer, and the screens reusing the original key on an ambiguous retry (they mint a new key per attempt) — Phase 5D (§7.3). |
| CFG14-303 | 3c `preview_configuration_version` | Done — `bc86e35b` | Read-only: schema defects as data (no Frappe pop-up), missing legal details, overlaps each marked declared/undeclared, replacement blocking new use, usage reported unknown (FU-15). Whitelisted API. test_cfg_preview 9 OK. |
| CFG14-304 | 3d `resolve_procurement_configuration` result envelope | Done — `d41a05cc` | New `configuration_resolver.py`: closed §4.10 statuses, exact selected version + verification, payload, resolution hash; `validate_procurement_configuration_for_decision` refuses a changed configuration (CFG_CONFIGURATION_CHANGED). Existing callers unchanged (FU-21). test_cfg_resolver 8 OK. |
| CFG14-305 | 3e Intake change evidence complete | Done — `9db808a6` | Open/close/deadline/scheduled close record module, year, displaced year, before/after flag + closing instant, reason, command identity (key + correlation id shared across a swap). Intake control 18 OK. |
| CFG14-306 | 3f Technical-read resolvers + probes | Done | `services/technical_read.py` + both hooks in `kentender_core/hooks.py`: rules, method profiles, schedules, calendars, funding sources, submission controls resolve to `system-setup` + `#…` links; the shared search opens a trailing `#` part as the fragment (TechnicalSearch 6 tests). Versions/source-check events are hash-named (gate admits real fields only) and Singles cannot be listed — reached via their rule link and probes. Conformance gate: a probe may name `setup_maintenance_exception: CFG11-EX-001` (only known value) to keep the setup commands §3.1 grants the technical roles; denials still fail. test_cfg_technical_read 3 + test_technical_read_conformance 3 OK. |
| CFG14-307 | D16 — refuse undeclared overlaps on every version save | Done | `_require_declared_supersession` runs before any write in all 8 save/correct paths (rules, method eligibility, schedules, calendars); schedules and calendars gain `supersedes_version_ids` (field + API); seeds declare their own replacements through wrappers; all four editors declare the version they came from only when the new dates overlap it. Found and removed 12 leaked test method profiles the old silent supersession had been hiding; the rule suite now purges its own. test_cfg_supersession 7; settings 18, rules 29, calendars 10, preview 9, resolver 8, intake 18 OK; Planning test_plan_workbench 49 OK; vitest 192; `ui-structure-gate` 619 + 35 (twice — board-comparing projects given a 30 s timeout after load timeouts). |

#### Phase 3 findings and open owner questions

| # | Finding | Disposition |
|---|---|---|
| F8 | `test_site_configuration.test_approval_applicability_is_verification_required_with_no_matching_rule` fails on the committed code before this phase: it assumes no approval rule exists, but the seed now creates one. Test depends on live data. | Rewrite against an isolated fixture in Phase 4. |
| F9 | `test_cfg_chg_002_v11_business_day_calendar.test_a_calendar_version_is_never_edited_in_place_or_deleted` fails on the committed code before this phase: in-place correction of unused versions was added later (owner, 23 Sep). | Depends on Q1. |
| F10 | Numeric payload values (e.g. exclusive-preference amount) go through `flt` (binary float); §4.1 requires exact decimal strings. | Phase 5D, with the typed editors. |
| F11 | `CFG_VERSION_CONFLICT`'s message differs from §8 ("This information has changed since you opened it."). | Phase 5H common states. |
| F12 | The canonical-world gap widened after cleaning Planning test residue: validation also reports no Tender on the canonical Requisition. | FU-23. |
| F13 | A direct `doc.save()` on an unused future calendar or method version is accepted by the controller without going through its correction command, so no audit event is written. D15 intends correction through the command only. | Phase 5 / 6: controllers should require the command flag for any change. |
| Q1 | *Answered: D15.* **Spec vs owner decision.** v0.14 §4.6: "Every saved version is immutable, even before first use… Corrections use Create new version." The code (owner decision 23 Sep 2026, `configuration_versions.version_editable`) lets an unused, unchecked, not-yet-effective version be corrected in place. | **Owner to decide** which governs. |
| Q2 | *Answered: D16 — implemented, `CFG14-307`.* **Spec vs code.** §5: an unrelated overlap is rejected on save; supersession must be declared. `save_regulatory_reference_version` silently supersedes any overlapping active version of the set. The preview now reports undeclared overlaps, but save does not refuse them. | **Owner to confirm** save should refuse an undeclared overlap (changes seeds and the new-version editor). |

### Phase 4 — fixture worlds

| ID | Item | Status | Evidence |
|---|---|---|---|
| CFG14-401 | CONFIG, CONFIG-FIRST, CONFIG-SWAP, CONFIG-RULES, CONFIG-EMPTY builders + purges | Planned | |

### Phase 5 — screen by screen

| ID | Screen | Status | Evidence |
|---|---|---|---|
| CFG14-5A | Procuring entity | Planned | |
| CFG14-5B | Financial years + submission-period forms | Planned | |
| CFG14-5C | Funding sources | Planned | |
| CFG14-5D | Procurement rules (all seven kinds) | Planned | |
| CFG14-5E | Source checks and history | Planned | |
| CFG14-5F | Schedules and working-day calendars | Planned | |
| CFG14-5G | Reminders | Planned | |
| CFG14-5H | Common states + AUTH-owned tabs | Planned | |

### Phase 6 — release

| ID | Item | Status | Evidence |
|---|---|---|---|
| CFG14-601 | Full `kentender_core` suite vs baseline | Planned | |
| CFG14-602 | All System setup gates, structure, industry-design, technical-read conformance | Planned | |
| CFG14-603 | Production build of `kentender_core` | Planned | |
| CFG14-604 | Scan: old denominator values and old sub-paths absent | Planned | |
| CFG14-605 | Representative-user walkthrough scripts; results or recorded as owed | Planned | |
| CFG14-606 | FOLLOW_UPS, memory, site left canonical | Planned | |

## Acceptance map

All 117 criteria in v0.14. "v0.11 claim" is what the previous tracker said; it is evidence of nothing until re-proved.

| ID | Required result | v0.11 claim | Phase | Status | Evidence |
|---|---|---|---|---|---|
| CFG10-AC-001 | First run shows the entity tab and disables the other four tabs; route/county inputs are present. | Done | 5A | Re-audit | |
| CFG10-AC-002 | Configuring the entity creates the PE and its root Organisation Unit in one transaction; a failure leaves neither. | Done | 5A | Re-audit | |
| CFG10-AC-003 | Creating a second Procuring Entity is impossible through the UI, the API and a fixture. | Done | 5A | Re-audit | |
| CFG10-AC-004 | `pe_code` cannot be changed after first save, through the UI or a direct API call. | Done | 5A | Re-audit | |
| CFG10-AC-005 | Renaming the entity does not alter the code, the root unit code or any previously issued document snapshot. | Done | 5A | Re-audit | |
| CFG10-AC-006 | No PE selector or PE/FY authority/context record is introduced; exact entity legal snapshots remain allowed. | Done | 5A | Re-audit | |
| CFG10-AC-007 | Retired KenTender context/year/register routes and models are removed after dependency checks; native ERPNext accounting routes and records remain available under their own permissions. | Done | 5A | Re-audit | |
| CFG10-AC-008 | Adding a fiscal year from start year 2028 generates 1 Jul 2028 – 30 Jun 2029 and attaches the site Company. | Done | 5B | Re-audit | |
| CFG10-AC-009 | Fiscal year dates cannot be overridden through the UI or a direct API call. | Done | 5B | Re-audit | |
| CFG10-AC-010 | Adding an existing fiscal year is rejected without creating a partial record. | Done | 5B | Re-audit | |
| CFG10-AC-011 | Concurrent needs-open commands serialize through its unique module control; one atomic swap, no two configured open years and no stale-token overwrite. | Done | 5B | Re-audit | |
| CFG10-AC-012 | A close instant in the past is rejected against the server clock, not the client clock. | Done | 5B | Re-audit | |
| CFG10-AC-013 | At the close instant effective intake is closed before cleanup; the hourly job clears it idempotently with distinct effective and recorded instants. | Done | 5B | Re-audit | |
| CFG10-AC-014 | Dependent commands recheck flag, FY enablement, exact close instant and token in the transaction; equality with the close instant is closed. | Done | 5B | Re-audit | |
| CFG10-AC-015 | Opening or closing needs submission creates no Departmental Need, Plan, Budget or task. | Done | 5B | Re-audit | |
| CFG10-AC-016 | Disable is blocked by any module flag, KenTender reference or native accounting validation, with exact authorized blockers. | Done | 5B | Re-audit | |
| CFG10-AC-017 | FY 2027/28 intake can be open while FY 2026/27 remains the current accounting year. | Done | 5B | Re-audit | |
| CFG10-AC-018 | No configuration submission/review/approval workflow exists; immutable versions and verification events are direct-save evidence, not business approval states. | Done | 6 scan | Re-audit | |
| CFG10-AC-019 | Opening needs submission confers no business authority; Administrator business-record access conforms to KT-STD-001 v1.7 §3A.6, with no fixture business-role grant. | Done | 6 scan | Re-audit | |
| CFG10-AC-020 | No `Reference Data Manager` role, `reference_data.*` capability string or configuration approval chain exists. | Done | 6 scan | Re-audit | |
| CFG10-AC-021 | Selectable UOM and precision come through the native owner adapter; no assumed enabled column, parallel catalogue, free-text unit or mass-disable of unrelated units. | Done | 6 scan | Re-audit | |
| CFG10-AC-022 | Missing-root repair preserves AUTH invariants and existing units, is Administrator-only, and refuses ambiguous structures; responsibilities are unavailable until resolved. | Met | 5H | Re-audit | |
| CFG10-AC-023 | Stale entity/set/control tokens fail atomically; same-key/same-payload returns original result, changed payload conflicts, and no duplicate semantic audit event is created. | Done | 3b | Re-audit | |
| CFG10-AC-024 | Route/hash/record-version detail survives direct load, refresh and Back/Forward across all five tabs without duplicate mount or focus loss. | Done | 2 | Re-audit | |
| CFG10-AC-025 | Loading, empty, forbidden and error states are visibly distinct and never appear as an empty successful table. | Done | 5H | Re-audit | |
| CFG10-AC-026 | ERPNext accounting and HRMS payroll continue to function after cutover; their Fiscal Year, Company and UOM records are shared, not duplicated or replaced. | Done | 6 | Re-audit | |
| CFG10-AC-027 | A new intake module is added through the reviewed CFG flag/control/schema pattern, not a local window lifecycle or new architecture record. | Done | 5B | Re-audit | |
| CFG10-AC-028 | Needs, DPP and disposal use separate controls/tokens/audit, may target different years, and cannot change one another. | Done | 5B | Re-audit | |
| CFG10-AC-029 | ConfigureProcuringEntity and first-run UI require a route from the four approved values; setup may expose pending applicability, but positive governance requires verified applicable capacity. | Done | 5A | Re-audit | |
| CFG10-AC-030 | Method rules require Goods/Works/Services and exact applicability facts; missing category or unsupported procedure cannot resolve admission. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-031 | County-only obligations require county applicability; contradictory entity facts fail setup validation and unresolved jurisdiction cannot silently select a rule. | Done | 5A | Re-audit | |
| CFG10-AC-032 | All three intake kinds have complete UI/API open/close/update-clock paths, independently atomic; DSP timing remains its own verified boundary. | Done | 5B | Re-audit | |
| CFG10-AC-033 | Rule resolution uses the legally verified date basis, not FY alone; exact historical version/verification pins survive later supersession. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-034 | Missing/unverified mandatory method or reservation rules block the affected positive action; a reservation shortfall blocks under PLN; absent optional price index returns NotPublished separately. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-035 | Funding-source create/rename/enable/disable uses CFG services and stable IDs; new selection excludes disabled entries, historical reads remain available. | Met | 5C | Re-audit | |
| CFG10-AC-036 | All §10 CFG artboards and AUTH-owned tab compositions have closed fixtures, complete controls/states and traceable requirements; actual rendering/usability evidence remains required. | Partial | 0 / 1 | Planned | |
| CFG10-AC-037 | Every page resolves its authorisation verdict before rendering; a denied actor sees the inline Forbidden panel with no header, filter, content or empty state painted, and no permission modal appears on page load. | Done | 5H | Re-audit | |
| CFG10-AC-038 | The Forbidden panel names the responsibilities that open the surface and directs the user to a KenTender administrator; it names no line manager or supervisor. | Done | 5H | Re-audit | |
| CFG10-AC-039 | Selecting this module without access pushes its own route, highlights it in navigation, and lands on its Forbidden state; the module is never hidden and route and view never diverge. | Done | 5H | Re-audit | |
| CFG10-AC-040 | Verified requires complete exact-version source, effective/amendment, applicability and interpretation evidence; no bulk verification from LAW/SEED approval. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-041 | Every saved reference/profile/calendar version is immutable; changes create an explicit successor and preserve consumer pins. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-042 | Unrelated overlaps fail save/resolution; declared supersession is date-scoped, gaps fail and creation time/version number never supplies priority. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-043 | FiscalYearStart, submission, approval, authorization, invitation and signing resolve only from authoritative owner facts/current action clocks; missing date returns MissingBasis. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-044 | Pending/rejected replacement or confidence withdrawal blocks affected new positive decisions; historical decision evidence remains visible and unmodified. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-045 | Rule/route/intake verification and consumer write serialize; concurrent configuration edits cannot commit a decision on mixed evidence. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-046 | Unsupported condition code/schema/operator is rejected; owner-condition evidence cannot be supplied as an unchecked boolean. | Done | 3 / 5D | Re-audit | |
| CFG10-AC-047 | Eligible-current-APP Planning basis, applicable-actual-procurement achievement basis, Budget ceiling, county basis and overlap policies remain separate; no missing-to-zero, unused-headroom or planned-to-actual fallback. | Done | 3a | Done (domain; UI in 5D)ï0b6cdc |
| CFG10-AC-048 | Preference margins and highest-advantage entitlement stay downstream; a planned designation cannot decide candidate eligibility. | N/A yet — kind doesn't exist | 5D | Planned | |
| CFG10-AC-049 | Seven milestone semantics, endpoints, min/max/defaults and assumptions are explicit; absent profile/mandatory bounds never use Open Tender or 5/2-day fallback. | Done | 5F | Re-audit | |
| CFG10-AC-050 | A WorkingDays interval requires a verified complete calendar/version; weekends alone or an empty holiday list are not legal verification. | Gap — no calendar doctype | 5F | Planned | |
| CFG10-AC-051 | Source-derived completion boundary remains separate from signing-plus-explicit-delivery estimate, including explicit zero period and missing default. | Done | 5F | Re-audit | |
| CFG10-AC-052 | Threshold is integer 0–365 calendar days, default 7; save affects later evaluations without duplicate notices or changed statutory deadlines. | Met | 5G | Re-audit | |
| CFG10-AC-053 | Funding, every reference kind, verification, history, profile/calendar and reminder maintenance are operable through §10 with exact authority/error states. | Gap — 5 kinds + calendar missing | 5C–5G | Planned | |
| CFG10-AC-054 | Business users receive only owner-authorized configuration evidence; no setup-page access or business-record authority is granted by a configuration read. | Done | 5H | Re-audit | |
| CFG10-AC-055 | Route/county edit cannot relabel an in-flight task or approved snapshot; owner positive checks detect incompatibility and permit controlled correction. | Done | 5H | Re-audit | |
| CFG10-AC-056 | CFG-XD-001 is explicitly resolved before any affected integrated positive claim; no date-guard waiver, FY relabel or fabricated backdated rule coverage. | Open dependency | External | Open dependency | |
| CFG10-AC-057 | Publication-obligation settings record applicable evidence; they cannot self-authorize government integration or close LAW-V-008. | Gap — kind doesn't exist | 5D | Planned | |
| CFG10-AC-058 | Full relevant artboards, keyboard/focus/error paths, 200% zoom and narrow data overflow have real browser evidence, distinct from spec completeness. | Partial | 5A–5H | Planned | |
| CFG10-AC-059 | Disabling/renaming a source preserves exact historic snapshots and ID lookup, and creates no budget balance or Plan lifecycle change. | Met | 5C | Re-audit | |
| CFG-UX-AC-01 | All five existing tab anchors and exact record/version links survive refresh and Back; visible titles use the new terminology with no duplicate setup shell. | Done | 2 / 5A | Re-audit | |
| CFG-UX-AC-02 | First-run entry, missing-root restrictions and ordinary deep links behave as specified; pending source checks never force an unrelated setup wizard. | Partial | 2 / 5A | Planned | |
| CFG-UX-AC-03 | Configure site creates entity/root atomically, retains immutable code and displays source-check gaps independently of structural success. | Done | 5A | Re-audit | |
| CFG-UX-AC-04 | County/type conflicts and required Plan approval authority remain explicit; no silent type inference, route exemption or additional approval is introduced. | Done | 5A | Re-audit | |
| CFG-UX-AC-05 | Year creation shows the generated July–June period, exact duplicate/Company defects and no editable dates or local Company selector. | Done | 5B | Re-audit | |
| CFG-UX-AC-06 | All three submission periods are visible at desktop and narrow widths; disable/re-enable honours native and KenTender blockers and retains shared records. | Done | 5B | Re-audit | |
| CFG-UX-AC-07 | Opening, closing or changing a deadline requires one focused final action with reason; cross-year replacement identifies the affected year and changes only that module atomically. | Done | 5B | Re-audit | |
| CFG-UX-AC-08 | Expiry at the exact instant and stale control tokens are enforced server-side; inputs remain recoverable and permitted owner corrections/updates remain accessible. | Done | 5B | Re-audit | |
| CFG-UX-AC-09 | Funding creation/edit requires only the baseline name/availability fields, with normalized duplicate validation and no new approval/reason. | Done | 5C | Re-audit | |
| CFG-UX-AC-10 | Disabled sources cannot be newly selected where the catalogue governs selection; exact-ID historical reads and frozen names remain intact, with BUD eligibility still owner-controlled. | Done | 5C | Re-audit | |
| CFG-UX-AC-11 | Add rule renders one kind-specific form and prevalidates content; successful set/version commands return the exact new immutable version without inventing a Draft state. | Done | 5D | Re-audit | |
| CFG-UX-AC-12 | Set-success/version-failure and ambiguous-timeout scenarios retain/recover the original identity and keys; retry never duplicates a reference set, and an empty set can be completed later. | Done | 5D | Re-audit | |
| CFG-UX-AC-13 | Every field in all seven typed rule kinds remains represented with readable labels and supported selectors; precision, condition grouping, bound states and date bases are unchanged. | Done | 5D | Re-audit | |
| CFG-UX-AC-14 | No illustrative threshold, evidence placeholder, missing bound or approved document produces Verified/usable configuration; optional price-index absence stays informational. | Done | 5D | Re-audit | |
| CFG-UX-AC-15 | Every correction creates a new version with exact predecessor linkage and a real reason; old payloads and decision-time verification pins remain readable. | Done | 5D | Re-audit | |
| CFG-UX-AC-16 | Impact preview identifies coverage and known usage; a pending replacement of usable coverage warns before save and blocks affected new use without silently falling back. | Partial | 3c / 5D | Planned | |
| CFG-UX-AC-17 | Check sources fixes target kind/version, groups all required fields and appends the exact selected outcome with actual recorder/check/recording evidence. | Done | 5E | Re-audit | |
| CFG-UX-AC-18 | Verified requires complete supported evidence and no unresolved mandatory point; pending/rejected remain distinct, and verification cannot change immutable payload fields. | Done | 5E | Re-audit | |
| CFG-UX-AC-19 | Schedule summary names each interval’s endpoints and separates defaults, bounds, counting and assumption/legal basis; invitation anchor and completion boundary remain distinct. | Done | 5F | Re-audit | |
| CFG-UX-AC-20 | Working-day rules require a supported verified exact calendar version; empty holiday examples, unsupported procedures and missing defaults cannot pass by display labels. | Done | 5F | Re-audit | |
| CFG-UX-AC-21 | Reminder control states calendar days and preserves default 7 with integer range 0–365; zero behavior is explicit. | Done | 5G | Re-audit | |
| CFG-UX-AC-22 | Reminder save changes subsequent evaluations only; it neither changes business deadlines nor creates duplicate tasks/notices. | Done | 5G | Re-audit | |
| CFG-UX-AC-23 | Both setup roles see authorised owned AUTH tabs; missing-root repair is actionable only for Administrator and refuses ambiguous trees. | Done | 5H | Re-audit | |
| CFG-UX-AC-24 | Technical access conforms to KT-STD-001 v1.7 §3A.6 and AUTH v1.9, with shared search and read-entry registration; business/Auditor reads stay owner-authorised and cannot mutate setup. | Gap — blocked, not ours | 3f | Planned | |
| CFG-UX-AC-25 | Each listed failure maps to a short problem/action message with current scope/date where relevant; saved, verified, complete and supported are not collapsed into one status. | Done | 5H | Re-audit | |
| CFG-UX-AC-26 | Business users receive an actionable owner-routed explanation inside their record; denied setup routes reveal no protected tabs/data and name the required technical roles. | Done (CFG's half) | 5H | Re-audit | |
| CFG-UX-AC-27 | Critical impacts/errors remain visible; supporting detail uses structured labels. Keyboard, focus return, first-error focus, 200% zoom and narrow layouts have recorded browser evidence. | Partial | 5A–5H | Planned | |
| CFG-UX-AC-28 | The full CFG v0.11 incorporates all 14 usability changes alongside retained baseline requirements and dependencies; representative-user evidence is recorded separately from document approval. | Partial | 6 | Planned | |
| CFG11-AC-029 | Current control, authority, design, interaction and release references cite approved KT-STD-001 v1.7; older references appear only as historical trace, not the current standard. This criterion does not by itself claim completion of a CFG Stage 2 presentation rewrite. | Done | 0 | Re-audit | |
| CFG11-AC-030 | CFG record types/read entry points are registered with the KT-STD §3A.6 shared search and AUTH v1.9 conformance mechanism; actual implementation evidence is recorded before release. | Gap | 3f | Planned | |
| CFG11-AC-031 | The three §3.1 exceptions are explicit and narrowly enforced: authorised setup writes remain operable, unrelated native UOMs remain usable, and missing-root recovery exposes no generic nested-set controls. | Done | 6 | Re-audit | |
| CFG11-AC-032 | A CFG-owned design package consists of KT-STD v1.7 §2 plus CFG §10 in full, with runtime behavior confined to §11; AUTH-owned tab bodies use AUTH v1.9 through the exact §10.1 exception. Each independent visible fact remains distinguishable and no fixture/diagnostic internals are rendered as product content. | Done | 0 / 1 | Re-audit | |
| CFG12-AC-001 | Administrator and System Manager can list installed Tender formats and open an exact release detail; no other setup authority is created. | — | Deferred | Deferred (D11) | |
| CFG12-AC-002 | List and detail reads create no release, verification, activation, approval or audit business event. | — | Deferred | Deferred (D11) | |
| CFG12-AC-003 | Status is derived from the exact installed template owner record and cannot be changed from System setup. | — | Deferred | Deferred (D11) | |
| CFG12-AC-004 | CFG-DES-05B shows the exact §10.11 order, labels and fixture values for supported/unsupported use, source, profiles, documents, five supplier tasks, supported answer types, MoH counts, evaluation/contract treatment, verification results and blocker; the designer needs no STD-TPL, TPR, BDS or ZIP lookup. | — | Deferred | Deferred (D11) | |
| CFG12-AC-005 | The page contains no edit, activate, override, clause-builder, schema-builder, raw JSON upload or generic template action. | — | Deferred | Deferred (D11) | |
| CFG12-AC-006 | An Unavailable release cannot be used by Tenders even if all visible document previews render. | — | Deferred | Deferred (D11) | |
| CFG12-AC-007 | Preview/download actions retrieve immutable owner assets and disclose no Draft or submitted bid content. | — | Deferred | Deferred (D11) | |
| CFG12-AC-008 | Technical digests are accessible under collapsed Technical details but are not required to understand the readiness outcome. | — | Deferred | Deferred (D11) | |
| CFG12-AC-009 | Separate Available, Unavailable, Superseded, Withdrawn and failed-verification list/detail variants use the exact plain consequences and truthful next steps in §10.11. No alternative state is conflated with the current Candidate/Unavailable fixture. | — | Deferred | Deferred (D11) | |
| CFG12-AC-010 | Desktop, keyboard, 200% zoom and 390 px rendering preserve the specified reading order, every labelled fact, task, mapping and permitted action; tables become labelled row cards without horizontal scrolling. | — | Deferred | Deferred (D11) | |
| CFG12-AC-011 | The design handoff uses KT-STD-001 v1.7 §2 plus CFG §10 in full; AUTH-owned tab bodies use AUTH v1.9 through the explicit §10.1 exception. No other document is required to complete a CFG-owned artboard. | — | Deferred | Deferred (D11) | |
| CFG12-AC-012 | List/detail values come only from the owner projections in §§4.11 and 7.2; previews use immutable installed assets, and missing facts are never inferred from a PDF, filename, release label or raw manifest. | — | Deferred | Deferred (D11) | |
| CFG12-AC-013 | Organisation structure, Users and responsibilities and Technical record search use AUTH v1.9 AUTH-DES-01–09; no superseded AUTH composition or duplicate CFG assignment/search screen remains. | — | 5H | Planned | |
| CFG12-AC-014 | Only a Scheduled responsibility detail shows **Edit scheduled assignment**; the prefilled owner dialog permits every AUTH-approved field change, uses **Save changes**, records one appended before/after history event and omits Edit for Active, Expired and Revoked assignments. | — | 5H | Planned | |
| CFG12-AC-015 | AUTH v1.9 resolves the former missing owner specification for AUTH-DES-09 and the registration hooks. Release still requires actual shared-search implementation, CFG record registration and technical-read conformance evidence. | — | 3f | Planned | |
| CFG14-AC-001 | List and detail show release 1.1 as supporting unreserved procurement and reservation for Youth, Women or Persons with disabilities, with County-residents treatment separately conditional on an applicable county entity, verified rule and explicit overlap treatment. | — | Deferred | Deferred (D11) | |
| CFG14-AC-002 | `supported_reservation_categories`, County-residents support, verification outcomes and blockers come from the exact installed release projection; no client, seed or hard-coded CFG copy may restore **Unreserved only**. | — | Deferred | Deferred (D11) | |
| CFG14-AC-003 | The Candidate/Unavailable fixture shows the Youth path as Passed, the remaining Women, Persons-with-disabilities and County-residents fixture coverage as Incomplete, and owner decision as Pending. It never claims that all technical verification passed. | — | Deferred | Deferred (D11) | |
| CFG14-AC-004 | The Available variant exists only when every supported base treatment and County-residents overlay has passed its required fixture/evidence/mapping checks and the exact manifest has owner approval. | — | Deferred | Deferred (D11) | |
| CFG14-AC-005 | Bid-response inspection shows the applicable reservation declaration/evidence as a separate eligibility pass/fail mapping, not a Planning result or contract obligation; category, County treatment and evaluated result remain available to Award/reporting. | — | Deferred | Deferred (D11) | |
| CFG14-AC-006 | This correction adds no format editor, activation, approval, override, upload or repair action. System setup remains a read-only inspection surface. | — | Deferred | Deferred (D11) | |
| CFG13-AC-001 | The AGPO Planning rule resolves only to `EligibleCurrentAPPValue`; no approved Budget amount or unused headroom is accepted as its denominator. | — | 3a | Done (domain; UI in 5D)ï0b6cdc |
| CFG13-AC-002 | The resolver returns the exact obligation/rule Version and enough applicability data for Planning to evidence every included or excluded current Plan Item. | — | 3a / 3d | Planned | |
| CFG13-AC-003 | A successor APP Version causes a new calculation snapshot; historical decisions retain their earlier Plan/rule Versions. | — | 3a | Planned | |
| CFG13-AC-004 | Actual achievement accepts authoritative downstream actual procurement values only and cannot be calculated from APP estimates. County and other obligations remain separate. | — | 3a | Done (domain; UI in 5D)ï0b6cdc |
| CFG13-AC-005 | Ordinary setup copy says **Planned allocation**, **Actual achievement**, **Eligible value of the current Annual Plan** and **Applicable actual procurement value**; it does not expose obsolete denominator choices. | — | 5D | Planned | |
