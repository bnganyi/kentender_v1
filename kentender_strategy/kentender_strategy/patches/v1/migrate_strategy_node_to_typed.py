"""One-time migration: Strategy Node tree -> Strategy Program / Objective / Target."""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Strategy Target"):
		return
	if not frappe.db.table_exists("tabStrategy Node"):
		return
	if frappe.db.count("Strategy Node") == 0:
		return

	plans = frappe.db.sql(
		"SELECT DISTINCT strategic_plan FROM `tabStrategy Node` WHERE strategic_plan IS NOT NULL AND strategic_plan != ''",
		pluck=True,
	)
	for plan_name in plans:
		if not frappe.db.exists("Strategic Plan", plan_name):
			continue
		_migrate_plan(plan_name)

	names = frappe.get_all("Strategy Node", pluck="name", order_by="modified desc")
	for name in names:
		try:
			frappe.delete_doc("Strategy Node", name, force=True, ignore_permissions=True)
		except Exception:
			frappe.log_error(title="Strategy Node migration delete", message=frappe.get_traceback())


def _migrate_plan(plan_name: str):
	nodes = frappe.get_all(
		"Strategy Node",
		filters={"strategic_plan": plan_name},
		fields=["*"],
		order_by="order_index asc, creation asc",
	)
	by_name = {n["name"]: n for n in nodes}
	node_to_program = {}
	node_to_objective = {}

	for n in nodes:
		if n["node_type"] != "Program" or n.get("parent_strategy_node"):
			continue
		pid = _ensure_program(plan_name, n)
		node_to_program[n["name"]] = pid

	for n in nodes:
		if n["node_type"] != "Objective":
			continue
		pn = n.get("parent_strategy_node")
		if not pn or pn not in node_to_program:
			continue
		oid = _ensure_objective(plan_name, node_to_program[pn], n)
		node_to_objective[n["name"]] = oid

	for n in nodes:
		if n["node_type"] != "Target":
			continue
		on = n.get("parent_strategy_node")
		if not on or on not in node_to_objective:
			continue
		obj_node = by_name.get(on)
		if not obj_node:
			continue
		pn = obj_node.get("parent_strategy_node")
		if not pn or pn not in node_to_program:
			continue
		_ensure_target(plan_name, node_to_program[pn], node_to_objective[on], n)


def _ensure_program(plan_name: str, n: dict) -> str:
	existing = frappe.db.get_value(
		"Strategy Program",
		{"strategic_plan": plan_name, "program_title": n.get("node_title")},
		"name",
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Strategy Program",
			"strategic_plan": plan_name,
			"program_title": n.get("node_title") or "Program",
			"description": n.get("node_description"),
			"order_index": n.get("order_index") or 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_objective(plan_name: str, program_name: str, n: dict) -> str:
	existing = frappe.db.get_value(
		"Strategy Objective",
		{
			"strategic_plan": plan_name,
			"program": program_name,
			"objective_title": n.get("node_title"),
		},
		"name",
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Strategy Objective",
			"strategic_plan": plan_name,
			"program": program_name,
			"objective_title": n.get("node_title") or "Objective",
			"description": n.get("node_description"),
			"order_index": n.get("order_index") or 0,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _ensure_target(plan_name: str, program_name: str, objective_name: str, n: dict) -> None:
	existing = frappe.db.get_value(
		"Strategy Target",
		{
			"strategic_plan": plan_name,
			"objective": objective_name,
			"target_title": n.get("node_title"),
		},
		"name",
	)
	if existing:
		return
	year = n.get("target_year")
	if not year:
		from frappe.utils import getdate

		year = getdate().year
	doc = frappe.get_doc(
		{
			"doctype": "Strategy Target",
			"strategic_plan": plan_name,
			"program": program_name,
			"objective": objective_name,
			"target_title": n.get("node_title") or "Target",
			"description": n.get("node_description"),
			"order_index": n.get("order_index") or 0,
			"measurement_type": "Numeric",
			"target_period_type": "Annual",
			"target_year": year,
			"target_value_numeric": n.get("target_value") or 0,
			"target_unit": (n.get("target_unit") or "Unit").strip() or "Unit",
		}
	)
	doc.insert(ignore_permissions=True)
