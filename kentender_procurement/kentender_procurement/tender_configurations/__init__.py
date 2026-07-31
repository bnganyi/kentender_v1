# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Configurations module — C1-M2 documented API entrypoints."""

from __future__ import annotations

import frappe

from kentender_procurement.tender_configurations.api import (
	approve_tender_configuration_for_preview as _approve_tender_configuration_for_preview,
	confirm_tender_configuration_document_preview as _confirm_tender_configuration_document_preview,
	create_tender_configuration as _create_tender_configuration,
	download_published_tender_document_pdf as _download_published_tender_document_pdf,
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
	get_tender_configuration_bidder_submission_schema as _get_tender_configuration_bidder_submission_schema,
	get_tender_configuration_carry_forward_bundle as _get_tender_configuration_carry_forward_bundle,
	get_electronic_bidder_workspace as _get_electronic_bidder_workspace,
	create_electronic_bid_draft as _create_electronic_bid_draft,
	save_electronic_bid_section as _save_electronic_bid_section,
	validate_electronic_bid as _validate_electronic_bid,
	submit_and_seal_electronic_bid as _submit_and_seal_electronic_bid,
	get_electronic_bid_receipt as _get_electronic_bid_receipt,
	fill_electronic_bid_draft_for_tests as _fill_electronic_bid_draft_for_tests,
	get_published_tender_overview as _get_published_tender_overview,
	start_or_get_bid_workspace as _start_or_get_bid_workspace,
	get_submission_checklist as _get_submission_checklist,
	get_tender_documents_addenda as _get_tender_documents_addenda,
	acknowledge_tender_documents as _acknowledge_tender_documents,
	append_issued_addendum as _append_issued_addendum,
	get_requirement_matrix as _get_requirement_matrix,
	get_requirement_drawer as _get_requirement_drawer,
	save_requirement_response as _save_requirement_response,
	get_requirements_compliance_review as _get_requirements_compliance_review,
	complete_requirements_compliance_section as _complete_requirements_compliance_section,
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
	confirm_tender_package as _confirm_tender_package,
	get_package_review_summary as _get_package_review_summary,
	list_publications as _list_publications,
	get_publication_setup as _get_publication_setup,
	save_publication_setup as _save_publication_setup,
	publish_tender as _publish_tender,
	return_publication_for_correction as _return_publication_for_correction,
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
def confirm_tender_package(configuration_id: str, payload=None):
	return _confirm_tender_package(configuration_id, payload)


@frappe.whitelist()
def get_package_review_summary(configuration_id: str):
	return _get_package_review_summary(configuration_id)


@frappe.whitelist()
def list_publications(tab=None, search=None, page=None, page_size=None):
	return _list_publications(tab=tab, search=search, page=page, page_size=page_size)


@frappe.whitelist()
def get_publication_setup(publication_id: str):
	return _get_publication_setup(publication_id)


@frappe.whitelist()
def save_publication_setup(publication_id: str, payload=None):
	return _save_publication_setup(publication_id, payload)


@frappe.whitelist()
def publish_tender(publication_id: str):
	return _publish_tender(publication_id)


@frappe.whitelist()
def return_publication_for_correction(publication_id: str, payload=None):
	return _return_publication_for_correction(publication_id, payload)


@frappe.whitelist()
def download_tender_configuration_document_preview_pdf(configuration_id: str):
	return _download_tender_configuration_document_preview_pdf(configuration_id)


@frappe.whitelist()
def download_published_tender_document_pdf(published_tender_ref: str):
	return _download_published_tender_document_pdf(published_tender_ref)


@frappe.whitelist()
def seed_ui00_dashboard_for_tests(clear: int | str = 1):
	"""Administrator-only seed for Playwright / integration fixtures."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard

	return seed_ui00_dashboard(clear=bool(int(clear)))


@frappe.whitelist()
def seed_publications_demo_for_tests(clear: int | str = 0):
	"""Administrator-only: seed Publications queue tab coverage."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.publications_seed import (
		seed_publications_demo,
	)

	return seed_publications_demo(clear=bool(int(clear)))


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


@frappe.whitelist()
def seed_demand_to_bidder_journey_sample_for_tests(clear: int | str = 1):
	"""Quiet Demand (Draft + Planning Ready) + CFG-01…09 + one Published lean tender."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.demand_to_bidder_journey_sample import (
		run as _run_journey,
	)

	return _run_journey(clear=bool(int(clear)))


@frappe.whitelist()
def get_tender_configuration_bidder_submission_schema(configuration_id: str):
	return _get_tender_configuration_bidder_submission_schema(configuration_id)


@frappe.whitelist()
def seed_e1_nssf_for_tests(clear: int | str = 1):
	"""Administrator-only E1 NSSF PoC seed (fixture 09 → TCFG-E1-NSSF-ERP)."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.e1_nssf_seed import (
		seed_e1_nssf_tender_configuration,
	)

	return seed_e1_nssf_tender_configuration(clear=bool(int(clear)))


