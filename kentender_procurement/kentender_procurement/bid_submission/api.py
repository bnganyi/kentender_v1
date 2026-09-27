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
from kentender_procurement.bid_submission.services import save as save_service
from kentender_procurement.bid_submission.services import security_intake as security_intake_service
from kentender_procurement.bid_submission.services import receipts as receipts_service
from kentender_procurement.bid_submission.services import signature as signature_service
from kentender_procurement.bid_submission.services import submission as submission_service
from kentender_procurement.bid_submission.services import tender_contact as tender_contact_service
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


def _masked(fn, **arguments) -> dict[str, Any]:
	"""A bid the person may not see reads as Not found, as data (§8)."""
	try:
		return fn(**arguments)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND", "heading": "Bid not found", "text": "This bid is unavailable or you do not have permission to view it."}


@frappe.whitelist(methods=["GET"])
def get_my_bids(organisation: str = "") -> dict[str, Any]:
	"""BDS §7.1 `GetMyBids`."""
	return reads.get_my_bids(organisation=organisation)


@frappe.whitelist(methods=["GET"])
def get_bid_workspace(bid_reference: str, organisation: str = "") -> dict[str, Any]:
	"""BDS §7.1 `GetBidWorkspace`."""
	return _masked(reads.get_bid_workspace, bid_reference=bid_reference, organisation=organisation)


@frappe.whitelist(methods=["GET"])
def get_bid_task(bid_reference: str, task: str, organisation: str = "") -> dict[str, Any]:
	"""BDS §7.1 `GetBidTask`."""
	return _masked(reads.get_bid_task, bid_reference=bid_reference, task=task, organisation=organisation)


@frappe.whitelist(methods=["GET"])
def get_bid_review(bid_reference: str, organisation: str = "") -> dict[str, Any]:
	"""BDS §7.1 `GetBidReview`."""
	return _masked(reads.get_bid_review, bid_reference=bid_reference, organisation=organisation)

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


@frappe.whitelist(methods=["POST"])
def save_bid_task(bid_reference: str, task: str, values=None, expected_record_version=None, organisation: str = "", idempotency_key: str = "") -> dict[str, Any]:
	"""BDS §7.2 `SaveBidTask`."""
	return _masked(save_service.save_bid_task, bid_reference=bid_reference, task=task, values=_parse_json(values, {}), expected_record_version=expected_record_version, organisation=organisation, idempotency_key=idempotency_key)


@frappe.whitelist(methods=["POST"])
def update_tender_contact(bid_reference: str, email: str = "", phone: str = "", expected_record_version=None, organisation: str = "", idempotency_key: str = "") -> dict[str, Any]:
	"""The bid's Tender contact (BDS §4.3; not named in BDS §7.2, FU-V08-34)."""
	return _masked(tender_contact_service.update_tender_contact, bid_reference=bid_reference, email=email, phone=phone, expected_record_version=expected_record_version, organisation=organisation, idempotency_key=idempotency_key)


# --------------------------------------------------------------------------
# Blind physical tender-security intake (owner decisions OD-G/OD-H) — the
# Head of Procurement Function's Desk page; nothing about bids is returned.
# --------------------------------------------------------------------------


@frappe.whitelist(methods=["POST"])
def record_physical_tender_security_receipt(tender_reference: str, instrument_type: str = "", issuer: str = "", instrument_reference: str = "", amount: str = "", currency: str = "", received_at: str = "", notes: str = "", confirmed=False, idempotency_key: str = "") -> dict[str, Any]:
	"""BDS §7.3 `RecordPhysicalTenderSecurityReceipt`, as a blind intake."""
	return security_intake_service.record_physical_tender_security_receipt(
		tender_reference=tender_reference, instrument_type=instrument_type, issuer=issuer, instrument_reference=instrument_reference, amount=amount, currency=currency,
		received_at=received_at, notes=notes, confirmed=confirmed, idempotency_key=idempotency_key,
	)


FORBIDDEN_INTAKE = {"outcome": "FORBIDDEN", "heading": "You do not have access to tender-security receipts", "text": security_intake_service.DENIED}


