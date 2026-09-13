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
FORECAST_FIELDS = tuple(f"forecast_{m}_date" for m in MILESTONES)
ACTUAL_FIELDS = tuple(f"actual_{m}_date" for m in MILESTONES)

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
# Forecast layer
# --------------------------------------------------------------------------


def seed_forecast_from_baseline(item_name: str) -> None:
	"""Invariant 12e — the one system-initiated forecast write, at activation."""
	values = frappe.db.get_value("Annual Plan Item", item_name, list(BASELINE_FIELDS), as_dict=True) or {}
	frappe.db.set_value(
		"Annual Plan Item",
		item_name,
		{f"forecast_{m}_date": values.get(f"baseline_{m}_date") for m in MILESTONES},
		update_modified=False,
	)


def behind_baseline(item) -> bool:
	"""A Plan Item is behind when any not-yet-actual milestone's forecast is
	later than its baseline (§8.1 schedule-health count)."""
	for m in MILESTONES:
		if item.get(f"actual_{m}_date"):
			continue
		forecast, baseline = item.get(f"forecast_{m}_date"), item.get(f"baseline_{m}_date")
		if forecast and baseline and getdate(forecast) > getdate(baseline):
			return True
	return False


def schedule_health(version_name: str) -> dict[str, int]:
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version_name, "item_state": "Active"},
		fields=["name", *BASELINE_FIELDS, *FORECAST_FIELDS, *ACTUAL_FIELDS],
		limit_page_length=0,
	)
	behind = sum(1 for item in items if behind_baseline(item))
	return {"behind": behind, "total": len(items)}


def schedule_rows(item) -> list[dict[str, Any]]:
	"""PLN-DES-14 — baseline / forecast / actual / variance per milestone."""
	rows = []
	for index, m in enumerate(MILESTONES):
		baseline = item.get(f"baseline_{m}_date")
		forecast = item.get(f"forecast_{m}_date")
		actual = item.get(f"actual_{m}_date")
		rows.append(
			{
				"milestone": m,
				"label": MILESTONE_LABELS[m],
				"baseline": cstr(baseline),
				"forecast": cstr(forecast),
				"actual": cstr(actual),
				"variance_baseline_days": date_diff(getdate(actual), getdate(baseline)) if actual and baseline else None,
				"variance_forecast_days": date_diff(getdate(actual), getdate(forecast)) if actual and forecast else None,
				"behind": bool(forecast and baseline and not actual and getdate(forecast) > getdate(baseline)),
				"can_shift": bool(forecast) and not actual,  # §5.5.1: a final-milestone single-row change is allowed with a reason
			}
		)
	return rows


def _cascade_rows(item, milestone: str, new_date) -> list[dict[str, Any]]:
	if milestone not in MILESTONES:
		fail("PLN_SCHEDULE_INVALID", "Unknown milestone.")
	if item.get(f"actual_{milestone}_date"):
		fail("PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE")
	current = item.get(f"forecast_{milestone}_date")
	if not current:
		fail("PLN_SCHEDULE_INVALID", "Forecast dates exist only on an Active Plan Version.")
	delta = date_diff(getdate(new_date), getdate(current))
	rows = []
	started = False
	for m in MILESTONES:
		if m == milestone:
			started = True
		if not started:
			continue
		if item.get(f"actual_{m}_date"):
			continue  # invariant 12c-ii: never proposed, simply absent
		forecast = item.get(f"forecast_{m}_date")
		if not forecast:
			continue
		rows.append(
			{
				"milestone": m,
				"label": MILESTONE_LABELS[m],
				"current_forecast": cstr(forecast),
				"proposed_forecast": cstr(add_days(getdate(forecast), delta)),
				"included": True,
				"is_anchor": m == milestone,
			}
		)
	return rows


