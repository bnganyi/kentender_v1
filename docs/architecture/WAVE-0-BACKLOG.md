# Wave 0 backlog (tracking) — KenTender foundation

**Purpose:** Sprint / milestone tracking only. **Do not** duplicate full objectives, acceptance criteria, or test plans here.

**Canonical tickets:** [`../prompts/architecture/prompts.md`](../prompts/architecture/prompts.md) — each `PHASE X` section is the source of truth.

**Execution order:** Phases **A → B → … → L** in prompt order, then **La** (UI smoke, after L). Do not skip or reorder without an explicit architecture decision.

**Architecture (non‑negotiable):** [`kentender_architecture_rules.md`](kentender_architecture_rules.md)

**Last verified (repo + bench):** 2026-04-18 — Phases A–L and **La** (docs + automation): nine apps; master DocTypes; numbering + **Audit Event** + `log_audit_event`; **Exception Record**; **Typed Attachment**; entity-scope stubs; `run_workflow_guard`; `execute_business_action`; `send_notification`; placeholder **Workspaces** (Strategy / Budget / Procurement) + **Workspace Sidebar** JSON; `test_wave0_smoke.py` + `make -C apps/kentender_v1 smoke`; `bench --site kentender.midas.com run-tests --app kentender_core` passes; `python3 apps/kentender_v1/scripts/guard_frappe_scaffolds.py` exits 0. **Phase La:** `cd apps/kentender_v1 && npm run test:ui:smoke` (requires running site, Node, `.env.ui` — see `playwright.config.ts`); `make -C apps/kentender_v1 ui-smoke` runs the same.

---

## Phase tracker

