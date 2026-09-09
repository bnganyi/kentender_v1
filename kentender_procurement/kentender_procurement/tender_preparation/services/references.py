# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.1 — the Tender reference, generated once and used in
every output: `TND-{PE}-{FY start}-{plan item number}` (fixture
`TND-MOH-2027-033`), with `-2`, `-3` … only for a successor Tender on the
same Plan Item after an upstream correction (plan D14/D20)."""

from __future__ import annotations

import frappe
from frappe.utils import cstr


def _pe_short_code() -> str:
	code = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_code")) or "PE"
	return code[3:] if code.upper().startswith("PE-") else code


def base_reference(*, plan_item_id: str) -> str:
	parts = cstr(plan_item_id).split("-")
	if len(parts) >= 4:
		year, number = parts[-2], parts[-1]
	else:
		year, number = "0000", cstr(plan_item_id) or "000"
	return f"TND-{_pe_short_code()}-{year}-{number}"


def tender_reference(*, plan_item_id: str) -> str:
	"""Mint under a database lock so two concurrent prepares on sibling
	handoffs of one Plan Item cannot collide; the column is unique too."""
	base = base_reference(plan_item_id=plan_item_id)
	frappe.db.sql("select get_lock(%s, 10)", (f"tpr-ref-{base}",))
	try:
		taken = set(frappe.get_all("Prepared Tender", filters={"tender_reference": ("like", f"{base}%")}, pluck="tender_reference"))
		if base not in taken:
			return base
		n = 2
		while f"{base}-{n}" in taken:
			n += 1
		return f"{base}-{n}"
	finally:
		frappe.db.sql("select release_lock(%s)", (f"tpr-ref-{base}",))
