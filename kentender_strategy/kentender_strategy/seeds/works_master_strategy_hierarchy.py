# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master strategy hierarchy — seed data specification §8 (R2-004 / LV-R2-001-04).

Idempotent upsert of **Strategic Plan**, **Strategy Program**, **Strategy Objective**, and
**Strategy Target** for the MOH healthcare-infrastructure priority chain. Respects G2: child
mutations require the parent **Strategic Plan** to be in **Draft**; the plan is set to
**Active** at the end (spec §8 *Approved* maps to Frappe **Active**).

**Prerequisite:** a **Procuring Entity** with ``entity_code`` **PE-MOH** or **MOH** must exist
(LV-R2-001-03). This module does not create the entity.
"""

from __future__ import annotations

from typing import Any, Final

import frappe

# --- Canonical codes (G0-008 / seed spec §8) ---
STRATEGY_PLAN_CODE: Final[str] = "STRAT-MOH-2026"
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026\u20132030"
START_YEAR: Final[int] = 2026
END_YEAR: Final[int] = 2030
PROGRAM_CODE: Final[str] = "PROG-MOH-INFRA"
PROGRAM_TITLE: Final[str] = "Healthcare Infrastructure Rehabilitation"
PROGRAM_DESCRIPTION: Final[str] = (
	"Rehabilitation and improvement of priority district health facilities to improve access and quality of care."
)
OBJECTIVE_CODE: Final[str] = "OBJ-MOH-HOSP-RENOV"
OBJECTIVE_TITLE: Final[str] = "Improve district hospital infrastructure readiness"
OBJECTIVE_DESCRIPTION: Final[str] = (
	"Renovate and restore critical district hospital facilities to support safe and continuous healthcare service delivery."
)
SUB_PROGRAM_CODE: Final[str] = "SUB-MOH-INFRA-001"
SUB_PROGRAM_TITLE: Final[str] = "District health facility rehabilitation"
TARGET_CODE: Final[str] = "TGT-MOH-HOSP-RENOV-2026"
TARGET_TITLE: Final[str] = "Renovate priority district hospital facilities in FY 2026/2027"
TARGET_METRIC_TEXT: Final[str] = "Number of priority district hospital renovation projects initiated"


def desk_visibility(procuring_entity_name: str) -> dict[str, str]:
	"""Explain why Desk lists / landing may look empty for non-Administrator users."""
	return {
		"procuring_entity": procuring_entity_name,
		"scope_rule": (
			"Strategic Plan, Strategy Program, Strategy Objective, and Strategy Target are entity-scoped. "
			"Unless you are Administrator or System Manager, your user must have "
			"User.kt_procuring_entity set to this exact Procuring Entity name, "
			"or a User Permission on Procuring Entity with For Value = this name."
		),
		"optional_seed_fix": (
			"bench execute kentender_strategy.seeds.seed_works_master_strategy_hierarchy.run "
			'--kwargs \'{"sync_scope_user_email": "you@example.com"}\' '
			"to add a User Permission for that user on the seeded entity (dev/UAT)."
		),
	}


def resolve_procuring_entity_moh() -> str | None:
	"""Return Procuring Entity ``name`` for PE-MOH or legacy MOH code."""
	for code in ("PE-MOH", "MOH"):
		name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
		if name:
			return name
	return None


def _find_strategic_plan(pe_name: str) -> str | None:
	"""Resolve an existing master plan row; never guess an unrelated PE+year-only match."""
	rows = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": pe_name,
			"start_year": START_YEAR,
			"end_year": END_YEAR,
		},
		fields=["name", "strategic_plan_name"],
		order_by="modified desc",
		limit=50,
	)
	for row in rows:
		if (row.get("strategic_plan_name") or "").strip() == PLAN_TITLE:
			return row.name
		if frappe.db.exists(
			"Strategy Program",
			{"strategic_plan": row.name, "program_code": PROGRAM_CODE},
		):
			return row.name
	return None


def _create_strategic_plan(pe_name: str) -> str:
	doc = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"strategic_plan_name": PLAN_TITLE,
			"procuring_entity": pe_name,
			"start_year": START_YEAR,
			"end_year": END_YEAR,
			"status": "Draft",
			"version_no": 1,
			"is_current_version": 1,
			"description": (
				f"WORKS master seed (spec §8). strategy_plan_code={STRATEGY_PLAN_CODE}. "
				f"plan_period {START_YEAR}-01-01 .. {END_YEAR}-12-31."
			),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _hierarchy_complete(plan_name: str) -> bool:
	prog = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_code": PROGRAM_CODE},
		"name",
	)
	if not prog:
		return False
	sp = frappe.db.get_value(
		"Sub Program",
		{"program": prog, "sub_program_code": SUB_PROGRAM_CODE},
		"name",
	)
	if not sp:
		return False
	obj = frappe.db.get_value(
		"Strategy Objective",
		{"sub_program": sp, "objective_code": OBJECTIVE_CODE},
		["name", "strategic_plan", "program", "sub_program"],
		as_dict=True,
	)
	if not obj or obj.strategic_plan != plan_name or obj.program != prog or obj.sub_program != sp:
		return False
	tgt = frappe.db.get_value(
		"Strategy Target",
		{"objective": obj.name, "target_code": TARGET_CODE},
		"name",
	)
	return bool(tgt)


def _ensure_program(plan_name: str) -> str:
	existing = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_code": PROGRAM_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Strategy Program", existing)
		changed = False
		if (doc.program_title or "").strip() != PROGRAM_TITLE:
			doc.program_title = PROGRAM_TITLE
			changed = True
		if (doc.description or "").strip() != PROGRAM_DESCRIPTION:
			doc.description = PROGRAM_DESCRIPTION
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Strategy Program",
			"strategic_plan": plan_name,
			"program_title": PROGRAM_TITLE,
			"program_code": PROGRAM_CODE,
			"description": PROGRAM_DESCRIPTION,
			"order_index": 10,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _ensure_sub_program(plan_name: str, program_name: str) -> str:
	existing = frappe.db.get_value(
		"Sub Program",
		{"program": program_name, "sub_program_code": SUB_PROGRAM_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Sub Program", existing)
		changed = False
		if doc.strategic_plan != plan_name:
			doc.strategic_plan = plan_name
			changed = True
		if (doc.title or "").strip() != SUB_PROGRAM_TITLE:
			doc.title = SUB_PROGRAM_TITLE
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Sub Program",
			"strategic_plan": plan_name,
			"program": program_name,
			"title": SUB_PROGRAM_TITLE,
			"sub_program_code": SUB_PROGRAM_CODE,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _ensure_objective(plan_name: str, program_name: str, sub_program_name: str) -> str:
	existing = frappe.db.get_value(
		"Strategy Objective",
		{"sub_program": sub_program_name, "objective_code": OBJECTIVE_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Strategy Objective", existing)
		changed = False
		if doc.strategic_plan != plan_name:
			doc.strategic_plan = plan_name
			changed = True
		if doc.program != program_name:
			doc.program = program_name
			changed = True
		if doc.sub_program != sub_program_name:
			doc.sub_program = sub_program_name
			changed = True
		if (doc.objective_title or "").strip() != OBJECTIVE_TITLE:
			doc.objective_title = OBJECTIVE_TITLE
			changed = True
		if (doc.description or "").strip() != OBJECTIVE_DESCRIPTION:
			doc.description = OBJECTIVE_DESCRIPTION
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": plan_name,
			"program": program_name,
			"sub_program": sub_program_name,
			"objective_title": OBJECTIVE_TITLE,
			"objective_code": OBJECTIVE_CODE,
			"description": OBJECTIVE_DESCRIPTION,
			"order_index": 10,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _ensure_target(plan_name: str, program_name: str, objective_name: str) -> str:
	existing = frappe.db.get_value(
		"Strategy Target",
		{"objective": objective_name, "target_code": TARGET_CODE},
		"name",
	)
	if existing:
		doc = frappe.get_doc("Strategy Target", existing)
		changed = False
		if doc.strategic_plan != plan_name:
			doc.strategic_plan = plan_name
			changed = True
		if doc.program != program_name:
			doc.program = program_name
			changed = True
		if (doc.target_title or "").strip() != TARGET_TITLE:
			doc.target_title = TARGET_TITLE
			changed = True
		desc = f"{TARGET_METRIC_TEXT} (spec §8.4)."
		if (doc.description or "").strip() != desc:
			doc.description = desc
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
		return existing
	child = frappe.get_doc(
		{
			"doctype": "Strategy Target",
			"strategic_plan": plan_name,
			"program": program_name,
			"objective": objective_name,
			"target_title": TARGET_TITLE,
			"target_code": TARGET_CODE,
			"description": f"{TARGET_METRIC_TEXT} (spec §8.4).",
			"order_index": 10,
			"measurement_type": "Numeric",
			"target_value_numeric": 1,
			"target_unit": "projects",
			"target_period_type": "Annual",
			"target_year": START_YEAR,
		}
	)
	child.insert(ignore_permissions=True)
	return child.name


def _names_when_complete(plan_name: str) -> tuple[str, str, str] | None:
	prog = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_code": PROGRAM_CODE},
		"name",
	)
	if not prog:
		return None
	sp = frappe.db.get_value(
		"Sub Program",
		{"program": prog, "sub_program_code": SUB_PROGRAM_CODE},
		"name",
	)
	if not sp:
		return None
	obj = frappe.db.get_value(
		"Strategy Objective",
		{"sub_program": sp, "objective_code": OBJECTIVE_CODE},
		"name",
	)
	if not obj:
		return None
	tgt = frappe.db.get_value(
		"Strategy Target",
		{"objective": obj, "target_code": TARGET_CODE},
		"name",
	)
	if not tgt:
		return None
	return prog, obj, tgt


def upsert_works_master_strategy_hierarchy() -> dict[str, Any]:
	"""Create or refresh the §8 strategy chain; return a small summary dict."""
	pe = resolve_procuring_entity_moh()
	if not pe:
		return {
			"ok": False,
			"error_code": "MISSING_PROCURING_ENTITY",
			"message": (
				"No Procuring Entity with entity_code PE-MOH or MOH. "
				"Run LV-R2-001-03 (PE-MOH seed) or create the entity before this seed."
			),
		}

	plan_name = _find_strategic_plan(pe)
	if not plan_name:
		plan_name = _create_strategic_plan(pe)

	plan = frappe.get_doc("Strategic Plan", plan_name)
	prev_status = (plan.status or "").strip()

	# G2: never save Program/Objective/Target while plan is Active. If already aligned, only
	# ensure plan status is Active (spec §8 Approved) and return.
	if _hierarchy_complete(plan_name):
		names = _names_when_complete(plan_name)
		if names:
			prog, obj, tgt = names
			if prev_status != "Active":
				plan.status = "Active"
				plan.save(ignore_permissions=True)
			return {
				"ok": True,
				"procuring_entity": pe,
				"strategic_plan": plan_name,
				"strategy_program": prog,
				"strategy_objective": obj,
				"strategy_target": tgt,
				"codes": {
					"strategy_plan_code": STRATEGY_PLAN_CODE,
					"programme_code": PROGRAM_CODE,
					"objective_code": OBJECTIVE_CODE,
					"target_code": TARGET_CODE,
				},
				"idempotent": True,
			}

	if prev_status != "Draft":
		plan.status = "Draft"
		plan.save(ignore_permissions=True)
		plan.reload()

	program_name = _ensure_program(plan_name)
	sub_program_name = _ensure_sub_program(plan_name, program_name)
	objective_name = _ensure_objective(plan_name, program_name, sub_program_name)
	target_name = _ensure_target(plan_name, program_name, objective_name)

	plan.reload()
	if (plan.status or "").strip() != "Active":
		plan.status = "Active"
		plan.save(ignore_permissions=True)

	return {
		"ok": True,
		"procuring_entity": pe,
		"strategic_plan": plan_name,
		"strategy_program": program_name,
		"strategy_objective": objective_name,
		"strategy_target": target_name,
		"codes": {
			"strategy_plan_code": STRATEGY_PLAN_CODE,
			"programme_code": PROGRAM_CODE,
			"objective_code": OBJECTIVE_CODE,
			"target_code": TARGET_CODE,
		},
		"idempotent": False,
	}
