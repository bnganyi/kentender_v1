# PLN-CHG-001 v1.23 — Procurement Planning — implementation plan

**Authority:** `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_23.md` (17 September 2026). v1.23 closes the two consistency gaps this plan first raised against v1.22: the forecast/reminder deferral is now complete (`PLN23-AC-001`) and both U06 classification artboards now exist (`PLN23-AC-002`).
**Design source:** `design/*.dc.html` — 15 files, 112 artboard panels (111 MVP states + the U15 deferral notice), all on `_ds/kentender-industry-82d82607-fd52-491b-bef1-023d4ec3bd0c`. These artboards are the build source for every screen (KT-STD-001 v1.6 §2; §10 of the specification).
**Companions:** `PLN-CHG-001_IMPLEMENTATION_TRACKER.md` (rows, gates, acceptance map), `PLN-CHG-001_FOLLOW_UPS.md`, `evidence/v1_22/`.
**Supersedes-in-planning:** `retired/PLN-CHG-001_Implementation_Plan_v1_18.md` and `retired/PLN-CHG-001_IMPLEMENTATION_TRACKER_v1_18.md` (v1.18 cycle, stopped after PLN18-306).

---

## 1. What this cycle actually is

This is **not** a rebuild. v1.22 keeps the v1.18 business, authority, governance, integration and audit rules unchanged and re-expresses them. Four later revisions sit on top of the v1.18 baseline that was already built:

| Revision | What it changed | Effort consequence |
|---|---|---|
| v1.19 | 20 usability rows (`PLN-UX-001..020`) from Blueprint v0.2 | Presentation only; no new domain rule |
| v1.20 | 6 composition rows (`PLN20-CHG-001..006`) — §10 rewritten as exact artboard contracts | New design pack; every screen re-ported |
| v1.21 | 3 classification rows (`PLN21-CHG-001..003`) | **The only new domain work in the cycle** |
| v1.22 | 13 simplicity rows (`PLN22-CHG-001..013`) — first-view reduction, U15/forecast/reminder deferral | Screens shrink; forecast and cascade exposure removed |
| v1.23 | 2 consistency rows (`PLN23-CHG-001..002`) | Deferral made total: no forecast schema, route, API, scheduler or notification producer. Both U06 classification artboards supplied |

So the plan is: **keep the domain, delta it (Phase 1), then rebuild the UI layer wholesale against the new artboards (Phase 2)**. Demolition is the dominant cost of a rebuild and there is nothing here that justifies paying it on the server side.

### 1.1 Inspected build state (facts, 18 September 2026)

Checked against the working tree, not against the v1.18 tracker's claims.

1. **Domain is built.** 36 doctypes under `kentender_procurement/kentender_procurement/procurement_planning/doctype/`; 31 service modules; `api.py` exposes 61 whitelisted endpoints covering every §7.2 command except the two named in §1.2 below; 16 Python test modules; `make planning-domain-gate` was green at Phase 2 exit.
2. **Stable identities exist.** `Plan Item` (stable) with `scope_locked_since`, `first_authorised_requisition`, `authorisation_hold`, `open_correction_requests`; `Annual Plan Item` is the per-Version content row; `Departmental Plan Entry.direct_source_id`; `Annual Plan Version.source_cohort` / `change_reason` / `project_name` / `preparation_signature`.
3. **Publication is asynchronous.** Intent, attempts, acknowledgement, hold, withdrawal, Treasury evidence and activation predicates are all present as separate records and commands.
4. **Prohibited constructs are gone.** `highest_advantage`, `multi_year_justification`, `PLN_RESERVATION_RELEASE_FAILED`, `record_requisition_drawdown` and `ocid` now appear only inside `tests/test_planning_v118_schema.py`, which asserts their absence. Two residues remain — see D6.
5. **UI is at the v1.18 dense design and is uncommitted.** `git log` shows Planning last committed at `0c4b6a54` (Phase 2 + the U01 slice). The working tree additionally holds PLN18-303..306 (departmental, annual plan, item editor, finance) plus their vitest specs and Playwright specs, built against the *deleted* v1.18 artboards. Those artboards are already `D` in `git status`; the new pack replaces them.
6. **U11, U12, U13, U14, U16 were never built to v1.18.** `ReviewScreen.vue`, `SourceEvidenceScreen.vue`, `ActivePlanScreen.vue`, `PublicationResultScreen.vue`, `GovernanceTaskScreen.vue` are v1.12 remnants. For those families this cycle is greenfield against v1.22 directly — no demolition at all.
7. **Design-system CSS is mostly already absorbed.** The Planning pack's `_ds/.../styles.css` is a newer revision than the Budget/STD packs carry (+304 lines: `kt-notice`, `kt-disclosure`, `kt-kpi-card`, `kt-record`, `kt-checkbox`, `kt-meta-row`, `kt-panel`). `kentender_core/.../public/css/kt_industry_tokens.css` already defines all of those — a sibling module absorbed them. Only the artboard's own page-chrome simulation (`kt-app-shell`, `kt-nav-item`, `kt-breadcrumb`) is absent, and that is Desk's job, not ours.
8. **Site state.** Only `PE-MOH` exists. The canonical seed stage `planning` feeds `requisitions` and `tender_preparation`. No RQ worker runs on this bench — the publication worker must run inline under tests and seeds.

