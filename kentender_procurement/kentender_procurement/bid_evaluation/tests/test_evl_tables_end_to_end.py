# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release 1.4 end to end: a bid whose tables are all populated (commission recipients on a Yes, persons
with an interest on a Yes) and whose Account profile is copied per entity is submitted, opened and
received for evaluation. The tables travel in the sealed package as rows, the entity's profile is in it
with the entity named, the opening record shows both as tables, and the committee is told a disclosed
interest needs assessment."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import aggregate, checks, intake, preparation, sources
from kentender_procurement.bid_evaluation.tests.support import EvaluationCase
from kentender_procurement.bid_opening.services import package_renderer
from kentender_procurement.tenders.services import opening_seam


class TestTablesEndToEnd(EvaluationCase):
	overrides = {"commissions_paid": "Yes", "procuring_entity_interest": "Yes"}

	def received(self):
		preparation.ensure_preparation(tender=self.name)
		self.completed_opening()
		self.assertTrue(intake.receive_opening_package(tender=self.name)["received"])
		doc = frappe.get_doc("Evaluation Case", {"tender": self.name})
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": doc.name}, "name")
		return doc, bid, sources.cached_package(doc, frappe.get_doc("Evaluation Bid", bid))

	def test_the_tables_and_the_entity_profile_travel_sealed_and_are_shown_as_tables(self):
		doc, bid, source = self.received()
		body = source["body"]
		by_key = {}
		for row in body["responses"]:
			by_key.setdefault(row["field_key"], []).append(row)
		recipients = by_key["commission_recipients"][0]["value"]
		self.assertTrue(recipients and set(recipients[0]) == {"recipient", "address", "reason", "amount", "currency"})
		persons = by_key["procuring_entity_interest_persons"][0]["value"]
		self.assertTrue(persons and set(persons[0]) == {"name", "designation", "relationship"})
		# the entity's own business profile is in the package, with the entity named
		structure = by_key["business_structure"][0]
		self.assertEqual((structure["value"], bool(structure["member"])), ("Registered company", True))
		self.assertTrue(by_key["directors"][0]["value"])
		self.assertEqual(sum(float(r["shares"]) for r in by_key["directors"][0]["value"]), 100.0)

		labels = opening_seam.definition_labels(self.name, body["tender"]["definition_version"])
		html = package_renderer.html_of(body, envelope_id="ENV-1", receipt_reference="RCP-1", labels=labels)
		self.assertIn("<th>Name of recipient</th>", html)
		self.assertIn("<th>Shares owned (%)</th>", html)
		self.assertIn("Business structure — ", html)
		self.assertNotIn("&quot;recipient&quot;", html)  # no raw rows

	def test_a_disclosed_interest_needs_the_committees_assessment(self):
		doc, bid, _source = self.received()
		rows = frappe.get_all("Evaluation Check Result", filters={"evaluation_case": doc.name, "field_key": "procuring_entity_interest"}, fields=["result", "reason"])
		self.assertEqual([r.result for r in rows], ["Needs review"])
		state = frappe.get_all("Evaluation Check Result", filters={"evaluation_case": doc.name, "field_key": "state_owned"}, fields=["result", "offered_display"])
		self.assertEqual([r.result for r in state], ["Meets"])  # "No" is the entity's profile answer
