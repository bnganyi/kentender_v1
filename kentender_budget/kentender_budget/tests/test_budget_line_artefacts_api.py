# Copyright (c) 2026, Midas and contributors
# License: MIT. See LICENSE
"""W5-04 — TDD tests for get_budget_line_artefacts endpoint.

Run:
  bench --site kentender.midas.com run-tests \
    --app kentender_budget \
    --module kentender_budget.tests.test_budget_line_artefacts_api
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, now_datetime

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


def _import_artefacts():
	from kentender_budget.api.artefacts import get_budget_line_artefacts  # noqa: PLC0415

	return get_budget_line_artefacts


class TestBudgetLineArtefactsApi(IntegrationTestCase):
	"""get_budget_line_artefacts must return the six artefact sections."""

	# ── Fixtures ──────────────────────────────────────────────────────────────

	def setUp(self):
		frappe.set_user("Administrator")
		ensure_currency_kes()
		h = frappe.generate_hash(length=6)
		self.entity = ensure_procuring_entity(f"ART_{h}", f"Artefacts Test Entity {h}")

		self.plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"strategic_plan_name": f"Plan ART {h}",
				"procuring_entity": self.entity,
				"start_year": 2026,
				"end_year": 2030,
				"status": "Draft",
			}
		).insert(ignore_permissions=True)

		self.program = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": self.plan.name,
				"program_title": f"Program ART {h}",
				"program_code": f"PRG-{h}",
				"order_index": 0,
			}
		).insert(ignore_permissions=True)

		self.budget = frappe.get_doc(
			{
				"doctype": "Budget",
				"budget_name": f"Budget ART {h}",
				"procuring_entity": self.entity,
				"fiscal_year": 2026,
				"strategic_plan": self.plan.name,
				"currency": "KES",
				"total_budget_amount": 1_000_000,
				"version_no": 1,
				"is_current_version": 1,
				"order_index": 0,
			}
		).insert(ignore_permissions=True)

		self.line = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"budget_line_code": f"BL-ART-{h}",
				"budget_line_name": f"Artefacts Line {h}",
				"fiscal_year": 2026,
				"currency": "KES",
				"is_active": 1,
				"amount_allocated": 500_000,
				"amount_reserved": 200_000,
				"amount_committed": 0,
				"amount_consumed": 0,
				"amount_available": 300_000,
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"line_status": "Active",
			}
		).insert(ignore_permissions=True)

		# Create an Active reservation on this line (simulates a demand reservation)
		self.reservation = frappe.get_doc(
			{
				"doctype": "Budget Reservation",
				"budget_line": self.line.name,
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"source_doctype": "Demand",
				"source_docname": f"DEM-ART-{h}",
				"source_business_id": f"DEM-ART-{h}",
				"amount": 200_000,
				"currency": "KES",
				"fiscal_year": 2026,
				"status": "Active",
				"created_at": now_datetime(),
				"created_by": frappe.session.user,
				"available_before_reservation": 500_000,
				"available_after_reservation": 300_000,
			}
		).insert(ignore_permissions=True)

		# Second reservation that was released (for movements coverage)
		self.reservation_released = frappe.get_doc(
			{
				"doctype": "Budget Reservation",
				"budget_line": self.line.name,
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"source_doctype": "Demand",
				"source_docname": f"DEM-ART-{h}-B",
				"source_business_id": f"DEM-ART-{h}-B",
				"amount": 50_000,
				"currency": "KES",
				"fiscal_year": 2026,
				"status": "Released",
				"created_at": now_datetime(),
				"created_by": frappe.session.user,
				"released_at": now_datetime(),
				"released_by": frappe.session.user,
				"release_reason": "Demand cancelled — funds no longer required.",
				"available_before_reservation": 300_000,
				"available_after_reservation": 250_000,
			}
		).insert(ignore_permissions=True)

		# Empty line — no reservations
		self.empty_line = frappe.get_doc(
			{
				"doctype": "Budget Line",
				"budget": self.budget.name,
				"procuring_entity": self.entity,
				"budget_line_code": f"BL-EMPTY-{h}",
				"budget_line_name": f"Empty Line {h}",
				"fiscal_year": 2026,
				"currency": "KES",
				"is_active": 1,
				"amount_allocated": 100_000,
				"amount_reserved": 0,
				"amount_committed": 0,
				"amount_consumed": 0,
				"amount_available": 100_000,
				"strategic_plan": self.plan.name,
				"program": self.program.name,
				"line_status": "Active",
			}
		).insert(ignore_permissions=True)

	# ── Response shape ────────────────────────────────────────────────────────

	def test_returns_all_six_sections(self):
		"""Response must contain strategy, demands, packages, tenders, contracts, movements."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		for key in ("strategy", "demands", "packages", "tenders", "contracts", "movements"):
			self.assertIn(key, result, f"Missing section: {key}")

	def test_all_list_sections_are_lists(self):
		"""demands, packages, tenders, contracts, movements must be lists."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		for key in ("demands", "packages", "tenders", "contracts", "movements"):
			self.assertIsInstance(result[key], list, f"Section '{key}' must be a list")

	def test_strategy_is_dict(self):
		"""strategy section must be a dict."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		self.assertIsInstance(result["strategy"], dict)

	# ── Strategy section ──────────────────────────────────────────────────────

	def test_strategy_has_program_label(self):
		"""strategy.program_label must be the human-readable program title."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		self.assertIn("program_label", result["strategy"])
		self.assertIn("Program ART", result["strategy"]["program_label"])

	def test_strategy_has_program_id(self):
		"""strategy.program must be the raw FK (for navigation)."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		self.assertEqual(result["strategy"]["program"], self.program.name)

	def test_strategy_optional_fields_present(self):
		"""sub_program, output_indicator, performance_target keys must exist (may be None)."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		for key in ("sub_program", "sub_program_label", "output_indicator",
					"output_indicator_label", "performance_target", "performance_target_label"):
			self.assertIn(key, result["strategy"])

	# ── Demands section ───────────────────────────────────────────────────────

	def test_demands_has_active_reservation(self):
		"""Active reservation with source_doctype='Demand' must appear in demands."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		refs = [d["ref"] for d in result["demands"]]
		self.assertIn(self.reservation.source_business_id, refs)

	def test_demand_item_has_required_fields(self):
		"""Each demand item must have: ref, amount, status, source_doctype."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		self.assertGreater(len(result["demands"]), 0)
		item = result["demands"][0]
		for field in ("ref", "amount", "status", "source_doctype"):
			self.assertIn(field, item, f"Demand item missing field: {field}")

	def test_demand_amount_is_numeric(self):
		"""demand.amount must be a number, not a string."""
		fn = _import_artefacts()
		item = fn(self.line.name)["demands"][0]
		self.assertIsInstance(flt(item["amount"]), float)

	# ── Movements section ─────────────────────────────────────────────────────

	def test_movements_includes_active_reservation(self):
		"""Active reservation must appear as a 'reservation' movement."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		types = [m["event_type"] for m in result["movements"]]
		self.assertIn("reservation", types)

	def test_movements_includes_released_reservation(self):
		"""Released reservation must appear as a 'release' movement."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		types = [m["event_type"] for m in result["movements"]]
		self.assertIn("release", types)

	def test_movement_item_has_event_model(self):
		"""Each movement must carry the full hub-timeline event model fields."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		self.assertGreater(len(result["movements"]), 0)
		item = result["movements"][0]
		for field in ("event_type", "icon", "title", "desc", "ref", "ts"):
			self.assertIn(field, item, f"Movement missing field: {field}")

	def test_movements_ordered_newest_first(self):
		"""Movements must be sorted newest-first by timestamp."""
		fn = _import_artefacts()
		result = fn(self.line.name)
		if len(result["movements"]) > 1:
			ts_list = [m["ts"] for m in result["movements"] if m["ts"]]
			self.assertEqual(ts_list, sorted(ts_list, reverse=True))

	# ── Empty line ────────────────────────────────────────────────────────────

	def test_empty_line_returns_empty_lists(self):
		"""A line with no reservations must return empty lists for all artefact sections."""
		fn = _import_artefacts()
		result = fn(self.empty_line.name)
		for key in ("demands", "packages", "tenders", "contracts", "movements"):
			self.assertEqual(result[key], [], f"Expected empty list for '{key}', got {result[key]}")

	def test_empty_line_strategy_still_populated(self):
		"""Empty line still has the strategy section populated from line fields."""
		fn = _import_artefacts()
		result = fn(self.empty_line.name)
		self.assertIn("program", result["strategy"])
		self.assertEqual(result["strategy"]["program"], self.program.name)

	# ── Error paths ───────────────────────────────────────────────────────────

	def test_nonexistent_line_raises(self):
		"""Requesting a non-existent budget line must raise a Frappe exception."""
		fn = _import_artefacts()
		with self.assertRaises(Exception):
			fn("NON-EXISTENT-LINE-XYZ")

	def test_empty_line_name_raises(self):
		"""Passing an empty string must raise a Frappe exception."""
		fn = _import_artefacts()
		with self.assertRaises(Exception):
			fn("")
