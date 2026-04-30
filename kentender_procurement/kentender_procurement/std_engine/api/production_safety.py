from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.production_safety_service import (
	build_std_production_safety_report,
)

_SAFETY_READ_ROLES = frozenset(
	{
		"Administrator",
		"System Manager",
		"STD Auditor",
		"Head of Procurement and Disposal Unit (HPDU)",
		"Procurement Compliance Officer",
	}
)


def _can_read_safety_report(actor: str) -> bool:
	if actor == "Guest":
		return False
	return bool(_SAFETY_READ_ROLES.intersection(set(frappe.get_roles(actor) or [])))


@frappe.whitelist()
def get_std_production_safety_report(smoke_tests_passed: bool | None = None) -> dict[str, Any]:
	actor = frappe.session.user
	if not _can_read_safety_report(actor):
		frappe.throw(_("Not permitted to read STD production safety report."), frappe.PermissionError)
	return build_std_production_safety_report(smoke_tests_passed=smoke_tests_passed, actor=actor)