@frappe.whitelist(methods=["GET"])
def list_my_tender_security_intakes(tender_reference: str = "") -> dict[str, Any]:
	try:
		return {"outcome": "OK", **security_intake_service.list_my_intakes(tender_reference=tender_reference)}
	except frappe.PermissionError:
		return dict(FORBIDDEN_INTAKE)


@frappe.whitelist(methods=["GET"])
def get_tender_security_requirement(tender_reference: str) -> dict[str, Any]:
	try:
		return {"outcome": "OK", **security_intake_service.tender_security_requirement(tender_reference=tender_reference)}
	except frappe.PermissionError:
		return dict(FORBIDDEN_INTAKE)


# --------------------------------------------------------------------------
# §7.3 Signature and submission — the Authorised Signatory only (checked in
# the services); every outcome the supplier must see is returned as data.
# --------------------------------------------------------------------------


@frappe.whitelist(methods=["GET"])
def get_submit_bid(bid_reference: str, organisation: str = "") -> dict[str, Any]:
	"""BDS-DES-12: server time, summary, signatory and whether Submit is possible now."""
	return _masked(submission_service.get_submit_bid, bid_reference=bid_reference, organisation=organisation)


@frappe.whitelist(methods=["GET"])
def check_certificate(bid_reference: str, organisation: str = "") -> dict[str, Any]:
	"""BDS §11.5 Check certificate — a fresh trust-service read; changes nothing."""
	return _masked(signature_service.check_certificate, bid_reference=bid_reference, organisation=organisation)


@frappe.whitelist(methods=["POST"])
def prepare_bid_signature(bid_reference: str, confirmed=False, expected_record_version=None, idempotency_key: str = "", organisation: str = "") -> dict[str, Any]:
	"""BDS §7.3 `PrepareBidSignature`."""
	return _masked(signature_service.prepare_bid_signature, bid_reference=bid_reference, confirmed=confirmed, expected_record_version=expected_record_version, idempotency_key=idempotency_key, organisation=organisation)


@frappe.whitelist(methods=["POST"])
def sign_with_test_trust_service(signing_request: str) -> dict[str, Any]:
	"""The Test Trust Service's own signing step — a test environment only (OD-C)."""
	return signature_service.sign_with_test_trust_service(signing_request=signing_request)


@frappe.whitelist(methods=["POST"])
def submit_bid(bid_reference: str, signature: str = "", confirmed=False, expected_record_version=None, idempotency_key: str = "", organisation: str = "") -> dict[str, Any]:
	"""BDS §7.3 `SubmitBid`."""
	return _masked(submission_service.submit_bid, bid_reference=bid_reference, signature_ref=signature, confirmed=confirmed, expected_record_version=expected_record_version, idempotency_key=idempotency_key, organisation=organisation)


@frappe.whitelist(methods=["GET"])
def get_submission_status(bid_reference: str, organisation: str = "") -> dict[str, Any]:
	"""BDS §11.5 View status — reads the latest attempt; never dispatches."""
	return _masked(submission_service.get_submission_status, bid_reference=bid_reference, organisation=organisation)


def _receipt_masked(fn, **arguments):
	try:
		return fn(**arguments)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND", "heading": "Receipt not found", "text": "This receipt is unavailable or you do not have permission to view it."}


@frappe.whitelist(methods=["GET"])
def get_bid_receipt(receipt_reference: str, organisation: str = "") -> dict[str, Any]:
	"""BDS-DES-13 receipt facts."""
	return _receipt_masked(receipts_service.get_bid_receipt, receipt_reference=receipt_reference, organisation=organisation)


@frappe.whitelist(methods=["GET"])
def download_bid_receipt(receipt_reference: str, organisation: str = "") -> None:
	"""BDS §11.6 Download receipt — the immutable receipt as a PDF."""
	try:
		name, content = receipts_service.receipt_pdf(receipt_reference=receipt_reference, organisation=organisation)
	except frappe.DoesNotExistError:
		raise frappe.DoesNotExistError("This receipt is unavailable or you do not have permission to view it.")
	frappe.local.response.filename = name
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"
