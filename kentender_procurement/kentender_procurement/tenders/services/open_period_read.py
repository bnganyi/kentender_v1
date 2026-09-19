# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §10.11–10.13 reads: one addendum (draft / HoPF issue /
material-change blocked, with the affected-reference catalogue and the
deadline rule), one inquiry, and the cancellation screen (grounds,
consequences preview, recommendation, cancelled detail). Reads create
nothing."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import addenda, cancellation, channel_confirmation, draft_commands, publication_read, read, serializer
from kentender_procurement.tenders.services import tender_authorization as authz


def _load(tender: str, user: str | None):
	actor = authz.actor(user)
	root = frappe.get_doc("Tender", draft_commands.resolve_tender_name(tender))
	mode = authz.reader_mode(actor, contributing_org_units=authz.contributing_units_of(root))
	if mode == "department":
		authz.not_found()
	return actor, root, read.actor_roles(actor)


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
	editable = bool(doc) and doc.status in ("Draft", "Returned") and (roles["officer"] or roles["hopf"]) and root.overall_status == "Published — open"
	actions: list[str] = []
	if editable:
		actions += ["save_addendum_draft", "submit_addendum_for_issue"]
	if doc and doc.status == "Awaiting issue" and roles["hopf"]:
		actions += ["return_addendum_for_correction", "issue_addendum"]
	if doc and doc.status == "Awaiting publication confirmation" and roles["hopf"]:
		actions.append("confirm_addendum_channel")
	if material:
		actions = [a for a in actions if a not in ("submit_addendum_for_issue", "issue_addendum")]
	channels = publication_read.confirmation_rows(subject_type="Addendum", subject_id=doc.name) if doc and doc.status in ("Awaiting publication confirmation", "Issued") else []
	import json

	original_channels = json.loads(frappe.db.get_value("Tender Publication", root.publication, "required_channels_json") or "[]") if root.publication else []
	return {
		"outcome": "OK", "mode": "technical" if roles["technical"] else "site", "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "overall_status": cstr(root.overall_status), "record_version": int(root.record_version or 0), "current_deadline_label": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else ""},
		"addendum": {
			"name": doc.name, "addendum_number": int(doc.addendum_number), "addendum_reference": cstr(doc.addendum_reference), "status": doc.status, "change_class": cstr(doc.change_class), "affected_area": cstr(doc.affected_area),
			"affected_reference_key": cstr(doc.affected_reference_key), "affected_reference": cstr(doc.affected_reference), "previous_value": cstr(doc.previous_value), "revised_value": cstr(doc.revised_value), "reason": cstr(doc.reason),
			"materiality_statement": cstr(doc.materiality_statement), "deadline_extension_required": bool(doc.deadline_extension_required), "revised_submission_deadline": cstr(doc.revised_submission_deadline),
			"revised_submission_deadline_label": serializer.fmt_datetime_short(doc.revised_submission_deadline) if doc.revised_submission_deadline else "", "addendum_digest": cstr(doc.addendum_digest),
			"drafted_by_name": read._full_name(doc.drafted_by), "submitted_by_name": read._full_name(doc.submitted_by), "issued_by_name": read._full_name(doc.issued_by), "issued_at_label": serializer.fmt_datetime_short(doc.issued_at) if doc.issued_at else "",
			"effective_at_label": serializer.fmt_datetime_short(doc.effective_at) if doc.effective_at else "", "return_reason": cstr(doc.return_reason), "record_version": int(doc.record_version or 0),
		} if doc else None,
		"references": references, "change_classes": list(addenda.CHANGE_CLASSES), "affected_areas": list(addenda.AFFECTED_AREAS),
		"material": material, "material_text": addenda.MATERIAL_TEXT if material else "", "deadline_rule": rule,
		"channels": channels, "original_channels": original_channels,
		"attestations": {c["channel"]: channel_confirmation.attestation_text(subject_type=channel_confirmation.SUBJECT_ADDENDUM, channel_label=c["label"]) for c in original_channels},
		"ready_to_issue": bool(doc and doc.status == "Awaiting issue" and not material), "editable": editable, "allowed_actions": actions,
		"task": _task_for(root, "HOPF addendum issue", doc.name) if doc else None,
	}


