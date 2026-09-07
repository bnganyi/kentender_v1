# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5.12 — the immutable `AuthorisedRequisitionHandoff v1.3`
built atomically with authorisation. Tender Preparation is the only reader;
this module never edits its own output after `insert()`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import digest

HANDOFF_VERSION = "1.3"


def build_payload(*, root, version, package_version, projection: dict[str, Any], reservations_by_line: dict[str, str]) -> dict[str, Any]:
	sources_by_line = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	drawdown = []
	for line in version.drawdown_lines:
		drawdown.append(
			{
				"drawdown_line_id": line.drawdown_line_id, "source_line_id": line.source_line_id,
				"plan_item_line_id": line.plan_item_line_id, "contributing_org_unit": line.contributing_org_unit,
				"requested_quantity": line.requested_quantity, "requested_value": line.requested_value,
				"unit": line.unit, "reservation_id": reservations_by_line.get(line.drawdown_line_id, ""),
				"planning_drawdown_reference": line.planning_drawdown_reference,
			}
		)
	return {
		"requisition_reference": root.requisition_reference, "requisition_version": version.name,
		"content_digest": version.content_digest,
		"plan_id": root.plan_id, "plan_version_id": root.plan_version_id, "plan_item_id": root.plan_item_id,
		"fiscal_year": projection.get("fiscal_year"),
		"contributing_org_unit_ids": sorted({u.organisation_unit for u in root.contributing_org_units}),
		"strategic_objective": root.strategic_objective, "strategic_objective_path": root.strategic_objective_path,
		"procurement_category": root.procurement_category, "plan_horizon": root.plan_horizon,
		"multi_year_justification": root.multi_year_justification,
		"drawdown_lines": drawdown,
		"business_need": "; ".join(sorted({s.get("description", "") for s in projection.get("sources", []) if s.get("description")})),
		"expected_operational_result": "; ".join(sorted({s.get("expected_operational_result", "") for s in projection.get("sources", []) if s.get("expected_operational_result")})),
		"planned_method": projection.get("procurement_method"), "planned_dates": projection.get("planned_dates"),
		"requirement_title": version.requirement_title, "delivery_location": version.delivery_location,
		"latest_delivery_date": cstr(version.latest_delivery_date),
		"items": [
			{"requisition_item_id": r.requisition_item_id, "plan_item_line_id": r.plan_item_line_id, "equipment_category": r.equipment_category, "item_name": r.item_name, "quantity": r.quantity, "unit": r.unit, "intended_use": r.intended_use}
			for r in package_version.items
		],
		"minimum_warranty_months": package_version.minimum_warranty_months, "onsite_support_required": bool(package_version.onsite_support_required),
		"maximum_support_response_hours": package_version.maximum_support_response_hours, "manufacturer_support_required": bool(package_version.manufacturer_support_required),
		"service_location_constraint": package_version.service_location_constraint, "support_description": package_version.support_description,
		"technical_requirements": [
			{"technical_requirement_id": r.technical_requirement_id, "applies_to_scope": r.applies_to_scope, "applies_to_id": r.applies_to_id, "characteristic_key": r.characteristic_key, "comparison": r.comparison, "required_value_json": r.required_value_json, "unit": r.unit}
			for r in package_version.technical_requirements
		],
		"related_services": [
			{"service_requirement_id": r.service_requirement_id, "service_type": r.service_type, "applies_to_scope": r.applies_to_scope, "applies_to_id": r.applies_to_id, "required_result": r.required_result, "completion_date": cstr(r.completion_date), "acceptance_evidence": r.acceptance_evidence}
			for r in package_version.related_services
		],
		"acceptance_requirements": [
			{"acceptance_requirement_id": r.acceptance_requirement_id, "applies_to_scope": r.applies_to_scope, "applies_to_id": r.applies_to_id, "check_type": r.check_type, "pass_condition": r.pass_condition, "evidence_type": r.evidence_type}
			for r in package_version.acceptance_requirements
		],
		"supporting_materials": [
			{"supporting_material_id": r.supporting_material_id, "title": r.title, "document_type": r.document_type, "treatment": r.treatment, "file_digest": r.file_digest, "linked_requirement_ids_json": r.linked_requirement_ids_json}
			for r in package_version.supporting_materials
		],
		"product_pattern": "IT Equipment", "reservation_category_value": projection.get("reservation_category"), "lotting_indicator": projection.get("lotting_indicator"),
		"handoff_version": HANDOFF_VERSION, "generated_at": cstr(now_datetime()),
	}


def build_and_insert(*, root, version, package_version, projection: dict[str, Any], reservations_by_line: dict[str, str], decisions: list[dict[str, Any]]) -> Any:
	payload = build_payload(root=root, version=version, package_version=package_version, projection=projection, reservations_by_line=reservations_by_line)
	payload["decisions"] = decisions
	handoff_digest = digest.sha256_hex(payload)
	payload["handoff_digest"] = handoff_digest
	doc = frappe.get_doc(
		{
			"doctype": "Authorised Requisition Handoff", "requisition": root.name, "requisition_version": version.name,
			"payload_json": digest.canonical_json(payload), "handoff_digest": handoff_digest, "handoff_version": HANDOFF_VERSION,
			"generated_at": now_datetime(),
		}
	).insert(ignore_permissions=True)
	return doc


def record_handoff_consumption(
	*, handoff: str, tender: str, tender_version: str, template_key: str, template_version: str, idempotency_key: str,
) -> dict[str, Any]:
	"""§10.2 `RecordHandoffConsumption` — a module boundary event, not a
	human decision (no Requisitions responsibility gates it, the same way
	`events.acknowledge()` gates none): Tender Preparation is the only real
	caller once it exists (D4), idempotently storing neutral consumption
	evidence on the immutable handoff itself. A repeat call naming the same
	Tender/Tender Version is a no-op; a second, DIFFERENT consumer is
	refused — a handoff is consumed by exactly one Tender."""
	from kentender_procurement.procurement_requisitions.services import envelope
	from kentender_procurement.procurement_requisitions.services.errors import fail

	payload = {"handoff": handoff, "tender": tender, "tender_version": tender_version, "template_key": template_key, "template_version": template_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not handoff or not frappe.db.exists("Authorised Requisition Handoff", handoff):
		frappe.throw("Handoff not found", frappe.DoesNotExistError)
	doc = envelope.locked("Authorised Requisition Handoff", handoff)
	if doc.consumed_at:
		if doc.tender == cstr(tender) and doc.tender_version == cstr(tender_version):
			result = {"ok": True, "idempotent": False, "action": "already_consumed", "handoff": doc.name, "consumed_at": cstr(doc.consumed_at)}
			envelope.record_command(idempotency_key=idempotency_key, command="RecordHandoffConsumption", payload=payload, result=result, document_type="Authorised Requisition Handoff", document_name=doc.name)
			return result
		fail("REQ_HANDOFF_CONSUMED", "This handoff was already consumed by a different Tender.")

	doc.tender = cstr(tender)
	doc.tender_version = cstr(tender_version)
	doc.template_key = cstr(template_key)
	doc.template_version = cstr(template_version)
	doc.consumed_at = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.set_value("Procurement Requisition", doc.requisition, "handoff_consumed_at", doc.consumed_at)

	result = {"ok": True, "idempotent": False, "action": "consumed", "handoff": doc.name, "consumed_at": cstr(doc.consumed_at)}
	envelope.record_command(idempotency_key=idempotency_key, command="RecordHandoffConsumption", payload=payload, result=result, document_type="Authorised Requisition Handoff", document_name=doc.name)
	return result
