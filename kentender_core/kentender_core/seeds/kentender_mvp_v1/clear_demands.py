# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear Demands-owned fixture rows (reverse dependency order)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_core.seeds.kentender_mvp_v1 import constants as C

_DEMAND_CODES = (
	C.DEMAND_CODE,
	C.DEMAND_CODE_RETURNED,
	C.DEMAND_CODE_COUNTY,
)

# Children before Demand; Funding Exception is Budget-owned but Demand-linked.
_CHILD_DOCTYPES = (
	"Plan Demand Allocation",
	"Planning Consumption",
	"Demand Decision",
	"Demand Value Treatment",
	"Demand Strategy Reference",
	"Demand Funding Allocation",
	"Funding Exception",
	"Demand Item",
)

_PLAYWRIGHT_NAMESPACES = (
	"DEMANDS_UI03_FACTORY",
	"DEMANDS_UI04_FACTORY",
	"DEMANDS_UI05_FACTORY",
	"DEMANDS_UI06_FACTORY",
	"DEMANDS_UI07_FACTORY",
	"DEMANDS_UI07_MM_FACTORY",
	"DEMANDS_UI09_FACTORY",
	C.PLAYWRIGHT_FIXTURE_NS,
)


def clear_kentender_mvp_v1_demands(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, Any]:
	"""Delete owned Demands; reverse test RSV effects and detach canonical RSV links."""
	deleted: dict[str, int] = {}
	if not frappe.db.exists("DocType", "Demand"):
		return {"ok": True, "deleted": deleted, "skipped": "Demand DocType unavailable"}

	demand_names = (
		frappe.get_all(
			"Demand",
			filters={"demand_code": ["in", list(_DEMAND_CODES)]},
			pluck="name",
		)
		if include_canonical
		else []
	)
	if frappe.db.has_column("Demand", "fixture_namespace"):
		namespaces = []
		if include_canonical:
			namespaces.extend((C.FIXTURE_NS, C.LEGACY_FIXTURE_NS))
		if include_playwright:
			namespaces.extend(_PLAYWRIGHT_NAMESPACES)
		if namespaces:
			for name in frappe.get_all(
				"Demand",
				filters={"fixture_namespace": ["in", namespaces]},
				pluck="name",
			):
				if name not in demand_names:
					demand_names.append(name)
	if include_playwright:
		# Legacy Planning Gate helpers predate fixture_namespace but use a
		# reserved, generated test prefix.
		for name in frappe.get_all(
			"Demand", filters={"demand_code": ["like", "DEM-G01-%"]}, pluck="name"
		):
			if name not in demand_names:
				demand_names.append(name)

	for demand in demand_names:
		demand_code = frappe.db.get_value("Demand", demand, "demand_code") or ""
		for doctype in _CHILD_DOCTYPES:
			if not frappe.db.exists("DocType", doctype):
				continue
			for name in frappe.get_all(doctype, filters={"demand": demand}, pluck="name"):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
				deleted[doctype] = deleted.get(doctype, 0) + 1
		if frappe.db.exists("DocType", "File"):
			for name in frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Demand", "attached_to_name": demand},
				pluck="name",
			):
				frappe.delete_doc("File", name, force=1, ignore_permissions=True)
				deleted["File"] = deleted.get("File", 0) + 1
		# Reservations created by a Playwright Demand are fixture-owned even
		# when they use a canonical Budget Line.
		if demand_code and frappe.db.exists("DocType", "Funding Reservation"):
			for name in frappe.get_all(
				"Funding Reservation", filters={"demand_code": demand_code}, pluck="name"
			):
				reservation = frappe.db.get_value(
					"Funding Reservation",
					name,
					["budget_line", "generated_reference", "remaining_reserved"],
					as_dict=True,
				)
				if frappe.db.exists("DocType", "Budget Audit Event"):
					frappe.flags.allow_budget_audit_purge = True
					try:
						audit_names = frappe.get_all(
							"Budget Audit Event",
							filters={"source_reference": demand_code},
							pluck="name",
						)
						if reservation and reservation.generated_reference:
							audit_names.extend(
								frappe.get_all(
									"Budget Audit Event",
									filters={
										"record_doctype": "Funding Reservation",
										"record_code": reservation.generated_reference,
									},
									pluck="name",
								)
							)
						for audit_name in dict.fromkeys(audit_names):
							if frappe.db.exists("Budget Audit Event", audit_name):
								frappe.delete_doc(
									"Budget Audit Event",
									audit_name,
									force=1,
									ignore_permissions=True,
								)
								deleted["Budget Audit Event"] = (
									deleted.get("Budget Audit Event", 0) + 1
								)
					finally:
						frappe.flags.allow_budget_audit_purge = False
				frappe.delete_doc("Funding Reservation", name, force=1, ignore_permissions=True)
				deleted["Funding Reservation"] = deleted.get("Funding Reservation", 0) + 1
				if reservation and reservation.budget_line:
					current = flt(
						frappe.db.get_value(
							"Procurement Budget Line", reservation.budget_line, "amount_reserved"
						)
					)
					frappe.db.set_value(
						"Procurement Budget Line",
						reservation.budget_line,
						"amount_reserved",
						max(0, current - flt(reservation.remaining_reserved)),
						update_modified=False,
					)
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
