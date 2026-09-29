# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan Phase 3 (BOP10-302…306): the renderer, the
operating-profile settings, opening availability in its stated order, the
Opening access support notification with retry, and the closed §8 error
contract. Plan D5, D7, D11, D16; owner decision OD-C."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_opening.services import availability, errors, notify, renderer, settings, simulation

SUPPORT = "bopt.support@example.test"


def package(**overrides) -> bytes:
	body = {
		"schema": "kt-bds-package/1",
		"tender": {"tender": "TEST", "tender_reference": "TND-TEST-BOP-001", "bid_definition_id": "DEF-TEST", "definition_version": 1, "definition_digest": "d"},
		"bid": {"bid_reference": "BID-TEST-BOP-001", "arrangement_type": "Single organisation", "tenderer_name": "Example Test Supplier Ltd", "members": []},
		"responses": [
			{"task": "company", "field_key": "legal_name", "value": "Example Test Supplier Ltd"},
			{"task": "company", "field_key": "security_form", "value": "Demand Bank Guarantee"},
			{"task": "company", "field_key": "issuer", "value": "Test Bank"},
			{"task": "company", "field_key": "guarantee_reference", "value": "TEST/TG/0001"},
			{"task": "company", "field_key": "instrument_amount", "value": "500.00"},
			{"task": "requirements", "field_key": "offered_make_model", "value": "Test model"},
		],
		"evidence": [{"field_key": "security_evidence", "files": [{"original_filename": "security.pdf", "file_digest": "abc", "size_bytes": 10, "media_type": "application/pdf", "content_base64": ""}]}],
		"price": {"currency": "KES", "complete": True, "subtotal": "10344.83", "tax": "1655.17", "total": "12000.00",
			"lines": [{"line": "1", "description": "Test item", "quantity": "1", "unit": "Each", "unit_price": "10344.83", "tax_amount": "1655.17", "amount_before_tax": "10344.83", "line_total": "12000.00"}]},
		"signatory": {"full_name": "Test Signatory", "job_title": "Director"},
		"confirmation": {"confirmed": True},
	}
	body.update(overrides)
	return json.dumps(body, sort_keys=True).encode()


class GatewayCase(IntegrationTestCase):
	def setUp(self):
		self.assertTrue(simulation.enabled(), "Phase 3 gateway tests run on a test environment (OD-C)")
		simulation.reset_controls()
		self.addCleanup(simulation.reset_controls)

	def conf(self, key, value):
		previous = frappe.local.conf.get(key)
		frappe.local.conf[key] = value
		self.addCleanup(lambda: frappe.local.conf.__setitem__(key, previous))


class TestRenderer(GatewayCase):
	def test_a_package_renders_deterministically_with_page_facts(self):
		first = renderer.render_package(package=package(), envelope_id="ENV-TEST-BOP-001", receipt_reference="RCPT-TEST-BOP-001", correlation_id="REN-1")
		again = renderer.render_package(package=package(), envelope_id="ENV-TEST-BOP-001", receipt_reference="RCPT-TEST-BOP-001", correlation_id="REN-2")
		self.assertEqual(first["outcome"], "Accepted/Verified")
		self.assertGreaterEqual(first["page_count"], 2)
		self.assertTrue(1 <= first["price_page"] <= first["page_count"])
		for field in ("page_count", "price_page", "render_digest", "page_digests", "facts"):
			self.assertEqual(first[field], again[field], field)
		self.assertEqual(len(first["page_digests"]), first["page_count"])
		self.assertEqual(first["change_pages"], [])  # BOP-CHG-001 v0.10 §5: no permitted modification for this product
		self.assertEqual(first["facts"], {
			"tenderer_name": "Example Test Supplier Ltd", "submitted_total": "12000.00", "currency": "KES",
			"security_given": {"form": "Demand Bank Guarantee", "issuer": "Test Bank", "reference": "TEST/TG/0001", "amount": "500.00", "currency": "KES"},
		})
		self.assertTrue(first["pdf"].startswith(b"%PDF"))

	def test_an_unreadable_package_is_rejected_not_guessed(self):
		for bad in (b"not json", json.dumps({"schema": "something-else"}).encode(), package(price={})):
			with self.subTest(bad=bad[:20]):
				out = renderer.render_package(package=bad, envelope_id="E", receipt_reference="R", correlation_id="REN-BAD")
				self.assertEqual(out["outcome"], "Rejected")
				self.assertNotIn("pdf", out)

	def test_the_test_controls_force_unreadable_and_indeterminate(self):
		for forced, outcome in (("Unreadable", "Rejected"), ("Indeterminate", "Indeterminate")):
			with self.subTest(forced=forced):
				simulation.set_controls(render_outcome=forced)
				out = renderer.render_package(package=package(), envelope_id="E", receipt_reference="R", correlation_id="REN-F")
				self.assertEqual((out["outcome"], out["correlation_id"]), (outcome, "REN-F"))
		simulation.set_controls(render_outcome="Render")
		self.assertEqual(renderer.render_package(package=package(), envelope_id="E", receipt_reference="R", correlation_id="REN-OK")["outcome"], "Accepted/Verified")


