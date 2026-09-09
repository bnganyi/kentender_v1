# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §9.5/§15 — the Tender Preparation outbox: one row per
published event, keyed by correlation ID so a repeated acknowledgment never
publishes twice (TPR-AC-042)."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

import frappe
from frappe.utils import cstr, now_datetime

EVENT_MILESTONE_ACTUAL = "TenderMilestoneActualPublished.v1"
EVENT_HANDOFF_READY = "TenderPublicationHandoffReady.v1"


def find(event_type: str, correlation_id: str) -> str | None:
	if not correlation_id:
		return None
	return frappe.db.get_value("Tender Preparation Event", {"event_type": event_type, "correlation_id": cstr(correlation_id)}, "name")


def emit(*, event_type: str, tender: str, tender_version: str, payload: dict[str, Any], correlation_id: str = "", consumer: str = "", delivered: bool = False) -> str:
	sequence = (frappe.db.count("Tender Preparation Event", {"tender": tender}) or 0) + 1
	doc = frappe.get_doc(
		{
			"doctype": "Tender Preparation Event", "event_id": f"TPE-{uuid4().hex.upper()}", "event_type": event_type,
			"tender": tender, "tender_version": tender_version, "correlation_id": cstr(correlation_id), "sequence": sequence,
			"occurred_at": now_datetime(), "payload": json.dumps(payload, default=str, sort_keys=True),
			"status": "Delivered" if delivered else "Pending", "consumer": consumer,
			"delivered_at": now_datetime() if delivered else None,
		}
	).insert(ignore_permissions=True)
	return doc.name
