# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-03 — TM2 Tender Timeline DocType (ordering, one-per-tender, published lock).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_timeline_p1_03
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2TenderTimelineP103(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for name in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P103%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", name):
				frappe.delete_doc("TM2 Tender Timeline", name, force=True, ignore_permissions=True)
		for name in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P103%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", name):
				frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)
		super().tearDown()

	def _mk_tm2(self, plan_name: str, pkg_name: str, *, tender_code: str) -> frappe.model.document.Document:
		return frappe.get_doc(
			{
				"doctype": "TM2 Tender",
				"tender_title": "P103 TM2",
				"tender_code": tender_code,
				"procurement_package": pkg_name,
				"procurement_plan": plan_name,
				"procurement_category": "Goods",
				"tender_visibility": "Public",
			}
		).insert(ignore_permissions=True)

	def _valid_datetimes(self):
		base = now_datetime()
		return {
			"planned_publication_at": add_to_date(base, hours=1),
			"clarification_deadline_at": add_to_date(base, days=2),
			"addendum_cutoff_at": add_to_date(base, days=3),
			"submission_deadline_at": add_to_date(base, days=5),
			"opening_scheduled_at": add_to_date(base, days=5),
		}

	def test_p103_insert_and_timeline_code(self) -> None:
		plan = self._mk_plan(fiscal_year=2028)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P103-2028-0001")
		dt = self._valid_datetimes()
		tl = frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2.name,
				"tender_validity_days": 90,
				"timezone": "Africa/Nairobi",
				**dt,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(tl.timeline_code, f"TTL-{tm2.tender_code}")
		self.assertEqual(tl.name, tl.timeline_code)

	def test_p103_second_timeline_same_tender_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2027)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P103-2027-0001")
		dt = self._valid_datetimes()
		frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2.name,
				"tender_validity_days": 60,
				"timezone": "Africa/Nairobi",
				**dt,
			}
		).insert(ignore_permissions=True)
		doc2 = frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2.name,
				"tender_validity_days": 60,
				"timezone": "Africa/Nairobi",
				**dt,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc2.insert(ignore_permissions=True)

	def test_p103_clarification_after_submission_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2026)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P103-2026-0001")
		base = now_datetime()
		pub = add_to_date(base, hours=1)
		sub = add_to_date(base, days=3)
		bad_clar = add_to_date(base, days=4)
		opn = add_to_date(base, days=5)
		doc = frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2.name,
				"tender_validity_days": 30,
				"timezone": "Africa/Nairobi",
				"planned_publication_at": pub,
				"clarification_deadline_at": bad_clar,
				"submission_deadline_at": sub,
				"opening_scheduled_at": opn,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_p103_published_tender_locks_core_deadlines(self) -> None:
		plan = self._mk_plan(fiscal_year=2030)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2 = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P103-2030-0001")
		dt = self._valid_datetimes()
		tl = frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2.name,
				"tender_validity_days": 90,
				"timezone": "Africa/Nairobi",
				**dt,
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("TM2 Tender", tm2.name, "status", "Published", update_modified=False)
		tl.reload()
		tl.submission_deadline_at = add_to_date(tl.submission_deadline_at, days=30)
		with self.assertRaises(frappe.ValidationError):
			tl.save(ignore_permissions=True)

	def test_p103_meta_doc9_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender Timeline")
		for fn in (
			"timeline_code",
			"tender_code",
			"planned_publication_at",
			"actual_publication_at",
			"clarification_deadline_at",
			"addendum_cutoff_at",
			"submission_deadline_at",
			"opening_scheduled_at",
			"tender_validity_days",
			"timezone",
			"deadline_extended",
			"extension_source_addendum_code",
			"extension_reason",
		):
			with self.subTest(fieldname=fn):
				self.assertIsNotNone(meta.get_field(fn), f"missing {fn}")

	def test_p103_duplicate_timeline_code_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2031)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		tm2a = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P103-2031-0001")
		tm2b = self._mk_tm2(plan.name, pkg.name, tender_code="TND-P103-2031-0002")
		dt = self._valid_datetimes()
		code = "TTL-P103-DUP-FIXED"
		frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2a.name,
				"timeline_code": code,
				"tender_validity_days": 30,
				"timezone": "Africa/Nairobi",
				**dt,
			}
		).insert(ignore_permissions=True)
		doc2 = frappe.get_doc(
			{
				"doctype": "TM2 Tender Timeline",
				"tm2_tender": tm2b.name,
				"timeline_code": code,
				"tender_validity_days": 30,
				"timezone": "Africa/Nairobi",
				**dt,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc2.insert(ignore_permissions=True)
