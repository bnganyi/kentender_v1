# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award issues and restrictions (AWD-CHG-001 v0.4 §4 "Issue / restriction",
§5.6, §5.10). One issue per source event (retries cannot duplicate it); an
issue is cleared only by its own evidenced disposition, never by resolving an
unrelated one, never by a timer. `holds` marks an issue that stops positive
progress (a decision to award, notice issue, Contracting delivery)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.award.services import clock, people, records, state

ISSUE = state.ISSUE


def open_issue(doc, *, source_event: str, issue_type: str, title: str, holds: bool = True, owner_role: str = people.HEAD_OF_PROCUREMENT, owner_user: str = "",
		subtype: str = "", basis: str = "", scope: str = "", source: str = "", evidence: str = "", reason: str = "", effective_at=None, received_at=None,
		detail: dict | None = None) -> Any:
	name = frappe.db.get_value(ISSUE, {"source_event": source_event}, "name")
	if name:
		return frappe.get_doc(ISSUE, name)
	now = clock.now()
	number = frappe.db.count(ISSUE, {"award_case": doc.name}) + 1
	if not owner_user and owner_role == people.HEAD_OF_PROCUREMENT:
		owner_user = hop_for(doc)
	return records.new(ISSUE, issue_id=f"{doc.name}-ISS-{number:02d}", award_case=doc.name, cycle=doc.current_cycle, source_event=source_event,
		issue_type=issue_type, subtype=subtype, title=title, basis=basis, holds=1 if holds else 0, scope=scope, source=source, evidence=evidence, reason=reason,
		effective_at=effective_at or now, received_at=received_at or now, owner_role=owner_role, owner_user=owner_user or None, state="Open",
		detail_json=records.dumps(detail or {}), fixture_namespace=doc.fixture_namespace)


def open_issues(doc, *, issue_type: str = "", subtype: str = "") -> list:
	filters = {"award_case": doc.name, "state": "Open"}
	if issue_type:
		filters["issue_type"] = issue_type
	if subtype:
		filters["subtype"] = subtype
	return [frappe.get_doc(ISSUE, n) for n in frappe.get_all(ISSUE, filters=filters, pluck="name", order_by="received_at asc, creation asc")]


def holding(doc) -> list:
	return [i for i in open_issues(doc) if i.holds]


def resolve(issue, *, disposition: str, reason: str = "", evidence: str = "", next_action: str = "", user: str = "") -> Any:
	return records.update(issue, state="Resolved", disposition=disposition, disposition_reason=cstr(reason), disposition_evidence=cstr(evidence),
		next_action=cstr(next_action), resolved_by=user if user and frappe.db.exists("User", user) else None, resolved_at=clock.now())


def resolve_automatic(doc, *, subtype: str, note: str) -> int:
	"""A system-detected condition that the system now sees cleared (a status
	read that works again, a verified profile): only that subtype closes."""
	count = 0
	for issue in open_issues(doc, subtype=subtype):
		resolve(issue, disposition="Owner correction confirmed", reason=note, evidence="Automatic recheck", user="")
		count += 1
	return count


def hop_for(doc) -> str:
	"""The Head of Procurement for this award: the report's recipient if they
	still hold the responsibility, otherwise the current holder (§5.9: an
	expired authority routes the task to the current holder)."""
	rep = state.current_report(doc)
	recipient = cstr(state.snapshot(rep).get("recipient")) if rep else ""
	if recipient and people.holds(recipient, people.HEAD_OF_PROCUREMENT):
		return recipient
	return people.first_holder(people.HEAD_OF_PROCUREMENT)


def ao_for(doc) -> str:
	return people.first_holder(people.ACCOUNTING_OFFICER)
