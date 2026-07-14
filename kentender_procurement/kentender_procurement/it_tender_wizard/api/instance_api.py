# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted configuration instance APIs."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.it_tender_wizard.api.response_envelope import success_envelope
from kentender_procurement.it_tender_wizard.services.dashboard_kpi_service import build_dashboard_summary
from kentender_procurement.it_tender_wizard.services.wizard_instance_service import (
	create_configuration,
	delete_draft_configuration,
	get_configuration_summary,
	list_configurations,
)
from kentender_procurement.it_tender_wizard.services.wizard_tds_service import get_tds, save_tds
from kentender_procurement.it_tender_wizard.services.wizard_tender_profile_service import (
	get_tender_profile,
	save_tender_profile,
)


@frappe.whitelist()
def list_configurations_api(
	state: str | None = None,
	states: str | None = None,
	procurement_entity_id: str | None = None,
	procurement_method_code: str | None = None,
	overdue_only: bool | int | None = None,
	q: str | None = None,
	page: int = 1,
	page_size: int = 25,
) -> dict[str, Any]:
	data = list_configurations(
		state=state,
		states=states,
		procurement_entity_id=procurement_entity_id,
		procurement_method_code=procurement_method_code,
		overdue_only=frappe.utils.cint(overdue_only) == 1,
		q=q,
		page=int(page or 1),
		page_size=int(page_size or 25),
	)
	return success_envelope(data)


@frappe.whitelist()
def get_dashboard_summary(procurement_entity_id: str | None = None) -> dict[str, Any]:
	return success_envelope(build_dashboard_summary(procurement_entity_id=procurement_entity_id))


@frappe.whitelist()
def create_configuration_api(**kwargs) -> dict[str, Any]:
	result = create_configuration(dict(kwargs))
	audit_event_id = result.pop("audit_event_id", None)
	return success_envelope(result, audit_event_id=audit_event_id)


@frappe.whitelist()
def get_configuration_summary_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_configuration_summary(configuration_id))


@frappe.whitelist()
def get_tender_profile_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_tender_profile(configuration_id))


@frappe.whitelist()
def save_tender_profile_api(configuration_id: str, profile_json: str | None = None, **kwargs) -> dict[str, Any]:
	payload = kwargs
	if profile_json:
		payload = frappe.parse_json(profile_json) or {}
	return success_envelope(save_tender_profile(configuration_id, payload))


@frappe.whitelist()
def get_tds_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_tds(configuration_id))


@frappe.whitelist()
def save_tds_api(configuration_id: str, tds_json: str | None = None, **kwargs) -> dict[str, Any]:
	payload = kwargs
	if tds_json:
		payload = frappe.parse_json(tds_json) or {}
	return success_envelope(save_tds(configuration_id, payload))


@frappe.whitelist()
def delete_draft_configuration_api(configuration_id: str) -> dict[str, Any]:
	result = delete_draft_configuration(configuration_id)
	return success_envelope(result, audit_event_id=result.get("audit_event_id"))
