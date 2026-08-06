# Copyright (c) 2026, KenTender and contributors
"""Write companions for Strategy hierarchy, PVO, commitments, measurements."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_domain_guards import _assert_plan_editable
from kentender_strategy.services.strategy_permissions import (
	assert_entity_in_scope,
	can_create_successor_plan,
	can_edit_draft_plan,
	require_any_role,
	ROLE_MANAGER,
	ROLE_OFFICER,
)
from kentender_strategy.services.strategy_measurement import derive_measurement_result

_META_SKIP = frozenset(
	{
		"name",
		"owner",
		"creation",
		"modified",
		"modified_by",
		"docstatus",
		"idx",
		"doctype",
		"amended_from",
	}
)

NODE_DOCTYPE = {
	"Programme": ("Strategy Programme", "programme_code"),
	"SubProgramme": ("Strategy Sub Programme", "sub_programme_code"),
	"StrategicOutcome": ("Strategic Outcome", "outcome_code"),
	"PerformanceIndicator": ("Performance Indicator", "indicator_code"),
	"PerformanceTarget": ("Performance Target", "target_code"),
}


def _next_order_index(doctype: str, plan_version: str, parent_filters: dict | None = None) -> int:
	filters = {"plan_version": plan_version}
	if parent_filters:
		filters.update(parent_filters)
	meta = frappe.get_meta(doctype)
	if not meta.has_field("order_index"):
		return 0
	rows = frappe.get_all(doctype, filters=filters, fields=["order_index"], order_by="order_index desc", limit=1)
	if not rows or rows[0].order_index is None:
		return 0
	return int(rows[0].order_index) + 1


def _parent_filter_for_order(node_type: str, data: dict) -> dict | None:
	if node_type == "SubProgramme" and data.get("programme"):
		return {"programme": data["programme"]}
	if node_type == "StrategicOutcome":
		if data.get("sub_programme"):
			return {"sub_programme": data["sub_programme"]}
		if data.get("programme"):
			return {"programme": data["programme"]}
	if node_type == "PerformanceIndicator" and data.get("strategic_outcome"):
		return {"strategic_outcome": data["strategic_outcome"]}
	if node_type == "PerformanceTarget" and data.get("performance_indicator"):
		return {"performance_indicator": data["performance_indicator"]}
	return None


def _blank(value: Any) -> bool:
	if value is None:
		return True
	if isinstance(value, str) and not value.strip():
		return True
	return False


def _validate_structure_node_fields(node_type: str, data: dict) -> dict[str, str]:
	"""Field-level validation for structure drawers — return map for inline UI."""
	errors: dict[str, str] = {}
	if _blank(data.get("title")):
		errors["title"] = _("Title is required")

	if node_type in ("Programme", "SubProgramme", "StrategicOutcome"):
		if _blank(data.get("responsible_function")):
			errors["responsible_function"] = _("Responsible function is required")

	if node_type == "PerformanceIndicator":
		if _blank(data.get("definition")):
			errors["definition"] = _("Definition is required")
		if _blank(data.get("measurement_type")):
			errors["measurement_type"] = _("Measurement type is required")
		if _blank(data.get("measurement_frequency")):
			errors["measurement_frequency"] = _("Measurement frequency is required")
		if _blank(data.get("data_source")):
			errors["data_source"] = _("Data source is required")
		if _blank(data.get("responsible_function")):
			errors["responsible_function"] = _("Responsible function is required")

	if node_type == "PerformanceTarget":
		if _blank(data.get("comparison_direction")):
			errors["comparison_direction"] = _("Comparison direction is required")
		if data.get("target_numeric") is None and _blank(data.get("target_text")):
			errors["target_numeric"] = _("Target value is required")
		if _blank(data.get("period_start")):
			errors["period_start"] = _("Period start is required")
		if _blank(data.get("period_end")):
			errors["period_end"] = _("Period end is required")
		if _blank(data.get("benefit_owner")):
			errors["benefit_owner"] = _("Benefit owner is required")
		if _blank(data.get("measurement_verifier")):
			errors["measurement_verifier"] = _("Measurement verifier is required")

	return errors


def upsert_structure_node(payload: dict) -> dict:
	if not can_edit_draft_plan():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	node_type = payload.get("type") or payload.get("node_type")
	if node_type not in NODE_DOCTYPE:
		frappe.throw(_("Unknown structure node type: {0}").format(node_type))
	doctype, code_field = NODE_DOCTYPE[node_type]
	name = payload.get("id") or payload.get("name")
	data = dict(payload.get("fields") or {})
	# Flatten common keys
	for key in (
		"plan_version",
		"title",
		"description",
		"responsible_function",
		"order_index",
		"programme",
		"sub_programme",
		"strategic_outcome",
		"performance_indicator",
		"executive_owner",
		"definition",
		"measurement_type",
		"unit",
		"measurement_frequency",
		"data_source",
		"comparison_direction",
		"target_numeric",
		"target_text",
		"target_date",
		"baseline_status",
		"baseline_numeric",
		"baseline_text",
		"baseline_as_of",
		"baseline_source",
		"tolerance_value",
		"period_start",
		"period_end",
		"benefit_owner",
		"measurement_verifier",
		"status",
	):
		if key in payload and key not in data:
			data[key] = payload[key]
	# Client-supplied codes are ignored on create (system-assigned). On edit, codes are immutable.
	data.pop(code_field, None)
	data.pop("code", None)

	plan_version = data.get("plan_version")
	if not plan_version and name and frappe.db.exists(doctype, name):
		plan_version = frappe.db.get_value(doctype, name, "plan_version")
		data["plan_version"] = plan_version
	if not plan_version:
		frappe.throw(_("Plan version is required"))
	_assert_plan_editable(plan_version)
	pe = frappe.db.get_value("Strategic Plan", plan_version, "procuring_entity")
	if pe:
		assert_entity_in_scope(pe)

	# Inherit parent links / plan from parent when omitted
	if node_type == "SubProgramme" and data.get("programme"):
		data["plan_version"] = plan_version
	elif node_type == "StrategicOutcome":
		if data.get("sub_programme") and not data.get("programme"):
			data["programme"] = frappe.db.get_value(
				"Strategy Sub Programme", data["sub_programme"], "programme"
			)
	elif node_type == "PerformanceIndicator" and data.get("strategic_outcome"):
		data["plan_version"] = plan_version
	elif node_type == "PerformanceTarget" and data.get("performance_indicator"):
		data["plan_version"] = plan_version

	field_errors = _validate_structure_node_fields(node_type, data)
	if field_errors:
		return {"ok": False, "errors": field_errors}

	if data.get("order_index") is None and frappe.get_meta(doctype).has_field("order_index"):
		data["order_index"] = _next_order_index(
			doctype, plan_version, _parent_filter_for_order(node_type, data)
		)

	if name and frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		# Never overwrite an existing system reference from the payload.
		data.pop(code_field, None)
		doc.update(data)
		doc.save(ignore_permissions=True)
	else:
		data["doctype"] = doctype
		data[code_field] = None
		doc = frappe.get_doc(data)
		doc.insert(ignore_permissions=True)
	return {
		"ok": True,
		"id": doc.name,
		"type": node_type,
		"code": doc.get(code_field),
		"name": doc.title,
	}


def reorder_structure_nodes(plan_version: str, ordered: list[dict]) -> dict:
	"""ordered: [{id, type, order_index}, ...]"""
	if not can_edit_draft_plan():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	for item in ordered or []:
		node_type = item.get("type")
		doctype = NODE_DOCTYPE.get(node_type, (None, None))[0]
		if not doctype or not item.get("id"):
			continue
		if "order_index" in item and frappe.db.has_column(f"tab{doctype}", "order_index"):
			frappe.db.set_value(doctype, item["id"], "order_index", int(item["order_index"]))
	return {"ok": True, "count": len(ordered or [])}


def delete_structure_node(node_type: str, name: str) -> dict:
	if not can_edit_draft_plan():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doctype = NODE_DOCTYPE.get(node_type, (None, None))[0]
	if not doctype:
		frappe.throw(_("Unknown type"))
	if not frappe.db.exists(doctype, name):
		frappe.throw(_("Structure node not found"))
	plan_version = frappe.db.get_value(doctype, name, "plan_version")
	_assert_plan_editable(plan_version)
	pe = frappe.db.get_value("Strategic Plan", plan_version, "procuring_entity")
	if pe:
		assert_entity_in_scope(pe)
	# Reference guards
	if node_type == "PerformanceTarget":
		if frappe.db.exists("Performance Measurement", {"performance_target": name}):
			frappe.throw(_("Cannot delete target with measurements"))
	if node_type == "PerformanceIndicator":
		if frappe.db.exists("Performance Target", {"performance_indicator": name}):
			frappe.throw(_("Delete child targets first"))
	if node_type == "StrategicOutcome":
		if frappe.db.exists("Performance Indicator", {"strategic_outcome": name}):
			frappe.throw(_("Delete child indicators first"))
	if node_type == "SubProgramme":
		if frappe.db.exists("Strategic Outcome", {"sub_programme": name}):
			frappe.throw(_("Delete child outcomes first"))
	if node_type == "Programme":
		if frappe.db.exists("Strategy Sub Programme", {"programme": name}) or frappe.db.exists(
			"Strategic Outcome", {"programme": name}
		):
			frappe.throw(_("Delete child structure first"))
	frappe.delete_doc(doctype, name, ignore_permissions=True)
	return {"ok": True}


def upsert_pvo(payload: dict) -> dict:
	require_any_role(ROLE_OFFICER, ROLE_MANAGER, "System Manager")
	name = payload.get("id") or payload.get("name")
	triggers = payload.pop("triggers", None)
	fields = {k: v for k, v in payload.items() if k not in ("id", "name", "doctype")}
	if name and frappe.db.exists("Public Value Objective", name):
		doc = frappe.get_doc("Public Value Objective", name)
		if doc.status in ("Active", "Superseded", "Retired"):
			frappe.throw(_("Active Public Value Objectives are immutable; create a successor"))
		# Objective codes are immutable after create (catalogue or system).
		fields.pop("objective_code", None)
		doc.update(fields)
		if triggers is not None:
			doc.set("triggers", [])
			for tr in triggers:
				doc.append("triggers", tr)
		doc.save()
	else:
		fields["doctype"] = "Public Value Objective"
		# Empty → system MOH-OBJ-####; catalogue seeds may pass PVO-* explicitly.
		if not (fields.get("objective_code") or "").strip():
			fields["objective_code"] = None
		doc = frappe.get_doc(fields)
		for tr in triggers or []:
			doc.append("triggers", tr)
		doc.insert()
	return {
		"id": doc.name,
		"code": doc.objective_code,
		"name": doc.title,
		"status": doc.status,
	}


_CONSIDERATION_LEVEL_MAP = {
	"required": "Required consideration",
	"required consideration": "Required consideration",
	"recommended": "Recommended consideration",
	"recommended consideration": "Recommended consideration",
	"available": "Available",
}


def _normalize_consideration_level(raw) -> str | None:
	if raw is None or raw == "":
		return None
	key = str(raw).strip().lower()
	if key in _CONSIDERATION_LEVEL_MAP:
		return _CONSIDERATION_LEVEL_MAP[key]
	# Already a DocType option
	if str(raw) in (
		"Required consideration",
		"Recommended consideration",
		"Available",
	):
		return str(raw)
	frappe.throw(_("Invalid consideration level: {0}").format(raw))


def upsert_plan_value_commitment(payload: dict) -> dict:
	if not can_edit_draft_plan():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	name = payload.get("id") or payload.get("name")
	links = payload.get("links")
	if "links" in payload:
		payload = dict(payload)
		payload.pop("links", None)
	fields = {k: v for k, v in payload.items() if k not in ("id", "name", "doctype", "type")}
	if "consideration_level" in fields:
		fields["consideration_level"] = _normalize_consideration_level(fields["consideration_level"])

	plan_version = fields.get("plan_version")
	if not plan_version and name and frappe.db.exists("Plan Value Commitment", name):
		plan_version = frappe.db.get_value("Plan Value Commitment", name, "plan_version")
		fields["plan_version"] = plan_version
	if not plan_version:
		frappe.throw(_("Plan version is required"))
	_assert_plan_editable(plan_version)
	pe = frappe.db.get_value("Strategic Plan", plan_version, "procuring_entity")
	if pe:
		assert_entity_in_scope(pe)

	pvo_id = fields.get("public_value_objective_version")
	if not name and not pvo_id:
		frappe.throw(_("Public Value Objective is required"))
	if pvo_id:
		pvo_status = frappe.db.get_value("Public Value Objective", pvo_id, "status")
		if pvo_status != "Active" and not name:
			frappe.throw(_("Only Active Public Value Objectives may be selected"))

	# Require ≥1 link on create; on update when links explicitly provided
	if links is not None:
		if not links:
			frappe.throw(_("Link at least one Strategic Outcome or Performance Target"))
	elif not name:
		frappe.throw(_("Link at least one Strategic Outcome or Performance Target"))

	if name and frappe.db.exists("Plan Value Commitment", name):
		doc = frappe.get_doc("Plan Value Commitment", name)
		doc.update(fields)
		if links is not None:
			doc.set("links", [])
			for link in links:
				doc.append("links", link)
		doc.save(ignore_permissions=True)
	else:
		fields["doctype"] = "Plan Value Commitment"
		fields.setdefault("status", "Draft")
		fields["commitment_code"] = None
		doc = frappe.get_doc(fields)
		for link in links or []:
			doc.append("links", link)
		doc.insert(ignore_permissions=True)
	return {"id": doc.name, "code": doc.get("commitment_code"), "status": doc.status}


def set_commitment_links(commitment_name: str, links: list[dict]) -> dict:
	if not can_edit_draft_plan():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("Plan Value Commitment", commitment_name)
	_assert_plan_editable(doc.plan_version)
	pe = frappe.db.get_value("Strategic Plan", doc.plan_version, "procuring_entity")
	if pe:
		assert_entity_in_scope(pe)
	if not links:
		frappe.throw(_("Link at least one Strategic Outcome or Performance Target"))
	doc.set("links", [])
	for link in links or []:
		doc.append("links", link)
	doc.save(ignore_permissions=True)
	return {"id": doc.name, "links": len(doc.links)}


def save_measurement_draft(payload: dict) -> dict:
	from kentender_strategy.services.strategy_permissions import can_submit_measurement

	if not can_submit_measurement():
		frappe.throw(_("Only Strategy Officer may save measurements"), frappe.PermissionError)
	name = payload.get("id") or payload.get("name")
	fields = {k: v for k, v in payload.items() if k not in ("id", "name", "doctype")}
	fields.setdefault("workflow_status", "Draft")
	# Duplicate period guard
	existing = frappe.db.get_value(
		"Performance Measurement",
		{
			"performance_target": fields.get("performance_target"),
			"measurement_period_start": fields.get("measurement_period_start"),
			"measurement_period_end": fields.get("measurement_period_end"),
			"workflow_status": ["not in", ["Rejected"]],
			"name": ["!=", name or ""],
		},
		"name",
	)
	if existing and not fields.get("supersedes_measurement"):
		frappe.throw(_("A measurement already exists for this period"))
	if name and frappe.db.exists("Performance Measurement", name):
		doc = frappe.get_doc("Performance Measurement", name)
		if doc.workflow_status == "Verified":
			frappe.throw(_("Verified measurements are immutable"))
		doc.update(fields)
		derive_measurement_result(doc)
		doc.save(ignore_permissions=True)
	else:
		fields["doctype"] = "Performance Measurement"
		fields["measurement_code"] = None
		doc = frappe.get_doc(fields)
		derive_measurement_result(doc)
		doc.insert(ignore_permissions=True)
	return {
		"id": doc.name,
		"code": doc.get("measurement_code"),
		"workflow_status": doc.workflow_status,
		"result_status": doc.result_status,
		"variance": doc.variance,
	}


def upsert_corrective_action(payload: dict) -> dict:
	require_any_role(
		ROLE_OFFICER,
		ROLE_MANAGER,
		"System Manager",
	)
	name = payload.get("id") or payload.get("name")
	fields = {k: v for k, v in payload.items() if k not in ("id", "name", "doctype")}
	if name and frappe.db.exists("Strategy Corrective Action", name):
		doc = frappe.get_doc("Strategy Corrective Action", name)
		doc.update(fields)
		doc.save(ignore_permissions=True)
	else:
		fields["doctype"] = "Strategy Corrective Action"
		fields["corrective_action_code"] = None
		doc = frappe.get_doc(fields)
		doc.insert(ignore_permissions=True)
	return {"id": doc.name, "code": doc.get("corrective_action_code"), "status": doc.status}


def update_plan_identity(plan_name: str, payload: dict) -> dict:
	if not can_edit_draft_plan():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	if doc.status not in ("Draft", "Returned"):
		frappe.throw(_("Plan identity can only be edited in Draft or Returned"))
	for key in ("title", "plan_type", "start_date", "end_date", "description"):
		if key in payload:
			doc.set(key, payload[key])
	doc.save()
	return {"id": doc.name, "code": doc.plan_code, "name": doc.title, "status": doc.status}


def get_pvo(name: str | None = None, objective_code: str | None = None) -> dict:
	if not name and objective_code:
		name = frappe.db.get_value(
			"Public Value Objective",
			{"objective_code": objective_code, "status": "Active"},
			"name",
		) or frappe.db.get_value("Public Value Objective", {"objective_code": objective_code}, "name")
	doc = frappe.get_doc("Public Value Objective", name)
	return {
		"id": doc.name,
		"code": doc.objective_code,
		"name": doc.title,
		"version_number": doc.version_number,
		"pillar": doc.pillar,
		"status": doc.status,
		"scope": doc.scope,
		"procuring_entity": doc.procuring_entity,
		"description": doc.description,
		"source_type": doc.source_type,
		"source_reference": doc.source_reference,
		"applicability_mode": doc.applicability_mode,
		"measure_guidance": doc.measure_guidance,
		"evidence_guidance": doc.evidence_guidance,
		"responsible_function": doc.responsible_function,
		"default_enforcement_guidance": doc.default_enforcement_guidance,
		"effective_from": doc.effective_from,
		"effective_to": doc.effective_to,
		"triggers": [
			{
				"trigger_type": t.trigger_type,
				"trigger_value": t.trigger_value,
				"include": t.include,
			}
			for t in (doc.triggers or [])
		],
	}


def _resolve_target_name_for_code(target_code: str, plan_code: str | None = None) -> str | None:
	"""Prefer target on the requested / Active plan — codes are not globally unique across versions."""
	if plan_code:
		from kentender_strategy.services.strategy_contracts import _resolve_plan

		plan = _resolve_plan(None, plan_code)
		name = frappe.db.get_value(
			"Performance Target",
			{"target_code": target_code, "plan_version": plan.name},
			"name",
		)
		if name:
			return name
	row = frappe.db.sql(
		"""
		select t.name
		from `tabPerformance Target` t
		inner join `tabStrategic Plan` p on p.name = t.plan_version
		where t.target_code = %s
		order by
			case when p.status = 'Active' then 0 else 1 end,
			case when exists(
				select 1 from `tabPerformance Measurement` m
				where m.performance_target = t.name
			) then 0 else 1 end,
			p.version_number desc
		limit 1
		""",
		(target_code,),
	)
	return row[0][0] if row else None


def _measurement_target_payload(tgt) -> dict:
	indicator_title = None
	frequency = None
	data_source = None
	measurement_type = None
	if getattr(tgt, "performance_indicator", None):
		ind = frappe.db.get_value(
			"Performance Indicator",
			tgt.performance_indicator,
			["title", "measurement_frequency", "data_source", "measurement_type"],
			as_dict=True,
		)
		if ind:
			indicator_title = ind.title
			frequency = ind.measurement_frequency
			data_source = ind.data_source
			measurement_type = ind.measurement_type
	return {
		"id": tgt.name,
		"code": tgt.target_code,
		"name": tgt.title,
		"target_numeric": tgt.target_numeric,
		"comparison_direction": tgt.comparison_direction,
		"baseline_numeric": tgt.baseline_numeric,
		"baseline_as_of": str(tgt.baseline_as_of) if getattr(tgt, "baseline_as_of", None) else None,
		"tolerance_value": tgt.tolerance_value,
		"period_start": str(tgt.period_start) if getattr(tgt, "period_start", None) else None,
		"period_end": str(tgt.period_end) if getattr(tgt, "period_end", None) else None,
		"indicator_name": indicator_title,
		"measurement_frequency": frequency,
		"data_source": data_source,
		"measurement_type": measurement_type,
	}


def _measurement_dto(doc, tgt, *, is_new: bool = False) -> dict:
	return {
		"id": None if is_new else doc.name,
		"performance_target": _measurement_target_payload(tgt),
		"plan_version": getattr(doc, "plan_version", None) or tgt.plan_version,
		"measurement_period_start": getattr(doc, "measurement_period_start", None),
		"measurement_period_end": getattr(doc, "measurement_period_end", None),
		"measurement_date": getattr(doc, "measurement_date", None),
		"actual_numeric": getattr(doc, "actual_numeric", None),
		"actual_text": getattr(doc, "actual_text", None),
		"evidence_reference": getattr(doc, "evidence_reference", None),
		"evidence_source": getattr(doc, "evidence_source", None),
		"commentary": getattr(doc, "commentary", None),
		"variance": getattr(doc, "variance", None),
		"result_status": getattr(doc, "result_status", None),
		"workflow_status": getattr(doc, "workflow_status", None),
		"submitted_by": getattr(doc, "submitted_by", None),
		"submitted_at": str(doc.submitted_at) if getattr(doc, "submitted_at", None) else None,
		"verified_by": getattr(doc, "verified_by", None),
		"verified_at": str(doc.verified_at) if getattr(doc, "verified_at", None) else None,
		"verification_comment": getattr(doc, "verification_comment", None),
		"authorised_exception": int(getattr(doc, "authorised_exception", 0) or 0),
		"exception_reason": getattr(doc, "exception_reason", None),
		"is_new": is_new,
	}


def get_measurement(
	name: str | None = None,
	target_code: str | None = None,
	plan_code: str | None = None,
	purpose: str | None = None,
) -> dict:
	"""Load a measurement by id, or the best open row for a target.

	purpose:
	  - "submit": Draft / Returned only (Verified must not block a new submission)
	  - "verify": Submitted first, else Verified (review / view)
	  - default: Draft / Returned / Submitted, then any historical row
	"""
	if name and frappe.db.exists("Performance Measurement", name):
		doc = frappe.get_doc("Performance Measurement", name)
		tgt = frappe.get_doc("Performance Target", doc.performance_target)
		return _measurement_dto(doc, tgt, is_new=False)

	if target_code:
		tgt_name = _resolve_target_name_for_code(target_code, plan_code)
		if not tgt_name:
			frappe.throw(_("Performance Target {0} not found").format(target_code), frappe.DoesNotExistError)
		purpose_key = (purpose or "").strip().lower()
		name = None
		if purpose_key == "verify":
			name = frappe.db.get_value(
				"Performance Measurement",
				{"performance_target": tgt_name, "workflow_status": "Submitted"},
				"name",
				order_by="modified desc",
			) or frappe.db.get_value(
				"Performance Measurement",
				{"performance_target": tgt_name, "workflow_status": "Verified"},
				"name",
				order_by="modified desc",
			)
		elif purpose_key == "submit":
			name = frappe.db.get_value(
				"Performance Measurement",
				{"performance_target": tgt_name, "workflow_status": ["in", ["Draft", "Returned"]]},
				"name",
				order_by="modified desc",
			)
		else:
			name = frappe.db.get_value(
				"Performance Measurement",
				{
					"performance_target": tgt_name,
					"workflow_status": ["in", ["Draft", "Returned", "Submitted"]],
				},
				"name",
				order_by="modified desc",
			) or frappe.db.get_value(
				"Performance Measurement",
				{"performance_target": tgt_name},
				"name",
				order_by="measurement_period_end desc",
			)
		if name:
			return get_measurement(name=name)

		# Submit path with no open/prior measurement — return target shell (do not get_doc(None)).
		tgt = frappe.get_doc("Performance Target", tgt_name)
		shell = frappe._dict(
			{
				"name": None,
				"plan_version": tgt.plan_version,
				"measurement_period_start": None,
				"measurement_period_end": None,
				"measurement_date": None,
				"actual_numeric": None,
				"actual_text": None,
				"evidence_reference": None,
				"evidence_source": None,
				"commentary": None,
				"variance": None,
				"result_status": None,
				"workflow_status": None,
				"submitted_by": None,
				"submitted_at": None,
				"verified_by": None,
				"verified_at": None,
				"verification_comment": None,
				"authorised_exception": 0,
				"exception_reason": None,
			}
		)
		return _measurement_dto(shell, tgt, is_new=True)

	frappe.throw(_("Performance Measurement not found"), frappe.DoesNotExistError)


def list_corrective_actions(
	plan_version: str | None = None,
	plan_code: str | None = None,
	status: str | None = None,
) -> list[dict]:
	from kentender_strategy.services.strategy_contracts import _resolve_plan

	filters: dict[str, Any] = {}
	if plan_version or plan_code:
		plan = _resolve_plan(plan_version, plan_code)
		filters["plan_version"] = plan.name
	if status:
		filters["status"] = status
	rows = frappe.get_all(
		"Strategy Corrective Action",
		filters=filters,
		fields=[
			"name",
			"action",
			"owner",
			"due_date",
			"status",
			"performance_target",
			"performance_measurement",
			"expected_result",
		],
		order_by="modified desc",
		limit_page_length=200,
	)
	out = []
	for r in rows:
		tgt = frappe.db.get_value(
			"Performance Target", r.performance_target, ["target_code", "title"], as_dict=True
		)
		out.append(
			{
				"id": r.name,
				"action": r.action,
				"owner": r.owner,
				"due_date": r.due_date,
				"status": r.status,
				"expected_result": r.expected_result,
				"target": {
					"id": r.performance_target,
					"code": tgt.target_code if tgt else None,
					"name": tgt.title if tgt else None,
				},
				"measurement_id": r.performance_measurement,
			}
		)
	return out


def _clone_fields(doc) -> dict:
	data = {}
	for df in doc.meta.fields:
		if df.fieldtype in ("Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold"):
			continue
		if df.fieldname in _META_SKIP:
			continue
		if df.fieldtype == "Table":
			continue
		data[df.fieldname] = doc.get(df.fieldname)
	return data


def create_successor_version(plan_version: str) -> dict:
	"""Clone Active/Approved plan into Draft vN+1 with hierarchy + commitments (no measurements)."""
	if not can_create_successor_plan():
		frappe.throw(_("Not permitted to create a successor version"), frappe.PermissionError)
	if not plan_version or not frappe.db.exists("Strategic Plan", plan_version):
		frappe.throw(_("Strategic Plan not found"))

	src = frappe.get_doc("Strategic Plan", plan_version)
	assert_entity_in_scope(src.procuring_entity)
	if src.status not in ("Active", "Approved"):
		frappe.throw(_("Only Active or Approved plan versions can create a successor"))

	if frappe.db.exists(
		"Strategic Plan",
		{
			"plan_code": src.plan_code,
			"procuring_entity": src.procuring_entity,
			"status": ["in", ["Draft", "Returned", "Submitted"]],
			"version_number": [">", 1],
		},
	):
		frappe.throw(_("An open successor version already exists for this plan"))

	next_ver = int(src.version_number or 1) + 1
	new_plan = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"plan_code": src.plan_code,
			"version_number": next_ver,
			"title": src.title,
			"procuring_entity": src.procuring_entity,
			"plan_type": src.plan_type,
			"scope_type": src.scope_type,
			"scope_id": src.scope_id,
			"parent_plan": src.parent_plan,
			"start_date": src.start_date,
			"end_date": src.end_date,
			"description": src.description,
			"status": "Draft",
			"supersedes_plan_version": src.name,
		}
	)
	new_plan.insert(ignore_permissions=True)

	id_map: dict[str, str] = {}

	for prog in frappe.get_all(
		"Strategy Programme",
		filters={"plan_version": src.name},
		fields=["name"],
		order_by="order_index asc",
	):
		old = frappe.get_doc("Strategy Programme", prog.name)
		data = _clone_fields(old)
		data["doctype"] = "Strategy Programme"
		data["plan_version"] = new_plan.name
		clone = frappe.get_doc(data)
		clone.insert(ignore_permissions=True)
		id_map[old.name] = clone.name

	for sub in frappe.get_all(
		"Strategy Sub Programme",
		filters={"plan_version": src.name},
		fields=["name"],
		order_by="order_index asc",
	):
		old = frappe.get_doc("Strategy Sub Programme", sub.name)
		data = _clone_fields(old)
		data["doctype"] = "Strategy Sub Programme"
		data["plan_version"] = new_plan.name
		data["programme"] = id_map.get(old.programme) or old.programme
		clone = frappe.get_doc(data)
		clone.insert(ignore_permissions=True)
		id_map[old.name] = clone.name

	for out in frappe.get_all(
		"Strategic Outcome",
		filters={"plan_version": src.name},
		fields=["name"],
		order_by="order_index asc",
	):
		old = frappe.get_doc("Strategic Outcome", out.name)
		data = _clone_fields(old)
		data["doctype"] = "Strategic Outcome"
		data["plan_version"] = new_plan.name
		data["programme"] = id_map.get(old.programme) or old.programme
		if old.sub_programme:
			data["sub_programme"] = id_map.get(old.sub_programme) or old.sub_programme
		clone = frappe.get_doc(data)
		clone.insert(ignore_permissions=True)
		id_map[old.name] = clone.name

	for ind in frappe.get_all(
		"Performance Indicator",
		filters={"plan_version": src.name},
		fields=["name"],
		order_by="order_index asc",
	):
		old = frappe.get_doc("Performance Indicator", ind.name)
		data = _clone_fields(old)
		data["doctype"] = "Performance Indicator"
		data["plan_version"] = new_plan.name
		data["strategic_outcome"] = id_map.get(old.strategic_outcome) or old.strategic_outcome
		clone = frappe.get_doc(data)
		clone.insert(ignore_permissions=True)
		id_map[old.name] = clone.name

	for tgt in frappe.get_all(
		"Performance Target",
		filters={"plan_version": src.name},
		fields=["name"],
		order_by="creation asc",
	):
		old = frappe.get_doc("Performance Target", tgt.name)
		data = _clone_fields(old)
		data["doctype"] = "Performance Target"
		data["plan_version"] = new_plan.name
		data["performance_indicator"] = (
			id_map.get(old.performance_indicator) or old.performance_indicator
		)
		clone = frappe.get_doc(data)
		clone.insert(ignore_permissions=True)
		id_map[old.name] = clone.name

	for cname in frappe.get_all(
		"Plan Value Commitment",
		filters={"plan_version": src.name},
		pluck="name",
	):
		old = frappe.get_doc("Plan Value Commitment", cname)
		links = []
		for link in old.get("links") or []:
			row = {
				"link_type": link.link_type,
				"linked_outcome": id_map.get(link.linked_outcome) if link.linked_outcome else None,
				"linked_target": id_map.get(link.linked_target) if link.linked_target else None,
			}
			links.append(row)
		clone = frappe.get_doc(
			{
				"doctype": "Plan Value Commitment",
				"plan_version": new_plan.name,
				"public_value_objective_version": old.public_value_objective_version,
				"rationale": old.rationale,
				"consideration_level": old.consideration_level,
				"responsible_owner": old.responsible_owner,
				"plan_measure_note": old.plan_measure_note,
				"status": "Draft",
				"links": links,
			}
		)
		clone.insert(ignore_permissions=True)
		id_map[old.name] = clone.name

	audit_id = record_event(
		entity_type="Strategic Plan",
		entity_name=new_plan.name,
		event_type="SuccessorCreated",
		prior_state=src.status,
		new_state="Draft",
		plan_version=new_plan.name,
		summary=f"Created successor draft v{next_ver} from {src.plan_code} v{src.version_number}",
	)
	return {
		"ok": True,
		"plan": {
			"id": new_plan.name,
			"code": new_plan.plan_code,
			"name": new_plan.title,
			"status": new_plan.status,
			"version_number": new_plan.version_number,
			"supersedes_plan_version": new_plan.supersedes_plan_version,
			"procuring_entity": new_plan.procuring_entity,
		},
		"source_plan_id": src.name,
		"audit_event": audit_id,
	}
