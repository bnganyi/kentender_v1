# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""get_budget_movements API — unit / integration tests.

Run:
  bench --site kentender.midas.com run-tests \\
    --app kentender_budget \\
    --module kentender_budget.tests.test_budget_movements_api
"""
from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_budget.api.movements import get_budget_movements
from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _make_approved_budget(version_no: int = 1) -> str:
	"""Create a Budget approved at now_datetime() and return its name."""
	ensure_currency_kes()
	h = frappe.generate_hash(length=6)
	entity = ensure_procuring_entity(f"MV-{h}", f"Movements Test {h}")
	plan = frappe.get_doc({
		"doctype": "Strategic Plan",
		"strategic_plan_name": f"Plan-MV-{h}",
		"procuring_entity": entity,
		"start_year": 2026, "end_year": 2030,
		"status": "Draft", "version_no": 1, "is_current_version": 1,
	}).insert(ignore_permissions=True)
	frappe.get_doc({
		"doctype": "Strategy Program",
		"strategic_plan": plan.name,
		"program_title": f"Prog-MV-{h}",
		"order_index": 1,
	}).insert(ignore_permissions=True)
	bud = frappe.get_doc({
		"doctype": "Budget",
		"budget_name": f"BUD-MV-{h}",
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"strategic_plan": plan.name,
		"currency": "KES",
		"total_budget_amount": 5_000_000,
		"version_no": version_no,
		"is_current_version": 1,
		"order_index": 0,
	}).insert(ignore_permissions=True)
	frappe.db.set_value("Budget", bud.name, {
		"status": "Approved",
		"approved_at": now_datetime(),
	})
	return bud.name


def _make_reservation(budget_name: str, status: str = "Active") -> str:
	"""Create a Budget Reservation linked to budget_name and return its name."""
	h = frappe.generate_hash(length=6)
	entity = frappe.db.get_value("Budget", budget_name, "procuring_entity")
	line_name = frappe.db.get_value("Budget Line", {"budget": budget_name}, "name")

	if not line_name:
		# Need strategic_plan + program for mandatory Budget Line fields
		strategic_plan = frappe.db.get_value("Budget", budget_name, "strategic_plan")
		prog = frappe.db.get_value(
			"Strategy Program", {"strategic_plan": strategic_plan}, "name"
		) if strategic_plan else None

		line = frappe.get_doc({
			"doctype": "Budget Line",
			"budget_line_code": f"BL-MV-{h}",
			"budget_line_name": f"MV Line {h}",
			"budget": budget_name,
			"procuring_entity": entity,
			"fiscal_year": 2026,
			"amount_allocated": 5_000_000,
			"currency": "KES",
			"is_active": 1,
			"strategic_plan": strategic_plan,
			"program": prog,
		}).insert(ignore_permissions=True)
		line_name = line.name

	res = frappe.get_doc({
		"doctype": "Budget Reservation",
		"reservation_id": f"RS-MV-{h}",
		"budget_line": line_name,
		"budget": budget_name,
		"procuring_entity": entity,
		"fiscal_year": 2026,
		"amount": 1_200_000,
		"currency": "KES",
		"status": "Active",
		"source_doctype": "Demand",
		"source_docname": f"DM-{h}",
		"source_business_id": f"DM-{h}",
		"created_at": now_datetime(),
	}).insert(ignore_permissions=True)

	if status == "Released":
		# Promote to Released directly; set_value bypasses BR-007 validator
		frappe.db.set_value("Budget Reservation", res.name, {
			"status": "Released",
			"released_at": now_datetime(),
			"released_by": frappe.session.user,
		})

	return res.name


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestBudgetMovementsShape(IntegrationTestCase):
	"""Basic contract: response shape and field presence."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_returns_movements_key(self):
		out = get_budget_movements()
		self.assertIn("movements", out, "Response must have a 'movements' key")
		self.assertIsInstance(out["movements"], list)

	def test_limit_respected(self):
		out = get_budget_movements(limit=3)
		self.assertLessEqual(len(out["movements"]), 3)

	def test_movement_fields_present(self):
		"""Every movement item must carry the canonical keys."""
		out = get_budget_movements(limit=20)
		required = {"event_type", "icon", "title", "desc", "ref", "ts", "entity_name"}
		for mov in out["movements"]:
			for key in required:
				self.assertIn(key, mov, f"movement missing field '{key}'")

	def test_event_types_are_valid(self):
		_valid = {"allocation", "reservation", "release", "revision"}
		out = get_budget_movements(limit=20)
		for mov in out["movements"]:
			self.assertIn(
				mov["event_type"],
				_valid,
				f"unexpected event_type '{mov['event_type']}'",
			)

	def test_icon_matches_event_type(self):
		_expected_icons = {
			"allocation": "add_box",
			"reservation": "lock",
			"release": "lock_open",
			"revision": "history",
		}
		out = get_budget_movements(limit=20)
		for mov in out["movements"]:
			expected = _expected_icons.get(mov["event_type"])
			if expected:
				self.assertEqual(
					mov["icon"],
					expected,
					f"event_type={mov['event_type']} should have icon={expected}",
				)

	def test_movements_sorted_descending(self):
		"""Movements must be ordered newest-first."""
		out = get_budget_movements(limit=20)
		timestamps = [m["ts"] for m in out["movements"] if m.get("ts")]
		self.assertEqual(
			timestamps,
			sorted(timestamps, reverse=True),
			"Movements must be sorted descending by timestamp",
		)


