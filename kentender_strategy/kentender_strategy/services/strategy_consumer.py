# Copyright (c) 2026, KenTender and contributors
"""Downstream Strategy Reference helpers for Budget / Demand / Planning.

This module is the STR-CHG-001 §12 integration-contract boundary: downstream
apps call the functions here, never a Strategy DocType controller or table
directly. The 5 canonically-named contracts (resolve_strategy_context,
list_strategy_commitments, get_strategy_lineage, create_strategy_snapshot,
record_verified_result) sit alongside the older, budget-shaped helpers below
that already route through them — both are legitimate parts of this same
boundary, not competing layers.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from kentender_strategy.services.strategy_contracts import (
	build_strategy_reference,
	list_active_targets,
	list_strategy_value_commitments,
	validate_strategy_reference,
)
from kentender_strategy.services.strategy_domain_guards import (
	PLAN_TYPE_ENTITY,
	SUBORDINATE_PLAN_TYPES,
)


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
	"""
	if not procuring_entity:
		frappe.throw(_("Procuring entity is required"), frappe.ValidationError)
	as_of = getdate(effective_date) if effective_date else getdate()

	primaries = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": procuring_entity,
			"plan_type": PLAN_TYPE_ENTITY,
			"status": "Active",
		},
		fields=["name", "plan_code", "title", "start_date", "end_date"],
	)
	covering = [p for p in primaries if _covers_date(p.start_date, p.end_date, as_of)]
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

	supporting_filters = {
		"procuring_entity": procuring_entity,
		"plan_type": ["in", list(SUBORDINATE_PLAN_TYPES)],
		"status": "Active",
	}
	if organisation_unit:
		supporting_filters["owner_org_unit"] = organisation_unit
	supporting_rows = frappe.get_all(
		"Strategic Plan",
		filters=supporting_filters,
		fields=["name", "plan_code", "title", "plan_type", "start_date", "end_date"],
	)
	supporting = [s for s in supporting_rows if _covers_date(s.start_date, s.end_date, as_of)]

	return {
		"procuring_entity": procuring_entity,
		"organisation_unit": organisation_unit,
		"effective_date": str(as_of),
		"primary_plan": {
			"id": primary.name,
			"code": primary.plan_code,
			"name": primary.title,
			"start_date": str(primary.start_date),
			"end_date": str(primary.end_date),
		},
		"supporting_plans": [
			{"id": s.name, "code": s.plan_code, "name": s.title, "plan_type": s.plan_type}
			for s in supporting
		],
	}


def list_strategy_commitments(
	procuring_entity: str | None = None,
	plan_version: str | None = None,
	node_id: str | None = None,
	target_id: str | None = None,
) -> list[dict]:
	"""STR-CHG-001 §12 — list_strategy_commitments.

	Input: resolved context (PE, or an explicit plan_version) plus optional
	node/target filters. Output: Approved (Locked), effective (Active plan)
	commitments only — server-side scope enforced, no Draft/incomplete rows.
	"""
	if not plan_version:
		if not procuring_entity:
			frappe.throw(
				_("Either procuring_entity or plan_version is required"), frappe.ValidationError
			)
		plan_version = resolve_strategy_context(procuring_entity)["primary_plan"]["id"]
	if frappe.db.get_value("Strategic Plan", plan_version, "status") != "Active":
		return []
	rows = [
		r
		for r in (list_strategy_value_commitments(plan_version=plan_version).get("rows") or [])
		if r.get("status") == "Locked"
	]
	wanted = {v for v in (node_id, target_id) if v}
	if wanted:
		rows = [
			r
			for r in rows
			if any(
				(ln.get("outcome") or {}).get("id") in wanted
				or (ln.get("target") or {}).get("id") in wanted
				for ln in r.get("links") or []
			)
		]
	return rows


def get_strategy_lineage(
	*,
	plan_version: str,
	node_id: str,
	node_type: str = "PerformanceTarget",
) -> dict:
	"""STR-CHG-001 §12 / §12.1 — get_strategy_lineage.

	Canonical titles, hierarchy path, version and effective period for a
	Strategy reference — no editable code. Scoped to Performance Target
	references (the only lineage entry point consumed by any downstream
	module today); extend when a genuine Objective/Outcome/Indicator-only
	consumer exists rather than speculatively.
	"""
	if node_type != "PerformanceTarget":
		frappe.throw(_("Unsupported node_type for lineage resolution: {0}").format(node_type))
	return build_strategy_reference(plan_version, node_id)


