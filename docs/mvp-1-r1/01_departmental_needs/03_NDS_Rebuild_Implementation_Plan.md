# Departmental Needs rebuild — implementation plan

**Authority:** `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1.1.md` (the single implementation authority; this plan sequences work against it and adds no new requirements).
**Companions:** `02_NDS_Rebuild_Gap_Analysis.md` (what is wrong today), `IMPLEMENTATION_TRACKER.md` (phase status, evidence, decision log).
**Status:** Phase 0 complete (gap analysis, this plan, tracker authored). Phases 1–10 not started.
**Author date:** 2026-08-29

## 1. Governing approach

Same workflow as CFG-CHG-002 (PE/FY), STR-CHG-001 v1.3 (Strategy), BUD-CHG-001 v1.2 (Budget) and STD-CHG-001 v1.3 (STD Configuration): research first, author plan + tracker, then execute phase by phase with the tracker's rows as the evidence ledger. No row is `Done` on inspection alone — each cites a command, test name, diff, or described screenshot.

NDS-CHG-001 v1.1's own posture governs disposition: **corrected in place, no alias, no redirect, no dual-read, no compatibility flag** (§1, §17). Where this plan says "delete," the deletion lands in the same phase as its replacement — never deferred as future cleanup. §17's prohibited-shortcuts list is a standing constraint on every phase, not a final check.

The transactional pattern in `services/lifecycle.py` (idempotency key → row lock → optimistic token → authorization → state guard → validation → mutate → audit event with before/after hashes → routed task dispatch) is the module's main existing asset. **Reuse the pattern; replace what it operates on.**

## 2. Decision register (resolve before or during the named phase)

| # | Decision | Recommendation | Phase | Why it needs recording |
|---|---|---|---|---|
| D1 | Owning app for Departmental Needs | **FIRM — decided by the Project Owner, 2026-08-29.** Departmental Needs and Procurement Planning remain **separate modules within `kentender_procurement`**. Planning consumes Accepted Needs **only** through the published handoff contract. Direct access to Departmental Needs DocTypes, tables or internal services is **prohibited** and **enforced by automated architecture tests** (Phase 9, NDS-910). **No additional Frappe app is introduced.** | 1 | Settled, not open. The boundary is executable rather than conventional: an architecture test fails the build if Planning imports a Needs DocType, queries a `tabDepartmental Need*` table, or calls a `departmental_needs.services.*` internal. |
| D2 | Permission engine | Native Frappe Role + DocType permission + User Permission, per §6 / NDS-AC-044 | 3 | **Diverges from CFG-CHG-002 and STR-CHG-001**, which both adopted `kentender_core.services.authorization_policy`. The spec is authority for this module; the platform-level split must stay visible rather than be silently resolved either way. |
| D3 | `DepartmentalNeedReviewTask` modelling | Typed projection over `kentender_core`'s `Workflow Task`, not a parallel task store | 1 | The core engine already supplies routing, decision tokens and atomic completion. §4.4's required fields (`task_type`, `decision_token`, scope) can be satisfied by the existing record plus a typed read contract. Revisit only if the projection cannot express `task_type` cleanly. |
| D4 | `DepartmentalNeedVersion` as standalone doctype vs. child table | Standalone doctype | 1 | Versions are referenced by review tasks, decisions, events and Planning lineage by their own ID (`need_version_id`) — a child table cannot carry stable cross-record identity. |
| D5 | Planning usage direction | Planning publishes `NeedPlanningUsageChanged.v1`; Needs stops reading `Plan Need Allocation` | 5 | §3 forbids querying a downstream table. Requires coordination with PLN-CHG-001 v1.1 — the one genuinely cross-module dependency in this rebuild. |
| D6 | Existing live Need records | Rebuild fixtures; no data migration | 1 | §1.1 prohibits legacy migration and compatibility; live rows in this module are seeded/test data, not production records. **Confirm against the target site before dropping anything.** |
| D7 | Frontend stack | Vue-in-Desk per `AGENTS.md` §6 and §16.1, replacing the jQuery page controllers | 7 | §16.1 explicitly names the `frappe.ui.make_app_page()` → bundle → `createApp().mount()` pattern proven by the Strategy pilot. |

## 3. Phase sequence

Each phase lists its exit condition. Detailed per-item rows live in `IMPLEMENTATION_TRACKER.md`.

### Phase 0 — Plan and tracker *(complete)*
Author `02_NDS_Rebuild_Gap_Analysis.md`, this plan, and the tracker. Reconcile the stale `design/uploads/` pre-approval draft.

### Phase 1 — Domain model
The spine everything else depends on.

