# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-05 — doc 9 §8.2 ``create_or_get_publication_snapshot`` (snapshot code + hash).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_05_create_or_get_publication_snapshot
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
	createOrGetPublicationSnapshot,
	create_or_get_publication_snapshot,
	create_or_get_publication_snapshot_for_tm2,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import StdInstanceGeneratedOutputService
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP305CreateOrGetPublicationSnapshot(_P401Tm2Cleanup):
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

	def _publish_all(self, si: str) -> dict[str, str]:
		out: dict[str, str] = {}
		for ot, fn in (
			("Bundle", StdInstanceGeneratedOutputService.generate_bundle),
			("DSM", StdInstanceGeneratedOutputService.generate_dsm),
			("DOM", StdInstanceGeneratedOutputService.generate_dom),
			("DEM", StdInstanceGeneratedOutputService.generate_dem),
			("DCM", StdInstanceGeneratedOutputService.generate_dcm),
		):
			doc = fn(si)
			pub = StdInstanceGeneratedOutputService.publish_output(doc.name)
			out[ot] = pub.name
		return out

	def _assert_ok_envelope(self, snap: dict, tcode: str) -> None:
		self.assertTrue(snap.get("ok"), snap)
		self.assertEqual(snap.get("status"), "CURRENT")
		self.assertEqual(snap.get("publication_snapshot_code"), f"PUBSNAP-{tcode}-TM2")
		sh = str(snap.get("snapshot_hash") or "")
		self.assertEqual(len(sh), 64, sh)
		for k in (
			"bundle_output_hash",
			"dsm_output_hash",
			"dom_output_hash",
			"dem_output_hash",
			"dcm_output_hash",
		):
			self.assertIn(k, snap)
			self.assertTrue(str(snap.get(k) or ""), k)

	def test_p3_05_happy_path_snapshot_code_and_hash(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		self._publish_all(si)
		snap = create_or_get_publication_snapshot(tcode, {})
		self._assert_ok_envelope(snap, tcode)
		self.assertEqual(snap.get("bundle_output_code"), frappe.db.get_value("Tender STD Instance", si, "current_bundle_output_code"))

	def test_p3_05_idempotent_same_hash(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		self._publish_all(si)
		a = create_or_get_publication_snapshot(tcode, None)
		b = create_or_get_publication_snapshot(tcode, {})
		self.assertEqual(a.get("snapshot_hash"), b.get("snapshot_hash"))
		self.assertEqual(a.get("publication_snapshot_code"), b.get("publication_snapshot_code"))

	def test_p3_05_missing_outputs_denied(self) -> None:
		tcode, _si = self._mk_tm2_with_std_instance()
		snap = create_or_get_publication_snapshot(tcode, {})
		self.assertFalse(snap.get("ok"))
		self.assertEqual(snap.get("denial_code"), DenialCode.AUTH_PUBLICATION_SNAPSHOT_MISSING.value)
		self.assertTrue(snap.get("missing_fields"))

	def test_p3_05_output_refs_matching_ok(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		codes = self._publish_all(si)
		refs = {
			"bundle_output_code": codes["Bundle"],
			"dsm_output_code": codes["DSM"],
			"dom_output_code": codes["DOM"],
			"dem_output_code": codes["DEM"],
			"dcm_output_code": codes["DCM"],
		}
		snap = create_or_get_publication_snapshot(tcode, refs)
		self._assert_ok_envelope(snap, tcode)

	def test_p3_05_output_refs_mismatch_denied(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		codes = self._publish_all(si)
		bad_refs = {
			"dem_output_code": codes["DEM"] + "-wrong",
			"bundle_output_code": codes["Bundle"],
		}
		snap = create_or_get_publication_snapshot(tcode, bad_refs)
		self.assertFalse(snap.get("ok"))
		self.assertEqual(snap.get("denial_code"), DenialCode.AUTH_CONTEXT_DENIED.value)
		self.assertEqual(snap.get("mismatched_field"), "dem_output_code")

	def test_p3_05_stub_outputs_hash_empty_but_snapshot_hash_stable(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		frappe.db.set_value(
			"Tender STD Instance",
			si,
			{
				"current_bundle_output_code": f"GB-{tcode}-STUB",
				"current_dsm_output_code": f"DSM-{tcode}-STUB",
				"current_dom_output_code": f"DOM-{tcode}-STUB",
				"current_dem_output_code": f"DEM-{tcode}-STUB",
				"current_dcm_output_code": f"DCM-{tcode}-STUB",
			},
			update_modified=False,
		)
		snap = create_or_get_publication_snapshot(tcode, {})
		self.assertTrue(snap.get("ok"), snap)
		self.assertEqual(snap.get("bundle_output_hash"), "")
		self.assertEqual(len(str(snap.get("snapshot_hash") or "")), 64)
		again = create_or_get_publication_snapshot(tcode, {})
		self.assertEqual(again.get("snapshot_hash"), snap.get("snapshot_hash"))

	def test_p3_05_for_tm2_wrapper_matches(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		self._publish_all(si)
		full = create_or_get_publication_snapshot(tcode, {})
		wrap = create_or_get_publication_snapshot_for_tm2(tcode)
		self.assertEqual(wrap, full)

	def test_p3_05_camel_case_alias_matches(self) -> None:
		tcode, si = self._mk_tm2_with_std_instance()
		self._publish_all(si)
		full = create_or_get_publication_snapshot(tcode, {})
		camel = createOrGetPublicationSnapshot(tcode, {})
		self.assertEqual(camel, full)
