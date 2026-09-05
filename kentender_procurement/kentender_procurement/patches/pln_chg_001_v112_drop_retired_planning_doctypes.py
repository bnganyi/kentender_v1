# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 — retire `Departmental Plan Submission Window` (replaced
by the departmental-plan intake flag on ERPNext Fiscal Year, CFG v0.9 §4.2)
and `Plan Reservation Reference` (Planning holds no reservation, §7.3).

Runs pre_model_sync so the DocType rows and their tables are gone before sync
looks for the (now deleted) JSON. `delete_doc` alone leaves the table behind
(v1.2 finding 10), so the table is dropped explicitly.
"""

from __future__ import annotations

import frappe

RETIRED = ("Departmental Plan Submission Window", "Plan Reservation Reference")


def execute() -> None:
	for doctype in RETIRED:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True, delete_permanently=True)
		frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")
	frappe.db.commit()
