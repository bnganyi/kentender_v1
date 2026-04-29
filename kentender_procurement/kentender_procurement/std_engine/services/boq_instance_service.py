from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.stale_output_service import mark_std_outputs_stale


def _instance(instance_code: str):
	name = frappe.db.get_value("STD Instance", {"instance_code": instance_code}, "name")
	if not name:
		frappe.throw(_("STD instance not found."), title=_("Invalid instance"))
	return frappe.get_doc("STD Instance", name)


def _block_if_locked(instance):
	if instance.instance_status in {"Published Locked", "Superseded", "Cancelled"}:
		frappe.throw(_("Published BOQ edit denied."), title=_("Instance locked"))


def _invalidate_outputs(instance_code: str) -> list[str]:
	outputs = frappe.get_all(
		"STD Generated Output",
		filters={"instance_code": instance_code, "status": ("in", ["Current", "Published"])},
		fields=["name", "output_code"],
		limit=200,
	)
	codes = []
	for row in outputs:
		doc = frappe.get_doc("STD Generated Output", row["name"])
		frappe.flags.std_transition_service_context = True
		try:
			doc.status = "Draft"
			doc.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False
		codes.append(row["output_code"])
	return codes


@frappe.whitelist()
def create_or_initialize_boq_instance(instance_code: str, actor: str) -> dict[str, Any]:
	instance = _instance(instance_code)
	profile = frappe.get_doc("STD Applicability Profile", instance.profile_code)
	if not int(profile.requires_boq or 0):
		frappe.throw(_("BOQ is not required for this profile."), title=_("BOQ not required"))
	existing = frappe.db.get_value("STD BOQ Instance", {"instance_code": instance_code}, "name")
	if existing:
		doc = frappe.get_doc("STD BOQ Instance", existing)
		return {"boq_instance_code": doc.boq_instance_code, "status": doc.status}

	defn = frappe.db.get_value(
		"STD BOQ Definition",
		{"version_code": instance.template_version_code},
		["boq_definition_code"],
		as_dict=True,
	)
	if not defn:
		frappe.throw(_("BOQ definition missing for template version."), title=_("Missing BOQ definition"))
	doc = frappe.get_doc(
		{
			"doctype": "STD BOQ Instance",
			"boq_instance_code": f"SBI-{frappe.generate_hash(length=10).upper()}",
			"instance_code": instance_code,
			"boq_definition_code": defn.boq_definition_code,
			"status": "Draft",
			"validation_status": "Not Run",
		}
	).insert(ignore_permissions=True)
	return {"boq_instance_code": doc.boq_instance_code, "status": doc.status}


@frappe.whitelist()
def add_boq_bill(instance_code: str, bill_payload: dict, actor: str) -> dict[str, Any]:
	instance = _instance(instance_code)
	_block_if_locked(instance)
	boq = create_or_initialize_boq_instance(instance_code, actor)
	doc = frappe.get_doc(
		{
			"doctype": "STD BOQ Bill Instance",
			"bill_instance_code": f"SBBI-{frappe.generate_hash(length=10).upper()}",
			"boq_instance_code": boq["boq_instance_code"],
			"bill_number": bill_payload.get("bill_number"),
			"bill_title": bill_payload.get("bill_title"),
			"bill_type": bill_payload.get("bill_type", "Work Items"),
			"order_index": int(bill_payload.get("order_index", 1)),
		}
	).insert(ignore_permissions=True)
	mark_std_outputs_stale(instance.instance_code, "boq_item_quantity", actor=actor)
	frappe.flags.std_transition_service_context = True
	try:
		instance.readiness_status = "Invalidated"
		instance.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False
	return {"bill_instance_code": doc.bill_instance_code}


@frappe.whitelist()
def add_boq_item(bill_instance_code: str, item_payload: dict, actor: str) -> dict[str, Any]:
	bill_name = frappe.db.get_value("STD BOQ Bill Instance", {"bill_instance_code": bill_instance_code}, "name")
	if not bill_name:
		frappe.throw(_("BOQ bill instance not found."), title=_("Invalid bill"))
	bill = frappe.get_doc("STD BOQ Bill Instance", bill_name)
	boq = frappe.get_doc("STD BOQ Instance", {"boq_instance_code": bill.boq_instance_code})
	instance = _instance(boq.instance_code)
	_block_if_locked(instance)
	quantity = float(item_payload.get("quantity", 0))
	if quantity < 0:
		frappe.throw(_("Negative quantity rejected."), title=_("Invalid quantity"))
	rate = float(item_payload.get("rate", 0) or 0)
	amount = quantity * rate
	doc = frappe.get_doc(
		{
			"doctype": "STD BOQ Item Instance",
			"item_instance_code": f"SBII-{frappe.generate_hash(length=10).upper()}",
			"bill_instance_code": bill_instance_code,
			"item_number": item_payload.get("item_number"),
			"description": item_payload.get("description"),
			"unit": item_payload.get("unit"),
			"quantity": quantity,
			"rate": rate,
			"amount": amount,
			"payload_json": json.dumps(item_payload),
		}
	).insert(ignore_permissions=True)
	mark_std_outputs_stale(instance.instance_code, "boq_item_quantity", actor=actor)
	frappe.flags.std_transition_service_context = True
	try:
		instance.readiness_status = "Invalidated"
		instance.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False
	_invalidate_outputs(instance.instance_code)
	record_std_audit_event("BOQ_UPDATED", "STD_INSTANCE", instance.instance_code, actor=actor)
	return {"item_instance_code": doc.item_instance_code, "amount": amount}


