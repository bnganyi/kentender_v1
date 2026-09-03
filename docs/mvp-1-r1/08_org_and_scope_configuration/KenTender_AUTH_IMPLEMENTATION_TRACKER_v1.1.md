# AUTH-ADR-001 v1.3 — role-bound responsibility cutover — tracker

**Authority:** `KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1.3.md`
(proposed for approval, 1 September 2026), including the complete administration UI contract in §12, with the two module correction slices
`KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1.3.md` §16.4 and
`KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1.4.md` §16.4.

**Visual review artifact:** `KenTender_AUTH-UI-001_Administration_Prototype_v0.1.html`.

**Status:** **P1–P3 verified; P5 live in the browser.** 2026-09-01 evening:
the Project Owner clarified that D5 ("do not seed") never meant "do not build" —
`bench migrate` and the kentender_core asset build have now run. The two
Configuration and Governance surfaces are live at `/desk/organisation-structure`
and `/desk/user-responsibilities`, appear in the shared sidebar, and the five
new test modules run green (11 + 10 + 38 + 26 + 25 = **110 tests OK**). The
seed world (PE-CGKIS etc.) remains unrestored, so the NDS/Planning baseline is
still not reproducible — that part of D5 stands. Evidence in the
**Verification run** section below.

**Started:** 2026-09-01.

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Blocked`, `Done`.
2. `Done` requires the row's own evidence — a command with its result, a named
   test, a diff, or a described browser observation. "Looks right" is not
   evidence, and a result that was not observed is never recorded.
3. A row that leaves production code reading a retired authority store
   (Frappe `User Permission`, `User Scope Assignment`, `Capability Profile`,
   `Operational Scope Assignment`, `kt_primary_department`, `Procuring
   Department`, or a browser context) is not `Done`.
4. Deletion lands in the same phase as its replacement. "Delete later" is not a
   valid row state.
5. No fallback chain. A caller is flipped onto the resolver exactly once and
   never reads two stores (§15.4).
6. Staged caller migration is not a fallback: the retired stores stay on disk,
   unread by any flipped caller, until P10.

## Baseline, captured 2026-09-01 before any edit

The trackers for NDS (v1.1) and Planning (v1.2) both close on a green suite.
That baseline is **not reproducible on this site today**: the site holds one
Procuring Entity (`PE-MOH`) and no `PE-CGKIS`, so every Departmental Needs and
Procurement Planning module errors in setup with
`LinkValidationError: Could not find For Value: PE-CGKIS` and runs zero tests.

| Module | Result |
|---|---|
| `kentender_core.tests.test_authorization_native` | Ran 12, OK |
| `kentender_core.tests.test_authorization_role_registry` | Ran 13, FAILED (failures=1) |
| `kentender_core.tests.test_auth_migration_inventory` | Ran 7, FAILED (failures=1) |
| `kentender_core.tests.test_working_context_service` | Ran 16, OK |
| `kentender_core.tests.test_master_data` | Ran 1, FAILED (errors=1) |
| `kentender_core.tests.test_kentender_mvp_v1_seed_contract` | Ran 0, FAILED (errors=1) |
| `departmental_needs.tests.*` (6 modules) | Ran 0 in 5 of 6; `test_departmental_needs_architecture` Ran 8, OK |
| `procurement_planning.tests.*` (7 modules) | Ran 0 in 5 of 7; `test_planning_context_ctx_chg_001` Ran 3, OK; `test_planning_v12_schema` Ran 6, FAILED (failures=1, skipped=1) |

The two suites that do run green — the NDS architecture guard and the Planning
v1.2 static scan — are the ones that read source files rather than site data,
which is consistent with the cause being missing fixtures rather than code.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-01 | **D1 (Project Owner).** Cut over Departmental Needs, Procurement Planning, Strategy, Budget and Reference Data in one controlled release. Everything else keeps its present mechanism behind a static guard. | Wider than the two modules with approved §16.4 slices, narrower than the whole repo: `procurement_lifecycle`, `tender_management`, STD Configuration, suppliers and the bidder workspace have no successor document, so their role vocabularies would have to be invented. |
| 2026-09-01 | **D2 (Project Owner).** Convert `Organisation Unit` to a Frappe nested set and retire `Procuring Department` in the same slice. | AUTH-AC-005/006/017/018 cannot be demonstrated without the tree, and a second unreferenced hierarchy is exactly the §2.3 defect. |
| 2026-09-01 | **D3 (Project Owner).** The §12 Organisation structure and User responsibilities surfaces are Vue 3 KenTender administration pages in Frappe Desk. Their Claude Design artboards are approved before production Vue implementation. | AUTH-ADR-001 v1.3 §12 is the complete functional and static design contract. Claude Design is visual evidence to hand-port; generated runtime code is not shipped. |
| 2026-09-01 | **D4 (Project Owner).** Migration is a read-only §15.1 reconciliation report plus rewritten seeds, not a data-conversion patch. | The personas come from deterministic seeds; a conversion patch would be production code with no production data to convert. |
| 2026-09-01 | **D5 (Project Owner).** Do not write site data until the Project Owner restores the seed world. Author code and tests; run nothing. | The site is missing `PE-CGKIS` and the seed restore is a data-writing action on the Project Owner's dev site. Consequence recorded honestly: **every row below is authored and statically checked, none is verified.** |
| 2026-09-01 | **D6.** `exclusive_office` is False for every registered responsibility. | §5 requires the property; no approved module document declares an exclusive office, and inventing one would be a business rule. §4.2's no-overlap rule already prevents two Enabled assignments for the same tuple, and NDS §14.2 deliberately seeds a substantive Head of User Department at a parent OU alongside an acting one at a descendant leaf — a subtree-wide office rule would reject an approved fixture. |
| 2026-09-01 | **D7.** The §4.1 status and appointment vocabulary lives in `responsibility_resolver`, not on the DocType controller. | The controller, the administration service and every caller share one definition without any of them importing a controller module. |
| 2026-09-01 | **D8.** No caching in the resolver. | Every query is indexed and small; a permission cache is the classic source of stale-authority defects, and §8.2 requires the server to resolve again on every command. Revisit only on a measurement. |

## Open conflicts between approved documents

Recorded rather than silently resolved (AGENTS.md §1). Each blocks only the
phase that needs it.

| # | Conflict | Recommended reading | Blocks |
|---|---|---|---|
| C1 | ADR §5 classifies Strategy Author/Approver as Procuring Entity; STR-CHG-001 v1.5 §7 says "permitted PE/OU scope". | Register both as PE-scoped per ADR §14; any departmental narrowing stays a record-ownership check inside Strategy. Applied in the registry, flagged here. | P7 |
| C2 | PLN-CHG-001 v1.4 §6 gives Planning Finance confirmation to *Budget Officer*; BUD-CHG-001 v1.2 §7 gives it to *Finance Confirmation Officer*. | Register both; keep Planning's current required responsibility unchanged; record for whichever document is revised next. | P9 |
| C3 | Budget's empty scope currently means every PE (`budget_authorization.py:176-178`). Under the ADR it must fail closed, invalidating `ensure_scopeless_budget_viewer`. | Fail closed; give that fixture a real assignment. | P7 |
| C4 | NDS §6 registers `Auditor`; PLN §6 registers `Planning Auditor`. | Keep both; §5 makes the module document the source of the exact role name. | — (applied) |
| C5 | §12.7 requires both pages to register in `cl_surface_registry` **and** `STITCH_DESK_SURFACES`. Neither is right for an Industry Vue page: `STITCH_DESK_SURFACES` is the registry for Tailwind/Stitch-HTML canvases, and its own docstring records three times that hand-authored Vue Industry pages (Strategy, Budget, Needs, Planning) deliberately get no row — a row there would make `ui-stitch-desk-chrome-gate` demand `kt-stitch-canvas` markup on a new Industry page, which AGENTS.md §6.6 forbids. `kt_cl_surface_registry.js` is the Civic Ledger chrome router; `reference-data`, the sibling Configuration and Governance Vue page, is in neither. | Follow the sibling precedent: register in neither, and participate in the shared shell exactly as `reference_data_page.js` does (`enterNative()` for the native sidebar, chrome host forced empty, own `PageRail.vue`). Recorded rather than silently obeyed or silently skipped. | — (applied, needs owner confirmation) |
| C6 | §12.1.2's add dialog collects no Organisation Unit Type, but `unit_type` was a required Link on the DocType. | Make `unit_type` optional. Existing records keep theirs and the tree shows it where present; nothing invents a governed type vocabulary to satisfy a required field. | — (applied) |

## Phase rows

| ID | Phase | Row | Status | Evidence |
|---|---|---|---|---|
| AUTH-001 | P0 | Baseline capture and tracker | Done | The baseline table above, captured from 19 module runs before any edit. |
| AUTH-101 | P1 | `Organisation Unit` becomes a Frappe nested set (`is_tree`, `nsm_parent_field`, `lft`/`rgt`/`old_parent`) | In progress | `organisation_unit.json` edited; JSON re-parsed and field_order/fields verified consistent. **Not migrated, not run.** |
| AUTH-102 | P1 | Controller extends `NestedSet`; PE boundary enforced on parent and on PE reassignment | In progress | `organisation_unit.py` rewritten; imports cleanly under a frappe stub. `validate_one_root` deliberately never called — KenTender has one root per PE. |
| AUTH-103 | P1 | `rebuild_tree` patch | In progress | `patches/v1_0/auth_adr_001_v12_organisation_unit_nested_set.py`, registered in `patches.txt`. Guarded on the column existing so a pre-migrate run is a no-op. **Not run.** |
| AUTH-104 | P1 | `descendant_org_units` becomes one `lft`/`rgt` range query | In progress | `services/org_scope_access.py`; falls back to the node itself when ranges are unstamped, so a pre-patch site degrades to leaf-only scope instead of denying everything. |
| AUTH-105 | P1 | Tree tests | In progress | `tests/test_organisation_unit_tree.py` — 10 cases covering AUTH-AC-005/006/017. **Authored, not run.** |
| AUTH-201 | P2 | Code-owned business-role registry | In progress | `services/business_role_registry.py` — 14 responsibilities, each naming its owning document. Verified under a frappe stub: scope types, subtree/tag queries and the unregistered-role refusal all behave. |
| AUTH-202 | P2 | §13 error contract | In progress | `services/responsibility_errors.py` — closed set of eight codes; `fail()` raises `ValueError` on anything outside it. |
| AUTH-203 | P2 | `ensure_roles()` wired into `after_migrate` | In progress | `install.py::_ensure_business_role_projections`. Closes the gap where role provisioning was imperative and seed-only. **Not run.** |
| AUTH-204 | P2 | Registry tests | In progress | `tests/test_business_role_registry.py` — 11 cases. **Authored, not run.** |
| AUTH-301 | P3 | `User Responsibility Assignment` DocType | In progress | §4.1 fields exactly; no Financial Year, module, capability string or policy JSON. Identity fields are `set_only_once`. |
| AUTH-302 | P3 | Controller invariants | In progress | Scope-type consistency, OU ∈ PE, period ordering, acting authority reference. `is_effective()` evaluates expiry at command time (§4.3). |
| AUTH-303 | P3 | Shared resolver | In progress | `services/responsibility_resolver.py` — the §8.1 operations. Reads and commands split only on technical status (§11). |
| AUTH-304 | P3 | Administration service with Role-projection sync | In progress | `services/responsibility_administration.py` — grant/revoke/list/describe, overlap settled under `SELECT … FOR UPDATE`, projection removed only when no other active assignment needs it. |
| AUTH-305 | P3 | Whitelisted API facade | In progress | `api/responsibility_api.py` — explicit signatures, no `**kwargs` (the NDS-914 defect class). |
| AUTH-306 | P3 | Resolver test suite | In progress | `tests/test_responsibility_resolver.py` — 33 cases across §17.1–17.15. **Authored, not run.** |
| AUTH-401 | P4 | §15.1 reconciliation report | In progress | `scripts/responsibility_reconciliation.py` — read-only; §15.2's mapping rules enforced as refusals with an exact reason, never as guesses. **Not run.** |
| AUTH-402 | P4 | Core seed rewrite onto assignments | Planned | Blocked on D5. |
| AUTH-500 | P5 | Claude Design artboards AUTH-DES-01–05 from the closed §12 fixture contract | Done | Supplied by the Project Owner at `08_org_and_scope_configuration/design/` — five `.dc.html` artboards plus the fixture index. Their `_ds` export is the Industry system with unprefixed class names, so the port is mechanical: `blueprint`→`kt-blueprint`, `card`→`kt-card`, `btn btn-primary`→`kt-btn kt-btn-primary`. |
| AUTH-501 | P5 | Register both surfaces under Configuration and Governance | In progress | Pages `organisation-structure` / `user-responsibilities` (module Kentender Core, Administrator + System Manager); `page_js` entries in `kentender_core/hooks.py`; two links at the head of the **Configuration and Governance** section of `workspace_sidebar/procurement.json`; Card Break, links and shortcuts on the `Platform Configuration & Governance` workspace. Registered in neither shared registry — see C5. **Not migrated, not opened in a browser.** |
| AUTH-502 | P5 | Organisation structure Vue page | In progress | `public/js/organisation_structure/` — `OrganisationStructure.vue` plus `UnitTree`/`UnitDetail`/`PromptDialog`/`ConfirmDialog`. PE selector, searchable tree, selected-unit panel, and every §12.1.3 state (no PE, needs repair, empty root, forbidden, load failure). Compiles under `@vue/compiler-sfc`; `.kt-industry` root and `globalProperties.__` binding both verified. |
| AUTH-503 | P5 | Organisation Unit administration APIs | In progress | `services/organisation_structure.py` + `api/organisation_structure_api.py`: tree projection, add child, rename, activate/deactivate and the governed `repair_pe_root`. One root per PE, generated `OU-{PE}-#####` codes, normalized sibling uniqueness, PE boundary, `modified` as the concurrency token. No delete, no reparent (§12.1.2). |
| AUTH-504 | P5 | User responsibilities register | In progress | `UserResponsibilities.vue` + `list_user_responsibilities`. All nine §12.2 columns, derived status, five filters with a debounced quiet refresh, and a `["user-responsibilities","unit",<id>]` route so the deep link from Organisation structure survives a refresh. |
| AUTH-505 | P5 | Assign responsibility dialog | In progress | `AssignDialog.vue` + `preview_assignment`. Fields appear only from the registry's scope classification; the summary, descendant count, per-field problems and the exact conflicting assignment all come from the server, and the primary button stays disabled with a visible reason until the preview says ok. |
| AUTH-506 | P5 | Responsibility detail, diagnostics and revoke | In progress | `ResponsibilityDetail.vue` + `RevokeDialog.vue` + `get_assignment_detail`. Full §12.4 detail, collapsed §12.6 diagnostics, no Edit action, revoke gated on a 10–500 character reason and an expected version. |
| AUTH-507 | P5 | Service and API contract tests | In progress | `tests/test_organisation_structure.py` (26 cases) and `tests/test_responsibility_administration.py` (25 cases). **Authored, not run.** Vue component tests are still owed — the repo's vitest projects are per-app and none covers `kentender_core` yet. |
| AUTH-508 | P5 | Browser acceptance journey | Blocked | Blocked on D5. PE root → add OU → assign → act → revoke → immediate denial, with direct load, refresh, back/forward and the return path. |
| AUTH-6xx | P6 | Cutover slice A — core consumers | Planned | |
| AUTH-7xx | P7 | Cutover slice B — Strategy and Budget | Planned | C1 and C3 to be settled first. |
| AUTH-8xx | P8 | Cutover slice C — Departmental Needs | Planned | |
| AUTH-9xx | P9 | Cutover slice D — Procurement Planning | Planned | C2 to be settled first. |
| AUTH-10xx | P10 | Removal of the retired stores and the static scan | Planned | |
| AUTH-11xx | P11 | Cross-module gate and release evidence | Planned | |

