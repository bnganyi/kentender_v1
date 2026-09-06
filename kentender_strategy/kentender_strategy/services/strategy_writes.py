# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §10.1 write commands: save_strategy_plan_draft,
create_strategy_successor_version, save_strategy_structure_draft.

Rebuilt for the Phase 1 domain model (Strategic Plan/Strategic Plan
Version split, unified Strategy Node) — the previous version of this file
targeted the pre-rebuild Programme/Sub-programme/Objective/Outcome
doctypes and combined Plan/Version schema."""

from __future__ import annotations

import frappe
from frappe import _

from kentender_strategy.services.strategy_audit import record_event
from kentender_strategy.services.strategy_authorization import (
	CAP_AUTHOR,
	ROLE_STRATEGY_AUTHOR,
	assignment_id,
	require_plan_create_capability,
	require_plan_version_capability,
)
from kentender_strategy.services.strategy_reference import resolve_plan_name, resolve_version_name
from kentender_strategy.services.strategy_transitions import _check_expected_version, _version_payload

# STR-CHG-001 v1.7 §4.1 — plan identity is title, role, parent and period.
# The Procuring Entity and organisation-unit columns are gone (§16.1).
PLAN_IDENTITY_FIELDS = (
	"title",
	"plan_role",
	"parent_primary_plan_id",
	"period_start",
	"period_end",
)
VERSION_FIELDS = ("effective_from", "effective_to")


def _plan_payload(plan) -> dict:
	return {
		"plan_id": plan.name,
		"plan_reference": plan.plan_id,
		"title": plan.title,
		"plan_role": plan.plan_role,
		"parent_primary_plan_id": plan.parent_primary_plan_id,
		"period_start": str(plan.period_start) if plan.period_start else None,
		"period_end": str(plan.period_end) if plan.period_end else None,
	}


def save_strategy_plan_draft(payload: dict, *, expected_version: str | None = None) -> dict:
	"""Create a new Strategic Plan + its Draft v1, or update an existing
	Draft plan's identity and version period fields."""
	plan_id = resolve_plan_name(payload.get("plan_id"))
	if plan_id:
		plan = frappe.get_doc("Strategic Plan", plan_id)
		version_id = resolve_version_name(payload.get("plan_version_id")) or frappe.db.get_value(
			"Strategic Plan Version",
			{"plan_id": plan_id, "status": "Draft"},
			"name",
		)
		if not version_id:
			frappe.throw(
				_("No editable Draft version found for this plan"),
				frappe.ValidationError,
				title="STRATEGY_INVALID_STATE",
			)
		version = frappe.get_doc("Strategic Plan Version", version_id)
		_check_expected_version(version, expected_version)
		exercised = require_plan_version_capability(frappe.session.user, CAP_AUTHOR, version)

		for field in PLAN_IDENTITY_FIELDS:
			if field in payload:
				plan.set(field, payload[field])
		plan.save(ignore_permissions=True)
		for field in VERSION_FIELDS:
			if field in payload:
				version.set(field, payload[field])
		version.save(ignore_permissions=True)

		record_event(
			entity_type="Strategic Plan Version",
			entity_name=version.name,
			event_type="Draft saved",
			plan_version=version.name,
			business_role=ROLE_STRATEGY_AUTHOR,
			assignment=assignment_id(exercised),
		)
		return {"plan": _plan_payload(plan), "version": _version_payload(version)}

	# CU-303 — one site is one Procuring Entity: no entity is supplied,
	# validated or stamped (the physical column falls to RM per D2).
	exercised = require_plan_create_capability(frappe.session.user)

	plan = frappe.get_doc(
		{"doctype": "Strategic Plan", **{f: payload.get(f) for f in PLAN_IDENTITY_FIELDS}}
	)
	plan.insert(ignore_permissions=True)
	version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan.name,
			"version_number": 1,
			**{f: payload.get(f) for f in VERSION_FIELDS},
		}
	)
	version.insert(ignore_permissions=True)

	record_event(
		entity_type="Strategic Plan Version",
		entity_name=version.name,
		event_type="Draft saved",
		plan_version=version.name,
		summary="Plan draft created",
		business_role=ROLE_STRATEGY_AUTHOR,
		assignment=assignment_id(exercised),
	)
	return {"plan": _plan_payload(plan), "version": _version_payload(version)}


