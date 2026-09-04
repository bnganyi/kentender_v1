# PLN-CHG-001 v1.2 — Procurement Planning Rebuild Implementation Plan

| Control | Value |
|---|---|
| Authority | `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1.2.md` (approved 30 August 2026; supersedes v1.1 in full) |
| Companions | `02_PLN_Rebuild_Gap_Analysis.md` (current-state facts), `IMPLEMENTATION_TRACKER.md` (progress and evidence) |
| End-to-end frame | `docs/mvp-1-r1/00_common/KenTender_E2E-REQ-001_…_v0.2.md` §17 delivery order, step 2 |
| Prepared | 30 August 2026 |
| Status | Awaiting Project Owner review before Phase 0 begins |

## 1. Governing approach

**Rebuild in place; no compatibility layer.** The §1.1 register removes concepts wholesale and the existing module implements a superseded product (Demand-sourced consolidation, Stitch UI, capability-store permissions) — see the gap analysis. Removed concepts are deleted, not renamed or flagged off. Proven transactional mechanics are deliberately retained as *patterns* (idempotency keys, expected record versions, immutable decision records, `fixture_namespace` isolation, seed orchestration wiring), even where their carrying code is replaced.

**Phase ordering is the point of this plan.** The last three module rebuilds (Strategy, NDS, Budget) each lost their largest block of time to verification-last ordering: NDS closed 242 green Python tests while four §8 endpoints returned 500 over HTTP, two decision screens were unreachable, and the Planner could not open the module at all — every one found only when a browser finally opened in Phase 9/10, and ~10 further fix commits landed within 36 hours of "close". This plan therefore keeps only the domain model and lifecycle core horizontal, then goes **vertical: one journey at a time, API → screen → real browser, with the slice's gate closing only on browser evidence.** Legacy demolition for a surface lands in the same slice that replaces it ("delete later" is not a row state).

Non-negotiables inherited from AGENTS.md and the module retrospectives, restated as tracker rules:

1. Every mutating endpoint gets a **request-shaped test through `frappe.handler`** (the NDS-914 `**kwargs`/`form_dict` class is invisible to direct-service tests), plus the `**kwargs` AST guard.
2. Every slice's browser evidence includes **per-role logins** for each §6 actor the slice serves, one **out-of-scope actor**, and **absence assertions** on refusal paths (nothing extra rendered — e.g. no duplicate native Message modal).
3. The **read/offer layer is asserted against the command layer**: for every open task type the slice creates, a queue/workspace row must offer it (the NDS-911 class), and nothing is offered the command layer would refuse (the NDS-807 class).
4. Playwright spec files each own their **own fixture Procuring Entity** (references are generated per PE/FY, so namespace isolation alone is insufficient), and fixture instants are **pinned, never `now`-relative**.
5. Static/architecture guards are proven **by planting a violation** before their row is Done.
6. Vue-in-Desk bundle checklist on every new bundle: `app.config.globalProperties.__`/`.frappe` before mount; CSS via `app_include_css` (never a bundle-side CSS import); every ref/computed a `railTrail` reads declared before `usePageRail(...)`; `touch hooks.py` after asset edits before re-testing; no `*/` sequence inside CSS comments; artboards ported **class-for-class from the `.dc.html` file**, never from the prose spec.
7. TDD ladder per §16.2: focused test → smallest change → focused rerun → module slice → module regression at checkpoints → full suite once before handoff. No full-suite runs as a diagnostic step.

## 2. Decision register

