from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.services.boq_import_service import import_boq_structured
from kentender_procurement.std_engine.tests.test_std_boq_instance_service import TestSTDBOQInstanceService


class TestSTDBOQImportService(TestSTDBOQInstanceService, IntegrationTestCase):
	def test_dry_run_preview_and_ambiguous_rows_rejected(self):
		resp = import_boq_structured(
			instance_code=self.instance_code,
			file_reference="/files/boq-import.xlsx",
			mapping_config={
				"rows": [
					{"bill_number": "1", "bill_title": "Bill 1", "item_number": "1.1", "description": "Excavation", "unit": "m3", "quantity": 10, "rate": 50},
					{"bill_number": "1", "bill_title": "Bill 1", "item_number": "1.2", "description": "", "unit": "m3", "quantity": 7, "rate": 20},
				]
			},
			actor="Administrator",
			dry_run=True,
		)
		self.assertEqual(1, len(resp["preview_rows"]))
		self.assertEqual(1, len(resp["rejected_rows"]))

	def test_file_alone_does_not_satisfy_boq_readiness(self):
		resp = import_boq_structured(
			instance_code=self.instance_code,
			file_reference="/files/boq-only-file.xlsx",
			mapping_config={"rows": []},
			actor="Administrator",
			dry_run=False,
		)
		self.assertFalse(resp["validation"]["is_valid"])

	def test_structured_records_satisfy_boq_validation_when_complete(self):
		resp = import_boq_structured(
			instance_code=self.instance_code,
			file_reference="/files/boq-complete.xlsx",
			mapping_config={
				"rows": [
					{"bill_number": "1", "bill_title": "Bill 1", "item_number": "1.1", "description": "Excavation", "unit": "m3", "quantity": 10, "rate": 50},
					{"bill_number": "1", "bill_title": "Bill 1", "item_number": "1.2", "description": "Backfill", "unit": "m3", "quantity": 5, "rate": 30},
				]
			},
			actor="Administrator",
			dry_run=False,
		)
		self.assertTrue(resp["validation"]["is_valid"])
		self.assertEqual(2, resp["imported_rows"])

