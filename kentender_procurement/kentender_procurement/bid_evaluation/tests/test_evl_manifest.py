# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The evidence manifest of a report version (OVS-CHG-001 v0.6 §3, §7, §15;
plan D3, D16, D18; owner approval 4 Oct 2026; tracker OVS6-0205, OVS6-0213,
OVS6-0214; acceptance OVS-AC-005, OVS-AC-006, OVS-AC-009).

A delivered version lists the bids it evaluated and every document they
submitted, cited by a finding or not, with its own digest. The Accounting
Officer and the Head of Procurement Function open a bid's detail or one
document only through that list, so a later submission or an unfinished
correction never inherits the disclosure. A version delivered before
manifests existed is reconstructed and labelled."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import correction, evidence_manifest, reads, simulation
from kentender_procurement.bid_evaluation.tests.support import AO, AUDITOR, HOP, MEMBER, OUTSIDER
from kentender_procurement.bid_evaluation.tests.test_evl_oversight import BIDDER, OversightCase
from kentender_procurement.bid_submission.tests.support import key


class ManifestCase(OversightCase):
	def first_version(self) -> str:
		return frappe.db.get_value("Evaluation Report Version", {"evaluation_case": self.case, "version_number": 1}, "name")

	def bid_name(self) -> str:
		return frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")


class TestManifestAtFreeze(ManifestCase):
	def test_a_frozen_version_lists_its_bids_and_every_submitted_document(self):
		self.deliver()
		version = self.first_version()
		row = frappe.db.get_value("Evaluation Report Version", version, ["evidence_manifest_basis", "evidence_manifest_digest"], as_dict=True)
		self.assertEqual(row.evidence_manifest_basis, "Frozen at signing")
		manifest = evidence_manifest.of(version)
		self.assertIsNotNone(manifest)  # present and matching its recorded digest
		self.assertEqual(evidence_manifest.digest(manifest), row.evidence_manifest_digest)
		bid = frappe.get_doc("Evaluation Bid", self.bid_name())
		entry = manifest["bids"][0]
		self.assertEqual((entry["bid"], entry["submission_version"], entry["receipt_reference"], entry["package_digest"]),
			(bid.name, bid.submission_version, bid.receipt_reference, bid.package_digest))
		# every document of the package, not only those a finding cites
		cited = {e["digest"] for r in reads.bid(tender_reference=self.reference, bid=bid.name, user=MEMBER)["requirements"] for e in r["evidence"]}
		listed = {d["file_digest"] for d in manifest["documents"][bid.name]}
		self.assertTrue(cited)
		self.assertTrue(cited <= listed)
		for d in manifest["documents"][bid.name]:
			self.assertTrue(d["filename"] and d["media_type"] and d["size_bytes"] > 0, d)
		self.assertIn("handoff_digest", manifest["intake"])

	def test_the_manifest_holds_the_committee_record_items_the_report_does_not(self):
		self.deliver()
		record = evidence_manifest.of(self.first_version())["committee_record"]
		self.assertEqual(set(record), {"declarations", "conclusions", "sessions", "clarification_replies", "notes"})
		self.assertTrue(record["declarations"])
		# a conflict's description never enters the manifest
		self.assertTrue(all("description" not in d for d in record["declarations"]))

	def test_a_package_that_cannot_be_read_refuses_the_freeze_and_leaves_no_trace(self):
		self.evl_ready()
		frappe.local.kt_evl_packages = {}  # the packages read earlier in this request are not reused
		simulation.set_controls(intake_outcome="Unavailable")
		try:
			self.assertEqual(self.refused(self.evl_freeze).code, "EVL_SOURCE_INCOMPLETE")
		finally:
			simulation.set_controls(intake_outcome="")
			frappe.local.kt_evl_packages = {}
		self.assertEqual(self.evl_doc().state, "Reviewing")
		self.assertFalse(frappe.db.exists("Evaluation Report Version", {"evaluation_case": self.case, "state": "Signing"}))


