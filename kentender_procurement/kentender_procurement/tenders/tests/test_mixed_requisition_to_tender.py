# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.18 §9.2 / REQ118-AC-001, AC-007, AC-008 — the decisive test with the REAL commands end to end:
100 laptops and 50 monitors receive their own defaults, the package applies without retargeting any row, the
request is submitted and authorised, Tender Preparation starts a Tender from the handoff (version 1.5), and the
Tender draws two goods lines whose technical requirements are each item's own."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as req_cmd
from kentender_procurement.procurement_requisitions.tests import fixtures as req_fx
from kentender_procurement.tenders.services import draft_commands as tender_cmd
from kentender_procurement.tenders.services import serializer
from kentender_procurement.tenders.tests import fixtures as fx


class TestMixedRequisitionToTender(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_all()
		self.addCleanup(frappe.set_user, "Administrator")

	def test_100_laptops_and_50_monitors_keep_their_own_specifications_into_the_tender(self):
		_, item_id = req_fx.active_combined_item()
		requisition = req_fx.prepare(item_id)["requisition"]
		view = req_fx.editor(requisition)
		first, second = view["amounts"][0]["drawdown_line_id"], view["amounts"][1]["drawdown_line_id"]
		req_fx.fill_request_information(requisition)
		req_fx.add_laptops(requisition, quantities={first: 100})
		req_fx.add_laptops(requisition, quantities={second: 50}, item_name="Office monitors", category="Monitor")
		req_fx.enter_estimates(requisition)

		# defaults per kind, applied exactly as shown
		rows = {r["characteristic_key"]: r for g in req_fx.editor(requisition)["requirements"]["technical_groups"] for r in g["rows"]}
		self.assertNotEqual(rows["storage_type"]["applies_to_scope"], "All items")
		self.assertEqual(rows["display_resolution"]["display"], "Full HD")
		req_fx.apply_standard_package(requisition)
		req_fx.send(requisition)
		req_fx.submit_as_hod(requisition)
		authorised = req_fx.authorise(requisition)
		frappe.set_user("Administrator")

		started = tender_cmd.start_tender(handoff=authorised["handoff"], idempotency_key=fx.key(), user=fx.OFFICER)
		frappe.set_user("Administrator")
		handoff = frappe.get_doc("Authorised Requisition Handoff", authorised["handoff"])
		self.assertEqual(handoff.handoff_version, "1.5")
		version = frappe.get_all("Tender Version", filters={"tender": started["tender"]}, fields=["requisition_snapshot_json"], limit=1)[0]
		snapshot = json.loads(version.requisition_snapshot_json)
		items = {i["equipment_category"]: i for i in snapshot["items"]}
		self.assertEqual((items["Laptop"]["quantity"], items["Monitor"]["quantity"]), (100, 50))

		lines = serializer.goods_lines(snapshot)
		self.assertEqual([(l["description"], l["quantity"]) for l in lines], [("Business laptops", "100"), ("Office monitors", "50")])
		technical = {r["technical_requirement_id"]: r for r in snapshot["technical_requirements"]}
		keys = lambda line: {technical[t]["characteristic_key"] for t in line["technical_requirement_ids"]}  # noqa: E731
		self.assertIn("storage_type", keys(lines[0]))
		self.assertNotIn("display_resolution", keys(lines[0]))
		self.assertEqual(keys(lines[1]), {"electrical_compatibility", "new_unused_equipment", "display_resolution", "panel_size"})
		for row in snapshot["technical_requirements"] + snapshot["acceptance_requirements"]:
			self.assertTrue(row["applies_to_item_ids"], "every requirement names the items it covers")
		labels = {r["characteristic_key"]: r["applies_to"] for r in serializer.technical_rows(snapshot)}
		self.assertEqual((labels["storage_type"], labels["display_resolution"], labels["electrical_compatibility"]), ("Business laptops", "Office monitors", "All items"))
