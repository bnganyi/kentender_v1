# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §7.5/§9 — the canonical serializer against a real
Version: grouped goods lines with lineage (D10, TPR-AC-007/012), one typed
response / evaluation / contract mapping per technical requirement
(TPR-AC-014/015/016), supplier placeholders only in the price schedule
(TPR-AC-013), the render context shape and the internal-only boundary
(TPR-AC-044), and digests (SMOKE-04)."""

from __future__ import annotations

import json

import frappe

from kentender_procurement.tender_preparation.services import digest, serializer
from kentender_procurement.tender_preparation.services import snapshot as snap
from kentender_procurement.tender_preparation.tests import fixtures as fx
from kentender_procurement.tender_preparation.tests.base import TenderCase
from kentender_procurement.tender_templates import loader


class TestSerializer(TenderCase):
	def _version(self):
		prep = fx.prepared()
		fx.complete_draft(prep["tender"])
		root = frappe.get_doc("Prepared Tender", prep["tender"])
		version = frappe.get_doc("Tender Preparation Version", prep["tender_version"])
		return root, version, snap.load(version)

	def test_goods_lines_group_items_sharing_one_specification_and_keep_every_id(self):
		root, version, snapshot = self._version()
		snapshot = dict(snapshot)
		snapshot["items"] = [
			{"requisition_item_id": "RQI-001", "plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "unit": "Each", "intended_use": "a"},
			{"requisition_item_id": "RQI-002", "plan_item_line_id": "DL-002", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 150, "unit": "Each", "intended_use": "b"},
		]
		# both items share every technical row (the requirement, not the funding split, is what groups)
		snapshot["technical_requirements"] = [{**r, "applies_to_scope": "All items", "applies_to_id": ""} for r in snapshot["technical_requirements"]]
		lines = serializer.goods_lines(snapshot)
		self.assertEqual(len(lines), 1)
		self.assertEqual(lines[0]["quantity"], "250")
		self.assertEqual(lines[0]["source_item_ids"], "RQI-001, RQI-002")
		self.assertEqual([s["requisition_item_id"] for s in lines[0]["source_items"]], ["RQI-001", "RQI-002"])
		snapshot["items"][1]["item_name"] = "Business desktops"
		self.assertEqual(len(serializer.goods_lines(snapshot)), 2)
		# a row scoped to one item makes the two items different specifications
		snapshot["items"][1]["item_name"] = "Business laptops"
		snapshot["technical_requirements"][0].update({"applies_to_scope": "Item", "applies_to_id": "RQI-001"})
		self.assertEqual(len(serializer.goods_lines(snapshot)), 2)

	def test_every_technical_requirement_has_exactly_one_response_evaluation_and_contract_mapping(self):
		root, version, snapshot = self._version()
		ids = [r["technical_requirement_id"] for r in snapshot["technical_requirements"]]
		self.assertTrue(ids)
		state = serializer.officer_state(version)
		from kentender_procurement.tender_preparation.services import evidence

		rows = evidence.rows_as_dicts(version)
		responses = [r["technical_requirement_id"] for r in serializer.supplier_response_schema(snapshot, set(ids))["technical"]]
		evaluation = [r["technical_requirement_id"] for r in serializer.evaluation_contract(state, snapshot, rows)["technical_pass_fail"]]
		contract = [r["technical_requirement_id"] for r in serializer.contract_obligations(state, snapshot)["technical"]]
		self.assertEqual(responses, ids)
		self.assertEqual(evaluation, ids)
		self.assertEqual(contract, ids)
		self.assertEqual(serializer.evaluation_contract(state, snapshot, rows)["hidden_criteria"], [])
		self.assertEqual(serializer.evaluation_contract(state, snapshot, rows)["stages"], list(serializer.EVALUATION_STAGES))

	def test_the_price_schedule_carries_no_officer_or_authorised_price(self):
		root, version, snapshot = self._version()
		schedule = serializer.price_schedule(snapshot)
		for row in schedule["rows"]:
			self.assertEqual(row["unit_price"], serializer.SUPPLIER)
			self.assertEqual(row["line_total"], serializer.CALCULATED)
			self.assertEqual(row["tax"], serializer.SUPPLIER)
		self.assertEqual(schedule["tender_total"], serializer.CALCULATED)
		self.assertNotIn(str(int(snap.total_value(snapshot))), json.dumps(schedule))

	def test_the_render_context_has_the_fixture_shape_and_no_internal_keys_in_public_view(self):
		root, version, snapshot = self._version()
		context = serializer.render_context(root, version, snapshot)
		fixture = json.loads(loader.read_text("fixtures/moh_input.json"))
		self.assertEqual(set(serializer.public_context(context)), set(fixture))
		for section in ("tender", "submission", "contract", "procuring_entity", "requisition"):
			self.assertEqual(set(context[section]), set(fixture[section]), section)
		self.assertEqual(set(context["goods"][0]), set(fixture["goods"][0]))
		self.assertEqual(set(context["technical_requirements"][0]), set(fixture["technical_requirements"][0]))
		self.assertIn("_internal", context)
		self.assertNotIn("_internal", serializer.public_context(context))
		public = json.dumps(serializer.public_context(context))
		for marker in ("strategic_objective", "plan_horizon", "multi_year_justification"):
			self.assertNotIn(marker, public)
		self.assertEqual(context["tender"]["clarification_deadline"], "27 January 2102, 17:00 EAT")
		self.assertEqual(context["tender"]["validity_date"], "5 June 2102")
		self.assertEqual(context["tender"]["tender_security"]["amount"], "500,000.00")
		self.assertEqual(context["contract"]["performance_security"]["percentage"], "10")
		self.assertEqual(context["contract"]["delay_damages"]["rate_per_week"], "0.5")

	def test_content_digest_is_deterministic_and_changes_with_officer_values(self):
		root, version, snapshot = self._version()
		first = serializer.content_digest(root, version, snapshot)
		self.assertEqual(first, serializer.content_digest(root, version, snapshot))
		self.assertEqual(first, version.content_digest)
		version.tender_title = "Another title"
		self.assertNotEqual(first, serializer.content_digest(root, version, snapshot))

	def test_canonical_json_is_stable(self):
		self.assertEqual(digest.canonical_json({"b": 1, "a": [1, 2]}), '{"a":[1,2],"b":1}')
		self.assertEqual(len(digest.sha256_hex({"a": 1})), 64)
