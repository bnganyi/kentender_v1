# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The real Evaluation → Award seam, read-only (AWD-CHG-001 v0.4 §3,
AWD-IF-01–03; plan D5, rule 11; tracker AWD4-207).

Reads the canonical delivered report (TND-MOH-2027-002, `make seed-canonical
THROUGH=bid_evaluation`) through the published seams and checks that the
real provider answers every fact the synthetic provider stands in for, in the
same shape. Nothing is written."""

from __future__ import annotations

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.award.services import sources
from kentender_procurement.award.test_services import sources as syn

REF = "TND-MOH-2027-002"
MARY = "mary.wanjiku@afyadigital.example"
DAVID = "david.ouma@afyadigital.example"
AT = "2027-06-17 10:00:00"


class TestRealSeams(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		case = frappe.db.get_value("Evaluation Case", {"tender_reference": REF, "state": "Report sent"}, ["name", "tender"], as_dict=True)
		if not case:
			raise unittest.SkipTest("the canonical evaluation is not seeded (make seed-canonical THROUGH=bid_evaluation)")
		cls.tender = case.tender
		cls.delivery = frappe.db.get_value("Evaluation Report Delivery", {"evaluation_case": case.name, "status": "Delivered"}, "name", order_by="delivered_at desc")

	def test_the_delivered_report_matches_the_synthetic_shape(self):
		real = sources.EvaluationSource().delivered_report(self.delivery)
		fake = syn.report("033", "TND-AWT-2100-033")
		self.assertTrue(real["digest_verified"])
		self.assertEqual((real["signatures"]["required"], real["signatures"]["signed"]), (3, 3))
		self.assertEqual(real["outcome"], "Recommendation")
		self.assertEqual(set(fake) - set(real) - {"world"}, set())
		self.assertEqual(set(fake["recommended"]) - set(real["recommended"]) - {"bidder_arrangement"}, set())
		rec = real["recommended"]
		self.assertEqual((rec["bidder"], rec["submitted_total"], rec["evaluated_total"], rec["quantity"], rec["warranty"]),
			("Afya Digital Supplies Limited", "46400000.00", "46400000.00", "250 Each", "36 months"))
		self.assertTrue(rec["organisation"])
		self.assertEqual(real["tender_title"], "Supply and delivery of business laptops")
		self.assertEqual(str(real["validity"]["validity_end"]), "2027-10-10 11:00:00")

	def test_the_bidder_audience_and_authority(self):
		p = sources.EvaluationSource()
		audience = p.audience(self.tender)
		self.assertEqual([(a["organisation_name"], a["status"]) for a in audience], [("Afya Digital Supplies Limited", "Submitted")])
		self.assertEqual(audience[0]["contact_email"], "tenders@afyadigital.example")
		org = audience[0]["organisation"]
		self.assertTrue(p.signatory(MARY, org, at=AT))
		self.assertIsNone(p.signatory(DAVID, org, at=AT))
		self.assertEqual(p.acting_for(DAVID, org, at=AT)["responsibility"], "Supplier Representative")
		self.assertEqual(p.notice_contact(audience[0]["bidder_arrangement"])["email"], "tenders@afyadigital.example")

	def test_tender_status_and_decision_status(self):
		from kentender_procurement.tenders.services import evaluation_seam

		p = sources.EvaluationSource()
		self.assertFalse(p.tender_facts(self.tender)["cancelled"])
		self.assertEqual(p.status_events(self.tender), [])
		self.assertIn(evaluation_seam.award_decision_status(self.tender)["status"], ("No award decision recorded", "Award decision recorded"))


class TestAudienceRule(IntegrationTestCase):
	"""AWD-AC-008: the audience comes from the sealed submission history — a
	replaced submission is notified once, for its final version; a withdrawn
	one is not a Submitted recipient. Bid Submission's sealed manifest is the
	external boundary here and is given directly."""

	def test_replacements_are_notified_once_and_withdrawals_not_at_all(self):
		from unittest.mock import patch

		from kentender_procurement.bid_submission.services import award_gateway, opening_gateway

		manifest = {"payload": {"envelopes": [
			{"bidder_arrangement": "ARR-A", "version_number": 1, "status": "Superseded", "submission_version": "A-1", "bid_reference": "BID-A"},
			{"bidder_arrangement": "ARR-A", "version_number": 2, "status": "Submitted", "submission_version": "A-2", "bid_reference": "BID-A"},
			{"bidder_arrangement": "ARR-B", "version_number": 1, "status": "Withdrawn", "submission_version": "B-1", "bid_reference": "BID-B"},
		]}}
		with patch.object(opening_gateway, "closed_manifest", return_value=manifest):
			rows = award_gateway.audience("ANY")
		by = {r["bidder_arrangement"]: r for r in rows}
		self.assertEqual(sorted(by), ["ARR-A", "ARR-B"])
		self.assertEqual((by["ARR-A"]["status"], by["ARR-A"]["submission_version"], by["ARR-A"]["replaced"]), ("Submitted", "A-2", ["A-1"]))
		self.assertEqual(by["ARR-B"]["status"], "Withdrawn")
