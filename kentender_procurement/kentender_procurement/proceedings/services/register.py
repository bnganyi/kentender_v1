# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Procurement meetings register (OVS-CHG-001 v0.6 §11, §13; PRC-CHG-001
v0.11 §7, §9; plan D5 to D8, D17; tracker OVS6-04xx).

One read-only list of the sessions that actually started: the single
session of a Bid Opening and each discussion session of a Bid Evaluation. A
planned opening recorded Not held appears once and is not counted as held.
It adds no scheduling, agenda, quorum or meeting administration.

Who sees which row is the owner's decision, asked of each owner's adapter
(`can_read_row`), never inferred here, and every row is checked before it is
listed or counted, so a total never discloses a row the reader cannot see
(AUTH-ADR-001 v1.11 §5.4). A row never carries a session's subject, notes,
a bidder's name, a count of bids or a finding. The department is the
Tender's lead department, read at request time through the owner's case
(nothing is stored on the Proceeding); a department filter matches the lead
or any contributor, and totals group once under the lead."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.proceedings.services import attendance, owners

OPENING, EVALUATION = "Bid opening", "Bid evaluation"
TYPES = (OPENING, EVALUATION)
OWNER_TYPES = {"Bid Opening Case": OPENING, "Evaluation Case": EVALUATION}
CASE_DOCTYPE = {"Bid Opening Case": "Bid Opening Case", "Evaluation Case": "Evaluation Case"}
#: PRC-CHG-001 v0.10 §5 states, in PRC's own words; an Evaluation session is In session or Session ended (OVS plan §4.2)
HELD_NOT = ("Pending", "Not held")
INCOMPLETE_MESSAGE = "Some meeting records could not be loaded. Totals are incomplete."
PAGE_SIZE = 50


def _site_date(value) -> str:
	return get_datetime(value).strftime("%Y-%m-%d") if value else ""


def _label(value) -> str:
	from kentender_core.utils.display import display_datetime

	return display_datetime(value) if value else ""


def _present(rows: list[dict[str, Any]], *, start) -> int:
	"""Distinct people with a recorded arrival during the meeting: a pre-session
	arrival counts if still present at the start (PRC-CHG-001 v0.10 §4)."""
	people: set[str] = set()
	departed_before: set[str] = set()
	for r in rows:
		who = attendance.identity(r)
		if r["movement"] == "Departure" and start and r["occurred_at"] and get_datetime(r["occurred_at"]) < get_datetime(start):
			departed_before.add(who)
		elif r["movement"] == "Arrival" and (not r["pre_session"] or who not in departed_before):
			people.add(who)
	return len(people)


def _departments(tender: str) -> tuple[str, list[str]]:
	"""(lead, contributors besides the lead) of the Tender, as Organisation Unit codes."""
	import json

	row = frappe.db.get_value("Tender", tender, ["lead_org_unit", "contributing_org_unit_ids"], as_dict=True)
	if not row:
		return "", []
	try:
		contributing = [cstr(u) for u in json.loads(row.contributing_org_unit_ids or "[]") if u]
	except (TypeError, ValueError):
		contributing = []
	lead = cstr(row.lead_org_unit)
	return lead, [u for u in contributing if u != lead]


