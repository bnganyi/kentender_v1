# H1 — Procurement Planning governance completeness review

**Date:** 2026-04-24  
**Scope:** Server-side state machines, workflow APIs, template and profile rules, locks, DIA/Budget traceability, and handoff preconditions. Evidence is from the current `kentender_procurement` codebase (controllers, `workflow.py`, `pp_policy.py`, `template_application.py`, `procurement_package_line.py`).

---

## Executive summary

| Category | Assessment |
|----------|--------------|
| **Overall** | Governance is **largely complete** for the intended Desk + whitelisted-workflow paths. |
| **Blocking production signoff** | **None** identified in code review, provided stakeholders accept the **one consistency gap** below as a known limitation or schedule a small hardening pass. |

---

## Checklist (Cursor Pack H1)

### 1. Plan / package states complete

| Area | Verdict | Evidence |
|------|---------|----------|
| **Procurement Plan** | **Complete** | `VALID_STATUSES`, `ALLOWED_STATUS_TRANSITIONS`, role gates, reason gates, Submitted→Approved precondition (`procurement_plan.py`). |
| **Procurement Package** | **Complete** | `VALID_STATUSES`, `ALLOWED_STATUS_TRANSITIONS`, role gates, reason gates, transition preconditions for lines and handoff (`procurement_package.py`). |

### 2. Invalid transitions blocked

| Area | Verdict | Evidence |
|------|---------|----------|
| **Document layer** | **Complete** | `_raise_if_invalid_transition` on both DocTypes; unknown prior state rejected. |
| **Workflow API layer** | **Complete** | `workflow.py` uses `_assert_status` before mutating `status`; `pp_policy.assert_may_run_*` enforces role + expected state. |
| **Desk bypass** | **Acceptable** | Direct `save()` with forged `status` still runs Document `validate()` — same transition graph. Admin/SM remain privileged by design. |

### 3. Template mandatory everywhere required

| Area | Verdict | Evidence |
|------|---------|----------|
| **Package save** | **Complete** | `_validate_required_links` requires `template_id` and existence of `Procurement Template` (`procurement_package.py`). |
| **Template apply** | **Complete** | `apply_template_to_demands` requires `template_id`; `validate_demands_for_template` before insert (`template_application.py`). |

### 4. Approved and ready states locked

| Area | Verdict | Evidence |
|------|---------|----------|
| **Plan** | **Complete** | `READONLY_STATUSES` includes Submitted+; `_enforce_lock_on_approved_states` with narrow escape for `status` + `workflow_reason`; `total_planned_value` skipped (`procurement_plan.py`). |
| **Package** | **Complete** | `READONLY_STATUSES` includes Submitted+; `_enforce_lock_on_terminal_states` allows workflow fields + planner/exception notes (`procurement_package.py`). |
| **Package lines** | **Complete** | `PACKAGE_EDITABLE_STATUSES` = Draft/Structured only (`procurement_package_line.py`). |

### 5. Method override governance

| Area | Verdict | Evidence |
|------|---------|----------|
| **Override reason** | **Complete** | `_validate_method_override` requires reason when flag set (`procurement_package.py`). |
| **Template sync (C3)** | **Complete** | `_apply_template_derived_defaults_c3` resets method/contract from template when not overriding, in Draft/Structured. |
| **Allowed methods** | **Complete** | Default must sit in template `allowed_methods`; override path validates chosen method in list (`procurement_package.py`). |
| **Post-Structured lock** | **Complete** | `_validate_procurement_method_editable_states_c3` blocks method/contract/override flag changes after Structured. |
| **Threshold rules** | **Acknowledged gap** | Non-empty `threshold_rules` on template is explicitly a **v1 no-op** (interpreter deferred per implementation tracker). Not a silent security hole — behaviour is documented. |

### 6. Traceability to DIA and Budget Line

| Area | Verdict | Evidence |
|------|---------|----------|
| **Line → Demand** | **Complete** | Demand must exist and status ∈ {Approved, Planning Ready} (`procurement_package_line.py`). |
| **Line → Budget Line** | **Complete** | Required link; must match `Demand.budget_line` (`_validate_budget_line_matches_demand`). |
| **One active line per demand (v1)** | **Complete** | `_validate_one_demand_one_active_line`. |
| **Upstream mutation** | **Complete** | `template_application.apply_template_to_demands` docstring and implementation: **no Demand mutation**. |

### 7. Package readiness handoff trustworthy

| Area | Verdict | Evidence |
|------|---------|----------|
| **Draft → Structured** | **Complete** | Not on first save as new without prior save path blocked; ≥1 active line (`procurement_package.py`). |
| **Structured → Submitted** | **Complete** | ≥1 active line. |
| **Approved → Ready** | **Complete** | ≥1 active line; competitive methods require `decision_criteria_profile_id` (duplicates `_validate_competitive_decision_profile` at submit time — consistent). |
| **Workflow API** | **Complete** | `mark_ready_for_tender` asserts Approved + policy role check (`workflow.py`, `pp_policy.py`). |

---

## Complete (summary list)

- Plan and package state machines with role and reason enforcement  
- Whitelisted workflow actions aligned with Document rules + `pp_policy`  
- Template required on every package save; template apply gated on Draft plan  
- Field locks on governance statuses; controlled exceptions for workflow and notes  
- Method override, template default sync, and post-Structured method lock  
- Package line eligibility, budget line integrity, single active assignment per demand (v1)  
- Handoff preconditions (lines + competitive criteria) for structure, submit, and ready-for-tender  
- No Demand mutation in template application path  

---

## Missing (gaps or deferred by design)

| Item | Severity | Notes |
|------|----------|-------|
| **Threshold band interpreter** | Design / Phase | Documented v1 no-op; not “missing” silently — tracker calls it out. |
| **Stricter parent-plan coupling on every save** | Optional hardening | See **Risky** — not implemented on package `validate` for all operations. |

---

## Risky (acceptable for UAT; watch for production)

| Risk | Detail | Mitigation |
|------|--------|------------|
| **New package on non-Draft plan via Desk Form** | Was a gap vs template apply. | **Resolved (H3):** `_validate_parent_plan_draft_for_bootstrap` on `Procurement Package` — insert and `plan_id` change (non–Admin/SM) require parent plan **Draft**. |
| **Operational** | G1 smoke can leave F1 plan in **Approved**; PP7 skips when demands fully packaged — documented in tracker. | Re-seed or use dedicated CI site for deterministic G1. |

---

## Must-fix before module signoff

**None** — the Form/bootstrap gap identified in the original H1 review was **closed in H3** (`procurement_package.py` + `test_procurement_planning_h3_plan_bootstrap.py`).

---

## Sign-off recommendation

- **H1 (governance completeness review):** **Pass** — documented, evidence-based; follow-up guard delivered in **H3**.  
- **Next:** **H2** / **H3** (completed 2026-04-24 per tracker).

---

## References (code)

- `procurement_planning/doctype/procurement_plan/procurement_plan.py`  
- `procurement_planning/doctype/procurement_package/procurement_package.py`  
- `procurement_planning/doctype/procurement_package_line/procurement_package_line.py`  
- `procurement_planning/api/workflow.py`  
- `procurement_planning/permissions/pp_policy.py`  
- `procurement_planning/services/template_application.py`  
- `procurement_planning/services/template_applicability.py` (C1 validation used by apply)
