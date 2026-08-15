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
	"""Compatibility wrapper over Core's governed ERPNext Fiscal Year service."""
	from kentender_core.services.financial_context import resolve_fiscal_year

	context = resolve_fiscal_year(financial_year)
	return context["start_date"], context["end_date"]


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
	pe = frappe.db.get_value("Procuring Entity", procuring_entity, "entity_code") or procuring_entity
	pe_code = (pe or "PE").removeprefix("PE-").strip() or "PE"
	fy_start = (financial_year or "").split("/", 1)[0]
	return f"PLN-{pe_code}-{fy_start}-001"


def next_plan_item_code(plan_code: str) -> str:
	parts = (plan_code or "").split("-")
	base = f"PPI-{parts[1]}-{parts[2]}" if len(parts) >= 4 else (plan_code or "PLN").replace("PLN-", "PPI-", 1)
	for i in range(1, 1000):
		code = f"{base}-{i:03d}"
		if not frappe.db.exists("Procurement Plan Item", {"plan_item_code": code}):
			return code
	return f"{base}-{frappe.generate_hash(length=4).upper()}"