def create_strategy_successor_version(plan_id: str) -> dict:
	"""STR-CHG-001 §10.1 create_strategy_successor_version — copy the plan's
	Active version's hierarchy/indicators/targets into a new Draft, with
	based_on_plan_version_id as the fixed comparison baseline."""
	plan_id = resolve_plan_name(plan_id) or plan_id
	baseline_name = frappe.db.get_value(
		"Strategic Plan Version",
		{"plan_id": plan_id, "status": "Active"},
		"name",
		order_by="version_number desc",
	)
	if not baseline_name:
		frappe.throw(
			_("No Active version to create a successor from"),
			frappe.ValidationError,
			title="STRATEGY_INVALID_STATE",
		)
	baseline = frappe.get_doc("Strategic Plan Version", baseline_name)
	exercised = require_plan_version_capability(frappe.session.user, CAP_AUTHOR, baseline)

	if frappe.db.exists(
		"Strategic Plan Version",
		{"plan_id": plan_id, "status": ["in", ("Draft", "Submitted for approval")]},
	):
		frappe.throw(
			_("An open successor version already exists for this plan"),
			frappe.ValidationError,
			title="STRATEGY_INVALID_STATE",
		)

	new_version = frappe.get_doc(
		{
			"doctype": "Strategic Plan Version",
			"plan_id": plan_id,
			"version_number": int(baseline.version_number) + 1,
			"based_on_plan_version_id": baseline.name,
			"effective_from": baseline.effective_from,
			"effective_to": baseline.effective_to,
		}
	)
	new_version.insert(ignore_permissions=True)

	id_map: dict[str, str] = {}
	remaining = frappe.get_all(
		"Strategy Node",
		filters={"plan_version_id": baseline.name},
		fields=["name", "node_type", "parent_node_id", "title", "display_order"],
	)
	# Clone parents before children regardless of original creation order.
	while remaining:
		still = []
		progressed = False
		for node in remaining:
			if node.parent_node_id and node.parent_node_id not in id_map:
				still.append(node)
				continue
			clone = frappe.get_doc(
				{
					"doctype": "Strategy Node",
					"plan_version_id": new_version.name,
					"node_type": node.node_type,
					"parent_node_id": id_map.get(node.parent_node_id) if node.parent_node_id else None,
					"title": node.title,
					"display_order": node.display_order,
				}
			)
			clone.insert(ignore_permissions=True)
			id_map[node.name] = clone.name
			progressed = True
		if not progressed and still:
			frappe.throw(_("Could not resolve hierarchy parent chain while cloning"))
		remaining = still

	indicator_ids = []
	for ind in frappe.get_all(
		"Performance Indicator",
		filters={"plan_version_id": baseline.name},
		fields=["name", "measures_node_id", "indicator_name", "definition", "unit"],
	):
		clone = frappe.get_doc(
			{
				"doctype": "Performance Indicator",
				"plan_version_id": new_version.name,
				"measures_node_id": id_map.get(ind.measures_node_id, ind.measures_node_id),
				"indicator_name": ind.indicator_name,
				"definition": ind.definition,
				"unit": ind.unit,
			}
		)
		clone.insert(ignore_permissions=True)
		id_map[ind.name] = clone.name
		indicator_ids.append(ind.name)

	for tgt in (
		frappe.get_all(
			"Performance Target",
			filters={"indicator_id": ["in", indicator_ids]},
			fields=["indicator_id", "fiscal_year", "target_by_date", "comparison", "target_value"],
		)
		if indicator_ids
		else []
	):
		frappe.get_doc(
			{
				"doctype": "Performance Target",
				"indicator_id": id_map.get(tgt.indicator_id, tgt.indicator_id),
				"fiscal_year": tgt.fiscal_year,
				"target_by_date": tgt.target_by_date,
				"comparison": tgt.comparison,
				"target_value": tgt.target_value,
			}
		).insert(ignore_permissions=True)

	record_event(
		entity_type="Strategic Plan Version",
		entity_name=new_version.name,
		event_type="Successor Version Created",
		plan_version=new_version.name,
		summary=f"Created successor v{new_version.version_number} based on {baseline.name}",
		business_role=ROLE_STRATEGY_AUTHOR,
		assignment=assignment_id(exercised),
	)
	return _version_payload(new_version)


def _resolve_client_id(id_map: dict[str, str], value):
	if isinstance(value, str) and value.startswith("$"):
		return id_map.get(value)
	return value


