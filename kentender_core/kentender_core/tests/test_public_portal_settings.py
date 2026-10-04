# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.16 §4.9A / §7 / §12 / CFG16-AC-002…006, 012 — the one
Supplier portal settings record, built ahead of CFG v0.16 approval under
BDS-CHG-001 v0.8 owner decision OD-A (26 Sep 2026).

`bench run-tests` has no rollback on this bench, so every test snapshots the
live Single and restores it on cleanup.
"""

from __future__ import annotations

import uuid

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import public_portal as portal
from kentender_core.services.configuration_errors import ConfigurationError

COMPLETE = {
	"supplier_support_email": "tendersupport@health.go.ke",
	"supplier_support_phone": "+254 20 271 7077",
	"supplier_support_hours": "Monday–Friday, 08:00–17:00 EAT",
	"privacy_notice_url": "https://health.example.test/kentender/privacy",
	"portal_terms_url": "https://health.example.test/kentender/terms",
	"accessibility_statement_url": "https://health.example.test/kentender/accessibility",
}
EDITABLE = tuple(COMPLETE)
PLAIN_USER = "pw.cfg.portal.plain@example.test"


def _key() -> str:
	return f"test-portal-{uuid.uuid4().hex}"


def purge_test_residue() -> None:
	"""Remove what these tests leave behind: their idempotency journal rows
	and the audit events of their saves (no rollback on this bench)."""
	frappe.db.delete("Reference Data Command Journal", {"idempotency_key": ("like", "test-portal-%")})
	frappe.db.delete("Audit Event", {"action": "update_public_portal_settings", "document_type": portal.SETTINGS, "performed_by": "Administrator", "creation": (">=", frappe.flags.kt_portal_test_started)})
	frappe.db.commit()


class TestPublicPortalSettings(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.flags.kt_portal_test_started = frappe.utils.now_datetime()
		cls.addClassCleanup(purge_test_residue)

	def setUp(self):
		frappe.set_user("Administrator")
		snapshot = {f: frappe.db.get_single_value(portal.SETTINGS, f) for f in (*EDITABLE, "record_version", "updated_by", "updated_at")}
		self.addCleanup(self._restore, snapshot)

	def _restore(self, snapshot):
		frappe.set_user("Administrator")
		for field, value in snapshot.items():
			frappe.db.set_single_value(portal.SETTINGS, field, value)
		frappe.db.commit()

	def _save(self, values=None, *, key=None):
		current = portal.get_public_portal_settings()["record_version"]
		return portal.update_public_portal_settings(**(values or COMPLETE), expected_version=current, idempotency_key=key or _key())

	# CFG16-AC-002 — setup authority only.
	def test_only_administrator_or_system_manager_may_read_or_update(self):
		if not frappe.db.exists("User", PLAIN_USER):
			frappe.get_doc({"doctype": "User", "email": PLAIN_USER, "first_name": "Portal plain", "send_welcome_email": 0}).insert(ignore_permissions=True)
			self.addCleanup(lambda: frappe.delete_doc("User", PLAIN_USER, force=True, ignore_permissions=True))
		frappe.set_user(PLAIN_USER)
		with self.assertRaises(ConfigurationError) as caught:
			portal.update_public_portal_settings(**COMPLETE, expected_version=0, idempotency_key=_key())
		self.assertEqual(caught.exception.code, "CFG_AUTHORITY_REQUIRED")
		with self.assertRaises(ConfigurationError):
			portal.get_public_portal_settings()

	# CFG16-AC-003/004 — required fields and HTTPS destinations; no partial update.
	def test_invalid_input_names_each_field_and_saves_nothing(self):
		self._save()
		before = portal.get_public_portal_settings()
		bad = dict(COMPLETE, supplier_support_email="", privacy_notice_url="", portal_terms_url="http://example.test/terms",
			accessibility_statement_url="https://user:secret@health.example.test/a11y")
		result = portal.update_public_portal_settings(**bad, expected_version=before["record_version"], idempotency_key=_key())
		self.assertFalse(result["ok"])
		self.assertEqual(result["errors"], {
			"supplier_support_email": "Enter the email suppliers should use for support.",
			"privacy_notice_url": "Enter a complete HTTPS address for Privacy and data use.",
			"portal_terms_url": "Enter a complete HTTPS address for Terms of portal use.",
			"accessibility_statement_url": "Enter a complete HTTPS address for Accessibility.",
		})
		after = portal.get_public_portal_settings()
		self.assertEqual(after["record_version"], before["record_version"])
		self.assertEqual(after["values"], before["values"])

	def test_support_hours_are_bounded_and_the_phone_is_a_phone(self):
		result = self._save(dict(COMPLETE, supplier_support_hours="x" * 161, supplier_support_phone="call us"))
		self.assertFalse(result["ok"])
		self.assertEqual(set(result["errors"]), {"supplier_support_hours", "supplier_support_phone"})

	# CFG16-AC-005 — one atomic save, version advance, before/after audit, exact replay.
	def test_a_save_advances_the_version_audits_before_and_after_and_replays_exactly(self):
		self._save(dict(COMPLETE, supplier_support_hours=""))
		start = portal.get_public_portal_settings()["record_version"]
		key = _key()
		audits_before = frappe.db.count("Audit Event", {"action": "update_public_portal_settings"})
		first = portal.update_public_portal_settings(**COMPLETE, expected_version=start, idempotency_key=key)
		self.assertTrue(first["ok"])
		self.assertEqual(first["record_version"], start + 1)
		replay = portal.update_public_portal_settings(**COMPLETE, expected_version=start, idempotency_key=key)
		self.assertEqual(replay, first)
		self.assertEqual(frappe.db.count("Audit Event", {"action": "update_public_portal_settings"}), audits_before + 1)
		event = frappe.get_last_doc("Audit Event", filters={"action": "update_public_portal_settings"})
		metadata = frappe.parse_json(event.metadata)
		self.assertEqual(metadata["before_version"], start)
		self.assertEqual(metadata["after_version"], start + 1)
		self.assertNotIn("Monday", str(metadata["before"]["support"].get("hours") or ""))
		self.assertEqual(metadata["after"]["support"]["hours"], COMPLETE["supplier_support_hours"])

	def test_the_same_key_with_different_content_is_refused(self):
		start = portal.get_public_portal_settings()["record_version"]
		key = _key()
		portal.update_public_portal_settings(**COMPLETE, expected_version=start, idempotency_key=key)
		with self.assertRaises(ConfigurationError) as caught:
			portal.update_public_portal_settings(**dict(COMPLETE, supplier_support_hours="Weekdays"), expected_version=start, idempotency_key=key)
		self.assertEqual(caught.exception.code, "CFG_IDEMPOTENCY_CONFLICT")

	def test_a_stale_version_is_refused_without_effect(self):
		self._save()
		current = portal.get_public_portal_settings()["record_version"]
		with self.assertRaises(ConfigurationError) as caught:
			portal.update_public_portal_settings(**dict(COMPLETE, supplier_support_hours="Weekdays"), expected_version=current - 1, idempotency_key=_key())
		self.assertEqual(caught.exception.code, "CFG_VERSION_CONFLICT")
		self.assertEqual(portal.get_public_portal_settings()["record_version"], current)

	# CFG16-AC-006 — the bidder-safe projection is allowlisted.
	def test_the_public_projection_carries_only_the_allowlisted_facts(self):
		self._save()
		info = portal.get_public_portal_information()
		self.assertEqual(set(info), {"status", "missing", "record_version", "support", "links"})
		self.assertEqual(info["status"], "Complete")
		self.assertEqual(info["missing"], [])
		self.assertEqual(info["support"], {"label": "Supplier support", "email": COMPLETE["supplier_support_email"],
			"phone": COMPLETE["supplier_support_phone"], "hours": COMPLETE["supplier_support_hours"]})
		self.assertEqual(info["links"], [
			{"key": "privacy", "label": "Privacy and data use", "url": COMPLETE["privacy_notice_url"]},
			{"key": "terms", "label": "Terms of portal use", "url": COMPLETE["portal_terms_url"]},
			{"key": "accessibility", "label": "Accessibility", "url": COMPLETE["accessibility_statement_url"]},
		])

	def test_optional_support_facts_are_omitted_rather_than_placeheld(self):
		self._save(dict(COMPLETE, supplier_support_phone="", supplier_support_hours=""))
		support = portal.get_public_portal_information()["support"]
		self.assertNotIn("phone", support)
		self.assertNotIn("hours", support)

	# CFG16-AC-007 input — an incomplete record reports exactly what is missing.
	def test_an_incomplete_record_is_reported_with_its_missing_categories(self):
		self._save()
		for field in ("privacy_notice_url", "supplier_support_email"):
			frappe.db.set_single_value(portal.SETTINGS, field, "")
		info = portal.get_public_portal_information()
		self.assertEqual(info["status"], "Incomplete")
		self.assertEqual(info["missing"], ["support", "privacy"])
		self.assertEqual([link["key"] for link in info["links"]], ["terms", "accessibility"])

	def test_the_record_cannot_be_written_around_the_command(self):
		doc = frappe.get_single(portal.SETTINGS)
		doc.supplier_support_email = "elsewhere@health.go.ke"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
