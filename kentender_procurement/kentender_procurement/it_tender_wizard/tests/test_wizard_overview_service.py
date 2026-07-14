# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-OVERVIEW-001 — Configuration overview summary contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_overview_service import (
	CONFIGURABLE_OVERVIEW_STEP_CODES,
	OVERVIEW_STEP_CODES,
	build_configuration_overview,
	map_step_rail_status,
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
SYSTEM_STEP_CODES = {
	"VALIDATION_REPORT",
	"REVIEW_AND_APPROVAL",
	"RENDER_PREVIEW",
	"PUBLICATION_READINESS",
}


class TestWizardOverviewService(IntegrationTestCase):
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

	def test_overview_step_codes_exclude_identity_and_overview_meta(self) -> None:
		self.assertEqual(len(OVERVIEW_STEP_CODES), 13)
		self.assertNotIn("TENDER_IDENTITY", OVERVIEW_STEP_CODES)
		self.assertNotIn("STD_CONFIG_OVERVIEW", OVERVIEW_STEP_CODES)
		self.assertIn("TENDER_PROFILE", OVERVIEW_STEP_CODES)
		self.assertIn("PUBLICATION_READINESS", OVERVIEW_STEP_CODES)

	def test_map_step_rail_status_locked_for_system_steps(self) -> None:
		for code in SYSTEM_STEP_CODES:
			status = map_step_rail_status(
				{"step_code": code, "status": "INCOMPLETE"},
				all_prior_configurable_complete=False,
				is_current=False,
			)
			self.assertEqual(status, "LOCKED")

	def test_build_overview_for_seed_001(self) -> None:
		payload = build_configuration_overview(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(payload["title"], "Data Center Hardware Refresh")
		self.assertEqual(payload["state"], ws.IN_CONFIGURATION)
		self.assertEqual(payload["state_label"], ws.state_label(ws.IN_CONFIGURATION))
		self.assertEqual(payload["completion_percent"], 67)
		self.assertIn("wizard_steps", payload)
		self.assertEqual(len(payload["wizard_steps"]), 13)

		step_codes = [row["step_code"] for row in payload["wizard_steps"]]
		self.assertEqual(step_codes, list(OVERVIEW_STEP_CODES))

		current_steps = [row for row in payload["wizard_steps"] if row.get("is_current")]
		self.assertEqual(len(current_steps), 1)
		self.assertEqual(current_steps[0]["step_code"], "IT_REQUIREMENTS")
		self.assertEqual(current_steps[0]["rail_status"], "IN_PROGRESS")

		tds_step = next(row for row in payload["wizard_steps"] if row["step_code"] == "TDS")
		self.assertEqual(tds_step["rail_status"], "IN_PROGRESS")

		locked_steps = [row for row in payload["wizard_steps"] if row["rail_status"] == "LOCKED"]
		self.assertTrue(locked_steps)
		self.assertTrue(all(row["step_code"] in SYSTEM_STEP_CODES for row in locked_steps))

		self.assertEqual(payload["validation"]["warnings"], 2)
		self.assertEqual(payload["validation"]["blockers"], 0)
		self.assertEqual(payload["planning_package"]["code"], "PP-ICT-2024-009")
		self.assertEqual(payload["procuring_entity"]["name"], "National Treasury")
		self.assertEqual(payload["method"]["name"], "Open Tender")
		self.assertEqual(payload["next_required_action"]["step_code"], "IT_REQUIREMENTS")

	def test_build_overview_for_seed_003_header_matches_step_grid(self) -> None:
		payload = build_configuration_overview("ITCFG-DASH-SEED-003")
		self.assertEqual(payload["state_label"], ws.state_label(ws.READY_FOR_REVIEW))
		self.assertEqual(payload["completion_percent"], 100)
		self.assertTrue(
			all(
				row["rail_status"] in {"COMPLETE", "HAS_WARNINGS", "LOCKED"}
				for row in payload["wizard_steps"]
				if row["step_code"]
				not in {
					"VALIDATION_REPORT",
					"REVIEW_AND_APPROVAL",
					"RENDER_PREVIEW",
					"PUBLICATION_READINESS",
				}
			)
		)
		not_started = [
			row
			for row in payload["wizard_steps"]
			if row["rail_status"] == "NOT_STARTED"
			and row["step_code"] in CONFIGURABLE_OVERVIEW_STEP_CODES
		]
		self.assertEqual(not_started, [])
