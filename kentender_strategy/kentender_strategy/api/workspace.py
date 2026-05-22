"""Strategy workspace APIs — plan metadata drawers."""

import json

import frappe
from frappe import _


@frappe.whitelist()
def create_strategic_plan(data=None):
	if isinstance(data, str):
		data = json.loads(data or "{}")
	frappe.has_permission("Strategic Plan", ptype="create", throw=True)
	doc = frappe.get_doc(
		{
			"doctype": "Strategic Plan",
			"strategic_plan_name": data.get("strategic_plan_name"),
			"procuring_entity": data.get("procuring_entity"),
			"start_year": data.get("start_year"),
			"end_year": data.get("end_year"),
			"description": data.get("description"),
			"status": "Draft",
			"version_no": 1,
			"is_current_version": 1,
		}
	)
	doc.insert()
	return {"name": doc.name}


@frappe.whitelist()
def update_strategic_plan_metadata(plan_name, data=None):
	if isinstance(data, str):
		data = json.loads(data or "{}")
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="write", throw=True)
	for f in ("strategic_plan_name", "procuring_entity", "start_year", "end_year", "description"):
		if f in data and data[f] is not None:
			doc.set(f, data[f])
	doc.save()
	return {"name": doc.name}


@frappe.whitelist()
def get_plan_downstream_usage(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="read", throw=True)

	items = []
	if frappe.db.exists("DocType", "Budget Line"):
		count = frappe.db.count("Budget Line", {"strategic_plan": plan_name})
		if count:
			items.append({"label": _("Linked budget lines"), "count": count})
	if frappe.db.exists("DocType", "Demand"):
		count = frappe.db.count("Demand", filters={"strategic_plan": plan_name})
		if count:
			items.append({"label": _("Linked requisitions"), "count": count})
	return {"items": items}
