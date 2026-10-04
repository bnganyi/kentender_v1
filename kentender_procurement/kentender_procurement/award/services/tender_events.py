# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tenders' authoritative events for an award (AWD-CHG-001 v0.4 §5.5–§5.7;
AWD-AC-018).

A valid cancellation before any notice was issued closes the case: pending
Award tasks close, all completed work is kept, the interrupted journey stage
is marked Blocked and the record shows "This tender was cancelled. Award
ended." An unavailable or stale status never closes a case. After a notice
was given the pre-notification route is unavailable, so a cancellation event
then becomes a restriction for the applicable legal disposition instead.
Suspensions become holds; validity extensions are Tenders' facts and are read
live. Tenders owns all of these; Award never creates a competing command."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import checks, clock, issues, notify, records, restrictions, sources, state


def consume(doc) -> int:
	"""Take up every new status event for this case, once per event key."""
	try:
		events = sources.for_case(doc).status_events(doc.tender)
	except sources.SourceUnavailable:
		checks.sync(doc)
		return 0
	count = 0
	for event in events:
		key = cstr(event.get("event_key"))
		if not key or frappe.db.exists(state.ISSUE, {"source_event": f"tender-event:{key}"}) or doc.cancellation_event == key:
			continue
		kind = cstr(event.get("kind"))
		if kind == "Cancellation":
			_cancel(doc, event)
		elif kind in ("Suspension", "Review order"):
			restrictions._hold(doc, source_event=f"tender-event:{key}", basis="Authoritative order", source=cstr(event.get("authority") or event.get("source")),
				received_at=clock.now(), effective_at=get_datetime(event.get("effective_at")) if event.get("effective_at") else clock.now(),
				scope=cstr(event.get("scope") or "This award"), evidence=cstr(event.get("source_reference") or event.get("instruction")),
				reason=cstr(event.get("reason")), actor="system")
		elif kind == "Resumption":
			for i in issues.open_issues(doc, issue_type="Review/order"):
				detail = records.loads(i.detail_json)
				detail.setdefault("release_evidence", []).append({"event": key, "reference": cstr(event.get("source_reference")), "at": str(clock.now())})
				records.update(i, detail_json=records.dumps(detail))
			issues.open_issue(doc, source_event=f"tender-event:{key}", issue_type="Review/order", subtype="Resumption received",
				title="This award is on hold.", holds=False, reason="Release evidence was received. Record the outcome of each restriction.",
				evidence=cstr(event.get("source_reference")))
		else:
			issues.open_issue(doc, source_event=f"tender-event:{key}", issue_type="Validity", subtype="Tender event", title=cstr(event.get("kind")), holds=False,
				reason=cstr(event.get("reason")), evidence=cstr(event.get("source_reference")))
		count += 1
		doc = state.reload(doc)
	return count


def _cancel(doc, event: dict[str, Any]) -> None:
	st = checks.tender_status(doc)
	if not st["known"] or not st["cancelled"]:
		return  # an invalid, stale or unavailable cancellation cannot close a case
	key = cstr(event.get("event_key"))
	if doc.notification_status != "Not issued":
		issues.open_issue(doc, source_event=f"tender-event:{key}", issue_type="Review/order", subtype="Cancellation after notification", basis="Authoritative order",
			title="This award is on hold.", reason="The tender was cancelled after an award notice was issued. Record the applicable legal disposition.",
			source=cstr(event.get("authority")), evidence=cstr(event.get("source_reference")))
		return
	c = state.cycle(doc)
	records.update(c, interrupted_stage=doc.stage, outcome="Cancelled", closed_at=clock.now(), stage="Closed")
	batch = state.current_batch(doc)
	if batch and batch.state in ("Prepared", "Authorised"):
		records.update(batch, state="Stopped", stop_reason="cancelled")
	records.bump(doc, cancelled=1, cancellation_event=key, stage="Closed", outcome="Cancelled", closed_at=clock.now(),
		closed_reason=cstr(event.get("reason")) or "This tender was cancelled. Award ended.")
	notify.tell(doc, [issues.hop_for(doc), issues.ao_for(doc)], subject=f"This tender was cancelled. Award ended. ({doc.tender_reference})", key=f"cancel:{key}")
	records.audit(doc.name, "ReceiveTenderCancellation", "system", event=key)


def consume_case(award: str) -> int:
	def body() -> dict[str, Any]:
		doc = records.lock(award)
		return {"ok": True, "award": award, "count": consume(doc)}

	return records.command("ReceiveTenderEvent", case=award, idempotency_key=f"tender-events:{award}:{frappe.generate_hash(length=10)}", actor="system",
		payload={}, body=body)["count"]


def sweep() -> int:
	count = 0
	for name in frappe.get_all(records.CASE, filters={"stage": ("!=", "Closed")}, pluck="name"):
		try:
			count += consume_case(name)
		except Exception:
			frappe.log_error(title=f"Award tender events failed for {name}")
	return count
