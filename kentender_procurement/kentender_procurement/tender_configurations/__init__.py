# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Configurations module — C1-M2 documented API entrypoints."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_configurations.api import (
	approve_tender_configuration_for_preview as _approve_tender_configuration_for_preview,
	confirm_tender_configuration_document_preview as _confirm_tender_configuration_document_preview,
	create_tender_configuration as _create_tender_configuration,
	download_tender_configuration_document_preview_pdf as _download_tender_configuration_document_preview_pdf,
	generate_tender_configuration_document_preview as _generate_tender_configuration_document_preview,
	get_eligible_procurement_packages as _get_eligible_procurement_packages,
	get_tender_configuration as _get_tender_configuration,
	get_tender_configuration_document_preview as _get_tender_configuration_document_preview,
	get_tender_configuration_home as _get_tender_configuration_home,
	get_tender_configuration_profile as _get_tender_configuration_profile,
	get_tender_configuration_implementation_schedule as _get_tender_configuration_implementation_schedule,
	get_tender_configuration_readiness as _get_tender_configuration_readiness,
	get_tender_configuration_requirements as _get_tender_configuration_requirements,
	get_tender_configuration_review as _get_tender_configuration_review,
	get_tender_configuration_contract_values as _get_tender_configuration_contract_values,
	get_tender_configuration_evaluation_setup as _get_tender_configuration_evaluation_setup,
	get_tender_configuration_forms_and_evidence as _get_tender_configuration_forms_and_evidence,
	get_tender_configuration_price_schedule as _get_tender_configuration_price_schedule,
	get_tender_configuration_system_inventory as _get_tender_configuration_system_inventory,
	get_tender_configuration_tds as _get_tender_configuration_tds,
	get_tender_configurations_dashboard as _get_tender_configurations_dashboard,
	request_tender_configuration_clarification as _request_tender_configuration_clarification,
	resolve_tender_configuration_review_finding as _resolve_tender_configuration_review_finding,
	return_tender_configuration_for_correction as _return_tender_configuration_for_correction,
	return_tender_configuration_preview_for_correction as _return_tender_configuration_preview_for_correction,
	run_tender_configuration_readiness_check as _run_tender_configuration_readiness_check,
	save_tender_configuration_contract_values as _save_tender_configuration_contract_values,
	save_tender_configuration_evaluation_setup as _save_tender_configuration_evaluation_setup,
	save_tender_configuration_forms_and_evidence as _save_tender_configuration_forms_and_evidence,
	save_tender_configuration_implementation_schedule as _save_tender_configuration_implementation_schedule,
	save_tender_configuration_price_schedule as _save_tender_configuration_price_schedule,
	save_tender_configuration_profile as _save_tender_configuration_profile,
	save_tender_configuration_requirements as _save_tender_configuration_requirements,
	save_tender_configuration_review as _save_tender_configuration_review,
	save_tender_configuration_system_inventory as _save_tender_configuration_system_inventory,
	save_tender_configuration_tds as _save_tender_configuration_tds,
	send_tender_configuration_to_publication_workflow as _send_tender_configuration_to_publication_workflow,
	submit_tender_configuration_for_review as _submit_tender_configuration_for_review,
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
def get_tender_configuration_implementation_schedule(configuration_id: str):
	return _get_tender_configuration_implementation_schedule(configuration_id)


