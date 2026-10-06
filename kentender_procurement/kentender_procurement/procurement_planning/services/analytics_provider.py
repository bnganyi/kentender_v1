# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §4, §4A.1, §4A.2, §7.1 — the Procurement Planning owner's feed to Procurement Analytics (fact kinds
`departmental_plans` and `plan_items`).

Registered on the `kt_analytics_providers` hook; core never imports this app. Two functions answer for one actor (never the session
user) and only read. `facts` never calls `dpp_read.get_departmental_plan` (it refreshes draft entries, which writes) or any
workspace read; it reads rows through the module's own scope helpers (`planning_authorization.dpp_read_profile`, `can_read_site`)
and creates, marks and persists nothing.

**departmental_plans** — one record per Departmental Plan root that has an accepted submission (the accepted version stays in
force while an update is being prepared). `state` is "Accepted". `accepted_at` is `decided_at` of the Departmental Plan Validation
Decision "Accept departmental plan" on the ACCEPTED version's own submission; if that submission carries several accept decisions
(it should not), the LATEST is used. A candidate or returned later version never changes it. Route: the owner's
`departmental-procurement-plan/<dpp_reference>` (the same route Planning's workspace and Home feed use; Planning exposes no
route to an individual submission).

**plan_items** — one record per stable Plan Item in the exact operative ACTIVE Annual Plan Version of each Annual Plan root
(`Annual Plan.active_version`; candidate and superseded versions are never counted, and a plan with no Active Version yields no
record). `planned_value` is the sum of the item's Active `Plan Source Allocation.indicative_amount`. `allocations` has one
`{org_unit, planned, covered}` per source department, largest planned share first (Planning records no lead department, so the
lead is the largest share). `covered` is the U14 basis (decision D6, FU-ANL-02a): the Active `Plan Drawdown Reference` amounts an
authorised Requisition drew, attributed to the source department of the drawn allocation (never `Proceeding Coverage`, which
exists only once an invitation is published); a Reversed drawdown covers nothing. `has_proceeding` is True when any department's
covered amount is above zero, i.e. an authorised Requisition exists, whether or not its Tender has been published.
`invitation_days` is Planning's Baseline lateness for the invitation milestone (`actuals.baseline_lateness_days`: actual invitation
date minus the baseline invitation date of the exact Plan Version that proceeding covers; positive is later) from the current,
non-superseded `Milestone Actual Event`; None when no invitation actual is recorded. When an item has several proceedings with an
invitation actual, the earliest actual invitation is the item's value and every proceeding is listed in the extra field
`invitation_actuals` ([{proceeding_id, days}]). `plan_title` is `Annual Plan.title`; `plan_version` the Active Version number.
Route: the owner's `procurement-plan-item/<plan_item_id>`.

Audience (decision OD-2, FU-ANL-02): existing readers keep their scope. Departmental plans: Head of User Department and Departmental
Author for their units, Procurement Planner and Auditor (`dpp_read_profile`), technical readers; additionally the Head of Procurement
Function and Accounting Officer. Plan items: the Planning site-wide readers (`PLAN_READERS`) and technical readers. The Head of
Procurement Function, Accounting Officer, Auditor and technical readers get the site-wide aggregate of both kinds.

OD-2 department view of plan items: a Head of User Department who is not also a site-wide reader gets `plan_items` limited to
their permitted units (`permitted_ou_scopes`, descendants included). A record appears only for an item with an Active allocation whose
source department is in those units. Its `planned_value` stays the item's WHOLE planned value (core prints "<department> share of
<whole>"), but `allocations` and `org_units` carry only the in-scope departments: no other department's allocation, covered amount
or identity leaves the provider. Planning records no lead department, so no out-of-scope "lead" is added. The Departmental Author
has no plan-item read (departmental plans only).

