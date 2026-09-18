# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.1 / §4.8 — server-generated business references.

`tender_reference` = `TND-{PE}-{FY start}-{Plan Item number}` (fixture
`TND-MOH-2027-033`). The Plan Item number is the trailing segment Planning
minted on `plan_item_id`; Tenders never re-derives it. A later Tender on the
same Plan Item (after a cancellation) takes a `-002` suffix; the first has
none. `addendum_reference` = `{tender_reference}-{NNN}` prefixed `ADD-`
(fixture `ADD-MOH-2027-033-001`). Both are minted under a named lock.
"""

from __future__ import annotations

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.tenders.services.errors import fail


def pe_code() -> str:
	code = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code"))
	if not code:
		fail("TND_HANDOFF_INVALID", "This site has no Procuring Entity configured yet.")
	return code.removeprefix("PE-") or code


def fy_start(fiscal_year: str) -> str:
	start = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
	if not start:
		fail("TND_HANDOFF_INVALID", "The Fiscal Year is not configured.")
	return str(getdate(start).year)


def plan_item_number(plan_item_id_value: str) -> str:
	value = cstr(plan_item_id_value).strip()
	if not value or "-" not in value:
		fail("TND_HANDOFF_INVALID", "The Plan Item reference is not well-formed.")
	return value.rsplit("-", 1)[1]


def _lock(name: str) -> None:
	if not frappe.db.sql("select get_lock(%s, 10)", name[:64])[0][0]:
		fail("TND_STALE_VERSION", "Reference generation is busy. Try again.")


def tender_reference(*, fiscal_year: str, plan_item_id_value: str) -> str:
	base = f"TND-{pe_code()}-{fy_start(fiscal_year)}-{plan_item_number(plan_item_id_value)}"
	_lock(f"tnd:ref:{base}")
	existing = frappe.get_all("Tender", filters={"tender_reference": ["like", f"{base}%"]}, pluck="tender_reference", limit_page_length=0)
	if not existing:
		return base
	seq = 1
	for ref in existing:
		tail = cstr(ref)[len(base):]
		if tail.startswith("-") and tail[1:].isdigit():
			seq = max(seq, int(tail[1:]))
	return f"{base}-{seq + 1:03d}"


def addendum_reference(*, tender_reference_value: str, addendum_number: int) -> str:
	return f"ADD-{cstr(tender_reference_value).removeprefix('TND-')}-{int(addendum_number):03d}"