@frappe.whitelist()
def update_boq_item(item_instance_code: str, payload: dict, actor: str) -> dict[str, Any]:
	name = frappe.db.get_value("STD BOQ Item Instance", {"item_instance_code": item_instance_code}, "name")
	if not name:
		frappe.throw(_("BOQ item instance not found."), title=_("Invalid item"))
	doc = frappe.get_doc("STD BOQ Item Instance", name)
	bill = frappe.get_doc("STD BOQ Bill Instance", {"bill_instance_code": doc.bill_instance_code})
	boq = frappe.get_doc("STD BOQ Instance", {"boq_instance_code": bill.boq_instance_code})
	instance = _instance(boq.instance_code)
	_block_if_locked(instance)
	quantity = float(payload.get("quantity", doc.quantity))
	if quantity < 0:
		frappe.throw(_("Negative quantity rejected."), title=_("Invalid quantity"))
	doc.quantity = quantity
	doc.rate = float(payload.get("rate", doc.rate or 0) or 0)
	doc.amount = float(doc.quantity or 0) * float(doc.rate or 0)
	doc.payload_json = json.dumps(payload)
	doc.save(ignore_permissions=True)
	mark_std_outputs_stale(instance.instance_code, "boq_item_quantity", actor=actor)
	frappe.flags.std_transition_service_context = True
	try:
		instance.readiness_status = "Invalidated"
		instance.save(ignore_permissions=True)
	finally:
		frappe.flags.std_transition_service_context = False
	_invalidate_outputs(instance.instance_code)
	record_std_audit_event("BOQ_UPDATED", "STD_INSTANCE", instance.instance_code, actor=actor)
	return {"item_instance_code": item_instance_code, "amount": doc.amount}


@frappe.whitelist()
def get_boq_instance(instance_code: str) -> dict[str, Any]:
	name = frappe.db.get_value("STD BOQ Instance", {"instance_code": instance_code}, "name")
	if not name:
		return {"boq_instance": None, "bills": [], "items": []}
	boq = frappe.get_doc("STD BOQ Instance", name)
	bills = frappe.get_all("STD BOQ Bill Instance", filters={"boq_instance_code": boq.boq_instance_code}, fields=["bill_instance_code", "bill_number", "bill_title", "bill_type", "order_index"], limit=1000)
	bill_codes = [b["bill_instance_code"] for b in bills]
	items = []
	if bill_codes:
		items = frappe.get_all("STD BOQ Item Instance", filters={"bill_instance_code": ("in", bill_codes)}, fields=["item_instance_code", "bill_instance_code", "item_number", "description", "unit", "quantity", "rate", "amount"], limit=5000)
	return {"boq_instance": {"boq_instance_code": boq.boq_instance_code, "status": boq.status, "validation_status": boq.validation_status}, "bills": bills, "items": items}


@frappe.whitelist()
def validate_boq_instance(instance_code: str, persist: bool = True) -> dict[str, Any]:
	name = frappe.db.get_value("STD BOQ Instance", {"instance_code": instance_code}, "name")
	if not name:
		return {"is_valid": False, "errors": ["BOQ instance not initialized"], "validation_status": "Fail"}
	boq = frappe.get_doc("STD BOQ Instance", name)
	bills = frappe.get_all("STD BOQ Bill Instance", filters={"boq_instance_code": boq.boq_instance_code}, fields=["bill_instance_code"], limit=1000)
	errors = []
	if not bills:
		errors.append("No BOQ bills defined")
	else:
		for b in bills:
			items = frappe.get_all("STD BOQ Item Instance", filters={"bill_instance_code": b["bill_instance_code"]}, fields=["item_number", "description", "unit", "quantity"], limit=5000)
			if not items:
				errors.append(f"Bill {b['bill_instance_code']} has no items")
			for item in items:
				if item["quantity"] in (None, ""):
					errors.append(f"Item {item['item_number']} missing quantity")
				elif float(item["quantity"]) < 0:
					errors.append(f"Item {item['item_number']} has negative quantity")
				for f in ("item_number", "description", "unit"):
					if not item.get(f):
						errors.append(f"Item missing required field: {f}")
	validation_status = "Pass" if not errors else "Fail"
	if persist:
		boq.validation_status = validation_status
		boq.status = "Validated" if not errors else "Draft"
		boq.save(ignore_permissions=True)
	return {"is_valid": not errors, "errors": errors, "validation_status": validation_status}