Returns an empty set from `applies` where Planning does not apply to the actor; a failed read raises.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_core.services import analytics_contract as ac
from kentender_core.services.authorization import PURPOSE_READ, authorise_record, permitted_ou_scopes
from kentender_core.services.home_viewer import is_technical_reader
from kentender_procurement.procurement_planning.services import actuals
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.plan_read import PLAN_READERS
from kentender_procurement.procurement_planning.services.planning_roles import (
	DEPARTMENTAL_ROLES,
	ROLE_ACCOUNTING_OFFICER,
	ROLE_AUDITOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_PLANNER,
)

DPP_PAGE = "departmental-procurement-plan"
PLAN_ITEM_PAGE = "procurement-plan-item"
ACCEPT = "Accept departmental plan"
INVITATION = "invitation"

#: OD-2: the site-wide aggregate audience beyond each kind's existing readers (technical readers are added in `_aggregate_reader`).
AGGREGATE_ROLES = (ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_ACCOUNTING_OFFICER, ROLE_AUDITOR)


def _site(user: str, role: str, at: datetime) -> bool:
	return authorise_record(user=user, business_role=role, organisation_unit="", at=at, purpose=PURPOSE_READ).allowed


def _aggregate_reader(user: str, at: datetime) -> bool:
	"""A technical reader, the Head of Procurement Function, the Accounting Officer or an Auditor: site-wide, aggregate."""
	return is_technical_reader(user, at) or any(_site(user, role, at) for role in AGGREGATE_ROLES)


def _plan_reader(user: str, at: datetime) -> bool:
	"""Annual Plan items: a Planning site-wide reader (the owner's `PLAN_READERS`) or a technical reader."""
	return is_technical_reader(user, at) or any(_site(user, role, at) for role in PLAN_READERS)


def _hod_units(user: str, at: datetime) -> set[str]:
	"""The units a Head of User Department may see plan items for (descendants included); empty without that responsibility."""
	return permitted_ou_scopes(user, ROLE_HEAD_OF_USER_DEPARTMENT, at) or set()


def _dpp_reader(user: str, at: datetime) -> bool:
	"""Departmental plans: any aggregate reader, the Planner, or a departmental responsibility with a scope."""
	if _aggregate_reader(user, at) or _site(user, ROLE_PROCUREMENT_PLANNER, at):
		return True
	return any(permitted_ou_scopes(user, role, at) for role in DEPARTMENTAL_ROLES)


def applies(*, user: str, at: datetime) -> set[str]:
	"""The kinds this actor may read from Planning (a cheap role check, no plan is read)."""
	if not user or user == "Guest":
		return set()
	kinds: set[str] = set()
	if _dpp_reader(user, at):
		kinds.add(ac.DEPARTMENTAL_PLANS)
	if _plan_reader(user, at) or _hod_units(user, at):
		kinds.add(ac.PLAN_ITEMS)
	return kinds


# --------------------------------------------------------------------------
# departmental plans
# --------------------------------------------------------------------------


def _accepted_decisions(submissions: list[str]) -> dict[str, datetime]:
	"""submission -> `decided_at` of its latest "Accept departmental plan" decision."""
	if not submissions:
		return {}
	out: dict[str, datetime] = {}
	for row in frappe.get_all(
		"Departmental Plan Validation Decision", filters={"submission": ("in", submissions), "decision": ACCEPT},
		fields=["submission", "decided_at"], limit_page_length=0,
	):
		if not row.decided_at:
			continue
		at = get_datetime(row.decided_at)
		if row.submission not in out or at > out[row.submission]:
			out[row.submission] = at
	return out


def _unit_names(units: set[str]) -> dict[str, str]:
	if not units:
		return {}
	return {
		row.name: cstr(row.unit_name or row.name)
		for row in frappe.get_all("Organisation Unit", filters={"name": ("in", sorted(units))}, fields=["name", "unit_name"], limit_page_length=0)
	}


