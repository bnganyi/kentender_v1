# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`UpdateTenderNoticeContact` (BDS-CHG-001 v0.8 §4.3, §5.2 item 10, §7.2).

Mandatory Tender notices cannot be opted out of; the address can only move to
another verified Account email. Each change appends a new notice-contact
version effective from its trusted instant, so Tenders' audience snapshot for
an earlier notice keeps the destination it was sent to."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import clock, records, supplier_gateway
from kentender_procurement.bid_submission.services.errors import MESSAGES, fail, field_errors

ARRANGEMENT = "Bidder Arrangement"


def update_tender_notice_contact(*, bidder_arrangement_id: str, notice_contact_id: str, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bidder_arrangement_id": cstr(bidder_arrangement_id).strip(), "notice_contact_id": cstr(notice_contact_id).strip(), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "UpdateTenderNoticeContact", payload, lambda: _update(actor=actor, **payload), actor=actor, organisation=payload["organisation"])


def _update(*, actor: str, bidder_arrangement_id: str, notice_contact_id: str, expected_record_version, organisation: str) -> dict[str, Any]:
	at = clock.now()
	lead = authz.acting_assignment(actor, organisation, at=at)["organisation_id"]
	authz.active_account(lead)
	if not bidder_arrangement_id or not frappe.db.exists(ARRANGEMENT, {"name": bidder_arrangement_id, "lead_organisation": lead}):
		fail("BDS_TENDER_NOT_FOUND")  # another organisation's arrangement is never confirmed
	doc = frappe.get_doc(ARRANGEMENT, bidder_arrangement_id)
	if doc.status != "Active":
		fail("BDS_TENDER_NOT_OPEN")
	records.check_version(doc, expected_record_version)
	contact = next((c for c in supplier_gateway.verified_contacts(organisation_id=lead) if c.get("contact_id") == notice_contact_id), None)
	if not contact:
		return field_errors({"notice_contact_id": MESSAGES["BDS_NOTICE_CONTACT_REQUIRED"]}, code="BDS_NOTICE_CONTACT_REQUIRED")
	if contact["value"] == doc.mandatory_notice_email:
		return {"ok": True, "changed": False, "notice_contact_version": int(doc.notice_contact_version), "record_version": int(doc.record_version)}
	version = int(doc.notice_contact_version or 0) + 1
	doc.append("notice_contacts", {"notice_contact_version": version, "email": contact["value"], "contact_id": contact["contact_id"], "contact_version": int(contact.get("contact_version") or 1), "set_by": actor, "set_at": at})
	records.bump(doc, mandatory_notice_email=contact["value"], notice_contact_version=version)
	records.emit("NoticeContactChanged", tender=doc.tender, arrangement=doc.name, organisation=lead, actor=actor, at=at, payload={"notice_contact_version": version})
	return {"ok": True, "changed": True, "notice_contact_version": version, "record_version": int(doc.record_version)}
