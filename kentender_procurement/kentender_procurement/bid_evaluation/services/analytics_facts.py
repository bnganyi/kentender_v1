# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — Bid Evaluation's facts for Procurement Analytics (plan Phase 2C; FU-ANL-06).

One function, `facts_for(*, user, tender_names, at)`, called by the Tenders Analytics provider. It only reads: no case is
prepared, advanced, refreshed or marked, and neither `reads.access` nor the stage summary is called. It does not decide the
audience (the Tenders provider does), and it gives every actor the same facts, technical readers included. It names no
bidder, finding, score or bid value. Per Tender with an evaluation case it returns:

- `case_state`: the owner's state (Preparing, Reviewing, Signing, Report sent, No evaluation required, Cancelled).
- `no_evaluation_required`: the case ended because no bids were received.
- `report_sent_at`: the EARLIEST delivered `Evaluation Report Delivery.delivered_at` with status Delivered (T4 end). A later
  or corrected report version does not move it, and a Pending or Failed delivery is not a report sent.
- `opening_completed_at`: `Evaluation Case.opening_completed_at`.
- `outstanding`: None, or `{text, holder, since}` (ANL-M-02). `text` is the owner's wording without any instant; `holder` is
  the person or people it names (the responsibility when the owner names no one); `since` is the RAW instant the matter reached
  its holder:
    * the committee has not been appointed: the intake's `received_at` (opening received), else the case's `prepared_at`,
      else its creation (Home's own fallback), holder the Accounting Officer;
    * committee review outstanding (Reviewing, committee appointed): the later of the intake's `received_at` (the automatic
      checks ran when the opening package was received) and the appointment's `appointed_at`. Home's oversight row uses the
      appointment alone; the two agree when the committee is appointed after the opening completes;
    * waiting for signatures (Signing): the signing version's `frozen_at`;
    * a delivered report returned for correction: the return's `returned_at`;
    * an open opening-package issue: the support issue's `opened_at`; a recorded suspension: its `received_at`.
  The module records no instant for clarification waits and they are not matters here (they would name a supplier). A
  matter whose real instant is not recorded is None, never an invented one. A case that is delivered, ended or only waiting for
  the opening to take place has no outstanding matter.

- `position`: a short phrase for the owner's state, without any stage label (the Tenders provider prefixes its bucket), from the
  same real fields as `outstanding`, one phrase per state: "no bids were received" (No evaluation required), "evaluation ended"
  (Cancelled), "report returned for correction", "report delivered — Award receipt pending" (the latest delivered report is still
  `Open`: Award has not taken it up), "paused by the recorded instruction", "waiting for the report to be signed",
  "committee not yet appointed", "automatic checks complete; committee review outstanding", "opening-package issue being resolved",
  "waiting for the opening to complete". Empty when nothing applies (a delivered report Award has taken up).

Technical readers get these facts in full. A failed read raises."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import analytics_contract as contract
from kentender_procurement.bid_evaluation.services import next_steps, oversight, people, records, roster, signing

PREPARING, REVIEWING, SIGNING, SENT, NONE_REQUIRED, CANCELLED = "Preparing", "Reviewing", "Signing", "Report sent", "No evaluation required", "Cancelled"


def facts_for(*, user: str, tender_names: list[str], at: datetime) -> dict[str, dict[str, Any]]:
	"""Evaluation facts keyed by Tender name; a Tender with no evaluation case is omitted."""
	names = list(dict.fromkeys(name for name in tender_names or [] if name))
	if not names:
		return {}
	out: dict[str, dict[str, Any]] = {}
	for case in frappe.get_all(records.CASE, filters={"tender": ("in", names)}, pluck="name", order_by="creation asc"):
		doc = frappe.get_doc(records.CASE, case)
		out.setdefault(doc.tender, _facts(doc))
	return out


def _facts(doc) -> dict[str, Any]:
	return {
		"case_state": cstr(doc.state), "no_evaluation_required": doc.state == NONE_REQUIRED, "report_sent_at": _report_sent_at(doc),
		"opening_completed_at": get_datetime(doc.opening_completed_at) if doc.opening_completed_at else None, "outstanding": _outstanding(doc),
		"position": _position(doc),
	}


def _report_sent_at(doc) -> datetime | None:
	"""The earliest delivered report (`oversight.deliveries` lists the newest first)."""
	rows = oversight.deliveries(doc.name)
	if not rows:
		return None
	if any(not row.delivered_at for row in rows):
		raise ValueError(f"a delivered report of {doc.name} has no delivered_at")
	return min(get_datetime(row.delivered_at) for row in rows)


