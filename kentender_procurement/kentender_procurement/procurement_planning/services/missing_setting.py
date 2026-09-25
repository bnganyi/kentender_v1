# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.23 §10.16 — the Planning-side missing-setting panel
(C01–C04).

System setup is owned by CFG. Planning never redefines it, never copies a
partial setup form into a business page, and never grows its own registry or
approval workflow for it. What Planning owes the person in front of the blocked
action is three facts in place: which setting is missing, which action it
blocks, and whose job it is to fix.

Two rules about the control. An actor who actually holds setup access gets an
enabled route to the exact section. An actor who does not is told plainly to ask
their administrator — never shown a disabled setup control, which teaches
nothing and reads as a fault (§10.16, PLN22-AC-005).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, formatdate

from kentender_core.services.authorization import is_technical

#: §10.16 — the same responsible role in all four variants: setup is a
#: technical maintenance responsibility, not a business one.
RESPONSIBLE_ROLE = "Administrator or System Manager"

ASK_ADMINISTRATOR = "Ask your KenTender administrator to complete this setting."
OPEN_SETUP = "Open System setup"

#: The exact CFG section each setting lives in, as `SystemSetup.vue` names its
#: own tabs. A wrong anchor is worse than none: it sends a maintainer to a page
#: that does not hold the setting.
SECTION_RESPONSIBILITIES = "users-and-responsibilities"
SECTION_FISCAL_YEARS = "fiscal-years"
SECTION_PROCUREMENT_SETTINGS = "procurement-settings"

#: Why a purchase's applicable rule cannot be used. The three causes want
#: three different sentences and, for one of them, two different people: only
#: an absent rule is something to add, an ambiguous configuration is something
#: to retire, and an unmarked one already exists and only wants the flag.
#: While this was a bare boolean all three read as "the rule is not verified"
#: (found live 23 Sep 2026), which sent a maintainer to a rule that read Valid
#: in System setup when the truth was that no rule covered the purchase's date
#: at all — the rule they were looking at had been superseded.
RULE_IN_FORCE = ""
RULE_ABSENT = "absent"
RULE_AMBIGUOUS = "ambiguous"
RULE_UNMARKED = "unmarked"


