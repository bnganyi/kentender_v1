"""Departmental Needs published event contracts (NDS-CHG-001 v1.1 §7.1).

This module is the **published handoff contract** named by the firm D1
decision. Downstream modules — Procurement Planning above all — consume
accepted Needs through `consume_events()` and `acknowledge()` here, or through
`get_current_accepted_need` (§8.1). They never read Departmental Needs
DocTypes, tables or internal services directly.

Delivery is a transactional outbox: `publish_*` appends a row inside the same
transaction as the command's state change and decision record, so an event
exists if and only if the change committed, and no separate "did we send it?"
question can arise. Events are ordered per Need by a monotonic `sequence` taken
while the command still holds the Need's row lock, and are idempotent because
each carries a unique `event_id` that a consumer records against its own
projection.

The three contracts (§7.1):

- `DepartmentalNeedAccepted.v2` — the accepted source payload. It carries the
  expected operational result (NDS-AC-038) and none of the excluded concepts
  (NDS-AC-024).
- `DepartmentalNeedSuperseded.v1` — Need, earlier accepted version and hash,
  successor accepted version and hash, plus the successor accepted payload.
- `DepartmentalNeedWithdrawn.v1` — the withdrawn accepted version and the
  withdrawal decision.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, flt, now_datetime

from kentender_procurement.departmental_needs.errors import fail

EVENT_ACCEPTED = "DepartmentalNeedAccepted.v2"
EVENT_SUPERSEDED = "DepartmentalNeedSuperseded.v1"
EVENT_WITHDRAWN = "DepartmentalNeedWithdrawn.v1"

EVENT_TYPES = frozenset({EVENT_ACCEPTED, EVENT_SUPERSEDED, EVENT_WITHDRAWN})

STATUS_PENDING = "Pending"
STATUS_DELIVERED = "Delivered"


def _next_sequence(need: str) -> int:
	"""Monotonic per Need (§7.1).

	Safe without extra locking because every publisher is inside a command that
	already holds `SELECT … FOR UPDATE` on the Need row.
	"""
	rows = frappe.get_all(
		"Departmental Need Event", filters={"departmental_need": need}, pluck="sequence"
	)
	return max([int(value or 0) for value in rows] or [0]) + 1


def accepted_payload(need, version) -> dict[str, Any]:
	"""The exact §7.1 `DepartmentalNeedAccepted.v2` field set — nothing more.

	Deliberately absent: Budget Line, indicative amount, funding source,
	currency, Strategy, requirement type, procurement method, location,
	attachment, source reference, generic evidence and notes (NDS-AC-024).
	"""
	unit_label = cstr(frappe.db.get_value("UOM", version.unit, "uom_name") or version.unit or "")
	return {
		"need_id": need.name,
		"need_reference": need.need_reference,
		"accepted_version_id": version.name,
		"version_number": int(version.version_number or 0),
		"content_hash": cstr(version.content_hash),
		"org_unit_id": need.organisation_unit,
		"financial_year_id": need.financial_year,
		"title": cstr(version.title),
		"description": cstr(version.description),
		"expected_operational_result": cstr(version.expected_operational_result),
		"indicative_quantity": flt(version.indicative_quantity),
		"unit_id": cstr(version.unit),
		"unit_display_value": unit_label,
		"required_by_date": str(version.required_by_date or ""),
	}


def _append(
	need,
	*,
	event_type: str,
	payload: dict[str, Any],
	version: str = "",
	superseded_version: str = "",
) -> str:
	if event_type not in EVENT_TYPES:
		raise ValueError(f"{event_type!r} is not a published Departmental Needs event contract.")
	occurred_at = now_datetime()
	event_id = f"NDE-{uuid4().hex.upper()}"
	body = {
		"event_id": event_id,
		"event_type": event_type,
		"occurred_at": str(occurred_at),
		**payload,
	}
	frappe.get_doc(
		{
			"doctype": "Departmental Need Event",
			"event_id": event_id,
			"event_type": event_type,
			"departmental_need": need.name,
			"sequence": _next_sequence(need.name),
			"need_version": version or None,
			"superseded_version": superseded_version or None,
			"occurred_at": occurred_at,
			"payload": json.dumps(body, sort_keys=True, indent=None),
			"status": STATUS_PENDING,
			"fixture_namespace": need.fixture_namespace,
		}
	).insert(ignore_permissions=True)
	return event_id


# --- publishers, called from the command layer -----------------------------


def publish_accepted(need, version) -> str:
	"""§7.1 — a version became the current accepted source."""
	return _append(
		need, event_type=EVENT_ACCEPTED, payload=accepted_payload(need, version), version=version.name
	)


def publish_superseded(need, *, earlier, successor) -> str:
	"""§7.1 — exact old/new lineage plus the successor accepted payload.

	NDS-BR-015 requires this to be atomic with the acceptance that caused it,
	which the shared transaction guarantees.
	"""
	return _append(
		need,
		event_type=EVENT_SUPERSEDED,
		payload={
			"need_id": need.name,
			"need_reference": need.need_reference,
			"earlier_accepted_version_id": earlier.name,
			"earlier_content_hash": cstr(earlier.content_hash),
			"successor_accepted_version_id": successor.name,
			"successor_content_hash": cstr(successor.content_hash),
			"successor_accepted_payload": accepted_payload(need, successor),
		},
		version=successor.name,
		superseded_version=earlier.name,
	)


def publish_withdrawn(need, *, version, withdrawal_request: str, decided_by: str) -> str:
	"""§7.1 — the withdrawn accepted version and the withdrawal decision.

	§5.3 guarantees an Active Plan dependency was cleared before this can exist.
	"""
	return _append(
		need,
		event_type=EVENT_WITHDRAWN,
		payload={
			"need_id": need.name,
			"need_reference": need.need_reference,
			"withdrawn_version_id": version.name if version else "",
			"content_hash": cstr(version.content_hash) if version else "",
			"withdrawal_request_id": cstr(withdrawal_request),
			"decided_by": cstr(decided_by),
		},
		version=version.name if version else "",
	)


# --- the consumer side of the published contract ---------------------------


def consume_events(
	*,
	consumer: str,
	need: str = "",
	after_sequence: int | None = None,
	limit: int = 200,
) -> dict[str, Any]:
	"""Drain pending events in per-Need order (§7.1). Does not acknowledge.

	A consumer applies each payload against its own projection, keyed by
	`event_id` so a redelivery is a no-op, then calls `acknowledge()`. Nothing
	is marked delivered until the consumer says so, which is what makes an
	interrupted consumer safe to retry.
	"""
	if not cstr(consumer).strip():
		fail("NDS_FIELD_REQUIRED", "A consumer identifier is required.")
	filters: dict[str, Any] = {"status": STATUS_PENDING}
	if cstr(need).strip():
		filters["departmental_need"] = cstr(need).strip()
	if after_sequence is not None:
		filters["sequence"] = (">", int(after_sequence))
	rows = frappe.get_all(
		"Departmental Need Event",
		filters=filters,
		fields=["name", "event_id", "event_type", "departmental_need", "sequence", "payload"],
		# Per-Need ordering is the contract; `creation` disambiguates across Needs.
		order_by="departmental_need asc, sequence asc",
		limit_page_length=int(limit),
	)
	return {
		"ok": True,
		"consumer": cstr(consumer).strip(),
		"events": [
			{
				"event_id": row.event_id,
				"event_type": row.event_type,
				"need_id": row.departmental_need,
				"sequence": row.sequence,
				"payload": json.loads(row.payload),
			}
			for row in rows
		],
	}


def acknowledge(*, consumer: str, event_ids: list[str] | str) -> dict[str, Any]:
	"""Mark events delivered once the consumer has durably applied them."""
	name = cstr(consumer).strip()
	if not name:
		fail("NDS_FIELD_REQUIRED", "A consumer identifier is required.")
	ids = json.loads(event_ids) if isinstance(event_ids, str) else list(event_ids or [])
	if not ids:
		return {"ok": True, "acknowledged": []}
	rows = frappe.get_all(
		"Departmental Need Event",
		filters={"event_id": ("in", ids), "status": STATUS_PENDING},
		pluck="name",
	)
	now = now_datetime()
	for row in rows:
		frappe.db.set_value(
			"Departmental Need Event",
			row,
			{"status": STATUS_DELIVERED, "consumer": name, "delivered_at": now},
			update_modified=False,
		)
	return {"ok": True, "acknowledged": rows}


def current_accepted_events(*, financial_year: str, organisation_unit: str = "") -> list[dict[str, Any]]:
	"""Every Need currently accepted in one context, as §7.1 payloads.

	The published way for a consumer to rebuild or reconcile its projection —
	for example a Plan being drafted after the original events were delivered.
	It replays from the outbox rather than querying Need tables, so the caller
	sees exactly what the event stream said. The site Procuring Entity is
	implicit (AUTH-ADR-001 v1.6 §1.1) — there is no `procuring_entity` filter.
	"""
	needs = frappe.get_all(
		"Departmental Need",
		filters={
			"financial_year": cstr(financial_year),
			**({"organisation_unit": cstr(organisation_unit)} if organisation_unit else {}),
			"current_state": "Accepted for planning",
		},
		fields=["name", "current_accepted_version"],
		order_by="need_reference asc",
		limit_page_length=0,
	)
	out = []
	for row in needs:
		if not row.current_accepted_version:
			continue
		event = frappe.db.get_value(
			"Departmental Need Event",
			{
				"departmental_need": row.name,
				"event_type": EVENT_ACCEPTED,
				"need_version": row.current_accepted_version,
			},
			"payload",
			order_by="sequence desc",
		)
		if event:
			out.append(json.loads(event))
	return out