- Create `Needs Intake Window` (`procuring_entity_id`, `financial_year_id`, `opens_at`, `closes_at`; unique per PE/FY; Scheduled/Open/Closed derived, never stored).
- Create `Departmental Need Version` (§4.3: `version_number`, `based_on_version_id`, `version_status` incl. `Superseded`, `title` 5–160, `description` 10–1,000, `expected_operational_result` 10–1,000, `indicative_quantity` > 0 ≤ 3dp, `unit_id` Link to governed catalogue, `required_by_date`, `content_hash`).
- Create `Need Withdrawal Request` (§4.6: 4-value status incl. `Awaiting planning clearance`, `planning_dependency_version`, reason 20–1,000; at most one open per Need).
- Slim `Departmental Need` to the §4.2 root: drop `title`, `business_justification`, `required_by_date`, `delivery_or_use_location`, `indicative_cost`, `currency`, `revision_no`, `submitted_by`, `pe_fy_context`; add `current_version_id`, `current_accepted_version_id`; rename `concurrency_token` → `record_version`; change `target_financial_year` from Data to a real Link.
- Delete `Departmental Need Item` and `Departmental Need Attachment` doctypes outright.
- Split `Departmental Need Review` into the §4.5 decision record; keep the idempotency ledger mechanism.
- Rename role `Departmental Need Requester` → `Departmental Author`.

**Exit:** schema matches §4 exactly; `bench migrate` clean on the target site; no prohibited field survives a static scan.

### Phase 2 — Services and lifecycle
- Rewrite `services/lifecycle.py` against §5.1/5.2/5.3 with the existing transactional pattern intact.
- Add the missing successor lifecycle: `create_accepted_need_successor`, `cancel_accepted_need_successor`; return-creates-copied-Draft (NDS-AC-011); successor acceptance supersedes atomically (NDS-AC-017); successor decline leaves the earlier accepted version current (NDS-AC-018).
- Complete the withdrawal lifecycle: `Approve` / `Evaluate` (→ `Awaiting planning clearance`) / re-evaluate / `Decline`, maker-checked (NDS-AC-019).
- Correct `_validate_submission()` bounds to §4.3 and delete validation for removed fields.
- Delete `services/attachments.py`.
- Rewrite `services/context.py` to read the real intake window with inclusive boundaries (NDS-AC-003).
- Reduce `services/usage.py` to `Not included` / `Fully included`.
- Extend `services/notifications.py` to cover withdrawal decisions.

**Exit:** every §8.2 command exists with its §9 error codes; §5 tables fully traversable in tests.

### Phase 3 — Permissions
- Replace this module's `authorization_policy` usage with native Frappe Role + DocType permission + User Permission (D2).
- Populate the `Departmental Need` permissions array; scope PE/FY/department through User Permission.
- Implement acting HoD as the same `Head of User Department` role plus a time-bound scoped User Permission; delete the `Departmental Review Delegate` role and the `Authorization Delegation` path in `notifications.py`.
- Remove `Budget Officer`, `Accounting Officer` and the Planner landing page from `setup/departmental_needs_page.py` (NDS-AC-023).
- Give the Procurement Planner intake-window maintenance and the read-only accepted-source deep link only (NDS-AC-043).
- Delete the support-lookup surface (`workspace.py::get_support_need`).

**Exit:** NDS-AC-022, 041–044 evidenced; no custom capability string remains in this module.

### Phase 4 — API and command surface
Rewrite `api.py` to the §8.1 read contracts and §8.2 commands, with the full §9 error contract as stable machine-readable codes. Mutating commands require idempotency key + expected token. No writable DocType endpoint bypasses a command (§16.1).

**Exit:** every §8.1/§8.2 contract whitelisted and reachable; every §9 code returnable.

### Phase 5 — Planning integration
- Emit `DepartmentalNeedAccepted.v2` with exactly the §7.1 field list, including `expected_operational_result` (NDS-AC-038, 024).
- Add `DepartmentalNeedSuperseded.v1` and `DepartmentalNeedWithdrawn.v1`; transactional-outbox delivery, idempotent and ordered per Need.
- Consume `NeedPlanningUsageChanged.v1` instead of querying `Plan Need Allocation` (D5).
- Verify Need ID remains the stable source-line identity through Planning (NDS-AC-039) and that Planning receives values read-only (NDS-AC-040).
- **Cross-app check:** grep the whole repo for real consumers of the old payload before changing it.

**Exit:** contract tests green on all three events; no Needs→Planning table query remains.

### Phase 6 — Seeds and fixtures
Rebuild `seeds/` to §14: prerequisites (§14.1), seven actors (§14.2), the four exact Needs with their exact descriptions and expected operational results (§14.3), and the independently selectable Planning-usage (§14.4), successor and withdrawal (§14.5) and KEBS first-slice (§14.6) profiles. Deterministic and idempotent (§14.7); no legacy Demand, partial allocation, reservation, Requisition or Tender.