### 1.2 The actual delta

**Server (small):**

- `CorrectAcceptedRequirementClassification` command — absent.
- `GetAcceptedDPPClassification` read — absent.
- `DPP Classification Correction` record and the effective-classification projection — absent.
- `Plan Source Allocation` carries no classification-evidence id or type/category snapshot (§4.6 requires both).
- Three error codes absent: `PLN_CLASSIFICATION_UNCHANGED`, `PLN_CLASSIFICATION_CORRECTION_STALE`, `PLN_CLASSIFICATION_CORRECTION_BLOCKED`. `PLN_CLASSIFICATION_INCOMPLETE` and `PLN_SOURCE_CORRECTION_REQUIRED` already exist in `errors.py`.
- `preview_forecast_cascade` / `confirm_forecast_cascade` are exposed in `api.py` and must not be (§11.9, PLN22-AC-010).
- Residues: `exclusive_preference` on `Annual Plan Item` and in `plan_governance.py:542`'s copy list; seven item-level `forecast_*` and seven `actual_*` date columns on `Annual Plan Item` that no service writes.
- Read projections reshaped per slice to feed the new compositions (workspace issue line, Plan checks, decision summary, four publication status rows, coverage rows, issue-first corrections).

**UI (all of it):** every screen family is re-ported from its artboard. Eight families have an existing screen to delete and re-port (U01, U02–U05, U06, U07, U08, U09, U10, U21); five are greenfield against v1.22 (U11, U12, U13, U14, U16); C01–C04 is new Planning-side panelling.

---

## 2. Consistency findings

Checked against v1.22 on 18 September 2026, against the design pack, and against the repository. **v1.23 resolved both blockers.**

### 2.1 Raised against v1.22 and now closed by v1.23

| ID | Finding | Resolution in v1.23 |
|---|---|---|
| **C1** | Two required artboards were missing: `U06-ACCEPTED-CLASSIFICATION` and `U06-CORRECT-CLASSIFICATION`. The one new feature in the cycle had no design source. | **Closed.** Both artboards now exist in `U06.dc.html` (8 panels, was 6). §10.5 adds an explicit classification design-asset gate and `PLN23-AC-002` forbids accepting U09 as a substitute. |
| **C2** | The forecast/reminder deferral was incomplete: `AC-126`, `AC-127` and `AC-131` stayed in the MVP gate while the body deferred the facility, and `PreviewForecastCascade` / `ConfirmForecastCascade` / `CheckApproachingMilestones` were still current contracts. | **Closed.** `PLN23-CHG-001` defers `AC-119` and `AC-124..131` in full, deletes both forecast error codes, removes the two cascade entries from the service catalogue, replaces §7.5 with "No MVP forecast or milestone-notification service", drops forecast columns from U14 and drops reminder configuration from C01–C04. `PLN23-AC-001` requires that no forecast or reminder runtime entry point exists. |

D7 is therefore no longer a judgement call — it is the specification. Existing tested forecast and reminder code **may remain in the repository but must be unreachable**: no route, no whitelisted endpoint, no scheduler registration, no notification producer, no setup control.

### 2.2 Non-blocking

