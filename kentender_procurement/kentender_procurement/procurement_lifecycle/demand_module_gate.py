# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Gate for legacy DIA Demand DocType during Demands MVP-1 preparatory teardown.

While Demand Intake is retired and Demands MVP-1 is not yet rebuilt, callers must
fail closed or return empty rather than importing deleted ``demand_intake`` modules.
"""

from __future__ import annotations

import frappe
from frappe import _

RETIRED_MESSAGE = (
	"Demand Intake and Approval has been retired pending Demands MVP-1 rebuild "
	"(see docs/mvp-1/03_demands/05_Demands_Teardown_Dependency_Inventory.md)."
)


def demand_doctype_available() -> bool:
	return bool(frappe.db.exists("DocType", "Demand"))


def assert_demand_module_available() -> None:
	if not demand_doctype_available():
		frappe.throw(_(RETIRED_MESSAGE), frappe.ValidationError)


def retired_payload(*, code: str = "DEMAND_MODULE_RETIRED") -> dict:
	return {
		"ok": False,
		"error_code": code,
		"message": RETIRED_MESSAGE,
		"skipped": True,
	}