def preview_forecast_cascade(*, plan_item: str, milestone: str, new_forecast_date, user: str | None = None) -> dict[str, Any]:
	"""§8.2 `PreviewForecastCascade` — non-mutating (PLN-AC-124/125)."""
	from kentender_procurement.procurement_planning.services import plan_read, planning_authorization
	from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

	principal = planning_authorization.actor(user)
	item = frappe.get_doc("Annual Plan Item", plan_read.resolve_item_doc_name(plan_item))
	planning_authorization.require_site_role(ROLE_PROCUREMENT_PLANNER, principal)
	version_status = frappe.db.get_value("Annual Plan Version", item.plan_version, "version_status")
	if version_status != "Active" or item.item_state != "Active":
		fail("PLN_STALE_WRITE", "Forecast dates can be shifted only on the Active Plan Version.")
	rows = _cascade_rows(item, milestone, new_forecast_date)
	return {
		"outcome": "OK",
		"plan_item_id": item.plan_item_id,
		"milestone": milestone,
		"milestone_label": MILESTONE_LABELS[milestone],
		"new_forecast_date": cstr(getdate(new_forecast_date)),
		"delta_days": date_diff(getdate(new_forecast_date), getdate(item.get(f"forecast_{milestone}_date"))),
		"rows": rows,
		"record_version": int(item.record_version or 0),
	}


def _validate_governed_gaps(item, new_forecasts: dict[str, Any]) -> None:
	"""§5.5.1 — every affected adjacency of the resulting schedule (included
	and excluded rows alike) is re-validated against the item's frozen
	schedule profile, applicable milestones in profile order. An honest late
	forecast is allowed; only a rule-breaking gap or a disordered sequence is
	refused."""
	from kentender_procurement.procurement_planning.services import profiles

	profile = profiles.schedule_profile_by_name(cstr(item.get("schedule_profile_version")))
	order = profiles.applicable_milestones(profile)
	dates = {m: getdate(new_forecasts.get(m) or item.get(f"forecast_{m}_date")) for m in order if (new_forecasts.get(m) or item.get(f"forecast_{m}_date"))}
	rules = profiles.period_rules(profile)
	previous = None
	for m in order:
		if m not in dates:
			continue
		if previous is not None:
			gap = date_diff(dates[m], dates[previous])
			key = profiles.settings.PERIOD_BY_MILESTONE.get(m, "")
			rule = rules.get(key, {})
			if rule.get("minimum_days") is not None and gap < int(rule["minimum_days"]):
				profiles._period_invalid(key, "minimum", int(rule["minimum_days"]), gap, field=m, reference=cstr(rule.get("statutory_reference")))
			if rule.get("maximum_days") is not None and gap > int(rule["maximum_days"]):
				profiles._period_invalid(key, "maximum", int(rule["maximum_days"]), gap, field=m, reference=cstr(rule.get("statutory_reference")))
		previous = m
	ordered = [dates[m] for m in order if m in dates]
	if ordered != sorted(ordered):
		fail("PLN_SCHEDULE_INVALID", detail={"field": "milestone"})


