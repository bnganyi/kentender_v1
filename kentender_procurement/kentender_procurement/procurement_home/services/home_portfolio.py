# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Home — portfolio snapshot (budget + tender counts)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, get_datetime, now_datetime

from kentender_procurement.procurement_home.services.pe_aliases import pe_aliases


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


def _can_see_tenders(user: str) -> bool:
	if user in ("Administrator",):
		return True
	roles = set(frappe.get_roles(user))
	return bool(
		roles
		& {
			"Tender Manager",
			"Procurement Officer",
			"Planning Authority",
			"System Manager",
			"Auditor",
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

	PRD: approved = total Approved/Active funding; allocated = plan allocations
	on those budgets; available = approved − allocated.
	Draft/Submitted budgets must not leak into any of the three figures.
	"""
	aliases = set(pe_aliases(procuring_entity))
	approved = 0.0
	allocated = 0.0
	for b in budgets or []:
		if fiscal_year is not None and int(b.get("fiscal_year") or 0) != int(fiscal_year):
			continue
		pe_val = (b.get("procuring_entity") or "").strip()
		if pe_val and pe_val not in aliases:
			continue
		if (b.get("status") or "") not in _APPROVED_ACTIVE:
			continue
		approved += flt(b.get("total_budget_amount"))
		allocated += flt(b.get("allocated_amount"))
	available = max(0.0, approved - allocated)
	return approved, allocated, available


def _unfunded_approved_demand(pe: str) -> float:
	"""Sum shortfall on approved demands without sufficient funding (best-effort)."""
	rows = frappe.get_all(
		"Demand",
		filters={"procuring_entity": ["in", pe_aliases(pe)], "status": "Approved"},
		fields=["name", "total_amount", "budget_line"],
		limit=500,
	)
	total_shortfall = 0.0
	for r in rows:
		bl = r.get("budget_line")
		need = flt(r.get("total_amount"))
		if not bl or need <= 0:
			# No confirmed funding line → treat full amount as unfunded
			if not bl and need > 0:
				total_shortfall += need
			continue
		try:
			from kentender_budget.api.dia_budget_control import get_budget_line_availability

			avail = get_budget_line_availability(bl)
			if isinstance(avail, dict):
				available = flt(avail.get("available") or avail.get("amount_available") or 0)
				if available < need:
					total_shortfall += need - available
		except Exception:
			# Fallback: if reservation_status Failed, count full amount
			rs = frappe.db.get_value("Demand", r.name, "reservation_status")
			if rs in ("Failed", "None", None) and need > 0:
				total_shortfall += need
	return total_shortfall


def _tender_counts(pe: str) -> tuple[int, int]:
	if not frappe.db.exists("DocType", "TM2 Tender"):
		return 0, 0
	filters: dict[str, Any] = {}
	if frappe.db.has_column("TM2 Tender", "procuring_entity_code"):
		filters["procuring_entity_code"] = ["in", pe_aliases(pe)]
	active_statuses = [
		"Draft",
		"STD Instance Incomplete",
		"Ready for Publication Review",
		"Returned for Correction",
		"Approved for Publication",
		"Published",
		"Closed",
		"Closed - No Valid Submissions",
		"Opening Ready",
	]
	active = int(
		frappe.db.count("TM2 Tender", {**filters, "status": ["in", active_statuses]})
	)
	published = frappe.get_all(
		"TM2 Tender",
		filters={**filters, "status": "Published"},
		fields=["name", "tender_code"],
		limit=500,
	)
	now = now_datetime()
	open_count = 0
	for t in published:
		deadline = None
		if frappe.db.exists("DocType", "TM2 Tender Timeline"):
			deadline = frappe.db.get_value(
				"TM2 Tender Timeline", {"tm2_tender": t.name}, "submission_deadline_at"
			)
			if not deadline:
				deadline = frappe.db.get_value(
					"TM2 Tender Timeline",
					{"tender_code": t.get("tender_code")},
					"submission_deadline_at",
				)
		if deadline:
			try:
				if get_datetime(deadline) > now:
					open_count += 1
			except Exception:
				pass
		else:
			open_count += 1
	return active, open_count


def get_home_portfolio(
	procuring_entity: str,
	fiscal_year: int | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	user = (user or frappe.session.user or "").strip()
	show_finance = _can_see_finance(user)
	show_tenders = _can_see_tenders(user)
	if not show_finance and not show_tenders:
		return {"ok": True, "visible": False, "figures": []}

	figures: list[dict[str, Any]] = []
	currency = "KES"

	if show_finance:
		try:
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
						"url": "/desk/budget-hub",
					},
					{
						"key": "allocated_plans",
						"label": "Allocated to procurement plans",
						"value": allocated,
						"display": _fmt_money(allocated, currency),
						"currency": currency,
						"tone": "committed",
						"url": "/desk/budget-hub",
					},
					{
						"key": "available_balance",
						"label": "Available funding balance",
						"value": available,
						"display": _fmt_money(available, currency),
						"currency": currency,
						"tone": "available",
						"url": "/desk/budget-hub",
					},
					{
						"key": "unfunded_demand",
						"label": "Unfunded approved demand",
						"value": unfunded,
						"display": _fmt_money(unfunded, currency),
						"currency": currency,
						"tone": "exhausted",
						"url": "/desk/demand-hub",
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

	if show_tenders:
		active, open_count = _tender_counts(procuring_entity)
		figures.extend(
			[
				{
					"key": "active_tenders",
					"label": "Active tenders",
					"value": active,
					"display": str(active),
					"tone": "default",
					"url": "/desk/tender-management-v2",
				},
				{
					"key": "open_tenders",
					"label": "Open tenders",
					"value": open_count,
					"display": str(open_count),
					"tone": "default",
					"url": "/desk/publications",
				},
			]
		)

	# Never include sealed-bid fields
	return {"ok": True, "visible": True, "figures": figures, "currency": currency}
