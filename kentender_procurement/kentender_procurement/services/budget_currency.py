# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Budget currency of a Fiscal Year, read through Budget & Funding's published API.

Used by Departmental Needs to validate and display a Need's estimated total
cost (NDS-CHG-001 v1.17 §4.9): a read-only lookup of the currency and decimal
precision, never a funding call. Procurement Planning reads the same contract
through its own gateway (`procurement_planning.services.budget_gateway`).

Neither value is ever defaulted: an unknown currency or an unsupported
precision raises `BudgetCurrencyUnavailable` and the caller blocks the write.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import NamedTuple

import frappe
from frappe.utils import cstr

SUPPORTED_PRECISIONS = (0, 1, 2, 3, 4, 5, 6)


class BudgetCurrencyUnavailable(Exception):
	"""The Budget currency or its decimal precision cannot be read."""


class CurrencyBasis(NamedTuple):
	currency: str
	precision: int


@contextmanager
def _system_principal():
	"""Evaluate the one Budget read as Administrator without `frappe.set_user`
	(which mangles the live session inside a web request). A departmental
	Author has no Budget read scope, and the answer is the site's own currency,
	not protected Budget data."""
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


def currency_basis(fiscal_year: str) -> CurrencyBasis:
	from kentender_budget.api.budget_api import resolve_budget_context

	try:
		with _system_principal():
			context = resolve_budget_context(fiscal_year=fiscal_year)
	except frappe.DoesNotExistError:
		context = None
	currency = cstr(((context or {}).get("budget") or {}).get("currency")).strip()
	if not currency:
		raise BudgetCurrencyUnavailable(f"No Budget currency for {fiscal_year}.")
	units = str(int(frappe.db.get_value("Currency", currency, "fraction_units") or 0))
	digits = len(units) - 1 if units.startswith("1") and set(units[1:]) <= {"0"} else None
	if digits is None or digits not in SUPPORTED_PRECISIONS:
		raise BudgetCurrencyUnavailable(f"No supported precision for {currency}.")
	return CurrencyBasis(currency, digits)
