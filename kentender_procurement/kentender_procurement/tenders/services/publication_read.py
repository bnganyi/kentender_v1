# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.1 `GetTenderPublication` projections used by
`GetTender` (Phase 5 fills the publication commands; the read shape is
declared here so the record read is complete from Phase 4). Reads create
nothing and never claim a channel is confirmed without its record."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import serializer


def _full_name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user) if user else ""


def confirmation_rows(*, subject_type: str, subject_id: str) -> list[dict[str, Any]]:
	rows = frappe.get_all(
		"Tender Channel Confirmation", filters={"subject_type": subject_type, "subject_id": subject_id},
		fields=["name", "channel", "channel_label", "confirmation_mode", "status", "available_at", "evidence_reference", "public_url", "url_not_applicable_reason", "evidence_file", "evidence_digest", "evidence_check_result", "evidence_notes", "attestation_text", "attested_by", "attested_at", "subject_digest", "record_version"],
		order_by="creation asc", limit_page_length=0,
	)
	for row in rows:
		row["available_at_label"] = serializer.fmt_datetime_short(row["available_at"]) if row["available_at"] else ""
		row["attested_at_label"] = serializer.fmt_datetime_short(row["attested_at"]) if row["attested_at"] else ""
		row["attested_by_name"] = _full_name(row["attested_by"])
		file_row = frappe.db.get_value("File", row["evidence_file"], ["file_name", "file_url", "file_size"], as_dict=True) if row["evidence_file"] else None
		row["evidence_file_name"] = file_row.file_name if file_row else ""
		row["evidence_file_url"] = file_row.file_url if file_row else ""
		row["how"] = "HOPF confirmation with evidence"
		row["result_label"] = row["status"] if row["status"] == "Confirmed" else ("Awaiting confirmation" if row["status"] == "Awaiting confirmation" else row["status"])
	return rows


def publication_summary(root, *, actor: str, roles: dict[str, bool]) -> dict[str, Any] | None:
	if not root.publication or not frappe.db.exists("Tender Publication", root.publication):
		return None
	pub = frappe.get_doc("Tender Publication", root.publication)
	channels = confirmation_rows(subject_type="Publication", subject_id=pub.name)
	confirmed = [c for c in channels if c["status"] == "Confirmed"]
	import json

	return {
		"name": pub.name, "publication_status": pub.publication_status, "authorised_by": cstr(pub.authorised_by), "authorised_by_name": _full_name(pub.authorised_by),
		"authorised_at": cstr(pub.authorised_at), "authorised_at_label": serializer.fmt_datetime_short(pub.authorised_at) if pub.authorised_at else "",
		"rule_snapshot_id": cstr(pub.rule_snapshot_id), "rule_snapshot": json.loads(pub.rule_snapshot_json or "{}"), "threshold_snapshot": json.loads(pub.threshold_snapshot_json or "{}"),
		"required_channels": json.loads(pub.required_channels_json or "[]"), "minimum_preparation_days": int(pub.minimum_preparation_days or 0),
		"package_digest": cstr(pub.package_digest), "published_at": cstr(pub.published_at), "published_at_label": serializer.fmt_datetime_short(pub.published_at) if pub.published_at else "",
		"publication_digest": cstr(pub.publication_digest), "withdrawn_by_name": _full_name(pub.withdrawn_by), "withdrawn_at_label": serializer.fmt_datetime_short(pub.withdrawn_at) if pub.withdrawn_at else "", "withdrawal_reason": cstr(pub.withdrawal_reason),
		"channels": channels, "confirmed_count": len(confirmed), "required_count": len(channels),
		"progress_text": f"{len(confirmed)} of {len(channels)} required channels confirmed", "record_version": int(pub.record_version or 0),
	}


