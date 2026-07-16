# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-08 — Price Schedule service contracts (Approach C owns qty/unit)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.services.wizard_price_schedule_service import (
	STEP_CODE,
	get_price_schedule,
	save_price_schedule,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import seed_dashboard_sample_instances
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import force_reset_package_state_for_tests
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_readiness_service import sync_activation_flags
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending

SEED_CODE = "ITCFG-DASH-SEED-001"


class TestWizardPriceScheduleService(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
		approve_all_pending(CANONICAL_PACKAGE_ID)
		sync_activation_flags(CANONICAL_PACKAGE_ID)
		activate_version(CANONICAL_PACKAGE_ID)
		seed_dashboard_sample_instances()
		frappe.set_user("Administrator")

	def test_get_returns_price_lines_with_configuration_context(self) -> None:
		payload = get_price_schedule(SEED_CODE)

		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(STEP_CODE, "PRICE_SCHEDULE")
		self.assertIn("planning_package", payload)
		self.assertEqual(set(payload["planning_package"]), {"code", "name"})
		self.assertTrue(payload["items"])
		for item in payload["items"]:
			self.assertEqual(item["line_id"], item["line_code"])
			self.assertNotIn("name", item)
			self.assertNotIn("parent", item)

	def test_save_roundtrip_persists_lines(self) -> None:
		payload = get_price_schedule(SEED_CODE)
		items = list(payload["items"])
		items[0]["title"] = "Updated Core Platform Supply"
		items[0]["quantity"] = 2
		items[0]["unit_of_measure"] = "SET"

		result = save_price_schedule(SEED_CODE, {"items": items, "schedule_title": "Price Schedule Updated"})

		self.assertEqual(result["schedule_title"], "Price Schedule Updated")
		updated = next(item for item in result["items"] if item["line_code"] == items[0]["line_code"])
		self.assertEqual(updated["title"], "Updated Core Platform Supply")
		self.assertEqual(updated["quantity"], 2)
		self.assertEqual(updated["unit_of_measure"], "SET")

		step_status = frappe.db.get_value(
			"Wizard Step Instance",
			{"tender_std_instance": SEED_CODE, "step_code": STEP_CODE},
			"status",
		)
		self.assertIn(step_status, {"IN_PROGRESS", "COMPLETE"})

	def test_approach_c_price_lines_own_quantity_fields(self) -> None:
		payload = get_price_schedule(SEED_CODE)
		self.assertTrue(payload["items"])
		for item in payload["items"]:
			self.assertIn("quantity", item)
			self.assertIn("unit_of_measure", item)
			self.assertIn("evaluated_price_included", item)
			self.assertIn("pricing_basis", item)
			self.assertIn(item["pricing_basis"], {"SUPPLY", "INSTALL", "RECURRENT", "OTHER"})