def panel(
	*,
	setting: str,
	affected_action: str,
	section: str,
	affected_purchase: str = "",
	note: str = "",
	lede: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""One missing-setting panel, for placement immediately above the action
	it blocks. `lede` is C03-METHOD-MISSING's own leading sentence naming the
	exact choice that is blocked; every other variant's board carries none."""
	actor = cstr(user or frappe.session.user)
	can_open = is_technical(actor)
	return {
		"setting": setting,
		"affected_action": affected_action,
		"affected_purchase": affected_purchase,
		"responsible_role": RESPONSIBLE_ROLE,
		"note": note,
		"lede": lede,
		# Either a real route, or the sentence that names who to ask. Never a
		# control the reader cannot use.
		"can_open_setup": can_open,
		"action": OPEN_SETUP if can_open else "",
		"href": f"/app/system-setup#{section}" if can_open else "",
		"ask_text": "" if can_open else ASK_ADMINISTRATOR,
	}


def approval_authority(*, user: str | None = None) -> dict[str, Any] | None:
	"""C01-ROUTE-MISSING — nobody holds the Plan Statutory Approver
	responsibility, so the Accounting Officer's adoption has nowhere to go.

	Derived from who actually holds it, never from a Planning-local list: an
	empty result means the responsibility is genuinely unassigned (§6.5)."""
	from kentender_procurement.procurement_planning.services import planning_authorization as authz
	from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PLAN_STATUTORY_APPROVER

	if authz.users_with_site_role(ROLE_PLAN_STATUTORY_APPROVER):
		return None
	return panel(
		setting="Annual Plan approval authority",
		affected_action="Adopt and submit",
		section=SECTION_RESPONSIBILITIES,
		user=user,
	)


def dpp_submissions(*, fiscal_year: str, user: str | None = None) -> dict[str, Any] | None:
	"""C02-DPP-CLOSED — initial departmental-plan submissions are closed for
	this year.

	The panel explains the one action that is unavailable. Everything the
	department may still lawfully do — saving a Draft, correcting a returned
	submission — stays exactly where it was (§10.16)."""
	from kentender_core.services import site_configuration

	if site_configuration.get_dpp_submission_state(fiscal_year).get("open"):
		return None
	return panel(
		setting="Departmental plan submissions",
		affected_action="Submit initial departmental plan",
		section=SECTION_FISCAL_YEARS,
		note="Initial submission is blocked until this is configured. Saving a draft or correcting a returned submission still works.",
		user=user,
	)


#: How many purchases a grouped panel names before it stops listing them.
#: Enough to recognise the group, short enough to stay one readable line.
NAMED_PURCHASES = 3


def affected_purchases(rows: list[tuple[str, str]]) -> str:
	"""One phrase for the purchases a single wrong setting affects.

	A setting is wrong once, not once per purchase. Naming each one on its
	own row was tolerable at four and absurd at a hundred, where the
	administrator still has exactly one thing to fix (found live 24 Sep
	2026). `rows` is (plan_item_id, title) in plan order."""
	if len(rows) == 1:
		item_id, title = rows[0]
		return f"{title} · {item_id}" if title else item_id
	named = ", ".join(item_id for item_id, _ in rows[:NAMED_PURCHASES])
	rest = len(rows) - NAMED_PURCHASES
	return f"{len(rows)} purchases: {named}" + (f" and {rest} more" if rest > 0 else "")


def rule_panels(*, items, fiscal_year: str, user: str | None = None) -> list[dict[str, Any]]:
	"""C03-METHOD-MISSING and C04-SCHEDULE-MISSING, one panel per wrong
	setting rather than one per purchase.

	Grouped by what is actually wrong — the setting, the cause, and the
	method it was resolved for — because those are what the administrator
	acts on. A missing rule and an unmarked one want different work, so they
	stay separate; four purchases blocked by the same missing rule are one
	panel naming all four."""
	groups: dict[tuple[str, str, str], list] = {}
	for item in items:
		# One resolution per purchase, not one per rule kind: both answers
		# come from the same resolve, and this loop runs once per purchase in
		# the plan.
		for which, (reason, on) in _rule_states(item, fiscal_year).items():
			if not reason:
				continue
			key = (which, reason, cstr(item.get("procurement_method")))
			groups.setdefault(key, []).append((item, on))

	order = {"method": 0, "schedule": 1}
	panels = []
	for (which, reason, _method), members in sorted(groups.items(), key=lambda kv: order[kv[0][0]]):
		setting, action = (
			("Applicable procurement method rule", "Send plan for governance review") if which == "method"
			else ("Applicable procurement schedule", "Submit annual plan")
		)
		first_item, first_on = members[0]
		rows = [(cstr(i.get("plan_item_id")), cstr(i.get("title"))) for i, _ in members]
		panels.append({
			**panel(
				setting=setting, affected_action=action, section=SECTION_PROCUREMENT_SETTINGS,
				affected_purchase=affected_purchases(rows),
				lede=_method_lede(first_item, reason, first_on, count=len(members)) if which == "method" else "",
				note=_method_note(first_item, reason, count=len(members)) if which == "method" else "",
				user=user,
			),
			"affected_count": len(members),
		})
	return panels


def procurement_rules(*, version_name: str, fiscal_year: str, user: str | None = None) -> list[dict[str, Any]]:
	"""The plan-level rule panels, over the Version being prepared — whatever
	state its purchases are in, since a Draft purchase is exactly where the
	missing rule bites."""
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "procurement_method", "procurement_category", "baseline_invitation_date", "schedule_profile_version", "method_profile_version"],
		order_by="creation asc",
		limit_page_length=0,
	)
	return rule_panels(items=items, fiscal_year=fiscal_year, user=user)


def _rule_states(item, fiscal_year: str) -> dict[str, tuple[str, str]]:
	"""Both rule kinds for one purchase, from a single resolution."""
	from kentender_procurement.procurement_planning.services import profiles, readiness

	out: dict[str, tuple[str, str]] = {}
	resolved = None
	no_method = not cstr(item.get("procurement_method")).strip()
	for which in ("method", "schedule"):
		# A method the Planner has not chosen yet is their unfinished work,
		# not a missing setting — and the schedule rule is resolved from the
		# method, so it cannot be missing either until one is chosen (PLN
		# v1.27 D2: that purchase is a contents gap, not a C04 panel).
		if no_method:
			out[which] = (RULE_IN_FORCE, "")
			continue
		if resolved is None:
			resolved = readiness.method_profile_for(item, fiscal_year)
		on = cstr(resolved.get("applicability_date"))
		if which in resolved["unresolved"]:
			out[which] = (RULE_AMBIGUOUS, on)
		elif not resolved[which].get("found"):
			out[which] = (RULE_ABSENT, on)
		elif not profiles.is_verified(resolved[which]):
			out[which] = (RULE_UNMARKED, on)
		else:
			out[which] = (RULE_IN_FORCE, on)
	return out


