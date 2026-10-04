# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission's `kt_tender_candidate_registry` provider (BDS-CHG-001 v0.8
§4.3 and §5.2 item 10; TPR-CHG-001 v0.12 §4.9–4.9A; retires the Tenders
stand-in, TPR FU-25).

A Tender's candidates are its bidder arrangements: the arrangement identity is
the candidate registration, created only by Start bid. The audience at an
instant is every arrangement registered by then and not closed before it,
each with the notice-contact version in force at that instant, so a later
contact change never rewrites an earlier notice's destination."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import clock

ARRANGEMENT = "Bidder Arrangement"


def _name(row) -> str:
	return cstr(row.joint_venture_name) or cstr(row.lead_legal_name)


def _contact_at(arrangement: str, instant) -> dict[str, Any] | None:
	rows = frappe.get_all(
		"Bidder Arrangement Notice Contact", filters={"parent": arrangement, "parenttype": ARRANGEMENT},
		fields=["notice_contact_version", "email", "set_at"], order_by="notice_contact_version asc", limit_page_length=0,
	)
	current = None
	for row in rows:
		if not row.set_at or get_datetime(row.set_at) <= instant:
			current = row
	return current


def candidate_audience(*, tender: str, at=None) -> list[dict[str, Any]]:
	instant = get_datetime(at or clock.now())
	rows = frappe.get_all(
		ARRANGEMENT, filters={"tender": tender}, fields=["name", "status", "status_since", "candidate_registered_at"],
		order_by="candidate_registered_at asc, creation asc", limit_page_length=0,
	)
	out = []
	for row in rows:
		if not row.candidate_registered_at or get_datetime(row.candidate_registered_at) > instant:
			continue
		if row.status != "Active" and row.status_since and get_datetime(row.status_since) <= instant:
			continue
		contact = _contact_at(row.name, instant)
		if contact:
			out.append({"candidate_registration_id": row.name, "destination": cstr(contact.email), "destination_version": cstr(contact.notice_contact_version)})
	return out


def candidate_registration(*, tender: str, candidate_registration_id: str) -> dict[str, Any] | None:
	"""The candidate's registration on this Tender, Active or Closed: closing
	the submission period does not unregister anyone, so Tenders' protected
	reads keep naming who asked and who was notified. Who is notified at an
	instant is `candidate_audience`'s question."""
	row = frappe.db.get_value(
		ARRANGEMENT, {"tender": tender, "name": cstr(candidate_registration_id).strip()},
		["name", "status", "joint_venture_name", "lead_legal_name", "mandatory_notice_email", "notice_contact_version", "candidate_registered_at"], as_dict=True,
	)
	if not row:
		return None
	return {
		"candidate_registration_id": row.name, "candidate_name": _name(row), "destination": cstr(row.mandatory_notice_email),
		"destination_version": cstr(row.notice_contact_version or 1), "registered_at": row.candidate_registered_at, "status": cstr(row.status),
	}
