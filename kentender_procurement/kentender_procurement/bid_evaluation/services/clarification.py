# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Written clarification (EVL-CHG-001 v0.4 §5.3, §7.2, §7.3 rows 7–9, §8
EVL_REPLY_CLOSED, EVL_CLARIFICATION_NOTICE_FAILED, EVL_REPLY_OVERDUE; plan
D11, D14; tracker EVL4-701…708; boards D05-CHAIR, D06-*).

The chair authorises, during the recorded collective discussion with the
whole current eligible roster present, the exact question, the affected
published requirement and original response, the permissible reply scope
and a future reply deadline; authorisation records the committee's question
and decision in one operation. The secretary sends that unchanged request;
no separate procurement approval. The request is available to the
supplier's authorised users whether or not the courtesy email arrives; a
failed notice is recorded truthfully and retried for the same request.

The supplier sends one reply with allowed supporting files; a draft can be
edited until sent; a sent reply cannot be replaced. Timeliness uses the
trusted received instant; while the request is open a late reply is kept and
labelled Received late for the committee's disposition. No reply gives Reply
overdue, never automatic rejection. The committee's final disposition closes
the request atomically, with or without a reply; withdrawal or cancellation
also closes it; the deadline alone does not. After closure the question,
any reply or unsent draft, the disposition and the closure time stay, and no
further draft or reply is accepted. An attempted price or specification
change is kept as correspondence and excluded. The original bid never
changes."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_evaluation.services import (
	clock, conclusion, discussion, findings, guards, notify, prc, records, roster, simulation,
)
from kentender_procurement.bid_evaluation.services.errors import Guards, fail, invalid
from kentender_procurement.services import sequence

REQUEST = "Evaluation Clarification"
REPLY = "Evaluation Clarification Reply"
DISPOSITIONS = ("Considered", "Not considered", "Excluded change", "No reply")
OPEN = ("Sent",)
TRANSPORT_HOOK = "kt_bds_supplier_message_transports"


def _request(doc, name: str):
	row = frappe.db.get_value(REQUEST, {"name": name, "evaluation_case": doc.name}, "name")
	if not row:
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(REQUEST, row)


def supplier_users(bid) -> list[str]:
	from kentender_procurement.bid_submission.services import bid_authorization, supplier_gateway

	return sorted({p["user"] for p in supplier_gateway.organisation_people(organisation_id=bid.organisation_id)
		if p.get("active", True) and p.get("responsibility") in bid_authorization.PREPARERS and p.get("user")})


