# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §10.2 — Draft commands.

Creation (`PrepareITEquipmentRequisition`), the Request-details and
Requirements edits, the atomic same-specification item set, and the grouped
standard package (`SaveRequirementProposalDraft`, `ApplySelectedRequirementPackage`,
Reset standard values). Every command acts only on a Draft; locked Versions
are changed only by `lifecycle.py`/`authorise.py`.

Who may change what (§7.3A): each contributing department's Author/HoD edits
that department's own approved-requirement and equipment rows; shared request
and package content needs Draft authority in the lead department. Money and
quantity are exact (§5.14, `precision.py`).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import (
	catalogue,
	compatibility,
	eligibility_gateway,
	envelope,
	precision,
	records,
	references,
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT


def _next_id(prefix: str, existing: list[str]) -> str:
	seq = max([int(cstr(e)[len(prefix):]) for e in existing if cstr(e).startswith(prefix) and cstr(e)[len(prefix):].isdigit()] or [0]) + 1
	return f"{prefix}{seq:03d}"


def _journal(idempotency_key, command, payload, result, doc, actor):
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type=doc.doctype, document_name=doc.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# PrepareITEquipmentRequisition (§10.2, §5A, §7.4B)
# --------------------------------------------------------------------------


def _preparation_authority(actor: str, units: set[str]) -> tuple[str, str]:
	"""§5.2 — the exercised capacity and exact assignment at preparation."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	for role in (ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_DEPARTMENTAL_AUTHOR):
		for unit in sorted(units):
			decision = authorise_record(user=actor, business_role=role, organisation_unit=unit, purpose=PURPOSE_COMMAND)
			if decision.allowed:
				return role, authz.authority_snapshot(decision.assignment)
	return "", "{}"


def prepare_it_equipment_requisition(*, plan_item_id: str, idempotency_key: str, user: str | None = None, prior: dict[str, str] | None = None) -> dict[str, Any]:
	"""Create a fresh Draft, or return the authorised route to the one open
	Requisition already occupying this stable item. Nothing is created until
	every §5A check passes and the open slot is taken."""
	actor = authz.actor(user)
	payload = {"plan_item_id": plan_item_id, "prior": prior or {}}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	projection = eligibility_gateway.get_requisition_eligible_plan_item(plan_item_id)
	units = set(projection.get("contributing_org_unit_ids") or [])
	authz.require_draft_author_for_any(units, actor)

	existing = records.open_root_for(projection["plan_item_id"])
	if existing:
		readable = True
		try:
			authz.require_requisition_reader(actor, contributing_org_units=records.contributing_units(frappe.get_doc("Procurement Requisition", existing)))
		except frappe.DoesNotExistError:
			readable = False
		if not readable:
			fail("REQ_OPEN_EXISTS")
		root = frappe.get_doc("Procurement Requisition", existing)
		result = {"ok": True, "idempotent": False, "action": "existing", "requisition": root.name, "requisition_reference": root.requisition_reference, "current_state": root.current_state, "record_version": root.record_version}
		return _journal(idempotency_key, "PrepareITEquipmentRequisition", payload, result, root, actor)

	compatibility.require_compatible(projection)
	if not projection.get("eligible"):
		# §13.13 "Existing procurement scope" — an authorised original with
		# nothing left is a scope fact, not a generic ineligibility.
		if (projection.get("scope") or {}).get("locked"):
			fail("PLN_ITEM_SCOPE_LOCKED")
		fail("REQ_PLAN_INELIGIBLE")

	lines = []
	for i, source in enumerate(projection.get("sources", [])):
		remaining_qty = precision.planning_quantity(source.get("remaining_quantity") or "0")
		remaining_value = precision.parse_money(source.get("remaining_amount") or "0", allow_zero=True)
		if remaining_qty <= 0 or remaining_value <= 0:
			continue
		if source.get("organisation_unit") not in units:
			fail("REQ_DEPARTMENT_NOT_CONTRIBUTING")
		lines.append(
			{
				"drawdown_line_id": f"DL-{frappe.generate_hash(length=10)}",
				"plan_item_line_id": source["plan_item_line_id"], "source_line_id": source["source_line_id"],
				"contributing_org_unit": source["organisation_unit"],
				"approved_quantity": precision.quantity_text(precision.planning_quantity(source.get("approved_quantity") or "0")),
				"approved_value": precision.money_text(precision.parse_money(source.get("allocated_amount") or "0", allow_zero=True)),
				"remaining_quantity": precision.quantity_text(remaining_qty), "remaining_value": precision.money_text(remaining_value),
				# §14.3 — each line defaults to its full remaining balance.
				"requested_quantity": precision.quantity_text(remaining_qty), "requested_value": precision.money_text(remaining_value),
				"unit": source.get("unit") or precision.UNIT,
			}
		)
	if not lines:
		fail("REQ_PLAN_INELIGIBLE")

	capacity, authority = _preparation_authority(actor, units)
	rule = projection.get("reservation_rule") or {}
	county = projection.get("county_rule") or {}
	snapshot_ids = [s for s in (rule.get("snapshot_id"), county.get("snapshot_id") if projection.get("county_resident_reservation") else "") if s]

	# All or nothing: the open-slot guard may refuse after the root row exists.
	with envelope.atomic("prepare"):
		root = frappe.get_doc(
			{
				"doctype": "Procurement Requisition",
				"requisition_reference": references.requisition_reference(fiscal_year=projection["fiscal_year"], plan_item_id_value=projection["plan_item_id"]),
				"plan_id": projection.get("plan_id") or projection["plan_reference"], "plan_version_id": projection.get("plan_version_id") or projection["version_reference"],
				"plan_item_id": projection["plan_item_id"], "plan_item_version_id": projection.get("plan_item_version_id") or "",
				"strategic_objective_id": projection.get("strategic_objective_id") or projection.get("strategic_objective") or "",
				"strategic_objective_path": projection.get("strategic_objective_path") or "",
				"procurement_category": projection.get("procurement_category"), "plan_horizon": projection.get("plan_horizon"),
				"contributing_org_units": [{"organisation_unit": u} for u in sorted(units)],
				"lead_org_unit_id": records.default_lead(lines), "current_state": "Draft", "record_version": 0,
				"prior_requisition_id": (prior or {}).get("requisition") or None,
				"prior_requisition_version_id": (prior or {}).get("requisition_version") or None,
				"planning_correction_request_id": (prior or {}).get("correction_request") or "",
				"planning_correction_outcome_event_id": (prior or {}).get("outcome_event") or "",
			}
		).insert(ignore_permissions=True)
		records.occupy_slot(root, projection["plan_item_id"])

		package = frappe.get_doc(
			{
				"doctype": "IT Equipment Requirement Package", "requisition": root.name, "product_pattern": "IT Equipment",
				"reservation_category": projection.get("reservation_category") or "None",
				"county_resident_reservation": 1 if projection.get("county_resident_reservation") else 0,
				"reservation_rule_snapshot_ids": json.dumps(snapshot_ids), "lotting_indicator": projection.get("lotting_indicator"),
				"record_version": 0,
			}
		).insert(ignore_permissions=True)
		package_version = frappe.get_doc(
			{
				"doctype": "IT Equipment Requirement Package Version", "package": package.name, "version_number": 1,
				"version_status": "Draft", "catalogue_version": catalogue.CATALOGUE_VERSION,
				"standard_package_review_state": "Not generated", "service_location_constraint": "None", "record_version": 0,
			}
		).insert(ignore_permissions=True)
		package.current_version = package_version.name
		package.save(ignore_permissions=True)

		version = frappe.get_doc(
			{
				"doctype": "Requisition Version", "requisition": root.name, "version_number": 1, "version_status": "Draft",
				"requirement_title": (projection.get("title") or "")[:160], "related_services_required": 0,
				"package_version": package_version.name, "drawdown_lines": lines,
				"prepared_by": actor, "prepared_capacity": capacity, "prepared_authority_snapshot": authority, "record_version": 0,
			}
		).insert(ignore_permissions=True)
		root.current_version = version.name
		envelope.bump(root)

	result = {
		"ok": True, "idempotent": False, "action": "created", "requisition": root.name, "requisition_reference": root.requisition_reference,
		"requisition_version": version.name, "package_version": package_version.name, "record_version": root.record_version,
	}
	return _journal(idempotency_key, "PrepareITEquipmentRequisition", payload, result, root, actor)


# --------------------------------------------------------------------------
# Loading a Draft for a write
# --------------------------------------------------------------------------


def _draft_for_write(requisition: str, actor: str):
	root = records.require_root(requisition)
	scope = records.require_edit_units(root, actor)
	version = envelope.locked("Requisition Version", root.current_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)
	records.require_draft(version, package_version)
	return root, version, package_version, scope


def _refresh_lead(root, version) -> None:
	"""§7.3A — the derived default follows the Draft's drawn amounts unless a
	Head of Procurement Function directive fixed the lead."""
	if version.lead_routing_directive:
		return
	lead = records.default_lead(records.child_rows(version, "drawdown_lines"))
	if lead and lead != root.lead_org_unit_id:
		root.lead_org_unit_id = lead
		envelope.bump(root)


# --------------------------------------------------------------------------
# SaveRequisitionSummary — request information and amounts requested
# --------------------------------------------------------------------------


_SUMMARY_FIELDS = ("requirement_title", "delivery_location", "latest_delivery_date", "related_services_required")


def save_requisition_summary(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	envelope.check_record_version(version, expected_record_version)

	if any(field in values for field in _SUMMARY_FIELDS):
		records.require_shared(scope)
	if "requirement_title" in values:
		title = " ".join(cstr(values["requirement_title"]).split())
		if not (5 <= len(title) <= 160):
			fail("REQ_CONTROL_INVALID", "Enter a requirement title of 5–160 characters.", {"fields": {"requirement_title": "Enter a requirement title of 5–160 characters."}})
		version.requirement_title = title
	if "delivery_location" in values:
		location = cstr(values["delivery_location"]).strip()
		if location and cstr(frappe.db.get_value("Delivery Location", location, "status")) != "Active":
			fail("REQ_CONTROL_INVALID", "Select an active delivery location.", {"fields": {"delivery_location": "Select an active delivery location."}})
		version.delivery_location = location or None
	if "latest_delivery_date" in values:
		version.latest_delivery_date = cstr(values["latest_delivery_date"]).strip() or None
	if "related_services_required" in values:
		wanted = bool(values["related_services_required"])
		if not wanted and package_version.related_services:
			if not values.get("confirm_remove_services"):
				fail("REQ_CONTROL_INVALID", "Removing the related services needs your confirmation.", {"requires_confirmation": "remove_services", "services": len(package_version.related_services)})
			package_version.set("related_services", [])
			envelope.bump(package_version)
		version.related_services_required = 1 if wanted else 0

	posted = {cstr(r.get("drawdown_line_id")): r for r in values.get("drawdown_lines") or []}
	for line in version.drawdown_lines:
		row = posted.pop(line.drawdown_line_id, None)
		if row is None:
			continue
		records.require_unit(scope, line.contributing_org_unit)
		quantity = precision.parse_quantity(row.get("requested_quantity"), field="Requested quantity")
		value = precision.parse_money(row.get("requested_value"), field="Requested value")
		if quantity > precision.stored_quantity(line.remaining_quantity) or value > precision.stored_money(line.remaining_value):
			fail("REQ_BALANCE_CHANGED", detail={"drawdown_line_id": line.drawdown_line_id})
		line.requested_quantity = precision.quantity_text(quantity)
		line.requested_value = precision.money_text(value)
	if posted:
		authz.not_found()

	envelope.bump(version)
	_refresh_lead(root, version)
	result = {"ok": True, "idempotent": False, "action": "saved", "requisition_version": version.name, "record_version": version.record_version, "lead_org_unit_id": root.lead_org_unit_id}
	return _journal(idempotency_key, "SaveRequisitionSummary", payload, result, version, actor)


# --------------------------------------------------------------------------
# Equipment items — the same-specification set and single rows (§5.6)
# --------------------------------------------------------------------------


_SHARED_ITEM_FIELDS = ("equipment_category", "item_name", "delivery_location", "latest_delivery_date")


def _validate_shared_item(shared: dict[str, Any], version) -> dict[str, Any]:
	errors: dict[str, str] = {}
	category = cstr(shared.get("equipment_category"))
	if category not in catalogue.EQUIPMENT_CATEGORIES:
		errors["equipment_category"] = "Select a supported equipment category."
	name = " ".join(cstr(shared.get("item_name")).split())
	if not (3 <= len(name) <= 120):
		errors["item_name"] = "Enter an item name of 3–120 characters."
	location = cstr(shared.get("delivery_location")).strip() or cstr(version.delivery_location)
	if location and cstr(frappe.db.get_value("Delivery Location", location, "status")) != "Active":
		errors["delivery_location"] = "Select an active delivery location."
	latest = cstr(shared.get("latest_delivery_date")).strip() or cstr(version.latest_delivery_date)
	if latest and version.latest_delivery_date and latest > cstr(version.latest_delivery_date):
		errors["latest_delivery_date"] = "An item's delivery date cannot be later than the requisition's latest delivery date."
	if errors:
		fail("REQ_BATCH_ITEM_INVALID", "Correct the shared details. Nothing was created.", {"fields": errors})
	return {"equipment_category": category, "item_name": name, "delivery_location": location or None, "latest_delivery_date": latest or None}


def _generate_proposal(package_version) -> None:
	"""§6.4 — (re)generate the one complete editable proposal for the Draft's
	equipment: Proposed rows plus the visible support values, Review required.
	Confirmed rows are history the proposal never overwrites."""
	categories = [row.equipment_category for row in package_version.items]
	proposal = catalogue.proposal_for(categories)
	if not proposal["technical"] and not proposal["acceptance"]:
		return
	kept_technical = [r for r in package_version.technical_requirements if r.row_state != "Proposed"]
	kept_acceptance = [r for r in package_version.acceptance_requirements if r.row_state != "Proposed"]
	package_version.set("technical_requirements", kept_technical)
	package_version.set("acceptance_requirements", kept_acceptance)
	technical_ids = [r.technical_requirement_id for r in kept_technical]
	for row in proposal["technical"]:
		row_id = _next_id("TECH-", technical_ids)
		technical_ids.append(row_id)
		package_version.append("technical_requirements", _technical_values(row_id, row, "Proposed", len(technical_ids)))
	acceptance_ids = [r.acceptance_requirement_id for r in kept_acceptance]
	for row in proposal["acceptance"]:
		row_id = _next_id("ACC-", acceptance_ids)
		acceptance_ids.append(row_id)
		package_version.append("acceptance_requirements", {**_acceptance_values(row), "acceptance_requirement_id": row_id, "row_state": "Proposed", "row_order": len(acceptance_ids)})
	for field_name, value in proposal["support"].items():
		if package_version.get(field_name) in (None, "", 0) or field_name == "service_location_constraint" and package_version.get(field_name) in (None, "", "None"):
			package_version.set(field_name, value)
	package_version.standard_profile_key = proposal["profile_key"]
	package_version.standard_profile_version = proposal["profile_version"]
	package_version.proposal_digest = proposal["proposal_digest"]
	package_version.standard_package_review_state = "Review required"


def _technical_values(row_id: str, row: dict[str, Any], state: str, order: int) -> dict[str, Any]:
	ch = catalogue.CATALOGUE_BY_KEY[row["characteristic_key"]]
	return {
		"technical_requirement_id": row_id, "applies_to_scope": row.get("applies_to_scope") or "All items", "applies_to_id": row.get("applies_to_id") or "",
		"characteristic_key": ch.key, "comparison": ch.comparison, "unit": ch.unit,
		"required_value_json": json.dumps(row["value"]), "required_value_display": catalogue.display_value(ch, row["value"]),
		"other_value": row.get("other_value") or "", "mandatory": 1, "reason": row.get("reason") or "", "row_state": state, "row_order": order,
	}


def _acceptance_values(row: dict[str, Any]) -> dict[str, Any]:
	return {
		"applies_to_scope": row.get("applies_to_scope") or "All items", "applies_to_id": row.get("applies_to_id") or "",
		"check_type": row.get("check_type"), "pass_condition": " ".join(cstr(row.get("pass_condition")).split()),
		"evidence_type": row.get("evidence_type"), "other_evidence_name": row.get("other_evidence_name") or "",
	}


def add_same_specification_items(*, requisition: str, shared: dict[str, Any], rows: list[dict[str, Any]], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§5.6/§10.2 `AddSameSpecificationItems` — one shared definition, one
	source-linked item per selected positive row; every row or none."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "shared": shared, "rows": rows}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	values = _validate_shared_item(shared, version)

	lines = {line.drawdown_line_id: line for line in version.drawdown_lines}
	already: dict[str, int] = {}
	for item in package_version.items:
		already[item.drawdown_line_id] = already.get(item.drawdown_line_id, 0) + int(item.quantity or 0)
	errors: dict[str, str] = {}
	mismatches: list[str] = []
	prepared = []
	for row in rows or []:
		line_id = cstr(row.get("drawdown_line_id"))
		line = lines.get(line_id)
		if not line:
			errors[line_id] = "This approved requirement is not part of the requisition."
			continue
		if line.contributing_org_unit not in scope["units"]:
			errors[line_id] = "You can add equipment only for your own department."
			continue
		try:
			quantity = int(precision.parse_quantity(row.get("quantity"), field="Quantity"))
		except frappe.ValidationError:
			errors[line_id] = "Enter a whole-number quantity above zero."
			continue
		wanted = int(precision.stored_quantity(line.requested_quantity)) - already.get(line_id, 0)
		if quantity != wanted:
			name = records.unit_name(line.contributing_org_unit)
			errors[line_id] = f"Must be {wanted:,} Each" if wanted > 0 else f"{name} already has equipment for its full requested quantity."
			if wanted > 0:
				mismatches.append(f"Requested equipment quantity for {name} is {quantity:,} Each but the approved requirement requests {wanted:,} Each")
			continue
		intended = " ".join(cstr(row.get("intended_use")).split())
		if not (10 <= len(intended) <= 500):
			errors[line_id] = "Describe the intended use in 10–500 characters."
			continue
		prepared.append((line, quantity, intended))
	if errors or not prepared:
		fail("REQ_BATCH_ITEM_INVALID", "; ".join(mismatches), detail={"rows": errors or {"": "Select at least one approved requirement."}})

	ids = [item.requisition_item_id for item in package_version.items]
	created = []
	for line, quantity, intended in prepared:
		item_id = _next_id("RQI-", ids)
		ids.append(item_id)
		package_version.append(
			"items",
			{
				"requisition_item_id": item_id, "drawdown_line_id": line.drawdown_line_id, "plan_item_line_id": line.plan_item_line_id,
				"quantity": quantity, "unit": precision.UNIT, "intended_use": intended, "row_order": len(ids), **values,
			},
		)
		created.append(item_id)
	_generate_proposal(package_version)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "added", "items": created, "package_version": package_version.name, "record_version": package_version.record_version, "review_state": package_version.standard_package_review_state}
	return _journal(idempotency_key, "AddSameSpecificationItems", payload, result, package_version, actor)


def update_shared_item_details(*, requisition: str, requisition_item_ids: list[str], shared: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§10.2 `UpdateSharedItemDetails` — category, name, location and date
	across the named same-specification items together; never source,
	quantity or intended use. A category change regenerates the proposal."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "requisition_item_ids": requisition_item_ids, "shared": shared}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	records.require_shared(scope)
	envelope.check_record_version(package_version, expected_record_version)
	values = _validate_shared_item(shared, version)
	wanted = set(requisition_item_ids or [])
	items = [item for item in package_version.items if item.requisition_item_id in wanted]
	if not items or len(items) != len(wanted):
		fail("REQ_BATCH_ITEM_INVALID", detail={"rows": {i: "Not found" for i in wanted - {item.requisition_item_id for item in items}}})
	category_changed = any(item.equipment_category != values["equipment_category"] for item in items)
	for item in items:
		for field_name in _SHARED_ITEM_FIELDS:
			item.set(field_name, values[field_name])
	if category_changed:
		_generate_proposal(package_version)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "updated", "items": sorted(wanted), "record_version": package_version.record_version, "review_state": package_version.standard_package_review_state}
	return _journal(idempotency_key, "UpdateSharedItemDetails", payload, result, package_version, actor)


def update_requisition_item(*, requisition: str, requisition_item_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""Edit quantity and intended use of one source-linked item only."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "requisition_item_id": requisition_item_id, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	item = next((i for i in package_version.items if i.requisition_item_id == requisition_item_id), None)
	if not item:
		authz.not_found()
	line = next((l for l in version.drawdown_lines if l.drawdown_line_id == item.drawdown_line_id), None)
	records.require_unit(scope, line.contributing_org_unit if line else "")
	if "quantity" in values:
		item.quantity = int(precision.parse_quantity(values["quantity"], field="Quantity"))
	if "intended_use" in values:
		intended = " ".join(cstr(values["intended_use"]).split())
		if not (10 <= len(intended) <= 500):
			fail("REQ_CONTROL_INVALID", "Describe the intended use in 10–500 characters.", {"fields": {"intended_use": "Describe the intended use in 10–500 characters."}})
		item.intended_use = intended
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "updated", "row_id": requisition_item_id, "record_version": package_version.record_version}
	return _journal(idempotency_key, "UpdateRequisitionItem", payload, result, package_version, actor)


def _item_is_referenced(package_version, item_id: str) -> bool:
	for table_field in ("technical_requirements", "related_services", "acceptance_requirements"):
		for row in package_version.get(table_field):
			if row.get("applies_to_scope") == "Item" and row.get("applies_to_id") == item_id:
				return True
	return any(item_id in records.json_list(m.linked_requirement_ids_json) for m in package_version.supporting_materials)


def remove_requisition_item(*, requisition: str, requisition_item_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "requisition_item_id": requisition_item_id}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	envelope.check_record_version(package_version, expected_record_version)
	item = next((i for i in package_version.items if i.requisition_item_id == requisition_item_id), None)
	if not item:
		authz.not_found()
	line = next((l for l in version.drawdown_lines if l.drawdown_line_id == item.drawdown_line_id), None)
	records.require_unit(scope, line.contributing_org_unit if line else "")
	if _item_is_referenced(package_version, requisition_item_id):
		fail("REQ_CONTROL_INVALID", "This equipment row is linked to requirements, services, acceptance checks or files. Remove those links first.")
	package_version.set("items", [i for i in package_version.items if i.requisition_item_id != requisition_item_id])
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "removed", "row_id": requisition_item_id, "record_version": package_version.record_version}
	return _journal(idempotency_key, "RemoveRequisitionItem", payload, result, package_version, actor)


# --------------------------------------------------------------------------
# The standard requirement package (§6.4)
# --------------------------------------------------------------------------


def _visible_technical(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out = []
	for row in rows or []:
		if not row.get("selected", True):
			continue
		ch = catalogue.CATALOGUE_BY_KEY.get(cstr(row.get("characteristic_key")))
		if not ch:
			fail("REQ_CONTROL_INVALID", "Unknown characteristic.", {"characteristic_key": row.get("characteristic_key")})
		try:
			value = catalogue.validate_value(ch, row.get("value"), other_value=cstr(row.get("other_value")))
		except catalogue.CatalogueValueError as exc:
			fail("REQ_CONTROL_INVALID", str(exc), {"fields": {ch.key: str(exc)}})
		out.append({**row, "characteristic_key": ch.key, "value": value})
	return out


def _visible_acceptance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	out = []
	for row in rows or []:
		if not row.get("selected", True):
			continue
		if row.get("check_type") not in catalogue.ACCEPTANCE_CHECK_TYPES or row.get("evidence_type") not in catalogue.ACCEPTANCE_EVIDENCE_TYPES:
			fail("REQ_CONTROL_INVALID", "Select a released check and evidence type.")
		condition = " ".join(cstr(row.get("pass_condition")).split())
		if not (10 <= len(condition) <= 500) or validation.is_subjective(condition):
			fail("REQ_CONTROL_INVALID", "State an observable pass condition of 10–500 characters.", {"fields": {"pass_condition": "State an observable pass condition of 10–500 characters."}})
		if row.get("evidence_type") == "Other stated record" and not (3 <= len(cstr(row.get("other_evidence_name")).strip()) <= 120):
			fail("REQ_CONTROL_INVALID", "Name the other evidence record.")
		out.append(row)
	return out


def _write_package_rows(package_version, technical, acceptance, state: str) -> None:
	kept_technical = [r for r in package_version.technical_requirements if r.row_state != "Proposed"] if state == "Proposed" else []
	kept_acceptance = [r for r in package_version.acceptance_requirements if r.row_state != "Proposed"] if state == "Proposed" else []
	package_version.set("technical_requirements", kept_technical)
	package_version.set("acceptance_requirements", kept_acceptance)
	technical_ids = [r.technical_requirement_id for r in kept_technical]
	for row in technical:
		row_id = row.get("technical_requirement_id") if row.get("technical_requirement_id") and row.get("technical_requirement_id") not in technical_ids else _next_id("TECH-", technical_ids)
		technical_ids.append(row_id)
		package_version.append("technical_requirements", _technical_values(row_id, row, state, len(technical_ids)))
	acceptance_ids = [r.acceptance_requirement_id for r in kept_acceptance]
	for row in acceptance:
		row_id = row.get("acceptance_requirement_id") if row.get("acceptance_requirement_id") and row.get("acceptance_requirement_id") not in acceptance_ids else _next_id("ACC-", acceptance_ids)
		acceptance_ids.append(row_id)
		package_version.append("acceptance_requirements", {**_acceptance_values(row), "acceptance_requirement_id": row_id, "row_state": state, "row_order": len(acceptance_ids)})


def _require_current_proposal(package_version, proposal_digest: str, profile_key: str, profile_version: str) -> None:
	if package_version.standard_package_review_state != "Review required":
		fail("REQ_STANDARD_PROPOSAL_STALE", "There is no standard proposal waiting for review.")
	if (cstr(proposal_digest), cstr(profile_key), cstr(profile_version)) != (cstr(package_version.proposal_digest), cstr(package_version.standard_profile_key), cstr(package_version.standard_profile_version)):
		fail("REQ_STANDARD_PROPOSAL_STALE")


def save_requirement_proposal_draft(*, requisition: str, proposal_digest: str, technical: list[dict[str, Any]], acceptance: list[dict[str, Any]], support: dict[str, Any], expected_record_version, idempotency_key: str, profile_key: str = "", profile_version: str = "", user: str | None = None) -> dict[str, Any]:
	"""§6.4 Save draft — persists the visible suggestions as Proposed rows and
	the visible support values. Review required remains; nothing confirms."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "proposal_digest": proposal_digest, "technical": technical, "acceptance": acceptance, "support": support}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	records.require_shared(scope)
	envelope.check_record_version(package_version, expected_record_version)
	_require_current_proposal(package_version, proposal_digest, profile_key or package_version.standard_profile_key, profile_version or package_version.standard_profile_version)
	_write_package_rows(package_version, _visible_technical(technical), _visible_acceptance(acceptance), "Proposed")
	_apply_support(package_version, support)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "saved", "record_version": package_version.record_version, "review_state": package_version.standard_package_review_state}
	return _journal(idempotency_key, "SaveRequirementProposalDraft", payload, result, package_version, actor)


