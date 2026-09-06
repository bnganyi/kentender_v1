# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.9/§4.9A/§8.2/§8.3 — the governed baseline / forecast /
actual schedule model.

Baseline: one Planner-set anchor (`baseline_invitation_date`) plus three
governed periods (tendering ≥ 7 days, regulation 86; evaluation ≤ 30 days,
Third Schedule; standstill ≥ 14 days, section 135(3)) and two labelled
planning-assumption buffers derive six of the seven baseline dates; delivery
completion is the department's own required-by date. Locked once the Version
leaves Draft (invariant 12b).

Forecast: null until activation, seeded equal to baseline in the activation
transaction, then changed only through the cascade preview/confirm pair —
every later not-yet-actual milestone is proposed with the same day-delta,
each row includable or excludable, one reason, one `cascade_id` (invariant
12c). Actual: never typed; written only by the §18 projection contract.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
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

# Governed floors and ceilings (§4.9). The system rejects, never silently fixes.
TENDERING_FLOOR = 7
EVALUATION_CEILING = 30
STANDSTILL_FLOOR = 14
# Flat fallbacks where the CFG register holds no category/method entry (§18).
DEFAULT_TENDERING = 21
DEFAULT_EVALUATION = 30
DEFAULT_AWARD_APPROVAL_BUFFER = 5
DEFAULT_NOTIFICATION_BUFFER = 2
DEFAULT_STANDSTILL = 14
# Invariant 12a — the "sensible implementation allowance" between contract
# signing and the department's required-by date. A planning assumption (no
# statutory figure fixes it), labelled as such wherever it is shown; tracker
# decision O7.
MIN_IMPLEMENTATION_ALLOWANCE_DAYS = 7
# §8.3 — days before a forecast milestone at which the daily nudge fires.
APPROACHING_THRESHOLD_DAYS = 14


def default_periods(reference: dict[str, Any] | None, category: str, method: str) -> dict[str, int]:
	"""§4.9 / PLN-AC-131 — buffers from the category/method-keyed register
	where an entry exists, the flat fallbacks otherwise."""
	award, notification = DEFAULT_AWARD_APPROVAL_BUFFER, DEFAULT_NOTIFICATION_BUFFER
	for row in (reference or {}).get("schedule_buffers", []):
		if row.get("procurement_category") == category and row.get("procurement_method") == method:
			award = int(row.get("award_approval_buffer_days") or award)
			notification = int(row.get("notification_buffer_days") or notification)
			break
	return {
		"tendering_period_days": DEFAULT_TENDERING,
		"evaluation_period_days": DEFAULT_EVALUATION,
		"award_approval_buffer_days": award,
		"notification_buffer_days": notification,
		"standstill_period_days": DEFAULT_STANDSTILL,
	}


def validate_periods(periods: dict[str, Any]) -> dict[str, int]:
	"""PLN-AC-114 — server-side floors and ceilings, bound to their field."""
	clean: dict[str, int] = {}
	for field in PERIOD_FIELDS:
		raw = periods.get(field)
		try:
			value = int(raw)
		except (TypeError, ValueError):
			fail("PLN_SCHEDULE_INVALID", f"Enter a whole number of days for {field.replace('_', ' ')}.", {"field": field})
		if value < 0:
			fail("PLN_SCHEDULE_INVALID", "Periods cannot be negative.", {"field": field})
		clean[field] = value
	if clean["tendering_period_days"] < TENDERING_FLOOR:
		fail("PLN_TENDERING_PERIOD_BELOW_MINIMUM", detail={"field": "tendering_period_days"})
	if clean["evaluation_period_days"] > EVALUATION_CEILING:
		fail("PLN_EVALUATION_PERIOD_ABOVE_MAXIMUM", detail={"field": "evaluation_period_days"})
	if clean["standstill_period_days"] < STANDSTILL_FLOOR:
		fail("PLN_STANDSTILL_BELOW_MINIMUM", detail={"field": "standstill_period_days"})
	return clean


def derive_baseline(anchor, periods: dict[str, Any], delivery_date) -> dict[str, Any]:
	"""PLN-AC-115 — the seven baseline dates from the anchor and periods.
	`delivery_date` is the earliest source required-by date (invariant 12).
	Raises the field-bound §9 codes; the delivery-boundary check is reported
	by `delivery_boundary_ok` so a Draft save may keep an incomplete
	schedule while readiness blocks (invariant 12a)."""
	clean = validate_periods(periods)
	if not anchor:
		return {field: None for field in BASELINE_FIELDS} | {"baseline_delivery_completion_date": getdate(delivery_date) if delivery_date else None}
	start = getdate(anchor)
	bid = add_days(start, clean["tendering_period_days"])
	evaluation = add_days(bid, clean["evaluation_period_days"])
	award = add_days(evaluation, clean["award_approval_buffer_days"])
	notification = add_days(award, clean["notification_buffer_days"])
	signing = add_days(notification, clean["standstill_period_days"])
	return {
		"baseline_invitation_date": start,
		"baseline_bid_opening_date": getdate(bid),
		"baseline_evaluation_completion_date": getdate(evaluation),
		"baseline_award_approval_date": getdate(award),
		"baseline_award_notification_date": getdate(notification),
		"baseline_contract_signing_date": getdate(signing),
		"baseline_delivery_completion_date": getdate(delivery_date) if delivery_date else None,
	}