| ID | Finding | Handling |
|---|---|---|
| C3 | `Index.dc.html` still lists "U15 — Update expected dates" in the left nav. The U15 page itself correctly renders a deferral notice. | Follow-up only; no code effect. |
| C4 | Several artboards render a **blank** input where §10 says generation should wait for an owner fixture value — `U07-UPDATE`'s reason, `U21-CANCEL-UPDATE`'s reason and others. The designer correctly declined to invent values (`PLN20-AC-008`). | Phase 3 supplies each one; the tracker lists them individually. |
| C5 | `U09.dc.html` contains "Rule version" and "Source check" — verified to sit **inside the collapsed `Supporting details` disclosure**, which §10.8 permits and `PLN22-AC-005` only forbids as ordinary business fields. **Not a violation.** | None. |
| C6 | The §16 prohibited-copy sweep across all artboards is otherwise clean. | None. |
| C7 | §10.2 arithmetic is internally consistent and reproduces in the artboards: 80m + 50m = 130m; 20m + 30m = 50m; 30% of the 160m annual budget = 48m; READY 50m = 31.25% of 160m; both schedules recompute exactly from 21/30/5/2/14 plus the 30- and 60-day delivery periods. | None. |
| C8 | Counts check out: §14.1 = 134 AC, §14.2 = 32 UX, §14.4 = 40, §14.6 = 12, §14.7 = 6, §14.8 = 13, §14.9 = 2; §17.4 = 72 + 20 + 6 + 3 + 13 + 2 = 116. | None. |
| C9 | §9.2 routes match the four existing Pages exactly. No new Page, no routing migrate, no slug collision. | None. |

---

## 3. Decision register

| ID | Decision | Why |
|---|---|---|
| **D1** | Keep the v1.18 domain. Phase 1 is a delta, not a rebuild. | v1.22 §17.1 retains the v1.18 business rules verbatim; §1.1 above confirms they are built and gated. Rebuilding would pay demolition cost for nothing. |
| **D2** | Delete the uncommitted v1.18 Phase-3 screens and re-port from the new artboards. Do not patch them. | Every affected composition changed materially — U07 loses its five tabs for Purchases + one Plan checks section; U09 loses two of seven sections and several fields; U10, U01, U02–U05 all reduce. Patching a changed composition costs more than a port and leaves v1.18 structure behind. |
| **D3** | Commit the uncommitted v1.18 Phase-3 work as a labelled checkpoint **before** deleting it. | It is real, tested work. The user authorised teardown, not loss of recoverability. One commit; the deletions land in their own slice. |
| **D4** | Slices are vertical: read projection → screen → vitest → fidelity → Playwright → live browser pass, one family at a time. Phases 0–1 stay horizontal. | Recorded lesson: verification-last ordering is where rebuild hours go. |
| **D5** | One fidelity assertion per artboard variant, one Playwright spec per slice, one Make gate per slice. Not one gate per variant. | 111 MVP artboards; per-variant gates would be unusable. |
| **D6** | Remove `exclusive_preference` and the fourteen unused item-level `forecast_*`/`actual_*` columns from `Annual Plan Item` in Phase 1C, with a patch. | §16 prohibits the preference override; §5.5.1A requires per-proceeding actuals, and dead columns invite a future writer. Deletion lands with its replacement, not later. |
| **D7** | Forecast cascade and reminder **domain** stays in the repository but becomes unreachable: no route, endpoint, scheduler registration, notification producer or setup control. | `PLN23-CHG-001` / `PLN23-AC-001` now require exactly this. Deleting the tested code buys nothing; exposing it fails the gate. |
| **D8** | Fixture instants stay pinned to §13.1 (Julia 1 Oct–30 Nov 2026 DHI; Peter DHI from 1 Dec; the 25/27 Nov chronology) under the frozen clock. Never `now`-relative. | §13.1; and the recorded Playwright fixture-realism lesson. |
| **D9** | Seeds never carry `verification_status = Verified`. Profiles seed as `Fixture-verified — not production law` and every screen showing a rule shows that status. | §13, §10.2 CONFIG note. |
| **D10** | Sibling contract work lands in the owning app with owning-app tests, tagged `[core]` `[budget]` `[nds]` `[req]` `[tpr]`. Sibling specification amendments are follow-ups, not rows. | v1.18 D17 precedent; keeps this cycle on implementation. |
| **D11** | Never run `bench run-tests` for Planning while any Planning Playwright process is live, and never run the Python suite and Playwright together. | Both move the intake flags; the Requisitions wipe is site-wide and unscoped. |
| **D12** | New component CSS goes into `kentender_core/.../kt_industry_tokens.css` only if genuinely missing after a diff against the pack's `styles.css`. Planning-local classes go in `procurement_planning_industry.css` namespaced `.kt-industry .kt-pln *`. | §1.1 item 7: core already carries almost all of it. Duplicating would fork the design system. |

