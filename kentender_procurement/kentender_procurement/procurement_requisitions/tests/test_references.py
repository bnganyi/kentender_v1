# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §5.1 — the requisition_reference generator."""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import references


class TestReferences(IntegrationTestCase):
	def test_plan_item_number_reads_the_trailing_segment(self):
		self.assertEqual(references.plan_item_number("PPI-MOH-2027-033"), "033")

	def test_pe_code_and_fy_start_resolve_from_the_canonical_site(self):
		self.assertEqual(references.pe_code(), "MOH")
		self.assertEqual(references.fy_start("2027-2028"), "2027")

	def test_requisition_reference_has_the_exact_shape_and_increments(self):
		first = references.requisition_reference(fiscal_year="2027-2028", plan_item_id_value="PPI-MOH-2027-999")
		self.assertTrue(first.startswith("REQ-MOH-2027-999-"))
		self.assertEqual(len(first.rsplit("-", 1)[1]), 3)

		# A distinct Plan Item number starts its own sequence at 001.
		other_item = references.requisition_reference(fiscal_year="2027-2028", plan_item_id_value="PPI-MOH-2027-998")
		self.assertEqual(other_item, "REQ-MOH-2027-998-001")
