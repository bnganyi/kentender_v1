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
#: REQ-CHG-001 v1.18 §5.12: 1.5 carries the exact items each requirement covers; 1.4 (no lists) stays usable.
SUPPORTED_HANDOFF_VERSIONS = frozenset({"1.4", req_handoff.HANDOFF_VERSION})
REQUISITION_DOCTYPE = "Procurement Requisition"


def list_eligible(user: str | None = None) -> list[dict[str, Any]]:
	return req_read.list_eligible_handoffs(user=user)


def load(handoff: str):
	name = cstr(handoff).strip()
	if not name or not frappe.db.exists(HANDOFF_DOCTYPE, name):
		return None
	return frappe.get_doc(HANDOFF_DOCTYPE, name)


def payload_of(handoff_doc) -> dict[str, Any]:
	"""The handoff payload with the v1.4 field names translated exactly as the
	stored snapshot translates them (`snapshot.build`), so the Start preview
	checks the same reservation category the Draft will carry."""
	from kentender_procurement.tenders.services import snapshot as snap

	payload = json.loads(handoff_doc.payload_json or "{}")
	return {**payload, **snap._handoff_v14_names(payload)}


def requisition_state(handoff_doc) -> str:
	return cstr(frappe.db.get_value(REQUISITION_DOCTYPE, handoff_doc.requisition, "current_state"))


def requisition_summary(handoff_doc) -> dict[str, Any]:
	row = frappe.db.get_value(REQUISITION_DOCTYPE, handoff_doc.requisition, ["name", "requisition_reference", "plan_item_id", "current_state", "lead_org_unit_id", "handoff_consumed_at"], as_dict=True)
	return {**row, "lead_org_unit": row.get("lead_org_unit_id")} if row else {}


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
	if cstr(handoff_doc.handoff_version) not in SUPPORTED_HANDOFF_VERSIONS:
		fail("TND_HANDOFF_INVALID", "The handoff version is not supported by this Tender format.")


def consumer_tender(handoff_doc) -> str:
	"""The live Tender this handoff is consumed by, if any."""
	if not handoff_doc.consumed_at or not handoff_doc.tender:
		return ""
	if frappe.db.exists("Tender", handoff_doc.tender):
		return cstr(handoff_doc.tender)
	return ""


def _require_tender_made_from(*, handoff: str, tender: str, tender_version: str) -> None:
	"""AUD-REQ-001 (REQ §9.2): Requisitions may bind a handoff only to a Tender
	that exists, was created from this very handoff and is the one Tender
	holding it. Tenders owns those facts, so Tenders checks them here, in the
	Start command's own transaction, before the owner command binds anything."""
	root = frappe.db.get_value("Tender", cstr(tender), ["name", "requisition_handoff"], as_dict=True) if cstr(tender).strip() else None
	if not root or cstr(root.requisition_handoff) != cstr(handoff):
		fail("TND_HANDOFF_INVALID", "The Tender was not created from this handoff.", detail={"handoff": handoff})
	version = frappe.db.get_value("Tender Version", cstr(tender_version), ["tender", "requisition_handoff"], as_dict=True) if cstr(tender_version).strip() else None
	if not version or cstr(version.tender) != root.name or cstr(version.requisition_handoff) != cstr(handoff):
		fail("TND_HANDOFF_INVALID", "The Tender Version was not created from this handoff.", detail={"handoff": handoff})
	other = frappe.get_all("Tender", filters={"requisition_handoff": handoff, "name": ("!=", root.name)}, pluck="name", limit=1)
	if other:
		fail("TND_HANDOFF_CONFLICT", detail={"handoff": handoff, "tender": other[0]})


def consume(*, handoff: str, tender: str, tender_version: str, template_key: str, template_version: str, idempotency_key: str) -> dict[str, Any]:
	"""Called only from inside a Tenders command (Start, Start corrected
	version), in the same transaction as the Tender it binds. There is no web
	endpoint for consumption: a caller outside a Tender transaction cannot
	consume a handoff (AUD-REQ-001)."""
	_require_tender_made_from(handoff=handoff, tender=tender, tender_version=tender_version)
	try:
		return req_handoff.record_handoff_consumption(
			handoff=handoff, tender=tender, tender_version=tender_version, template_key=template_key, template_version=template_version, idempotency_key=idempotency_key,
		)
	except ProcurementRequisitionsError as exc:
		held_by = cstr(frappe.db.get_value(HANDOFF_DOCTYPE, handoff, "tender")) if frappe.db.exists(HANDOFF_DOCTYPE, handoff) else ""
		if exc.code == "REQ_HANDOFF_CONSUMED" or (exc.code == "REQ_HANDOFF_CONFLICT" and held_by and held_by != cstr(tender)):
			fail("TND_HANDOFF_CONFLICT", detail={"handoff": handoff, "tender": held_by})
		fail("TND_HANDOFF_INVALID", detail={"requisition_error": exc.code})
	except frappe.DoesNotExistError:
		fail("TND_HANDOFF_INVALID")
	return {}  # unreachable


def release(*, handoff: str, tender: str, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""REQ-CHG-001 v1.11 §7.4 removed handoff release: once Tender Preparation
	consumes a handoff the Requisition can no longer be revoked. This route
	stays unavailable until the Tenders revamp defines its own correction
	route (REQ plan D15, REQ FOLLOW_UPS FU-30)."""
	fail("TND_HANDOFF_INVALID", "A consumed requisition handoff can no longer be released. The Tender correction route is being revised.", detail={"handoff": handoff})
	return {}  # unreachable


def successors(*, plan_item_id: str, user: str | None = None) -> list[dict[str, Any]]:
	"""Authorised, unconsumed handoffs on the same Plan Item — the corrected
	successor a stopped Tender may continue from (§5.1 last row)."""
	return [row for row in list_eligible(user) if row.get("plan_item_id") == plan_item_id]
