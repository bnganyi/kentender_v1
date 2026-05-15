# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-05 — doc 9 §9.5 ``approve_tender_publication``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_05_approve_tender_publication
"""

from __future__ import annotations

import json
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
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.submit_tender_for_publication_review import (
	submit_tender_for_publication_review,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


_MGR_EMAIL = "p405-mgr-tm2@test.local"


class TestP405ApproveTenderPublication(_P401Tm2Cleanup):
	def _ensure_std_bindable(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)

	def _ensure_manager_user(self) -> str:
		name = frappe.db.get_value("User", {"email": _MGR_EMAIL}, "name")
		if name:
			frappe.delete_doc("User", name, force=True, ignore_permissions=True)
		elif frappe.db.exists("User", _MGR_EMAIL):
			frappe.delete_doc("User", _MGR_EMAIL, force=True, ignore_permissions=True)
		u = frappe.new_doc("User")
		u.email = _MGR_EMAIL
		u.first_name = "P405"
		u.last_name = "Manager"
		u.user_type = "System User"
		u.enabled = 1
		u.send_welcome_email = 0
		u.insert(ignore_permissions=True)
		frappe.db.set_value("User", u.name, "user_type", "System User")
		self.addCleanup(self._delete_manager_user)
		return u.name

	def _delete_manager_user(self) -> None:
		name = frappe.db.get_value("User", {"email": _MGR_EMAIL}, "name")
		if name:
			frappe.delete_doc("User", name, force=True, ignore_permissions=True)

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

	def test_p4_05_success_independent_approver(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		mgr = self._ensure_manager_user()
		spec_a = spec_for_action("TND2_APPROVE_PUBLICATION")
		self.assertIsNotNone(spec_a)
		assert spec_a is not None
		out = approve_tender_publication(
			mgr,
			tcode,
			comments="Approved under test delegated authority.",
			context={"granted_permissions": [spec_a.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("status"), "Approved for Publication")
		tm2 = out.get("tm2_tender")
		row = frappe.db.get_value(
			"TM2 Tender",
			tm2,
			["status", "approved_for_publication_by", "approved_for_publication_at"],
			as_dict=True,
		)
		self.assertEqual(row.get("status"), "Approved for Publication")
		self.assertEqual(row.get("approved_for_publication_by"), mgr)
		self.assertTrue(row.get("approved_for_publication_at"))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": tm2, "event_type": "Tender Approved for Publication"},
			limit=1,
		)
		self.assertEqual(len(ev), 1)

	def test_p4_05_sod_denied_same_actor_without_override(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		spec_a = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_a is not None
		out = approve_tender_publication(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_a.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_SOD_DENIED.value)

	def test_p4_05_sod_override_allows_administrator(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		spec_a = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_a is not None
		out = approve_tender_publication(
			"Administrator",
			tcode,
			comments=None,
			context={
				"granted_permissions": [spec_a.required_permission],
				"sod_delegated_override_reason": "Delegated AO approval per TM2-SOD-001 test fixture.",
			},
		)
		self.assertTrue(out.get("ok"), out)
		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": out.get("tm2_tender"), "event_type": "Tender Approved for Publication"},
			fields=["event_payload"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		pl = ev[0].get("event_payload") or {}
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertIn("sod_delegated_override_reason", pl)

	def test_p4_05_wrong_status_denied(self) -> None:
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
		spec_a = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_a is not None
		mgr = self._ensure_manager_user()
		aout = approve_tender_publication(
			mgr,
			tcode,
			context={"granted_permissions": [spec_a.required_permission]},
		)
		self.assertFalse(aout.get("ok"))
		self.assertEqual(aout.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)

	def test_p4_05_auth_denied(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		mgr = self._ensure_manager_user()
		out = approve_tender_publication(mgr, tcode, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_05_readiness_no_longer_ready_denied(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		rows = frappe.get_all(
			"TM2 Publication Readiness",
			filters={"tender_code": tcode},
			pluck="name",
			order_by="validation_run_number desc",
			limit=1,
		)
		self.assertTrue(rows)
		pr = rows[0]
		frappe.db.set_value("TM2 Publication Readiness", pr, {"readiness_status": "Blocked"}, update_modified=False)
		spec_a = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_a is not None
		mgr = self._ensure_manager_user()
		out = approve_tender_publication(
			mgr,
			tcode,
			context={"granted_permissions": [spec_a.required_permission]},
		)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_STD_NOT_READY.value)

	def test_p4_05_second_approve_state_denied(self) -> None:
		tcode = self._mk_ready_for_publication_review()
		mgr = self._ensure_manager_user()
		spec_a = spec_for_action("TND2_APPROVE_PUBLICATION")
		assert spec_a is not None
		ctx = {"granted_permissions": [spec_a.required_permission]}
		out1 = approve_tender_publication(mgr, tcode, context=ctx)
		self.assertTrue(out1.get("ok"), out1)
		out2 = approve_tender_publication(mgr, tcode, context=ctx)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.AUTH_STATE_DENIED.value)
