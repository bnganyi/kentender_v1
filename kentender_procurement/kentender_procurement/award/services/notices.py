# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award notices (AWD-CHG-001 v0.4 §5.4; AWD-AC-007–010, AC-014).

The audience is every person who submitted a tender, from Bid Submission's
sealed submission and withdrawal history under the verified audience rule —
not the candidate registry, not Evaluation's responsive-only list; draft-only
candidates are never notified and a replaced submission is notified once.
The Accounting Officer's one action authorises the exact generated batch; no
further approval follows. `IssueAwardNotices` is one serialised operation
under the case lock: it rechecks cancellation, validity and restrictions
before the first outward effect, publishes every recipient's portal notice
together, then dispatches the email channel for all. Whether a notice has
been *given* is the verified channel rule's answer, never a send status.
Retries keep the same logical notice and letter; a contact correction changes
only the route and keeps every earlier address and attempt."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import checks, clock, clocks, issues, letters, notify, people, profile, records, simulation, sources, state

BATCH = state.BATCH
NOTICE = state.NOTICE
TRANSPORT_HOOK = "kt_award_notice_transports"
DELIVERY_SUBTYPE = "Notice delivery"
SERVICE_SUBTYPE = "Notice service"
AUDIENCE_SUBTYPE = "Audience unresolved"


class IssueStopped(Exception):
	pass


def audience(doc) -> tuple[list[dict[str, Any]], list[str]]:
	"""(recipients, problems). Withdrawn submissions receive no notice under the
	test profile's audience rule; a missing contact is a problem that stops
	issue and names the Head of Procurement."""
	try:
		rows = sources.for_case(doc).audience(doc.tender)
	except sources.SourceUnavailable:
		return [], ["The bidder list could not be read."]
	recipients = [r for r in rows if r.get("status") == "Submitted"]
	problems = [f"No notice contact is recorded for {r.get('organisation_name')}." for r in recipients if not cstr(r.get("contact_email"))]
	if not recipients:
		problems.append("No submitted tender was found for this tender.")
	return recipients, problems


def _labels(batch_version: int, kind: str) -> str:
	return f"Revised notice {batch_version}" if kind == "Revised" else f"Award notice {batch_version}"


def prepare_batch(doc, decision, *, kind: str = "Initial") -> Any:
	"""The exact notice batch for one decision: one notice per recipient."""
	recipients, problems = audience(doc)
	if problems:
		from kentender_procurement.award.services.errors import fail

		fail("AWD_ON_HOLD", {"reason": problems[0], "problems": problems, "owner": "Head of Procurement"})
	version = records.next_number(BATCH, {"award_case": doc.name})
	batch = records.new(BATCH, batch_id=f"{doc.name}-NB-{version:02d}", award_case=doc.name, decision=decision.name, version=version, kind=kind,
		state="Prepared", status="Not issued", profile_version=profile.current().get("profile_version"), fixture_namespace=doc.fixture_namespace)
	rows = {r.get("organisation"): r for r in state.snapshot(state.current_report(doc)).get("comparison") or []}
	label = _labels(version, kind)
	for i, r in enumerate(recipients, start=1):
		body = letters.content(doc=doc, decision=decision, recipient=r, row=rows.get(r.get("organisation")), notice_label=label, reply_deadline="", kind=kind)
		records.new(NOTICE, notice_id=f"{batch.name}-{i:02d}", batch=batch.name, award_case=doc.name, notice_number=i, version=version,
			organisation=r.get("organisation"), organisation_name=r.get("organisation_name"), bid=cstr(r.get("bidder_arrangement")), bid_reference=r.get("bid_reference"),
			result=body["result"], content_json=records.dumps(body), letter_html="", content_digest="", contact_email=r.get("contact_email"),
			contact_history_json=records.dumps([{"email": r.get("contact_email"), "version": r.get("contact_version"), "at": str(clock.now())}]),
			channels_json=records.dumps(["Portal", "Email"]), attempts_json="[]", evidence_json="[]", status="Prepared", fixture_namespace=doc.fixture_namespace)
	return batch


def preview(doc) -> list[dict[str, Any]]:
	"""What the AO's one action would send, without writing anything."""
	recipients, problems = audience(doc)
	rec = checks.recommendation(doc)
	supplier = (rec.get("recommended") or {}).get("organisation")
	out = [{"organisation": r.get("organisation_name"), "result": "Successful" if r.get("organisation") == supplier else "Unsuccessful",
		"label": f"{'Successful' if r.get('organisation') == supplier else 'Unsuccessful'} bidder notice — {r.get('organisation_name')}"} for r in recipients]
	return out + [{"problem": p} for p in problems]


