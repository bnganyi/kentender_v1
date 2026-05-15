# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-04 — doc 9 §9.4 ``submit_tender_for_publication_review``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_04_submit_tender_for_publication_review
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP404SubmitTenderForPublicationReview(_P401Tm2Cleanup):
	def _ensure_std_bindable(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)

	def _mk_tm2_with_binding_and_ready_readiness(self) -> str:
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
		self.assertIsNotNone(spec_c)
		self.assertIsNotNone(spec_b)
		self.assertIsNotNone(spec_r)
		assert spec_c is not None and spec_b is not None and spec_r is not None
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
		self.assertEqual(rout.get("readiness_status"), "Ready")
		return tcode

	def test_p4_04_success_status_audit(self) -> None:
		tcode = self._mk_tm2_with_binding_and_ready_readiness()
		spec_s = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		self.assertIsNotNone(spec_s)
		assert spec_s is not None
		out = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_s.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Ready for Publication Review")
		tm2 = out.get("tm2_tender")
		self.assertTrue(tm2)
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "submitted_for_review_by", "submitted_for_review_at"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Ready for Publication Review")
		self.assertEqual(row.get("submitted_for_review_by"), "Administrator")
		self.assertTrue(row.get("submitted_for_review_at"))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Submitted for Publication Review"},
			limit=1,
		)
		self.assertEqual(len(ev), 1)

	def test_p4_04_second_submit_state_denied(self) -> None:
		tcode = self._mk_tm2_with_binding_and_ready_readiness()
		spec_s = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		assert spec_s is not None
		ctx = {"granted_permissions": [spec_s.required_permission]}
		out1 = submit_tender_for_publication_review("Administrator", tcode, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = submit_tender_for_publication_review("Administrator", tcode, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_04_blocked_readiness_denied(self) -> None:
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
		assert spec_c is not None and spec_b is not None and spec_r is not None
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
		rout = run_publication_readiness(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_r.required_permission]},
		)
		self.assertTrue(rout.get("ok"), rout)
		self.assertEqual(rout.get("readiness_status"), "Blocked")

		spec_s = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		assert spec_s is not None
		sout = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_s.required_permission]},
		)
		self.assertFalse(sout.get("ok"))
		self.assertEqual(sout.get("denial_code"), DenialCode.AUTH_STD_NOT_READY.value)

	def test_p4_04_no_readiness_denied(self) -> None:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_b = spec_for_action("TND2_BIND_STD")
		assert spec_c is not None and spec_b is not None
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

		spec_s = spec_for_action("TND2_SUBMIT_PUBLICATION_REVIEW")
		assert spec_s is not None
		sout = submit_tender_for_publication_review(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_s.required_permission]},
		)
		self.assertFalse(sout.get("ok"))
		self.assertEqual(sout.get("denial_code"), DenialCode.AUTH_STD_NOT_READY.value)

	def test_p4_04_auth_denied(self) -> None:
		tcode = self._mk_tm2_with_binding_and_ready_readiness()
		out = submit_tender_for_publication_review("Administrator", tcode, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)
