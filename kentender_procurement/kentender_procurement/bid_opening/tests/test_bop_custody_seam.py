# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan D4 and D17 (BOP10-301): the Bid Submission
published seam for Bid Opening, against a real closed Tender built by the
Bid Submission test world, with the Test Tender Box. TRUST-ADR-001 v0.1 §2
proxy negative paths covered here: early attempt, one-member and
no-independent attempt, stale roster, invalid package. The proxy is a test
control, not the production key threshold."""

from __future__ import annotations

import hashlib

import frappe

from kentender_procurement.bid_opening.services import custody
from kentender_procurement.bid_submission.services import close, simulation as bds_simulation
from kentender_procurement.bid_submission.tests.support import key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase
from kentender_procurement.tenders.services import submission_close

CHAIR, MEMBER, INDEPENDENT = "bopt.chair@example.test", "bopt.member@example.test", "bopt.independent@example.test"
ROSTER = "roster-digest-1"


class SeamCase(SubmissionCase):
	def close_now(self):
		self.at(str(frappe.db.get_value("Tender", self.name, "submission_deadline")))
		submission_close.close_tender_submission_period(tender=self.name, idempotency_key=key(), user="Administrator")
		close.consume_tender_events(tender=self.name)

	def confirm(self, member, independent, manifest, roster=ROSTER):
		return custody.confirm_participation(tender=self.name, member=member, independent=independent, manifest_digest=manifest, roster_digest=roster,
			correlation_id=f"CUS-{member}")

	def reveal(self, envelope, manifest, roster=ROSTER):
		return custody.reveal(tender=self.name, envelope_id=envelope, manifest_digest=manifest, roster_digest=roster, correlation_id="REV-1")


class TestClosedManifest(SeamCase):
	def test_before_close_there_is_no_manifest_and_no_reveal(self):
		result = self.submit(self.signed())
		self.assertTrue(result["ok"], result)
		self.assertIsNone(custody.closed_manifest(self.name))
		self.assertEqual(self.reveal("ENV-ANY", "any")["outcome"], "Rejected")
		self.assertEqual(self.confirm(MEMBER, False, "any")["outcome"], "Rejected")

	def test_the_manifest_is_verified_and_acknowledged_once(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.close_now()
		manifest = custody.closed_manifest(self.name)
		self.assertEqual(manifest["digest"], hashlib.sha256(frappe.db.get_value("Bid Opening Handoff", manifest["handoff_id"], "payload_json").encode()).hexdigest())
		current = custody.current_envelopes(manifest)
		self.assertEqual([e["status"] for e in current], ["Submitted"])
		custody.acknowledge(manifest["handoff_id"])
		custody.acknowledge(manifest["handoff_id"])
		self.assertEqual(frappe.db.get_value("Bid Opening Handoff", manifest["handoff_id"], "delivery_status"), "Delivered")


class TestReveal(SeamCase):
	def setUp(self):
		super().setUp()
		self.assertTrue(self.submit(self.signed())["ok"])
		self.close_now()
		self.manifest = custody.closed_manifest(self.name)
		self.envelope = custody.current_envelopes(self.manifest)[0]
		self.addCleanup(lambda: bds_simulation.set_controls(reveal_outcome="Deliver"))

	def test_one_member_or_no_independent_member_cannot_release(self):
		self.assertEqual(self.confirm(CHAIR, False, self.manifest["digest"])["outcome"], "Accepted/Verified")
		self.assertEqual(self.reveal(self.envelope["envelope_id"], self.manifest["digest"])["outcome"], "Rejected")
		self.confirm(MEMBER, False, self.manifest["digest"])
		refused = self.reveal(self.envelope["envelope_id"], self.manifest["digest"])
		self.assertEqual((refused["outcome"], refused["reason"]), ("Rejected", "release_not_confirmed"))
		self.assertNotIn("package", refused)

	def test_two_distinct_members_including_the_independent_member_release_the_exact_package(self):
		self.confirm(CHAIR, False, self.manifest["digest"])
		self.confirm(INDEPENDENT, True, self.manifest["digest"])
		opened = self.reveal(self.envelope["envelope_id"], self.manifest["digest"])
		self.assertEqual(opened["outcome"], "Accepted/Verified")
		self.assertEqual(hashlib.sha256(opened["package"]).hexdigest(), self.envelope["package_digest"])
		self.assertEqual(opened["receipt_reference"], self.envelope["receipt_reference"])

	def test_a_changed_roster_or_manifest_makes_the_participation_stale(self):
		self.confirm(CHAIR, False, self.manifest["digest"])
		self.confirm(INDEPENDENT, True, self.manifest["digest"])
		self.assertEqual(self.reveal(self.envelope["envelope_id"], self.manifest["digest"], roster="roster-digest-2")["reason"], "release_not_confirmed")
		self.assertEqual(self.reveal(self.envelope["envelope_id"], "another-manifest")["outcome"], "Rejected")

	def test_an_unknown_envelope_or_a_mismatched_package_is_never_released(self):
		self.confirm(CHAIR, False, self.manifest["digest"])
		self.confirm(INDEPENDENT, True, self.manifest["digest"])
		self.assertEqual(self.reveal("ENV-NOT-IN-THE-BOX", self.manifest["digest"])["reason"], "not_current")
		bds_simulation.set_controls(reveal_outcome="Mismatch")
		mismatch = self.reveal(self.envelope["envelope_id"], self.manifest["digest"])
		self.assertEqual((mismatch["outcome"], mismatch["reason"]), ("Rejected", "package_mismatch"))
		self.assertNotIn("package", mismatch)
		for forced in ("Unavailable", "Indeterminate"):
			bds_simulation.set_controls(reveal_outcome=forced)
			self.assertEqual(self.reveal(self.envelope["envelope_id"], self.manifest["digest"])["outcome"], forced)
