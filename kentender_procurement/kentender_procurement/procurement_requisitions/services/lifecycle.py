# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §7 — Requisition lifecycle transitions (excluding
authorisation and revocation, which cross into Planning/Budget and live in
`authorise.py`).

Every transition into a locked state recomputes the deterministic findings
and content digest from scratch (never trusts a client-supplied digest) and
refuses with `REQ_BLOCKING_FINDINGS` on any Blocking finding (§7.2). A
return or withdrawal never edits the reviewed Version; it is preserved
exactly and a copied Draft successor is created instead, carrying every
stable row id forward unchanged (§4, §7.4).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import digest, envelope, validation
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.draft_commands import _contributing_units, _load, _package_dict, _version_dict
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION


def _digest_payload(version, package_version) -> dict[str, Any]:
	return {"version": _version_dict(version), "package": _package_dict(package_version)}


def _lock(root, version, package_version, *, target_status: str) -> None:
	"""§7.2 — recheck everything, recompute the canonical digest, lock."""
	from kentender_procurement.procurement_requisitions.services import eligibility_gateway

	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	report = validation.validate(version=_version_dict(version), package=_package_dict(package_version), eligibility=projection)
	if report["blocking_count"]:
		fail("REQ_BLOCKING_FINDINGS", detail={"findings": report["findings"]})
	content_digest = digest.sha256_hex(_digest_payload(version, package_version))
	version.content_digest = content_digest
	package_version.content_digest = content_digest
	version.flags.kt_lifecycle = True
	package_version.flags.kt_lifecycle = True
	envelope.bump(version, version_status=target_status)
	envelope.bump(package_version, version_status=target_status)


def _copy_draft_successor(root, reviewed_version, reviewed_package_version) -> tuple[Any, Any]:
	"""§7.4 — the reviewed Version/Package Version are preserved exactly;
	every row is copied forward with its stable id unchanged (§4)."""
	new_package_version = frappe.get_doc(
		{
			"doctype": "IT Equipment Requirement Package Version", "package": reviewed_package_version.package,
			"version_number": reviewed_package_version.version_number + 1, "based_on_version": reviewed_package_version.name,
			"version_status": "Draft", "minimum_warranty_months": reviewed_package_version.minimum_warranty_months,
			"onsite_support_required": reviewed_package_version.onsite_support_required,
			"maximum_support_response_hours": reviewed_package_version.maximum_support_response_hours,
			"manufacturer_support_required": reviewed_package_version.manufacturer_support_required,
			"service_location_constraint": reviewed_package_version.service_location_constraint,
			"support_description": reviewed_package_version.support_description,
			"catalogue_version": reviewed_package_version.catalogue_version, "record_version": 0,
			"items": [r.as_dict() for r in reviewed_package_version.items],
			"technical_requirements": [r.as_dict() for r in reviewed_package_version.technical_requirements],
			"related_services": [r.as_dict() for r in reviewed_package_version.related_services],
			"acceptance_requirements": [r.as_dict() for r in reviewed_package_version.acceptance_requirements],
			"supporting_materials": [r.as_dict() for r in reviewed_package_version.supporting_materials],
		}
	).insert(ignore_permissions=True)

	new_version = frappe.get_doc(
		{
			"doctype": "Requisition Version", "requisition": root.name, "version_number": reviewed_version.version_number + 1,
			"based_on_version": reviewed_version.name, "version_status": "Draft",
			"requirement_title": reviewed_version.requirement_title, "delivery_location": reviewed_version.delivery_location,
			"latest_delivery_date": reviewed_version.latest_delivery_date, "related_services_required": reviewed_version.related_services_required,
			"package_version": new_package_version.name, "record_version": 0,
			"drawdown_lines": [r.as_dict() for r in reviewed_version.drawdown_lines],
		}
	).insert(ignore_permissions=True)

	pkg = frappe.get_doc("IT Equipment Requirement Package", new_package_version.package)
	pkg.current_version = new_package_version.name
	pkg.save(ignore_permissions=True)

	root.current_version = new_version.name
	root.current_state = "Draft"
	envelope.bump(root)
	return new_version, new_package_version


def _new_task(root, version, *, business_role: str, organisation_unit: str = "") -> Any:
	task = frappe.get_doc(
		{
			"doctype": "Requisition Task", "requisition": root.name, "requisition_version": version.name,
			"business_role": business_role, "organisation_unit": organisation_unit, "status": "Open",
			"task_token": envelope.token(), "record_version": 0,
		}
	).insert(ignore_permissions=True)
	return task


