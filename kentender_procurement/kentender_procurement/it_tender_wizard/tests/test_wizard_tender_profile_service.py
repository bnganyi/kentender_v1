# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-PROFILE-001 — Tender profile service contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.services.wizard_tender_profile_service import (
	REQUIRED_FIELD_TOTAL,
	_ensure_profile_doc,
	compute_profile_completion,
	get_tender_profile,
	save_tender_profile,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import (
	SEED_001_PROFILE,
	seed_dashboard_sample_instances,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import force_reset_package_state_for_tests
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_readiness_service import sync_activation_flags
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending

SEED_CODE = "ITCFG-DASH-SEED-001"
SEED_COMPLETE_CODE = "ITCFG-DASH-SEED-003"


class TestWizardTenderProfileService(IntegrationTestCase):
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

	def test_get_profile_returns_context_and_empty_draft_values(self) -> None:
		payload = get_tender_profile(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(payload["title"], "Data Center Hardware Refresh")
		self.assertEqual(payload["planning_package"]["code"], "PP-ICT-2024-009")
		self.assertEqual(payload["procuring_entity"]["name"], "National Treasury")
		self.assertEqual(payload["method"]["name"], "Open Tender")
		self.assertIn("profile", payload)
		self.assertEqual(payload["profile"]["language_code"], "en")
		self.assertEqual(payload["profile"]["currency_code"], "KES")

	def test_seed_001_profile_is_partially_complete(self) -> None:
		profile_name = frappe.db.get_value("Tender STD Profile", {"tender_std_instance": SEED_CODE})
		if profile_name:
			frappe.db.set_value("Tender STD Profile", profile_name, SEED_001_PROFILE)
		payload = get_tender_profile(SEED_CODE)
		completion = payload["completion"]
		self.assertEqual(completion["total"], REQUIRED_FIELD_TOTAL)
		self.assertGreaterEqual(completion["completed"], 6)
		self.assertLess(completion["completed"], REQUIRED_FIELD_TOTAL)
		self.assertTrue(completion["missing_fields"])

	def test_save_profile_persists_and_updates_step_status(self) -> None:
		payload = save_tender_profile(
			SEED_CODE,
			{
				"tender_name": "Updated Data Center Refresh Title",
				"contract_description": "Updated scope summary for integration test.",
				"lotting_strategy": "SINGLE_LOT",
				"reservation_applies": 1,
				"reserved_group_code": "AGPO",
				"tender_security_applicability": "BANK_GUARANTEE",
				"clarification_contact_email": "procurement@treasury.go.ke",
				"alternative_tenders_allowed": 1,
				"jv_allowed": 1,
				"pre_tender_meeting_required": 0,
			},
		)
		self.assertEqual(payload["profile"]["tender_name"], "Updated Data Center Refresh Title")
		self.assertEqual(payload["completion"]["completed"], REQUIRED_FIELD_TOTAL)
		step_status = frappe.db.get_value(
			"Wizard Step Instance",
			{
				"tender_std_instance": SEED_CODE,
				"step_code": "TENDER_PROFILE",
			},
			"status",
		)
		self.assertEqual(step_status, "COMPLETE")

	def test_seed_003_profile_is_complete(self) -> None:
		payload = get_tender_profile(SEED_COMPLETE_CODE)
		self.assertEqual(payload["completion"]["completed"], REQUIRED_FIELD_TOTAL)
		self.assertEqual(payload["completion"]["missing_fields"], [])

	def test_compute_profile_completion_counts_missing_email(self) -> None:
		result = compute_profile_completion(
			{
				"tender_name": "Title",
				"contract_description": "Desc",
				"lotting_strategy": "SINGLE_LOT",
				"reservation_applies": 0,
				"reserved_group_code": "",
				"tender_security_applicability": "NONE",
				"clarification_contact_email": "not-an-email",
				"alternative_tenders_allowed": 0,
				"jv_allowed": 1,
				"pre_tender_meeting_required": 0,
				"language_code": "en",
				"currency_code": "KES",
			}
		)
		self.assertIn("Clarification Contact Email", result["missing_fields"])

	def test_ensure_profile_doc_is_idempotent(self) -> None:
		profile_name = frappe.db.get_value("Tender STD Profile", {"tender_std_instance": SEED_CODE})
		if profile_name:
			frappe.delete_doc("Tender STD Profile", profile_name, force=True)
		first = _ensure_profile_doc(SEED_CODE)
		second = _ensure_profile_doc(SEED_CODE)
		self.assertEqual(first.name, second.name)
		self.assertEqual(
			frappe.db.count("Tender STD Profile", {"tender_std_instance": SEED_CODE}),
			1,
		)

	def test_get_profile_is_idempotent_when_profile_missing(self) -> None:
		profile_name = frappe.db.get_value("Tender STD Profile", {"tender_std_instance": SEED_CODE})
		if profile_name:
			frappe.delete_doc("Tender STD Profile", profile_name, force=True)
		first = get_tender_profile(SEED_CODE)
		second = get_tender_profile(SEED_CODE)
		self.assertEqual(first["configuration_id"], second["configuration_id"])
		self.assertEqual(
			frappe.db.count("Tender STD Profile", {"tender_std_instance": SEED_CODE}),
			1,
		)
