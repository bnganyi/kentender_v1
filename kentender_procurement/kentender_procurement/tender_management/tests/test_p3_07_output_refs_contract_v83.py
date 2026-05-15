# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-07 — doc 9 §8.3 adapter output-reference return contract.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_07_output_refs_contract_v83
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
	STD_ADAPTER_OUTPUT_REFS_V83_KEYS,
	analyze_addendum_impact,
	create_or_get_publication_snapshot,
	extract_std_output_refs_contract_v83,
	getTenderStdOutputRefs,
	get_tender_std_output_refs,
	regenerate_outputs_for_addendum,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP307OutputRefsContractV83(_P401Tm2Cleanup):
	def _mk_bound_tm2_with_published_outputs(self) -> tuple[str, str, str]:
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

	def test_p3_07_v83_key_set_get_tender_std_output_refs(self) -> None:
		tcode, _si, _tm2 = self._mk_bound_tm2_with_published_outputs()
		row = get_tender_std_output_refs(tcode)
		self.assertTrue(row.get("ok"), row)
		keys = frozenset(k for k in row if k != "ok")
		self.assertEqual(keys, frozenset(STD_ADAPTER_OUTPUT_REFS_V83_KEYS))
		self.assertEqual(row.get("status"), "CURRENT")
		self.assertEqual(len(str(row.get("snapshot_hash") or "")), 64)
		self.assertEqual(getTenderStdOutputRefs(tcode), row)

	def test_p3_07_extract_rejects_failed_snapshot(self) -> None:
		with self.assertRaises(frappe.ValidationError):
			extract_std_output_refs_contract_v83({"ok": False})

	def test_p3_07_create_or_get_includes_nested_v83(self) -> None:
		tcode, _si, _tm2 = self._mk_bound_tm2_with_published_outputs()
		snap = create_or_get_publication_snapshot(tcode, {})
		self.assertTrue(snap.get("ok"), snap)
		nested = snap.get("output_refs_contract_v83")
		self.assertIsInstance(nested, dict)
		self.assertEqual(frozenset(nested), frozenset(STD_ADAPTER_OUTPUT_REFS_V83_KEYS))
		self.assertEqual(nested, extract_std_output_refs_contract_v83(snap))

	def test_p3_07_analyze_and_regenerate_include_v83_slices(self) -> None:
		tcode, _si, tm2 = self._mk_bound_tm2_with_published_outputs()
		ad = frappe.get_doc(
			{
				"doctype": "TM2 Addendum",
				"tm2_tender": tm2,
				"title": "P3-07 v83",
				"reason": "Contract slice fixture.",
				"status": "Draft",
				"primary_impact_type": "No Structural Impact",
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
		self.addCleanup(frappe.delete_doc, "TM2 Addendum", ad.name, force=True, ignore_permissions=True)

		an = analyze_addendum_impact(ad.addendum_code, {})
		self.assertTrue(an.get("ok"), an)
		v83 = an.get("output_refs_contract_v83")
		self.assertIsInstance(v83, dict)
		self.assertEqual(frozenset(v83), frozenset(STD_ADAPTER_OUTPUT_REFS_V83_KEYS))

		reg = regenerate_outputs_for_addendum(ad.addendum_code)
		self.assertTrue(reg.get("ok"), reg)
		prev83 = reg.get("previous_output_refs_contract_v83")
		rev83 = reg.get("revised_output_refs_contract_v83")
		self.assertIsInstance(prev83, dict)
		self.assertIsInstance(rev83, dict)
		self.assertEqual(frozenset(prev83), frozenset(STD_ADAPTER_OUTPUT_REFS_V83_KEYS))
		self.assertEqual(frozenset(rev83), frozenset(STD_ADAPTER_OUTPUT_REFS_V83_KEYS))
