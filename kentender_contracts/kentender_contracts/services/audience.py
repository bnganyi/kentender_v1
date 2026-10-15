# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Who reads which contract, and which fields they see (CM-CHG-001 v0.8 §6.2; plan D11; tracker CM8-311; CM-AC-20, 43, 48).

An **audience** is a reader profile of the §6.2 table. A user can belong to several for one contract; each is decided separately by AUTH's role-bound resolver
(a responsibility at the unit it names), so "one role's OU never broadens another role": a user who prepares in unit A and receives in unit B reads a
unit-A contract as a preparer only. The fields a reader sees are the **union** of the field sets their matching audiences allow. Every list, count, search, tab,
task record, export and direct link goes through `readable`/`require_read`, which are filtered **before** counting and pagination, and a task is neither required
for reading nor an authority grant.

A field set names a group of fields; a read model tags each of its fields with one (`reads.py`). Withheld by design for every audience in Phase 3: `bank_full`
(full banking is granted only by an independently reviewed oversight projection, which does not exist yet) and credentials, which are no field set at all.

Facts the resolver needs about a case come from `facts_of`: the managing unit and source-allocation units arrive with the intake package that creates them.
The table below is a reading of §6.2 into field sets and is **authored (for owner review)**; the audience names, the responsibilities and the scope rules are the
specification's."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_contracts.services import authority, people
from kentender_contracts.services.errors import fail
from kentender_core.services import business_role_registry as registry
from kentender_core.services import supplier_account_contract

#: every field set a read model may use
FIELD_SETS: dict[str, str] = {
	"core": "Identity, parties, lifecycle and dates",
	"terms": "The agreement, source and commercial particulars",
	"delivery": "Arrival, custody, inspection, acceptance",
	"obligations": "Changes, issues, security, warranty, close-out",
	"money_summary": "Operational financial totals",
	"money_native": "Native invoice and payment projections and settlement",
	"finance_accounts": "Accounts and the verified beneficiary",
	"bank_full": "Full banking details (independent oversight projection only)",
	"deliberation": "Internal deliberation, staff declarations, legal advice, funding allocation",
	"history": "History and audit evidence",
	"appointments": "Inspectors, certifiers, mandates",
	"source_projection": "The permitted departmental projection of the source allocation",
	"signing_subject": "The exact signature subject and what is needed to understand it",
	"supplier_view": "What the supplier may see: agreement, supplier-visible inspection, their claims and payments, addressed issues, notices",
}
_ALL_BUT_SENSITIVE = ("core", "terms", "delivery", "obligations", "money_summary", "money_native", "history", "appointments", "source_projection", "deliberation")


@dataclass(frozen=True)
class Audience:
	key: str
	label: str  # the first column of the §6.2 table
	field_sets: frozenset[str]
	responsibilities: tuple[str, ...] = ()  # registered responsibilities, any one of which qualifies (at the managing unit where Organisation Unit)
	rule: str = ""  # how the case is matched: site | unit | unit_or_source | appointment | supplier | technical


AUDIENCES: tuple[Audience, ...] = (
	Audience("office", "AO / HOPF", frozenset(_ALL_BUT_SENSITIVE + ("signing_subject",)), ("Accounting Officer", "Head of Procurement Function"), "site"),
	Audience("preparer", "Contract preparer", frozenset(("core", "terms", "delivery", "obligations", "money_summary", "history", "appointments", "source_projection")), ("Contract preparation",), "unit"),
	Audience("coordinator", "Contract coordinator", frozenset(("core", "terms", "delivery", "obligations", "money_summary", "history", "appointments", "source_projection")), ("Contract coordination",), "unit"),
	Audience("user_department", "Head of User Department", frozenset(("core", "terms", "delivery", "obligations", "money_summary", "source_projection")), ("Head of User Department",), "unit_or_source"),
	Audience("receiver", "Receiver", frozenset(("core", "delivery", "money_summary")), ("Receiving",), "unit"),
	Audience("appointee", "Current inspector/chair/technical certifier", frozenset(("core", "terms", "delivery", "history", "appointments")), ("Contract inspection", "Technical certification"), "appointment"),
	Audience("signatory", "Entity signatory", frozenset(("core", "signing_subject", "obligations", "history")), ("Entity contract signing",), "appointment"),
	Audience("finance", "Finance maker / approver", frozenset(("core", "terms", "delivery", "obligations", "money_summary", "money_native", "finance_accounts", "history")), ("Finance preparation", "Finance approval"), "site"),
	Audience("auditor", "Auditor", frozenset(("core", "terms", "delivery", "obligations", "money_summary", "money_native", "history", "appointments")), ("Auditor",), "site"),
	Audience("technical", "Administrator / System Manager / Technical Operator", frozenset(("core", "terms", "delivery", "obligations", "money_summary", "money_native", "finance_accounts", "history", "appointments")), (), "technical"),
	Audience("supplier", "Supplier representative / signatory", frozenset(("core", "supplier_view")), (), "supplier"),
)
BY_KEY = {a.key: a for a in AUDIENCES}
#: capacity (§6.2.1) -> the responsibility that qualifies an appointee audience
APPOINTEE_CAPACITY = {"Contract inspection": ("inspector", "final acceptance representative"), "Technical certification": ("technical certifier",), "Entity contract signing": ("entity signatory",)}


@dataclass(frozen=True)
class Facts:
	"""What the resolver needs to know about one contract."""

	case: str
	managing_unit: str = ""
	source_units: tuple[str, ...] = ()
	supplier_organisation: str = ""


