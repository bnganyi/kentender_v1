# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 server-generated business references.

`requisition_reference` format (§5.1): `REQ-{PE}-{FY start}-{Plan Item
number}-{3 digits}`. The Plan Item number is the trailing sequence segment
Planning's own `plan_item_id` generator already minted (`PPI-{PE}-{FY
start}-{NNN}`) — Requisitions never re-derives or re-mints that number, only
reads it back off the business id Planning's eligibility projection returned.
The final 3 digits are this module's own sequence, scoped to that one Plan
Item (REQ-AC-001/§5.1: several sequential Requisitions may exist against one
Plan Item over time, never more than one *open* at once — §7.5 invariant 3).

`pe_code`/`fy_start` are small independent copies of the same primitives
Planning's own `references.py` uses (reading `Site Procuring Entity`/
`Fiscal Year` — core doctypes, not Planning internals) rather than an import
of Planning's module: Requisitions is a sibling module that calls Planning's
*published* `plan_requisition` contract, never its internal service files.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_requisitions.services.errors import fail


def pe_code() -> str:
	code = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	if not code:
		fail("REQ_PLAN_INELIGIBLE", "This site has no Procuring Entity configured yet.")
	return code.removeprefix("PE-") or code


def fy_start(fiscal_year: str) -> str:
	start = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	if not start:
		fail("REQ_PLAN_INELIGIBLE", "The Fiscal Year is not configured.")
	return str(getdate(start).year)


def plan_item_number(plan_item_id_value: str) -> str:
	"""The trailing sequence segment of a Planning `plan_item_id` business
	reference (`PPI-MOH-2027-033` -> `033`), never re-derived — only read
	back off the id Planning itself minted."""
	value = cstr(plan_item_id_value).strip()
	if not value or "-" not in value:
		fail("REQ_PLAN_INELIGIBLE", "The Plan Item reference is not well-formed.")
	return value.rsplit("-", 1)[1]


def _next_requisition_sequence(prefix: str) -> str:
	lock = f"req:ref:{prefix}"[:64]
	if not frappe.db.sql("select get_lock(%s, 10)", lock)[0][0]:
		fail("REQ_STALE_VERSION", "Reference generation is busy. Try again.")
	rows = frappe.get_all(
		"Procurement Requisition", filters={"requisition_reference": ["like", f"{prefix}%"]},
		pluck="requisition_reference", limit_page_length=0,
	)
	seq = max([int(ref[len(prefix):]) for ref in rows if cstr(ref)[len(prefix):].isdigit()] or [0]) + 1
	return f"{prefix}{seq:03d}"


def requisition_reference(*, fiscal_year: str, plan_item_id_value: str) -> str:
	prefix = f"REQ-{pe_code()}-{fy_start(fiscal_year)}-{plan_item_number(plan_item_id_value)}-"
	return _next_requisition_sequence(prefix)