@frappe.whitelist()
def save_tender_configuration_implementation_schedule(configuration_id: str, payload=None):
	return _save_tender_configuration_implementation_schedule(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_system_inventory(configuration_id: str):
	return _get_tender_configuration_system_inventory(configuration_id)


@frappe.whitelist()
def save_tender_configuration_system_inventory(configuration_id: str, payload=None):
	return _save_tender_configuration_system_inventory(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_price_schedule(configuration_id: str):
	return _get_tender_configuration_price_schedule(configuration_id)


@frappe.whitelist()
def save_tender_configuration_price_schedule(configuration_id: str, payload=None):
	return _save_tender_configuration_price_schedule(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_evaluation_setup(configuration_id: str):
	return _get_tender_configuration_evaluation_setup(configuration_id)


@frappe.whitelist()
def save_tender_configuration_evaluation_setup(configuration_id: str, payload=None):
	return _save_tender_configuration_evaluation_setup(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_forms_and_evidence(configuration_id: str):
	return _get_tender_configuration_forms_and_evidence(configuration_id)


@frappe.whitelist()
def save_tender_configuration_forms_and_evidence(configuration_id: str, payload=None):
	return _save_tender_configuration_forms_and_evidence(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_contract_values(configuration_id: str):
	return _get_tender_configuration_contract_values(configuration_id)


@frappe.whitelist()
def save_tender_configuration_contract_values(configuration_id: str, payload=None):
	return _save_tender_configuration_contract_values(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_readiness(configuration_id: str):
	return _get_tender_configuration_readiness(configuration_id)


@frappe.whitelist()
def run_tender_configuration_readiness_check(configuration_id: str):
	return _run_tender_configuration_readiness_check(configuration_id)


@frappe.whitelist()
def submit_tender_configuration_for_review(configuration_id: str, payload=None):
	return _submit_tender_configuration_for_review(configuration_id, payload)


@frappe.whitelist()
def get_tender_configuration_review(configuration_id: str):
	return _get_tender_configuration_review(configuration_id)


@frappe.whitelist()
def save_tender_configuration_review(configuration_id: str, payload=None):
	return _save_tender_configuration_review(configuration_id, payload)


@frappe.whitelist()
def approve_tender_configuration_for_preview(configuration_id: str, payload=None):
	return _approve_tender_configuration_for_preview(configuration_id, payload)


@frappe.whitelist()
def return_tender_configuration_for_correction(configuration_id: str, payload=None):
	return _return_tender_configuration_for_correction(configuration_id, payload)


@frappe.whitelist()
def request_tender_configuration_clarification(configuration_id: str, payload=None):
	return _request_tender_configuration_clarification(configuration_id, payload)


@frappe.whitelist()
def resolve_tender_configuration_review_finding(configuration_id: str, finding_id: str):
	return _resolve_tender_configuration_review_finding(configuration_id, finding_id)


@frappe.whitelist()
def get_tender_configuration_document_preview(configuration_id: str):
	return _get_tender_configuration_document_preview(configuration_id)


@frappe.whitelist()
def generate_tender_configuration_document_preview(configuration_id: str):
	return _generate_tender_configuration_document_preview(configuration_id)


@frappe.whitelist()
def confirm_tender_configuration_document_preview(configuration_id: str, payload=None):
	return _confirm_tender_configuration_document_preview(configuration_id, payload)


@frappe.whitelist()
def return_tender_configuration_preview_for_correction(configuration_id: str, payload=None):
	return _return_tender_configuration_preview_for_correction(configuration_id, payload)


@frappe.whitelist()
def send_tender_configuration_to_publication_workflow(configuration_id: str):
	return _send_tender_configuration_to_publication_workflow(configuration_id)


@frappe.whitelist()
def download_tender_configuration_document_preview_pdf(configuration_id: str):
	return _download_tender_configuration_document_preview_pdf(configuration_id)


@frappe.whitelist()
def seed_ui00_dashboard_for_tests(clear: int | str = 1):
	"""Administrator-only seed for Playwright / integration fixtures."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard

	return seed_ui00_dashboard(clear=bool(int(clear)))


@frappe.whitelist()
def prepare_wg01_returned_corrections_for_tests():
	"""Administrator-only: return seeded Under Review config with one open correction (WG-01)."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.constants import STATUS_UNDER_REVIEW
	from kentender_procurement.tender_configurations.services.readiness import get_readiness_report
	from kentender_procurement.tender_configurations.services.review_workspace import (
		return_for_correction,
	)

	configuration_id = "TCFG-SEED-TCFG-UR"
	if not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Seed configuration missing. Run UI-00 seed first."), title="SEED_REQUIRED")
	# Ensure returnable status even if a prior test already returned it.
	import json

	frappe.db.set_value(
		"Tender Configuration",
		configuration_id,
		{
			"status": STATUS_UNDER_REVIEW,
			"review_workspace": json.dumps({"checklist": [], "findings": [], "decisions": []}),
		},
		update_modified=False,
	)
	frappe.db.commit()
	return_for_correction(
		configuration_id,
		{
			"affected_section": "CFG-03",
			"correction_required": "Playwright correction item",
		},
	)
	report = get_readiness_report(configuration_id)
	open_items = [
		f
		for f in (report.get("review_corrections") or [])
		if (f.get("status") or "Open") in ("", "Open")
	]
	finding_id = (open_items[0] or {}).get("id") if open_items else ""
	return {
		"configuration_id": configuration_id,
		"finding_id": finding_id,
		"open_correction_count": report.get("open_correction_count") or 0,
	}


@frappe.whitelist()
def seed_ui01_mockups_for_tests(clear: int | str = 1):
	"""Administrator-only UI-01 mockups: SHOWCASE + CFG-01…09 focus configs."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.ui01_mockup_seed import (
		seed_ui01_mockup_configurations,
	)

	return seed_ui01_mockup_configurations(clear=bool(int(clear)))
