# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-08 — workbench tender detail + action availability + publish whitelist (doc 9 §16).

Doc 9 §25 **EX-17** (exit gate): workbench **detail DTO** carries all doc §17.1 tab payloads + §16.3
``actions`` (not raw DocType workflow) — ``test_EX_17_*``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_08_workbench_tender_detail
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import (
	execute_workbench_tender_publish,
	get_workbench_tender_action_availability,
	get_workbench_tender_detail,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	get_workbench_tender_detail as get_workbench_tender_detail_service,
)
from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP908WorkbenchTenderDetail(_P401Tm2Cleanup, IntegrationTestCase):
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

	def test_EX_17_workbench_detail_carries_pack_section_17_1_tabs_and_action_bar(self) -> None:
		"""Doc 9 §25 / §17.1 + §16.3 — canonical workbench surface (tabs + actions), not DocType form."""
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		for key in (
			"overview",
			"std_readiness",
			"timeline_tab",
			"supplier_access_tab",
			"clarifications_tab",
			"addenda_tab",
			"submissions_tab",
			"opening_readiness_tab",
			"evaluation_handoff_tab",
			"contract_handoff_tab",
			"audit_evidence_tab",
			"actions",
		):
			self.assertIn(key, out, f"missing workbench detail key: {key}")
			self.assertIsInstance(out[key], (dict, list), f"bad type for {key}: {type(out[key])!r}")
		self.assertIsInstance(out["actions"], list)
		self.assertGreater(len(out["actions"]), 0)
		for tab_key in (
			"overview",
			"std_readiness",
			"timeline_tab",
			"supplier_access_tab",
			"clarifications_tab",
			"addenda_tab",
			"submissions_tab",
			"opening_readiness_tab",
			"evaluation_handoff_tab",
			"contract_handoff_tab",
			"audit_evidence_tab",
		):
			self.assertIsInstance(out[tab_key], dict, tab_key)

	def test_p9_08_not_found(self) -> None:
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", "__no_such_tender__")
		self.assertFalse(out.get("ok"))

	def test_p9_08_detail_shape_and_actions(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("tender_code"), tcode)
		self.assertTrue(out.get("tender_title"))
		self.assertTrue(out.get("tender_status"))
		self.assertIsInstance(out.get("header_lines"), list)
		self.assertGreaterEqual(len(out.get("header_lines") or []), 3)
		self.assertIsInstance(out.get("state_cards"), list)
		self.assertGreaterEqual(len(out.get("state_cards") or []), 3)
		actions = out.get("actions") or []
		self.assertTrue(actions)
		codes = {a.get("action_code") for a in actions}
		self.assertIn("TND2_PUBLISH", codes)
		self.assertIn("TND2_VIEW", codes)
		for a in actions:
			self.assertIn(a.get("ui_state"), ("enabled", "disabled"))
			self.assertIn("availability", a)
		self.assertIsInstance(out.get("overview"), dict)

	def test_p9_08_whitelist_detail_matches_service(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		api = get_workbench_tender_detail(tcode)
		svc = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertEqual(api.get("ok"), svc.get("ok"))
		self.assertEqual(api.get("tender_code"), svc.get("tender_code"))

	def test_p9_08_single_action_availability(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_action_availability(tcode, "TND2_VIEW")
		self.assertTrue(out.get("ok"), out)
		self.assertIn("availability", out)

	def test_p9_08_publish_execute_denied_when_not_approved(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		pub = execute_workbench_tender_publish(tcode)
		self.assertFalse(pub.get("ok"), pub)
