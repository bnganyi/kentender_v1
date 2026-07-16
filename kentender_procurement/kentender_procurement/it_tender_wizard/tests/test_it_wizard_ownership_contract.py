# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-OWN-GATE — Screen Ownership Matrix contract tests."""

from __future__ import annotations

from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.it_tender_wizard.tests.it_wizard_ownership_contract import (
	FIELD_SOURCE_TYPES,
	assert_cross_screen_ownership_html,
	assert_inventory_ownership_html,
	assert_requirements_ownership_html,
	iter_screen_html_paths,
)
from kentender_procurement.it_tender_wizard.tests.it_wizard_ui_layout_guard_util import (
	deployed_asset_path,
	design_source_path,
	read_text,
)


class TestItWizardOwnershipContract(UnitTestCase):
	def test_field_source_types_cover_matrix_taxonomy(self) -> None:
		self.assertEqual(
			set(FIELD_SOURCE_TYPES),
			{
				"USER_ENTERED",
				"TEMPLATE_PREFILLED",
				"DERIVED",
				"OWNED_ELSEWHERE",
				"STD_LOCKED",
				"NOT_CONFIGURED",
			},
		)

	def test_system_inventory_design_and_deploy_forbid_magical_summaries(self) -> None:
		design = read_text(design_source_path("07 system-inventory"))
		deployed = read_text(deployed_asset_path("it_wizard_system_inventory.html"))
		assert_inventory_ownership_html(design, context="design inventory")
		assert_inventory_ownership_html(deployed, context="deployed inventory")

	def test_it_requirements_forbids_scored_evidence_set_labels(self) -> None:
		design = read_text(design_source_path("05 it-requirements"))
		deployed = read_text(deployed_asset_path("it_wizard_it_requirements.html"))
		assert_requirements_ownership_html(design, context="design requirements")
		assert_requirements_ownership_html(deployed, context="deployed requirements")

	def test_ownership_tracker_and_plan_exist(self) -> None:
		root = Path(__file__).resolve().parents[4] / "docs" / "std-prod-impl" / "IT-STD-Wizard"
		self.assertTrue((root / "98 IT_Tender_Wizard_Screen_Ownership_Correction_Plan.md").exists())
		self.assertTrue((root / "Screen_Ownership_Implementation_Tracker.md").exists())
		self.assertTrue((root / "99 IT_Tender_Wizard_Screen_Ownership_Matrix.md").exists())
		tracker = (root / "Screen_Ownership_Implementation_Tracker.md").read_text(encoding="utf-8")
		self.assertIn("ITW-OWN-GATE-02", tracker)
		self.assertIn("it-wizard-ownership-gate", tracker)
		self.assertIn("Blocks ITW-08 wiring", tracker)

	def test_all_screens_forbid_cross_screen_magical_fixtures(self) -> None:
		root = Path(__file__).resolve().parents[4]
		for design_dir, design_path, deploy_path in iter_screen_html_paths(root):
			design = design_path.read_text(encoding="utf-8")
			deployed = deploy_path.read_text(encoding="utf-8")
			self.assertEqual(
				design,
				deployed,
				f"{design_dir}: design and deployed HTML must stay byte-identical",
			)
			assert_cross_screen_ownership_html(design, context=f"design {design_dir}")
			assert_cross_screen_ownership_html(deployed, context=f"deployed {design_dir}")

	def test_profile_static_tds_owned_elsewhere_chrome(self) -> None:
		deployed = read_text(deployed_asset_path("it_wizard_tender_profile.html"))
		self.assertIn('data-itw-owned-elsewhere="1"', deployed)
		self.assertIn("Source: Tender Data Sheet", deployed)
		self.assertIn("Edit in Tender Data Sheet", deployed)
		self.assertIn('data-itw-field="tender_security_applicability"', deployed)
		self.assertIn('data-itw-field="clarification_contact_email"', deployed)

	def test_engine_implements_ownership_behaviors(self) -> None:
		engine = (
			Path(__file__).resolve().parents[2]
			/ "public"
			/ "js"
			/ "it_wizard_engine.js"
		).read_text(encoding="utf-8")
		self.assertIn("hydrate_system_inventory_summaries", engine)
		self.assertIn("mark_profile_field_owned_elsewhere", engine)
		self.assertIn("handle_it_turnkey_field_action", engine)
		self.assertIn("TURNKEY_TEMPLATE_DEFAULTS", engine)
		self.assertIn("Edit in Tender Data Sheet", engine)
		self.assertIn("requirements_treatment_display_label", engine)
		self.assertIn('data-itw-inv-security-value="bidder_consideration"', engine)
		self.assertIn("it-wizard-hydration-error", engine)
		self.assertNotIn('values.envelope_marking || "ELECTRONIC_ONLY"', engine)
		self.assertNotIn("Scored (15%)", engine)
		self.assertNotIn("Evidence Set", engine)
		self.assertNotIn("Acceptance Set", engine)
		self.assertNotIn("access_logic", engine)

	def test_pack_docs_cite_matrix_override(self) -> None:
		root = Path(__file__).resolve().parents[4] / "docs" / "std-prod-impl" / "IT-STD-Wizard"
		prd = (root / "01 IT_Tender_Configuration_Wizard_PRD.md").read_text(encoding="utf-8")
		domain = (root / "02 IT_Tender_Configuration_Wizard_Domain_Model.md").read_text(encoding="utf-8")
		api = (root / "05 IT_Tender_Configuration_Wizard_API_UI_Service_Contract.md").read_text(encoding="utf-8")
		gov = (
			root / "03 IT_Tender_Configuration_Wizard_Governance_Roles_Permissions_State_Model.md"
		).read_text(encoding="utf-8")
		sprint = (
			root / "07 IT_Tender_Configuration_Wizard_Sprint_Backlog_and_Task_Breakdown.md"
		).read_text(encoding="utf-8")
		self.assertIn("Ownership Matrix override", prd)
		self.assertIn("Ownership Matrix override", domain)
		self.assertIn("Ownership Matrix override", api)
		self.assertIn("Ownership Matrix override", gov)
		self.assertIn("Matrix override (ITW-OWN-DOC-05)", sprint)
