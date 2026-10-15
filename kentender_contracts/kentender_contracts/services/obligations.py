# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Compliance obligations (CM-CHG-001 v0.8 sections 4.1, 5.15, 7, 19.3 CM-R-13, CM-R-15; legal question LQ-06; plan Phase 8; boards D15-L, D10).

A triggered duty is an obligation: the trigger kept with its **instant**, the rule, the due date only where one is verified, the recipient, the owner and the evidence. Publication, variation reporting, progress reporting
and the like stay apart from the lifecycle: a supplier's signature does not discharge a publication obligation, and a submitted report does not prove every row's contract complete. **Unknown applicability creates
head-of-procurement review work at once and preserves the original event**; no deadline is invented. A person may record source evidence for the legal owner (a reference, a date, a copy, notes): it is a proposal
for review, never an executable rule, an officer-authored deadline or a verified status.

Each duty's own event is kept apart from the others: the award decision is not erased by the signing, and a variation is reported from the effective amendment."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, getdate

from kentender_contracts.services import clock, events, preflight, records, work
from kentender_contracts.services.errors import fail, invalid

OBL = "Contract Obligation"
CASE = "Contract Case"
KINDS = ("Publication", "Progress report", "Variation report", "Termination record", "Security action", "Other")
UNCONFIRMED = "Not confirmed — set by current directions"


def get(case: str, kind: str, subject: str = ""):
	filters = {"contract_case": case, "kind": kind, "state": ["!=", "Superseded"]}
	if subject:
		filters["subject"] = subject
	name = frappe.db.get_value(OBL, filters, "name", order_by="creation desc")
	return frappe.get_doc(OBL, name) if name else None


def all_for(case: str) -> list[Any]:
	return [frappe.get_doc(OBL, n) for n in frappe.get_all(OBL, filters={"contract_case": case, "state": ["!=", "Superseded"]}, pluck="name", order_by="creation asc")]


def detail(row) -> dict[str, Any]:
	return records.loads(row.evidence_json)


def open_obligation(case: str, *, kind: str, rule: str, trigger_event: str, trigger_at, subject: str, owner: str = "", recipient: str = "", due_at=None, due_basis: str = "", state: str = "Needs review", facts: dict[str, Any] | None = None):
	"""One obligation per (contract, kind, subject): the same trigger arriving again finds it. The due date is set only when the caller has a verified one; otherwise the basis says it is not confirmed."""
	existing = get(case, kind, subject)
	if existing is not None:
		return existing
	row = records.new(OBL, contract_case=case, kind=kind, state=state, rule=rule, trigger_event=trigger_event, trigger_at=trigger_at, due_at=due_at, due_basis=due_basis or (UNCONFIRMED if not due_at else ""),
		recipient=recipient, owner_user=owner or next(iter(work.holders(work.HOP)), ""), evidence_json=records.dumps({"events": [{"event": trigger_event, "at": str(trigger_at)}], "evidence": [], **(facts or {})}), subject=subject, record_version=1)
	return row


def add_event(row, event: str, at) -> None:
	"""A separate fact about the same duty (the contract was signed): kept beside the trigger, never replacing it."""
	body = detail(row)
	if not any(e["event"] == event for e in body["events"]):
		body["events"].append({"event": event, "at": str(at)})
		records.update(row, evidence_json=records.dumps(body), record_version=cint(row.record_version) + 1)


# -- publication --------------------------------------------------------------------------------------------------------------------------
def on_award_received(case: str, package: dict[str, Any]) -> None:
	"""The award decision arrived: publication is an obligation whose deadline and channel nobody can state yet, so it is opened for review now with the decision's own instant."""
	notices = (package.get("notice_batch") or {}).get("notices") or []
	at = (package.get("decision") or {}).get("decided_at") or (notices[0].get("given_at") if notices else None) or clock.now()
	row = open_obligation(case, kind="Publication", rule="CM-R-13", trigger_event="Award decision recorded", trigger_at=at, subject="publication",
		facts={"destinations": "Notice boards; website if available; report to PPRA"})
	events.record(case, "Publication obligation opened", "", "The publication requirement needs review; no deadline has been confirmed.", obligation=row.name)


def on_signed(case: str, at) -> None:
	"""The contract was signed: a separate fact about the same duty (the award event and its instant are kept untouched). The duty stays in the contract's Duties, Needs review, until the requirement is confirmed."""
	row = get(case, "Publication", "publication")
	if row is not None:
		add_event(row, "Contract signed", at)


