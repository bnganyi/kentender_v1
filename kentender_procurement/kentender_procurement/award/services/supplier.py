# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The supplier's award notice (AWD-CHG-001 v0.4 §5.5, §5.6, §6, §9;
AWD-AC-011, AC-012, AC-015).

`GetSupplierAwardNotice` shows a supplier user their own organisation's
notice only — never another recipient's letter, the internal record or its
tracker. `RespondToAward` is the organisation's active Authorised Signatory's
act on the exact current notice: acceptance records identity, authority,
exact wording and trusted time and does not re-sign the bid; a decline needs
a reason; a response after the deadline is kept, labelled late and cannot be
used to proceed. A representative can read and ask for an explanation but
cannot accept or decline. `RequestAwardExplanation` opens private
correspondence for the Head of Procurement; it is not a Review Board filing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.award.services import clock, clocks, eligibility, issues, notify, people, records, sources, state
from kentender_procurement.award.services.errors import fail, invalid
from kentender_procurement.services import sequence

NOTICE = state.NOTICE
NOT_A_CONTRACT = "Accepting this award does not create a contract."
LATE = "Your response was received after the deadline. It cannot be used to proceed with this award."


def _load(notice: str):
	if not notice or not frappe.db.exists(NOTICE, notice):
		raise frappe.DoesNotExistError("Not found")
	n = frappe.get_doc(NOTICE, notice)
	if not n.published_at:
		raise frappe.DoesNotExistError("Not found")
	return n, frappe.get_doc(records.CASE, n.award_case)


def _authority(doc, n, user: str) -> dict[str, Any]:
	"""(signatory, acting) at the trusted instant; anyone else sees Not found."""
	provider = sources.for_case(doc)
	at = clock.now()
	acting = provider.acting_for(user, n.organisation, at=at) if user and user != "Guest" else None
	if not acting:
		raise frappe.DoesNotExistError("Not found")
	signatory = provider.signatory(user, n.organisation, at=at)
	return {"acting": acting, "signatory": signatory}


def _case_of(notice: str) -> str:
	return (frappe.db.get_value(NOTICE, notice, "award_case") if notice else "") or ""


def _authorise(notice: str, user: str, *, signatory: bool = False) -> None:
	"""The caller's standing for a supplier command, before the journal is read."""
	n, doc = _load(notice)
	auth = _authority(doc, n, user)
	if signatory and not auth["signatory"]:
		fail("AWD_AUTHORITY_REQUIRED", {"reason": "signatory_required"})


def _current(doc, n) -> bool:
	return doc.current_batch == n.batch and not doc.cancelled


def notice_view(*, notice: str, user: str) -> dict[str, Any]:
	n, doc = _load(notice)
	auth = _authority(doc, n, user)
	body = records.loads(n.content_json)
	deadline = clocks.reply_deadline_for(n) if n.result == "Successful" else None
	own = state.responses(n)
	operative = state.operative_response(n)
	late = [r for r in own if r.late]
	signatory = bool(auth["signatory"])
	signatory_name = ""
	if not signatory:
		people_ = sources.for_case(doc).organisation_users(n.organisation, at=clock.now())
		signatory_name = next((people.full_name(p.get("user")) for p in people_ if p.get("responsibility") == "Authorised Signatory"), "")
	current = _current(doc, n)
	can_respond = bool(signatory and current and n.result == "Successful" and not operative and not late and n.status == "Given" and
		not (deadline and clock.now() > deadline))
	if n.result == "Successful":
		if late:
			headline, sentence, kind = LATE, "", "waiting"
		elif operative:
			headline = "You accepted this award." if operative.response == "Accept" else "You declined this award."
			sentence, kind = "", "done"
		elif not signatory:
			headline, sentence, kind = "Your tender was successful.", f"{signatory_name or 'Your Authorised Signatory'} must respond for {n.organisation_name}.", "waiting"
		else:
			headline, sentence, kind = "Your tender was successful.", "", "turn"
	else:
		headline, sentence, kind = "Your tender was unsuccessful.", "", "done"
	requests = [explanation_view(c) for c in (frappe.get_doc(state.CORRESPONDENCE, x) for x in frappe.get_all(state.CORRESPONDENCE,
		filters={"notice": n.name}, pluck="name", order_by="requested_at asc"))]
	return {
		"ok": True, "notice": n.name, "notice_version": n.version, "notice_label": body.get("notice"), "tender_reference": doc.tender_reference,
		"tender_title": doc.tender_title, "procuring_entity": doc.procuring_entity, "organisation": n.organisation, "organisation_name": n.organisation_name,
		"result": n.result, "statement": body.get("statement"), "reason": body.get("reason"), "amount": body.get("award_amount") if n.result == "Successful" else "",
		"successful_supplier": body.get("successful_supplier") if n.result == "Unsuccessful" else "", "award_amount": body.get("award_amount"),
		"own_amount": body.get("own_amount", ""), "own_evaluated": body.get("own_evaluated", ""),
		"reply_deadline": clock.when(deadline) if deadline else "", "not_a_contract": NOT_A_CONTRACT if n.result == "Successful" else "",
		"review_information": body.get("review_information"), "letter_html": n.letter_html, "current": current,
		"responses": [{"response": r.response, "by": people.full_name(r.responder), "received_at": clock.when(r.received_at), "late": bool(r.late),
			"wording": r.wording, "reason": r.reason} for r in own],
		"can_respond": can_respond, "is_signatory": signatory, "signatory_name": signatory_name,
		"accept_wording": f"I accept {body.get('notice')} on behalf of {n.organisation_name}.",
		"next_step": {"kind": kind, "headline": headline, "sentence": sentence}, "requests": requests,
		"test_environment": _test_label(doc),
	}