---

## 4. The slice gate

A UI slice is `Done` only when all of this is true and recorded on its row:

1. Component tests (vitest, project `procurement-planning`) for every state the slice serves.
2. One fidelity assertion per artboard variant in `tests/ui/smoke/design-fidelity/planning-fidelity.spec.ts`, asserting landmark structure and geometry — not fixture text.
3. A Playwright spec on the seeded world with a real login per §6 actor the slice serves, **plus** an outsider and a no-responsibility user refused, with absence assertions on the refusal paths.
4. First paint **and** at least one interactive re-render observed live in a browser — not inferred from a passing test.
5. Direct load, reload, and browser back/forward preserve route context, including exact historical Version selection.
6. One forced server-error state and the inline-error presentation checked.
7. Zero page-specific console errors, filtering only the two known Desk noises (socket.io `:8000` 404 and the sidebar divider `<img src=undefined>` 404).
8. Bundle content hash changed after the asset build — proving the edit actually landed.
9. Screenshots in `evidence/v1_22/`.
10. The superseded v1.18 component and its spec deleted in the same slice.

---

## 5. Phases

### Phase 0 — Baseline and disposition

| Item | Detail |
|---|---|
| 0.1 | Checkpoint commit of the uncommitted v1.18 Phase-3 UI work (D3). |
| 0.2 | Record per-module baseline: `bench run-tests` counts for the 18 Planning modules one module per run; `npx vitest run --project procurement-planning`; Playwright not run (its fixtures target the retired artboards). |
| 0.3 | Generate `evidence/v1_22/FRAMES.md` — the 111 MVP artboard ids as the fidelity/evidence filename list (U01 6, U02–U05 13, U06 8, U07 7, U08 4, U09 7, U10 7, U11 9, U12 4, U13 14, U14 5, U16 7, C01–C04 4, U21 16). |
| 0.4 | Raise C1 and C2 with the owner. C1 blocks Phase 2C only; C2 proceeds on D7 unless answered otherwise. |
| 0.5 | Retire the v1.18 plan/tracker (done) and point `PLN-CHG-001_FOLLOW_UPS.md` at this cycle. |

Exit: baseline recorded, no product code changed.

### Phase 1 — Domain delta

**1A — Classification provenance and correction** (§4.4, §5.1.6, §7.2; PLN21-AC-001..006)

- `dpp_validation.py`: the Planner supplies only `requirement_type_id`; the server derives `procurement_category` from the same effective catalogue entry and **rejects a client-supplied category**. Freeze both on acceptance.
- New doctype `DPP Classification Correction` with the seven §4.4 fields; immutable, append-only, superseding by `supersedes_classification_evidence_id`.
- New service + command `correct_accepted_requirement_classification` — rechecks accepted submission, current correction head, authority, catalogue mapping and every affected allocation in one transaction; stale or concurrent attempts fail whole.
- Effective-classification projection: latest valid correction, used for new work only; never rewrites an accepted decision, allocation, submitted Plan or Active Plan.
- `Plan Source Allocation` gains `classification_evidence`, `classification_requirement_type`, `classification_procurement_category` (snapshot at allocation; a later correction never rewrites it). Patch existing rows from their acceptance evidence.
- Affected-item recovery: unallocated source → available with the corrected classification; mutable Draft item → `Source correction required`, dissolve-and-re-form only; submitted/approved/Active → unchanged, route to correction or successor; scope-locked → correction recorded, new authorisation held, downstream owner route identified and **no** reclassify/dissolve/duplicate.
- New read `get_accepted_dpp_classification`.
- Error codes: `PLN_CLASSIFICATION_UNCHANGED`, `PLN_CLASSIFICATION_CORRECTION_STALE`, `PLN_CLASSIFICATION_CORRECTION_BLOCKED`. `PLN_SOURCE_CORRECTION_REQUIRED` already exists — reuse it.
- Tests: `tests/test_dpp_classification_correction.py` — derivation, client-supplied category rejected, unchanged rejected, stale head rejected, excluded entry rejected, unauthorised rejected, each of the four affected-item outcomes, concurrency, audit/export.

