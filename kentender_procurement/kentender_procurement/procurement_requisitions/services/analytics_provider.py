# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1 — the Requisitions owner's feed to Procurement Analytics (fact kind `requisitions`).

Registered on the `kt_analytics_providers` hook (the contract is `kentender_core.services.analytics_contract`); core never
imports this app. Two functions answer for one actor (never the session user) and only read: nothing is created, marked,
locked or persisted, and no personal queue is mixed in (this is not `get_requisition_workspace`).

One record per Requisition root the actor may know. The facts, per ANL-M-08, ANL-M-01/02/03 and the T1/T2 inputs:

- **state** — the owner's stored state (Draft, Awaiting Department Approval, Submitted to Procurement, Authorised, Withdrawn,
  Revoked, Upstream correction required), except that a Draft that is the successor of a Version returned for correction
  (Return for correction, Return to department, Change submitting department and return) is "Returned", the state ANL-M-08
  names. `state_key` is the stored `current_state` in every case.
- **value_kind / value_lines** — the drawdown lines of the Version the state is about, `requested_value` parsed from the
  owner's Data strings to `Decimal`, one line per drawdown line attributed to its `contributing_org_unit`: REQUESTED for
  Awaiting Department Approval and Submitted to Procurement (the current Version), AUTHORISED for Authorised (the authorised
  Version). Every other state has no value total (None and no lines).
- **submitted_at** — the instant the authorised Version, else the current Version, entered Submitted to Procurement.
  **authorised_at** — the Authorise requisition decision of the authorised Version. **consumed_at** — the handoff
  consumption instant. **submission_events** — every Version of the root entering Submitted to Procurement (returned ones
  too). **authorisation_events** — every Authorise requisition decision.
- **tender_reference** — the reference of the Tender that consumed the handoff, read the way the Requisition record already
  reads it (`read.get_authorised_requisition`: the handoff's `tender`, then `Tender.tender_reference`; the Tender name when
  the Tender row cannot be read; "" when no Tender was created).
- **outstanding** — a Requisition Submitted to Procurement with the Head of Procurement Function's task open is awaiting
  authorisation, since the instant it entered Submitted to Procurement.

**Who may know a record.** Existing readers keep the owner's own scope: a Departmental Author or Head of User Department
knows every Requisition (Draft included) that a department of theirs contributes to, exactly as `requisition_authorization`
decides, and a revoked or expired assignment stops counting on the next read. ADDITIONALLY, under OD-2 (owner decision of
5 October 2026, "aggregate-only reads"), the Head of Procurement Function, Procurement Planner, Procurement Officer, Auditor,
Accounting Officer and technical readers (Administrator, System Manager, Technical Operator) know every Requisition in every
state except Draft, site-wide, as counts, values and instants only. This widens today's rule for the Accounting Officer, who
reads Authorised and Revoked Requisitions only: the widening is owner-approved, aggregate-only, and does not change what
the Accounting Officer may open (`requisition_authorization` is untouched). A Draft of someone else never appears to a
site-wide reader, and a Requisition outside a department reader's units never appears to them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import analytics_contract as ac
from kentender_core.services.authorization import PURPOSE_READ, authorise_record, is_technical, permitted_ou_scopes
from kentender_core.services.home_viewer import is_technical_reader
from kentender_procurement.procurement_requisitions.services.home_provider import _full_name, _holders, _people
from kentender_procurement.procurement_requisitions.services.requisition_roles import (
	DEPARTMENTAL_ROLES,
	OVERSIGHT_READ_ROLES,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	SITE_WIDE_ROLES,
)

PAGE = "procurement-requisitions"
ROOT, VERSION, DECISION = "Procurement Requisition", "Requisition Version", "Requisition Decision"
ROOT_FIELDS = [
	"name", "requisition_reference", "plan_id", "lead_org_unit_id", "current_state", "current_version", "authorised_version",
	"handoff_consumed_at",
]
SUBMIT, AUTHORISE = "Submit to Procurement", "Authorise requisition"
#: The decisions that send a Version back to its authors: the next Draft is a "Returned" requisition (ANL-M-08).
RETURNS = ("Return for correction", "Return to department", "Change submitting department and return")
#: ANL-M-08: requested for the two states awaiting a decision to authorise, authorised for Authorised; nothing otherwise.
VALUE_KIND = {"Awaiting Department Approval": ac.REQUESTED, "Submitted to Procurement": ac.REQUESTED, "Authorised": ac.AUTHORISED}
#: The owner's own destination rule (`read.get_requisition_workspace`): the authorised view for Authorised and Revoked.
AUTHORISED_ROUTE_STATES = ("Authorised", "Revoked")
AWAITING_AUTHORISATION = "Awaiting authorisation by {who}."


