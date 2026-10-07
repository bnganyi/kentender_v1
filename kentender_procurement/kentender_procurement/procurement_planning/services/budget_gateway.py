# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §7.3 — the Budget & Funding contracts, under the spec's
verbs (decision D6/D11).

Planning calls only Budget's published API module and never reads Budget
tables directly. Two contracts remain after v1.7's lifecycle simplification:

	ListEligibleBudgetLines   → budget_api.list_eligible_budget_lines
	CheckPlanAffordability    → budget_api.check_plan_affordability

Planning creates no reservation at any point (§7.3, BUD-BR-009): the v1.2
module's check/reserve/release/revalidate gateway paths are deleted, not
wrapped. Neither contract takes a Procuring Entity argument (§16.2).
The approved budget is the plan's funding ceiling only: the 30%
reservation is a share of the plan's own eligible value (PLN v1.25
§5.5.3.1), so there is no annual-budget-basis contract here.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import frappe
from frappe.utils import cstr


@contextmanager
def _system_principal():
	"""Temporarily evaluate one cross-module read as Administrator WITHOUT
	`frappe.set_user` (v1.2 finding: `set_user` inside a web request mangles
	the live session so every later request arrives as Guest).

	Budget's read scope admits only Budget-side responsibilities; §7.3/§12.3
	require the *departmental* author to see their department's eligible
	Active lines and the Planner to see the affordability statement. Every
	Planning caller authorises its own actor first; the result is already
	narrowed to the department or the plan's own totals."""
	local = frappe.local
	session = local.session
	saved = (session.user, session.sid, session.data)
	saved_form_dict = local.form_dict
	saved_user_obj = getattr(local, "user_obj", None)
	try:
		session.user = "Administrator"
		local.role_permissions = {}
		local.user_obj = None
		yield
	finally:
		session.user, session.sid, session.data = saved
		local.form_dict = saved_form_dict
		local.role_permissions = {}
		local.user_obj = saved_user_obj


def list_eligible_budget_lines(*, fiscal_year: str, source_org_unit: str | None = None) -> list[dict[str, Any]]:
	"""BUD v1.5 §9.1 — Active eligible lines (Entity-wide or matching the
	source unit), each with its human `reference`."""
	from kentender_budget.api.budget_api import list_eligible_budget_lines as contract

	with _system_principal():
		return contract(fiscal_year=fiscal_year, source_org_unit=source_org_unit)


def eligible_line_ids(*, fiscal_year: str, source_org_unit: str | None = None) -> set[str]:
	return {
		cstr(row.get("id") or row.get("name"))
		for row in list_eligible_budget_lines(fiscal_year=fiscal_year, source_org_unit=source_org_unit)
	}


def line_labels(fiscal_year: str) -> dict[str, dict[str, Any]]:
	"""`id` → {reference, title, label, funding_source, currency} for display."""
	out = {}
	for row in list_eligible_budget_lines(fiscal_year=fiscal_year):
		reference = cstr(row.get("reference")) or cstr(row.get("id"))
		out[cstr(row.get("id"))] = {
			"reference": reference,
			"title": cstr(row.get("title")),
			"label": f"{reference} — {row.get('title')}" if row.get("title") else reference,
			"funding_source": cstr(row.get("funding_source")),
			"approved": row.get("approved"),
		}
	return out


def budget_currency(fiscal_year: str) -> str:
	"""The Budget's own currency for the Fiscal Year (BUD §4.8 CurrencyBasis),
	through its published `resolve_budget_context`. Never defaulted: a missing
	or blank currency blocks the caller (PLN §4.1)."""
	from kentender_budget.api.budget_api import resolve_budget_context

	from kentender_procurement.procurement_planning.errors import fail

	try:
		with _system_principal():
			context = resolve_budget_context(fiscal_year=fiscal_year)
	except frappe.DoesNotExistError:
		context = None
	currency = cstr(((context or {}).get("budget") or {}).get("currency")).strip()
	if not currency:
		fail("PLN_REFERENCE_UNAVAILABLE", "The Budget currency for this Fiscal Year is not available.", {"fiscal_year": fiscal_year})
	return currency