def authorise(batch, user: str) -> None:
	records.update(batch, state="Authorised", authorised_by=user, authorised_at=clock.now())


def _stop_reasons(doc) -> list[str]:
	out = []
	st = checks.tender_status(doc)
	if not st["known"]:
		out.append("status")
	elif st["cancelled"] or doc.cancelled:
		out.append("cancelled")
	v = checks.validity(doc)
	if v["expired"]:
		out.append("validity")
	if any(i.subtype not in (DELIVERY_SUBTYPE, SERVICE_SUBTYPE) for i in issues.holding(doc)):
		out.append("hold")
	if not profile.verified():
		out.append("rules")
	if checks.funding_stop(doc):
		out.append("funding")
	return out


def issue(doc, batch, *, actor: str = "system") -> dict[str, Any]:
	"""IssueAwardNotices. The caller holds the case lock (the serialised
	issue/cancellation transition): nothing outward happens unless every
	check passes at this moment."""
	if batch.state == "Issued" or batch.status == "Issued":
		return {"status": batch.status}
	stop = _stop_reasons(doc)
	if stop:
		records.update(batch, state="Stopped", stop_reason=", ".join(stop))
		if "validity" in stop:
			issues.open_issue(doc, source_event=f"validity-expired:{doc.name}", issue_type="Validity", subtype=checks.VALIDITY_EXPIRED,
				title="Tender validity has expired. No award can proceed.", reason="Tender validity expired before an award could be notified.")
		if "status" in stop:
			records.bump(doc, notification_status="Unknown" if doc.notification_status == "Issue in progress" else doc.notification_status)
		return {"status": "Stopped", "reasons": stop}
	now = clock.now()
	deadline, rule = profile.reply_deadline(now)
	records.update(batch, state="Issuing", status="Issue in progress", issued_at=now, reply_deadline=deadline)
	records.bump(doc, notification_status="Issue in progress", current_batch=batch.name)
	for n in state.notices(batch):
		body = records.loads(n.content_json)
		if body.get("result") == "Successful":
			body["reply_deadline"] = clock.when(deadline)
		html = letters.render(body)
		records.update(n, content_json=records.dumps(body), letter_html=html, content_digest=records.digest(html), published_at=now, status="Pending",
			reply_deadline=deadline if body.get("result") == "Successful" else None)
		records.append_json(n, "evidence_json", {"channel": "Portal", "at": str(now), "outcome": "Published", "given": False})
		records.save(n)
		if body.get("result") == "Successful":
			clocks.record(doc, kind="Reply deadline", notice=n.name, trigger_at=now, trigger_evidence=f"{n.name} issued {clock.when(now)}", deadline=deadline, rule=rule)
	for n in state.notices(batch):
		_dispatch(doc, n)
	records.update(batch, state="Issued", status="Issued")
	records.bump(state.reload(doc), notification_status="Issued")
	refresh_given(state.reload(doc), batch)
	records.audit(doc.name, "IssueAwardNotices", actor, batch=batch.name)
	for n in state.notices(batch):
		users = [p.get("user") for p in sources.for_case(doc).organisation_users(n.organisation, at=clock.now())]
		notify.tell(doc, users, subject=f"Award notice for {doc.tender_reference}", message=f"{n.organisation_name}: your award result is available.",
			key=f"notice:{n.name}", event_type="Award notice")
	return {"status": "Issued"}


def _transport(message: dict[str, Any]) -> dict[str, Any] | None:
	for path in frappe.get_hooks(TRANSPORT_HOOK) or []:
		result = frappe.get_attr(path)(message)
		if result:
			return result
	return None


