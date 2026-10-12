# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Same-tender separation on the evaluation panel (owner decision 7 Oct 2026; RG-15,
AUD-AWD-001; EVL-CHG-001 §3 amendment logged in the document follow-ups).

Evaluators assess and recommend; the secretary manages the proceedings; the Head of
Procurement issues the professional opinion; the Accounting Officer decides the award.
So, for one tender's evaluation:

* the Accounting Officer may not be on the panel at all (member, chair or secretary);
* the Head of Procurement may be the secretary but not a member or chair.

The rule is applied when someone is appointed or replaced (`panel_refusal`) and again at
every command a panel member or secretary runs (`require_standing`, called by the command
envelope), so a person appointed earlier who later holds the other office is refused. It
reads the person's active responsibilities at any scope: a department-scoped office is
still the office. Refusals are the closed `EVL_MEMBER_INELIGIBLE` code with a `reason`."""

from __future__ import annotations

from kentender_procurement.bid_evaluation.services import people, roster
from kentender_procurement.bid_evaluation.services.errors import fail

REASON_ACCOUNTING_OFFICER = "accounting_officer"
REASON_HEAD_OF_PROCUREMENT = "head_of_procurement"
#: Commands the offices run in office, not as a panel member: the remedy for a roster that breaks the rule.
OFFICE_COMMANDS = frozenset({"AppointEvaluationCommittee", "ReplaceEvaluationMember", "DelegateEvaluationSecretary"})


def panel_refusal(user: str, *, as_member: bool, as_secretary: bool = False) -> str | None:
	"""Why `user` may not hold the panel capacity, or None."""
	held = people.active_responsibilities(user)
	if (as_member or as_secretary) and people.ACCOUNTING_OFFICER in held:
		return REASON_ACCOUNTING_OFFICER
	if as_member and people.HEAD_OF_PROCUREMENT in held:
		return REASON_HEAD_OF_PROCUREMENT
	return None


def require_standing(case: str | None, actor: str, command: str = "") -> None:
	"""Refuse a command from a panel member or secretary who now holds an office they may not combine with it."""
	if not case or not actor or actor == "system" or command in OFFICE_COMMANDS:
		return
	member, secretary = actor in roster.member_users(case), actor == roster.secretary(case)
	if not (member or secretary):
		return
	reason = panel_refusal(actor, as_member=member, as_secretary=secretary)
	if reason:
		fail("EVL_MEMBER_INELIGIBLE", {"reason": reason, "person": actor})
