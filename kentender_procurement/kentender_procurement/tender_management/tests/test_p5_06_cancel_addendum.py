# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5-06 — doc 4 §12 ``cancel_addendum`` (governed cancel + audit).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p5_06_cancel_addendum
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.cancel_addendum import cancelAddendum, cancel_addendum
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.request_addendum_impact_analysis import (
	request_addendum_impact_analysis,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)
from kentender_procurement.tender_management.tests.test_p5_addendum_fixture import (
	_P5PublishedTenderChainMixin,
)


class TestP506CancelAddendum(_P5PublishedTenderChainMixin, _P401Tm2Cleanup):
	def _cancel_ctx(self) -> dict:
		spec = spec_for_action("ADD2_CANCEL")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def _impact_ctx(self) -> dict:
		spec = spec_for_action("ADD2_REQUEST_IMPACT_ANALYSIS")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_p5_06_success_draft_cancelled_and_audit(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		ac = str(out.get("addendum_code") or "")
		ad_name = str(out.get("addendum") or "")

		can = cancel_addendum(
			"Administrator",
			ac,
			payload={"cancellation_reason": "Duplicate entry; superseded by corrected package."},
			context=self._cancel_ctx(),
		)
		self.assertTrue(can.get("ok"), can)
		ad = frappe.get_doc("TM2 Addendum", ad_name)
		self.assertEqual(ad.status, "Cancelled")
		self.assertIn("Duplicate entry", cstr(ad.cancellation_reason or ""))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Addendum Cancelled"},
			fields=["related_object_id", "event_payload"],
			order_by="creation desc",
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("related_object_id"), ad_name)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertEqual(pl.get("addendum_code"), ac)
		self.assertIn("Duplicate entry", cstr(pl.get("cancellation_reason") or ""))

	def test_p5_06_after_impact_analysis_complete(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertTrue(out.get("ok"), out)
		ac = str(out.get("addendum_code") or "")
		ad_name = str(out.get("addendum") or "")
		for air in frappe.get_all(
			"TM2 Addendum Impact Record",
			filters={"tm2_addendum": ad_name},
			pluck="name",
		):
			frappe.delete_doc("TM2 Addendum Impact Record", air, force=True, ignore_permissions=True)
		ia = request_addendum_impact_analysis("Administrator", ac, context=self._impact_ctx())
		self.assertTrue(ia.get("ok"), ia)

		can = cancel_addendum(
			"Administrator",
			ac,
			payload={"reason": "Legal hold lifted; withdraw addendum before approval."},
			context=self._cancel_ctx(),
		)
		self.assertTrue(can.get("ok"), can)
		self.assertEqual(frappe.db.get_value("TM2 Addendum", ad_name, "status"), "Cancelled")

	def test_p5_06_reason_required(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		ac = str(out.get("addendum_code") or "")
		can = cancel_addendum(
			"Administrator",
			ac,
			payload={"cancellation_reason": "  "},
			context=self._cancel_ctx(),
		)
		self.assertFalse(can.get("ok"))
		self.assertEqual(can.get("denial_code"), DenialCode.AUTH_REASON_REQUIRED.value)

	def test_p5_06_role_denied(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		ac = str(out.get("addendum_code") or "")
		can = cancel_addendum(
			"Administrator",
			ac,
			payload={"cancellation_reason": "x"},
			context={"granted_permissions": []},
		)
		self.assertFalse(can.get("ok"))
		self.assertEqual(can.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p5_06_unknown_addendum_denied(self) -> None:
		can = cancel_addendum(
			"Administrator",
			"ADD-NONEXISTENT-999999-99",
			payload={"cancellation_reason": "x"},
			context=self._cancel_ctx(),
		)
		self.assertFalse(can.get("ok"))
		self.assertEqual(can.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)

	def test_p5_06_issued_denied(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		ac = str(out.get("addendum_code") or "")
		ad_name = str(out.get("addendum") or "")
		frappe.db.set_value(
			"TM2 Addendum",
			ad_name,
			{"status": "Issued"},
			update_modified=False,
		)
		can = cancel_addendum(
			"Administrator",
			ac,
			payload={"cancellation_reason": "Should not apply."},
			context=self._cancel_ctx(),
		)
		self.assertFalse(can.get("ok"))
		self.assertEqual(can.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p5_06_idempotent_cancel_denied(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		ac = str(out.get("addendum_code") or "")
		p = {"cancellation_reason": "Withdrawn by procurement manager."}
		self.assertTrue(cancel_addendum("Administrator", ac, payload=p, context=self._cancel_ctx()).get("ok"))
		second = cancel_addendum("Administrator", ac, payload=p, context=self._cancel_ctx())
		self.assertFalse(second.get("ok"))
		self.assertEqual(second.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p5_06_camel_case_alias(self) -> None:
		tcode, tm2 = self._published_tender()
		self.addCleanup(self._cleanup_p503, tm2)
		out = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		ac = str(out.get("addendum_code") or "")
		self.assertTrue(
			cancelAddendum(
				"Administrator",
				ac,
				payload={"cancellation_reason": "Alias path smoke."},
				context=self._cancel_ctx(),
			).get("ok")
		)