def _dispatch(doc, n) -> str:
	"""One email attempt for one notice; the giving evidence follows the
	profile's channel rule (test profile: the test mailbox's delivery)."""
	now = clock.now()
	attempt = {"channel": "Email", "at": str(now), "to": n.contact_email}
	failing = simulation.failing_organisations()
	if simulation.flag("email_service_down"):
		attempt.update(outcome="Service unavailable")
	elif n.organisation in failing or n.organisation_name in failing:
		attempt.update(outcome="Delivery failed", detail="The notice address was rejected.")
	else:
		result = _transport({"to": n.contact_email, "subject": f"Award notice for {doc.tender_reference}", "body": records.loads(n.content_json).get("statement", ""),
			"link": f"/supplier/awards/{n.name}"})
		if result:
			attempt.update(outcome="Delivered", detail=cstr(result.get("result")))
		else:
			attempt.update(outcome="Service unavailable")
	records.append_json(n, "attempts_json", attempt)
	if attempt["outcome"] == "Delivered":
		records.append_json(n, "evidence_json", {"channel": "Email", "at": str(now), "outcome": "Delivered", "given": True, "rule": profile.current().get("profile_version")})
		records.update(n, status="Given", given_at=now, failure_reason="")
		min_at, rule = profile.earliest_permitted(now)
		clocks.record(doc, kind="Minimum wait", notice=n.name, trigger_at=now, trigger_evidence=f"{n.name} given {clock.when(now)}", deadline=min_at, rule=rule)
		for i in issues.open_issues(doc, subtype=DELIVERY_SUBTYPE) + issues.open_issues(doc, subtype=SERVICE_SUBTYPE):
			if records.loads(i.detail_json).get("notice") == n.name:
				issues.resolve(i, disposition="Owner correction confirmed", reason="The notice was given.", evidence=f"Email delivered {clock.when(now)}")
		checks.support_resolved(f"notice:{n.name}")
	elif attempt["outcome"] == "Service unavailable":
		records.update(n, status="Failed", failure_reason="Service unavailable")
		issues.open_issue(doc, source_event=f"notice-service:{n.name}", issue_type="Service failure", subtype=SERVICE_SUBTYPE,
			title="A required notice is not yet confirmed.", owner_role=people.TECHNICAL_OPERATOR, owner_user=checks._technical(), reason="Service unavailable",
			detail={"notice": n.name, "channel": "Email"})
		checks.open_support_issue(doc, "IssueAwardNotices", f"notice:{n.name}", "Restore notice delivery",
			"Operation: Award notice delivery. Result: Service unavailable.")
	else:
		records.update(n, status="Failed", failure_reason=attempt.get("detail") or "Delivery failed")
		issues.open_issue(doc, source_event=f"notice-delivery:{n.name}:{n.contact_email}", issue_type="Delivery", subtype=DELIVERY_SUBTYPE,
			title="A required notice is not yet confirmed.", reason=attempt.get("detail") or "Delivery failed", detail={"notice": n.name, "channel": "Email",
			"organisation": n.organisation_name})
	return attempt["outcome"]


def refresh_given(doc, batch) -> bool:
	"""When every required recipient's notice is given, the Notices stage ends
	(§5.4 "All bidders have been notified")."""
	notices = state.notices(batch)
	if notices and all(n.status == "Given" for n in notices) and not batch.given_complete_at:
		records.update(batch, given_complete_at=clock.now())
		if doc.stage == "Notices":
			state.set_stage(doc, "Waiting to proceed")
		return True
	return bool(batch.given_complete_at)


def all_given(batch) -> bool:
	return bool(batch and batch.given_complete_at)


def retry(doc, n, *, actor: str = "system") -> str:
	"""RetryNoticeDelivery: the same logical notice to its current authoritative
	route. No new decision, no duplicate notice."""
	if n.status == "Given":
		return n.status
	if doc.cancelled:
		return n.status
	current = sources.for_case(doc).notice_contact(n.bid) if n.bid else {}
	if current.get("email") and current["email"] != n.contact_email:
		records.append_json(n, "contact_history_json", {"email": current["email"], "version": current.get("version"), "at": str(clock.now()),
			"source": "Contact owner correction"})
		records.update(n, contact_email=current["email"])
	outcome = _dispatch(doc, n)
	batch = frappe.get_doc(BATCH, n.batch)
	refresh_given(state.reload(doc), batch)
	records.audit(doc.name, "RetryNoticeDelivery", actor, notice=n.name, outcome=outcome)
	return outcome


def retry_failed() -> int:
	"""The sweep retries failed notices of open cases (service failures)."""
	count = 0
	for name in frappe.get_all(NOTICE, filters={"status": "Failed", "failure_reason": "Service unavailable"}, pluck="name"):
		n = frappe.get_doc(NOTICE, name)
		doc = frappe.get_doc(records.CASE, n.award_case)
		if doc.stage in ("Notices", "Waiting to proceed") and retry(doc, n) == "Delivered":
			count += 1
	return count


def notification_summary(batch) -> dict[str, Any]:
	notices = state.notices(batch)
	return {"total": len(notices), "given": len([n for n in notices if n.status == "Given"]), "failed": [n.name for n in notices if n.status == "Failed"]}
