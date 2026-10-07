# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BDS-CHG-001 v0.8 §5.12, §5.13, §10.19 (plan Phase 10, BDS8-1001): each bid
next-step row — its kind, exact headline, stage markers and named holder —
computed on the server from the same checks the commands use, with every
Submit blocker returned together; and no answer leaves its viewer at a dead
end (KT-STD-001 v1.8 §3B.7). The operational holders are the current
Technical Operator and Release Operator (owner decision 27 Sep 2026)."""

from __future__ import annotations

from unittest import mock

import frappe
from kentender_core.services.command_write_guard import purge_doc

from kentender_core.services import next_step as ns

from kentender_procurement.bid_submission.services import guidance, labels, reads, simulation, submission
from kentender_procurement.bid_submission.test_services import trust
from kentender_procurement.bid_submission.tests.support import DAVID, MARY, NS, key
from kentender_procurement.bid_submission.tests.test_changes_and_close import ChangeCase

# Daniel Otieno (technical operator, KT-STD-001 v1.11 §8.3) and Nadia Kamau
# (release operator, v1.12 §8.3) are seeded by the site stage since 30 Sep
# 2026: the tests use those people (a second test user of the same name made
# the guidance name "Daniel Otieno, Daniel Otieno").
DANIEL, NADIA = "daniel.otieno@moh.example.test", "nadia.kamau@moh.example.test"
_CREATED: set[str] = set()


def _operators() -> None:
	from kentender_core.services import responsibility_administration as administration
	from kentender_core.services.business_role_registry import ensure_roles

	ensure_roles()
	for email, name, role, responsibility in ((DANIEL, "Daniel Otieno", "System Manager", guidance.TECHNICAL), (NADIA, "Nadia Kamau", "Desk User", guidance.RELEASE)):
		if not frappe.db.exists("User", email):
			first, _, last = name.partition(" ")
			user = frappe.get_doc({"doctype": "User", "email": email, "first_name": first, "last_name": last, "user_type": "System User", "send_welcome_email": 0}).insert(ignore_permissions=True)
			user.add_roles(role)
			_CREATED.add(email)
		if not frappe.db.exists("User Responsibility Assignment", {"user": email, "business_role": responsibility, "status": "Enabled"}):
			administration.grant(user=email, business_role=responsibility, fixture_namespace=NS, actor="Administrator")
	frappe.db.commit()


def _remove_operators() -> None:
	"""Only what these tests made: their own grants (stamped NS) and users
	they created. The register's people and their canonical roles stay."""
	frappe.db.delete("Notification Log", {"for_user": ("in", (DANIEL, NADIA))})
	for name in frappe.get_all("User Responsibility Assignment", filters={"user": ("in", (DANIEL, NADIA)), "fixture_namespace": NS}, pluck="name"):
		purge_doc("User Responsibility Assignment", name)
	for email in (DANIEL, NADIA):
		if email in _CREATED and frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	_CREATED.clear()
	frappe.db.commit()


