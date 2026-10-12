# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §7.4B/§9.1B — the Planning correction outcome and the
explicit follow-ups.

`record_plan_item_correction_outcome` is the registered consumer of
`PlanItemCorrectionOutcome.v1`. It authenticates the producer against
Planning's own request record, validates the exact lineage, deduplicates by
event identity and payload, and quarantines anything that does not match —
recording the neutral outcome only. The stopped Version, its status and
digest never change, and receipt never creates a Draft (§9.1B).

`prepare_requisition_after_plan_correction` and
`create_requisition_correction_draft` are the two explicit, guarded
follow-ups: a fresh root after a terminal outcome, and a corrected Draft of a
revoked root whose pinned baseline is still eligible.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import envelope, events, records
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail

SCHEMA_VERSION = 1
PRODUCER = "Procurement Planning"
OUTCOMES = ("Resolved", "Closed without change")
_REQUIRED = (
	"event_id", "schema_version", "producer", "producer_sequence", "correction_request_id", "requesting_requisition_id",
	"requesting_requisition_version_id", "plan_item_id", "requested_plan_version_id", "requested_plan_item_version_id",
	"outcome", "actor", "decision_at",
)


def _digest(event: dict[str, Any]) -> str:
	import hashlib

	return hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _quarantine(event: dict[str, Any], reason: str, root_name: str = "") -> None:
	envelope.insert(frappe.get_doc(
		{
			"doctype": "Requisition Correction Outcome", "event_id": f"Q-{frappe.generate_hash(length=12)}:{cstr(event.get('event_id'))[:80]}",
			"schema_version": int(event.get("schema_version") or 0) if str(event.get("schema_version") or "").isdigit() else 0,
			"producer": cstr(event.get("producer"))[:140], "correction_request_id": cstr(event.get("correction_request_id"))[:140],
			"requisition": root_name or None, "payload_digest": _digest(event), "received_at": now_datetime(),
			"status": "Quarantined", "quarantine_reason": reason,
		}
	))


def _invalid(event: dict[str, Any], reason: str, root_name: str = "") -> dict[str, Any]:
	"""Quarantine and report, never raise: delivery runs inside Planning's
	disposition transaction, and an invalid event must not undo the owner's
	decision or leave no evidence behind (§9.1B "reject/quarantine without
	lifecycle changes")."""
	_quarantine(event, reason, root_name)
	return {"ok": False, "idempotent": False, "action": "quarantined", "code": "REQ_CORRECTION_EVENT_INVALID", "reason": reason}