@dataclass(frozen=True)
class Grant:
	audience: str
	field_sets: frozenset[str] = field(default_factory=frozenset)
	evidence: dict[str, Any] = field(default_factory=dict)


def facts_of(case: str) -> Facts:
	meta = frappe.get_meta("Contract Case")
	values = frappe.db.get_value("Contract Case", case, [f for f in ("managing_unit", "supplier_organisation") if meta.has_field(f)], as_dict=True) or {}
	return Facts(case=case, managing_unit=values.get("managing_unit") or "", supplier_organisation=values.get("supplier_organisation") or "")


def _holds(user: str, role: str, unit: str, at) -> bool:
	if registry.REGISTRY[role].requires_organisation_unit and not unit:
		return False
	return people.holds(user, role, unit if registry.REGISTRY[role].requires_organisation_unit else "", at=at)


def _supplier_standing(user: str, organisation: str, at) -> bool:
	if not organisation:
		return False
	provider = supplier_account_contract.provider()
	if provider is None:
		return False
	return any(a["organisation_id"] == organisation and a.get("active") for a in provider.active_assignments(user=user, at=at))


def _reviewing(user: str, case: str) -> bool:
	"""The person is named to review a requested change on this contract and the change is still open. The appointment is what reads the contract: nobody else sees it through this audience, and it ends with the change."""
	from kentender_contracts.services import change, records

	for name in frappe.get_all("Contract Change", filters={"contract_case": case, "state": ["in", list(change.OPEN)]}, pluck="name"):
		row = frappe.get_doc("Contract Change", name)
		if any(cstr(slot.get("reviewer")).lower() == user.lower() for slot in records.loads(row.reviews_json, []) if slot.get("state") != "Superseded"):
			return True
	return False


def grants(user: str, facts: Facts, *, at=None) -> list[Grant]:
	"""Every audience this user belongs to for this contract, each with the field sets it allows."""
	if not user or user == "Guest":
		return []
	out: list[Grant] = []
	for audience in AUDIENCES:
		evidence: dict[str, Any] = {}
		if audience.rule == "technical":
			ok = people.technical(user)
		elif audience.rule == "supplier":
			ok = _supplier_standing(user, facts.supplier_organisation, at)
		elif people.technical(user):
			ok = False  # a technical account reads as the technical audience only; it holds no business capacity
		elif audience.rule == "site":
			ok = any(_holds(user, role, "", at) for role in audience.responsibilities)
		elif audience.rule == "unit":
			ok = any(_holds(user, role, facts.managing_unit, at) for role in audience.responsibilities)
		elif audience.rule == "unit_or_source":
			ok = any(_holds(user, role, unit, at) for role in audience.responsibilities for unit in (facts.managing_unit, *facts.source_units) if unit)
		elif audience.rule == "appointment":
			ok = False
			for role in audience.responsibilities:
				if not _holds(user, role, "", at):
					continue
				for capacity in APPOINTEE_CAPACITY[role]:
					found = authority.readable_binding(facts.case, user, capacity, at=at)
					if found:
						ok, evidence = True, {"capacity": capacity, **found}
						break
				if not ok and audience.key == "appointee" and _reviewing(user, facts.case):  # named by the head of procurement to review a requested change on this contract: the appointment is what reads it
					ok, evidence = True, {"capacity": "change reviewer"}
				if ok:
					break
		else:
			raise ValueError(audience.rule)
		if ok:
			out.append(Grant(audience.key, audience.field_sets, evidence))
	return out


def readable(user: str, case: str, *, at=None) -> list[Grant]:
	return grants(user, facts_of(case), at=at)


def require_read(user: str, case: str, *, at=None) -> list[Grant]:
	"""The grants that let this user read the contract, or a stable denial. The denial is for a genuinely unreadable record only; a reader who may read but not act
	is never denied here (§6.2 last paragraph)."""
	found = readable(user, case, at=at)
	if not found:
		fail("CM_AUTHORITY", denied=True, reason="You do not have access to this contract.")
	return found


def field_sets(found: list[Grant]) -> frozenset[str]:
	"""The union of what each matching audience allows."""
	return frozenset().union(*(g.field_sets for g in found)) if found else frozenset()


def assignment_units(user: str, role: str) -> list[str]:
	"""The organisation units where this user holds an enabled assignment of a unit-scoped responsibility (AUTH decides whether it is in force)."""
	return [u for u in frappe.get_all("User Responsibility Assignment", filters={"user": user, "business_role": role, "status": "Enabled"}, pluck="organisation_unit") if u]


def workspace_audiences(user: str, *, at=None) -> list[str]:
	"""Every audience this user belongs to **somewhere**: who may open the Contracts workspace at all. A contract is still read only through `grants`; an assignment
	or an appointee responsibility opens the (possibly empty) workspace but reads no contract (§6.2)."""
	if not user or user == "Guest":
		return []
	if people.technical(user):
		return ["technical"]
	found: list[str] = []
	for entry in AUDIENCES:
		if entry.rule == "technical":
			continue
		if entry.rule == "supplier":
			provider = supplier_account_contract.provider()
			if provider is not None and any(a.get("active") for a in provider.active_assignments(user=user, at=at)):
				found.append(entry.key)
			continue
		for role in entry.responsibilities:
			if registry.REGISTRY[role].requires_organisation_unit:
				ok = any(_holds(user, role, unit, at) for unit in assignment_units(user, role))
			else:
				ok = _holds(user, role, "", at)
			if ok:
				found.append(entry.key)
				break
	return found

