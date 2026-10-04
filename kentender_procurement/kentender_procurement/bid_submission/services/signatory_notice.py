# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Telling the Authorised Signatory the bid is ready (owner request, 2 Oct 2026).

When the bid becomes ready the system already opens a "Review and submit" item
for the signatory and sends one message (`handoffs.sync`). The person who
prepared the bid cannot see that, cannot repeat it and cannot add a word. This
is the deliberate version: from the bid page the preparer sends the signatory
a message with a link to the bid and an optional note, through the same supplier
message transport, recorded as a `SignatoryNotified` event, and not more often
than every ten minutes. The signatory never needs it, and a bid that is not
ready or not open cannot be handed over."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import frappe
from frappe.utils import cstr, escape_html, get_datetime, get_url

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import bid_context, clock, guidance, handoffs, labels, records, save, tenders_gateway
from kentender_procurement.bid_submission.services.errors import field_errors

EVENT = "SignatoryNotified"
INTERVAL = timedelta(minutes=10)
MAX_NOTE = 500
READY = "Ready to submit"


def next_allowed(last: datetime | None) -> datetime | None:
	"""When another notice may be sent, given when the last one was; None when none was."""
	return get_datetime(last) + INTERVAL if last else None


def compose(*, sender: str, tender_title: str, bid: str, deadline_label: str, url: str, note: str) -> tuple[str, str]:
	"""The subject and the HTML body. Everything typed or looked up is escaped."""
	quoted = f"<blockquote>{escape_html(note)}</blockquote>" if note else ""
	body = (
		f"<p>{escape_html(sender)} has finished preparing the bid {escape_html(bid)} for {escape_html(tender_title)} and is waiting for you to review and submit it.</p>"
		f"{quoted}<p>Submissions close {escape_html(deadline_label)}.</p>"
		f'<p><a href="{escape_html(url)}">Open the bid</a></p>'
	)
	return f"Bid ready for your signature: {tender_title}", body


def _last(workspace: str) -> dict[str, Any] | None:
	rows = frappe.get_all("Bid Submission Event", filters={"bid_workspace": workspace, "event_type": EVENT}, fields=["actor", "occurred_at"], order_by="occurred_at desc", limit_page_length=1)
	return rows[0] if rows else None


def status(ctx, *, at) -> dict[str, Any] | None:
	"""What the bid page shows the preparer: who is waiting, when they were last
	told and whether another notice may go now. None for the signatory, and for a
	bid that is not ready or not open."""
	ws = ctx.workspace
	if guidance.viewer_submits(ctx) or ws.status != READY:
		return None
	root = tenders_gateway.tender_root(ws.tender_reference)
	if not root or not root.submission_deadline or get_datetime(at) >= get_datetime(root.submission_deadline):
		return None
	names = guidance.signatory_names(ctx, at)
	if not names:
		return None
	last = _last(ws.name)
	allowed = next_allowed(last["occurred_at"]) if last else None
	waiting = bool(allowed and get_datetime(at) < allowed)
	return {
		"signatories": names, "can_notify": not waiting,
		"last": {"by": labels.person_name(last["actor"]), "at_label": labels.datetime_label(last["occurred_at"])} if last else None,
		"wait_text": f"You can send another reminder after {labels.datetime_label(allowed)}." if waiting else "",
		"max_note": MAX_NOTE,
	}


def notify_signatory(*, bid_reference: str, note: str = "", organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "note": cstr(note).strip(), "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "NotifySignatory", payload, lambda: _notify(actor=actor, **payload), actor=actor, organisation=payload["organisation"])


def _notify(*, actor: str, bid_reference: str, note: str, organisation: str) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	authz.active_account(ctx.workspace.lead_organisation)
	save.require_open(ctx)  # a closed bid or Tender is refused with its own code
	ws = ctx.workspace
	if guidance.viewer_submits(ctx):
		return field_errors({"notify": "You are the Authorised Signatory: submit the bid yourself."})
	if ws.status != READY:
		return field_errors({"notify": "Finish the bid first: the signatory can only be notified once every task is complete."})
	if len(note) > MAX_NOTE:
		return field_errors({"note": f"Keep the message to {MAX_NOTE} characters or fewer."})
	users = handoffs._signatories(ws, ctx.arrangement)
	if not users:
		return field_errors({"notify": "No Authorised Signatory is registered for this bid. Ask your Account administrator to add one."})
	last = _last(ws.name)
	allowed = next_allowed(last["occurred_at"]) if last else None
	if allowed and get_datetime(at) < allowed:
		return field_errors({"notify": f"{', '.join(guidance.signatory_names(ctx, at))} was already notified. You can send another reminder after {labels.datetime_label(allowed)}."})
	published = tenders_gateway.published_tender(ws.tender_reference, at=at) or {}
	root = tenders_gateway.tender_root(ws.tender_reference)
	subject, body = compose(
		sender=labels.person_name(actor), tender_title=cstr(published.get("title") or ws.tender_reference), bid=ws.name, deadline_label=labels.datetime_label(root.submission_deadline) if root else "",
		url=get_url(f"/tenders/{ws.tender_reference}/bid/review"), note=note,
	)
	with records.atomic("notify-signatory"):
		result = handoffs._message(users, subject, body)
		records.emit(EVENT, tender=ws.tender, arrangement=ctx.arrangement.name, workspace=ws.name, organisation=ws.lead_organisation, actor=actor, at=at,
			payload={"recipients": users, "note": note, "result": result})
	return {"ok": True, "recipients": [labels.person_name(u) for u in users], "notified_at": labels.datetime_label(at), "result": result}
