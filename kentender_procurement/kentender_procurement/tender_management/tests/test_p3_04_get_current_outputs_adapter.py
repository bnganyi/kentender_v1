# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-04 — doc 9 §8.2 ``get_current_*`` ×5 (adapter; missing / stale detectable).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_04_get_current_outputs_adapter
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	getCurrentDem,
	get_current_bundle,
	get_current_dcm,
	get_current_dem,
	get_current_dom,
	get_current_dsm,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP304GetCurrentOutputsAdapter(_P401Tm2Cleanup):
	def _mk_tm2_with_std_instance(self) -> tuple[str, str]:
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
		si = str(bout.get("tender_std_instance") or "")
		self.assertTrue(si)
		return tcode, si

	def _assert_missing_envelope(self, row: dict) -> None:
		self.assertFalse(row.get("ok"))
		self.assertTrue(row.get("missing"))
		self.assertFalse(row.get("stale_or_invalid"))
		self.assertIn("reason", row)

	def test_p3_04_empty_code_all_missing(self) -> None:
		for fn in (
			get_current_bundle,
			get_current_dsm,
			get_current_dom,
			get_current_dem,
			get_current_dcm,
		):
			with self.subTest(fn=fn.__name__):
				self._assert_missing_envelope(fn(""))

	def test_p3_04_unknown_instance_missing(self) -> None:
		out = get_current_dsm("STDINST-NONEXISTENT-P304-99999")
		self._assert_missing_envelope(out)
		self.assertEqual(out.get("reason"), "INSTANCE_NOT_FOUND")

	def test_p3_04_bound_tm2_missing_outputs_detectable(self) -> None:
		_, si = self._mk_tm2_with_std_instance()
		for fn, ot in (
			(get_current_bundle, "Bundle"),
			(get_current_dsm, "DSM"),
			(get_current_dom, "DOM"),
			(get_current_dem, "DEM"),
			(get_current_dcm, "DCM"),
		):
			with self.subTest(output=ot):
				row = fn(si)
				self.assertFalse(row.get("ok"), row)
				self.assertTrue(row.get("missing"), row)
				self.assertEqual(row.get("reason"), "OUTPUT_NOT_LINKED")

	def test_p3_04_ok_after_publish_dem(self) -> None:
		_, si = self._mk_tm2_with_std_instance()
		d = StdInstanceGeneratedOutputService.generate_dem(si)
		pub = StdInstanceGeneratedOutputService.publish_output(d.name)
		out = get_current_dem(si)
		self.assertTrue(out.get("ok"), out)
		self.assertFalse(out.get("missing"))
		self.assertFalse(out.get("stale_or_invalid"))
		self.assertEqual(out.get("output_code"), pub.name)
		camel = getCurrentDem(si)
		self.assertEqual(camel, out)

	def test_p3_04_non_consumable_status_detectable(self) -> None:
		_, si = self._mk_tm2_with_std_instance()
		d = StdInstanceGeneratedOutputService.generate_dem(si)
		frappe.db.set_value("Tender STD Instance", si, "current_dem_output_code", d.name)
		out = get_current_dem(si)
		self.assertFalse(out.get("ok"))
		self.assertFalse(out.get("missing"))
		self.assertTrue(out.get("stale_or_invalid"))
		self.assertEqual(out.get("reason"), "OUTPUT_NOT_CONSUMABLE")
