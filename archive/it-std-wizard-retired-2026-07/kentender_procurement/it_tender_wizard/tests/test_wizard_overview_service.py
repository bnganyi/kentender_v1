# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-OVERVIEW-001 — Configuration home (Screen 02 v2) contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.services.wizard_home_service import (
	HOME_STEP_CATALOG,
	V2_HOME_STATUS_LABELS,
	build_configuration_home,
	map_rail_to_home_status,
)
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

	def test_home_step_catalog_has_thirteen_steps(self) -> None:
		self.assertEqual(len(HOME_STEP_CATALOG), 13)
		self.assertEqual(HOME_STEP_CATALOG[0]["step_label"], "Tender Profile")
		self.assertEqual(HOME_STEP_CATALOG[0]["step_number"], 1)
		self.assertEqual(HOME_STEP_CATALOG[-1]["step_label"], "Publication Readiness")

	def test_map_rail_to_home_status_v2_labels_only(self) -> None:
		self.assertEqual(map_rail_to_home_status("LOCKED"), "Available later")
		self.assertEqual(map_rail_to_home_status("HAS_BLOCKERS", blockers=1), "Needs attention")
		self.assertEqual(map_rail_to_home_status("IN_PROGRESS"), "In progress")
		self.assertEqual(map_rail_to_home_status("COMPLETE"), "Complete")
		self.assertEqual(map_rail_to_home_status("NOT_STARTED"), "Not started")
		for label in V2_HOME_STATUS_LABELS:
			self.assertNotIn(label.lower(), {"locked", "ready"})

	def test_map_step_rail_status_locked_for_system_steps(self) -> None:
		for code in SYSTEM_STEP_CODES:
			status = map_step_rail_status(
				{"step_code": code, "status": "INCOMPLETE"},
				all_prior_configurable_complete=False,
				is_current=False,
			)
			self.assertEqual(status, "LOCKED")

	def test_build_configuration_home_for_seed_001(self) -> None:
		payload = build_configuration_home(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(payload["tender_title"], "Data Center Hardware Refresh")
		self.assertEqual(payload["wizard_state_label"], ws.state_label(ws.IN_CONFIGURATION))
		self.assertIn("next_action", payload)
		self.assertIn("steps", payload)
		self.assertEqual(len(payload["steps"]), 13)
		self.assertNotIn("governance", payload)
		self.assertNotIn("wizard_steps", payload)

		step_labels = [row["step_label"] for row in payload["steps"]]
		self.assertEqual(step_labels[0], "Tender Profile")
		self.assertEqual(payload["steps"][0]["step_number"], 1)

		status_labels = {row["status_label"] for row in payload["steps"]}
		self.assertTrue(status_labels.issubset(V2_HOME_STATUS_LABELS))
		self.assertNotIn("Locked", status_labels)
		self.assertNotIn("Ready", status_labels)

		current_steps = [row for row in payload["steps"] if row.get("is_current")]
		self.assertEqual(len(current_steps), 1)
		self.assertEqual(current_steps[0]["step_label"], "IT Requirements")
		self.assertEqual(current_steps[0]["status_label"], "In progress")

		self.assertEqual(payload["next_action"]["label"], "Continue IT Requirements")
		self.assertEqual(payload["next_action"]["button_label"], "Continue")
		self.assertEqual(payload["planning_package_ref"], "PP-ICT-2024-009")
		self.assertEqual(payload["procuring_entity_name"], "National Treasury")
		self.assertEqual(payload["procurement_method_label"], "Open Tender")
		self.assertEqual(payload["warning_count"], 2)
		self.assertEqual(payload["blocker_count"], 0)

	def test_build_overview_legacy_shim_for_seed_001(self) -> None:
		payload = build_configuration_overview(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertIn("wizard_steps", payload)
		self.assertEqual(len(payload["wizard_steps"]), 13)
		self.assertIn("governance", payload)
		step_codes = [row["step_code"] for row in payload["wizard_steps"]]
		self.assertEqual(step_codes, list(OVERVIEW_STEP_CODES))

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