**1B — Forecast and reminder withdrawal** (§10.14, §11.9, §15.3; PLN22-AC-010)

- Remove `preview_forecast_cascade` and `confirm_forecast_cascade` from `api.py`. Keep the services, records and their tests (D7).
- Delete `ShiftScheduleDialog.vue` and its spec; confirm no screen offers "Update expected dates".
- Confirm no MVP route, control, artboard or gate for U15; add the absence to the removed-construct scan.

**1C — Residue removal** (D6)

- Drop `exclusive_preference` from `Annual Plan Item` and from `plan_governance.py`'s copy list.
- Drop the fourteen unused `forecast_*`/`actual_*` date columns; confirm `Milestone Actual Event` is the only actual store and that per-proceeding coverage reads from it.
- Confirm `plan_horizon` is a fixed literal with no editable selector and that multi-year payloads are rejected server-side.
- Extend `tests/test_planning_v118_schema.py` → rename to `test_planning_v122_schema.py`, add the new prohibited strings, and **prove each guard with a planted violation**.

**1D — Phase 1 exit**

`make planning-domain-gate` green; three clean `bench migrate`; cross-module checkpoint (Budget, NDS, Requisitions, Tender Preparation suites, one module per run).

### Phase 2 — Vertical UI slices

Each slice: reshape its read projection → port the screen class-for-class from its artboard → vitest → fidelity → Playwright → live browser pass → delete the superseded component. Ordered so that the two greenfield-heavy governance slices come after the preparation chain that produces their data.

| Slice | Families | Artboard variants | Starting point |
|---|---|---|---|
| 2A | U01 workspace + U21 shared states | 6 + 16 | v1.18 `WorkspaceScreen.vue` / `CommonStates.vue` — re-port |
| 2B | U02–U05 departmental preparation and certification | 13 | v1.18 `DppPlanScreen` / `DppEntryEditorScreen` — re-port |
| 2C | U06 validation + classification correction | 6 + **2 missing (C1)** | v1.18 `DppValidationScreen` — re-port; correction panel greenfield |
| 2D | U07 annual plan preparation + U08 add requirements | 7 + 4 | v1.18 `AnnualPlanScreen` (five tabs → Purchases + Plan checks) — re-port |
| 2E | U09 purchase editor | 7 | v1.18 `PlanItemEditorScreen` (five → six sections, fields removed) — re-port |
| 2F | U10 funding review and reassessment | 7 | v1.18 `FinanceTaskScreen` / `FinanceHistory` — re-port |
| 2G | U11 governance review + U12 source evidence | 9 + 4 | **Greenfield** (v1.12 remnants deleted) |
| 2H | U13 publication evidence and recovery | 14 | **Greenfield** |
| 2I | U14 procurement progress + U16 correction requests | 5 + 7 | **Greenfield** |
| 2J | C01–C04 Planning-side missing-setting panels | 4 | New; setup itself stays CFG-owned (§10.16) |

Per-slice notes worth stating up front:

- **2A** — the workspace shows one plain shortfall sentence and one recovery action, never four reservation numbers (PLN22-CHG-003). Current plan resolves the Active pointer, not the highest version number.
- **2C** — Requirement type is the only classification input anywhere; Category is read-only derived text beside it.
- **2D** — no Approval-and-publication section while the Planner is preparing a Draft; `Send to Finance for funding review` is **absent**, not disabled, while a blocking check fails.
- **2E** — first view is Purchase details, Included requirements, Estimated cost, Procurement approach, Dates. Everything else goes under one collapsed `Supporting details`. Omit `None`, `Not applicable`, `Single lot`, `Lot count 1` and the plan-level reservation arithmetic.
- **2G** — decision summary, visible issues, concise purchase rows, actor statement. **No purchase starts expanded.** Only header, prior accountability, decision statement and buttons vary between HOPF, AO, statutory, collective and reader.
- **2H** — four distinct status rows (approval, Treasury, website publication, use for procurement). Unknown is never rendered as failure. Retry and reconcile appear only for a separately authorised technical operator; technical read alone does not grant them.
- **2I** — lead with what must change and the hold consequence; request ids, versions and timestamps stay in detail.

