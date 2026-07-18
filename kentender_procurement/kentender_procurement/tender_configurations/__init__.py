# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Configurations module — C1-M2 documented API entrypoints."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_configurations.api import (
	create_tender_configuration as _create_tender_configuration,
	get_eligible_procurement_packages as _get_eligible_procurement_packages,
	get_tender_configuration as _get_tender_configuration,
	get_tender_configuration_home as _get_tender_configuration_home,
	get_tender_configuration_profile as _get_tender_configuration_profile,
	get_tender_configuration_requirements as _get_tender_configuration_requirements,
	get_tender_configuration_tds as _get_tender_configuration_tds,
	get_tender_configurations_dashboard as _get_tender_configurations_dashboard,
	save_tender_configuration_profile as _save_tender_configuration_profile,
	save_tender_configuration_requirements as _save_tender_configuration_requirements,
	save_tender_configuration_tds as _save_tender_configuration_tds,
)

# Re-export whitelisted methods at package path:
# kentender_procurement.tender_configurations.get_eligible_procurement_packages
# kentender_procurement.tender_configurations.create_tender_configuration


@frappe.whitelist()
def get_eligible_procurement_packages(search: str | None = None):
	return _get_eligible_procurement_packages(search=search)


@frappe.whitelist()
def create_tender_configuration(package_id: str, std_document_id: str | None = None):
	return _create_tender_configuration(package_id=package_id, std_document_id=std_document_id)


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
):
	return _get_tender_configurations_dashboard(
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
def get_tender_configuration(configuration_id: str):
	return _get_tender_configuration(configuration_id)


@frappe.whitelist()
def get_tender_configuration_home(configuration_id: str):
	return _get_tender_configuration_home(configuration_id)


@frappe.whitelist()
def get_tender_configuration_profile(configuration_id: str):
	return _get_tender_configuration_profile(configuration_id)


@frappe.whitelist()
def save_tender_configuration_profile(configuration_id: str, payload=None):
	return _save_tender_configuration_profile(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_tds(configuration_id: str):
	return _get_tender_configuration_tds(configuration_id)


@frappe.whitelist()
def save_tender_configuration_tds(configuration_id: str, payload=None):
	return _save_tender_configuration_tds(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_requirements(configuration_id: str):
	return _get_tender_configuration_requirements(configuration_id)


@frappe.whitelist()
def save_tender_configuration_requirements(configuration_id: str, payload=None):
	return _save_tender_configuration_requirements(configuration_id, payload)


@frappe.whitelist()
def seed_ui00_dashboard_for_tests(clear: int | str = 1):
	"""Administrator-only seed for Playwright / integration fixtures."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard

	return seed_ui00_dashboard(clear=bool(int(clear)))


@frappe.whitelist()
def seed_ui01_mockups_for_tests(clear: int | str = 1):
	"""Administrator-only UI-01 mockups: SHOWCASE + CFG-01…09 focus configs."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.ui01_mockup_seed import (
		seed_ui01_mockup_configurations,
	)

	return seed_ui01_mockup_configurations(clear=bool(int(clear)))