def record_source_evidence(case: str, *, obligation: str, reference: str, dated: str, copy: str, notes: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordLegalSourceEvidence`: attributed evidence for the legal owner to review. It never edits a rule, sets a deadline or marks anything verified; it only sends the owner its work and keeps the proposal."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(OBL, obligation)
		if row.contract_case != case:
			raise frappe.DoesNotExistError("Not found")
		try:
			day = getdate(dated)
		except Exception:  # noqa: BLE001
			day = None
		invalid({"reference": "" if cstr(reference).strip() else "Enter the source reference.", "dated": "" if day else "Enter the date of the source."})
		found = detail(row)
		found["evidence"].append({"reference": cstr(reference).strip(), "dated": str(day), "copy": cstr(copy).strip(), "notes": cstr(notes).strip(), "by": actor, "at": str(clock.now()), "status": "Proposed for the legal owner's review"})
		records.update(row, evidence_json=records.dumps(found), record_version=cint(row.record_version) + 1)
		work.assign(case, work.waiting_command("RecordContractAwardPublication", "legal"), "Waiting for the legal and reporting owner to confirm the requirement.", "publication", 1, work.holders(work.HOP), role=work.HOP, state="Waiting")
		events.record(case, "Legal source evidence recorded", actor, f"Source evidence {cstr(reference).strip()} was recorded for the legal owner's review.", obligation=row.name)
		records.bump(doc)
		return records.summary(doc, obligation=row.name)

	return records.command("RecordLegalSourceEvidence", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "obligation": obligation, "reference": reference, "dated": dated,
		"copy": copy, "notes": notes}, body=body, authorise=authorise)


def record_publication(case: str, *, obligation: str, channel: str, published_on: str, evidence: list[dict[str, Any]], expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordContractAwardPublication`: the publication as it actually happened, with its channel and evidence. Receipt and completion stay distinct, and the original trigger instants are preserved. It is a consequential
	record, so the profile's rule must be verified; it sets no deadline and takes no channel from an unconfirmed direction."""
	preflight.exists(case)

	def authorise() -> None:
		preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or "")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(OBL, obligation)
		if row.contract_case != case or row.kind != "Publication":
			raise frappe.DoesNotExistError("Not found")
		if row.state == "Satisfied":
			return records.summary(doc, obligation=row.name, already=True)
		try:
			day = getdate(published_on)
		except Exception:  # noqa: BLE001
			day = None
		invalid({"channel": "" if cstr(channel).strip() else "Enter the channel it was published in.", "published_on": "" if day else "Enter the day it was published.",
			"evidence": "" if evidence and all(cstr(e.get("label")).strip() for e in evidence) else "Attach the evidence of publication."})
		preflight.rules(doc, "RecordContractAwardPublication").raise_if_any()
		found = detail(row)
		found["published"] = {"channel": cstr(channel).strip(), "on": str(day), "evidence": evidence, "by": actor, "at": str(clock.now())}
		records.update(row, state="Satisfied", disposition=f"Published on {day.strftime('%-d %B %Y')} ({cstr(channel).strip()})", evidence_json=records.dumps(found), record_version=cint(row.record_version) + 1)
		work.finish(case, command="RecordContractAwardPublication", subject="publication", actor=actor)
		events.record(case, "Award publication recorded", actor, f"The award was published on {day.strftime('%-d %B %Y')} ({cstr(channel).strip()}).", obligation=row.name)
		records.bump(doc)
		return records.summary(doc, obligation=row.name, state="Satisfied")

	return records.command("RecordContractAwardPublication", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "obligation": obligation, "channel": channel, "on": published_on,
		"evidence": evidence}, body=body, authorise=authorise)


# -- the other duties ---------------------------------------------------------------------------------------------------------------------
def on_variation_effective(case: str, change_name: str, change_no: int, at) -> None:
	"""An amendment took effect: its report is a duty of the profile, whose reporting period and recipient are not confirmed, so it is opened for review with the effective instant."""
	row = open_obligation(case, kind="Variation report", rule="CM-R-15", trigger_event=f"Amendment {change_no} effective", trigger_at=at, subject=f"amendment {change_no}", facts={"change": change_name})
	work.assign(case, "RecordContractReportSubmission", f"Report amendment {change_no}.", f"amendment {change_no} report", 1, work.holders(work.HOP), role=work.HOP, state="Scheduled")
	events.record(case, "Variation obligation opened", "", f"Amendment {change_no} must be reported; the period and recipient are not confirmed.", obligation=row.name)


def on_termination_effective(case: str, termination_no: int, at) -> None:
	"""A termination took effect: its record is an internal output for the Accounting Officer and the head of procurement. No Regulations-only quarterly statutory default is imported."""
	open_obligation(case, kind="Termination record", rule="CM-R-16", trigger_event=f"Termination {termination_no} effective", trigger_at=at, subject=f"termination {termination_no}", state="Open",
		due_basis="Internal record; no statutory deadline is confirmed", recipient="Accounting Officer; head of procurement function")


def satisfy(case: str, kind: str, subject: str, disposition: str) -> None:
	row = get(case, kind, subject)
	if row is not None and row.state != "Satisfied":
		records.update(row, state="Satisfied", disposition=disposition, record_version=cint(row.record_version) + 1)
