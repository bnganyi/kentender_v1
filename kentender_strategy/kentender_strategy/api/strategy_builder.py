import json

import frappe
from frappe import _

from kentender_strategy.services import strategy_builder as svc


def _check_plan_write(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="write", throw=True)


@frappe.whitelist()
def get_strategy_tree(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="read", throw=True)
	return svc.build_tree(plan_name)


@frappe.whitelist()
def create_strategy_node(plan_name, parent_name=None, node_type=None, initial_data=None):
	_check_plan_write(plan_name)
	if parent_name in (None, ""):
		parent_name = None
	if isinstance(initial_data, str):
		initial_data = json.loads(initial_data or "{}")
	if not node_type:
		frappe.throw(_("node_type is required"))
	if node_type == "Program":
		frappe.has_permission("Strategy Program", ptype="create", throw=True)
	elif node_type == "Objective":
		frappe.has_permission("Strategy Objective", ptype="create", throw=True)
	elif node_type == "Target":
		frappe.has_permission("Strategy Target", ptype="create", throw=True)
	name = svc.create_node(plan_name, parent_name, node_type, initial_data or {})
	return {"name": name}


@frappe.whitelist()
def update_strategy_node(node_name, data):
	if isinstance(data, str):
		data = json.loads(data or "{}")
	if frappe.db.exists("Strategy Program", node_name):
		frappe.has_permission("Strategy Program", ptype="write", throw=True)
	elif frappe.db.exists("Strategy Objective", node_name):
		frappe.has_permission("Strategy Objective", ptype="write", throw=True)
	elif frappe.db.exists("Strategy Target", node_name):
		frappe.has_permission("Strategy Target", ptype="write", throw=True)
	else:
		frappe.throw(_("Strategy node not found."), frappe.DoesNotExistError)
	svc.update_node(node_name, data)
	return {"ok": True}


@frappe.whitelist()
def delete_strategy_node(node_name):
	if frappe.db.exists("Strategy Program", node_name):
		frappe.has_permission("Strategy Program", ptype="delete", throw=True)
	elif frappe.db.exists("Strategy Objective", node_name):
		frappe.has_permission("Strategy Objective", ptype="delete", throw=True)
	elif frappe.db.exists("Strategy Target", node_name):
		frappe.has_permission("Strategy Target", ptype="delete", throw=True)
	else:
		frappe.throw(_("Strategy node not found."), frappe.DoesNotExistError)
	svc.delete_node(node_name)
	return {"ok": True}
