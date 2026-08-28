"""AUTH-ADR-001 Phase 2 — PE Fiscal Year Context resolution (read-only)."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate

from kentender_core.services.pe_fy_context_resolver import (
	resolve_by_date_overlap,
	resolve_by_financial_year_label,
)


class TestPeFyContextResolver(IntegrationTestCase):
	def setUp(self):
		self.suffix = uuid4().hex[:6]
		self.pe = frappe.get_all("Procuring Entity", pluck="name", limit=1)[0]
		self.other_pe = frappe.get_all("Procuring Entity", pluck="name", limit=2)[-1]
		# Pick a start_year unlikely to collide with any other fixture/test.
		self.start_year = 4000 + int(self.suffix[:4], 16) % 900
		self.fy = frappe.get_doc({"doctype": "Financial Year", "start_year": self.start_year}).insert(ignore_permissions=True)
		self.ctx = frappe.get_doc({
			"doctype": "PE Fiscal Year Context",
			"procuring_entity": self.pe,
			"financial_year": self.fy.name,
			"context_status": "Scheduled",
			"active_from": self.fy.start_date,
			"active_to": self.fy.end_date,
		}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.delete_doc("PE Fiscal Year Context", self.ctx.name, force=True, ignore_permissions=True)
		frappe.delete_doc("Financial Year", self.fy.name, force=True, ignore_permissions=True)

	def test_resolves_by_exact_label_and_pe(self):
		result = resolve_by_financial_year_label(self.pe, self.fy.label)

		self.assertEqual(result, self.ctx.name)

	def test_label_match_wrong_pe_is_unresolved(self):
		result = resolve_by_financial_year_label(self.other_pe, self.fy.label)

		self.assertIsNone(result)

	def test_unknown_label_is_unresolved(self):
		result = resolve_by_financial_year_label(self.pe, "1999/00")

		self.assertIsNone(result)

	def test_blank_inputs_are_unresolved(self):
		self.assertIsNone(resolve_by_financial_year_label(self.pe, ""))
		self.assertIsNone(resolve_by_financial_year_label("", self.fy.label))

	def test_resolves_by_overlapping_date_range(self):
		result = resolve_by_date_overlap(
			self.pe,
			add_days(getdate(self.fy.start_date), 10),
			add_days(getdate(self.fy.end_date), -10),
		)

		self.assertEqual(result, self.ctx.name)

	def test_non_overlapping_date_range_is_unresolved(self):
		result = resolve_by_date_overlap(
			self.pe,
			add_days(getdate(self.fy.end_date), 1),
			add_days(getdate(self.fy.end_date), 365),
		)

		self.assertIsNone(result)

	def test_date_overlap_wrong_pe_is_unresolved(self):
		result = resolve_by_date_overlap(self.other_pe, getdate(self.fy.start_date), getdate(self.fy.end_date))

		self.assertIsNone(result)
