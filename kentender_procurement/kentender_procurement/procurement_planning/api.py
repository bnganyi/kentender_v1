# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 — Procurement Planning API surface (§8.1 reads, §8.2
commands).

Every endpoint keeps an explicit signature: the framework passes the whole
`form_dict` (including `cmd`/`csrf_token`) into a whitelisted method that
declares **kwargs, which is exactly how NDS-914 broke four commands over HTTP
while every direct-service test passed. Playwright fixture endpoints live in
seed/fixture modules, never here (decision D8). No endpoint takes or returns
a Procuring Entity; the Fiscal Year is record data (§10).
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_planning.services import dpp_lifecycle, dpp_validation, planning_context


def _parse_json(value, default):
	"""HTTP transports lists/dicts as JSON strings; direct callers pass values.
	`from __future__ import annotations` disables Frappe's own coercion."""
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


def _truthy(value) -> bool:
	return value in (True, 1, "1", "true", "True")


# --- context (PLN-UI-01) -------------------------------------------------------


@frappe.whitelist()
def resolve_planning_context(financial_year: str | None = None) -> dict[str, Any]:
	return planning_context.resolve_planning_context(financial_year=financial_year)


@frappe.whitelist()
def select_planning_context(financial_year: str) -> dict[str, Any]:
	return planning_context.select_planning_context(financial_year=financial_year)


@frappe.whitelist()
def reset_planning_context() -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import planning_context

	return planning_context.reset_planning_context()


@frappe.whitelist()
def get_regulatory_reference(fiscal_year: str) -> dict[str, Any]:
	"""§8.1 `GetRegulatoryReference` — read-only; Planning never writes it."""
	from kentender_core.services.regulatory_reference import get_regulatory_reference as read
	from kentender_procurement.procurement_planning.services import planning_authorization as authz

	if not authz.holds_any_planning_responsibility():
		authz.not_found()
	return read(fiscal_year)


# --- §8.2 DPP commands -------------------------------------------------------


