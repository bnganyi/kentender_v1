# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Tender Configurations APIs (UI-00 / UI-M01 / UI-01)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_configurations.services.configuration_home import (
	get_configuration_home as _get_configuration_home,
)
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


@frappe.whitelist()
def get_tender_configuration_home(configuration_id: str) -> dict[str, Any]:
	"""UI-01 home payload (context strip, next action, steps, handoff)."""
	_require_login()
	return _get_configuration_home(configuration_id)


@frappe.whitelist()
def get_tender_configuration_profile(configuration_id: str) -> dict[str, Any]:
	"""CFG-01 Tender Profile GET (C2-CFG1 §13)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.profile import (
		get_configuration_profile,
	)

	return get_configuration_profile(configuration_id)


@frappe.whitelist()
def save_tender_configuration_profile(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-01 Tender Profile POST (C2-CFG1 §13)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.profile import (
		save_configuration_profile,
	)

	return save_configuration_profile(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_tds(configuration_id: str) -> dict[str, Any]:
	"""CFG-02 Tender Data Sheet GET (C2-CFG2 §13)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tds import (
		get_configuration_tds,
	)

	return get_configuration_tds(configuration_id)


@frappe.whitelist()
def save_tender_configuration_tds(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-02 Tender Data Sheet POST (C2-CFG2 §13)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tds import (
		save_configuration_tds,
	)

	return save_configuration_tds(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_requirements(configuration_id: str) -> dict[str, Any]:
	"""CFG-03 IT Requirements GET (C2-CFG3 §19)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.it_requirements import (
		get_configuration_requirements,
	)

	return get_configuration_requirements(configuration_id)


@frappe.whitelist()
def save_tender_configuration_requirements(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-03 IT Requirements POST (C2-CFG3 §19)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.it_requirements import (
		save_configuration_requirements,
	)

	return save_configuration_requirements(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_implementation_schedule(configuration_id: str) -> dict[str, Any]:
	"""CFG-04 Implementation Schedule GET (C2-CFG4 §19)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.implementation_schedule import (
		get_configuration_implementation_schedule,
	)

	return get_configuration_implementation_schedule(configuration_id)


@frappe.whitelist()
def save_tender_configuration_implementation_schedule(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-04 Implementation Schedule POST (C2-CFG4 §19)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.implementation_schedule import (
		save_configuration_implementation_schedule,
	)

	return save_configuration_implementation_schedule(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_system_inventory(configuration_id: str) -> dict[str, Any]:
	"""CFG-05 System Inventory & Bidder Background GET (C2-CFG5 §21)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.system_inventory import (
		get_configuration_system_inventory,
	)

	return get_configuration_system_inventory(configuration_id)


@frappe.whitelist()
def save_tender_configuration_system_inventory(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-05 System Inventory & Bidder Background POST (C2-CFG5 §21)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.system_inventory import (
		save_configuration_system_inventory,
	)

	return save_configuration_system_inventory(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_price_schedule(configuration_id: str) -> dict[str, Any]:
	"""CFG-06 Price Schedule GET (C2-CFG6 §20)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule import (
		get_configuration_price_schedule,
	)

	return get_configuration_price_schedule(configuration_id)


@frappe.whitelist()
def save_tender_configuration_price_schedule(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-06 Price Schedule POST (C2-CFG6 §20)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule import (
		save_configuration_price_schedule,
	)

	return save_configuration_price_schedule(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_evaluation_setup(configuration_id: str) -> dict[str, Any]:
	"""CFG-07 Evaluation Setup GET (C2-CFG7 §21)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.evaluation_setup import (
		get_configuration_evaluation_setup,
	)

	return get_configuration_evaluation_setup(configuration_id)


@frappe.whitelist()
def save_tender_configuration_evaluation_setup(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-07 Evaluation Setup POST (C2-CFG7 §21)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.evaluation_setup import (
		save_configuration_evaluation_setup,
	)

	return save_configuration_evaluation_setup(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_forms_and_evidence(configuration_id: str) -> dict[str, Any]:
	"""CFG-08 Forms & Evidence GET (C2-CFG8 §20)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.forms_and_evidence import (
		get_configuration_forms_and_evidence,
	)

	return get_configuration_forms_and_evidence(configuration_id)


@frappe.whitelist()
def save_tender_configuration_forms_and_evidence(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-08 Forms & Evidence POST (C2-CFG8 §20)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.forms_and_evidence import (
		save_configuration_forms_and_evidence,
	)

	return save_configuration_forms_and_evidence(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_contract_values(configuration_id: str) -> dict[str, Any]:
	"""CFG-09 Contract Values GET (C2-CFG9 §19)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.contract_values import (
		get_configuration_contract_values,
	)

	return get_configuration_contract_values(configuration_id)


@frappe.whitelist()
def save_tender_configuration_contract_values(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""CFG-09 Contract Values POST (C2-CFG9 §19)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.contract_values import (
		save_configuration_contract_values,
	)

	return save_configuration_contract_values(configuration_id, payload)
