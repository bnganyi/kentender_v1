# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B1: rename legacy procurement method label ``Direct`` to ``Direct Procurement``."""

from __future__ import annotations

import json

import frappe
from frappe.utils.data import parse_json


def execute():
	# ``has_table`` / ``table_exists`` expect DocType names (e.g. ``Tender``), not ``tab...`` SQL names.
	if frappe.db.table_exists("Tender"):
		frappe.db.sql(
			"UPDATE `tabTender` SET `procurement_method` = %s WHERE `procurement_method` = %s",
			("Direct Procurement", "Direct"),
		)
	if frappe.db.table_exists("Procurement Package"):
		frappe.db.sql(
			"UPDATE `tabProcurement Package` SET `procurement_method` = %s WHERE `procurement_method` = %s",
			("Direct Procurement", "Direct"),
		)
	if frappe.db.table_exists("Procurement Template"):
		frappe.db.sql(
			"UPDATE `tabProcurement Template` SET `default_method` = %s WHERE `default_method` = %s",
			("Direct Procurement", "Direct"),
		)
		for row in frappe.db.sql(
			"select name, allowed_methods from `tabProcurement Template` where ifnull(allowed_methods,'') != ''",
			as_dict=True,
		):
			raw = row.get("allowed_methods")
			try:
				lst = parse_json(raw) if isinstance(raw, str) else raw
			except Exception:
				continue
			if not isinstance(lst, list):
				continue
			new_list = []
			changed = False
			for m in lst:
				if m == "Direct":
					new_list.append("Direct Procurement")
					changed = True
				else:
					new_list.append(m)
			if changed:
				frappe.db.set_value(
					"Procurement Template",
					row["name"],
					"allowed_methods",
					json.dumps(new_list),
					update_modified=False,
				)