@frappe.whitelist()
def publish_e1_nssf_lean_for_tests(clear: int | str = 1):
	"""Administrator-only: seed NSSF + confirm package + publish with electronic template snapshot."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.e1_nssf_seed import (
		publish_e1_nssf_with_electronic_template,
	)

	return publish_e1_nssf_with_electronic_template(clear=bool(int(clear)))


@frappe.whitelist()
def publish_lean_requirements_compliance_for_tests(
	clear: int | str = 1,
	fixture: str | None = None,
):
	"""Administrator-only: publish lean Requirements Compliance fixture for Playwright smoke."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.lean_requirements_compliance import (
		FIXTURE_STANDARD,
		publish_lean_requirements_compliance_for_tests as _publish,
	)

	return _publish(fixture=fixture or FIXTURE_STANDARD, clear=bool(int(clear)))


@frappe.whitelist()
def seed_bwmf_canonical_for_tests(clear: int | str = 1):
	"""Administrator-only BWMF canonical persistence fixture (G1 Phase 2)."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
		seed_bwmf_canonical_fixture,
	)

	return seed_bwmf_canonical_fixture(clear=bool(int(clear)))


@frappe.whitelist()
def clear_bwmf_canonical_for_tests():
	"""Administrator-only clear of all BWMF persistence rows."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.seed.bwmf_canonical_fixture import (
		clear_bwmf_canonical_fixture,
	)

	return clear_bwmf_canonical_fixture()


@frappe.whitelist()
def get_tender_configuration_carry_forward_bundle(configuration_id: str):
	return _get_tender_configuration_carry_forward_bundle(configuration_id)


@frappe.whitelist()
def get_electronic_bidder_workspace(configuration_id: str):
	return _get_electronic_bidder_workspace(configuration_id)


@frappe.whitelist()
def create_electronic_bid_draft(configuration_id: str, bidder_label: str | None = None):
	return _create_electronic_bid_draft(configuration_id, bidder_label)


@frappe.whitelist()
def save_electronic_bid_section(bid_id: str, section_key: str, payload=None):
	return _save_electronic_bid_section(bid_id, section_key, payload)


@frappe.whitelist()
def validate_electronic_bid(bid_id: str):
	return _validate_electronic_bid(bid_id)


@frappe.whitelist()
def submit_and_seal_electronic_bid(bid_id: str):
	return _submit_and_seal_electronic_bid(bid_id)


@frappe.whitelist()
def get_electronic_bid_receipt(bid_id: str):
	return _get_electronic_bid_receipt(bid_id)


@frappe.whitelist()
def fill_electronic_bid_draft_for_tests(bid_id: str):
	return _fill_electronic_bid_draft_for_tests(bid_id)


@frappe.whitelist()
def get_published_tender_overview(published_tender_ref: str):
	return _get_published_tender_overview(published_tender_ref)


@frappe.whitelist()
def start_or_get_bid_workspace(published_tender_ref: str, bidder_label: str | None = None):
	return _start_or_get_bid_workspace(published_tender_ref, bidder_label=bidder_label)


@frappe.whitelist()
def get_submission_checklist(published_tender_ref: str):
	return _get_submission_checklist(published_tender_ref)


@frappe.whitelist()
def get_tender_documents_addenda(published_tender_ref: str):
	return _get_tender_documents_addenda(published_tender_ref)


@frappe.whitelist()
def acknowledge_tender_documents(published_tender_ref: str):
	return _acknowledge_tender_documents(published_tender_ref)


@frappe.whitelist()
def append_issued_addendum(publication_id: str, row=None):
	"""Administrator-only: append an issued addendum for S100 tests / calibration."""
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	import json as _json

	if isinstance(row, str):
		row = _json.loads(row)
	return _append_issued_addendum(publication_id, row or {})


@frappe.whitelist()
def get_requirement_matrix(
	published_tender_ref: str,
	section_key: str,
	group: str | None = None,
	q: str | None = None,
	status: str | None = None,
	page: int | str = 1,
	page_size: int | str = 10,
):
	return _get_requirement_matrix(
		published_tender_ref,
		section_key,
		group=group,
		q=q,
		status=status,
		page=int(page or 1),
		page_size=int(page_size or 10),
	)


@frappe.whitelist()
def get_requirement_drawer(published_tender_ref: str, section_key: str, requirement_id: str):
	return _get_requirement_drawer(published_tender_ref, section_key, requirement_id)