# -- the committee ----------------------------------------------------------------
def authorise(*, tender: str, bid: str, requirement_key: str, question: str, reply_scope: str, reply_deadline, replaces: str = "", replacement_reason: str = "",
		idempotency_key: str, user: str) -> dict[str, Any]:
	"""AuthoriseClarification. A question that replaces one already sent
	carries the chair's reason, which the secretary's withdrawal records."""
	payload = {"bid": bid, "requirement_key": requirement_key, "question": question, "reply_scope": reply_scope, "reply_deadline": cstr(reply_deadline),
		"replaces": replaces, "replacement_reason": replacement_reason}
	discussion.recheck_presence(tender)

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.chair(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		members = conclusion.collective(doc, idempotency_key)
		requirement = findings._requirement(doc, bid, requirement_key)
		fields = {f: "Required." for f, v in (("question", question), ("reply_scope", reply_scope)) if not cstr(v).strip()}
		deadline = get_datetime(reply_deadline) if reply_deadline else None
		if deadline is None or deadline <= clock.now():
			fields["reply_deadline"] = "Set a reply deadline in the future."
		if replaces and not cstr(replacement_reason).strip():
			fields["replacement_reason"] = "Give the reason for replacing the question."
		invalid(fields)
		if replaces:
			prior = _request(doc, replaces)
			if prior.status not in ("Sent", "Authorised") or prior.replaced_by:
				fail("EVL_VERSION_CONFLICT", {"reason": "not_replaceable"})
		out = conclusion.committed(doc, event_type="ClarificationAuthorised", owner_event_id=f"clarification:{doc.name}:{idempotency_key}", members=members,
			payload={"bid": bid, "requirement": requirement_key, "deadline": cstr(deadline), "replaces": replaces}, note=cstr(question).strip(),
			idempotency_key=idempotency_key)
		item = conclusion.open_item_for(doc, bid, requirement_key)
		decided = conclusion.insert(doc, kind="Clarification authorised", session=out["session_id"],
			reason=cstr(replacement_reason).strip() if replaces else cstr(question).strip(), recorded_by=user,
			participants=out["participants"], event=out["event_id"], bid=bid, requirement_key=requirement_key, next_action="Clarification", item=item or "")
		number = sequence.next_count(REQUEST, {"evaluation_case": doc.name})
		request = records.insert(frappe.get_doc({
			"doctype": REQUEST, "clarification_id": f"{doc.name}-CLR-{number:02d}", "evaluation_case": doc.name, "evaluation_bid": bid,
			"requirement_key": requirement_key, "response_id": "", "question": cstr(question).strip(), "reply_scope": cstr(reply_scope).strip(),
			"reply_deadline": deadline, "authorised_by": user, "authorised_at": clock.now(), "session": out["session_id"], "conclusion": decided.name,
			"status": "Authorised", "replaces": replaces, "record_version": 1,
		}))
		if replaces:
			records.save(frappe.get_doc(REQUEST, replaces).update({"replaced_by": request.name}))
		if item:
			findings.clear_item(doc, item, kind="Clarification", reference=request.name)
		conflicts = date_conflicts(doc, deadline)
		sec = roster.secretary(doc.name)
		bidder = frappe.db.get_value("Evaluation Bid", bid, "tenderer_name")
		notify.tell(doc, [sec] if sec else [], subject=f"Send clarification for {bidder}", message=f"Send the committee's authorised question to {bidder}.",
			key=f"send-{request.name}")
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, clarification=request.name, requirement=requirement["label"], date_conflicts=conflicts)

	return records.command("AuthoriseClarification", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def date_conflicts(doc, deadline) -> list[str]:
	"""The dates the chair sees before authorising (§5.3)."""
	from kentender_procurement.bid_evaluation.services import timers

	dated, out = timers.dated(doc), []
	if deadline and dated["validity_end"] and get_datetime(deadline) > get_datetime(dated["validity_end"]):
		out.append("The reply deadline is after the tender validity ends.")
	if deadline and dated["evaluation_deadline"] and get_datetime(deadline) > get_datetime(dated["evaluation_deadline"]):
		out.append("The reply deadline is after the evaluation deadline.")
	return out


def _deliver(doc, request) -> bool:
	if simulation.controls().get("notice_outcome") == "Failed":
		return False
	bid = frappe.get_doc("Evaluation Bid", request.evaluation_bid)
	users = supplier_users(bid)
	transports = [frappe.get_attr(p) for p in reversed(frappe.get_hooks(TRANSPORT_HOOK) or [])]
	if not users or not transports:
		return False
	for user in users:
		message = {"to": user, "subject": f"Reply to clarification for {doc.tender_reference}",
			"body": f"Reply by {cstr(request.reply_deadline)} EAT. The question is in your bid workspace.",
			"link": f"/tenders/{doc.tender_reference}/bid/evaluation-clarifications/{request.name}"}
		answer = next((taken for taken in (t(message) for t in transports) if taken is not None), None)
		if answer is None:
			return False
	return True


def _notice(doc, request) -> str:
	delivered = _deliver(doc, request)
	request.notice_attempts = (request.notice_attempts or 0) + 1
	request.notice_state = "Delivered" if delivered else "Delivery problem"
	records.save(request)
	return request.notice_state


def send(*, tender: str, clarification: str, idempotency_key: str, user: str) -> dict[str, Any]:

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.secretary(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		guards.open_case(doc).raise_if_any()
		request = _request(doc, clarification)
		if request.status != "Authorised":
			fail("EVL_VERSION_CONFLICT", {"reason": "not_authorised", "status": request.status})
		bid = frappe.get_doc("Evaluation Bid", request.evaluation_bid)
		request.update({"status": "Sent", "sent_by": user, "sent_at": clock.now(), "recipient_organisation": bid.organisation_id,
			"recipient_users_json": json.dumps(supplier_users(bid)), "notice_correlation": f"notice:{request.name}"})
		records.save(request)
		state = _notice(doc, request)
		event = prc.owner_event(doc, "ClarificationSent", f"sent:{request.name}", {"clarification": request.name, "notice": state}, idempotency_key=idempotency_key)
		records.bump(doc, last_committed_event=event)
		out = records.summary(doc, clarification=request.name, notice_state=state)
		if state != "Delivered":
			out.update({"notice_code": "EVL_CLARIFICATION_NOTICE_FAILED", "notice_message": "The clarification notice could not be delivered."})
		return out

	return records.command("SendClarification", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"clarification": clarification}, body=body)


def retry_notice(*, tender: str, clarification: str, idempotency_key: str, user: str) -> dict[str, Any]:

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.secretary(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		request = _request(doc, clarification)
		if request.status != "Sent" or request.notice_state == "Delivered":
			return records.summary(doc, clarification=request.name, notice_state=request.notice_state)
		state = _notice(doc, request)
		out = records.summary(doc, clarification=request.name, notice_state=state)
		if state != "Delivered":
			out.update({"notice_code": "EVL_CLARIFICATION_NOTICE_FAILED", "notice_message": "The clarification notice could not be delivered."})
		return out

	return records.command("RetryClarificationNotice", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"clarification": clarification},
		body=body)


def withdraw(*, tender: str, clarification: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""The secretary withdraws with the chair's recorded reason."""

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if roster.secretary(doc.name) != user:
			raise frappe.DoesNotExistError("Not found")
		guards.closed(doc, Guards()).raise_if_any()
		invalid({"reason": "Give the chair's recorded reason."} if not cstr(reason).strip() else {})
		request = _request(doc, clarification)
		if request.status not in ("Authorised", "Sent"):
			fail("EVL_VERSION_CONFLICT", {"reason": "closed", "status": request.status})
		request.update({"status": "Withdrawn", "withdrawal_reason": cstr(reason).strip(), "withdrawn_by": user, "withdrawn_at": clock.now(), "closed_at": clock.now(),
			"closure_reason": "Withdrawn"})
		records.save(request)
		event = prc.owner_event(doc, "ClarificationWithdrawn", f"withdrawn:{request.name}", {"clarification": request.name}, idempotency_key=idempotency_key,
			note=cstr(reason).strip())
		records.bump(doc, last_committed_event=event)
		return records.summary(doc, clarification=request.name)

	return records.command("WithdrawClarification", tender=tender, idempotency_key=idempotency_key, actor=user, payload={"clarification": clarification,
		"reason": reason}, body=body)


def record_disposition(*, tender: str, clarification: str, disposition: str, result: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	"""RecordReplyDisposition: the committee's final disposition, which is
	itself the linked conclusion and closes the request atomically."""
	payload = {"clarification": clarification, "disposition": disposition, "result": result, "reason": reason}
	discussion.recheck_presence(tender)

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		conclusion.require_recorder(doc, user)
		members = conclusion.collective(doc, idempotency_key)
		request = _request(doc, clarification)
		if request.status != "Sent":
			fail("EVL_VERSION_CONFLICT", {"reason": "not_open", "status": request.status})
		reply = frappe.db.get_value(REPLY, {"clarification": request.name, "state": "Sent"}, ["name", "timeliness"], as_dict=True)
		fields = {}
		if disposition not in DISPOSITIONS:
			fields["disposition"] = "Choose the disposition."
		elif disposition == "No reply" and reply:
			fields["disposition"] = "A reply was received; record how it is treated."
		elif disposition != "No reply" and not reply:
			fields["disposition"] = "No reply was received; record No reply."
		if result not in findings.RESULTS:
			fields["result"] = "Choose Meets, Does not meet or Needs review."
		if not cstr(reason).strip():
			fields["reason"] = "Give the committee's reason."
		requirement = findings._requirement(doc, request.evaluation_bid, request.requirement_key)
		if requirement["automatic"] == "Does not meet" and result == "Meets":
			fields["result"] = "A failed mandatory requirement cannot be waived."
		invalid(fields)
		out = conclusion.committed(doc, event_type="ReplyDisposition", owner_event_id=f"disposition:{request.name}", members=members,
			payload={"clarification": request.name, "disposition": disposition, "result": result}, note=cstr(reason).strip(), idempotency_key=idempotency_key)
		decided = conclusion.insert(doc, kind="Reply disposition", session=out["session_id"], reason=reason, recorded_by=user, participants=out["participants"],
			event=out["event_id"], bid=request.evaluation_bid, requirement_key=request.requirement_key, result=result,
			evidence=[request.name] + ([reply.name] if reply else []), next_action="Qualified report" if result == "Needs review" else "")
		request.update({"disposition": disposition, "disposition_result": result, "disposition_reason": cstr(reason).strip(), "disposition_conclusion": decided.name,
			"status": "Closed", "closed_at": clock.now(), "closure_reason": "Final disposition"})
		request.record_version = (request.record_version or 0) + 1
		records.save(request)
		records.bump(doc, last_committed_event=out["event_id"])
		return records.summary(doc, clarification=request.name, conclusion=decided.name)

	return records.command("RecordReplyDisposition", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


# -- the supplier -------------------------------------------------------------------
def _supplier_request(tender: str, clarification: str, user: str, organisation: str = ""):
	"""The supplier's own request, or the protected Not found."""
	from kentender_procurement.bid_submission.services import bid_authorization
	from kentender_procurement.bid_submission.services.errors import BidSubmissionError

	name = records.case_for(tender)
	request = frappe.db.get_value(REQUEST, {"name": clarification, "evaluation_case": name}, ["name", "evaluation_bid", "status"], as_dict=True) if name else None
	if not request or request.status == "Authorised":
		raise frappe.DoesNotExistError("Not found")
	org = frappe.db.get_value("Evaluation Bid", request.evaluation_bid, "organisation_id")
	try:
		# on the trusted instant, as Bid Submission's own commands ask it
		bid_authorization.acting_assignment(user, organisation or org, at=clock.now())
	except BidSubmissionError as exc:
		raise frappe.DoesNotExistError("Not found") from exc
	if organisation and organisation != org:
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(REQUEST, request.name), org


def _reply(request, org: str, user: str):
	name = frappe.db.get_value(REPLY, {"clarification": request.name}, "name")
	if name:
		return frappe.get_doc(REPLY, name)
	return frappe.get_doc({"doctype": REPLY, "reply_id": f"{request.name}-RPL", "clarification": request.name, "evaluation_case": request.evaluation_case,
		"organisation": org, "author_user": user, "state": "Draft", "record_version": 0})


def _closed(request) -> None:
	if request.status != "Sent":
		fail("EVL_REPLY_CLOSED", {"closure": request.closure_reason or request.status, "closed_at": cstr(request.closed_at)})


ATTACHMENT_TYPES = ("application/pdf", "image/png", "image/jpeg")
MAX_ATTACHMENTS = 3
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024


def _attachments(attachments: list | None) -> list[dict[str, Any]]:
	"""The supporting explanation files: request-bound, PDF or image, at most
	three of 5 MB each (EVL-CHG-001 v0.4 §10 "Supporting explanation"). The
	submitted bid itself never changes."""
	import base64
	import hashlib

	out = []
	for item in attachments or []:
		content = base64.b64decode(cstr((item or {}).get("content_base64")) or "", validate=False)
		media = cstr((item or {}).get("media_type"))
		name = cstr((item or {}).get("filename")).strip()
		if not name or media not in ATTACHMENT_TYPES or not content or len(content) > MAX_ATTACHMENT_BYTES:
			invalid({"attachments": "Attach a PDF or image of 5 MB or less."})
		out.append({"filename": name, "media_type": media, "size": len(content), "file_digest": hashlib.sha256(content).hexdigest(),
			"content_base64": base64.b64encode(content).decode()})
	if len(out) > MAX_ATTACHMENTS:
		invalid({"attachments": f"Attach at most {MAX_ATTACHMENTS} files."})
	return out


def save_draft(*, tender: str, clarification: str, body: str, attachments: list | None = None, organisation: str = "", idempotency_key: str,
		user: str) -> dict[str, Any]:
	payload = {"clarification": clarification, "body": body, "attachments": attachments or []}

	def run() -> dict[str, Any]:
		request, org = _supplier_request(tender, clarification, user, organisation)
		frappe.db.sql("select name from `tabEvaluation Clarification` where name=%s for update", request.name)
		request.reload()
		_closed(request)
		reply = _reply(request, org, user)
		if reply.state == "Sent":
			fail("EVL_REPLY_CLOSED", {"reason": "already_sent"})
		reply.update({"body": cstr(body), "attachments_json": json.dumps(_attachments(attachments)), "saved_at": clock.now(), "author_user": user})
		reply.record_version = (reply.record_version or 0) + 1
		records.save(reply) if not reply.is_new() else records.insert(reply)
		return {"ok": True, "clarification": request.name, "state": "Draft", "saved_at": cstr(reply.saved_at)}

	return records.command("SaveClarificationDraft", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=run)


def submit_reply(*, tender: str, clarification: str, body: str, attachments: list | None = None, organisation: str = "", idempotency_key: str,
		user: str) -> dict[str, Any]:
	payload = {"clarification": clarification, "body": body, "attachments": attachments or []}

	def run() -> dict[str, Any]:
		request, org = _supplier_request(tender, clarification, user, organisation)
		frappe.db.sql("select name from `tabEvaluation Clarification` where name=%s for update", request.name)
		request.reload()
		_closed(request)
		reply = _reply(request, org, user)
		if reply.state == "Sent":
			fail("EVL_REPLY_CLOSED", {"reason": "already_sent"})
		invalid({"body": "Write your reply."} if not cstr(body).strip() else {})
		received = clock.now()
		late = received > get_datetime(request.reply_deadline)
		reply.update({"body": cstr(body).strip(), "attachments_json": json.dumps(_attachments(attachments)), "saved_at": received, "received_at": received,
			"state": "Sent", "timeliness": "Received late" if late else "On time", "author_user": user})
		reply.record_version = (reply.record_version or 0) + 1
		records.save(reply) if not reply.is_new() else records.insert(reply)
		doc = frappe.get_doc(records.CASE, request.evaluation_case)
		event = prc.owner_event(doc, "ClarificationReplyReceived", f"reply:{reply.name}", {"clarification": request.name, "timeliness": reply.timeliness},
			idempotency_key=idempotency_key)
		records.bump(doc, last_committed_event=event)
		chair, sec = roster.chair(doc.name), roster.secretary(doc.name)
		bidder = frappe.db.get_value("Evaluation Bid", request.evaluation_bid, "tenderer_name")
		notify.tell(doc, [u for u in (chair, sec) if u], subject=f"Review clarification outcome for {bidder}",
			message=f"{bidder} replied to the clarification for {doc.tender_reference}.", key=f"outcome-{request.name}")
		return {"ok": True, "clarification": request.name, "state": "Sent", "received_at": cstr(received), "timeliness": reply.timeliness}

	return records.command("SubmitClarificationReply", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=run)


def overdue(request) -> bool:
	"""Reply overdue (§8 nonblocking): open, no reply sent and past the deadline."""
	return request.status == "Sent" and clock.now() > get_datetime(request.reply_deadline) and not frappe.db.exists(REPLY, {"clarification": request.name,
		"state": "Sent"})
