# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Hand-offs and operational incidents (BDS-CHG-001 v0.8 §5.14; plan D15;
KT-STD-001 v1.8 §3B.4).

Suppliers are Website users with no Desk My Work, so a supplier hand-off is a
`Bid Hand-off` row: the holder's item ("Review and submit BID-…", "Review
ADD-… for BID-…") and the sender's waiting line ("Waiting for Mary Wanjiku to
submit BID-…"), shown in My bids and beside the bid's next step, with a
message to the holder through the supplier message transport. Operational
conditions — supplier-portal information incomplete, the production gate
closed, a submission service down, an attempt still unconfirmed — are
`Bid Submission Incident` rows for the current Technical Operator or Release
Operator (owner decision 27 Sep 2026), each with an in-product alert and a
safe reference only; the affected signatory gets the matching waiting line.

`sync` sets a bid's rows to match its recorded facts. It runs from the
commands that change those facts (a bid's saved state, an attempt's outcome,
a replacement, a withdrawal, the close) and from the scheduled `sweep`
(service health, a newly effective addendum, the deadline) — never from a
read, and never because someone read a notification."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import availability, clock, records, signature, supplier_gateway

HANDOFF = "Bid Hand-off"
INCIDENT = "Bid Submission Incident"
OPEN_STATUSES = ("Draft", "Needs attention", "Ready to submit")
TRANSPORT_HOOK = "kt_bds_supplier_message_transports"
NO_TRANSPORT = "Not sent — no supplier message transport is configured"


def _name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user)


def _names(users: list[str]) -> str:
	return ", ".join(_name(u) for u in users)


# -- the facts ----------------------------------------------------------------------


def _signatories(ws, arrangement) -> list[str]:
	named = cstr(arrangement.authorised_signatory_assignment)
	if named:
		row = supplier_gateway.assignment(assignment_id=named)
		return [row["user"]] if row else []
	return [a["user"] for a in supplier_gateway.organisation_signatories(organisation_id=ws.lead_organisation)]


def _preparer(ws, arrangement) -> list[str]:
	return [cstr(arrangement.tender_contact_user or ws.created_by)]


def _addendum_due(ws) -> str:
	"""The reference of the effective addendum this Draft still has to review, or ""."""
	from kentender_procurement.bid_submission.services import tenders_gateway

	current = tenders_gateway.current_definition(ws.tender)
	pending = bool(current and int(current["definition_version"]) > int(ws.definition_version or 0))
	if not pending and not json.loads(ws.attention_json or "[]"):
		return ""
	return cstr(frappe.db.get_value("Tender Addendum", {"tender": ws.tender, "status": "Issued"}, "addendum_reference", order_by="issued_at desc")) or "the current addendum"


def _blocking_condition() -> str:
	"""The operational condition that stops a ready bid being submitted, if any."""
	from kentender_core.services import public_portal

	gate = availability.get_submission_availability()
	if gate["code"] == "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED":
		return "gate"
	if gate["code"] in ("BDS_SIGNATURE_UNAVAILABLE", "BDS_SUBMISSION_SERVICE_UNAVAILABLE"):
		return "service"
	if (public_portal.get_public_portal_information() or {}).get("status") != "Complete":
		return "portal"
	return ""


WAITING = {
	"gate": ("Waiting for production submission availability", "Production submission gate"),
	"service": ("Waiting for electronic submission recovery", "Submission service"),
	"portal": ("Waiting for supplier portal information", "Supplier portal information"),
}


def desired(ws, *, at) -> dict[str, dict[str, Any]]:
	"""The hand-offs this bid should have open now, by key."""
	deadline = frappe.db.get_value("Tender", ws.tender, "submission_deadline")
	if ws.status not in OPEN_STATUSES or (deadline and get_datetime(at) >= get_datetime(deadline)):
		return {}
	arrangement = frappe.get_doc("Bidder Arrangement", ws.bidder_arrangement)
	signatories, preparer = _signatories(ws, arrangement), _preparer(ws, arrangement)
	correlation = signature.pending_attempt(ws.name)
	if correlation:
		kind = "Waiting for the result of this submission attempt"
		return {f"{ws.name}:attempt": {"kind": kind, "holder_role": "Technical Operator", "item_title": "", "sender_users": signatories, "waiting_title": kind, "notify": False}}
	addendum = _addendum_due(ws)
	if addendum:
		was_ready = bool(frappe.db.exists(HANDOFF, {"bid_workspace": ws.name, "kind": "Review and submit"}))
		return {f"{ws.name}:addendum": {
			"kind": "Review addendum", "holder_role": "Supplier Representative", "holder_users": preparer, "item_title": f"Review {addendum} for {ws.name}",
			"sender_users": signatories if was_ready else [], "waiting_title": f"Waiting for {_names(preparer)} to review the addendum" if was_ready else "", "notify": True,
		}}
	if ws.status != "Ready to submit":
		return {}
	condition = _blocking_condition()
	if condition:
		kind = WAITING[condition][0]
		return {f"{ws.name}:{condition}": {"kind": kind, "holder_role": "", "item_title": "", "sender_users": signatories, "waiting_title": kind, "notify": False}}
	return {f"{ws.name}:ready": {
		"kind": "Review and submit", "holder_role": "Authorised Signatory", "holder_users": signatories, "item_title": f"Review and submit {ws.name}",
		"sender_users": [u for u in preparer if u not in signatories], "waiting_title": f"Waiting for {_names(signatories)} to submit {ws.name}", "notify": True,
	}}


