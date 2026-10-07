# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §5.12/§9.2 — `AuthorisedRequisitionHandoff v1.4` and its
guarded consumption.

v1.4 (owner D4, 24 Sep 2026) supersedes v1.3 under a new version rather than a
second shape under the old name (§5.14): Money and Quantity are exact decimal
strings, and the payload adds the pinned item Version, the Strategic Objective
identity, the independent County treatment and the exact verified rule
snapshots, one Budget reservation per drawdown line and the nine compatibility
results. Stored v1.3 handoffs are history and are never rewritten or rehashed.

`record_handoff_consumption` is the owner command Tender Preparation calls in
the same transaction as its Draft Tender, in-process only (there is no web
endpoint, AUD-REQ-001; the Tenders gateway first verifies the Tender exists
and was created from this handoff). It takes the locks revocation takes, in
the same order — Requisition root, then handoff (AUD-XC-109) — rechecks
Authorised and unconsumed, and binds exactly one Tender. There is no release: once consumed, the authorisation cannot be
revoked (§7.4).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_requisitions.services import digest, envelope, precision, records
from kentender_procurement.procurement_requisitions.services.errors import fail

HANDOFF_VERSION = "1.4"


def _rows(doc, fieldname: str, fields: tuple[str, ...]) -> list[dict[str, Any]]:
	return [{f: row.get(f) for f in fields} for row in doc.get(fieldname) or []]


def build_payload(*, root, version, package_version, projection: dict[str, Any], checks: list[Any], reservations: list[dict[str, Any]], hopf_decision) -> dict[str, Any]:
	sources = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	package = frappe.get_doc("IT Equipment Requirement Package", package_version.package)
	submit = records.decision_of(version.name, "Submit to Procurement")
	lines = []
	for line, reservation in zip(version.drawdown_lines, reservations):
		source = sources.get(line.plan_item_line_id, {})
		lines.append(
			{
				"drawdown_line_id": line.drawdown_line_id, "plan_item_line_id": line.plan_item_line_id, "source_line_id": line.source_line_id,
				"source_origin": source.get("source_origin"), "need_revision": source.get("need_revision"), "dpp_entry": source.get("dpp_entry"),
				"contributing_org_unit": line.contributing_org_unit, "budget_line": source.get("budget_line"),
				"requested_quantity": precision.quantity_text(precision.stored_quantity(line.requested_quantity)),
				"requested_value": precision.money_text(precision.stored_money(line.requested_value)), "unit": line.unit,
				"reservation_id": reservation["reservation_id"], "reservation_reference": reservation.get("reservation_code"),
				"planning_drawdown_reference": line.planning_drawdown_reference,
			}
		)
	return {
		"handoff_version": HANDOFF_VERSION,
		"requisition_id": root.name, "requisition_reference": root.requisition_reference, "requisition_version": version.name, "content_digest": version.content_digest,
		"fiscal_year": projection.get("fiscal_year"), "plan_id": root.plan_id, "plan_version_id": root.plan_version_id,
		"plan_item_id": root.plan_item_id, "plan_item_version_id": root.plan_item_version_id,
		"contributing_org_unit_ids": sorted(records.contributing_units(root)),
		"strategic_objective_id": root.strategic_objective_id, "strategic_objective_path": root.strategic_objective_path,
		"procurement_category": root.procurement_category, "plan_horizon": root.plan_horizon,
		"business_need": "; ".join(sorted({s.get("description", "") for s in projection.get("sources", []) if s.get("description")})),
		"expected_operational_result": "; ".join(sorted({s.get("expected_operational_result", "") for s in projection.get("sources", []) if s.get("expected_operational_result")})),
		"planned_method": projection.get("procurement_method"), "planned_dates": projection.get("planned_dates"),
		"plan_completion_boundary": projection.get("plan_completion_boundary"), "estimated_completion_date": projection.get("estimated_completion_date"),
		"currency": precision.CURRENCY, "money_scale": precision.MONEY_SCALE,
		"drawdown_lines": lines,
		"reservation_category": package.reservation_category, "county_resident_reservation": bool(package.county_resident_reservation),
		"reservation_rule_snapshot_ids": records.json_list(package.reservation_rule_snapshot_ids), "lotting_indicator": package.lotting_indicator,
		"requirement_title": version.requirement_title, "delivery_location": version.delivery_location,
		"delivery_address_snapshot": version.delivery_address_snapshot, "latest_delivery_date": cstr(version.latest_delivery_date),
		"items": _rows(package_version, "items", ("requisition_item_id", "drawdown_line_id", "plan_item_line_id", "equipment_category", "item_name", "quantity", "unit", "intended_use", "delivery_location", "latest_delivery_date")),
		"warranty_support": {f: package_version.get(f) for f in ("minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description")},
		"standard_profile": {"key": package_version.standard_profile_key, "version": package_version.standard_profile_version},
		"technical_requirements": _rows(package_version, "technical_requirements", ("technical_requirement_id", "applies_to_scope", "applies_to_id", "characteristic_key", "comparison", "required_value_json", "required_value_display", "unit", "other_value", "reason")),
		"related_services": _rows(package_version, "related_services", ("service_requirement_id", "service_type", "applies_to_scope", "applies_to_id", "required_result", "quantity_or_coverage", "completion_date", "acceptance_evidence", "other_evidence_name")),
		"acceptance_requirements": _rows(package_version, "acceptance_requirements", ("acceptance_requirement_id", "applies_to_scope", "applies_to_id", "check_type", "pass_condition", "evidence_type", "other_evidence_name")),
		"supporting_materials": _rows(package_version, "supporting_materials", ("supporting_material_id", "title", "document_type", "other_document_type", "purpose", "treatment", "file_digest", "linked_requirement_ids_json", "document_version")),
		"product_pattern": "IT Equipment",
		"compatibility": [c.as_dict() for c in checks],
		"departmental_certification": {
			"lead_org_unit_id": version.certified_lead_org_unit_id, "actor": version.submitted_by, "capacity": version.submitted_capacity,
			"decided_at": cstr(version.submitted_at), "decision": submit.name if submit else "",
		},
		"procurement_authorisation": {"actor": hopf_decision.actor, "capacity": hopf_decision.legal_capacity, "decided_at": cstr(hopf_decision.decided_at), "decision": hopf_decision.name},
		"generated_at": cstr(now_datetime()),
	}


