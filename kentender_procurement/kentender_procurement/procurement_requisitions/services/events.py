# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §9.2 — the transactional outbox. Copied from Departmental
Needs' proven pattern (`departmental_needs/services/events.py`): `publish_*`
appends one row inside the same transaction as the state change it records;
the event exists only if that change committed.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime

EVENT_AUTHORISED = "ProcurementRequisitionAuthorised.v1.3"
EVENT_REVOKED = "ProcurementRequisitionRevoked.v1"
EVENT_WITHDRAWN = "ProcurementRequisitionWithdrawn.v1"
EVENT_TYPES = frozenset({EVENT_AUTHORISED, EVENT_REVOKED, EVENT_WITHDRAWN})


def _next_sequence(requisition: str) -> int:
	last = frappe.db.count("Requisition Event", {"requisition": requisition})
	return last + 1


def _append(*, requisition: str, event_type: str, requisition_version: str, payload: dict[str, Any]) -> str:
	if event_type not in EVENT_TYPES:
		raise ValueError(f"{event_type!r} is not a registered Requisition event type.")
	doc = frappe.get_doc(
		{
			"doctype": "Requisition Event", "event_id": f"RQE-{uuid4().hex.upper()}",
			"event_type": event_type, "requisition": requisition,
			"sequence": _next_sequence(requisition), "requisition_version": requisition_version,
			"occurred_at": now_datetime(), "payload": json.dumps(payload, default=str), "status": "Pending",
		}
	).insert(ignore_permissions=True)
	return doc.name


def publish_authorised(*, requisition: str, requisition_version: str, handoff_payload: dict[str, Any]) -> str:
	return _append(requisition=requisition, event_type=EVENT_AUTHORISED, requisition_version=requisition_version, payload=handoff_payload)


def publish_revoked(*, requisition: str, requisition_version: str, reason: str) -> str:
	return _append(requisition=requisition, event_type=EVENT_REVOKED, requisition_version=requisition_version, payload={"reason": reason})


def acknowledge(*, consumer: str, event_ids: list[str]) -> int:
	updated = 0
	for name in event_ids:
		if frappe.db.get_value("Requisition Event", name, "status") == "Pending":
			frappe.db.set_value("Requisition Event", name, {"status": "Delivered", "consumer": consumer, "delivered_at": now_datetime()})
			updated += 1
	return updated
