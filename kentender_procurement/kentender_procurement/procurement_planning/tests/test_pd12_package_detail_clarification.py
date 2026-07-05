# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PD12 — Package Detail clarification decision + view-model gates."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.package_detail import get_pp3_package_detail
from kentender_procurement.procurement_planning.api.workflow import request_clarification
from kentender_procurement.procurement_planning.pp2_constants import PKG_IN_REVIEW
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.package_detail_view_model import (
	get_pp3_package_detail_view_model,
)
from kentender_procurement.procurement_planning.services.package_review_service import (
	list_package_review_decisions,
	request_clarification_on_package,
)
from kentender_procurement.procurement_planning.services.planning_audit_constants import (
	PACKAGE_CLARIFICATION_REQUESTED,
)

_REVIEWER = "planning.reviewer@moh.test"
_MESSAGE = "Please confirm the district hospital scope boundary."


class TestPD12PackageDetailClarification(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False

	def _seed(self) -> None:
		out = seed_procurement_planning_works_master(checkpoint="PACKAGE_DRAFT", force_reset=True)
		if not out.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {out}")
		pkg = frappe.get_doc("Procurement Package", {"package_code": PKG_CODE})
		frappe.db.set_value("Procurement Package", pkg.name, "status", PKG_IN_REVIEW, update_modified=False)
		frappe.db.commit()

	def test_pd12_clarification_decision_requires_reason(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		doc = frappe.get_doc(
			{
				"doctype": "Package Review Decision",
				"package_code": PKG_CODE,
				"decision_type": "Clarification Requested",
				"from_state": PKG_IN_REVIEW,
				"to_state": PKG_IN_REVIEW,
				"decided_by": "Administrator",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert(ignore_permissions=True)

	def test_pd12_request_clarification_keeps_in_review_and_records_audit(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _REVIEWER):
			self.skipTest(f"{_REVIEWER} not configured")
		self._seed()
		frappe.set_user(_REVIEWER)
		out = request_clarification_on_package(PKG_CODE, _MESSAGE, _REVIEWER)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), PKG_IN_REVIEW)
		self.assertEqual(
			frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "status"),
			PKG_IN_REVIEW,
		)
		history = list_package_review_decisions(PKG_CODE)
		self.assertTrue(any(row.get("decision_type") == "Clarification Requested" for row in history))
		audit = frappe.get_all(
			"Planning Audit Event",
			filters={
				"object_type": "Procurement Package",
				"object_code": PKG_CODE,
				"event_type": PACKAGE_CLARIFICATION_REQUESTED,
			},
			fields=["name", "reason"],
			limit=1,
		)
		self.assertTrue(audit, "Expected clarification audit event")
		self.assertIn(_MESSAGE, audit[0].get("reason") or "")

	def test_pd12_reviewer_api_can_load_package_detail(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _REVIEWER):
			self.skipTest(f"{_REVIEWER} not configured")
		self._seed()
		frappe.set_user(_REVIEWER)
		out = get_pp3_package_detail(package=PKG_CODE)
		self.assertTrue(out.get("ok"), out)
		review = (out.get("tabs") or {}).get("review") or {}
		self.assertTrue(review.get("may_approve"), review)

	def test_pd12_approved_package_detail_loads_without_review_guard_throw(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _REVIEWER):
			self.skipTest(f"{_REVIEWER} not configured")
		self._seed()
		from kentender_procurement.procurement_planning.api.workflow import approve_package

		frappe.set_user(_REVIEWER)
		approve_package(PKG_CODE)
		frappe.db.commit()
		out = get_pp3_package_detail(package=PKG_CODE)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("display_status_pill"), "APPROVED")
		review = (out.get("tabs") or {}).get("review") or {}
		self.assertFalse(review.get("may_approve"), review)

	def test_pd12_reviewer_view_model_exposes_clarify_action(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _REVIEWER):
			self.skipTest(f"{_REVIEWER} not configured")
		self._seed()
		out = get_pp3_package_detail_view_model(PKG_CODE, _REVIEWER)
		self.assertTrue(out.get("ok"), out)
		review = (out.get("tabs") or {}).get("review") or {}
		self.assertTrue(review.get("may_clarify"), review)

	def test_pd12_whitelisted_api_delegates_to_service(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not frappe.db.exists("User", _REVIEWER):
			self.skipTest(f"{_REVIEWER} not configured")
		self._seed()
		frappe.set_user(_REVIEWER)
		out = request_clarification(package_id=PKG_CODE, message=_MESSAGE)
		self.assertEqual(out.get("status"), PKG_IN_REVIEW)
