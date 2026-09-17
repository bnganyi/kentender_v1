# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §7.5 / §15.3 (PLN23-CHG-001) — remove the forecast and
reminder facility from the Planning schema.

v1.23 defers Planner-managed forecasting, cascades and schedule-driven
reminders in full: no MVP forecast schema, route, API, scheduler registration,
reminder configuration or notification producer. Leaving the tables in place
would leave `PLN23-AC-001` arguable rather than provable, so the two retired
records and the fourteen item-level forecast/actual date columns go.

The item-level `actual_*_date` columns additionally violated §5.5.1A: two
Tenders against one Plan Item have two invitation actuals, and collapsing them
onto the item lost material information. Per-proceeding actuals live on
`Milestone Actual Event`, which this patch leaves untouched — no operational
evidence is destroyed.

`exclusive_preference` goes with them under §5.5.3.2, which removes the
candidate-preference override from Planning.
"""

import frappe

RETIRED_DOCTYPES = ("Plan Item Forecast Revision", "Milestone Notice")

MILESTONES = (
	"invitation",
	"bid_opening",
	"evaluation_completion",
	"award_approval",
	"award_notification",
	"contract_signing",
	"delivery_completion",
)

RETIRED_ITEM_COLUMNS = (
	*(f"forecast_{m}_date" for m in MILESTONES),
	*(f"actual_{m}_date" for m in MILESTONES),
	"exclusive_preference",
)


def execute() -> None:
	for doctype in RETIRED_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, force=True, ignore_permissions=True, ignore_missing=True)
		# `table_exists` takes the DOCTYPE name and adds the `tab` prefix itself;
		# passing `tab{doctype}` here silently looked for `tabtab…` and skipped
		# the drop.
		if frappe.db.table_exists(doctype):
			frappe.db.sql_ddl(f"drop table if exists `tab{doctype}`")

	if not frappe.db.table_exists("Annual Plan Item"):
		return
	existing = {row.Field for row in frappe.db.sql("desc `tabAnnual Plan Item`", as_dict=True)}
	for column in RETIRED_ITEM_COLUMNS:
		if column in existing:
			frappe.db.sql_ddl(f"alter table `tabAnnual Plan Item` drop column `{column}`")
	frappe.clear_cache(doctype="Annual Plan Item")
