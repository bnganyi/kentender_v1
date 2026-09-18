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
from frappe.utils import cstr

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


def panel(
	*,
	setting: str,
	affected_action: str,
	section: str,
	affected_purchase: str = "",
	note: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""One missing-setting panel, for placement immediately above the action
	it blocks."""
	actor = cstr(user or frappe.session.user)
	can_open = is_technical(actor)
	return {
		"setting": setting,
		"affected_action": affected_action,
		"affected_purchase": affected_purchase,
		"responsible_role": RESPONSIBLE_ROLE,
		"note": note,
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
		note="Saving a draft and correcting a returned submission are unaffected.",
		user=user,
	)


def procurement_rules(*, version_name: str, fiscal_year: str, user: str | None = None) -> list[dict[str, Any]]:
	"""C03-METHOD-MISSING and C04-SCHEDULE-MISSING — the purchases whose
	applicable rule is not in force.

	Each missing rule names its own purchase, because the maintainer has to
	know which one to configure for; a plan-level "a rule is missing" tells
	them nothing they can act on."""
	from kentender_procurement.procurement_planning.services import readiness

	method: list[str] = []
	schedule: list[str] = []
	for item in frappe.get_all(
		"Annual Plan Item",
		# The Version being prepared, whatever state its purchases are in: a
		# Draft purchase is exactly where the missing rule bites.
		filters={"plan_version": version_name, "item_state": ("!=", "Dissolved")},
		fields=["name", "plan_item_id", "title", "procurement_method", "procurement_category", "schedule_profile_version", "method_profile_version"],
		order_by="creation asc",
		limit_page_length=0,
	):
		label = f"{cstr(item.title)} · {cstr(item.plan_item_id)}"
		for setting, purchases in zip(("method", "schedule"), (method, schedule)):
			if _rule_unresolved(item, fiscal_year, setting):
				purchases.append(label)

	panels = []
	for purchases, setting, action in (
		(method, "Applicable procurement method rule", "Send plan for governance review"),
		(schedule, "Applicable procurement schedule", "Submit annual plan"),
	):
		for purchase in purchases:
			panels.append(
				panel(
					setting=setting, affected_action=action, section=SECTION_PROCUREMENT_SETTINGS,
					affected_purchase=purchase, user=user,
				)
			)
	return panels


def _rule_unresolved(item, fiscal_year: str, which: str) -> bool:
	"""Whether the applicable rule for this purchase is genuinely absent.

	A method the Planner has not chosen yet is *their* unfinished work, not a
	setting an administrator must add — claiming otherwise sends the wrong
	person to the wrong page (§10.16)."""
	from kentender_procurement.procurement_planning.services import readiness

	if which == "method" and not cstr(item.get("procurement_method")).strip():
		return False
	resolved = readiness.method_profile_for(item, fiscal_year)
	return which in resolved["unresolved"] or not resolved[which].get("found")


def item_procurement_rules(*, item, fiscal_year: str, user: str | None = None) -> list[dict[str, Any]]:
	"""The same two variants for one purchase's own editor, where the missing
	rule is what stops that purchase being completed."""
	label = f"{cstr(item.title)} · {cstr(item.plan_item_id)}"
	panels = []
	for which, setting, action in (
		("method", "Applicable procurement method rule", "Send plan for governance review"),
		("schedule", "Applicable procurement schedule", "Submit annual plan"),
	):
		if _rule_unresolved(item, fiscal_year, which):
			panels.append(panel(
				setting=setting, affected_action=action,
				section=SECTION_PROCUREMENT_SETTINGS, affected_purchase=label, user=user,
			))
	return panels