def _rule_state(item, fiscal_year: str, which: str) -> tuple[str, str]:
	"""Why one rule kind for this purchase cannot be used, and the date it
	was judged on.

	A method the Planner has not chosen yet is *their* unfinished work, not a
	setting an administrator must add — claiming otherwise sends the wrong
	person to the wrong page (§10.16).

	A rule that is found but not yet marked valid counts too (found live 23
	Sep 2026): the currently active version can be `Production verification
	pending`, which only surfaced as a raw, unexplained error at the moment
	of Sign and submit."""
	return _rule_states(item, fiscal_year)[which]


def _applicable_on(item, on: str) -> str:
	"""The date the rule is judged on, with what makes it that date.

	Naming the basis is the whole point: the date is either one the Planner
	chose and can move, or a fallback they have not set yet, and the two lead
	to different work."""
	when = formatdate(on, "d MMM yyyy") if on else ""
	if not when:
		return "this purchase's applicable date"
	basis = (
		"this purchase's planned invitation date"
		if cstr(item.get("baseline_invitation_date"))
		else "the start of this purchase's financial year"
	)
	return f"{when} ({basis})"


def _method_lede(item, reason: str, on: str, *, count: int = 1) -> str:
	"""C03-METHOD-MISSING's leading sentence: the method that is blocked, the
	actual cause, and the date the rule was judged on.

	Where one wrong setting blocks several purchases the sentence speaks for
	all of them at once — naming each purchase's own date would be the same
	sentence repeated, which is what this grouping exists to stop."""
	method = cstr(item.get("procurement_method"))
	where = _applicable_on(item, on) if count == 1 else "the planned invitation dates of these purchases"
	if reason == RULE_AMBIGUOUS:
		return (
			f"More than one procurement method rule is in force for {method} on {where}, "
			"so it cannot be confirmed until one of them is retired."
		)
	if reason == RULE_UNMARKED:
		return (
			f"The {method} rule in force on {where} is not marked valid in System setup, "
			f"so {method} cannot be confirmed."
		)
	return f"No procurement method rule is in force on {where}, so {method} cannot be confirmed."


def _method_note(item, reason: str, *, count: int = 1) -> str:
	"""Only an absent rule has a second way out, and it belongs to the Planner
	reading this: the date the rule is judged on is one they set."""
	if reason != RULE_ABSENT:
		return ""
	if count > 1:
		return (
			"Either a rule covering those dates is added in System setup, or the planned invitation "
			"dates move to ones an existing rule already covers."
		)
	if cstr(item.get("baseline_invitation_date")):
		return (
			"Either a rule covering that date is added in System setup, or this purchase's planned "
			"invitation date moves to one an existing rule already covers."
		)
	return (
		"Either a rule covering that date is added in System setup, or this purchase is given a "
		"planned invitation date that an existing rule already covers."
	)


def item_procurement_rules(*, item, fiscal_year: str, user: str | None = None) -> list[dict[str, Any]]:
	"""The same two variants for one purchase's own editor, where the missing
	rule is what stops that purchase being completed."""
	label = f"{cstr(item.title)} · {cstr(item.plan_item_id)}"
	panels = []
	for which, setting, action in (
		("method", "Applicable procurement method rule", "Send plan for governance review"),
		("schedule", "Applicable procurement schedule", "Submit annual plan"),
	):
		reason, on = _rule_state(item, fiscal_year, which)
		if reason:
			# C03-METHOD-MISSING's own leading sentence names the exact choice
			# that stopped resolving — the method is always set here, since an
			# unset one exits `_rule_state` above before this runs.
			is_method = which == "method"
			panels.append(panel(
				setting=setting, affected_action=action,
				lede=_method_lede(item, reason, on) if is_method else "",
				note=_method_note(item, reason) if is_method else "",
				section=SECTION_PROCUREMENT_SETTINGS, affected_purchase=label, user=user,
			))
	return panels