def confirm_forecast_cascade(
	*,
	plan_item: str,
	milestone: str,
	new_forecast_date,
	included_milestones: list[str] | str | None,
	reason: str,
	expected_record_version,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	"""§8.2 `ConfirmForecastCascade` — atomic; one `PlanItemForecastRevision`
	per included row sharing one `cascade_id` (null when only the anchor is
	included — invariant 12c-iv); touches no baseline or actual field."""
	import json

	from kentender_procurement.procurement_planning.services import envelope, plan_read, planning_authorization
	from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER

	principal = planning_authorization.actor(user)
	if isinstance(included_milestones, str):
		included_milestones = json.loads(included_milestones) if included_milestones.strip() else None
	included = list(included_milestones) if included_milestones is not None else None
	reason = cstr(reason).strip()
	payload = {
		"plan_item": plan_item, "milestone": milestone, "new_forecast_date": cstr(new_forecast_date),
		"included": sorted(included) if included is not None else None, "reason": reason,
	}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (20 <= len(reason) <= 500):
		fail("PLN_FORECAST_REASON_REQUIRED")

	item = envelope.locked("Annual Plan Item", plan_read.resolve_item_doc_name(plan_item))
	planning_authorization.require_site_role(ROLE_PROCUREMENT_PLANNER, principal)
	version_status = frappe.db.get_value("Annual Plan Version", item.plan_version, "version_status")
	if version_status != "Active" or item.item_state != "Active":
		fail("PLN_STALE_WRITE", "Forecast dates can be shifted only on the Active Plan Version.")
	envelope.check_record_version(item, expected_record_version)

	proposal = _cascade_rows(item, milestone, new_forecast_date)
	proposable = {row["milestone"] for row in proposal}
	if included is None:
		included = sorted(proposable, key=MILESTONES.index)
	for m in included:
		if m not in MILESTONES:
			fail("PLN_SCHEDULE_INVALID", "Unknown milestone.")
		if item.get(f"actual_{m}_date"):
			fail("PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE")
		if m not in proposable:
			fail("PLN_SCHEDULE_INVALID", "Only the revised milestone and later milestones may be included.")
	if milestone not in included:
		fail("PLN_SCHEDULE_INVALID", "The revised milestone itself is always included.")

	new_forecasts = {row["milestone"]: row["proposed_forecast"] for row in proposal if row["milestone"] in included}
	_validate_governed_gaps(item, new_forecasts)

	cascade_id = uuid.uuid4().hex if len(included) > 1 else None
	written = []
	for m in sorted(included, key=MILESTONES.index):
		previous = item.get(f"forecast_{m}_date")
		revision = frappe.get_doc(
			{
				"doctype": "Plan Item Forecast Revision",
				"plan_item": item.name,
				"plan_item_id": item.plan_item_id,
				"milestone": m,
				"previous_forecast_date": previous,
				"new_forecast_date": getdate(new_forecasts[m]),
				"reason": reason,
				"cascade_id": cascade_id,
				"revised_by": principal,
				"revised_at": now_datetime(),
				"fixture_namespace": cstr(item.fixture_namespace),
			}
		).insert(ignore_permissions=True)
		written.append(revision.name)
		item.set(f"forecast_{m}_date", getdate(new_forecasts[m]))
	envelope.bump(item)
	result = {
		"ok": True, "idempotent": False, "action": "forecast_shifted", "plan_item": item.plan_item_id,
		"cascade_id": cascade_id or "", "revisions": written, "record_version": int(item.record_version or 0),
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ConfirmForecastCascade", payload=payload,
		result=result, document_type="Annual Plan Item", document_name=item.name,
		actor=principal, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


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
	frappe.db.set_value("Annual Plan Item", name, f"actual_{milestone}_date", getdate(actual_date), update_modified=False)
	status = "Completed" if milestone == "delivery_completion" else "In progress"
	frappe.db.set_value("Annual Plan Item", name, "item_status", status, update_modified=False)

	from kentender_procurement.procurement_planning.services import notifications

	notifications.clear_milestone_notice(plan_item_id=plan_item_id, milestone=milestone, proceeding_id="")
	if proceeding_id:
		notifications.clear_milestone_notice(plan_item_id=plan_item_id, milestone=milestone, proceeding_id=proceeding_id)

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


# --------------------------------------------------------------------------
# §8.3 scheduled nudge
# --------------------------------------------------------------------------


def check_approaching_milestones(*, today=None) -> dict[str, Any]:
	"""`CheckApproachingMilestones` — daily; one notification per approaching
	milestone per day at most (PLN-AC-130), and one evolving `Milestone
	Notice` per recipient/item/milestone (plan D11, §5.5.1B), covering the
	pre-proceeding case the rule names first ("use the item's current
	forecast or approved baseline if unrevised"). Following an in-flight
	proceeding's own identified schedule once one exists is a further
	integration this MVP defers — proceedings carry no forecast of their
	own yet. Creates no task or state; a missed reminder blocks nothing."""
	from kentender_procurement.procurement_planning.services import notifications

	from kentender_core.services.procurement_settings import get_reminder_threshold_days

	today = getdate(today or nowdate())
	threshold = get_reminder_threshold_days()  # §5.5.1B: governed configuration, not a statutory period
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"item_state": "Active"},
		fields=["name", "plan_item", "plan_item_id", "title", "plan_version", "fixture_namespace", *FORECAST_FIELDS, *ACTUAL_FIELDS],
		limit_page_length=0,
	)
	raised = []
	for item in items:
		for m in MILESTONES:
			if item.get(f"actual_{m}_date"):
				continue
			forecast = item.get(f"forecast_{m}_date")
			if not forecast:
				continue
			days = date_diff(getdate(forecast), today)
			if days <= threshold:
				status = "Overdue" if days < 0 else ("Due today" if days == 0 else "Approaching")
				notifications.upsert_milestone_notice(item=item, milestone=m, proceeding_id="", due_date=forecast, status=status, evaluated_at=now_datetime())
				if days >= 0:
					notifications.notify_approaching_milestone(item, m, forecast, days, today)
				raised.append((item.plan_item_id, m))
			break  # only the next milestone with no actual (§8.3)
	return {"raised": raised, "checked": len(items)}