class TestBudgetMovementsEvents(IntegrationTestCase):
	"""Event-type coverage: allocation, revision, reservation, release."""

	def setUp(self):
		frappe.set_user("Administrator")

	def test_allocation_event_appears_for_approved_v1_budget(self):
		"""Approving a version-1 Budget creates an 'allocation' event."""
		bname = _make_approved_budget(version_no=1)
		out = get_budget_movements(limit=50)
		alloc_events = [m for m in out["movements"] if m["event_type"] == "allocation"]
		refs = [m["ref"] for m in alloc_events]
		self.assertIn(bname, refs, "allocation event not found for v1 Approved budget")

	def test_revision_event_appears_for_approved_v2_budget(self):
		"""Approving a version-2 Budget creates a 'revision' event."""
		bname = _make_approved_budget(version_no=2)
		out = get_budget_movements(limit=50)
		rev_events = [m for m in out["movements"] if m["event_type"] == "revision"]
		refs = [m["ref"] for m in rev_events]
		self.assertIn(bname, refs, "revision event not found for v2 Approved budget")

	def test_reservation_event_appears_for_active_reservation(self):
		"""An Active Budget Reservation creates a 'reservation' event."""
		bname = _make_approved_budget()
		_make_reservation(bname, status="Active")
		out = get_budget_movements(limit=50)
		res_events = [m for m in out["movements"] if m["event_type"] == "reservation"]
		self.assertTrue(len(res_events) > 0, "no reservation events found")

	def test_release_event_appears_for_released_reservation(self):
		"""A Released Budget Reservation creates a 'release' event."""
		bname = _make_approved_budget()
		_make_reservation(bname, status="Released")
		out = get_budget_movements(limit=50)
		rel_events = [m for m in out["movements"] if m["event_type"] == "release"]
		self.assertTrue(len(rel_events) > 0, "no release events found")

	def test_allocation_event_has_non_empty_desc(self):
		bname = _make_approved_budget(version_no=1)
		out = get_budget_movements(limit=50)
		ev = next((m for m in out["movements"]
		           if m["event_type"] == "allocation" and m["ref"] == bname), None)
		self.assertIsNotNone(ev)
		self.assertTrue(ev["desc"].strip(), "allocation event desc must not be empty")

	def test_reservation_event_includes_amount_in_desc(self):
		bname = _make_approved_budget()
		_make_reservation(bname, status="Active")
		out = get_budget_movements(limit=50)
		res_ev = next((m for m in out["movements"] if m["event_type"] == "reservation"), None)
		self.assertIsNotNone(res_ev)
		self.assertIn("KES", res_ev["desc"], "reservation desc should include KES amount")