def open_period_summary(root, *, actor: str, roles: dict[str, bool]) -> dict[str, Any] | None:
	if not root.publication:
		return None
	addenda = frappe.get_all("Tender Addendum", filters={"tender": root.name}, fields=["name", "addendum_number", "addendum_reference", "status", "change_class", "affected_area", "affected_reference", "previous_value", "revised_value", "reason", "materiality_statement", "deadline_extension_required", "revised_submission_deadline", "issued_by", "issued_at", "effective_at", "drafted_by", "drafted_at", "record_version"], order_by="addendum_number asc", limit_page_length=0)
	for row in addenda:
		row["issued_at_label"] = serializer.fmt_datetime_short(row["issued_at"]) if row["issued_at"] else ""
		row["effective_at_label"] = serializer.fmt_datetime_short(row["effective_at"]) if row["effective_at"] else ""
		row["revised_submission_deadline_label"] = serializer.fmt_datetime_short(row["revised_submission_deadline"]) if row["revised_submission_deadline"] else ""
		row["issued_by_name"] = _full_name(row["issued_by"])
		row["change_summary"] = _change_summary(row)
		row["channels"] = confirmation_rows(subject_type="Addendum", subject_id=row["name"]) if row["status"] in ("Awaiting publication confirmation", "Issued") else []
	inquiries = frappe.get_all("Tender Addendum Inquiry", filters={"tender": root.name}, fields=["name", "addendum", "question", "received_at", "status", "response", "affects_requirements", "responded_by", "responded_at", "broadcast_status", "record_version"], order_by="received_at asc", limit_page_length=0)
	for row in inquiries:
		row["received_at_label"] = serializer.fmt_datetime_short(row["received_at"]) if row["received_at"] else ""
		row["responded_at_label"] = serializer.fmt_datetime_short(row["responded_at"]) if row["responded_at"] else ""
		row["addendum_reference"] = cstr(frappe.db.get_value("Tender Addendum", row["addendum"], "addendum_reference")) if row["addendum"] else ""
		row["candidate_label"] = "Verified supplier account"
		row["response_status"] = "Answered" if row["status"] == "Answered" else ("Late" if row["status"] == "Late" else "Awaiting response")
	cancellation = None
	if root.cancellation and frappe.db.exists("Tender Cancellation", root.cancellation):
		doc = frappe.get_doc("Tender Cancellation", root.cancellation)
		cancellation = {
			"name": doc.name, "ground": cstr(doc.ground), "ground_label": cstr(doc.ground_label), "reason": cstr(doc.reason), "decided_by_name": _full_name(doc.decided_by), "decided_at_label": serializer.fmt_datetime_short(doc.decided_at) if doc.decided_at else "",
			"ppra_report_due_by": serializer.fmt_date_short(doc.ppra_report_due_by), "candidate_notice_due_by": serializer.fmt_date_short(doc.candidate_notice_due_by),
			"recommendation": _recommendation(doc), "obligations": [{"obligation_id": o.obligation_id, "obligation_type": o.obligation_type, "channel": cstr(o.channel), "label": o.label, "due_by": serializer.fmt_date_short(o.due_by), "status": o.status, "evidence_reference": cstr(o.evidence_reference), "recorded_by_name": _full_name(o.recorded_by), "recorded_at_label": serializer.fmt_datetime_short(o.recorded_at) if o.recorded_at else ""} for o in doc.obligations],
			"cancellation_digest": cstr(doc.cancellation_digest), "notice_document_digest": cstr(doc.notice_document_digest), "record_version": int(doc.record_version or 0),
		}
	effective_addenda = [a for a in addenda if a["status"] == "Issued"]
	return {
		"addenda": addenda, "effective_addenda_count": len(effective_addenda), "current_addendum": effective_addenda[-1] if effective_addenda else None,
		"inquiries": inquiries, "cancellation": cancellation,
		"empty_addenda_text": "No addenda have been issued." if not effective_addenda else "", "empty_inquiries_text": "No addendum inquiries have been received." if not inquiries else "",
	}


def _change_summary(row: dict[str, Any]) -> str:
	area = cstr(row.get("affected_area"))
	reference = cstr(row.get("affected_reference"))
	if "delivery location" in reference.lower():
		return "Delivery point clarified"
	if row.get("change_class") == "Submission deadline extension":
		return "Submission deadline extended"
	return f"{area}: {reference}" if reference else area


def _recommendation(doc) -> dict[str, Any] | None:
	if not doc.recommendation:
		return None
	row = frappe.db.get_value("Tender Decision", doc.recommendation, ["actor", "decided_at", "reason"], as_dict=True)
	if not row:
		return None
	return {"by_name": _full_name(row.actor), "at_label": serializer.fmt_datetime_short(row.decided_at) if row.decided_at else "", "text": cstr(row.reason)}