class _Audience:
	"""What the actor may know: every Requisition but a Draft (`site_wide`), and every Requisition a department of theirs
	contributes to, Draft included (`units`)."""

	def __init__(self, site_wide: bool, units: set[str]):
		self.site_wide = site_wide
		self.units = units

	def __bool__(self) -> bool:
		return self.site_wide or bool(self.units)


def _audience(user: str, at: datetime) -> _Audience:
	if not user or user == "Guest":
		return _Audience(False, set())
	site_wide = is_technical_reader(user, at) or any(
		authorise_record(user=user, business_role=role, at=at, purpose=PURPOSE_READ).allowed for role in SITE_WIDE_ROLES + OVERSIGHT_READ_ROLES
	)
	units: set[str] = set()
	if not is_technical(user):
		for role in DEPARTMENTAL_ROLES:
			units |= permitted_ou_scopes(user, role, at) or set()
	return _Audience(site_wide, units)


def applies(*, user: str, at: datetime) -> set[str]:
	"""`requisitions` for an actor who holds a Requisitions responsibility, the Accounting Officer or a technical reader."""
	return {ac.REQUISITIONS} if _audience(user, at) else set()


def _roots(audience: _Audience) -> list[Any]:
	"""The root rows the actor may know, one scan, oldest first."""
	rows: dict[str, Any] = {}
	if audience.site_wide:
		for row in frappe.get_all(ROOT, filters={"current_state": ("!=", "Draft")}, fields=ROOT_FIELDS, order_by="creation asc", limit_page_length=0):
			rows[row.name] = row
	if audience.units:
		names = frappe.get_all(
			"Requisition Contributing Unit", filters={"parenttype": ROOT, "organisation_unit": ("in", sorted(audience.units))}, pluck="parent",
			distinct=True, limit_page_length=0,
		)
		for row in frappe.get_all(ROOT, filters={"name": ("in", names or [""])}, fields=ROOT_FIELDS, order_by="creation asc", limit_page_length=0):
			rows[row.name] = row
	return sorted(rows.values(), key=lambda row: row.name)


def _by(rows: list[Any], key: str) -> dict[str, list[Any]]:
	out: dict[str, list[Any]] = {}
	for row in rows:
		out.setdefault(row[key], []).append(row)
	return out


