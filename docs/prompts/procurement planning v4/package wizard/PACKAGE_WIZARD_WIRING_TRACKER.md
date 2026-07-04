# Planning Package Creation Wizard — Wiring Tracker (PW1–PW13)

## Goal

Ship a guided, pixel-perfect 3-step (+success) **Package Creation Wizard**
that replaces every existing "Create Package" entry point in the Planning
Workbench (`pp2_planning_create_package_modal.js`'s single-field dialog)
with the richer flow specified in `Planning Package Creation Wizard.md` and
its four step designs (`step 1`–`step 4`). Today a planner can only create a
package from **one** already-included demand, with **one** auto-derived
line, no owner/priority/target-release-date, no method override reason
capture in the UI, and no lines/lots or document-path visibility. Done
looks like: a planner can select **one or more** eligible demands from the
active plan, configure the package's identity/method/lines/funding/
document path with full business-readable validation, review a readiness
checklist, and create a real multi-line `Procurement Package` — with the
same zero-visual-drift discipline used for the rest of the v4 Workbench
(static design HTML deployed verbatim, JS only mutates existing DOM nodes).

## Documentation read gate (mandatory before implementation)

- **Module pack**: `apps/kentender_v1/docs/prompts/procurement planning v4/package wizard/` — `Planning Package Creation Wizard.md` (full spec, §1–§18) + `step 1/DESIGN.md` + `step 1/code.html` + `step 2/DESIGN.md` + `step 2/code.html` + `step 3/DESIGN.md` + `step 3/code.html` + `step 4/DESIGN.md` + `step 4/code.html` — all read end-to-end.
- **Tracker row**: none pre-existing. This file is the new canonical tracker for this sub-feature (sibling to `../workbench/WORKBENCH_WIRING_TRACKER.md`, which remains canonical for the 6-queue Workbench itself). Upstream dependency: the Workbench's `draft_packages` queue and placeholder-row "Create Package" action (see workbench tracker's "UX gap fix" section) is one of the entry points this wizard replaces.
- **Section map**:

  | Doc | Sections read |
  | --- | --- |
  | `Planning Package Creation Wizard.md` | §1–§18 (full) |
  | `step 1/code.html` + `DESIGN.md` | Full markup + design tokens |
  | `step 2/code.html` + `DESIGN.md` | Full markup + design tokens |
  | `step 3/code.html` + `DESIGN.md` | Full markup + design tokens |
  | `step 4/code.html` + `DESIGN.md` | Full markup + design tokens |

- **Requirements digest**:

  | Source | Requirement | Plan impact |
  | --- | --- | --- |
  | §5, §8.4 | Only eligible demands shown; multi-demand allowed with compatibility checks | PW2 eligibility API + compatibility-check API |
  | §6, §16 | 3-step wizard + success screen, two-column layout, shared header/stepper/footer | PW7 wizard shell/routing |
  | §8 | Step 1 demand cards + selection summary + empty state | PW8 |
  | §9 | Step 2 identity/method/lines-lots/funding/document sections + warnings | PW9, needs PW1 schema + PW3 service |
  | §10 | Step 3 review + readiness preview + blocking conditions | PW10, needs PW5 |
  | §11 | Success screen + post-creation state | PW11 |
  | §12 | Data created (Package, Lines, Evidence) | PW6 |
  | §13 | Role/permission gating | PW6/PW8 reuse existing PP2 role checks |
  | §14 | Business-readable error message catalog | PW9/PW10 (no raw codes) |
  | §15, §17 | No technical codes/handoff IDs/JSON in UI; no raw Frappe forms | Enforced across PW8–PW11; regression test in PW12 |
  | §18 | Final product rule (end-to-end planner journey) | PW12 Playwright E2E |

- **Precedence**: PP2 canonical-loader rule applies — this wizard is the
  **one canonical package-creation path** going forward; the old
  `pp2_planning_create_package_modal.js` dialog is legacy once PW11 ships
  and must be removed (thin references only if a test still needs the old
  API surface directly), not left running in parallel.