def delivery_boundary_ok(baseline: dict[str, Any]) -> bool:
	signing = baseline.get("baseline_contract_signing_date")
	delivery = baseline.get("baseline_delivery_completion_date")
	if not signing or not delivery:
		return False
	return date_diff(getdate(delivery), getdate(signing)) >= MIN_IMPLEMENTATION_ALLOWANCE_DAYS


def baseline_complete(item) -> bool:
	return all(item.get(field) for field in BASELINE_FIELDS)


def require_delivery_boundary(baseline: dict[str, Any]) -> None:
	if not delivery_boundary_ok(baseline):
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
				"can_shift": bool(forecast) and not actual and index < len(MILESTONES) - 1,
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
	"""Invariant 12c-iii — an included later row is re-validated against the
	same floors/ceilings as baseline derivation, against its new predecessor."""
	dates = {m: getdate(new_forecasts.get(m) or item.get(f"forecast_{m}_date")) for m in MILESTONES if (new_forecasts.get(m) or item.get(f"forecast_{m}_date"))}
	if "invitation" in dates and "bid_opening" in dates and date_diff(dates["bid_opening"], dates["invitation"]) < TENDERING_FLOOR:
		fail("PLN_TENDERING_PERIOD_BELOW_MINIMUM", detail={"field": "bid_opening"})
	if "bid_opening" in dates and "evaluation_completion" in dates and date_diff(dates["evaluation_completion"], dates["bid_opening"]) > EVALUATION_CEILING:
		fail("PLN_EVALUATION_PERIOD_ABOVE_MAXIMUM", detail={"field": "evaluation_completion"})
	if "award_notification" in dates and "contract_signing" in dates and date_diff(dates["contract_signing"], dates["award_notification"]) < STANDSTILL_FLOOR:
		fail("PLN_STANDSTILL_BELOW_MINIMUM", detail={"field": "contract_signing"})
	ordered = [dates[m] for m in MILESTONES if m in dates]
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


def record_tender_milestone_actual(*, plan_item_id: str, milestone: str, actual_date, source_event_id: str) -> dict[str, Any]:
	"""§8.2 `RecordTenderMilestoneActual` — inbound only (§18): writes the one
	matching actual date from an owning module's projection. No publisher
	exists in MVP-1; the shape is fixed so TPR-CHG-001 can implement against
	it. Never callable from a user-facing endpoint (PLN-AC-119)."""
	if milestone not in MILESTONES:
		fail("PLN_SCHEDULE_INVALID", "Unknown milestone.")
	name = frappe.db.get_value("Annual Plan Item", {"plan_item_id": plan_item_id, "item_state": "Active"}, "name")
	if not name:
		fail("PLN_STALE_WRITE", "No Active Plan Item carries that id.")
	frappe.db.set_value("Annual Plan Item", name, f"actual_{milestone}_date", getdate(actual_date), update_modified=False)
	status = "Completed" if milestone == "delivery_completion" else "In progress"
	frappe.db.set_value("Annual Plan Item", name, "item_status", status, update_modified=False)
	return {"ok": True, "plan_item": plan_item_id, "milestone": milestone, "source_event_id": source_event_id}


# --------------------------------------------------------------------------
# §8.3 scheduled nudge
# --------------------------------------------------------------------------


def check_approaching_milestones(*, today=None) -> dict[str, Any]:
	"""`CheckApproachingMilestones` — daily; one notification per approaching
	milestone per day at most (PLN-AC-130); creates no task or state."""
	from kentender_procurement.procurement_planning.services import notifications

	today = getdate(today or nowdate())
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"item_state": "Active"},
		fields=["name", "plan_item_id", "title", "plan_version", *FORECAST_FIELDS, *ACTUAL_FIELDS],
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
			if 0 <= days <= APPROACHING_THRESHOLD_DAYS:
				notifications.notify_approaching_milestone(item, m, forecast, days, today)
				raised.append((item.plan_item_id, m))
			break  # only the next milestone with no actual (§8.3)
	return {"raised": raised, "checked": len(items)}
