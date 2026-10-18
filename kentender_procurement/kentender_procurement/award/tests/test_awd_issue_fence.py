# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The shared cancellation / first-notice fence and the three-phase issue
(AWD-CHG-001 v0.9 §5.4, §5.11 "One current fence", §7.2; TPR-CHG-001 v0.24
§5.12; AWD-OF-AC-005, AC-007).

One fence winner. The fence is the Tender-level authority record's row lock
(order: Tender → record → case). The worker commits "Issue in progress" under
it before the first outward effect, sends with no transaction or lock held, and
records the outcome afterwards. A queued issue that finds the cancellation
stamped sends nothing; an interrupted issue becomes Unknown, never Not issued
by timeout."""

from __future__ import annotations

from kentender_core.seeds.calendar import fiscal as F  # noqa: F401
from kentender_procurement.award.test_services.timeline import W  # noqa: F401
import frappe

from kentender_procurement.award.services import authority, issue_worker, notices, restrictions, simulation, state, tender_authority
from kentender_procurement.award.tests.support import AO, CASE, HOP, NS, AwardCase
from kentender_procurement.bid_submission.test_services import mailbox
from kentender_procurement.tests.two_connections import WAIT, Conn

RECIPIENTS = ("tenders@afyadigital.example", "tenders@jirani.example")


def _in_world():
	frappe.flags.kt_awd_fixture_namespace = NS
	frappe.flags.kt_awd_clock = W("2027-06-17 10:00:00")


def _sent() -> int:
	return sum(1 for m in mailbox._read() if m["to"] in RECIPIENTS)


def _recipients() -> int:
	"""The notices the batch carries: the ordinary world's one successful bidder and any unsuccessful ones."""
	return len(state.notices(frappe.get_doc(state.BATCH, frappe.get_all(state.BATCH, filters={"award_case": CASE}, pluck="name")[0])))


class FenceCase(AwardCase):
	"""An award recorded and its notices authorised, but not yet issued: the AO's request committed and the issue is still queued."""

	def setUp(self) -> None:
		super().setUp()
		mailbox.clear()
		simulation.set_controls(issue_deferred=1)
		self.deliver()
		self.tender = self.case().tender
		self.awarded()  # the decision commits; the issue stays queued
		frappe.db.commit()
		self.batch = self.case().current_batch or frappe.get_all(state.BATCH, filters={"award_case": CASE}, pluck="name")[0]

	def tearDown(self) -> None:
		mailbox.clear()
		super().tearDown()

	def batch_doc(self):
		return frappe.get_doc(state.BATCH, self.batch)

	def authority_status(self) -> str:
		return frappe.db.get_value(tender_authority.DOCTYPE, self.tender, "notification_status")


class TestQueuedIssue(FenceCase):
	def test_the_decision_leaves_the_batch_authorised_and_nothing_sent(self):
		self.assertEqual((self.batch_doc().state, self.authority_status(), _sent()), ("Authorised", "Not issued", 0))

	def test_the_queued_issue_runs_in_three_phases_and_replay_sends_nothing_more(self):
		first = issue_worker.run(self.batch, actor=AO)
		self.assertEqual(first["status"], "Issued")
		self.assertEqual((self.batch_doc().state, self.authority_status(), self.case().notification_status), ("Issued", "Issued", "Issued"))
		self.assertEqual(_sent(), _recipients())
		again = issue_worker.run(self.batch, actor=AO)
		self.assertEqual(again["status"], "Issued")
		self.assertEqual(_sent(), _recipients())

	def test_issue_in_progress_is_committed_and_no_lock_is_held_while_the_notice_is_sent(self):
		"""AWD §5.11: do not hold a database transaction open across an external send. At the moment of each send another connection reads the
		marker with a locking read: it must see "Issue in progress" (committed) and must not be blocked."""
		seen: list[tuple[str, str]] = []
		original = notices.send

		def probe(doc, n):
			conn = Conn("Administrator", lambda: (tender_authority.lock(self.tender).notification_status, frappe.get_doc(state.BATCH, self.batch).state), setup=_in_world)
			self.assertTrue(conn.finished.wait(WAIT), "the send held a lock on the Tender authority record")
			self.assertIsNone(conn.error, conn.error)
			seen.append(conn.value)
			return original(doc, n)

		notices.send = probe
		try:
			issue_worker.run(self.batch, actor=AO)
		finally:
			notices.send = original
		self.assertEqual(len(seen), _recipients())
		self.assertTrue(all(value == ("Issue in progress", "Issuing") for value in seen), seen)

	def test_the_after_commit_step_issues_once_the_decision_has_committed(self):
		simulation.set_controls(issue_deferred=0)
		mailbox.clear()
		# a second award case of this world is not needed: queue the existing batch the way the command does and commit
		frappe.db.after_commit.add(lambda: issue_worker.run(self.batch, actor=AO))
		self.assertEqual(_sent(), 0)
		frappe.db.commit()
		self.assertEqual((self.authority_status(), _sent()), ("Issued", _recipients()))


