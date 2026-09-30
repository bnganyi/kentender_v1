# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Roster terms (EVL-CHG-001 v0.4 §3 "Roster terminology"; tracker EVL4-408).

- The **current roster**: the members whose appointments have not been
  replaced or ended.
- An **eligible member**: a current member with the required declaration and
  confidentiality acceptance, no unresolved conflict and no recorded
  inability to serve.
- The **current eligible roster** is complete only when every current
  appointee is eligible and the appointment has 3–5 members.

Collective decisions require that complete roster present; report signing
requires every member of it. Former members never count, and an unavailable
or conflicted member is never silently removed to reduce participation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

APPOINTMENT = "Evaluation Appointment"
DECLARATION = "Evaluation Declaration"
UNAVAILABILITY = "Evaluation Member Unavailability"
SECRETARY = "Evaluation Secretary Appointment"
MIN_MEMBERS, MAX_MEMBERS = 3, 5
MEMBER_FIELDS = ("member_user", "full_name", "department", "designation", "capacity", "status")


def current_appointment(case: str):
	name = frappe.db.get_value(APPOINTMENT, {"evaluation_case": case, "status": "Current"}, "name")
	return frappe.get_doc(APPOINTMENT, name) if name else None


def current_members(case: str) -> list[dict[str, Any]]:
	doc = current_appointment(case)
	return [{f: m.get(f) for f in MEMBER_FIELDS} for m in (doc.members if doc else []) if m.status == "Current"]


def member_users(case: str) -> list[str]:
	return [m["member_user"] for m in current_members(case)]


def chair(case: str) -> str | None:
	return next((m["member_user"] for m in current_members(case) if m["capacity"] == "Chair"), None)


def secretary(case: str) -> str | None:
	return frappe.db.get_value(SECRETARY, {"evaluation_case": case, "status": "Current"}, "secretary_user")


def declaration(case: str, user: str) -> dict[str, Any] | None:
	return frappe.db.get_value(DECLARATION, {"evaluation_case": case, "member_user": user, "status": "Current"},
		["declaration_id", "choice", "conflict_description", "confidentiality_accepted", "declared_at"], as_dict=True)


def unavailable(case: str, user: str) -> dict[str, Any] | None:
	return frappe.db.get_value(UNAVAILABILITY, {"evaluation_case": case, "member_user": user, "status": "Open"}, ["unavailability_id", "reason", "recorded_at"],
		as_dict=True)


def status(case: str, user: str) -> dict[str, Any]:
	"""One person's standing on this evaluation, with every reason they are not eligible."""
	member = user in member_users(case)
	decl = declaration(case, user) if member else None
	conflict = bool(decl and decl.choice == "Declare a conflict")
	away = unavailable(case, user) if member else None
	reasons = []
	if member and not decl:
		reasons.append("declaration_required")
	if conflict:
		reasons.append("declared_conflict")
	if away:
		reasons.append("unable_to_serve")
	return {"member": member, "declared": bool(decl) and not conflict, "conflict": conflict, "unavailable": bool(away), "eligible": member and not reasons,
		"reasons": reasons, "declaration": decl}


def eligible_members(case: str) -> list[str]:
	return [u for u in member_users(case) if status(case, u)["eligible"]]


def complete(case: str) -> dict[str, Any]:
	"""Whether the current eligible roster is complete, with who is holding it up and why."""
	members = member_users(case)
	pending = [{"user": u, "reasons": status(case, u)["reasons"]} for u in members if not status(case, u)["eligible"]]
	size_ok = MIN_MEMBERS <= len(members) <= MAX_MEMBERS
	return {"complete": bool(members) and size_ok and not pending, "members": members, "pending": pending, "size_ok": size_ok}


def prc_roster(case: str) -> list[dict[str, Any]]:
	"""The roster as Proceedings records it (attributed history; no authority)."""
	doc = current_appointment(case)
	return [{"member_user": m["member_user"], "full_name": m["full_name"], "designation": cstr(m["designation"]) or cstr(m["department"]),
		"committee_capacity": m["capacity"], "appointment_reference": cstr(doc.appointment_reference)} for m in current_members(case)] if doc else []