def _departmental_plans(user: str, at: datetime) -> list[dict[str, Any]]:
	roots = frappe.get_all(
		"Departmental Plan", filters={"current_accepted_version": ("is", "set")},
		fields=["name", "dpp_reference", "organisation_unit", "fiscal_year", "current_accepted_version"], order_by="creation asc", limit_page_length=0,
	)
	if not _aggregate_reader(user, at):
		roots = [root for root in roots if authz.dpp_read_profile(cstr(root.organisation_unit), user)]
	submission_of = {
		row.name: cstr(row.submission)
		for row in frappe.get_all("Departmental Plan Version", filters={"name": ("in", sorted({cstr(r.current_accepted_version) for r in roots}) or [""])}, fields=["name", "submission"], limit_page_length=0)
	}
	accepted = _accepted_decisions([submission for submission in submission_of.values() if submission])
	units = _unit_names({cstr(root.organisation_unit) for root in roots})
	records = []
	for root in roots:
		unit = cstr(root.organisation_unit)
		records.append(ac.record(
			ac.DEPARTMENTAL_PLANS, id=root.name, title=f"{units.get(unit, unit)} departmental plan", reference=cstr(root.dpp_reference),
			fiscal_year=cstr(root.fiscal_year), org_units=[unit] if unit else [], route=[DPP_PAGE, cstr(root.dpp_reference)],
			state="Accepted", accepted_at=accepted.get(submission_of.get(cstr(root.current_accepted_version), "")),
		))
	return records


# --------------------------------------------------------------------------
# plan items
# --------------------------------------------------------------------------


def _decimal(value: Any) -> Decimal:
	return ac.money(0 if value is None else value)


def _covered_by_unit(item_ids: list[str]) -> dict[str, dict[str, Decimal]]:
	"""plan_item_id -> source department -> the amount authorised Requisitions drew down (Active drawdowns only; the U14 basis)."""
	rows = frappe.get_all(
		"Plan Drawdown Reference", filters={"plan_item_id": ("in", item_ids), "drawdown_state": "Active"},
		fields=["name", "plan_item_id", "allocation", "requesting_org_unit", "amount"], limit_page_length=0,
	)
	allocations = {
		row.name: cstr(row.organisation_unit)
		for row in frappe.get_all("Plan Source Allocation", filters={"name": ("in", sorted({cstr(r.allocation) for r in rows if r.allocation}) or [""])}, fields=["name", "organisation_unit"], limit_page_length=0)
	}
	out: dict[str, dict[str, Decimal]] = {}
	for row in rows:
		unit = allocations.get(cstr(row.allocation)) or cstr(row.requesting_org_unit)
		if not unit:
			raise ValueError(f"Plan drawdown {row.name} names no source department")
		by_unit = out.setdefault(cstr(row.plan_item_id), {})
		by_unit[unit] = by_unit.get(unit, Decimal(0)) + _decimal(row.amount)
	return out


