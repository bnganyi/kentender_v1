# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-09 — doc 8 **TM2-SMOKE-SEAL-001**; doc 9 §21.2 ``test_TM2_SMOKE_SEAL_001_…``.

Internal desk actors (doc 8 **USER-PO-001** / **Procurement Officer**) must **not** read sealed bid
content before lawful opening: ``get_bid_content`` returns ``AUTH_SEALED_BID_DENIED`` and appends
**Access Denied** on **TM2 Tender Audit Event** (doc 8 §14). Regress:
``test_EX_11_sealed_bid_denied_for_procurement_officer_pre_opening_with_audit`` in ``test_p6_07_get_bid_content``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o09_tm2_smoke_seal_001_internal_cannot_view_sealed_bid_before_opening
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.get_bid_content import get_bid_content
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture


# Doc 8 fixture label USER-PO-001 — internal procurement officer (not Administrator / not O-10).
_O09_INTERNAL_USER_EMAIL = "o09_user_po001@example.test"


class TestO09Tm2SmokeSeal001InternalCannotViewSealedBidBeforeOpening(
	_P401Tm2Cleanup,
	P6PublishedTm2Fixture,
):
	"""Doc 8 TM2-SMOKE-SEAL-001 — internal user denied sealed bid desk read pre-opening + audit."""

	p6_supplier_fixture_prefix = "O09"

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
		frappe.set_user("Administrator")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _ensure_role(self, role: str) -> None:
		if not frappe.db.exists("Role", role):
			doc = frappe.new_doc("Role")
			doc.role_name = role
			doc.insert(ignore_permissions=True)

	def _ensure_internal_user(self) -> None:
		self._ensure_role("Procurement Officer")
		if not frappe.db.exists("User", _O09_INTERNAL_USER_EMAIL):
			u = frappe.new_doc("User")
			u.email = _O09_INTERNAL_USER_EMAIL
			u.first_name = "O09"
			u.last_name = "PO001"
			u.user_type = "System User"
			u.enabled = 1
			u.new_password = "Test@1234"
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
		frappe.get_doc("User", _O09_INTERNAL_USER_EMAIL).add_roles("Procurement Officer")

	def _cleanup_internal_user(self) -> None:
		if frappe.db.exists("User", _O09_INTERNAL_USER_EMAIL):
			frappe.delete_doc("User", _O09_INTERNAL_USER_EMAIL, force=True, ignore_permissions=True)

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

	def test_TM2_SMOKE_SEAL_001_internal_user_cannot_view_sealed_bid_before_opening(self) -> None:
		self._ensure_internal_user()
		self.addCleanup(self._cleanup_internal_user)
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
		out = get_bid_content(_O09_INTERNAL_USER_EMAIL, bc, context={})
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