class TestOversightOpensOnlyWhatTheManifestLists(ManifestCase):
	def setUp(self):
		super().setUp()
		self.deliver()
		self.version = self.first_version()
		self.bid = self.bid_name()
		self.digest = evidence_manifest.of(self.version)["documents"][self.bid][0]["file_digest"]

	def test_the_accounting_officer_and_the_head_read_a_bid_and_its_documents(self):
		for user in (AO, HOP):
			detail = reads.delivered_bid(tender_reference=self.reference, bid=self.bid, user=user)
			self.assertEqual(detail["bidder"], BIDDER, user)
			self.assertEqual(detail["report"], self.version, user)
			self.assertTrue(detail["findings"]["eligibility"] or detail["findings"]["technical"], user)  # from the frozen content
			self.assertTrue(detail["documents"], user)
			file = reads.evidence(tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user)
			self.assertTrue(file["content"], user)
			self.assertEqual(reads.evidence(tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user, version=self.version)["content"], file["content"])

	def test_a_document_or_bid_the_manifest_does_not_list_is_not_found(self):
		for user in (AO, HOP):
			self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest="0" * 64, user=user)
			self.not_found(reads.delivered_bid, tender_reference=self.reference, bid="NO-SUCH-BID", user=user)
			self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user, version="NO-SUCH-VERSION")

	def test_a_document_in_the_live_package_but_not_in_the_manifest_is_not_found(self):
		# a later addition to the package must not inherit the earlier delivery's disclosure
		manifest = evidence_manifest.of(self.version)
		manifest["documents"][self.bid] = [d for d in manifest["documents"][self.bid] if d["file_digest"] != self.digest]
		frappe.db.set_value("Evaluation Report Version", self.version, evidence_manifest.values(manifest, "Frozen at signing"))
		self.assertIsNotNone(evidence_manifest.of(self.version))  # still a valid manifest
		self.assertTrue(reads.evidence(tender_reference=self.reference, bid=self.bid, digest=self.digest, user=MEMBER)["content"])  # the live case still has it
		for user in (AO, HOP):
			self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user)
			self.assertNotIn(self.digest, [d["digest"] for d in reads.delivered_bid(tender_reference=self.reference, bid=self.bid, user=user)["documents"]])

	def test_nobody_outside_the_two_offices_and_the_committee_is_given_a_bid(self):
		self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=self.bid, user=OUTSIDER)
		self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest=self.digest, user=OUTSIDER)
		for user in (MEMBER, AUDITOR):  # the committee reads the live case; the delivered-bid view is the offices'
			self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=self.bid, user=user)

	def test_a_manifest_that_no_longer_matches_its_digest_opens_nothing(self):
		frappe.db.set_value("Evaluation Report Version", self.version, "evidence_manifest_digest", "f" * 64)
		self.assertIsNone(evidence_manifest.of(self.version))
		for user in (AO, HOP):
			self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=self.bid, user=user)
			self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user)

	def test_a_version_in_signing_or_a_correction_is_never_opened(self):
		correction.return_report(tender=self.name, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=key(), user=HOP)
		self.evl_freeze()
		from kentender_procurement.bid_evaluation.services import signing

		corrected = signing.signing_version(self.evl_doc()).name
		self.assertTrue(evidence_manifest.of(corrected))  # the correction has its own manifest, written at its own freeze
		for user in (AO, HOP):
			self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user, version=corrected)
			self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=self.bid, user=user, version=corrected)
			# the earlier delivered version keeps opening
			self.assertTrue(reads.evidence(tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user, version=self.version)["content"])

	def test_before_delivery_nothing_opens(self):
		# a different case state: a version still out for signature
		frappe.db.set_value("Evaluation Report Delivery", {"evaluation_case": self.case}, "status", "Pending")
		for user in (AO, HOP):
			self.not_found(reads.delivered_bid, tender_reference=self.reference, bid=self.bid, user=user)
			self.not_found(reads.evidence, tender_reference=self.reference, bid=self.bid, digest=self.digest, user=user)


class TestBackfill(ManifestCase):
	def test_a_version_delivered_before_manifests_existed_is_reconstructed_and_labelled(self):
		self.deliver()
		version = self.first_version()
		original = evidence_manifest.of(version)
		doc = frappe.get_doc("Evaluation Report Version", version)
		doc.flags.kt_evl_command = True
		doc.update({"evidence_manifest_json": "", "evidence_manifest_digest": "", "evidence_manifest_basis": ""})
		doc.save(ignore_permissions=True)
		self.assertIsNone(evidence_manifest.of(version))
		self.assertTrue(evidence_manifest.backfill(version))
		row = frappe.db.get_value("Evaluation Report Version", version, "evidence_manifest_basis")
		self.assertEqual(row, "Reconstructed after delivery")
		rebuilt = evidence_manifest.of(version)
		self.assertEqual(rebuilt["bids"], original["bids"])
		self.assertEqual(rebuilt["documents"], original["documents"])
		self.assertFalse(evidence_manifest.backfill(version))  # safe to run again
		self.assertEqual(reads.delivered_bid(tender_reference=self.reference, bid=self.bid_name(), user=AO)["basis"], "Reconstructed after delivery")
