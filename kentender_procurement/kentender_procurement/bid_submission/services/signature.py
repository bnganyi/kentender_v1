# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Signing a bid (BDS-CHG-001 v0.8 §5.7 items 3–6, §7.3 `PrepareBidSignature`,
§11.5 Check certificate; plan D6).

`submittable` is the one set of checks run immediately before signing and
again immediately before deposit (§5.7 item 3, BDS01-AC-056): the person is
the bid's active Authorised Signatory; the Account is Active; the bid is not
already submitted; the Tender is open and the trusted instant is before the
effective deadline; the production switch is on and every service is
healthy; the supplier-portal information is complete; the record version is
the one the signatory reviewed; no addendum waits and nothing is Must fix;
no earlier attempt is still being confirmed; and the signatory holds a
valid certificate. Each failure is its own §8 code, and none creates
anything.

`prepare_bid_signature` then asks the approved trust service for a signing
request over the exact canonical package; the signatory signs it in that
service's own step, and `SubmitBid` verifies the returned signature against
the package it rebuilds. A typed name, a checkbox, an image, a password or a
staff flag is never a signature: the only accepted proof is the trust
service's verification."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import (
	addendum,
	availability,
	bid_context,
	clock,
	gateways,
	labels,
	package,
	readiness,
	records,
	simulation,
	tenders_gateway,
)
from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services.errors import fail, field_errors

PENDING = ("Dispatching", "Uncertain")
CONFIRMATION_MISSING = "Confirm that the information in this bid is correct and that you are authorised to submit it."


def signatory_of(ctx, actor: str) -> dict[str, Any]:
	"""The submitting signatory: the actor's own active Authorised Signatory
	assignment in the lead organisation (for a joint venture, the one the
	arrangement names)."""
	assignment = ctx.assignment
	named = cstr(ctx.arrangement.authorised_signatory_assignment)
	if assignment.get("responsibility") != authz.SIGNATORY or not assignment.get("active") or not assignment.get("signatory_ready"):
		fail("BDS_SIGNATORY_REQUIRED")
	if named and assignment.get("assignment_id") != named:
		fail("BDS_SIGNATORY_REQUIRED")
	return {"assignment_id": assignment["assignment_id"], "full_name": labels.person_name(actor), "job_title": cstr(assignment.get("job_title"))}


def require_before_deadline(ctx, at) -> Any:
	root = tenders_gateway.tender_root(ctx.workspace.tender_reference)
	if not root or not root.submission_deadline:
		fail("BDS_TENDER_NOT_OPEN")
	if get_datetime(at) >= get_datetime(root.submission_deadline):
		fail("BDS_DEADLINE_PASSED")
	if tenders_gateway.availability(ctx.workspace.tender_reference, at=at) != "open":
		fail("BDS_TENDER_NOT_OPEN")
	return root


def require_portal_information() -> None:
	from kentender_core.services import public_portal

	if (public_portal.get_public_portal_information() or {}).get("status") != "Complete":
		fail("BDS_PORTAL_INFORMATION_UNAVAILABLE")


def pending_attempt(workspace: str) -> str | None:
	return frappe.db.get_value("Bid Submission Attempt", {"bid_workspace": workspace, "status": ("in", PENDING)}, "correlation_id")


def certificate(actor: str, organisation: str, at) -> dict[str, Any]:
	service = gateways.trust()
	if not gateways.trust_healthy():
		fail("BDS_SIGNATURE_UNAVAILABLE")
	return service.certificate(user=actor, organisation=organisation, at=at)


