# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §9.1B `PlanItemCorrectionOutcome.v1` — the payload
Planning emits from a terminal correction disposition.

The schema is the contract. Delivery is in the same disposition transaction,
to every consumer registered under the `kt_plan_item_correction_outcome_consumers`
hook, so Planning never imports the Requisitions lifecycle. A consumer that
raises rolls the disposition back with it: the outcome is never recorded on
one side only.

`producer_sequence` is the monotonic position of this disposition within the
request's own disposition stream (Start is 1, the terminal outcome follows),
never a wall-clock sort or a UUID.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

SCHEMA_VERSION = 1
PRODUCER = "Procurement Planning"
HOOK = "kt_plan_item_correction_outcome_consumers"


def _utc(value) -> str:
	"""The site stores naive system-timezone datetimes; §9.1B wants a UTC
	instant."""
	from kentender_core.utils.instants import to_utc_iso

	return to_utc_iso(value)


def replacement_lineage(correcting_plan_version: str, plan_item_id: str) -> dict[str, Any]:
	"""The exact eligible stable item, item Version and allocation IDs on the
	correcting Active Plan Version."""
	item = frappe.db.get_value(
		"Annual Plan Item",
		{"plan_item_id": plan_item_id, "plan_version": correcting_plan_version, "item_state": "Active"},
		["name", "plan_item_id"],
		as_dict=True,
	)
	if not item:
		return {}
	allocations = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": item.name, "allocation_state": "Active"},
		fields=["allocation_id", "dpp_entry", "need"],
		order_by="creation asc",
	)
	return {
		"plan_item_id": item.plan_item_id,
		"plan_item_version_id": item.name,
		"allocation_ids": [a.allocation_id for a in allocations],
		"source_replacements": [{"allocation_id": a.allocation_id, "source_line_id": cstr(a.need) or a.dpp_entry} for a in allocations],
	}


def build(
	*,
	request,
	disposition,
	outcome: str,
	hold: dict[str, Any],
	eligibility_revision: int,
	reason: str | None = None,
	correcting_plan_version: str | None = None,
	lineage: dict[str, Any] | None = None,
) -> dict[str, Any]:
	sequence = frappe.db.count("Plan Item Correction Disposition", {"correction_request": request.name})
	return {
		"event_id": disposition.name,
		"schema_version": SCHEMA_VERSION,
		"producer": PRODUCER,
		"producer_sequence": int(sequence),
		"correction_request_id": request.name,
		"requesting_requisition_id": cstr(request.requisition_reference),
		"requesting_requisition_version_id": cstr(request.requisition_version),
		"plan_item_id": cstr(request.plan_item_id),
		"requested_plan_version_id": cstr(request.plan_version),
		"requested_plan_item_version_id": cstr(request.plan_item),
		"outcome": outcome,
		"reason": reason,
		"correcting_plan_version_id": correcting_plan_version,
		"replacement_lineage": lineage,
		"actor": cstr(disposition.actor),
		"decision_at": _utc(disposition.disposed_at),
		"item_hold_state": bool(hold.get("held")),
		"unresolved_request_count": int(hold.get("open_requests") or 0),
		"eligibility_revision": int(eligibility_revision or 0),
	}


def digest(event: dict[str, Any]) -> str:
	import hashlib

	return hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def deliver(event: dict[str, Any]) -> None:
	for path in frappe.get_hooks(HOOK) or []:
		frappe.get_attr(path)(event=event)
