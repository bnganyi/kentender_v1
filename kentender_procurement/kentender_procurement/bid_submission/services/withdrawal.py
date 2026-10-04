# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`WithdrawBid` (BDS-CHG-001 v0.8 §4.11, §5.8 items 5–7, §7.3, §10.15).

Only the active Authorised Signatory, before the deadline, names the current
submitted bid (by its receipt), gives a reason of 10–500 characters and
confirms. The Version becomes Withdrawn, the bid has no current submission,
and a `WD-…` acknowledgement records who and when on the trusted clock.
Nothing is deleted: the envelope, the signature, the receipt and the whole
history stay, and the Bid Opening hand-off carries the withdrawal. A new
replacement may still be started before the deadline. After the deadline the
command is refused (`BDS_WITHDRAWAL_BLOCKED`) and changes nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import bid_context, clock, labels, records, signature, submission, tenders_gateway
from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services.errors import fail, field_errors

CHANGE = "Bid Submission Change"
REASON_HINT = "Enter 10–500 characters."
CONFIRM_TEXT = "Confirm that you want to withdraw this bid."
NOTICE = "The bid will no longer be considered. You may submit a new replacement before the deadline. The submitted history will not be deleted."


def _acknowledgement_reference(tender: str, tender_reference: str) -> str:
	from kentender_procurement.bid_submission.services import references

	references.lock_tender(tender)
	number = frappe.db.count(CHANGE, {"tender": tender, "change_type": "Withdrawal"}) + 1
	return f"WD-{cstr(tender_reference).removeprefix('TND-')}-{number:03d}"


def withdraw_bid(*, bid_reference: str, receipt_reference: str = "", reason: str = "", confirmed=False, expected_record_version=None, idempotency_key: str = "", organisation: str = "", user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"bid_reference": cstr(bid_reference), "receipt_reference": cstr(receipt_reference).strip(), "reason": cstr(reason).strip(), "confirmed": signature._ticked(confirmed), "expected_record_version": cstr(expected_record_version)}
	return records.idempotent(idempotency_key, "WithdrawBid", payload, lambda: _withdraw(actor, organisation=organisation, **payload), actor=actor, organisation=organisation)


def _withdraw(actor: str, *, organisation: str, bid_reference: str, receipt_reference: str, reason: str, confirmed: bool, expected_record_version) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	signature.signatory_of(ctx, actor)
	authz.active_account(ctx.workspace.lead_organisation)
	ws = ctx.workspace
	root = tenders_gateway.tender_root(ws.tender_reference)
	if not root or not root.submission_deadline or get_datetime(at) >= get_datetime(root.submission_deadline):
		fail("BDS_WITHDRAWAL_BLOCKED")
	if tenders_gateway.availability(ws.tender_reference, at=at) != "open":
		fail("BDS_TENDER_NOT_OPEN")
	current = cstr(ws.current_submission_version)
	current_receipt = cstr(frappe.db.get_value("Bid Submission Version", current, "receipt")) if current else ""
	if not current:
		fail("BDS_STALE_VERSION", detail={"record_version": int(ws.record_version or 0)})  # nothing submitted to withdraw
	if receipt_reference and receipt_reference != current_receipt:
		fail("BDS_REPLACEMENT_CONFLICT", detail={"current_receipt": current_receipt})
	records.check_version(ws, expected_record_version)
	correlation = signature.pending_attempt(ws.name)
	if correlation:
		fail("BDS_SUBMISSION_UNCERTAIN", detail={"correlation_id": correlation})
	problems = {}
	if not (10 <= len(reason) <= 500):
		problems["reason"] = REASON_HINT
	if not confirmed:
		problems["confirmed"] = CONFIRM_TEXT
	if problems:
		return field_errors(problems)
	version = frappe.get_doc("Bid Submission Version", current)
	with records.atomic("withdraw-bid"):
		records.save(submission._set(version, status="Withdrawn", status_since=at))
		change = submission._change(ws, "Withdrawal", affected=version.name, actor=actor, at=at, acknowledgement=_acknowledgement_reference(ws.tender, ws.tender_reference), reason=reason)
		records.bump(ws, status="Withdrawn", status_since=at, current_submission_version=None)
		records.emit(
			"BidWithdrawn", tender=ws.tender, arrangement=ctx.arrangement.name, workspace=ws.name, organisation=ws.lead_organisation, actor=actor, at=at,
			payload={"submission_version": version.name, "acknowledgement": change.acknowledgement_ref, "envelope": version.tender_box_envelope},
		)
	return {"ok": True, **acknowledgement_facts(change)}


def acknowledgement_facts(change) -> dict[str, Any]:
	ws = frappe.get_doc("Bid Workspace", change.bid_workspace)
	arrangement = frappe.get_doc("Bidder Arrangement", ws.bidder_arrangement)
	version = frappe.db.get_value("Bid Submission Version", change.affected_submission_version, ["version_number", "receipt"], as_dict=True)
	return {
		"acknowledgement_reference": change.acknowledgement_ref, "tender_reference": ws.tender_reference, "bidder": cstr(arrangement.joint_venture_name) or cstr(arrangement.lead_legal_name),
		"bid_reference": ws.name, "withdrawn_version": f"Submitted bid Version {int(version.version_number)}", "withdrawn_receipt": version.receipt, "withdrawn_by": change.requested_by_name,
		"withdrawn_at": labels.datetime_seconds_label(change.acknowledged_at), "status": "Withdrawn", "notice": "The submitted history has not been deleted.",
	}


def get_withdrawal_acknowledgement(*, acknowledgement_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	name = frappe.db.get_value(CHANGE, {"acknowledgement_ref": cstr(acknowledgement_reference).strip(), "change_type": "Withdrawal"}, "name") if cstr(acknowledgement_reference).strip() else None
	if not name:
		raise frappe.DoesNotExistError("This acknowledgement is unavailable or you do not have permission to view it.")
	change = frappe.get_doc(CHANGE, name)
	try:
		bid_context.workspace_for(change.bid_workspace, actor=cstr(user or frappe.session.user), organisation=organisation, at=clock.now())
	except frappe.DoesNotExistError:
		raise frappe.DoesNotExistError("This acknowledgement is unavailable or you do not have permission to view it.")
	return acknowledgement_facts(change)
