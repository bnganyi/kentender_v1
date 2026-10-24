# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The checks every consequential command makes before it acts, in one place so they are made the same way (CM-CHG-001 v0.8 sections 5.17, 6, 7, 19.3).

* `profile` -- the code-owned rule profile the case runs under (the synthetic one exists only on a simulation site; anywhere else the production profile applies, which is Draft);
* `rules` -- the rules and legal questions that govern a command, as one set of `CM_RULE` / `CM_HOLD` reasons;
* `holds` -- the open holds that block a consequence, naming every one;
* `lifecycle` -- the case must be in a state the command applies to, else `CM_CHANGED` (the record moved on; reload).
Reasons are collected with `Guards` and raised once, so a person sees everything that stops them."""

from __future__ import annotations

from typing import Iterable

import frappe

from kentender_contracts.rules import gate
from kentender_contracts.rules import profile as profiles
from kentender_contracts.services import holds as hold_rules
from kentender_contracts.services import people, simulation
from kentender_contracts.services.errors import Guards, fail

PRODUCTION_BRANCH = "production_execution_of_form_no_4"


def profile(case_doc) -> profiles.Profile:
	found = profiles.PROFILES.get(case_doc.legal_profile or "")
	if found is None or (found.synthetic and not simulation.enabled()):
		return profiles.PRODUCTION
	return found


def rules(case_doc, command: str, branches: Iterable[str] = ()) -> Guards:
	return gate.reasons(command, profile(case_doc), set(branches))


def holds(guards: Guards, case: str, capability: str, subject: str | None = None, *, except_keys: Iterable[str] = ()) -> Guards:
	skip = set(except_keys)
	for hold in hold_rules.blocking(case, capability, subject):
		if hold.key in skip:
			continue
		guards.add("CM_HOLD", hold=hold.key, kind=hold.kind, reason=hold.reason, holder=hold.owner, clears_with=hold.clearing, scope=list(hold.scope), consequence=capability)
	return guards


def lifecycle(case_doc, *allowed: str) -> None:
	if case_doc.lifecycle not in allowed:
		fail("CM_CHANGED", lifecycle=case_doc.lifecycle, expected=list(allowed))


def exists(case: str) -> None:
	if not case or not frappe.db.exists("Contract Case", case):
		raise frappe.DoesNotExistError("Not found")


def acts_as_preparer(user: str, unit: str) -> None:
	"""The head of procurement, or a person whose Contract preparation responsibility covers the managing unit (CM v0.8 section 5.3: the effective binding must include this work)."""
	from kentender_contracts.services import authority

	if people.holds(user, "Head of Procurement Function"):
		return
	authority.require(user, "Contract preparation", organisation_unit=unit)
