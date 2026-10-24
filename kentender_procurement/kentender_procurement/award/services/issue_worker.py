# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IssueAwardNotices as a three-phase worker (AWD-CHG-001 v0.9 §5.4, §5.11
"One current fence", §7, §7.2; TPR-CHG-001 v0.24 §5.12; AWD-OF-AC-005, AC-007).

The AO's decision commits with the batch **Authorised**; the issue runs after
that commit (`request` registers it with `frappe.db.after_commit`, so the AO's
screen stays synchronous and no worker is needed), and the sweep recovers a
request that died first. The worker never holds a database transaction or a
lock across an external send:

1. `begin` — one short transaction under the fence (Tender → authority record →
   case → batch). It rechecks, with locking reads, that the cancellation is not
   stamped on the record, the status can be believed and every existing stop
   reason is clear, then writes the batch **Issuing** and the Tender-level
   status **Issue in progress**, and COMMITS. This is the first outward effect's
   durable marker: a cancellation arriving afterwards finds it and is refused.
2. `publish_and_send` — publish every recipient's portal notice together (one
   transaction, committed), then send each external notice with nothing held,
   recording each attempt in its own short transaction.
3. `finish` — lock again, mark the batch **Issued** and the Tender-level status
   **Issued**, derive the given-state, audit, tell the recipients, commit.

A cancellation that wins the fence first leaves the stamp: `begin` then stops the
batch and sends nothing — including a stale queued batch. An interrupted issue
(a process that died after `begin`) stays **Issue in progress**; the sweep turns
it **Unknown** after `STALE_AFTER` and opens a worked issue. It never becomes
Not issued by timeout; only a reconciliation with evidence (`reconcile`) can
settle it, and the server checks that evidence against its own notice rows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.award.services import checks, clock, issues, notices, notify, people, profile, records, simulation, state, tender_authority
from kentender_procurement.award.services.errors import fail

#: An Issue in progress older than this was interrupted. An implementation constant for crash recovery, not a legal or operational target.
STALE_AFTER = timedelta(minutes=15)
#: An Authorised batch whose request never ran its after-commit step is picked up by the sweep after this long.
QUEUED_GRACE = timedelta(minutes=1)
UNKNOWN_SUBTYPE = "Notice status unknown"


def request(doc, batch, *, actor: str = "system") -> None:
	"""Inside the AO's command: the batch is Authorised. Issue it once this transaction commits. A rolled-back command discards the callback."""
	if simulation.flag("issue_deferred"):  # a test control that holds the queued issue back, as a request that died after committing would
		return
	name = batch.name
	frappe.db.after_commit.add(lambda: run(name, actor=actor))


def run(batch_name: str, *, actor: str = "system") -> dict[str, Any]:
	"""The whole issue. Never raises: a failure is logged and leaves the batch where the sweep can find it."""
	try:
		begun = begin(batch_name, actor=actor)
		if begun["status"] != "Started":
			return begun
		publish_and_send(batch_name, token=begun["token"], actor=actor)
		return finish(batch_name, token=begun["token"], actor=actor)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=f"Award notice issue failed for {batch_name}")
		return {"status": "Failed", "batch": batch_name}


def _reasons(doc, row) -> list[str]:
	out = notices.stop_reasons(doc)
	if cstr(row.cancellation_ref) and "cancelled" not in out:
		out.insert(0, "cancelled")
	if cstr(row.notification_status) == tender_authority.UNKNOWN and "status" not in out:
		out.append("status")
	return out