def create_strategy_snapshot(
	*,
	plan_version: str,
	node_id: str,
	correlation_key: str,
	node_type: str = "PerformanceTarget",
) -> dict:
	"""STR-CHG-001 §12 / STR-FR-022 — create_strategy_snapshot.

	Input: an approved downstream record boundary (correlation_key) plus
	selected references. Output: immutable lineage payload and source version.
	Idempotent by construction — Strategy source data is immutable once
	Approved/Active, so recomputing for the same correlation_key always
	yields the same payload. No separate persisted snapshot ledger doctype.
	Audited: this is the one contract among the five that represents a real
	downstream-resolution *action* (an approval boundary freezing a
	reference), not a routine read — logged accordingly, unlike
	resolve_strategy_context/list_strategy_commitments/get_strategy_lineage.
	"""
	if not correlation_key:
		frappe.throw(_("correlation_key is required"), frappe.ValidationError)
	result = validate_strategy_reference(
		{"plan_version_id": plan_version, "node_id": node_id, "node_type": node_type}
	)
	if not result.get("valid"):
		frappe.throw(_(result.get("reason") or "Invalid strategy reference"), frappe.ValidationError)
	snapshot = dict(result["reference"])
	snapshot["correlation_key"] = correlation_key
	snapshot["selectable_for_new"] = result.get("selectable_for_new")

	from kentender_strategy.services.strategy_audit import record_event

	record_event(
		entity_type=node_type,
		entity_name=node_id,
		event_type="Strategy Snapshot Created",
		plan_version=plan_version,
		reason=correlation_key,
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
	"""Resolve a Performance Target name from id or business code.

	When resolving by code and duplicates exist, prefer Active targets on Active plans
	(STR-AC-009 / selectable_for_new).
	"""
	tid = (target_id or "").strip()
	if tid and frappe.db.exists("Performance Target", tid):
		return tid
	code = (target_code or "").strip()
	if not code:
		return tid or None
	rows = frappe.get_all(
		"Performance Target",
		filters={"target_code": code, "status": "Active"},
		fields=["name", "plan_version"],
		order_by="modified desc",
	)
	for row in rows:
		plan_status = frappe.db.get_value("Strategic Plan", row.plan_version, "status")
		if plan_status == "Active":
			return row.name
	if rows:
		return rows[0].name
	return frappe.db.get_value("Performance Target", {"target_code": code}, "name")


def target_snapshot_fields(target_id: str) -> dict | None:
	"""Non-validating field lookup for a Performance Target by id — the
	downstream-safe alternative to querying the DocType directly. Returns
	None rather than throwing when the target doesn't exist; callers that
	need Active-status enforcement should use validated_supporting_target_row
	or apply_strategy_reference_to_doc instead."""
	tid = (target_id or "").strip()
	if not tid:
		return None
	return frappe.db.get_value(
		"Performance Target",
		tid,
		["name", "title", "plan_version", "target_code"],
		as_dict=True,
	)


def resolve_commitment_id(commitment_code: str) -> str | None:
	"""Resolve a Strategy Value Commitment name from its business code — the
	downstream-safe alternative to querying the DocType directly."""
	code = (commitment_code or "").strip()
	if not code:
		return None
	return frappe.db.get_value("Strategy Value Commitment", {"commitment_code": code}, "name")


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


def strategy_fields_from_doc(doc) -> dict:
	"""DTO slice for builder/artefact payloads."""
	empty = {
		"strategy_plan_version": None,
		"strategy_target": None,
		"performance_target": None,
		"performance_target_label": "",
		"performance_target_code": "",
		"strategy_reference": None,
		"strategic_plan": None,
		"program": None,
		"program_label": "",
		"program_code": "",
		"sub_program": None,
		"sub_program_label": "",
		"sub_program_code": "",
		"output_indicator": None,
		"output_indicator_label": "",
		"output_indicator_code": "",
	}
	target_id = getattr(doc, "strategy_target", None) or getattr(doc, "performance_target", None)
	plan_id = getattr(doc, "strategy_plan_version", None)
	if not target_id or not plan_id:
		return empty
	try:
		ref = build_strategy_reference(plan_id, target_id)
	except Exception:
		return empty
	path_by_type = {p["type"]: p for p in ref.get("path") or []}
	return {
		"strategy_plan_version": plan_id,
		"strategy_target": target_id,
		"performance_target": target_id,
		"performance_target_label": ref.get("node_name") or "",
		"performance_target_code": ref.get("node_code") or "",
		"strategy_reference": ref,
		"strategic_plan": plan_id,
		"program": (path_by_type.get("Programme") or {}).get("id"),
		"program_label": (path_by_type.get("Programme") or {}).get("name") or "",
		"program_code": (path_by_type.get("Programme") or {}).get("code") or "",
		"sub_program": (path_by_type.get("SubProgramme") or {}).get("id"),
		"sub_program_label": (path_by_type.get("SubProgramme") or {}).get("name") or "",
		"sub_program_code": (path_by_type.get("SubProgramme") or {}).get("code") or "",
		"output_indicator": (path_by_type.get("StrategicOutcome") or {}).get("id"),
		"output_indicator_label": (path_by_type.get("StrategicOutcome") or {}).get("name") or "",
		"output_indicator_code": (path_by_type.get("StrategicOutcome") or {}).get("code") or "",
	}


def active_target_options(procuring_entity: str | None = None, plan_code: str | None = None) -> list[dict]:
	return list_active_targets(procuring_entity=procuring_entity, plan_code=plan_code)