**Exit:** seeds run twice with identical results; NDS-AC-032, 045 evidenced.

### Phase 7 — Frontend
Rebuild all eight §10 screens as Vue-in-Desk (D7), porting the `.dc.html` artboards class-for-class rather than rebuilding layout from prose.

- NDS-UI-01 workspace (DES-01) with all five states (DES-14a–e), one table, minimal filters, no summary cards.
- NDS-UI-02 department review with both tabs (DES-02, 02b).
- NDS-UI-03 editor (DES-03, 04, 08) — six fields only, expected-result help text, no items/attachments/cost/location.
- NDS-UI-04 detail (DES-05 Submitted, DES-07 Accepted) with Create update / Request withdrawal / View Plan Item.
- NDS-UI-05 review task (DES-06, 09) with dialogs DES-13a/13b.
- NDS-UI-06 accepted source detail.
- NDS-UI-07 withdrawal review (DES-12a blocked, 12b cleared) + request dialog DES-11.
- NDS-UI-08 intake window (DES-10).

Register only §10's canonical routes; no redirect or alias (NDS-AC-030). Add stable accessible test selectors, not CSS-class selectors (§16.1). Route changes unmount Vue and cancel stale requests; use an active-flag guard, not `frappe.router.off()`.

**Exit:** all eight routes render live data; production-mode asset build clean.

### Phase 8 — Shell and registry wiring
Register routes in `kt_cl_surface_registry.js`; module menu with only the three §10 entries and their role visibility; module placed after Budget & Funding and before Procurement Planning; `hooks.py` updated; old page records and JS/CSS deleted. Watch the known workspace-sidebar reverse-sync hazard — a dangling Workspace/Page link fails the whole-site migrate.

**Exit:** clean `bench migrate`; menu visibility correct per role.

### Phase 9 — Tests
- Rewrite the Python suite against the corrected model; delete `test_departmental_needs_attachments.py` and the delegate-review case.
- Cover §15.1's six layers: domain unit, permission unit, command integration, contract integration, UI component, browser smoke.
- Playwright specs for all eight screens.
- Static-scan test proving every prohibited field, object, role and legacy route is absent (§16.3) — extends the existing `test_departmental_needs_completeness_gaps.py` boundary-test pattern.
- Visual regression references at 1440 × 1024 for every artboard, modal and workspace state.

**Exit:** clean module suite; clean accepted-source and Planning contract tests.

### Phase 10 — Verification and release evidence
Full NDS-AC-001–045 mapping with per-criterion evidence; §19 E2E-REQ-001 conformance check against all eight non-drift controls; live browser walkthrough of the golden path and edge cases, verifying first paint **and** at least one interactive re-render; zero page console errors and zero failed own requests; schema scan per §16.3. Tracker rows move to `Done` only with real observed evidence.

## 4. Files in scope

**Rebuild:** `departmental_needs/doctype/departmental_need/`, `services/{lifecycle,permissions,context,usage,workspace,notifications,constants,errors}.py`, `api.py`, `seeds/kentender_mvp_r1.py`, `setup/departmental_needs_doctypes.py`, `setup/departmental_needs_page.py`, `tests/`.

**Create:** `doctype/needs_intake_window/`, `doctype/departmental_need_version/`, `doctype/need_withdrawal_request/`, the Vue bundle and components for eight screens, Playwright specs for the four missing screens.

**Delete:** `doctype/departmental_need_item/`, `doctype/departmental_need_attachment/`, `services/attachments.py`, `tests/test_departmental_needs_attachments.py`, `public/js/departmental_needs_*.js`, `public/css/departmental_needs*.css`, the five legacy `page/*` records.

**Touch:** `kentender_procurement/hooks.py`, `kentender_core/public/js/kt_cl_surface_registry.js`, `procurement_planning/services/need_allocations.py` (usage-projection direction), `docs/mvp-1-r1/01_departmental_needs/design/uploads/` (stale draft).

## 5. Verification commands

```bash
# focused Python test (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.departmental_needs.tests.<module>

# focused Playwright
npx playwright test tests/ui/smoke/departmental_needs/<spec>.spec.ts -g "<test name>"

# assets (from apps/kentender_v1) — never plain `bench build`
./scripts/bench-with-node.sh build --app kentender_procurement

# bench lifecycle
make validate-links && make migrate SITE=kentender.midas.com && make clear SITE=kentender.midas.com
make seed-kentender-mvp-v1 SITE=kentender.midas.com
make seed-kentender-mvp-v1-validate SITE=kentender.midas.com
```

Per §16.2 and `CLAUDE.md`: red/green on the focused node first, then the affected group, then the module suite once. Do not rerun the repository suite after each small fix. After CSS/JS changes, clear the site cache and hard-refresh Desk before diagnosing a code defect.
