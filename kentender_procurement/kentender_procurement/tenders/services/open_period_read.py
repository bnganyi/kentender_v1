# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §10.11–10.13 reads: one addendum (draft / HoPF issue /
publication confirmation / issued / material-change blocked and its
cancellation review, with the affected-reference catalogue and the deadline
rule), one supplier clarification, and the cancellation screen (grounds,
consequences preview, recommendation, cancelled detail). Reads create
nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import addenda, cancellation, channel_confirmation, draft_commands, guidance, publication_read, read, serializer
from kentender_procurement.tenders.services import tender_authorization as authz


def _load(tender: str, user: str | None):
	actor = authz.actor(user)
	root = frappe.get_doc("Tender", draft_commands.resolve_tender_name(tender))
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	if mode == "department":
		authz.not_found()
	return actor, root, read.actor_roles(actor)


def _guidance(root, actor: str, roles: dict[str, bool], context: str, subject=None) -> dict[str, Any]:
	"""§10.17 — the answer for this screen's subject (an addendum, a
	clarification) or the cancellation screen."""
	return guidance.guidance(root, actor=actor, roles=roles, mode="technical" if roles["technical"] else "site", context=context, subject=subject.as_dict() if subject is not None else None)


def get_tender_addendum(*, tender: str, addendum: str = "", user: str | None = None) -> dict[str, Any]:
	actor, root, roles = _load(tender, user)
	version = frappe.get_doc("Tender Version", root.approved_version or root.current_version)
	state = serializer.officer_state(version)
	doc = None
	if addendum:
		if cstr(frappe.db.get_value("Tender Addendum", addendum, "tender")) != root.name:
			authz.not_found()
		doc = frappe.get_doc("Tender Addendum", addendum)
	references = addenda.affected_references(root)
	catalogue = {r["key"]: r for r in references}
	reference = catalogue.get(cstr(doc.affected_reference_key)) if doc else None
	material = bool(reference and reference["material"])
	rule = addenda.deadline_rule(root, change_class=cstr(doc.change_class) if doc else "")
	review_status = cstr(doc.cancellation_review_status) if doc else ""
	drafter = roles["officer"] or roles["hopf"]
	open_tender = root.overall_status == "Published — open"
	editable = bool(doc) and doc.status == "Draft" and drafter and open_tender and not review_status
	actions: list[str] = []
	if editable:
		actions += ["save_addendum_draft", "submit_addendum_for_issue"]
	if doc and doc.status == "Awaiting issue" and roles["hopf"]:
		actions += ["return_addendum_for_correction", "issue_addendum"]
	if doc and doc.status == "Awaiting publication confirmation" and roles["hopf"]:
		actions.append("confirm_addendum_channel")
	if material:
		actions = [a for a in actions if a not in ("submit_addendum_for_issue", "issue_addendum")]
		if doc and doc.status == "Draft" and drafter and open_tender and not review_status:
			actions.append("request_cancellation_review")
		if doc and review_status == "Requested" and roles["ao"]:
			actions.append("close_cancellation_review")
	if doc and doc.status == "Draft" and drafter and open_tender and review_status != "Requested":
		actions.append("discard_addendum_draft")
	if material and drafter:
		actions.append("view_cancellation_requirements")
	channels = publication_read.confirmation_rows(subject_type="Addendum", subject_id=doc.name) if doc and doc.status in ("Awaiting publication confirmation", "Issued") else []
	import json

	original_channels = json.loads(frappe.db.get_value("Tender Publication", root.publication, "required_channels_json") or "[]") if root.publication else []
	# §10.11: "Confirm addendum publication — {channel}"
	for row in channels:
		row["dialog_title"] = f"Confirm addendum publication — {row['channel_label']}"
	return {
		"outcome": "OK", "mode": "technical" if roles["technical"] else "site", "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "overall_status": cstr(root.overall_status), "record_version": int(root.record_version or 0), "current_deadline_label": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else ""},
		"addendum": {
			"name": doc.name, "addendum_number": int(doc.addendum_number), "addendum_reference": cstr(doc.addendum_reference), "status": doc.status, "change_class": cstr(doc.change_class), "affected_area": cstr(doc.affected_area),
			"affected_reference_key": cstr(doc.affected_reference_key), "affected_reference": cstr(doc.affected_reference), "previous_value": cstr(doc.previous_value), "revised_value": cstr(doc.revised_value), "reason": cstr(doc.reason),
			"materiality_statement": cstr(doc.materiality_statement), "deadline_extension_required": bool(doc.deadline_extension_required), "revised_submission_deadline": cstr(doc.revised_submission_deadline),
			"revised_submission_deadline_label": serializer.fmt_datetime_short(doc.revised_submission_deadline) if doc.revised_submission_deadline else "", "addendum_digest": cstr(doc.addendum_digest),
			"drafted_by_name": read._full_name(doc.drafted_by), "submitted_by_name": read._full_name(doc.submitted_by), "issue_decided_by_name": read._full_name(doc.issue_decided_by),
			"issue_decided_at_label": serializer.fmt_datetime_short(doc.issue_decided_at) if doc.issue_decided_at else "", "issued_at_label": serializer.fmt_datetime_short(doc.issued_at) if doc.issued_at else "",
			"confirmation_completed_at_label": _completed_label(doc), "return_reason": cstr(doc.return_reason), "predecessor_addendum": cstr(doc.predecessor_addendum),
			"cancellation_review_status": review_status, "cancellation_review_reason": cstr(doc.cancellation_review_reason), "cancellation_review_closed_reason": cstr(doc.cancellation_review_closed_reason),
			"record_version": int(doc.record_version or 0),
		} if doc else None,
		"references": references, "change_classes": list(addenda.CHANGE_CLASSES), "affected_areas": list(addenda.AFFECTED_AREAS),
		"material": material, "material_text": addenda.MATERIAL_TEXT if material else "", "deadline_rule": rule,
		"channels": channels, "original_channels": original_channels,
		"attestations": {c["channel"]: channel_confirmation.attestation_text(subject_type=channel_confirmation.SUBJECT_ADDENDUM, channel_label=c["label"]) for c in original_channels},
		"ready_to_issue": bool(doc and doc.status == "Awaiting issue" and not material), "editable": editable, "allowed_actions": actions,
		"task": _task_for(root, "HOPF addendum issue", doc.name) if doc else None,
		"guidance": _guidance(root, actor, roles, "addendum", doc),
	}


