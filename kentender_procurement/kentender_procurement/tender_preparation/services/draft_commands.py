# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §11.2 — the Draft-stage commands: `PrepareTender`,
`SaveTenderDraft`, the three evidence-row commands and
`RunTenderReadiness`. Every command runs inside the envelope (idempotency
key, expected record version under a row lock, monotonic bump), re-checks
the actor's responsibility and the Version's state on the server, and
records itself in the command journal (§15)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_preparation.services import compatibility, controls, envelope, evidence, handoff_gateway, readiness, references, serializer
from kentender_procurement.tender_preparation.services import snapshot as snap
from kentender_procurement.tender_preparation.services import tender_authorization as authz
from kentender_procurement.tender_preparation.services.errors import fail
from kentender_procurement.tender_templates import registry

OPEN_STATES = ("Draft", "Submitted for approval", "Approved for publication")


def load(tender: str) -> tuple[Any, Any]:
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = frappe.get_doc("Prepared Tender", tender)
	version = frappe.get_doc("Tender Preparation Version", root.current_version)
	return root, version


def _require_draft(root, version) -> None:
	if root.current_state != "Draft" or version.version_status != "Draft":
		fail("TPR_STALE_VERSION", "This Tender Version is no longer a Draft.")


def _refresh_content(root, version, snapshot: dict[str, Any]) -> None:
	version.content_digest = serializer.content_digest(root, version, snapshot)


def existing_tender_for_handoff(handoff: str) -> dict[str, Any] | None:
	rows = frappe.get_all("Prepared Tender", filters={"requisition_handoff": handoff, "current_state": ("in", OPEN_STATES)}, fields=["name", "tender_reference", "current_state", "current_version", "record_version"], limit=1)
	return rows[0] if rows else None


# --------------------------------------------------------------------------
# PrepareTender (§10.2, §11.2)
# --------------------------------------------------------------------------


