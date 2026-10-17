# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Contracts list draws the design's five filters (the Project Owner, 17 October 2026: "Do not deviate from the design"; the design then put them all in one row): Search, Status, Source, Responsible
person and Managing unit in the one bar. A person or a unit chosen from a list that can grow is the shared record picker (AGENTS.md section 6.12), and what it offers is only the people and units of contracts the
reader may read: the filters narrow the list, they never tell a reader who or what else exists."""

from __future__ import annotations

import frappe

from kentender_contracts.boards import listing
from kentender_contracts.services import errors, formation
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase
from kentender_core.services import record_picker


class TestTheListFilters(ContractCase):
	native = True  # the particulars name real catalogue items and a real location

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p = self.people
		self.n = 0
		# A is still being prepared: the head of procurement's turn. B has been sent and the supplier has signed: the Accounting Officer's turn, in another managing unit.
		self.a = tw.receive(self.p, contract_id="CM-TEST-RFA", award_case="CM-TEST-RFA-AWD")["contract"]
		self.b = tw.receive(self.p, contract_id="CM-TEST-RFB", award_case="CM-TEST-RFB-AWD")["contract"]
		formation.save_particulars(self.b, expected_version=self.version(self.b), idempotency_key=self.k(), actor=self.p["brian"], values=tw.package_particulars(self.p))
		formation.request_signatures(self.b, expected_version=self.version(self.b), idempotency_key=self.k(), actor=self.p["charles"])
		formation.sign_contract(self.b, party="Supplier", expected_version=self.version(self.b), idempotency_key=self.k(), actor=self.p["mary"])
		self.unit_a = frappe.db.get_value("Contract Case", self.a, "managing_unit")
		self.unit_b = next(u for u in frappe.get_all("Organisation Unit", pluck="name", order_by="name asc") if u != self.unit_a)
		frappe.db.set_value("Contract Case", self.b, "managing_unit", self.unit_b)

	def k(self):
		self.n += 1
		return f"k-{self.id().rsplit('.', 1)[-1][:30]}-{self.n}"

	def version(self, case):
		return int(frappe.db.get_value("Contract Case", case, "record_version"))

	def ids(self, who, **filters):
		board = listing.workspace(self.p[who], view="All contracts", **filters)["board"]
		return {frappe.db.get_value("Contract Case", route[0], "contract_id") for route in board["rowRoutes"]}

	def lead_holder(self, who, contract_id):
		"""Whoever holds the next action of that contract as this reader sees it (the head of procurement's turn on a contract still being prepared belongs to every head the site has, and the list names one)."""
		return next(r["lead"]["holder"] for r in listing._register(self.p[who]) if r["doc"].get("contract_id") == contract_id)

	def ask(self, who, source, query=""):
		frappe.set_user(self.p[who])
		self.addCleanup(frappe.set_user, "Administrator")
		return record_picker.search(source, query, {})

	def test_the_list_offers_the_designs_five_filters_in_its_order_and_a_supplier_one(self):
		board = listing.workspace(self.p["amina"], view="All contracts")["board"]
		self.assertEqual([(f["l"], f["name"], f["t"]) for f in board["filters"]],
			[("Search contracts", "search", "tx"), ("Status", "status", "sel"), ("Source", "source", "sel"), ("Responsible person", "responsible", "pick"), ("Managing unit", "unit", "pick")])
		pickers = {f["name"]: f for f in board["filters"] if f["t"] == "pick"}
		self.assertEqual((pickers["responsible"]["source"], pickers["responsible"]["o"]["allLabel"]), (listing.RESPONSIBLE, "All people"))
		self.assertEqual((pickers["unit"]["source"], pickers["unit"]["o"]["allLabel"]), (listing.MANAGING_UNIT, "All units"))
		self.assertEqual(record_picker.check_sources(), [], "both sources are registered and well shaped")

	def test_responsible_person_is_who_holds_the_next_action_and_narrows_the_list_to_them(self):
		self.assertEqual(self.ids("amina"), {"CM-TEST-RFA", "CM-TEST-RFB"})
		head = self.lead_holder("amina", "CM-TEST-RFA")
		self.assertNotEqual(head, self.p["amina"])
		self.assertEqual(self.lead_holder("amina", "CM-TEST-RFB"), self.p["amina"], "her own signature is B's next action")
		self.assertEqual(self.ids("amina", responsible=self.p["amina"]), {"CM-TEST-RFB"})
		self.assertEqual(self.ids("amina", responsible=head), {"CM-TEST-RFA"}, "A waits for the head to prepare it")
		self.assertEqual(self.ids("amina", responsible=self.p["julia"]), set(), "someone who holds no next action matches nothing")

	def test_managing_unit_narrows_the_list_to_the_contracts_that_unit_manages(self):
		self.assertEqual(self.ids("amina", unit=self.unit_a), {"CM-TEST-RFA"})
		self.assertEqual(self.ids("amina", unit=self.unit_b), {"CM-TEST-RFB"})
		self.assertEqual(self.ids("amina", unit="OU-NO-SUCH-UNIT"), set())

	def test_the_choice_is_kept_on_the_board_with_its_saved_name_and_clearing_it_restores_the_list(self):
		board = listing.workspace(self.p["amina"], view="All contracts", responsible=self.p["amina"], unit=self.unit_b)["board"]
		chosen = {f["name"]: f for f in board["filters"]}
		self.assertEqual((chosen["responsible"]["v"], chosen["responsible"]["valueLabel"]), (self.p["amina"], frappe.db.get_value("User", self.p["amina"], "full_name")))
		self.assertEqual((chosen["unit"]["v"], chosen["unit"]["valueLabel"]), (self.unit_b, frappe.db.get_value("Organisation Unit", self.unit_b, "unit_name") or self.unit_b))
		self.assertEqual(board["emptyAct"], "Clear search", "a filter in force is a search that can be cleared")
		self.assertEqual(self.ids("amina", responsible="", unit=""), {"CM-TEST-RFA", "CM-TEST-RFB"})

	def test_the_pickers_offer_only_the_people_and_units_of_contracts_the_reader_may_read(self):
		people = {row["id"] for row in self.ask("amina", listing.RESPONSIBLE)["rows"]}
		self.assertEqual(people, {self.p["amina"], self.lead_holder("amina", "CM-TEST-RFA")})
		units = {row["id"] for row in self.ask("amina", listing.MANAGING_UNIT)["rows"]}
		self.assertEqual(units, {self.unit_a, self.unit_b})
		self.assertEqual({row["id"] for row in self.ask("amina", listing.MANAGING_UNIT, self.unit_b)["rows"]}, {self.unit_b}, "typing narrows the units")

	def test_everything_the_picker_offers_returns_at_least_one_contract(self):
		for row in self.ask("amina", listing.RESPONSIBLE)["rows"]:
			self.assertTrue(self.ids("amina", responsible=row["id"]), row["label"])
		for row in self.ask("amina", listing.MANAGING_UNIT)["rows"]:
			self.assertTrue(self.ids("amina", unit=row["id"]), row["label"])

	def test_a_reader_with_no_part_in_contracts_and_a_supplier_are_told_nothing(self):
		frappe.flags.kt_supplier_account_provider = None
		for who in ("stranger", "mary"):
			user = self.p.get(who) or "stranger@x.example"
			frappe.set_user(user)
			self.addCleanup(frappe.set_user, "Administrator")
			for source in (listing.RESPONSIBLE, listing.MANAGING_UNIT):
				with self.assertRaises((frappe.DoesNotExistError, errors.ContractError)):
					record_picker.search(source, "", {})
