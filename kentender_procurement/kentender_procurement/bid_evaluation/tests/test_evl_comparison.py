# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Aggregation and the comparison after intake (EVL-CHG-001 v0.4 §4.2, §4.4;
tracker EVL4-506, EVL4-507; acceptance EVL-A03, EVL-A04, EVL-A09 (service
parts); boards D03, D04, D04-AUTO, D04-FAIL, D07-NO-RESPONSIVE).

A compliant bid's offered values meet their published conditions, while its
supporting evidence and free-text requirements stay Needs review for the
committee, so the bid is not yet ranked and nothing is recommended. An 8 GB
offer against a 16 GB minimum fails automatically with that reason; the bid
is Not responsive, its financial assessment reads Not assessed, its
submitted total stays visible as a source fact, and the outcome is No
responsive bids."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import aggregate, checks, comparison, intake, preparation
from kentender_procurement.bid_evaluation.tests.support import EvaluationCase


class ReceivedCase(EvaluationCase):
	def received(self):
		preparation.ensure_preparation(tender=self.name)
		self.completed_opening()
		out = intake.receive_opening_package(tender=self.name)
		self.assertTrue(out["received"], out)
		return frappe.get_doc("Evaluation Case", {"tender": self.name})

	def requirement(self, doc, label):
		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": doc.name}, "name")
		res = aggregate.bid_results(doc.name, checks.current_run(doc.name), bid)
		return res, next(r for r in res["requirements"] if r["label"] == label)


class TestCompliantBid(ReceivedCase):
	def test_values_meet_and_evidence_waits_for_the_committee(self):
		doc = self.received()
		res, memory = self.requirement(doc, "Memory")
		value = next(c for c in memory["checks"] if c.field_key == "offered_value")
		self.assertEqual((value.result, value.reason, value.required_display), ("Meets", "Offered memory meets the minimum.", "Minimum 16 GB"))
		self.assertEqual(memory["automatic"], "Meets")
		self.assertEqual((memory["result"], memory["reason"]), ("Needs review", "The offered values have been checked. Supporting evidence needs review."))
		_res, processor = self.requirement(doc, "Processor requirement")
		self.assertEqual(processor["result"], "Needs review")  # free text: a member's finding
		self.assertEqual(res["responsiveness"], "Needs review")
		table = comparison.compare(doc.name, with_funding=False)
		row = table["rows"][0]
		self.assertEqual((row["evaluated_total"], row["position"], row["adjustments"]), ("Needs review", "Not ranked", "None"))
		self.assertIsNone(table["outcome"])
		self.assertFalse(table["provisional"])  # one bid: nothing else it could change


class TestMemoryBelowMinimum(ReceivedCase):
	overrides = {"memory": 8}

	def test_the_bid_is_not_responsive_and_nothing_is_recommended(self):
		doc = self.received()
		res, memory = self.requirement(doc, "Memory")
		self.assertEqual((memory["result"], memory["reason"]), ("Does not meet", "8 GB is below the required 16 GB."))
		self.assertEqual(res["groups"]["EVG-TECHNICAL-COMPLIANCE"], "Does not meet")
		self.assertEqual(res["responsiveness"], "Not responsive")
		table = comparison.compare(doc.name, with_funding=False)
		row = table["rows"][0]
		self.assertEqual((row["evaluated_total"], row["adjustments"], row["position"]),
			("Not assessed — mandatory requirement not met", "Not assessed — mandatory requirement not met", "Not ranked"))
		self.assertTrue(row["submitted_total"])  # the source fact stays visible
		self.assertEqual(table["outcome"], "No responsive bids")
		self.assertIsNone(table["recommended"])
		# the original offer is untouched: nothing is written back
		self.assertEqual(frappe.db.get_value("Evaluation Bid", row["bid"], "submitted_total"), row["submitted_total"])
