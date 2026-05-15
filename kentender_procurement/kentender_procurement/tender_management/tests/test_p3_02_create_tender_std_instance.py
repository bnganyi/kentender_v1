# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-02 — doc 9 §8.2 ``create_tender_std_instance`` (adapter; instance code persisted).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p3_02_create_tender_std_instance
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import TEMPLATE_CODE, upsert_std_template
from kentender_procurement.tender_management.services.tm2_std_adapter import (
	createTenderStdInstance,
	create_tender_std_instance,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_CREATED
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP302CreateTenderStdInstance(_P401Tm2Cleanup):
	def _mk_draft_tm2(self) -> tuple[str, str]:
		"""Return ``(tm2_tender_name, tender_code)``."""
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
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		tm2_name = str(out.get("tm2_tender") or "")
		tcode = str(out.get("tender_code") or "")
		self.assertTrue(tm2_name and tcode)
		self.addCleanup(self._cleanup_tm2, tm2_name)
		return tm2_name, tcode

	def test_p3_02_success_persists_instance_code_and_binding_fields(self) -> None:
		tm2_name, tcode = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out = create_tender_std_instance(tcode, ver, prof)
		self.assertTrue(out.get("ok"), out)
		code = str(out.get("tender_std_instance_code") or out.get("tender_std_instance") or "")
		self.assertTrue(code)
		self.assertTrue(frappe.db.exists("Tender STD Instance", code))
		row = frappe.db.get_value(
			"Tender STD Instance",
			code,
			[
				"name",
				"tm2_tender",
				"template_version_code",
				"applicability_profile_code",
				"instance_status",
				"readiness_status",
				"created_from_tender_context",
			],
			as_dict=True,
		)
		self.assertIsNotNone(row)
		assert row is not None
		self.assertEqual(row.get("name"), code)
		self.assertTrue(str(row.get("name") or "").startswith("STDINST-"))
		self.assertEqual(row.get("tm2_tender"), tm2_name)
		self.assertEqual(str(row.get("template_version_code") or "").strip(), ver)
		self.assertEqual(str(row.get("applicability_profile_code") or "").strip().lower(), prof.lower())
		self.assertEqual(row.get("instance_status"), "Draft")
		self.assertEqual(row.get("readiness_status"), "Not Ready")
		self.assertEqual(int(row.get("created_from_tender_context") or 0), 1)

	def test_p3_02_camel_case_alias_matches(self) -> None:
		_tm2a, tcode_a = self._mk_draft_tm2()
		_tm2b, tcode_b = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		a = create_tender_std_instance(tcode_a, ver, prof)
		b = createTenderStdInstance(tcode_b, ver, prof)
		self.assertTrue(a.get("ok"), a)
		self.assertTrue(b.get("ok"), b)
		self.assertEqual(set(a.keys()), set(b.keys()))

	def test_p3_02_missing_parameters_denied(self) -> None:
		_, tcode = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out = create_tender_std_instance("", ver, prof)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_TENDER_CONTEXT_REQUIRED.value)
		out2 = create_tender_std_instance(tcode, "", prof)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.STD_AUTH_TENDER_CONTEXT_REQUIRED.value)
		out3 = create_tender_std_instance(tcode, ver, "  ")
		self.assertFalse(out3.get("ok"))
		self.assertEqual(out3.get("denial_code"), DenialCode.STD_AUTH_TENDER_CONTEXT_REQUIRED.value)

	def test_p3_02_unknown_tender_denied(self) -> None:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out = create_tender_std_instance("TND-NONEXISTENT-P302-9999", ver, prof)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value)

	def test_p3_02_template_version_profile_mismatch_denied(self) -> None:
		_, tcode = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out = create_tender_std_instance(tcode, ver, f"{prof}-wrong")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_TEMPLATE_INCOMPATIBLE.value)

	def test_p3_02_second_active_instance_denied(self) -> None:
		_, tcode = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out1 = create_tender_std_instance(tcode, ver, prof)
		self.assertTrue(out1.get("ok"), out1)
		out2 = create_tender_std_instance(tcode, ver, prof)
		self.assertFalse(out2.get("ok"))
		self.assertEqual(out2.get("denial_code"), DenialCode.STD_AUTH_ACTIVE_VERSION_LOCKED.value)

	def test_p3_02_governance_not_eligible_denied(self) -> None:
		_, tcode = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		prev = frappe.db.get_value(
			"STD Template",
			TEMPLATE_CODE,
			["allowed_for_tender_creation", "lifecycle_status"],
			as_dict=True,
		)

		def _restore_std() -> None:
			if prev:
				frappe.db.set_value("STD Template", TEMPLATE_CODE, prev)

		self.addCleanup(_restore_std)
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 0, "lifecycle_status": "Suspended"},
		)
		out = create_tender_std_instance(tcode, ver, prof)
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("denial_code"), DenialCode.STD_TEMPLATE_NOT_ACTIVE.value)
		self.assertIn("eligibility", out)

	def test_p3_02_emits_std_instance_created_audit(self) -> None:
		tm2_name, tcode = self._mk_draft_tm2()
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		out = create_tender_std_instance(tcode, ver, prof)
		self.assertTrue(out.get("ok"), out)
		code = str(out.get("tender_std_instance_code") or "")
		ev = frappe.get_all(
			"Audit Event",
			filters={"document_type": "Tender STD Instance", "document_name": code, "event_type": EVT_STDINST_CREATED},
			fields=["name", "metadata"],
			limit=1,
		)
		self.assertEqual(len(ev), 1)
		meta = ev[0].get("metadata")
		if isinstance(meta, str):
			meta = json.loads(meta)
		self.assertIsInstance(meta, dict)
		details = (meta or {}).get("details") or {}
		if isinstance(details, str):
			details = json.loads(details)
		self.assertEqual(details.get("tm2_tender"), tm2_name)
		self.assertEqual(details.get("template_version_code"), ver)
