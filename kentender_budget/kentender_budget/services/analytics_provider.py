# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ANL-CHG-001 v0.8 §7.1, §5.5 rule 5 — Budget's funding position for Procurement Analytics (fact kind `funding`).

Registered on the `kt_analytics_providers` hook (the contract is `kentender_core.services.analytics_contract`); core never
imports this app, and this app imports nothing from Procurement. Two functions answer for one actor (never the session
user: nothing here binds to `frappe.session.user` or calls `frappe.set_user`) and only read.

`facts(user=, kind="funding", at=, fiscal_year=, org_unit="")` answers for ONE Fiscal Year's ACTIVE budget Version:

- **lines** — every Budget Line of that Version with its title as `label`, `owner_org_unit` ("" = available to all
  departments), and `registered` (the Version's `approved_amount`), `reserved` (the line's Active, Partially Converted and
  Needs Attention reservations' remaining amounts), `committed` (the line's Active commitments) and `available`
  (registered - reserved - committed), the same definitions as `budget_contracts._line_position`, recomputed here from the
  stored exact decimals, never through `float`. `reserved + committed + available == registered` holds exactly.
- **reservations** — every Funding Reservation of that Fiscal Year's budget that holds an amount, with its
  `source_org_unit`, its line's `line_owner_org_unit`, and its `reserved` and `committed` amounts. A reservation that is
  Released or fully converted and carries no commitment holds nothing and is left out; the line totals are unaffected.
- **view** — `"whole"` for the whole-Budget audience, `"department"` when the actor is a Head of User Department (or a
  department was named): lines are then only those whose `owner_org_unit` is one of the department(s), and reservations
  only those whose `source_org_unit` is. A shared line's allocation and available amount are therefore never given to
  a department view, and never divided.

When the Fiscal Year has no Budget or no Active Version the answer is `{"funding": None, "reason": "no_active_budget"}`
(never an exception, never zeros), so core can show nothing for that year.

**Who may read it.** The whole-Budget audience of ANL §5.5 rule 5: Budget Officer, Budget Approver, Finance Confirmation
Officer, Auditor, Head of Procurement Function, Accounting Officer and technical readers (Administrator, System Manager,
Technical Operator). The Accounting Officer and the Head of Procurement Function read approved Versions only
(`budget_read_scope`); the Active Version is approved, and no other Version is ever read here, so that rule holds.

**Head of User Department (owner decision, 5 October 2026: "HOD has to have budget visibility").** The Head of User
Department reads the department funding view through THIS aggregate projection only: their own department's lines in
full, and only their own department's reservations and commitments on lines available to all departments. It adds no
DocPerm and changes no Budget read rule: that role still cannot open a Budget, a line, a version or a reservation record
(`test_ovs_budget_reads`, FU-OVS-30).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_budget.services.budget_authorization import APPROVED_READ_ROLES, BUDGET_READ_ROLES
from kentender_core.services import analytics_contract as ac
from kentender_core.services.authorization import PURPOSE_READ, authorise_record, is_technical, permitted_ou_scopes
from kentender_core.services.home_viewer import is_technical_reader

BUDGET, VERSION = "Procurement Budget", "Procurement Budget Version"
#: The registry's own name for the one department-scoped reader (Budget does not import Procurement's constant).
ROLE_HEAD_OF_USER_DEPARTMENT = "Head of User Department"
#: ANL §5.5 rule 5, whole-Budget audience: the three Budget responsibilities and the Auditor, and the two approved-only readers.
WHOLE_ROLES = BUDGET_READ_ROLES + APPROVED_READ_ROLES
#: The owner's own definition of a reservation that still holds funds (`budget_contracts._ACTIVE_RESERVATION_STATUSES`).
HOLDING = ("Active", "Partially Converted", "Needs Attention")
NO_ACTIVE_BUDGET = {"funding": None, "reason": "no_active_budget"}
_CENT = Decimal("0.01")


def _audience(user: str, at: datetime) -> tuple[bool, set[str]]:
	"""(whole-Budget reader, the departments a Head of User Department may see)."""
	if not user or user == "Guest":
		return False, set()
	whole = is_technical_reader(user, at) or any(authorise_record(user=user, business_role=role, at=at, purpose=PURPOSE_READ).allowed for role in WHOLE_ROLES)
	units = set() if is_technical(user) else (permitted_ou_scopes(user, ROLE_HEAD_OF_USER_DEPARTMENT, at) or set())
	return whole, units


def applies(*, user: str, at: datetime) -> set[str]:
	"""`funding` for the whole-Budget audience and for a Head of User Department."""
	whole, units = _audience(user, at)
	return {ac.FUNDING} if whole or units else set()


def _amount(value: Any) -> Decimal:
	"""A stored exact decimal (read as text, never as a float) in cents where it is exact to the cent."""
	amount = ac.money(value if value not in (None, "") else "0")
	return amount.quantize(_CENT) if amount == amount.quantize(_CENT) else amount


def _texts(sql: str, values: tuple) -> list[Any]:
	return frappe.db.sql(sql, values, as_dict=True)


