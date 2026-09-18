# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §10.1 — the shared fixture pack as a synthetic
`AuthorisedRequisitionHandoff v1.3` payload plus the §10.1 officer values,
for tests that exercise the serializer, renders, review and documents
without building a live Requisition. Every literal here is the spec's own
(two Requisition items 100 + 150 → one 250-Each line; eleven technical
rows; six warranty/support values; five acceptance checks; no services, no
materials)."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.tenders.services import controls, envelope, snapshot as snap

TECHNICAL: tuple[tuple[str, str, str, dict[str, Any], str], ...] = (
	# (id, characteristic_key, comparison, value json, unit)
	("TECH-001", "electrical_compatibility", "Required", {"value": "Yes"}, ""),
	("TECH-002", "new_unused_equipment", "Required", {"value": "Yes"}, ""),
	("TECH-003", "memory", "Minimum", {"value": 16}, "GB"),
	("TECH-004", "storage_capacity", "Minimum", {"value": 512}, "GB"),
	("TECH-005", "storage_type", "One of", {"value": "NVMe SSD"}, ""),
	("TECH-006", "display_size", "Minimum", {"value": 14.0}, "inches"),
	("TECH-007", "battery_runtime", "Minimum", {"value": 8}, "hours"),
	("TECH-008", "processor_requirement", "Minimum", {"value": "64-bit business-class processor, minimum 10 cores or equivalent benchmark"}, ""),
	("TECH-009", "operating_system_compatibility", "Required", {"value": "Approved organisational Windows environment"}, ""),
	("TECH-010", "network_connectivity", "Required", {"values": ["Wi-Fi 6", "Bluetooth 5 or later"]}, ""),
	("TECH-011", "required_ports", "Required", {"ports": [{"port_type": "USB-C", "minimum_count": 2}, {"port_type": "USB-A", "minimum_count": 2}, {"port_type": "HDMI", "minimum_count": 1}]}, ""),
)
ACCEPTANCE: tuple[tuple[str, str, str, str], ...] = (
	("ACC-001", "Quantity", "Delivered quantities equal the authorised schedule", "Inspection record"),
	("ACC-002", "Physical condition", "No visible damage and all listed accessories are present", "Inspection record"),
	("ACC-003", "Required specification", "Every delivered unit complies with all mandatory technical rows", "Inspection record"),
	("ACC-004", "Functional test", "Each device powers on and completes the agreed basic functional test", "Test result"),
	("ACC-005", "Documents received", "Warranty and delivery documents are received and verified", "Certificate"),
)


