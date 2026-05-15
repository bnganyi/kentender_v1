# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-24 — TM2 Tender Audit Event (TAE-{tender_code}-{####}, TM2-AUD-001/003/004/005/006).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_audit_event_p1_24
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestTM2TenderAuditEventP124(_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tender_code": ["like", "TND-P124%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Tender Audit Event", row):
				frappe.delete_doc("TM2 Tender Audit Event", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P124%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _fixture_tender(self, *, tender_code: str = "TND-P124-2028-0001"):
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		return self._mk_tm2(plan.name, pkg.name, tender_code=tender_code)

	def _tae_doc(self, tm2_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Tender Audit Event",
			"tm2_tender": tm2_name,
			"event_type": "Tender Created",
			"actor_type": "System",
			"event_payload": {"fixture": True},
		}
		base.update(kwargs)
		return base

	def test_p124_sequential_codes(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0001")
		a = frappe.get_doc(self._tae_doc(tm2.name)).insert(ignore_permissions=True)
		b = frappe.get_doc(self._tae_doc(tm2.name, event_type="Tender STD Bound")).insert(ignore_permissions=True)
		self.assertEqual(a.audit_event_code, f"TAE-{tm2.tender_code}-0001")
		self.assertEqual(b.audit_event_code, f"TAE-{tm2.tender_code}-0002")

	def test_p124_aud_001_rejects_update(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0002")
		doc = frappe.get_doc(self._tae_doc(tm2.name)).insert(ignore_permissions=True)
		doc.reload()
		doc.event_payload = {"mutated": True}
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_p124_aud_005_delete_blocked_outside_test(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0003")
		doc = frappe.get_doc(self._tae_doc(tm2.name)).insert(ignore_permissions=True)
		with patch.object(frappe, "in_test", False):
			with self.assertRaises(frappe.ValidationError):
				frappe.delete_doc("TM2 Tender Audit Event", doc.name, force=True, ignore_permissions=True)

	def test_p124_aud_005_delete_allowed_with_flag(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0004")
		doc = frappe.get_doc(self._tae_doc(tm2.name)).insert(ignore_permissions=True)
		doc.flags.ignore_tm2_aud_allow_delete = True
		doc.delete(ignore_permissions=True)
		self.assertFalse(frappe.db.exists("TM2 Tender Audit Event", doc.name))

	def test_p124_aud_003_high_risk_requires_reason(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0005")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._tae_doc(tm2.name, event_type="Tender Cancelled")).insert(ignore_permissions=True)
		d = frappe.get_doc(
			self._tae_doc(tm2.name, event_type="Tender Cancelled", reason="Scope withdrawn per HOP decision.")
		).insert(ignore_permissions=True)
		self.assertTrue(d.name)

	def test_p124_aud_004_tender_published_requires_snapshot_in_payload(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0006")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._tae_doc(tm2.name, event_type="Tender Published", event_payload={"bundle_output_code": "X"})
			).insert(ignore_permissions=True)
		d = frappe.get_doc(
			self._tae_doc(
				tm2.name,
				event_type="Tender Published",
				event_payload={"publication_snapshot_code": "PUBSNAP-P124-001"},
				publication_snapshot_code="PUBSNAP-P124-001",
			)
		).insert(ignore_permissions=True)
		self.assertEqual(d.event_type, "Tender Published")

	def test_p124_aud_006_denial_events_require_denial_code(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0007")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._tae_doc(tm2.name, event_type="Access Denied")).insert(ignore_permissions=True)
		frappe.get_doc(
			self._tae_doc(tm2.name, event_type="Access Denied", denial_code="AUTH_SEALED_BID_DENIED")
		).insert(ignore_permissions=True)

	def test_p124_user_actor_requires_actor_user(self) -> None:
		tm2 = self._fixture_tender(tender_code="TND-P124-2028-0008")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._tae_doc(tm2.name, actor_type="User")).insert(ignore_permissions=True)

	def test_p124_meta_doc3_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender Audit Event")
		names = {df.fieldname for df in meta.fields}
		for req in (
			"audit_event_code",
			"tm2_tender",
			"tender_code",
			"event_type",
			"actor_user",
			"actor_role",
			"actor_type",
			"occurred_at",
			"related_object_type",
			"related_object_id",
			"previous_state",
			"new_state",
			"reason",
			"std_template_version_code",
			"tender_std_instance_code",
			"output_reference_code",
			"publication_snapshot_code",
			"denial_code",
			"source_ip",
			"user_agent",
			"event_payload",
			"hash",
		):
			self.assertIn(req, names, msg=f"missing field {req}")