def record_plan_item_correction_outcome(*, event: dict[str, Any]) -> dict[str, Any]:
	"""The registered `kt_plan_item_correction_outcome_consumers` hook."""
	event = dict(event or {})
	missing = [f for f in _REQUIRED if event.get(f) in (None, "")]
	if missing:
		return _invalid(event, f"Missing {', '.join(missing)}.")
	if event.get("schema_version") != SCHEMA_VERSION:
		return _invalid(event, "Unsupported schema version.")
	if event.get("producer") != PRODUCER:
		return _invalid(event, "Unknown producer.")
	if event.get("outcome") not in OUTCOMES:
		return _invalid(event, "Only a terminal outcome may be recorded.")

	payload_digest = _digest(event)
	existing = frappe.db.get_value("Requisition Correction Outcome", {"event_id": event["event_id"]}, ["name", "payload_digest", "requisition"], as_dict=True)
	if existing:
		if existing.payload_digest == payload_digest:
			return {"ok": True, "idempotent": True, "action": "duplicate", "outcome": existing.name}
		return _invalid(event, "The same event identity arrived with a different payload.", existing.requisition or "")

	# Authenticate against the owner's own record: the request must exist in
	# Planning, belong to this Requisition/Version/item, and carry this outcome.
	from kentender_procurement.procurement_requisitions.services import eligibility_gateway

	facts = eligibility_gateway.correction_request_facts(correction_request=event["correction_request_id"])
	if not facts:
		return _invalid(event, "The correction request is not known to Planning.")
	request = facts[0]
	lineage_ok = (
		request["requisition_reference"] == event["requesting_requisition_id"]
		and request["requisition_version"] == event["requesting_requisition_version_id"]
		and request["plan_item_id"] == event["plan_item_id"]
		and request["plan_version_id"] == event["requested_plan_version_id"]
		and request["plan_item_version_id"] == event["requested_plan_item_version_id"]
		and request["status"] == event["outcome"]
	)
	if not lineage_ok:
		return _invalid(event, "The outcome does not match Planning's request lineage.")
	if event["outcome"] == "Resolved":
		lineage = event.get("replacement_lineage") or {}
		if not event.get("correcting_plan_version_id") or not lineage.get("plan_item_version_id") or not lineage.get("allocation_ids"):
			return _invalid(event, "A Resolved outcome names the Active correcting Plan and its exact replacement lineage.")
	elif not (20 <= len(cstr(event.get("reason")).strip()) <= 1000):
		return _invalid(event, "A Closed-without-change outcome carries the Planner's reason.")

	root_name = frappe.db.get_value("Procurement Requisition", {"requisition_reference": event["requesting_requisition_id"]}, "name")
	if not root_name:
		return _invalid(event, "The requesting Requisition is not known.")
	root = envelope.locked("Procurement Requisition", root_name)
	version_ok = frappe.db.get_value("Requisition Version", event["requesting_requisition_version_id"], ["requisition", "version_status"], as_dict=True)
	if not version_ok or version_ok.requisition != root.name or version_ok.version_status != "Upstream correction required":
		return _invalid(event, "The requesting Version is not the stopped Version of this Requisition.", root.name)

	last = frappe.db.get_value(
		"Requisition Correction Outcome", {"correction_request_id": event["correction_request_id"], "status": "Recorded"}, "producer_sequence",
		order_by="producer_sequence desc",
	)
	if last is not None and int(event["producer_sequence"]) <= int(last):
		return _invalid(event, "Out-of-order outcome: a later outcome for this request is already recorded.", root.name)

	doc = envelope.insert(frappe.get_doc(
		{
			"doctype": "Requisition Correction Outcome", "event_id": event["event_id"], "schema_version": SCHEMA_VERSION, "producer": PRODUCER,
			"producer_sequence": int(event["producer_sequence"]), "correction_request_id": event["correction_request_id"],
			"requisition": root.name, "requisition_version": event["requesting_requisition_version_id"], "plan_item_id": event["plan_item_id"],
			"requested_plan_version_id": event["requested_plan_version_id"], "requested_plan_item_version_id": event["requested_plan_item_version_id"],
			"outcome": event["outcome"], "reason": cstr(event.get("reason")), "correcting_plan_version_id": cstr(event.get("correcting_plan_version_id")),
			"replacement_lineage_json": json.dumps(event.get("replacement_lineage")) if event.get("replacement_lineage") else "",
			"decided_by": cstr(event["actor"]), "decision_at": cstr(event["decision_at"]),
			"item_hold_state": 1 if event.get("item_hold_state") else 0, "unresolved_request_count": int(event.get("unresolved_request_count") or 0),
			"eligibility_revision": int(event.get("eligibility_revision") or 0), "payload_digest": payload_digest, "received_at": now_datetime(),
			"status": "Recorded",
		}
	))
	events.publish(requisition=root.name, requisition_version=event["requesting_requisition_version_id"], event_type=events.EVENT_OUTCOME_RECEIVED, payload={"outcome": doc.name, "result": event["outcome"]})
	_notify_requester(root, event)
	return {"ok": True, "idempotent": False, "action": "recorded", "outcome": doc.name}


