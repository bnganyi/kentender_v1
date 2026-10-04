# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reads (EVL-CHG-001 v0.4 §3, §7.2 "Reads"; plan D20; tracker EVL4-1002,
EVL4-1003): ResolveEvaluation, ListEvaluationWork, ReadEvaluationEvidence,
ReadEvaluationReport, the committee record and the supplier's own
clarification.

Disclosure follows appointment and eligibility, never a menu, role or
opening membership:

- an eligible appointed member, the secretary and an authorised auditor
  read the bids, results and correspondence;
- an appointed member who has not declared, or has declared a conflict,
  reads no bid content;
- the Accounting Officer reads setup and history but no bid facts;
- the Head of Procurement reads setup, and the exact delivered report;
- a technical reader sees status only (KT-STD-001 §3A.6);
- anyone else, and any protected record outside scope, is Not found.

No count, name, amount or finding reaches anyone who may not read bids,
through a field, an error, a task title or an export."""

from __future__ import annotations

import base64
import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import (
	aggregate, checks, comparison, next_steps, people, records, report, roster, signing, sources, timers,
)

WORK_STATES = ("Preparing", "Reviewing", "Signing", "Report sent", "No evaluation required", "Cancelled")


def _case(tender_reference: str):
	name = frappe.db.get_value(records.CASE, {"tender_reference": tender_reference}, "name")
	if not name:
		raise frappe.DoesNotExistError("Not found")
	return frappe.get_doc(records.CASE, name)


def access(doc, user: str) -> dict[str, Any]:
	v = next_steps.viewer(doc, user)
	former = user in [m.member_user for a in frappe.get_all("Evaluation Appointment", filters={"evaluation_case": doc.name}, pluck="name")
		for m in frappe.get_doc("Evaluation Appointment", a).members]
	delivered = frappe.db.exists("Evaluation Report Delivery", {"evaluation_case": doc.name, "recipient_user": user, "status": "Delivered"})
	read = v["technical"] or v["ao"] or v["hop"] or v["auditor"] or v["member"] or v["secretary"] or former
	bids = (v["eligible"] or v["secretary"] or v["auditor"]) and not v["technical"]
	return {**v, "read": read, "bids": bids, "report": bids or bool(delivered), "former": former and not v["member"]}


def require(doc, user: str) -> dict[str, Any]:
	a = access(doc, user)
	if not a["read"]:
		raise frappe.DoesNotExistError("Not found")
	return a


def _source(doc) -> dict[str, Any] | None:
	if not doc.source_intake:
		return None
	bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": doc.name}, ["submission_version", "receipt_reference"], as_dict=True, order_by="entry_number asc")
	return {"opening_completed": next_steps.when(doc.opening_completed_at), "submitted_version": cstr(bid.submission_version) if bid else "",
		"intake": frappe.db.get_value("Evaluation Source Intake", doc.source_intake, "source_kind")}


def committee(doc) -> dict[str, Any]:
	members = []
	for m in roster.current_members(doc.name):
		s = roster.status(doc.name, m["member_user"])
		members.append({"user": m["member_user"], "name": m["full_name"], "department": m["department"], "capacity": m["capacity"],
			"declaration": "Conflict declared" if s["conflict"] else ("No conflict" if s["declared"] else "Declaration owed"), "unavailable": s["unavailable"]})
	sec = frappe.db.get_value("Evaluation Secretary Appointment", {"evaluation_case": doc.name, "status": "Current"}, ["secretary_user", "full_name",
		"appointment_reference"], as_dict=True)
	appointment = roster.current_appointment(doc.name)
	return {"members": members, "appointment_reference": cstr(appointment.appointment_reference) if appointment else "",
		"secretary": {"user": sec.secretary_user, "name": sec.full_name, "reference": sec.appointment_reference} if sec else None}


def conditions(doc) -> dict[str, Any]:
	dated = timers.dated(doc)
	return {"suspended": bool(doc.suspended), "overdue": dated["overdue"], "evaluation_deadline": next_steps.when(dated["evaluation_deadline"]),
		"validity_end": next_steps.when(dated["validity_end"]), "validity_expired": dated["validity_expired"],
		"overdue_message": "The evaluation deadline has passed." if dated["overdue"] else ""}


def resolve(*, tender_reference: str, user: str) -> dict[str, Any]:
	"""ResolveEvaluation: permission, data, available actions and next step."""
	doc = _case(tender_reference)
	a = require(doc, user)
	guidance = next_steps.answer(doc, user)
	holder = cstr((guidance.get("holder") or {}).get("display"))
	out: dict[str, Any] = {
		"evaluation": doc.name, "tender": doc.tender_reference, "title": doc.tender_title, "state": doc.state, "record_version": doc.record_version,
		"guidance": guidance, "tracker": next_steps.tracker(doc, a, holder), "viewer": {k: a[k] for k in ("ao", "hop", "chair", "member", "secretary", "auditor",
			"eligible", "undeclared", "conflicted", "technical", "bids")},
		"conditions": conditions(doc), "closed_reason": cstr(doc.closed_reason),
	}
	if a["technical"]:
		return out
	out["committee"] = committee(doc)
	out["source"] = _source(doc)
	if a["bids"]:
		table = comparison.compare(doc.name)
		out["comparison"] = table
		out["attention"] = frappe.get_all("Evaluation Discussion Item", filters={"evaluation_case": doc.name, "status": "Open"}, fields=["name", "subject",
			"opened_by", "opened_at", "evaluation_bid", "requirement_key"], order_by="opened_at asc")
		for item in out["attention"]:
			item["opened_by_name"] = people.full_name(item.opened_by)
			item["opened"] = next_steps.when(item.opened_at)
		out["outcome"] = report.outcome(doc, table)
	out["work"] = work(doc, a)
	return out


def _attendance(doc, session: str) -> list[dict[str, Any]]:
	"""Each person's joins and departures in one session, in order."""
	rows: dict[str, dict[str, Any]] = {}
	for r in frappe.get_all("Proceeding Attendance", filters={"session": session}, fields=["user", "person_name", "capacity", "movement", "occurred_at"],
			order_by="occurred_at asc, creation asc"):
		row = rows.setdefault(r.user or r.person_name, {"user": r.user, "name": r.person_name, "capacity": r.capacity, "joined": "", "left": "", "present": False})
		if r.movement == "Arrival":
			row.update(joined=next_steps.when(r.occurred_at), left="", present=True)
		else:
			row.update(left=next_steps.when(r.occurred_at), present=False)
	return list(rows.values())