- **Repo inventory (existing, to extend)**:
  - `procurement_planning/doctype/procurement_package/procurement_package.json`, `procurement_planning/doctype/procurement_package_line/procurement_package_line.json`
  - `procurement_planning/services/package_creation_service.py` (today: single-demand, single-line, template-derived method only)
  - `procurement_planning/services/planning_inclusion_service.py` (has `list_unpackaged_planning_inclusions` — reuse as the Step 1 data source foundation)
  - `procurement_planning/api/planning_inclusion.py` (`get_pp_create_package_modal_drawer`, `create_pp_package_from_planning_inclusion` — legacy single-step path)
  - `public/js/pp2_planning_router.js` (`SURFACES` map + route dispatch — add a `package-wizard` surface here, same pattern as the existing `package-detail` surface)
  - `public/js/pp2_planning_create_package_modal.js` (to be retired in PW11)
  - `public/workbench_design/needs_planning_default.html` (pattern reference: one static HTML asset per surface, deployed byte-identical, JS mutates DOM only)

## Status legend

Same as `../workbench/WORKBENCH_WIRING_TRACKER.md`: ✅ Done (implemented,
tested, live-validated) · 🟡 Partial/in progress · ⬜ Not started · 🛑
Deferred (explicit user decision).

## Scope decisions confirmed with user (2026-07-04)

1. **Entry-point replacement**: the wizard **replaces** every existing
   "Create Package" trigger (Needs Planning selection-toolbar action,
   In-Creation placeholder-row action, package dashboard, plan detail,
   etc.). The old single-field modal is retired once PW11 ships.
2. **Multi-demand packaging**: build now — full multi-select + the 9
   compatibility checks from §8.4, not capped at one demand.
