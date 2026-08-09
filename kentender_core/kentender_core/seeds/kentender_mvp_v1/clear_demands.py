# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear Demands-owned fixture rows (reverse dependency order)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.kentender_mvp_v1 import constants as C

_DEMAND_CODES = (
	C.DEMAND_CODE,
	C.DEMAND_CODE_RETURNED,
	C.DEMAND_CODE_COUNTY,
)

# Children before Demand; Funding Exception is Budget-owned but Demand-linked.
_CHILD_DOCTYPES = (
	"Demand Decision",
	"Demand Value Treatment",
	"Demand Strategy Reference",
	"Demand Funding Allocation",
	"Funding Exception",
	"Demand Item",
)


def clear_kentender_mvp_v1_demands() -> dict[str, Any]:
	"""Delete fixture Demands and related rows; leave Budget RSV graph intact."""
	deleted: dict[str, int] = {}
	if not frappe.db.exists("DocType", "Demand"):
		return {"ok": True, "deleted": deleted, "skipped": "Demand DocType unavailable"}

	demand_names = frappe.get_all(
		"Demand",
		filters={"demand_code": ["in", list(_DEMAND_CODES)]},
		pluck="name",
	)
	if frappe.db.has_column("Demand", "fixture_namespace"):
		for name in frappe.get_all(
			"Demand",
			filters={"fixture_namespace": C.FIXTURE_NS},
			pluck="name",
		):
			if name not in demand_names:
				demand_names.append(name)

	for demand in demand_names:
		for doctype in _CHILD_DOCTYPES:
			if not frappe.db.exists("DocType", doctype):
				continue
			for name in frappe.get_all(doctype, filters={"demand": demand}, pluck="name"):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
				deleted[doctype] = deleted.get(doctype, 0) + 1
		if frappe.db.exists("Demand", demand):
			frappe.delete_doc("Demand", demand, force=1, ignore_permissions=True)
			deleted["Demand"] = deleted.get("Demand", 0) + 1

	# Detach RSV business code only — do not delete the reservation (Budget-owned).
	if frappe.db.exists("DocType", "Funding Reservation"):
		for name in frappe.get_all(
			"Funding Reservation",
			filters={"demand_code": ["in", list(_DEMAND_CODES)]},
			pluck="name",
		):
			frappe.db.set_value(
				"Funding Reservation",
				name,
				{"demand_code": "", "demand_title": ""},
				update_modified=False,
			)
			deleted["Funding Reservation.detach"] = (
				deleted.get("Funding Reservation.detach", 0) + 1
			)

	return {"ok": True, "deleted": deleted}