def _completed_label(doc) -> str:
	"""§10.11 Issued: "confirmation completed" = the final attestation time."""
	if doc.status != "Issued":
		return ""
	rows = frappe.get_all("Tender Channel Confirmation", filters={"subject_type": "Addendum", "subject_id": doc.name, "status": "Confirmed"}, pluck="attested_at")
	latest = max((r for r in rows if r), default=None)
	return serializer.fmt_datetime_short(latest) if latest else ""


def _task_for(root, task_type: str, subject_id: str) -> dict[str, Any] | None:
	name = frappe.db.get_value("Tender Task", {"tender": root.name, "task_type": task_type, "subject_id": subject_id, "status": "Open"}, ["name", "task_token"], as_dict=True)
	return {"name": name.name, "task_token": name.task_token} if name else None


def get_tender_clarification(*, tender: str, clarification: str, user: str | None = None) -> dict[str, Any]:
	"""§10.12 — one supplier clarification. The candidate's identity and
	notice destinations are protected: authorised procurement, audit and
	technical readers only (§12.3(7)); a broadcast never names the asker."""
	from kentender_procurement.tenders.services import candidate_gateway, candidate_notices

	actor, root, roles = _load(tender, user)
	if cstr(frappe.db.get_value("Tender Clarification", clarification, "tender")) != root.name:
		authz.not_found()
	doc = frappe.get_doc("Tender Clarification", clarification)
	protected = roles["officer"] or roles["hopf"] or roles["auditor"] or roles["technical"]
	issued = frappe.get_all("Tender Addendum", filters={"tender": root.name, "status": "Issued"}, fields=["name", "addendum_reference"], order_by="addendum_number asc")
	notices = candidate_notices.rows_for(doc.name, notice_type="Clarification response", protected=protected)
	actions: list[str] = []
	required_effective = bool(doc.required_addendum) and frappe.db.get_value("Tender Addendum", doc.required_addendum, "status") == "Issued"
	if root.overall_status == "Published — open" and (roles["officer"] or roles["hopf"]):
		if doc.status == "Awaiting response":
			actions += ["send_response", "prepare_addendum"]
		elif doc.status == "Awaiting addendum":
			# §10.12: the kept answer is sent only once its addendum is Issued
			actions += ["send_response"] if required_effective else ["prepare_addendum"]
		if any(n["status"] == "Failed" for n in notices):
			actions.append("retry_notice")
	return {
		"outcome": "OK", "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "overall_status": cstr(root.overall_status), "record_version": int(root.record_version or 0), "clarification_deadline_label": serializer.fmt_datetime_short(root.clarification_deadline) if root.clarification_deadline else ""},
		"clarification": {
			"name": doc.name, "candidate_label": "Registered Tender candidate",
			"candidate_name": candidate_gateway.candidate_name(tender=root.name, candidate_registration_id=doc.candidate_registration_id) if protected else "",
			"question": cstr(doc.question), "received_at_label": serializer.fmt_datetime_short(doc.received_at), "status": doc.status,
			"related_addendum": cstr(doc.related_addendum), "related_addendum_reference": cstr(frappe.db.get_value("Tender Addendum", doc.related_addendum, "addendum_reference")) if doc.related_addendum else "None",
			"response": cstr(doc.response), "response_audience": cstr(doc.response_audience), "affects_published_tender": bool(doc.affects_published_tender),
			"required_addendum": cstr(doc.required_addendum), "required_addendum_reference": cstr(frappe.db.get_value("Tender Addendum", doc.required_addendum, "addendum_reference")) if doc.required_addendum else "",
			"responded_by_name": read._full_name(doc.responded_by), "responded_at_label": serializer.fmt_datetime_short(doc.responded_at) if doc.responded_at else "",
			"record_version": int(doc.record_version or 0),
		},
		"issued_addenda": [{"name": a.name, "addendum_reference": a.addendum_reference} for a in issued],
		"notices": notices, "notice_summary": candidate_notices.delivery_summary(doc.name, notice_type="Clarification response"),
		"audiences": [{"value": "Asker only", "label": "Only the supplier who asked"}, {"value": "All registered candidates", "label": "All registered candidates"}],
		"allowed_actions": actions,
		"required_addendum_effective": required_effective,
		"guidance": _guidance(root, actor, roles, "clarification", doc),
		"guidance_if_published_change": guidance.clarification_change_guidance(root, doc.as_dict(), actor=actor, roles=roles) if not roles["technical"] else None,
	}


