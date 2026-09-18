# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §7.2 — `StartTender`, `SaveTenderDraft` and the three
evidence-requirement commands.

`StartTender` rechecks the handoff, the template release and the eight
compatibility checks, then creates the Tender, its Draft Version 1 (snapshot
+ defaults) and records the authoritative Requisition consumption inside
one savepoint: the Draft and the consumption commit together or neither
commits (§5.8 invariants 1–3). A repeated or concurrent start for one
handoff returns the one Tender's identity (TPR08-AC-007). `SaveTenderDraft`
accepts only applicable §5.2 officer fields and regenerates the review
result and every generated digest on every save (TPR08-AC-025)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_templates import loader
from kentender_procurement.tenders.services import clock, compatibility, controls, envelope, events, evidence, handoff_gateway, references, review, serializer, template_binding
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail

PRODUCT_KEY = "IT-EQUIPMENT-OPEN-V1"
EDITABLE_STATUSES = ("Draft",)


# --------------------------------------------------------------------------
# helpers shared by the command modules
# --------------------------------------------------------------------------


def resolve_tender_name(tender: str) -> str:
	"""Commands and reads accept the doc name or the business reference."""
	value = cstr(tender).strip()
	if not value:
		authz.not_found()
	if frappe.db.exists("Tender", value):
		return value
	name = frappe.db.get_value("Tender", {"tender_reference": value}, "name")
	if not name:
		authz.not_found()
	return cstr(name)


def load(tender: str) -> tuple[Any, Any]:
	"""Row-locked root plus its current Version."""
	root = envelope.locked("Tender", resolve_tender_name(tender))
	if not root.current_version:
		fail("TND_STALE_VERSION", "This Tender has no current Version.")
	return root, frappe.get_doc("Tender Version", root.current_version)


def require_editable(root, version) -> None:
	if root.overall_status == "Cancelled":
		fail("TND_CANCELLED")
	if version.status not in EDITABLE_STATUSES or root.overall_status != "Draft":
		fail("TND_STALE_VERSION", "This Tender Version is no longer editable.")


def version_dict(version) -> dict[str, Any]:
	return {"name": version.name, "version_number": int(version.version_number), "status": version.status, "record_version": int(version.record_version or 0)}


def _regenerate(root, version) -> dict[str, Any]:
	"""Recompute the review result and every generated digest for a Draft."""
	result = review.run(root, version, with_renders=True)
	review.store(version, result)
	return result


def _touch(root, version, **version_values) -> None:
	envelope.bump(version, **version_values)
	envelope.bump(root)


# --------------------------------------------------------------------------
# StartTender
# --------------------------------------------------------------------------


