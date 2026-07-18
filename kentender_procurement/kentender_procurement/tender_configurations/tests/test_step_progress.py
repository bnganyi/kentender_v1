# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Exit-condition step progress + overall average."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.seed.ui00_seed import seed_ui00_dashboard
from kentender_procurement.tender_configurations.services.configuration_home import (
	get_configuration_home,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_IN_PROGRESS,
	STEP_NOT_AVAILABLE,
	STEP_NOT_STARTED,
	get_steps_for_family,
	merge_step_rows,
)
from kentender_procurement.tender_configurations.services.profile import (
	LOT_MULTIPLE,
	LOT_SINGLE,
	save_configuration_profile,
)
from kentender_procurement.tender_configurations.services.step_progress import (
	compute_step_progress,
	evaluate_conditions,
	overall_progress_pct,
)


class TestStepProgress(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.seed = seed_ui00_dashboard(clear=True)
		self.cfg_id = self.seed["configurations"][0]

	def test_evaluate_conditions_pct(self):
		out = evaluate_conditions(
			[
				{"key": "a", "label": "A", "met": True},
				{"key": "b", "label": "B", "met": True},
				{"key": "c", "label": "C", "met": False},
			]
		)
		self.assertEqual(out["met_count"], 2)
		self.assertEqual(out["required_count"], 3)
		self.assertEqual(out["progress_pct"], 67)

	def test_status_fallback_complete_vs_in_progress(self):
		# Unregistered steps still use status fallback (CFG-04 has no field builder yet).
		done = compute_step_progress("CFG-04", status_label=STEP_COMPLETE, doc=None)
		self.assertEqual(done["progress_pct"], 100)
		self.assertFalse(done["show_progress_bar"])

		wip = compute_step_progress("CFG-04", status_label=STEP_IN_PROGRESS, doc=None)
		self.assertEqual(wip["progress_pct"], 0)
		self.assertTrue(wip["show_progress_bar"])

		na = compute_step_progress("CFG-09", status_label=STEP_NOT_AVAILABLE, doc=None)
		self.assertEqual(na["progress_pct"], 0)
		self.assertFalse(na["show_progress_bar"])

	def test_cfg01_partial_and_complete(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		# Clear profile fields for a clean checklist
		doc.tender_title = ""
		doc.short_scope_summary = ""
		doc.lot_structure = ""
		doc.lots = "[]"
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)

		partial = compute_step_progress(
			"CFG-01", status_label=STEP_IN_PROGRESS, doc=doc, step_state={}
		)
		# STD family + document usually present from seed; title/scope/lot unmet
		self.assertGreaterEqual(partial["required_count"], 5)
		self.assertLess(partial["progress_pct"], 100)
		self.assertTrue(partial["show_progress_bar"])

		out = save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_SINGLE,
				"lots": [],
			},
		)
		self.assertTrue(out["can_continue"])
		doc.reload()
		done = compute_step_progress("CFG-01", status_label=STEP_COMPLETE, doc=doc)
		self.assertEqual(done["progress_pct"], 100)

	def test_cfg02_partial_and_complete(self):
		from kentender_procurement.tender_configurations.services.tds import (
			save_configuration_tds,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_tds_api import (
			_complete_tds_payload,
		)

		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		doc.tds_values = "{}"
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)

		partial = compute_step_progress(
			"CFG-02", status_label=STEP_IN_PROGRESS, doc=doc, step_state={}
		)
		self.assertGreaterEqual(partial["required_count"], 15)
		self.assertEqual(partial["progress_pct"], 0)

		out = save_configuration_tds(
			self.cfg_id, {"tds_values": _complete_tds_payload()}
		)
		self.assertTrue(out["can_continue"])
		doc.reload()
		done = compute_step_progress("CFG-02", status_label=STEP_COMPLETE, doc=doc)
		self.assertEqual(done["progress_pct"], 100)

	def test_cfg03_partial_and_complete(self):
		from kentender_procurement.tender_configurations.services.it_requirements import (
			save_configuration_requirements,
		)
		from kentender_procurement.tender_configurations.tests.test_configuration_it_requirements_api import (
			_complete_requirement,
		)

		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		doc.it_requirements = "[]"
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)

		partial = compute_step_progress(
			"CFG-03", status_label=STEP_IN_PROGRESS, doc=doc, step_state={}
		)
		self.assertGreaterEqual(partial["required_count"], 1)
		self.assertEqual(partial["progress_pct"], 0)

		out = save_configuration_requirements(
			self.cfg_id, {"requirements": [_complete_requirement()]}
		)
		self.assertTrue(out["can_continue"])
		doc.reload()
		done = compute_step_progress("CFG-03", status_label=STEP_COMPLETE, doc=doc)
		self.assertEqual(done["progress_pct"], 100)

	def test_cfg01_multiple_lots_adds_condition(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_MULTIPLE,
				"lots": [],
			},
		)
		doc.reload()
		wip = compute_step_progress("CFG-01", status_label=STEP_IN_PROGRESS, doc=doc)
		keys = {c["key"] for c in wip["conditions"]}
		self.assertIn("lots", keys)
		self.assertLess(wip["progress_pct"], 100)

	def test_overall_is_average_of_step_pcts(self):
		rows = [
			{"progress_pct": 100},
			{"progress_pct": 100},
			{"progress_pct": 0},
			{"progress_pct": 60},
			{"progress_pct": 0},
		]
		# (100+100+0+60+0)/5 = 52
		self.assertEqual(overall_progress_pct(rows), 52)

	def test_home_payload_includes_overall_progress(self):
		save_configuration_profile(
			self.cfg_id,
			{
				"tender_title": "ERP Implementation Services",
				"short_scope_summary": (
					"Procurement of ERP software licences, implementation, training, "
					"and support for national treasury systems."
				),
				"lot_structure": LOT_SINGLE,
			},
		)
		home = get_configuration_home(self.cfg_id)
		self.assertIn("overall_progress", home)
		op = home["overall_progress"]
		self.assertIn("progress_pct", op)
		self.assertEqual(op["total"], 9)
		steps = home["configuration_steps"]
		self.assertEqual(len(steps), 9)
		cfg01 = next(s for s in steps if s["id"] == "CFG-01")
		self.assertEqual(cfg01["progress_pct"], 100)
		# Average of live step percents matches API
		self.assertEqual(op["progress_pct"], overall_progress_pct(steps))

	def test_merge_never_defaults_to_sixty_seven(self):
		catalog = get_steps_for_family("IT")
		rows = merge_step_rows(
			catalog,
			{"CFG-04": {"status_label": STEP_IN_PROGRESS}},
			doc=None,
		)
		cfg04 = next(r for r in rows if r["id"] == "CFG-04")
		self.assertEqual(cfg04["progress_pct"], 0)
		self.assertNotEqual(cfg04["progress_pct"], 67)
		self.assertEqual(
			next(r for r in rows if r["id"] == "CFG-05")["status_label"],
			STEP_NOT_STARTED,
		)
