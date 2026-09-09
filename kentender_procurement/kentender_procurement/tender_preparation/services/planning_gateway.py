# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §9.5 / plan D8 — the one write path into Planning:
`PublishTenderMilestoneActual` consumed by PLN-CHG-001's
`RecordTenderMilestoneActual`. The never-overwrite rule (§10.5) is checked
here before the call because Planning's function has no guard of its own
(TPR FU-05)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import getdate

from kentender_procurement.procurement_planning.services import schedule
from kentender_procurement.tender_preparation.services.errors import fail

MILESTONE_INVITATION = "invitation"


def current_actual_invitation_date(plan_item_id: str):
	name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": plan_item_id, "item_state": "Active"}, "name")
	if not name:
		return None
	return frappe.db.get_value("Annual Plan Item", name, "actual_invitation_date")


def publish_invitation_actual(*, plan_item_id: str, actual_date, correlation_id: str) -> dict[str, Any]:
	existing = current_actual_invitation_date(plan_item_id)
	if existing and getdate(existing) != getdate(actual_date):
		fail(
			"TPR_MILESTONE_ACTUAL_REJECTED",
			"Planning already carries a different actual invitation date for this Plan Item; it is never overwritten.",
			{"plan_item_id": plan_item_id, "existing": str(existing), "offered": str(getdate(actual_date))},
		)
	try:
		return schedule.record_tender_milestone_actual(plan_item_id=plan_item_id, milestone=MILESTONE_INVITATION, actual_date=actual_date, source_event_id=correlation_id)
	except Exception as exc:  # Planning's own closed error set
		fail("TPR_MILESTONE_ACTUAL_REJECTED", str(exc), {"plan_item_id": plan_item_id})
		raise  # unreachable
