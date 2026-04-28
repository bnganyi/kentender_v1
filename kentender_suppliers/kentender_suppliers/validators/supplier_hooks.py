# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import re

import frappe
from frappe import _

# SUP-KE-YYYY-##### — year is 4 digits; sequence is at least 4 digits (zero-padded) and may grow past 9999.
KENTENDER_SUPPLIER_CODE_PATTERN = re.compile(r"^SUP-KE-\d{4}-\d{4,12}$")


def validate_kentender_supplier(doc, method: str | None = None) -> None:
	"""B1: format + uniqueness of KenTender business id on ERPNext Supplier."""
	c = (doc.get("kentender_supplier_code") or "").strip()
	if not c:
		return
	if not KENTENDER_SUPPLIER_CODE_PATTERN.match(c):
		frappe.throw(
			_("KenTender Supplier Code must match format SUP-KE-YYYY-#### (e.g. SUP-KE-2026-0001 or SUP-KE-2026-10000).")
		)
	flt: dict = {"kentender_supplier_code": c}
	if getattr(doc, "name", None):
		flt["name"] = ("!=", doc.name)
	existing = frappe.db.get_value("Supplier", flt, "name")
	if existing:
		frappe.throw(_("KenTender Supplier Code must be unique."))
	# Company → tax_id / company registration: rely on standard Supplier validation where present
