# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""View status (BDS-CHG-001 v0.8 §11.5, §10.17; plan Phase 11, slice 11.15):
a read of the latest submission attempt, or of the submission service when
there is none — it never dispatches anything. It answers with one §10.17
common state:

- an attempt still being checked → Confirmation pending, with its correlation
  and support reference (View status reads again);
- a definite rejection → the tender box rejected this attempt, with Try
  confirmation again only while the server allows a new attempt;
- an accepted attempt → straight to its receipt;
- no attempt → the deadline passed, the production gate, a signing or
  submission outage, or simply "not submitted"."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import availability, common_states, labels, submission, tenders_gateway, workspace_view

ATTEMPT = "Bid Submission Attempt"


def _support_href() -> str:
	links = workspace_view._support_links()
	return links[0]["href"] if links else ""


def view(ctx, *, at) -> dict[str, Any]:
	ws = ctx.workspace
	base = f"/tenders/{ws.tender_reference}/bid"
	root = tenders_gateway.tender_root(ws.tender_reference)
	deadline = labels.datetime_label(root.submission_deadline) if root else ""
	closed = bool(root and root.submission_deadline and get_datetime(at) >= get_datetime(root.submission_deadline))
	now = labels.datetime_seconds_label(at)
	page = {"title": "Submission status", "back_href": base}
	name = frappe.db.get_value(ATTEMPT, {"bid_workspace": ws.name}, "name", order_by="creation desc")
	attempt = frappe.get_doc(ATTEMPT, name) if name else None
	if attempt and attempt.status == "Accepted":
		receipt = cstr(frappe.db.get_value("Bid Submission Version", attempt.submission_version, "receipt"))
		return {"page": page, "state": None, "redirect": f"{base}/receipt/{quote(receipt)}"}
	if attempt and attempt.status == "Rejected" and ws.status != "Submitted":
		outcome = submission.outcome(attempt)
		retry = bool(outcome.get("retry_allowed"))
		state = common_states.state(
			"custody-rejected", href=f"{base}/submit" if retry else _support_href(), retry=retry,
			rejection_reference=outcome.get("rejection_reference"), current_time=now, deadline=deadline,
		)
		return {"page": page, "state": state, "redirect": ""}
	if attempt:  # received, not yet answered: the same attempt is being checked
		outcome = submission.outcome(attempt)
		state = common_states.state("confirmation-pending", href=f"{base}/status", correlation_id=outcome.get("correlation_id"), support_reference=outcome.get("support_reference"))
		return {"page": page, "state": state, "redirect": ""}
	if closed:
		return {"page": page, "state": common_states.state("deadline-passed", href="/my-bids", deadline=deadline, current_time=now), "redirect": ""}
	code = availability.get_submission_availability()["code"]
	if code == "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED":
		state = common_states.state("production-not-enabled", href=base, deadline=deadline)
	elif code == "BDS_SIGNATURE_UNAVAILABLE":
		state = common_states.state("signing-unavailable", href=_support_href(), deadline=deadline)
	elif code == "BDS_SUBMISSION_SERVICE_UNAVAILABLE":
		state = common_states.state("submission-unavailable", href=_support_href())
	else:
		state = common_states.state("not-submitted", href=base)
	return {"page": page, "state": state, "redirect": ""}


def get_status_page(*, tender_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import bid_context, clock, reads

	actor, at = cstr(user or frappe.session.user), clock.now()
	bid = reads.bid_for_tender(tender_reference=tender_reference, actor=actor, organisation=organisation, at=at)
	return view(bid_context.load(bid, actor=actor, organisation=organisation, at=at), at=at)