def build_and_insert(*, root, version, package_version, projection, checks, reservations, hopf_decision):
	payload = build_payload(root=root, version=version, package_version=package_version, projection=projection, checks=checks, reservations=reservations, hopf_decision=hopf_decision)
	handoff_digest = digest.sha256_hex(payload)
	payload["handoff_digest"] = handoff_digest
	return envelope.insert(frappe.get_doc(
		{
			"doctype": "Authorised Requisition Handoff", "requisition": root.name, "requisition_version": version.name,
			"payload_json": digest.canonical_json(payload), "handoff_digest": handoff_digest, "handoff_version": HANDOFF_VERSION,
			"generated_at": now_datetime(),
		}
	))


def record_handoff_consumption(*, handoff: str, tender: str, tender_version: str, template_key: str, template_version: str, idempotency_key: str) -> dict[str, Any]:
	"""§9.2 `RecordHandoffConsumption` — one Tender, under the handoff lock
	revocation also takes. Same Tender replays; another Tender, or a handoff
	that is no longer the Requisition's current authorised one, is
	`REQ_HANDOFF_CONFLICT`. Consumption frees the item's open slot (§5.1) but
	releases no drawdown."""
	payload = {"handoff": handoff, "tender": tender, "tender_version": tender_version, "template_key": template_key, "template_version": template_version}
	actor = frappe.session.user  # an in-process owner call made inside Tenders' own start command
	replay = envelope.replay_or_none(idempotency_key, payload, command="RecordHandoffConsumption", actor=actor)
	if replay:
		return replay
	if not handoff or not frappe.db.exists("Authorised Requisition Handoff", handoff):
		raise frappe.DoesNotExistError("Handoff not found")
	# Lock order (AUD-XC-109): Requisition root, then its handoff — the order
	# `authorise_requisition` and `revoke_unconsumed_authorisation` take, so
	# consumption and revocation queue on the root instead of deadlocking. The
	# handoff's requisition never changes, so it is read before the locks.
	requisition = cstr(frappe.db.get_value("Authorised Requisition Handoff", handoff, "requisition"))
	root = envelope.locked("Procurement Requisition", requisition)
	doc = envelope.locked("Authorised Requisition Handoff", handoff)
	if doc.consumed_at:
		if doc.tender == cstr(tender):
			result = {"ok": True, "idempotent": True, "action": "already_consumed", "handoff": doc.name, "tender": doc.tender, "consumed_at": cstr(doc.consumed_at)}
			envelope.record_command(idempotency_key=idempotency_key, command="RecordHandoffConsumption", payload=payload, result=result, document_type="Authorised Requisition Handoff", document_name=doc.name, actor=actor)
			return result
		fail("REQ_HANDOFF_CONFLICT", detail={"tender": cstr(doc.tender)})
	if root.current_state != "Authorised" or root.handoff != doc.name:
		fail("REQ_HANDOFF_CONFLICT", detail={"state": root.current_state})

	doc.tender = cstr(tender)
	doc.tender_version = cstr(tender_version)
	doc.template_key = cstr(template_key)
	doc.template_version = cstr(template_version)
	doc.consumed_at = now_datetime()
	envelope.save(doc)
	root.handoff_consumed_at = doc.consumed_at
	records.release_slot(root)
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "consumed", "handoff": doc.name, "tender": doc.tender, "consumed_at": cstr(doc.consumed_at)}
	envelope.record_command(idempotency_key=idempotency_key, command="RecordHandoffConsumption", payload=payload, result=result, document_type="Authorised Requisition Handoff", document_name=doc.name, actor=actor)
	return result