@frappe.whitelist()
def save_requirement_response(
	published_tender_ref: str,
	section_key: str,
	requirement_id: str,
	payload: dict | str | None = None,
):
	return _save_requirement_response(published_tender_ref, section_key, requirement_id, payload)


@frappe.whitelist()
def get_requirements_compliance_review(published_tender_ref: str):
	return _get_requirements_compliance_review(published_tender_ref)


@frappe.whitelist()
def complete_requirements_compliance_section(published_tender_ref: str):
	return _complete_requirements_compliance_section(published_tender_ref)


@frappe.whitelist()
def get_evidence_register(published_tender_ref: str):
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		get_evidence_register as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def upload_evidence(
	published_tender_ref: str,
	title: str | None = None,
	evidence_type: str | None = None,
	filename: str | None = None,
	content_b64: str | None = None,
	content_type: str | None = None,
	metadata=None,
):
	from kentender_procurement.tender_configurations.api import upload_evidence as _upload

	return _upload(
		published_tender_ref,
		title=title,
		evidence_type=evidence_type,
		filename=filename,
		content_b64=content_b64,
		content_type=content_type,
		metadata=metadata,
	)


@frappe.whitelist()
def replace_evidence(
	published_tender_ref: str,
	evidence_id: str,
	filename: str | None = None,
	content_b64: str | None = None,
	content_type: str | None = None,
):
	from kentender_procurement.tender_configurations.api import replace_evidence as _replace

	return _replace(
		published_tender_ref,
		evidence_id,
		filename=filename,
		content_b64=content_b64,
		content_type=content_type,
	)


@frappe.whitelist()
def link_evidence(
	published_tender_ref: str,
	evidence_id: str,
	target_kind: str | None = None,
	target_key: str | None = None,
):
	from kentender_procurement.tender_configurations.api import link_evidence as _link

	return _link(published_tender_ref, evidence_id, target_kind=target_kind, target_key=target_key)


@frappe.whitelist()
def unlink_evidence(
	published_tender_ref: str,
	evidence_id: str,
	target_kind: str | None = None,
	target_key: str | None = None,
):
	from kentender_procurement.tender_configurations.api import unlink_evidence as _unlink

	return _unlink(published_tender_ref, evidence_id, target_kind=target_kind, target_key=target_key)


