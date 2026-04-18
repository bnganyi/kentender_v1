import json

import frappe
from frappe import _

from kentender_strategy.services import strategy_builder as svc


@frappe.whitelist()
def get_strategy_tree(plan_name: str):
	frappe.has_permission("Strategic Plan", ptype="read", throw=True)
	return svc.build_tree(plan_name)


@frappe.whitelist()
def create_strategy_node(plan_name, parent_name=None, node_type=None, initial_data=None):
	frappe.has_permission("Strategic Plan", ptype="write", throw=True)
	frappe.has_permission("Strategy Node", ptype="create", throw=True)
	if isinstance(initial_data, str):
		initial_data = json.loads(initial_data or "{}")
	if not node_type:
		frappe.throw(_("node_type is required"))
	name = svc.create_node(plan_name, parent_name, node_type, initial_data or {})
	return {"name": name}


@frappe.whitelist()
def update_strategy_node(node_name, data):
	frappe.has_permission("Strategy Node", ptype="write", throw=True)
	if isinstance(data, str):
		data = json.loads(data or "{}")
	svc.update_node(node_name, data)
	return {"ok": True}


@frappe.whitelist()
def delete_strategy_node(node_name):
	frappe.has_permission("Strategy Node", ptype="delete", throw=True)
	svc.delete_node(node_name)
	return {"ok": True}