# -- keeping the rows in step ------------------------------------------------------------


def _message(users: list[str], subject: str, body: str) -> str:
	override = frappe.flags.get("kt_bds_message_transport")
	transports = [override] if override else [frappe.get_attr(p) for p in reversed(frappe.get_hooks(TRANSPORT_HOOK) or [])]
	results = []
	for user in users:
		message = {"to": user, "subject": subject, "body": body}
		# the last transport that takes the message wins; one returning None
		# declines (the Test Mailbox off a test environment)
		answer = next((taken for taken in (transport(message) for transport in transports) if taken is not None), None)
		if answer is None:
			return NO_TRANSPORT
		results.append(cstr(answer.get("result") or "Sent"))
	return ", ".join(sorted(set(results)))[:140]


def sync(workspace: str, *, at=None, reason: str = "") -> dict[str, int]:
	at = at or clock.now()
	ws = frappe.get_doc("Bid Workspace", workspace)
	want = desired(ws, at=at)
	have = {row.handoff_key: row for row in frappe.get_all(HANDOFF, filters={"bid_workspace": ws.name, "status": "Open"}, fields=["name", "handoff_key"])}
	done = {"opened": 0, "cleared": 0}
	for key, row in have.items():
		if key not in want:
			records.save(frappe.get_doc(HANDOFF, row.name).update({"status": "Cleared", "cleared_at": at, "clear_reason": (reason or f"Bid is now {ws.status}")[:140]}))
			done["cleared"] += 1
	for key, spec in want.items():
		if key in have:
			continue
		existing = frappe.db.get_value(HANDOFF, {"handoff_key": key}, "name")
		values = {
			"bid_workspace": ws.name, "tender": ws.tender, "kind": spec["kind"], "holder_role": spec.get("holder_role", ""), "holder_users": json.dumps(spec.get("holder_users") or []),
			"item_title": spec.get("item_title", ""), "sender_users": json.dumps(spec.get("sender_users") or []), "waiting_title": spec.get("waiting_title", ""), "status": "Open",
			"opened_at": at, "cleared_at": None, "clear_reason": "",
		}
		if spec.get("notify") and spec.get("holder_users"):
			values["notification_result"] = _message(spec["holder_users"], spec["item_title"], f"{spec['item_title']} before the deadline.")
		if existing:
			records.save(frappe.get_doc(HANDOFF, existing).update(values))  # the same hand-off opens again
		else:
			records.insert(frappe.get_doc({"doctype": HANDOFF, "handoff_key": key, **values}))
		done["opened"] += 1
	sync_incidents(at=at)
	return done


# -- operational incidents -----------------------------------------------------------------


def _holders(role: str) -> list[str]:
	return frappe.get_all("User Responsibility Assignment", filters={"business_role": role, "status": "Enabled"}, pluck="user", distinct=True)


