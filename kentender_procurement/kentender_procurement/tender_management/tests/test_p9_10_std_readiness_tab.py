# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-10 — workbench STD & Readiness tab DTO (doc 9 §17.3, smoke TM2-SMOKE-UI-003).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_10_std_readiness_tab
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.run_publication_readiness import run_publication_readiness
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	get_workbench_tender_detail as get_workbench_tender_detail_service,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP910StdReadinessTab(_P401Tm2Cleanup, IntegrationTestCase):
	def _mk_wizard_tender(self) -> str:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name

		frappe.set_user("Administrator")
		opt = list_new_tender_wizard_std_options_service("Administrator", pc)
		self.assertTrue(opt.get("ok"), opt)
		options = opt.get("options") or []
		self.assertTrue(options, opt)
		first = options[0]
		std_name = str(first.get("std_template") or "").strip()
		ver = str(first.get("template_version_code") or "").strip()
		prof = str(first.get("applicability_profile_code") or "").strip()
		out = submit_new_tender_wizard_completion(
			"Administrator",
			pc,
			std_name,
			ver,
			prof,
			context={},
		)
		self.assertTrue(out.get("ok"), out)
		self.addCleanup(self._cleanup_tm2, out.get("tm2_tender"))
		tcode = str(out.get("tender_code") or "").strip()
		self.assertTrue(tcode)
		return tcode
	def test_p9_10_std_readiness_shape(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		sr = out.get("std_readiness")
		self.assertIsInstance(sr, dict)
		self.assertIn("binding", sr)
		self.assertIn("readiness_meta", sr)
		self.assertIn("readiness_checklist", sr)
		self.assertIn("derived_outputs", sr)
		self.assertIn("dem_missing_block", sr)
		b = sr["binding"]
		for k in (
			"std_template_code",
			"std_template_title",
			"std_template_version_code",
			"tender_std_instance_code",
			"binding_code",
			"publication_snapshot_code",
		):
			self.assertIn(k, b)
		self.assertIsInstance(sr["readiness_checklist"], list)
		self.assertGreaterEqual(len(sr["readiness_checklist"]), 8)
		ids = {row.get("id") for row in sr["readiness_checklist"]}
		self.assertIn("dem_current", ids)
		self.assertIsNone(sr.get("dem_missing_block"))

	def test_p9_10_dem_missing_block_after_readiness_run(self) -> None:
		upsert_std_template()
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
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

		spec_r = spec_for_action("TND2_RUN_READINESS")
		self.assertIsNotNone(spec_r)
		assert spec_r is not None
		rout = run_publication_readiness(
			"Administrator",
			tcode,
			context={"granted_permissions": [spec_r.required_permission]},
		)
		self.assertTrue(rout.get("ok"), rout)

		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		sr = detail.get("std_readiness") or {}
		dem_blk = sr.get("dem_missing_block")
		self.assertIsInstance(dem_blk, dict)
		self.assertEqual(dem_blk.get("blocker_code"), "DEM_MISSING_OR_STALE")
		self.assertIn("Document Evaluation Model", str(dem_blk.get("headline") or ""))