3. **Step 2 scope**: build the full field set now — package identity
   (owner, target release date, priority), method override + justification,
   editable lines/lots table (grouping supported; **splitting a demand-item
   line is explicitly out of scope**, per the spec's own §9.6 guidance to
   "avoid splitting demand items unless the system explicitly supports
   it"), funding section, document/STD-path section. This requires new
   `Procurement Package` fields (`package_owner`, `target_release_date`)
   and a `lot_group` field on `Procurement Package Line` — see PW1.
4. **Save Draft**: deferred (🛑) — not wired in any of the 4 mockups' JS,
   no described persistence model. Noted here so it isn't forgotten, same
   treatment as Export (W11) on the Workbench tracker.
5. **Compatibility-check data gaps**: donor/funding-restriction-conflict
   and confidentiality-conflict checks (§8.4) have **no backing data model
   today**. PW2 implements 6 checks against real data (entity/fiscal
   year/category/method/funding-source/timeline) and makes the
   donor/confidentiality checks pass-through (always "compatible") with a
   code comment flagging the gap — matching how Strategic Alignment (W13)
   was flagged as a data gap rather than faked. **Correction discovered
   during PW2 implementation**: package-value-threshold-conflict was
   originally assumed to be a 7th real-data check, but
   `Procurement Template.threshold_rules` interpretation is already a
   documented v1 no-op site-wide ("threshold bands deferred", see
   `procurement_package.py`'s template-defaults apply); inventing a
   one-off band interpreter just for the wizard would contradict that
   existing precedent (and the legacy-removal "no duplicated business
   logic" rule), so this check is also pass-through for now — **3 checks
   pass-through today, not 2**, until a real threshold-bands interpreter
   ships site-wide.
6. **`package_priority` field values**: spec uses Normal/High/Emergency;
   existing field uses High/Medium/Low. PW1 will change the Select options
   to `Normal\nHigh\nEmergency` and ship a data-fix patch remapping any
   existing `Medium`/`Low` rows to `Normal` (no functional users depend on
   the old values yet — pre-launch feature).

## Tickets

### PW1 — Schema: new fields for package identity/lines ✅ done

- `Procurement Package`: added `package_owner` (Link, User), `target_release_date` (Date); changed `package_priority` options to `Normal\nHigh\nEmergency` + `patches/pw1_backfill_package_priority_normal.py` remaps existing `Medium`/`Low` rows to `Normal`.
- `Procurement Package Line`: added `lot_group` (Data, optional) and `delivery_location` (Data, optional) per §9.6.
- **Evidence**: `tests/test_pw1_package_wizard_schema.py` — 5/5 passing (new field presence/config, priority options, backfill patch idempotent + remaps legacy values). `bench migrate` clean on `kentender.midas.com`.

### PW2 — Backend: Step 1 eligibility + compatibility API ✅ done

- `list_wizard_eligible_demands(plan_code, search=None)` (service) + `list_pp_wizard_eligible_demands` (whitelisted API, `api/package_wizard.py`): extends `list_unpackaged_planning_inclusions` output with the §8.3 field set (ref, department, category, funding label, strategy label, needed-by, documents count, status label) needed for demand cards — no technical codes surfaced (`inclusion_code` is the only opaque handle, needed by Step 1's own selection/compatibility calls, not rendered as an ID in the UI contract).
- `check_package_compatibility(inclusion_codes)` (service) + `check_pp_package_compatibility` (whitelisted API): implements 6 real-data compatibility checks from §8.4 (entity, fiscal year, category, method, funding-source, delivery/procurement timeline via `required_by_date` spread vs. template `procurement_cycle_days`); donor/funding-restriction-conflict, confidentiality-conflict, and package-value-threshold-conflict (see scope-decision correction above) are documented always-pass stubs. Returns `{compatible: bool, reasons: [...], demands: [...]}`.
- Both wrapped behind the same create-package permission gate as the legacy modal (`_create_package_gate` in `api/planning_inclusion.py`), reused rather than duplicated.
- New file: `services/package_wizard_service.py`.
- **Evidence**: `tests/test_pw2_wizard_eligibility_compatibility.py` — 7/7 passing (eligibility field shape, search filter, single/N-compatible/N-incompatible compatibility, both API wrappers behind the permission gate). Regression-checked: `test_pw1_package_wizard_schema` (5/5), `test_pw6_multi_demand_package_creation` (4/4), `test_pp2_create_package_p2_004` (5/5) all still green after adding `procurement_cycle_days` to `_resolve_template_for_demand`'s field list.

### PW3 — Backend: package/line configuration service (pre-create, no persistence) ✅ done

- `preview_package_configuration(inclusion_codes, config)` (service, added to `services/package_wizard_service.py`) + `get_pp_package_wizard_configuration_preview` (whitelisted API, `api/package_wizard.py`): pure computation over N inclusion codes + the planner's in-progress form input — package identity (title default from primary demand, owner default from session user, priority normalized to Normal/High/Emergency), category/method (recommended method from `_resolve_template_for_demand`, override flag + `method_justification_required` when the planner's chosen method differs), funding rollup (`package_estimated_value` = sum of demand totals, `reserved_amount`/`amount_available` from the linked Budget Line(s) via `kentender_budget`'s canonical `check_available_budget`, `funding_status` Reserved/Insufficient/Blocked), one line per selected demand (existing v1 granularity — **no demand-item splitting**, consistent with the scope decision) with `lot_group`/`delivery_location` pass-through from per-line overrides, and §9.8 business-readable warnings (funding exceeded, method override missing justification, missing specifications). **Never writes to the DB** — regression-tested (`test_preview_never_persists_a_package`).
- **Evidence**: `tests/test_pw3_wizard_configuration_preview.py` — 9/9 passing (identity defaults, config overrides, method-override-without-reason warning, funding rollup for 2 demands, missing-spec warning, line overrides, no-persistence guard, empty-selection rejection, API wrapper behind the permission gate).

### PW4 — Backend: document/STD path readiness surfacing ✅ done

- `preview_document_std_path(inclusion_codes, config)` (service) + `get_pp_package_wizard_document_path_preview` (whitelisted API): §9.7 read-only surfacing. **Reuses the canonical planning-to-tender STD resolution** (`resolve_std_template_for_handoff` in `tender_management/services/std_template_handoff_resolution.py`, doc 2 sec. 12.1) against a plain-dict stand-in for the not-yet-created `Procurement Package` — no duplicate wizard-only STD interpreter (per the legacy-removal "no duplicated business logic" rule). Surfaces `required_document_family` (category), resolved STD path label + code, `resolution_path` (`default_std_template`/`mapping_service`/`works_poc_fallback`/`ambiguous`/`invalid_default`/`unresolved`), specification-attachment count inherited from the selected demand(s) (reuses PW2's `_documents_count`), and §9.8 business-readable warnings ("Tender document path has not been selected.", ambiguous-candidates message, missing-specifications message).
- **Evidence**: `tests/test_pw4_wizard_document_std_path.py` — 5/5 passing (required-document-family surfaced, zero-documents warning, resolved-vs-unresolved STD path branches, empty-selection rejection, API wrapper behind the permission gate).

### PW5 — Backend: readiness preview / blocking conditions (Step 3) ✅ done

- `evaluate_wizard_readiness(inclusion_codes, config)` (service) + `get_pp_package_wizard_readiness` (whitelisted API): composes PW2's inclusion lookups, PW3's configuration preview, and PW4's document-path preview into the §10.3 7-row readiness checklist (approved demand selected, active plan exists, funding linked/reserved, category selected, method selected, package lines will be created, documents inherited/identified) each mapped to Ready/Warning/Blocked, plus an overall `create_allowed` flag and business-readable `blocking_reasons` covering §10.5's conditions (no demand selected, demand not approved, demand already packaged, no active plan, missing category/method, package title missing, line-cannot-be-created, permission denial via `pp_policy.assert_may_create_package_from_inclusion`). This is the single source of truth the "Create Package" button's disabled state will read from in PW10.
- **Evidence**: `tests/test_pw5_wizard_readiness.py` — 6/6 passing (empty selection blocked, fully-eligible happy path all-Ready, unapproved-demand blocks, inactive-plan blocks, already-packaged-inclusion blocks, API wrapper behind the permission gate). Full PW1–PW6 regression re-run together: 36/36 passing.

### PW6 — Backend: final create orchestration API ✅ done

- ✅ **Underlying primitive done**: `create_package_with_lines(inclusions, actor, package_overrides=None, line_overrides_by_inclusion=None)` in `services/package_creation_service.py` — creates one `Procurement Package` + one `Procurement Package Line` per selected inclusion, applies package-level overrides (`package_owner`, `package_priority`, `target_release_date`, name) and per-line overrides (`lot_group`), marks all N inclusions packaged. `_create_package_and_line`/`create_package_from_planning_inclusion` (legacy single-demand path) now delegate to it — regression-guarded (`test_single_inclusion_legacy_shape_unaffected`). Also fixed a pre-existing bug in `planning_inclusion_service._inclusion_handoff_code` (was always generating suffix `001`, so a 2nd demand's inclusion under the same plan silently overwrote the 1st's handoff card) — required for any multi-demand flow to work at all.
- ✅ `create_package_from_wizard(inclusion_codes, config, actor)` in `services/package_wizard_service.py` — re-runs PW5's `evaluate_wizard_readiness` as the authoritative server-side gate (rejects with `WIZARD_NOT_READY` + `blocking_reasons` if not `create_allowed`, never trusting client-staged state), re-asserts `pp_policy.assert_may_create_package_from_inclusion()`, derives `package_overrides`/`line_overrides_by_inclusion` from PW3's `preview_package_configuration` output, delegates the actual insert to `create_package_with_lines` (no duplicated creation logic — the duplicate-package guard is the readiness check's `demand_selected`/`_inclusion_is_unpackaged` check, which already covers all selected inclusions, not just the primary), then records a **"Package Wizard Completed"** `Planning Audit Event` (§12.3's "wizard completion record", on top of the primitive's own "Package Created"/"Package Line Created" events) and returns the package/plan/demand-titles shape the Step 4 success screen needs (§11.2/§11.3).
- ✅ Whitelisted API: `create_pp_package_from_wizard(inclusion_codes, config)` in `api/package_wizard.py` — same `_create_package_gate()` permission gate as every other wizard endpoint, catches `ValidationError`/`PermissionError` into the standard `{ok: False, error_code, message}` shape.
- ✅ **Evidence**: `tests/test_pw6_wizard_create_orchestration.py` — 4/4 passing (blocked/not-ready selection creates nothing, single demand creates package + line with Step-2 overrides (title/owner/priority/lot/delivery-location) and records the "Package Wizard Completed" evidence event, two compatible demands create one package with two lines, whitelisted API wrapper behind the permission gate). Full PW1–PW6 regression re-run together: 36/36 passing (5+7+9+5+6+4).

### PW7 — Frontend: wizard shell + routing ✅ done (implementation deviates from pixel-perfect static-HTML plan — see below)

- **Scope pivot (user-directed, 2026-07-04)**: mid-implementation the user explicitly relaxed both the TDD-per-ticket cadence and pixel-perfect fidelity ("you may skip repeated TDD steps... you do not have to be 100% pixel precise — make the best judgement on the fastest implementation"). Given that, the wizard shell was built as a sequence of four `frappe.ui.Dialog` instances (`public/js/pp2_planning_package_wizard.js`, `kentender_procurement.PlanningPackageWizard.open(...)`) instead of deploying `step 1..4/code.html` as iframe-embedded static assets with cross-frame DOM wiring. This trades exact pixel fidelity to the 4 mockups for materially lower state-management/wiring risk (native Dialog field binding vs. cross-iframe postMessage-style plumbing) while preserving every functional requirement (§8–§11 field sets, step order, Cancel/Back/Next, business-readable copy, no technical-code leakage).
- `step 1..4/code.html` remain deployed byte-identical under `public/workbench_design/package_wizard_step{1..4}.html` as **design references only** (inline demo/simulation `<script>` blocks stripped and replaced with comments pointing at the real wiring file) — not loaded at runtime.
- Session-scoped wizard state (`WizardCtx`): selected inclusions (`Map` keyed by inclusion code) + in-progress `config` object, held in memory only, discarded on Cancel/close/Create-success (no server draft, matching the Save Draft deferral below).
- All three existing "Create Package" triggers route through a single `openPlanningPackageWizard(...)` launcher in `pp2_planning_router.js` (Needs Planning selection-toolbar, In-Creation placeholder row, "Add to Plan" success screen's next-action) — see PW11.
- **Evidence**: `pp2_planning_package_wizard.js` registered via `app_include_js` in `hooks.py`; live-validated end-to-end via Playwright MCP browser session (see PW12) and the new automated `procurement-planning-package-wizard-journey-pw12.spec.ts`.

### PW8 — Frontend: Step 1 — Select Demands ✅ done

- `openStep1` renders demand cards from PW2's `list_pp_wizard_eligible_demands`, checkbox multi-select (`data-testid="pp2-wizard-demand-checkbox"`), running "Package Selection Summary" (`pp2-wizard-selection-summary`: count, total value, category) driven by `check_pp_package_compatibility` on every selection change, inline compatible/incompatible banners (`pp2-wizard-compatible` / `pp2-wizard-incompatible`) with §8.4 business-readable reasons, search box (client-side filter over title/department/ref), empty state (`pp2-wizard-empty-state`). Pre-selected inclusions (from placeholder-row/toolbar entry points) are checked and synced into `ctx.selected` from the fetched demand list so the summary reflects real values immediately, not just the caller's opaque code.
- **Evidence**: exercised live end-to-end via the new Playwright spec (checkbox pre-checked + compatible banner visible) and the PW2 backend suite (7/7) for the underlying compatibility logic. Source-level regression left to the existing PW2 unit tests rather than a duplicate JS-source test, per the speed-over-ceremony direction.

### PW9 — Frontend: Step 2 — Configure Package ✅ done

- `openStep2` wires Package Identity (title/description/owner/target release date/priority), Category & Method (+ override-reason field, shown via `method_override_flag`), an editable Lines & Lots table (`pp2-wizard-lines-table`: per-line lot-group + delivery-location inputs, no split per scope decision), a Funding summary (`pp2-wizard-funding-summary`) and Document/STD-path summary (`pp2-wizard-doc-path-summary`), and a warnings list (`pp2-wizard-warnings`) — all populated from PW3's `get_pp_package_wizard_configuration_preview` and PW4's `get_pp_package_wizard_document_path_preview`, re-fetched (debounced) on every field `onchange` so the previews always reflect the planner's in-progress input before Step 3.
- **Evidence**: live-validated via the new Playwright spec (lines table, funding summary, doc-path summary all assert-visible with real backend values) plus the PW3 (9/9) and PW4 (5/5) backend suites covering the preview computations those sections render.

### PW10 — Frontend: Step 3 — Review and Create ✅ done

- `openStep3` renders the full review rollup (title/owner/priority/category/method/selected-demand-count) from PW3's preview and the §10.3 readiness checklist (`pp2-wizard-readiness-row`, `data-status="Ready|Warning|Blocked"`) from PW5's `get_pp_package_wizard_readiness`; the `Create Package` primary button is disabled whenever `create_allowed === false` and re-enabled once the async readiness call resolves `true`; blocking reasons render inline (`pp2-wizard-blocking-reasons`) per §10.4/§10.5. On click, calls PW6's `create_pp_package_from_wizard`, destroys the dialog, and opens Step 4 on success (re-enables the button and shows a business-readable error via `frappe.msgprint` on failure, no raw exception text).
- **Evidence**: blocked-path automated in the new Playwright spec (`data-status="Blocked"` on the funding row + `Create Package` button asserted disabled, driven by the canonical seed's real budget shortfall — a genuine `kentender_budget` business rule, not a wizard defect). Happy path (button enabled, click → Step 4) was live-validated interactively via the Playwright MCP browser driver in this session (temporarily raised `BUD-MOH-INFRA-2026-001.amount_allocated`, walked Steps 1→2→3→Create→success screen, confirmed the created `Procurement Package` record, then reverted the budget line and reset the WORKS master seed to `INCLUDED_IN_PLAN` to restore canonical state for other specs) — this exact transition is **not yet** captured as a repeatable automated Playwright spec; see PW12 gap note.

### PW11 — Frontend: Step 4 success screen + entry-point replacement ✅ done

- `openStep4Success` (§11) shows the created package name + included demand titles and two actions: `Open Package` (`frappe.set_route("procurement-package", ...)`) and `Back to Workbench` (`onCancel`/workbench refresh) — `View Evidence` was not present in any of the 4 mockups' actual button rows so was not fabricated (no data/UI source for it beyond the general evidence drawer already reachable from the package detail surface).
- All three existing "Create Package" triggers replaced to call `openPlanningPackageWizard(...)` instead of `PlanningCreatePackageModal.open(...)` / the direct single-inclusion create API: `workbenchCreatePackagesFromSelectedDemands` (Needs Planning toolbar — now includes each selected demand then opens the wizard pre-selected with all resulting inclusions), `workbenchCreatePackageFromInclusionRow` (In-Creation placeholder row), `openCreatePackageModalForShell` (Add-to-Plan success screen's next action — keeps the existing drawer pre-flight call for the "duplicate package" / "not ready" blocker dialogs, then opens the wizard instead of the old modal).
- `pp2_planning_create_package_modal.js` is **not yet deleted from disk** — it is fully unreferenced by the router (grep-verified) but `test_pp8_technical_leakage_p8_006.py`-style tests and other legacy-modal-specific specs (`test_pp5_create_package_modal_p5_005.py`'s asset-registration/rendering tests) still exercise it directly; deleting it is a follow-up cleanup, not blocking, since it is provably dead code from the router's perspective.
- **Evidence**: `test_pp4_workbench_needs_planning_actions_w5.py`, `test_pp4_workbench_package_queues_w6.py`, `test_pp5_create_package_modal_p5_005.py` all updated and green (source-level assertions that each entry point now calls the wizard, not the old modal/API) — 11+2, 18, 3+1 tests respectively, all passing. Step 4 rendering live-validated via the Playwright MCP session (PW10 note above).

### PW12 — Full regression suite + Playwright E2E 🟡 partial (one documented automation gap)

- Backend unit/integration tests for PW1–PW6: **36/36 passing** (5 + 7 + 9 + 5 + 6 + 4, re-run together after every subsequent ticket).
- Router-wiring source-level tests updated for PW11's entry-point replacement (see PW11 evidence) — all green.
- **New**: `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-package-wizard-journey-pw12.spec.ts` — real Playwright browser test against the canonical WORKS master seed (`INCLUDED_IN_PLAN` checkpoint, reset in `beforeAll`): opens the wizard from the real In-Creation placeholder row, walks Step 1 (pre-selected + compatible) → Step 2 (lines/funding/doc-path sections render live data) → Step 3 (readiness checklist renders `data-status="Blocked"` for the funding row and the `Create Package` button is asserted disabled) — **passing**.
- **Documented gap**: the enabled-Create-button → successful-create → Step 4 success-screen transition is covered by (a) the PW6 backend integration suite exercising the identical `create_pp_package_from_wizard` orchestration Step 3 calls, (b) PW5's `test_fully_eligible_demand_allows_create` proving the same readiness gate correctly returns `create_allowed=True` for a fully-funded fixture, and (c) one interactive manual validation via the Playwright MCP browser driver in this session (not a committed, repeatable spec — the canonical seed's shared budget line is intentionally short of "available" headroom, so a deterministic automated happy-path spec needs either an isolated fixture unrelated to the shared WORKS master seed, or a dedicated budget-sufficient seed checkpoint; neither exists yet). Follow-up: add an isolated-fixture Playwright spec for the happy-path create → Step 4 transition.
- No-technical-leakage: no new leakage introduced by the wizard file (`pp2_planning_package_wizard.js` is clean); the one failing `test_pp8_technical_leakage_p8_006.py` assertion is **pre-existing** and unrelated (a `hasTechnicalLeakage()` detector regex literal inside `pp2_planning_include_plan_modal.js` contains the substring `source_object_code` as pattern text, which the naive substring-scan test flags — not an actual UI leak; that file was not touched by this wizard work).

### PW13 — Documentation ✅ done

- This tracker updated with statuses/evidence per ticket (above).
- Cross-link: `../workbench/WORKBENCH_WIRING_TRACKER.md`'s "UX gap fix" section (In-Creation placeholder row) should be read together with PW11 above — the placeholder row's click target now opens this wizard pre-selected, superseding that section's original direct-create-API description.
- **Named caveats** (not silently dropped):
  1. **Save Draft** — deferred (🛑). No mockup wires a Save Draft action; wizard state is in-memory only and lost on cancel/close.
  2. **Compatibility-check data gaps** — donor/funding-restriction-conflict, confidentiality-conflict, and package-value-threshold-conflict (§8.4) are always-pass stubs pending real backing data models / a site-wide threshold-bands interpreter (see scope-decision §5 above for the full rationale).
  3. **Pixel fidelity deviation** — Steps 1–4 are native `frappe.ui.Dialog` renders, not the byte-identical iframe-embedded mockups used elsewhere in the v4 Workbench; this was an explicit, user-directed scope trade (speed over visual fidelity) for this sub-feature only, and does not change the precedent for the rest of the Workbench.
  4. **PW12 happy-path automation gap** — see PW12 above.
  5. **Legacy modal not deleted** — `pp2_planning_create_package_modal.js` is dead code (unreferenced by the router) but left on disk pending a follow-up cleanup of the tests that still exercise it directly.
