# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — portfolio snapshot (budget figures; the tender counts read the
retired tender workbench and were removed with it)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt

from kentender_procurement.procurement_home.services.home_context import year_from_fiscal_period
from kentender_procurement.procurement_home.services.pe_aliases import pe_aliases
from kentender_procurement.procurement_lifecycle.demand_module_gate import (
	demand_doctype_available,
)


def _budget_fiscal_year(budget: dict[str, Any]) -> int | None:
	"""Prefer legacy fiscal_year; otherwise parse Budget.fiscal_period."""
	if budget.get("fiscal_year") not in (None, ""):
		return year_from_fiscal_period(budget.get("fiscal_year"))
	return year_from_fiscal_period(budget.get("fiscal_period"))


def _can_see_finance(user: str) -> bool:
	if user in ("Administrator",):
		return True
	roles = set(frappe.get_roles(user))
	return bool(
		roles
		& {
			"Budget Officer",
			"Finance Reviewer",
			"Head of Procurement",
			"Procurement Officer",
			"Planning Authority",
			"System Manager",
			"Accounts Manager",
		}
	)


def _fmt_money(amount: float, currency: str) -> str:
	# Compact display for large values
	abs_amt = abs(amount)
	if abs_amt >= 1_000_000_000:
		body = f"{amount / 1_000_000_000:.2f}B"
	elif abs_amt >= 1_000_000:
		body = f"{amount / 1_000_000:.0f}M" if abs_amt >= 10_000_000 else f"{amount / 1_000_000:.2f}M"
	elif abs_amt >= 1_000:
		body = f"{amount:,.0f}"
	else:
		body = f"{amount:,.2f}"
	return f"{currency} {body}".replace(".00B", "B")


_APPROVED_ACTIVE = frozenset(("Approved", "Active"))


def _finance_sums_for_context(
	budgets: list[dict[str, Any]],
	procuring_entity: str,
	fiscal_year: int | None,
) -> tuple[float, float, float]:
	"""Approved / allocated / available for selected PE + FY.

	Uses Budget & Funding landing figures (PRD: do not invent competing maths):

	- approved = Approved/Active ``total_budget_amount`` (envelope), never below
	  active line allocations when the envelope is stale
	- available = sum of Budget Line ``amount_available`` on those budgets
	- allocated = approved − available (funding already reserved/committed/consumed)

	Draft/Submitted budgets must not leak into any of the three figures.
	"""
	aliases = set(pe_aliases(procuring_entity))
	approved = 0.0
	available = 0.0
	for b in budgets or []:
		if fiscal_year is not None and _budget_fiscal_year(b) != int(fiscal_year):
			continue
		pe_val = (b.get("procuring_entity") or "").strip()
		if pe_val and pe_val not in aliases:
			continue
		if (b.get("status") or "") not in _APPROVED_ACTIVE:
			continue
		envelope = flt(b.get("total_budget_amount"))
		line_allocated = flt(b.get("allocated_amount"))
		# Defensive: IT supplement historically left envelope < line sum.
		approved += max(envelope, line_allocated)
		available += flt(b.get("available_amount"))
	available = max(0.0, min(available, approved))
	allocated = max(0.0, approved - available)
	return approved, allocated, available


def _unfunded_approved_demand(pe: str) -> float:
	_ = pe
	# Demands package retired; guard is permanently unreachable but kept explicit.
	if not demand_doctype_available():
		return 0.0
	return 0.0


def get_home_portfolio(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	user = (user or frappe.session.user or "").strip()
	show_finance = _can_see_finance(user)
	if not show_finance:
		return {"ok": True, "visible": False, "figures": []}

	figures: list[dict[str, Any]] = []
	currency = "KES"

	if show_finance:
		try:
			# MVP-1 Budget teardown: landing returns empty budgets until rebuild.
			from kentender_budget.api.landing import get_budget_landing_data

			data = get_budget_landing_data() or {}
			budgets = list(data.get("budgets") or [])
			# Prefer currency from first budget row when present
			for b in budgets:
				if b.get("currency"):
					currency = b["currency"]
					break
			approved, allocated, available = _finance_sums_for_context(
				budgets, procuring_entity, fiscal_year
			)
			unfunded = _unfunded_approved_demand(procuring_entity)
			figures.extend(
				[
					{
						"key": "approved_budget",
						"label": "Approved procurement budget",
						"value": approved,
						"display": _fmt_money(approved, currency),
						"currency": currency,
						"tone": "default",
						"url": "/desk/budget-management",
					},
					{
						"key": "allocated_plans",
						"label": "Allocated to procurement plans",
						"value": allocated,
						"display": _fmt_money(allocated, currency),
						"currency": currency,
						"tone": "committed",
						"url": "/desk/budget-management",
					},
					{
						"key": "available_balance",
						"label": "Available funding balance",
						"value": available,
						"display": _fmt_money(available, currency),
						"currency": currency,
						"tone": "available",
						"url": "/desk/budget-management",
					},
					{
						"key": "unfunded_demand",
						"label": "Unfunded approved demand",
						"value": unfunded,
						"display": _fmt_money(unfunded, currency),
						"currency": currency,
						"tone": "exhausted",
						"url": "/desk/departmental-needs",
					},
				]
			)
		except Exception as exc:
			frappe.log_error(title="Procurement Home portfolio finance", message=str(exc))
			return {
				"ok": False,
				"visible": True,
				"error": True,
				"message": "Portfolio figures are temporarily unavailable.",
				"figures": [],
			}

	# Never include sealed-bid fields
	return {"ok": True, "visible": True, "figures": figures, "currency": currency}
