# Copyright (c) 2026, KenTender and contributors
"""Downstream Strategy contracts — STR-CHG-001 v1.7 §7/§8.

This module is the integration boundary: downstream apps call the functions
here, never a Strategy DocType controller or table directly (STR-BR-020).
The four §8 read contracts are `resolve_strategy_context`,
`list_strategy_objectives`, `get_strategy_lineage` and
`create_strategy_snapshot`; `record_verified_result` stays a deferred stub.

The Performance-Target-based helpers below them
(`validate_strategy_reference`, `build_strategy_reference`,
`list_active_targets`, `apply_budget_primary_strategy_reference` and
friends) are kentender_budget's XMOD-STR-001 linkage: a Budget Line
references a Performance Target for funding-target lineage, a distinct
relationship from the Plan Item → Strategic Objective selection above. They
moved here from `strategy_contracts.py` (deleted in the v1.7 correction,
tracker STR-501/502): that file was ~1,450 lines of pre-rebuild code naming
deleted doctypes, of which exactly these four functions were still imported.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate

from kentender_strategy.services.strategy_domain_guards import PLAN_ROLE_PRIMARY, PLAN_ROLE_SUPPORTING


def _covers_date(start, end, as_of) -> bool:
	if not start or not end:
		return False
	return getdate(start) <= as_of <= getdate(end)


def _overlaps_range(start, end, range_start, range_end) -> bool:
	if not start or not end:
		return False
	return getdate(start) <= range_end and range_start <= getdate(end)


def _hierarchy_summary(plan_version_id: str) -> dict[str, int]:
	counts = {"pillars": 0, "programmes": 0, "sub_programmes": 0, "strategic_objectives": 0}
	key = {
		"Pillar": "pillars",
		"Programme": "programmes",
		"Sub-programme": "sub_programmes",
		"Strategic Objective": "strategic_objectives",
	}
	for row in frappe.get_all("Strategy Node", filters={"plan_version_id": plan_version_id}, fields=["node_type"]):
		counts[key[row.node_type]] += 1
	counts["performance_indicators"] = frappe.db.count("Performance Indicator", {"plan_version_id": plan_version_id})
	return counts


def _context_entry(plan, version) -> dict:
	return {
		"id": plan.name,
		"code": plan.plan_id,
		"name": plan.title,
		"plan_role": plan.plan_role,
		"period_start": str(plan.period_start) if plan.period_start else None,
		"period_end": str(plan.period_end) if plan.period_end else None,
		"version_id": version.name,
		"version_reference": version.plan_version_id,
		"version_number": version.version_number,
		"status": version.status,
		"start_date": str(version.effective_from) if version.effective_from else None,
		"end_date": str(version.effective_to) if version.effective_to else None,
		"hierarchy_summary": _hierarchy_summary(version.name),
	}


def resolve_strategy_context(
	*,
	as_of_date: str | None = None,
	fiscal_year: str | None = None,
	include_supporting: bool = False,
) -> dict:
	"""STR-CHG-001 v1.7 §7 — resolve_strategy_context.

	Input is exactly one of `as_of_date` or `fiscal_year`, plus the optional
	`include_supporting` flag. There is no Procuring Entity or
	organisation-unit input, no scope validation step and no preference
	rule (STR-BR-017): zero applicable Active Primary versions raise
	`STRATEGY_CONTEXT_NOT_FOUND`, more than one raise
	`STRATEGY_CONTEXT_AMBIGUOUS`.

	A date is covered when both the plan period and the version's effective
	period contain it; a Fiscal Year is covered when both overlap it. The
	result carries only IDs, titles, role, period, version, status and the
	hierarchy summary a consumer needs — no authoring or audit internals.
	"""
	if bool(as_of_date) == bool(fiscal_year):
		frappe.throw(
			_("Provide exactly one of as_of_date or fiscal_year"),
			frappe.ValidationError,
			title="STRATEGY_CONTEXT_NOT_FOUND",
		)

	if fiscal_year:
		fy = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
		if not fy:
			frappe.throw(
				_("Fiscal Year {0} is not configured").format(fiscal_year),
				frappe.ValidationError,
				title="STRATEGY_CONFIG_MISSING",
			)
		range_start, range_end = getdate(fy.year_start_date), getdate(fy.year_end_date)
		label = fiscal_year
	else:
		range_start = range_end = getdate(as_of_date)
		label = str(range_start)

	def _applicable(plan_role: str) -> list[dict]:
		plans = frappe.get_all(
			"Strategic Plan",
			filters={"plan_role": plan_role},
			fields=["name", "plan_id", "title", "plan_role", "period_start", "period_end"],
			order_by="title asc, name asc",
		)
		if not plans:
			return []
		versions = frappe.get_all(
			"Strategic Plan Version",
			filters={"plan_id": ["in", [p.name for p in plans]], "status": "Active"},
			fields=["name", "plan_version_id", "plan_id", "version_number", "status", "effective_from", "effective_to"],
		)
		by_plan = {v.plan_id: v for v in versions}
		out = []
		for plan in plans:
			version = by_plan.get(plan.name)
			if not version:
				continue
			if not (
				_overlaps_range(plan.period_start, plan.period_end, range_start, range_end)
				and _overlaps_range(version.effective_from, version.effective_to, range_start, range_end)
			):
				continue
			out.append(_context_entry(plan, version))
		return out

	primaries = _applicable(PLAN_ROLE_PRIMARY)
	if not primaries:
		frappe.throw(
			_("No Active Primary strategic plan applies to {0}").format(label),
			frappe.DoesNotExistError,
			title="STRATEGY_CONTEXT_NOT_FOUND",
		)
	if len(primaries) > 1:
		frappe.throw(
			_("More than one Active Primary strategic plan applies to {0}").format(label),
			frappe.ValidationError,
			title="STRATEGY_CONTEXT_AMBIGUOUS",
		)
	primary = primaries[0]

	supporting: list[dict] = []
	if include_supporting:
		supporting = [
			entry
			for entry in _applicable(PLAN_ROLE_SUPPORTING)
			if frappe.db.get_value("Strategic Plan", entry["id"], "parent_primary_plan_id") == primary["id"]
		]

	return {
		"as_of_date": str(range_start) if as_of_date else None,
		"fiscal_year": fiscal_year or None,
		"primary_plan": primary,
		"supporting_plans": supporting,
	}


def list_strategy_objectives(
	plan_version_id: str,
	*,
	parent_node_id: str | None = None,
	search: str | None = None,
	limit_start: int = 0,
	limit_page_length: int = 20,
) -> dict:
	"""STR-CHG-001 §8 — list_strategy_objectives.

	Active Strategic Objectives from one resolved Active plan version, each
	with its ordered Pillar -> Programme -> optional Sub-programme ancestor
	path so a planner can distinguish similarly-named objectives (§12.6).
	Never returns Draft-version content — the caller supplies an already
	Active plan_version_id (from resolve_strategy_context), and this
	function itself re-confirms that before returning anything (STR-BR-018).
	"""
	if frappe.db.get_value("Strategic Plan Version", plan_version_id, "status") != "Active":
		return {"rows": [], "count": 0}

	filters = {"plan_version_id": plan_version_id, "node_type": "Strategic Objective"}
	if parent_node_id:
		filters["parent_node_id"] = parent_node_id
	if search:
		filters["title"] = ["like", f"%{search}%"]

	total = frappe.db.count("Strategy Node", filters)
	rows = frappe.get_all(
		"Strategy Node",
		filters=filters,
		fields=["name", "strategy_node_id", "title", "parent_node_id"],
		order_by="display_order asc",
		limit_start=limit_start,
		limit_page_length=limit_page_length,
	)
	out = []
	for row in rows:
		path = _node_ancestor_path(row.name)
		out.append(
			{
				"id": row.name,
				"reference": row.strategy_node_id,
				"title": row.title,
				"path": [{"type": n["node_type"], "id": n["name"], "title": n["title"]} for n in path],
			}
		)
	return {"rows": out, "count": total}


def get_strategy_lineage(node_id: str) -> dict:
	"""STR-CHG-001 §8 — get_strategy_lineage.

	Ordered path with stable IDs, types and titles from plan to the
	requested Strategic Objective, Performance Indicator or Performance
	Target — auto-detecting which of the three the id belongs to rather
	than requiring the caller to state it.
	"""
	if frappe.db.exists("Strategy Node", node_id):
		path = _node_ancestor_path(node_id)
	elif frappe.db.exists("Performance Indicator", node_id):
		indicator = frappe.get_doc("Performance Indicator", node_id)
		path = _node_ancestor_path(indicator.measures_node_id)
		path.append(
			{
				"name": indicator.name,
				"node_type": "Performance Indicator",
				"title": indicator.indicator_name,
				"parent_node_id": indicator.measures_node_id,
			}
		)
	elif frappe.db.exists("Performance Target", node_id):
		target = frappe.get_doc("Performance Target", node_id)
		indicator = frappe.get_doc("Performance Indicator", target.indicator_id)
		path = _node_ancestor_path(indicator.measures_node_id)
		path.append(
			{
				"name": indicator.name,
				"node_type": "Performance Indicator",
				"title": indicator.indicator_name,
				"parent_node_id": indicator.measures_node_id,
			}
		)
		path.append(
			{
				"name": target.name,
				"node_type": "Performance Target",
				"title": f"{target.comparison} {target.target_value}",
				"parent_node_id": indicator.name,
			}
		)
	else:
		frappe.throw(_("Unknown Strategy reference"), frappe.DoesNotExistError)

	return {
		"node_id": node_id,
		"path": [{"id": n["name"], "type": n["node_type"], "title": n["title"]} for n in path],
	}


def create_strategy_snapshot(*, plan_version_id: str, objective_id: str, correlation_key: str) -> dict:
	"""STR-CHG-001 §8/§12.6 — create_strategy_snapshot.

	Freezes one selected Strategic Objective's plan/version identity,
	period and ordered Pillar->Programme->[Sub-programme]->Objective path
	for a downstream approval boundary (a Procurement Plan Version
	approval). Idempotent per correlation_key — see
	strategy_idempotency.run_idempotent, wired at the API layer, not here;
	this function is pure/re-computable given the same inputs since source
	data is immutable once Active.
	"""
	if not correlation_key:
		frappe.throw(_("correlation_key is required"), frappe.ValidationError, title="STRATEGY_OBJECTIVE_NOT_ELIGIBLE")

	version = frappe.db.get_value(
		"Strategic Plan Version", plan_version_id, ["plan_id", "status", "effective_from", "effective_to"], as_dict=True
	)
	if not version:
		frappe.throw(_("Unknown plan version"), frappe.DoesNotExistError, title="STRATEGY_OBJECTIVE_NOT_ELIGIBLE")
	objective = frappe.db.get_value(
		"Strategy Node", objective_id, ["node_type", "plan_version_id", "title"], as_dict=True
	)
	if (
		not objective
		or objective.node_type != "Strategic Objective"
		or objective.plan_version_id != plan_version_id
		or version.status != "Active"
	):
		frappe.throw(
			_("The selected Objective is not eligible for a new snapshot"),
			frappe.ValidationError,
			title="STRATEGY_OBJECTIVE_NOT_ELIGIBLE",
		)

	plan = frappe.db.get_value("Strategic Plan", version.plan_id, ["plan_id", "title"], as_dict=True)
	path = _node_ancestor_path(objective_id)

	snapshot = {
		"plan_id": version.plan_id,
		"plan_code": plan.plan_id,
		"plan_title": plan.title,
		"plan_version_id": plan_version_id,
		"effective_from": str(version.effective_from) if version.effective_from else None,
		"effective_to": str(version.effective_to) if version.effective_to else None,
		"path": [{"id": n["name"], "type": n["node_type"], "title": n["title"]} for n in path],
		"objective_id": objective_id,
		"objective_title": objective.title,
		"correlation_key": correlation_key,
	}

	from kentender_strategy.services.strategy_audit import record_event

	record_event(
		entity_type="Strategy Node",
		entity_name=objective_id,
		event_type="Strategy Snapshot Created",
		plan_version=plan_version_id,
		reason=correlation_key,
		correlation_id=correlation_key,
		summary=f"Snapshot created for downstream boundary {correlation_key}",
	)
	return snapshot


def record_verified_result(*_args, **_kwargs):
	"""STR-CHG-001 §8 — record_verified_result.

	Explicitly deferred until Contract Management scope activates it; this
	contract makes no direct Strategy master-data mutation. Stub only — do
	not wire a caller to this until that scope exists.
	"""
	raise NotImplementedError(
		"record_verified_result is deferred to Contract Management scope (STR-CHG-001 §8)"
	)


# --------------------------------------------------------------------------
# Lineage helpers and the Performance-Target reference contract
# (kentender_budget's XMOD-STR-001 Budget Line linkage)
# --------------------------------------------------------------------------

# Strategy Node node_type values -> the compact, space-free path-entry "type"
# tokens build_strategy_reference()/list_active_targets() callers expect.
_NODE_PATH_TYPE = {
	"Pillar": "Pillar",
	"Programme": "Programme",
	"Sub-programme": "SubProgramme",
	"Strategic Objective": "StrategicObjective",
}


def _node_ancestor_path(node_id: str) -> list[dict]:
	"""Root-first Strategy Node ancestor chain, self included."""
	chain = []
	current = frappe.db.get_value(
		"Strategy Node", node_id, ["name", "node_type", "title", "parent_node_id"], as_dict=True
	)
	while current:
		chain.append(current)
		current = (
			frappe.db.get_value(
				"Strategy Node",
				current.parent_node_id,
				["name", "node_type", "title", "parent_node_id"],
				as_dict=True,
			)
			if current.parent_node_id
			else None
		)
	chain.reverse()
	return chain


def validate_strategy_reference(reference: dict | None = None) -> dict:
	"""XMOD-STR-001 — validates a Performance Target reference for a
	downstream consumer (kentender_budget's Budget Line). Eligibility is the
	owning Strategic Plan Version's status; the reference's own generated id
	is its code."""
	reference = reference or {}
	plan_version_id = reference.get("plan_version_id")
	node_id = reference.get("node_id")
	node_type = reference.get("node_type") or "PerformanceTarget"
	if node_type != "PerformanceTarget":
		return {"valid": False, "reason": f"Unsupported node_type {node_type}"}

	target = frappe.db.get_value("Performance Target", node_id, "indicator_id")
	if not target:
		return {"valid": False, "reason": "Unknown target"}
	indicator_plan_version_id = frappe.db.get_value("Performance Indicator", target, "plan_version_id")
	if not indicator_plan_version_id:
		return {"valid": False, "reason": "Unknown target"}
	if plan_version_id and indicator_plan_version_id != plan_version_id:
		return {"valid": False, "reason": "Target/plan version mismatch"}

	version_status = frappe.db.get_value("Strategic Plan Version", indicator_plan_version_id, "status")
	selectable = version_status == "Active"
	dto = build_strategy_reference(indicator_plan_version_id, node_id)
	return {"valid": True, "selectable_for_new": selectable, "historical_ok": True, "reference": dto}


def build_strategy_reference(plan_version_id: str, target_id: str) -> dict:
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	target = frappe.get_doc("Performance Target", target_id)
	indicator = frappe.get_doc("Performance Indicator", target.indicator_id)

	path = [
		{"type": _NODE_PATH_TYPE[n.node_type], "id": n.name, "code": n.name, "name": n.title}
		for n in _node_ancestor_path(indicator.measures_node_id)
	]
	path.append(
		{
			"type": "PerformanceIndicator",
			"id": indicator.name,
			"code": indicator.name,
			"name": indicator.indicator_name,
		}
	)
	target_label = f"{target.comparison} {target.target_value}"
	path.append({"type": "PerformanceTarget", "id": target.name, "code": target.name, "name": target_label})

	snapshot = " / ".join(
		p["name"] for p in path if p["type"] in ("Programme", "SubProgramme", "PerformanceTarget")
	)
	return {
		"plan_version_id": version.name,
		"plan_code": frappe.db.get_value("Strategic Plan", version.plan_id, "plan_id"),
		"plan_version": version.version_number,
		"node_type": "PerformanceTarget",
		"node_id": target.name,
		"node_code": target.name,
		"node_name": target_label,
		"path": path,
		"snapshot_label": snapshot,
	}


def list_active_targets(plan_code: str | None = None) -> list[dict]:
	"""XMOD-STR-001 read for a Budget Line "primary target" picker: every
	Performance Target on an Active plan version, as reference DTOs. One
	site is one entity, so no entity parameter exists (STR-AC-033)."""
	plan_filters: dict[str, Any] = {}
	if plan_code:
		plan_filters["plan_id"] = plan_code
	plans = frappe.get_all("Strategic Plan", filters=plan_filters, pluck="name")
	if not plans:
		return []
	versions = frappe.get_all(
		"Strategic Plan Version",
		filters={"plan_id": ["in", plans], "status": "Active"},
		pluck="name",
	)
	if not versions:
		return []
	indicators = frappe.get_all(
		"Performance Indicator", filters={"plan_version_id": ["in", versions]}, fields=["name", "plan_version_id"]
	)
	if not indicators:
		return []
	version_by_indicator = {i.name: i.plan_version_id for i in indicators}
	targets = frappe.get_all(
		"Performance Target",
		filters={"indicator_id": ["in", list(version_by_indicator)]},
		fields=["name", "indicator_id"],
	)
	return [build_strategy_reference(version_by_indicator[t.indicator_id], t.name) for t in targets]


def resolve_performance_target_id(
	*, target_id: str | None = None, target_code: str | None = None
) -> str | None:
	"""Resolve a Performance Target name from its generated id.

	Performance Target has no business code distinct from its generated id
	— target_code is accepted only for callers that historically passed
	either interchangeably, and is treated as a literal target id.
	"""
	tid = (target_id or "").strip() or (target_code or "").strip()
	if tid and frappe.db.exists("Performance Target", tid):
		return tid
	return None


def target_snapshot_fields(target_id: str) -> dict | None:
	"""Non-validating field lookup for a Performance Target by id — the
	downstream-safe alternative to querying the DocType directly. Returns
	None rather than throwing when the target doesn't exist; callers that
	need Active-status enforcement should use validated_supporting_target_row
	or apply_strategy_reference_to_doc instead."""
	tid = (target_id or "").strip()
	if not tid:
		return None
	target = frappe.db.get_value(
		"Performance Target", tid, ["name", "indicator_id", "comparison", "target_value"], as_dict=True
	)
	if not target:
		return None
	plan_version_id = frappe.db.get_value("Performance Indicator", target.indicator_id, "plan_version_id")
	return {
		"name": target.name,
		"title": f"{target.comparison} {target.target_value}",
		"plan_version": plan_version_id,
		"target_code": target.name,
	}


def _validated_strategy_reference(target_id: str, *, require_active: bool = True) -> dict:
	"""Validate a Performance Target id and return the Strategy Reference dict."""
	tgt = frappe.db.get_value(
		"Performance Target", target_id, ["name", "indicator_id"], as_dict=True
	)
	if not tgt:
		frappe.throw(_("Unknown Performance Target"))
	plan_version_id = frappe.db.get_value(
		"Performance Indicator", tgt.indicator_id, "plan_version_id"
	)
	result = validate_strategy_reference(
		{
			"plan_version_id": plan_version_id,
			"node_id": tgt.name,
			"node_type": "PerformanceTarget",
		}
	)
	if not result.get("valid"):
		frappe.throw(_(result.get("reason") or "Invalid strategy reference"))
	if require_active and not result.get("selectable_for_new"):
		frappe.throw(_("Only Active targets on Active plan versions may be selected for new records"))
	return result["reference"]


def apply_strategy_reference_to_doc(doc, target_id: str | None, *, require_active: bool = True) -> dict | None:
	"""Set strategy_plan_version + strategy_target (+ snapshot) on a consumer doc."""
	if not target_id:
		if hasattr(doc, "strategy_target"):
			doc.strategy_target = None
		if hasattr(doc, "strategy_plan_version"):
			doc.strategy_plan_version = None
		if hasattr(doc, "strategy_snapshot_label"):
			doc.strategy_snapshot_label = None
		return None

	ref = _validated_strategy_reference(target_id, require_active=require_active)
	if hasattr(doc, "strategy_plan_version"):
		doc.strategy_plan_version = ref["plan_version_id"]
	if hasattr(doc, "strategy_target"):
		doc.strategy_target = ref["node_id"]
	if hasattr(doc, "strategy_snapshot_label"):
		doc.strategy_snapshot_label = ref.get("snapshot_label")
	return ref


def apply_budget_primary_strategy_reference(
	doc, target_id: str | None, *, require_active: bool = True
) -> dict | None:
	"""XMOD-STR-001 — set Budget Line primary_* fields from validated Strategy Reference."""
	if not target_id:
		if hasattr(doc, "primary_target_id"):
			doc.primary_target_id = None
		if hasattr(doc, "primary_target_code"):
			doc.primary_target_code = None
		if hasattr(doc, "primary_target_name"):
			doc.primary_target_name = None
		if hasattr(doc, "primary_plan_version_id"):
			doc.primary_plan_version_id = None
		if hasattr(doc, "primary_snapshot_label"):
			doc.primary_snapshot_label = None
		if hasattr(doc, "primary_strategy_linked"):
			doc.primary_strategy_linked = 0
		return None

	ref = _validated_strategy_reference(target_id, require_active=require_active)
	doc.primary_target_id = ref["node_id"]
	doc.primary_target_code = ref.get("node_code") or ""
	doc.primary_target_name = ref.get("node_name") or ""
	doc.primary_plan_version_id = ref["plan_version_id"]
	doc.primary_snapshot_label = ref.get("snapshot_label") or ""
	doc.primary_strategy_linked = 1
	return ref


def validated_supporting_target_row(
	*,
	target_id: str | None = None,
	target_code: str | None = None,
	reason: str | None = None,
	require_active: bool = True,
) -> dict:
	"""Resolve + validate a supporting Performance Target into a child-row dict."""
	resolved = resolve_performance_target_id(target_id=target_id, target_code=target_code)
	if not resolved:
		frappe.throw(_("Unknown supporting Performance Target"))
	ref = _validated_strategy_reference(resolved, require_active=require_active)
	return {
		"target_id": ref["node_id"],
		"target_code": ref.get("node_code") or "",
		"target_name": ref.get("node_name") or "",
		"plan_version_id": ref["plan_version_id"],
		"snapshot_label": ref.get("snapshot_label") or "",
		"reason": (reason or "").strip(),
	}


def active_target_options(plan_code: str | None = None) -> list[dict]:
	return list_active_targets(plan_code=plan_code)
