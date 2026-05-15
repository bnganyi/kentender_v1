# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender duplicate guard (doc 2 sec. 16.3, Tracker B9).

At most **one** active ``TM2 Tender`` (status not in the retender/replan terminal set)
may reference a given ``Procurement Package``. Enforced on ``TM2 Tender`` validate.

Legacy ``Procurement Tender`` duplicate checks remain until that DocType is removed (R07/P11-04).
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cstr

# Must match ``create_tender_from_package`` active-tender duplicate semantics.
TM2_STATUSES_RELEASING_PACKAGE_FOR_NEW_TENDER = frozenset(
	{"Cancelled", "Superseded", "Archived", "Retender Required"}
)


def validate_at_most_one_active_planning_tender_per_package(
	procurement_package: str | None,
	*,
	current_tender_name: str | None = None,
) -> None:
	"""Raise ``ValidationError`` if another non-cancelled tender already uses this package."""
	if not (procurement_package or "").strip():
		return
	pkg = procurement_package.strip()
	excl = (current_tender_name or "").strip()
	others = frappe.get_all(
		"Procurement Tender",
		filters={
			"procurement_package": pkg,
			"tender_status": ("!=", "Cancelled"),
		},
		pluck="name",
		limit=5,
	)
	peer = next((n for n in others if n != excl), None)
	if not peer:
		return
	frappe.throw(
		_(
			"A Procurement Tender is already linked to package {0} (tender {1}). "
			"Cancel it before creating another, or use the existing handoff record."
		).format(pkg, peer),
		title=_("Duplicate planning handoff"),
	)


def validate_at_most_one_active_tm2_tender_per_package(
	procurement_package: str | None,
	*,
	current_tm2_name: str | None = None,
) -> None:
	"""Raise ``ValidationError`` if another active TM2 tender already uses this package."""
	if not (procurement_package or "").strip():
		return
	pkg = procurement_package.strip()
	excl = (current_tm2_name or "").strip()
	for name in frappe.get_all(
		"TM2 Tender",
		filters={"procurement_package": pkg},
		pluck="name",
		limit=20,
	):
		if name == excl:
			continue
		st = cstr(frappe.db.get_value("TM2 Tender", name, "status") or "").strip()
		if st and st not in TM2_STATUSES_RELEASING_PACKAGE_FOR_NEW_TENDER:
			frappe.throw(
				_(
					"A TM2 Tender is already linked to package {0} (tender {1}). "
					"Cancel or terminal-complete it before creating another, or use the existing handoff record."
				).format(pkg, name),
				title=_("Duplicate planning handoff"),
			)
