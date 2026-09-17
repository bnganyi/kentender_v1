# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.1 / §5.5.1A / §5.5.1B — the baseline / forecast /
actual schedule model.

Baseline: one Planner-set anchor (`baseline_invitation_date`) plus the
periods the resolved Procedure Schedule Profile makes applicable (its
verified limits and separately labelled planning assumptions) derive the
applicable baseline dates; delivery completion is the source-derived
boundary (earliest required-by). Feasibility = signing + the Planner's
estimated delivery period on or before that boundary. Baseline and the
resolved rule-profile evidence lock at submission.

Forecast: null until activation, seeded equal to baseline in the activation
transaction, then changed only through the cascade preview/confirm pair —
every later not-yet-actual milestone is proposed with the same day-delta,
each row includable or excludable, one reason, one `cascade_id` (invariant
12c). Actual: never typed; written only by the §18 projection contract.
"""

from __future__ import annotations

import uuid
from typing import Any

import frappe
from frappe.utils import add_days, cstr, date_diff, getdate, now_datetime, nowdate

from kentender_procurement.procurement_planning.errors import fail

MILESTONES: tuple[str, ...] = (
	"invitation",
	"bid_opening",
	"evaluation_completion",
	"award_approval",
	"award_notification",
	"contract_signing",
	"delivery_completion",
)
MILESTONE_LABELS: dict[str, str] = {
	"invitation": "Invitation or advertisement",
	"bid_opening": "Bid opening",
	"evaluation_completion": "Evaluation completion",
	"award_approval": "Tender award approval",
	"award_notification": "Notification of award",
	"contract_signing": "Contract signing",
	"delivery_completion": "Delivery or implementation completion",
}

PERIOD_FIELDS: tuple[str, ...] = (
	"tendering_period_days",
	"evaluation_period_days",
	"award_approval_buffer_days",
	"notification_buffer_days",
	"standstill_period_days",
)
BASELINE_FIELDS = tuple(f"baseline_{m}_date" for m in MILESTONES)

# PLN-CHG-001 v1.18 §5.5.1 — every timing rule comes from the resolved
# Procedure Schedule Profile (services/profiles.py); this module holds no
# universal floor, ceiling, buffer or fallback.


def validate_periods(periods: dict[str, Any], schedule_profile: dict[str, Any] | None = None) -> dict[str, int]:
	"""The entered periods against the resolved profile (labelled
	`PLN_PROFILE_PERIOD_INVALID` parameters); Draft values without a profile."""
	from kentender_procurement.procurement_planning.services import profiles

	return profiles.validate_period_inputs(periods, schedule_profile or dict(profiles.NOT_FOUND))


def derive_baseline(anchor, periods: dict[str, Any], delivery_date, schedule_profile: dict[str, Any] | None = None) -> dict[str, Any]:
	"""The applicable baseline dates from the anchor and periods in the
	profile's milestone order; `delivery_date` is the earliest source
	required-by date (the completion boundary). Feasibility is reported by
	`delivery_boundary_ok` so a Draft save may keep an infeasible schedule
	while readiness blocks."""
	from kentender_procurement.procurement_planning.services import profiles

	profile = schedule_profile or dict(profiles.NOT_FOUND)
	clean = validate_periods(periods, profile)
	return profiles.derive_baseline(anchor or None, clean, delivery_date, profile)


def delivery_boundary_ok(baseline: dict[str, Any], estimated_delivery_period_days=None) -> bool:
	"""§5.5.1 feasibility: baseline contract signing plus the Planner's
	estimated delivery/implementation period on or before the source-derived
	completion boundary. False until the inputs exist."""
	from kentender_procurement.procurement_planning.services import profiles

	return bool(profiles.feasible(baseline, estimated_delivery_period_days))


def baseline_complete(item, schedule_profile: dict[str, Any] | None = None) -> bool:
	from kentender_procurement.procurement_planning.services import profiles

	return profiles.baseline_complete(item, schedule_profile or dict(profiles.NOT_FOUND))


def require_delivery_boundary(baseline: dict[str, Any], estimated_delivery_period_days=None) -> None:
	if not delivery_boundary_ok(baseline, estimated_delivery_period_days):
		fail("PLN_DELIVERY_BOUNDARY_INSUFFICIENT", detail={"field": "baseline_invitation_date"})


# --------------------------------------------------------------------------
# Owner-supplied operational evidence
#
# PLN-CHG-001 v1.23 §5.5.1A / §7.5 / §15.3 (PLN23-CHG-001): Planning keeps no
# forecast records, cascade preview/confirm service or milestone-notification
# job in the MVP. The approved baseline above is immutable; actual milestone
# dates arrive only from the module that owns the real event, are stored per
# procurement proceeding on `Milestone Actual Event`, and never collapse into
# an unqualified item-level actual.
# --------------------------------------------------------------------------


def record_tender_milestone_actual(
	*,
	plan_item_id: str,
	milestone: str,
	actual_date,
	source_event_id: str,
	producer: str = "",
	proceeding_id: str = "",
	proceeding_type: str = "",
	producer_sequence: int = 0,
	coverage: list[dict[str, Any]] | None = None,
	supersedes_event_id: str = "",
) -> dict[str, Any]:
	"""§7.2 `RecordTenderMilestoneActual` / §4.8 / §5.5.1A — inbound only: the
	owning module's authenticated event envelope (producer, unique event id,
	proceeding, producer sequence, optional correction linkage). Never
	callable from a user-facing endpoint (PLN18-AC-120).

	A repeated `(producer, event_id)` is idempotent (plan D10; DB-unique
	`pln_uniq_actual_event`). The never-overwrite guard is scoped to this
	same proceeding (`proceeding_id`, "" counting as its own scope): two
	different proceedings on the same item keep two independent actuals for
	the same milestone (§5.5.1A's own example — 100 and 150 laptops, two
	Tenders, two invitation dates, "both must remain visible") rather than
	one ever silently overwriting the other. `Annual Plan Item.actual_*_date`
	stays a best-effort last-recorded mirror for the single-proceeding
	common case and every existing item-level reader (§8.3 reminders,
	`schedule_rows`, the Requisition eligibility projection) — aggregating
	it correctly across multiple proceedings is explicitly outside the MVP
	(§5.5.1A); the per-proceeding `Milestone Actual Event`/`Proceeding
	Coverage` store below is the fact of record. `coverage` rows (owner-
	supplied) upsert this proceeding's own coverage projection."""
	if milestone not in MILESTONES:
		fail("PLN_SCHEDULE_INVALID", "Unknown milestone.")
	source_event_id = cstr(source_event_id).strip()
	producer = cstr(producer).strip()
	if not source_event_id or not producer:
		fail("PLN_ACTUAL_NOT_WRITABLE", "An actual date must arrive as an identified event from the process that recorded it.")
	name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": plan_item_id, "item_state": "Active"}, "name")
	if not name:
		fail("PLN_STALE_WRITE", "No Active Plan Item carries that id.")

	from kentender_procurement.procurement_planning.services import actuals

	item = frappe.get_doc("Annual Plan Item", name)
	if frappe.db.exists("Milestone Actual Event", {"producer": producer, "event_id": source_event_id}):
		return {"ok": True, "idempotent": True, "plan_item": plan_item_id, "milestone": milestone, "source_event_id": source_event_id, "proceeding_id": proceeding_id}

	current_for_proceeding = actuals.proceeding_events(plan_item_id, cstr(proceeding_id).strip()).get(milestone)
	if current_for_proceeding and getdate(current_for_proceeding.actual_date) != getdate(actual_date):
		if cstr(supersedes_event_id).strip() != cstr(current_for_proceeding.event_id):
			fail(
				"PLN_ACTUAL_NOT_WRITABLE",
				"This proceeding already carries a different actual date for this milestone; a correction must supersede that earlier event.",
				{"plan_item_id": plan_item_id, "milestone": milestone, "proceeding_id": proceeding_id, "existing": str(current_for_proceeding.actual_date), "offered": str(getdate(actual_date))},
			)

	written = actuals.record_actual_event(
		item=item, producer=producer, event_id=source_event_id, milestone=milestone, actual_date=actual_date,
		proceeding_type=proceeding_type, proceeding_id=proceeding_id, producer_sequence=producer_sequence,
		supersedes_event_id=supersedes_event_id,
	)
	# §5.5.1A — the event is the record. No unqualified item-level actual date
	# is written: two Tenders for one item have two invitation actuals, and
	# collapsing them onto the item would lose material information.
	status = "Completed" if milestone == "delivery_completion" else "In progress"
	frappe.db.set_value("Annual Plan Item", name, "item_status", status, update_modified=False)

	for row in coverage or []:
		actuals.upsert_coverage(
			item=item, proceeding_type=proceeding_type, proceeding_id=proceeding_id, allocation=cstr(row.get("allocation")),
			requisition_reference=cstr(row.get("requisition_reference")), requisition_version=cstr(row.get("requisition_version")),
			covered_quantity=row.get("covered_quantity"), covered_value=row.get("covered_value"),
			authorisation_state=cstr(row.get("authorisation_state")), publication_state=cstr(row.get("publication_state")),
			reversal_state=cstr(row.get("reversal_state")), last_event=written["event"],
		)

	return {
		"ok": True, "idempotent": False, "plan_item": plan_item_id, "milestone": milestone, "source_event_id": source_event_id,
		"producer": producer, "proceeding_id": proceeding_id, "proceeding_type": proceeding_type,
		"producer_sequence": int(producer_sequence or 0), "supersedes_event_id": supersedes_event_id, "event": written["event"],
	}