def begin(batch_name: str, *, actor: str = "system") -> dict[str, Any]:
	"""Phase 1 (see the module docstring). Commits before it returns."""
	head = frappe.db.get_value(state.BATCH, batch_name, ["award_case"], as_dict=True)
	if not head:
		return {"status": "Skipped", "reason": "no_such_batch", "batch": batch_name}
	tender = frappe.db.get_value(records.CASE, head.award_case, "tender")
	try:
		row = tender_authority.lock(tender)  # Tender → record → case → batch
		if row is None:
			frappe.db.commit()
			return {"status": "Skipped", "reason": "no_authority_record", "batch": batch_name}
		doc = records.lock(head.award_case)
		batch = frappe.get_doc(state.BATCH, batch_name, for_update=True)
		if batch.state == "Issued" or batch.status == "Issued":
			frappe.db.commit()
			return {"status": "Issued", "batch": batch_name}
		if batch.state != "Authorised":
			frappe.db.commit()
			return {"status": "Skipped", "reason": "in_progress" if batch.state == "Issuing" else cstr(batch.state).lower(), "batch": batch_name}
		if cstr(row.notification_status) == tender_authority.IN_PROGRESS and cstr(row.current_batch) != batch.name:
			frappe.db.commit()
			return {"status": "Skipped", "reason": "another_issue_in_progress", "batch": batch_name}
		stop = _reasons(doc, row)
		if stop:
			notices.stop_batch(doc, batch, stop)
			frappe.db.commit()
			return {"status": "Stopped", "reasons": stop, "batch": batch_name}
		now = clock.now()
		deadline, _rule = profile.reply_deadline(now)
		token = uuid4().hex
		records.update(batch, state="Issuing", status="Issue in progress", issued_at=now, reply_deadline=deadline)
		tender_authority.set_notification(tender, tender_authority.IN_PROGRESS, batch=batch.name, token=token)
		frappe.db.commit()  # the durable marker: from here a cancellation is refused
		return {"status": "Started", "token": token, "case": doc.name, "tender": tender, "batch": batch_name}
	except Exception:
		frappe.db.rollback()
		raise


def publish_and_send(batch_name: str, *, token: str, actor: str = "system") -> dict[str, Any]:
	"""Phase 2: the portal notices together, then each external notice with no transaction or lock held."""
	batch = frappe.get_doc(state.BATCH, batch_name)
	doc = frappe.get_doc(records.CASE, batch.award_case)
	try:
		notices.publish_portal(doc, batch, now=get_datetime(batch.issued_at))
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=f"Award portal publication failed for {batch_name}")
		return {"status": "Failed", "phase": "publish", "batch": batch_name}
	outcomes: dict[str, str] = {}
	for name in [n.name for n in state.notices(frappe.get_doc(state.BATCH, batch_name))]:
		doc = frappe.get_doc(records.CASE, batch.award_case)
		notice = frappe.get_doc(state.NOTICE, name)
		attempt = notices.send(doc, notice)  # outside every transaction: it writes nothing and nothing is locked
		try:
			outcomes[name] = notices.record_attempt(doc, frappe.get_doc(state.NOTICE, name), attempt)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Award notice attempt could not be recorded for {name}")
			outcomes[name] = "Unrecorded"
	return {"status": "Sent", "batch": batch_name, "outcomes": outcomes}


def finish(batch_name: str, *, token: str, actor: str = "system") -> dict[str, Any]:
	"""Phase 3: record the outcome under the fence. Commits before it returns."""
	head = frappe.db.get_value(state.BATCH, batch_name, ["award_case"], as_dict=True)
	tender = frappe.db.get_value(records.CASE, head.award_case, "tender")
	try:
		tender_authority.lock(tender)
		doc = records.lock(head.award_case)
		batch = frappe.get_doc(state.BATCH, batch_name, for_update=True)
		if batch.state != "Issuing":
			frappe.db.commit()
			return {"status": "Issued" if batch.state == "Issued" else "Skipped", "batch": batch_name}
		records.update(batch, state="Issued", status="Issued")
		tender_authority.set_notification(tender, tender_authority.ISSUED, batch=batch.name, token=token)
		doc = state.reload(doc)
		notices.refresh_given(doc, frappe.get_doc(state.BATCH, batch_name))
		records.audit(doc.name, "IssueAwardNotices", actor, batch=batch_name)
		notices.tell_recipients(state.reload(doc), frappe.get_doc(state.BATCH, batch_name))
		frappe.db.commit()
		return {"status": "Issued", "batch": batch_name}
	except Exception:
		frappe.db.rollback()
		raise


# ---------------------------------------------------------------- recovery