def facts(*, user: str, kind: str, at: datetime, **params: Any) -> dict[str, Any]:
	"""The `requisitions` records the actor may know. Raises for another kind or an actor with no audience (never a zero)."""
	if kind != ac.REQUISITIONS:
		raise ValueError(f"the Requisitions provider has no fact kind {kind!r}")
	audience = _audience(user, at)
	if not audience:
		raise frappe.PermissionError("No Requisitions responsibility.")
	roots = _roots(audience)
	names = [root.name for root in roots] or [""]

	versions = frappe.get_all(VERSION, filters={"requisition": ("in", names)}, fields=["name", "requisition", "requirement_title", "submitted_at", "version_number", "based_on_version"], order_by="version_number asc", limit_page_length=0)
	version_by_name = {row.name: row for row in versions}
	versions_of = _by(versions, "requisition")
	decisions = frappe.get_all(
		DECISION, filters={"requisition_version": ("in", [v.name for v in versions] or [""]), "decision": ("in", [SUBMIT, AUTHORISE, *RETURNS])},
		fields=["requisition_version", "decision", "decided_at"], order_by="decided_at asc", limit_page_length=0,
	)
	decided: dict[tuple[str, str], list[datetime]] = {}
	returned: set[str] = set()
	for row in decisions:
		if row.decision in RETURNS:
			returned.add(row.requisition_version)
		elif row.decided_at:
			decided.setdefault((row.requisition_version, row.decision), []).append(get_datetime(row.decided_at))

	# the value lines are read only for the Version each state is about
	valued = {root.name: _valued_version(root) for root in roots}
	lines = frappe.get_all(
		"Requisition Drawdown Line", filters={"parenttype": VERSION, "parent": ("in", sorted({v for v in valued.values() if v}) or [""])},
		fields=["parent", "contributing_org_unit", "requested_value"], order_by="parent asc, idx asc", limit_page_length=0,
	)
	lines_of = _by(lines, "parent")
	units_of = _by(
		frappe.get_all("Requisition Contributing Unit", filters={"parenttype": ROOT, "parent": ("in", names)}, fields=["parent", "organisation_unit"], order_by="idx asc", limit_page_length=0),
		"parent",
	)
	years = _fiscal_years({root.plan_id for root in roots if root.plan_id})
	tenders = _tenders(names)
	waiting = {
		task.requisition_version: task for task in frappe.get_all(
			"Requisition Task", filters={"requisition": ("in", names), "status": "Open", "business_role": ROLE_HEAD_OF_PROCUREMENT_FUNCTION},
			fields=["requisition_version", "creation"], limit_page_length=0,
		)
	}
	who = ""
	if any(root.current_state == "Submitted to Procurement" for root in roots):
		who = _people([_full_name(person) for person in _holders(ROLE_HEAD_OF_PROCUREMENT_FUNCTION)], ROLE_HEAD_OF_PROCUREMENT_FUNCTION)

	records = []
	for root in roots:
		current = version_by_name.get(cstr(root.current_version))
		authorised = version_by_name.get(cstr(root.authorised_version)) if root.authorised_version else None
		state = cstr(root.current_state)
		value_kind = VALUE_KIND.get(state)
		label = "Returned" if state == "Draft" and current and cstr(current.based_on_version) in returned else state
		submitted_at = _submitted(authorised or current, decided)
		units = [cstr(root.lead_org_unit_id)] if root.lead_org_unit_id else []
		units += [row.organisation_unit for row in units_of.get(root.name, []) if row.organisation_unit not in units]
		out = None
		task = waiting.get(cstr(root.current_version)) if state == "Submitted to Procurement" else None
		if task and (submitted_at or task.creation):
			out = ac.outstanding(AWAITING_AUTHORISATION.format(who=who), who, get_datetime(submitted_at or task.creation))
		records.append(ac.record(
			ac.REQUISITIONS, id=root.name, title=cstr((current.requirement_title if current else "") or root.requisition_reference or root.name),
			reference=cstr(root.requisition_reference), fiscal_year=years.get(cstr(root.plan_id), ""), org_units=units,
			route=[PAGE, root.name, "authorised"] if state in AUTHORISED_ROUTE_STATES else [PAGE, root.name], outstanding=out,
			state=label, state_key=state, value_kind=value_kind,
			value_lines=[ac.line(row.contributing_org_unit, row.requested_value) for row in lines_of.get(valued[root.name], [])] if value_kind else [],
			submitted_at=submitted_at,
			authorised_at=max(decided.get((authorised.name, AUTHORISE), []), default=None) if authorised else None,
			consumed_at=get_datetime(root.handoff_consumed_at) if root.handoff_consumed_at else None,
			submission_events=sorted(filter(None, (_submitted(v, decided) for v in versions_of.get(root.name, [])))),
			authorisation_events=sorted(at_ for v in versions_of.get(root.name, []) for at_ in decided.get((v.name, AUTHORISE), [])),
			tender_reference=tenders.get(root.name, ""),
		))
	return ac.facts_result(records)


def _valued_version(root) -> str:
	"""The Version a value total is about: the authorised one for Authorised, the current one while a decision is awaited."""
	kind = VALUE_KIND.get(cstr(root.current_state))
	if kind == ac.AUTHORISED:
		return cstr(root.authorised_version or root.current_version)
	return cstr(root.current_version) if kind else ""


def _submitted(version, decided: dict[tuple[str, str], list[datetime]]) -> datetime | None:
	"""The instant a Version entered Submitted to Procurement: its own `submitted_at`, else the Submit to Procurement decision."""
	if not version:
		return None
	if version.submitted_at:
		return get_datetime(version.submitted_at)
	return min(decided.get((version.name, SUBMIT), []), default=None)


def _fiscal_years(plans: set[str]) -> dict[str, str]:
	if not plans or not frappe.db.exists("DocType", "Annual Plan"):
		return {}
	return {row.name: cstr(row.fiscal_year) for row in frappe.get_all("Annual Plan", filters={"name": ("in", sorted(plans))}, fields=["name", "fiscal_year"], limit_page_length=0)}


def _tenders(requisitions: list[str]) -> dict[str, str]:
	"""requisition -> the reference of the Tender created from its consumed handoff, as the record read does (published Tender
	field `tender_reference`; the Tender name when only that is reachable)."""
	handoffs = frappe.get_all(
		"Authorised Requisition Handoff", filters={"requisition": ("in", requisitions), "consumed_at": ("is", "set"), "tender": ("is", "set")},
		fields=["requisition", "tender"], order_by="consumed_at asc", limit_page_length=0,
	)
	if not handoffs:
		return {}
	references: dict[str, str] = {}
	if frappe.db.exists("DocType", "Tender"):
		references = {row.name: cstr(row.tender_reference) for row in frappe.get_all("Tender", filters={"name": ("in", sorted({h.tender for h in handoffs}))}, fields=["name", "tender_reference"], limit_page_length=0)}
	return {h.requisition: references.get(h.tender) or cstr(h.tender) for h in handoffs}
