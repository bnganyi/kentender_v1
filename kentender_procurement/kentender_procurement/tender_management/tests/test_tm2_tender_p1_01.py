# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-01 — TM2 Tender DocType: uniqueness, status vocabulary, auto ``tender_code``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_tm2_tender_p1_01
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)


class TestTM2TenderP101(_ReleaseProcurementPackageHandoffFixtures):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		for dt, name in reversed(self._created):
			if dt != "TM2 Tender" or not name:
				continue
			if frappe.db.exists("TM2 Tender", name):
				frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)
		super().tearDown()

	def _minimal_tm2_payload(self, plan_name: str, pkg_name: str, **kwargs):
		base = {
			"doctype": "TM2 Tender",
			"tender_title": kwargs.get("tender_title", "P101 Test Tender"),
			"procurement_package": pkg_name,
			"procurement_plan": plan_name,
			"procurement_category": "Goods",
			"tender_visibility": "Public",
		}
		base.update(kwargs)
		return base

	def test_p101_auto_generates_tender_code(self) -> None:
		plan = self._mk_plan(fiscal_year=2029)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		doc = frappe.get_doc(self._minimal_tm2_payload(plan.name, pkg.name)).insert(
			ignore_permissions=True
		)
		self._created.append(("TM2 Tender", doc.name))
		self.assertTrue(doc.tender_code.startswith("TND-MOH-2029-"), doc.tender_code)
		self.assertRegex(doc.tender_code, r"^TND-MOH-2029-\d{4}$")
		self.assertEqual(doc.name, doc.tender_code)
		self.assertTrue(doc.procurement_package_code)
		self.assertTrue(doc.procurement_plan_code)

	def test_p101_duplicate_tender_code_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2099)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		code = "TND-DUP-2099-0001"
		d1 = frappe.get_doc(
			self._minimal_tm2_payload(
				plan.name,
				pkg.name,
				tender_title="First",
				tender_code=code,
			)
		).insert(ignore_permissions=True)
		self._created.append(("TM2 Tender", d1.name))
		d2 = frappe.get_doc(
			self._minimal_tm2_payload(
				plan.name,
				pkg.name,
				tender_title="Second",
				tender_code=code,
			)
		)
		with self.assertRaises(frappe.ValidationError):
			d2.insert(ignore_permissions=True)

	def test_p101_invalid_status_rejected(self) -> None:
		plan = self._mk_plan(fiscal_year=2031)
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		doc = frappe.get_doc(
			self._minimal_tm2_payload(plan.name, pkg.name, status="NotARealLifecycleState")
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_p101_meta_includes_doc9_minimum_fields(self) -> None:
		meta = frappe.get_meta("TM2 Tender")
		for fieldname in (
			"tender_code",
			"tender_title",
			"tender_description",
			"procurement_package_code",
			"procurement_plan_code",
			"procuring_entity_code",
			"fiscal_year",
			"procurement_method",
			"procurement_category",
			"contract_type",
			"tender_visibility",
			"status",
			"estimated_value_internal",
			"currency",
			"std_bound",
			"std_readiness_status",
			"created_by_user",
			"created_at",
			"published_at",
			"closed_at",
			"cancelled_at",
			"cancellation_reason",
			"retender_of_tender_code",
			"supersedes_tender_code",
			"is_active",
		):
			with self.subTest(fieldname=fieldname):
				self.assertIsNotNone(meta.get_field(fieldname), f"missing field {fieldname}")