| ID | Decision | Why |
|---|---|---|
| D1 | Rebuild in place per the §1.1 register; retain proven transactional mechanics as patterns; no Demand migration, alias, dual-read or compatibility shim. | The register removes concepts; patching toward fewer concepts means holding two models at once. Rebuild cost is dominated by demolition/re-verification, which an existing live module cannot skip anyway. |
| D2 | §10 route slugs are owned by Desk Pages. DocType names are chosen so their scrubbed slugs never equal a §10 route slug. Exact names fixed in Phase 1 with a scrub-check row. | A Page route always loses to a same-named readable DocType's list view; DocType `Procurement Plan Item` already scrubs to the §10 route `procurement-plan-item`. NDS precedent: doctype `Departmental Need`, page `departmental-needs`. |
| D3 | Phase 0 empirically verifies Page-vs-Workspace precedence for `/app/procurement-planning` (a Workspace fixture of that name exists) and the fixture is retired or renamed accordingly, minding the workspace_sidebar reverse-sync (a dangling Workspace/Page link fails whole-site migrate). | The route is the §10 workspace URL; the existing Workspace is empty and carries stale roles. |
| D4 | Native Frappe Role / Workflow permission / User Permission only. Task records are **module-local doctypes** (§4.6, §4.11, §4.12), not core `Workflow Task`. | v1.2 §6 prohibits a second permission store. Core's task engine calls `require_capability()` internally (NDS D3 finding) and would rebind Planning to the prohibited capability store. Resolves the AUTH-ADR-001 `plan.*` dual-path BLOCKED finding by removing the capability path. |
| D5 | Planning consumes Departmental Needs only through published events and read contracts (`DepartmentalNeedAccepted.v2` outbox + `get_current_accepted_need`), enforced by an AST architecture test in both directions (NDS D1 precedent). Planning adds the outbox-drain consumer for Superseded/Withdrawn. | Owner-published contracts are the repo's cross-app rule; the AST test is the enforcement that held for NDS. |
| D6 | Cross-app Strategy/Budget calls go through the siblings' published API modules, wrapped in Planning-side adapter services named after the §8 spec verbs. The adapters record the name deltas: `list_strategy_objectives` (+`resolve_strategy_context`, `create_strategy_snapshot`), `list_eligible_budget_lines`, `check_funding`→token→`reserve_funding` (300 s TTL), `release_reservation` (off the legacy `dia_budget_control` adapter), `revalidate_reservations`. | The spec names are contract intents, not existing symbols; the adapters keep the spec vocabulary inside Planning while honouring the real published surface, and close the current direct-table reads of Budget Lines. |
| D7 | Industry design system only. One page-shell pattern copied from `departmental_needs_page.js` / `budget_funding_page.js`: `enterNative({sidebarWorkspaceKey})` sidebar-only, clear `#kt-cl-chrome-host`, hide `.navbar`/`.page-head`, shared `kt_industry_page_rail.bundle.js`, **no `kt_cl_surface_registry.js` entries**. Work queues are never sidebar entries — My Work provider + notification deep links. | Stitch/Civic Ledger are legacy debt; the surface-registry rule and the My Work rule are both Project-Owner-settled (NDS FU-14). |
| D8 | Playwright fixture endpoints live in seed/fixture modules invoked via `bench execute`, never in `api.py`. | The old module's `api.py` is ~60% fixture endpoints; production surface and test scaffolding must not share a file. |
| D9 | **(User decision, 30 Aug 2026)** §15.1(5) is satisfied literally: a Vue SFC vitest project (`@vitejs/plugin-vue` + jsdom) is added for Planning components — the repo's first. It lands in Slice A with the first component; every later slice ships component tests (exact fields, absent fields, task detail, errors, dialog copy, action visibility) alongside, not instead of, browser evidence. | Spec letter; the toolchain gap was a repo omission, not a decision. |

## 3. Phase sequence and exit conditions

Gates PLN-G00–PLN-G12 in the tracker mirror these phases 1:1. A slice phase (3–10) exits only when: its focused + request-shaped tests are green; its component tests are green; its Playwright spec passes on its own fixture PE; a real browser click-through (first paint **and** one interactive re-render, per-role) is recorded as evidence; and the legacy surface it replaces is deleted.

