# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Opening's sources for the shared record picker (kentender_core.services.record_picker).

One source answers "who may take this role on this opening committee": the Add member dialog on
Prepare opening and the replacement form after an interruption both ask it. The list is the Accounting
Officer's, on a Tender whose committee can still be named; anyone else gets the masked not-found
`appoint_opening_committee` gives. Eligibility is `appointment.picker_rows`, which uses the
command's own refusals word for word (and `appointment.validate` is the check when the choice is saved)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_opening.services import appointment, people, records

SOURCE = "bid_opening.committee_member"


def sources() -> list[dict[str, Any]]:
	return [{
		"key": SOURCE,
		"noun": "person",
		"plural": "people",
		"match": "core",
		"provider": "kentender_procurement.bid_opening.services.picker_sources.committee_members",
		"hint": "Only people holding an active responsibility can be named here.",
	}]


def committee_members(*, query: str, context: dict, actor: str, limit: int) -> list[dict[str, Any]]:
	"""context: `tender`, `role` (the committee role being filled), `taken` (users already on the committee being drafted)."""
	tender = cstr(context.get("tender"))
	case = records.case_for(tender) if tender else None
	if not case or not people.holds(actor, people.ACCOUNTING_OFFICER):
		raise frappe.DoesNotExistError("Not found")
	if frappe.db.get_value(records.CASE, case, "state") not in appointment.APPOINTABLE:
		return []
	taken = context.get("taken")
	return appointment.picker_rows(tender, actor, cstr(context.get("role")), {cstr(u) for u in taken} if isinstance(taken, list) else set())
