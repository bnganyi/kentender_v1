# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 §13 — seed determinism, idempotent double-run, MoH/Kisumu
isolation, no-expenditure-fixture and no-negative-fixture rules in the
canonical (`include_test_edges=False`) seed path.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.seeds.kentender_mvp_v1_portfolio import upsert_kentender_mvp_v1_portfolio
from kentender_budget.services.budget_permissions import ensure_budget_roles

_CANONICAL_DOCTYPES = (
	"Budget",
	"Budget Line",
	"Funding Reservation",
	"Procurement Commitment",
	"Expenditure Snapshot",
)


class TestBudgetSeedIntegrity(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_budget_roles()

	def test_seed_double_run_is_idempotent(self):
		"""BUD-CHG-001 §13 — rerunning the canonical seed creates nothing new."""
		first = upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		second = upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		self.assertTrue(first.get("ok"))
		self.assertTrue(second.get("ok"))
		self.assertEqual(sorted(first["codes"]), sorted(second["codes"]))
		self.assertEqual(sorted(first["budgets"]), sorted(second["budgets"]))

	def test_seed_double_run_creates_no_duplicate_rows(self):
		upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		counts_before = {
			dt: frappe.db.count(dt, {"fixture_namespace": "KENTENDER_MVP_V1"})
			for dt in _CANONICAL_DOCTYPES
		}
		upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		counts_after = {
			dt: frappe.db.count(dt, {"fixture_namespace": "KENTENDER_MVP_V1"})
			for dt in _CANONICAL_DOCTYPES
		}
		self.assertEqual(counts_before, counts_after)

	def test_no_expenditure_fixture_in_canonical_seed(self):
		"""BUD-CHG-001 §13 — no Actual Expenditure Snapshot unless a named demo
		integration is explicitly enabled; the canonical seed enables none."""
		upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		self.assertEqual(
			frappe.db.count("Expenditure Snapshot", {"fixture_namespace": "KENTENDER_MVP_V1"}), 0
		)

	def test_canonical_seed_carries_no_reservation_or_commitment(self):
		"""The MoH reservation/conversion-scenario arithmetic from §13.1 is proven
		deterministically by `upsert_budget_activity_test_fixture` (see
		`test_budget_integration_contracts.py` /
		`test_budget_funding_activity.py`), not baked into the canonical
		`include_test_edges=False` seed — the canonical seed's own Budget Lines
		(MOH-BL-DHI-2027, MOH-BL-HWD-2027, ...) must start at their full
		approved amount with nothing reserved/committed against them, since a
		wide range of other Budget Lines/Check-Reserve tests assert exactly
		that starting state. This test locks in that boundary so a future
		change doesn't silently entangle the two.
		"""
		upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		self.assertEqual(
			frappe.db.count("Funding Reservation", {"fixture_namespace": "KENTENDER_MVP_V1"}), 0
		)
		self.assertEqual(
			frappe.db.count("Procurement Commitment", {"fixture_namespace": "KENTENDER_MVP_V1"}), 0
		)
		line = frappe.get_doc("Budget Line", {"generated_reference": "MOH-BL-DHI-2027"})
		self.assertEqual(line.approved_amount, 480_000_000)
		self.assertEqual(line.amount_reserved, 0)
		self.assertEqual(line.amount_committed, 0)

	def test_moh_and_kisumu_budgets_are_isolated(self):
		"""BUD-CHG-001 §13 — Kisumu baseline has at least one modest demo line
		and no MoH references."""
		upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		moh_pe = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOH"}, "name")
		cgk_pe = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-CGKIS"}, "name")
		self.assertTrue(moh_pe)
		self.assertTrue(cgk_pe)
		self.assertNotEqual(moh_pe, cgk_pe)

		cgk_budgets = frappe.get_all(
			"Budget", filters={"procuring_entity": cgk_pe}, fields=["name", "generated_reference"]
		)
		self.assertTrue(cgk_budgets)
		for b in cgk_budgets:
			lines = frappe.get_all(
				"Budget Line",
				filters={"budget": b.name},
				fields=["generated_reference", "organisational_owner", "funding_source_name"],
			)
			self.assertTrue(lines, f"{b.generated_reference} has no lines")
			for ln in lines:
				self.assertNotIn("MOH", (ln.generated_reference or "").upper())
				self.assertNotIn("Ministry of Health", ln.funding_source_name or "")

		moh_budgets = frappe.get_all("Budget", filters={"procuring_entity": moh_pe}, pluck="name")
		for name in moh_budgets:
			self.assertNotIn(name, [b.name for b in cgk_budgets])

	def test_edge_budgets_excluded_from_canonical_seed(self):
		"""BUD-CHG-001 §13 — negative/edge fixtures stay test-only; the
		canonical (`include_test_edges=False`) seed's own upsert pass does not
		touch the Submitted/Draft-incomplete UI-edge budgets at all.

		Note: this only asserts the canonical call's own `codes`/`budgets`
		result — it does not assert the edge records are absent from the
		(shared, not-rolled-back) test database, since other test classes in
		this suite legitimately seed them via `include_test_edges=True`.
		"""
		result = upsert_kentender_mvp_v1_portfolio(include_test_edges=False)
		for code in ("MOH-BUD-0002", "MOH-BUD-0004"):
			self.assertNotIn(code, result["codes"])
