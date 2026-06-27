import os

import frappe
from frappe.modules.import_file import import_file_by_path


def after_migrate():
	"""Ensure the Strategy Builder Desk Page exists (synced from module JSON)."""
	page_path = os.path.join(
		frappe.get_app_path("kentender_strategy"),
		"kentender_strategy",
		"page",
		"strategy_builder",
		"strategy_builder.json",
	)
	if os.path.exists(page_path) and not frappe.db.exists("Page", "strategy-builder"):
		import_file_by_path(page_path)
	_ensure_strategy_builder_roles()
	_sync_strategy_management_workspace()
	_sync_strategy_desktop_icon()
	_backfill_strategic_plan_required_fields()


def _ensure_strategy_builder_roles():
	"""Guarantee Strategy Manager and Planning Authority can access the Strategy Builder page."""
	if not frappe.db.exists("Page", "strategy-builder"):
		return
	existing = {
		r.role
		for r in frappe.get_all(
			"Has Role",
			filters={"parent": "strategy-builder", "parenttype": "Page"},
			fields=["role"],
		)
	}
	for role in ("Strategy Manager", "Planning Authority"):
		if role not in existing and frappe.db.exists("Role", role):
			frappe.db.sql(
				"""INSERT IGNORE INTO `tabHas Role`
				   (name, creation, modified, modified_by, owner,
				    docstatus, idx, role, parent, parentfield, parenttype)
				   VALUES (CONCAT('strategy-builder-', %(role)s, '-', UUID()),
				           NOW(), NOW(), 'Administrator', 'Administrator',
				           0, 0, %(role)s, 'strategy-builder', 'roles', 'Page')""",
				{"role": role},
			)
	frappe.db.commit()


def _sync_strategy_management_workspace():
	"""Sync Strategy Management workspace HTML (master–detail mount points) from module JSON."""
	path = os.path.join(
		frappe.get_app_path("kentender_strategy"),
		"kentender_strategy",
		"workspace",
		"strategy_management",
		"strategy_management.json",
	)
	if not os.path.exists(path):
		return
	import_file_by_path(path, force=True)
	# G0-016: harmonised sidebar/list label. Keep `title` == legacy headline: Frappe Desk
	# `generate_route` for module tiles uses `workspaces.title` (see frappe/desk/page/desktop/desktop.js).
	if frappe.db.exists("Workspace", "Strategy Management"):
		frappe.db.set_value(
			"Workspace",
			"Strategy Management",
			{"label": "Strategy Alignment", "title": "Strategy Management"},
			update_modified=False,
		)


def _sync_strategy_desktop_icon():
	"""Keep Desktop Icon row aligned with repo JSON (e.g. hidden home tile per IA)."""
	path = os.path.join(
		frappe.get_app_path("kentender_strategy"),
		"desktop_icon",
		"strategy.json",
	)
	if os.path.exists(path):
		import_file_by_path(path, force=True)


def _backfill_strategic_plan_required_fields():
	"""Fill missing required fields on legacy Strategic Plan rows (dev / partial upgrades)."""
	if not frappe.db.table_exists("tabStrategic Plan"):
		return
	default_entity = frappe.db.get_value("Procuring Entity", {}, "name", order_by="creation asc")
	for row in frappe.get_all(
		"Strategic Plan",
		fields=["name", "strategic_plan_name", "procuring_entity", "start_year", "end_year"],
	):
		doc = frappe.get_doc("Strategic Plan", row.name)
		changed = False
		if not doc.strategic_plan_name:
			doc.strategic_plan_name = "Strategic Plan"
			changed = True
		if not doc.procuring_entity and default_entity:
			doc.procuring_entity = default_entity
			changed = True
		if not doc.start_year:
			doc.start_year = 2026
			changed = True
		if not doc.end_year:
			doc.end_year = 2030
			changed = True
		if changed:
			doc.flags.ignore_validate = True
			try:
				doc.save()
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Strategic Plan backfill")