def prepare_tender(*, handoff: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"handoff": handoff}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authz.require_officer(actor)

	handoff_doc = handoff_gateway.load(handoff)
	if handoff_doc is None:
		fail("TPR_HANDOFF_INVALID", "The source Requisition handoff does not exist.")
	if handoff_gateway.requisition_state(handoff_doc) != "Authorised":
		fail("TPR_HANDOFF_INVALID")
	if cstr(handoff_doc.handoff_version) != handoff_gateway.REQUIRED_HANDOFF_VERSION:
		fail("TPR_HANDOFF_INVALID", f"Handoff version {handoff_doc.handoff_version} is not the required v{handoff_gateway.REQUIRED_HANDOFF_VERSION}.")

	existing = existing_tender_for_handoff(handoff_doc.name)
	if existing:
		result = {"ok": True, "idempotent": False, "action": "reused", "tender": existing.name, "tender_reference": existing.tender_reference, "tender_version": existing.current_version, "record_version": existing.record_version, "current_state": existing.current_state}
		envelope.record_command(idempotency_key=idempotency_key, command="PrepareTender", payload=payload, result=result, document_type="Prepared Tender", document_name=existing.name, actor=actor)
		return result
	if handoff_doc.consumed_at:
		fail("TPR_HANDOFF_CONSUMED", detail={"tender": handoff_doc.tender})

	snapshot, snapshot_digest = snap.build(handoff_doc)
	failure = compatibility.first_failure(compatibility.evaluate(snapshot, handoff_version=handoff_doc.handoff_version))
	if failure:
		fail("TPR_PRODUCT_UNSUPPORTED", f"This Requisition is not supported by the IT-equipment Tender pattern ({failure.test}: {failure.actual}).", {"test": failure.test, "required": failure.required, "actual": failure.actual})
	binding = registry.resolve()

	with envelope.atomic("prepare_tender"):
		reference = references.tender_reference(plan_item_id=cstr(snapshot.get("plan_item_id")))
		root = frappe.get_doc(
			{
				"doctype": "Prepared Tender", "tender_reference": reference,
				"requisition_handoff": handoff_doc.name, "requisition": handoff_doc.requisition,
				"requisition_reference": snapshot.get("requisition_reference"), "requisition_version": handoff_doc.requisition_version,
				"requisition_content_digest": snapshot.get("content_digest"), "handoff_digest": handoff_doc.handoff_digest,
				"handoff_version": handoff_doc.handoff_version, "plan_item_id": snapshot.get("plan_item_id"), "fiscal_year": snapshot.get("fiscal_year"),
				"requirement_title": snapshot.get("requirement_title"),
				"template_key": binding["template_key"], "template_version": binding["template_version"],
				"official_source_digest": binding["official_source_digest"], "bundle_digest": binding["bundle_digest"],
				"current_state": "Draft", "prepared_by": actor, "record_version": 0,
			}
		).insert(ignore_permissions=True)
		version = frappe.get_doc(
			{
				"doctype": "Tender Preparation Version", "tender": root.name, "version_number": 1, "version_status": "Draft",
				"snapshot_json": snap.digest.canonical_json(snapshot), "snapshot_digest": snapshot_digest,
				"prepared_by": actor, "prepared_at": now_datetime(), "record_version": 0,
				**controls.defaults(snapshot),
			}
		)
		evidence.rebuild(version, snapshot)
		version.insert(ignore_permissions=True)
		_refresh_content(root, version, snapshot)
		version.save(ignore_permissions=True)
		root.current_version = version.name
		root.save(ignore_permissions=True)
		consumption = handoff_gateway.record_consumption(
			handoff=handoff_doc.name, tender=root.name, tender_version=version.name, template_key=binding["template_key"],
			template_version=binding["template_version"], idempotency_key=f"{idempotency_key}:consume",
		)

	result = {"ok": True, "idempotent": False, "action": "created", "tender": root.name, "tender_reference": root.tender_reference, "tender_version": version.name, "record_version": root.record_version, "current_state": root.current_state, "consumption": consumption.get("action")}
	envelope.record_command(idempotency_key=idempotency_key, command="PrepareTender", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# SaveTenderDraft (§8, §11.2)
# --------------------------------------------------------------------------


def save_tender_draft(*, tender: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"tender": tender, "values": values}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authz.require_officer(actor)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = envelope.locked("Prepared Tender", tender)
	version = envelope.locked("Tender Preparation Version", root.current_version)
	envelope.check_record_version(root, expected_record_version)
	_require_draft(root, version)
	snapshot = snap.load(version)

	clean, errors = controls.validate(values, serializer.officer_state(version))
	if errors:
		return {"ok": False, "errors": errors, "record_version": root.record_version}

	task4_before = {f: version.get(f) for f in controls.FIELDS_BY_TASK[4]}
	for field, value in clean.items():
		version.set(field, value)
	if not version.prepared_by:
		version.prepared_by = actor
		version.prepared_at = now_datetime()
	if {f: version.get(f) for f in controls.FIELDS_BY_TASK[4]} != task4_before:
		evidence.rebuild(version, snapshot)
	_refresh_content(root, version, snapshot)
	envelope.bump(version)
	envelope.bump(root)

	result = {"ok": True, "idempotent": False, "errors": {}, "tender": root.name, "tender_version": version.name, "record_version": root.record_version, "saved": sorted(clean), "missing": [{"task": t, "field": f, "label": l} for t, f, l in controls.missing(serializer.officer_state(version))]}
	envelope.record_command(idempotency_key=idempotency_key, command="SaveTenderDraft", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


# --------------------------------------------------------------------------
# Evidence rows (§7.4, §8.4)
# --------------------------------------------------------------------------


def _evidence_command(*, command: str, tender: str, payload: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None, mutate) -> dict[str, Any]:
	actor = authz.actor(user)
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authz.require_officer(actor)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = envelope.locked("Prepared Tender", tender)
	version = envelope.locked("Tender Preparation Version", root.current_version)
	envelope.check_record_version(root, expected_record_version)
	_require_draft(root, version)
	snapshot = snap.load(version)
	outcome = mutate(version, snapshot)
	if outcome.get("errors"):
		return {"ok": False, "errors": outcome["errors"], "record_version": root.record_version}
	_refresh_content(root, version, snapshot)
	envelope.bump(version)
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "errors": {}, "tender": root.name, "tender_version": version.name, "record_version": root.record_version, **outcome}
	envelope.record_command(idempotency_key=idempotency_key, command=command, payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result


def add_tender_evidence_requirement(*, tender: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(version, snapshot):
		clean, errors = evidence.validate_additional(values or {}, snapshot)
		if errors:
			return {"errors": errors}
		row_id = evidence.next_additional_id(version)
		order = max([r.row_order or 0 for r in version.get("evidence_requirements") or []] or [0]) + 1
		version.append("evidence_requirements", {**clean, "evidence_requirement_id": row_id, "source": evidence.SOURCE_ADDITIONAL, "row_order": order})
		return {"evidence_requirement_id": row_id}

	return _evidence_command(command="AddTenderEvidenceRequirement", tender=tender, payload={"tender": tender, "values": values}, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, mutate=mutate)


def update_tender_evidence_requirement(*, tender: str, evidence_requirement_id: str, values: dict[str, Any], expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(version, snapshot):
		row = next((r for r in version.get("evidence_requirements") or [] if r.evidence_requirement_id == evidence_requirement_id), None)
		if row is None:
			fail("TPR_CONTROL_INVALID", "Unknown evidence row.")
		if row.source != evidence.SOURCE_ADDITIONAL:
			fail("TPR_INHERITED_EDIT", "Fixed and generated evidence rows cannot be edited; change the Task 4 decision instead.")
		clean, errors = evidence.validate_additional(values or {}, snapshot)
		if errors:
			return {"errors": errors}
		for k, v in clean.items():
			row.set(k, v)
		return {"evidence_requirement_id": evidence_requirement_id}

	return _evidence_command(command="UpdateTenderEvidenceRequirement", tender=tender, payload={"tender": tender, "evidence_requirement_id": evidence_requirement_id, "values": values}, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, mutate=mutate)


def remove_tender_evidence_requirement(*, tender: str, evidence_requirement_id: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	def mutate(version, snapshot):
		row = next((r for r in version.get("evidence_requirements") or [] if r.evidence_requirement_id == evidence_requirement_id), None)
		if row is None:
			fail("TPR_CONTROL_INVALID", "Unknown evidence row.")
		if row.source != evidence.SOURCE_ADDITIONAL:
			fail("TPR_INHERITED_EDIT", "Fixed and generated evidence rows cannot be removed; change the Task 4 decision instead.")
		version.remove(row)
		return {"evidence_requirement_id": evidence_requirement_id, "removed": True}

	return _evidence_command(command="RemoveTenderEvidenceRequirement", tender=tender, payload={"tender": tender, "evidence_requirement_id": evidence_requirement_id}, expected_record_version=expected_record_version, idempotency_key=idempotency_key, user=user, mutate=mutate)


# --------------------------------------------------------------------------
# RunTenderReadiness (§10.1, §11.2)
# --------------------------------------------------------------------------


def run_tender_readiness(*, tender: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	payload = {"tender": tender}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	authz.require_officer(actor)
	if not tender or not frappe.db.exists("Prepared Tender", tender):
		authz.not_found()
	root = envelope.locked("Prepared Tender", tender)
	version = envelope.locked("Tender Preparation Version", root.current_version)
	envelope.check_record_version(root, expected_record_version)
	_require_draft(root, version)
	snapshot = snap.load(version)
	evidence.rebuild(version, snapshot)
	_refresh_content(root, version, snapshot)
	result_run = readiness.run(root, version)
	readiness.store(version, result_run)
	envelope.bump(version)
	envelope.bump(root)
	result = {
		"ok": True, "idempotent": False, "tender": root.name, "tender_version": version.name, "record_version": root.record_version,
		"blocking_count": result_run["blocking_count"], "warning_count": result_run["warning_count"], "findings": result_run["findings"],
		"readiness_digest": result_run["readiness_digest"], "ready": result_run["blocking_count"] == 0,
	}
	envelope.record_command(idempotency_key=idempotency_key, command="RunTenderReadiness", payload=payload, result=result, document_type="Prepared Tender", document_name=root.name, actor=actor)
	return result
