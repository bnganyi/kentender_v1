# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demand consumer gate after the legacy Demands package retirement.

Consumers are live when the Demand DocType exists. ``CONSUMERS_LIVE`` remains as
an explicit package flag (True) for callers/tests that still import it.
"""

from __future__ import annotations

import frappe
from frappe import _

RETIRED_MESSAGE = (
	"Demand DocType is not available on this site "
	"(see docs/mvp-1-r1/01_departmental_needs/06_Departmental_Needs_Greenfield_Rebuild_Tracker.md)."
)


def demand_doctype_available() -> bool:
	return bool(frappe.db.exists("DocType", "Demand"))


def demand_consumers_live() -> bool:
	"""True when Demand consumers may run — DocType present and package flag live."""
	try:
		from kentender_procurement.demands import CONSUMERS_LIVE

		flag = bool(CONSUMERS_LIVE)
	except ImportError:
		flag = False
	return flag and demand_doctype_available()


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
