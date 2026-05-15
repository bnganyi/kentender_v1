# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §11.2 / §11.3 — TM2 addendum acknowledgement checks (DB-backed).

Issued addenda with ``requires_supplier_acknowledgement`` must have a corresponding
``TM2 Addendum Acknowledgement`` row with ``required`` and ``acknowledged`` satisfied.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint, cstr


def missing_required_addendum_acknowledgements(tm2_name: str, supplier: str) -> list[str]:
	"""Return addendum codes still missing required acknowledgement for ``supplier``."""
	missing: list[str] = []
	rows = frappe.get_all(
		"TM2 Addendum",
		filters={
			"tm2_tender": tm2_name,
			"status": "Issued",
			"requires_supplier_acknowledgement": 1,
		},
		fields=["name", "addendum_code"],
	)
	for row in rows:
		code = cstr(row.get("addendum_code") or "").strip() or cstr(row.get("name") or "").strip()
		ack = frappe.db.get_value(
			"TM2 Addendum Acknowledgement",
			{"tm2_addendum": row.name, "supplier": supplier},
			["acknowledged", "required"],
			as_dict=True,
		)
		if not ack:
			missing.append(code)
			continue
		if cint(ack.get("required")) and not cint(ack.get("acknowledged")):
			missing.append(code)
	return missing
