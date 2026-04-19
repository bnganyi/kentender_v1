# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""pre_model_sync: migrate Strategy Target period fields before DocType sync drops target_period_value."""

from __future__ import annotations

import frappe
from frappe.utils import cint, getdate


def execute():
	if not frappe.db.table_exists("tabStrategy Target"):
		return

	# Add v1.1 columns if missing (before JSON sync creates them — idempotent).
	if not frappe.db.has_column("Strategy Target", "target_year"):
		frappe.db.sql(
			"ALTER TABLE `tabStrategy Target` ADD COLUMN `target_year` INT(11) NULL DEFAULT NULL"
		)
	if not frappe.db.has_column("Strategy Target", "target_due_date"):
		frappe.db.sql(
			"ALTER TABLE `tabStrategy Target` ADD COLUMN `target_due_date` DATE NULL DEFAULT NULL"
		)

	if not frappe.db.has_column("Strategy Target", "target_period_value"):
		return

	rows = frappe.db.sql(
		"""
		SELECT st.name, st.strategic_plan, st.target_period_type, st.target_period_value
		FROM `tabStrategy Target` st
		""",
		as_dict=True,
	)

	for row in rows:
		name = row.name
		ptype = (row.target_period_type or "").strip()
		pval = (row.target_period_value or "").strip()

		# Normalize deprecated Quarterly → Annual (year from plan start).
		if ptype == "Quarterly":
			start_y = frappe.db.get_value("Strategic Plan", row.strategic_plan, "start_year")
			ty = cint(start_y) if start_y is not None else None
			frappe.db.sql(
				"""
				UPDATE `tabStrategy Target`
				SET target_period_type = %s, target_year = %s, target_due_date = NULL
				WHERE name = %s
				""",
				("Annual", ty, name),
			)
			continue

		if ptype == "Annual":
			try:
				year = cint(pval) if pval else None
			except Exception:
				year = None
			frappe.db.sql(
				"""
				UPDATE `tabStrategy Target`
				SET target_year = %s, target_due_date = NULL
				WHERE name = %s
				""",
				(year, name),
			)
			continue

		if ptype == "End of Plan":
			frappe.db.sql(
				"""
				UPDATE `tabStrategy Target`
				SET target_year = NULL, target_due_date = NULL
				WHERE name = %s
				""",
				(name,),
			)
			continue

		if ptype == "Milestone Date":
			due = None
			if pval:
				try:
					due = getdate(pval)
				except Exception:
					due = None
			frappe.db.sql(
				"""
				UPDATE `tabStrategy Target`
				SET target_year = NULL, target_due_date = %s
				WHERE name = %s
				""",
				(due, name),
			)
			continue

	frappe.db.commit()