class TestSettingsAndAvailability(GatewayCase):
	def test_simulation_supplies_operating_profile_defaults(self):
		self.assertEqual(settings.get(), {"presence_lapse_seconds": 60, "public_join_lead_minutes": 5, "register_self_service": 1})

	def test_outside_a_test_environment_nothing_is_available(self):
		self.conf("kt_bds_simulation_environment", 0)
		self.assertIsNone(settings.get()["presence_lapse_seconds"])
		verdict = availability.get_opening_availability()
		self.assertEqual((verdict["available"], verdict["code"]), (False, "BOP_OPENING_PROFILE_UNAVAILABLE"))

	def test_the_order_is_profile_then_credential_then_service(self):
		self.assertEqual(availability.get_opening_availability(), {"available": True, "code": "", "message": "", "reason": ""})
		from kentender_procurement.bid_submission.services import simulation as bds_simulation

		bds_simulation.set_controls(custody_service_down=1)
		self.addCleanup(lambda: bds_simulation.set_controls(custody_service_down=0))
		self.assertEqual(availability.get_opening_availability()["code"], "BOP_CREDENTIAL_UNAVAILABLE")
		simulation.set_controls(opening_profile_down=1)
		verdict = availability.get_opening_availability()
		self.assertEqual((verdict["code"], verdict["message"]), ("BOP_OPENING_PROFILE_UNAVAILABLE", "Bid opening isn’t available yet."))

	def test_the_public_attendance_channel_can_be_down(self):
		self.assertTrue(availability.attendance_channel_available())
		simulation.set_controls(attendance_service_down=1)
		self.assertFalse(availability.attendance_channel_available())

	def test_the_production_switch_is_read_in_one_place(self):
		from pathlib import Path

		root = Path(frappe.get_app_path("kentender_procurement", "bid_opening"))
		readers = sorted(str(p.relative_to(root)) for p in root.rglob("*.py") if "production_bid_opening_enabled" in p.read_text(encoding="utf-8") and "tests" not in p.parts)
		self.assertEqual(readers, ["services/availability.py"])


class TestSupportNotification(GatewayCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.exists("User", SUPPORT):
			frappe.get_doc({"doctype": "User", "email": SUPPORT, "first_name": "Test", "last_name": "Support", "send_welcome_email": 0}).insert(ignore_permissions=True)
		self.addCleanup(self.cleanup)

	def cleanup(self):
		frappe.db.delete("Notification Log", {"for_user": SUPPORT})
		if frappe.db.exists("User", SUPPORT):
			frappe.delete_doc("User", SUPPORT, force=True, ignore_permissions=True)
		frappe.db.commit()

	def send(self):
		return notify.deliver(incident_id="INC-TEST-BOP-01", subject="Bid opening isn’t available yet", message="Opening service unavailable before Start.", users=[SUPPORT])

	def test_a_failed_notification_is_retried_for_the_same_incident_without_a_second_one(self):
		simulation.set_controls(notify_outcome="Fail")
		self.assertEqual(self.send(), {"delivered": False, "delivered_to": []})
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": SUPPORT}), 0)
		simulation.set_controls(notify_outcome="Deliver")
		self.assertEqual(self.send(), {"delivered": True, "delivered_to": [SUPPORT]})
		self.assertEqual(self.send(), {"delivered": True, "delivered_to": [SUPPORT]})
		self.assertEqual(frappe.db.count("Notification Log", {"for_user": SUPPORT}), 1)

	def test_no_holder_is_not_delivered(self):
		self.assertEqual(notify.deliver(incident_id="INC-TEST-BOP-02", subject="s", message="m", users=[]), {"delivered": False, "delivered_to": []})


class TestErrorContract(IntegrationTestCase):
	def test_the_contract_is_the_closed_section_8_set(self):
		self.assertEqual(len(errors.ERROR_CODES), 13)
		self.assertEqual(errors.message("BOP_DEADLINE_NOT_REACHED", deadline="12 Jun 2027, 11:00 EAT"), "Bids can be opened after submissions close at 12 Jun 2027, 11:00 EAT.")
		self.assertEqual(errors.message("BOP_MEMBER_ABSENT", name="Beatrice Kamau"), "Opening cannot start because Beatrice Kamau has not joined.")
		self.assertEqual(errors.message("BOP_MEMBER_ABSENT", name="Beatrice Kamau", started=True), "Opening is paused because Beatrice Kamau is not present.")
		self.assertEqual(errors.message("BOP_CREDENTIAL_UNAVAILABLE", started=True), "Opening is paused because secure access is unavailable.")
		with self.assertRaises(ValueError):
			errors.fail("BOP_SOMETHING_NEW")

	def test_proceedings_errors_map_to_bid_opening_copy(self):
		# BOP-CHG-001 v0.10 §7.1 "Product vocabulary".
		self.assertEqual(errors.from_prc("PRC_VERSION_CONFLICT"), ("BOP_VERSION_CONFLICT", "Someone updated this opening record. Refresh the page before continuing."))
		self.assertEqual(errors.from_prc("PRC_ALREADY_FINALIZED")[1], "This opening record is final. Add a correction if a fact needs to change.")
		self.assertEqual(errors.from_prc("PRC_TARGET_CHANGED")[1], "The opening record changed. Review the latest version before signing.")
