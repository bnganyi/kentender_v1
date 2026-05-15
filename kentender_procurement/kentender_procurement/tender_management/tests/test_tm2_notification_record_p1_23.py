# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-23 — TM2 Notification Record (NTF-{tender_code}-{####}, TM2-NTF-003, post-send lock).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_notification_record_p1_23
"""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestTM2NotificationRecordP123(_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Notification Record",
			filters={"tender_code": ["like", "TND-P123%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Notification Record", row):
				frappe.delete_doc("TM2 Notification Record", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P123%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_tender(self, *, tender_code: str = "TND-P123-2028-0001"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		return self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)

	def _ntf_doc(self, tm2_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Notification Record",
			"tm2_tender": tm2_name,
			"notification_type": "Addendum",
			"recipient_type": "Supplier",
			"channel": "Email",
			"payload_snapshot": {"subject": "Fixture"},
		}
		base.update(kwargs)
		return base

	def test_p123_sequential_codes_per_tender(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P123-2028-0001")
		a = frappe.get_doc(self._ntf_doc(tm2.name)).insert(ignore_permissions=True)
		b = frappe.get_doc(self._ntf_doc(tm2.name, recipient_ref="SUP-X")).insert(ignore_permissions=True)
		self.assertEqual(a.notification_code, f"NTF-{tm2.tender_code}-0001")
		self.assertEqual(b.notification_code, f"NTF-{tm2.tender_code}-0002")

	def test_p123_ntf_003_public_blocks_confidential_marker(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P123-2028-0002")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._ntf_doc(
					tm2.name,
					recipient_type="Public",
					payload_snapshot={"confidential_evaluation_payload": {"scores": [1, 2]}},
				)
			).insert(ignore_permissions=True)

	def test_p123_public_allows_safe_payload(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P123-2028-0003")
		n = frappe.get_doc(
			self._ntf_doc(
				tm2.name,
				recipient_type="Public",
				notification_type="Publication",
				payload_snapshot={"headline": "Tender published"},
			)
		).insert(ignore_permissions=True)
		self.assertTrue(n.name)

	def test_p123_post_send_locks_core_fields(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P123-2028-0004")
		n = frappe.get_doc(self._ntf_doc(tm2.name)).insert(ignore_permissions=True)
		n.reload()
		n.sent_at = now_datetime()
		n.delivery_status = "Sent"
		n.save(ignore_permissions=True)
		n.reload()
		n.notification_type = "General"
		with self.assertRaises(frappe.ValidationError):
			n.save(ignore_permissions=True)

	def test_p123_post_send_allows_delivery_status(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P123-2028-0005")
		n = frappe.get_doc(self._ntf_doc(tm2.name)).insert(ignore_permissions=True)
		n.reload()
		n.sent_at = now_datetime()
		n.save(ignore_permissions=True)
		n.reload()
		n.delivery_status = "Delivered"
		n.failure_reason = ""
		n.save(ignore_permissions=True)
		self.assertEqual(n.delivery_status, "Delivered")

	def test_p123_invalid_notification_type(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P123-2028-0006")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._ntf_doc(tm2.name, notification_type="InvalidType")).insert(ignore_permissions=True)

	def test_p123_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Notification Record")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"notification_code",
			"tm2_tender",
			"tender_code",
			"related_object_type",
			"related_object_id",
			"notification_type",
			"recipient_type",
			"recipient_ref",
			"channel",
			"message_template_code",
			"payload_snapshot",
			"sent_at",
			"delivery_status",
			"failure_reason",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
