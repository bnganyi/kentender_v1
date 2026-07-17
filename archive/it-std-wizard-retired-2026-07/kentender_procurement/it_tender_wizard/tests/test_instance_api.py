# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-DASH-002/004 — Instance API contracts."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.api.instance_api import (
	create_configuration_api,
	delete_draft_configuration_api,
	get_configuration_summary_api,
	get_create_configuration_context_api,
	get_tds_api,
	get_tender_profile_api,
	list_configurations_api,
	save_tds_api,
	save_tender_profile_api,
)
from kentender_procurement.it_tender_wizard.enums import wizard_states as ws
from kentender_procurement.it_tender_wizard.tests.create_options_test_helpers import (
	cleanup_created_packages,
	ensure_released_it_procurement_package,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import (
	ROLE_NAME,
	_ensure_implementation_schedule,
	_ensure_requirements,
	seed_dashboard_sample_instances,
)
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID
from kentender_procurement.std_engine.package_import.commit_importer import CommitImporter
from kentender_procurement.std_engine.package_import.draft_cleanup import force_reset_package_state_for_tests
from kentender_procurement.std_engine.paths import default_official_pdf_path, default_seed_zip_path_v1_1
from kentender_procurement.std_engine.services.activation_readiness_service import sync_activation_flags
from kentender_procurement.std_engine.services.activation_service import activate_version
from kentender_procurement.std_engine.services.legal_review_service import approve_all_pending


class TestInstanceApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		force_reset_package_state_for_tests(CANONICAL_PACKAGE_ID, family_code="KE-PPRA-IT")
		CommitImporter(default_seed_zip_path_v1_1(), default_official_pdf_path()).run()
		approve_all_pending(CANONICAL_PACKAGE_ID)
		sync_activation_flags(CANONICAL_PACKAGE_ID)
		activate_version(CANONICAL_PACKAGE_ID)
		if not frappe.db.exists("Role", ROLE_NAME):
			frappe.get_doc({"doctype": "Role", "role_name": ROLE_NAME}).insert(ignore_permissions=True)
		seed_dashboard_sample_instances()
		frappe.set_user("Administrator")

	@classmethod
	def tearDownClass(cls) -> None:
		cleanup_created_packages()
		super().tearDownClass()

	def test_get_create_configuration_context_api_returns_create_options(self) -> None:
		pkg = ensure_released_it_procurement_package(
			package_code="PP-ICT-WIZARD-API-001",
			package_name="API Create Modal Package",
		)
		payload = get_create_configuration_context_api()
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertIn("create_options", data)
		self.assertNotIn("shells", data)
		self.assertTrue(
			any(row["procurement_package_id"] == pkg["name"] for row in data["create_options"])
		)

	def test_create_options_context_does_not_corrupt_session_sid(self) -> None:
		"""Regression: create-options must not call frappe.set_user() in-request.

		frappe.set_user() rewrites frappe.session.sid to the username, which
		overwrites the response ``sid`` cookie and silently logs the real user
		out on their next request (create modal -> Guest / re-login). Guard that
		loading the create context leaves the live session id untouched.
		"""
		sentinel_sid = "sid-guard-live-session-token"
		original_sid = frappe.session.sid
		frappe.session.sid = sentinel_sid
		try:
			payload = get_create_configuration_context_api()
			self.assertTrue(payload["success"])
			self.assertEqual(
				frappe.session.sid,
				sentinel_sid,
				"create-options context must not mutate frappe.session.sid",
			)
		finally:
			frappe.session.sid = original_sid

	def test_list_filters_and_pagination(self) -> None:
		payload = list_configurations_api(state=ws.IN_CONFIGURATION, page=1, page_size=10)
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertGreaterEqual(data["total"], 1)
		self.assertTrue(any(item["code"] == "ITCFG-DASH-SEED-001" for item in data["items"]))

	def test_list_q_filter(self) -> None:
		payload = list_configurations_api(q="Data Center", page=1, page_size=25)
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["total"], 1)
		self.assertEqual(data["items"][0]["code"], "ITCFG-DASH-SEED-001")

	def test_list_entity_filter(self) -> None:
		payload = list_configurations_api(procurement_entity_id="PE-MIN-ICT", page=1, page_size=25)
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertGreaterEqual(data["total"], 1)
		self.assertTrue(any(item["code"] == "ITCFG-DASH-SEED-002" for item in data["items"]))

	def test_list_method_filter(self) -> None:
		payload = list_configurations_api(procurement_method_code="RFP", page=1, page_size=25)
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertGreaterEqual(data["total"], 1)
		self.assertTrue(any(item["code"] == "ITCFG-DASH-SEED-002" for item in data["items"]))

	def test_list_states_filter(self) -> None:
		payload = list_configurations_api(
			states=f"{ws.VALIDATION_FAILED},{ws.RETURNED_FOR_CORRECTION}",
			page=1,
			page_size=25,
		)
		self.assertTrue(payload["success"])
		data = payload["data"]
		codes = {item["code"] for item in data["items"]}
		self.assertIn("ITCFG-DASH-SEED-002", codes)
		self.assertIn("ITCFG-DASH-SEED-004", codes)
		self.assertNotIn("ITCFG-DASH-SEED-001", codes)

	def test_list_overdue_only_filter(self) -> None:
		payload = list_configurations_api(overdue_only=1, page=1, page_size=25)
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertGreaterEqual(data["total"], 1)
		self.assertTrue(any(item["code"] == "ITCFG-DASH-SEED-004" for item in data["items"]))

	def test_list_pagination_page_four(self) -> None:
		all_payload = list_configurations_api(page=1, page_size=100)
		total = all_payload["data"]["total"]
		if total < 31:
			self.skipTest("Need at least 31 configurations to validate page-4 window.")
		payload = list_configurations_api(page=4, page_size=10)
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["page"], 4)
		self.assertEqual(data["page_size"], 10)
		expected_count = min(10, max(0, total - 30))
		self.assertEqual(len(data["items"]), expected_count)

	def test_create_api_returns_envelope(self) -> None:
		payload = create_configuration_api(
			std_template_version_id=CANONICAL_PACKAGE_ID,
			title="API Created Config",
			procuring_entity_id="PE-API-001",
		)
		self.assertTrue(payload["success"])
		self.assertTrue(payload["data"]["summary"]["configuration_id"].startswith("ITCFG-"))
		self.assertIsNotNone(payload.get("audit_event_id"))

	def test_delete_draft_api(self) -> None:
		created = create_configuration_api(
			std_template_version_id=CANONICAL_PACKAGE_ID,
			title="API Delete Config",
		)
		code = created["data"]["summary"]["configuration_id"]
		deleted = delete_draft_configuration_api(code)
		self.assertTrue(deleted["success"])
		self.assertFalse(frappe.db.exists("Tender STD Instance", {"instance_code": code}))

	def test_permission_denied_for_guest(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			list_configurations_api()
		frappe.set_user("Administrator")

	def test_get_configuration_summary_api_returns_home_payload(self) -> None:
		payload = get_configuration_summary_api("ITCFG-DASH-SEED-001")
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["configuration_id"], "ITCFG-DASH-SEED-001")
		self.assertEqual(data["wizard_state_label"], "In configuration")
		self.assertIn("steps", data)
		self.assertEqual(len(data["steps"]), 13)
		self.assertIn("next_action", data)
		self.assertIn("validation", data)
		self.assertNotIn("governance", data)
		self.assertNotIn("wizard_steps", data)
		self.assertEqual(data["planning_package_ref"], "PP-ICT-2024-009")

	def test_get_configuration_summary_denied_for_guest(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_configuration_summary_api("ITCFG-DASH-SEED-001")
		frappe.set_user("Administrator")

	def test_get_tender_profile_api_returns_envelope(self) -> None:
		payload = get_tender_profile_api("ITCFG-DASH-SEED-001")
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["configuration_id"], "ITCFG-DASH-SEED-001")
		self.assertIn("profile", data)
		self.assertIn("completion", data)

	def test_save_tender_profile_api_persists(self) -> None:
		payload = save_tender_profile_api(
			"ITCFG-DASH-SEED-001",
			frappe.as_json(
				{
					"tender_name": "API Saved Profile Title",
					"contract_description": "Saved via API.",
					"lotting_strategy": "SINGLE_LOT",
					"reservation_applies": 0,
					"tender_security_applicability": "NONE",
					"clarification_contact_email": "api@treasury.go.ke",
					"alternative_tenders_allowed": 0,
					"jv_allowed": 1,
					"pre_tender_meeting_required": 1,
				}
			),
		)
		self.assertTrue(payload["success"])
		self.assertEqual(payload["data"]["profile"]["tender_name"], "API Saved Profile Title")

	def test_get_tender_profile_denied_for_guest(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_tender_profile_api("ITCFG-DASH-SEED-001")
		frappe.set_user("Administrator")

	def test_get_tds_api_returns_envelope(self) -> None:
		payload = get_tds_api("ITCFG-DASH-SEED-001")
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["configuration_id"], "ITCFG-DASH-SEED-001")
		self.assertIn("values", data)
		self.assertIn("completion", data)

	def test_save_tds_api_persists(self) -> None:
		payload = save_tds_api(
			"ITCFG-DASH-SEED-001",
			frappe.as_json(
				{
					"procuring_entity_address": "National Treasury, P.O. Box 30007-00100, Nairobi",
					"tender_number": "API-TDS-REF-001",
					"tender_name": "API Saved TDS Title",
					"alternative_tenders_allowed": "NO",
					"jv_max_members": 3,
					"local_sourcing_preference": "MARGIN_15",
					"submission_deadline_at": "2026-08-15 17:00:00",
					"opening_at": "2026-08-16 10:00:00",
					"clarification_contact_email": "api@treasury.go.ke",
					"electronic_tenders_allowed": 1,
					"tender_security_amount": 500000,
					"tender_validity_days": 120,
					"security_issuer_type": "COMMERCIAL_BANK",
				}
			),
		)
		self.assertTrue(payload["success"])
		self.assertEqual(payload["data"]["values"]["tender_number"], "API-TDS-REF-001")

	def test_get_tds_denied_for_guest(self) -> None:
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_tds_api("ITCFG-DASH-SEED-001")
		frappe.set_user("Administrator")

	def test_get_it_requirements_api_returns_envelope(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import get_it_requirements_api

		payload = get_it_requirements_api("ITCFG-DASH-SEED-001")
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["configuration_id"], "ITCFG-DASH-SEED-001")
		self.assertIn("sections", data)
		self.assertIn("completion", data)

	def test_save_it_requirements_api_persists(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import (
			get_it_requirements_api,
			save_it_requirements_api,
		)

		_ensure_requirements("ITCFG-DASH-SEED-001", {"instance_code": "ITCFG-DASH-SEED-001"})
		payload = save_it_requirements_api(
			"ITCFG-DASH-SEED-001",
			frappe.as_json(
				{
					"selected_item_id": "3.2",
					"selected_item": {
						"requirement_code": "3.2",
						"description": "API saved requirements description for storage capacity.",
						"evaluation_binding": "technical_solution_proposal",
					},
				}
			),
		)
		self.assertTrue(payload["success"])
		saved = next(
			row
			for section in payload["data"]["sections"]
			for row in section["items"]
			if row["requirement_code"] == "3.2"
		)
		self.assertIn("API saved requirements description", saved["description"])

	def test_get_it_requirements_denied_for_guest(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import get_it_requirements_api

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_it_requirements_api("ITCFG-DASH-SEED-001")
		frappe.set_user("Administrator")

	def test_get_implementation_schedule_api_returns_envelope(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import get_implementation_schedule_api

		payload = get_implementation_schedule_api("ITCFG-DASH-SEED-001")
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertEqual(data["configuration_id"], "ITCFG-DASH-SEED-001")
		self.assertIn("phases", data)
		self.assertIn("completion", data)
		self.assertTrue(any(phase.get("milestones") for phase in data["phases"]))

	def test_save_implementation_schedule_api_persists(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import (
			get_implementation_schedule_api,
			save_implementation_schedule_api,
		)

		_ensure_implementation_schedule("ITCFG-DASH-SEED-001", {"instance_code": "ITCFG-DASH-SEED-001"})
		payload = save_implementation_schedule_api(
			"ITCFG-DASH-SEED-001",
			frappe.as_json(
				{
					"selected_phase_id": "PHASE_3",
					"selected_phase": {
						"phase_code": "PHASE_3",
						"key_deliverable_summary": "API saved operational acceptance deliverables.",
						"description": "API saved phase 3 description.",
					},
				}
			),
		)
		self.assertTrue(payload["success"])
		saved = next(row for row in payload["data"]["phases"] if row["phase_code"] == "PHASE_3")
		self.assertIn("API saved operational acceptance", saved["key_deliverable_summary"])

	def test_get_implementation_schedule_denied_for_guest(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import get_implementation_schedule_api

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_implementation_schedule_api("ITCFG-DASH-SEED-001")
		frappe.set_user("Administrator")

	def test_get_system_inventory_api_returns_grouped_envelope(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import get_system_inventory_api

		payload = get_system_inventory_api("ITCFG-DASH-SEED-001")
		self.assertTrue(payload["success"])
		self.assertEqual(payload["data"]["configuration_id"], "ITCFG-DASH-SEED-001")
		self.assertEqual(len(payload["data"]["categories"]), 8)

	def test_save_system_inventory_api_upserts_selected_item(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import save_system_inventory_api

		payload = save_system_inventory_api(
			"ITCFG-DASH-SEED-001",
			frappe.as_json(
				{
					"selected_item_id": "SYS-CORE-ERP",
					"selected_item": {
						"item_code": "SYS-CORE-ERP",
						"bidder_consideration": "API-updated technical disclosure guidance.",
					},
				}
			),
		)
		self.assertTrue(payload["success"])
		item = next(
			item
			for category in payload["data"]["categories"]
			for item in category["items"]
			if item["item_code"] == "SYS-CORE-ERP"
		)
		self.assertEqual(item["bidder_consideration"], "API-updated technical disclosure guidance.")

	def test_get_system_inventory_denied_for_guest(self) -> None:
		from kentender_procurement.it_tender_wizard.api.instance_api import get_system_inventory_api

		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			get_system_inventory_api("ITCFG-DASH-SEED-001")
		frappe.set_user("Administrator")
