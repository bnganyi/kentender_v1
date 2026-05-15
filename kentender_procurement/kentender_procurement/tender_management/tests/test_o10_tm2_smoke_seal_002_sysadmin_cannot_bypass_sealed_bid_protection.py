# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""O-10 — doc 8 **TM2-SMOKE-SEAL-002**; doc 9 §21.2 ``test_TM2_SMOKE_SEAL_002_…``.

**System Administrator** (doc 8 **USER-SYSADMIN-001**, Frappe **Administrator**) must **not** bypass
sealed-bid confidentiality before lawful opening: ``get_bid_content`` returns ``AUTH_SEALED_BID_DENIED``
and appends **Access Denied** on **TM2 Tender Audit Event** (doc 8 §14). Regress:
``test_EX_11_sealed_bid_denied_for_administrator_pre_opening_with_audit`` in ``test_p6_07_get_bid_content``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_o10_tm2_smoke_seal_002_sysadmin_cannot_bypass_sealed_bid_protection
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


class TestO10Tm2SmokeSeal002SysadminCannotBypassSealedBidProtection(
	_P401Tm2Cleanup,
	P6PublishedTm2Fixture,
):
	"""Doc 8 TM2-SMOKE-SEAL-002 — Administrator denied sealed bid desk read pre-opening + audit."""

	p6_supplier_fixture_prefix = "O10"

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

	def test_TM2_SMOKE_SEAL_002_sysadmin_cannot_bypass_sealed_bid_protection(self) -> None:
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