def _assert_deletable(doctype: str, name: str) -> None:
	if doctype == "Strategy Node":
		if frappe.db.exists("Strategy Node", {"parent_node_id": name}):
			frappe.throw(_("Delete child nodes first"), frappe.ValidationError, title="STRATEGY_INVALID_HIERARCHY")
		if frappe.db.exists("Performance Indicator", {"measures_node_id": name}):
			frappe.throw(
				_("Delete indicators measuring this node first"),
				frappe.ValidationError,
				title="STRATEGY_INVALID_HIERARCHY",
			)
	elif doctype == "Performance Indicator":
		if frappe.db.exists("Performance Target", {"indicator_id": name}):
			frappe.throw(
				_("Delete targets for this indicator first"), frappe.ValidationError, title="STRATEGY_INVALID_TARGET"
			)


def save_strategy_structure_draft(
	plan_version_id: str,
	*,
	nodes: list[dict] | None = None,
	indicators: list[dict] | None = None,
	targets: list[dict] | None = None,
	deletes: list[dict] | None = None,
	expected_version: str | None = None,
) -> dict:
	"""STR-CHG-001 §10.1 save_strategy_structure_draft — create, update,
	reorder or remove Draft nodes/indicators/targets as one validated
	change set. `client_id` on a node/indicator item lets a later item in
	the same batch reference it (as e.g. parent_node_id="$1") before it has
	a real generated id."""
	plan_version_id = resolve_version_name(plan_version_id) or plan_version_id
	version = frappe.get_doc("Strategic Plan Version", plan_version_id)
	_check_expected_version(version, expected_version)
	exercised = require_plan_version_capability(frappe.session.user, CAP_AUTHOR, version)

	id_map: dict[str, str] = {}
	result: dict[str, list[str]] = {"nodes": [], "indicators": [], "targets": [], "deleted": []}

	for item in deletes or []:
		doctype, name = item.get("doctype"), item.get("name")
		if not doctype or not name or not frappe.db.exists(doctype, name):
			continue
		_assert_deletable(doctype, name)
		frappe.delete_doc(doctype, name, ignore_permissions=True)
		result["deleted"].append(name)

	for item in nodes or []:
		data = dict(item)
		client_id = data.pop("client_id", None)
		name = data.pop("name", None)
		data["plan_version_id"] = plan_version_id
		if "parent_node_id" in data:
			data["parent_node_id"] = _resolve_client_id(id_map, data["parent_node_id"])
		if name and frappe.db.exists("Strategy Node", name):
			doc = frappe.get_doc("Strategy Node", name)
			doc.update(data)
			doc.save(ignore_permissions=True)
		else:
			data["doctype"] = "Strategy Node"
			doc = frappe.get_doc(data)
			doc.insert(ignore_permissions=True)
		if client_id:
			id_map[client_id] = doc.name
		result["nodes"].append(doc.name)

	for item in indicators or []:
		data = dict(item)
		client_id = data.pop("client_id", None)
		name = data.pop("name", None)
		data["plan_version_id"] = plan_version_id
		if "measures_node_id" in data:
			data["measures_node_id"] = _resolve_client_id(id_map, data["measures_node_id"])
		if name and frappe.db.exists("Performance Indicator", name):
			doc = frappe.get_doc("Performance Indicator", name)
			doc.update(data)
			doc.save(ignore_permissions=True)
		else:
			data["doctype"] = "Performance Indicator"
			doc = frappe.get_doc(data)
			doc.insert(ignore_permissions=True)
		if client_id:
			id_map[client_id] = doc.name
		result["indicators"].append(doc.name)

	for item in targets or []:
		data = dict(item)
		name = data.pop("name", None)
		if "indicator_id" in data:
			data["indicator_id"] = _resolve_client_id(id_map, data["indicator_id"])
		if name and frappe.db.exists("Performance Target", name):
			doc = frappe.get_doc("Performance Target", name)
			doc.update(data)
			doc.save(ignore_permissions=True)
		else:
			data["doctype"] = "Performance Target"
			doc = frappe.get_doc(data)
			doc.insert(ignore_permissions=True)
		result["targets"].append(doc.name)

	record_event(
		entity_type="Strategic Plan Version",
		entity_name=version.name,
		event_type="Draft structure saved",
		plan_version=version.name,
		summary=(
			f"{len(result['nodes'])} node(s), {len(result['indicators'])} indicator(s), "
			f"{len(result['targets'])} target(s), {len(result['deleted'])} deletion(s)"
		),
		business_role=ROLE_STRATEGY_AUTHOR,
		assignment=assignment_id(exercised),
	)
	result["expected_version"] = str(frappe.db.get_value("Strategic Plan Version", version.name, "modified"))
	return result