def _test_label(doc) -> str:
	from kentender_procurement.award.services import simulation

	return simulation.TEST_LABEL if simulation.enabled() else ""


def explanation_view(c) -> dict[str, Any]:
	return {"request": c.name, "text": c.request_text, "requested_at": clock.when(c.requested_at), "by": people.full_name(c.requested_by),
		"state": c.state, "reply": c.reply_text if c.reply_state == "Sent" else "", "closed_at": clock.when(c.closed_at)}


def respond(*, notice: str, response: str, reason: str = "", notice_version=None, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		n, doc = _load(notice)
		doc = records.lock(doc.name)
		n = frappe.get_doc(NOTICE, notice)
		auth = _authority(doc, n, user)
		if not auth["signatory"]:
			fail("AWD_AUTHORITY_REQUIRED", {"reason": "signatory_required"})
		if response not in ("Accept", "Decline"):
			invalid({"response": "Choose Accept award or Decline award."})
		if not _current(doc, n) or n.result != "Successful" or cint(notice_version) != cint(n.version):
			fail("AWD_NOTICE_CHANGED", {"notice": n.name})
		invalid({"reason": "Enter the reason." if response == "Decline" and not cstr(reason).strip() else ""})
		if state.operative_response(n):
			fail("AWD_RECORD_CHANGED", {"reason": "already_responded"})
		for i in issues.holding(doc):
			if i.issue_type == "Review/order" and i.basis == "Authoritative order":
				fail("AWD_ON_HOLD", {"issue": i.name})
		now = clock.now()
		deadline = clocks.reply_deadline_for(n)
		late = bool(deadline and now > deadline)
		label = records.loads(n.content_json).get("notice")
		wording = (f"I accept {label} on behalf of {n.organisation_name}." if response == "Accept" else f"I decline {label} on behalf of {n.organisation_name}.")
		number = sequence.next_count(state.RESPONSE, {"notice": n.name})
		row = records.new(state.RESPONSE, response_id=f"{n.name}-R{number:02d}", notice=n.name, award_case=doc.name, notice_version=n.version, response=response,
			responder=user, organisation=n.organisation, authority_evidence=cstr(auth["signatory"].get("assignment_id")), wording=wording, reason=cstr(reason).strip(),
			received_at=now, late=1 if late else 0, operative=0 if late else 1, fixture_namespace=doc.fixture_namespace)
		hop = issues.hop_for(doc)
		if late:
			existing = issues.open_issues(doc, subtype=eligibility.RESPONSE_SUBTYPE_OVERDUE)
			if existing:
				detail = {**records.loads(existing[0].detail_json), "late_response": row.name}
				records.update(existing[0], detail_json=records.dumps(detail), evidence=f"Received after the deadline: {clock.when(now)}")
			else:
				issues.open_issue(doc, source_event=f"no-response:{n.name}", issue_type="Supplier response", subtype=eligibility.RESPONSE_SUBTYPE_OVERDUE,
					title="The supplier has not replied by the deadline.", reason=f"Reply deadline: {clock.when(deadline)}", effective_at=deadline,
					detail={"notice": n.name, "deadline": str(deadline), "late_response": row.name})
			notify.tell(doc, [hop], subject=f"Resolve supplier response for {doc.tender_reference}", message=LATE, key=f"late:{row.name}")
		elif response == "Decline":
			issues.open_issue(doc, source_event=f"declined:{row.name}", issue_type="Supplier response", subtype=eligibility.RESPONSE_SUBTYPE_DECLINED,
				title="Review the supplier’s response.", reason=cstr(reason).strip(), effective_at=now, detail={"notice": n.name, "response": row.name})
			notify.tell(doc, [hop], subject=f"Resolve supplier response for {doc.tender_reference}", message=cstr(reason).strip(), key=f"declined:{row.name}")
		else:
			notify.tell(doc, [hop], subject=f"{n.organisation_name} accepted the award for {doc.tender_reference}", key=f"accepted:{row.name}")
		records.bump(doc)
		records.audit(doc.name, "RespondToAward", user, notice=n.name, response=response, late=late)
		eligibility.refresh(state.reload(doc))
		out = {"ok": True, "response": row.name, "late": late}
		if late:
			out.update(code="AWD_RESPONSE_LATE", message=LATE)
		return out

	return records.command("RespondToAward", case=_case_of(notice), idempotency_key=idempotency_key, actor=user,
		payload={"notice": notice, "response": response, "reason": reason, "version": cstr(notice_version)}, body=body,
		authorise=lambda: _authorise(notice, user, signatory=True))


def request_explanation(*, notice: str, request: str, idempotency_key: str, user: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		n, doc = _load(notice)
		_authority(doc, n, user)
		invalid({"request": "Enter your request." if not cstr(request).strip() else ""})
		previous = frappe.db.get_value(state.CORRESPONDENCE, {"notice": n.name}, "name", order_by="requested_at desc")
		number = sequence.next_count(state.CORRESPONDENCE, {"award_case": doc.name})
		row = records.new(state.CORRESPONDENCE, correspondence_id=f"{doc.name}-REQ-{number:02d}", award_case=doc.name, notice=n.name, organisation=n.organisation,
			organisation_name=n.organisation_name, requested_by=user, request_text=cstr(request).strip(), requested_at=clock.now(), predecessor=previous or "",
			reply_state="", attempts_json="[]", state="Open", fixture_namespace=doc.fixture_namespace)
		notify.tell(doc, [issues.hop_for(doc)], subject=f"Respond to request for {doc.tender_reference}", message=cstr(request).strip(), key=f"request:{row.name}")
		records.audit(doc.name, "RequestAwardExplanation", user, request=row.name)
		return {"ok": True, "request": row.name}

	return records.command("RequestAwardExplanation", case=_case_of(notice), idempotency_key=idempotency_key, actor=user, payload={"notice": notice, "request": request}, body=body,
		authorise=lambda: _authorise(notice, user))


def my_notices(*, user: str) -> list[dict[str, Any]]:
	"""The supplier user's own published notices, newest first."""
	out = []
	orgs = set()
	for kind in sources.providers().values():
		orgs |= set(kind.organisations_of(user, at=clock.now()))
	if not orgs:
		return out
	for name in frappe.get_all(NOTICE, filters={"organisation": ("in", list(orgs)), "published_at": ("is", "set")}, pluck="name", order_by="published_at desc"):
		n = frappe.get_doc(NOTICE, name)
		doc = frappe.get_doc(records.CASE, n.award_case)
		out.append({"notice": n.name, "tender_reference": doc.tender_reference, "tender_title": doc.tender_title, "result": n.result,
			"label": records.loads(n.content_json).get("notice"), "current": _current(doc, n)})
	return out

