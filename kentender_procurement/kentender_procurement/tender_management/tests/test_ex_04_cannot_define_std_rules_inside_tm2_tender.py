# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""EX-04 — doc 9 §25 exit gate: **cannot define DSM/DOM/DEM/DCM-owned rules inside TM2 Tender**.

``TM2 Tender`` validate calls ``assert_tm2_tender_no_legacy_rule_injection`` (same canonical
``LEGACY_RULE_INJECTION_KEYS`` / nested ``configuration_json`` scan as **P11-01** on
``Procurement Tender``). Any v1-style manual rule flags → ``AUTH_LEGACY_PATH_DENIED``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_ex_04_cannot_define_std_rules_inside_tm2_tender
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import cstr

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.create_tender_from_package import (
	create_tender_from_package,
)
from kentender_procurement.tender_management.services.std_template_loader import upsert_std_template
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestEx04CannotDefineStdRulesInsideTm2Tender(_P401Tm2Cleanup, IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _mk_draft_tm2(self) -> tuple[str, str]:
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec_c)
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		tm2 = str(out.get("tm2_tender") or "")
		tcode = str(out.get("tender_code") or "")
		self.assertTrue(tm2 and tcode)
		self.addCleanup(self._cleanup_tm2, tm2)
		return tcode, tm2

	def test_EX_04_save_denies_manual_dsm_rule_in_configuration_json(self) -> None:
		_tcode, tm2 = self._mk_draft_tm2()
		doc = frappe.get_doc("TM2 Tender", tm2)
		doc.configuration_json = json.dumps({"section": {"manual_submission_checklist_enabled": True}})
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.save()
		ex = ctx.exception
		msg = str(ex)
		self.assertIn("manual_submission_checklist_enabled", msg)
		self.assertIn("internal rule-injection", msg.lower())

	def test_EX_04_save_allows_empty_configuration_json(self) -> None:
		_tcode, tm2 = self._mk_draft_tm2()
		doc = frappe.get_doc("TM2 Tender", tm2)
		doc.configuration_json = ""
		doc.tender_title = doc.tender_title + " — EX-04 ok"
		doc.save()
		self.assertEqual(cstr(frappe.db.get_value("TM2 Tender", tm2, "configuration_json") or ""), "")
