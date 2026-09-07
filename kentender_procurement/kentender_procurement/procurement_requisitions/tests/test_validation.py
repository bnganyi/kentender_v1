# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §6.5 — the findings engine and step completion, pure and
DB-free. Proves the §16.3 Ministry of Health fixture text passes cleanly
(the load-bearing risk this module's own tracker/plan named up front)."""

from __future__ import annotations

import json
import unittest

from kentender_procurement.procurement_requisitions.services import validation

ELIGIBILITY = {
	"sources": [
		{"plan_source_allocation_id": "SRC-1", "remaining_quantity": 100, "remaining_amount": 20_000_000},
		{"plan_source_allocation_id": "SRC-2", "remaining_quantity": 150, "remaining_amount": 30_000_000},
	],
	"planned_dates": {"completion_date": "2027-09-30"},
}


def _fixture_version(**overrides):
	base = {
		"requirement_title": "Clinical training and deployment laptops for digital health rollout",
		"delivery_location": "LOC-1",
		"latest_delivery_date": "2027-09-30",
		"related_services_required": False,
		"drawdown_lines": [
			{"drawdown_line_id": "DL-1", "plan_item_line_id": "SRC-1", "requested_quantity": 100, "requested_value": 20_000_000},
			{"drawdown_line_id": "DL-2", "plan_item_line_id": "SRC-2", "requested_quantity": 150, "requested_value": 30_000_000},
		],
	}
	base.update(overrides)
	return base


def _fixture_package(**overrides):
	base = {
		"items": [
			{"requisition_item_id": "ITM-1", "plan_item_line_id": "DL-1", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "intended_use": "Clinical training for HRMD staff"},
			{"requisition_item_id": "ITM-2", "plan_item_line_id": "DL-2", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 150, "intended_use": "Field digital-health deployment for DHI staff"},
		],
		"technical_requirements": [
			{"technical_requirement_id": "TECH-001", "characteristic_key": "electrical_compatibility", "row_status": "Confirmed", "required_value_json": json.dumps({"value": "Yes"})},
			{"technical_requirement_id": "TECH-002", "characteristic_key": "new_unused_equipment", "row_status": "Confirmed", "required_value_json": json.dumps({"value": "Yes"})},
			{"technical_requirement_id": "TECH-003", "characteristic_key": "memory", "row_status": "Confirmed", "required_value_json": json.dumps({"value": 16})},
			{"technical_requirement_id": "TECH-004", "characteristic_key": "storage_capacity", "row_status": "Confirmed", "required_value_json": json.dumps({"value": 512})},
			{"technical_requirement_id": "TECH-005", "characteristic_key": "storage_type", "row_status": "Confirmed", "required_value_json": json.dumps({"value": "NVMe SSD"})},
			{"technical_requirement_id": "TECH-006", "characteristic_key": "display_size", "row_status": "Confirmed", "required_value_json": json.dumps({"value": 14.0})},
			{"technical_requirement_id": "TECH-007", "characteristic_key": "battery_runtime", "row_status": "Confirmed", "required_value_json": json.dumps({"value": 8})},
			{"technical_requirement_id": "TECH-008", "characteristic_key": "processor_requirement", "row_status": "Confirmed", "required_value_json": json.dumps({"value": "64-bit business-class processor, minimum 10 cores or equivalent benchmark"})},
			{"technical_requirement_id": "TECH-009", "characteristic_key": "operating_system_compatibility", "row_status": "Confirmed", "required_value_json": json.dumps({"value": "Approved organisational Windows environment"})},
			{"technical_requirement_id": "TECH-010", "characteristic_key": "network_connectivity", "row_status": "Confirmed", "required_value_json": json.dumps({"values": ["Wi-Fi 6", "Bluetooth 5 or later"]})},
			{"technical_requirement_id": "TECH-011", "characteristic_key": "required_ports", "row_status": "Confirmed", "required_value_json": json.dumps({"ports": [{"port_type": "USB-C", "minimum_count": 2}]})},
		],
		"related_services": [],
		"acceptance_requirements": [
			{"acceptance_requirement_id": "ACC-1", "pass_condition": "Delivered quantities equal the authorised schedule"},
			{"acceptance_requirement_id": "ACC-2", "pass_condition": "No visible damage and all listed accessories are present"},
			{"acceptance_requirement_id": "ACC-3", "pass_condition": "Every delivered unit complies with all mandatory technical rows"},
			{"acceptance_requirement_id": "ACC-4", "pass_condition": "Each device powers on and completes the agreed basic functional test"},
			{"acceptance_requirement_id": "ACC-5", "pass_condition": "Warranty and delivery documents are received and verified"},
		],
		"supporting_materials": [],
	}
	base.update(overrides)
	return base


class TestValidationFixture(unittest.TestCase):
	def test_the_moh_fixture_has_zero_blocking_findings(self):
		result = validation.validate(version=_fixture_version(), package=_fixture_package(), eligibility=ELIGIBILITY)
		self.assertEqual(result["blocking_count"], 0, result["findings"])
		self.assertTrue(result["steps"][5]["complete"])
		# §13.9's own Step 5 fixture reads "0 Blocking · 1 Warning" — the MoH
		# fixture's own delivery date exactly matches the Plan's completion
		# date, which is the one case this document calls out as worth a
		# visible nudge, never a blocker.
		self.assertEqual(result["warning_count"], 1, result["findings"])
		self.assertEqual(result["findings"][0]["code"], "DATE_MATCHES_PLAN_COMPLETION")

	def test_a_delivery_date_before_the_plan_boundary_carries_no_warning(self):
		result = validation.validate(version=_fixture_version(latest_delivery_date="2027-08-15"), package=_fixture_package(), eligibility=ELIGIBILITY)
		self.assertEqual(result["warning_count"], 0, result["findings"])

	def test_a_balance_exceeding_line_blocks_step_1(self):
		version = _fixture_version(drawdown_lines=[{"drawdown_line_id": "DL-1", "plan_item_line_id": "SRC-1", "requested_quantity": 1000, "requested_value": 20_000_000}])
		result = validation.validate(version=version, package=_fixture_package(), eligibility=ELIGIBILITY)
		codes = {f["code"] for f in result["findings"]}
		self.assertIn("BALANCE_CHANGED", codes)
		self.assertFalse(result["steps"][1]["complete"])

	def test_item_quantity_mismatch_blocks_step_2(self):
		package = _fixture_package()
		package["items"][0]["quantity"] = 5
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertIn("QUANTITY_MISMATCH", {f["code"] for f in result["findings"]})

	def test_unconfirmed_baseline_row_blocks_step_3(self):
		package = _fixture_package()
		package["technical_requirements"][0]["row_status"] = "Proposed"
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertIn("BASELINE_UNCONFIRMED", {f["code"] for f in result["findings"]})

	def test_restrictive_brand_without_equivalent_treatment_blocks(self):
		package = _fixture_package()
		package["technical_requirements"].append({
			"technical_requirement_id": "TECH-012", "characteristic_key": "processor_requirement",
			"row_status": "Confirmed", "required_value_json": json.dumps({"value": "Intel Core i7-1165G7"}),
		})
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertIn("RESTRICTIVE_TERM", {f["code"] for f in result["findings"]})

	def test_restrictive_brand_with_equivalent_and_reason_passes(self):
		package = _fixture_package()
		package["technical_requirements"].append({
			"technical_requirement_id": "TECH-012", "characteristic_key": "processor_requirement",
			"row_status": "Confirmed", "reason": "Matches the performance benchmark the workload requires.",
			"required_value_json": json.dumps({"value": "Intel Core i7-1165G7 or equivalent"}),
		})
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertNotIn("RESTRICTIVE_TERM", {f["code"] for f in result["findings"]})

	def test_subjective_acceptance_wording_blocks(self):
		package = _fixture_package()
		package["acceptance_requirements"] = [{"acceptance_requirement_id": "ACC-1", "pass_condition": "Satisfactory"}]
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertIn("SUBJECTIVE_ACCEPTANCE", {f["code"] for f in result["findings"]})

	def test_no_acceptance_rows_blocks(self):
		package = _fixture_package(acceptance_requirements=[])
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertIn("MISSING_ACCEPTANCE_ROW", {f["code"] for f in result["findings"]})

	def test_complex_service_blocks_when_related_services_required(self):
		package = _fixture_package(related_services=[
			{"service_requirement_id": "SVC-1", "service_type": "Other", "required_result": "Custom software development", "quantity_or_coverage": "1", "completion_date": "2027-09-30", "acceptance_evidence": "Test result"},
		])
		version = _fixture_version(related_services_required=True)
		result = validation.validate(version=version, package=package, eligibility=ELIGIBILITY)
		self.assertIn("SERVICE_COMPLEX", {f["code"] for f in result["findings"]})

	def test_unlinked_operative_supporting_material_blocks(self):
		package = _fixture_package(supporting_materials=[
			{"supporting_material_id": "MAT-1", "treatment": "Forms part of requirement", "linked_requirement_ids_json": json.dumps([])},
		])
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertIn("FILE_UNLINKED", {f["code"] for f in result["findings"]})

	def test_informational_supporting_material_never_blocks(self):
		package = _fixture_package(supporting_materials=[
			{"supporting_material_id": "MAT-1", "treatment": "Informational", "linked_requirement_ids_json": ""},
		])
		result = validation.validate(version=_fixture_version(), package=package, eligibility=ELIGIBILITY)
		self.assertNotIn("FILE_UNLINKED", {f["code"] for f in result["findings"]})
