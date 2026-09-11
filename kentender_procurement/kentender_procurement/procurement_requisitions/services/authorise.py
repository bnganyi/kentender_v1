# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §9.1A/§9.1/§7 — AuthoriseRequisition and
RevokeUnconsumedAuthorisation.

Ordering (D6): every external call (Budget's `check_funding` then
`reserve_funding`; Planning's `record_requisition_drawdown`, once per
contributing Organisation Unit) happens BEFORE this module's own writes, so
a failure in either sibling leaves nothing here to undo. This module's own
writes (decision, lock, handoff, outbox event, task close) then happen
inside one savepoint (`envelope.atomic`): if any of them fails, only this
module's own tables roll back — the already-committed Budget reservation and
Planning drawdown are a known, accepted residual risk of calling two
independent siblings with no real two-phase commit across apps (recorded in
the plan's own risk register), not an oversight.
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
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.draft_commands import _contributing_units, _package_dict, _version_dict
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION


def _submitting_actor(version) -> str:
	decision = frappe.db.get_value(
		"Requisition Decision", {"requisition_version": version.name, "decision": "Submit to Procurement"}, "actor", order_by="decided_at desc",
	)
	return cstr(decision) or cstr(version.owner)


def authorise_requisition(*, requisition: str, task: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Submitted to Procurement":
		fail("REQ_STALE_VERSION")
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = envelope.locked("Requisition Task", task)
	if task_doc.status != "Open" or task_doc.requisition != root.name:
		fail("REQ_STALE_VERSION")

	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)

	# §7.3 — the authoriser cannot also be the departmental submitting authority.
	if _submitting_actor(version) == actor:
		fail("REQ_SOD_BLOCKED")

	# §7.2 — recheck everything against the immutable submitted Version.
	report = validation.validate(version=_version_dict(version), package=_package_dict(package_version), eligibility=eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id))
	if report["blocking_count"]:
		fail("REQ_BLOCKING_FINDINGS", detail={"findings": report["findings"]})
	recomputed_digest = digest.sha256_hex({"version": _version_dict(version), "package": _package_dict(package_version)})
	if recomputed_digest != version.content_digest:
		fail("REQ_BLOCKING_FINDINGS", detail={"findings": [{"code": "DIGEST_FAILED"}]})

	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	if not projection.get("eligible"):
		fail("REQ_PLAN_INELIGIBLE")
	failure = compatibility.first_failure(projection)
	if failure:
		fail("REQ_PRODUCT_UNSUPPORTED", detail={"test": failure.test})

	sources_by_line = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	contributing_units_now = set(projection.get("contributing_org_unit_ids") or [])
	for line in version.drawdown_lines:
		if line.contributing_org_unit not in contributing_units_now:
			fail("REQ_DEPARTMENT_NOT_CONTRIBUTING")
		source = sources_by_line.get(line.plan_item_line_id)
		if not source:
			fail("REQ_BALANCE_CHANGED")
		if line.requested_quantity > (source.get("remaining_quantity") or 0) + 1e-6 or line.requested_value > (source.get("remaining_amount") or 0) + 1e-6:
			fail("REQ_BALANCE_CHANGED")

	# --- External calls first (D6) ---
	allocations = [
		{"budget_line": sources_by_line[line.plan_item_line_id]["budget_line"], "plan_source_allocation": line.plan_item_line_id, "amount": line.requested_value}
		for line in version.drawdown_lines
	]
	correlation_id = f"{idempotency_key}:budget"
	checked = funding_gateway.check_funding(
		plan_item=root.plan_item_id, plan_version=root.plan_version_id, source_set_hash=digest.sha256_hex({"lines": sorted(a["plan_source_allocation"] for a in allocations)}),
		allocations=allocations, correlation_id=correlation_id, caller_reference=root.requisition_reference,
	)
	if not checked.get("all_sufficient"):
		shortfall_lines = [a for a in checked.get("allocations", []) if not a.get("sufficient")]
		fail("REQ_FUNDING_UNAVAILABLE", detail={"lines": shortfall_lines})
	reserved = funding_gateway.reserve_funding(
		token=checked["token"], source_set_hash=digest.sha256_hex({"lines": sorted(a["plan_source_allocation"] for a in allocations)}), idempotency_key=correlation_id,
	)
	reservations_by_allocation = {r["plan_source_allocation"]: r["reservation_id"] for r in reserved["reservations"]}
	reservations_by_line = {line.drawdown_line_id: reservations_by_allocation.get(line.plan_item_line_id, "") for line in version.drawdown_lines}

	lines_by_unit: dict[str, list] = {}
	for line in version.drawdown_lines:
		lines_by_unit.setdefault(line.contributing_org_unit, []).append(line)
	drawdown_refs_by_line: dict[str, str] = {}
	all_pdr_names: list[str] = []
	for unit, lines in lines_by_unit.items():
		drawn = eligibility_gateway.record_requisition_drawdown(
			plan_item_id=root.plan_item_id, requisition_reference=root.requisition_reference, requesting_org_unit=unit,
			allocations=[{"plan_source_allocation_id": l.plan_item_line_id, "quantity": l.requested_quantity, "amount": l.requested_value} for l in lines],
			expected_record_version=projection["record_version"], idempotency_key=f"{idempotency_key}:planning:{unit}",
		)
		refs = drawn["drawdown_references"]
		for line, ref in zip(lines, refs):
			drawdown_refs_by_line[line.drawdown_line_id] = ref["drawdown_reference"]
			all_pdr_names.append(ref["drawdown_reference"])

	# --- This module's own writes, atomically (D6) ---
	with envelope.atomic("authorise"):
		for line in version.drawdown_lines:
			line.reservation_id = reservations_by_line.get(line.drawdown_line_id, "")
			line.planning_drawdown_reference = drawdown_refs_by_line.get(line.drawdown_line_id, "")
		version.flags.kt_lifecycle = True
		package_version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Authorised")
		envelope.bump(package_version, version_status="Authorised")

		decision = frappe.get_doc(
			{
				"doctype": "Requisition Decision", "task": task_doc.name, "requisition_version": version.name,
				"actor": actor, "legal_capacity": ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "decision": "Authorise for Tender Preparation",
				"authority_snapshot": authz.authority_snapshot(assignment), "decided_at": now_datetime(),
				"command_idempotency_key": idempotency_key,
			}
		).insert(ignore_permissions=True)
		envelope.bump(task_doc, status="Completed", decision=decision.name)

		handoff_doc = handoff_service.build_and_insert(
			root=root, version=version, package_version=package_version, projection=projection,
			reservations_by_line={line.drawdown_line_id: reservations_by_line.get(line.drawdown_line_id, "") for line in version.drawdown_lines},
			decisions=[{"decision": decision.name, "actor": actor, "capacity": ROLE_HEAD_OF_PROCUREMENT_FUNCTION}],
		)
		events.publish_authorised(requisition=root.name, requisition_version=version.name, handoff_payload={"handoff": handoff_doc.name})

		root.current_state = "Authorised"
		root.authorised_version = version.name
		root.handoff = handoff_doc.name
		root.planning_drawdown_reference = ", ".join(all_pdr_names)
		envelope.bump(root)

	result = {
		"ok": True, "idempotent": False, "action": "authorised", "requisition_version": version.name,
		"handoff": handoff_doc.name, "reservations": list(reservations_by_allocation.values()),
		"planning_drawdown_references": all_pdr_names, "record_version": root.record_version,
	}
	envelope.record_command(idempotency_key=idempotency_key, command="AuthoriseRequisition", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def revoke_unconsumed_authorisation(*, requisition: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = cstr(reason).strip()
	if len(reason) < 20 or len(reason) > 1000:
		fail("REQ_CONTROL_INVALID", "A reason of 20-1,000 characters is required.")
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Authorised":
		fail("REQ_STALE_VERSION")
	if root.handoff_consumed_at:
		fail("REQ_HANDOFF_CONSUMED")

	version = frappe.get_doc("Requisition Version", root.authorised_version)

	# --- External calls first (D6): release every reservation, reverse every drawdown ---
	for line in version.drawdown_lines:
		if line.reservation_id:
			funding_gateway.release_reservation(
				reservation=line.reservation_id, amount=None, downstream_event_id=root.requisition_reference,
				idempotency_key=f"{idempotency_key}:budget:{line.reservation_id}",
			)
		if line.planning_drawdown_reference:
			eligibility_gateway.reverse_requisition_drawdown(
				drawdown_reference=line.planning_drawdown_reference,
				expected_record_version=frappe.db.get_value("Plan Drawdown Reference", line.planning_drawdown_reference, "record_version"),
				idempotency_key=f"{idempotency_key}:planning:{line.planning_drawdown_reference}",
			)

	with envelope.atomic("revoke"):
		version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Revoked")
		events.publish_revoked(requisition=root.name, requisition_version=version.name, reason=reason)
		root.current_state = "Revoked"
		envelope.bump(root)

	result = {"ok": True, "idempotent": False, "action": "revoked", "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="RevokeUnconsumedAuthorisation", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result
