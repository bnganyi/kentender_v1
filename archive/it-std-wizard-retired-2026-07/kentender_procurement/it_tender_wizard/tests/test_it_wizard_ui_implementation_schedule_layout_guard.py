# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""IT Wizard UI layout guard — Implementation Schedule screen."""

from __future__ import annotations

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	assert_verbatim_deploy,
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardUiImplementationScheduleLayoutGuard(UnitTestCase):
	"""Deployed it_wizard_implementation_schedule.html must match design verbatim."""

	def test_deployed_matches_design_verbatim(self) -> None:
		assert_verbatim_deploy(
			design_source_path("06 implementation-schedule"),
			deployed_asset_path("it_wizard_implementation_schedule.html"),
		)

	def test_preserves_key_regions(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_implementation_schedule.html"))
		self.assertIn("Implementation Schedule Definition", deployed)
		self.assertIn("Implementation Approach", deployed)
		self.assertIn("Schedule Guidance", deployed)
		self.assertIn("Phase Detail Configuration", deployed)
		self.assertIn("data-itw-sched-drawer-hidden", deployed)
		self.assertIn("data-itw-sched-actions", deployed)
		self.assertIn("data-itw-sched-source", deployed)
		self.assertIn("Reset to Template", deployed)
		self.assertIn("Override", deployed)
		self.assertIn('data-itw-field="duration_label"', deployed)
		self.assertIn('data-itw-sched-mode-host="phased"', deployed)
		self.assertIn('data-itw-sched-mode-host="single-turnkey"', deployed)
		self.assertIn('data-itw-turnkey-field="expected_delivery_duration"', deployed)
		self.assertIn('data-itw-turnkey-field="unified_acceptance_criteria"', deployed)
		self.assertIn('data-itw-turnkey-field-action="reset"', deployed)
		self.assertIn('data-itw-turnkey-field-key="expected_delivery_duration"', deployed)
		self.assertIn("Expected Delivery Duration", deployed)
		self.assertIn("Unified Acceptance Criteria", deployed)
		self.assertIn("Save Schedule", deployed)
		self.assertIn("Continue to System Inventory", deployed)

	def test_preserves_inline_script_or_config(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_implementation_schedule.html"))
		self.assertIn('<title>Implementation Schedule - Phase Detail View</title>', deployed)
		self.assertIn('id="tailwind-config"', deployed)