@frappe.whitelist()
def get_issue_register(published_tender_ref: str):
	from kentender_procurement.tender_configurations.services.bid_issues import (
		get_issue_register as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_qualification_and_capability(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import (
		get_qualification_and_capability as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_qualification_category(published_tender_ref: str, category_key: str):
	from kentender_procurement.tender_configurations.api import (
		get_qualification_category as _get,
	)

	return _get(published_tender_ref, category_key)


@frappe.whitelist()
def save_qualification_category(
	published_tender_ref: str,
	category_key: str,
	payload=None,
	expected_modified: str | None = None,
):
	from kentender_procurement.tender_configurations.api import (
		save_qualification_category as _save,
	)

	return _save(
		published_tender_ref,
		category_key,
		payload,
		expected_modified=expected_modified,
	)


@frappe.whitelist()
def get_technical_proposal(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import get_technical_proposal as _get

	return _get(published_tender_ref)


@frappe.whitelist()
def get_technical_proposal_subsection(published_tender_ref: str, subsection_key: str):
	from kentender_procurement.tender_configurations.api import (
		get_technical_proposal_subsection as _get,
	)

	return _get(published_tender_ref, subsection_key)


@frappe.whitelist()
def get_technical_proposal_review(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import (
		get_technical_proposal_review as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_technical_proposal_subsection(
	published_tender_ref: str,
	subsection_key: str,
	payload=None,
	expected_modified: str | None = None,
):
	from kentender_procurement.tender_configurations.api import (
		save_technical_proposal_subsection as _save,
	)

	return _save(
		published_tender_ref,
		subsection_key,
		payload,
		expected_modified=expected_modified,
	)


@frappe.whitelist()
def confirm_technical_proposal_integration(
	published_tender_ref: str,
	expected_modified: str | None = None,
):
	from kentender_procurement.tender_configurations.api import (
		confirm_technical_proposal_integration as _confirm,
	)

	return _confirm(published_tender_ref, expected_modified=expected_modified)


@frappe.whitelist()
def get_price_schedule_overview(published_tender_ref: str, offer_id: str | None = None, lot_id: str | None = None):
	from kentender_procurement.tender_configurations.api import get_price_schedule_overview as _get

	return _get(published_tender_ref, offer_id=offer_id, lot_id=lot_id)


@frappe.whitelist()
def get_price_schedule_editor(
	published_tender_ref: str,
	schedule_key: str,
	offer_id: str | None = None,
	lot_id: str | None = None,
):
	from kentender_procurement.tender_configurations.api import get_price_schedule_editor as _get

	return _get(published_tender_ref, schedule_key, offer_id=offer_id, lot_id=lot_id)


@frappe.whitelist()
def get_price_schedule_review(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import get_price_schedule_review as _get

	return _get(published_tender_ref)


@frappe.whitelist()
def save_price_schedule_lines(published_tender_ref: str, payload=None):
	from kentender_procurement.tender_configurations.api import save_price_schedule_lines as _save

	return _save(published_tender_ref, payload)


@frappe.whitelist()
def complete_price_schedule(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import complete_price_schedule as _complete

	return _complete(published_tender_ref)


@frappe.whitelist()
def publish_lean_price_schedule_for_tests(fixture: str = "single_lot", clear: int | bool = 1):
	from kentender_procurement.tender_configurations.api import (
		publish_lean_price_schedule_for_tests as _publish,
	)

	return _publish(fixture=fixture, clear=clear)


@frappe.whitelist()
def get_bid_submission_readiness(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import (
		get_bid_submission_readiness as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_final_bid_review(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import get_final_bid_review as _get

	return _get(published_tender_ref)


@frappe.whitelist()
def get_submit_bid_page(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import get_submit_bid_page as _get

	return _get(published_tender_ref)


@frappe.whitelist()
def submit_electronic_bid(published_tender_ref: str, declaration_confirmed: int | bool | str = 0):
	from kentender_procurement.tender_configurations.api import submit_electronic_bid as _submit

	return _submit(published_tender_ref, declaration_confirmed=declaration_confirmed)


@frappe.whitelist()
def get_submission_receipt(published_tender_ref: str):
	from kentender_procurement.tender_configurations.api import get_submission_receipt as _get

	return _get(published_tender_ref)


@frappe.whitelist()
def seed_ready_lean_bid_for_final_submission_tests(fixture: str = "single_lot", clear: int | bool = 1):
	from kentender_procurement.tender_configurations.api import (
		seed_ready_lean_bid_for_final_submission_tests as _seed,
	)

	return _seed(fixture=fixture, clear=clear)


@frappe.whitelist()
def list_bid_submission_tenders(search=None, stage=None, page=1, page_size=20):
	from kentender_procurement.tender_configurations.api import list_bid_submission_tenders as _list

	return _list(search=search, stage=stage, page=page, page_size=page_size)


@frappe.whitelist()
def get_bid_submission_sealed_status(publication_id: str):
	from kentender_procurement.tender_configurations.api import get_bid_submission_sealed_status as _get

	return _get(publication_id)


@frappe.whitelist()
def open_submitted_bids(publication_id: str):
	from kentender_procurement.tender_configurations.api import open_submitted_bids as _open

	return _open(publication_id)


@frappe.whitelist()
def get_opening_register(publication_id: str):
	from kentender_procurement.tender_configurations.api import get_opening_register as _get

	return _get(publication_id)


@frappe.whitelist()
def get_submitted_bid_overview(publication_id: str, bid_id: str):
	from kentender_procurement.tender_configurations.api import get_submitted_bid_overview as _get

	return _get(publication_id, bid_id)


@frappe.whitelist()
def get_submitted_section_response(publication_id: str, bid_id: str, section_key: str):
	from kentender_procurement.tender_configurations.api import get_submitted_section_response as _get

	return _get(publication_id, bid_id, section_key)


@frappe.whitelist()
def get_submission_receipt_view(publication_id: str, bid_id: str):
	from kentender_procurement.tender_configurations.api import get_submission_receipt_view as _get

	return _get(publication_id, bid_id)


@frappe.whitelist()
def get_opening_record_view(publication_id: str):
	from kentender_procurement.tender_configurations.api import get_opening_record_view as _get

	return _get(publication_id)


@frappe.whitelist()
def download_submitted_evidence(publication_id: str, bid_id: str, evidence_key: str):
	from kentender_procurement.tender_configurations.api import download_submitted_evidence as _dl

	return _dl(publication_id, bid_id, evidence_key)


@frappe.whitelist()
def get_submission_version_history(publication_id: str):
	from kentender_procurement.tender_configurations.api import get_submission_version_history as _get

	return _get(publication_id)


@frappe.whitelist()
def seed_bid_submissions_officer_fixtures(clear: int | bool = 1):
	from kentender_procurement.tender_configurations.api import (
		seed_bid_submissions_officer_fixtures as _seed,
	)

	return _seed(clear=clear)
