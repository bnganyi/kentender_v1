# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Eligible packages for Tender Configuration — PP2 Package path retired.

MVP-1 Plan Item take-up will replace this surface. Until then APIs return empty.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_configurations.constants import ACTIVE_CONFIGURATION_STATUSES


def packages_with_active_configuration() -> set[str]:
	rows = frappe.get_all(
		"Tender Configuration",
		filters={"status": ("in", list(ACTIVE_CONFIGURATION_STATUSES))},
		fields=["procurement_package"],
	)
	return {str(r.procurement_package) for r in rows if r.procurement_package}


def serialize_eligible_package(pkg: Any, configured: set[str] | None = None) -> dict[str, Any]:
	"""Retained for callers; Package DocType no longer exists."""
	return {}


def list_eligible_procurement_packages(search: str | None = None, *, limit: int = 100) -> list[dict[str, Any]]:
	"""PP2 Package eligibility retired — empty until MVP-1 Plan Item handoff."""
	return []


def get_procurement_package(package_id: str | None) -> Any:
	frappe.throw(
		_("Procurement Package is retired. Tender Configuration create from package is unavailable."),
		frappe.ValidationError,
	)


def get_package_or_throw(package_id: str | None) -> Any:
	return get_procurement_package(package_id)


def resolve_applicable_std_document(
	pkg: Any,
	*,
	std_document_id: str | None = None,
) -> dict[str, Any]:
	return {
		"std_document_id": "",
		"std_family_code": "",
		"std_family_name": "",
		"std_version_label": "",
	}
