# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Award clocks (AWD-CHG-001 v0.4 §4 last paragraph, §5.5; AWD-AC-013).

A clock is derived from a retained authoritative event (issue, giving) and
the verified profile, never entered as a date and never a browser timer. Each
record keeps its rule and profile version, the triggering evidence, the
timezone and calendar treatment and the calculated deadline; a lawful
revision appends a new revision and keeps the earlier one."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, get_datetime

from kentender_procurement.award.services import clock, profile, records, state
from kentender_procurement.services import sequence

CLOCK = state.CLOCK


def record(doc, *, kind: str, notice: str = "", trigger_at, trigger_evidence: str, deadline, rule: str) -> Any:
	p = profile.current()
	existing = frappe.get_all(CLOCK, filters={"award_case": doc.name, "notice": notice, "kind": kind, "state": "Current"}, fields=["name", "deadline", "revision"])
	if existing and get_datetime(existing[0].deadline) == get_datetime(deadline):
		return frappe.get_doc(CLOCK, existing[0].name)
	revision = 1
	for row in existing:
		revision = cint(row.revision) + 1
		records.update(frappe.get_doc(CLOCK, row.name), state="Revised")
	number = sequence.next_count(CLOCK, {"award_case": doc.name})
	return records.new(CLOCK, clock_id=f"{doc.name}-CLK-{number:02d}", award_case=doc.name, notice=notice, kind=kind, rule=rule,
		profile_version=p.get("profile_version"), trigger_evidence=trigger_evidence, trigger_at=trigger_at, timezone=p.get("timezone"), calendar=p.get("calendar"),
		deadline=deadline, revision=revision, state="Current", fixture_namespace=doc.fixture_namespace)


def current(doc, kind: str, notice: str = ""):
	filters = {"award_case": doc.name, "kind": kind, "state": "Current"}
	if notice:
		filters["notice"] = notice
	rows = frappe.get_all(CLOCK, filters=filters, fields=["name", "deadline", "notice"], order_by="deadline desc")
	return rows


def reply_deadline_for(notice) -> Any:
	rows = current(frappe.get_doc(records.CASE, notice.award_case), "Reply deadline", notice.name)
	return get_datetime(rows[0].deadline) if rows else (get_datetime(notice.reply_deadline) if notice.reply_deadline else None)


def earliest_permitted(doc, batch) -> dict[str, Any]:
	"""The latest minimum-wait deadline over every required recipient (§5.5
	"in a batch with delayed giving, conservatively prevent progress until all
	affected recipients' applicable minimum periods have ended"). Unknown until
	every recipient's giving evidence exists — never estimated before."""
	notices = state.notices(batch)
	if not notices or any(n.status != "Given" for n in notices):
		return {"known": False, "at": None}
	deadlines = []
	for n in notices:
		rows = current(doc, "Minimum wait", n.name)
		if not rows:
			return {"known": False, "at": None}
		deadlines.append(get_datetime(rows[0].deadline))
	at = max(deadlines)
	return {"known": True, "at": at, "passed": clock.now() >= at}
