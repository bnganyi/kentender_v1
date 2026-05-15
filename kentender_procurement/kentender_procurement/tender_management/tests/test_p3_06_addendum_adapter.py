# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-06 — doc 9 §8.2 addendum impact + regenerate (adapter; revised output refs).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_06_addendum_adapter
"""

from __future__ import annotations

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	analyzeAddendumImpact,
	analyze_addendum_impact,
	regenerateOutputsForAddendum,
	regenerate_outputs_for_addendum,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP306AddendumAdapter(_P401Tm2Cleanup):
	def _cleanup_addenda_for_tm2(self, tm2: str | None) -> None:
		if not tm2 or not frappe.db.exists("TM2 Tender", tm2):
			return
		for ad in frappe.get_all("TM2 Addendum", filters={"tm2_tender": tm2}, pluck="name"):
			for air in frappe.get_all(
				"TM2 Addendum Impact Record",
				filters={"tm2_addendum": ad},
				pluck="name",
			):
				frappe.delete_doc("TM2 Addendum Impact Record", air, force=True, ignore_permissions=True)
			frappe.delete_doc("TM2 Addendum", ad, force=True, ignore_permissions=True)

	def _mk_tm2_si_published_outputs(self) -> tuple[str, str, str]:
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
		tm2 = str(out.get("tm2_tender") or "")
		self.addCleanup(self._cleanup_tm2, tm2)
		self.addCleanup(self._cleanup_addenda_for_tm2, tm2)
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
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			d = fn(si)
			StdInstanceGeneratedOutputService.publish_output(d.name)
		return tcode, si, tm2

	def _mk_addendum(self, tm2: str, *, pit: str = "BOQ Change") -> frappe.Document:
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P3-06 fixture",
				"reason": "Fixture reason for P3-06 adapter tests (non-empty).",
				"status": "Draft",
				"primary_impact_type": pit,
				"affects_deadline": 0,
				"affects_submission_model": 0,
				"affects_opening_model": 0,
				"affects_evaluation_model": 0,
				"affects_contract_model": 0,
				"requires_supplier_acknowledgement": 0,
			}
		)
		ad.flags.ignore_tm2_add_tender_state_gate = True
		ad.insert(ignore_permissions=True)
		return ad

	def test_p3_06_analyze_boq_placeholders_then_regenerate_real_refs(self) -> None:
		_tcode, si, tm2 = self._mk_tm2_si_published_outputs()
		ad = self._mk_addendum(tm2, pit="BOQ Change")
		an = analyze_addendum_impact(ad.addendum_code, {})
		self.assertTrue(an.get("ok"), an)
		self.assertIn("Bundle", an.get("affected_outputs") or [])
		self.assertTrue(str(an.get("revised_bundle_output_code") or "").startswith("REV-PENDING-"))
		prev_b = an.get("previous_bundle_output_code")
		self.assertTrue(prev_b)

		reg = regenerate_outputs_for_addendum(ad.addendum_code)
		self.assertTrue(reg.get("ok"), reg)
		self.assertEqual(reg.get("previous_bundle_output_code"), prev_b)
		self.assertNotEqual(reg.get("revised_bundle_output_code"), prev_b)
		self.assertFalse(str(reg.get("revised_bundle_output_code") or "").startswith("REV-PENDING-"))
		self.assertNotEqual(reg.get("revised_snapshot_hash"), reg.get("previous_snapshot_hash"))

	def test_p3_06_regenerate_without_analyze_uses_primary_impact(self) -> None:
		_tcode, _si, tm2 = self._mk_tm2_si_published_outputs()
		ad = self._mk_addendum(tm2, pit="BOQ Change")
		reg = regenerate_outputs_for_addendum(ad.addendum_code)
		self.assertTrue(reg.get("ok"), reg)
		self.assertIn("Bundle", reg.get("affected_outputs") or [])

	def test_p3_06_no_structural_revised_equals_previous(self) -> None:
		_tcode, _si, tm2 = self._mk_tm2_si_published_outputs()
		ad = self._mk_addendum(tm2, pit="No Structural Impact")
		an = analyze_addendum_impact(ad.addendum_code, {})
		self.assertTrue(an.get("ok"), an)
		self.assertEqual(an.get("affected_outputs"), [])
		self.assertEqual(an.get("revised_bundle_output_code"), an.get("previous_bundle_output_code"))

	def test_p3_06_unknown_addendum_denied(self) -> None:
		out = analyze_addendum_impact("ADD-NONEXISTENT-999999-99", {})
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p3_06_invalid_change_types_denied(self) -> None:
		_tcode, _si, tm2 = self._mk_tm2_si_published_outputs()
		ad = self._mk_addendum(tm2, pit="No Structural Impact")
		bad = analyze_addendum_impact(ad.addendum_code, {"change_types": ["not_a_real_change_type"]})
		self.assertFalse(bad.get("ok"))
		self.assertEqual(bad.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)

	def test_p3_06_camel_case_aliases(self) -> None:
		_tcode, _si, tm2 = self._mk_tm2_si_published_outputs()
		ad = self._mk_addendum(tm2, pit="No Structural Impact")
		c1 = analyzeAddendumImpact(ad.addendum_code, {})
		c2 = analyze_addendum_impact(ad.addendum_code, {})
		self.assertEqual(c1, c2)
		self.assertTrue(c1.get("ok"), c1)
		r1 = regenerateOutputsForAddendum(ad.addendum_code)
		r2 = regenerate_outputs_for_addendum(ad.addendum_code)
		self.assertEqual(r1, r2)
		self.assertTrue(r1.get("ok"), r1)
