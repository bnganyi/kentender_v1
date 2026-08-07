# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Gate for Demand consumers during Demands MVP-1 rebuild.

Schema (DocType Demand) may exist while Planning/lifecycle consumers still expect
legacy DIA shapes. Those consumers stay fail-closed until ``CONSUMERS_LIVE``.
"""

from __future__ import annotations

import frappe
from frappe import _

RETIRED_MESSAGE = (
	"Demand Intake and Approval has been retired; Demands MVP-1 consumer rewires "
	"are not live yet "
	"(see docs/mvp-1/03_demands/05_Demands_Teardown_Dependency_Inventory.md)."
)


def demand_doctype_available() -> bool:
	return bool(frappe.db.exists("DocType", "Demand"))


def demand_consumers_live() -> bool:
	try:
		from kentender_procurement.demands import CONSUMERS_LIVE

		return bool(CONSUMERS_LIVE)
	except ImportError:
		return False


def assert_demand_module_available() -> None:
	if not demand_doctype_available() or not demand_consumers_live():
		frappe.throw(_(RETIRED_MESSAGE), frappe.ValidationError)


def retired_payload(*, code: str = "DEMAND_MODULE_RETIRED") -> dict:
	return {
		"ok": False,
		"error_code": code,
		"message": RETIRED_MESSAGE,
		"skipped": True,
	}