| Phase | Name | Scope summary | Exit condition (beyond the standing slice rules) |
|---|---|---|---|
| 0 | Baseline & demolition survey | Exact non-passing test baseline (per-file pass/fail/error, incl. the two known broken imports); keep/correct/delete catalogue over all ~142 files; repo-wide grep for external callers of planning services/API; slug-ownership audit (D2/D3); duplicate `_ds` bundle resolution; confirm every gap-analysis **[confirm in Phase 0]** row. | Baseline recorded verbatim in tracker; catalogue and audits recorded; no code changed. |
| 1 | Domain model (horizontal) | All §4 doctypes under D2 naming; DB uniqueness for invariants 2, 17, 24; drop-old-doctypes patch (clean domain — no data migration); removed-concept absence guard; thin controllers. | `bench migrate` clean on the dev site; schema tests green; absence guard proven by planted violation. |
| 2 | Lifecycle + permissions core (horizontal) | §5 command services on the §8 envelope (idempotency key + expected record version, rechecked in-transaction); §6 native roles + single scope predicate; §6.1 maker-checker matrix; §9 error contract; working-context integration; Needs outbox drain + projections; Strategy/Budget adapters (D6); request-shaped test harness + `**kwargs` guard. | Domain/permission/contract tests green at the service and handler layers; no UI yet. |
| 3 | Slice A — Workspace & context | PLN-UI-01; PLN-DES-01 + DES-16 states; `ResolvePlanningContexts` / `GetPlanningWorkspace`; My Work provider (retire core `_PRESENTATION` plan.* rows); nav revival (single entry); SFC vitest toolchain (D9). | Browser: each §6 role sees exactly its work; no-context user gets the DES-16 state; zero console errors. |
| 4 | Slice B — DPP authoring | PLN-UI-02..05; DES-02..05; `OpenDepartmentalPlan`, `SaveNeedFunding`, `SaveDirectRequirement`, `RemoveDirectRequirement`, `SubmitDepartmentalPlan`; window gating; certification; withdrawal/reopen; returned-correction display. | Browser: Author + HoD + acting-HoD journeys; submit blocked/unblocked states observed live. |
| 5 | Slice C — DPP validation → auto Annual Plan | PLN-UI-06; DES-06 + return dialog; `ReturnDepartmentalPlan`, `AcceptDepartmentalPlan`; classification; automatic Draft-plan creation with the invariant-24 uniqueness race; pending-addition holding. | Browser: Planner accepts and the workspace shows the unallocated source; concurrency test proves one winner. |
| 6 | Slice D — Workbench, formation, Plan Item | PLN-UI-07..09; DES-07/08/09/09A; `FormPlanItems`, `SavePlanItem`, `DissolvePlanItem`; Strategy selector on live contracts; compatibility + schedule validation; source-correction-required marking. | Browser: single + combined formation, dissolve returning sources, schedule errors bound to exact controls. |
| 7 | Slice E — Finance | PLN-UI-10; DES-10 + shortfall state; `RequestFinanceConfirmation`, `ConfirmFunding`, `ReturnFromFinance`; check→token→reserve inside the 300 s TTL; §4.11 stale rules; release/revalidate migration off `dia_budget_control`; dissolve-with-reservations atomicity. | Browser: Budget Officer confirm and shortfall paths; release-failure rollback proven by test. |
| 8 | Slice F — Governance | PLN-UI-11/12; DES-11/12/15; `SubmitConsolidatedPlan`, `AdoptAndSubmitPlan`, `ApproveAnnualPlan`, `ReturnPlanVersion`, `SubmitCorrectedPlan`; correction chain restarting at AO; selective Finance repeat; Board resolution reference; maker-checker across the chain. | Browser: AO and statutory logins each see the complete immutable Plan before controls; returns produce correction Drafts. |
| 9 | Slice G — Publication, Active, successor | PLN-UI-13/14; DES-13/14; `PublishAnnualPlan` (adapter, activation on acknowledgement only, idempotent retry); `BeginPlanUpdate`, `RemovePlanItemInSuccessor`, `CancelPlanUpdate`; successor reservation release after downstream checks; `NeedPlanningUsageChanged.v1` publisher. | Browser: Active plan renders the §14 evidence card; failed-publication retry path observed; System-Manager-only retry control. |
| 10 | Slice H — Requisition eligibility | §7.4 `GetRequisitionEligiblePlanItem.v2` projection + drawdown-reference consumption (atomic balance math), API-only. | Contract tests cover eligible, blocked and remaining-balance cases; no UI. |
| 11 | Seeds (§14) | Integrated baseline (§14.4–14.6) + isolated profiles (direct §14.7, combined §14.8, KEBS ×2 §14.9, return/shortfall/stale/successor/publication-failure) driven through real commands with frozen clocks and named actors; orchestrator/validate/purge wiring; **a browser pass logged in as the §14 personas** (the Playwright-fixture world and the seed world are parallel — bugs living only in the seed world are otherwise invisible). | `make seed-kentender-mvp-v1` + validate green twice (idempotent); persona browser pass recorded. |
| 12 | Release verification | §15.1(6) integrated journeys; one full module regression (server + vitest + Playwright); cross-module contract checkpoint (Needs/Strategy/Budget suites); asset build via `./scripts/bench-with-node.sh build --app kentender_procurement` with bundle-hash confirmation; §16.3 evidence pack (16 artboard screenshots at 1440×1024, zero console errors / failed requests); final demolition sweep (registry, Makefile gates, workspace fixtures, removed-field audit); AC map + §19 conformance completed; `FOLLOW_UPS.md` authored. | Every §16.3 item evidenced; tracker Status paragraph states exactly what was and was not run. |

