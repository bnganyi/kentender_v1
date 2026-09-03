# CU-305 (AUTH tracker) — Performance Target's year link moves from the
# condemned KenTender `Financial Year` doctype to ERPNext `Fiscal Year`
# (CFG-CHG-002 v0.6 §4.2: ERPNext Fiscal Year is the one canonical year).
#
# Existing values are remapped by matching the legacy year's start/end dates
# onto the Fiscal Year covering the same period; a legacy value with no
# matching Fiscal Year is left in place and reported, never silently blanked.

import frappe


def execute():
	frappe.reload_doc("kentender_strategy", "doctype", "performance_target")

	if not frappe.db.table_exists("Financial Year"):
		return
	legacy_years = frappe.get_all(
		"Financial Year", fields=["name", "start_date", "end_date"], limit_page_length=0
	)
	if not legacy_years:
		return

	mapping: dict[str, str] = {}
	for row in legacy_years:
		target = frappe.db.get_value(
			"Fiscal Year",
			{"year_start_date": row.start_date, "year_end_date": row.end_date},
			"name",
		)
		if target:
			mapping[row.name] = target

	unmapped: set[str] = set()
	for old, new in mapping.items():
		frappe.db.set_value(
			"Performance Target",
			{"financial_year_id": old},
			"financial_year_id",
			new,
			update_modified=False,
		)
	for value in frappe.get_all(
		"Performance Target",
		filters={"financial_year_id": ("in", [row.name for row in legacy_years])},
		pluck="financial_year_id",
	):
		unmapped.add(value)
	if unmapped:
		frappe.log_error(
			title="CU-305 unmapped Performance Target years",
			message=f"No Fiscal Year covers: {sorted(unmapped)}",
		)
