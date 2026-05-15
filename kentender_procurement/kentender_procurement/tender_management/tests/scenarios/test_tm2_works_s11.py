# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12-01 / doc 7 §2 — TM2-WORKS-S11 (Sealed Bid Access Denial).

**§2:** internal desk actors must not read sealed bid content before lawful opening —
``get_bid_content`` → ``AUTH_SEALED_BID_DENIED`` + **TM2 Tender Audit Event** **Access Denied**
(doc 9 §11.7 **P6-07**; doc 8 **TM2-SMOKE-SEAL-001** / **TM2-SMOKE-SEAL-002** / **EX-11**).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.scenarios.test_tm2_works_s11
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
from kentender_procurement.tender_management.services.get_bid_content import get_bid_content
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_bid import submit_bid
from kentender_procurement.tender_management.tests.p6_published_tm2_fixture import P6PublishedTm2Fixture
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p6_05_submit_bid import _valid_bid_for_fixture

_CODE = "TM2-WORKS-S11"

_S11_PO_EMAIL = "s11-works-po001@example.test"


class TestTM2WorksS11Catalog(unittest.TestCase):
	def test_scenario_registered_in_catalog(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(spec.code, _CODE)
		self.assertEqual(spec.name, "Sealed Bid Access Denial")
		self.assertTrue(spec.purpose)
		self.assertTrue(spec.expected_result)

	def test_tracker_slug_matches_row_s_table(self) -> None:
		spec = scenario_by_code(_CODE)
		self.assertEqual(scenario_tracker_slug(spec), f"S-{int(_CODE.split('S')[-1]):02d}")


class TestTM2WorksS11SealedBidAccess(_P401Tm2Cleanup, P6PublishedTm2Fixture):
	"""Doc 7 §2 — TM2-WORKS-S11 (tracker **S-11**). Mirrors ``test_EX_11_*`` in ``test_p6_07_get_bid_content``."""

	p6_supplier_fixture_prefix = "S11"

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
		self.assertTrue(si)
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

	def _ensure_procurement_officer(self) -> None:
		self._ensure_role("Procurement Officer")
		if not frappe.db.exists("User", _S11_PO_EMAIL):
			u = frappe.new_doc("User")
			u.email = _S11_PO_EMAIL
			u.first_name = "S11"
			u.last_name = "PO001"
			u.user_type = "System User"
			u.enabled = 1
			u.new_password = "Test@1234"
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
		frappe.get_doc("User", _S11_PO_EMAIL).add_roles("Procurement Officer")

	def _cleanup_procurement_officer(self) -> None:
		if frappe.db.exists("User", _S11_PO_EMAIL):
			frappe.delete_doc("User", _S11_PO_EMAIL, force=True, ignore_permissions=True)

	def _assert_sealed_denial_audited(self, actor: str, tm2: str, bid_code: str) -> None:
		aud_before = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Access Denied",
				"denial_code": DenialCode.AUTH_SEALED_BID_DENIED.value,
				"related_object_id": bid_code,
			},
			pluck="name",
		)
		out = get_bid_content(actor, bid_code, context={})
		self.assertFalse(out.get("ok"), out)
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SEALED_BID_DENIED.value)
		aud_after = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={
				"tm2_tender": tm2,
				"event_type": "Access Denied",
				"denial_code": DenialCode.AUTH_SEALED_BID_DENIED.value,
				"related_object_id": bid_code,
			},
			pluck="name",
		)
		self.assertEqual(len(aud_after), len(aud_before) + 1)

	def test_S_11_procurement_officer_denied_sealed_bid_pre_opening_with_audit(self) -> None:
		"""Doc 8 **USER-PO-001** / **TM2-SMOKE-SEAL-001** — desk ``get_bid_content`` denied + **Access Denied**."""
		self._ensure_procurement_officer()
		self.addCleanup(self._cleanup_procurement_officer)
		_tcode, tm2, _sup, bc = self._submit_sealed_bid()
		self._assert_sealed_denial_audited(_S11_PO_EMAIL, tm2, bc)

	def test_S_11_administrator_denied_sealed_bid_pre_opening_with_audit(self) -> None:
		"""Doc 8 **USER-SYSADMIN-001** / **TM2-SMOKE-SEAL-002** — Administrator cannot bypass seal pre-opening."""
		_tcode, tm2, _sup, bc = self._submit_sealed_bid()
		self._assert_sealed_denial_audited("Administrator", tm2, bc)
