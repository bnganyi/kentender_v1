# Copyright (c) 2026, KenTender and contributors
"""STD Module POC retired stub — TM2 STD adapter unavailable."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.services.std_template_handoff_resolution import (
	RETIRED_MESSAGE,
)


def load_procurement_package_by_code(package_code: str) -> dict[str, Any] | None:
	if not package_code:
		return None
	if not frappe.db.exists("Procurement Package", package_code):
		return None
	return frappe.db.get_value(
		"Procurement Package",
		package_code,
		["name", "package_code", "package_title", "status", "procurement_method"],
		as_dict=True,
	)


def get_eligible_std_templates(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
	return []


def assert_std_eligible_for_package(*args: Any, **kwargs: Any) -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": "STD_MODULE_RETIRED",
		"message": RETIRED_MESSAGE,
		"retired": True,
	}
