# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Guards every Award command applies (AWD-CHG-001 v0.4 §6, §7): the
actor's active responsibility is rechecked at each action, never just at page
load; a person with no Award responsibility gets exactly the answer a missing
record gets; stage, cycle and holds are checked on the server."""

from __future__ import annotations

import frappe
from frappe.utils import cint

from kentender_procurement.award.services import checks, issues, people, state
from kentender_procurement.award.services.errors import Guards, fail

INTERNAL_READERS = (people.HEAD_OF_PROCUREMENT, people.ACCOUNTING_OFFICER, people.AUDITOR)


def can_read(user: str) -> bool:
	return any(people.holds(user, role) for role in INTERNAL_READERS)


def require_reader(user: str) -> None:
	if not can_read(user):
		raise frappe.DoesNotExistError("Not found")


def require(user: str, role: str) -> None:
	if people.holds(user, role):
		return
	if can_read(user):
		fail("AWD_AUTHORITY_REQUIRED", {"holder": role})
	raise frappe.DoesNotExistError("Not found")


def require_hop(user: str) -> None:
	require(user, people.HEAD_OF_PROCUREMENT)


def require_ao(user: str) -> None:
	require(user, people.ACCOUNTING_OFFICER)


def _segregated(holder: str, reason: str) -> None:
	"""Owner decision 6 Oct 2026 (D2) and default for open question Q3: whoever
	prepared or signed the professional opinion for a case does not record its
	award decision, and whoever recorded the decision does not prepare or sign
	the opinion. Evaluated on the actions actually taken in this case."""
	fail("AWD_AUTHORITY_REQUIRED", {"holder": holder, "reason": "segregation_of_duties", "explanation": reason})


def ao_is_opinion_author(user: str, doc) -> bool:
	return any(user in (o.author, o.signed_by) for o in frappe.get_all(state.OPINION, filters={"award_case": doc.name}, fields=["author", "signed_by"]))


def hop_is_decider(user: str, doc) -> bool:
	return bool(frappe.db.exists(state.DECISION, {"award_case": doc.name, "decided_by": user}))


def require_ao_not_opinion_author(user: str, doc) -> None:
	if ao_is_opinion_author(user, doc):
		_segregated(people.ACCOUNTING_OFFICER, "The person who prepared or signed the professional opinion cannot record the award decision.")


def require_hop_not_decider(user: str, doc) -> None:
	if hop_is_decider(user, doc):
		_segregated(people.HEAD_OF_PROCUREMENT, "The person who recorded the award decision cannot prepare or sign the professional opinion.")


def open_case(doc, g: Guards | None = None) -> Guards:
	g = g or Guards()
	if doc.cancelled:
		g.add("AWD_ON_HOLD", reason="This tender was cancelled. Award ended.")
	elif doc.stage == "Closed":
		g.add("AWD_RECORD_CHANGED", reason="closed")
	return g


def stage(doc, *allowed: str) -> None:
	if doc.stage not in allowed:
		fail("AWD_RECORD_CHANGED", {"reason": "stage", "stage": doc.stage})


def positive(doc, g: Guards | None = None) -> Guards:
	"""Everything that stops a positive advance (award, issue, delivery): holds,
	unverified rules, expired validity, unavailable status — all together."""
	g = g or Guards()
	for issue in issues.holding(doc):
		if issue.subtype == checks.RULES_UNVERIFIED:
			g.add("AWD_RULE_UNVERIFIED", issue=issue.name)
		elif issue.subtype == checks.VALIDITY_EXPIRED:
			g.add("AWD_VALIDITY_EXPIRED", issue=issue.name, reason=issue.reason)
		elif issue.subtype == checks.STATUS_UNAVAILABLE:
			g.add("AWD_STATUS_UNAVAILABLE", issue=issue.name)
		elif issue.subtype == checks.SOURCE_INCOMPLETE:
			g.add("AWD_SOURCE_INCOMPLETE", issue=issue.name, reason=issue.reason)
		else:
			g.add("AWD_ON_HOLD", issue=issue.name, title=issue.title, owner=people.full_name(issue.owner_user) if issue.owner_user else issue.owner_role)
	return g


def funding(doc, g: Guards | None = None) -> Guards:
	"""Funding read from Budget at this moment (AWD §5.1, §5.5, AWD-IF-07). An
	unreadable position and an established shortfall are different facts, and
	neither permits an unsupported positive step."""
	g = g if g is not None else Guards()  # an empty Guards is falsy
	f = checks.funding(doc)
	if not f["known"]:
		g.add("AWD_STATUS_UNAVAILABLE", check="funding", reason="Budget could not confirm the funding for this award.")
	elif f["restricted"]:
		g.add("AWD_ON_HOLD", check="funding", reason="The funding Budget now holds for this tender is less than the evaluated amount.", shortfall=f["detail"]["shortfall"])
	return g


def cycle_ready(doc) -> None:
	c = state.cycle(doc)
	if c and cint(c.awaiting_report):
		fail("AWD_RECORD_CHANGED", {"reason": "awaiting_corrected_report"})
