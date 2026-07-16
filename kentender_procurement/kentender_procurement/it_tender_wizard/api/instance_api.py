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
	get_create_configuration_context,
	list_configurations,
	list_eligible_tender_shells,
)
from kentender_procurement.it_tender_wizard.services.wizard_tds_service import get_tds, save_tds
from kentender_procurement.it_tender_wizard.services.wizard_implementation_schedule_service import (
	get_implementation_schedule,
	save_implementation_schedule,
)
from kentender_procurement.it_tender_wizard.services.wizard_it_requirements_service import (
	get_it_requirements,
	save_it_requirements,
)
from kentender_procurement.it_tender_wizard.services.wizard_system_inventory_service import (
	get_system_inventory,
	save_system_inventory,
)
from kentender_procurement.it_tender_wizard.services.wizard_price_schedule_service import (
	get_price_schedule,
	save_price_schedule,
)
from kentender_procurement.it_tender_wizard.services.wizard_evaluation_setup_service import (
	get_evaluation_setup,
	save_evaluation_setup,
)
from kentender_procurement.it_tender_wizard.services.wizard_forms_evidence_service import (
	get_forms_and_evidence,
	save_forms_and_evidence,
)
from kentender_procurement.it_tender_wizard.services.wizard_scc_service import (
	get_scc,
	save_scc,
)
from kentender_procurement.it_tender_wizard.services.wizard_validation_report_service import (
	get_validation_report,
	save_validation_report,
)
from kentender_procurement.it_tender_wizard.services.wizard_review_service import (
	get_review_and_approval,
	save_review_and_approval,
)
from kentender_procurement.it_tender_wizard.services.wizard_render_preview_service import (
	get_render_preview,
	save_render_preview,
)
from kentender_procurement.it_tender_wizard.services.wizard_publication_readiness_service import (
	get_publication_readiness,
	save_publication_readiness,
)
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
def list_eligible_tender_shells_api() -> dict[str, Any]:
	return success_envelope({"items": list_eligible_tender_shells()})


@frappe.whitelist()
def get_create_configuration_context_api(
	tender_id: str | None = None,
	std_version_id: str | None = None,
	plan_item_id: str | None = None,
) -> dict[str, Any]:
	return success_envelope(
		get_create_configuration_context(
			tender_id=tender_id,
			std_version_id=std_version_id,
			plan_item_id=plan_item_id,
		)
	)


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
def get_it_requirements_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_it_requirements(configuration_id))


@frappe.whitelist()
def save_it_requirements_api(
	configuration_id: str,
	requirements_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if requirements_json:
		payload = frappe.parse_json(requirements_json) or {}
	return success_envelope(save_it_requirements(configuration_id, payload))


@frappe.whitelist()
def get_implementation_schedule_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_implementation_schedule(configuration_id))


@frappe.whitelist()
def save_implementation_schedule_api(
	configuration_id: str,
	schedule_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if schedule_json:
		payload = frappe.parse_json(schedule_json) or {}
	return success_envelope(save_implementation_schedule(configuration_id, payload))


@frappe.whitelist()
def get_system_inventory_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_system_inventory(configuration_id))


@frappe.whitelist()
def save_system_inventory_api(
	configuration_id: str,
	inventory_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if inventory_json:
		payload = frappe.parse_json(inventory_json) or {}
	return success_envelope(save_system_inventory(configuration_id, payload))


@frappe.whitelist()
def get_price_schedule_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_price_schedule(configuration_id))


@frappe.whitelist()
def save_price_schedule_api(
	configuration_id: str,
	price_schedule_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if price_schedule_json:
		payload = frappe.parse_json(price_schedule_json) or {}
	return success_envelope(save_price_schedule(configuration_id, payload))


@frappe.whitelist()
def get_evaluation_setup_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_evaluation_setup(configuration_id))


@frappe.whitelist()
def save_evaluation_setup_api(
	configuration_id: str,
	evaluation_setup_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if evaluation_setup_json:
		payload = frappe.parse_json(evaluation_setup_json) or {}
	return success_envelope(save_evaluation_setup(configuration_id, payload))


@frappe.whitelist()
def get_forms_and_evidence_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_forms_and_evidence(configuration_id))


@frappe.whitelist()
def save_forms_and_evidence_api(
	configuration_id: str,
	forms_and_evidence_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if forms_and_evidence_json:
		payload = frappe.parse_json(forms_and_evidence_json) or {}
	return success_envelope(save_forms_and_evidence(configuration_id, payload))


@frappe.whitelist()
def get_scc_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_scc(configuration_id))


@frappe.whitelist()
def save_scc_api(
	configuration_id: str,
	scc_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if scc_json:
		payload = frappe.parse_json(scc_json) or {}
	return success_envelope(save_scc(configuration_id, payload))


@frappe.whitelist()
def get_validation_report_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_validation_report(configuration_id))


@frappe.whitelist()
def save_validation_report_api(
	configuration_id: str,
	validation_report_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if validation_report_json:
		payload = frappe.parse_json(validation_report_json) or {}
	return success_envelope(save_validation_report(configuration_id, payload))


@frappe.whitelist()
def get_review_and_approval_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_review_and_approval(configuration_id))


@frappe.whitelist()
def save_review_and_approval_api(
	configuration_id: str,
	review_and_approval_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if review_and_approval_json:
		payload = frappe.parse_json(review_and_approval_json) or {}
	return success_envelope(save_review_and_approval(configuration_id, payload))


@frappe.whitelist()
def get_render_preview_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_render_preview(configuration_id))


@frappe.whitelist()
def save_render_preview_api(
	configuration_id: str,
	render_preview_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if render_preview_json:
		payload = frappe.parse_json(render_preview_json) or {}
	return success_envelope(save_render_preview(configuration_id, payload))


@frappe.whitelist()
def get_publication_readiness_api(configuration_id: str) -> dict[str, Any]:
	return success_envelope(get_publication_readiness(configuration_id))


@frappe.whitelist()
def save_publication_readiness_api(
	configuration_id: str,
	publication_readiness_json: str | None = None,
	**kwargs,
) -> dict[str, Any]:
	payload = kwargs
	if publication_readiness_json:
		payload = frappe.parse_json(publication_readiness_json) or {}
	return success_envelope(save_publication_readiness(configuration_id, payload))


@frappe.whitelist()
def delete_draft_configuration_api(configuration_id: str) -> dict[str, Any]:
	result = delete_draft_configuration(configuration_id)
	return success_envelope(result, audit_event_id=result.get("audit_event_id"))