def work(doc, a: dict[str, Any]) -> dict[str, Any]:
	"""The working detail a screen needs, filtered by what this viewer may read."""
	from kentender_procurement.bid_evaluation.services import clarification, diligence, discussion

	out: dict[str, Any] = {}
	events = frappe.get_all("Evaluation Source Event", filters={"evaluation_case": doc.name, "kind": ("in", ("Suspension", "Resumption", "Cancellation"))},
		fields=["name", "kind", "instruction_reference", "authority", "reason", "received_at", "effective_at", "source"], order_by="received_at asc")
	out["owner_events"] = [{**e, "authority_name": people.full_name(e.authority) if e.authority else "", "received": next_steps.when(e.received_at),
		"effective": next_steps.when(e.effective_at)} for e in events]
	issues = frappe.get_all("Support Issue", filters={"module": "Bid Evaluation", "reference_name": doc.name}, fields=["issue_id", "subject", "safe_detail", "status",
		"holder_users_json", "opened_at", "operation"], order_by="opened_at asc")
	out["issues"] = [{**i, "holders": [people.full_name(u) for u in json.loads(i.holder_users_json or "[]")], "opened": next_steps.when(i.opened_at)} for i in issues
		if a["secretary"] or a["ao"] or a["hop"] or a["chair"]]
	delivery = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": doc.name}, ["name", "status", "recipient_user", "delivered_at", "review_state",
		"return_comment", "returned_by", "report_version"], as_dict=True, order_by="creation desc")
	if delivery and (a["report"] or a["chair"]):
		out["delivery"] = {**delivery, "recipient_name": people.full_name(delivery.recipient_user) if delivery.recipient_user else "",
			"delivered": next_steps.when(delivery.delivered_at), "returned_by_name": people.full_name(delivery.returned_by) if delivery.returned_by else "",
			"report_number": frappe.db.get_value("Evaluation Report Version", delivery.report_version, "version_number")}
	if a["report"] or a["bids"]:
		# opening updates and correction notices sit beside the delivered report (the Head's review)
		out["updates"] = [{**e, "detail": json.loads(e.detail_json or "{}"), "received": next_steps.when(e.received_at), "author": people.full_name(e.authority)}
			for e in frappe.get_all("Evaluation Source Event", filters={"evaluation_case": doc.name, "kind": "Opening supplement"}, fields=["name", "source_reference",
				"authority", "detail_json", "received_at", "impact", "impact_reason", "delivered_context", "head_review_state"], order_by="received_at asc")]
		out["notices"] = [{**n, "recorded_by_name": people.full_name(n.recorded_by)} for n in frappe.get_all("Evaluation Correction Notice",
			filters={"evaluation_case": doc.name}, fields=["name", "reason", "correction", "recorded_at", "recorded_by", "head_review_state", "downstream_status"],
			order_by="recorded_at asc")]
	if not a["bids"]:
		return out
	session = discussion.active_session(doc)
	if session:
		row = frappe.db.get_value("Proceeding Session", session, ["session_number", "subject", "actual_start", "started_by"], as_dict=True)
		members = roster.member_users(doc.name)
		present = discussion.present(doc)
		out["session"] = {"id": session, "number": row.session_number, "subject": row.subject, "started": next_steps.when(row.actual_start),
			"started_by": people.full_name(row.started_by), "attendance": _attendance(doc, session), "present": present,
			"missing": [u for u in members if u not in present], "missing_names": [people.full_name(u) for u in members if u not in present]}
	out["clarifications"] = []
	for c in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": doc.name}, fields=["name", "status", "evaluation_bid", "requirement_key", "question",
			"reply_scope", "reply_deadline", "authorised_by", "authorised_at", "sent_at", "notice_state", "replaces", "replaced_by", "withdrawal_reason", "disposition",
			"disposition_result", "disposition_reason", "closed_at", "conclusion"], order_by="creation asc"):
		reply = frappe.db.get_value("Evaluation Clarification Reply", {"clarification": c.name, "state": "Sent"}, ["body", "received_at", "timeliness"], as_dict=True)
		out["clarifications"].append({**c, "bidder": frappe.db.get_value("Evaluation Bid", c.evaluation_bid, "tenderer_name"),
			"authorised_by_name": people.full_name(c.authorised_by), "authorised": next_steps.when(c.authorised_at), "sent": next_steps.when(c.sent_at),
			"deadline": next_steps.when(c.reply_deadline), "closed": next_steps.when(c.closed_at),
			"overdue": clarification.overdue(frappe.get_doc("Evaluation Clarification", c.name)),
			"replace_reason": cstr(frappe.db.get_value("Evaluation Conclusion", c.conclusion, "reason")) if c.replaces else "",
			"reply": {"body": reply.body, "received": next_steps.when(reply.received_at), "timeliness": reply.timeliness} if reply else None})
	plan = diligence.current_plan(doc.name)
	if plan:
		out["verification"] = {"plan": plan.name, "scope": plan.scope, "basis": plan.basis, "status": plan.status, "report_state": plan.report_state,
			"participants": [{"user": u, "name": people.full_name(u)} for u in diligence.participants(plan)], "lead": plan.lead_user,
			"lead_name": people.full_name(plan.lead_user), "observations": [{"user": o.participant_user, "name": people.full_name(o.participant_user),
			"findings": o.findings, "recorded": next_steps.when(o.recorded_at)} for o in diligence.observations(plan)],
			"my_targets": diligence.my_targets(doc, plan, a["user"]), "signatures": _proofs(plan.report_version) if plan.report_version else []}
	out["notes"] = [n for n in notes(doc) if session and n.get("session") == session]
	out["conclusions"] = [{**c, "recorded_by_name": people.full_name(c.recorded_by), "at": next_steps.when(c.recorded_at), "at_time": next_steps.when(c.recorded_at)[-9:-4],
		"question": frappe.db.get_value("Evaluation Clarification", {"conclusion": c.name}, "question") if c.kind == "Clarification" else ""}
		for c in frappe.get_all("Evaluation Conclusion", filters={"evaluation_case": doc.name}, fields=["name", "session", "kind", "result", "reason", "recorded_by",
			"recorded_at", "evaluation_bid", "requirement_key"], order_by="recorded_at asc")]
	version = signing.signing_version(doc)
	if version:
		out["signing"] = {"report": version.name, "version_number": version.version_number, "signatures": [{**s, "signed": next_steps.when(s["signed_at"])}
			for s in signing.signatures(version)]}
	return out


