# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 section 19.4 (plan D20; tracker CM8-513, CM8-517, CM8-520; gate CM-G05): is every source the canonical award's agreement is made from available and verified through the real providers?

Level L2: no synthetic source. The canonical laptop award (AWD-MOH-2026-002, tender TND-MOH-2026-002, Afya Digital Supplies Limited, KES 46,400,000) is read through the core source seam, to which Award's provider
answers by asking Tenders, Bid Evaluation, the site configuration, Supplier Accounts and Budget through their published seams (Award's own side is tested in `award/tests/test_contract_sources.py`). Contract Management
imports none of them: this module uses the core seam and the award's own records. The assertions are the **present truth**, source by source, including the gaps: an unavailable source
blocks formation, and the reason and the owner are what the head of procurement sees. When an owner closes a gap this test is changed with it, in the open; it is not a test that passes by ignoring one.

The gaps this run shows (owner and what is needed):

* S7 Form No. 4: the issued template declares no place to fill (its blanks are plain underscores) so no agreement can be generated from it. The template owner declares the insertions (CM-TPL-01).
* S9 funding: the award draws on two reservations and no funding owner has allocated the awarded price between them. Budget or Award decides how (owner decision).
* S10 entity: the principal address is not held in the entity's site configuration. The configuration owner records it once (the field now exists)."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
import json
import unittest
import unittest.mock

import frappe

from kentender_contracts import award_receiver as receiving
from kentender_contracts.boards import router
from kentender_contracts.services import availability, errors, formation, source_package
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase
from kentender_core.services import contract_source_contract as seam

AWARD = "AWD-MOH-2026-002"
GAPS = {"S7", "S10"}  # S9, the funding lineage, is served by Award since AWD v0.7 section 7.1 (commit 478512c6): it was a gap here until then


class TestCanonicalSources(ContractCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Award Case", AWARD):
			raise unittest.SkipTest("the canonical award is not on this site")
		if not frappe.db.get_single_value("Site Procuring Entity", "pe_name"):
			raise unittest.SkipTest("the site has no procuring entity")
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.previous = frappe.flags.get("kt_cm_clock")
		frappe.flags.kt_cm_clock = D("2027-07-02 09:00:00")
		self.addCleanup(lambda: setattr(frappe.flags, "kt_cm_clock", self.previous))

	def rows(self):
		return {r["source"]: r for r in availability.report(AWARD)["sources"]}

	def test_every_source_the_owners_can_give_is_available_and_verified_and_the_rest_say_why(self):
		report = availability.report(AWARD)
		by = {r["source"]: r for r in report["sources"]}
		self.assertEqual([r["source"] for r in report["sources"]], [f"S{n}" for n in range(1, 13)])
		self.assertEqual({n for n, r in by.items() if not r["verified"]}, GAPS, "exactly these sources are not yet formable")
		self.assertFalse(report["formable"], "formation is not accepted while a source is missing")
		for number, row in by.items():
			if number in GAPS:
				self.assertTrue(row["reason"] and row["owner"], f"{number} says why and whose it is")
			else:
				self.assertTrue(row["available"] and not row["reason"], number)
		self.assertIn("declares no place to fill", by["S7"]["reason"])
		self.assertTrue(by["S9"]["available"] and not by["S9"]["reason"], "the funding lineage is served by Award (AWD v0.7 section 7.1)")
		self.assertIn("principal address", by["S10"]["reason"])
		self.assertEqual((by["S7"]["owner"], by["S10"]["owner"]), ("Tenders and the template release", "Site configuration"))

	def test_a_source_that_changed_after_the_award_is_seen(self):
		rows = seam.handoff(AWARD)
		s1 = next(r for r in rows if r["source"] == "S1")
		self.assertEqual(source_package.gather([{**s1, "sha256": "0" * 64}])["failed"][0]["reason"], "It changed after the award was made.")

	def package(self):
		"""The package Award would deliver, rebuilt from the award's own records (Contract Management never imports Award's code): the keys Contracting reads, and the references Award froze."""
		award = frappe.get_doc("Award Case", AWARD)
		decision = frappe.get_all("Award Decision", filters={"award_case": AWARD, "committed": 1}, fields=["name", "version", "outcome", "supplier_name", "supplier_organisation", "bid_reference", "submitted_amount",
			"evaluated_amount", "currency"], order_by="version desc", limit=1)[0]
		recommended = json.loads(frappe.db.get_value("Award Source Report", award.current_report, "snapshot_json") or "{}").get("recommended") or {}
		return {"award_case": AWARD, "tender": award.tender, "tender_reference": award.tender_reference, "lot": award.lot, "cycle": 1, "reference": f"{AWARD}-PKG-TEST", "package_digest": "e" * 64,
			"decision": {"id": decision.name, "version": decision.version, "outcome": decision.outcome, "supplier": decision.supplier_name, "organisation": decision.supplier_organisation, "bid": decision.bid_reference,
				"submitted_amount": decision.submitted_amount, "evaluated_amount": decision.evaluated_amount, "currency": decision.currency},
			"contract_terms": {"quantity": recommended.get("quantity", ""), "warranty": recommended.get("warranty", "")}, "restrictions": [], "legal_profile": "", "fixture_namespace": "CM_TEST", "handoff": seam.handoff(AWARD),
			"managing_unit": frappe.db.get_value("Procurement Requisition", frappe.db.get_value("Tender", award.tender, "requisition"), "lead_org_unit_id")}

	def test_the_canonical_package_reaches_contract_management_and_the_head_of_procurement_sees_the_gaps(self):
		package = self.package()
		self.assertTrue(package["managing_unit"])
		self.assertEqual(len(package["handoff"]), 12)
		with unittest.mock.patch.object(receiving, "answers", return_value=True):
			receipt = receiving.Receiver().receive_package(package)
		case = receipt["contract"]
		self.assertEqual(frappe.db.get_value("Contract Case", case, ["source_reference", "managing_unit", "supplier_name"], as_dict=True),
			{"source_reference": AWARD, "managing_unit": package["managing_unit"], "supplier_name": "Afya Digital Supplies Limited"})
		board = router.board_for(case, self.people["charles"])
		self.assertEqual((board["id"], board["p"]), ("D02", ""), "no agreement is offered for signature")
		self.assertEqual(board["next"]["k"], "blk")
		table = board["regions"][0]["b"][0]
		self.assertEqual({row[0] for row in table["rows"]}, GAPS)
		with self.assertRaises(errors.ContractError) as caught:
			formation.save_particulars(case, expected_version=frappe.db.get_value("Contract Case", case, "record_version"), idempotency_key="sources-1", actor=self.people["charles"], values={})
		self.assertEqual(caught.exception.code, "CM_SOURCE")
		self.assertEqual({f["source"] for f in caught.exception.detail["failed"]}, GAPS)