### Phase 3 — Seed and browser world

- Rebuild the §10.2/§13 fixture under the frozen clock: 2 items, 3 sources, 2 departments, KES 130,000,000, BASE as a **blocked** mandatory-allocation case.
- Supply every value the artboards left blank (C4), each as its own tracker row: U04-EDIT's saved direct reference, U05-ALL-EXCLUDED's second exclusion reason, U06-STALE-SOURCE's changed revision, U07-WAITING-FINANCE's request instant, U07-UPDATE's reason, U08-INCOMPATIBLE's differing budget lines, U08-DUPLICATE's cohort facts, U09-LOCKED's requisition, U09-CLASSIFICATION-LOCKED's downstream record and route, U10's as-at instants, U11-COLLECTIVE's recorder, U11-LATE-ADOPTION's date and reason, U12's certification text, U13's attempt/activation instants, U14's proceeding ids, U16's accepted DPP update reference, U21-CANCEL-UPDATE's reason.
- Isolated presentation profiles per §13.3, including the classification-correction history on Submission 3 — never mutations of the shared BASE records.
- Re-run the Requisitions and Tender Preparation canonical stages on the new Plan.
- A persona browser pass as each §10.2 actor.

### Phase 4 — Release evidence

Full Planning regression; cross-module checkpoint; production asset build for `kentender_procurement` and `kentender_core` with changed bundle hashes; all MVP artboards compared at 1440 × 1024 and at a narrow width; removed-construct scan; the acceptance map closed truthfully against §§14.1–14.8; follow-ups and memory updated.

---

## 6. Commands

```bash
# Focused Python (one module per run — never alongside Playwright)
cd /home/midasuser/frappe-bench && bench --site kentender.midas.com run-tests \
  --app kentender_procurement --module kentender_procurement.procurement_planning.tests.<module>

# Component tests
cd /home/midasuser/frappe-bench/apps/kentender_v1 && npx vitest run --project procurement-planning

# One browser test
npx playwright test tests/ui/smoke/planning/<spec>.ts -g "<name>"

# Assets (never plain `bench build`)
cd /home/midasuser/frappe-bench && ./scripts/bench-with-node.sh build --app kentender_procurement

# Gates
make planning-domain-gate SITE=kentender.midas.com
make ui-planning-<slice>-gate SITE=kentender.midas.com
make ui-planning-fidelity-gate SITE=kentender.midas.com
make seed-canonical SITE=kentender.midas.com THROUGH=tender_preparation
```

---

## 7. Traps carried in from earlier cycles

1. Editing CSS or JS on disk is not enough — touch `hooks.py`, clear the site cache, and clear the browser cache. Confirm the bundle content hash changed.
2. A dead `bench serve` stdout pipe turns every `frappe.throw` into an HTML 500. Restart with `nohup` before debugging app code.
3. No RQ worker runs on this bench. The publication worker must run inline under tests and seeds, or jobs pile up and trip `QueueOverloaded` mid-seed.
4. `make purge-kentender-playwright-data` has previously deleted live canonical records. Confirm scope before running it.
5. A `**kwargs` `@frappe.whitelist()` endpoint receives `cmd` and `csrf_token` in `form_dict`; forwarding them into a keyword-only service is a 500 that no direct-service test can see.
6. Scope Playwright locators to the dialog, not the page — sidebar text collides.
7. `parse_json` is needed for list arguments; future annotations disable Frappe's own coercion.
8. Fire-and-forget reloads after save clobber the next edit. Await them and sequence-guard loaders.
9. Redis must be up before any run.
10. Do not add Planning pages to `kt_cl_surface_registry.js`. Industry is the only design system in play; Civic Ledger and Stitch Desk are legacy debt.

---

## 8. Non-goals

U15 and any forecast editor, cascade control or forecast-driven reminder surface. Multi-year procurement. Full OCDS publication. Automated Treasury transmission. Aggregate item-level actuals. The six unimplemented milestone actual integrations. Candidate-level preference entitlement. Statutory returns using downstream facts. Any change to CFG's System setup design — Planning renders only its own missing-setting consequence and an authorised link.
