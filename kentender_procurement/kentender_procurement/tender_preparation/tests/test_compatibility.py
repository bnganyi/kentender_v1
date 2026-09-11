# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.4 — the compatibility test as pure rows (§18 layer 1)."""

from __future__ import annotations

import json

from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_preparation.services import compatibility
from kentender_procurement.tender_templates import loader


def _payload() -> dict:
	fixture = json.loads(loader.read_text("fixtures/moh_input.json"))
	return {
		"handoff_version": "1.3", "product_pattern": "IT Equipment", "procurement_category": "Goods", "planned_method": "Open Tender",
		"lotting_indicator": "Single lot", "reservation_category_value": "None", "latest_delivery_date": "2027-09-30",
		"items": [{"requisition_item_id": "RQI-001", "equipment_category": "Laptop", "quantity": 250}],
		"technical_requirements": [{"technical_requirement_id": "TECH-003", "comparison": "Minimum", "required_value_json": "{\"value\": 16}"}],
		"related_services": [], "supporting_materials": [], "drawdown_lines": [{"requested_value": 50000000}],
		"_fixture_title": fixture["tender"]["title"],
	}


class TestCompatibility(IntegrationTestCase):
	def test_the_fixture_shaped_payload_passes_every_row(self):
		rows = compatibility.evaluate(_payload(), handoff_version="1.3")
		self.assertEqual([r.test for r in rows if not r.ok], [])
		self.assertEqual(len(rows), 13)

	def test_each_named_failure_is_reported_by_its_own_row(self):
		cases = {
			"Handoff version": ({}, "1.2"),
			"Product pattern": ({"product_pattern": "Complex IT"}, "1.3"),
			"Procurement category": ({"procurement_category": "Works"}, "1.3"),
			"Method": ({"planned_method": "Restricted Tender"}, "1.3"),
			"Currency": ({"currency": "USD"}, "1.3"),
			"Award package": ({"award_packages": 2}, "1.3"),
			"Lotting indicator": ({"lotting_indicator": "Packaged into lots"}, "1.3"),
			"Reservation category": ({"reservation_category_value": "Regional — county"}, "1.3"),
			"Equipment": ({"items": []}, "1.3"),
			"Technical response": ({"technical_requirements": [{"technical_requirement_id": "T", "comparison": "Roughly", "required_value_json": "{}"}]}, "1.3"),
			"Complex work": ({"related_services": [{"service_type": "Data migration", "required_result": "Migrate the ERP"}]}, "1.3"),
			"Dates and value": ({"latest_delivery_date": ""}, "1.3"),
			"Supporting materials": ({"supporting_materials": [{"supporting_material_id": "MAT-001", "treatment": ""}]}, "1.3"),
		}
		for test, (patch, version) in cases.items():
			rows = compatibility.evaluate({**_payload(), **patch}, handoff_version=version)
			failure = compatibility.first_failure(rows)
			self.assertIsNotNone(failure, test)
			self.assertEqual(failure.test, test)

	def test_every_supported_reservation_category_passes(self):
		for category in compatibility.supported_reservation_categories():
			rows = compatibility.evaluate({**_payload(), "reservation_category_value": category}, handoff_version="1.3")
			self.assertIsNone(compatibility.first_failure(rows), category)
