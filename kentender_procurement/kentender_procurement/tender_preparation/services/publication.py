# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §9.5 / §11.2 — the inbound publication acknowledgment
(`AcknowledgeTenderPublicationConsumed`, from a downstream process that does
not yet exist — TPR FU-06) and the outbound `PublishTenderMilestoneActual`
to Planning. Idempotent by correlation ID; a repeat publishes nothing
(TPR-AC-042/043, SMOKE-17/18)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate, now_datetime, nowdate

from kentender_procurement.tender_preparation.services import envelope, events, planning_gateway
from kentender_procurement.tender_preparation.services.errors import fail


def acknowledge_publication_consumed(*, tender: str, correlation_id: str, published_on=None, user: str | None = None) -> dict[str, Any]:
	correlation_id = cstr(correlation_id).strip()
	if not correlation_id:
		fail("TPR_CONTROL_INVALID", "A correlation ID is required.")
	existing = events.find(events.EVENT_MILESTONE_ACTUAL, correlation_id)
	if existing:
		return {"ok": True, "idempotent": True, "action": "already_acknowledged", "event": existing, "tender": tender}
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		fail("TPR_MILESTONE_ACTUAL_REJECTED", "No such Tender.")
	root = envelope.locked("Prepared Tender", tender)
	if root.current_state != "Approved for publication" or not root.publication_handoff or root.publication_consumed_at:
		fail("TPR_MILESTONE_ACTUAL_REJECTED")
	handoff = envelope.locked("Tender Publication Handoff", root.publication_handoff)
	if handoff.status != "Ready" or handoff.consumed_at:
		fail("TPR_MILESTONE_ACTUAL_REJECTED")

	actual_date = getdate(published_on) if published_on else getdate(nowdate())
	with envelope.atomic("acknowledge_publication"):
		handoff.status = "Consumed"
		handoff.consumed_at = now_datetime()
		handoff.consumption_correlation_id = correlation_id
		handoff.published_on = actual_date
		handoff.save(ignore_permissions=True)
		envelope.bump(root, publication_consumed_at=handoff.consumed_at)
		published = publish_tender_milestone_actual(root=root, actual_date=actual_date, correlation_id=correlation_id)
	return {"ok": True, "idempotent": False, "action": "acknowledged", "tender": root.name, "publication_handoff": handoff.name, "actual_invitation_date": str(actual_date), **published}


def publish_tender_milestone_actual(*, root, actual_date, correlation_id: str) -> dict[str, Any]:
	existing = events.find(events.EVENT_MILESTONE_ACTUAL, correlation_id)
	if existing:
		return {"event": existing, "milestone_published": False}
	planning_gateway.publish_invitation_actual(plan_item_id=root.plan_item_id, actual_date=actual_date, correlation_id=correlation_id)
	event = events.emit(
		event_type=events.EVENT_MILESTONE_ACTUAL, tender=root.name, tender_version=root.approved_version,
		payload={"plan_item_id": root.plan_item_id, "milestone": planning_gateway.MILESTONE_INVITATION, "actual_date": str(getdate(actual_date)), "correlation_id": correlation_id},
		correlation_id=correlation_id, consumer="procurement_planning", delivered=True,
	)
	return {"event": event, "milestone_published": True}