def _invitation_actuals(item_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
	"""plan_item_id -> its invitation actuals, one per proceeding, earliest actual first: {proceeding_id, actual, days}.

	`days` is Planning's Baseline lateness (`actuals.baseline_lateness_days`) against the baseline invitation date of the exact
	Plan Version the event was recorded against; None where that version holds no baseline."""
	pairs = {
		(cstr(row.plan_item_id), cstr(row.proceeding_id))
		for row in frappe.get_all("Milestone Actual Event", filters={"plan_item_id": ("in", item_ids), "milestone": INVITATION}, fields=["plan_item_id", "proceeding_id"], limit_page_length=0)
	}
	out: dict[str, list[dict[str, Any]]] = {}
	for item_id, proceeding in sorted(pairs):
		event = actuals.proceeding_events(item_id, proceeding).get(INVITATION)
		if not event or not event.actual_date:
			continue
		version = frappe.db.get_value("Milestone Actual Event", event.name, "plan_version")
		baseline = frappe.db.get_value("Annual Plan Item", {"plan_item_id": item_id, "plan_version": version}, "baseline_invitation_date") if version else None
		days = actuals.baseline_lateness_days(event.actual_date, baseline)
		out.setdefault(item_id, []).append({"proceeding_id": proceeding, "actual": event.actual_date, "days": days if isinstance(days, int) else None})
	for rows in out.values():
		rows.sort(key=lambda row: (row["actual"], row["proceeding_id"]))
	return out


def _plan_items(scope: set[str] | None = None) -> list[dict[str, Any]]:
	"""`scope` None is the site-wide view; a set of units is a Head of User Department's department view (see the module docstring)."""
	plans = frappe.get_all(
		"Annual Plan", filters={"active_version": ("is", "set")}, fields=["name", "title", "fiscal_year", "active_version"], order_by="creation asc", limit_page_length=0,
	)
	if not plans:
		return []
	versions = {
		row.name: row.version_number
		for row in frappe.get_all("Annual Plan Version", filters={"name": ("in", [cstr(plan.active_version) for plan in plans])}, fields=["name", "version_number"], limit_page_length=0)
	}
	plan_of = {cstr(plan.active_version): plan for plan in plans}
	items = frappe.get_all(
		"Annual Plan Item", filters={"plan_version": ("in", sorted(plan_of)), "item_state": "Active"},
		fields=["name", "plan_item_id", "plan_version", "title"], order_by="creation asc", limit_page_length=0,
	)
	if not items:
		return []
	item_ids = [cstr(item.plan_item_id) for item in items]
	planned: dict[str, dict[str, Decimal]] = {}
	for row in frappe.get_all(
		"Plan Source Allocation", filters={"plan_item": ("in", [item.name for item in items]), "allocation_state": "Active"},
		fields=["plan_item", "organisation_unit", "indicative_amount"], order_by="creation asc", limit_page_length=0,
	):
		by_unit = planned.setdefault(cstr(row.plan_item), {})
		by_unit[cstr(row.organisation_unit)] = by_unit.get(cstr(row.organisation_unit), Decimal(0)) + _decimal(row.indicative_amount)
	covered = _covered_by_unit(item_ids)
	invitations = _invitation_actuals(item_ids)
	records = []
	for item in items:
		plan = plan_of[cstr(item.plan_version)]
		item_id = cstr(item.plan_item_id)
		drawn = covered.get(item_id, {})
		shares = planned.get(item.name, {})
		# largest planned share first (the lead), ties in the order Planning recorded the allocations
		units = sorted([*shares, *(unit for unit in drawn if unit not in shares)], key=lambda unit: -shares.get(unit, Decimal(0)))
		allocations = [{"org_unit": unit, "planned": shares.get(unit, Decimal(0)), "covered": drawn.get(unit, Decimal(0))} for unit in units]
		proceeding = any(row["covered"] > 0 for row in allocations)  # whole item: an authorised Requisition exists for it
		if scope is not None:
			if not scope & set(shares):
				continue  # no Active allocation of this item belongs to the actor's departments
			allocations = [row for row in allocations if row["org_unit"] in scope]
		given = [row for row in invitations.get(item_id, []) if row["days"] is not None]
		records.append(ac.record(
			ac.PLAN_ITEMS, id=item_id, title=cstr(item.title) or item_id, reference=item_id, fiscal_year=cstr(plan.fiscal_year), org_units=[row["org_unit"] for row in allocations],
			route=[PLAN_ITEM_PAGE, item_id], planned_value=sum(shares.values(), Decimal(0)), allocations=allocations,
			invitation_days=given[0]["days"] if given else None, has_proceeding=proceeding,
			plan_title=cstr(plan.title), plan_version=int(versions[cstr(plan.active_version)]),
			invitation_actuals=[{"proceeding_id": row["proceeding_id"], "days": row["days"]} for row in invitations.get(item_id, [])],
		))
	return records


def facts(*, user: str, kind: str, at: datetime, **params: Any) -> dict[str, Any]:
	"""One kind of Planning facts (see the module docstring)."""
	if kind not in (ac.DEPARTMENTAL_PLANS, ac.PLAN_ITEMS):
		raise ValueError(f"Procurement Planning supplies no {kind!r} facts")
	if kind not in applies(user=user, at=at):
		return ac.facts_result([])
	if kind == ac.DEPARTMENTAL_PLANS:
		return ac.facts_result(_departmental_plans(user, at))
	# a site-wide reader (or technical reader) gets every item; otherwise the actor holds only the Head of User Department view
	return ac.facts_result(_plan_items(None if _plan_reader(user, at) else _hod_units(user, at)))