## Verification run — 2026-09-01 evening

Executed after the Project Owner's clarification of D5:

1. `bench --site kentender.midas.com migrate` — clean.
   `auth_adr_001_v12_organisation_unit_nested_set` ran ("Success: Done in
   0.102s"); the two Pages, the sidebar links and the workspace card synced;
   `ensure_roles()` created the missing projections (`Plan Statutory Approver`,
   `Finance Confirmation Officer` verified present).
2. `bench-with-node.sh build --app kentender_core` — both bundles built, hashes
   confirmed changed on the rebuild (`organisation_structure.bundle.QNNOVIAJ`,
   `user_responsibilities.bundle.CK5ZQPIR`).
3. Discovered while wiring the build: **this bench's esbuild pipeline discards
   the CSS it extracts from `<style scoped>`** — no dist/css output, no
   assets.json entry, no runtime injection. All nine SFCs' styles were moved to
   `public/css/kt_admin_configuration.css` (scoped under `.kt-industry`,
   comment-safety and brace-balance parse-verified), registered in
   `app_include_css` with `_asset_version`, matching the NDS/Planning
   `*_industry.css` precedent. The SFCs now carry no style blocks.
4. Browser pass as Administrator (Playwright): sidebar shows both entries under
   **Configuration and Governance**; Organisation structure rendered the exact
   §12.1.3 *needs repair* state; `repair_pe_root("PE-MOH")` created root
   `PE-MOH`; reload showed the tree + *empty root* state; **Add organisation
   unit** dialog created *Digital Health* → `OU-MOH-00001`, tree re-rendered
   with the detail panel. User responsibilities rendered the register empty
   state with all five server-fed filters; the assign dialog walked
   user → responsibility → PE → OU and rendered the server preview sentence
   ("Bonface R Nganyi will be Departmental Author for Digital Health from now
   with no scheduled end."), primary enabling only then; cancelled without
   creating an assignment. Zero console errors on every page (all warnings are
   Frappe's own icon-preload noise).
5. Focused suites, red→green with four findings fixed at their source:
   - `Procuring Entity` requires `reporting_currency` — test fixtures now set
     `KES`;
   - Frappe flips a role-less user to `Website User` on save, which the
     administration service rightly refuses — test users now get `Desk User`,
     the same baseline every seed grants;
   - `parent_org_unit in ('', NULL)` never matches SQL `NULL` through
     `frappe.db.count` — service and test now use the `("is", "not set")`
     filter;
   - the `PE-` prefix strip in `_generate_code` hit an embedded `PE-` anywhere
     in an entity code — now strips only a leading prefix.

6. **Project Owner rule (2026-09-01): test data never stays in the
   database.** All four fixture-bearing modules now register
   `kentender_core.tests.responsibility_test_cleanup.purge` as a class cleanup
   (deletes only by the fixtures' own constructed patterns — `KT-TEST-%`
   entities/unit types, `kt.test.%` users, `KT_TEST_%` namespaces — in
   dependency order, leaves-first for the nested set), and the same function is
   `bench execute`-able for residue from a crashed run. Applied retroactively:
   12 units, 7 test entities, 9 test users, 2 unit types and the
   browser-walkthrough `OU-MOH-00001` were purged; all four suites then re-ran
   green (10 + 38 + 26 + 25) and the post-run check showed 0 test PEs, 0 test
   users, 0 assignments and exactly one Organisation Unit — the `PE-MOH` root
   from the governed repair, which is bootstrap, not test data.

| Module | Result |
|---|---|
| `test_business_role_registry` | Ran 11, OK |
| `test_organisation_unit_tree` | Ran 10, OK |
| `test_responsibility_resolver` | Ran 38, OK |
| `test_organisation_structure` | Ran 26, OK |
| `test_responsibility_administration` | Ran 25, OK |

Still owed for P5: Vue component tests (no vitest project covers
`kentender_core` yet — AUTH-507's second half) and the full AUTH-508 journey
(assign → act in Departmental Needs → revoke → denial), which needs the module
cutover (P8) before a Needs action can consume an assignment.

## What has not been run, and why

Nothing in P1–P4 has been executed: no `bench migrate`, no test, no seed, no
browser pass. The Project Owner's D5 decision holds every site write until the
seed world is restored. Static verification only:

- every changed and new Python module imports cleanly against a frappe stub;
- both changed DocType JSONs re-parse and their `field_order` matches `fields`;
- the registry's scope types, subtree queries and refusal path were exercised
  directly;
- `_periods_overlap` was exercised for the open-ended, disjoint and touching
  cases;
- all nine new `.vue` files compile under `@vue/compiler-sfc` — template,
  `<script setup>` and scoped styles — as do the seven existing Reference Data
  components, unchanged;
- both static UI gates' own rules were re-run directly over the new bundles:
  each mounts a `.kt-industry` root, binds `globalProperties.__`, and imports no
  CSS at bundle top level. No new CSS file was added at all; the only file that
  declares Industry tokens is still `kt_industry_tokens.css`;
- the DB-free service logic was exercised against the stub: normalized sibling
  comparison, the 2–160 name gate, all five coverage labels and all four derived
  statuses.

The first real verification step remains `make migrate SITE=kentender.midas.com`
— which runs the nested-set patch, `ensure_roles()` and the two new Pages — then
the four new focused test modules, then `repair_pe_root` for PE-MOH before the
Organisation structure page has a root to show.

The first real verification step, once the site is restored, is
`make migrate SITE=kentender.midas.com` (which runs the nested-set patch and
`ensure_roles()`), then the three new focused test modules.
