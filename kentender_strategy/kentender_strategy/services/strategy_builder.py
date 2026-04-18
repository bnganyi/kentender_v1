import frappe
from frappe import _


def get_plan_or_throw(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	return frappe.get_doc("Strategic Plan", plan_name)


def build_tree(plan_name: str) -> dict:
	plan = get_plan_or_throw(plan_name)
	rows = frappe.db.get_all(
		"Strategy Node",
		filters={"strategic_plan": plan_name},
		fields=[
			"name",
			"parent_strategy_node",
			"node_type",
			"node_title",
			"node_description",
			"order_index",
			"target_year",
			"target_value",
			"target_unit",
		],
		order_by="order_index asc, name asc",
	)
	nodes = []
	for r in rows:
		nodes.append(
			{
				"name": r.name,
				"parent": r.parent_strategy_node,
				"node_type": r.node_type,
				"title": r.node_title,
				"description": r.node_description or "",
				"order_index": r.order_index or 0,
				"target_year": r.target_year,
				"target_value": r.target_value,
				"target_unit": r.target_unit or "",
			}
		)
	counts = {"programs": 0, "objectives": 0, "targets": 0}
	for r in rows:
		if r.node_type == "Program":
			counts["programs"] += 1
		elif r.node_type == "Objective":
			counts["objectives"] += 1
		elif r.node_type == "Target":
			counts["targets"] += 1
	return {
		"plan": {
			"name": plan.name,
			"title": plan.title,
			"description": plan.description or "",
		},
		"nodes": nodes,
		"counts": counts,
	}


def validate_new_node(plan_name: str, parent_name: str | None, node_type: str) -> None:
	get_plan_or_throw(plan_name)
	if node_type == "Program":
		if parent_name:
			frappe.throw(_("Program cannot have a parent."))
		return
	if not parent_name or not frappe.db.exists("Strategy Node", parent_name):
		frappe.throw(_("Parent node is required."))
	parent = frappe.get_doc("Strategy Node", parent_name)
	if parent.strategic_plan != plan_name:
		frappe.throw(_("Parent belongs to a different Strategic Plan."))
	if node_type == "Objective":
		if parent.node_type != "Program":
			frappe.throw(_("Objective must be created under a Program."))
	elif node_type == "Target":
		if parent.node_type != "Objective":
			frappe.throw(_("Target must be created under an Objective."))
	else:
		frappe.throw(_("Invalid node type."))


def _next_order_index(plan_name: str, parent_name: str | None) -> int:
	if parent_name:
		filters = {"strategic_plan": plan_name, "parent_strategy_node": parent_name}
	else:
		filters = {"strategic_plan": plan_name, "parent_strategy_node": ("is", "not set")}
	rows = frappe.db.get_all(
		"Strategy Node",
		filters=filters,
		fields=["order_index"],
		order_by="order_index desc",
		limit=1,
	)
	if not rows:
		return 1
	return (rows[0].order_index or 0) + 1


def create_node(
	plan_name: str,
	parent_name: str | None,
	node_type: str,
	initial_data: dict | None = None,
) -> str:
	validate_new_node(plan_name, parent_name, node_type)
	data = initial_data or {}
	doc_dict = {
		"doctype": "Strategy Node",
		"strategic_plan": plan_name,
		"node_type": node_type,
		"node_title": data.get("node_title") or _("Untitled"),
		"node_description": data.get("node_description"),
		"order_index": _next_order_index(plan_name, parent_name),
	}
	if parent_name:
		doc_dict["parent_strategy_node"] = parent_name
	doc = frappe.get_doc(doc_dict)
	if node_type == "Target":
		doc.target_year = data.get("target_year")
		doc.target_value = data.get("target_value")
		doc.target_unit = data.get("target_unit")
	doc.insert()
	return doc.name


def update_node(node_name: str, data: dict) -> None:
	doc = frappe.get_doc("Strategy Node", node_name)
	allowed = {"node_title", "node_description"}
	for k in allowed:
		if k in data and data[k] is not None:
			doc.set(k, data[k])
	if doc.node_type == "Target":
		for k in ("target_year", "target_value", "target_unit"):
			if k in data:
				doc.set(k, data[k])
	doc.save()


def delete_node(node_name: str) -> None:
	if frappe.db.count("Strategy Node", {"parent_strategy_node": node_name}):
		frappe.throw(_("Delete child nodes first."))
	frappe.delete_doc("Strategy Node", node_name)
