# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.11 §§5.3, 8, 12 — the bound release's state on the Tender
record and the **View STD Template** route on template errors (STD-TPL-IMP-001
follow-up FU-10). Uses its own switched-off test release only; never touches
Tender or Requisition rows."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_templates.services import installer, lifecycle
from kentender_procurement.std_templates.tests import support
from kentender_procurement.tenders.services import template_binding
from kentender_procurement.tenders.services.errors import TendersError


class TemplateBindingCase(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		root, info = support.make_test_package(template_release="9.0-test")
		self.addCleanup(lambda: support.purge([info["release_id"]]))
		self.addCleanup(lambda: support.cleanup_tmp(info))
		installer.install_approved_std_release(str(root), installed_by="test", site_switch="Off")
		frappe.db.commit()
		self.release = frappe.get_doc("Installed STD Release", info["release_id"])

	def record(self, **overrides):
		values = {
			"template_key": self.release.template_key, "template_release_id": self.release.name,
			"bundle_digest": self.release.bundle_digest, "official_source_digest": self.release.official_source_digest, "published_at": None,
		}
		values.update(overrides)
		return frappe._dict(values)


class TestReleaseNotice(TemplateBindingCase):
	def test_a_usable_release_shows_no_notice(self):
		self.assertIsNone(template_binding.release_notice(self.record(), "Administrator"))

	def test_superseded_unpublished_names_the_release_and_offers_the_route_to_readers_only(self):
		lifecycle.supersede(self.release.name, release_owner="test release owner")
		notice = template_binding.release_notice(self.record(), "Administrator")
		self.assertEqual((notice["state"], notice["tone"], notice["heading"]), ("Superseded", "is-warning", "Tender format has a newer release"))
		self.assertIn("release 9.0-test", notice["text"])
		self.assertEqual(notice["std_template_route"], ["std-templates", self.release.name])
		self.assertEqual(template_binding.release_notice(self.record(), "Guest")["std_template_route"], [])

	def test_withdrawn_before_and_after_publication(self):
		lifecycle.withdraw(self.release.name, reason="Legal defect in the reservation clause.", release_owner="test release owner")
		before = template_binding.release_notice(self.record(), "Administrator")
		self.assertEqual((before["tone"], before["heading"]), ("is-critical", "Tender format withdrawn"))
		self.assertIn("Your work is preserved", before["text"])
		after = template_binding.release_notice(self.record(published_at="2027-05-15 08:00:00"), "Administrator")
		self.assertEqual(after["tone"], "is-info")
		self.assertIn("remain the record", after["text"])

	def test_a_failed_integrity_check_blocks_only_unpublished_work(self):
		frappe.db.set_value("Installed STD Release", self.release.name, "integrity_status", "Failed", update_modified=False)
		self.assertEqual(template_binding.release_notice(self.record(), "Administrator")["state"], "Failed")
		self.assertIsNone(template_binding.release_notice(self.record(published_at="2027-05-15 08:00:00"), "Administrator"))

	def test_a_record_without_a_bound_release_shows_nothing(self):
		self.assertIsNone(template_binding.release_notice(self.record(template_key=""), "Administrator"))


class TestErrorRoute(TemplateBindingCase):
	def test_a_withdrawn_release_error_carries_the_route_for_a_reader(self):
		lifecycle.withdraw(self.release.name, reason="Legal defect in the reservation clause.", release_owner="test release owner")
		with self.assertRaises(TendersError) as ctx:
			template_binding.require_bound(self.record(), "continue")
		self.assertEqual(ctx.exception.code, "TND_TEMPLATE_RELEASE_WITHDRAWN")
		self.assertEqual(ctx.exception.detail["std_template_route"], ["std-templates", self.release.name])

	def test_the_route_is_withheld_from_a_non_reader(self):
		lifecycle.withdraw(self.release.name, reason="Legal defect in the reservation clause.", release_owner="test release owner")
		frappe.set_user("Guest")
		try:
			with self.assertRaises(TendersError) as ctx:
				template_binding.require_bound(self.record(), "continue")
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(ctx.exception.detail["std_template_route"], [])
