from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.boq_instance_service import (
	add_boq_bill,
	add_boq_item,
	create_or_initialize_boq_instance,
	validate_boq_instance,
)
from kentender_procurement.std_engine.services.section_attachment_service import add_std_section_attachment


@frappe.whitelist()
def import_boq_structured(
	instance_code: str,
	file_reference: str,
	mapping_config: dict,
	actor: str,
	dry_run: bool = False,
) -> dict[str, Any]:
	if not file_reference:
		frappe.throw(_("file_reference is required."), title=_("Invalid import"))
	rows = (mapping_config or {}).get("rows", [])
	preview = []
	rejected = []
	for idx, row in enumerate(rows):
		required = ["bill_number", "bill_title", "item_number", "description", "unit", "quantity"]
		missing = [f for f in required if row.get(f) in (None, "")]
		if missing:
			rejected.append({"row_index": idx, "reason": f"Missing required: {', '.join(missing)}", "row": row})
		else:
			preview.append(row)

	if dry_run:
		return {"dry_run": True, "preview_rows": preview, "rejected_rows": rejected, "imported_rows": 0}

	if not rows:
		return {"dry_run": False, "preview_rows": [], "rejected_rows": [], "imported_rows": 0, "validation": validate_boq_instance(instance_code)}

	create_or_initialize_boq_instance(instance_code, actor)
	bills_by_number: dict[str, str] = {}
	imported = 0
	for row in preview:
		bill_number = str(row["bill_number"])
		if bill_number not in bills_by_number:
			bill = add_boq_bill(
				instance_code,
				{
					"bill_number": bill_number,
					"bill_title": row["bill_title"],
					"bill_type": row.get("bill_type", "Work Items"),
					"order_index": int(row.get("order_index", 1)),
				},
				actor,
			)
			bills_by_number[bill_number] = bill["bill_instance_code"]
		add_boq_item(
			bills_by_number[bill_number],
			{
				"item_number": row["item_number"],
				"description": row["description"],
				"unit": row["unit"],
				"quantity": row["quantity"],
				"rate": row.get("rate", 0),
			},
			actor,
		)
		imported += 1

	boq_def = frappe.db.get_value(
		"STD BOQ Instance",
		{"instance_code": instance_code},
		["boq_definition_code"],
		as_dict=True,
	)
	if boq_def:
		section_code = frappe.db.get_value("STD BOQ Definition", boq_def.boq_definition_code, "section_code")
		if section_code:
			add_std_section_attachment(
				instance_code=instance_code,
				section_code=section_code,
				file_reference=file_reference,
				classification="Supporting",
				actor=actor,
			)

	validation = validate_boq_instance(instance_code)
	record_std_audit_event(
		event_type="BOQ_UPDATED",
		object_type="STD_INSTANCE",
		object_code=instance_code,
		actor=actor,
		metadata={"imported_rows": imported, "rejected_rows": len(rejected), "file_reference": file_reference},
	)
	return {
		"dry_run": False,
		"preview_rows": preview,
		"rejected_rows": rejected,
		"imported_rows": imported,
		"validation": validation,
	}

