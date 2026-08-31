# Copyright (c) 2026, KenTender and contributors
"""Downstream Strategy Reference helpers for Budget / Demand / Planning.

This module is the STR-CHG-001 §10 integration-contract boundary: downstream
apps call the functions here, never a Strategy DocType controller or table
directly. The 5 canonically-named contracts are resolve_strategy_context,
list_strategy_objectives, get_strategy_lineage, create_strategy_snapshot and
record_verified_result (deferred stub). They sit alongside the older,
Target-based helpers below (apply_budget_primary_strategy_reference and
friends — kentender_budget's XMOD-STR-001 integration) — both are legitimate,
separate parts of this same boundary, not competing layers: Procurement Plan
Items select a Strategic Objective (§9), Budget Lines reference a
Performance Target for funding-target linkage, a distinct relationship v1.3
does not change.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from kentender_strategy.services.strategy_contracts import (
	_node_ancestor_path,
	build_strategy_reference,
	list_active_targets,
	validate_strategy_reference,
)
from kentender_strategy.services.strategy_domain_guards import PLAN_ROLE_PRIMARY, PLAN_ROLE_SUPPORTING


def _covers_date(start, end, as_of) -> bool:
	if not start or not end:
		return False
	return getdate(start) <= as_of <= getdate(end)


def resolve_strategy_context(
	procuring_entity: str,
	organisation_unit: str | None = None,
	effective_date: str | None = None,
) -> dict:
	"""STR-CHG-001 §12 — resolve_strategy_context.

	Input: PE, optional OU, effective date (defaults to today). Output: exactly
	one primary Active plan context, or a typed error when zero or multiple
	primary Active plans cover the PE at that date — never a silent pick.
	Supporting frameworks (Programme Strategy / Thematic Plan / Annual
	Implementation Plan) active for the same PE/date are returned explicitly,
	never folded into the primary context.

	`primary_plan.version_id` is the Active Strategic Plan Version's own id —
	the value `list_strategy_objectives`/`create_strategy_snapshot` require as
	their `plan_version_id`, per this module's own docstrings. It was computed
	internally but never surfaced on this return value; the first real
	downstream caller (PLN-CHG-001 v1.2 Phase 6, kentender_procurement's
	strategy_gateway) found the gap live rather than in this module's own
	tests, which only assert `resolve_strategy_context`'s error paths.
	"""
	if not procuring_entity:
		frappe.throw(_("Procuring entity is required"), frappe.ValidationError)
	as_of = getdate(effective_date) if effective_date else getdate()

	def _active_versions(plan_role: str) -> list[dict]:
		filters = {"procuring_entity_id": procuring_entity, "plan_role": plan_role}
		if organisation_unit and plan_role == PLAN_ROLE_SUPPORTING:
			filters["owner_org_unit_id"] = organisation_unit
		plans = frappe.get_all("Strategic Plan", filters=filters, fields=["name", "plan_id", "title"])
		if not plans:
			return []
		plan_names = [p.name for p in plans]
		versions = frappe.get_all(
			"Strategic Plan Version",
			filters={"plan_id": ["in", plan_names], "status": "Active"},
			fields=["name", "plan_id", "effective_from", "effective_to"],
		)
		plans_by_name = {p.name: p for p in plans}
		out = []
		for v in versions:
			if not _covers_date(v.effective_from, v.effective_to, as_of):
				continue
			plan = plans_by_name.get(v.plan_id)
			if not plan:
				continue
			out.append(
				{
					"id": plan.name,
					"code": plan.plan_id,
					"name": plan.title,
					"version_id": v.name,
					"effective_from": v.effective_from,
					"effective_to": v.effective_to,
				}
			)
		return out

	covering = _active_versions(PLAN_ROLE_PRIMARY)
	if not covering:
		frappe.throw(
			_("No primary Active strategic plan covers {0} for this procuring entity").format(as_of),
			frappe.DoesNotExistError,
		)
	if len(covering) > 1:
		frappe.throw(
			_(
				"Multiple primary Active strategic plans cover {0} for this procuring "
				"entity — ambiguous lineage"
			).format(as_of),
			frappe.ValidationError,
		)
	primary = covering[0]
	supporting = _active_versions(PLAN_ROLE_SUPPORTING)

	return {
		"procuring_entity": procuring_entity,
		"organisation_unit": organisation_unit,
		"effective_date": str(as_of),
		"primary_plan": {
			"id": primary["id"],
			"version_id": primary["version_id"],
			"code": primary["code"],
			"name": primary["name"],
			"start_date": str(primary["effective_from"]),
			"end_date": str(primary["effective_to"]),
		},
		"supporting_plans": [
			{"id": s["id"], "code": s["code"], "name": s["name"], "plan_type": PLAN_ROLE_SUPPORTING}
			for s in supporting
		],
	}


def list_strategy_objectives(
	plan_version_id: str,
	*,
	parent_node_id: str | None = None,
	search: str | None = None,
	limit_start: int = 0,
	limit_page_length: int = 20,
) -> dict:
	"""STR-CHG-001 §9/§10 — list_strategy_objectives.

	Active Strategic Objectives from one resolved Active plan version, each
	with its ordered Pillar -> Programme -> optional Sub-programme ancestor
	path so a planner can distinguish similarly-named objectives (§13.6).
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
		fields=["name", "title", "parent_node_id"],
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
				"title": row.title,
				"path": [{"type": n["node_type"], "id": n["name"], "title": n["title"]} for n in path],
			}
		)
	return {"rows": out, "count": total}


def get_strategy_lineage(node_id: str) -> dict:
	"""STR-CHG-001 §10 — get_strategy_lineage.

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
	"""STR-CHG-001 §9/§10/§13.6 — create_strategy_snapshot.

	Freezes one selected Strategic Objective's plan/version identity,
	period and ordered Pillar->Programme->[Sub-programme]->Objective path
	for a downstream approval boundary (a Procurement Plan Version
	approval). Idempotent per correlation_key — see
	strategy_idempotency.run_idempotent, wired at the API layer, not here;
	this function is pure/re-computable given the same inputs since source
	data is immutable once Approved/Active.
	"""
	if not correlation_key:
		frappe.throw(_("correlation_key is required"), frappe.ValidationError, title="STRATEGY_SCOPE_REQUIRED")

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
	"""STR-CHG-001 §12 — record_verified_result.

	Explicitly deferred until Contract Management scope activates it; this
	contract makes no direct Strategy master-data mutation. Stub only — do
	not wire a caller to this until that scope exists.
	"""
	raise NotImplementedError(
		"record_verified_result is deferred to Contract Management scope (STR-CHG-001 §12)"
	)


def resolve_performance_target_id(
	*, target_id: str | None = None, target_code: str | None = None
) -> str | None:
	"""Resolve a Performance Target name from its generated id.

	Performance Target has no business code distinct from its generated id
	(Phase 1 schema) — target_code is accepted only for backward
	compatibility with callers that historically passed either
	interchangeably, and is treated as a literal target id.
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
		"Performance Target",
		target_id,
		["name", "plan_version", "status", "target_code", "title"],
		as_dict=True,
	)
	if not tgt:
		frappe.throw(_("Unknown Performance Target"))
	result = validate_strategy_reference(
		{
			"plan_version_id": tgt.plan_version,
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


def active_target_options(procuring_entity: str | None = None, plan_code: str | None = None) -> list[dict]:
	return list_active_targets(procuring_entity=procuring_entity, plan_code=plan_code)
