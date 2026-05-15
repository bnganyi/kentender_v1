# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-07 — doc 4 ``return_tender_for_correction`` (TM2).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_07_return_tender_for_correction
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.approve_tender_publication import (
	approve_tender_publication,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.return_tender_for_correction import (
	return_tender_for_correction,
)
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP407ReturnTenderForCorrection(_P401Tm2Cleanup):
	def _ensure_std_bindable(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)

	def _mk_ready_for_publication_review(self) -> str:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_b = spec_for_action("TND2_BIND_STD")
		spec_r = spec_for_action("TND2_RUN_READINESS")
		spec_sub = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		assert spec_c and spec_b and spec_r and spec_sub
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "")
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		bout = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(bout.get("ok"), bout)
		fake = {
			"ok": True,
			"status": "Ready",
			"blockers": [],
			"warnings": [],
			"instance": "STDINST-FAKE",
			"bundle_current": True,
			"dsm_current": True,
			"dom_current": True,
			"dem_current": True,
			"dcm_current": True,
		}
		with patch(
			"kentender_procurement.tender_management.services.run_publication_readiness.validate_tender_std_readiness",
			return_value=fake,
		):
			rout = run_publication_readiness(
				"Administrator",
				tcode,
				context={"granted_permissions": [spec_r.required_permission]},
			)
		self.assertTrue(rout.get("ok"), rout)
		sout = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_sub.required_permission]},
		)
		self.assertTrue(sout.get("ok"), sout)
		self.assertEqual(sout.get("status"), "Ready for Publication Review")
		return tcode

	def _mk_approved_for_publication(self) -> str:
		tcode = self._mk_ready_for_publication_review()
		spec_ap = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_ap is not None
		aout = approve_tender_publication(
			"Administrator",
			tcode,
			context={
				"granted_permissions": [spec_ap.required_permission],
				"sod_delegated_override_reason": "P4-07 fixture — approve then return.",
			},
		)
		self.assertTrue(aout.get("ok"), aout)
		return tcode

	def test_p4_07_success_from_ready_for_review(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		spec_ret = spec_for_action("TND2_RETURN_CORRECTION")
		self.assertIsNotNone(spec_ret)
		assert spec_ret is not None
		reason = "BOQ line items must be reconciled with the latest approved package revision before re-submission."
		out = return_tender_for_correction(
			"Administrator",
			tcode,
			reason,
			context={"granted_permissions": [spec_ret.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Returned for Correction")
		tm2 = out.get("tm2_tender")
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "submitted_for_review_by", "submitted_for_review_at"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Returned for Correction")
		self.assertIsNone(row.get("submitted_for_review_by"))
		self.assertIsNone(row.get("submitted_for_review_at"))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Returned for Correction"},
			fields=["reason", "previous_state", "new_state"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		self.assertEqual(ev[0].get("previous_state"), "Ready for Publication Review")
		self.assertEqual(ev[0].get("new_state"), "Returned for Correction")
		self.assertIn("BOQ", ev[0].get("reason") or "")

	def test_p4_07_success_from_approved_clears_approval_fields(self) -> None:
		tcode = self._mk_approved_for_publication()
		spec_ret = spec_for_action("TND2_RETURN_CORRECTION")
		assert spec_ret is not None
		out = return_tender_for_correction(
			"Administrator",
			tcode,
			"Legal review identified inconsistent evaluation weighting; revise DEM-linked criteria.",
			context={"granted_permissions": [spec_ret.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		tm2 = out.get("tm2_tender")
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			[
				"status",
				"approved_for_publication_by",
				"approved_for_publication_at",
				"submitted_for_review_by",
			],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Returned for Correction")
		self.assertIsNone(row.get("approved_for_publication_by"))
		self.assertIsNone(row.get("approved_for_publication_at"))
		self.assertIsNone(row.get("submitted_for_review_by"))

	def test_p4_07_empty_reason_denied(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		spec_ret = spec_for_action("TND2_RETURN_CORRECTION")
		assert spec_ret is not None
		out = return_tender_for_correction(
			"Administrator",
			tcode,
			"   ",
			context={"granted_permissions": [spec_ret.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_REASON_REQUIRED.value)

	def test_p4_07_wrong_status_denied(self) -> None:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "")
		spec_ret = spec_for_action("TND2_RETURN_CORRECTION")
		assert spec_ret is not None
		rout = return_tender_for_correction(
			"Administrator",
			tcode,
			"Cannot return a draft tender.",
			context={"granted_permissions": [spec_ret.required_permission]},
		)
		self.assertFalse(rout.get("ok"))
		self.assertEqual(rout.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_07_auth_denied(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		out = return_tender_for_correction(
			"Administrator",
			tcode,
			"Missing permission path.",
			context={"granted_permissions": []},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_07_second_return_denied(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		spec_ret = spec_for_action("TND2_RETURN_CORRECTION")
		assert spec_ret is not None
		ctx = {"granted_permissions": [spec_ret.required_permission]}
		out1 = return_tender_for_correction("Administrator", tcode, "First return: fix bundle references.", context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = return_tender_for_correction("Administrator", tcode, "Second return should fail same state.", context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)
