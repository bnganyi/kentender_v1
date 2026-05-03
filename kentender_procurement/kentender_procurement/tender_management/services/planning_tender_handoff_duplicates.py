# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning-to-tender duplicate guard (doc 2 sec. 16.3, Tracker B9).

At most **one** non-cancelled ``Procurement Tender`` may reference a given
``Procurement Package``. Enforced on ``Procurement Tender`` validate so desk/API
paths cannot bypass ``release_procurement_package_to_tender`` idempotency.

``XMV-PT-009`` in ``planning_tender_handoff_xmv`` still flags data corruption when
multiple active tenders exist (e.g. legacy imports); this module prevents new violations.
"""

from __future__ import annotations

import frappe
from frappe import _


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
