# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-14 — workbench Addenda tab DTO (doc 9 §17.7, doc 6 §20).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_14_addenda_tab
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.create_addendum import create_addendum
from kentender_procurement.tender_management.services.request_addendum_impact_analysis import (
	request_addendum_impact_analysis,
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
from kentender_procurement.tender_management.tests.test_p5_addendum_fixture import (
	_P5PublishedTenderChainMixin,
)


class TestP914AddendaTabShape(_P401Tm2Cleanup, IntegrationTestCase):
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

	def test_p9_14_addenda_tab_shape(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(out.get("ok"), out)
		tab = out.get("addenda_tab")
		self.assertIsInstance(tab, dict)
		self.assertIn("rows", tab)
		self.assertIn("status_counts", tab)
		self.assertIn("status_filter_order", tab)
		self.assertIn("read_only_notice", tab)
		self.assertIsInstance(tab["rows"], list)
		self.assertIsInstance(tab["status_filter_order"], list)
		self.assertIsInstance(tab["status_counts"], dict)


class TestP914AddendaTabOutputTransitions(_P5PublishedTenderChainMixin, _P401Tm2Cleanup, IntegrationTestCase):
	def _impact_ctx(self) -> dict:
		spec = spec_for_action("ADD2_REQUEST_IMPACT_ANALYSIS")
		self.assertIsNotNone(spec)
		assert spec is not None
		return {"granted_permissions": [spec.required_permission]}

	def test_p9_14_addenda_output_transitions_from_impact_record(self) -> None:
		"""Doc 6 §20.5 — previous vs revised output refs surface on workbench addenda tab."""
		tcode, _tm2 = self._published_tender()
		ca = create_addendum(
			"Administrator",
			tcode,
			payload=self._base_payload(),
			context=self._add_ctx(),
		)
		self.assertTrue(ca.get("ok"), ca)
		ac = str(ca.get("addendum_code") or "").strip()
		self.assertTrue(ac)
		ria = request_addendum_impact_analysis("Administrator", ac, context=self._impact_ctx())
		self.assertTrue(ria.get("ok"), ria)
		air_name = str(ria.get("impact_record") or "").strip()
		self.assertTrue(air_name)
		frappe.db.set_value(
			"TM2 Addendum Impact Record",
			air_name,
			{
				"previous_bundle_output_code": "GB-FIXTURE-V1",
				"revised_bundle_output_code": "GB-FIXTURE-V2",
				"previous_dsm_output_code": "DSM-FIXTURE-V1",
				"revised_dsm_output_code": "DSM-FIXTURE-V2",
			},
			update_modified=False,
		)
		frappe.set_user("Administrator")
		detail = get_workbench_tender_detail_service("Administrator", tcode)
		self.assertTrue(detail.get("ok"), detail)
		tab = detail.get("addenda_tab") or {}
		rows = tab.get("rows") or []
		self.assertEqual(len(rows), 1)
		trans = rows[0].get("output_transitions") or []
		by_key = {t.get("output_key"): t for t in trans}
		self.assertIn("bundle", by_key)
		self.assertEqual(by_key["bundle"].get("previous_code"), "GB-FIXTURE-V1")
		self.assertEqual(by_key["bundle"].get("revised_code"), "GB-FIXTURE-V2")
		self.assertIn("→", str(by_key["bundle"].get("arrow_display") or ""))
		self.assertIn("dsm", by_key)
