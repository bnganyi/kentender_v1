# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-03 — doc 9 §9.3 ``run_publication_readiness``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p4_03_run_publication_readiness
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
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP403RunPublicationReadiness(_P401Tm2Cleanup):
	def _ensure_std_bindable(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)

	def _mk_tm2_with_binding(self) -> str:
		self._ensure_std_bindable()
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		spec_b = spec_for_action("TND2_BIND_STD")
		self.assertIsNotNone(spec_c)
		self.assertIsNotNone(spec_b)
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
		return tcode

	def test_p4_03_blocked_row_and_dem_pack_code(self) -> None:
		tcode = self._mk_tm2_with_binding()
		spec_r = spec_for_action("TND2_RUN_READINESS")
		self.assertIsNotNone(spec_r)
		assert spec_r is not None
		out = run_publication_readiness(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_r.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("readiness_status"), "Blocked")
		v = out.get("validate_tender_std_readiness") or {}
		self.assertFalse(v.get("dem_current"))
		codes = [b.get("code") for b in (v.get("blockers") or [])]
		self.assertIn("DEM_MISSING", codes)

		rn = out.get("tm2_publication_readiness")
		self.assertTrue(rn)
		pl = frappe.db.get_value("TM2 Publication Readiness", rn, "validation_payload")
		if isinstance(pl, str):
			pl = json.loads(pl)
		self.assertIn("DEM_MISSING_OR_STALE", pl.get("doc9_pack_codes", []))

		ev = frappe.get_all(
			"TM2 Tender Audit Event",
			filters={"tm2_tender": out.get("tm2_tender"), "event_type": "STD Readiness Validation Run"},
			limit=1,
		)
		self.assertEqual(len(ev), 1)

	def test_p4_03_ready_path_via_adapter_patch(self) -> None:
		tcode = self._mk_tm2_with_binding()
		spec_r = spec_for_action("TND2_RUN_READINESS")
		assert spec_r is not None
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
			out = run_publication_readiness(
				"Administrator",
				tcode,
				context={"granted_permissions": [spec_r.required_permission]},
			)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("readiness_status"), "Ready")
		self.assertEqual(out.get("std_readiness_status"), "Ready")

	def test_p4_03_auth_denied(self) -> None:
		tcode = self._mk_tm2_with_binding()
		out = run_publication_readiness("Administrator", tcode, context={"granted_permissions": []})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_ROLE_DENIED.value)

	def test_p4_03_no_binding_denied(self) -> None:
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
		spec_r = spec_for_action("TND2_RUN_READINESS")
		assert spec_r is not None
		out2 = run_publication_readiness(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_r.required_permission]},
		)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)
