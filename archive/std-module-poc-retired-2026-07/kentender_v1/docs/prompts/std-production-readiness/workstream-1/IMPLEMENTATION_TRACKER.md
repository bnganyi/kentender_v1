# STD Template Governance and Lifecycle — implementation tracker

**Purpose:** Single place to record status, evidence (`bench run-tests`, `bench migrate`, Playwright), acceptance criteria, blockers, and pointers to [`ISSUES_LOG.md`](ISSUES_LOG.md) for **STD Template Governance and Lifecycle** (STD production readiness **Workstream 1**).

**Programme rollup:** [`../IMPLEMENTATION_TRACKER.md`](../IMPLEMENTATION_TRACKER.md)

**Issues log (canonical):** [`ISSUES_LOG.md`](ISSUES_LOG.md) — prefix **`STD-GOV-*`**. Cross-post to planning→tender handoff only when shared with **`STD-INT-*`**.

---

## Workstream docs (source of truth)

| # | Document |
|---|----------|
| 1 | [`1. std_template_governance_lifecycle_scope_document.md`](1.%20std_template_governance_lifecycle_scope_document.md) |
| 2 | [`2. std_template_governance_lifecycle_state_transition_model.md`](2.%20std_template_governance_lifecycle_state_transition_model.md) |
| 3 | [`3. std_template_governance_lifecycle_role_permission_matrix.md`](3.%20std_template_governance_lifecycle_role_permission_matrix.md) |
| 4 | [`4. std_template_governance_lifecycle_domain_model_data_dictionary.md`](4.%20std_template_governance_lifecycle_domain_model_data_dictionary.md) |
| 5 | [`5. std_template_governance_lifecycle_admin_ux_specification.md`](5.%20std_template_governance_lifecycle_admin_ux_specification.md) |
| 6 | [`6. std_template_governance_lifecycle_audit_event_catalogue_snapshot_rules.md`](6.%20std_template_governance_lifecycle_audit_event_catalogue_snapshot_rules.md) |
| 7 | [`7. std_template_governance_lifecycle_complete_cursor_implementation_pack.md`](7.%20std_template_governance_lifecycle_complete_cursor_implementation_pack.md) |
| 8 | [`8. std_template_governance_lifecycle_smoke_test_specification.md`](8.%20std_template_governance_lifecycle_smoke_test_specification.md) |

**Upstream POC context (not duplicated here):** [`../../std poc/IMPLEMENTATION_TRACKER.md`](../../std%20poc/IMPLEMENTATION_TRACKER.md) · [`../../std poc/admin console/IMPLEMENTATION_TRACKER.md`](../../std%20poc/admin%20console/IMPLEMENTATION_TRACKER.md)

---

## Rules of engagement

1. **Spec and pack are law** — Docs 1–6 define governance; **doc 7** locks DocTypes, fields, roles, method names, event codes, and **STD-GOV-001 … STD-GOV-014** sequence. Doc **8** is the minimum acceptance smoke gate. Do not mark **Done** without evidence for the mapped acceptance criteria (or a logged **deviation** in [`ISSUES_LOG.md`](ISSUES_LOG.md)).
2. **Non-negotiable boundaries (doc 7 §3, doc 1 §9)** — No bidder portal, submission/opening/evaluation/award, publication, addenda, free editing of active package payload, or scope listed as out-of-scope in doc 1.
3. **TDD; Playwright for Desk** — Workspace [`.cursor/rules/kentender-tdd-playwright-quality-gate.mdc`](../../../../../../.cursor/rules/kentender-tdd-playwright-quality-gate.mdc); Desk patterns [`.cursor/rules/frappe-desk-playwright-patterns.mdc`](../../../../../../.cursor/rules/frappe-desk-playwright-patterns.mdc). **Done** on admin UI (STD-GOV-011) requires passing Playwright or a logged environment blocker.
4. **Bench / Node** — Use [`./scripts/bench-with-node.sh`](../../../../../../scripts/bench-with-node.sh) from bench root for any `bench build` touching `public/js` / `public/css` per [`.cursor/rules/frappe-bench-node.mdc`](../../../../../../.cursor/rules/frappe-bench-node.mdc).
5. **Regression** — After touching `STD Template`, loader, or engine, run targeted `kentender_procurement` tests: at minimum `test_std_works_poc_step9_doctypes`, `test_std_works_poc_step10_loader`, `test_std_works_poc_step11_engine` (and any new `test_std_template_governance*` modules) unless a deviation is recorded.

