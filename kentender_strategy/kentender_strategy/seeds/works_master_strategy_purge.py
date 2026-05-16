# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UAT cleanup: remove Strategic Plan trees that are not the WORKS master §8 row.

Keeps at most one canonical plan: **Ministry of Health Strategic Plan 2026–2030** on PE-MOH/MOH
with years 2026–2030. Prefer the row that already has ``program_code`` **PROG-MOH-INFRA** when
duplicates exist.

Cross-module rows (Demand, Budget Line, Budget, Budget Allocation) that **link** to a plan
scheduled for removal block deletion unless ``delete_blocking_demands_and_budget_lines`` is true
(UAT destructive — removes those Demands and Budget Lines first).
"""

from __future__ import annotations

from typing import Any, Final

import frappe
from frappe.utils import cint

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	OBJECTIVE_CODE,
	PLAN_TITLE,
	PROGRAM_CODE,
	START_YEAR,
	END_YEAR,
	TARGET_CODE,
	STRATEGY_PLAN_CODE,
	resolve_procuring_entity_moh,
)

_ALLOWED_ENTITY_CODES: Final[tuple[str, ...]] = ("PE-MOH", "MOH")


def allowed_procuring_entity_names() -> set[str]:
	names: set[str] = set()
	for code in _ALLOWED_ENTITY_CODES:
		n = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
		if n:
			names.add(n)
	return names


def protected_works_strategic_plan_names() -> set[str]:
	"""Docnames of Strategic Plan rows that must survive purge (canonical §8 shell)."""
	pe_names = allowed_procuring_entity_names()
	if not pe_names:
		return set()
	candidates = frappe.get_all(
		"Strategic Plan",
		filters={
			"strategic_plan_name": PLAN_TITLE,
			"start_year": START_YEAR,
			"end_year": END_YEAR,
			"procuring_entity": ("in", list(pe_names)),
		},
		fields=["name", "modified"],
		order_by="modified desc",
	)
	if not candidates:
		return set()
	with_prog = [
		c.name
		for c in candidates
		if frappe.db.exists(
			"Strategy Program",
			{"strategic_plan": c.name, "program_code": PROGRAM_CODE},
		)
	]
	if with_prog:
		return {with_prog[0]}
	return {candidates[0].name}


def _programs_objectives_targets(plan_name: str) -> tuple[list[str], list[str], list[str]]:
	progs = frappe.get_all("Strategy Program", filters={"strategic_plan": plan_name}, pluck="name")
	objs = frappe.get_all("Strategy Objective", filters={"strategic_plan": plan_name}, pluck="name")
	tgts = frappe.get_all("Strategy Target", filters={"strategic_plan": plan_name}, pluck="name")
	return progs, objs, tgts


def count_blocking_links(plan_name: str) -> int:
	"""Count Demand / Budget / Budget Allocation / Budget Line rows referencing this plan tree."""
	progs, objs, tgts = _programs_objectives_targets(plan_name)
	n = 0
	n += frappe.db.count("Budget Line", {"strategic_plan": plan_name})
	n += frappe.db.count("Budget", {"strategic_plan": plan_name})
	n += frappe.db.count("Budget Allocation", {"strategic_plan": plan_name})
	for p in progs:
		n += frappe.db.count("Budget Allocation", {"program": p})
	n += frappe.db.count("Demand", {"strategic_plan": plan_name})
	for p in progs:
		n += frappe.db.count("Budget Line", {"program": p})
		n += frappe.db.count("Demand", {"program": p})
	for o in objs:
		n += frappe.db.count("Budget Line", {"output_indicator": o})
		n += frappe.db.count("Demand", {"output_indicator": o})
	for t in tgts:
		n += frappe.db.count("Budget Line", {"performance_target": t})
		n += frappe.db.count("Demand", {"performance_target": t})
	return int(n)


def _delete_blocking_rows(plan_name: str) -> dict[str, int]:
	"""Remove rows that block Strategic Plan deletion (UAT only).

	Budget Line / Budget controllers block normal deletes; we set ``frappe.flags.budget_line_force_delete``
	and force-affected **Budget** rows to **Draft** via SQL so ``BudgetAllocation`` / ``Budget`` trash hooks pass.
	"""
	progs, objs, tgts = _programs_objectives_targets(plan_name)
	deleted: dict[str, int] = {"Demand": 0, "Budget Line": 0, "Budget Allocation": 0, "Budget": 0}

	flt_budget_lines: list[dict[str, Any]] = [{"strategic_plan": plan_name}]
	for p in progs:
		flt_budget_lines.append({"program": p})
	for o in objs:
		flt_budget_lines.append({"output_indicator": o})
	for t in tgts:
		flt_budget_lines.append({"performance_target": t})

	flt_ba: list[dict[str, Any]] = [{"strategic_plan": plan_name}]
	for p in progs:
		flt_ba.append({"program": p})

	budget_names: set[str] = set()
	budget_names.update(frappe.get_all("Budget", filters={"strategic_plan": plan_name}, pluck="name"))
	for flt in flt_budget_lines:
		for row in frappe.get_all("Budget Line", filters=flt, fields=["name", "budget"]):
			if row.get("budget"):
				budget_names.add(row.budget)
	for flt in flt_ba:
		for row in frappe.get_all("Budget Allocation", filters=flt, fields=["name", "budget"]):
			if row.get("budget"):
				budget_names.add(row.budget)

	if budget_names:
		for bn in budget_names:
			frappe.db.sql("UPDATE `tabBudget` SET `status`=%s WHERE `name`=%s", ("Draft", bn))

	seen_bl: set[str] = set()
	try:
		frappe.flags.budget_line_force_delete = True
		for flt in flt_budget_lines:
			for name in frappe.get_all("Budget Line", filters=flt, pluck="name"):
				if name in seen_bl:
					continue
				seen_bl.add(name)
				frappe.delete_doc("Budget Line", name, force=1, ignore_permissions=True)
				deleted["Budget Line"] += 1
	finally:
		frappe.flags.budget_line_force_delete = False

	seen_ba: set[str] = set()
	for flt in flt_ba:
		for name in frappe.get_all("Budget Allocation", filters=flt, pluck="name"):
			if name in seen_ba:
				continue
			seen_ba.add(name)
			frappe.delete_doc("Budget Allocation", name, force=1, ignore_permissions=True)
			deleted["Budget Allocation"] += 1

	for name in frappe.get_all("Budget", filters={"strategic_plan": plan_name}, pluck="name"):
		frappe.delete_doc("Budget", name, force=1, ignore_permissions=True)
		deleted["Budget"] += 1

	seen_dm: set[str] = set()
	for flt in (
		{"strategic_plan": plan_name},
		*({"program": p} for p in progs),
		*({"output_indicator": o} for o in objs),
		*({"performance_target": t} for t in tgts),
	):
		for name in frappe.get_all("Demand", filters=flt, pluck="name"):
			if name in seen_dm:
				continue
			seen_dm.add(name)
			frappe.delete_doc("Demand", name, force=1, ignore_permissions=True)
			deleted["Demand"] += 1

	return deleted


def _set_plan_draft(plan_name: str) -> None:
	"""Set status to Draft without loading the document (avoids LinkValidationError for stale PE links)."""
	frappe.db.sql(
		"UPDATE `tabStrategic Plan` SET `status`=%s WHERE `name`=%s",
		("Draft", plan_name),
	)


def _delete_plan_tree(plan_name: str) -> None:
	_set_plan_draft(plan_name)
	for node in frappe.get_all("Strategy Node", filters={"strategic_plan": plan_name}, pluck="name"):
		frappe.delete_doc("Strategy Node", node, force=1, ignore_permissions=True)
	for tgt in frappe.get_all("Strategy Target", filters={"strategic_plan": plan_name}, pluck="name"):
		frappe.delete_doc("Strategy Target", tgt, force=1, ignore_permissions=True)
	for obj in frappe.get_all("Strategy Objective", filters={"strategic_plan": plan_name}, pluck="name"):
		frappe.delete_doc("Strategy Objective", obj, force=1, ignore_permissions=True)
	for prog in frappe.get_all("Strategy Program", filters={"strategic_plan": plan_name}, pluck="name"):
		for sp in frappe.get_all("Sub Program", filters={"program": prog}, pluck="name"):
			frappe.delete_doc("Sub Program", sp, force=1, ignore_permissions=True)
		frappe.delete_doc("Strategy Program", prog, force=1, ignore_permissions=True)
	frappe.delete_doc("Strategic Plan", plan_name, force=1, ignore_permissions=True)


def purge_non_works_strategy_hierarchy(
	*,
	dry_run: bool = False,
	delete_blocking_demands_and_budget_lines: bool = False,
	restrict_procuring_entity_names: list[str] | None = None,
) -> dict[str, Any]:
	"""Delete Strategic Plan documents (and children) that are not the protected WORKS §8 row.

	:param restrict_procuring_entity_names: When set, only consider Strategic Plan rows whose
		``procuring_entity`` is in this list (tests / narrow UAT cleanup). When omitted, every
		non-protected plan in the site is eligible for removal.
	"""
	protected = protected_works_strategic_plan_names()
	all_plans = frappe.get_all("Strategic Plan", pluck="name")
	if restrict_procuring_entity_names:
		allowed_pe = frozenset(restrict_procuring_entity_names)
		all_plans = [
			n
			for n in all_plans
			if (frappe.db.get_value("Strategic Plan", n, "procuring_entity") or "") in allowed_pe
		]
	to_remove = [n for n in all_plans if n not in protected]

	removed: list[str] = []
	skipped: list[dict[str, Any]] = []
	deleted_blockers: dict[str, int] = {}

	for plan in to_remove:
		links = count_blocking_links(plan)
		if links > 0 and not delete_blocking_demands_and_budget_lines:
			skipped.append({"strategic_plan": plan, "blocking_link_count": links})
			continue
		if dry_run:
			removed.append(plan)
			continue
		if links > 0 and delete_blocking_demands_and_budget_lines:
			db = _delete_blocking_rows(plan)
			for k, v in db.items():
				deleted_blockers[k] = deleted_blockers.get(k, 0) + v
		_delete_plan_tree(plan)
		removed.append(plan)

	return {
		"ok": len(skipped) == 0,
		"dry_run": dry_run,
		"restrict_procuring_entity_names": restrict_procuring_entity_names,
		"protected_strategic_plans": sorted(protected),
		"removed_strategic_plans": removed,
		"skipped_strategic_plans": skipped,
		"deleted_blockers": deleted_blockers or None,
	}


def verify_works_master_strategy_seed() -> dict[str, Any]:
	"""Deterministic checks that §8 strategy codes exist and are linked (post-seed / post-purge)."""
	checks: list[dict[str, Any]] = []
	pe_names = allowed_procuring_entity_names()
	if not resolve_procuring_entity_moh():
		checks.append(
			{
				"id": "WORKS-PE-001",
				"ok": False,
				"message": "Procuring Entity PE-MOH or MOH missing.",
			}
		)
		return {
			"ok": False,
			"checks": checks,
			"desk_list_title": PLAN_TITLE,
			"strategy_plan_code": STRATEGY_PLAN_CODE,
			"programme_code": PROGRAM_CODE,
			"objective_code": OBJECTIVE_CODE,
			"target_code": TARGET_CODE,
		}

	protected = protected_works_strategic_plan_names()
	if len(protected) != 1:
		checks.append(
			{
				"id": "WORKS-STRAT-001",
				"ok": False,
				"message": (
					f"Expected exactly one canonical WORKS Strategic Plan (title {PLAN_TITLE!r}, "
					f"{START_YEAR}–{END_YEAR} on PE-MOH/MOH); found {len(protected)}. Run seed after purge."
				),
				"protected": sorted(protected),
			}
		)
		pe_resolved = resolve_procuring_entity_moh()
		n_for_pe = (
			len(frappe.get_all("Strategic Plan", filters={"procuring_entity": pe_resolved}, pluck="name"))
			if pe_resolved
			else 0
		)
		checks.append(
			{
				"id": "WORKS-STRAT-SEED-PE-COUNT",
				"ok": bool(pe_resolved) and n_for_pe == 1,
				"message": (
					f"Exactly one Strategic Plan for seed procuring entity {pe_resolved!r} (got {n_for_pe})."
					if pe_resolved
					else "No resolved procuring entity."
				),
				"procuring_entity": pe_resolved,
				"plans_for_procuring_entity": n_for_pe,
			}
		)
		all_ok = all(c.get("ok") for c in checks)
		return {
			"ok": all_ok,
			"checks": checks,
			"desk_list_title": PLAN_TITLE,
			"strategy_plan_code": STRATEGY_PLAN_CODE,
			"programme_code": PROGRAM_CODE,
			"objective_code": OBJECTIVE_CODE,
			"target_code": TARGET_CODE,
		}

	pn = list(protected)[0]
	row = frappe.db.get_value(
		"Strategic Plan",
		pn,
		["strategic_plan_name", "procuring_entity", "start_year", "end_year", "status"],
		as_dict=True,
	)
	ok_pe = bool(row and row.procuring_entity in pe_names)
	ok_title = bool(row and (row.strategic_plan_name or "").strip() == PLAN_TITLE)
	ok_years = bool(
		row and cint(row.start_year) == START_YEAR and cint(row.end_year) == END_YEAR
	)
	ok_status = bool(row and (row.status or "").strip() == "Active")
	ok_row = ok_pe and ok_title and ok_years and ok_status
	checks.append(
		{
			"id": "WORKS-STRAT-001",
			"ok": ok_row,
			"message": "Canonical Strategic Plan present with §8 title, allowed PE, years, Active status."
			if ok_row
			else f"Strategic Plan row mismatch: {row!r}",
			"name": pn,
		}
	)

	prog = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": pn, "program_code": PROGRAM_CODE},
		["name", "program_title"],
		as_dict=True,
	)
	checks.append(
		{
			"id": "WORKS-PROG-001",
			"ok": bool(prog),
			"message": "Strategy Program PROG-MOH-INFRA exists on canonical plan." if prog else "Missing programme.",
			"name": prog.name if prog else None,
		}
	)

	obj = None
	if prog:
		obj = frappe.db.get_value(
			"Strategy Objective",
			{"program": prog.name, "objective_code": OBJECTIVE_CODE},
			["name", "strategic_plan", "program"],
			as_dict=True,
		)
	ok_obj = bool(obj and obj.strategic_plan == pn and obj.program == prog.name) if prog and obj else False
	checks.append(
		{
			"id": "WORKS-OBJ-001",
			"ok": ok_obj,
			"message": "Strategy Objective OBJ-MOH-HOSP-RENOV linked to plan and programme." if ok_obj else "Objective missing or mis-linked.",
			"name": obj.name if obj else None,
		}
	)

	tgt = None
	if prog and obj:
		tgt = frappe.db.get_value(
			"Strategy Target",
			{"objective": obj.name, "target_code": TARGET_CODE},
			["name", "strategic_plan", "program", "objective"],
			as_dict=True,
		)
	ok_tgt = (
		bool(
			tgt
			and tgt.strategic_plan == pn
			and tgt.program == prog.name
			and tgt.objective == obj.name
		)
		if prog and obj and tgt
		else False
	)
	checks.append(
		{
			"id": "WORKS-TGT-001",
			"ok": ok_tgt,
			"message": "Strategy Target TGT-MOH-HOSP-RENOV-2026 linked under objective." if ok_tgt else "Target missing or mis-linked.",
			"name": tgt.name if tgt else None,
		}
	)

	pe_resolved = resolve_procuring_entity_moh()
	n_for_pe = (
		len(frappe.get_all("Strategic Plan", filters={"procuring_entity": pe_resolved}, pluck="name"))
		if pe_resolved
		else 0
	)
	checks.append(
		{
			"id": "WORKS-STRAT-SEED-PE-COUNT",
			"ok": bool(pe_resolved) and n_for_pe == 1,
			"message": (
				f"Exactly one Strategic Plan for seed procuring entity {pe_resolved!r} (got {n_for_pe})."
				if pe_resolved
				else "No resolved procuring entity."
			),
			"procuring_entity": pe_resolved,
			"plans_for_procuring_entity": n_for_pe,
		}
	)

	all_ok = all(c.get("ok") for c in checks)
	out: dict[str, Any] = {
		"ok": all_ok,
		"checks": checks,
		"desk_list_title": PLAN_TITLE,
		"strategy_plan_code": STRATEGY_PLAN_CODE,
		"programme_code": PROGRAM_CODE,
		"objective_code": OBJECTIVE_CODE,
		"target_code": TARGET_CODE,
	}
	return out
