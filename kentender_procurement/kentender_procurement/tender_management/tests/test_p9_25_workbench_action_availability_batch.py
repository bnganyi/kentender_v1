# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P9-25 — doc 9 §19.3 action availability (single POST + batch; §7.3 per availability).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_p9_25_workbench_action_availability_batch
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.api.tm2_workbench import (
	batch_workbench_tender_action_availability,
	post_tm2_action_availability,
)
from kentender_procurement.tender_management.security.action_availability.service import (
	pack_action_availability_v73_errors,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.tm2_workbench_tender_detail import (
	post_section_19_3_tm2_action_availability,
	resolve_section_19_3_object_type,
)
from kentender_procurement.tender_management.services.tm2_workbench_wizard import (
	list_new_tender_wizard_std_options as list_new_tender_wizard_std_options_service,
	submit_new_tender_wizard_completion,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


class TestP925WorkbenchActionAvailabilityBatch(_P401Tm2Cleanup, IntegrationTestCase):
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

	def test_p9_25_resolve_object_type_tender_alias(self) -> None:
		self.assertEqual(resolve_section_19_3_object_type("Tender"), "TM2 Tender")
		self.assertEqual(resolve_section_19_3_object_type("tender"), "TM2 Tender")
		self.assertEqual(resolve_section_19_3_object_type(""), "TM2 Tender")
		self.assertEqual(resolve_section_19_3_object_type("OtherThing"), "OtherThing")

	def test_p9_25_post_section_19_3_unsupported_object_type(self) -> None:
		frappe.set_user("Administrator")
		out = post_section_19_3_tm2_action_availability(
			"Administrator",
			"TND2_VIEW",
			"ANY-CODE",
			object_type="NotATm2Type",
		)
		self.assertFalse(out.get("ok"), out)

	def test_p9_25_whitelist_post_payload_and_discrete_override(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		payload = json.dumps(
			{
				"action_code": "TND2_VIEW",
				"object_type": "Tender",
				"object_code": tcode,
				"context": {"p9_25_probe": "from_payload"},
			}
		)
		out1 = post_tm2_action_availability(payload=payload)
		self.assertTrue(out1.get("ok"), out1)
		avail1 = out1.get("availability") or {}
		self.assertEqual(avail1.get("object_type"), "TM2 Tender")
		self.assertEqual(avail1.get("object_code"), tcode)
		self.assertEqual(pack_action_availability_v73_errors(avail1), [])

		out2 = post_tm2_action_availability(
			payload=payload,
			action_code="TND2_PUBLISH",
			object_code=tcode,
			object_type="Tender",
		)
		self.assertTrue(out2.get("ok"), out2)
		avail2 = out2.get("availability") or {}
		self.assertEqual(avail2.get("action_code"), "TND2_PUBLISH")
		self.assertEqual(pack_action_availability_v73_errors(avail2), [])

	def test_p9_25_batch_mixed_known_and_unknown_codes(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		codes = json.dumps(["TND2_VIEW", "NOT_A_REAL_TM2_ACTION_CODE_XYZ"])
		out = batch_workbench_tender_action_availability(
			tender_code=tcode,
			action_codes=codes,
			context=json.dumps({"batch_ctx": 1}),
		)
		self.assertTrue(out.get("ok"), out)
		self.assertEqual(out.get("object_type"), "TM2 Tender")
		self.assertEqual(out.get("tender_code"), tcode)
		items = out.get("items") or []
		self.assertEqual(len(items), 2)
		by_code = {i.get("action_code"): i.get("availability") or {} for i in items}
		self.assertEqual(pack_action_availability_v73_errors(by_code["TND2_VIEW"]), [])
		self.assertFalse(by_code["NOT_A_REAL_TM2_ACTION_CODE_XYZ"].get("allowed"))
		self.assertEqual(
			pack_action_availability_v73_errors(by_code["NOT_A_REAL_TM2_ACTION_CODE_XYZ"]),
			[],
		)

	def test_p9_25_batch_empty_codes_error(self) -> None:
		tcode = self._mk_wizard_tender()
		frappe.set_user("Administrator")
		out = batch_workbench_tender_action_availability(tender_code=tcode, action_codes="[]")
		self.assertFalse(out.get("ok"), out)