Dependency note: reservations first exist in Phase 7, so dissolve-releases (PLN-AC-048) and Finance-stale behaviours are finished there even though dissolution itself lands in Phase 6. Publication (Phase 9) needs nothing from Phase 10; Phases 9 and 10 may swap if Requisitions work (REQ-CHG-001) becomes urgent.

## 4. Files in scope (representative, not exhaustive)

- **Module root:** `kentender_procurement/kentender_procurement/procurement_planning/` — `doctype/` rebuilt per §4; `services/` rebuilt per §5/§7/§8 (porting envelope patterns from the NDS `lifecycle.py` family); `api.py` rebuilt lean (fixtures out, D8); `seeds/` rewritten to §14; `tests/` largely rewritten; `page/` replaced by the D2-named Desk pages.
- **UI:** new `public/js/procurement_planning/` Vue tree + `*.bundle.js` + `*_page.js` controllers on the D7 shell; new `public/css/procurement_planning_industry.css` via `app_include_css`; delete `planning_live_bind.js`, all `planning_*_bind.js`/`planning_ui_fixtures/`, `planning_workspace.css`, `planning_workspace_redirect.js`.
- **Cross-app touch points:** `kentender_core/.../services/my_work.py` (`_PRESENTATION` plan.* rows out), `kentender_core/.../public/js/kt_cl_surface_registry.js` (7 stale entries out), `kentender_core/.../seeds/kentender_mvp_v1/{planning,clear,validate}.py`, `kentender_procurement/hooks.py` (page_js, css/js includes, `kt_my_work_providers`, fixtures), `workspace_sidebar/*.json`, `setup/sidebar_availability.py`, `patches.txt` (+ new `pln_chg_001_v12_*` patches), root `Makefile` planning gates, root `vitest.config.ts` (+ SFC plugin), `tests/ui/smoke/planning/` (replaced per slice), `.env.ui` actor entries as needed.
- **Contracts consumed (read-only for this rebuild):** `departmental_needs/services/{events,workspace,usage}.py`; `kentender_strategy/api/strategy_consumer_api.py`; `kentender_budget/api/budget_api.py`.

## 5. Verification commands

```bash
# Focused / module Python (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_planning.tests.<module>

# Component tests (repo root)
npx vitest run --project procurement-planning

# Per-slice browser spec
npx playwright test tests/ui/smoke/planning/<spec>.spec.ts

# Seeds
make seed-kentender-mvp-v1 SITE=kentender.midas.com
make seed-kentender-mvp-v1-validate SITE=kentender.midas.com

# Assets (never plain bench build)
cd /home/midasuser/frappe-bench && ./scripts/bench-with-node.sh build --app kentender_procurement
```

Make gates for Planning are re-pointed slice-by-slice as their specs are replaced; the Phase 12 sweep confirms no gate references a deleted file.

## 6. Non-goals

Everything in §2.1, and specifically: no Requisition, Tender, template or STD work (E2E-REQ-001 steps 3–4); no Needs-side changes (its events already match §7.1); no Budget/Strategy service changes beyond consuming what is published (any gap found there becomes a follow-up to the owning module, not an in-place edit); no generic composer or configuration engine (E2E-REQ-001 §18); no production publication destination — the sandbox destination only.

## 7. Risks

| Risk | Mitigation |
|---|---|
| Slug/Workspace precedence surprises break routes late | Settled empirically in Phase 0 (D2/D3) before any doctype is named. |
| The UI phase is historically the highest-defect phase | It is not one phase here: each slice's screen is browser-verified before the next slice opens; artboards are ported literally. |
| Budget check-token TTL (300 s) vs a slow Finance confirmation UX | Confirm command re-runs `check_funding` server-side when the token is expired rather than failing the user. Designed in Slice E. |
| Publication adapter has no precedent in the repo | Isolated behind `PublishAnnualPlan`; sandbox destination; failure/indeterminate paths are first-class §4.13 states with tests. |
| Cross-app demolition breaking migrate (workspace_sidebar reverse-sync) | Workspace/fixture edits land with a migrate run in the same phase; FU-01-style fresh-install patch risk checked for every patch touching deleted modules. |
| Seed world vs Playwright world divergence | Phase 11's persona browser pass is a gate condition, not an optional extra. |