def notes(doc) -> list[dict[str, Any]]:
	"""The discussion notes recorded on this case, in order (their words are
	the RecordDiscussionNote results)."""
	out = []
	for row in frappe.get_all(records.JOURNAL, filters={"evaluation_case": doc.name, "command": "RecordDiscussionNote"}, fields=["result_json", "recorded_at"],
			order_by="recorded_at asc"):
		result = json.loads(row.result_json or "{}")
		out.append({"session": result.get("session"), "subject": result.get("subject", ""), "note": result.get("note", ""), "reason": result.get("reason", ""),
			"recorded_by_name": people.full_name(result.get("recorded_by") or ""), "at": next_steps.when(row.recorded_at)})
	return out


def candidates(*, tender_reference: str, user: str, purpose: str) -> list[dict[str, Any]]:
	"""The people this viewer may name in an appointment form: internal people
	for the committee (AO), procurement officers for the secretary (HoP).
	Eligibility is decided again by the command; this is only the pick list."""
	doc = _case(tender_reference)
	if purpose == "secretary":
		if not people.holds(user, people.HEAD_OF_PROCUREMENT):
			raise frappe.DoesNotExistError("Not found")
		users = sorted(set(people.holders(people.PROCUREMENT_OFFICER)) | {user})
	else:
		if not people.holds(user, people.ACCOUNTING_OFFICER):
			raise frappe.DoesNotExistError("Not found")
		# every staff account, not only responsibility holders (KT-STD-001 v1.13 §8.3)
		users = sorted(frappe.get_all("User", filters={"enabled": 1, "user_type": "System User", "name": ("not in", ("Administrator", "Guest"))}, pluck="name"))
	out = []
	for u in users:
		ok, designation = people.internal(u)
		if not ok:
			continue
		unit = frappe.db.get_value("User Responsibility Assignment", {"user": u, "status": "Enabled", "organisation_unit": ("is", "set")}, "organisation_unit")
		department = cstr(frappe.db.get_value("Organisation Unit", unit, "unit_name")) if unit and frappe.db.exists("DocType", "Organisation Unit") else ""
		out.append({"user": u, "name": people.full_name(u), "designation": designation, "department": department})
	del doc
	return sorted(out, key=lambda r: r["name"])


