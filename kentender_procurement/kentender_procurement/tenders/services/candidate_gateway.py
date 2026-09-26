# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §3 / §4.9–4.9A — the one seam to the Bid Submission
owner's Tender-bound candidate registry (plan D8′, W2).

Bid Submission (BDS-CHG-001 v0.7) creates a candidate registration only
through **Start bid** and publishes `GetTenderCandidateAudience`: the exact
Active `bidder_arrangement_id`s of a Tender and each one's current verified
mandatory-notice destination version at an instant. Tenders consumes that
projection; it never creates or edits supplier contacts.

Until BDS registers a provider on the `kt_tender_candidate_registry` hook,
this gateway uses the Tenders **stand-in** (`Tender Candidate Registration`,
registered only by a service identity standing in for Start bid). The
stand-in keeps BDS v0.7's names so the switch is a hook registration and
the removal of the stand-in (FOLLOW_UPS FU-25). A provider module exposes:

- `candidate_audience(*, tender: str, at) -> list[dict]` — rows with
  `candidate_registration_id`, `destination`, `destination_version`;
- `candidate_registration(*, tender: str, candidate_registration_id: str) -> dict | None`
  — the Active registration of that candidate on that Tender.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.tenders.services import clock, envelope
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE

HOOK = "kt_tender_candidate_registry"
STAND_IN = "Tender Candidate Registration"


def _provider():
	"""The registered provider module (the last `kt_tender_candidate_registry`
	hook value), or None for the stand-in."""
	paths = frappe.get_hooks(HOOK) or []
	return frappe.get_module(paths[-1]) if paths else None


def is_stand_in() -> bool:
	return _provider() is None


def candidate_audience(*, tender: str, at=None) -> list[dict[str, Any]]:
	"""The authoritative Active candidates of `tender` at `at` (§4.9A: a
	candidate registered later is never a recipient of an earlier notice)."""
	provider = _provider()
	if provider is not None:
		return list(provider.candidate_audience(tender=tender, at=at or clock.now()))
	instant = get_datetime(at or clock.now())
	rows = frappe.get_all(
		STAND_IN, filters={"tender": tender, "status": "Active"},
		fields=["bidder_arrangement_id", "notice_address", "notice_address_version", "registered_at"], order_by="registered_at asc, creation asc", limit_page_length=0,
	)
	return [
		{"candidate_registration_id": r.bidder_arrangement_id, "destination": cstr(r.notice_address), "destination_version": cstr(r.notice_address_version or 1)}
		for r in rows
		if not r.registered_at or get_datetime(r.registered_at) <= instant
	]


def candidate_registration(*, tender: str, candidate_registration_id: str) -> dict[str, Any] | None:
	provider = _provider()
	if provider is not None:
		return provider.candidate_registration(tender=tender, candidate_registration_id=candidate_registration_id)
	row = frappe.db.get_value(
		STAND_IN, {"tender": tender, "bidder_arrangement_id": cstr(candidate_registration_id).strip(), "status": "Active"},
		["bidder_arrangement_id", "candidate_name", "notice_address", "notice_address_version", "registered_at"], as_dict=True,
	)
	if not row:
		return None
	return {"candidate_registration_id": row.bidder_arrangement_id, "candidate_name": cstr(row.candidate_name), "destination": cstr(row.notice_address), "destination_version": cstr(row.notice_address_version or 1), "registered_at": row.registered_at}


def candidate_name(*, tender: str, candidate_registration_id: str) -> str:
	"""Protected: authorised procurement / support / audit readers only."""
	row = candidate_registration(tender=tender, candidate_registration_id=candidate_registration_id)
	return cstr((row or {}).get("candidate_name"))


# --------------------------------------------------------------------------
# the stand-in's service-identity command (plan W2) — the Start bid stand-in
# --------------------------------------------------------------------------


def ensure_producer_role() -> None:
	if not frappe.db.exists("Role", INQUIRY_PRODUCER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": INQUIRY_PRODUCER_ROLE, "desk_access": 0}).insert(ignore_permissions=True)


def require_producer(user: str | None = None) -> str:
	"""The bidder-facing service identity (never a business responsibility)."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest" or INQUIRY_PRODUCER_ROLE not in set(frappe.get_roles(principal)):
		fail("TND_RESPONSIBILITY_REQUIRED", "Only the registered bidder-facing service may deliver this event.")
	return principal


def register_stand_in_candidate(*, tender: str, bidder_arrangement_id: str, candidate_name: str, notice_address: str, registered_at=None, user: str | None = None) -> dict[str, Any]:
	"""Stand-in for BDS **Start bid**'s candidate registration: idempotent on
	`bidder_arrangement_id`; only for a Published — open Tender."""
	producer = require_producer(user)
	if not is_stand_in():
		fail("TND_RESPONSIBILITY_REQUIRED", "Candidates are registered through Bid Submission on this site.")
	arrangement = cstr(bidder_arrangement_id).strip()
	address = cstr(notice_address).strip()
	if not arrangement or "@" not in address:
		fail("TND_CONTROL_INVALID", "A bidder arrangement and a verified mandatory-notice email address are required.")
	existing = frappe.db.get_value(STAND_IN, {"bidder_arrangement_id": arrangement}, ["name", "tender"], as_dict=True)
	if existing:
		if existing.tender != tender:
			fail("TND_CONTROL_INVALID", "This bidder arrangement is registered on another Tender.")
		return {"ok": True, "idempotent": True, "candidate_registration_id": arrangement}
	root = frappe.db.get_value("Tender", {"name": tender}, ["name", "overall_status", "fixture_namespace"], as_dict=True) or frappe.db.get_value("Tender", {"tender_reference": tender}, ["name", "overall_status", "fixture_namespace"], as_dict=True)
	if not root:
		fail("TND_NOT_FOUND")
	if root.overall_status != "Published — open":
		fail("TND_STALE_VERSION", "Candidates can register only while the Tender is Published — open.")
	envelope.insert(
		frappe.get_doc(
			{
				"doctype": STAND_IN, "tender": root.name, "bidder_arrangement_id": arrangement, "candidate_name": cstr(candidate_name).strip(),
				"notice_address": address, "notice_address_version": 1, "status": "Active", "registered_at": get_datetime(registered_at) if registered_at else clock.now(),
				"registered_by": producer, "record_version": 0, "fixture_namespace": root.fixture_namespace,
			}
		)
	)
	return {"ok": True, "idempotent": False, "candidate_registration_id": arrangement}
