# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S09 (Supplier Eligibility Block).

**§2:** ineligible supplier cannot prepare or submit a bid — ``start_bid_draft`` and ``submit_bid`` deny
with ``AUTH_SUPPLIER_INELIGIBLE`` via :func:`~kentender_procurement.tender_management.services.check_supplier_tender_access.check_supplier_tender_access`
(doc 9 §11.1 / **P6-01**). ``TM2 Tender Access Rule.supplier_category_restriction`` is set **before**
``publish_tender`` (**TM2-ACR-003** locks policy fields after publication).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s09
"""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	scenario_by_code,
	scenario_tracker_slug,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.check_supplier_tender_access import (
	check_supplier_tender_access,
)
from kentender_procurement.tender_management.services.publish_tender import publish_tender
from kentender_procurement.tender_management.services.start_bid_draft import start_bid_draft
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S09"


class TestTM2WorksS09Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Supplier Eligibility Block")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS09EligibilityBlock(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S09 (tracker **S-09**)."""

	p6_supplier_fixture_prefix = "S09"

	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
			update_modified=False,
		)

	def setUp(self) -> None:
		super().setUp()
		self._p602_suppliers_created: list[str] = []
		self._s09_groups: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for gn in self._s09_groups:
			if frappe.db.exists("Supplier Group", gn):
				try:
					frappe.delete_doc("Supplier Group", gn, force=True, ignore_permissions=True)
				except Exception:
					pass
		self._s09_groups.clear()
		super().tearDown()

	def _parent_supplier_group(self) -> str:
		parent = frappe.db.get_value("Supplier Group", {"name": "All Supplier Groups"}, "name")
		if parent:
			return str(parent)
		return str(
			frappe.db.get_value("Supplier Group", {"is_group": 1}, "name", order_by="lft asc") or ""
		)

	def _ensure_leaf_supplier_group(self, label: str) -> str:
		name = f"KT-S09-{label}"
		if frappe.db.exists("Supplier Group", name):
			if name not in self._s09_groups:
				self._s09_groups.append(name)
			return name
		parent = self._parent_supplier_group()
		self.assertTrue(parent, "No parent Supplier Group for S-09 fixtures")
		frappe.get_doc(
			{
				"doctype": "Supplier Group",
				"supplier_group_name": name,
				"parent_supplier_group": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		self._s09_groups.append(name)
		return name

	def _portal_draft_ctx(self) -> dict:
		spec_s = spec_for_action("BID2_START_DRAFT")
		spec_v = spec_for_action("BID2_SAVE_DRAFT")
		self.assertIsNotNone(spec_s)
		self.assertIsNotNone(spec_v)
		assert spec_s is not None and spec_v is not None
		return {"granted_permissions": [spec_s.required_permission, spec_v.required_permission]}

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_S_09_category_mismatch_blocks_draft_start_and_submit_bid(self) -> None:
		"""Pre-publish ``supplier_category_restriction`` (**TM2-ACR-003**), then publish — **P6-01** / §11.1."""
		sg_allowed = self._ensure_leaf_supplier_group("Building")
		sg_actual = self._ensure_leaf_supplier_group("Roads")
		tcode = self._mk_approved_for_publication()
		tm2_pre = frappe.db.get_value("TM2 Tender", {"tender_code": tcode}, "name")
		self.assertTrue(tm2_pre)
		rule_name = frappe.db.get_value("TM2 Tender Access Rule", {"tm2_tender": tm2_pre}, "name")
		self.assertTrue(rule_name)
		rule = frappe.get_doc("TM2 Tender Access Rule", str(rule_name))
		rule.supplier_category_restriction = {"categories": [sg_allowed]}
		rule.save(ignore_permissions=True)

		prefix = str(getattr(self, "p6_supplier_fixture_prefix", "P6"))
		supplier_name = f"{prefix} Alpha Supplier"
		existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
		if existing:
			frappe.db.set_value(
				"Supplier",
				existing,
				{"disabled": 0, "supplier_group": sg_actual},
				update_modified=False,
			)
			sup = str(existing)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Supplier",
					"naming_series": "SUP-.YYYY.-",
					"supplier_name": supplier_name,
					"supplier_type": "Company",
					"supplier_group": sg_actual,
				}
			).insert(ignore_permissions=True)
			self._p602_suppliers_created.append(doc.name)
			sup = doc.name

		spec_p = spec_for_action("TND2_PUBLISH")
		self.assertIsNotNone(spec_p)
		assert spec_p is not None
		pub = publish_tender(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_p.required_permission]},
		)
		self.assertTrue(pub.get("ok"), pub)
		tm2 = str(pub.get("tm2_tender") or "")
		self.assertTrue(tm2)
		self._ensure_open_submission_window(tm2)
		frappe.get_doc({"doctype": "TM2 Supplier Participation", "tm2_tender": tm2, "supplier": sup}).insert(
			ignore_permissions=True
		)
		self.addCleanup(self._cleanup_p602, tm2)

		gate = check_supplier_tender_access("Administrator", tcode, sup, context={})
		self.assertFalse(gate.get("ok"), gate)
		self.assertEqual(gate.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)

		ctx_draft = {**self._portal_draft_ctx(), "acting_supplier": sup}
		out_draft = start_bid_draft("Administrator", tcode, sup, context=ctx_draft)
		self.assertFalse(out_draft.get("ok"), out_draft)
		self.assertEqual(out_draft.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
		self.assertIn("category", str(out_draft.get("message") or "").lower())

		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		self.assertTrue(si)
		ctx_sub = {**self._portal_submit_ctx(), "acting_supplier": sup}
		bid = _valid_bid_for_fixture(tcode, sup, str(si))
		bid_before = frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup})
		out_sub = submit_bid("Administrator", tcode, sup, bid, context=ctx_sub)
		self.assertFalse(out_sub.get("ok"), out_sub)
		self.assertEqual(out_sub.get("denial_code"), DenialCode.AUTH_SUPPLIER_INELIGIBLE.value)
		self.assertEqual(
			bid_before,
			frappe.db.count("TM2 Bid Submission", {"tm2_tender": tm2, "supplier": sup}),
		)
