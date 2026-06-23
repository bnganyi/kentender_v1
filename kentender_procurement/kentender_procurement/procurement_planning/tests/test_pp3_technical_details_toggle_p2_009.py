# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P2-009 — PP3 Technical Details toggle permission contract."""

from __future__ import annotations

import re

import frappe
from frappe.tests import IntegrationTestCase

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

_REQUIRED_TECHNICAL_FIELD_KEYS = {
	"source_object_code",
	"target_object_code",
	"locked_summary_json",
	"passed_forward_summary_json",
	"technical_refs_json",
	"audit_event_ref",
}


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Package"))


class TestPP3TechnicalDetailsToggleP2009(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []
		if not _pp_ok():
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER")
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")
		if not frappe.db.exists("Procurement Package", {"package_code": PKG_CODE}):
			self.skipTest("WORKS master package missing for technical-details tests")

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def _ensure_planner(self) -> str:
		email = f"p2009.planner.{frappe.generate_hash(length=6)}@moh.test"
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "P2009",
				"last_name": "Planner",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
		user.add_roles("Procurement Planner")
		self._cleanup.append(("User", email))
		return email

	def test_authorized_user_receives_technical_payload(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("visible_by_default"))
		self.assertTrue(technical.get("requires_permission"))
		self.assertTrue(technical.get("may_view_technical"))
		codes = technical.get("codes") or []
		self.assertGreater(len(codes), 0)
		self.assertTrue(any(str(code).startswith("PKG-") for code in codes), msg=codes)
		fields = technical.get("fields") or []
		field_keys = {
			str(row.get("key") or "").strip()
			for row in fields
			if isinstance(row, dict) and str(row.get("key") or "").strip()
		}
		self.assertTrue(
			_REQUIRED_TECHNICAL_FIELD_KEYS.issubset(field_keys),
			msg=f"missing keys: {_REQUIRED_TECHNICAL_FIELD_KEYS - field_keys}",
		)

	def test_unauthorized_user_receives_no_technical_payload(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		planner = self._ensure_planner()
		out = get_evidence_view_model(package_code=PKG_CODE, actor=planner)
		self.assertTrue(out.get("ok"), msg=out)
		technical = out.get("technical_details") or {}
		self.assertFalse(technical.get("may_view_technical"))
		self.assertFalse(technical.get("codes"))
		self.assertFalse(technical.get("fields"))

	def test_timeline_and_records_do_not_leak_technical_strings(self) -> None:
		if self._skip:
			self.skipTest("Procurement Planning DocTypes not installed")
		out = get_evidence_view_model(package_code=PKG_CODE, actor="Administrator")
		self.assertTrue(out.get("ok"), msg=out)
		for row in out.get("timeline") or []:
			self.assertNotRegex(str(row.get("label") or ""), _PROHIBITED_TEXT_RE.pattern)
		for row in out.get("records") or []:
			self.assertNotRegex(str(row.get("label") or ""), _PROHIBITED_TEXT_RE.pattern)