def _proofs(record_version: str) -> list[dict[str, Any]]:
	row = frappe.get_doc("Proceeding Minutes Version", record_version)
	signed = {(p.target_id, p.member_user): p.recorded_at for p in frappe.get_all("Proceeding Attestation", filters={"minutes_version": record_version,
		"verification_result": "Accepted/Verified"}, fields=["target_id", "member_user", "recorded_at"])}
	out: dict[str, dict[str, Any]] = {}
	for t in row.targets:
		entry = out.setdefault(t.required_member, {"user": t.required_member, "name": people.full_name(t.required_member), "signed": ""})
		if t.target_type.endswith("signature") and (t.target_id, t.required_member) in signed:
			entry["signed"] = next_steps.when(signed[(t.target_id, t.required_member)])
	return list(out.values())


def bid(*, tender_reference: str, bid: str, user: str) -> dict[str, Any]:
	"""One opened bid's requirements, automatic results, evidence and findings (board D04)."""
	doc = _case(tender_reference)
	a = require(doc, user)
	if a["undeclared"]:
		from kentender_procurement.bid_evaluation.services.errors import fail

		fail("EVL_DECLARATION_REQUIRED")
	if not a["bids"] or not frappe.db.exists("Evaluation Bid", {"name": bid, "evaluation_case": doc.name}):
		raise frappe.DoesNotExistError("Not found")
	row = frappe.get_doc("Evaluation Bid", bid)
	run = checks.current_run(doc.name)
	res = aggregate.bid_results(doc.name, run, bid) if run else {"requirements": [], "groups": {}, "responsiveness": ""}
	source = sources.cached_package(doc, row)
	files = {}
	for e in (source.get("body") or {}).get("evidence") or []:
		files.setdefault(e["response_id"], []).extend({"name": f.get("original_filename"), "digest": f.get("file_digest"), "media_type": f.get("media_type")}
			for f in e.get("files") or [])
	requirements = []
	for r in res["requirements"]:
		history = frappe.get_all("Evaluation Finding", filters={"evaluation_case": doc.name, "evaluation_bid": bid, "requirement_key": r["requirement_key"]},
			fields=["name", "kind", "result", "reason", "author", "recorded_at", "status", "evidence_reference"], order_by="recorded_at asc")
		requirements.append({
			"requirement_key": r["requirement_key"], "label": r["label"], "group_id": r["group_id"], "result": r["result"], "automatic": r["automatic"],
			"basis": r["basis"], "reason": r["reason"], "evidence_pending": r["evidence_pending"], "qualified": r["qualified"],
			"checks": [{"field": c.field_key, "kind": c.check_kind, "required": c.required_display, "offered": c.offered_display, "result": c.result,
				"reason": c.reason, "automatic": True} for c in r["checks"]],
			"evidence": [f for c in r["checks"] for f in files.get(c.response_id, [])],
			"history": [{**h, "author_name": people.full_name(h.author), "at": next_steps.when(h.recorded_at)} for h in history],
		})
	return {"evaluation": doc.name, "tender": doc.tender_reference, "bid": bid, "bidder": row.tenderer_name, "submitted_version": row.submission_version,
		"groups": res["groups"], "responsiveness": res["responsiveness"], "requirements": requirements, "state": doc.state, "record_version": doc.record_version}