def _unit_name(code: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", code, "unit_name")) if code else ""


def _candidates() -> list[dict[str, Any]]:
	"""Every meeting the Proceedings hold, before any reader's verdict."""
	out: list[dict[str, Any]] = []
	for p in frappe.get_all("Proceeding", fields=["name", "owner_type", "owner_id", "proceeding_type", "state", "actual_start", "actual_end"],
			filters={"owner_type": ("in", list(OWNER_TYPES))}, order_by="creation asc"):
		kind = OWNER_TYPES[p.owner_type]
		if kind == OPENING:
			if not p.actual_start and p.state != "Not held":
				continue  # a planned opening that has not started is not a meeting yet
			out.append({"proceeding": p.name, "owner_type": p.owner_type, "owner_id": p.owner_id, "type": kind, "session": 1 if p.actual_start else 0,
				"start": p.actual_start, "end": p.actual_end, "state": p.state, "attendance_session": ""})
			continue
		for s in frappe.get_all("Proceeding Session", filters={"proceeding": p.name, "actual_start": ("is", "set")}, fields=["name", "session_number", "state", "actual_start",
				"actual_end"], order_by="session_number asc"):
			out.append({"proceeding": p.name, "owner_type": p.owner_type, "owner_id": p.owner_id, "type": kind, "session": cint(s.session_number), "start": s.actual_start,
				"end": s.actual_end, "state": "In session" if s.state == "Active" else "Session ended", "attendance_session": s.name})
	return out


def _row(c: dict[str, Any]) -> dict[str, Any]:
	"""One meeting as the register shows it: facts about the meeting, never its content."""
	case = frappe.db.get_value(c["owner_type"], c["owner_id"], ["tender", "tender_reference", "tender_title"], as_dict=True)
	if not case:
		raise frappe.DoesNotExistError("Not found")
	if c["type"] == OPENING:
		scheduled = frappe.db.get_value("Bid Opening Case", c["owner_id"], "effective_deadline")
	else:
		scheduled = None
	lead, others = _departments(case.tender)
	held = c["state"] not in HELD_NOT and bool(c["start"])
	rows = frappe.get_all("Proceeding Attendance", filters={"proceeding": c["proceeding"], **({"session": c["attendance_session"]} if c["attendance_session"] else {})},
		fields=["user", "person_name", "movement", "pre_session", "occurred_at"], order_by="occurred_at asc, creation asc") if held else []
	start, end = c["start"], c["end"]
	minutes = round((get_datetime(end) - get_datetime(start)).total_seconds() / 60) if held and start and end else None
	return {
		"proceeding": c["proceeding"], "owner_type": c["owner_type"], "owner_id": c["owner_id"], "type": c["type"], "tender": case.tender_reference, "title": case.tender_title,
		"tender_name": case.tender, "session": c["session"] or None, "state": c["state"], "held": held,
		"date": _site_date(start) or _site_date(scheduled), "date_label": _label(start) or (f"Scheduled {_label(scheduled)}" if scheduled else ""),
		"started": _label(start), "ended": _label(end), "duration_minutes": minutes, "present": _present(rows, start=start) if held else None,
		"department": lead, "department_name": _unit_name(lead) or "Department not recorded", "contributors": [_unit_name(u) or u for u in others],
		"contributor_units": others, "route": ["tenders", case.tender_reference, "opening" if c["type"] == OPENING else "evaluation"],
	}


def _page_open(user: str) -> bool:
	"""Who may open the register at all: the offices that oversee procurement, an auditor,
	a department head, a technical reader; anyone else only if some row is theirs (checked by the caller)."""
	from kentender_core.services.authorization import PURPOSE_READ, authorise_record, is_technical, permitted_ou_scopes

	if is_technical(user):
		return True
	if permitted_ou_scopes(user, "Head of User Department"):  # an OU-scoped role is held through its unit, not site-wide
		return True
	return any(authorise_record(user=user, business_role=role, purpose=PURPOSE_READ).allowed for role in ("Accounting Officer", "Head of Procurement Function", "Auditor"))


def list_meetings(*, user: str, type: str = "", department: str = "", state: str = "", date_from: str = "", date_to: str = "", query: str = "",
		start: int = 0, limit: int = PAGE_SIZE) -> dict[str, Any]:
	"""ListProcurementMeetings: rows, totals and the filters in force, for this reader."""
	adapters = owners.adapters()
	visible: list[dict[str, Any]] = []
	incomplete = False
	for c in _candidates():
		adapter = adapters.get(c["owner_type"])
		try:
			if adapter is None or not adapter.can_read_row(c["owner_id"], user):
				continue
			row = _row(c)
			# A row is meeting facts only; the owner's record applies its own rule again, so the
			# link is offered only where it opens (KT-ACCESS-REV-001 AR-07).
			opens = getattr(adapter, "can_open_record", None)
			row["record_readable"] = True if opens is None else bool(opens(c["owner_id"], user))
			visible.append(row)
		except frappe.DoesNotExistError:
			continue  # an owner record that is gone or protected is not a row
		except Exception:
			incomplete = True
			frappe.log_error(title="Procurement meetings: a row could not be loaded")
	forbidden = not visible and not _page_open(user)
	departments = {}
	for r in visible:
		for code in [r["department"], *r["contributor_units"]]:
			if code:
				departments[code] = _unit_name(code) or code

	def matches(r: dict[str, Any]) -> bool:
		if type and r["type"] != type:
			return False
		if state and r["state"] != state:
			return False
		if department and department not in [r["department"], *r["contributor_units"]]:
			return False
		if query and query.lower() not in f"{r['tender']} {r['title']}".lower():
			return False
		if date_from or date_to:
			if not r["date"] or (date_from and r["date"] < date_from) or (date_to and r["date"] > date_to):
				return False
		return True

	matched = [r for r in visible if matches(r)]
	held = [r for r in matched if r["held"]]
	by_type = {t: sum(1 for r in held if r["type"] == t) for t in TYPES}
	groups: dict[str, dict[str, Any]] = {}
	for r in matched:
		g = groups.setdefault(r["department"], {"department": r["department"], "department_name": r["department_name"], OPENING: 0, EVALUATION: 0, "total": 0})
		if r["held"]:
			g[r["type"]] += 1
			g["total"] += 1
	ordered = sorted(matched, key=lambda r: (r["date"] or "9999", r["tender"], r["type"], r["session"] or 0), reverse=True)
	page = ordered[max(0, cint(start)): max(0, cint(start)) + max(1, cint(limit))]
	return {
		"rows": page, "matched": len(matched), "held_total": len(held), "totals": {"by_type": by_type, "by_department": sorted(groups.values(), key=lambda g: g["department_name"]),
			"grouping": "Grouped by lead department"},
		"incomplete": incomplete, "incomplete_message": INCOMPLETE_MESSAGE if incomplete else "", "forbidden": forbidden,
		"filters": {"type": type, "department": department, "state": state, "from": date_from, "to": date_to, "query": query},
		"options": {"types": list(TYPES), "departments": [{"unit": k, "name": v} for k, v in sorted(departments.items(), key=lambda kv: kv[1])],
			"states": sorted({r["state"] for r in visible})}, "start": cint(start), "limit": max(1, cint(limit)),
	}
