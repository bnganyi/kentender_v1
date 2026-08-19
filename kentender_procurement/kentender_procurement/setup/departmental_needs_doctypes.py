"""Generate Departmental Needs records through Frappe's DocType lifecycle."""

from __future__ import annotations

import frappe


# These records are deliberately service-only. Even support reads must pass through
# the audited projection, so no Desk role receives raw DocType permissions.
CONTROLLED_PERMISSIONS: list[dict] = []


def _f(label: str, fieldname: str, fieldtype: str = "Data", **extra):
	return {"label": label, "fieldname": fieldname, "fieldtype": fieldtype, **extra}


SCHEMAS = (
	{
		"name": "Departmental Need",
		"module": "Departmental Needs",
		"autoname": "field:need_reference",
		"title_field": "title",
		"search_fields": "need_reference,title",
		"fields": [
			_f("Need Reference", "need_reference", reqd=1, unique=1, read_only=1, search_index=1, in_list_view=1),
			_f("Title", "title", reqd=1, in_list_view=1),
			_f("Procuring Entity", "procuring_entity", "Link", options="Procuring Entity", reqd=1, read_only=1, search_index=1),
			_f("Organisation Unit", "organisation_unit", "Link", options="Organisation Unit", reqd=1, read_only=1, search_index=1),
			_f("Target Financial Year", "target_financial_year", reqd=1, read_only=1, search_index=1),
			_f("Submitted By", "submitted_by", "Link", options="User", reqd=1, read_only=1, search_index=1),
			_f("Business Justification", "business_justification", "Long Text", reqd=1),
			_f("Required By", "required_by_date", "Date", reqd=1),
			_f("Delivery or Use Location", "delivery_or_use_location", reqd=1),
			_f("Indicative Cost", "indicative_cost", "Currency", options="currency"),
			_f("Currency", "currency", "Link", options="Currency"),
			_f("Status", "status", "Select", options="Draft\nSubmitted\nReturned\nAccepted for planning\nNot taken forward\nWithdrawn", default="Draft", reqd=1, read_only=1, in_list_view=1, search_index=1),
			_f("Submitted At", "submitted_at", "Datetime", read_only=1),
			_f("Last Decision At", "last_decision_at", "Datetime", read_only=1),
			_f("Concurrency Token", "concurrency_token", read_only=1, reqd=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Departmental Need Item",
		"module": "Departmental Needs",
		"autoname": "field:item_reference",
		"fields": [
			_f("Item Reference", "item_reference", reqd=1, unique=1, read_only=1, search_index=1, in_list_view=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1),
			_f("Line Number", "line_number", "Int", reqd=1, read_only=1),
			_f("Description", "description", "Small Text", reqd=1),
			_f("Indicative Quantity", "indicative_quantity", "Float", reqd=1),
			_f("Unit", "unit", "Link", options="UOM", reqd=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Departmental Need Review",
		"module": "Departmental Needs",
		"autoname": "field:review_reference",
		"fields": [
			_f("Review Reference", "review_reference", reqd=1, unique=1, read_only=1, search_index=1, in_list_view=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1),
			_f("Action", "action", "Select", options="Create\nUpdate\nSubmit\nResubmit\nReturn for correction\nAccept for planning\nDo not take forward\nWithdraw\nRequest withdrawal\nApprove withdrawal", reqd=1, read_only=1, in_list_view=1),
			_f("Prior State", "prior_state", read_only=1, reqd=1),
			_f("Result State", "result_state", read_only=1, reqd=1),
			_f("Reason", "reason", "Small Text", read_only=1),
			_f("Actor", "actor", "Link", options="User", reqd=1, read_only=1),
			_f("Workflow Task", "workflow_task", "Link", options="Workflow Task", read_only=1),
			_f("Occurred At", "occurred_at", "Datetime", reqd=1, read_only=1),
			_f("Idempotency Key", "idempotency_key", reqd=1, unique=1, read_only=1, search_index=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
	{
		"name": "Plan Need Allocation",
		"module": "Procurement Planning",
		"autoname": "hash",
		"fields": [
			_f("Plan Item", "plan_item", "Link", options="Procurement Plan Item", reqd=1, search_index=1),
			_f("Departmental Need", "departmental_need", "Link", options="Departmental Need", reqd=1, read_only=1, search_index=1),
			_f("Departmental Need Item", "departmental_need_item", "Link", options="Departmental Need Item", reqd=1, read_only=1, search_index=1),
			_f("Source Organisation Unit", "source_organisation_unit", "Link", options="Organisation Unit", reqd=1, read_only=1, search_index=1),
			_f("Allocated Quantity", "allocated_quantity", "Float", reqd=1),
			_f("Status", "status", "Select", options="Draft\nEffective\nReversed", default="Draft", reqd=1, in_list_view=1, search_index=1),
			_f("Proposed In Version", "proposed_in_version", "Link", options="Procurement Plan Version", reqd=1, search_index=1),
			_f("Effective From Version", "effective_from_version", "Link", options="Procurement Plan Version", read_only=1, search_index=1),
			_f("Reversed By Version", "reversed_by_version", "Link", options="Procurement Plan Version", read_only=1),
			_f("Effective At", "effective_at", "Datetime", read_only=1),
			_f("Reversed At", "reversed_at", "Datetime", read_only=1),
			_f("Reason", "reason", "Small Text"),
			_f("Idempotency Key", "idempotency_key", reqd=1, read_only=1, search_index=1),
			_f("Fixture Namespace", "fixture_namespace", hidden=1, read_only=1, search_index=1),
		],
	},
)


def generate() -> list[str]:
	"""Create and export all greenfield DocTypes idempotently."""
	frappe.flags.allow_doctype_export = True
	if not frappe.db.exists("Module Def", "Departmental Needs"):
		frappe.get_doc({"doctype": "Module Def", "module_name": "Departmental Needs", "app_name": "kentender_procurement"}).insert(ignore_permissions=True)
	created: list[str] = []
	for schema in SCHEMAS:
		if frappe.db.exists("DocType", schema["name"]):
			continue
		doc = frappe.get_doc({
			"doctype": "DocType",
			"custom": 0,
			"engine": "InnoDB",
			"track_changes": 1,
			"allow_rename": 0,
			"permissions": CONTROLLED_PERMISSIONS,
			**schema,
		})
		doc.insert(ignore_permissions=True)
		created.append(doc.name)
	frappe.db.commit()
	return created