def _position(doc) -> str:
	"""The owner's state as a short phrase, in the order `_outstanding` decides the matter."""
	if doc.state == NONE_REQUIRED:
		return "no bids were received"
	if doc.state == CANCELLED:
		return "evaluation ended"
	rows = oversight.deliveries(doc.name)
	if oversight.correction(doc, rows):
		return "report returned for correction"
	if doc.state == SENT:
		return "report delivered — Award receipt pending" if rows and rows[0].review_state == "Open" else ""
	if doc.suspended:
		return "paused by the recorded instruction"
	if doc.state == SIGNING:
		return "waiting for the report to be signed"
	if not roster.current_appointment(doc.name):
		return "committee not yet appointed"
	if doc.state == REVIEWING:
		return "automatic checks complete; committee review outstanding"
	if doc.state == PREPARING:
		return "opening-package issue being resolved" if next_steps._source_issue(doc) else "waiting for the opening to complete"
	return ""


# --------------------------------------------------------------------------
# the outstanding matter
# --------------------------------------------------------------------------


def _matter(text: str, holder: str, since: Any) -> dict[str, Any] | None:
	"""None when the real instant is not recorded."""
	return contract.outstanding(text, holder, get_datetime(since)) if since else None


def _outstanding(doc) -> dict[str, Any] | None:
	if doc.state in (NONE_REQUIRED, CANCELLED):
		return None
	rows = oversight.deliveries(doc.name)
	returned = oversight.correction(doc, rows)
	if returned:
		return _matter(returned["headline"], _correcting(doc), rows[0].returned_at)
	if doc.state == SENT:
		return None
	if doc.suspended:
		return _suspended(doc)
	if doc.state == SIGNING:
		return _signing(doc)
	if not roster.current_appointment(doc.name):
		return _unappointed(doc)
	if doc.state == REVIEWING:
		return _review(doc)
	if doc.state == PREPARING:
		return _source_issue(doc)
	return None


def _correcting(doc) -> str:
	"""The chair or the secretary: the people the owner tells to correct a returned report."""
	return " or ".join(people.full_name(user) for user in (roster.chair(doc.name), roster.secretary(doc.name)) if user) or "Chair or Secretary"


def _intake_received(doc) -> Any:
	return (frappe.db.get_value("Evaluation Source Intake", doc.source_intake, "received_at") if doc.source_intake else None) or None


def _unappointed(doc) -> dict[str, Any] | None:
	holders = people.holders(people.ACCOUNTING_OFFICER)
	holder = " or ".join(people.full_name(user) for user in holders) if 0 < len(holders) <= 2 else people.ACCOUNTING_OFFICER
	received = _intake_received(doc)
	if doc.source_intake:
		return _matter("Opening is complete. The evaluation committee has not been appointed.", holder, received or doc.opening_completed_at or doc.prepared_at or doc.creation)
	return _matter("The evaluation committee has not been appointed.", holder, doc.prepared_at or doc.creation)


def _review(doc) -> dict[str, Any] | None:
	appointment = roster.current_appointment(doc.name)
	received = _intake_received(doc) or doc.opening_completed_at
	instants = [get_datetime(value) for value in (received, appointment.appointed_at) if value]
	chair = roster.chair(doc.name)
	text = "Automatic checks complete; committee review outstanding."
	if chair:
		text += f" {people.full_name(chair)} chairs the appointed committee."
	return _matter(text, people.full_name(chair) if chair else "Evaluation committee", max(instants) if instants else None)


def _signing(doc) -> dict[str, Any] | None:
	version = signing.signing_version(doc)
	pending = [s["member"] for s in signing.signatures(version) if not s["signed_at"]] if version else []
	if not pending:
		return None
	return _matter(f"Waiting for {next_steps.names(pending)} to sign report {version.version_number}.", " and ".join(people.full_name(user) for user in pending), version.frozen_at)


def _suspended(doc) -> dict[str, Any] | None:
	event = frappe.db.get_value("Evaluation Source Event", doc.suspension_event, ["authority", "received_at"], as_dict=True) or {}
	authority = cstr(event.get("authority"))
	return _matter("Evaluation is paused by the recorded instruction.", people.full_name(authority) if authority else people.ACCOUNTING_OFFICER, event.get("received_at"))


def _source_issue(doc) -> dict[str, Any] | None:
	issue = next_steps._source_issue(doc)
	if not issue:
		return None
	holders = [people.full_name(user) for user in json.loads(issue.holder_users_json or "[]")]
	who = next_steps.names(json.loads(issue.holder_users_json or "[]")) or "Technical support"
	return _matter(f"{who} is resolving the opening-package issue.", " and ".join(holders) or cstr(issue.holder_role), issue.opened_at)
