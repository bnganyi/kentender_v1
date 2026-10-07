# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §7 — lifecycle transitions other than authorisation and
revocation (`authorise.py`) and the Planning outcome (`correction.py`).

Locking recomputes every finding, all nine §5A checks and the canonical digest
from scratch, and freezes the exact basis snapshot (§5.14). A decision never
edits the Version it decides: a return or lead change preserves it and opens a
copied Draft; withdrawal and a Planning correction stop it in place. The
certified lead department and the submitting authority are frozen on the
Version at departmental submission (§7.3A).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import (
	catalogue,
	compatibility,
	digest,
	eligibility_gateway,
	envelope,
	events,
	records,
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import (
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
)

AFFECTED_SECTIONS = ("Request details", "Equipment", "Technical requirements", "Warranty and support", "Services", "Acceptance", "Supporting materials", "Whole requisition")


def _reason(value: str, low: int = 20, high: int = 1000, label: str = "reason") -> str:
	text = " ".join(cstr(value).split())
	if not (low <= len(text) <= high):
		fail("REQ_CONTROL_INVALID", f"Enter a {label} of {low}–{high:,} characters.", {"fields": {label.replace(' ', '_'): f"Enter a {label} of {low}–{high:,} characters."}})
	return text


def _section(value: str | None) -> str:
	section = cstr(value).strip()
	if section and section not in AFFECTED_SECTIONS:
		fail("REQ_CONTROL_INVALID", "Select a governed affected section.")
	return section


def basis_snapshot(projection: dict[str, Any]) -> str:
	"""§5.14 — the exact identities and currency basis this Version was
	decided on; current eligibility is always rechecked separately."""
	return json.dumps(
		{
			"observed_at": projection.get("evaluated_at"),
			"plan_id": projection.get("plan_id"), "plan_version_id": projection.get("plan_version_id"),
			"plan_item_id": projection.get("plan_item_id"), "plan_item_version_id": projection.get("plan_item_version_id"),
			"currency": projection.get("currency"), "money_scale": 2, "unit": "Each",
			"reservation_category": projection.get("reservation_category"), "county_resident_reservation": bool(projection.get("county_resident_reservation")),
			"reservation_rule": projection.get("reservation_rule"), "county_rule": projection.get("county_rule"),
			"sources": [
				{k: s.get(k) for k in ("plan_item_line_id", "source_line_id", "source_origin", "dpp_entry", "need", "need_revision", "organisation_unit", "budget_line", "approved_quantity", "allocated_amount", "remaining_quantity", "remaining_amount", "required_by_date")}
				for s in projection.get("sources", [])
			],
		},
		sort_keys=True,
	)


def recheck(root, version, package_version) -> dict[str, Any]:
	"""§7.2 — the checks made before departmental routing **or submission**:
	current Planning eligibility, the nine compatibility checks and every field
	and row control with zero Blocking findings. Returns the projection."""
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	compatibility.require_compatible(projection)
	report = validation.validate(version=records.version_dict(version), package=records.package_dict(package_version), eligibility=projection)
	if report["blocking_count"]:
		fail("REQ_BLOCKING_FINDINGS", detail={"findings": [f for f in report["findings"] if f["severity"] == "Blocking"]})
	return projection


def lock(root, version, package_version, *, target_status: str) -> dict[str, Any]:
	"""§7.2 — recheck everything on the exact content, freeze it, lock it."""
	projection = recheck(root, version, package_version)
	content_digest = digest.sha256_hex(records.digest_payload(version, package_version))
	version.content_digest = content_digest
	package_version.content_digest = content_digest
	version.basis_snapshot_json = basis_snapshot(projection)
	# §5.2 — generated from the selected location at submission.
	location = frappe.db.get_value("Delivery Location", version.delivery_location, ["location_name", "address"], as_dict=True) or {}
	version.delivery_address_snapshot = ", ".join(v for v in (location.get("location_name"), location.get("address")) if v)
	envelope.bump(version, version_status=target_status)
	envelope.bump(package_version, version_status=target_status)
	return projection


def copy_draft_successor(root, reviewed_version, reviewed_package_version, *, lead_directive: str = "") -> tuple[Any, Any]:
	"""§7.4 — the reviewed Version stays exactly as it was; every row is
	copied forward with its stable id. §6.4: a copied package is Review
	required — its rows return as Proposed for one deliberate confirmation,
	and the reviewed Version keeps the confirmed history."""
	def proposed(rows):
		out = []
		for row in rows:
			data = row.as_dict()
			for key in ("name", "parent", "parentfield", "parenttype", "idx", "creation", "modified", "owner", "modified_by", "docstatus"):
				data.pop(key, None)
			data["row_state"] = "Proposed"
			out.append(data)
		return out

	copied_technical = proposed(reviewed_package_version.technical_requirements)
	copied_acceptance = proposed(reviewed_package_version.acceptance_requirements)
	proposal_digest = digest.sha256_hex({"technical": copied_technical, "acceptance": copied_acceptance, "based_on": reviewed_package_version.name})
	new_package_version = envelope.insert(frappe.get_doc(
		{
			"doctype": "IT Equipment Requirement Package Version", "package": reviewed_package_version.package,
			"version_number": int(reviewed_package_version.version_number) + 1, "based_on_version": reviewed_package_version.name,
			"version_status": "Draft", **{f: reviewed_package_version.get(f) for f in ("minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description")},
			"catalogue_version": catalogue.CATALOGUE_VERSION,
			"standard_profile_key": reviewed_package_version.standard_profile_key or catalogue.CATALOGUE_PROFILE_KEY,
			"standard_profile_version": reviewed_package_version.standard_profile_version or catalogue.STANDARD_PROFILE_VERSION,
			"proposal_digest": proposal_digest, "standard_package_review_state": "Review required" if (copied_technical or copied_acceptance) else "Not generated",
			"record_version": 0,
			"items": [r.as_dict() for r in reviewed_package_version.items],
			"technical_requirements": copied_technical,
			"related_services": [r.as_dict() for r in reviewed_package_version.related_services],
			"acceptance_requirements": copied_acceptance,
			"supporting_materials": [r.as_dict() for r in reviewed_package_version.supporting_materials],
		}
	))

	new_version = envelope.insert(frappe.get_doc(
		{
			"doctype": "Requisition Version", "requisition": root.name, "version_number": int(reviewed_version.version_number) + 1,
			"based_on_version": reviewed_version.name, "version_status": "Draft",
			**{f: reviewed_version.get(f) for f in ("requirement_title", "delivery_location", "latest_delivery_date", "related_services_required", "prepared_by", "prepared_capacity", "prepared_authority_snapshot")},
			"lead_routing_directive": lead_directive or None,
			"package_version": new_package_version.name, "record_version": 0,
			"drawdown_lines": [{k: v for k, v in r.as_dict().items() if k not in ("reservation_id", "planning_drawdown_reference")} for r in reviewed_version.drawdown_lines],
		}
	))

	package = frappe.get_doc("IT Equipment Requirement Package", new_package_version.package)
	package.current_version = new_package_version.name
	envelope.save(package)
	root.current_version = new_version.name
	root.current_state = "Draft"
	if lead_directive:
		root.lead_org_unit_id = lead_directive
	envelope.bump(root)
	return new_version, new_package_version


def new_task(root, version, *, business_role: str, organisation_unit: str = "") -> Any:
	return envelope.insert(frappe.get_doc(
		{
			"doctype": "Requisition Task", "requisition": root.name, "requisition_version": version.name,
			"business_role": business_role, "organisation_unit": organisation_unit or None, "status": "Open",
			"task_token": envelope.token(), "record_version": 0,
		}
	))


def cancel_open_tasks(root) -> None:
	for name in frappe.get_all("Requisition Task", filters={"requisition": root.name, "status": "Open"}, pluck="name"):
		task = envelope.locked("Requisition Task", name)
		envelope.bump(task, status="Cancelled")


def record_decision(*, task, version, actor: str, capacity: str, decision: str, assignment, idempotency_key: str, reason: str = "", affected_section: str = "", new_lead: str = "", resulting_state: str = ""):
	return envelope.insert(frappe.get_doc(
		{
			"doctype": "Requisition Decision", "task": task.name if task else None, "requisition_version": version.name,
			"actor": actor, "legal_capacity": capacity, "decision": decision, "reason": reason, "affected_section": affected_section or None,
			"new_lead_org_unit_id": new_lead or None, "resulting_state": resulting_state,
			"authority_snapshot": authz.authority_snapshot(assignment), "decided_at": now_datetime(), "command_idempotency_key": idempotency_key,
		}
	))


def _require_role_in(actor: str, role: str, unit: str, *, masked: bool = True):
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	decision = authorise_record(user=actor, business_role=role, organisation_unit=cstr(unit), purpose=PURPOSE_COMMAND)
	if not decision.allowed:
		if masked:
			authz.not_found()
		fail("REQ_RESPONSIBILITY_REQUIRED")
	return decision.assignment


def _lead_hod(root, actor: str):
	return _require_role_in(actor, ROLE_HEAD_OF_USER_DEPARTMENT, root.lead_org_unit_id)


def _load_current(root):
	version = envelope.locked("Requisition Version", root.current_version)
	package_version = envelope.locked("IT Equipment Requirement Package Version", version.package_version)
	return version, package_version


def _journal(idempotency_key, command, payload, result, root, actor):
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type="Procurement Requisition", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------


def send_for_department_approval(*, requisition: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.1 — a Departmental Author acting for the lead department locks the
	exact Version and routes it to the lead Head of User Department."""
	actor = authz.actor(user)
	payload = {"requisition": requisition}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root = records.require_root(requisition)
	scope = records.require_edit_units(root, actor)
	if not scope["shared"]:
		fail("REQ_RESPONSIBILITY_REQUIRED", "Only the submitting department can send this requisition for department approval.")
	_require_role_in(actor, ROLE_DEPARTMENTAL_AUTHOR, root.lead_org_unit_id, masked=False)
	envelope.check_record_version(root, expected_record_version)
	version, package_version = _load_current(root)
	if root.current_state != "Draft" or version.version_status != "Draft":
		fail("REQ_STALE_VERSION")
	# §5.2 / §7.3 — who sent it is evidence, so the Head of User Department decision can refuse them later.
	version.sent_for_approval_by = actor
	version.sent_for_approval_at = now_datetime()
	lock(root, version, package_version, target_status="Awaiting Department Approval")
	task = new_task(root, version, business_role=ROLE_HEAD_OF_USER_DEPARTMENT, organisation_unit=root.lead_org_unit_id)
	root.current_state = "Awaiting Department Approval"
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "sent", "requisition_version": version.name, "task": task.name, "record_version": root.record_version}
	return _journal(idempotency_key, "SendForDepartmentApproval", payload, result, root, actor)


def submit_requisition_to_procurement(*, requisition: str, expected_record_version, idempotency_key: str, task: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""§7.1 — the lead department's Head of User Department certifies the
	whole request once: from its approval task, or directly on a Draft they
	prepare. The certified lead and submitting authority are frozen here."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "task": task}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root = records.require_root(requisition)
	assignment = _lead_hod(root, actor)
	envelope.check_record_version(root, expected_record_version)
	version, package_version = _load_current(root)

	task_doc = None
	if root.current_state == "Awaiting Department Approval":
		if not task or not frappe.db.exists("Requisition Task", task):
			authz.not_found()
		task_doc = envelope.locked("Requisition Task", task)
		if task_doc.status != "Open" or task_doc.requisition_version != version.name:
			fail("REQ_STALE_VERSION")
		# §7.3 — an Author cannot complete the HoD decision on a Version they
		# prepared or sent, unless they hold the HoD role and prepared it in that capacity.
		if records.certifier_conflict(version, actor):
			fail("REQ_SOD_BLOCKED")
		# §7.2 — "before departmental routing or submission": the content is locked, the facts around it are not.
		recheck(root, version, package_version)
		if digest.sha256_hex(records.digest_payload(version, package_version)) != version.content_digest:
			fail("REQ_BLOCKING_FINDINGS", detail={"findings": [{"code": "DIGEST_FAILED", "message": "The canonical preview could not be reproduced."}]})
		envelope.bump(version, version_status="Submitted to Procurement")
		envelope.bump(package_version, version_status="Submitted to Procurement")
	elif root.current_state == "Draft":
		if version.version_status != "Draft":
			fail("REQ_STALE_VERSION")
		# §7.1/§7.3 — only a Head of User Department preparing directly certifies a Draft; the Draft an Author prepared goes through the approval task.
		if records.certifier_conflict(version, actor):
			fail("REQ_SOD_BLOCKED")
		lock(root, version, package_version, target_status="Submitted to Procurement")
	else:
		fail("REQ_STALE_VERSION")

	record_decision(task=task_doc, version=version, actor=actor, capacity=ROLE_HEAD_OF_USER_DEPARTMENT, decision="Submit to Procurement", assignment=assignment, idempotency_key=idempotency_key, resulting_state="Submitted to Procurement")
	if task_doc:
		envelope.bump(task_doc, status="Completed")
	envelope.bump(
		version, certified_lead_org_unit_id=root.lead_org_unit_id, submitted_by=actor, submitted_capacity=ROLE_HEAD_OF_USER_DEPARTMENT,
		submitted_authority_snapshot=authz.authority_snapshot(assignment), submitted_at=now_datetime(),
	)
	procurement_task = new_task(root, version, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	root.current_state = "Submitted to Procurement"
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "submitted", "requisition_version": version.name, "task": procurement_task.name, "record_version": root.record_version}
	return _journal(idempotency_key, "SubmitRequisitionToProcurement", payload, result, root, actor)


def _return(*, task: str, reason: str, affected_section: str, expected_record_version, idempotency_key: str, user: str | None, from_state: str, capacity: str, decision: str, command: str) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"task": task, "reason": reason, "affected_section": affected_section}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason, label="correction")
	affected_section = _section(affected_section)
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = envelope.locked("Requisition Task", task)
	root = records.require_root(task_doc.requisition)
	assignment = authz.require_hopf(actor) if capacity == ROLE_HEAD_OF_PROCUREMENT_FUNCTION else _lead_hod(root, actor)
	envelope.check_record_version(task_doc, expected_record_version)
	if task_doc.status != "Open" or root.current_state != from_state:
		fail("REQ_STALE_VERSION")
	reviewed_version = frappe.get_doc("Requisition Version", task_doc.requisition_version)
	reviewed_package_version = frappe.get_doc("IT Equipment Requirement Package Version", reviewed_version.package_version)
	envelope.bump(reviewed_version, version_status="Returned")
	envelope.bump(reviewed_package_version, version_status="Returned")
	decision_doc = record_decision(task=task_doc, version=reviewed_version, actor=actor, capacity=capacity, decision=decision, assignment=assignment, idempotency_key=idempotency_key, reason=reason, affected_section=affected_section, resulting_state="Draft")
	envelope.bump(task_doc, status="Completed", decision=decision_doc.name)
	new_version, _ = copy_draft_successor(root, reviewed_version, reviewed_package_version)
	result = {"ok": True, "idempotent": False, "action": "returned", "requisition_version": new_version.name, "affected_section": affected_section, "record_version": root.record_version}
	return _journal(idempotency_key, command, payload, result, root, actor)


def return_to_department_author(*, task: str, reason: str, expected_record_version, idempotency_key: str, affected_section: str = "", user: str | None = None) -> dict[str, Any]:
	return _return(task=task, reason=reason, affected_section=affected_section, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, from_state="Awaiting Department Approval", capacity=ROLE_HEAD_OF_USER_DEPARTMENT, decision="Return for correction", command="ReturnToDepartmentAuthor")


def return_requisition_to_department(*, task: str, reason: str, expected_record_version, idempotency_key: str, affected_section: str = "", user: str | None = None) -> dict[str, Any]:
	return _return(task=task, reason=reason, affected_section=affected_section, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, from_state="Submitted to Procurement", capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Return to department", command="ReturnRequisitionToDepartment")


def change_requisition_lead_department(*, task: str, new_lead_org_unit: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.3A `ChangeRequisitionLeadDepartment` — HOPF only, at Submitted to
	Procurement: a reasoned return that preserves the certified submission
	and opens a copied Draft the new lead must certify afresh."""
	actor = authz.actor(user)
	payload = {"task": task, "new_lead_org_unit": new_lead_org_unit, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason, high=500)
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = envelope.locked("Requisition Task", task)
	root = records.require_root(task_doc.requisition)
	assignment = authz.require_hopf(actor)
	envelope.check_record_version(task_doc, expected_record_version)
	if task_doc.status != "Open" or root.current_state != "Submitted to Procurement":
		fail("REQ_STALE_VERSION", "The submitting department can be changed only while the requisition is submitted to Procurement.")
	if new_lead_org_unit not in records.contributing_units(root):
		fail("REQ_DEPARTMENT_NOT_CONTRIBUTING")
	if new_lead_org_unit == root.lead_org_unit_id:
		fail("REQ_CONTROL_INVALID", "Select a different contributing department.")
	reviewed_version = frappe.get_doc("Requisition Version", task_doc.requisition_version)
	reviewed_package_version = frappe.get_doc("IT Equipment Requirement Package Version", reviewed_version.package_version)
	envelope.bump(reviewed_version, version_status="Returned")
	envelope.bump(reviewed_package_version, version_status="Returned")
	decision_doc = record_decision(task=task_doc, version=reviewed_version, actor=actor, capacity=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, decision="Change submitting department and return", assignment=assignment, idempotency_key=idempotency_key, reason=reason, new_lead=new_lead_org_unit, resulting_state="Draft")
	envelope.bump(task_doc, status="Completed", decision=decision_doc.name)
	new_version, _ = copy_draft_successor(root, reviewed_version, reviewed_package_version, lead_directive=new_lead_org_unit)
	result = {"ok": True, "idempotent": False, "action": "lead_changed_and_returned", "requisition_version": new_version.name, "lead_org_unit_id": new_lead_org_unit, "record_version": root.record_version}
	return _journal(idempotency_key, "ChangeRequisitionLeadDepartment", payload, result, root, actor)


def withdraw_requisition(*, requisition: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.1 — the lead Head of User Department closes a pre-authorisation
	Version with no drawdown and no reservation."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason)
	root = records.require_root(requisition)
	assignment = _lead_hod(root, actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state not in ("Draft", "Awaiting Department Approval", "Submitted to Procurement"):
		fail("REQ_STALE_VERSION")
	version, package_version = _load_current(root)
	if root.current_state == "Draft":
		version.content_digest = digest.sha256_hex(records.digest_payload(version, package_version))
		package_version.content_digest = version.content_digest
	envelope.bump(version, version_status="Withdrawn")
	envelope.bump(package_version, version_status="Withdrawn")
	cancel_open_tasks(root)
	record_decision(task=None, version=version, actor=actor, capacity=ROLE_HEAD_OF_USER_DEPARTMENT, decision="Withdraw requisition", assignment=assignment, idempotency_key=idempotency_key, reason=reason, resulting_state="Withdrawn")
	root.current_state = "Withdrawn"
	records.release_slot(root)
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "withdrawn", "record_version": root.record_version}
	return _journal(idempotency_key, "WithdrawRequisition", payload, result, root, actor)


def _lead_hod_or_hopf(root, actor: str) -> tuple[Any, str]:
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	decision = authorise_record(user=actor, business_role=ROLE_HEAD_OF_PROCUREMENT_FUNCTION, organisation_unit="", purpose=PURPOSE_COMMAND)
	if decision.allowed:
		return decision.assignment, ROLE_HEAD_OF_PROCUREMENT_FUNCTION
	return _lead_hod(root, actor), ROLE_HEAD_OF_USER_DEPARTMENT


def request_upstream_plan_correction(*, requisition: str, reason: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.4A `RequestUpstreamPlanCorrection` — freeze the exact
	pre-authorisation Version, close its open tasks and record Planning's
	request and item hold, all in this one transaction: if Planning refuses,
	nothing here changes."""
	actor = authz.actor(user)
	payload = {"requisition": requisition, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	reason = _reason(reason, label="description of what is wrong")
	root = records.require_root(requisition)
	assignment, capacity = _lead_hod_or_hopf(root, actor)
	envelope.check_record_version(root, expected_record_version)
	if root.current_state not in ("Draft", "Awaiting Department Approval", "Submitted to Procurement"):
		fail("REQ_STALE_VERSION", "A Planning correction can be requested only before authorisation.")
	version, package_version = _load_current(root)
	with envelope.atomic("upstream-correction"):
		if version.version_status == "Draft":
			version.content_digest = digest.sha256_hex(records.digest_payload(version, package_version))
			package_version.content_digest = version.content_digest
		envelope.bump(version, version_status="Upstream correction required")
		envelope.bump(package_version, version_status="Upstream correction required")
		cancel_open_tasks(root)
		correction = eligibility_gateway.receive_plan_item_correction_request(
			plan_item_id=root.plan_item_id, requisition_reference=root.requisition_reference,
			requisition_version=version.name, reason=reason, idempotency_key=f"{idempotency_key}:planning",
		)
		record_decision(task=None, version=version, actor=actor, capacity=capacity, decision="Request Planning correction", assignment=assignment, idempotency_key=idempotency_key, reason=reason, resulting_state="Upstream correction required")
		root.current_state = "Upstream correction required"
		root.planning_correction_request_id = correction.get("correction_request") or ""
		records.release_slot(root)
		envelope.bump(root)
		events.publish(requisition=root.name, requisition_version=version.name, event_type="ProcurementRequisitionCorrectionRequested", payload={"correction_request": root.planning_correction_request_id})
	result = {"ok": True, "idempotent": False, "action": "upstream_correction_requested", "correction_request": root.planning_correction_request_id, "record_version": root.record_version}
	return _journal(idempotency_key, "RequestUpstreamPlanCorrection", payload, result, root, actor)
