# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Whitelisted Tender Configurations APIs (UI-00 / UI-M01 / UI-01)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

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


# --- WG-01 Readiness ---


@frappe.whitelist()
def get_tender_configuration_readiness(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.readiness import get_readiness_report

	return get_readiness_report(configuration_id)


@frappe.whitelist()
def run_tender_configuration_readiness_check(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.readiness import run_readiness_check

	return run_readiness_check(configuration_id)


@frappe.whitelist()
def submit_tender_configuration_for_review(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.readiness import submit_for_review

	return submit_for_review(configuration_id, payload)


# --- WG-02 Review ---


@frappe.whitelist()
def get_tender_configuration_review(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.review_workspace import (
		get_review_workspace,
	)

	return get_review_workspace(configuration_id)


@frappe.whitelist()
def save_tender_configuration_review(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.review_workspace import (
		save_review_workspace,
	)

	return save_review_workspace(configuration_id, payload)


@frappe.whitelist()
def approve_tender_configuration_for_preview(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.review_workspace import (
		approve_for_preview,
	)

	return approve_for_preview(configuration_id, payload)


@frappe.whitelist()
def return_tender_configuration_for_correction(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.review_workspace import (
		return_for_correction,
	)

	return return_for_correction(configuration_id, payload)


@frappe.whitelist()
def request_tender_configuration_clarification(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.review_workspace import (
		request_clarification,
	)

	return request_clarification(configuration_id, payload)


@frappe.whitelist()
def resolve_tender_configuration_review_finding(
	configuration_id: str,
	finding_id: str,
) -> dict[str, Any]:
	"""Preparer marks a returned Correction Required finding as fixed (WG-01)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.review_workspace import (
		resolve_review_finding,
	)

	return resolve_review_finding(configuration_id, finding_id)


# --- WG-03 Preview + Handoff ---


@frappe.whitelist()
def get_tender_configuration_document_preview(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		get_document_preview,
	)

	return get_document_preview(configuration_id)


@frappe.whitelist()
def generate_tender_configuration_document_preview(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		generate_document_preview,
	)

	return generate_document_preview(configuration_id)


@frappe.whitelist()
def confirm_tender_configuration_document_preview(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_document_preview,
	)

	return confirm_document_preview(configuration_id, payload)


@frappe.whitelist()
def return_tender_configuration_preview_for_correction(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		return_preview_for_correction,
	)

	return return_preview_for_correction(configuration_id, payload)


@frappe.whitelist()
def send_tender_configuration_to_publication_workflow(configuration_id: str) -> dict[str, Any]:
	"""Legacy shim — prefer confirm_tender_package / confirm preview (auto-opens setup)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		send_to_publication_workflow,
	)

	return send_to_publication_workflow(configuration_id)


@frappe.whitelist()
def confirm_tender_package(
	configuration_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		confirm_tender_package as _confirm_tender_package,
	)

	return _confirm_tender_package(configuration_id, payload)


@frappe.whitelist()
def get_package_review_summary(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.package_review import (
		get_package_review_summary as _get,
	)

	return _get(configuration_id)


@frappe.whitelist()
def list_publications(
	tab: str | None = None,
	search: str | None = None,
	page: int | str | None = None,
	page_size: int | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.publication_setup import (
		list_publications as _list,
	)

	return _list(tab=tab, search=search, page=page, page_size=page_size)


@frappe.whitelist()
def get_publication_setup(publication_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.publication_setup import (
		get_publication_setup as _get,
	)

	return _get(publication_id)


@frappe.whitelist()
def save_publication_setup(
	publication_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.publication_setup import (
		save_publication_setup as _save,
	)

	return _save(publication_id, payload)


@frappe.whitelist()
def publish_tender(publication_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.publication_setup import (
		publish_tender as _publish,
	)

	return _publish(publication_id)


@frappe.whitelist()
def return_publication_for_correction(
	publication_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.publication_setup import (
		return_publication_for_correction as _ret,
	)

	return _ret(publication_id, payload)


@frappe.whitelist()
def download_tender_configuration_document_preview_pdf(configuration_id: str) -> None:
	_require_login()
	from kentender_procurement.tender_configurations.services.document_preview import (
		download_document_preview_pdf,
	)

	return download_document_preview_pdf(configuration_id)


@frappe.whitelist()
def download_published_tender_document_pdf(published_tender_ref: str) -> None:
	"""Bidder-facing PDF download keyed by public publication_ref (no configuration_id)."""
	_require_login()
	from frappe.utils import cstr

	from kentender_procurement.tender_configurations.services.document_preview import (
		download_document_preview_pdf,
	)
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		resolve_published_tender_backend,
	)

	ref = cstr(published_tender_ref or "").strip()
	backend = resolve_published_tender_backend(ref)
	return download_document_preview_pdf(cstr(backend.get("configuration_id") or ""))


@frappe.whitelist()
def get_tender_configuration_bidder_submission_schema(configuration_id: str) -> dict[str, Any]:
	"""Return persisted electronic bidder submission schema artifact (E1 Phase 1)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.bidder_submission_schema import (
		get_bidder_submission_schema,
	)

	return get_bidder_submission_schema(configuration_id)


@frappe.whitelist()
def get_tender_configuration_carry_forward_bundle(configuration_id: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.contract_carry_forward import (
		get_carry_forward_bundle,
	)

	return get_carry_forward_bundle(configuration_id)


@frappe.whitelist()
def get_electronic_bidder_workspace(configuration_id: str) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		get_bidder_workspace,
	)

	return get_bidder_workspace(configuration_id)


@frappe.whitelist()
def create_electronic_bid_draft(configuration_id: str, bidder_label: str | None = None) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		create_or_get_draft,
	)

	return create_or_get_draft(configuration_id, bidder_label)


@frappe.whitelist()
def save_electronic_bid_section(
	bid_id: str,
	section_key: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		save_section_responses,
	)

	return save_section_responses(bid_id, section_key, payload)


@frappe.whitelist()
def validate_electronic_bid(bid_id: str) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		validate_submission,
	)

	return validate_submission(bid_id)


@frappe.whitelist()
def submit_and_seal_electronic_bid(bid_id: str) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		submit_and_seal,
	)

	return submit_and_seal(bid_id)


@frappe.whitelist()
def get_electronic_bid_receipt(bid_id: str) -> dict[str, Any]:
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		get_receipt,
	)

	return get_receipt(bid_id)


@frappe.whitelist()
def fill_electronic_bid_draft_for_tests(bid_id: str) -> dict[str, Any]:
	"""Administrator helper for Playwright / integration tests."""
	from kentender_procurement.tender_configurations.services.electronic_bid import (
		fill_draft_for_tests,
	)

	return fill_draft_for_tests(bid_id)


@frappe.whitelist()
def get_published_tender_overview(published_tender_ref: str) -> dict[str, Any]:
	"""Bidder A1 — published tender overview DTO (keyed by publication_ref)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		get_published_tender_overview as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def start_or_get_bid_workspace(
	published_tender_ref: str,
	bidder_label: str | None = None,
) -> dict[str, Any]:
	"""Bidder A1 — start or resume bid workspace for a published tender."""
	_require_login()
	from kentender_procurement.tender_configurations.services.published_tender_overview import (
		start_or_get_bid_workspace as _start,
	)

	return _start(published_tender_ref, bidder_label=bidder_label)


@frappe.whitelist()
def get_submission_checklist(published_tender_ref: str) -> dict[str, Any]:
	"""Bidder A2 — Submission Checklist (workspace home) DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.submission_checklist import (
		get_submission_checklist as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_form_of_tender(published_tender_ref: str) -> dict[str, Any]:
	"""Lean Website Form of Tender DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		get_form_of_tender as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_form_of_tender(
	published_tender_ref: str,
	payload: dict[str, Any] | str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save Form of Tender commissions disclosure (does not certify)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		save_form_of_tender as _save,
	)

	return _save(published_tender_ref, payload, expected_modified=expected_modified)


@frappe.whitelist()
def certify_form_of_tender(
	published_tender_ref: str,
	offer_id: str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Certify one Form of Tender instance (Review and Certify)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.form_of_tender import (
		certify_form_of_tender as _cert,
	)

	return _cert(
		published_tender_ref,
		offer_id=offer_id,
		expected_modified=expected_modified,
	)


@frappe.whitelist()
def get_statutory_declarations(published_tender_ref: str) -> dict[str, Any]:
	"""Statutory Declarations Review-and-Certify DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.statutory_declarations import (
		get_statutory_declarations as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_statutory_declarations(
	published_tender_ref: str,
	payload: dict[str, Any] | str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save independent-tender answer and competitor disclosures (does not certify)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.statutory_declarations import (
		save_statutory_declarations as _save,
	)

	return _save(published_tender_ref, payload, expected_modified=expected_modified)


@frappe.whitelist()
def certify_statutory_declarations(
	published_tender_ref: str,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Atomically certify the four statutory declaration legal records."""
	_require_login()
	from kentender_procurement.tender_configurations.services.statutory_declarations import (
		certify_statutory_declarations as _cert,
	)

	return _cert(published_tender_ref, expected_modified=expected_modified)


@frappe.whitelist()
def get_preliminary_requirements(published_tender_ref: str) -> dict[str, Any]:
	"""Preliminary Requirements and Evidence checklist DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.preliminary_requirements import (
		get_preliminary_requirements as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_preliminary_response(
	published_tender_ref: str,
	criterion_id: str,
	payload: dict[str, Any] | str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save one preliminary criterion response (upload / select / verification / structured)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.preliminary_requirements import (
		save_preliminary_response as _save,
	)

	return _save(
		published_tender_ref,
		criterion_id,
		payload,
		expected_modified=expected_modified,
	)


@frappe.whitelist()
def get_qualification_and_capability(published_tender_ref: str) -> dict[str, Any]:
	"""Qualification and Capability overview DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.qualification_and_capability import (
		get_qualification_and_capability as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_qualification_category(published_tender_ref: str, category_key: str) -> dict[str, Any]:
	"""One qualification category detail DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.qualification_and_capability import (
		get_qualification_category as _get,
	)

	return _get(published_tender_ref, category_key)


@frappe.whitelist()
def save_qualification_category(
	published_tender_ref: str,
	category_key: str,
	payload: dict[str, Any] | str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save one qualification category bucket (+ optional shared collections)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.qualification_and_capability import (
		save_qualification_category as _save,
	)

	return _save(
		published_tender_ref,
		category_key,
		payload,
		expected_modified=expected_modified,
	)


@frappe.whitelist()
def get_technical_proposal(published_tender_ref: str) -> dict[str, Any]:
	"""Technical Proposal and Implementation Plan overview DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
		get_technical_proposal as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_technical_proposal_subsection(published_tender_ref: str, subsection_key: str) -> dict[str, Any]:
	"""One technical proposal subsection detail DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
		get_technical_proposal_subsection as _get,
	)

	return _get(published_tender_ref, subsection_key)


@frappe.whitelist()
def get_technical_proposal_review(published_tender_ref: str) -> dict[str, Any]:
	"""Technical Proposal review + integration confirmation DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
		get_technical_proposal_review as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_technical_proposal_subsection(
	published_tender_ref: str,
	subsection_key: str,
	payload: dict[str, Any] | str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save one technical proposal subsection bucket."""
	_require_login()
	from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
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
) -> dict[str, Any]:
	"""Confirm integration/interoperability responsibility (does not seal the bid)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.technical_proposal_and_implementation_plan import (
		confirm_integration_responsibility as _confirm,
	)

	return _confirm(published_tender_ref, expected_modified=expected_modified)


@frappe.whitelist()
def get_tender_security(published_tender_ref: str) -> dict[str, Any]:
	"""Tender Security instrument or Tender-Securing Declaration DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tender_security import (
		get_tender_security as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_tender_security(
	published_tender_ref: str,
	payload: dict[str, Any] | str | None = None,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Save tender security instrument details (structural validation only)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tender_security import (
		save_tender_security as _save,
	)

	return _save(published_tender_ref, payload, expected_modified=expected_modified)


@frappe.whitelist()
def certify_tender_securing_declaration(
	published_tender_ref: str,
	expected_modified: str | None = None,
) -> dict[str, Any]:
	"""Certify the Tender-Securing Declaration."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tender_security import (
		certify_tender_securing_declaration as _cert,
	)

	return _cert(published_tender_ref, expected_modified=expected_modified)


@frappe.whitelist()
def get_confidential_business_questionnaire(published_tender_ref: str) -> dict[str, Any]:
	"""S300 — Confidential Business Questionnaire DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		get_confidential_business_questionnaire as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_confidential_business_questionnaire(
	published_tender_ref: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""S300 — save CBQ draft (does not certify)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		save_confidential_business_questionnaire as _save,
	)
	import json as _json

	if isinstance(payload, str):
		payload = _json.loads(payload) if payload else {}
	return _save(published_tender_ref, payload)


@frappe.whitelist()
def add_cbq_jv_entity(published_tender_ref: str, legal_name: str | None = None) -> dict[str, Any]:
	"""S300 — add a JV member questionnaire instance."""
	_require_login()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		add_jv_entity as _add,
	)

	return _add(published_tender_ref, legal_name or "")


@frappe.whitelist()
def certify_cbq_entity(
	published_tender_ref: str,
	entity_id: str,
	certifier_name: str | None = None,
	certifier_title: str | None = None,
	authority_affirmed: int | str | bool | None = None,
) -> dict[str, Any]:
	"""S300 — deliberate entity-scoped CBQ certification."""
	_require_login()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		certify_cbq_entity as _cert,
	)

	return _cert(
		published_tender_ref,
		entity_id,
		certifier_name=certifier_name,
		certifier_title=certifier_title,
		authority_affirmed=authority_affirmed,
	)


@frappe.whitelist()
def amend_cbq_certification(published_tender_ref: str, entity_id: str) -> dict[str, Any]:
	"""S300 — confirm amend after certification; clears the cert record."""
	_require_login()
	from kentender_procurement.tender_configurations.services.confidential_business_questionnaire import (
		amend_cbq_certification as _amend,
	)

	return _amend(published_tender_ref, entity_id)


@frappe.whitelist()
def get_tender_documents_addenda(published_tender_ref: str) -> dict[str, Any]:
	"""Bidder A3 — Tender Documents & Addenda DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		get_tender_documents_addenda as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def acknowledge_tender_documents(published_tender_ref: str) -> dict[str, Any]:
	"""Bidder A3 — acknowledge official tender documents (document_acknowledgement section)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		acknowledge_tender_documents as _ack,
	)

	return _ack(published_tender_ref)


@frappe.whitelist()
def append_issued_addendum(publication_id: str, row: dict[str, Any] | str | None = None) -> dict[str, Any]:
	"""Administrator-only — append an issued addendum to the publication register (S100)."""
	_require_login()
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	from kentender_procurement.tender_configurations.services.tender_documents_addenda import (
		append_issued_addendum as _append,
	)

	if isinstance(row, str):
		row = json.loads(row)
	return _append(publication_id, row or {})


@frappe.whitelist()
def get_requirement_matrix(
	published_tender_ref: str,
	section_key: str,
	group: str | None = None,
	q: str | None = None,
	status: str | None = None,
	page: int | str = 1,
	page_size: int | str = 10,
) -> dict[str, Any]:
	"""Bidder A4 — Requirement Matrix section DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		get_requirement_matrix as _get,
	)

	return _get(
		published_tender_ref,
		section_key,
		group=group,
		q=q,
		status=status,
		page=int(page or 1),
		page_size=int(page_size or 10),
	)


@frappe.whitelist()
def get_requirement_drawer(
	published_tender_ref: str,
	section_key: str,
	requirement_id: str,
) -> dict[str, Any]:
	"""Bidder A4 — Requirement response drawer DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		get_requirement_drawer as _get,
	)

	return _get(published_tender_ref, section_key, requirement_id)


@frappe.whitelist()
def save_requirement_response(
	published_tender_ref: str,
	section_key: str,
	requirement_id: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""Bidder A4 — merge-save one requirement response into electronic bid section map."""
	_require_login()
	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		save_requirement_response as _save,
	)

	return _save(published_tender_ref, section_key, requirement_id, payload)


@frappe.whitelist()
def get_requirements_compliance_review(published_tender_ref: str) -> dict[str, Any]:
	"""Requirements Compliance review screen DTO."""
	_require_login()
	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		get_requirements_compliance_review as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def complete_requirements_compliance_section(published_tender_ref: str) -> dict[str, Any]:
	"""Complete Requirements Compliance when ready (does not seal the bid)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.requirement_matrix import (
		complete_requirements_compliance_section as _complete,
	)

	return _complete(published_tender_ref)


@frappe.whitelist()
def get_evidence_register(published_tender_ref: str) -> dict[str, Any]:
	"""X100 — bidder Evidence Register DTO."""
	_require_login()
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
	metadata: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		upload_evidence as _upload,
	)

	return _upload(
		published_tender_ref,
		title=cstr(title or ""),
		evidence_type=cstr(evidence_type or "supporting_document"),
		filename=cstr(filename or ""),
		content_b64=content_b64,
		content_type=cstr(content_type or "application/pdf"),
		metadata=metadata,
	)


@frappe.whitelist()
def replace_evidence(
	published_tender_ref: str,
	evidence_id: str,
	filename: str | None = None,
	content_b64: str | None = None,
	content_type: str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		replace_evidence as _replace,
	)

	return _replace(
		published_tender_ref,
		evidence_id=evidence_id,
		filename=cstr(filename or ""),
		content_b64=content_b64,
		content_type=cstr(content_type or "application/pdf"),
	)


@frappe.whitelist()
def link_evidence(
	published_tender_ref: str,
	evidence_id: str,
	target_kind: str | None = None,
	target_key: str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		link_evidence as _link,
	)

	return _link(
		published_tender_ref,
		evidence_id=evidence_id,
		target_kind=cstr(target_kind or "obligation"),
		target_key=cstr(target_key or ""),
	)


@frappe.whitelist()
def unlink_evidence(
	published_tender_ref: str,
	evidence_id: str,
	target_kind: str | None = None,
	target_key: str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.bid_evidence import (
		unlink_evidence as _unlink,
	)

	return _unlink(
		published_tender_ref,
		evidence_id=evidence_id,
		target_kind=cstr(target_kind or "obligation"),
		target_key=cstr(target_key or ""),
	)


@frappe.whitelist()
def get_issue_register(published_tender_ref: str) -> dict[str, Any]:
	"""X100 — bidder Issues register DTO (server-derived)."""
	_require_login()
	from kentender_procurement.tender_configurations.services.bid_issues import (
		get_issue_register as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_price_schedule_overview(published_tender_ref: str, offer_id: str | None = None, lot_id: str | None = None) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
		get_price_schedule_overview as _get,
	)

	return _get(published_tender_ref, offer_id=offer_id, lot_id=lot_id)


@frappe.whitelist()
def get_price_schedule_editor(
	published_tender_ref: str,
	schedule_key: str,
	offer_id: str | None = None,
	lot_id: str | None = None,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
		get_price_schedule_editor as _get,
	)

	return _get(published_tender_ref, schedule_key, offer_id=offer_id, lot_id=lot_id)


@frappe.whitelist()
def get_price_schedule_review(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
		get_price_schedule_review as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def save_price_schedule_lines(published_tender_ref: str, payload: dict[str, Any] | str | None = None) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
		save_price_schedule_lines as _save,
	)

	return _save(published_tender_ref, payload)


@frappe.whitelist()
def complete_price_schedule(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.price_schedule_bidder import (
		complete_price_schedule as _complete,
	)

	return _complete(published_tender_ref)


@frappe.whitelist()
def publish_lean_price_schedule_for_tests(fixture: str = "single_lot", clear: int | bool = 1) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.seed.lean_price_schedule import (
		publish_lean_price_schedule_for_tests as _publish,
	)

	return _publish(fixture=fixture or "single_lot", clear=bool(int(clear)))


@frappe.whitelist()
def get_bid_submission_readiness(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.final_submission import (
		get_bid_submission_readiness as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_final_bid_review(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.final_submission import (
		get_final_bid_review as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def get_submit_bid_page(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.final_submission import (
		get_submit_bid_page as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def submit_electronic_bid(
	published_tender_ref: str,
	declaration_confirmed: int | bool | str = 0,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.final_submission import (
		submit_bid as _submit,
	)

	return _submit(published_tender_ref, declaration_confirmed=declaration_confirmed)


@frappe.whitelist()
def get_submission_receipt(published_tender_ref: str) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.final_submission import (
		get_submission_receipt as _get,
	)

	return _get(published_tender_ref)


@frappe.whitelist()
def seed_ready_lean_bid_for_final_submission_tests(
	fixture: str = "single_lot",
	clear: int | bool = 1,
) -> dict[str, Any]:
	_require_login()
	from kentender_procurement.tender_configurations.services.final_submission import (
		seed_ready_lean_bid_for_final_submission_tests as _seed,
	)

	return _seed(fixture=fixture or "single_lot", clear=bool(int(clear)))