def apply_selected_requirement_package(*, requisition: str, profile_key: str, profile_version: str, proposal_digest: str, technical: list[dict[str, Any]], acceptance: list[dict[str, Any]], support: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§10.2 `ApplySelectedRequirementPackage` — the complete visible selected
	payload is validated together and recorded as Confirmed, and the package
	marked Reviewed, or nothing changes."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "profile_key": profile_key, "profile_version": profile_version, "proposal_digest": proposal_digest, "technical": technical, "acceptance": acceptance, "support": support}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	records.require_shared(scope)
	envelope.check_record_version(package_version, expected_record_version)
	_require_current_proposal(package_version, proposal_digest, profile_key, profile_version)
	selected_technical = _visible_technical(technical)
	selected_acceptance = _visible_acceptance(acceptance)
	if not selected_acceptance:
		fail("REQ_CONTROL_INVALID", "Keep at least one objective acceptance check.", {"fields": {"acceptance": "Keep at least one objective acceptance check."}})
	_apply_support(package_version, support, complete=True)
	# Confirmed rows the user already had stay; the proposal's rows replace
	# only the Proposed ones (§6.4 "without overwriting confirmed history").
	_write_package_rows(package_version, selected_technical, selected_acceptance, "Proposed")
	for row in package_version.technical_requirements:
		row.row_state = "Confirmed"
	for row in package_version.acceptance_requirements:
		row.row_state = "Confirmed"
	package_version.standard_package_review_state = "Reviewed"
	envelope.bump(package_version)
	result = {
		"ok": True, "idempotent": False, "action": "applied", "record_version": package_version.record_version, "review_state": "Reviewed",
		"technical": len(package_version.technical_requirements), "acceptance": len(package_version.acceptance_requirements),
	}
	return _journal(idempotency_key, "ApplySelectedRequirementPackage", payload, result, package_version, actor)


def reset_standard_values(*, requisition: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""Restore the visible code-owned proposal; it stays Review required."""
	actor = authz.actor(user)
	payload = {"requisition": requisition}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	records.require_shared(scope)
	envelope.check_record_version(package_version, expected_record_version)
	for field_name in catalogue.STANDARD_SUPPORT:
		package_version.set(field_name, None if field_name != "service_location_constraint" else "None")
	_generate_proposal(package_version)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "reset", "record_version": package_version.record_version, "review_state": package_version.standard_package_review_state}
	return _journal(idempotency_key, "ResetStandardValues", payload, result, package_version, actor)


# --- Warranty and support (package-level fields) ---


_SUPPORT_FIELDS = ("minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description")
_SERVICE_LOCATIONS = ("None", "Within Kenya", "At delivery location")


def _apply_support(package_version, values: dict[str, Any], *, complete: bool = False) -> None:
	values = dict(values or {})
	errors: dict[str, str] = {}
	onsite = bool(values.get("onsite_support_required", package_version.onsite_support_required))

	def _int(name: str, low: int, high: int, message: str):
		raw = values.get(name)
		if raw in (None, ""):
			if complete:
				errors[name] = message
			return None
		if isinstance(raw, (bool, float)):
			errors[name] = message
			return None
		try:
			number = int(str(raw).strip())
		except ValueError:
			errors[name] = message
			return None
		if not (low <= number <= high):
			errors[name] = message
		return number

	if "minimum_warranty_months" in values or complete:
		values["minimum_warranty_months"] = _int("minimum_warranty_months", 1, 120, "Enter the minimum warranty in months.")
	if onsite and ("maximum_support_response_hours" in values or complete):
		values["maximum_support_response_hours"] = _int("maximum_support_response_hours", 1, 168, "Enter the maximum support response in hours (1–168).")
	elif not onsite:
		values["maximum_support_response_hours"] = None
	if "service_location_constraint" in values and values["service_location_constraint"] not in _SERVICE_LOCATIONS:
		errors["service_location_constraint"] = "Select the service location constraint."
	if len(cstr(values.get("support_description"))) > 500:
		errors["support_description"] = "Support description must be 500 characters or fewer."
	if errors:
		fail("REQ_CONTROL_INVALID", next(iter(errors.values())), {"fields": errors})
	for name in _SUPPORT_FIELDS:
		if name in values:
			value = values[name]
			if name in ("onsite_support_required", "manufacturer_support_required"):
				value = 1 if value else 0
			package_version.set(name, value)


def save_warranty_and_support(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	records.require_shared(scope)
	envelope.check_record_version(package_version, expected_record_version)
	_apply_support(package_version, values)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "action": "saved", "record_version": package_version.record_version}
	return _journal(idempotency_key, "SaveWarrantyAndSupport", payload, result, package_version, actor)


# --------------------------------------------------------------------------
# Single-row CRUD for the remaining Requirements rows
# --------------------------------------------------------------------------


def _row_command(*, requisition, table_field, id_field, id_prefix, command, idempotency_key, expected_record_version, user, payload, mutate):
	actor = authz.actor(user)
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version, package_version, scope = _draft_for_write(requisition, actor)
	records.require_shared(scope)
	envelope.check_record_version(package_version, expected_record_version)
	row_id = mutate(package_version, version)
	envelope.bump(package_version)
	result = {"ok": True, "idempotent": False, "row_id": row_id, "package_version": package_version.name, "record_version": package_version.record_version}
	return _journal(idempotency_key, command, payload, result, package_version, actor)


def _target(values: dict[str, Any], package_version, *, allow_service: bool = False) -> tuple[str, str]:
	scope = cstr(values.get("applies_to_scope") or "All items")
	target = cstr(values.get("applies_to_id"))
	if scope == "All items":
		return scope, ""
	if scope == "Item" and any(i.requisition_item_id == target for i in package_version.items):
		return scope, target
	if allow_service and scope == "Service" and any(s.service_requirement_id == target for s in package_version.related_services):
		return scope, target
	fail("REQ_CONTROL_INVALID", "Select what this row applies to.", {"fields": {"applies_to": "Select what this row applies to."}})
	return "", ""


def add_technical_requirement(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""A deliberate manual Add creates a Confirmed Draft row; it confirms no
	Proposed row (§10.2)."""

	def mutate(package_version, version):
		scope, target = _target(values, package_version)
		row = _visible_technical([{**values, "selected": True}])[0]
		ids = [r.technical_requirement_id for r in package_version.technical_requirements]
		row_id = _next_id("TECH-", ids)
		package_version.append("technical_requirements", _technical_values(row_id, {**row, "applies_to_scope": scope, "applies_to_id": target}, "Confirmed", len(ids) + 1))
		return row_id

	return _row_command(requisition=requisition, table_field="technical_requirements", id_field="technical_requirement_id", id_prefix="TECH-", command="AddTechnicalRequirement", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "values": values}, mutate=mutate)


def update_technical_requirement(*, requisition: str, technical_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(package_version, version):
		existing = next((r for r in package_version.technical_requirements if r.technical_requirement_id == technical_requirement_id), None)
		if not existing:
			authz.not_found()
		scope, target = _target({"applies_to_scope": values.get("applies_to_scope", existing.applies_to_scope), "applies_to_id": values.get("applies_to_id", existing.applies_to_id)}, package_version)
		row = _visible_technical([{**values, "characteristic_key": existing.characteristic_key, "selected": True}])[0]
		fresh = _technical_values(existing.technical_requirement_id, {**row, "applies_to_scope": scope, "applies_to_id": target}, existing.row_state, existing.row_order)
		for field_name, value in fresh.items():
			existing.set(field_name, value)
		return existing.technical_requirement_id

	return _row_command(requisition=requisition, table_field="technical_requirements", id_field="technical_requirement_id", id_prefix="TECH-", command="UpdateTechnicalRequirement", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": technical_requirement_id, "values": values}, mutate=mutate)


def _remove(table_field: str, id_field: str, row_id: str):
	def mutate(package_version, version):
		rows = package_version.get(table_field)
		kept = [r for r in rows if r.get(id_field) != row_id]
		if len(kept) == len(rows):
			authz.not_found()
		package_version.set(table_field, kept)
		return row_id

	return mutate


def remove_technical_requirement(*, requisition: str, technical_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _row_command(requisition=requisition, table_field="technical_requirements", id_field="technical_requirement_id", id_prefix="TECH-", command="RemoveTechnicalRequirement", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": technical_requirement_id}, mutate=_remove("technical_requirements", "technical_requirement_id", technical_requirement_id))


def _service_values(values: dict[str, Any], package_version, version) -> dict[str, Any]:
	scope, target = _target(values, package_version)
	errors = {}
	if values.get("service_type") not in catalogue.SERVICE_TYPES:
		errors["service_type"] = "Select a service type."
	result = " ".join(cstr(values.get("required_result")).split())
	if not (10 <= len(result) <= 500):
		errors["required_result"] = "Describe the required result in 10–500 characters."
	coverage = cstr(values.get("quantity_or_coverage")).strip()
	if not (1 <= len(coverage) <= 120):
		errors["quantity_or_coverage"] = "Enter the quantity or coverage."
	completion = cstr(values.get("completion_date")).strip()
	if not completion:
		errors["completion_date"] = "Enter the completion date."
	elif version.latest_delivery_date and completion > cstr(version.latest_delivery_date):
		errors["completion_date"] = "The completion date cannot be later than the latest delivery date."
	if values.get("acceptance_evidence") not in catalogue.SERVICE_ACCEPTANCE_EVIDENCE:
		errors["acceptance_evidence"] = "Select the acceptance evidence."
	other = cstr(values.get("other_evidence_name")).strip()
	if values.get("acceptance_evidence") == "Other stated record" and not (3 <= len(other) <= 120):
		errors["other_evidence_name"] = "Name the other evidence record."
	if errors:
		fail("REQ_CONTROL_INVALID", next(iter(errors.values())), {"fields": errors})
	return {"service_type": values["service_type"], "applies_to_scope": scope, "applies_to_id": target, "required_result": result, "quantity_or_coverage": coverage, "completion_date": completion, "acceptance_evidence": values["acceptance_evidence"], "other_evidence_name": other}


def add_related_service(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(package_version, version):
		if not version.related_services_required:
			fail("REQ_CONTROL_INVALID", "Change Related services required to Yes before adding a service.")
		ids = [r.service_requirement_id for r in package_version.related_services]
		row_id = _next_id("SVC-", ids)
		package_version.append("related_services", {**_service_values(values, package_version, version), "service_requirement_id": row_id, "row_order": len(ids) + 1})
		return row_id

	return _row_command(requisition=requisition, table_field="related_services", id_field="service_requirement_id", id_prefix="SVC-", command="AddRelatedService", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "values": values}, mutate=mutate)


def update_related_service(*, requisition: str, service_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(package_version, version):
		row = next((r for r in package_version.related_services if r.service_requirement_id == service_requirement_id), None)
		if not row:
			authz.not_found()
		for field_name, value in _service_values(values, package_version, version).items():
			row.set(field_name, value)
		return service_requirement_id

	return _row_command(requisition=requisition, table_field="related_services", id_field="service_requirement_id", id_prefix="SVC-", command="UpdateRelatedService", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": service_requirement_id, "values": values}, mutate=mutate)


def remove_related_service(*, requisition: str, service_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _row_command(requisition=requisition, table_field="related_services", id_field="service_requirement_id", id_prefix="SVC-", command="RemoveRelatedService", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": service_requirement_id}, mutate=_remove("related_services", "service_requirement_id", service_requirement_id))


def add_acceptance_requirement(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(package_version, version):
		scope, target = _target(values, package_version, allow_service=True)
		row = _visible_acceptance([{**values, "selected": True}])[0]
		ids = [r.acceptance_requirement_id for r in package_version.acceptance_requirements]
		row_id = _next_id("ACC-", ids)
		package_version.append("acceptance_requirements", {**_acceptance_values({**row, "applies_to_scope": scope, "applies_to_id": target}), "acceptance_requirement_id": row_id, "row_state": "Confirmed", "row_order": len(ids) + 1})
		return row_id

	return _row_command(requisition=requisition, table_field="acceptance_requirements", id_field="acceptance_requirement_id", id_prefix="ACC-", command="AddAcceptanceRequirement", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "values": values}, mutate=mutate)


def update_acceptance_requirement(*, requisition: str, acceptance_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(package_version, version):
		row = next((r for r in package_version.acceptance_requirements if r.acceptance_requirement_id == acceptance_requirement_id), None)
		if not row:
			authz.not_found()
		scope, target = _target({"applies_to_scope": values.get("applies_to_scope", row.applies_to_scope), "applies_to_id": values.get("applies_to_id", row.applies_to_id)}, package_version, allow_service=True)
		fresh = _visible_acceptance([{"check_type": row.check_type, "evidence_type": row.evidence_type, "pass_condition": row.pass_condition, "other_evidence_name": row.other_evidence_name, **values, "selected": True}])[0]
		for field_name, value in _acceptance_values({**fresh, "applies_to_scope": scope, "applies_to_id": target}).items():
			row.set(field_name, value)
		return acceptance_requirement_id

	return _row_command(requisition=requisition, table_field="acceptance_requirements", id_field="acceptance_requirement_id", id_prefix="ACC-", command="UpdateAcceptanceRequirement", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": acceptance_requirement_id, "values": values}, mutate=mutate)


def remove_acceptance_requirement(*, requisition: str, acceptance_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _row_command(requisition=requisition, table_field="acceptance_requirements", id_field="acceptance_requirement_id", id_prefix="ACC-", command="RemoveAcceptanceRequirement", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": acceptance_requirement_id}, mutate=_remove("acceptance_requirements", "acceptance_requirement_id", acceptance_requirement_id))


def _material_values(values: dict[str, Any], package_version) -> dict[str, Any]:
	errors = {}
	title = " ".join(cstr(values.get("title")).split())
	if not (3 <= len(title) <= 160):
		errors["title"] = "Enter a title of 3–160 characters."
	if values.get("document_type") not in catalogue.SUPPORTING_MATERIAL_TYPES:
		errors["document_type"] = "Select the document type."
	other_type = cstr(values.get("other_document_type")).strip()
	if values.get("document_type") == "Other supporting material" and not (3 <= len(other_type) <= 80):
		errors["other_document_type"] = "Name the document type."
	purpose = " ".join(cstr(values.get("purpose")).split())
	if not (10 <= len(purpose) <= 300):
		errors["purpose"] = "Describe the purpose in 10–300 characters."
	treatment = values.get("treatment")
	if treatment not in ("Informational", "Forms part of requirement"):
		errors["treatment"] = "Select how the file is treated."
	linked = list(values.get("linked_requirement_ids") or [])
	structured = {r.technical_requirement_id for r in package_version.technical_requirements} | {r.service_requirement_id for r in package_version.related_services} | {r.acceptance_requirement_id for r in package_version.acceptance_requirements}
	if treatment == "Forms part of requirement" and (not linked or any(l not in structured for l in linked)):
		errors["linked_requirement_ids"] = "Link the file to at least one structured requirement."
	version_label = cstr(values.get("document_version")).strip()
	if not version_label or len(version_label) > 40:
		errors["document_version"] = "Enter the document version."
	if errors:
		fail("REQ_CONTROL_INVALID", next(iter(errors.values())), {"fields": errors})
	return {"title": title, "document_type": values["document_type"], "other_document_type": other_type, "purpose": purpose, "treatment": treatment, "linked_requirement_ids_json": json.dumps(linked), "document_version": version_label}


def add_supporting_material(*, requisition: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.services import files

	def mutate(package_version, version):
		checked = files.check_file(values.get("file"))
		ids = [r.supporting_material_id for r in package_version.supporting_materials]
		row_id = _next_id("MAT-", ids)
		package_version.append("supporting_materials", {**_material_values(values, package_version), "supporting_material_id": row_id, "file": values.get("file"), "file_digest": checked["digest"], "file_check_result": checked["check_result"]})
		return row_id

	return _row_command(requisition=requisition, table_field="supporting_materials", id_field="supporting_material_id", id_prefix="MAT-", command="AddSupportingMaterial", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "values": values}, mutate=mutate)


def update_supporting_material(*, requisition: str, supporting_material_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(package_version, version):
		row = next((r for r in package_version.supporting_materials if r.supporting_material_id == supporting_material_id), None)
		if not row:
			authz.not_found()
		current = {"title": row.title, "document_type": row.document_type, "other_document_type": row.other_document_type, "purpose": row.purpose, "treatment": row.treatment, "linked_requirement_ids": records.json_list(row.linked_requirement_ids_json), "document_version": row.document_version}
		for field_name, value in _material_values({**current, **values}, package_version).items():
			row.set(field_name, value)
		return supporting_material_id

	return _row_command(requisition=requisition, table_field="supporting_materials", id_field="supporting_material_id", id_prefix="MAT-", command="UpdateSupportingMaterial", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": supporting_material_id, "values": values}, mutate=mutate)


def remove_supporting_material(*, requisition: str, supporting_material_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	return _row_command(requisition=requisition, table_field="supporting_materials", id_field="supporting_material_id", id_prefix="MAT-", command="RemoveSupportingMaterial", idempotency_key=idempotency_key, expected_record_version=expected_record_version, user=user, payload={"requisition": requisition, "row": supporting_material_id}, mutate=_remove("supporting_materials", "supporting_material_id", supporting_material_id))


# --------------------------------------------------------------------------
# ValidateRequisition — findings and preview digest; no lifecycle change
# --------------------------------------------------------------------------


def validate_requisition(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_requisitions.services import digest

	actor = authz.actor(user)
	root = records.require_root(requisition, lock=False)
	authz.require_requisition_reader(actor, contributing_org_units=records.contributing_units(root))
	root, version, package_version = records.load(requisition)
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	report = validation.validate(version=records.version_dict(version), package=records.package_dict(package_version), eligibility=projection)
	return {"ok": True, **report, "preview_digest": digest.sha256_hex(records.digest_payload(version, package_version)), "evaluated_at": cstr(now_datetime())}
