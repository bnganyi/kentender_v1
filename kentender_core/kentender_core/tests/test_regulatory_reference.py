"""CFG-CHG-002 v0.9 §4.4A — the effective-dated regulator reference register.

CFG-BR-015 (every version carries its Fiscal Year; superseded versions are
retained and never edited in place), CFG-BR-016 (a read resolves the version
in force for the requested year, never today's), CFG-AC-030a, CFG-AC-031 and
CFG-AC-032.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_regulatory_reference
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup
from kentender_core.services import regulatory_reference as register
from kentender_core.services import site_configuration as configuration
from kentender_core.tests import v16_fixtures as fx

NS = "KT_TEST_REGREF"
Y = 2094  # far-future, purged by fiscal-year cleanup in the shared purge


class RegulatoryReferenceTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		fx.ensure_site_configured()
		site_setup._seed_catalogues()
		cls.fy = configuration._fy_name(Y)
		if not frappe.db.exists("Fiscal Year", cls.fy):
			configuration.add_fiscal_year(start_year=Y)
		register.purge_fixture_references(NS)
		cls.addClassCleanup(lambda: (register.purge_fixture_references(NS), frappe.db.commit()))
		frappe.db.commit()

	def _register(self, gazette: str, *, low_value_goods=50_000, effective_from="2094-07-01"):
		return register.register_regulatory_reference(
			fiscal_year=self.fy,
			effective_from=effective_from,
			gazette_reference=gazette,
			threshold_bands=[
				{"procurement_category": "Goods", "procurement_method": "Low Value Procurement", "max_amount": low_value_goods, "basis": "Per item per financial year"},
				{"procurement_category": "Works", "procurement_method": "Low Value Procurement", "max_amount": 100_000, "basis": "Per item per financial year"},
				{"procurement_category": "Services", "procurement_method": "Low Value Procurement", "max_amount": 50_000, "basis": "Per item per financial year"},
				{"procurement_category": "Goods", "procurement_method": "Open Tender", "max_amount": 0, "basis": "Funds allocated"},
			],
			reservation_categories=[
				{"category": "None", "advantage_rank": 0},
				{"category": "Youth", "advantage_rank": 1},
			],
			reservation_target_percent=30,
			county_resident_target_percent=20,
			exclusive_preference_works_amount=1_000_000_000,
			exclusive_preference_goods_services_amount=500_000_000,
			fixture_namespace=NS,
		)

	def test_missing_year_reports_unavailable_without_raising(self):
		"""CFG-AC-032 — the consumer decides what fails closed; the read never raises."""
		out = register.get_regulatory_reference(configuration._fy_name(Y + 1))
		self.assertFalse(out["available"])
		self.assertEqual(out["threshold_matrix"], [])
		self.assertFalse(out["reservation"]["published"])
		self.assertFalse(out["market_price_index"]["published"])

	def test_matrix_is_keyed_on_category_and_superseding_retains_the_earlier_version(self):
		first = self._register("GAZ-TEST-1")
		self.assertTrue(first["created"])
		again = self._register("GAZ-TEST-1")
		self.assertFalse(again["created"])
		self.assertEqual(again["reference"], first["reference"])

		out = register.get_regulatory_reference(self.fy)
		self.assertTrue(out["available"])
		by_key = {(r["procurement_category"], r["procurement_method"]): r["max_amount"] for r in out["threshold_matrix"]}
		# CFG-AC-030a — goods, works and services carry different limits.
		self.assertEqual(by_key[("Goods", "Low Value Procurement")], 50_000)
		self.assertEqual(by_key[("Works", "Low Value Procurement")], 100_000)
		self.assertEqual(out["reservation"]["target_percent"], 30)
		self.assertEqual(out["reservation"]["categories"][0]["category"], "None")
		self.assertEqual(out["exclusive_preference"]["works_amount"], 1_000_000_000)

		# CFG-BR-015 — never edited in place.
		doc = frappe.get_doc(register.DOCTYPE, first["reference"])
		doc.reservation_target_percent = 35
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(register.DOCTYPE, first["reference"], ignore_permissions=True)

		# CFG-AC-031 — a newer version supersedes; the earlier one is retained.
		second = self._register("GAZ-TEST-2", low_value_goods=60_000, effective_from="2094-10-01")
		self.assertTrue(second["created"])
		self.assertEqual(frappe.db.get_value(register.DOCTYPE, first["reference"], "status"), "Superseded")
		self.assertEqual(register.get_regulatory_reference(self.fy)["reference"], second["reference"])
		in_force = {
			(r["procurement_category"], r["procurement_method"]): r["max_amount"]
			for r in register.get_regulatory_reference(self.fy)["threshold_matrix"]
		}
		self.assertEqual(in_force[("Goods", "Low Value Procurement")], 60_000)
		self.assertTrue(frappe.db.exists(register.DOCTYPE, first["reference"]))

	def test_canonical_seed_registers_the_second_schedule_for_the_planning_year(self):
		"""PLN-CHG-001 v1.12 §14.1 — the seed carries the exact statutory figures."""
		fy = configuration._fy_name(site_setup.DPP_INTAKE["start_year"])
		if not frappe.db.exists("Fiscal Year", fy):
			configuration.add_fiscal_year(start_year=site_setup.DPP_INTAKE["start_year"])
		site_setup._seed_regulatory_reference()
		out = register.get_regulatory_reference(fy)
		self.assertTrue(out["available"])
		by_key = {(r["procurement_category"], r["procurement_method"]): r for r in out["threshold_matrix"]}
		self.assertEqual(len(by_key), 33)
		self.assertEqual(by_key[("Services", "Restricted Tender")]["max_amount"], 20_000_000)
		self.assertEqual(by_key[("Works", "Request for Quotations")]["max_amount"], 5_000_000)
		self.assertEqual(by_key[("Goods", "Low Value Procurement")]["basis"], "Per item per financial year")
		self.assertEqual(out["reservation"]["target_percent"], 30)
		self.assertEqual(out["reservation"]["county_target_percent"], 20)
		self.assertEqual({c["category"] for c in out["reservation"]["categories"]} >= {"None", "Youth", "Women", "Persons with disabilities"}, True)
		self.assertFalse(out["market_price_index"]["published"])
		self.assertEqual(frappe.db.count("Procurement Method", {"status": "Active"}) >= 11, True)
		self.assertTrue(frappe.db.exists("Requirement Type", "Works"))
