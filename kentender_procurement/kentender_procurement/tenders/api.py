# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 — Tenders API surface (§7.1 reads, §7.2–7.4 commands).

Every endpoint keeps an explicit signature: the framework passes the whole
`form_dict` (including `cmd`/`csrf_token`) into a whitelisted method that
declares `**kwargs` (the NDS-914 class), and a form field named `values`
shadows `frappe._dict.values()` — so JSON-payload parameters are named for
what they carry (`draft_values`, `evidence_values`, ...). Record reads mask
an unauthorised or missing record as `{"outcome": "NOT_FOUND"}` data so no
Frappe "Not found" modal ever appears on a Vue surface (AGENTS §6.10)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.tenders.services import correction, documents, draft_commands as cmd, history, lifecycle, read


def _parse_json(value, default):
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


def _masked_read(fn, arguments: dict[str, Any]) -> dict[str, Any]:
	try:
		return fn(**arguments)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND", "heading": "Tender not found", "text": "This Tender is unavailable or you do not have permission to view it."}


# --------------------------------------------------------------------------
# §7.1 Reads
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_tenders_workspace(search: str = "", status: str = "", fiscal_year: str = "") -> dict[str, Any]:
	return read.get_tenders_workspace(search=search, status=status, fiscal_year=fiscal_year)


@frappe.whitelist()
def get_tender_start(handoff: str) -> dict[str, Any]:
	return _masked_read(read.get_tender_start, dict(handoff=handoff))


@frappe.whitelist()
def get_tender(tender: str) -> dict[str, Any]:
	return _masked_read(read.get_tender, dict(tender=tender))


@frappe.whitelist()
def get_tender_review(tender: str) -> dict[str, Any]:
	return _masked_read(read.get_tender_review, dict(tender=tender))


@frappe.whitelist()
def get_tender_history(tender: str) -> dict[str, Any]:
	return _masked_read(history.get_tender_history, dict(tender=tender))


@frappe.whitelist()
def get_tender_document(digest: str, audience: str = "Internal") -> dict[str, Any]:
	return _masked_read(documents.get_tender_document, dict(digest_value=digest, audience=audience))


@frappe.whitelist()
def preview_tender_documents(tender: str) -> dict[str, Any]:
	"""§11.3 Preview Invitation / Preview complete Tender — a read-only
	render of the current saved Version; freezes and submits nothing."""
	from kentender_procurement.tenders.services import render_service, snapshot as snap
	from kentender_procurement.tenders.services import tender_authorization as authz

	def _preview(tender: str) -> dict[str, Any]:
		actor = authz.actor()
		root = frappe.get_doc("Tender", cmd.resolve_tender_name(tender))
		mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
		if mode == "department":
			authz.not_found()
		version = frappe.get_doc("Tender Version", root.current_version)
		out = render_service.render(root, version, snap.load(version), approval=render_service.approval_block(version))
		return {"outcome": "OK", "invitation_html": out["invitation_html"], "issued_tender_html": out["issued_tender_html"], "invitation_digest": out["invitation_digest"], "issued_tender_digest": out["issued_tender_digest"], "problems": out["problems"]}

	return _masked_read(_preview, dict(tender=tender))


# --------------------------------------------------------------------------
# §7.2 Preparation and approval commands
# --------------------------------------------------------------------------


@frappe.whitelist()
def start_tender(handoff: str, idempotency_key: str) -> dict[str, Any]:
	return cmd.start_tender(handoff=handoff, idempotency_key=idempotency_key)


@frappe.whitelist()
def save_tender_draft(tender: str, draft_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.save_tender_draft(tender=tender, values=_parse_json(draft_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def add_tender_evidence_requirement(tender: str, evidence_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.add_tender_evidence_requirement(tender=tender, values=_parse_json(evidence_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def update_tender_evidence_requirement(tender: str, evidence_requirement_id: str, evidence_values, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.update_tender_evidence_requirement(tender=tender, evidence_requirement_id=evidence_requirement_id, values=_parse_json(evidence_values, {}), expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def remove_tender_evidence_requirement(tender: str, evidence_requirement_id: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.remove_tender_evidence_requirement(tender=tender, evidence_requirement_id=evidence_requirement_id, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_tender_for_approval(tender: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.submit_tender_for_approval(tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_tender_for_correction(tender: str, reason: str, affected_task: str, expected_record_version, idempotency_key: str, task: str = "", task_token: str = "") -> dict[str, Any]:
	return lifecycle.return_tender_for_correction(tender=tender, reason=reason, affected_task=affected_task, expected_record_version=expected_record_version, idempotency_key=idempotency_key, task=task, task_token=task_token)


@frappe.whitelist()
def approve_tender_package(tender: str, expected_record_version, idempotency_key: str, task: str = "", task_token: str = "") -> dict[str, Any]:
	return lifecycle.approve_tender_package(tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key, task=task, task_token=task_token)


@frappe.whitelist()
def reopen_approved_tender(tender: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.reopen_approved_tender(tender=tender, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def request_requisition_correction(tender: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return correction.request_requisition_correction(tender=tender, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def start_corrected_tender_version(tender: str, handoff: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return correction.start_corrected_tender_version(tender=tender, handoff=handoff, expected_record_version=expected_record_version, idempotency_key=idempotency_key)