class TestCancellationFirst(FenceCase):
	def test_a_queued_issue_after_a_committed_cancellation_sends_nothing(self):
		tender_authority.record_cancellation(self.tender, cancellation_ref="TCN-QUEUED")
		frappe.db.commit()
		out = issue_worker.run(self.batch, actor=AO)
		self.assertEqual((out["status"], out["reasons"]), ("Stopped", ["cancelled"]))
		self.assertEqual((_sent(), self.authority_status(), self.batch_doc().state), (0, "Not issued", "Stopped"))
		self.assertIn("cancelled", cstr_(self.batch_doc().stop_reason))

	def test_a_cancellation_holding_the_record_lock_makes_a_waiting_issue_stop(self):
		"""Both orderings of the race, with real concurrency: the cancellation wins the lock first and has not committed; the issue waits on it, then
		sees the stamp as last committed and sends nothing."""
		frappe.db.commit()
		cancel = Conn("Administrator", lambda: tender_authority.record_cancellation(self.tender, cancellation_ref="TCN-RACE"), hold=True, setup=_in_world)
		self.assertTrue(cancel.ran.wait(WAIT))
		self.assertIsNone(cancel.error, cancel.error)
		issuing = Conn("Administrator", lambda: issue_worker.run(self.batch, actor=AO), setup=_in_world)
		self.assertFalse(issuing.finished.wait(1.5), "the issue must wait for the cancellation holding the fence")
		cancel.commit()
		self.assertTrue(issuing.finished.wait(WAIT))
		self.assertIsNone(issuing.error, issuing.error)
		self.assertEqual(issuing.value["status"], "Stopped")
		self.assertEqual(_sent(), 0)
		self.assertEqual(frappe.db.get_value(tender_authority.DOCTYPE, self.tender, "cancellation_ref"), "TCN-RACE")


class TestIssueFirst(FenceCase):
	def test_after_phase_one_the_fence_refuses_cancellation_and_names_the_award_owner(self):
		begun = issue_worker.begin(self.batch, actor=AO)
		self.assertEqual(begun["status"], "Started")
		frappe.db.commit()
		fence = authority.cancellation_fence(tender=self.tender)
		self.assertFalse(fence["allowed"])
		self.assertEqual([b["reason"] for b in fence["blockers"]], ["issue_in_progress"])
		self.assertTrue(fence["blockers"][0]["holder"])
		self.assertIn("pre-notification cancellation route is unavailable", authority.cancellation_guard(tender=self.tender))
		with self.assertRaises(Exception):
			tender_authority.record_cancellation(self.tender, cancellation_ref="TCN-LATE")
		issue_worker.finish(self.batch, token=begun["token"], actor=AO)
		self.assertEqual((authority.cancellation_fence(tender=self.tender)["blockers"][0]["reason"], self.authority_status()), ("issued", "Issued"))

	def test_a_cancellation_that_opened_its_snapshot_before_phase_one_committed_still_sees_it(self):
		"""AUD-XC-108 for the new fence: the cancellation's transaction already holds a snapshot when the issue commits Issue in progress; its locking
		read of the record must see the committed marker and refuse, not answer from the older snapshot."""
		frappe.db.commit()
		cancel = Conn("Administrator", lambda: authority.cancellation_fence(tender=self.tender), snapshot_first=True, setup=_in_world)
		self.assertTrue(cancel.snapshot_open.wait(WAIT))
		self.assertEqual(issue_worker.begin(self.batch, actor=AO)["status"], "Started")
		cancel.start_gate.set()
		self.assertTrue(cancel.finished.wait(WAIT))
		self.assertIsNone(cancel.error, cancel.error)
		self.assertFalse(cancel.value["allowed"])
		self.assertEqual(cancel.value["blockers"][0]["reason"], "issue_in_progress")


