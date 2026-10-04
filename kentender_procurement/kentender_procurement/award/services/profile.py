# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The legal/operating profile (AWD-CHG-001 v0.4 §5.5, §15; plan D8).

Clocks, channels, what counts as giving a notice, the audience treatment and
the revised-notice treatment come from one versioned profile; business users
cannot relax it per tender. The only profile on this bench is the simulation
test profile — its terms reproduce the §13 fixture (reply by the seventh day
at 17:00; contracting no earlier than fourteen days after giving, at the next
09:00) and are not a claim about statutory day-counting. Without a verified
profile no positive advance is allowed (AWD_RULE_UNVERIFIED, V15)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.award.services import simulation

SETTINGS = "Award Settings"
TEST_PROFILE = {
	"profile_id": "AWD-TEST-PROFILE", "profile_version": "test-1", "verified": 1, "simulation_only": 1, "reviewer": "Simulation test profile (no legal review)",
	"reviewed_on": "", "reply_days": 7, "reply_time": "17:00", "minimum_wait_days": 14, "earliest_time": "09:00", "timezone": "Africa/Nairobi (EAT)",
	"calendar": "Calendar days; no holiday treatment (test profile)", "channels": "Portal, Email",
	"giving_rule": "Test profile: a notice is given when the email channel records delivery evidence from the test mailbox; portal publication alone is not giving.",
	"audience_rule": "Test profile: every organisation whose final sealed submission was Submitted receives one notice; withdrawn submissions receive none; a replaced submission is notified once, for its final version.",
	"debrief_rule": "Test profile: an explanation request does not extend the waiting period; an open request does not block Contracting delivery.",
	"revised_notice_treatment": "Verified",
}


def current() -> dict[str, Any]:
	doc = frappe.get_single(SETTINGS)
	values = {k: doc.get(k) for k in TEST_PROFILE}
	values.update(contracting_owner=cstr(doc.get("contracting_owner")), technical_operator=cstr(doc.get("technical_operator")))
	return values


def verified() -> bool:
	"""Only a verified profile allows positive progress; a simulation-only
	profile counts only on a test environment, and the test switch can
	withdraw it (V15)."""
	p = current()
	if not cint(p.get("verified")) or not cstr(p.get("profile_id")):
		return False
	if cint(p.get("simulation_only")) and not simulation.enabled():
		return False
	return not simulation.flag("rule_unverified")


def revised_treatment_verified() -> bool:
	return verified() and cstr(current().get("revised_notice_treatment")) == "Verified" and not simulation.flag("revised_treatment_unverified")


def install_test_profile(*, contracting_owner: str = "", technical_operator: str = "") -> dict[str, Any]:
	if not simulation.enabled():
		raise frappe.PermissionError("The Award test profile is available on a test environment only.")
	doc = frappe.get_single(SETTINGS)
	for k, v in TEST_PROFILE.items():
		doc.set(k, v)
	if contracting_owner:
		doc.contracting_owner = contracting_owner
	if technical_operator:
		doc.technical_operator = technical_operator
	doc.save(ignore_permissions=True)
	return current()


def _at_time(day: datetime, hhmm: str) -> datetime:
	h, m = (int(x) for x in (cstr(hhmm) or "00:00").split(":")[:2])
	return day.replace(hour=h, minute=m, second=0, microsecond=0)


def reply_deadline(issued_at) -> tuple[datetime, str]:
	p = current()
	base = get_datetime(issued_at) + timedelta(days=cint(p.get("reply_days")))
	deadline = _at_time(base, p.get("reply_time"))
	return deadline, f"{cint(p.get('reply_days'))} calendar days after issue, at {p.get('reply_time')} ({p.get('timezone')})"


def earliest_permitted(given_at) -> tuple[datetime, str]:
	"""Minimum wait after giving: the minimum period, then the next
	`earliest_time` at or after it."""
	p = current()
	floor = get_datetime(given_at) + timedelta(days=cint(p.get("minimum_wait_days")))
	candidate = _at_time(floor, p.get("earliest_time"))
	if candidate < floor:
		candidate += timedelta(days=1)
	return candidate, f"{cint(p.get('minimum_wait_days'))} calendar days after the notice was given, then the next {p.get('earliest_time')} ({p.get('timezone')})"
