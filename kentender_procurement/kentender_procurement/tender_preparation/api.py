# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 — Tender Preparation API surface (§11.1 reads, §11.2
commands).

Every endpoint keeps an explicit signature (never `**kwargs`: the framework
hands a whitelisted method the whole `form_dict`, `cmd` and `csrf_token`
included — see `procurement_requisitions.api`'s own docstring), and every
JSON-payload parameter is named for what it carries, never bare `values`.
The server derives actor, role-bound assignment, state, totals, template
binding, digests and permitted actions; no endpoint accepts a Procuring
Entity or Fiscal Year argument (TPR-AC-030)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.tender_preparation.services import draft_commands as cmd
from kentender_procurement.tender_preparation.services import lifecycle, publication, read
from kentender_procurement.tender_preparation.services.errors import fail


def _masked_read(fn):
	"""§11.3 `TPR_NOT_FOUND` at the API boundary: the services mask an absent
	or invisible record with `DoesNotExistError` (test-pinned); the page
	receives that verdict as data — `{"outcome": "NOT_FOUND"}` — so the screen
	paints "Tender not found" inline and the framework's own 404 handler never
	raises a modal over it (KT-STD-001 §3A.2, AGENTS.md §6.10)."""
	try:
		return fn()
	except frappe.DoesNotExistError:
		frappe.clear_last_message()
		return {"outcome": "NOT_FOUND", "message": "Tender not found."}


def _parse_json(value, default):
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


# --------------------------------------------------------------------------
# §11.1 Reads
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_tender_preparation_workspace() -> dict[str, Any]:
	return read.get_tender_preparation_workspace()


@frappe.whitelist()
def get_tender_compatibility(handoff: str) -> dict[str, Any]:
	return _masked_read(lambda: read.get_tender_compatibility(handoff=handoff))


@frappe.whitelist()
def get_tender_editor(tender: str) -> dict[str, Any]:
	return _masked_read(lambda: read.get_tender_editor(tender=tender))


@frappe.whitelist()
def get_tender_approval_task(task: str) -> dict[str, Any]:
	return _masked_read(lambda: read.get_tender_approval_task(task=task))


@frappe.whitelist()
def get_approved_tender(tender: str) -> dict[str, Any]:
	return _masked_read(lambda: read.get_approved_tender(tender=tender))


@frappe.whitelist()
def get_tender_history(tender: str) -> dict[str, Any]:
	return _masked_read(lambda: read.get_tender_history(tender=tender))


@frappe.whitelist()
def get_tender_preview(tender: str, output: str) -> dict[str, Any]:
	return _masked_read(lambda: read.get_tender_preview(tender=tender, output=output))


# --------------------------------------------------------------------------
# §11.2 Commands
# --------------------------------------------------------------------------


@frappe.whitelist()
def prepare_tender(handoff: str, idempotency_key: str) -> dict[str, Any]:
	return cmd.prepare_tender(handoff=handoff, idempotency_key=idempotency_key)


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
def run_tender_readiness(tender: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return cmd.run_tender_readiness(tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def submit_tender_for_approval(tender: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.submit_tender_for_approval(tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def return_tender_for_correction(task: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.return_tender_for_correction(task=task, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def approve_tender_for_publication(task: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.approve_tender_for_publication(task=task, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def reopen_approved_tender(tender: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.reopen_approved_tender(tender=tender, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def request_tender_upstream_correction(tender: str, reason: str, expected_record_version, idempotency_key: str) -> dict[str, Any]:
	return lifecycle.request_tender_upstream_correction(tender=tender, reason=reason, expected_record_version=expected_record_version, idempotency_key=idempotency_key)


@frappe.whitelist()
def acknowledge_tender_publication_consumed_technical(tender: str, correlation_id: str, published_on: str | None = None) -> dict[str, Any]:
	"""§11.2 `AcknowledgeTenderPublicationConsumed` — inbound from a
	downstream publication process that does not exist yet (TPR FU-06).
	Until it does, this technical endpoint (System Manager only, AUTH §8 —
	a technical action, never a Tender decision) gives smoke tests and the
	seed a fixed shape to call. It is deleted the day the real consumer
	arrives."""
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		fail("TPR_RESPONSIBILITY_REQUIRED", "The publication acknowledgment is a technical operation reserved to System Manager.")
	return publication.acknowledge_publication_consumed(tender=tender, correlation_id=correlation_id, published_on=published_on or None)
