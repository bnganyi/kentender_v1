# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10.2 — Draft-stage commands: creation, the five-step
editor's row CRUD, baseline confirmation and on-demand validation.

Every command here operates only on a `Draft` Version/Package Version
(§7.5 invariant 9/12: a locked Version is immutable — `lifecycle.py` owns
the transitions that lock one). Authorisation is `require_draft_author_for_any`
against the root's own `contributing_org_units` throughout: §2.1's narrow
cross-department relaxation means any contributing department's Author/HoD
may edit the shared Draft, not only a single "owning" department.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.procurement_requisitions.services import (
	catalogue,
	compatibility,
	digest,
	envelope,
	eligibility_gateway,
	references,
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail


# --------------------------------------------------------------------------
# Loaders / projections — plain dicts, never the Frappe document, for
# `validation.py`'s DB-free contract.
# --------------------------------------------------------------------------


# Frappe's own bookkeeping fields on any document or child row. A digest
# (or any DB-free validation.py projection) must never include these: they
# change on every save regardless of whether the row's own business content
# changed (confirmed live — a child row's `modified` timestamp is rewritten
# by every parent `.save()`, even an unrelated one), which would make the
# content digest spuriously differ between the moment it was computed and
# the moment it is later recomputed for comparison (§7.2's "recheck the
# submitted Version" is meaningless if the digest itself is not stable).
_FRAPPE_BOOKKEEPING_FIELDS = frozenset(
	{"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "parent", "parentfield", "parenttype", "doctype"}
)


def _child_rows(doc, fieldname: str) -> list[dict[str, Any]]:
	return [
		{k: v for k, v in row.as_dict().items() if k not in _FRAPPE_BOOKKEEPING_FIELDS}
		for row in doc.get(fieldname) or []
	]


def _version_dict(version) -> dict[str, Any]:
	return {
		"requirement_title": version.requirement_title,
		"delivery_location": version.delivery_location,
		"latest_delivery_date": cstr(version.latest_delivery_date),
		"related_services_required": bool(version.related_services_required),
		"drawdown_lines": _child_rows(version, "drawdown_lines"),
	}


def _package_dict(package_version) -> dict[str, Any]:
	return {
		"minimum_warranty_months": package_version.minimum_warranty_months,
		"onsite_support_required": bool(package_version.onsite_support_required),
		"maximum_support_response_hours": package_version.maximum_support_response_hours,
		"manufacturer_support_required": bool(package_version.manufacturer_support_required),
		"service_location_constraint": package_version.service_location_constraint,
		"support_description": package_version.support_description,
		"items": _child_rows(package_version, "items"),
		"technical_requirements": _child_rows(package_version, "technical_requirements"),
		"related_services": _child_rows(package_version, "related_services"),
		"acceptance_requirements": _child_rows(package_version, "acceptance_requirements"),
		"supporting_materials": _child_rows(package_version, "supporting_materials"),
	}


def _load(requisition: str) -> tuple[Any, Any, Any]:
	root = frappe.get_doc("Procurement Requisition", requisition)
	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	return root, version, package_version


def _contributing_units(root) -> set[str]:
	return {row.organisation_unit for row in root.contributing_org_units}


def _next_id(prefix: str, existing: list[str]) -> str:
	seq = max([int(cstr(e)[len(prefix):]) for e in existing if cstr(e).startswith(prefix) and cstr(e)[len(prefix):].isdigit()] or [0]) + 1
	return f"{prefix}{seq:03d}"


def _require_draft(version, package_version) -> None:
	if version.version_status != "Draft" or package_version.version_status != "Draft":
		fail("REQ_STALE_VERSION", "This Requisition is no longer a Draft. Reload before continuing.")


# --------------------------------------------------------------------------
# PrepareITEquipmentRequisition
# --------------------------------------------------------------------------


def prepare_it_equipment_requisition(*, plan_item_id: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"plan_item_id": plan_item_id}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	projection = eligibility_gateway.get_requisition_eligible_plan_item(plan_item_id)
	if projection.get("outcome") == "FORBIDDEN":
		authz.not_found()
	if not projection.get("eligible"):
		fail("REQ_PLAN_INELIGIBLE")
	failure = compatibility.first_failure(projection)
	if failure:
		fail("REQ_PRODUCT_UNSUPPORTED", f"This Plan Item is not supported by the IT-equipment Requisition pattern ({failure.test}).", {"test": failure.test})

	contributing_units = set(projection.get("contributing_org_unit_ids") or [])
	authz.require_draft_author_for_any(contributing_units, actor)

	existing = frappe.get_all(
		"Procurement Requisition", filters={"plan_item_id": projection["plan_item_id"], "current_state": ["not in", ("Withdrawn", "Revoked", "Superseded")]},
		fields=["name", "current_state", "current_version"], limit_page_length=1,
	)
	if existing:
		row = existing[0]
		if row.current_state != "Draft":
			fail("REQ_OPEN_EXISTS")
		root, version, package_version = _load(row.name)
		result = {
			"ok": True, "idempotent": False, "action": "reused", "requisition": root.name,
			"requisition_reference": root.requisition_reference, "requisition_version": version.name,
			"package_version": package_version.name, "record_version": root.record_version,
		}
		envelope.record_command(idempotency_key=idempotency_key, command="PrepareITEquipmentRequisition", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
		return result

	# §5.1 — defaults to the department with the largest drawn (here:
	# planned remaining) value; confirmed implicitly at departmental
	# submission and changeable only by the Head of Procurement Function
	# at authorisation review (lifecycle.py, later phase).
	by_unit: dict[str, float] = {}
	for source in projection.get("sources", []):
		by_unit[source["organisation_unit"]] = by_unit.get(source["organisation_unit"], 0) + flt(source.get("remaining_amount"))
	lead_org_unit = max(by_unit, key=by_unit.get) if by_unit else (sorted(contributing_units)[0] if contributing_units else "")

	requisition_reference = references.requisition_reference(fiscal_year=projection["fiscal_year"], plan_item_id_value=projection["plan_item_id"])

	root = frappe.get_doc(
		{
			"doctype": "Procurement Requisition",
			"requisition_reference": requisition_reference,
			"plan_id": projection["plan_reference"], "plan_version_id": projection["version_reference"],
			"plan_item_id": projection["plan_item_id"], "strategic_objective": projection.get("strategic_objective"),
			"strategic_objective_path": projection.get("strategic_objective_path"),
			"procurement_category": projection.get("procurement_category"), "plan_horizon": projection.get("plan_horizon"),
			"multi_year_justification": projection.get("multi_year_justification"),
			"contributing_org_units": [{"organisation_unit": u} for u in sorted(contributing_units)],
			"lead_org_unit": lead_org_unit, "current_state": "Draft", "record_version": 0,
		}
	).insert(ignore_permissions=True)

	package = frappe.get_doc(
		{
			"doctype": "IT Equipment Requirement Package", "requisition": root.name, "product_pattern": "IT Equipment",
			"reservation_category": projection.get("reservation_category"), "lotting_indicator": projection.get("lotting_indicator"),
			"record_version": 0,
		}
	).insert(ignore_permissions=True)

	package_version = frappe.get_doc(
		{
			"doctype": "IT Equipment Requirement Package Version", "package": package.name, "version_number": 1,
			"version_status": "Draft", "catalogue_version": catalogue.CATALOGUE_VERSION, "record_version": 0,
		}
	).insert(ignore_permissions=True)
	package.current_version = package_version.name
	package.save(ignore_permissions=True)

	drawdown_lines = [
		{
			"drawdown_line_id": f"DL-{i + 1:03d}", "plan_item_line_id": source["plan_item_line_id"],
			"source_line_id": source["source_line_id"], "contributing_org_unit": source["organisation_unit"],
			"approved_quantity": source["approved_quantity"], "approved_value": source["allocated_amount"],
			"remaining_quantity": source["remaining_quantity"], "remaining_value": source["remaining_amount"],
			"requested_quantity": source["remaining_quantity"], "requested_value": source["remaining_amount"],
			"unit": source.get("unit") or "Each",
		}
		for i, source in enumerate(projection.get("sources", []))
	]
	version = frappe.get_doc(
		{
			"doctype": "Requisition Version", "requisition": root.name, "version_number": 1, "version_status": "Draft",
			"requirement_title": projection.get("title") or "", "latest_delivery_date": projection.get("planned_dates", {}).get("delivery_completion_date") or projection.get("planned_dates", {}).get("completion_date"),
			"related_services_required": 0, "package_version": package_version.name, "drawdown_lines": drawdown_lines,
			"record_version": 0,
		}
	).insert(ignore_permissions=True)

	root.current_version = version.name
	root.save(ignore_permissions=True)

	result = {
		"ok": True, "idempotent": False, "action": "created", "requisition": root.name,
		"requisition_reference": root.requisition_reference, "requisition_version": version.name,
		"package_version": package_version.name, "record_version": root.record_version,
	}
	envelope.record_command(idempotency_key=idempotency_key, command="PrepareITEquipmentRequisition", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# SaveRequisitionSummary
# --------------------------------------------------------------------------


def save_requisition_summary(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	authz.require_draft_author_for_any(_contributing_units(root), actor)
	version = envelope.locked("Requisition Version", root.current_version)
	envelope.check_record_version(version, expected_record_version)
	if version.version_status != "Draft":
		fail("REQ_STALE_VERSION", "This Requisition is no longer a Draft. Reload before continuing.")

	for field_name in ("requirement_title", "delivery_location", "latest_delivery_date"):
		if field_name in values:
			version.set(field_name, values[field_name])
	if "related_services_required" in values:
		version.related_services_required = 1 if values["related_services_required"] else 0

	requested_by_line = {r["drawdown_line_id"]: r for r in (values.get("drawdown_lines") or [])}
	for line in version.drawdown_lines:
		posted = requested_by_line.get(line.drawdown_line_id)
		if not posted:
			continue
		requested_qty = flt(posted.get("requested_quantity"))
		requested_value = flt(posted.get("requested_value"))
		if requested_qty <= 0 or requested_value <= 0:
			fail("REQ_CONTROL_INVALID", "A drawdown quantity and value must both be positive.")
		if requested_qty > flt(line.remaining_quantity) + 1e-6 or requested_value > flt(line.remaining_value) + 1e-6:
			fail("REQ_BALANCE_CHANGED")
		line.requested_quantity = requested_qty
		line.requested_value = requested_value

	envelope.bump(version)
	result = {"ok": True, "idempotent": False, "action": "saved", "requisition_version": version.name, "record_version": version.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="SaveRequisitionSummary", payload=payload, result=result, document_type="Requisition Version", document_name=version.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# Package-row CRUD — items, technical requirements, related services,
# acceptance requirements, supporting materials. One shared load/gate/bump
# path; each public command supplies its own row shape and stable-id prefix.
# --------------------------------------------------------------------------


def _load_for_row_command(requisition: str, actor: str) -> tuple[Any, Any, Any]:
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	authz.require_draft_author_for_any(_contributing_units(root), actor)
	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)
	_require_draft(version, package_version)
	return root, version, package_version


def _add_row(*, requisition: str, table_field: str, id_field: str, id_prefix: str, values: dict[str, Any], expected_record_version, idempotency_key: str, command: str, user: str | None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "table_field": table_field, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version = _load_for_row_command(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	existing_ids = [row.get(id_field) for row in package_version.get(table_field)]
	row_id = _next_id(id_prefix, existing_ids)
	row_values = dict(values)
	row_values[id_field] = row_id
	row_values["row_order"] = len(existing_ids) + 1
	package_version.append(table_field, row_values)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "added", "row_id": row_id, "package_version": package_version.name, "record_version": package_version.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type="IT Equipment Requirement Package Version", document_name=package_version.name, actor=actor)
	return result


def _update_row(*, requisition: str, table_field: str, id_field: str, row_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, command: str, user: str | None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "table_field": table_field, "row_id": row_id, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version = _load_for_row_command(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	rows = [r for r in package_version.get(table_field) if r.get(id_field) == row_id]
	if not rows:
		authz.not_found()
	row = rows[0]
	for field_name, value in values.items():
		row.set(field_name, value)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "updated", "row_id": row_id, "package_version": package_version.name, "record_version": package_version.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type="IT Equipment Requirement Package Version", document_name=package_version.name, actor=actor)
	return result


def _remove_row(*, requisition: str, table_field: str, id_field: str, row_id: str, expected_record_version, idempotency_key: str, command: str, user: str | None, block_if_referenced: bool = False) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "table_field": table_field, "row_id": row_id}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version = _load_for_row_command(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	if block_if_referenced and _row_is_referenced(package_version, row_id):
		fail("REQ_QUANTITY_MISMATCH", "This item is linked to technical, service, acceptance or supporting-material rows. Remove those first.")
	rows = package_version.get(table_field)
	remaining = [r for r in rows if r.get(id_field) != row_id]
	if len(remaining) == len(rows):
		authz.not_found()
	package_version.set(table_field, remaining)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "removed", "row_id": row_id, "package_version": package_version.name, "record_version": package_version.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type="IT Equipment Requirement Package Version", document_name=package_version.name, actor=actor)
	return result


def _row_is_referenced(package_version, item_id: str) -> bool:
	for table_field in ("technical_requirements", "related_services", "acceptance_requirements"):
		for row in package_version.get(table_field):
			if row.get("applies_to_scope") == "Item" and row.get("applies_to_id") == item_id:
				return True
	for material in package_version.get("supporting_materials"):
		try:
			linked = json.loads(material.get("linked_requirement_ids_json") or "[]")
		except (TypeError, ValueError):
			linked = []
		if item_id in linked:
			return True
	return False


# --- Requisition Item ---


def add_requisition_item(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	result = _add_row(requisition=requisition, table_field="items", id_field="requisition_item_id", id_prefix="RQI-", values={**values, "unit": "Each"}, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="AddRequisitionItem", user=user)
	if result.get("idempotent"):
		return result
	_propose_baseline_for_item(requisition, result["row_id"], values.get("equipment_category", ""), actor=authz.actor(user))
	return result


def update_requisition_item(*, requisition: str, requisition_item_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _update_row(requisition=requisition, table_field="items", id_field="requisition_item_id", row_id=requisition_item_id, values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="UpdateRequisitionItem", user=user)


def remove_requisition_item(*, requisition: str, requisition_item_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _remove_row(requisition=requisition, table_field="items", id_field="requisition_item_id", row_id=requisition_item_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="RemoveRequisitionItem", user=user, block_if_referenced=True)


def _propose_baseline_for_item(requisition: str, requisition_item_id: str, equipment_category: str, *, actor: str) -> None:
	"""§6.4/§13.6A — the moment an item is added, its category's baseline
	rows are proposed (row_status=Proposed), never silently confirmed.

	§13.7's own fixture is explicit that a shared characteristic "is All
	items, so nothing is entered twice": when the identical baseline
	proposal (same characteristic, same proposed value) already exists for
	a *different* item, this widens that existing row to All-items scope
	instead of appending a second, duplicate per-item row — confirmed live
	on the two-item Business laptops fixture, where the naive per-item
	version doubled every shared row (22 rows instead of §13.7's 11)."""
	root, version, package_version = _load(requisition)
	rows = package_version.technical_requirements
	existing_ids = [row.technical_requirement_id for row in rows]
	covered_keys = {row.characteristic_key for row in rows if row.applies_to_scope == "All items"}
	covered_keys |= {row.characteristic_key for row in rows if row.applies_to_id == requisition_item_id}
	for proposal in catalogue.propose_baseline(equipment_category):
		key = proposal["characteristic_key"]
		if key in covered_keys:
			continue
		value_json = proposal["required_value_json"] or ""
		twin = next((row for row in rows if row.characteristic_key == key and row.applies_to_scope == "Item" and (row.required_value_json or "") == value_json), None)
		if twin:
			twin.applies_to_scope = "All items"
			twin.applies_to_id = ""
			continue
		ch = catalogue.CATALOGUE_BY_KEY[key]
		row_id = _next_id("TECH-", existing_ids)
		existing_ids.append(row_id)
		# A baseline rule that DOES propose a default (e.g. "Storage type":
		# "NVMe SSD") needs its own display text too — found live: this was
		# the only path in the module that ever wrote `required_value_json`
		# without also computing `required_value_display`, so a screen that
		# renders the display field directly (REQ-DES-08's task screen)
		# showed a blank cell for every baseline-proposed row, confirmed or
		# not, while `add_technical_requirement`'s own rows always had text.
		display = catalogue.display_value(ch, json.loads(value_json)) if value_json else ""
		package_version.append(
			"technical_requirements",
			{
				"technical_requirement_id": row_id, "applies_to_scope": "Item", "applies_to_id": requisition_item_id,
				"characteristic_key": key, "comparison": ch.comparison, "unit": ch.unit,
				"required_value_json": value_json, "required_value_display": display, "mandatory": 1,
				"row_status": "Proposed", "proposed_by_rule": key, "row_order": len(existing_ids),
			},
		)
	envelope.bump(package_version)


# --- Requisition Technical Requirement ---


def add_technical_requirement(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	ch = catalogue.CATALOGUE_BY_KEY.get(values.get("characteristic_key"))
	if not ch:
		fail("REQ_CONTROL_INVALID", "Unknown characteristic.")
	try:
		normalised = catalogue.validate_value(ch, values.get("value"), other_value=values.get("other_value", ""))
	except catalogue.CatalogueValueError as exc:
		fail("REQ_CONTROL_INVALID", str(exc))
	row_values = {
		"applies_to_scope": values.get("applies_to_scope", "All items"), "applies_to_id": values.get("applies_to_id", ""),
		"characteristic_key": ch.key, "comparison": ch.comparison, "unit": ch.unit,
		"required_value_json": json.dumps(normalised), "required_value_display": catalogue.display_value(ch, normalised),
		"other_value": values.get("other_value", ""), "mandatory": 1, "reason": values.get("reason", ""),
		"row_status": "Confirmed",
	}
	return _add_row(requisition=requisition, table_field="technical_requirements", id_field="technical_requirement_id", id_prefix="TECH-", values=row_values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="AddTechnicalRequirement", user=user)


def update_technical_requirement(*, requisition: str, technical_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _update_row(requisition=requisition, table_field="technical_requirements", id_field="technical_requirement_id", row_id=technical_requirement_id, values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="UpdateTechnicalRequirement", user=user)


def remove_technical_requirement(*, requisition: str, technical_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _remove_row(requisition=requisition, table_field="technical_requirements", id_field="technical_requirement_id", row_id=technical_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="RemoveTechnicalRequirement", user=user)


def confirm_proposed_requirement(*, requisition: str, technical_requirement_id: str, expected_record_version, idempotency_key: str, value: Any = None, other_value: str = "", user: str | None = None) -> dict[str, Any]:
	"""§6.4/§13.6A — confirms a Proposed baseline row. A baseline rule that
	proposes no default (e.g. Memory, Storage capacity) has an empty
	`required_value_json`; confirming that row with no value would silently
	produce a "Confirmed" row with nothing actually required — the exact
	failure REQ-AC-011's visible confirm-or-remove moment exists to prevent
	(found live: the naive version let a bare Confirm click do exactly
	this). `value`/`other_value` are therefore required whenever the row
	does not already carry a value, validated through the same catalogue
	rule `add_technical_requirement` uses — never a second, looser check."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "table_field": "technical_requirements", "row_id": technical_requirement_id, "value": value, "other_value": other_value}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version = _load_for_row_command(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	rows = [r for r in package_version.get("technical_requirements") if r.get("technical_requirement_id") == technical_requirement_id]
	if not rows:
		authz.not_found()
	row = rows[0]
	if not row.required_value_json:
		if value is None:
			fail("REQ_CONTROL_INVALID", "A required value must be supplied before this proposed characteristic can be confirmed.")
		ch = catalogue.CATALOGUE_BY_KEY.get(row.characteristic_key)
		if not ch:
			fail("REQ_CONTROL_INVALID", "Unknown characteristic.")
		try:
			normalised = catalogue.validate_value(ch, value, other_value=other_value)
		except catalogue.CatalogueValueError as exc:
			fail("REQ_CONTROL_INVALID", str(exc))
		row.required_value_json = json.dumps(normalised)
		row.required_value_display = catalogue.display_value(ch, normalised)
		if other_value:
			row.other_value = other_value
	row.row_status = "Confirmed"
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "updated", "row_id": technical_requirement_id, "package_version": package_version.name, "record_version": package_version.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="ConfirmProposedRequirement", payload=payload, result=result, document_type="IT Equipment Requirement Package Version", document_name=package_version.name, actor=actor)
	return result


# --- Warranty and support (package-level fields, not a row) ---


def save_warranty_and_support(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version = _load_for_row_command(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	for field_name in ("minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description"):
		if field_name in values:
			package_version.set(field_name, values[field_name])
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "saved", "package_version": package_version.name, "record_version": package_version.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="SaveWarrantyAndSupport", payload=payload, result=result, document_type="IT Equipment Requirement Package Version", document_name=package_version.name, actor=actor)
	return result


# --- Requisition Related Service ---


def add_related_service(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _add_row(requisition=requisition, table_field="related_services", id_field="service_requirement_id", id_prefix="SVC-", values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="AddRelatedService", user=user)


def update_related_service(*, requisition: str, service_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _update_row(requisition=requisition, table_field="related_services", id_field="service_requirement_id", row_id=service_requirement_id, values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="UpdateRelatedService", user=user)


def remove_related_service(*, requisition: str, service_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _remove_row(requisition=requisition, table_field="related_services", id_field="service_requirement_id", row_id=service_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="RemoveRelatedService", user=user)


# --- Requisition Acceptance Requirement ---


def add_acceptance_requirement(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _add_row(requisition=requisition, table_field="acceptance_requirements", id_field="acceptance_requirement_id", id_prefix="ACC-", values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="AddAcceptanceRequirement", user=user)


def update_acceptance_requirement(*, requisition: str, acceptance_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _update_row(requisition=requisition, table_field="acceptance_requirements", id_field="acceptance_requirement_id", row_id=acceptance_requirement_id, values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="UpdateAcceptanceRequirement", user=user)


def remove_acceptance_requirement(*, requisition: str, acceptance_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _remove_row(requisition=requisition, table_field="acceptance_requirements", id_field="acceptance_requirement_id", row_id=acceptance_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="RemoveAcceptanceRequirement", user=user)


# --- Requisition Supporting Material ---


def add_supporting_material(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.services import files

	file_check = files.check_file(values["file"])
	row_values = {**values, "file_digest": file_check["digest"], "file_check_result": file_check["check_result"]}
	return _add_row(requisition=requisition, table_field="supporting_materials", id_field="supporting_material_id", id_prefix="MAT-", values=row_values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="AddSupportingMaterial", user=user)


def update_supporting_material(*, requisition: str, supporting_material_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _update_row(requisition=requisition, table_field="supporting_materials", id_field="supporting_material_id", row_id=supporting_material_id, values=values, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="UpdateSupportingMaterial", user=user)


def remove_supporting_material(*, requisition: str, supporting_material_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _remove_row(requisition=requisition, table_field="supporting_materials", id_field="supporting_material_id", row_id=supporting_material_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key, command="RemoveSupportingMaterial", user=user)


# --------------------------------------------------------------------------
# ValidateRequisition — recompute deterministic findings; no lifecycle change.
# --------------------------------------------------------------------------


def validate_requisition(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = frappe.get_doc("Procurement Requisition", requisition)
	authz.require_draft_author_for_any(_contributing_units(root), actor)
	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	report = validation.validate(version=_version_dict(version), package=_package_dict(package_version), eligibility=projection)
	return {"ok": True, **report}