def wanted_incidents() -> dict[str, dict[str, Any]]:
	from kentender_procurement.bid_submission.services import guidance

	out: dict[str, dict[str, Any]] = {}
	ready = frappe.db.count("Bid Workspace", {"status": "Ready to submit"})
	condition = _blocking_condition() if ready else ""
	if condition == "gate":
		out["production-gate"] = {"kind": "Production submission gate", "title": "Production submission is not enabled while bids are ready", "holder_role": guidance.RELEASE, "users": _holders(guidance.RELEASE), "reference": "production-submission-gate", "affected": ready}
	elif condition == "service":
		out["submission-service"] = {"kind": "Submission service", "title": "Electronic signing or submission is unavailable", "holder_role": guidance.TECHNICAL, "users": _holders(guidance.TECHNICAL), "reference": availability.get_submission_availability()["code"], "affected": ready}
	elif condition == "portal":
		out["portal-information"] = {"kind": "Supplier portal information", "title": "Supplier portal information is incomplete", "holder_role": "CFG System Manager", "users": [u for u in _holders(guidance.TECHNICAL) if "System Manager" in frappe.get_roles(u)], "reference": "public-portal-information", "affected": ready}
	from kentender_procurement.bid_submission.services import close

	for row in close.overdue_closes():  # FU-V08-44: the deadline passed and nothing closed
		out[f"close-overdue:{row['tender']}"] = {
			"kind": "Submission close", "title": f"Close {row['tender_reference']}: submissions ended {row['deadline']} but Bid Submission has not closed", "holder_role": guidance.TECHNICAL,
			"users": _holders(guidance.TECHNICAL), "reference": row["tender_reference"], "affected": frappe.db.count("Bid Workspace", {"tender": row["tender"]}),
		}
	for correlation in frappe.get_all("Bid Submission Attempt", filters={"status": ("in", ("Uncertain", "Dispatching"))}, pluck="correlation_id"):
		out[f"attempt:{correlation}"] = {"kind": "Submission attempt", "title": f"Reconcile submission attempt {correlation}", "holder_role": guidance.TECHNICAL, "users": _holders(guidance.TECHNICAL), "reference": correlation, "affected": 1}
	return out


def sync_incidents(*, at=None) -> dict[str, int]:
	from kentender_core.services.notification_service import emit_notification_log

	at = at or clock.now()
	want = wanted_incidents()
	done = {"opened": 0, "resolved": 0}
	for row in frappe.get_all(INCIDENT, filters={"status": "Open"}, fields=["name", "incident_key"]):
		if row.incident_key not in want:
			records.save(frappe.get_doc(INCIDENT, row.name).update({"status": "Resolved", "resolved_at": at}))
			done["resolved"] += 1
	open_keys = set(frappe.get_all(INCIDENT, filters={"status": "Open"}, pluck="incident_key"))
	for key, spec in want.items():
		if key in open_keys:
			continue
		values = {"kind": spec["kind"], "title": spec["title"], "holder_role": spec["holder_role"], "holder_users": json.dumps(spec["users"]), "reference": spec["reference"], "affected_bids": spec["affected"], "status": "Open", "opened_at": at, "resolved_at": None}
		existing = frappe.db.get_value(INCIDENT, {"incident_key": key}, "name")
		doc = records.save(frappe.get_doc(INCIDENT, existing).update(values)) if existing else records.insert(frappe.get_doc({"doctype": INCIDENT, "incident_key": key, **values}))
		for user in spec["users"]:
			emit_notification_log(
				for_user=user, subject=spec["title"], message=f"{spec['title']}. Reference {spec['reference']}.", document_type=INCIDENT, document_name=doc.name,
				event_type=spec["kind"], entity_scope="Bid Submission", route=f"/app/bid-submission-incident/{doc.name}", correlation_key=f"bds-incident:{doc.name}:{cstr(at)}",
			)
		done["opened"] += 1
	return done


def sweep() -> dict[str, int]:
	"""Scheduler: keep every open bid's hand-offs and the incidents in step
	with service health, newly effective addenda and the deadline."""
	done = {"bids": 0}
	names = set(frappe.get_all("Bid Workspace", filters={"status": ("in", OPEN_STATUSES)}, pluck="name"))
	names |= set(frappe.get_all(HANDOFF, filters={"status": "Open"}, pluck="bid_workspace"))
	for name in sorted(names):
		sync(name)
		done["bids"] += 1
	sync_incidents()
	frappe.db.commit()
	return done


# -- what a supplier sees ------------------------------------------------------------------------


def items_for(user: str, workspaces: list[str]) -> list[dict[str, Any]]:
	"""The person's open hand-off items and waiting lines on these bids."""
	out = []
	for row in frappe.get_all(HANDOFF, filters={"bid_workspace": ("in", workspaces or [""]), "status": "Open"}, fields=["bid_workspace", "kind", "holder_users", "item_title", "sender_users", "waiting_title", "opened_at"], order_by="opened_at asc"):
		if user in json.loads(row.holder_users or "[]") and row.item_title:
			out.append({"bid_reference": row.bid_workspace, "kind": "item", "title": row.item_title})
		elif user in json.loads(row.sender_users or "[]") and row.waiting_title:
			out.append({"bid_reference": row.bid_workspace, "kind": "waiting", "title": row.waiting_title})
	return out