def start_tender(*, handoff: str, idempotency_key: str, user: str | None = None, fixture_namespace: str = "") -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_officer(actor, masked=False)
	payload = {"handoff": handoff}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	handoff_doc = handoff_gateway.load(handoff)
	handoff_gateway.require_startable(handoff_doc)
	existing = handoff_gateway.consumer_tender(handoff_doc)
	if existing:
		root = frappe.get_doc("Tender", existing)
		result = {"ok": True, "idempotent": False, "action": "existing", "tender": root.name, "tender_reference": root.tender_reference, "tender_version": root.current_version, "record_version": root.record_version}
		envelope.record_command(idempotency_key=idempotency_key, command="StartTender", payload=payload, result=result, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=fixture_namespace)
		return result
	if handoff_doc.consumed_at:
		fail("TND_HANDOFF_CONFLICT", detail={"handoff": handoff_doc.name, "tender": cstr(handoff_doc.tender)})
	binding = template_binding.require_available()
	snapshot, snapshot_digest = snap.build(handoff_doc)
	compatibility.require_supported(snapshot)

	with envelope.atomic("start"):
		reference = references.tender_reference(fiscal_year=cstr(snapshot.get("fiscal_year")), plan_item_id_value=cstr(snapshot.get("plan_item_id")))
		units = snapshot.get("contributing_org_unit_ids") or []
		lead = cstr(handoff_gateway.requisition_summary(handoff_doc).get("lead_org_unit")) or snap.lead_unit(snapshot)
		root = envelope.insert(
			frappe.get_doc(
				{
					"doctype": "Tender", "tender_reference": reference, "requirement_title": snapshot.get("requirement_title"), "requisition_handoff": handoff_doc.name,
					"requisition": handoff_doc.requisition, "requisition_reference": snapshot.get("requisition_reference"), "requisition_version": handoff_doc.requisition_version,
					"plan_item_id": snapshot.get("plan_item_id"), "plan_item_version_id": snapshot.get("plan_version_id"), "fiscal_year": snapshot.get("fiscal_year") if frappe.db.exists("Fiscal Year", cstr(snapshot.get("fiscal_year"))) else None,
					"lead_org_unit": lead if lead and frappe.db.exists("Organisation Unit", lead) else None, "contributing_org_unit_ids": json.dumps(units),
					"product_key": PRODUCT_KEY, "template_release_id": binding["template_release_id"], "official_source_digest": binding["official_source_digest"],
					"bundle_digest": binding["bundle_digest"], "overall_status": "Draft", "record_version": 0, "fixture_namespace": fixture_namespace,
				}
			)
		)
		version = frappe.get_doc(
			{
				"doctype": "Tender Version", "tender": root.name, "version_number": 1, "status": "Draft", "requisition_handoff": handoff_doc.name,
				"requisition_version": handoff_doc.requisition_version, "template_release_id": binding["template_release_id"], "official_source_digest": binding["official_source_digest"],
				"bundle_digest": binding["bundle_digest"], "requisition_snapshot_digest": snapshot_digest, "requisition_snapshot_json": json.dumps(snapshot, sort_keys=True, default=str),
				"officer_payload_json": json.dumps(controls.normalise(controls.defaults(snapshot)), sort_keys=True, default=str),
				"prepared_by": actor, "prepared_at": clock.now(), "record_version": 0, "fixture_namespace": fixture_namespace,
			}
		)
		envelope.insert(version)
		_regenerate(root, version)
		envelope.bump(version)
		envelope.bump(root, current_version=version.name, submission_deadline=None)
		handoff_gateway.consume(handoff=handoff_doc.name, tender=root.name, tender_version=version.name, template_key=loader.TEMPLATE_KEY, template_version=loader.TEMPLATE_VERSION, idempotency_key=f"{idempotency_key}:consume")
		events.emit(
			tender=root.name, event_type="TenderStarted", command="StartTender", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="", resulting_status="Draft", record_version=root.record_version, subject_type="Tender Version", subject_id=version.name,
			payload={"requisition_handoff": handoff_doc.name, "handoff_digest": handoff_doc.handoff_digest, "requisition_snapshot_digest": snapshot_digest, "template_release_id": binding["template_release_id"], "bundle_digest": binding["bundle_digest"]},
			fixture_namespace=fixture_namespace,
		)
	result = {"ok": True, "idempotent": False, "action": "started", "tender": root.name, "tender_reference": root.tender_reference, "tender_version": version.name, "record_version": root.record_version}
	envelope.record_command(idempotency_key=idempotency_key, command="StartTender", payload=payload, result=result, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=fixture_namespace)
	return result


# --------------------------------------------------------------------------
# SaveTenderDraft
# --------------------------------------------------------------------------


