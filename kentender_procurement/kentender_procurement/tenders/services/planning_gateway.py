# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §3 "Actual invitation date" / §5.5(7) — the one seam to
Planning's published `RecordTenderMilestoneActual` event envelope
(PLN-CHG-001 v1.20 §4.8). The actual invitation date is published exactly
once per publication through an outbox `Tender Event`; replay or recovery
emits nothing new because the event id is deterministic
(`<publication>:invitation`) and Planning is idempotent on
`(producer, event_id)`. A refusal on Planning's side is recorded truthfully
on the event (TPR08-AC-079), never retried as a different fact."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, getdate

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import schedule
from kentender_procurement.tenders.services import events

CONSUMER = "planning"
EVENT_TYPE = "TenderPublished"
PROCEEDING_TYPE = "Tender"


def event_id_for(publication: str) -> str:
	return f"{publication}:invitation"


def publish_invitation_actual(*, root, publication, published_at, actor: str, idempotency_key: str) -> dict[str, Any]:
	"""Write the outbox event (once) and deliver it to Planning (once)."""
	event_id = event_id_for(publication.name)
	existing = [e for e in events.pending(tender=root.name, event_type=EVENT_TYPE, consumer=CONSUMER)]
	delivered = frappe.get_all("Tender Event", filters={"tender": root.name, "event_type": EVENT_TYPE, "consumer": CONSUMER, "status": "Delivered"}, pluck="name")
	if delivered:
		return {"ok": True, "idempotent": True, "event": delivered[0]}
	event = existing[0] if existing else events.emit(
		tender=root.name, event_type=EVENT_TYPE, command="ConfirmTenderPublished", idempotency_key=idempotency_key, actor=actor,
		previous_status="Publication authorised", resulting_status="Published — open", record_version=root.record_version,
		subject_type="Tender Publication", subject_id=publication.name, status="Pending", consumer=CONSUMER,
		payload={"planning_event_id": event_id, "plan_item_id": root.plan_item_id, "milestone": "invitation", "actual_date": str(getdate(published_at)), "proceeding_id": root.tender_reference, "package_digest": publication.package_digest},
		fixture_namespace=root.fixture_namespace,
	)
	coverage = _coverage(root)
	try:
		result = schedule.record_tender_milestone_actual(
			plan_item_id=cstr(root.plan_item_id), milestone="invitation", actual_date=getdate(published_at), source_event_id=event_id, producer=events.PRODUCER,
			proceeding_id=cstr(root.tender_reference), proceeding_type=PROCEEDING_TYPE, producer_sequence=int(event.sequence or 0), coverage=coverage,
		)
	except ProcurementPlanningError as exc:
		events.mark_rejected(event, reason=f"{exc.code}: {exc}")
		return {"ok": False, "event": event.name, "planning_error": exc.code}
	events.mark_delivered(event, consumer=CONSUMER)
	return {"ok": True, "idempotent": bool(result.get("idempotent")), "event": event.name, "planning": result}


def _coverage(root) -> list[dict[str, Any]]:
	"""The exact allocation coverage this proceeding carries (PLN v1.20 §4.8)."""
	from kentender_procurement.tenders.services import snapshot as snap

	version = frappe.get_doc("Tender Version", root.current_version) if root.current_version else None
	if version is None:
		return []
	snapshot = snap.load(version)
	rows = []
	for line in snapshot.get("drawdown_lines") or []:
		allocation = cstr(line.get("plan_item_line_id"))
		if not allocation or not frappe.db.exists("Plan Source Allocation", allocation):
			continue
		rows.append(
			{
				"allocation": allocation, "requisition_reference": cstr(snapshot.get("requisition_reference")), "requisition_version": cstr(version.requisition_version),
				"covered_quantity": line.get("requested_quantity"), "covered_value": line.get("requested_value"), "authorisation_state": "Authorised",
				"publication_state": "Published", "reversal_state": "",
			}
		)
	return rows


def current_invitation_actual(root):
	return schedule.current_proceeding_actual(plan_item_id=cstr(root.plan_item_id), milestone="invitation", proceeding_id=cstr(root.tender_reference))