def money_precision(fiscal_year: str) -> int:
	"""Decimal places of the Budget's currency for the Fiscal Year (BUD §4.8
	CurrencyBasis), read from the native Currency record the Budget itself reads.
	Never defaulted to two: an unknown or unsupported precision blocks the write
	(PLN §4.1, `PLN_MONEY_PRECISION_INVALID`)."""
	from kentender_procurement.procurement_planning.errors import fail
	from kentender_procurement.procurement_planning.services import money

	currency = budget_currency(fiscal_year)
	units = str(int(frappe.db.get_value("Currency", currency, "fraction_units") or 0))
	digits = len(units) - 1 if units.startswith("1") and set(units[1:]) <= {"0"} else None
	if digits is None or digits not in money.SUPPORTED_PRECISIONS:
		fail("PLN_MONEY_PRECISION_INVALID", "The currency precision for this amount is not configured.", {"currency": currency})
	return digits


def _totals_as_text(planned_totals: dict[str, Any]) -> dict[str, str]:
	"""PLN §4.1 — amounts cross the Budget contract as exact decimal strings,
	never as binary floats (Budget reads them with its own exact parser)."""
	from kentender_procurement.procurement_planning.services import money

	return {str(line): money.money_text(amount) for line, amount in (planned_totals or {}).items()}


def check_plan_affordability(*, fiscal_year: str, planned_totals: dict[str, Any]) -> dict[str, Any]:
	"""BUD v1.5 §8.2 — non-mutating; blocking within-approved, advisory
	within-available. No token, no lock, no ledger event."""
	from kentender_budget.api.budget_api import check_plan_affordability as contract

	with _system_principal():
		return contract(fiscal_year=fiscal_year, planned_totals=_totals_as_text(planned_totals))


#: BUD v1.11 §6 — Planning's registered principal for the revision-request
#: calls; Budget checks this flag, never a browser-supplied value.
PLANNING_PRINCIPAL_FLAG = "kt_budget_service_principal"


@contextmanager
def _planning_principal():
	with _system_principal():
		previous = frappe.flags.get(PLANNING_PRINCIPAL_FLAG)
		frappe.flags[PLANNING_PRINCIPAL_FLAG] = "procurement_planning"
		try:
			yield
		finally:
			frappe.flags[PLANNING_PRINCIPAL_FLAG] = previous


def receive_budget_revision_request(payload: dict[str, Any]) -> dict[str, Any]:
	"""BUD v1.11 §8.5 item 1 — inside Planning's `RequestBudgetRevision`
	transaction; Budget records one Open request or refuses."""
	from kentender_budget.api.budget_api import receive_budget_revision_request as contract

	with _planning_principal():
		return contract(payload)


def withdraw_budget_revision_request(payload: dict[str, Any]) -> dict[str, Any]:
	"""BUD v1.11 §8.5 item 4 — Planning withdraws its own Open request."""
	from kentender_budget.api.budget_api import withdraw_budget_revision_request as contract

	with _planning_principal():
		return contract(payload)


class BudgetBasisStale(Exception):
	"""Budget refused the positive decision: its authoritative basis changed
	since the review (`BUD_BASIS_STALE`) or is unavailable (`BUD_BASIS_UNAVAILABLE`)."""

	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def validate_plan_affordability_for_decision(*, fiscal_year: str, planned_totals: dict[str, Any], expected_revisions: dict[str, str] | None = None, correlation: str = "") -> dict[str, Any]:
	"""BUD v1.8 (owed) §5.3.3 — the decision-time counterpart of the display
	read: inside the caller's transaction Budget serialises its Active
	Version and line versions, validates the reviewed revisions and returns
	the comparison statement with the line revisions and its basis digest.
	No reservation, ledger event or Budget record is created. A stale or
	missing basis is raised as `BudgetBasisStale` for the caller to map."""
	import frappe as _frappe

	from kentender_budget.api.budget_api import validate_plan_affordability_for_decision as contract

	before = len(_frappe.local.message_log or [])
	with _system_principal():
		try:
			return contract(fiscal_year=fiscal_year, planned_totals=_totals_as_text(planned_totals), expected_revisions=expected_revisions or {}, correlation=correlation)
		except _frappe.ValidationError as exc:
			titles = [m.get("title") for m in (_frappe.local.message_log or [])[before:] if isinstance(m, dict)]
			code = next((t for t in reversed(titles) if t in ("BUD_BASIS_STALE", "BUD_BASIS_UNAVAILABLE")), "")
			if code:
				_frappe.clear_last_message()
				raise BudgetBasisStale(code, str(exc)) from exc
			raise
