# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared Gate 01 invariant guards."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from kentender_procurement.procurement_planning.mvp1_constants import (
	VERSION_IMMUTABLE_STATUSES,
)


def period_dates_for_financial_year(financial_year: str) -> tuple[str, str]:
	"""Map FY string ``YYYY/YY`` to period start/end (1 Jul → 30 Jun)."""
	fy = (financial_year or "").strip()
	if "/" not in fy:
		frappe.throw(_("Financial year must use YYYY/YY format."), title="PLN_FY_FORMAT")
	start_year_s, _end = fy.split("/", 1)
	try:
		start_year = int(start_year_s)
	except ValueError:
		frappe.throw(_("Financial year must use YYYY/YY format."), title="PLN_FY_FORMAT")
	return f"{start_year}-07-01", f"{start_year + 1}-06-30"


def assert_planning_actor(user: str | None = None) -> str:
	"""Reject Administrator / System Manager fallback without a Planning operational role."""
	from kentender_procurement.procurement_planning.services.planning_permissions import (
		assert_planning_actor as _assert,
	)

	return _assert(user)


def assert_version_concurrency(version_name: str, expected_token: str | None) -> None:
	"""Optimistic concurrency: client must pass the current concurrency_token."""
	if expected_token is None:
		return
	current = frappe.db.get_value(
		"Procurement Plan Version", version_name, "concurrency_token"
	)
	if (current or "") != (expected_token or ""):
		frappe.throw(
			_("This plan version was changed by another user. Reload and try again."),
			title="PLN_STALE_VERSION",
		)


def assert_version_mutable(status: str) -> None:
	if (status or "").strip() in VERSION_IMMUTABLE_STATUSES:
		frappe.throw(
			_("Approved, Superseded and Cancelled plan versions are immutable."),
			title="PLN_VERSION_IMMUTABLE",
		)


def new_concurrency_token() -> str:
	return frappe.generate_hash(length=12)


def ensure_unique_plan(procuring_entity: str, financial_year: str, *, exclude: str | None = None) -> None:
	filters: dict[str, Any] = {
		"procuring_entity": procuring_entity,
		"financial_year": financial_year,
	}
	names = frappe.get_all("Procurement Plan", filters=filters, pluck="name", limit=5)
	if exclude:
		names = [n for n in names if n != exclude]
	if names:
		frappe.throw(
			_("A procurement plan already exists for this Procuring Entity and financial year."),
			title="PLN_DUPLICATE_PLAN",
		)


def next_plan_code(procuring_entity: str, financial_year: str) -> str:
	pe = (procuring_entity or "").replace("PE-", "").strip() or "PE"
	fy = (financial_year or "").strip().replace("/", "-")
	base = f"PLN-{pe}-{fy}"
	if not frappe.db.exists("Procurement Plan", {"plan_code": base}):
		return base
	for i in range(2, 100):
		code = f"{base}-{i:02d}"
		if not frappe.db.exists("Procurement Plan", {"plan_code": code}):
			return code
	return f"{base}-{frappe.generate_hash(length=4).upper()}"


def next_plan_item_code(plan_code: str) -> str:
	base = (plan_code or "PLN").replace("PLN-", "PPI-", 1)
	if not base.startswith("PPI-"):
		base = f"PPI-{base}"
	for i in range(1, 1000):
		code = f"{base}-{i:03d}"
		if not frappe.db.exists("Procurement Plan Item", {"plan_item_code": code}):
			return code
	return f"{base}-{frappe.generate_hash(length=4).upper()}"