def evidence(*, tender_reference: str, bid: str, digest: str, user: str) -> dict[str, Any]:
	"""ReadEvaluationEvidence: one submitted file of an opened bid, by its digest; never a file URL."""
	doc = _case(tender_reference)
	a = require(doc, user)
	if not a["bids"] or not frappe.db.exists("Evaluation Bid", {"name": bid, "evaluation_case": doc.name}):
		raise frappe.DoesNotExistError("Not found")
	source = sources.cached_package(doc, frappe.get_doc("Evaluation Bid", bid))
	for e in (source.get("body") or {}).get("evidence") or []:
		for f in e.get("files") or []:
			if f.get("file_digest") == digest:
				return {"filename": f.get("original_filename"), "media_type": f.get("media_type"), "content": base64.b64decode(f.get("content_base64") or "")}
	raise frappe.DoesNotExistError("Not found")


def report_view(*, tender_reference: str, user: str, version: str = "") -> dict[str, Any]:
	"""ReadEvaluationReport: the exact frozen version asked for, else the
	version being signed or the latest delivered one, else (for a reader of
	bids, while reviewing) the live draft generated from the record."""
	doc = _case(tender_reference)
	a = require(doc, user)
	if not a["report"]:
		raise frappe.DoesNotExistError("Not found")
	versions = frappe.get_all("Evaluation Report Version", filters={"evaluation_case": doc.name}, fields=["name", "version_number", "state", "frozen_at",
		"supersession_kind", "supersession_reason"], order_by="version_number asc")
	frozen = [v for v in versions if v.state != "Draft"]
	if version:
		chosen = next((v for v in frozen if v.name == version), None)
		if chosen is None:
			raise frappe.DoesNotExistError("Not found")
	else:
		chosen = next((v for v in reversed(frozen) if v.state == "Signing"), None) or (
			next((v for v in reversed(frozen) if v.state in ("Delivered", "Returned")), None) if doc.state == "Report sent" or not a["bids"] else None)
	if chosen is not None:
		row = frappe.get_doc("Evaluation Report Version", chosen.name)
		content, live = json.loads(row.content_json or "{}"), False
	elif a["bids"]:
		draft = frappe.db.get_value("Evaluation Report Version", {"evaluation_case": doc.name, "state": "Draft"}, "name")
		row = frappe.get_doc("Evaluation Report Version", draft) if draft else None
		content, live = {**report.build(doc), "narrative": cstr(row.narrative) if row else ""}, True
	else:
		raise frappe.DoesNotExistError("Not found")
	extra: dict[str, Any] = {}
	if live and a["secretary"]:
		ready = signing.readiness(doc)
		extra["readiness"] = [{"label": i.get("item", ""), "holder_name": i.get("holder_name", ""), "bid": frappe.db.get_value("Evaluation Bid",
			{"evaluation_case": doc.name, "tenderer_name": i.get("bidder")}, "name") if i.get("bidder") else ""}
			for r in (ready.reasons if ready else []) for i in (r.get("detail") or {}).get("issues") or []]
	if doc.state == "Report sent":
		from kentender_procurement.bid_evaluation.services import correction

		status = correction.decision_status(doc)
		extra.update(downstream=status.get("status"), downstream_checked=next_steps.when(status.get("checked_at")),
			downstream_label=f"{status.get('status')} {next_steps.when(status.get('decided_at'))}".strip() if status.get("decided_at") else status.get("status"))
	return {"evaluation": doc.name, "tender": doc.tender_reference, "state": doc.state, "report": row.name if row else "",
		"version_number": row.version_number if row else len(versions) + 1, "report_state": row.state if row else "Draft",
		# before its first save the draft does not exist yet; it is created at version 1
		"report_record_version": row.record_version if row else 1, "live": live, "content": content, **extra,
		"signatures": [{**s, "signed": next_steps.when(s["signed_at"])} for s in signing.signatures(row)] if row is not None and not live else [],
		"history": [{**v, "frozen": next_steps.when(v.frozen_at)} for v in frozen]}