def _open_review(root) -> dict[str, Any] | None:
	"""§10.13 TPR-DES-12-REQUEST — the open cancellation-review request: who
	asked and the proposed change no addendum may make (no request time or
	ground is invented)."""
	from kentender_procurement.tenders.services import handoffs

	task = frappe.db.get_value("Tender Task", {"tender": root.name, "task_type": handoffs.CANCELLATION_REVIEW, "status": "Open"}, ["subject_id", "sender"], as_dict=True)
	if not task:
		return None
	doc = frappe.db.get_value("Tender Addendum", task.subject_id, ["name", "addendum_reference", "affected_reference_key", "revised_value", "reason", "cancellation_review_reason"], as_dict=True)
	if not doc:
		return None
	reference = {r["key"]: r for r in addenda.affected_references(root)}.get(cstr(doc.affected_reference_key)) or {}
	# the responsibility the requester acted under, as recorded with the request
	role = cstr(frappe.db.get_value("Tender Decision", {"tender": root.name, "decision": "Request cancellation review", "subject_id": doc.name}, "business_role", order_by="decided_at desc")) or "Procurement Officer"
	return {
		"addendum": doc.name, "addendum_reference": cstr(doc.addendum_reference), "requested_by_name": read._full_name(task.sender), "requested_by_role": role,
		"field": cstr(reference.get("label") or doc.affected_reference_key), "current": cstr(reference.get("value")), "proposed": cstr(doc.revised_value), "reason": cstr(doc.reason),
		"request_reason": cstr(doc.cancellation_review_reason),
	}


