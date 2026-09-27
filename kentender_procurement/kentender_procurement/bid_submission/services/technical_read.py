# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The technical read of Bid Submission (KT-STD-001 v1.6 §3A.6; AUTH-ADR-001
§8; BDS-CHG-001 v0.8 §5.9 item 7, §12.3 item 7; owner decision 27 Sep 2026).

A technical reader — Administrator or System Manager — finds bid records
through the shared Technical record search and reads their metadata only:
identities, states, instants, versions, custody and correlation references.
Never a response, price, file name, evidence, supplier name or any other bid
content, and never a business action: the next step is "not involved". The
supplier-facing reads stay closed to technical readers (they answer Not
found), so these reads are the technical reader's own. The service status
(availability and open incidents) is also readable by the Technical Operator.

Registered through the `kt_technical_reference_resolvers` and
`kt_technical_read_probes` hooks."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_core.services import next_step as ns
from kentender_core.services.authorization import is_technical

from kentender_procurement.bid_submission.services import availability, labels


def _form(doctype: str):
	return lambda name: ["Form", doctype, name]


def reference_resolvers() -> list[dict]:
	return [
		{"doctype": "Bid Workspace", "label": "Bid", "reference_field": "bid_reference", "title_field": "tender_reference", "status_field": "status", "route": _form("Bid Workspace")},
		{"doctype": "Bidder Arrangement", "label": "Bidder arrangement", "reference_field": "bidder_arrangement_id", "title_field": "tender_reference", "status_field": "status", "route": _form("Bidder Arrangement")},
		{"doctype": "Bid Receipt", "label": "Bid receipt", "reference_field": "receipt_reference", "title_field": "tender_reference", "status_field": "version_number", "route": _form("Bid Receipt")},
		{"doctype": "Bid Submission Attempt", "label": "Submission attempt", "reference_field": "correlation_id", "title_field": "bid_workspace", "status_field": "status", "route": _form("Bid Submission Attempt")},
		{"doctype": "Tender Security Intake", "label": "Tender-security receipt", "reference_field": "intake_reference", "title_field": "tender_reference", "status_field": "deadline_class", "route": _form("Tender Security Intake")},
		{"doctype": "Bid Submission Incident", "label": "Bid Submission incident", "reference_field": "incident_key", "title_field": "title", "status_field": "status", "route": _form("Bid Submission Incident")},
		{"doctype": "Bid Opening Handoff", "label": "Bid Opening hand-off", "reference_field": "handoff_id", "title_field": "tender_reference", "status_field": "delivery_status", "route": _form("Bid Opening Handoff")},
	]


def _require_technical(user: str) -> None:
	if not is_technical(user):
		raise frappe.DoesNotExistError("This record is unavailable or you do not have permission to view it.")


def get_bid_technical_summary(*, bid_reference: str, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	_require_technical(actor)
	if not frappe.db.exists("Bid Workspace", cstr(bid_reference)):
		raise frappe.DoesNotExistError("This record is unavailable or you do not have permission to view it.")
	ws = frappe.get_doc("Bid Workspace", bid_reference)
	versions = frappe.get_all(
		"Bid Submission Version", filters={"bid_workspace": ws.name},
		fields=["name", "version_number", "status", "received_at", "accepted_at", "receipt", "tender_box_envelope"], order_by="version_number asc",
	)
	attempts = frappe.get_all("Bid Submission Attempt", filters={"bid_workspace": ws.name}, fields=["correlation_id", "status", "received_at", "support_reference"], order_by="creation asc")
	handoffs = frappe.get_all("Bid Hand-off", filters={"bid_workspace": ws.name, "status": "Open"}, pluck="kind")
	return {
		"outcome": "OK",
		"bid": {
			"bid_reference": ws.name, "tender_reference": ws.tender_reference, "bidder_arrangement": frappe.db.get_value("Bidder Arrangement", ws.bidder_arrangement, "bidder_arrangement_id"),
			"status": ws.status, "status_since": labels.datetime_label(ws.status_since), "draft_version": int(ws.current_draft_version or 0),
			"bid_definition_id": ws.bid_definition_id, "definition_version": int(ws.definition_version or 0), "record_version": int(ws.record_version or 0),
		},
		"submission_versions": [
			{"submission_version": v.name, "version_number": int(v.version_number), "status": v.status, "received_at": labels.datetime_seconds_label(v.received_at),
			 "accepted_at": labels.datetime_seconds_label(v.accepted_at), "receipt_reference": v.receipt, "envelope": v.tender_box_envelope}
			for v in versions
		],
		"attempts": [{"correlation_id": a.correlation_id, "status": a.status, "received_at": labels.datetime_seconds_label(a.received_at), "support_reference": cstr(a.support_reference)} for a in attempts],
		"open_handoffs": handoffs,
		"next_step": ns.not_involved(stage=""),
	}


def get_submission_service_status(*, user: str | None = None) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	from kentender_procurement.bid_submission.services import guidance

	if not is_technical(actor) and actor not in _holders(guidance.TECHNICAL):
		raise frappe.DoesNotExistError("This record is unavailable or you do not have permission to view it.")
	gate = availability.get_submission_availability()
	incidents = frappe.get_all("Bid Submission Incident", filters={"status": "Open"}, fields=["incident_key", "kind", "title", "reference", "opened_at", "affected_bids"], order_by="opened_at asc")
	return {
		"outcome": "OK",
		"availability": {"available": gate["available"], "reason_code": gate["code"], "message": gate["message"]},
		"open_incidents": [{**dict(i), "opened_at": labels.datetime_label(i.opened_at)} for i in incidents],
	}


def _holders(role: str) -> list[str]:
	return frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user")


def _bid_kwargs() -> dict | None:
	name = frappe.db.get_value("Bid Workspace", {}, "name", order_by="modified desc")
	return {"bid_reference": name} if name else None


def read_probes() -> list[dict]:
	from kentender_procurement.bid_submission import api

	return [
		{"label": "bid_submission.get_submission_service_status", "call": api.get_submission_service_status, "kwargs": lambda: {}},
		{"label": "bid_submission.get_bid_technical_summary", "call": api.get_bid_technical_summary, "kwargs": _bid_kwargs},
	]
