# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Tender Configurations APIs (UI-00 / UI-M01)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_configurations.services.create_configuration import (
	create_tender_configuration as _create,
	get_configuration as _get_configuration,
)
from kentender_procurement.tender_configurations.services.dashboard import get_dashboard
from kentender_procurement.tender_configurations.services.eligibility import (
	list_eligible_procurement_packages,
)


def _require_login() -> None:
	if frappe.session.user == "Guest":
		frappe.throw(frappe._("Login required."), frappe.PermissionError)


@frappe.whitelist()
def get_tender_configurations_dashboard(
	tab: str | None = None,
	search: str | None = None,
	std_family: str | None = None,
	procuring_entity: str | None = None,
	procurement_method: str | None = None,
	issue_status: str | None = None,
	page: int | str = 1,
	page_size: int | str = 20,
) -> dict[str, Any]:
	_require_login()
	return get_dashboard(
		tab=tab,
		search=search,
		std_family=std_family,
		procuring_entity=procuring_entity,
		procurement_method=procurement_method,
		issue_status=issue_status,
		page=page,
		page_size=page_size,
	)


@frappe.whitelist()
def get_eligible_procurement_packages(search: str | None = None) -> dict[str, Any]:
	_require_login()
	return {"packages": list_eligible_procurement_packages(search=search)}


@frappe.whitelist()
def create_tender_configuration(
	package_id: str,
	std_document_id: str | None = None,
) -> dict[str, Any]:
	_require_login()
	return _create(package_id=package_id, std_document_id=std_document_id)


@frappe.whitelist()
def get_tender_configuration(configuration_id: str) -> dict[str, Any]:
	_require_login()
	return _get_configuration(configuration_id)
