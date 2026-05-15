# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P6-07 — doc 9 §11.7 ``get_bid_content`` / ``getBidContent`` (sealed bid access guard).

**EX-11** (doc 9 §25 / doc 8 TM2-SMOKE-SEAL-001 / TM2-SMOKE-SEAL-002): ``test_EX_11_*`` — sealed bid
desk reads denied **pre-opening** for **Procurement Officer** and **Administrator** (``AUTH_SEALED_BID_DENIED``)
with **Access Denied** audit on **TM2 Tender Audit Event**.

**EX-12** (doc 9 §25 / doc 8 TM2-SMOKE-SEC-003): ``test_EX_12_*`` — supplier **A** cannot read supplier **B**'s
bid via ``acting_supplier`` impersonation (``AUTH_CONTEXT_DENIED``).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p6_07_get_bid_content
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.get_bid_content import getBidContent, get_bid_content
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_P607_EX11_PO_EMAIL = "p607-ex11-po001@example.com"


class TestP607GetBidContent(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	p6_supplier_fixture_prefix = "P607"

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

	def _portal_submit_ctx(self) -> dict:
		spec = spec_for_action("BID2_SUBMIT")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _published_si_supplier(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup = self._published_with_supplier()
		si = frappe.db.get_value(
			"TM2 Tender STD Binding",
			{"tm2_tender": tm2, "is_active": 1},
			"tender_std_instance",
		)
		assert si
		return tcode, tm2, sup, str(si)

	def _submit_sealed_bid(self) -> tuple[str, str, str, str]:
		tcode, tm2, sup, si = self._published_si_supplier()
		ctx = {**self._portal_submit_ctx(), "acting_supplier": sup}
		bid = _valid_bid_for_fixture(tcode, sup, si)
		out = submit_bid("Administrator", tcode, sup, bid, context=ctx)
		self.assertTrue(out.get("ok"), out)
		bc = str(out.get("bid_code") or "")
		self.assertTrue(bc)
		return tcode, tm2, sup, bc

	def _ensure_role(self, role: str) -> None:
		if not frappe.db.exists("Role", role):
			doc = frappe.new_doc("Role")
			doc.role_name = role
			doc.insert(ignore_permissions=True)

	def _ensure_procurement_officer_ex11(self) -> None:
		self._ensure_role("Procurement Officer")
		if not frappe.db.exists("User", _P607_EX11_PO_EMAIL):
			u = frappe.new_doc("User")
			u.email = _P607_EX11_PO_EMAIL
			u.first_name = "P607"
			u.last_name = "EX11PO"
			u.user_type = "System User"
			u.enabled = 1
			u.new_password = "Test@1234"
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
		frappe.get_doc("User", _P607_EX11_PO_EMAIL).add_roles("Procurement Officer")

	def _cleanup_procurement_officer_ex11(self) -> None:
		if frappe.db.exists("User", _P607_EX11_PO_EMAIL):
			frappe.delete_doc("User", _P607_EX11_PO_EMAIL, force=True, ignore_permissions=True)

	def test_EX_11_sealed_bid_denied_for_administrator_pre_opening_with_audit(self) -> None:
		"""Doc 8 USER-SYSADMIN-001 / TM2-SMOKE-SEAL-002 — Administrator desk path denied pre-opening."""
		_tcode, tm2, _sup, bc = self._submit_sealed_bid()
		aud_before = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Access Denied",
				"denial_code": DenialCode.AUTH_SEALED_BID_DENIED.value,
				"related_object_id": bc,
			},
			pluck="name",
		)
		out = get_bid_content("Administrator", bc, context={})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SEALED_BID_DENIED.value)
		aud_after = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Access Denied",
				"denial_code": DenialCode.AUTH_SEALED_BID_DENIED.value,
				"related_object_id": bc,
			},
			pluck="name",
		)
		self.assertEqual(len(aud_after), len(aud_before) + 1)

	def test_EX_11_sealed_bid_denied_for_procurement_officer_pre_opening_with_audit(self) -> None:
		"""Doc 8 USER-PO-001 / TM2-SMOKE-SEAL-001 — officer desk path denied pre-opening."""
		self._ensure_procurement_officer_ex11()
		self.addCleanup(self._cleanup_procurement_officer_ex11)
		_tcode, tm2, _sup, bc = self._submit_sealed_bid()
		aud_before = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Access Denied",
				"denial_code": DenialCode.AUTH_SEALED_BID_DENIED.value,
				"related_object_id": bc,
			},
			pluck="name",
		)
		out = get_bid_content(_P607_EX11_PO_EMAIL, bc, context={})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SEALED_BID_DENIED.value)
		aud_after = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Access Denied",
				"denial_code": DenialCode.AUTH_SEALED_BID_DENIED.value,
				"related_object_id": bc,
			},
			pluck="name",
		)
		self.assertEqual(len(aud_after), len(aud_before) + 1)

	def test_p6_07_supplier_acting_own_metadata(self) -> None:
		tcode, _tm2, sup, bc = self._submit_sealed_bid()
		ctx = {**self._portal_submit_ctx(), "acting_supplier": sup}
		out = getBidContent("Administrator", bc, context=ctx)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("access_tier"), "metadata")
		self.assertEqual(out.get("bid_code"), bc)
		self.assertTrue(out.get("submission_hash"))
		self.assertIn("components", out)

	def test_EX_12_get_bid_content_denied_when_acting_supplier_not_bid_owner(self) -> None:
		"""Doc 8 TM2-SMOKE-SEC-003 — wrong ``acting_supplier`` cannot read another supplier's bid."""
		tcode, tm2, sup_alpha, bc = self._submit_sealed_bid()
		sup_beta = self._ensure_supplier("Beta")
		frappe.get_doc(
			{"doctype": "TM2 Supplier Participation", "tm2_tender": tm2, "supplier": sup_beta}
		).insert(ignore_permissions=True)
		ctx = {**self._portal_submit_ctx(), "acting_supplier": sup_beta}
		out = get_bid_content("Administrator", bc, context=ctx)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p6_07_post_opening_desk_with_sealed_permission_ok(self) -> None:
		_tcode, tm2, _sup, bc = self._submit_sealed_bid()
		frappe.db.set_value("TM2 Tender", tm2, "status", "Opening Completed", update_modified=False)
		spec = spec_for_action("BID2_VIEW_SEALED_CONTENT")
		self.assertIsNotNone(spec)
		assert spec is not None
		out = get_bid_content(
			"Administrator",
			bc,
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertTrue(out.get("lawful_opening"))
		self.assertEqual(out.get("access_tier"), "metadata")

	def test_p6_07_post_opening_desk_without_permission_denied(self) -> None:
		_tcode, tm2, _sup, bc = self._submit_sealed_bid()
		frappe.db.set_value("TM2 Tender", tm2, "status", "Opening Completed", update_modified=False)
		out = get_bid_content("Administrator", bc, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p6_07_unknown_bid_denied(self) -> None:
		out = get_bid_content("Administrator", "BID-NONEXISTENT-000000", context={})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)
