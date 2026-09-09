# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`kentender_core.seeds.canonical` — the progressive canonical-world seed
(KT-STD-001 §8 + SEED-001): selection of non-canonical rows, the stage
ladder, idempotency of a rerun and the fail-closed validator."""

from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import canonical


class TestCanonicalSelection(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)

	def test_stage_ladder_is_ordered_and_closed(self):
		self.assertEqual(
			canonical.STAGES,
			("site", "strategy", "budget", "needs", "planning", "requisitions", "tender_preparation"),
		)
		with self.assertRaises(frappe.ValidationError):
			canonical._stage_index("tender")

	def test_register_actor_and_real_person_are_never_selected(self):
		plan = canonical.collect_non_canonical()
		for email in canonical.REGISTER_USERS:
			self.assertNotIn(email, plan.get("User", []))
		# A non-fixture domain is never a seed's to delete, whatever its name.
		self.assertTrue(all(canonical._fixture_email(u) for u in plan.get("User", [])))

	def test_reset_removes_a_fiscal_year_only_unreferenced_by_this_same_clear(self):
		"""Regression: the fiscal-year removal list must be recomputed after
		the other deletions in `clear_non_canonical()`, not read from the
		pre-clear snapshot — a year referenced only by a stray Procurement
		Budget only becomes deletable once that budget is gone."""
		year = 2500 + int(uuid4().hex[:2], 16)
		fy = f"{year}-{year + 1}"
		frappe.get_doc(
			{"doctype": "Fiscal Year", "year": fy, "year_start_date": f"{year}-07-01", "year_end_date": f"{year + 1}-06-30"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("Fiscal Year", fy))
		budget = frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": f"STRAY-{uuid4().hex[:6]}", "fiscal_year": fy, "currency": "KES"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("Procurement Budget", budget.name))

		self.assertTrue(canonical._fiscal_year_referenced(fy))
		canonical.clear_non_canonical()
		self.assertFalse(frappe.db.exists("Procurement Budget", budget.name))
		self.assertFalse(frappe.db.exists("Fiscal Year", fy), "the year must be removed once its only reference is gone")

	def test_dry_run_selects_an_isolation_fiscal_year_without_deleting_it(self):
		year = 2400 + int(uuid4().hex[:2], 16)  # far outside any real or test year
		fy = f"{year}-{year + 1}"
		frappe.get_doc(
			{"doctype": "Fiscal Year", "year": fy, "year_start_date": f"{year}-07-01", "year_end_date": f"{year + 1}-06-30"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("Fiscal Year", fy))

		report = canonical.dry_run()
		self.assertIn(fy, report["would_remove"].get("Fiscal Year", []))
		self.assertTrue(frappe.db.exists("Fiscal Year", fy), "dry_run must delete nothing")

	def test_fixture_user_outside_the_register_is_selected(self):
		email = f"canonical.stray.{uuid4().hex[:6]}@example.test"
		frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": "Stray", "send_welcome_email": 0, "user_type": "System User"}
		).insert(ignore_permissions=True)
		self._cleanup.append(("User", email))
		self.assertIn(email, canonical.collect_non_canonical().get("User", []))

	def test_a_stray_departmental_need_outside_the_namespace_is_a_stray(self):
		need = frappe.get_doc({"doctype": "Departmental Need", "need_reference": f"STRAY-NDS-{uuid4().hex[:6]}", "current_state": "Draft"})
		# Only the namespace stamp matters to selection; a minimal insert
		# would fail on this doctype's own required fields, so bypass them —
		# `collect_non_canonical()` reads the raw db row, not the full doc.
		need.flags.ignore_mandatory = True
		need.insert(ignore_permissions=True)
		try:
			self.assertIn(need.name, canonical.collect_non_canonical().get("Departmental Need", []))
		finally:
			# `on_trash` refuses every delete on this doctype by design (a
			# Need is "retained and cannot be deleted") — the seed's own
			# purge goes raw for exactly this reason; mirror it here.
			frappe.db.delete("Departmental Need", {"name": need.name})


class TestCanonicalSeedRun(IntegrationTestCase):
	"""Runs the real seed on the test site (the seed is idempotent and only
	adds canonical rows; `reset=False` keeps this to the seed itself)."""

	def test_seed_through_budget_is_idempotent(self):
		frappe.set_user("Administrator")
		first = canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(first["ok"])
		budgets = frappe.db.count("Procurement Budget")
		versions = frappe.db.count("Procurement Budget Version")
		plans = frappe.db.count("Strategic Plan", {"fixture_namespace": canonical.STRATEGY_NS})
		units = frappe.db.count("Organisation Unit")
		assignments = frappe.db.count("User Responsibility Assignment")

		second = canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(second["ok"])
		self.assertFalse(second["seeded"]["budget"]["moh"]["created"])
		self.assertEqual(frappe.db.count("Procurement Budget"), budgets)
		self.assertEqual(frappe.db.count("Procurement Budget Version"), versions)
		self.assertEqual(frappe.db.count("Strategic Plan", {"fixture_namespace": canonical.STRATEGY_NS}), plans)
		self.assertEqual(frappe.db.count("Organisation Unit"), units)
		self.assertEqual(frappe.db.count("User Responsibility Assignment"), assignments)

	def test_validate_fails_closed_on_a_stray_budget(self):
		frappe.set_user("Administrator")
		canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		stray = frappe.get_doc(
			{"doctype": "Procurement Budget", "generated_reference": f"STRAY-{uuid4().hex[:6]}", "fiscal_year": "2026-2027", "currency": "KES"}
		).insert(ignore_permissions=True)
		try:
			with self.assertRaises(frappe.ValidationError):
				canonical.validate(through="budget")
		finally:
			frappe.delete_doc("Procurement Budget", stray.name, force=1, ignore_permissions=True)


class TestCanonicalSeedFullChain(IntegrationTestCase):
	"""The full site → strategy → budget → needs → planning → requisitions →
	tender_preparation chain, on the real test site, `reset=False` so this
	stays scoped to the seed's own rows (as `TestCanonicalSeedRun` already
	does for budget)."""

	def test_seed_through_tender_preparation_is_idempotent(self):
		frappe.set_user("Administrator")
		first = canonical.run(through="tender_preparation", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(first["ok"])
		counts = {dt: frappe.db.count(dt) for dt in ("Departmental Need", "Annual Plan", "Procurement Requisition", "Prepared Tender")}

		second = canonical.run(through="tender_preparation", reset=False, validate=True, force=True, commit=False)
		self.assertTrue(second["ok"])
		self.assertTrue(second["seeded"]["requisitions"]["idempotent"])
		self.assertTrue(second["seeded"]["tender_preparation"]["idempotent"])
		for dt, count in counts.items():
			self.assertEqual(frappe.db.count(dt), count, dt)


class TestCanonicalReservationNamespace(IntegrationTestCase):
	"""REQ-CHG-001 v1.6 — reservation begins at Procurement Requisition, not a
	canonical stage yet. A row stamped `REQUISITIONS_NS` is canonical evidence
	of an authorised Requisition; anything else on the canonical budget is a
	stray the seed's own reservation checks must still catch."""

	def setUp(self):
		frappe.set_user("Administrator")
		canonical.run(through="budget", reset=False, validate=True, force=True, commit=False)
		self.budget = frappe.db.get_value(
			"Procurement Budget", {"generated_reference": ["in", canonical.CANONICAL_BUDGET_CODES]}, "name"
		)
		self.budget_version = frappe.db.get_value(
			"Procurement Budget Version", {"budget": self.budget, "status": "Active"}, "name"
		)
		self.budget_line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": self.budget_version}, "budget_line")
		self._reservations: list[str] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self._reservations:
			if frappe.db.exists("Funding Reservation", name):
				frappe.delete_doc("Funding Reservation", name, force=1, ignore_permissions=True)

	def _reserve(self, *, fixture_namespace: str, plan_source_allocation: str) -> str:
		doc = frappe.get_doc(
			{
				"doctype": "Funding Reservation",
				"generated_reference": f"RSV-TEST-{uuid4().hex[:8]}",
				"budget": self.budget,
				"budget_version_at_creation": self.budget_version,
				"budget_line": self.budget_line,
				"status": "Active",
				"plan_item": "TEST-PLAN-ITEM",
				"plan_source_allocation": plan_source_allocation,
				"original_amount": 1,
				"remaining_amount": 1,
				"currency": "KES",
				"correlation_id": plan_source_allocation,
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
		self._reservations.append(doc.name)
		return doc.name

	def test_a_reservation_stamped_requisitions_ns_is_not_a_stray(self):
		self._reserve(fixture_namespace=canonical.REQUISITIONS_NS, plan_source_allocation=f"TEST-PSA-{uuid4().hex[:8]}")
		plan = canonical.collect_non_canonical()
		self.assertNotIn(self._reservations[0], plan.get("Funding Reservation", []))
		canonical.validate(through="budget")  # must not raise

	def test_a_reservation_outside_requisitions_ns_is_a_stray(self):
		self._reserve(fixture_namespace="", plan_source_allocation=f"TEST-PSA-{uuid4().hex[:8]}")
		plan = canonical.collect_non_canonical()
		self.assertIn(self._reservations[0], plan.get("Funding Reservation", []))
		with self.assertRaises(frappe.ValidationError):
			canonical.validate(through="budget")
