# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-TDS-001 — Tender Data Sheet service contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.services.wizard_tds_service import (
	FIELD_TOTAL,
	_ensure_tds_doc,
	compute_tds_completion,
	get_tds,
	save_tds,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import (
	SEED_001_TDS,
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


def _complete_tds_payload() -> dict:
	return {
		"procuring_entity_address": "National Treasury, P.O. Box 30007-00100, Nairobi",
		"tender_number": "NT/T/ICT/2024-009",
		"tender_name": "Supply and Commissioning of Data Center Hardware Refresh 2024",
		"alternative_tenders_allowed": "NO",
		"jv_max_members": 3,
		"local_sourcing_preference": "MARGIN_15",
		"submission_deadline_at": "2026-08-15 17:00:00",
		"opening_at": "2026-08-16 10:00:00",
		"clarification_contact_email": "procurement@treasury.go.ke",
		"electronic_tenders_allowed": 1,
		"tender_security_amount": 500000,
		"tender_validity_days": 120,
		"security_issuer_type": "COMMERCIAL_BANK",
	}


class TestWizardTdsService(IntegrationTestCase):
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

	def test_get_tds_returns_context_and_values(self) -> None:
		payload = get_tds(SEED_CODE)
		self.assertEqual(payload["configuration_id"], SEED_CODE)
		self.assertEqual(payload["title"], "Data Center Hardware Refresh")
		self.assertEqual(payload["planning_package"]["code"], "PP-ICT-2024-009")
		self.assertEqual(payload["procuring_entity"]["name"], "National Treasury")
		self.assertIn("values", payload)
		self.assertEqual(payload["values"]["envelope_marking"], "ELECTRONIC_ONLY")

	def test_seed_001_tds_is_partially_complete(self) -> None:
		instance_name = frappe.db.get_value(
			"Tender STD Instance",
			{"instance_code": SEED_CODE},
		)
		tds_name = frappe.db.get_value("Tender STD TDS", {"tender_std_instance": instance_name})
		if tds_name:
			doc = frappe.get_doc("Tender STD TDS", tds_name)
			doc.update(SEED_001_TDS)
			doc.submission_deadline_at = None
			doc.opening_at = None
			doc.clarification_contact_email = ""
			doc.tender_security_amount = 0
			doc.tender_validity_days = 0
			doc.security_issuer_type = ""
			doc.save(ignore_permissions=True)
		payload = get_tds(SEED_CODE)
		completion = payload["completion"]
		self.assertEqual(completion["total"], FIELD_TOTAL)
		self.assertGreaterEqual(completion["completed"], 8)
		self.assertLess(completion["completed"], FIELD_TOTAL)
		self.assertIn("Submission Deadline", completion["missing_fields"])

	def test_save_tds_persists_and_updates_step_status(self) -> None:
		payload = save_tds(SEED_CODE, _complete_tds_payload())
		self.assertEqual(payload["values"]["tender_number"], "NT/T/ICT/2024-009")
		self.assertEqual(payload["completion"]["completed"], FIELD_TOTAL)
		step_status = frappe.db.get_value(
			"Wizard Step Instance",
			{"tender_std_instance": SEED_CODE, "step_code": "TDS"},
			"status",
		)
		self.assertEqual(step_status, "COMPLETE")

	def test_seed_003_tds_is_complete(self) -> None:
		payload = get_tds(SEED_COMPLETE_CODE)
		self.assertEqual(payload["completion"]["completed"], FIELD_TOTAL)
		self.assertEqual(payload["completion"]["missing_fields"], [])

	def test_save_rejects_opening_before_submission(self) -> None:
		bad_payload = _complete_tds_payload()
		bad_payload["submission_deadline_at"] = "2026-08-20 17:00:00"
		bad_payload["opening_at"] = "2026-08-15 10:00:00"
		with self.assertRaises(frappe.ValidationError):
			save_tds(SEED_CODE, bad_payload)

	def test_compute_tds_completion_counts_missing_deadline(self) -> None:
		result = compute_tds_completion(
			{
				"procuring_entity_address": "Address",
				"tender_number": "REF-001",
				"tender_name": "Title",
				"alternative_tenders_allowed": "NO",
				"jv_max_members": 2,
				"local_sourcing_preference": "NONE",
				"submission_deadline_at": None,
				"opening_at": "2026-08-16 10:00:00",
				"clarification_contact_email": "",
				"electronic_tenders_allowed": 1,
				"envelope_marking": "ELECTRONIC_ONLY",
				"tender_security_amount": 1000,
				"tender_validity_days": 90,
				"security_issuer_type": "COMMERCIAL_BANK",
			}
		)
		self.assertIn("Submission Deadline", result["missing_fields"])

	def test_ensure_tds_doc_is_idempotent(self) -> None:
		tds_name = frappe.db.get_value("Tender STD TDS", {"tender_std_instance": SEED_CODE})
		if tds_name:
			frappe.delete_doc("Tender STD TDS", tds_name, force=True)
		first = _ensure_tds_doc(SEED_CODE)
		second = _ensure_tds_doc(SEED_CODE)
		self.assertEqual(first.name, second.name)
		self.assertEqual(
			frappe.db.count("Tender STD TDS", {"tender_std_instance": SEED_CODE}),
			1,
		)

	def test_get_tds_is_idempotent_when_doc_missing(self) -> None:
		tds_name = frappe.db.get_value("Tender STD TDS", {"tender_std_instance": SEED_CODE})
		if tds_name:
			frappe.delete_doc("Tender STD TDS", tds_name, force=True)
		first = get_tds(SEED_CODE)
		second = get_tds(SEED_CODE)
		self.assertEqual(first["configuration_id"], second["configuration_id"])
		self.assertEqual(
			frappe.db.count("Tender STD TDS", {"tender_std_instance": SEED_CODE}),
			1,
		)
