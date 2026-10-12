# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.15 §20 (Project Owner, 9 October 2026): a Draft created under
the v1.14 full-amount default keeps every entered value, but those quantities
and estimated total costs came from the default, not from the requester, so
they are not treated as confirmed intent. Every drawdown line of every Draft
Version is listed as awaiting review; a line leaves the list when the
requester saves its estimated total cost. Nothing is erased or recomputed.

Submitted, authorised, returned, withdrawn and revoked Versions are not
touched. Idempotent: a Draft that already has a list (including an empty one)
is left alone, so a Draft created or reviewed under v1.15 is never re-marked.
"""

from __future__ import annotations

import json

import frappe


def execute():
	if not frappe.db.has_column("Requisition Version", "unreviewed_line_ids_json"):
		return
	marked = 0
	for name in frappe.get_all("Requisition Version", filters={"version_status": "Draft", "unreviewed_line_ids_json": ("is", "not set")}, pluck="name"):
		lines = frappe.get_all("Requisition Drawdown Line", filters={"parent": name, "parenttype": "Requisition Version"}, pluck="drawdown_line_id")
		frappe.db.set_value("Requisition Version", name, "unreviewed_line_ids_json", json.dumps(sorted(lines)), update_modified=False)
		marked += 1
	if marked:
		frappe.logger().info(f"REQ v1.15: {marked} carried-over Draft(s) marked for review")
