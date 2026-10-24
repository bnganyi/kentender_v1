# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Which rules and legal questions stop a consequential command, and why (CM-CHG-001 v0.8 §4.1, §5.17, §19.3, §19.7; CM-AC-36, CM-AC-71).

A command that is a rule's consequential action asks here before it acts. A rule whose profile is not Verified refuses it with `CM_RULE`
("The applicable requirement has not been confirmed"). An open legal question holds only the **branch** of the command it names (the early
total-price increase, a security exemption, an automatic deduction, production execution of Form No. 4, a publication deadline), reported by
the command as the branch it is taking; it refuses with `CM_HOLD` naming the question, its holder and what answers it. Every applicable reason
is returned together. Nothing a user edits (a percentage, an illustration, a label) can turn a hold into a pass: the profile is code-owned and
the synthetic one is not available on a live site. Factual and protective recording is not a consequential action and never asks."""

from __future__ import annotations

from kentender_contracts.rules import profile as profiles
from kentender_contracts.rules import register
from kentender_contracts.services import simulation
from kentender_contracts.services.errors import Guards

OWNER = "Legal/procurement owner"


def available(profile: profiles.Profile) -> profiles.Profile:
	"""The synthetic profile exists only on a simulation site."""
	if profile.synthetic and not simulation.enabled():
		raise PermissionError("The illustrative test terms are not available on this site.")
	return profile


def reasons(command: str, profile: profiles.Profile, branches: frozenset[str] | set[str] = frozenset()) -> Guards:
	available(profile)
	guards = Guards()
	for rule in register.governing(command):
		status = profile.rule_status(rule.id)
		if status != profiles.VERIFIED:
			guards.add("CM_RULE", rule=rule.id, name=rule.name, hold_key=rule.hold_key, profile=profile.id, profile_status=status, holder=OWNER, consequence=command)
	for question in register.QUESTIONS:
		if question.id in profile.resolved_questions:
			continue
		for held_command, branch in question.holds:
			if held_command == command and branch in branches:
				guards.add("CM_HOLD", hold=question.hold_key, kind="Legal question", question=question.id, branch=branch, holder=question.reviewer,
					clears_with="The reviewer's recorded answer for this deployment", consequence=command)
	return guards


def require(command: str, profile: profiles.Profile, branches: frozenset[str] | set[str] = frozenset()) -> None:
	reasons(command, profile, branches).raise_if_any()
