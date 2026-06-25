# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-005..P7-010 — Released surface evidence drawer and supplier denial."""

from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.evidence_view_model import (
	get_pp_evidence_view_model,
)
from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_released_to_tender,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
)
from kentender_procurement.procurement_planning.services.evidence_view_model import (
	get_evidence_view_model,
)

_PROHIBITED_TEXT_RE = re.compile(
	r"(source_object_code|target_object_code|technical_refs_json|audit_event_ref|PLANINCL-|PKGREL-|PKGCONSUME-)",
	re.IGNORECASE,
)


class TestPP3ReleasedEvidenceP7005P7010(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_planner(self) -> str:
		email = f"p7010.planner.{frappe.generate_hash(length=6)}@moh.test"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P7010",
				"last_name": "Planner",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Procurement Planner")
		self._cleanup.append(("User", email))
		return email

	def _ensure_supplier(self) -> str:
		email = f"p7010.supplier.{frappe.generate_hash(length=6)}@moh.test"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P7010",
				"last_name": "Supplier",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Supplier")
		self._cleanup.append(("User", email))
		return email

	def test_pp7_006_evidence_timeline_has_business_events(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		labels = [str(row.get("label") or "") for row in out.get("timeline") or []]
		self.assertTrue(
			any("Demand entered planning queue" in label or "Demand included" in label for label in labels),
			msg=labels,
		)
		self.assertTrue(
			any("Package released" in label or "released" in label.lower() for label in labels),
			msg=labels,
		)

	def test_pp7_007_evidence_records_use_business_labels(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		labels = [str(row.get("label") or "") for row in out.get("records") or []]
		self.assertIn("Demand Approval Certificate", labels)
		self.assertIn("Planning Inclusion Record", labels)
		self.assertIn("Procurement Package", labels)
		for label in labels:
			self.assertNotRegex(label, _PROHIBITED_TEXT_RE.pattern)

	def test_pp7_008_technical_details_collapsed_by_default(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("visible_by_default"))
		self.assertTrue(technical.get("requires_permission"))

	def test_pp7_009_unauthorized_user_cannot_view_technical_payload(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		planner = self._ensure_planner()
		out = get_evidence_view_model(package_code=PKG_CODE, actor=planner)
		self.assertTrue(out.get("ok"), msg=out)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("may_view_technical"))

	def test_pp7_009_authorized_user_can_view_technical_payload(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		technical = out.get("technical_details") or {}
		self.assertTrue(technical.get("may_view_technical"))
		self.assertTrue(technical.get("codes"))

	def test_pp7_010_supplier_denied_released_list_and_evidence(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		supplier = self._ensure_supplier()
		frappe.set_user(supplier)
		list_out = get_pp_released_to_tender()
		self.assertFalse(list_out.get("ok"))
		self.assertEqual(list_out.get("error_code"), "PP_ACCESS_DENIED")
		evidence_out = get_pp_evidence_view_model(package_code=PKG_CODE)
		self.assertFalse(evidence_out.get("ok"))
		self.assertEqual(evidence_out.get("error_code"), "PP_ACCESS_DENIED")

	def test_pp7_005_evidence_drawer_opens_only_from_view_evidence_action(self) -> None:
		summary_path = Path(frappe.get_app_path("kentender_procurement")) / "public" / "js" / "pp3_planning_release_summary.js"
		with summary_path.open(encoding="utf-8") as fh:
			summary_source = fh.read()
		self.assertIn("pp3-view-release-evidence", summary_source)
		self.assertIn("onViewEvidence", summary_source)
		self.assertNotIn("PlanningWorkbenchEvidenceDrawer.open", summary_source)