**Status values:** `Not started` | `In progress` | `Partial` | `Blocked` | `Done`

---

## Workstream health

| Field | Value |
|-------|--------|
| Primary template code | `KE-PPRA-WORKS-BLDG-2022-04-POC` |
| Governed DocType (v1 path) | `STD Template` extended; child tables per doc 7 §§8–10 |
| Target code locations (adapt if repo differs) | Doc 7 §5 — e.g. `tender_management/services/std_template_governance*.py`, `doctype/std_template/*` |
| Last tracker update | 2026-05-07 — §E workspace narrative extended (admin-revamp §A A3–A7: validation/bundle, Advanced Technical View, STD Instances read-only usage, Desk-first vs SPA, ROLE_STD_ADMIN Frappe role mapping); [`test_std_governance_workspace_nav.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_governance_workspace_nav.py) + [`std-governance-workspace-nav.spec.ts`](../../../../tests/ui/smoke/procurement/std-governance-workspace-nav.spec.ts). 2026-05-03 — doc 8 §C; **STD-GOV-103** / **STD-GOV-104**. |

---

## A. Design artefacts — acceptance / sign-off

Record product/architecture sign-off on written specs before or while implementation proceeds.

| ID | Artefact | Document | Sign-off status | Evidence | Notes |
|----|----------|----------|-----------------|----------|-------|
| A1 | Scope | Doc 1 | Not started | | Doc 1 §§7–8 in-scope capabilities; §9 out-of-scope; §13 governance decisions |
| A2 | State transition model | Doc 2 | Not started | | States, guards, immutability, audit per transition |
| A3 | Role and permission matrix | Doc 3 | Not started | | SoD, System Manager override, server enforcement |
| A4 | Domain model and data dictionary | Doc 4 | Not started | | Option A extend `STD Template`; child objects; field intent |
| A5 | Admin UX specification | Doc 5 | Not started | | Journeys, catalogue, panels, permission-aware actions |
| A6 | Audit catalogue and snapshot rules | Doc 6 | Not started | | Event codes, payloads, snapshot/hash rules |
| A7 | Cursor implementation pack (executable plan) | Doc 7 | Not started | | Tickets STD-GOV-001–014; §25 STD-GOV-IMPL-AC-001–017; §26 exit |

---

## B. Implementation tickets (doc 7 §23)

Execute **in order** unless a row’s Notes allow parallel prep (e.g. fixtures while services are in flight—still avoid skipping guards).

| Ticket | Title (summary) | Status | Evidence | Notes |
|--------|-----------------|--------|----------|-------|
| STD-GOV-001 | Add roles (doc 7 §6) | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_std_template_governance_roles` (3/3 OK, 2026-05-03) · [`std_template_governance_roles.py`](../../../../kentender_procurement/kentender_procurement/tender_management/seeds/std_template_governance_roles.py) · [`hooks.py`](../../../../kentender_procurement/kentender_procurement/hooks.py) (`after_migrate`) · [`test_std_template_governance_roles.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_roles.py) | Idempotent `Role` inserts only; no DocPerms (doc 7 §23). `QA / Test User` excluded per pack. |
| STD-GOV-002 | Extend `STD Template` fields (doc 7 §7) | Done | `bench --site kentender.midas.com migrate` · `bench … run-tests …test_std_template_governance_doctype_gov002` (4/4) · `…test_std_works_poc_step9_doctypes` (9/9) · `…test_std_works_poc_step10_loader` (16/16) · `…test_std_works_poc_step11_engine` (26/26) · [`std_template.json`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template/std_template.json) · [`std_gov_002_backfill_std_template_governance_fields.py`](../../../../kentender_procurement/kentender_procurement/patches/std_gov_002_backfill_std_template_governance_fields.py) · [`std_gov_002b_backfill_template_version.py`](../../../../kentender_procurement/kentender_procurement/patches/std_gov_002b_backfill_template_version.py) · [`std_template_loader.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_loader.py) · [`std_template.py`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template/std_template.py) · [`test_std_template_governance_doctype_gov002.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_doctype_gov002.py) | Deviations: [`ISSUES_LOG.md`](ISSUES_LOG.md) **STD-GOV-102**. No `package_payload_json` / `package_manifest_json`; `template_family` Select + manifest long-code → `Works`. |
| STD-GOV-003 | Child DocTypes + child table fields (doc 7 §§8–10) | Done | `bench … migrate` · `bench … test_std_template_governance_doctype_gov002` (4/4) · `…test_std_template_governance_doctype_gov003` (5/5) · `…test_std_works_poc_step9_doctypes` (9/9) · `…test_std_works_poc_step10_loader` (16/16) · [`std_template_lifecycle_event`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template_lifecycle_event/) · [`std_template_validation_finding`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template_validation_finding/) · [`std_template_usage`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template_usage/) · [`std_template.json`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template/std_template.json) (`lifecycle_events`, `validation_findings`, `template_usage`) · [`test_std_template_governance_doctype_gov003.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_doctype_gov003.py) | Doc 7 §§8–10 fieldnames; `STD Template` section **Governance — History (child tables)**. |
| STD-GOV-004 | Constants and hash helpers (doc 7 §§11–12 constants) | Done | `bench … run-tests …test_std_template_governance_hash_gov004` (9/9, 2026-05-03) · [`std_template_governance.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance.py) · [`test_std_template_governance_hash_gov004.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_hash_gov004.py) | `canonicalize_std_package_payload` / `compute_std_package_hash` (V1 JSON + SHA-256). Loader file-hash unchanged (Step 10). |
| STD-GOV-005 | Audit / lifecycle event service (doc 7 §13.5, §12 codes) | Done | `bench … run-tests …test_std_template_governance_events_gov005` (8/8, 2026-05-03) · [`std_template_governance_events.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_events.py) · [`test_std_template_governance_events_gov005.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_events_gov005.py) | `write_std_template_lifecycle_event` (append-only, actor/roles/at, `package_hash`, sorted `payload_json`, `doc.save()`). `get_std_template_audit_timeline` deferred (doc 7 §13.5; use GOV-009/013 if needed). |
| STD-GOV-006 | Validation service (doc 7 §13.2, §15) | Done | `bench … run-tests …test_std_template_governance_validation_gov006` (8/8, 2026-05-03) · `…test_std_template_governance_events_gov005` (8/8 regression) · [`std_template_governance_validation.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_validation.py) · [`std_template_governance_events.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_events.py) (`save` kw-only) · [`test_std_template_governance_validation_gov006.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_validation_gov006.py) | `validate_std_template_package_payload`, `run_std_template_validation`, `clear_std_template_validation_findings`, `write_std_template_validation_findings`; wraps ``run_package_validation``. |
| STD-GOV-007 | Lifecycle transitions (doc 7 §13.3, §14) | Done | `bench … run-tests …test_std_template_governance_lifecycle_gov007` (13/13, 2026-05-04) incl. `test_std_gov_007_supersede_with_usage_serializes_impact_payload` · [`std_template_governance_lifecycle.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_lifecycle.py) · [`test_std_template_governance_lifecycle_gov007.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_lifecycle_gov007.py) | §13.3 methods; doc 3 role matrix + site `Administrator` bypass where noted; SoD + `EVT_OVERRIDE_USED`; activation hash alignment; supersede/retire call ``get_std_template_usage_impact`` (GOV-008); JSON-safe `usage_impact` in supersede/retire event payloads. |
| STD-GOV-008 | Eligibility, usage, impact, mapping (doc 7 §13.4, §16) | Done | `bench … run-tests …test_std_template_governance_usage_gov008` (11/11, 2026-05-03) · `…test_std_template_governance_lifecycle_gov007` (13/13 regression) · [`std_template_governance_usage.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_usage.py) · [`std_template_governance_lifecycle.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_lifecycle.py) (`get_std_template_usage_impact`) · [`test_std_template_governance_usage_gov008.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_usage_gov008.py) | `check_std_template_tender_creation_eligibility`, `record_std_template_usage`, `get_std_template_usage_impact`, `resolve_active_std_template_for_context`; context flag ``emit_usage_blocked_event``; full planning→tender mapping deferred per **`STD-INT-*`**. |
| STD-GOV-009 | Governance snapshot service (doc 7 §13.5 snapshot, §18) | Done | `bench … run-tests …test_std_template_governance_snapshot_gov009` (4/4, 2026-05-03) · [`std_template_governance_snapshot.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_snapshot.py) · [`test_std_template_governance_snapshot_gov009.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_snapshot_gov009.py) | `generate_std_template_governance_snapshot`; `latest_governance_snapshot_*`; SHA-256 of canonical JSON; `EVT_SNAPSHOT_GENERATED`; roles: Administrator / System Manager / STD Template Administrator / STD Template Auditor. |
| STD-GOV-010 | `STD Template` controller guards (doc 7 §19) | Done | `bench … run-tests …test_std_template_governance_controller_gov010` (7/7, 2026-05-03) · regressions: `…test_std_template_governance_events_gov005` (8/8), `…test_std_template_governance_validation_gov006` (8/8), `…test_std_template_governance_lifecycle_gov007` (13/13), `…test_std_works_poc_step10_loader` (16/16) · [`std_template.py`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template/std_template.py) · [`std_template_governance.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance.py) (`PROTECTED_PACKAGE_FIELD_NAMES`, `HISTORICAL_LIFECYCLE_STATUSES`) · [`std_template_loader.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_loader.py) (`skip_std_template_guards`) | Package-field mutation guards; usage/delete rules; derived flags; `allowed_for_tender_creation` clamp unless Active; loader bypass flag; `ignore_permissions` delete cleanup. |
| STD-GOV-011 | Admin UI buttons and dialogs (doc 7 §20) | Done | `bench … run-tests …test_std_template_governance_desk_api_gov011` (4/4, 2026-05-03) · `npx playwright test tests/ui/smoke/procurement/std-template-governance-desk-gov011.spec.ts` (1/1) · `./scripts/bench-with-node.sh build --app kentender_procurement` · [`std_template.js`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template/std_template.js) · [`std_template.py`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/doctype/std_template/std_template.py) (whitelisted governance + `replace_std_template_package`) · [`std_template_governance_validation.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/std_template_governance_validation.py) (STD Template Administrator may run validation) · [`test_std_template_governance_desk_api_gov011.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_desk_api_gov011.py) · Playwright: [`std-template-governance-desk-gov011.spec.ts`](../../../../tests/ui/smoke/procurement/std-template-governance-desk-gov011.spec.ts) | **STD Governance** custom group: replace, governance validation, submit/return/reject/approve, activate/suspend/reinstate/supersede/retire/archive, snapshot, summary/usage/timeline; client visibility mirrors doc 3 matrix; server still authoritative. |
| STD-GOV-012 | Seed/migrate WORKS POC template governance (doc 7 §21) | Done | `bench … run-tests …test_std_template_governance_seed_gov012` (6/6, 2026-05-03) · [`std_template_governance_seed.py`](../../../../kentender_procurement/kentender_procurement/tender_management/seeds/std_template_governance_seed.py) · [`hooks.py`](../../../../kentender_procurement/kentender_procurement/hooks.py) (`after_migrate` after roles) · [`test_std_template_governance_seed_gov012.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_seed_gov012.py) | `seed_std_template_governance_for_existing_works_poc()` idempotent; **approved** (default migrate) vs **active** (`developer_mode` or `force_mode`); approved→active upgrade; `after_migrate` errors logged only. |
| STD-GOV-013 | Tests (doc 7 §22) | Done | `bench … run-tests` §22 modules (27/27, 2026-05-04): `test_std_template_governance` (12) · `test_std_template_governance_permissions` (7) · `test_std_template_governance_audit` (8) — run **sequentially** to avoid DB deadlocks with other suites · [`test_std_template_governance.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance.py) · [`test_std_template_governance_permissions.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_permissions.py) · [`test_std_template_governance_audit.py`](../../../../kentender_procurement/kentender_procurement/tender_management/tests/test_std_template_governance_audit.py) | Doc 7 §22.1–§22.3 matrix names; complements existing `test_std_template_governance_*_gov00X` modules. |
| STD-GOV-014 | Implementation review report (doc 7 §23 tail) | Done | [`STD-GOV-014_implementation_review_report.md`](STD-GOV-014_implementation_review_report.md) · rollup `bench … run-tests` 18 modules **159/159** OK (2026-05-04) incl. §22 sequential triplet + step9/10/11 · `test_std_template_governance_usage_gov008` tearDown fix (usage rows + counter reset before delete) | §1–§8 narrative; **doc 8 §C** closed — see §C and [`STD-GOV-doc8_smoke_environment_and_results.md`](STD-GOV-doc8_smoke_environment_and_results.md). |

---

## C. Smoke and acceptance gate (doc 8)

Minimum gate after **STD-GOV-013**: execute [`8. std_template_governance_lifecycle_smoke_test_specification.md`](8.%20std_template_governance_lifecycle_smoke_test_specification.md) scenarios (import → validate → … → retirement/archival, mutation/delete blocks, usage, audit, snapshot, UI visibility, SoD negatives, WORKS POC migration).

| Gate | Description | Status | Evidence | Notes |
|------|-------------|--------|----------|-------|
| C1 | Doc 8 preconditions satisfied | Done | `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8` — **12/12** tests OK (2026-05-04); includes **ST-001** · roles/seed covered by STD-GOV-001/012 + smoke | Roles, migrations, services; doc 8 fixture users created in smoke module |
| C2 | Doc 8 scenario execution (manual and/or automated) | Done | Bench **ST-002–ST-017, ST-020** · `npx playwright test …std-template-governance-smoke-doc8.spec.ts` **2/2** (ST-018, ST-019 direct URL) · **ST-019** officer tender `std_template` ref: [`officer-tender-poc-off-st-desk.spec.ts`](../../../../tests/ui/smoke/procurement/officer-tender-poc-off-st-desk.spec.ts) OFF-ST-002 · **§E** Desk navigation: [`std-governance-workspace-nav.spec.ts`](../../../../tests/ui/smoke/procurement/std-governance-workspace-nav.spec.ts) · matrix: [`STD-GOV-doc8_smoke_environment_and_results.md`](STD-GOV-doc8_smoke_environment_and_results.md) | Doc 8 §32 — **STD-GOV-103**; §33 — **STD-GOV-104** |
| C3 | Doc 8 principle: server-side enforcement, not cosmetic status | Done | Smoke class `TestStdTemplateGovernanceSmokeDoc8C3Principle` · ST-004/ST-016/ST-017 negatives in smoke module · GOV-007 `test_std_gov_007_supersede_with_usage_serializes_impact_payload` | Server guards + permission denials; JSON-safe audit payloads for supersede/retire with usage |

---

## D. Pack acceptance criteria rollup (doc 7 §25)

Track closure of **STD-GOV-IMPL-AC-001** … **017** here or in STD-GOV-014 notes.

| AC | Statement | Met |
|----|-----------|-----|
| STD-GOV-IMPL-AC-001 | Required roles created/seeded | Yes |
| STD-GOV-IMPL-AC-002 | `STD Template` has all required governance fields | Yes |
| STD-GOV-IMPL-AC-003 | Required child DocTypes exist | Yes |
| STD-GOV-IMPL-AC-004 | Hash canonicalization and package hash work | Yes |
| STD-GOV-IMPL-AC-005 | Audit event service appends lifecycle events | Yes |
| STD-GOV-IMPL-AC-006 | Validation service writes findings and updates status | Yes |
| STD-GOV-IMPL-AC-007 | Lifecycle transition methods enforce state guards | Yes |
| STD-GOV-IMPL-AC-008 | Approval and activation enforce package hash consistency | Yes |
| STD-GOV-IMPL-AC-009 | Separation of duty enforced or override-audited | Yes |
| STD-GOV-IMPL-AC-010 | Active-only tender eligibility enforced | Yes |
| STD-GOV-IMPL-AC-011 | Usage recording locks template from mutation/delete | Yes |
| STD-GOV-IMPL-AC-012 | Protected package mutation blocked and audited | Yes |
| STD-GOV-IMPL-AC-013 | Governance snapshot JSON and hash generated | Yes |
| STD-GOV-IMPL-AC-014 | Admin UI buttons/dialogs follow state and role matrix | Yes |
| STD-GOV-IMPL-AC-015 | Existing WORKS POC template governed through seed/migration | Yes |
| STD-GOV-IMPL-AC-016 | Required tests implemented | Yes |
| STD-GOV-IMPL-AC-017 | No out-of-scope downstream functionality introduced | Yes |

---

## E. STD Governance Desk navigation (Workspaces / §NAV)

Entry points for **Governance & Configuration** so admins are not expected to type DocType routes. Workspace: [`governance_and_configuration.json`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/workspace/governance_and_configuration/governance_and_configuration.json) (shortcuts + `lifecycle_status` filters per product spec).

| AC | Statement | Met | Evidence |
|----|-----------|-----|----------|
| STD-GOV-NAV-AC-001 | STD Governance workspace/menu exists (`Governance & Configuration` under Procurement) | Yes | Workspace JSON + Procurement sidebar link |
| STD-GOV-NAV-AC-002 | Admin can open catalogue from workspace (**Official STD Library — Catalogue** shortcut) | Yes | Playwright |
| STD-GOV-NAV-AC-003 | Admin can start import from workspace (**Import Official STD Package** shortcut) | Yes | Playwright (quick entry or new form) |
| STD-GOV-NAV-AC-004 | Admin can open Pending Validation filtered list | Yes | Shortcut + `stats_filter` (Imported, Validation Failed) |
| STD-GOV-NAV-AC-005 | Reviewer/Approver can open Pending Approval filtered list | Yes | Workspace **Has Role** includes Reviewer + Approver; Playwright Pending Approval |
| STD-GOV-NAV-AC-006 | Admin can open Active STD Templates filtered list | Yes | Playwright |
| STD-GOV-NAV-AC-007 | Admin/Auditor can open Usage and Audit views | Yes | Workspace roles include Auditor; shortcuts → `STD Template Usage`, `STD Template Lifecycle Event` |
| STD-GOV-NAV-AC-008 | Procurement Officer cannot see governance workspace unless separately authorized | Yes | Workspace roles **exclude** `Procurement Officer`; Playwright sidebar |

**Tests:** `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.tender_management.tests.test_std_governance_workspace_nav` · `npx playwright test tests/ui/smoke/procurement/std-governance-workspace-nav.spec.ts`

---

## How to use during implementation

1. Complete **§A** sign-off rows as stakeholders confirm specs (or log deferrals in [`ISSUES_LOG.md`](ISSUES_LOG.md)).
2. Run **§B** tickets in sequence; update **Evidence** with `bench` commands, module paths, Playwright spec paths, PR links.
3. Run **§C** smoke gate before declaring Workstream 1 implementation complete.
4. Tick **§D** AC rows when evidenced; **STD-GOV-014** should attach a final rollup narrative.
5. Run **§E** navigation tests after changing the Governance workspace or Procurement sidebar.
