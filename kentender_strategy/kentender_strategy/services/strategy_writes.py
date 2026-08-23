# Copyright (c) 2026, KenTender and contributors
"""Write companions for Strategy hierarchy, commitments, measurements."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_domain_guards import _assert_version_editable as _assert_plan_editable
from kentender_strategy.services.strategy_permissions import (
	assert_entity_in_scope,
	assert_org_unit_in_scope,
	can_create_successor_plan,
	can_edit_draft_plan,
)
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
	"StrategicObjective": ("Strategic Objective", "objective_code"),
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
	if node_type in ("StrategicObjective", "StrategicOutcome"):
		if data.get("sub_programme"):
			return {"sub_programme": data["sub_programme"]}
		if data.get("programme"):
			return {"programme": data["programme"]}
	if node_type == "PerformanceIndicator":
		if data.get("strategic_objective"):
			return {"strategic_objective": data["strategic_objective"]}
		if data.get("strategic_outcome"):
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

	if node_type in ("Programme", "SubProgramme", "StrategicObjective", "StrategicOutcome"):
		if _blank(data.get("responsible_function")):
			errors["responsible_function"] = _("Responsible function is required")

	if node_type == "PerformanceIndicator":
		has_objective = not _blank(data.get("strategic_objective"))
		has_outcome = not _blank(data.get("strategic_outcome"))
		if has_objective and has_outcome:
			errors["strategic_outcome"] = _(
				"Choose either a Strategic Objective or a Strategic Outcome, not both"
			)
		elif not has_objective and not has_outcome:
			errors["strategic_outcome"] = _(
				"A Strategic Objective or a Strategic Outcome is required"
			)
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
		"strategic_objective",
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
	owner_ou = data.get("owner_org_unit")
	if owner_ou is None and name and frappe.db.exists(doctype, name):
		owner_ou = frappe.db.get_value(doctype, name, "owner_org_unit")
	if pe:
		assert_org_unit_in_scope(pe, owner_ou, require_write=True)

	# Inherit parent links / plan from parent when omitted
	if node_type == "SubProgramme" and data.get("programme"):
		data["plan_version"] = plan_version
	elif node_type in ("StrategicObjective", "StrategicOutcome"):
		if data.get("sub_programme") and not data.get("programme"):
			data["programme"] = frappe.db.get_value(
				"Strategy Sub Programme", data["sub_programme"], "programme"
			)
	elif node_type == "PerformanceIndicator" and (
		data.get("strategic_objective") or data.get("strategic_outcome")
	):
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
	if node_type == "StrategicObjective":
		if frappe.db.exists("Performance Indicator", {"strategic_objective": name}):
			frappe.throw(_("Delete child indicators first"))
	if node_type == "StrategicOutcome":
		if frappe.db.exists("Performance Indicator", {"strategic_outcome": name}):
			frappe.throw(_("Delete child indicators first"))
	if node_type == "SubProgramme":
		if (
			frappe.db.exists("Strategic Outcome", {"sub_programme": name})
			or frappe.db.exists("Strategic Objective", {"sub_programme": name})
		):
			frappe.throw(_("Delete child outcomes first"))
	if node_type == "Programme":
		if (
			frappe.db.exists("Strategy Sub Programme", {"programme": name})
			or frappe.db.exists("Strategic Outcome", {"programme": name})
			or frappe.db.exists("Strategic Objective", {"programme": name})
		):
			frappe.throw(_("Delete child structure first"))
	frappe.delete_doc(doctype, name, ignore_permissions=True)
	return {"ok": True}


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

	for obj in frappe.get_all(
		"Strategic Objective",
		filters={"plan_version": src.name},
		fields=["name"],
		order_by="order_index asc",
	):
		old = frappe.get_doc("Strategic Objective", obj.name)
		data = _clone_fields(old)
		data["doctype"] = "Strategic Objective"
		data["plan_version"] = new_plan.name
		data["programme"] = id_map.get(old.programme) or old.programme
		if old.sub_programme:
			data["sub_programme"] = id_map.get(old.sub_programme) or old.sub_programme
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
		if old.strategic_objective:
			data["strategic_objective"] = id_map.get(old.strategic_objective) or old.strategic_objective
		if old.strategic_outcome:
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
		"Strategy Value Commitment",
		filters={"plan_version": src.name},
		pluck="name",
	):
		old = frappe.get_doc("Strategy Value Commitment", cname)
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
				"doctype": "Strategy Value Commitment",
				"plan_version": new_plan.name,
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