def save_tender_draft(*, tender: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_officer(actor)
	payload = {"tender": tender, "values": json.dumps(values, sort_keys=True, default=str) if isinstance(values, dict) else cstr(values)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = load(tender)
	require_editable(root, version)
	envelope.check_record_version(root, expected_record_version)
	current = serializer.officer_state(version)
	clean, errors = controls.validate(values, current)
	if errors:
		return {"ok": False, "errors": errors, "record_version": root.record_version}
	changed = {field: {"previous": current.get(field), "new": value} for field, value in clean.items() if current.get(field) != value}
	merged = dict(current)
	merged.update(clean)
	# Clear conditional fields that no longer apply so hidden values never survive.
	for field in list(merged):
		if merged[field] is not None and field in controls.CATALOGUE and not controls.applies(field, merged):
			merged[field] = None
			changed.setdefault(field, {"previous": current.get(field), "new": None})
	with envelope.atomic("save"):
		version.officer_payload_json = json.dumps(controls.normalise(merged), sort_keys=True, default=str)
		result = _regenerate(root, version)
		_touch(root, version)
		events.emit(
			tender=root.name, event_type="TenderDraftSaved", command="SaveTenderDraft", idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Draft", resulting_status="Draft", record_version=root.record_version, subject_type="Tender Version", subject_id=version.name,
			payload={"changed_fields": changed, "review_result_digest": result["review_result_digest"], "package_digest": version.package_digest}, fixture_namespace=root.fixture_namespace,
		)
	out = {
		"ok": True, "idempotent": False, "action": "saved", "tender": root.name, "record_version": root.record_version, "version": version_dict(version),
		"review": {"result": result["result"], "must_fix_count": result["must_fix_count"], "review_note_count": result["review_note_count"]},
		"tasks": task_statuses(version),
	}
	envelope.record_command(idempotency_key=idempotency_key, command="SaveTenderDraft", payload=payload, result=out, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return out


def task_statuses(version) -> dict[str, str]:
	state = serializer.officer_state(version)
	baseline = controls.defaults(snap.load(version))
	details = controls.task_status(state, controls.TASK_DETAILS, baseline=baseline)
	requirements = controls.task_status(state, controls.TASK_REQUIREMENTS, baseline=baseline)
	must_fix = [r for r in version.get("review_findings") or [] if r.severity == review.MUST_FIX]
	if details == "Complete" and requirements == "Complete":
		rev = "Needs attention" if must_fix else "Complete"
	else:
		rev = "Not started"
	return {controls.TASK_DETAILS: details, controls.TASK_REQUIREMENTS: requirements, controls.TASK_REVIEW: rev}


# --------------------------------------------------------------------------
# Evidence requirements (§4.4)
# --------------------------------------------------------------------------


def _evidence_command(*, command: str, tender: str, expected_record_version, idempotency_key: str, user: str | None, payload: dict[str, Any], mutate) -> dict[str, Any]:
	actor = authz.actor(user)
	assignment = authz.require_officer(actor)
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	root, version = load(tender)
	require_editable(root, version)
	envelope.check_record_version(root, expected_record_version)
	snapshot = snap.load(version)
	outcome = mutate(version, snapshot)
	if outcome.get("errors"):
		return {"ok": False, "errors": outcome["errors"], "record_version": root.record_version}
	with envelope.atomic(command):
		_regenerate(root, version)
		_touch(root, version)
		events.emit(
			tender=root.name, event_type=f"Tender{command}", command=command, idempotency_key=idempotency_key, actor=actor, assignment_snapshot=authz.authority_snapshot(assignment),
			previous_status="Draft", resulting_status="Draft", record_version=root.record_version, subject_type="Tender Evidence Requirement", subject_id=outcome["evidence_requirement_id"],
			payload={"evidence": outcome.get("row"), "package_digest": version.package_digest}, fixture_namespace=root.fixture_namespace,
		)
	result = {"ok": True, "idempotent": False, "action": command, "tender": root.name, "record_version": root.record_version, "evidence_requirement_id": outcome["evidence_requirement_id"], "evidence_requirements": evidence.rows_as_dicts(version)}
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type="Tender", document_name=root.name, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


def add_tender_evidence_requirement(*, tender: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(version, snapshot):
		clean, errors = evidence.validate_values(values, snapshot)
		if errors:
			return {"errors": errors}
		row_id = evidence.next_id(version)
		order = len(version.get("evidence_requirements") or []) + 1
		version.append("evidence_requirements", {"evidence_requirement_id": row_id, "row_order": order, **clean})
		return {"evidence_requirement_id": row_id, "row": clean}

	payload = {"tender": tender, "values": json.dumps(values, sort_keys=True, default=str) if isinstance(values, dict) else cstr(values)}
	return _evidence_command(command="AddTenderEvidenceRequirement", tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, payload=payload, mutate=mutate)


def update_tender_evidence_requirement(*, tender: str, evidence_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(version, snapshot):
		row = next((r for r in version.get("evidence_requirements") or [] if r.evidence_requirement_id == evidence_requirement_id), None)
		if row is None:
			fail("TND_CONTROL_INVALID", "That evidence requirement does not exist on this Draft.")
		merged = {"label": row.label, "evidence_type": row.evidence_type, "linked_requirement_type": row.linked_requirement_type, "linked_requirement_id": row.linked_requirement_id, "mandatory": row.mandatory}
		merged.update(values if isinstance(values, dict) else {})
		clean, errors = evidence.validate_values(merged, snapshot)
		if errors:
			return {"errors": errors}
		for key, value in clean.items():
			row.set(key, value)
		return {"evidence_requirement_id": evidence_requirement_id, "row": clean}

	payload = {"tender": tender, "evidence_requirement_id": evidence_requirement_id, "values": json.dumps(values, sort_keys=True, default=str) if isinstance(values, dict) else cstr(values)}
	return _evidence_command(command="UpdateTenderEvidenceRequirement", tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, payload=payload, mutate=mutate)


def remove_tender_evidence_requirement(*, tender: str, evidence_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(version, snapshot):
		rows = [r for r in version.get("evidence_requirements") or [] if r.evidence_requirement_id != evidence_requirement_id]
		if len(rows) == len(version.get("evidence_requirements") or []):
			fail("TND_CONTROL_INVALID", "That evidence requirement does not exist on this Draft.")
		version.set("evidence_requirements", [])
		for order, row in enumerate(rows, start=1):
			version.append("evidence_requirements", {"evidence_requirement_id": row.evidence_requirement_id, "label": row.label, "evidence_type": row.evidence_type, "linked_requirement_type": row.linked_requirement_type, "linked_requirement_id": row.linked_requirement_id, "mandatory": row.mandatory, "row_order": order})
		return {"evidence_requirement_id": evidence_requirement_id, "row": None}

	payload = {"tender": tender, "evidence_requirement_id": evidence_requirement_id}
	return _evidence_command(command="RemoveTenderEvidenceRequirement", tender=tender, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, payload=payload, mutate=mutate)