def submittable(ctx, *, actor: str, at, expected_record_version, confirmed) -> tuple[dict[str, Any], Any]:
	"""(signatory, Tender root) once every pre-signing and pre-deposit check passes."""
	signatory = signatory_of(ctx, actor)
	authz.active_account(ctx.workspace.lead_organisation)
	if ctx.workspace.status == "Submitted":
		fail("BDS_ALREADY_SUBMITTED")
	if ctx.workspace.status in ("Withdrawn", "Closed without submission"):
		fail("BDS_TENDER_NOT_OPEN")
	root = require_before_deadline(ctx, at)
	availability.require_available()
	require_portal_information()
	records.check_version(ctx.workspace, expected_record_version)
	if addendum.pending(ctx) is not None:
		fail("BDS_ADDENDUM_REVIEW_REQUIRED")
	tasks = readiness.evaluate(ctx, attention=addendum.attention(ctx))
	if readiness.bid_status(tasks) != "Ready to submit":
		items = [{"task": key, "label": s.field.label, "text": s.issue["text"]} for key, t in tasks.items() for s in t.fields if s.issue and s.issue["severity"] == readiness.MUST_FIX]
		fail("BDS_MUST_FIX", detail={"items": items, "needs_attention": [key for key, t in tasks.items() if t.status == "Needs attention"]})
	correlation = pending_attempt(ctx.workspace.name)
	if correlation:
		fail("BDS_SUBMISSION_UNCERTAIN", detail={"correlation_id": correlation})
	if certificate(actor, ctx.workspace.lead_organisation, at)["status"] != "Ready":
		fail("BDS_SIGNATORY_CERTIFICATE_REQUIRED")
	if not _ticked(confirmed):
		raise _Unconfirmed()
	return signatory, root


class _Unconfirmed(Exception):
	"""The final confirmation is a field error, returned as data."""


def _ticked(value) -> bool:
	return bool(value) and cstr(value).lower() not in ("0", "false", "no")


def prepare_bid_signature(*, bid_reference: str, confirmed=False, expected_record_version=None, idempotency_key: str = "", organisation: str = "", user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	payload = {"bid_reference": cstr(bid_reference), "confirmed": _ticked(confirmed), "expected_record_version": cstr(expected_record_version)}
	return records.idempotent(idempotency_key, "PrepareBidSignature", payload, lambda: _prepare(actor, bid_reference, confirmed, expected_record_version, organisation), actor=actor, organisation=organisation)


def _prepare(actor: str, bid_reference: str, confirmed, expected_record_version, organisation: str) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	try:
		signatory, _root = submittable(ctx, actor=actor, at=at, expected_record_version=expected_record_version, confirmed=confirmed)
	except _Unconfirmed:
		return field_errors({"confirmed": CONFIRMATION_MISSING})
	built = package.build(ctx, signatory=signatory, confirmed=True)
	request = gateways.trust().request_signature(package_digest=built.package_digest, user=actor, organisation=ctx.workspace.lead_organisation, at=at)
	if not request.get("ok"):
		fail("BDS_SIGNATORY_CERTIFICATE_REQUIRED")
	records.emit(
		"BidSignatureRequested", tender=ctx.workspace.tender, arrangement=ctx.arrangement.name, workspace=ctx.workspace.name, organisation=ctx.workspace.lead_organisation, actor=actor, at=at,
		payload={"draft_version": int(ctx.workspace.current_draft_version or 0), "package_digest": built.package_digest, "signing_request_id": request["signing_request_id"], "signatory_assignment": signatory["assignment_id"]},
	)
	return {"ok": True, "signing_request": request["signing_request_id"], "signing_service": gateways.trust().name, "simulation": bool(request.get("simulation"))}


def check_certificate(*, bid_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""§11.5 Check certificate: a fresh trust-service read for the signatory;
	it creates nothing and changes nothing."""
	actor = cstr(user or frappe.session.user)
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	signatory_of(ctx, actor)
	found = certificate(actor, ctx.workspace.lead_organisation, at)
	from kentender_procurement.bid_submission.services import labels

	ready = found["status"] == "Ready"
	return {
		"status": "Ready" if ready else "Required", "valid_to": labels.date_label(found.get("valid_to")) if ready else "",
		"text": "Digital certificate ready" if ready else "A valid digital signature certificate is required before you can submit.",
		"simulation": bool(found.get("simulation")),
	}


def sign_with_test_trust_service(*, signing_request: str, user: str | None = None) -> dict[str, Any]:
	"""The Test Trust Service's own signing step (owner decision OD-C): on a
	test environment only, the person the request names signs it. A real
	trust service runs this step in its own signing client."""
	if not simulation.enabled():
		raise frappe.PermissionError("The test signing step exists only on a test environment.")
	service = gateways.trust()
	return service.sign(signing_request_id=cstr(signing_request), user=cstr(user or frappe.session.user), at=clock.now())