class GuidanceCase(ChangeCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		_operators()
		cls.addClassCleanup(_remove_operators)

	def step(self, user):
		view = reads.get_bid_workspace(bid_reference=self.bid, user=user)
		self.assertEqual(ns.problems(view["next_step"]), [], view["next_step"])  # never a dead end
		return view["next_step"], "".join(r["marker"][0].upper() if r["marker"] != "not_started" else "N" for r in view["journey"]["stages"])

	def expect(self, user, kind, headline, markers, holder=None):
		answer, got = self.step(user)
		self.assertEqual((answer["kind"], answer["headline"]), (kind, headline))
		self.assertEqual(got, markers)
		if holder is not None:
			self.assertEqual(answer["holder"]["people"], holder)
		return answer

	def deadline_label(self):
		return labels.datetime_label(self.deadline())


class TestPreparationAndReadiness(GuidanceCase):
	def test_draft_ready_and_the_signatorys_turn(self):
		ready = self.expect(DAVID, ns.KIND_WAITING, "Authorised Signatory Mary Wanjiku must submit this bid.", "DCN", ["Mary Wanjiku"])
		self.assertIsNone(ready["since"])  # no ready-state instant is recorded
		self.expect(MARY, ns.KIND_YOUR_TURN, f"Review, sign and submit this bid before {self.deadline_label()}.", "DCN")
		journey = reads.get_bid_workspace(bid_reference=self.bid, user=MARY)["journey"]
		self.assertEqual(journey["reduced_text"], "Stage Sign and submit of 3")

	def test_a_draft_in_progress_names_its_task(self):
		from kentender_procurement.bid_submission.services import save

		field = next(f for g in reads.get_bid_task(bid_reference=self.bid, task="requirements", user=DAVID)["groups"] for f in g["fields"] if f["label"] == "Offered make and model")
		self.assertTrue(save.save_bid_task(bid_reference=self.bid, task="requirements", values={field["handle"]: None}, expected_record_version=self.version(), idempotency_key=key(), user=DAVID)["ok"])
		self.expect(DAVID, ns.KIND_YOUR_TURN, "Continue the requirements and supporting evidence task.", "CNN")

	def test_the_submit_guard_returns_every_blocker_together(self):
		trust.revoke_certificate(self.certificate)
		with mock.patch("kentender_core.services.public_portal.get_public_portal_information", return_value={"status": "Incomplete"}):
			guard = submission.get_submit_bid(bid_reference=self.bid, user=MARY)["submit_guard"]
		self.assertEqual({b["reason_code"] for b in guard["blockers"]}, {"BDS_PORTAL_INFORMATION_UNAVAILABLE", "BDS_SIGNATORY_CERTIFICATE_REQUIRED"})
		self.assertTrue(all(b["fixes"] for b in guard["blockers"]))


class TestSubmissionWorlds(GuidanceCase):
	def test_each_blocked_world_names_its_own_holder(self):
		trust.revoke_certificate(self.certificate)
		blocked = self.expect(MARY, ns.KIND_BLOCKED, "Obtain a valid digital signature certificate from an approved licensed certifying agency before submitting.", "DBN")
		self.assertEqual(blocked["fixes"][0]["fix_id"], "check_certificate")
		trust.issue_certificate(user=MARY, organisation="ORG-BDST-AFYA", subject_name="Mary Wanjiku", valid_from="2027-01-01 00:00:00", valid_to="2027-12-31 23:59:59")
		simulation.set_controls(gate_closed=1)
		self.expect(MARY, ns.KIND_WAITING, "Release operator Nadia Kamau holds the verified production-submission release.", "DBN", ["Nadia Kamau"])
		simulation.set_controls(gate_closed=0, trust_service_down=1)
		self.expect(MARY, ns.KIND_WAITING, "Technical operator Daniel Otieno is restoring digital signing.", "DBN", ["Daniel Otieno"])
		simulation.set_controls(trust_service_down=0, custody_service_down=1)
		self.expect(MARY, ns.KIND_WAITING, "Technical operator Daniel Otieno is restoring electronic submission.", "DBN")
		simulation.set_controls(custody_service_down=0)
		with mock.patch("kentender_core.services.public_portal.get_public_portal_information", return_value={"status": "Incomplete"}):
			self.expect(MARY, ns.KIND_WAITING, "CFG System Manager Daniel Otieno is restoring supplier portal information.", "DBN")

	def test_rejected_and_uncertain_attempts(self):
		simulation.set_controls(deposit_outcome="Reject")
		self.submit(self.signed())
		rejected = self.expect(MARY, ns.KIND_BLOCKED, "The tender box rejected this attempt; no bid was submitted.", "DBN")
		self.assertEqual([f["fix_id"] for f in rejected["fixes"]], ["submit_bid", "contact_support"])
		simulation.set_controls(deposit_outcome="Uncertain")
		self.submit(self.signed())
		for viewer in (MARY, DAVID):
			pending = self.expect(viewer, ns.KIND_WAITING, "Technical operator Daniel Otieno is checking the same submission attempt.", "DBN", ["Daniel Otieno"])
			self.assertEqual(pending["since"]["display"], "30 May 2027, 14:30 EAT")


class TestAfterSubmission(GuidanceCase):
	def test_submitted_replacement_withdrawn_and_closed(self):
		self.submitted()
		accepted = labels.datetime_seconds_label(frappe.db.get_value("Bid Submission Version", self.current()[1], "accepted_at"))
		options = self.expect(MARY, ns.KIND_YOUR_TURN, f"You may prepare a replacement or withdraw before {self.deadline_label()}. Version 1 remains submitted.", "DDD")
		self.assertEqual([f["fix_id"] for f in options["fixes"]], ["prepare_replacement", "withdraw_bid"])
		self.expect(DAVID, ns.KIND_DONE, f"Bid Version 1 was accepted on {accepted}.", "DDD")
		self.at("2027-05-31 08:30:00")
		self.replace()
		self.expect(MARY, ns.KIND_YOUR_TURN, "Finish and submit the replacement before the deadline. Version 1 remains submitted.", "CNN")
		self.expect(DAVID, ns.KIND_WAITING, "Authorised Signatory Mary Wanjiku must submit this bid.", "DCN")
		self.at(str(self.deadline()))
		self.expect(MARY, ns.KIND_DONE, f"Bid Version 1 remains submitted; submission changes closed at {self.deadline_label()}.", "DDD")

	def test_withdrawn_then_an_unsubmitted_draft_after_the_deadline(self):
		receipt = self.submitted()
		self.at("2027-05-30 15:00:00")
		self.withdraw(receipt=receipt)
		self.expect(MARY, ns.KIND_YOUR_TURN, "You may start a new bid before the deadline. This bid was withdrawn; no bid is currently submitted.", "DDD")
		self.at("2027-05-31 10:00:00")
		self.replace()
		self.at(str(self.deadline()))
		self.expect(MARY, ns.KIND_DONE, f"Submission closed at {self.deadline_label()}; this Draft was not submitted.", "DNN")
