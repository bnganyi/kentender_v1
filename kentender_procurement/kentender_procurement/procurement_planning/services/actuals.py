# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §4.8/§5.5.1A — actuals recorded per procurement
proceeding, and the distinct variance measures derived from them (plan D10).

`Milestone Actual Event` is the fact of record: producer + event id unique
(DB index `pln_uniq_actual_event`), append-only, a correction names the
event it supersedes rather than overwriting it. `Proceeding Coverage` is the
read-only projection of what an authorised proceeding covers, upserted from
the owner-supplied coverage rows on the same event (unique on
(proceeding_type, proceeding_id, allocation) — index `pln_uniq_coverage`).

Two Tenders for the same stable item keep two independent actual dates
(§5.5.1A's own example: 100 and 150 laptops, invitation actuals on 1 May and
1 September). The four variance measures below never guess at a missing
date: `NOT_AVAILABLE` means the evidence is absent, `NOT_APPLICABLE` means
the stage does not apply — neither is zero.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, date_diff, getdate, now_datetime

from kentender_procurement.procurement_planning.errors import fail

NOT_AVAILABLE = "Not available"
NOT_APPLICABLE = "Not applicable"


def record_actual_event(
	*,
	item,
	producer: str,
	event_id: str,
	milestone: str,
	actual_date,
	proceeding_type: str = "",
	proceeding_id: str = "",
	requisition_reference: str = "",
	allocation: str = "",
	producer_sequence: int = 0,
	supersedes_event_id: str = "",
	source_evidence_reference: str = "",
) -> dict[str, Any]:
	"""§4.8 `MilestoneActualEvent` — idempotent on `(producer, event_id)`; a
	repeated event id returns the earlier row unchanged. `item` is the
	Active `Annual Plan Item` doc the event belongs to (the caller has
	already resolved and validated it)."""
	producer = cstr(producer).strip()
	event_id = cstr(event_id).strip()
	existing = frappe.db.get_value("Milestone Actual Event", {"producer": producer, "event_id": event_id}, "name")
	if existing:
		return {"event": existing, "idempotent": True}
	event = frappe.get_doc(
		{
			"doctype": "Milestone Actual Event", "producer": producer, "event_id": event_id,
			"schema_version": "MilestoneActualEvent.v1", "proceeding_type": cstr(proceeding_type).strip(),
			"proceeding_id": cstr(proceeding_id).strip(), "requisition_reference": cstr(requisition_reference).strip(),
			"plan_version": item.plan_version, "plan_item": item.plan_item, "plan_item_id": item.plan_item_id,
			"allocation": allocation or None, "milestone": milestone, "actual_date": getdate(actual_date),
			"recorded_at": now_datetime(), "producer_sequence": int(producer_sequence or 0),
			"supersedes_event_id": cstr(supersedes_event_id).strip(), "source_evidence_reference": cstr(source_evidence_reference).strip(),
			"fixture_namespace": cstr(item.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	return {"event": event.name, "idempotent": False}


def upsert_coverage(
	*,
	item,
	proceeding_type: str,
	proceeding_id: str,
	allocation: str,
	requisition_reference: str = "",
	requisition_version: str = "",
	covered_quantity=None,
	covered_value=None,
	authorisation_state: str = "",
	publication_state: str = "",
	reversal_state: str = "",
	last_event: str = "",
) -> str:
	"""§4.8 `ProceedingCoverage` — a read-only operational projection, one
	row per (proceeding, allocation); the owner supplies the covered
	quantity/value and current authorisation/publication/reversal evidence
	on every call, never inferred here from the stable item link alone."""
	proceeding_type = cstr(proceeding_type).strip()
	proceeding_id = cstr(proceeding_id).strip()
	filters = {"proceeding_type": proceeding_type, "proceeding_id": proceeding_id, "allocation": allocation}
	values = {
		"requisition_reference": requisition_reference, "requisition_version": requisition_version,
		"plan_version": item.plan_version, "plan_item": item.plan_item, "plan_item_id": item.plan_item_id,
		"covered_quantity": covered_quantity, "covered_value": covered_value,
		"authorisation_state": authorisation_state, "publication_state": publication_state,
		"reversal_state": reversal_state, "last_event": last_event or None,
	}
	existing = frappe.db.get_value("Proceeding Coverage", filters, "name")
	if existing:
		frappe.db.set_value("Proceeding Coverage", existing, values, update_modified=False)
		return existing
	doc = frappe.get_doc(
		{"doctype": "Proceeding Coverage", **filters, **values, "fixture_namespace": cstr(item.fixture_namespace)}
	).insert(ignore_permissions=True)
	return doc.name


def baseline_lateness_days(actual_date, baseline_date, *, applicable: bool = True):
	"""Actual milestone date − baseline milestone date; positive is late."""
	if not applicable:
		return NOT_APPLICABLE
	if not actual_date or not baseline_date:
		return NOT_AVAILABLE
	return date_diff(getdate(actual_date), getdate(baseline_date))


# PLN-CHG-001 v1.23 §10.13 / §15.3 (PLN23-CHG-001): there is no forecast tier
# in the MVP, so there is no forecast-error measure. A future facility that
# reintroduces forecasts must compare against the exact revision in force when
# the proceeding's actual was recorded (§5.5.1A: "never substitute ... a
# forecast revised after the event"), never the latest one.


def elapsed_days(start_date, end_date, *, applicable: bool = True):
	"""Between two explicitly defined events, on the applicable profile's
	counting rule (calendar days here; a working-day rule is a future
	profile-driven refinement, not part of this MVP measure)."""
	if not applicable:
		return NOT_APPLICABLE
	if not start_date or not end_date:
		return NOT_AVAILABLE
	return date_diff(getdate(end_date), getdate(start_date))


def duration_variance_days(planned_start, planned_end, actual_start, actual_end, *, applicable: bool = True):
	"""Planned elapsed days − actual elapsed days; negative means the stage
	took longer (the sign convention recorded in the supplied LAW register).
	Never populate a statutory duration field with simple milestone-date
	lateness — this is a distinct measure from `baseline_lateness_days`."""
	if not applicable:
		return NOT_APPLICABLE
	planned = elapsed_days(planned_start, planned_end)
	actual = elapsed_days(actual_start, actual_end)
	if planned == NOT_AVAILABLE or actual == NOT_AVAILABLE:
		return NOT_AVAILABLE
	return planned - actual


def proceeding_events(plan_item_id: str, proceeding_id: str) -> dict[str, dict[str, Any]]:
	"""The current (non-superseded) actual per milestone for one proceeding:
	the highest `producer_sequence` row not itself named as a
	`supersedes_event_id` by a later row — replay can never resurrect an
	event a correction has superseded."""
	rows = frappe.get_all(
		"Milestone Actual Event",
		filters={"plan_item_id": plan_item_id, "proceeding_id": proceeding_id},
		fields=["name", "event_id", "milestone", "actual_date", "producer_sequence", "supersedes_event_id"],
		order_by="producer_sequence asc, creation asc",
	)
	superseded_ids = {r.supersedes_event_id for r in rows if cstr(r.supersedes_event_id).strip()}
	current: dict[str, dict[str, Any]] = {}
	for row in rows:
		if cstr(row.event_id) in superseded_ids:
			continue
		current[row.milestone] = row
	return current


def proceeding_variance(plan_item_id: str, proceeding_id: str) -> list[dict[str, Any]]:
	"""§5.5.1A's per-proceeding table: the approved baseline, the owner-
	supplied actual and the three labelled measures for every milestone the
	item's resolved schedule profile makes applicable — the shape U14
	renders under its own explicit labels, never an unexplained "Variance"
	heading. Forecast comparison is absent from the MVP (§10.13)."""
	from kentender_procurement.procurement_planning.services import profiles, schedule

	item = frappe.get_doc("Annual Plan Item", {"plan_item_id": plan_item_id})
	resolved_profile = profiles.schedule_profile_by_name(cstr(item.schedule_profile_version)) if item.schedule_profile_version else {"found": False}
	applicable = set(profiles.applicable_milestones(resolved_profile)) if resolved_profile.get("found") else set(schedule.MILESTONES)
	events = proceeding_events(plan_item_id, proceeding_id)

	rows = []
	previous_actual = None
	previous_applicable_milestone = None
	for m in schedule.MILESTONES:
		is_applicable = m in applicable
		baseline = item.get(f"baseline_{m}_date")
		event = events.get(m)
		actual = event.actual_date if event else None
		rows.append(
			{
				"milestone": m, "applicable": is_applicable,
				"baseline": cstr(baseline), "actual": cstr(actual),
				"event": event.name if event else "", "event_id": event.event_id if event else "",
				"baseline_lateness_days": baseline_lateness_days(actual, baseline, applicable=is_applicable),
				"elapsed_since_previous_days": elapsed_days(previous_actual, actual, applicable=is_applicable and previous_actual is not None),
				"duration_variance_since_previous_days": duration_variance_days(
					item.get(f"baseline_{previous_applicable_milestone}_date") if previous_applicable_milestone else None, baseline,
					previous_actual, actual, applicable=is_applicable and previous_actual is not None,
				),
			}
		)
		if is_applicable and actual:
			previous_actual = actual
			previous_applicable_milestone = m
	return rows
