# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published seams Bid Evaluation reads through (EVL-CHG-001 v0.4 §5.1,
§5.7, §6; plan D5, D6, D8, D21, D22; tracker EVL4-301, EVL4-303, EVL4-304).

On a real completed opening in the Bid Opening test world: Bid Opening's
completion verifies by recomputation, is acknowledged once and is never
confused with an incomplete opening; Bid Submission releases the exact sealed
package of an opened envelope and refuses anything else, with the four trust
outcomes; Tenders gives the six scope predicates from published values, the
published validity end, no guessed evaluation deadline and an authoritative
award-decision status."""

from __future__ import annotations

import hashlib
import json

import frappe

from kentender_procurement.bid_evaluation.tests.support import CHAIR, EvaluationCase
from kentender_procurement.bid_opening.services import evaluation_seam as bop
from kentender_procurement.bid_opening.tests.support import INDEPENDENT, MEMBER
from kentender_procurement.bid_submission.services import evaluation_gateway as bds
from kentender_procurement.tenders.services import evaluation_seam as tenders


class TestOpeningSeam(EvaluationCase):
	shared_world = False  # each test needs the opening at its own moment (one before close)

	def test_completion_is_verified_acknowledged_once_and_never_an_empty_opening(self):
		self.assertIsNone(bop.completion(self.name))
		self.assertIsNone(bop.final_outcome(self.name))
		self.prepared()
		self.assertEqual(bop.final_outcome(self.name)["outcome"], "Incomplete")  # never "No bids" while not final
		completion = self.completed_opening()
		self.assertTrue(completion["verified"])
		self.assertEqual(len(completion["payload"]["packages"]), 1)
		self.assertEqual(bop.final_outcome(self.name)["outcome"], "Bids opened")
		self.assertTrue(bop.acknowledge(completion["handoff_id"]))
		self.assertFalse(bop.acknowledge(completion["handoff_id"]))
		self.assertEqual(frappe.db.get_value("Evaluation Handoff", completion["handoff_id"], "delivery_status"), "Delivered")
		self.assertEqual(len(bop.register_rows(self.name)), 1)
		# BOP-A17 / FU-BOP-11: the independent opening member cannot evaluate this Tender.
		self.assertTrue(bop.is_excluded_from_evaluation(self.name, INDEPENDENT))
		self.assertFalse(bop.is_excluded_from_evaluation(self.name, MEMBER))
		self.assertFalse(bop.is_excluded_from_evaluation(self.name, CHAIR))

	def test_a_changed_payload_does_not_verify(self):
		completion = self.completed_opening()
		row = frappe.get_doc("Evaluation Handoff", completion["handoff_id"])
		payload = json.loads(row.payload_json)
		payload["packages"][0]["package_digest"] = "0" * 64
		frappe.db.set_value("Evaluation Handoff", row.name, "payload_json", json.dumps(payload))
		self.assertFalse(bop.completion(self.name)["verified"])

	def test_the_package_is_released_only_for_an_opened_envelope(self):
		completion = self.completed_opening()
		package = completion["payload"]["packages"][0]
		out = bds.released_package(tender=self.name, envelope_id=package["envelope_id"], package_digest=package["package_digest"],
			completion_reference=completion["handoff_id"], correlation_id="evl-test-1")
		self.assertEqual(out["outcome"], "Accepted/Verified")
		self.assertEqual(hashlib.sha256(out["package"]).hexdigest(), package["package_digest"])
		self.assertEqual(out["correlation_id"], "evl-test-1")
		body = json.loads(out["package"])
		self.assertEqual(body["schema"], "kt-bds-package/1")
		# C23: the package carries the definition identity the hand-off lacks.
		self.assertTrue(body["tender"]["bid_definition_id"])
		refused = bds.released_package(tender=self.name, envelope_id=package["envelope_id"], package_digest="0" * 64, completion_reference=completion["handoff_id"],
			correlation_id="evl-test-2")
		self.assertEqual((refused["outcome"], refused["reason"]), ("Rejected", "digest_mismatch"))
		unknown = bds.released_package(tender=self.name, envelope_id="TBX-ENV-UNKNOWN", package_digest=package["package_digest"],
			completion_reference=completion["handoff_id"], correlation_id="evl-test-3")
		self.assertEqual((unknown["outcome"], unknown["reason"]), ("Rejected", "not_current"))
		frappe.conf["kt_bds_simulation_environment"] = 0
		try:
			none = bds.released_package(tender=self.name, envelope_id=package["envelope_id"], package_digest=package["package_digest"],
				completion_reference=completion["handoff_id"], correlation_id="evl-test-4")
		finally:
			frappe.conf["kt_bds_simulation_environment"] = 1
		self.assertEqual(none["outcome"], "Unavailable")  # no custody provider: never a guess

	def test_nothing_is_released_before_close(self):
		out = bds.released_package(tender=self.name, envelope_id="TBX-ENV-ANY", package_digest="0" * 64, completion_reference="x", correlation_id="evl-test-5")
		self.assertEqual((out["outcome"], out["reason"]), ("Rejected", "no_close"))


class TestTendersSeam(EvaluationCase):
	world = "open"

	def test_scope_dates_and_decision_status(self):
		fact = tenders.publication_fact(self.name)
		self.assertTrue(fact["published_at"])
		self.assertTrue(fact["definition"]["bid_definition_id"])
		self.assertEqual(fact["product_key"], "IT-EQUIPMENT-OPEN-V1")
		scope = tenders.scope_facts(self.name)
		self.assertEqual(scope["status"], "In scope", scope)
		self.assertEqual([p["key"] for p in scope["predicates"]], ["product_key", "procurement_method", "procurement_category", "lotting", "currency",
			"price_treatment", "financial_evaluation"])
		self.assertTrue(all(p["source"] for p in scope["predicates"]))
		dated = tenders.dated_rules(self.name)
		self.assertIsNotNone(dated["validity_end"])
		self.assertIn("validity days", dated["validity_rule"]["counting"])
		self.assertIsNone(dated["evaluation_deadline"])  # C24: never guessed from a planning assumption
		self.assertEqual(tenders.award_decision_status(self.name)["status"], "No award decision recorded")
		self.assertEqual(tenders.status_events(self.name), [])

	def test_a_missing_product_key_is_unresolved_not_a_default(self):
		previous = frappe.db.get_value("Tender", self.name, "product_key")
		self.addCleanup(frappe.db.set_value, "Tender", self.name, "product_key", previous)
		frappe.db.set_value("Tender", self.name, "product_key", "")
		scope = tenders.scope_facts(self.name)
		self.assertEqual(scope["status"], "Unresolved")
		self.assertIn("The product key is not published for this Tender.", scope["issues"])