class TestInterruptedAndUncertain(FenceCase):
	def test_an_interrupted_issue_becomes_unknown_never_not_issued_and_still_blocks_cancellation(self):
		issue_worker.begin(self.batch, actor=AO)  # the process dies here: nothing else runs
		frappe.db.commit()
		self.at(W("2027-06-17 10:05:00"))
		self.assertEqual(issue_worker.sweep()["marked_unknown"], 0)
		self.assertEqual(self.authority_status(), "Issue in progress")
		self.at(W("2027-06-17 10:30:00"))
		self.assertEqual(issue_worker.sweep()["marked_unknown"], 1)
		self.assertEqual((self.authority_status(), self.case().notification_status), ("Unknown", "Unknown"))
		self.assertEqual(issue_worker.sweep()["marked_unknown"], 0)
		self.assertEqual(self.authority_status(), "Unknown")
		self.assertEqual([b["reason"] for b in authority.cancellation_fence(tender=self.tender)["blockers"]], ["status_unknown"])
		# the failed issue is visible to the Award owner as a worked issue, and nothing was sent
		self.assertEqual(_sent(), 0)
		self.assertTrue(frappe.get_all("Award Issue", filters={"award_case": CASE, "subtype": issue_worker.UNKNOWN_SUBTYPE, "state": "Open"}))

	def _unknown_issue(self) -> str:
		self.at(W("2027-06-17 10:30:00"))
		self.assertEqual(issue_worker.sweep()["marked_unknown"], 1)
		return frappe.get_all("Award Issue", filters={"award_case": CASE, "subtype": issue_worker.UNKNOWN_SUBTYPE, "state": "Open"}, pluck="name")[0]

	def test_no_notice_was_given_is_accepted_only_when_the_server_finds_nothing_published_or_attempted(self):
		issue_worker.begin(self.batch, actor=AO)  # the process died before it published anything
		frappe.db.commit()
		issue = self._unknown_issue()
		self.assertIn(issue_worker.NOT_GIVEN, restrictions.applicable(frappe.get_doc("Award Issue", issue)))
		out = self.run_as(HOP, restrictions.disposition, award=CASE, issue=issue, outcome=issue_worker.NOT_GIVEN, reason="Nothing left the server.",
			evidence="The batch has no published notice and no attempt.")
		self.assertTrue(out["ok"])
		self.assertEqual((self.authority_status(), self.batch_doc().state, self.batch_doc().status), ("Not issued", "Authorised", "Not issued"))
		self.assertEqual(issue_worker.run(self.batch, actor=AO)["status"], "Issued")
		self.assertEqual(_sent(), _recipients())

	def test_notices_were_given_needs_a_published_notice_and_no_notice_was_given_is_refused_when_one_was(self):
		begun = issue_worker.begin(self.batch, actor=AO)
		issue_worker.publish_and_send(self.batch, token=begun["token"], actor=AO)  # published and sent; the process died before the outcome was recorded
		frappe.db.commit()
		issue = self._unknown_issue()
		with self.assertRaises(Exception):
			self.run_as(HOP, restrictions.disposition, award=CASE, issue=issue, outcome=issue_worker.NOT_GIVEN, reason="We believe it was not sent.", evidence="A colleague says so.")
		self.assertEqual(self.authority_status(), "Unknown")
		out = self.run_as(HOP, restrictions.disposition, award=CASE, issue=issue, outcome=issue_worker.GIVEN, reason="The portal notices were published.",
			evidence="Each notice shows its portal publication.")
		self.assertTrue(out["ok"])
		self.assertEqual((self.authority_status(), self.batch_doc().state), ("Issued", "Issued"))
		self.assertFalse(authority.cancellation_fence(tender=self.tender)["allowed"])

	def test_a_second_worker_does_not_resume_an_issue_already_in_progress(self):
		issue_worker.begin(self.batch, actor=AO)
		frappe.db.commit()
		out = issue_worker.run(self.batch, actor=AO)
		self.assertEqual(out["status"], "Skipped")
		self.assertEqual(_sent(), 0)

	def test_an_uncertain_send_keeps_the_fence_and_is_reconciled_not_resent_silently(self):
		simulation.set_controls(email_outcome_unknown=1)
		out = issue_worker.run(self.batch, actor=AO)
		self.assertEqual(out["status"], "Issued")  # the portal notices are published: the Tender-level fact is Issued
		self.assertEqual(self.authority_status(), "Issued")
		self.assertFalse(authority.cancellation_fence(tender=self.tender)["allowed"])
		attempts = [a for n in state.notices(self.batch_doc()) for a in tender_authority.records.loads(n.attempts_json, [])]
		self.assertTrue(attempts and all(a["outcome"] == "Unknown" for a in attempts), attempts)
		self.assertTrue(frappe.get_all("Award Issue", filters={"award_case": CASE, "state": "Open"}))

	def test_a_retry_after_a_cancellation_stamp_sends_nothing(self):
		simulation.set_controls(email_service_down=1)
		issue_worker.run(self.batch, actor=AO)
		simulation.set_controls(email_service_down=0)
		mailbox.clear()
		frappe.db.set_value(tender_authority.DOCTYPE, self.tender, "cancellation_ref", "TCN-STALE-VIEW")  # a view that lags the stamp
		doc = self.case()
		failed = [n for n in state.notices(self.batch_doc()) if n.status == "Failed"]
		self.assertTrue(failed)
		for n in failed:
			notices.retry(doc, n, actor="system")
		self.assertEqual(_sent(), 0)


def cstr_(value) -> str:
	return "" if value is None else str(value)
