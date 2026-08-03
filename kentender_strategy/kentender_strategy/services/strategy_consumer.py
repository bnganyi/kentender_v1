# Copyright (c) 2026, KenTender and contributors
"""Downstream Strategy Reference helpers for Budget / Demand / Planning."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_contracts import (
	build_strategy_reference,
	list_active_targets,
	validate_strategy_reference,
)


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

	ref = result["reference"]
	if hasattr(doc, "strategy_plan_version"):
		doc.strategy_plan_version = ref["plan_version_id"]
	if hasattr(doc, "strategy_target"):
		doc.strategy_target = ref["node_id"]
	if hasattr(doc, "strategy_snapshot_label"):
		doc.strategy_snapshot_label = ref.get("snapshot_label")
	return ref


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
