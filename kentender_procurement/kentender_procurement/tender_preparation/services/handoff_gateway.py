# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §4/§10.4 / plan D7 — the only door to Procurement
Requisitions. Every Requisition read or write goes through the owner's
published services; this module never reads a Requisition table for
business state and never writes one (AGENTS.md §2)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_requisitions.services import handoff as req_handoff
from kentender_procurement.procurement_requisitions.services import read as req_read
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.tender_preparation.services.errors import fail

HANDOFF_DOCTYPE = "Authorised Requisition Handoff"
REQUIRED_HANDOFF_VERSION = req_handoff.HANDOFF_VERSION

_REQ_TO_TPR = {
	"REQ_HANDOFF_CONSUMED": "TPR_HANDOFF_CONSUMED",
	"REQ_STALE_VERSION": "TPR_HANDOFF_INVALID",
	"REQ_RESPONSIBILITY_REQUIRED": "TPR_RESPONSIBILITY_REQUIRED",
	"REQ_IDEMPOTENCY_CONFLICT": "TPR_IDEMPOTENCY_CONFLICT",
	"REQ_CONTROL_INVALID": "TPR_CONTROL_INVALID",
}


def _translate(exc: ProcurementRequisitionsError) -> None:
	fail(_REQ_TO_TPR.get(exc.code, "TPR_HANDOFF_INVALID"), str(exc), exc.detail)


def list_eligible(*, user: str | None = None) -> list[dict[str, Any]]:
	return req_read.list_eligible_handoffs(user=user)


def load(handoff: str) -> Any | None:
	"""The immutable handoff row itself — read-only, the seam's published
	shape (REQ §5.12); None when absent."""
	if not handoff or not frappe.db.exists(HANDOFF_DOCTYPE, handoff):
		return None
	return frappe.get_doc(HANDOFF_DOCTYPE, handoff)


def requisition_state(handoff_doc) -> str:
	return frappe.db.get_value("Procurement Requisition", handoff_doc.requisition, "current_state") or ""


def record_consumption(*, handoff: str, tender: str, tender_version: str, template_key: str, template_version: str, idempotency_key: str) -> dict[str, Any]:
	try:
		return req_handoff.record_handoff_consumption(
			handoff=handoff, tender=tender, tender_version=tender_version, template_key=template_key,
			template_version=template_version, idempotency_key=idempotency_key,
		)
	except ProcurementRequisitionsError as exc:
		_translate(exc)
		raise  # unreachable


def release_consumption(*, handoff: str, tender: str, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	try:
		return req_handoff.release_handoff_consumption(handoff=handoff, tender=tender, reason=reason, idempotency_key=idempotency_key, user=user)
	except ProcurementRequisitionsError as exc:
		_translate(exc)
		raise  # unreachable