def committee_record(*, tender_reference: str, user: str) -> dict[str, Any]:
	"""The Committee record: roster, sessions and attendance, correspondence, disagreement, history."""
	doc = _case(tender_reference)
	a = require(doc, user)
	out = {"evaluation": doc.name, "tender": doc.tender_reference, "committee": committee(doc),
		"appointments": report._committee(doc)["history"],
		"declarations": [{"member": people.full_name(d.member_user), "choice": d.choice, "at": next_steps.when(d.declared_at), "status": d.status,
			"description": cstr(d.conflict_description) if a["ao"] or d.member_user == user else ""}
			for d in frappe.get_all("Evaluation Declaration", filters={"evaluation_case": doc.name}, fields=["member_user", "choice", "declared_at", "status",
				"conflict_description"],
				order_by="declared_at asc")]}
	if a["bids"]:
		built = report.build(doc)
		out.update(built["clarifications_and_record"])
	return out


def list_work(*, user: str, query: str = "", state: str = "") -> dict[str, Any]:
	"""ListEvaluationWork (board D01): the viewer's tasks, and the register of
	evaluations they may read, searchable and filterable locally."""
	from kentender_procurement.bid_evaluation.services import my_work_provider

	tasks = my_work_provider.my_work_rows(user)["assigned"]
	register = []
	for name in frappe.get_all(records.CASE, pluck="name", order_by="creation desc"):
		doc = frappe.get_doc(records.CASE, name)
		if not access(doc, user)["read"] or people.technical(user):
			continue
		register.append({"tender": doc.tender_reference, "title": doc.tender_title, "state": doc.state})
	matched = [r for r in register if (not state or r["state"] == state) and (not query or query.lower() in (r["tender"] + " " + r["title"]).lower())]
	# S-FORBIDDEN: no evaluation responsibility, appointment or readable record
	offices = any(people.holds(user, r) for r in (people.ACCOUNTING_OFFICER, people.HEAD_OF_PROCUREMENT, people.AUDITOR))
	forbidden = not (offices or register or tasks or people.technical(user))
	return {"tasks": tasks, "register": matched, "total": len(register), "states": list(WORK_STATES), "forbidden": forbidden}


def own_clarification(*, tender_reference: str, clarification: str, user: str, organisation: str = "") -> dict[str, Any]:
	"""ReadOwnClarification: the supplier's own request and reply only (allowlist)."""
	from kentender_procurement.bid_evaluation.services import clarification as clar

	name = frappe.db.get_value(records.CASE, {"tender_reference": tender_reference}, "tender")
	if not name:
		raise frappe.DoesNotExistError("Not found")
	request, org = clar._supplier_request(name, clarification, user, organisation)
	reply = frappe.db.get_value(clar.REPLY, {"clarification": request.name}, ["state", "body", "attachments_json", "saved_at", "received_at", "timeliness"],
		as_dict=True)
	replacement = frappe.db.get_value(clar.REQUEST, {"replaces": request.name}, ["name", "question", "reply_deadline", "sent_at", "status"], as_dict=True)
	doc = frappe.get_doc(records.CASE, request.evaluation_case)
	return {
		"tender": doc.tender_reference, "title": doc.tender_title, "organisation": org,
		"organisation_name": frappe.db.get_value("Evaluation Bid", request.evaluation_bid, "tenderer_name"), "clarification": request.name, "question": request.question,
		"reply_scope": request.reply_scope, "reply_deadline": next_steps.when(request.reply_deadline), "sent": next_steps.when(request.sent_at),
		"status": request.status, "closed": next_steps.when(request.closed_at), "closure_reason": cstr(request.closure_reason),
		"withdrawal_reason": cstr(request.withdrawal_reason) if request.status == "Withdrawn" else "", "overdue": clar.overdue(request),
		"reply": {"state": reply.state, "body": reply.body, "attachments": [{"filename": f.get("filename"), "size": f.get("size")} for f in json.loads(reply.attachments_json or "[]")], "received": next_steps.when(reply.received_at),
			"timeliness": reply.timeliness} if reply else None,
		"replacement": {"clarification": replacement.name, "question": replacement.question, "reply_deadline": next_steps.when(replacement.reply_deadline),
			"sent": next_steps.when(replacement.sent_at)} if replacement and replacement.status != "Authorised" else None,
	}
