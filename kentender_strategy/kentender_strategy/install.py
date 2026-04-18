import os

import frappe
from frappe.modules.import_file import import_file_by_path


def after_migrate():
	"""Ensure the Strategy Builder Desk Page exists (synced from module JSON)."""
	path = os.path.join(
		frappe.get_app_path("kentender_strategy"),
		"kentender_strategy",
		"page",
		"strategy_builder",
		"strategy_builder.json",
	)
	if not os.path.exists(path):
		return
	if not frappe.db.exists("Page", "strategy-builder"):
		import_file_by_path(path)
	_backfill_strategic_plan_required_fields()


def _backfill_strategic_plan_required_fields():
	"""Fill missing required fields on legacy Strategic Plan rows (dev / partial upgrades)."""
	if not frappe.db.table_exists("tabStrategic Plan"):
		return
	default_company = frappe.defaults.get_global_default("company") or frappe.db.get_value(
		"Company", {}, "name", order_by="creation asc"
	)
	for row in frappe.get_all(
		"Strategic Plan",
		fields=["name", "strategic_plan_name", "procuring_entity", "start_year", "end_year"],
	):
		doc = frappe.get_doc("Strategic Plan", row.name)
		changed = False
		if not doc.strategic_plan_name:
			doc.strategic_plan_name = "Strategic Plan"
			changed = True
		if not doc.procuring_entity and default_company:
			doc.procuring_entity = default_company
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
