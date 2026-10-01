# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DeliverAwardPackage (AWD-CHG-001 v0.4 §5.8; AWD-AC-019–021; tracker AWD4-703)."""

from __future__ import annotations

import frappe

from kentender_procurement.award.services import eligibility, restrictions, simulation, state, supplier
from kentender_procurement.award.tests.support import HOP, MARY, AwardCase


class TestDelivery(AwardCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.awarded()
		notice = state.successful_notice(state.current_batch(self.case()))
		self.at("2027-06-18 09:00:00")
		self.run_as(MARY, supplier.respond, notice=notice.name, response="Accept", notice_version=1)
		self.at("2027-07-02 09:00:00")

	def test_delivered(self):
		eligibility.refresh_case(self.case().name)
		doc = self.case()
		pkg = eligibility.current_package(doc)
		self.assertEqual((doc.stage, pkg.status, pkg.recipient_user), ("Sent to Contracting", "Delivered", HOP))
		content = frappe.parse_json(pkg.content_json)
		self.assertEqual((content["decision"]["submitted_amount"], content["contract_terms"]["warranty"], content["contract_terms"]["quantity"]),
			("46400000.00", "36 months", "250 Each"))
		self.assertEqual(frappe.db.count("Award Test Contracting Inbox", {"award_case": doc.name, "kind": "Package", "task_state": "Open"}), 1)

	def test_receiver_down(self):
		simulation.set_controls(contracting_down=1)
		out = eligibility.refresh_case(self.case().name)
		doc = self.case()
		self.assertEqual((out["stage"], eligibility.current_package(doc).status), ("Waiting to proceed", "Failed"))
		self.assertTrue(frappe.db.exists("Support Issue", {"module": "Award", "subject": "Restore Contracting delivery", "status": "Open"}))
		digest = eligibility.current_package(doc).digest
		# a restriction arising during the outage blocks the retry after service returns
		self.run_as(HOP, restrictions.record_external, award=doc.name, basis="Reported challenge", source="Complaint letter", received_at="2027-07-02 09:10:00",
			reason="A bidder reported a challenge.")
		simulation.set_controls(contracting_down=0)
		self.assertEqual(eligibility.refresh_case(doc.name)["stage"], "Waiting to proceed")
		self.assertEqual(eligibility.current_package(self.case()).status, "Held")
		self.assertEqual(eligibility.current_package(self.case()).digest, digest)

	def test_later_restriction_reaches_contracting_without_rewriting_the_package(self):
		eligibility.refresh_case(self.case().name)
		pkg = eligibility.current_package(self.case())
		before = pkg.digest
		self.run_as(HOP, restrictions.record_external, award=self.case().name, basis="Authoritative order", source="Review Board suspension notice",
			received_at="2027-07-03 11:00:00", evidence="PPARB/2027/33", reason="The Review Board suspended the procurement.")
		pkg = frappe.get_doc(state.PACKAGE, pkg.name)
		self.assertEqual((pkg.digest, len(frappe.parse_json(pkg.updates_json))), (before, 1))
		self.assertEqual(self.case().stage, "Sent to Contracting")
		self.assertEqual(frappe.db.count("Award Test Contracting Inbox", {"award_case": self.case().name, "kind": "Update"}), 1)