def _compliance_rows(cancellation_summary: dict[str, Any]) -> list[dict[str, Any]]:
	"""§10.13 Cancelled detail — the notice channels as one "Cancellation
	notices" obligation (with its count), the candidate notices and the PPRA
	report; each row names its next outstanding obligation for its action."""
	obligations = cancellation_summary.get("obligations") or []

	def status_of(rows) -> str:
		if rows and all(o["status"] == "Recorded" for o in rows):
			return "Recorded"
		return "Overdue" if any(o["status"] == "Overdue" for o in rows) else "Outstanding"

	out = []
	groups = (
		("Cancellation notices", [o for o in obligations if o["obligation_type"] == "Notice channel"], "record_cancellation_notice_evidence", "Record cancellation notice evidence"),
		("Candidate notices", [o for o in obligations if o["obligation_type"] == "Candidate notice"], "", ""),
		("PPRA report", [o for o in obligations if o["obligation_type"] == "PPRA report"], "record_ppra_report_evidence", "Record PPRA report evidence"),
	)
	for label, rows, action, action_label in groups:
		if not rows:
			continue
		status = status_of(rows)
		outstanding = next((o for o in rows if o["status"] != "Recorded"), None)
		recorded = sum(1 for o in rows if o["status"] == "Recorded")
		out.append({
			"key": action or "candidate_notices", "label": label, "due_by": rows[0]["due_by"], "status": status,
			"detail": f"{recorded} of {len(rows)} recorded" if len(rows) > 1 else (rows[0]["evidence_reference"] or ""),
			"action": action if outstanding and action else "", "action_label": action_label, "obligation_id": outstanding["obligation_id"] if outstanding else "",
		})
	return out


def get_tender_cancellation(*, tender: str, user: str | None = None) -> dict[str, Any]:
	actor, root, roles = _load(tender, user)
	version = frappe.get_doc("Tender Version", root.approved_version or root.current_version)
	state = serializer.officer_state(version)
	summary = publication_read.open_period_summary(root, actor=actor, roles=roles) or {}
	existing = summary.get("cancellation")
	if existing and root.cancellation:
		doc = frappe.get_doc("Tender Cancellation", root.cancellation)
		cancellation.refresh_obligation_statuses(doc)
		summary = publication_read.open_period_summary(root, actor=actor, roles=roles) or {}
		existing = summary.get("cancellation")
	recommendation_name = cancellation.latest_recommendation(root)
	recommendation = None
	if recommendation_name:
		row = frappe.db.get_value("Tender Decision", recommendation_name, ["actor", "decided_at", "reason", "affected_task"], as_dict=True)
		recommendation = {"by_name": read._full_name(row.actor), "at_label": serializer.fmt_datetime_short(row.decided_at), "text": cstr(row.reason).split(": ", 1)[-1], "ground": cstr(row.affected_task)}
	import json

	channels = json.loads(frappe.db.get_value("Tender Publication", root.publication, "required_channels_json") or "[]") if root.publication else []
	preview = cancellation.preview_obligations(root) if root.overall_status == "Published — open" else []
	review = _open_review(root)
	actions = [a for a in read.allowed_actions(root, version, actor, roles) if a in ("cancel_tender", "recommend_cancellation", "record_cancellation_evidence")]
	if review and roles["ao"] and not roles["technical"]:
		actions.append("close_cancellation_review")
	return {
		"outcome": "OK", "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "overall_status": cstr(root.overall_status), "badge": read.badge_for(root, version, roles), "record_version": int(root.record_version or 0), "published_at_label": serializer.fmt_datetime_short(root.published_at) if root.published_at else "", "submission_deadline_label": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else ""},
		"summary": {"purchase": cstr(state.get("tender_title") or root.requirement_title), "tender": root.tender_reference, "published_at": serializer.fmt_datetime_short(root.published_at) if root.published_at else "", "submission_deadline": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else "", "required_channels": ", ".join(c["label"] for c in channels), "channel_count": len(channels)},
		"grounds": cancellation.grounds_for_client(), "grounds_source": cancellation.GROUNDS_SOURCE,
		"recommendation": recommendation,
		"consequences": {"closes_immediately": True, "notice_channels": [c["label"] for c in channels], "ppra_report_due_by": next((serializer.fmt_date_short(o["due_by"]) for o in preview if o["obligation_type"] == "PPRA report"), ""), "candidate_notice_due_by": next((serializer.fmt_date_short(o["due_by"]) for o in preview if o["obligation_type"] == "Candidate notice"), ""), "replacement_text": "A replacement procurement requires new governance."},
		"cancellation": existing,
		"notice_channels": publication_read.confirmation_rows(subject_type="Cancellation notice", subject_id=root.cancellation) if root.cancellation else [],
		"allowed_actions": actions,
		"review": review,
		"compliance": _compliance_rows(existing) if existing else [],
		"warning_text": "Cancellation is final for this Tender. It does not restore the Requisition or create a replacement Tender.",
		"guidance": _guidance(root, actor, roles, "cancellation"),
	}
