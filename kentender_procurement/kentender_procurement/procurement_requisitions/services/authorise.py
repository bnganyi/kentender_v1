# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §7.2/§9.1/§9.1A — AuthoriseRequisition and
RevokeUnconsumedAuthorisation, each one transaction.

Every effect — Budget's complete-array check and one reservation per drawdown
line, Planning's one-call drawdown and first-authorisation scope marker, the
decision, the immutable handoff and the outbox event — happens inside one
savepoint (`envelope.atomic`). None of the owner contracts commits, so a
failure anywhere rolls every owner's effect back together; no compensating
release is ever presented as atomicity (§9.1A step 4).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import (
	compatibility,
	digest,
	eligibility_gateway,
	envelope,
	events,
	funding_gateway,
	handoff as handoff_service,
	precision,
	records,
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.lifecycle import record_decision
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION


def recheck(root, version, package_version) -> tuple[dict[str, Any], list[Any]]:
	"""§7.2 — every gate, again, on the immutable submitted Version and the
	current owner facts. Returns the projection and the nine checks."""
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	checks = compatibility.require_compatible(projection)
	if cstr(projection.get("plan_item_version_id")) != cstr(root.plan_item_version_id):
		fail("REQ_PLAN_INELIGIBLE", "The approved baseline was replaced. Return the requisition or request a Planning correction.")
	if (projection.get("hold") or {}).get("held"):
		fail("PLN_ITEM_AUTHORISATION_HELD", detail={"requests": (projection.get("hold") or {}).get("unresolved_requests")})
	if not projection.get("eligible"):
		fail("REQ_PLAN_INELIGIBLE")
	report = validation.validate(version=records.version_dict(version), package=records.package_dict(package_version), eligibility=projection)
	blocking = [f for f in report["findings"] if f["severity"] == "Blocking"]
	if any(f["code"] == "BALANCE_CHANGED" for f in blocking):
		fail("REQ_BALANCE_CHANGED", detail={"findings": blocking})
	if any(f["code"] == "DEPARTMENT_NOT_CONTRIBUTING" for f in blocking):
		fail("REQ_DEPARTMENT_NOT_CONTRIBUTING", detail={"findings": blocking})
	if blocking:
		fail("REQ_BLOCKING_FINDINGS", detail={"findings": blocking})
	if digest.sha256_hex(records.digest_payload(version, package_version)) != version.content_digest:
		fail("REQ_BLOCKING_FINDINGS", detail={"findings": [{"code": "DIGEST_FAILED", "message": "The canonical preview could not be reproduced."}]})
	return projection, checks


def funding_rows(version, projection: dict[str, Any]) -> list[dict[str, Any]]:
	sources = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	return [
		{
			"budget_line": sources[line.plan_item_line_id]["budget_line"], "plan_source_allocation": line.plan_item_line_id,
			"drawdown_line_id": line.drawdown_line_id, "source_organisation_unit": line.contributing_org_unit,
			"amount": precision.money_text(precision.stored_money(line.requested_value)),
		}
		for line in version.drawdown_lines
		if line.plan_item_line_id in sources
	]


def source_set_hash(version) -> str:
	return digest.sha256_hex({"version": version.name, "lines": sorted((l.drawdown_line_id, l.plan_item_line_id, l.requested_quantity, l.requested_value) for l in version.drawdown_lines)})


def authorise_requisition(*, requisition: str, task: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root = records.require_root(requisition)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Submitted to Procurement":
		fail("REQ_STALE_VERSION")
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = envelope.locked("Requisition Task", task)
	if task_doc.status != "Open" or task_doc.requisition != root.name:
		fail("REQ_STALE_VERSION")
	version = envelope.locked("Requisition Version", root.current_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)
	if task_doc.requisition_version != version.name or version.version_status != "Submitted to Procurement":
		fail("REQ_STALE_VERSION")
	if cstr(version.certified_lead_org_unit_id) != cstr(root.lead_org_unit_id):
		fail("REQ_LEAD_RECERTIFICATION_REQUIRED")
	# §7.3 — the authoriser cannot also be the departmental submitting authority.
	if cstr(version.submitted_by) == actor:
		fail("REQ_SOD_BLOCKED")

	projection, checks = recheck(root, version, package_version)
	rows = funding_rows(version, projection)
	correlation = f"{idempotency_key}:authorise"

	with envelope.atomic("authorise"):
		checked = funding_gateway.check_funding(
			plan_item=root.plan_item_id, plan_version=root.plan_version_id, source_set_hash=source_set_hash(version),
			allocations=rows, correlation_id=correlation, caller_reference=root.requisition_reference,
		)
		if not checked.get("all_sufficient"):
			fail("REQ_FUNDING_UNAVAILABLE", detail={"lines": [l for l in checked.get("lines", []) if not l.get("sufficient")]})
		reserved = funding_gateway.reserve_funding(token=checked["token"], source_set_hash=source_set_hash(version), idempotency_key=correlation, caller_reference=root.requisition_reference)
		reservation_by_line = {r["drawdown_line_id"]: r for r in reserved["reservations"]}
		if set(reservation_by_line) != {line.drawdown_line_id for line in version.drawdown_lines}:
			fail("REQ_OWNER_VALIDATION_UNAVAILABLE", detail={"reason": "Budget did not return one reservation per drawdown line."})

		drawn = eligibility_gateway.authorise_requisition_drawdown(
			plan_item_id=root.plan_item_id, requisition_reference=root.requisition_reference, requisition_version=version.name,
			correlation_id=correlation,
			allocations=[{"plan_source_allocation_id": l.plan_item_line_id, "quantity": l.requested_quantity, "amount": l.requested_value} for l in version.drawdown_lines],
			expected_record_version=projection["record_version"], idempotency_key=f"{idempotency_key}:planning",
		)
		drawdown_by_allocation = {d["plan_source_allocation_id"]: d["drawdown_reference"] for d in drawn["drawdowns"]}

		for line in version.drawdown_lines:
			line.reservation_id = reservation_by_line[line.drawdown_line_id]["reservation_id"]
			line.planning_drawdown_reference = drawdown_by_allocation.get(line.plan_item_line_id, "")
		version.flags.kt_lifecycle = True
		package_version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Authorised")
		envelope.bump(package_version, version_status="Authorised")
		decision = record_decision(task=task_doc, version=version, actor=actor, capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Authorise requisition", assignment=assignment, idempotency_key=idempotency_key, resulting_state="Authorised")
		envelope.bump(task_doc, status="Completed", decision=decision.name)

		handoff_doc = handoff_service.build_and_insert(
			root=root, version=version, package_version=package_version, projection=projection, checks=checks,
			reservations=[reservation_by_line[line.drawdown_line_id] for line in version.drawdown_lines], hopf_decision=decision,
		)
		events.publish_authorised(requisition=root.name, requisition_version=version.name, handoff_payload={"handoff": handoff_doc.name, "handoff_digest": handoff_doc.handoff_digest})

		package = frappe.get_doc("IT Equipment Requirement Package", package_version.package)
		package.authorised_version = package_version.name
		package.save(ignore_permissions=True)
		root.current_state = "Authorised"
		root.authorised_version = version.name
		root.handoff = handoff_doc.name
		root.planning_drawdown_reference = ", ".join(d["drawdown_reference"] for d in drawn["drawdowns"])
		envelope.bump(root)

	result = {
		"ok": True, "idempotent": False, "action": "authorised", "requisition_version": version.name, "handoff": handoff_doc.name,
		"reservations": [reservation_by_line[l.drawdown_line_id]["reservation_id"] for l in version.drawdown_lines],
		"planning_drawdown_references": [d["drawdown_reference"] for d in drawn["drawdowns"]], "record_version": root.record_version,
	}
	envelope.record_command(idempotency_key=idempotency_key, command="AuthoriseRequisition", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def revoke_unconsumed_authorisation(*, requisition: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4/§9.1A — only while the handoff is authoritatively unconsumed
	(checked under the handoff row lock that consumption also takes): reverse
	the exact Planning drawdowns and release every exact reservation, once,
	together. The permanent scope marker stays."""
	from kentender_procurement.procurement_requisitions.services.lifecycle import _reason

	actor = authz.actor(user)
	payload = {"requisition": requisition, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason)
	root = records.require_root(requisition)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Authorised":
		fail("REQ_STALE_VERSION")
	handoff_doc = envelope.locked("Authorised Requisition Handoff", root.handoff)
	if handoff_doc.consumed_at:
		fail("REQ_HANDOFF_CONSUMED", detail={"tender": cstr(handoff_doc.tender)})
	version = envelope.locked("Requisition Version", root.authorised_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)

	with envelope.atomic("revoke"):
		for line in version.drawdown_lines:
			if line.reservation_id:
				funding_gateway.release_reservation(reservation=line.reservation_id, requisition_reference=root.requisition_reference, downstream_event_id=f"{root.requisition_reference}:revoked", idempotency_key=f"{idempotency_key}:budget:{line.reservation_id}")
		for row in eligibility_gateway.list_requisition_drawdowns(root.requisition_reference):
			if row["requisition_version"] == version.name and row["drawdown_state"] == "Active":
				eligibility_gateway.reverse_requisition_drawdown(drawdown_reference=row["drawdown_reference"], expected_record_version=row["record_version"], idempotency_key=f"{idempotency_key}:planning:{row['drawdown_reference']}")
		version.flags.kt_lifecycle = True
		package_version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Revoked")
		envelope.bump(package_version, version_status="Revoked")
		record_decision(task=None, version=version, actor=actor, capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Revoke authorisation", assignment=assignment, idempotency_key=idempotency_key, reason=reason, resulting_state="Revoked")
		events.publish_revoked(requisition=root.name, requisition_version=version.name, reason=reason)
		root.current_state = "Revoked"
		records.release_slot(root)
		envelope.bump(root)

	result = {"ok": True, "idempotent": False, "action": "revoked", "record_version": root.record_version, "revoked_at": cstr(now_datetime())}
	envelope.record_command(idempotency_key=idempotency_key, command="RevokeUnconsumedAuthorisation", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result