def _notify_requester(root, event: dict[str, Any]) -> None:
	"""§9.1B — a durable notification for the requester; it grants nothing."""
	decision = frappe.db.get_value(
		"Requisition Decision", {"requisition_version": event["requesting_requisition_version_id"], "decision": "Request Planning correction"}, "actor",
	)
	if not decision or not frappe.db.exists("User", decision):
		return
	title = "Planning correction completed" if event["outcome"] == "Resolved" else "Planning request closed without change"
	frappe.get_doc(
		{
			"doctype": "Notification Log", "for_user": decision, "type": "Alert", "document_type": "Procurement Requisition", "document_name": root.name,
			"subject": f"{root.requisition_reference}: {title}", "email_content": title,
		}
	).insert(ignore_permissions=True)


def terminal_outcome(root) -> Any:
	name = frappe.db.get_value(
		"Requisition Correction Outcome", {"requisition": root.name, "correction_request_id": root.planning_correction_request_id, "status": "Recorded"}, "name",
		order_by="producer_sequence desc",
	)
	return frappe.get_doc("Requisition Correction Outcome", name) if name else None


def prepare_requisition_after_plan_correction(*, requisition: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4B `PrepareRequisitionAfterPlanCorrection` — an explicit fresh root
	against current eligible lineage, linked to the stopped root, Version,
	request and outcome. Decisions, reservations and digests are not copied;
	current eligibility and the one-open slot are rechecked."""
	from kentender_procurement.procurement_requisitions.services import draft_commands

	actor = authz.actor(user)
	root = records.require_root(requisition, lock=False)
	authz.require_requisition_reader(actor, contributing_org_units=records.contributing_units(root), state=root.current_state)
	if root.current_state != "Upstream correction required":
		fail("REQ_STALE_VERSION")
	outcome = terminal_outcome(root)
	if not outcome:
		fail("REQ_CORRECTION_OUTCOME_PENDING")
	plan_item_id = root.plan_item_id
	if outcome.outcome == "Resolved":
		lineage = json.loads(outcome.replacement_lineage_json or "{}")
		plan_item_id = lineage.get("plan_item_id") or plan_item_id
	return draft_commands.prepare_it_equipment_requisition(
		plan_item_id=plan_item_id, idempotency_key=idempotency_key, user=actor,
		prior={"requisition": root.name, "requisition_version": root.current_version, "correction_request": root.planning_correction_request_id, "outcome_event": outcome.event_id},
	)


def create_requisition_correction_draft(*, requisition: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4B `CreateRequisitionCorrectionDraft` — for a Revoked root only,
	only while its pinned baseline is still the eligible Active item and no
	other root occupies the item. New governance; nothing restored."""
	from kentender_procurement.procurement_requisitions.services import eligibility_gateway, lifecycle

	actor = authz.actor(user)
	payload = {"requisition": requisition}
	root = records.require_root(requisition)
	scope = records.require_edit_units(root, actor)
	records.require_shared(scope)
	replay = envelope.replay_or_none(idempotency_key, payload, command="CreateRequisitionCorrectionDraft", actor=actor)
	if replay:
		return replay
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Revoked":
		fail("REQ_STALE_VERSION")
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	if not projection.get("eligible") or cstr(projection.get("plan_item_version_id")) != cstr(root.plan_item_version_id):
		fail("REQ_PLAN_INELIGIBLE", "The approved baseline changed. Start a new requisition against the current approved purchase.")
	if records.open_root_for(root.plan_item_id):
		fail("REQ_OPEN_EXISTS")
	revoked_version = frappe.get_doc("Requisition Version", root.authorised_version)
	revoked_package_version = frappe.get_doc("IT Equipment Requirement Package Version", revoked_version.package_version)
	records.occupy_slot(root, root.plan_item_id)
	root.authorised_version = None
	root.handoff = None
	root.planning_drawdown_reference = ""
	new_version, _ = lifecycle.copy_draft_successor(root, revoked_version, revoked_package_version)
	result = {"ok": True, "idempotent": False, "action": "corrected_draft_created", "requisition_version": new_version.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="CreateRequisitionCorrectionDraft", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result