def send_for_department_approval(*, requisition: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	authz.require_draft_author_for_any(_contributing_units(root), actor)
	envelope.check_record_version(root, expected_record_version)
	version = envelope.locked("Requisition Version", root.current_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)
	if version.version_status != "Draft":
		fail("REQ_STALE_VERSION")

	_lock(root, version, package_version, target_status="Awaiting Department Approval")
	task = _new_task(root, version, business_role="Head of User Department", organisation_unit=root.lead_org_unit)
	root.current_state = "Awaiting Department Approval"
	envelope.bump(root)

	result = {"ok": True, "idempotent": False, "action": "sent", "requisition_version": version.name, "task": task.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="SendForDepartmentApproval", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def return_to_department_author(*, task: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"task": task, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = cstr(reason).strip()
	if len(reason) < 20 or len(reason) > 1000:
		fail("REQ_CONTROL_INVALID", "A correction reason of 20-1,000 characters is required.")
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = envelope.locked("Requisition Task", task)
	root = envelope.locked("Procurement Requisition", task_doc.requisition)
	assignment, _lead_unit = authz.require_hod_for_any(_contributing_units(root), actor)
	envelope.check_record_version(task_doc, expected_record_version)
	if task_doc.status != "Open" or root.current_state != "Awaiting Department Approval":
		fail("REQ_STALE_VERSION")

	reviewed_version = frappe.get_doc("Requisition Version", task_doc.requisition_version)
	reviewed_package_version = frappe.get_doc("IT Equipment Requirement Package Version", reviewed_version.package_version)
	envelope.bump(reviewed_version, version_status="Returned")
	reviewed_package_version.flags.kt_lifecycle = True
	envelope.bump(reviewed_package_version, version_status="Returned")

	decision = frappe.get_doc(
		{
			"doctype": "Requisition Decision", "task": task_doc.name, "requisition_version": reviewed_version.name,
			"actor": actor, "legal_capacity": "Head of User Department", "decision": "Return for correction",
			"return_reason": reason, "authority_snapshot": authz.authority_snapshot(assignment),
			"decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)

	new_version, _ = _copy_draft_successor(root, reviewed_version, reviewed_package_version)
	result = {"ok": True, "idempotent": False, "action": "returned", "requisition_version": new_version.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="ReturnToDepartmentAuthor", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def submit_requisition_to_procurement(*, requisition: str, expected_record_version, idempotency_key: str, task: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""§7.1 — reached either from `Awaiting Department Approval` (the lead
	HoD submits the Author's locked Version, closing `task`) or directly
	from `Draft` (a HoD preparing and submitting without an internal task —
	REQ-AC-021). `task` is required only for the first path."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	hod_assignment, _lead_unit = authz.require_hod_for_any(_contributing_units(root), actor)
	envelope.check_record_version(root, expected_record_version)
	version = envelope.locked("Requisition Version", root.current_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)

	if root.current_state == "Awaiting Department Approval":
		if not task or not frappe.db.exists("Requisition Task", task):
			authz.not_found()
		task_doc = envelope.locked("Requisition Task", task)
		if task_doc.status != "Open" or task_doc.requisition_version != version.name:
			fail("REQ_STALE_VERSION")
		decision = frappe.get_doc(
			{
				"doctype": "Requisition Decision", "task": task_doc.name, "requisition_version": version.name,
				"actor": actor, "legal_capacity": "Head of User Department", "decision": "Submit to Procurement",
				"authority_snapshot": authz.authority_snapshot(hod_assignment),
				"decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
			}
		).insert(ignore_permissions=True)
		envelope.bump(task_doc, status="Completed", decision=decision.name)
		version.flags.kt_lifecycle = True
		package_version.flags.kt_lifecycle = True
		envelope.bump(version, version_status="Submitted to Procurement")
		envelope.bump(package_version, version_status="Submitted to Procurement")
	elif root.current_state == "Draft":
		if version.version_status != "Draft":
			fail("REQ_STALE_VERSION")
		_lock(root, version, package_version, target_status="Submitted to Procurement")
	else:
		fail("REQ_STALE_VERSION")

	procurement_task = _new_task(root, version, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	root.current_state = "Submitted to Procurement"
	envelope.bump(root)

	result = {"ok": True, "idempotent": False, "action": "submitted", "requisition_version": version.name, "task": procurement_task.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="SubmitRequisitionToProcurement", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def return_requisition_to_department(*, task: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"task": task, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = cstr(reason).strip()
	if len(reason) < 20 or len(reason) > 1000:
		fail("REQ_CONTROL_INVALID", "A correction reason of 20-1,000 characters is required.")
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = envelope.locked("Requisition Task", task)
	root = envelope.locked("Procurement Requisition", task_doc.requisition)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(task_doc, expected_record_version)
	if task_doc.status != "Open" or root.current_state != "Submitted to Procurement":
		fail("REQ_STALE_VERSION")

	reviewed_version = frappe.get_doc("Requisition Version", task_doc.requisition_version)
	reviewed_package_version = frappe.get_doc("IT Equipment Requirement Package Version", reviewed_version.package_version)
	reviewed_version.flags.kt_lifecycle = True
	reviewed_package_version.flags.kt_lifecycle = True
	envelope.bump(reviewed_version, version_status="Returned")
	envelope.bump(reviewed_package_version, version_status="Returned")

	decision = frappe.get_doc(
		{
			"doctype": "Requisition Decision", "task": task_doc.name, "requisition_version": reviewed_version.name,
			"actor": actor, "legal_capacity": ROLE_HEAD_OF_PROCUREMENT_FUNCTION, "decision": "Return to department",
			"return_reason": reason, "authority_snapshot": authz.authority_snapshot(assignment),
			"decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
		}
	).insert(ignore_permissions=True)
	envelope.bump(task_doc, status="Completed", decision=decision.name)

	new_version, _ = _copy_draft_successor(root, reviewed_version, reviewed_package_version)
	result = {"ok": True, "idempotent": False, "action": "returned", "requisition_version": new_version.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="ReturnRequisitionToDepartment", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def withdraw_requisition(*, requisition: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"requisition": requisition}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	authz.require_hod_for_any(_contributing_units(root), actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state not in ("Awaiting Department Approval", "Submitted to Procurement"):
		fail("REQ_STALE_VERSION")

	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	version.flags.kt_lifecycle = True
	package_version.flags.kt_lifecycle = True
	envelope.bump(version, version_status="Withdrawn")
	envelope.bump(package_version, version_status="Withdrawn")
	for open_task in frappe.get_all("Requisition Task", filters={"requisition": root.name, "status": "Open"}, pluck="name"):
		frappe.db.set_value("Requisition Task", open_task, "status", "Cancelled")

	root.current_state = "Withdrawn"
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "withdrawn", "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="WithdrawRequisition", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def _require_hod_or_hopf(root, actor: str) -> None:
	"""§7.4A step 1 — Head of User Department (any contributing department)
	or Head of Procurement Function may request an upstream correction."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	if authorise_record(user=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, organisation_unit="", purpose=PURPOSE_COMMAND).allowed:
		return
	authz.require_hod_for_any(_contributing_units(root), actor)


def request_upstream_plan_correction(*, requisition: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4A step 1/2 — closes the current Version as `Upstream correction
	required`, preserving it exactly, and forwards the request to Planning."""
	from kentender_procurement.procurement_requisitions.services import eligibility_gateway

	actor = authz.actor(user)
	payload = {"requisition": requisition, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = cstr(reason).strip()
	if len(reason) < 20 or len(reason) > 1000:
		fail("REQ_CONTROL_INVALID", "A reason of 20-1,000 characters identifying the wrong Planning fact is required.")
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	_require_hod_or_hopf(root, actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state not in ("Draft", "Returned", "Awaiting Department Approval", "Submitted to Procurement"):
		fail("REQ_STALE_VERSION")

	version = frappe.get_doc("Requisition Version", root.current_version)
	version.flags.kt_lifecycle = True
	envelope.bump(version, version_status="Upstream correction required")

	correction = eligibility_gateway.receive_plan_item_correction_request(
		plan_item_id=root.plan_item_id, requisition_reference=root.requisition_reference,
		requisition_version=version.name, reason=reason, idempotency_key=f"{idempotency_key}:planning",
	)
	root.current_state = "Upstream correction required"
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "upstream_correction_requested", "correction_request": correction.get("correction_request"), "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="RequestUpstreamPlanCorrection", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


def change_lead_organisation_unit(*, requisition: str, new_lead_org_unit: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§5.1/§13.11 — the one place `lead_org_unit` can change: the Head of
	Procurement Function, at authorisation review, only before the
	authorisation decision itself, always with a reason."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "new_lead_org_unit": new_lead_org_unit, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = cstr(reason).strip()
	if len(reason) < 20 or len(reason) > 500:
		fail("REQ_CONTROL_INVALID", "A reason of 20-500 characters is required.")
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = envelope.locked("Procurement Requisition", requisition)
	authz.require_hopf(actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state != "Submitted to Procurement":
		fail("REQ_STALE_VERSION", "Change lead department is only available while a Requisition is submitted for authorisation.")
	contributing_units = _contributing_units(root)
	if new_lead_org_unit not in contributing_units:
		fail("REQ_DEPARTMENT_NOT_CONTRIBUTING")

	envelope.bump(root, lead_org_unit=new_lead_org_unit)
	result = {"ok": True, "idempotent": False, "action": "lead_unit_changed", "lead_org_unit": new_lead_org_unit, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="ChangeLeadOrganisationUnit", payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result
