# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-004 — Procurement Journey Step child table + WORKS seed §15 order contract."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_lifecycle.works_seed_step_contract import (
	WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
)


class TestR1004WorksSeedStepOrder(unittest.TestCase):
	"""LV-R1-004-02 — base checkpoint step_key order matches WORKS master seed spec §15."""

	def test_twelve_steps_in_contract(self):
		self.assertEqual(len(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER), 12)

	def test_order_matches_spec_table(self):
		self.assertEqual(
			WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER,
			(
				"strategy",
				"budget",
				"demand",
				"planning_inclusion",
				"package_release",
				"std_readiness",
				"tender_publication",
				"tender_closing",
				"opening_readiness",
				"bid_opening",
				"evaluation_award",
				"contract",
			),
		)


class TestR1004ProcurementJourneyStepMeta(IntegrationTestCase):
	"""LV-R1-004-01 — child DocType schema."""

	def test_child_doctype_is_table(self):
		self.assertTrue(frappe.db.exists("DocType", "Procurement Journey Step"))
		meta = frappe.get_meta("Procurement Journey Step")
		self.assertEqual(int(meta.istable or 0), 1)

	def test_parent_has_steps_table_field(self):
		meta = frappe.get_meta("Procurement Journey")
		names = {df.fieldname for df in meta.fields}
		self.assertIn("steps", names)
		steps_field = meta.get_field("steps")
		self.assertEqual(steps_field.fieldtype, "Table")
		self.assertEqual(steps_field.options, "Procurement Journey Step")


class TestR1004JourneyWithSteps(IntegrationTestCase):
	"""Materialize §15-shaped rows on a journey header; parent validation."""

	def tearDown(self):
		frappe.db.delete("Procurement Journey", {"journey_code": "JRN-TEST-R1004-001"})
		super().tearDown()

	def _minimal_step_row(self, order: int, step_key: str, label: str, owner: str, status: str) -> dict:
		return {
			"doctype": "Procurement Journey Step",
			"step_order": order,
			"step_key": step_key,
			"label": label,
			"owner_module": owner,
			"status_category": status,
			"blocker_count": 0,
		}

	def test_insert_twelve_seed_ordered_steps(self):
		labels = (
			"Strategy Priority",
			"Funding Available",
			"Need Approved",
			"Procurement Planned",
			"Package Released",
			"Tender Document Ready",
			"Tender Published",
			"Tender Closed",
			"Opening Ready",
			"Opening Complete",
			"Evaluation / Award",
			"Contract Handoff",
		)
		owners = (
			"Strategy",
			"Budget",
			"Demands",
			"Procurement Planning",
			"Procurement Planning",
			"STD Engine / Tender Management",
			"Tender Management",
			"Tender Management",
			"Tender Management / Bid Opening",
			"Bid Opening",
			"Evaluation & Award",
			"Contract Management",
		)
		statuses = (
			"Completed",
			"Completed",
			"Completed",
			"Completed",
			"Handed Off",
			"Completed",
			"Completed",
			"Not Started",
			"Not Started",
			"Not Started",
			"Not Started",
			"Not Started",
		)
		steps = [
			self._minimal_step_row(i + 1, k, labels[i], owners[i], statuses[i])
			for i, k in enumerate(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER)
		]
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1004-001",
				"journey_title": "R1-004 step table test",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "tender_published",
				"current_stage_label": "Tender Published",
				"current_status_category": "Completed",
				"current_owner_module": "Tender Management",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
				"steps": steps,
			}
		)
		doc.insert()
		reloaded = frappe.get_doc("Procurement Journey", "JRN-TEST-R1004-001")
		ordered = sorted(reloaded.steps, key=lambda r: int(r.step_order or 0))
		self.assertEqual([r.step_key for r in ordered], list(WORKS_SEED_TENDER_PUBLISHED_STEP_KEYS_IN_ORDER))

	def test_duplicate_step_order_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1004-001",
				"journey_title": "Dup order",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "strategy",
				"current_stage_label": "Strategic Priority",
				"current_status_category": "Not Started",
				"current_owner_module": "Strategy",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
				"steps": [
					self._minimal_step_row(1, "strategy", "A", "Strategy", "Not Started"),
					self._minimal_step_row(1, "budget", "B", "Budget", "Not Started"),
				],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_child_invalid_status_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "Procurement Journey",
				"journey_code": "JRN-TEST-R1004-001",
				"journey_title": "Bad child status",
				"procuring_entity_code": "PE-TEST",
				"fiscal_year": "2026/2027",
				"current_stage_key": "strategy",
				"current_stage_label": "Strategic Priority",
				"current_status_category": "Not Started",
				"current_owner_module": "Strategy",
				"blocker_count": 0,
				"critical_blocker_count": 0,
				"is_master_seed": 0,
				"steps": [
					{
						"doctype": "Procurement Journey Step",
						"step_order": 1,
						"step_key": "strategy",
						"label": "X",
						"owner_module": "Strategy",
						"status_category": "BogusStatus",
						"blocker_count": 0,
					},
				],
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.insert()