def handoff_payload(*, delivery_location: str = "Ministry of Health Headquarters, Afya House, Nairobi") -> dict[str, Any]:
	return {
		"requisition_reference": "REQ-MOH-2027-033-001", "requisition_version": "RQV-SAMPLE", "content_digest": "c" * 64,
		"plan_id": "PLN-MOH-2027-001", "plan_version_id": "PLN-MOH-2027-001-V1", "plan_item_id": "PPI-MOH-2027-033", "fiscal_year": "2027-2028",
		"contributing_org_unit_ids": ["OU-SAMPLE-HRMD", "OU-SAMPLE-DH"],
		"strategic_objective": "SO-SAMPLE", "strategic_objective_path": "Strengthen interoperable national digital health services",
		"procurement_category": "Goods", "plan_horizon": "Single year", "multi_year_justification": None,
		"drawdown_lines": [
			{"drawdown_line_id": "DL-001", "source_line_id": "NDS-MOH-2027-0001", "plan_item_line_id": "PSA-MOH-2027-033-001", "contributing_org_unit": "OU-SAMPLE-HRMD", "requested_quantity": 100.0, "requested_value": 20000000.0, "unit": "Each", "reservation_id": "RES-SAMPLE-001", "planning_drawdown_reference": "PDR-SAMPLE-001"},
			{"drawdown_line_id": "DL-002", "source_line_id": "NDS-MOH-2027-0002", "plan_item_line_id": "PSA-MOH-2027-033-002", "contributing_org_unit": "OU-SAMPLE-DH", "requested_quantity": 150.0, "requested_value": 30000000.0, "unit": "Each", "reservation_id": "RES-SAMPLE-002", "planning_drawdown_reference": "PDR-SAMPLE-002"},
		],
		"business_need": "Laptop computers for clinical training and field digital-health deployment.",
		"expected_operational_result": "Endpoint equipment required to use the deployed digital health services.",
		"planned_method": "Open Tender",
		"planned_dates": {"invitation_date": "2027-05-15", "bid_opening_date": "2027-06-05"},
		"requirement_title": "Clinical training and deployment laptops for digital health rollout",
		"delivery_location": delivery_location, "latest_delivery_date": "2027-09-30",
		"items": [
			{"requisition_item_id": "SRC-MOH-033-001", "plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "unit": "Each", "intended_use": "Clinical training"},
			{"requisition_item_id": "SRC-MOH-033-002", "plan_item_line_id": "DL-002", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 150, "unit": "Each", "intended_use": "Field digital-health deployment"},
		],
		"minimum_warranty_months": 36, "onsite_support_required": True, "maximum_support_response_hours": 8, "manufacturer_support_required": True,
		"service_location_constraint": "Within Kenya", "support_description": "Supplier to provide escalation and warranty-contact details.",
		"technical_requirements": [
			{"technical_requirement_id": tid, "applies_to_scope": "All items", "applies_to_id": "", "characteristic_key": key, "comparison": comparison, "required_value_json": json.dumps(value), "unit": unit}
			for tid, key, comparison, value, unit in TECHNICAL
		],
		"related_services": [],
		"acceptance_requirements": [{"acceptance_requirement_id": aid, "applies_to_scope": "All items", "applies_to_id": None, "check_type": check, "pass_condition": condition, "evidence_type": evidence} for aid, check, condition, evidence in ACCEPTANCE],
		"supporting_materials": [],
		"product_pattern": "IT Equipment", "reservation_category_value": "Youth", "lotting_indicator": "Single lot",
		"handoff_version": "1.3", "generated_at": "2027-03-15 10:00:00",
		"decisions": [{"actor": "charles.mutiso@moh.example.test", "capacity": "Head of Procurement Function", "decision": "RQD-SAMPLE"}],
		"handoff_digest": "d" * 64,
	}


class _FakeHandoff:
	def __init__(self, payload: dict[str, Any]):
		self.name = "RQH-SAMPLE"
		self.payload_json = json.dumps(payload)
		self.handoff_digest = payload["handoff_digest"]


def sample_snapshot(**kwargs) -> tuple[dict[str, Any], str]:
	return snap.build(_FakeHandoff(handoff_payload(**kwargs)))


def officer_values(*, inspection_location: str, contact_office: str, meeting: str = "No") -> dict[str, Any]:
	"""§10.1 "Officer values" — the complete, valid set."""
	values = {
		"tender_title": "Supply and delivery of business laptops", "issue_date": "2027-05-15", "clarification_deadline": "2027-05-27 17:00:00",
		"submission_deadline": "2027-06-05 11:00:00", "tender_validity_days": 120, "tender_security_amount": 500000.00, "pre_tender_meeting": False,
		"manufacturer_authorisation_required": True, "datasheets_required": True, "past_experience_required": True, "minimum_comparable_contracts": 2,
		"experience_period_years": 5, "after_sales_evidence_required": True, "after_sales_evidence": "Kenya service-centre details and escalation contacts",
		"inspection_location": inspection_location, "payment_timing_days": "30", "performance_security_required": True, "performance_security_percent": 10,
		"delay_damages_per_week_percent": 0.5, "maximum_delay_damages_percent": 10, "contract_contact_office": contact_office,
	}
	if meeting == "Physical":
		values.update({"pre_tender_meeting": True, "meeting_datetime": "2027-05-22 10:00:00", "meeting_mode": "Physical", "meeting_venue": inspection_location})
	elif meeting == "Online":
		values.update({"pre_tender_meeting": True, "meeting_datetime": "2027-05-22 10:00:00", "meeting_mode": "Online", "online_joining_information": "Microsoft Teams — https://meet.example.test/tnd-moh-2027-033"})
	return values


def insert_tender_with_version(*, reference: str = "TND-MOH-2027-033", values: dict[str, Any] | None = None, fixture_namespace: str = "", evidence: list[dict[str, Any]] | None = None, status: str = "Draft") -> tuple[Any, Any]:
	"""A Tender + Version pair carrying the sample snapshot, for tests below
	the command layer. Commands (Phase 4) build these the real way."""
	snapshot, snapshot_digest = sample_snapshot()
	tender = envelope.insert(
		frappe.get_doc(
			{
				"doctype": "Tender", "tender_reference": reference, "requirement_title": snapshot["requirement_title"], "requisition_handoff": snapshot["handoff"],
				"requisition": "PRQ-SAMPLE", "requisition_reference": snapshot["requisition_reference"], "requisition_version": snapshot["requisition_version"],
				"plan_item_id": snapshot["plan_item_id"], "plan_item_version_id": snapshot["plan_version_id"], "product_key": "IT-EQUIPMENT-OPEN-V1",
				"lead_org_unit": None, "contributing_org_unit_ids": json.dumps(snapshot["contributing_org_unit_ids"]), "overall_status": "Draft",
				"record_version": 0, "fixture_namespace": fixture_namespace,
			}
		)
	)
	version = frappe.get_doc(
		{
			"doctype": "Tender Version", "tender": tender.name, "version_number": 1, "status": status, "requisition_handoff": snapshot["handoff"],
			"requisition_version": snapshot["requisition_version"], "template_release_id": "IT-EQUIPMENT-OPEN-V1-1.1", "official_source_digest": "o" * 64,
			"bundle_digest": "b" * 64, "requisition_snapshot_digest": snapshot_digest, "requisition_snapshot_json": json.dumps(snapshot, sort_keys=True),
			"officer_payload_json": json.dumps(controls.normalise(values or {}), sort_keys=True, default=str), "record_version": 0, "fixture_namespace": fixture_namespace,
		}
	)
	for index, row in enumerate(evidence or [], start=1):
		version.append("evidence_requirements", {"evidence_requirement_id": f"EV-{index:03d}", "row_order": index, **row})
	envelope.insert(version)
	envelope.bump(tender, current_version=version.name)
	return tender, version
