# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""get_consumption_velocity — unit / integration tests.

Run:
  bench --site kentender.midas.com run-tests \
    --app kentender_budget \
    --module kentender_budget.tests.test_budget_velocity_api
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_months, getdate, now_datetime

from kentender_budget.api.velocity import get_consumption_velocity
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _make_reservation(amount: float, months_ago: int = 0) -> str:
	"""Insert a Budget Reservation with a known amount and creation timestamp.

	*months_ago* shifts the creation timestamp so tests can place events in
	specific months relative to today.  Uses frappe.db.set_value to backdate
	the ``created_at`` field without triggering validation.
	Returns the reservation name.
	"""
	ensure_currency_kes()
	h = frappe.generate_hash(length=6)
	entity = ensure_procuring_entity(f"VL-{h}", f"Velocity Test {h}")
	plan = frappe.get_doc({
		"doctype": "Strategic Plan",
		"strategic_plan_name": f"Plan-VL-{h}",
		"procuring_entity": entity,
		"start_year": 2026, "end_year": 2030,
		"status": "Draft", "version_no": 1, "is_current_version": 1,
	}).insert(ignore_permissions=True)
	prog = frappe.get_doc({
		"doctype": "Strategy Program",
		"strategic_plan": plan.name,
		"program_title": f"Prog-VL-{h}",
		"order_index": 1,
	}).insert(ignore_permissions=True)
	bud = frappe.get_doc({
		"doctype": "Budget",
		"budget_name": f"BUD-VL-{h}",
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"strategic_plan": plan.name,
		"currency": "KES",
		"total_budget_amount": amount * 2,
		"version_no": 1,
		"is_current_version": 1,
		"order_index": 0,
	}).insert(ignore_permissions=True)
	frappe.db.set_value("Budget", bud.name, "status", "Approved")

	line = frappe.get_doc({
		"doctype": "Budget Line",
		"budget_line_code": f"BL-VL-{h}",
		"budget_line_name": f"VL Line {h}",
		"budget": bud.name,
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"amount_allocated": amount * 2,
		"amount_reserved": amount,
		"amount_available": amount,
		"currency": "KES",
		"is_active": 1,
		"strategic_plan": plan.name,
		"program": prog.name,
	}).insert(ignore_permissions=True)

	target_dt = add_months(now_datetime(), -months_ago)
	res = frappe.get_doc({
		"doctype": "Budget Reservation",
		"budget_line": line.name,
		"budget": bud.name,
		"procuring_entity": entity,
		"amount": amount,
		"currency": "KES",
		"fiscal_year": 2026,
		"status": "Active",
		"source_doctype": "Budget Line",
		"source_docname": line.name,
		"available_before_reservation": amount * 2,
		"available_after_reservation": amount,
	}).insert(ignore_permissions=True)

	# Backdate created_at to the requested month
	frappe.db.set_value("Budget Reservation", res.name, "created_at", target_dt)

	return res.name


# ── Shape contract ─────────────────────────────────────────────────────────────

class TestVelocityShape(IntegrationTestCase):
	"""Response shape and field contracts."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_returns_months_and_trend_note_keys(self):
		out = get_consumption_velocity()
		self.assertIn("months", out)
		self.assertIn("trend_note", out)
		self.assertIn("data_source", out)

	def test_months_is_list(self):
		out = get_consumption_velocity()
		self.assertIsInstance(out["months"], list)

	def test_default_returns_7_months(self):
		out = get_consumption_velocity()
		self.assertEqual(len(out["months"]), 7)

	def test_custom_months_param(self):
		out = get_consumption_velocity(months=3)
		self.assertEqual(len(out["months"]), 3)

	def test_month_entry_fields_present(self):
		out = get_consumption_velocity()
		for m in out["months"]:
			self.assertIn("label", m)
			self.assertIn("amount", m)
			self.assertIn("pct", m)

	def test_pct_is_float(self):
		out = get_consumption_velocity()
		for m in out["months"]:
			self.assertIsInstance(m["pct"], float)

	def test_pct_range_zero_to_100(self):
		"""pct values must all be in [0, 100]."""
		out = get_consumption_velocity()
		for m in out["months"]:
			self.assertGreaterEqual(m["pct"], 0.0)
			self.assertLessEqual(m["pct"], 100.01)

	def test_labels_are_3_letter_strings(self):
		out = get_consumption_velocity()
		for m in out["months"]:
			self.assertEqual(len(m["label"]), 3)
			self.assertTrue(m["label"].isupper())

	def test_trend_note_is_string(self):
		out = get_consumption_velocity()
		self.assertIsInstance(out["trend_note"], str)

	def test_data_source_is_valid(self):
		out = get_consumption_velocity()
		self.assertIn(out["data_source"], ("reservation", "none"))


# ── Data accuracy ──────────────────────────────────────────────────────────────

class TestVelocityValues(IntegrationTestCase):
	"""Aggregation correctness."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_reservation_in_current_month_appears(self):
		"""A reservation created this month must appear in the last bucket."""
		_make_reservation(amount=100_000.0, months_ago=0)
		out = get_consumption_velocity()
		last = out["months"][-1]
		# The current month bucket must have amount ≥ 100k
		self.assertGreaterEqual(last["amount"], 100_000.0)

	def test_reservation_one_month_ago_appears(self):
		"""A reservation from last month must appear in the second-to-last bucket."""
		_make_reservation(amount=200_000.0, months_ago=1)
		out = get_consumption_velocity()
		second_last = out["months"][-2]
		self.assertGreaterEqual(second_last["amount"], 200_000.0)

	def test_max_bucket_has_pct_100(self):
		"""The month with the highest amount must have pct == 100.0."""
		_make_reservation(amount=500_000.0, months_ago=0)
		out = get_consumption_velocity()
		max_pct = max(m["pct"] for m in out["months"])
		self.assertAlmostEqual(max_pct, 100.0, delta=0.1)

	def test_empty_months_have_zero_amount_and_pct(self):
		"""Months with no reservation activity must show amount=0 and pct=0."""
		out = get_consumption_velocity()
		# At least the earliest months in the window should be zero
		# (cannot guarantee which, but all zero amounts must also have pct 0)
		for m in out["months"]:
			if m["amount"] == 0.0:
				self.assertAlmostEqual(m["pct"], 0.0, delta=0.1)

	def test_data_source_is_reservation_when_reservations_exist(self):
		"""data_source must be 'reservation' when reservation data is present."""
		_make_reservation(amount=50_000.0, months_ago=0)
		out = get_consumption_velocity()
		self.assertEqual(out["data_source"], "reservation")

	def test_trend_note_not_empty_when_data_exists(self):
		"""trend_note must be a non-empty string when reservation data exists."""
		_make_reservation(amount=75_000.0, months_ago=0)
		out = get_consumption_velocity()
		self.assertTrue(len(out["trend_note"].strip()) > 0)