def facts(*, user: str, kind: str, at: datetime, fiscal_year: str = "", org_unit: str = "", **params: Any) -> dict[str, Any]:
	"""The funding position of `fiscal_year` for the actor, or `NO_ACTIVE_BUDGET`. Raises for another kind, an actor outside the
	audience, a missing Fiscal Year argument, and a department a department-only reader does not hold (never a silent
	widening)."""
	if kind != ac.FUNDING:
		raise ValueError(f"the Budget provider has no fact kind {kind!r}")
	whole, scope = _audience(user, at)
	if not whole and not scope:
		raise frappe.PermissionError("No Budget funding responsibility.")
	fiscal_year, org_unit = cstr(fiscal_year).strip(), cstr(org_unit).strip()
	if not fiscal_year:
		raise ValueError("Fiscal Year is required")
	if org_unit and not whole and org_unit not in scope:
		raise frappe.PermissionError("Not a department in your permitted scope.")
	# whole-Budget actors with no department named see the whole position; a named department, and every Head of User
	# Department, see the department view
	units = {org_unit} if org_unit else (None if whole else scope)

	budget = frappe.db.get_value(BUDGET, {"fiscal_year": fiscal_year}, ["name", "title"], as_dict=True)
	versions = frappe.get_all(VERSION, filters={"budget": budget.name, "status": "Active"}, fields=["name", "version_number"], limit_page_length=0) if budget else []
	if not versions:
		return dict(NO_ACTIVE_BUDGET)
	if len(versions) > 1:
		raise frappe.ValidationError("Multiple Active Budget Versions found for this Budget")  # BUD-BR-002: unreachable unless the data is wrong
	version = versions[0]

	line_versions = _texts(
		"select budget_line, title, owner_org_unit, cast(approved_amount as char) as registered from `tabProcurement Budget Line Version` "
		"where budget_version = %s order by title asc, budget_line asc", (version.name,),
	)
	lines_by_id = [row.budget_line for row in line_versions] or [""]
	reserved_by_line = {
		row.budget_line: _amount(row.total) for row in _texts(
			"select budget_line, cast(coalesce(sum(remaining_amount), 0) as char) as total from `tabFunding Reservation` "
			"where budget_line in %s and status in %s group by budget_line", (lines_by_id, HOLDING),
		)
	}
	committed_by_line = {
		row.budget_line: _amount(row.total) for row in _texts(
			"select r.budget_line as budget_line, cast(coalesce(sum(c.current_amount), 0) as char) as total from `tabProcurement Commitment` c "
			"join `tabFunding Reservation` r on r.name = c.reservation where r.budget_line in %s and c.status = 'Active' group by r.budget_line", (lines_by_id,),
		)
	}
	lines: list[dict[str, Any]] = []
	owner_of: dict[str, str] = {}
	for row in line_versions:
		owner = cstr(row.owner_org_unit)
		owner_of[row.budget_line] = owner
		if units is not None and (not owner or owner not in units):
			continue  # a department view holds only that department's own lines: a shared line is never given or divided
		registered = _amount(row.registered)
		reserved, committed = reserved_by_line.get(row.budget_line, Decimal("0.00")), committed_by_line.get(row.budget_line, Decimal("0.00"))
		lines.append({"label": cstr(row.title) or cstr(row.budget_line), "owner_org_unit": owner, "registered": registered, "reserved": reserved, "committed": committed, "available": registered - reserved - committed})

	reservations = _reservations(budget.name, units, owner_of)
	return ac.funding(fiscal_year=fiscal_year, budget_title=cstr(budget.title), version=int(version.version_number), as_at=at, lines=lines, reservations=reservations,
		view="whole" if units is None else "department")


def _reservations(budget: str, units: set[str] | None, owner_of: dict[str, str]) -> list[dict[str, Any]]:
	"""Every reservation of the budget that holds an amount, filtered by source department for a department view."""
	rows = _texts(
		"select r.name as name, r.budget_line as budget_line, r.source_organisation_unit as source, "
		"cast(case when r.status in %s then r.remaining_amount else 0 end as char) as reserved, "
		"cast(coalesce((select sum(c.current_amount) from `tabProcurement Commitment` c where c.reservation = r.name and c.status = 'Active'), 0) as char) as committed "
		"from `tabFunding Reservation` r where r.budget = %s order by r.name asc", (HOLDING, budget),
	)
	missing = sorted({row.budget_line for row in rows if row.budget_line and row.budget_line not in owner_of})
	if missing:  # a reservation on a line the Active Version no longer carries: that line's latest recorded owner
		for row in _texts("select budget_line, owner_org_unit from `tabProcurement Budget Line Version` where budget_line in %s order by creation asc", (missing,)):
			owner_of[row.budget_line] = cstr(row.owner_org_unit)
	out = []
	for row in rows:
		reserved, committed = _amount(row.reserved), _amount(row.committed)
		source = cstr(row.source)
		if not reserved and not committed:
			continue
		if units is not None and source not in units:
			continue
		out.append({"source_org_unit": source, "line_owner_org_unit": owner_of.get(row.budget_line, ""), "reserved": reserved, "committed": committed})
	return out
