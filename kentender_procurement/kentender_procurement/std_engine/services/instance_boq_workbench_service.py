"""STD workbench: BOQ instance panel (STD-CURSOR-1104)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)
from kentender_procurement.std_engine.services.boq_instance_service import validate_boq_instance as run_boq_validation


def build_std_instance_boq_workbench_panel(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this instance code."))}

	doctype, name, inst = resolved
	if doctype != "STD Instance" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	read_only = str(inst.get("instance_status") or "") in ("Published Locked", "Superseded", "Cancelled")

	boq_name = frappe.db.get_value("STD BOQ Instance", {"instance_code": code}, "name")
	if not boq_name:
		return {
			"ok": True,
			"instance_code": code,
			"read_only": read_only,
			"boq": None,
			"validation": run_boq_validation(code, False),
			"import_preview": None,
		}

	boq = frappe.get_doc("STD BOQ Instance", boq_name)
	defn = frappe.db.get_value(
		"STD BOQ Definition",
		{"boq_definition_code": boq.boq_definition_code},
		[
			"boq_definition_code",
			"pricing_model",
			"supplier_input_mode",
			"arithmetic_correction_stage",
			"quantity_owner",
			"amount_computation_rule",
		],
		as_dict=True,
	) or {}

	bills = frappe.get_all(
		"STD BOQ Bill Instance",
		filters={"boq_instance_code": boq.boq_instance_code},
		fields=["bill_instance_code", "bill_number", "bill_title", "bill_type", "order_index"],
		order_by="order_index asc, bill_number asc",
		limit=500,
	)
	bill_rows: list[dict[str, Any]] = []
	item_total = 0
	for b in bills:
		items = frappe.get_all(
			"STD BOQ Item Instance",
			filters={"bill_instance_code": b["bill_instance_code"]},
			fields=[
				"item_instance_code",
				"item_number",
				"description",
				"unit",
				"quantity",
				"rate",
				"amount",
				"payload_json",
			],
			order_by="item_number asc",
			limit=2000,
		)
		item_total += len(items)
		bill_rows.append({**b, "items": items})

	val = run_boq_validation(code, False)

	completeness = str(_("Complete")) if val.get("is_valid") else str(_("Incomplete"))

	return {
		"ok": True,
		"instance_code": code,
		"read_only": read_only,
		"quantity_owner_label": str(_("Procuring Entity")),
		"rate_owner_note": str(_("Supplier input at bid stage; not an internal estimate.")),
		"boq": {
			"boq_instance_code": boq.boq_instance_code,
			"status": boq.status,
			"validation_status": boq.validation_status,
			"boq_definition_code": boq.boq_definition_code,
			"definition": defn,
			"bill_count": len(bill_rows),
			"item_count": item_total,
			"bills": bill_rows,
			"currency": "KES",
			"completeness_status": completeness,
		},
		"validation": val,
		"import_preview": None,
	}
