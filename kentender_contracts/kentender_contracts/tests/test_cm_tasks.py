# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §6.3 and §6.4 (tracker CM8-312; CM-AC-59 started): one logical item per command subject, version and required holder; the actor's actionable work is
ordered protective deadline at risk, other verified overdue, earliest verified upcoming, then undated by assignment instant and stable id; a blocked duty stays visible with
its fix owner and cannot hide actionable work; waiting and scheduled rows sit below; an unknown date says Not established; the leading item is not repeated in Other work."""

from __future__ import annotations

from datetime import datetime, timedelta

from frappe.tests import IntegrationTestCase

from kentender_contracts.services import next_steps, tasks

NOW = datetime(2027, 7, 22, 10, 0)


def task(task_id, *, due=None, assigned="2027-07-20 09:00", state="actionable", holder="amina@x", protective=False, at_risk=False, subject="report", version=1, command="SignAcceptanceReport", **extra):
	return {"task_id": task_id, "case": "CM-1", "subject": subject, "version": version, "command": command, "holder": holder, "state": state,
		"due": datetime.fromisoformat(due) if due else None, "assigned_at": datetime.fromisoformat(assigned), "protective": protective, "at_risk": at_risk, **extra}


class TestIdentityAndDedup(IntegrationTestCase):
	def test_identity_is_command_subject_version_and_required_holder(self):
		self.assertEqual(tasks.identity(task("T1")), "CM-1|report|1|SignAcceptanceReport|amina@x")
		self.assertNotEqual(tasks.identity(task("T1")), tasks.identity(task("T1", version=2)))
		self.assertNotEqual(tasks.identity(task("T1")), tasks.identity(task("T1", holder="julia@x")))

	def test_a_retry_or_replay_never_creates_a_second_item_and_keeps_the_first_assignment(self):
		first, replay = task("T1", assigned="2027-07-20 09:00"), task("T9", assigned="2027-07-21 12:00")
		kept = tasks.dedupe([replay, first])
		self.assertEqual([t["task_id"] for t in kept], ["T1"])
		self.assertEqual(kept[0]["assigned_at"], datetime(2027, 7, 20, 9, 0))

	def test_the_same_subject_for_two_holders_is_two_independent_obligations(self):
		self.assertEqual(len(tasks.dedupe([task("T1"), task("T2", holder="julia@x")])), 2)

	def test_reassignment_keeps_the_previous_holder_and_time_and_the_old_identity_confers_no_authority(self):
		moved = tasks.reassign(task("T1"), "julia@x", at=datetime(2027, 7, 21, 8, 0))
		self.assertEqual((moved["holder"], moved["history"][0]["holder"], moved["history"][0]["until"]), ("julia@x", "amina@x", datetime(2027, 7, 21, 8, 0)))
		self.assertEqual(moved["assigned_at"], datetime(2027, 7, 21, 8, 0))
		self.assertFalse(tasks.may_act(moved, "amina@x"))
		self.assertTrue(tasks.may_act(moved, "julia@x"))


class TestOrdering(IntegrationTestCase):
	def order(self, *items):
		return [t["task_id"] for t in tasks.order(list(items), NOW)]

	def test_protective_at_risk_then_overdue_then_earliest_upcoming_then_undated(self):
	def test_work_that_blocks_the_contract_leads_the_standing_publication_duty_even_when_the_duty_is_older(self):
		"""The Project Owner, 16 October 2026 (FU-CM-133): "The one that blocks should lead"."""
		duty = task("publication", assigned="2027-07-01 09:00", command="RecordContractAwardPublication")
		resolve = task("resolve", assigned="2027-07-01 09:00", command="ResolvePublicationRequirement")
		restriction = task("restriction", assigned="2027-07-20 09:00", command="ReviewAwardRestriction")
		self.assertEqual(self.order(duty, resolve, restriction), ["restriction", "publication", "resolve"])
		self.assertEqual(self.order(restriction, duty), ["restriction", "publication"], "whatever order they arrive in")

	def test_with_nothing_else_to_do_the_publication_duty_leads_and_a_verified_urgent_duty_keeps_its_place(self):
		duty = task("publication", assigned="2027-07-01 09:00", command="RecordContractAwardPublication")
		self.assertEqual(self.order(duty), ["publication"])
		overdue = task("overdue-publication", due="2027-07-10 00:00", command="RecordContractAwardPublication")
		later = task("later", assigned="2027-07-05 09:00", command="ReviewAwardRestriction")
		self.assertEqual(self.order(later, overdue), ["overdue-publication", "later"], "a duty overdue by a verified date is protective work and is not demoted")

	def test_a_blocked_or_waiting_task_still_sits_below_an_actionable_duty(self):
		duty = task("publication", command="RecordContractAwardPublication")
		blocked = task("blocked", state="blocked", command="SignContractCertification")
		waiting = task("waiting", state="waiting", command="SignContractVersion")
		self.assertEqual(self.order(waiting, blocked, duty), ["publication", "blocked", "waiting"])

		got = self.order(
			task("undated-late", assigned="2027-07-21 09:00"),
			task("upcoming-far", due="2027-08-30 00:00"),
			task("overdue", due="2027-07-15 00:00"),
			task("upcoming-soon", due="2027-07-25 00:00"),
			task("at-risk", due="2027-09-01 00:00", protective=True, at_risk=True),
			task("undated-early", assigned="2027-07-19 09:00"),
		)
		self.assertEqual(got, ["at-risk", "overdue", "upcoming-soon", "upcoming-far", "undated-early", "undated-late"])

	def test_two_obligations_assigned_at_the_same_instant_are_led_by_the_one_recorded_first_not_by_their_names(self):
		first, second = task("zzz-first", assigned="2027-07-20 09:00"), task("aaa-second", assigned="2027-07-20 09:00")
		first["created"], second["created"] = datetime(2026, 10, 16, 1, 0, 0, 1), datetime(2026, 10, 16, 1, 0, 0, 2)
		self.assertEqual(self.order(second, first), ["zzz-first", "aaa-second"])
		self.assertEqual(self.order(first, second), ["zzz-first", "aaa-second"])

	def test_undated_work_with_the_same_assignment_instant_has_a_stable_order_by_id(self):
		self.assertEqual(self.order(task("B"), task("A")), ["A", "B"])

	def test_an_unverified_date_is_not_an_urgency(self):
		undated = task("claims-a-date", due="2027-07-01 00:00", due_verified=False)
		verified_later = task("verified", due="2027-08-01 00:00")
		self.assertEqual(self.order(undated, verified_later), ["verified", "claims-a-date"])
		self.assertEqual(tasks.due_display(undated, NOW), "Not established")
		self.assertEqual(tasks.due_display(verified_later, NOW), "2027-08-01 00:00")

	def test_a_blocked_duty_stays_visible_but_never_hides_actionable_work_and_waiting_sits_below(self):
		got = self.order(
			task("waiting", state="waiting", due="2027-07-10 00:00"),
			task("blocked-urgent", state="blocked", due="2027-07-01 00:00"),
			task("actionable-late", due="2027-09-01 00:00"),
			task("scheduled", state="scheduled", due="2027-07-23 00:00"),
		)
		self.assertEqual(got, ["actionable-late", "blocked-urgent", "waiting", "scheduled"])

	def test_the_leading_item_is_not_repeated_in_other_work(self):
		view = tasks.view([task("T1", due="2027-07-23 00:00"), task("T2", due="2027-07-30 00:00", subject="certificate"), task("T1-replay", due="2027-07-23 00:00", assigned="2027-07-21 00:00")], "amina@x", NOW)
		self.assertEqual(view["leading"]["task_id"], "T1")
		self.assertEqual([t["task_id"] for t in view["other"]], ["T2"])

	def test_with_no_work_of_the_actors_own_the_leading_item_names_the_next_holder_and_the_true_assignment_time(self):
		view = tasks.view([task("T1", holder="julia@x", state="waiting", assigned="2027-07-20 09:00")], "amina@x", NOW)
		self.assertEqual((view["leading"]["task_id"], view["leading"]["holder"], view["leading"]["assigned_at"]), ("T1", "julia@x", datetime(2027, 7, 20, 9, 0)))
		self.assertTrue(view["leading_is_waiting_on_someone_else"])

	def test_a_neutral_reader_has_no_personal_task_block(self):
		view = tasks.view([task("T1", holder="julia@x")], "auditor@x", NOW, neutral=True)
		self.assertEqual((view["leading"], view["other"]), (None, []))

	def test_a_task_of_another_holder_is_never_the_actors_leading_item_when_the_actor_has_work(self):
		view = tasks.view([task("theirs", holder="julia@x", due="2027-07-01 00:00"), task("mine", due="2027-09-01 00:00")], "amina@x", NOW)
		self.assertEqual(view["leading"]["task_id"], "mine")


class TestNextStepAnswer(IntegrationTestCase):
	def answer(self, items, actor="amina@x", **kw):
		return next_steps.answer(tasks.view(items, actor, NOW, **kw), headline_for=lambda t: f"Do {t['command']}")

	def test_actionable_work_is_your_turn(self):
		result = self.answer([task("T1", due="2027-07-23 00:00")])
		self.assertEqual((result["kind"], result["headline"], result["primary_action"]), ("your_turn", "Do SignAcceptanceReport", "SignAcceptanceReport"))

	def test_a_blocked_duty_names_its_fix_owner(self):
		result = self.answer([task("T1", state="blocked", blocker={"reason_code": "CM_APPOINTMENT", "message": "An inspector has not declared.", "responsibility": "Head of procurement function"})])
		self.assertEqual(result["kind"], "your_turn_blocked")
		self.assertEqual(result["blockers"][0]["reason_code"], "CM_APPOINTMENT")
		self.assertEqual(result["fixes"][0]["responsibility"], "Head of procurement function")

	def test_waiting_on_someone_names_the_holder_and_since_when(self):
		result = self.answer([task("T1", holder="julia@x", state="waiting", assigned="2027-07-20 09:00", holder_role="Head of procurement function")])
		self.assertEqual((result["kind"], result["holder"]["display"], result["since"]["at"]), ("waiting", "julia@x (Head of procurement function)", "2027-07-20 09:00:00"))

	def test_a_scheduled_event_is_not_a_person_to_wait_on(self):
		result = self.answer([task("T1", state="scheduled", holder="", due="2027-08-01 00:00")])
		self.assertEqual((result["kind"], result["holder"]), ("timed", None))

	def test_nothing_involving_the_actor_is_not_involved(self):
		self.assertEqual(self.answer([], neutral=True)["kind"], "not_involved")
		self.assertEqual(self.answer([])["kind"], "done")
