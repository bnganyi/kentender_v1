# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.6 §1.1/§4 — drop the `procuring_entity` column outright.

The site is implicitly one Procuring Entity (AUTH-ADR-001 v1.6 §1.1); no
Departmental Needs DocType carries a `procuring_entity` field any more. The
column was already removed from `field_order`/`fields` in
`departmental_need.json` and `departmental_need_review_task.json`, but
Frappe's DocType sync does not drop a removed column on `bench migrate` — it
is dropped explicitly here, following the same pattern as
`nds_chg_001_v11_decision_review_task`.

No live or seed data existed in either table at the time of this patch
(verified: `frappe.db.count("Departmental Need") == 0`), so this is a pure
schema drop. If a future environment somehow carries a populated value, fail
loudly rather than discard it.
"""

from __future__ import annotations

import frappe

_TABLES = ("Departmental Need", "Departmental Need Review Task")


def execute():
	for doctype in _TABLES:
		_drop_column(doctype)


def _drop_column(doctype: str) -> None:
	table = f"tab{doctype}"
	if not frappe.db.table_exists(doctype):
		return
	columns = {
		row.get("Field") or row.get("column_name")
		for row in frappe.db.sql(f"desc `{table}`", as_dict=True)
	}
	if "procuring_entity" not in columns:
		return
	populated = frappe.db.sql(
		f"select count(*) from `{table}` where ifnull(procuring_entity, '') != ''"
	)[0][0]
	if populated:
		frappe.throw(
			f"{populated} {doctype} rows carry a procuring_entity value; "
			"reconcile them before dropping the column.",
			title="NDS_TEARDOWN_BLOCKED",
		)
	frappe.db.sql(f"alter table `{table}` drop column `procuring_entity`")
	frappe.db.delete("DocField", {"parent": doctype, "fieldname": "procuring_entity"})
