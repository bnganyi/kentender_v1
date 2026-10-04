# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The opening audit export (BOP-CHG-001 v0.10 §12; PRC-CHG-001 v0.9 §12).

One bundle joining Bid Opening's own evidence (appointments and successors,
published arrangements, presence, custody participation without secrets,
each opened bid with its digests and readout, the register versions, every
exception, incident and decision, register-copy requests and deliveries, the
Evaluation handoff) with the Proceedings export (the final opening record
and its digest, each member's proof, every supplement). Narrative minutes
never replace the primary events. For oversight readers only; a technical
reader gets nothing here."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.bid_opening.services import people, prc_owner, records, reads

TABLES = {
	"appointments": ("Opening Committee Appointment", ["appointment_id", "version_number", "appointed_by", "appointed_at", "status", "supersedes_appointment", "reason"]),
	"arrangements": ("Opening Arrangement", ["arrangement_id", "version_number", "attendance_method", "scheduled_at", "join_opens_at", "published_by", "published_at", "status"]),
	"presence": ("Opening Presence", ["presence_id", "member_user", "joined_at", "left_at", "state"]),
	"custody_participation": ("Opening Custody Participation", ["participation_id", "member_user", "manifest_digest", "roster_digest", "confirmed_at", "outcome", "stale"]),
	"bids": ("Opening Entry", ["entry_id", "entry_number", "envelope_id", "receipt_reference", "package_digest", "render_digest", "page_count", "price_page",
		"designated_pages", "bidder_name", "submitted_total", "currency", "security_given", "revealed_at", "readout_speaker", "readout_confirmed_at",
		"readout_confirmed_by", "reported_speech_at", "status"]),
	"registers": ("Opening Register", ["register_id", "version_number", "entry_ids_json", "entry_count", "is_empty", "register_digest", "frozen_at"]),
	"exceptions": ("Opening Exception", ["exception_id", "exception_class", "entry", "observed_fact", "speaker_name", "response", "recorded_by", "recorded_at", "outcome"]),
	"incidents": ("Opening Access Incident", ["incident_id", "incident_type", "raised_at", "status", "resolved_at", "notification_state", "notification_attempts"]),
	"decisions": ("Opening Decision Item", ["decision_item_id", "kind", "holder_user", "reason", "status", "created_at", "cleared_at"]),
	"register_requests": ("Opening Register Request", ["request_id", "requester_user", "receipt_reference", "requested_at", "status", "delivery_mode", "register_digest",
		"delivered_at", "decline_reason"]),
}


def export_opening(*, tender: str, user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import reads as prc_reads

	case = records.case_for(tender)
	if not case or people.technical(user) or not reads.can_read(case, user):
		raise frappe.DoesNotExistError("Not found")
	doc = frappe.get_doc(records.CASE, case)
	bundle: dict[str, Any] = {"opening": {f: doc.get(f) for f in ("opening_id", "tender_reference", "state", "outcome", "manifest_handoff", "manifest_digest",
		"started_at", "ended_at", "completed_at", "evaluation_handoff")}}
	for key, (doctype, fields) in TABLES.items():
		bundle[key] = frappe.get_all(doctype, filters={"opening_case": case}, fields=fields, order_by="creation asc")
	handoff = frappe.db.get_value("Evaluation Handoff", {"opening_case": case}, ["handoff_id", "handoff_digest", "issued_at", "payload_json"], as_dict=True)
	bundle["evaluation_handoff"] = {**handoff, "payload": json.loads(handoff.payload_json)} if handoff else None
	if bundle["evaluation_handoff"]:
		bundle["evaluation_handoff"].pop("payload_json")
	with prc_owner.acting(case):
		bundle["proceedings"] = prc_reads.export_proceeding(owner_type=prc_owner.OWNER_TYPE, owner_id=case, user=user)
	return json.loads(json.dumps(bundle, default=str))