| Phase ID | Title (short) | Epic | Depends on | # | Status | Verify (repeatable) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PHASE-A | App skeleton | EPIC-FOUNDATION | none | 1 | Done | `make -C apps/kentender_v1 validate-links`; `bench --site kentender.midas.com list-apps`; `python3 apps/kentender_v1/scripts/guard_frappe_scaffolds.py` | Nine apps; `doctype/`, `services/`, `api/`, `tests/`, `utils/` under each inner package; monorepo Makefile + scripts. |
| PHASE-B | Core foundational DocTypes | EPIC-FOUNDATION | PHASE-A | 2 | Done | `bench --site kentender.midas.com run-tests --app kentender_core`; DocTypes visible in Desk under Kentender Core | **Procuring Department** (not `Department`) — ERPNext already defines `Department`. Files live under `kentender_core/kentender_core/kentender_core/doctype/`. |
| PHASE-C | Numbering service | EPIC-SERVICES | PHASE-B | 3 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_numbering.py`) | `generate_business_id` in `kentender_core/kentender_core/services/business_id_service.py`; counters in DocType **Business ID Counter**. |
| PHASE-D | Audit event framework | EPIC-SERVICES | PHASE-A | 4 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_audit_event.py`) | DocType **Audit Event**; `log_audit_event` in `kentender_core/kentender_core/services/audit_event_service.py` (insert with `ignore_permissions=True`). |
| PHASE-E | Exception record | EPIC-SERVICES | PHASE-A | 5 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_exception_record.py`) | DocType **Exception Record** (`reference_doctype` → DocType, `reference_name` Dynamic Link); `created_by` from session on insert; files under `kentender_core/kentender_core/kentender_core/doctype/exception_record/`. |
| PHASE-F | Typed attachment model | EPIC-SERVICES | PHASE-A | 6 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_typed_attachment.py`) | DocType **Typed Attachment** (`file` Attach; `attachment_type`; `linked_doctype` / `linked_name` Dynamic Link; `sensitivity_level`); files under `kentender_core/kentender_core/kentender_core/doctype/typed_attachment/`. |
| PHASE-G | Entity scope & permission helpers | EPIC-SECURITY | PHASE-B | 7 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_entity_scope.py`) | Stubs: `get_user_entity`, `get_user_departments`, `filter_by_entity` in `kentender_core/kentender_core/utils/entity_scope.py`. |
| PHASE-H | Workflow guard framework | EPIC-SECURITY | PHASE-A | 8 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_workflow_guard.py`) | `run_workflow_guard(action, document)` → `(ok, message)` in `kentender_core/kentender_core/services/workflow_guard_service.py` (Phase H placeholder). |
| PHASE-I | Controlled business action pattern | EPIC-SECURITY | PHASE-D, PHASE-H | 9 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_business_action.py`) | `execute_business_action(action, document)` in `kentender_core/kentender_core/services/business_action_service.py` (guard then `log_audit_event`, `event_type` `ken.business_action`). |
| PHASE-J | Notification framework | EPIC-SERVICES | PHASE-A | 10 | Done | `bench --site kentender.midas.com run-tests --app kentender_core` (includes `test_notification_service.py`) | `send_notification(user, message)` in `kentender_core/kentender_core/services/notification_service.py` (Frappe logger `kentender.notification`). |
| PHASE-K | Base workspace scaffolding | EPIC-UX | PHASE-A | 11 | Done | `bench --site kentender.midas.com migrate` (Workspace + Workspace Sidebar sync) | **Strategy Management**, **Budget Management**, **Procurement** + sidebars; workspace JSON under inner module package `.../kentender_*/kentender_*/kentender_*/workspace/`; `workspace_sidebar/*.json` under `.../kentender_*/kentender_*/`. |
| PHASE-L | Smoke test foundation | EPIC-QUALITY | All previous | 12 | Done | `make -C apps/kentender_v1 smoke`; `bench --site kentender.midas.com run-tests --app kentender_core --module kentender_core.tests.test_wave0_smoke` | `test_wave0_smoke.py`: installed apps + hooks import; **Procuring Entity** round-trip; `generate_business_id`; `log_audit_event`; **Exception Record**; `run_workflow_guard`. |
| PHASE-La | UI smoke (Playwright) | EPIC-QUALITY | PHASE-I, PHASE-K, PHASE-L | 13 | Done | `cd apps/kentender_v1 && npm run test:ui:smoke`; `make -C apps/kentender_v1 ui-smoke` | Playwright specs under `tests/ui/smoke/`; `UI_BASE_URL` / `.env.ui`; does not replace Phase L (no UI tests in bench smoke). |

**Status values:** `Not Started` | `In Progress` | `Blocked` | `Done`

**Maintenance:** After each merged story or agreed milestone, update **Status** and **Notes** for that row. Use **Done** only when the matching section in [`prompts.md`](../prompts/architecture/prompts.md) is satisfied.

---

## Allowed apps (9)

- kentender_core  
- kentender_strategy  
- kentender_budget  
- kentender_procurement  
- kentender_governance  
- kentender_compliance  
- kentender_stores  
- kentender_assets  
- kentender_integrations  

**Dependency direction (strict):** `core → strategy → budget → procurement → stores → assets` (governance / compliance / integrations consume published interfaces — see global architecture doc).

---

## Wave 1

TBD after Wave 0 phases A–L (and optional La) are **Done**.

---

## Changelog

- **2026-04-18** — **PHASE-La** **Done** (tracking): UI smoke via Playwright — `npm run test:ui:smoke` / `tests/ui/smoke/`; `make -C apps/kentender_v1 ui-smoke`; canonical prompt in [`prompts.md`](../prompts/architecture/prompts.md) (**PHASE La**); browser-level verification after Phase L (Phase L remains backend-only).
- **2026-04-18** — PHASE-L **Done**: `kentender_core/tests/test_wave0_smoke.py` (nine apps + hooks; PE; numbering; audit; exception; workflow guard); `make -C apps/kentender_v1 smoke` runs `guard_frappe_scaffolds.py` + targeted `bench run-tests --module kentender_core.tests.test_wave0_smoke`.
- **2026-04-18** — PHASE-K **Done**: Placeholder Workspaces **Strategy Management**, **Budget Management**, **Procurement** (JSON under triple inner module path per app); **Workspace Sidebar** for Kentender Strategy / Budget / Procurement.
- **2026-04-18** — PHASE-J **Done**: `send_notification` in `services/notification_service.py` (log-based); tests in `test_notification_service.py`.
- **2026-04-18** — PHASE-I **Done**: `execute_business_action` in `services/business_action_service.py` (`run_workflow_guard` then `log_audit_event`); tests in `test_business_action.py`.
- **2026-04-18** — PHASE-H **Done**: `run_workflow_guard(action, document)` in `services/workflow_guard_service.py` (returns `(True, "")`); tests in `test_workflow_guard.py`.
- **2026-04-18** — PHASE-G **Done**: `get_user_entity`, `get_user_departments`, `filter_by_entity` in `utils/entity_scope.py` (stubs); tests in `test_entity_scope.py`.
- **2026-04-18** — PHASE-F **Done**: DocType **Typed Attachment** (hash autoname; **Attach** `file`; `attachment_type`, `linked_doctype` / `linked_name`, `sensitivity_level`); tests in `test_typed_attachment.py`.
- **2026-04-18** — PHASE-E **Done**: DocType **Exception Record** (hash autoname; `reference_doctype` / `reference_name` Dynamic Link; `reason`, `approved_by`, `status`, `created_by`); thin `before_insert` for `created_by`; tests in `test_exception_record.py`.
- **2026-04-18** — PHASE-D **Done**: DocType **Audit Event** (eight fields); `log_audit_event(...)`; JSON metadata; tests in `test_audit_event.py`.
- **2026-04-18** — PHASE-C **Done**: `Business ID Counter` DocType; `generate_business_id(prefix, entity, year)` → `PREFIX-ENTITY-YEAR-XXXX`; persisted counters with `SELECT … FOR UPDATE`; tests in `test_numbering.py`.
- **2026-04-18** — PHASE-B **Done**: `Procuring Entity`, `Procuring Department`, `Business Unit` in `kentender_core` (module **Kentender Core**); thin controllers; minimal System Manager / Administrator permissions; integration test `test_master_data.py`; `reload_doc` / migrate used to sync JSON into `tabDocType`.
- **2026-04-18** — PHASE-A **Done**: Frappe apps generated with `bench new-app`, placed under `apps/kentender_v1/<app>/`, symlinks from `apps/`, standard empty packages; `sites/apps.txt` lists all nine `kentender_*` apps; Makefile + `scripts/dev-*.sh` added; guard script passes.
