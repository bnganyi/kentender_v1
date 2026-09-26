# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission endpoints (BDS-CHG-001 v0.8 §7). Thin: each forwards to
one service; authority and every rule live in the services."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.bid_submission.services import clarification as clarification_service
from kentender_procurement.bid_submission.services import notice_contact as notice_contact_service
from kentender_procurement.bid_submission.services import reads
from kentender_procurement.bid_submission.services import snapshot as snapshot_service
from kentender_procurement.bid_submission.services import start_bid as start_bid_service


def _parse_json(value, default):
	# `from __future__ import annotations` switches off Frappe's argument
	# coercion, so a dict posted as form data arrives as a JSON string.
	if value is None:
		return default
	if isinstance(value, str):
		return json.loads(value) if value.strip() else default
	return value


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_available_tenders(search: str = "", method: str = "", reservation: str = "", closing: str = "open") -> dict[str, Any]:
	"""BDS §7.1 `GetAvailableTenders` — public; no identity is needed."""
	return reads.get_available_tenders(search=search, method=method, reservation=reservation, closing=closing)


# --------------------------------------------------------------------------
# §7.2 Preparation commands — signed-in suppliers; the services check who
# may act, for which organisation, on which Tender.
# --------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def start_bid(tender_reference: str, organisation: str = "", arrangement=None, notice_contact_id: str = "", idempotency_key: str = "") -> dict[str, Any]:
	"""BDS §7.2 `StartBid`."""
	return start_bid_service.start_bid(tender_reference=tender_reference, organisation=organisation, arrangement=_parse_json(arrangement, {}), notice_contact_id=notice_contact_id, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def update_tender_notice_contact(bidder_arrangement_id: str, notice_contact_id: str, expected_record_version=None, organisation: str = "", idempotency_key: str = "") -> dict[str, Any]:
	"""BDS §7.2 `UpdateTenderNoticeContact`."""
	return notice_contact_service.update_tender_notice_contact(bidder_arrangement_id=bidder_arrangement_id, notice_contact_id=notice_contact_id, expected_record_version=expected_record_version, organisation=organisation, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def submit_tender_clarification(tender_reference: str, question: str, organisation: str = "", idempotency_key: str = "") -> dict[str, Any]:
	"""BDS §7.2 `SubmitTenderClarification`."""
	return clarification_service.submit_tender_clarification(tender_reference=tender_reference, question=question, organisation=organisation, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def refresh_bid_organisation_snapshot(bid_reference: str, confirm=False, expected_record_version=None, organisation: str = "", idempotency_key: str = "") -> dict[str, Any]:
	"""BDS §7.2 `RefreshBidOrganisationSnapshot`."""
	confirmed = str(confirm).strip().lower() in ("1", "true", "yes") if not isinstance(confirm, bool) else confirm
	return snapshot_service.refresh_bid_organisation_snapshot(bid_reference=bid_reference, confirm=confirmed, expected_record_version=expected_record_version, organisation=organisation, idempotency_key=idempotency_key)