def mark_unknown(batch_name: str) -> bool:
	"""An interrupted issue: nothing is known about what went out. The Tender-level status becomes Unknown (it stays Issued if a notice was already
	given), the batch's status Unknown, and a worked issue is opened. Never Not issued."""
	head = frappe.db.get_value(state.BATCH, batch_name, ["award_case"], as_dict=True)
	if not head:
		return False
	tender = frappe.db.get_value(records.CASE, head.award_case, "tender")
	try:
		tender_authority.lock(tender)
		doc = records.lock(head.award_case)
		batch = frappe.get_doc(state.BATCH, batch_name, for_update=True)
		if batch.state != "Issuing" or batch.status != "Issue in progress":
			frappe.db.commit()
			return False
		records.update(batch, status="Unknown")
		tender_authority.set_notification(tender, tender_authority.UNKNOWN, batch=batch.name)
		issues.open_issue(doc, source_event=f"issue-unknown:{batch.name}", issue_type="Service failure", subtype=UNKNOWN_SUBTYPE,
			title="A required notice is not yet confirmed.", owner_role=people.TECHNICAL_OPERATOR, owner_user=checks._technical(),
			reason="The notice issue was interrupted before its outcome was recorded. No notice is assumed to have been sent or withheld.",
			detail={"batch": batch.name, "owner": "Award service owner"})
		checks.open_support_issue(doc, "IssueAwardNotices", f"issue-unknown:{batch.name}", "Reconcile the interrupted notice issue",
			"Operation: Award notice issue. Result: interrupted before its outcome was recorded.")
		records.audit(doc.name, "IssueAwardNoticesInterrupted", "system", batch=batch.name)
		frappe.db.commit()
		return True
	except Exception:
		frappe.db.rollback()
		raise


def sweep() -> dict[str, int]:
	"""The scheduler's step: issue what a dead request left Authorised, and mark what was left Issue in progress Unknown. Idempotent."""
	out = {"issued": 0, "marked_unknown": 0, "stopped": 0}
	now = clock.now()
	if not simulation.flag("issue_deferred"):
		for name in frappe.get_all(state.BATCH, filters={"state": "Authorised"}, pluck="name", order_by="authorised_at asc"):
			authorised = frappe.db.get_value(state.BATCH, name, "authorised_at")
			if authorised and now - get_datetime(authorised) < QUEUED_GRACE:
				continue
			result = run(name)
			out["issued"] += result["status"] == "Issued"
			out["stopped"] += result["status"] == "Stopped"
	for name in frappe.get_all(state.BATCH, filters={"state": "Issuing", "status": "Issue in progress"}, pluck="name"):
		started = frappe.db.get_value(state.BATCH, name, "issued_at")
		if started and now - get_datetime(started) >= STALE_AFTER and mark_unknown(name):
			out["marked_unknown"] += 1
	return out


def reconcile(*, award: str, issue: str, outcome: str, evidence: str, user: str) -> dict[str, Any]:
	"""Settle an Unknown issue with evidence, checked against the server's own notice rows (never the text alone):

	- "Notices were given": at least one notice of the batch was published to its recipient → the batch and the Tender-level status are Issued;
	- "No notice was given": no notice of the batch was published and no attempt was recorded → the Tender-level status returns to Not issued (with that
	  evidence) and the batch to Authorised so it can be issued again.

	Called from the existing issue disposition, which holds the Tender's record, the case and the issue, in that order."""
	row = frappe.get_doc(state.ISSUE, issue)
	batch_name = records.loads(row.detail_json).get("batch")
	batch = frappe.get_doc(state.BATCH, batch_name)
	rows = state.notices(batch)
	published = [n for n in rows if records.loads(n.evidence_json, [])]
	attempted = [n for n in rows if records.loads(n.attempts_json, [])]
	tender = frappe.db.get_value(records.CASE, award, "tender")
	if outcome == GIVEN:
		if not published:
			fail("AWD_ON_HOLD", {"reason": "no_notice_was_published", "owner": "Award service owner"})
		records.update(batch, state="Issued", status="Issued")
		tender_authority.set_notification(tender, tender_authority.ISSUED, batch=batch.name, token=cstr(batch_name))
		notices.refresh_given(state.reload(frappe.get_doc(records.CASE, award)), frappe.get_doc(state.BATCH, batch_name))
	elif outcome == NOT_GIVEN:
		if published or attempted:
			fail("AWD_ON_HOLD", {"reason": "notices_were_published_or_attempted", "owner": "Award service owner"})
		tender_authority.set_notification(tender, tender_authority.NOT_ISSUED, batch=batch.name, no_send_evidence=cstr(evidence))
		records.update(batch, state="Authorised", status="Not issued", issued_at=None)
	else:
		fail("AWD_RECORD_CHANGED", {"reason": "unknown_reconciliation_outcome"})
	return {"batch": batch_name, "outcome": outcome}


GIVEN = "Notices were given"
NOT_GIVEN = "No notice was given"
