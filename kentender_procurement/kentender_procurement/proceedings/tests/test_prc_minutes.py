# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PRC-CHG-001 v0.9 §5 freeze/supersede/attest/finalize/supplement against the
simulated owner (BOP10-203): PRC-S02, PRC-N02, PRC-N04, PRC-N05, PRC-N06,
PRC-N07. Test attestations are not electronic signatures (TRUST-ADR-001 v0.1
§2); these are shared-service contract results only."""

from __future__ import annotations

import frappe

from kentender_procurement.proceedings.tests.support import (
	CHAIR, INDEPENDENT, MEMBER, OUTSIDER, OWNER_TYPE, ProceedingsCase, attestation, finalize, minutes, reads,
)


class TestHappyPath(ProceedingsCase):
	def test_prc_s02_start_to_finalized(self):
		created = self.create()
		self.start(created)
		self.at("2027-06-12 11:01:00")
		reveal = self.owner_event(created, "PackageRevealed", "reveal-1")
		self.at("2027-06-12 11:01:45")
		self.owner_event(created, "ReadoutConfirmed", "readout-1", linked_event=reveal["event_id"])
		self.end(created)
		frozen = self.freeze(created)
		self.assertEqual((frozen["version_number"], frappe.db.get_value("Proceeding", created["proceeding"], "state")), (1, "Awaiting attestations"))
		self.attest_all(created, self.current_minutes(created))
		self.at("2027-06-12 11:10:30")
		done = finalize.finalize_proceeding(**self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)
		self.assertEqual(done["state"], "Finalized")
		row = frappe.db.get_value("Proceeding", created["proceeding"], ["finalized_at"], as_dict=True)
		self.assertEqual(str(row.finalized_at), "2027-06-12 11:10:30")
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", frozen["minutes_version"], "state"), "Finalized")
		self.assertCode("PRC_ALREADY_FINALIZED", self.owner_event, created, "LateFact", "late-1")
		self.assertCode("PRC_ALREADY_FINALIZED", minutes.supersede_minutes, **self.ref(created), reason="x", content="y", page_count=1, register_reference="R",
			register_digest="d", event_ids=[], targets=self.targets(), idempotency_key=self.key(), actor=CHAIR)

	def test_frozen_html_content_is_stored_exactly_and_its_digest_still_verifies(self):
		"""The opening record is HTML; saving must not rewrite it (Frappe's HTML
		sanitiser would), or the frozen digest no longer matches (found in Bid
		Opening Phase 6)."""
		created = self.create()
		self.start(created)
		self.end(created)
		html = "<html><head><style>td{border:1px solid #999}</style></head><body><h1>Opening record</h1><table><tr><td>Test</td></tr></table></body></html>"
		frozen = self.freeze(created, content=html)
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", frozen["minutes_version"], "content"), html)
		self.attest_all(created, self.current_minutes(created))
		finalize.finalize_proceeding(**self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)
		owner_id = frappe.db.get_value("Proceeding", created["proceeding"], "owner_id")
		self.assertTrue(reads.export_proceeding(owner_type=OWNER_TYPE, owner_id=owner_id, user=CHAIR)["original_digest_verified"])

	def test_the_frozen_digest_is_the_content_digest(self):
		created = self.create()
		self.start(created)
		self.end(created)
		frozen = self.freeze(created, content="Exact minutes text")
		import hashlib

		self.assertEqual(frozen["content_digest"], hashlib.sha256("Exact minutes text".encode()).hexdigest())


class TestTargets(ProceedingsCase):
	def ready(self):
		created = self.create()
		self.start(created)
		self.end(created)
		self.freeze(created)
		return created, self.current_minutes(created)

	def test_prc_n02_a_proof_on_an_obsolete_digest_is_rejected_and_the_prior_proof_stays(self):
		created, version = self.ready()
		mine = [t for t in version["targets"] if t["required_member"] == MEMBER]
		first = attestation.attest_target(**self.ref(created), minutes_version=version["minutes_version"], target_id=mine[0]["target_id"],
			target_digest=mine[0]["target_digest"], action="Initial", idempotency_key=self.key(), actor=MEMBER)
		self.assertTrue(first["ok"])
		self.assertCode("PRC_TARGET_CHANGED", attestation.attest_target, **self.ref(created), minutes_version=version["minutes_version"], target_id=mine[1]["target_id"],
			target_digest="an-obsolete-digest", action="Initial", idempotency_key=self.key(), actor=MEMBER)
		self.assertEqual(frappe.db.count("Proceeding Attestation", {"proceeding": created["proceeding"], "member_user": MEMBER}), 1)

	def test_no_proxy_and_no_outsider_can_attest(self):
		created, version = self.ready()
		theirs = next(t for t in version["targets"] if t["required_member"] == MEMBER)
		for actor in (CHAIR, OUTSIDER, "Administrator"):
			with self.subTest(actor=actor):
				self.assertCode("PRC_MEMBER_REQUIRED", attestation.attest_target, **self.ref(created), minutes_version=version["minutes_version"], target_id=theirs["target_id"],
					target_digest=theirs["target_digest"], action="Initial", idempotency_key=self.key(), actor=actor)

	def test_prc_n04_unverified_proof_is_recorded_and_blocks_completion(self):
		created, version = self.ready()
		self._flag("kt_prc_signing_outcome", "Rejected")
		target = next(t for t in version["targets"] if t["required_member"] == INDEPENDENT)
		out = attestation.attest_target(**self.ref(created), minutes_version=version["minutes_version"], target_id=target["target_id"],
			target_digest=target["target_digest"], action="Initial", idempotency_key=self.key(), actor=INDEPENDENT)
		self.assertEqual((out["ok"], out["code"]), (False, "PRC_PROOF_UNVERIFIED"))
		self.assertEqual(frappe.db.get_value("Proceeding Attestation", {"proceeding": created["proceeding"], "member_user": INDEPENDENT}, ["verification_result", "satisfies_current"]),
			("Rejected", 0))
		self._flag("kt_prc_signing_outcome", None)
		error = self.assertCode("PRC_EVIDENCE_INCOMPLETE", finalize.finalize_proceeding, **self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)
		self.assertEqual(len(error.detail["missing"]), len(version["targets"]))

	def test_prc_n04_an_unfinished_session_or_missing_owner_event_blocks(self):
		created = self.create()
		self.start(created)
		self.assertCode("PRC_VERSION_CONFLICT", finalize.finalize_proceeding, **self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)
		self.assertCode("PRC_VERSION_CONFLICT", self.freeze, created)
		self.owner_event(created, "PackageRevealed", "reveal-1")
		self.end(created)
		error = self.assertCode("PRC_EVIDENCE_INCOMPLETE", minutes.freeze_minutes, **self.ref(created), content="c", page_count=1, register_reference="R",
			register_digest="d", event_ids=[], targets=self.targets(), idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(len(error.detail["missing_events"]), 1)
		self.assertCode("PRC_MEMBER_REQUIRED", self.freeze, created, targets=[self.targets()[0] | {"required_member": OUTSIDER}])
		self.assertEqual(frappe.db.count("Proceeding Minutes Version", {"proceeding": created["proceeding"]}), 0)


class TestSupersede(ProceedingsCase):
	def test_prc_n06_superseding_keeps_old_proof_and_needs_fresh_proofs(self):
		created = self.create()
		self.start(created)
		self.end(created)
		self.freeze(created)
		v1 = self.current_minutes(created)
		self.attest_all(created, v1, members=(MEMBER,))
		self.assertCode("PRC_EVIDENCE_INCOMPLETE", minutes.supersede_minutes, **self.ref(created), reason="", content="v2", page_count=1, register_reference="R",
			register_digest="d", event_ids=[], targets=self.targets(prefix="V2"), idempotency_key=self.key(), actor=CHAIR)
		self.at("2027-06-12 11:08:45")
		v2_out = minutes.supersede_minutes(**self.ref(created), reason="Add the attendee’s repeat request and the chair’s response", content="Test minutes version 2",
			page_count=1, register_reference="R", register_digest="d", event_ids=[], targets=self.targets(prefix="V2"), idempotency_key=self.key(), actor=CHAIR)
		self.assertEqual(v2_out["version_number"], 2)
		self.assertEqual(frappe.db.get_value("Proceeding Minutes Version", v1["minutes_version"], "state"), "Superseded")
		old = frappe.get_all("Proceeding Attestation", filters={"proceeding": created["proceeding"], "member_user": MEMBER}, fields=["satisfies_current", "minutes_version"])
		self.assertEqual({(o.minutes_version, o.satisfies_current) for o in old}, {(v1["minutes_version"], 0)})
		stale = next(t for t in v1["targets"] if t["required_member"] == MEMBER)
		self.assertCode("PRC_TARGET_CHANGED", attestation.attest_target, **self.ref(created), minutes_version=v1["minutes_version"], target_id=stale["target_id"],
			target_digest=stale["target_digest"], action="Initial", idempotency_key=self.key(), actor=MEMBER)
		error = self.assertCode("PRC_EVIDENCE_INCOMPLETE", finalize.finalize_proceeding, **self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)
		self.assertEqual(len(error.detail["missing"]), 6)
		v2 = self.current_minutes(created)
		self.attest_all(created, v2)
		self.assertEqual(finalize.finalize_proceeding(**self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)["state"], "Finalized")


class TestSupplementAndExport(ProceedingsCase):
	def test_prc_n05_a_correction_is_a_supplement_and_the_original_export_is_unchanged(self):
		created = self.create()
		self.start(created)
		self.end(created)
		self.freeze(created)
		self.attest_all(created, self.current_minutes(created))
		finalize.finalize_proceeding(**self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)
		owner_id = frappe.db.get_value("Proceeding", created["proceeding"], "owner_id")
		before = reads.export_proceeding(owner_type=OWNER_TYPE, owner_id=owner_id, user=CHAIR)
		self.at("2027-06-12 11:15:00")
		key = self.key()
		args = dict(original_version=1, kind="Attendance note", correct_information="Test Visitor left at 11:03 EAT", reason="Add the departure noted during the opening",
			idempotency_key=key, actor=CHAIR)
		added = finalize.append_supplement(**self.ref(created), **args)
		finalize.append_supplement(**(self.ref(created) | {"expected_version": added["record_version"] - 1}), **args)
		after = reads.export_proceeding(owner_type=OWNER_TYPE, owner_id=owner_id, user=CHAIR)
		self.assertEqual(before["original"], after["original"])
		self.assertTrue(after["original_digest_verified"])
		self.assertEqual([s["correct_information"] for s in after["supplements"]], ["Test Visitor left at 11:03 EAT"])
		self.assertEqual(after["supplements"][0]["author"], CHAIR)

	def test_a_supplement_needs_a_finalized_record_and_a_reason(self):
		created = self.create()
		self.start(created)
		self.assertCode("PRC_VERSION_CONFLICT", finalize.append_supplement, **self.ref(created), original_version=1, kind="Attendance note", correct_information="x",
			reason="y", idempotency_key=self.key(), actor=CHAIR)


class TestZeroAndNeverHeld(ProceedingsCase):
	def test_prc_n07_a_convened_zero_bid_session_completes_with_an_opening_record(self):
		created = self.create()
		self.start(created)
		self.end(created, outcome_event={"event_type": "NoBidsOutcome", "owner_event_id": "zero-1", "payload": {"count": 0}})
		one_page = [{"target_id": f"REC-{m.split('@')[0]}", "target_type": "Final minutes page", "target_reference": "TEST-OPENING-RECORD", "page_number": 1,
			"target_digest": "one-page-digest", "required_member": m, "roster_segment": 1} for m in (CHAIR, MEMBER, INDEPENDENT)]
		self.freeze(created, targets=one_page)
		self.attest_all(created, self.current_minutes(created))
		self.assertEqual(finalize.finalize_proceeding(**self.ref(created), idempotency_key=self.key(), actor=finalize.SYSTEM_ACTOR)["state"], "Finalized")
		self.assertIsNotNone(frappe.db.get_value("Proceeding", created["proceeding"], "actual_start"))
