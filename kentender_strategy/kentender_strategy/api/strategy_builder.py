import json

import frappe
from frappe import _

from kentender_strategy.services import strategy_builder as svc


def _check_plan_write(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="write", throw=True)


def _normalize_node_type(node_type: str | None) -> str:
	return svc.normalize_node_type(node_type or "")


@frappe.whitelist()
def get_plan_meta(plan_name: str):
	"""Return plan header fields and per-plan KPI metrics for the workbench hero section."""
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="read", throw=True)

	counts = frappe.db.sql(
		"""
		SELECT
			(SELECT COUNT(*) FROM `tabStrategy Program` WHERE strategic_plan = %(p)s) AS programs,
			(SELECT COUNT(*) FROM `tabStrategy Objective` WHERE strategic_plan = %(p)s) AS objectives,
			(SELECT COUNT(*) FROM `tabStrategy Target` WHERE strategic_plan = %(p)s) AS targets,
			(SELECT MIN(target_due_date) FROM `tabStrategy Target`
				WHERE strategic_plan = %(p)s AND target_due_date IS NOT NULL
				AND target_due_date >= CURDATE()) AS next_milestone
		""",
		{"p": plan_name},
		as_dict=True,
	)
	c = counts[0] if counts else {}

	# Procuring entity display name for breadcrumb / header
	entity_code = doc.procuring_entity or ""
	entity_name = ""
	if entity_code:
		entity_name = (
			frappe.db.get_value("Procuring Entity", entity_code, "entity_name") or entity_code
		)

	# Compute per-plan success from its targets
	from kentender_strategy.api.landing import (
		_compute_portfolio_success,
		_budget_by_plan,
	)
	budget_by = _budget_by_plan([plan_name])
	success_rate, data_coverage = _compute_portfolio_success([plan_name], budget_by)

	return {
		"plan_name": plan_name,
		"plan_title": doc.strategic_plan_name or plan_name,
		"description": doc.description or "",
		"status": doc.status or "Draft",
		"start_year": doc.start_year,
		"end_year": doc.end_year,
		"procuring_entity": entity_code,
		"procuring_entity_name": entity_name,
		"programs": int(c.get("programs") or 0),
		"objectives": int(c.get("objectives") or 0),
		"targets": int(c.get("targets") or 0),
		"next_milestone": str(c.get("next_milestone") or "") if c.get("next_milestone") else "",
		"success_rate": round(float(success_rate or 0), 1),
		"data_coverage": round(float(data_coverage or 0), 1),
	}


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
	node_type = _normalize_node_type(node_type)
	if node_type == "Program":
		frappe.has_permission("Strategy Program", ptype="create", throw=True)
	elif node_type == "SubProgram":
		frappe.has_permission("Sub Program", ptype="create", throw=True)
	elif node_type == "Indicator":
		frappe.has_permission("Strategy Objective", ptype="create", throw=True)
	elif node_type == "Target":
		frappe.has_permission("Strategy Target", ptype="create", throw=True)
	else:
		frappe.throw(_("Invalid node type."))
	name = svc.create_node(plan_name, parent_name, node_type, initial_data or {})
	return {"name": name}


@frappe.whitelist()
def update_strategy_node(node_name, data):
	if isinstance(data, str):
		data = json.loads(data or "{}")
	if frappe.db.exists("Strategy Program", node_name):
		frappe.has_permission("Strategy Program", ptype="write", throw=True)
	elif frappe.db.exists("Sub Program", node_name):
		frappe.has_permission("Sub Program", ptype="write", throw=True)
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
	elif frappe.db.exists("Sub Program", node_name):
		frappe.has_permission("Sub Program", ptype="delete", throw=True)
	elif frappe.db.exists("Strategy Objective", node_name):
		frappe.has_permission("Strategy Objective", ptype="delete", throw=True)
	elif frappe.db.exists("Strategy Target", node_name):
		frappe.has_permission("Strategy Target", ptype="delete", throw=True)
	else:
		frappe.throw(_("Strategy node not found."), frappe.DoesNotExistError)
	svc.delete_node(node_name)
	return {"ok": True}


