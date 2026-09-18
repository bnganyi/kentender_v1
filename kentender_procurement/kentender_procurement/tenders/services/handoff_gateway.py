# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §3 — the one seam to Procurement Requisitions'
published handoff contract (`AuthorisedRequisitionHandoff v1.3`).

Tenders never writes a Requisition table: eligibility is Requisitions'
`list_eligible_handoffs`, consumption is `record_handoff_consumption`, the
correction route releases through `release_handoff_consumption`, and the
immutable handoff record itself is read as a published record. Every
Requisitions error is remapped onto the closed §8 set here."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import handoff as req_handoff, read as req_read
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.tenders.services.errors import fail

HANDOFF_DOCTYPE = "Authorised Requisition Handoff"
REQUISITION_DOCTYPE = "Procurement Requisition"


def list_eligible(user: str | None = None) -> list[dict[str, Any]]:
	return req_read.list_eligible_handoffs(user=user)


def load(handoff: str):
	name = cstr(handoff).strip()
	if not name or not frappe.db.exists(HANDOFF_DOCTYPE, name):
		return None
	return frappe.get_doc(HANDOFF_DOCTYPE, name)


def payload_of(handoff_doc) -> dict[str, Any]:
	return json.loads(handoff_doc.payload_json or "{}")


def requisition_state(handoff_doc) -> str:
	return cstr(frappe.db.get_value(REQUISITION_DOCTYPE, handoff_doc.requisition, "current_state"))


def requisition_summary(handoff_doc) -> dict[str, Any]:
	row = frappe.db.get_value(REQUISITION_DOCTYPE, handoff_doc.requisition, ["name", "requisition_reference", "plan_item_id", "current_state", "lead_org_unit", "handoff_consumed_at"], as_dict=True)
	return dict(row) if row else {}


def require_startable(handoff_doc) -> None:
	"""§5.1 row 1 / §8 `TND_HANDOFF_INVALID`: Authorised, unrevoked, the
	Requisition's current handoff, v1.3."""
	if handoff_doc is None:
		fail("TND_HANDOFF_INVALID")
	root = requisition_summary(handoff_doc)
	if not root or root.get("current_state") != "Authorised":
		fail("TND_HANDOFF_INVALID")
	if cstr(frappe.db.get_value(REQUISITION_DOCTYPE, handoff_doc.requisition, "handoff")) != handoff_doc.name:
		fail("TND_HANDOFF_INVALID", "This handoff is no longer the Requisition's current authorised handoff.")
	if cstr(handoff_doc.handoff_version) != req_handoff.HANDOFF_VERSION:
		fail("TND_HANDOFF_INVALID", "The handoff version is not supported by this Tender format.")


def consumer_tender(handoff_doc) -> str:
	"""The live Tender this handoff is consumed by, if any."""
	if not handoff_doc.consumed_at or not handoff_doc.tender:
		return ""
	if frappe.db.exists("Tender", handoff_doc.tender):
		return cstr(handoff_doc.tender)
	return ""


def consume(*, handoff: str, tender: str, tender_version: str, template_key: str, template_version: str, idempotency_key: str) -> dict[str, Any]:
	try:
		return req_handoff.record_handoff_consumption(
			handoff=handoff, tender=tender, tender_version=tender_version, template_key=template_key, template_version=template_version, idempotency_key=idempotency_key,
		)
	except ProcurementRequisitionsError as exc:
		if exc.code == "REQ_HANDOFF_CONSUMED":
			fail("TND_HANDOFF_CONFLICT", detail={"handoff": handoff, "tender": cstr(frappe.db.get_value(HANDOFF_DOCTYPE, handoff, "tender"))})
		fail("TND_HANDOFF_INVALID", detail={"requisition_error": exc.code})
	except frappe.DoesNotExistError:
		fail("TND_HANDOFF_INVALID")
	return {}  # unreachable


def release(*, handoff: str, tender: str, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	try:
		return req_handoff.release_handoff_consumption(handoff=handoff, tender=tender, reason=reason, idempotency_key=idempotency_key, user=user)
	except ProcurementRequisitionsError as exc:
		if exc.code == "REQ_RESPONSIBILITY_REQUIRED":
			fail("TND_RESPONSIBILITY_REQUIRED")
		fail("TND_HANDOFF_INVALID", detail={"requisition_error": exc.code})
	return {}  # unreachable


def successors(*, plan_item_id: str, user: str | None = None) -> list[dict[str, Any]]:
	"""Authorised, unconsumed handoffs on the same Plan Item — the corrected
	successor a stopped Tender may continue from (§5.1 last row)."""
	return [row for row in list_eligible(user) if row.get("plan_item_id") == plan_item_id]
