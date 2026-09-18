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
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_planning.services import schedule
from kentender_procurement.tender_preparation.services.errors import fail

MILESTONE_INVITATION = "invitation"


def current_actual_invitation_date(plan_item_id: str, tender: str = ""):
	"""What this Tender has already told Planning, asked through Planning's
	own published read.

	PLN-CHG-001 v1.23 §5.5.1A removed the `Annual Plan Item.actual_*_date`
	mirror this used to read directly: §611 forbids collapsing two
	proceedings' dates into one unqualified item actual, since two Tenders
	against one Plan Item legitimately hold two invitation dates and both
	must remain visible. The answer is therefore scoped to this Tender, and
	comes from the owner's service rather than its table (AGENTS.md §2)."""
	return schedule.current_proceeding_actual(
		plan_item_id=plan_item_id, milestone=MILESTONE_INVITATION, proceeding_id=cstr(tender).strip(),
	)


PRODUCER = "tender_preparation"
PROCEEDING_TYPE = "Prepared Tender"


def publish_invitation_actual(*, plan_item_id: str, actual_date, correlation_id: str, tender: str = "", producer_sequence: int = 1) -> dict[str, Any]:
	"""PLN-CHG-001 v1.18 §4.8 — the event envelope: producer, unique event id
	(the correlation id), the proceeding this actual belongs to and its
	producer sequence. Planning now enforces idempotency and never-overwrite
	itself (plan D10); this module's pre-check stays as the earlier, explicit
	refusal."""
	existing = current_actual_invitation_date(plan_item_id, tender)
	if existing and getdate(existing) != getdate(actual_date):
		fail(
			"TPR_MILESTONE_ACTUAL_REJECTED",
			"Planning already carries a different actual invitation date for this Tender; it is never overwritten.",
			{"plan_item_id": plan_item_id, "tender": tender, "existing": str(existing), "offered": str(getdate(actual_date))},
		)
	try:
		return schedule.record_tender_milestone_actual(
			plan_item_id=plan_item_id, milestone=MILESTONE_INVITATION, actual_date=actual_date, source_event_id=correlation_id,
			producer=PRODUCER, proceeding_id=tender or "", proceeding_type=PROCEEDING_TYPE, producer_sequence=int(producer_sequence or 1),
		)
	except Exception as exc:  # Planning's own closed error set
		fail("TPR_MILESTONE_ACTUAL_REJECTED", str(exc), {"plan_item_id": plan_item_id})
		raise  # unreachable
