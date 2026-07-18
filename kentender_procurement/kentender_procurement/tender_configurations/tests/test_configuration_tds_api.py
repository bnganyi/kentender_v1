# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-02 Tender Data Sheet GET/POST contract tests."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.profile import LOT_MULTIPLE, LOT_SINGLE
from kentender_procurement.tender_configurations.services.tds import (
	YES,
	get_configuration_tds,
	save_configuration_tds,
)


def _complete_tds_payload(**overrides):
	base = {
		"contact_officer": "Jane Doe",
		"contact_email": "procurement@example.go.ke",
		"clarification_submission_method": "E-Procurement Portal",
		"clarification_deadline": "2026-08-01T12:00",
		"pre_tender_meeting": "No",
		"tender_submission_deadline": "2026-08-15T17:00",
		"tender_opening_datetime": "2026-08-15T17:30",
		"bid_validity_period": "120",
		"bid_validity_unit": "days",
		"submission_channel": "E-Procurement Portal",
		"submission_language": "English",
		"tender_currency": "KES",
		"alternative_tenders_allowed": "No",
		"joint_ventures_allowed": "Yes",
		"eligible_tenderers": "Open to all eligible tenderers",
		"reserved_procurement": "No",
		"tender_security_required": "No",
		"margin_of_preference_applies": "No",
		"opening_method": "Electronic Opening",
		"opening_location": "KenTender portal",
		"opening_attendance_allowed": "Yes",
	}
	base.update(overrides)
	return base


class TestConfigurationTdsApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_get_tds_shape(self):
		out = get_configuration_tds(self.cfg_id)
		for key in (
			"configuration_id",
			"tds_groups",
			"tds_values",
			"can_continue",
			"has_progress",
			"blockers",
			"warnings",
			"context",
			"options",
			"guidance",
		):
			self.assertIn(key, out)
		self.assertEqual(len(out["tds_groups"]), 7)
		self.assertFalse(out["can_continue"])
		self.assertFalse(out["has_progress"])
		self.assertGreater(out["blocker_count"], 0)

	def test_has_progress_after_partial_save(self):
		out = save_configuration_tds(
			self.cfg_id, {"tds_values": {"contact_officer": "Jane"}}
		)
		self.assertTrue(out["has_progress"])
		self.assertFalse(out["can_continue"])

	def test_empty_cannot_continue(self):
		out = save_configuration_tds(self.cfg_id, {"tds_values": {}})
		self.assertFalse(out["can_continue"])
		self.assertGreater(out["blocker_count"], 0)

	def test_complete_can_continue(self):
		out = save_configuration_tds(self.cfg_id, {"tds_values": _complete_tds_payload()})
		self.assertTrue(out["can_continue"])
		self.assertEqual(out["blocker_count"], 0)
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		from kentender_procurement.tender_configurations.services.configuration_home import (
			_parse_steps_state,
		)

		state = _parse_steps_state(doc.steps_state)
		self.assertEqual((state.get("CFG-02") or {}).get("status_label"), "Complete")

	def test_clarification_deadline_required_when_method_set(self):
		payload = _complete_tds_payload(clarification_deadline="")
		out = save_configuration_tds(self.cfg_id, {"tds_values": payload})
		self.assertFalse(out["can_continue"])
		self.assertTrue(
			any(b["code"] == "clarification_deadline" for b in out["blockers"])
		)

	def test_security_conditionals(self):
		payload = _complete_tds_payload(
			tender_security_required="Yes",
			tender_security_type="",
			tender_security_amount="",
			tender_security_validity_period="",
		)
		out = save_configuration_tds(self.cfg_id, {"tds_values": payload})
		self.assertFalse(out["can_continue"])
		codes = {b["code"] for b in out["blockers"]}
		self.assertIn("tender_security_type", codes)
		self.assertIn("tender_security_amount", codes)

		payload2 = _complete_tds_payload(
			tender_security_required="Yes",
			tender_security_type="Tender Security",
			tender_security_amount="500000",
			tender_security_validity_period="90",
		)
		out2 = save_configuration_tds(self.cfg_id, {"tds_values": payload2})
		self.assertTrue(out2["can_continue"])

	def test_preference_and_reservation_conditionals(self):
		payload = _complete_tds_payload(
			reserved_procurement="Yes",
			reservation_category="",
			margin_of_preference_applies="Yes",
			preference_basis="",
			preference_evidence_required="",
		)
		out = save_configuration_tds(self.cfg_id, {"tds_values": payload})
		codes = {b["code"] for b in out["blockers"]}
		self.assertIn("reservation_category", codes)
		self.assertIn("preference_basis", codes)
		self.assertIn("preference_evidence_required", codes)

	def test_meeting_details_required_when_yes(self):
		payload = _complete_tds_payload(
			pre_tender_meeting="Yes",
			pre_tender_meeting_details="",
		)
		out = save_configuration_tds(self.cfg_id, {"tds_values": payload})
		self.assertTrue(any(b["code"] == "pre_tender_meeting_details" for b in out["blockers"]))

	def test_lots_allowed_read_only_from_profile(self):
		frappe.db.set_value("Tender Configuration", self.cfg_id, "lot_structure", LOT_SINGLE)
		out = save_configuration_tds(
			self.cfg_id,
			{"tds_values": _complete_tds_payload(lots_allowed="Yes")},
		)
		self.assertEqual(out["tds_values"]["lots_allowed"], "No")

		frappe.db.set_value("Tender Configuration", self.cfg_id, "lot_structure", LOT_MULTIPLE)
		out2 = get_configuration_tds(self.cfg_id)
		self.assertEqual(out2["tds_values"]["lots_allowed"], YES)

	def test_forbidden_keys_ignored(self):
		out = save_configuration_tds(
			self.cfg_id,
			{
				"tds_values": _complete_tds_payload(
					std_version_hash="secret-hash",
					binding_id="bind-1",
					tender_publication_date="2099-01-01",
				)
			},
		)
		self.assertTrue(out["can_continue"])
		blob = frappe.as_json(out).lower()
		self.assertNotIn("secret-hash", blob)
		self.assertNotIn("bind-1", blob)
		self.assertEqual(out["tds_values"]["tender_publication_date"], "—")

	def test_group_statuses_present(self):
		out = save_configuration_tds(
			self.cfg_id,
			{
				"tds_values": {
					"contact_officer": "Jane",
					"contact_email": "a@b.co",
				}
			},
		)
		keys = {g["group_key"] for g in out["tds_groups"]}
		self.assertEqual(
			keys,
			{
				"communication",
				"key_dates",
				"submission",
				"eligibility",
				"security",
				"preferences",
				"bid_opening",
			},
		)
		comm = next(g for g in out["tds_groups"] if g["group_key"] == "communication")
		self.assertIn(comm["status_label"], ("Needs attention", "In progress", "Not started"))