# ---------------------------------------------------------------------------
# Per-plan activity feed
# ---------------------------------------------------------------------------

# Node types in the hierarchy, in display order.
_HIERARCHY_DOCTYPES = [
	("Strategic Plan",    "name",             "strategic_plan_name", "Plan"),
	("Strategy Program",  "strategic_plan",   "program_title",       "Program"),
	("Sub Program",       "strategic_plan",   "title",               "Sub-program"),
	("Strategy Objective","strategic_plan",   "objective_title",     "Indicator"),
	("Strategy Target",   "strategic_plan",   "target_title",        "Target"),
]


@frappe.whitelist()
def get_plan_activity(plan_name: str, limit: int = 20) -> list:
	"""Return last N activity records scoped to one plan and its full hierarchy.

	Queries tabVersion for Strategic Plan, Strategy Program, Sub Program,
	Strategy Objective, and Strategy Target documents that belong to *plan_name*.
	Synthetic creation events are synthesised from each document's `creation`
	timestamp so new plans with no version history still show something.

	Each item returned:
	  {time, action, dot_class, node_type, node_title, user}
	"""
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	plan_doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(plan_doc, ptype="read", throw=True)

	limit = max(1, min(int(limit), 100))

	from kentender_strategy.api.landing import _parse_action_label

	# ── Build scope ──────────────────────────────────────────────────────────
	# For each doctype, collect (name, title, node_type, creation, owner).
	# Strategic Plan is a single doc; hierarchy doctypes are filtered by plan.
	scope_by_dt: dict[str, list[tuple]] = {}

	for doctype, plan_field, title_field, node_type in _HIERARCHY_DOCTYPES:
		if doctype == "Strategic Plan":
			rows = frappe.db.get_all(
				doctype,
				filters={"name": plan_name},
				fields=["name", title_field, "creation", "owner"],
			)
		else:
			rows = frappe.db.get_all(
				doctype,
				filters={plan_field: plan_name},
				fields=["name", title_field, "creation", "owner"],
				limit=500,
			)
		scope_by_dt[doctype] = [
			(r.name, r.get(title_field) or r.name, node_type, str(r.creation or ""), r.owner or "—")
			for r in rows
		]

	events: list[dict] = []

	# ── Version events + synthetic creation events per doctype ───────────────
	for doctype, items in scope_by_dt.items():
		if not items:
			continue

		docnames = tuple(i[0] for i in items)
		title_map = {i[0]: (i[1], i[2]) for i in items}  # name -> (title, node_type)

		# Batch version query for all names of this doctype in one SQL call
		version_rows = frappe.db.sql(
			"""
			SELECT docname, owner, creation, data
			FROM `tabVersion`
			WHERE ref_doctype = %(dt)s
			  AND docname IN %(dns)s
			ORDER BY creation DESC
			LIMIT %(lim)s
			""",
			{"dt": doctype, "dns": docnames, "lim": limit * 3},
			as_dict=True,
		)
		for row in version_rows:
			node_title, node_type = title_map.get(row.docname, (row.docname, ""))
			action, dot = _parse_action_label(row.get("data"))
			label = f"{node_type}: {action}" if node_type and node_type != "Plan" else action
			events.append({
				"time": str(row.creation),
				"action": label,
				"dot_class": dot,
				"node_type": node_type,
				"node_title": node_title,
				"user": row.owner or "—",
			})

		# Synthetic creation row for every document in this doctype
		for name, title, node_type, creation, owner in items:
			if not creation:
				continue
			label = "Plan created" if node_type == "Plan" else f"{node_type} added"
			dot = "primary" if node_type == "Plan" else "slate"
			events.append({
				"time": creation,
				"action": label,
				"dot_class": dot,
				"node_type": node_type,
				"node_title": title,
				"user": owner,
			})

	events.sort(key=lambda e: e["time"], reverse=True)
	return events[:limit]


@frappe.whitelist()
def update_plan(plan_name: str, data: str):
	"""Update Strategic Plan title and description from the workbench modal."""
	_check_plan_write(plan_name)
	svc.update_plan(plan_name, json.loads(data or "{}"))
	return {"ok": True}