@frappe.whitelist()
def open_departmental_plan(organisation_unit: str, fiscal_year: str, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.open_departmental_plan(organisation_unit=organisation_unit, fiscal_year=fiscal_year, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_need_funding(
	dpp_version: str, entry_id: str, expected_record_version, idempotency_key: str,
	budget_line: str | None = None, indicative_amount=None,
) -> dict[str, Any]:
	return dpp_lifecycle.save_need_funding(
		dpp_version=dpp_version, entry_id=entry_id, budget_line=budget_line or "", indicative_amount=indicative_amount,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def set_need_planning_disposition(
	dpp_version: str, entry_id: str, disposition: str, expected_record_version, idempotency_key: str, reason: str | None = None,
) -> dict[str, Any]:
	return dpp_lifecycle.set_need_planning_disposition(
		dpp_version=dpp_version, entry_id=entry_id, disposition=disposition, reason=reason or "",
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def save_direct_requirement(dpp_version: str, entry_values, expected_record_version, idempotency_key: str, entry_id: str | None = None) -> dict[str, Any]:
	# `entry_values`, deliberately not `values`: a form-encoded field named
	# "values" shadows frappe._dict.values() on frappe.local.form_dict and
	# degrades the whole request to Guest (v1.2 finding).
	return dpp_lifecycle.save_direct_requirement(
		dpp_version=dpp_version, values=_parse_json(entry_values, {}), entry_id=entry_id,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def remove_direct_requirement(dpp_version: str, entry_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.remove_direct_requirement(dpp_version=dpp_version, entry_id=entry_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_departmental_plan(dpp_version: str, certification_confirmed, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.submit_departmental_plan(
		dpp_version=dpp_version, certification_confirmed=_truthy(certification_confirmed),
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def withdraw_departmental_submission(dpp_version: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.withdraw_departmental_submission(dpp_version=dpp_version, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def create_departmental_plan_update(departmental_plan: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return dpp_lifecycle.create_departmental_plan_update(departmental_plan=departmental_plan, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_departmental_plan(task: str, issues, task_token: str, idempotency_key: str) -> dict[str, Any]:
	return dpp_validation.return_departmental_plan(task=task, issues=_parse_json(issues, []), task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def accept_departmental_plan(task: str, classifications, task_token: str, idempotency_key: str) -> dict[str, Any]:
	return dpp_validation.accept_departmental_plan(task=task, classifications=_parse_json(classifications, {}), task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def get_accepted_dpp_classification(dpp_submission: str, dpp_entry_id: str = "") -> dict[str, Any]:
	"""PLN-CHG-001 v1.23 §7.1 `GetAcceptedDPPClassification`."""
	from kentender_procurement.procurement_planning.services import dpp_classification

	return dpp_classification.get_accepted_dpp_classification(dpp_submission=dpp_submission, dpp_entry_id=dpp_entry_id)


@frappe.whitelist()
def correct_accepted_requirement_classification(
	dpp_submission: str, dpp_entry_id: str, expected_evidence_id: str, new_requirement_type: str, reason: str,
	idempotency_key: str,
) -> dict[str, Any]:
	"""PLN-CHG-001 v1.23 §7.2 `CorrectAcceptedRequirementClassification`.

	Explicit parameters only: a `**kwargs` signature here would forward Frappe's
	own `cmd` and `csrf_token` form fields into the keyword-only service.
	Procurement category is deliberately absent — the server derives it.
	"""
	from kentender_procurement.procurement_planning.services import dpp_classification

	return dpp_classification.correct_accepted_requirement_classification(
		dpp_submission=dpp_submission, dpp_entry_id=dpp_entry_id, expected_evidence_id=expected_evidence_id,
		new_requirement_type=new_requirement_type, reason=reason, idempotency_key=idempotency_key,
	)


# --- §8.1 reads ------------------------------------------------------------


@frappe.whitelist()
def get_planning_workspace(financial_year: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import workspace

	return workspace.get_planning_workspace(financial_year=financial_year)


@frappe.whitelist()
def get_departmental_plan(dpp_reference: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_departmental_plan(dpp_reference=dpp_reference)


@frappe.whitelist()
def get_dpp_entry_editor(dpp_reference: str, entry_id: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_dpp_entry_editor(dpp_reference=dpp_reference, entry_id=entry_id)


@frappe.whitelist()
def get_dpp_validation_task(task: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import dpp_read

	return dpp_read.get_dpp_validation_task(task=task)


@frappe.whitelist()
def get_annual_plan(plan_reference: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_annual_plan(plan_reference=plan_reference)


@frappe.whitelist()
def get_plan_item(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_plan_item(plan_item_id=plan_item_id)


@frappe.whitelist()
def get_finance_task(task: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_finance_task(task=task)


@frappe.whitelist()
def get_plan_governance_task(task: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_plan_governance_task(task=task)


@frappe.whitelist()
def get_source_evidence(task: str, source_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_source_evidence(task=task, source_key=source_key)


@frappe.whitelist()
def download_review_pack(task: str) -> None:
	"""U11 **Download review pack** — a plain authenticated file download
	(not the JSON API layer), so it must not be called through `run()`."""
	import json as _json

	from kentender_procurement.procurement_planning.services import plan_read

	pack = plan_read.build_review_pack(task=task)
	frappe.local.response.filename = f"{pack['task_reference']}-review-pack.json"
	frappe.local.response.filecontent = _json.dumps(pack, indent=2, default=str)
	frappe.local.response.type = "download"


@frappe.whitelist()
def get_publication_task(publication: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_read

	return plan_read.get_publication_task(publication=publication)


# --- workbench, formation, Plan Item -------------------------------------------


@frappe.whitelist()
def form_plan_items(
	plan_version: str, dpp_entries, mode: str, expected_record_version, idempotency_key: str,
	combination_reason: str = "", combined_title: str = "",
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.form_plan_items(
		plan_version=plan_version, dpp_entries=_parse_json(dpp_entries, []), mode=mode,
		combination_reason=combination_reason, combined_title=combined_title,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def dissolve_plan_item(plan_item: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.dissolve_plan_item(plan_item=plan_item, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_plan_item(plan_item: str, item_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.save_plan_item(plan_item=plan_item, values=_parse_json(item_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_plan_version_details(plan_version: str, detail_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.save_plan_version_details(
		plan_version=plan_version, values=_parse_json(detail_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def confirm_splitting_advisory(plan_version: str, confirmation: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_workbench

	return plan_workbench.confirm_splitting_advisory(plan_version=plan_version, confirmation=confirmation, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --- plan-level Finance ---------------------------------------------------------


@frappe.whitelist()
def request_plan_funding_confirmation(plan_version: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	return plan_finance.request_plan_funding_confirmation(plan_version=plan_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def confirm_plan_funding(task: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	return plan_finance.confirm_plan_funding(task=task, task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_from_finance(task: str, reason: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_finance

	return plan_finance.return_from_finance(task=task, reason=reason, task_token=task_token, idempotency_key=idempotency_key)


# --- governance ---------------------------------------------------------------


@frappe.whitelist()
def submit_consolidated_plan(plan_version: str, expected_record_version, idempotency_key: str, late_activation_reason: str | None = None) -> dict[str, Any]:
	# `late_activation_reason` is still sent by the current Annual Plan screen; v1.18
	# moves the explanation to the Accounting Officer (adoption / RecordLateActivationExplanation).
	# The parameter is ignored until the U07 re-port (Phase 3C) stops sending it.
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.submit_consolidated_plan(plan_version=plan_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def adopt_and_submit_plan(task: str, task_token: str, idempotency_key: str, late_activation_explanation: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.adopt_and_submit_plan(task=task, task_token=task_token, idempotency_key=idempotency_key, late_activation_explanation=late_activation_explanation or "")


@frappe.whitelist()
def approve_annual_plan(task: str, task_token: str, idempotency_key: str, collective_resolution_reference: str = "", resolution_reference: str | None = None) -> dict[str, Any]:
	# `resolution_reference` is the pre-v1.18 parameter name the live U11 screen
	# still sends; kept as a fallback until its Phase 3 re-port switches to
	# `collective_resolution_reference` (v1.18 §6.1 D7).
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.approve_annual_plan(
		task=task, task_token=task_token,
		collective_resolution_reference=collective_resolution_reference or resolution_reference or "",
		idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def record_late_activation_explanation(plan_version: str, reason: str, idempotency_key: str, supersedes: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.record_late_activation_explanation(plan_version=plan_version, reason=reason, supersedes=supersedes or "", idempotency_key=idempotency_key)


@frappe.whitelist()
def begin_held_plan_correction(plan_version: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.begin_held_plan_correction(plan_version=plan_version, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_plan_version(task: str, reason: str, task_token: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.return_plan_version(task=task, reason=reason, task_token=task_token, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_corrected_plan(plan_version: str, expected_record_version, idempotency_key: str, late_activation_reason: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_governance

	return plan_governance.submit_corrected_plan(plan_version=plan_version, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --- publication, Active, successor --------------------------------------------


@frappe.whitelist()
def publish_annual_plan(plan_version: str, idempotency_key: str) -> dict[str, Any]:
	"""§7.2 `PublishAnnualPlan` — the system worker; runs inline here (no RQ
	worker on this bench) and would otherwise be `frappe.enqueue`d post-commit
	by `ApproveAnnualPlan`. Technical/System Manager only."""
	from kentender_core.services.authorization import is_technical
	from kentender_procurement.procurement_planning.services import planning_authorization as authz
	from kentender_procurement.procurement_planning.services import publication_pipeline

	if not is_technical(authz.actor(None)):
		authz.not_found()
	return publication_pipeline.publish_annual_plan(plan_version=plan_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def receive_publication_acknowledgement(publication: str, event_id: str, package_hash: str, idempotency_key: str, public_location: str | None = None, external_reference: str | None = None) -> dict[str, Any]:
	"""§7.2 `ReceivePublicationAcknowledgement` — the authenticated System
	endpoint an external destination's callback would call. Technical only."""
	from kentender_core.services.authorization import is_technical
	from kentender_procurement.procurement_planning.services import planning_authorization as authz
	from kentender_procurement.procurement_planning.services import publication_pipeline

	if not is_technical(authz.actor(None)):
		authz.not_found()
	return publication_pipeline.receive_publication_acknowledgement(
		event_id=event_id, publication=publication, package_hash=package_hash,
		public_location=public_location or "", external_reference=external_reference or "", idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def reconcile_publication(publication: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import publication_pipeline

	return publication_pipeline.reconcile_publication(publication=publication, idempotency_key=idempotency_key)


@frappe.whitelist()
def retry_publication(publication: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import publication_pipeline

	return publication_pipeline.retry_publication(publication=publication, idempotency_key=idempotency_key)


@frappe.whitelist()
def hold_plan_publication(plan_version: str, reason: str, idempotency_key: str, hold_kind: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import publication_pipeline

	return publication_pipeline.hold_plan_publication(plan_version=plan_version, reason=reason, hold_kind=hold_kind or "Accounting Officer correction request", idempotency_key=idempotency_key)


@frappe.whitelist()
def record_treasury_submission(
	plan_version: str, submitted_at: str, channel: str, destination: str, dispatch_reference: str, exact_document_confirmed, idempotency_key: str, supporting_attachment: str | None = None,
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import treasury

	return treasury.record_treasury_submission(
		plan_version=plan_version, submitted_at=submitted_at, channel=channel, destination=destination, dispatch_reference=dispatch_reference,
		exact_document_confirmed=exact_document_confirmed, supporting_attachment=supporting_attachment or "", idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def correct_treasury_submission_evidence(prior_evidence: str, reason: str, submitted_at: str, channel: str, destination: str, dispatch_reference: str, idempotency_key: str, supporting_attachment: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import treasury

	return treasury.correct_treasury_submission_evidence(
		prior_evidence=prior_evidence, reason=reason, submitted_at=submitted_at, channel=channel, destination=destination,
		dispatch_reference=dispatch_reference, supporting_attachment=supporting_attachment or "", idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def request_plan_withdrawal(plan_version: str, reason: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import treasury

	return treasury.request_plan_withdrawal(plan_version=plan_version, reason=reason, idempotency_key=idempotency_key)


@frappe.whitelist()
def withdraw_approved_plan_for_correction(task: str, task_token: str, idempotency_key: str, collective_resolution_reference: str | None = None) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import treasury

	return treasury.withdraw_approved_plan_for_correction(task=task, task_token=task_token, collective_resolution_reference=collective_resolution_reference or "", idempotency_key=idempotency_key)





@frappe.whitelist()
def begin_plan_update(plan_reference: str, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.begin_plan_update(plan_reference=plan_reference, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_plan_item_in_successor(plan_item: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.remove_plan_item_in_successor(plan_item=plan_item, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def cancel_plan_update(plan_reference: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_publication

	return plan_publication.cancel_plan_update(plan_reference=plan_reference, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


# --- §10.13 / §10.15 progress and correction requests -----------------------


@frappe.whitelist()
def get_procurement_progress(plan_reference: str = "") -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import progress_read

	return progress_read.get_procurement_progress(plan_reference=plan_reference)


@frappe.whitelist()
def get_plan_correction_requests(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import progress_read

	return progress_read.get_plan_correction_requests(plan_item_id=plan_item_id)


# --- forecast cascade -------------------------------------------------------
#
# PLN-CHG-001 v1.23 §7.5 / §15.3 (PLN23-CHG-001): the MVP registers no
# `PreviewForecastCascade` or `ConfirmForecastCascade` service. The tested
# implementation stays in `services/schedule.py` so its regressions keep
# passing, but it has no whitelisted endpoint, no route and no control. Do not
# re-expose it until the forecast facility is separately approved with its
# owner integrations.


# --- §7.4 Requisition eligibility — published for a sibling module ----------------


@frappe.whitelist()
def get_requisition_eligible_plan_item(plan_item_id: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.get_requisition_eligible_plan_item(plan_item_id=plan_item_id)


@frappe.whitelist()
def authorise_requisition_drawdown(plan_item_id: str, requisition_reference: str, requesting_org_unit: str, allocations, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.authorise_requisition_drawdown(
		plan_item_id=plan_item_id, requisition_reference=requisition_reference, requesting_org_unit=requesting_org_unit,
		allocations=_parse_json(allocations, []), expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def reverse_requisition_drawdown(drawdown_reference: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.reverse_requisition_drawdown(drawdown_reference=drawdown_reference, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def receive_plan_item_correction_request(
	plan_item_id: str, requisition_reference: str, requisition_version: str, reason: str, idempotency_key: str,
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.receive_plan_item_correction_request(
		plan_item_id=plan_item_id, requisition_reference=requisition_reference, requisition_version=requisition_version,
		reason=reason, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def start_plan_item_correction(correction_request: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.start_plan_item_correction(
		correction_request=correction_request, expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def resolve_plan_item_correction_request(
	correction_request: str, correcting_plan_version: str, expected_record_version, idempotency_key: str, replacement_plan_item_id: str = "",
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.resolve_plan_item_correction_request(
		correction_request=correction_request, correcting_plan_version=correcting_plan_version,
		replacement_plan_item_id=replacement_plan_item_id,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)


@frappe.whitelist()
def close_plan_item_correction_without_change(
	correction_request: str, reason: str, expected_record_version, idempotency_key: str,
) -> dict[str, Any]:
	from kentender_procurement.procurement_planning.services import plan_requisition

	return plan_requisition.close_plan_item_correction_without_change(
		correction_request=correction_request, reason=reason,
		expected_record_version=expected_record_version, idempotency_key=idempotency_key,
	)