def _task_for(root, task_type: str, subject_id: str) -> dict[str, Any] | None:
	name = frappe.db.get_value("Tender Task", {"tender": root.name, "task_type": task_type, "subject_id": subject_id, "status": "Open"}, ["name", "task_token"], as_dict=True)
	return {"name": name.name, "task_token": name.task_token} if name else None


def get_addendum_inquiry(*, tender: str, inquiry: str, user: str | None = None) -> dict[str, Any]:
	actor, root, roles = _load(tender, user)
	if cstr(frappe.db.get_value("Tender Addendum Inquiry", inquiry, "tender")) != root.name:
		authz.not_found()
	doc = frappe.get_doc("Tender Addendum Inquiry", inquiry)
	oversight = roles["auditor"] or roles["technical"]
	return {
		"outcome": "OK", "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "overall_status": cstr(root.overall_status), "record_version": int(root.record_version or 0)},
		"inquiry": {
			"name": doc.name, "addendum": cstr(doc.addendum), "addendum_reference": cstr(frappe.db.get_value("Tender Addendum", doc.addendum, "addendum_reference")), "candidate_label": "Verified supplier account",
			"candidate_identity": cstr(doc.candidate_identity) if oversight else "", "question": cstr(doc.question), "received_at_label": serializer.fmt_datetime_short(doc.received_at), "status": doc.status,
			"response": cstr(doc.response), "affects_requirements": bool(doc.affects_requirements), "responded_by_name": read._full_name(doc.responded_by), "responded_at_label": serializer.fmt_datetime_short(doc.responded_at) if doc.responded_at else "",
			"broadcast_status": cstr(doc.broadcast_status), "broadcast_digest": cstr(doc.broadcast_digest), "record_version": int(doc.record_version or 0),
		},
		"effect_texts": {"no": "The response will be sent to the candidate and recorded.", "yes": "The response will be sent to every registered candidate without identifying who asked."},
		"allowed_actions": ["send_response"] if doc.status == "Awaiting response" and (roles["officer"] or roles["hopf"]) and root.overall_status == "Published — open" else [],
		"late_text": "The inquiry deadline has passed." if doc.status == "Late" else "",
	}


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
	return {
		"outcome": "OK", "roles": roles,
		"tender": {"name": root.name, "tender_reference": root.tender_reference, "title": cstr(state.get("tender_title") or root.requirement_title), "overall_status": cstr(root.overall_status), "badge": read.badge_for(root, version, roles), "record_version": int(root.record_version or 0), "published_at_label": serializer.fmt_datetime_short(root.published_at) if root.published_at else "", "submission_deadline_label": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else ""},
		"summary": {"purchase": cstr(root.requirement_title), "tender": root.tender_reference, "published_at": serializer.fmt_datetime_short(root.published_at) if root.published_at else "", "submission_deadline": serializer.fmt_datetime_short(root.submission_deadline) if root.submission_deadline else "", "required_channels": ", ".join(c["label"] for c in channels), "channel_count": len(channels)},
		"grounds": cancellation.grounds_for_client(), "grounds_source": cancellation.GROUNDS_SOURCE,
		"recommendation": recommendation,
		"consequences": {"closes_immediately": True, "notice_channels": [c["label"] for c in channels], "ppra_report_due_by": next((serializer.fmt_date_short(o["due_by"]) for o in preview if o["obligation_type"] == "PPRA report"), ""), "candidate_notice_due_by": next((serializer.fmt_date_short(o["due_by"]) for o in preview if o["obligation_type"] == "Candidate notice"), ""), "replacement_text": "A replacement procurement requires new governance."},
		"cancellation": existing,
		"notice_channels": publication_read.confirmation_rows(subject_type="Cancellation notice", subject_id=root.cancellation) if root.cancellation else [],
		"allowed_actions": [a for a in read.allowed_actions(root, version, actor, roles) if a in ("cancel_tender", "recommend_cancellation", "record_cancellation_evidence")],
		"warning_text": "Cancellation is final for this Tender. It does not restore the Requisition or create a replacement Tender.",
	}
