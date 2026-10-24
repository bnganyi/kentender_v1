# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The canonical `contracts` stage (SEED-002 v0.10 section A8.1): the closed year's three awards, carried into Contract Management by the owners' own commands.

Level L2 on the canonical world: nothing here builds a world. The stage is told once by the seed (`make seed-canonical`); these tests read it, so they skip on a site that was not seeded with it. What they
establish is the story's own facts (where each contract stands, what it cost, what Budget and ERPNext hold for it) and that a second run of the stage changes nothing."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import contracts_stage as stage


def _world() -> bool:
	return all(stage.case_of(stage.award_of(story)) for story in stage.STORIES)


class TestCanonicalContractsStage(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not _world():
			raise unittest.SkipTest("the site holds no canonical contracts stage (make seed-canonical)")

	def case(self, ref: str) -> str:
		story = next(s for s in stage.STORIES if s.ref == ref)
		return stage.case_of(stage.award_of(story))

	def test_the_validation_of_the_stage_has_no_failing_row(self):
		failing = [row["check"] for row in stage.validate_contracts_seed() if not row["ok"]]
		self.assertEqual(failing, [])

	def test_a_second_run_of_the_stage_changes_nothing(self):
		before = {doctype: frappe.db.count(doctype) for doctype in ("Contract Case", "Contract Event", "Contract Invoice", "Contract Settlement", "Purchase Order", "Purchase Receipt", "Payment Entry", "Procurement Commitment")}
		out = stage.upsert_contracts_base()
		self.assertTrue(out["idempotent"])
		self.assertEqual({doctype: frappe.db.count(doctype) for doctype in before}, before)

	def test_the_three_contracts_stand_where_the_story_puts_them(self):
		lifecycle = {ref: frappe.db.get_value("Contract Case", self.case(ref), "lifecycle") for ref in ("Y0-1", "Y0-2", "Y0-3")}
		self.assertEqual(lifecycle, {"Y0-1": "Active", "Y0-2": "Active", "Y0-3": "Preparing"})
		for ref in ("Y0-1", "Y0-2", "Y0-3"):
			self.assertEqual(frappe.db.get_value("Contract Case", self.case(ref), "fixture_namespace"), stage.NAMESPACE, ref)
			self.assertEqual(frappe.db.get_value("Contract Case", self.case(ref), "legal_profile"), "SYNTHETIC-ILLUSTRATIVE", ref)

	def test_the_workstations_are_paid_in_full_and_budget_holds_the_commitment(self):
		case = self.case("Y0-1")
		value = frappe.db.get_value("Contract Case", case, "contract_value")
		settlement = frappe.get_all("Contract Settlement", filters={"contract_case": case}, fields=["state", "amount"])
		self.assertEqual([(s.state, s.amount) for s in settlement], [("Confirmed", value)])
		self.assertEqual(frappe.db.get_value("Contract Invoice", {"contract_case": case}, ["state", "accounting_state"], as_dict=True), {"state": "Paid", "accounting_state": "Posted"})
		commitments = frappe.get_all("Procurement Commitment", filters={"contract": case}, fields=["current_amount", "fixture_namespace", "status"])
		self.assertEqual([(c.current_amount, c.fixture_namespace) for c in commitments], [(value, stage.BUDGET_NAMESPACE)])
		self.assertEqual(frappe.db.get_value("Payment Entry", {"party": stage.SUPPLIER, "docstatus": 1}, "paid_amount"), value)

	def test_the_printers_are_part_delivered_and_part_accepted_and_not_claimed(self):
		case = self.case("Y0-2")
		terms = stage._terms(case)
		ordered = int(terms["lines"][0]["quantity"])
		arrived = sum(int(item["quantity"]) for row in frappe.get_all("Contract Arrival", filters={"contract_case": case}, pluck="items_json") for item in frappe.parse_json(row))
		self.assertEqual((ordered, arrived), (30, 20))
		self.assertTrue(frappe.db.exists("Contract Acceptance", {"contract_case": case, "state": "Effective"}))
		self.assertFalse(frappe.db.exists("Contract Invoice", {"contract_case": case}), "nothing is claimed until the supplier claims")
		self.assertEqual(frappe.db.count("Purchase Order", {"supplier": stage.SUPPLIER, "docstatus": 1}), 2)

	def test_the_laptops_wait_for_their_agreement_with_the_head_of_procurement_to_prepare_it(self):
		case = self.case("Y0-3")
		self.assertFalse(frappe.db.exists("Contract Signature", {"contract_case": case, "state": "Signed"}))
		task = frappe.get_all("Contract Task", filters={"contract_case": case, "command": "RequestContractSignatures"}, fields=["holder", "state"])
		self.assertEqual([(t.holder, t.state) for t in task], [(stage.PEOPLE["charles"], "Open")])
		self.assertEqual(frappe.db.get_value("Award Case", stage.award_of(next(s for s in stage.STORIES if s.ref == "Y0-3")), "stage"), "Sent to Contracting")

	def test_the_agreement_was_generated_from_the_issued_form_with_its_declared_places_filled(self):
		case = self.case("Y0-1")
		agreement = frappe.db.get_value("Contract Agreement Version", {"contract_case": case, "state": "Effective"}, "rendered_html")
		self.assertIn('<span data-insertion="supplier_name">Afya Digital Supplies Limited</span>', agreement)
		self.assertIn('<span data-insertion="entity_address">Afya House, Cathedral Road, Nairobi</span>', agreement)
		self.assertRegex(agreement, r'<span data-insertion="agreement_day">\d{1,2}(st|nd|rd|th)</span>')
		self.assertIn('<span data-insertion="addenda">none</span>', agreement)
		self.assertIn("THIS AGREEMENT made the", agreement, "the covenant and precedence text of the issued form is untouched")
		self.assertEqual(frappe.db.get_value("Contract Case", case, "legal_profile"), "SYNTHETIC-ILLUSTRATIVE")

	def test_every_step_was_taken_by_the_people_the_register_names_and_none_after_the_anchor(self):
		from kentender_core.seeds import canonical as world

		self.assertEqual([line for line in world.events_after_anchor() if "Contract" in line], [])
		held = {row.user for row in frappe.get_all("User Responsibility Assignment", filters={"business_role": ["in", ["Contract preparation", "Contract inspection", "Entity contract signing", "Technical certification", "Receiving",
			"Finance preparation", "Finance approval"]], "status": "Enabled"}, fields=["user"])}
		self.assertEqual(held, {stage.PEOPLE[p] for p in ("brian", "amina", "julia", "peter", "grace", "josphat", "beatrice")})


class TestStageHelpers(unittest.TestCase):
	def test_an_offset_moves_a_fixture_instant_by_exactly_that_much(self):
		self.assertEqual(stage.plus("2026-02-14 09:00:00", days=1, hours=1), "2026-02-15 10:00:00")
		self.assertEqual(stage.plus("2026-02-14 09:00:00", minutes=30), "2026-02-14 09:30:00")

	def test_each_story_has_one_state_the_validation_knows(self):
		self.assertEqual({s.state for s in stage.STORIES}, set(stage.EXPECTED))
		self.assertEqual([s.ref for s in stage.STORIES], ["Y0-1", "Y0-2", "Y0-3"])
