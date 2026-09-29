# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BOP-CHG-001 v0.10 plan Phase 4 (BOP10-401…409): the opening case, the
committee, how to attend, presence, the sealed close, custody participation,
the Start guard, incidents, Not held and a cancellation before Start, the
next step and My Work before Start. Fixtures BOP-N01, BOP-N02 (guard part),
BOP-N10, BOP-N14, BOP-N17; acceptance BOP-A01, A02 (pre-session), A11, A13,
A17, A18 (Not held)."""

from __future__ import annotations

import json

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening.services import (
	appointment, arrangements, guards, incidents, my_work_provider, next_steps, not_held, presence, reads, simulation,
)
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER, SUPPORT, OpeningCase
from kentender_procurement.bid_submission.tests.support import DAVID, key
from kentender_procurement.bid_submission.tests.test_submission import SubmissionCase
from kentender_procurement.tenders.services import opening_seam


def prc_events(tender: str, event_type: str | None = None) -> list[dict]:
	proceeding = frappe.db.get_value("Bid Opening Case", {"tender": tender}, "proceeding")
	filters = {"proceeding": proceeding}
	if event_type:
		filters["event_type"] = event_type
	return frappe.get_all("Proceeding Event", filters=filters, fields=["event_type", "actor", "pre_session", "note", "source"], order_by="sequence asc")


class TestCaseAndCommittee(OpeningCase):
	def test_bop_n14_the_case_is_prepared_once_and_content_free(self):
		first, again = self.prepare_case(), self.prepare_case()
		self.assertEqual(first, again)  # a replay returns the original result
		self.assertEqual(frappe.db.count("Bid Opening Case", {"tender": self.name}), 1)
		doc = frappe.get_doc("Bid Opening Case", first["opening"])
		self.assertEqual((doc.state, doc.manifest_digest, doc.started_at), ("Awaiting deadline", None, None))
		self.assertEqual(frappe.db.get_value("Proceeding", doc.proceeding, ["state", "actual_start"]), ("Pending", None))

	def test_bop_a02_the_committee_needs_three_members_and_an_independent_one(self):
		self.prepare_case()
		# Board a2: a chair and a member with no independent member are told what is missing.
		two = self.appoint(self.roster()[:2])
		self.assertEqual((two["ok"], two["code"]), (False, "BOP_INDEPENDENT_MEMBER_REQUIRED"))
		with_independent = self.appoint([self.roster()[0], self.roster()[2]])
		self.assertEqual((with_independent["ok"], with_independent["code"]), (False, "BOP_COMMITTEE_INCOMPLETE"))
		no_independent = self.appoint([*self.roster()[:2], {"user": INDEPENDENT, "committee_role": "Member"}])
		self.assertEqual(no_independent["code"], "BOP_INDEPENDENT_MEMBER_REQUIRED")
		self.assertEqual(no_independent["guard"]["headline"], "The opening committee needs an independent third member")
		self.assertEqual(no_independent["guard"]["fixes"][0]["label"], "Add an independent third member")
		processed = self.appoint([{"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": INDEPENDENT, "committee_role": "Member"},
			{"user": MEMBER, "committee_role": "Independent member"}])
		self.assertEqual(processed["code"], "BOP_INDEPENDENT_MEMBER_REQUIRED")  # the Procurement Officer prepared this Tender
		website_user = self.appoint([*self.roster()[:2], {"user": DAVID, "committee_role": "Independent member"}])
		self.assertEqual((website_user["code"], list(website_user["errors"])), ("BOP_COMMITTEE_INCOMPLETE", [DAVID]))
		self.assertEqual(frappe.db.count("Opening Committee Appointment", {"opening_case": frappe.db.get_value("Bid Opening Case", {"tender": self.name})}), 0)
		self.assertTrue(self.appoint()["ok"])
		case = frappe.db.get_value("Bid Opening Case", {"tender": self.name})
		rows = {m["member_user"]: (m["committee_role"], m["designation"], m["is_chair"], m["is_recorder"], m["is_independent"]) for m in appointment.roster(case)}
		self.assertEqual(rows[CHAIR][:1] + rows[CHAIR][2:], ("Chair and recorder", 1, 1, 0))
		self.assertEqual(rows[INDEPENDENT], ("Independent member", "Budget Approver", 0, 0, 1))
		self.assertTrue(self.appoint()["ok"])  # a second appointment supersedes the first with history
		self.assertEqual(frappe.get_all("Opening Committee Appointment", filters={"opening_case": case}, pluck="status", order_by="version_number asc"), ["Superseded", "Active"])

	def test_bop_a17_the_independent_member_is_excluded_from_evaluation(self):
		self.prepare_case()
		self.appoint()
		self.assertTrue(appointment.is_excluded_from_evaluation(self.name, INDEPENDENT))
		self.assertFalse(appointment.is_excluded_from_evaluation(self.name, MEMBER))

	def test_the_accounting_officer_sees_who_can_be_appointed(self):
		self.prepare_case()
		candidates = {c["user"]: c for c in reads.get_opening(tender=self.name, user=AO)["candidates"]}
		self.assertEqual((candidates[INDEPENDENT]["designation"], candidates[INDEPENDENT]["involved"]), ("Budget Approver", False))
		self.assertTrue(candidates[MEMBER]["involved"])  # prepared this Tender
		self.assertNotIn("Administrator", candidates)
		self.assertEqual(reads.get_opening(tender=self.name, user=CHAIR)["candidates"], [])

	def test_only_the_accounting_officer_appoints_or_publishes(self):
		self.prepare_case()
		for user in (MEMBER, CHAIR, "Administrator"):
			with self.subTest(user=user), self.assertRaises(frappe.DoesNotExistError):
				self.appoint(user=user)
		with self.assertRaises(frappe.DoesNotExistError):
			self.publish(user=CHAIR)

	def test_how_to_attend_is_published_with_its_times_and_no_bid_facts(self):
		self.prepare_case()
		case = frappe.db.get_value("Bid Opening Case", {"tender": self.name})
		self.assertEqual(arrangements.public_projection(case), {"published": False, "message": "Details on how to attend the opening are coming soon"})
		self.assertTrue(self.publish()["ok"])
		public = arrangements.public_projection(case)
		self.assertEqual((public["attendance_method"], public["scheduled_at"], public["join_opens_at"]), ("Attend the public bid opening online", str(self.deadline),
			self.minutes_before(5)))
		self.assertFalse({"bids", "bid_count", "envelopes", "tenderers"} & set(public))

	def test_the_tenders_seam_names_the_processing_people(self):
		from kentender_procurement.tenders.tests import fixtures as tender_fx

		self.assertLessEqual({tender_fx.OFFICER, tender_fx.HOPF, tender_fx.AO}, opening_seam.processing_actors(self.name))


class TestPresence(OpeningCase):
	def test_bop_n14_members_join_before_start_without_a_start(self):
		self.prepared()
		self.at(self.minutes_before(30))
		early = self.join(MEMBER)
		self.assertEqual((early["ok"], early["reason"]), (False, "join_not_open"))
		self.at(self.minutes_before(0.5))
		self.assertTrue(self.join(MEMBER)["joined"])
		self.assertFalse(self.join(MEMBER)["joined"])  # already present
		with self.assertRaises(frappe.DoesNotExistError):
			self.join(OUTSIDER)
		arrivals = prc_events(self.name, "AttendanceArrival")
		self.assertEqual([(e.actor, e.pre_session) for e in arrivals], [(MEMBER, 1)])
		self.assertEqual(frappe.db.get_value("Proceeding", frappe.db.get_value("Bid Opening Case", {"tender": self.name}, "proceeding"), ["state", "actual_start"]),
			("Pending", None))
		presence.leave_opening(tender=self.name, idempotency_key=key(), user=MEMBER)
		self.assertEqual([e.actor for e in prc_events(self.name, "AttendanceDeparture")], [MEMBER])

	def test_a_lapsed_heartbeat_is_recorded_as_a_departure_by_the_system(self):
		self.prepared()
		self.at(self.minutes_before(4))
		self.join(MEMBER)
		self.at(self.minutes_before(3))
		self.assertTrue(presence.heartbeat(tender=self.name, user=MEMBER)["present"])
		self.at(self.minutes_before(1))  # 120 s without a heartbeat; the simulation lapse is 60 s
		self.assertFalse(presence.heartbeat(tender=self.name, user=MEMBER)["present"])
		departure = prc_events(self.name, "AttendanceDeparture")
		self.assertEqual([(e.actor, e.source) for e in departure], [(None, "Recorder")])
		self.assertEqual(frappe.db.get_value("Opening Presence", {"member_user": MEMBER}, "state"), "Lapsed")


class TestNextStepsBeforeClose(OpeningCase):
	def answer(self, user):
		return reads.get_opening(tender=self.name, user=user)["next_step"]

	def test_the_accounting_officer_appoints_then_publishes_then_is_done(self):
		self.prepare_case()
		first = self.answer(AO)
		self.assertEqual((first["kind"], first["headline"], first["primary_action"]), (ns.KIND_YOUR_TURN, "Appoint opening committee", "appoint"))
		waiting = self.answer(CHAIR)
		self.assertEqual((waiting["kind"], waiting["holder"]["role"]), (ns.KIND_WAITING, "Accounting Officer"))
		self.assertTrue(waiting["headline"].startswith("Waiting for ") and waiting["headline"].endswith(" to appoint the opening committee"))
		self.appoint()
		second = self.answer(AO)
		self.assertEqual((second["headline"], second["primary_action"]), ("Publish how to attend", "publish"))
		self.assertTrue(second["sentence"].endswith("The opening cannot start until attendance details are published."))
		self.publish()
		done = self.answer(AO)
		self.assertEqual(done["kind"], ns.KIND_DONE)
		self.assertTrue(done["headline"].startswith("You published how to attend on "))
		for answer in (first, waiting, second, done):
			self.assertEqual(ns.problems(answer), [])

	def test_members_are_scheduled_or_asked_to_join(self):
		self.prepared()
		self.at(self.minutes_before(30))
		self.assertEqual(self.answer(MEMBER)["kind"], ns.KIND_SCHEDULED)
		self.assertTrue(self.answer(MEMBER)["headline"].startswith("You can join from "))
		self.at(self.minutes_before(0.5))
		join = self.answer(MEMBER)
		self.assertEqual((join["kind"], join["primary_action"]), (ns.KIND_YOUR_TURN, "join"))
		self.join(CHAIR)
		chair = self.answer(CHAIR)
		self.assertEqual((chair["kind"], chair["label"], chair["holder"]["role"]), (ns.KIND_SCHEDULED, "Scheduled", "System"))
		self.assertTrue(chair["headline"].startswith("Submissions close automatically at ") and chair["headline"].endswith("EAT."))
		self.assertEqual(ns.problems(chair), [])

	def test_my_work_items_follow_the_state(self):
		self.prepare_case()
		titles = lambda user, bucket="assigned": [r["title"] for r in my_work_provider.my_work_rows(user)[bucket] if r["reference"] == self.reference]  # noqa: E731
		self.assertEqual(titles(AO), [f"Appoint opening committee for {self.reference}"])
		self.assertTrue(titles(CHAIR, "waiting"))
		self.appoint()
		self.assertEqual(titles(AO), [f"Publish how to attend for {self.reference}"])
		self.assertEqual(titles(CHAIR, "waiting"), [])
		self.assertIn(f"Join opening for {self.reference}", titles(MEMBER))
		start = [r for r in my_work_provider.my_work_rows(CHAIR)["assigned"] if r["task_type"] == "bid_opening.start" and r["reference"] == self.reference]
		self.assertEqual(start[0]["status"], "Upcoming")
		self.publish()
		self.assertEqual(titles(AO), [])
		self.at(self.minutes_before(0.5))
		self.join(MEMBER)
		self.assertNotIn(f"Join opening for {self.reference}", titles(MEMBER))

	def test_readers_and_not_found(self):
		self.prepared()
		for user in (AUDITOR, "Administrator"):
			with self.subTest(user=user):
				self.assertEqual(reads.get_opening(tender=self.name, user=user)["next_step"]["kind"], ns.KIND_NOT_INVOLVED)
		self.assertEqual(reads.get_opening(tender=self.name, user="Administrator")["attendees"], [])
		for user in (OUTSIDER, DAVID):
			with self.subTest(user=user), self.assertRaises(frappe.DoesNotExistError):
				reads.get_opening(tender=self.name, user=user)


class TestNotHeld(OpeningCase):
	def test_bop_n17_not_held_is_terminal_and_gives_the_accounting_officer_a_decision(self):
		self.prepared()
		with self.assertRaises(Exception) as early:
			not_held.record_opening_not_held(tender=self.name, reason="x", expected_version=self.case_version(), idempotency_key=key(), user=AO)
		self.assertEqual(early.exception.code, "BOP_DEADLINE_NOT_REACHED")
		self.at(self.minutes_after(10))
		with self.assertRaises(frappe.DoesNotExistError):
			not_held.record_opening_not_held(tender=self.name, reason="x", expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		out = not_held.record_opening_not_held(tender=self.name, reason="The public attendance service was unavailable; opening did not start",
			expected_version=self.case_version(), idempotency_key=key(), user=AO)
		self.assertEqual(out["state"], "Not held")
		case = frappe.get_doc("Bid Opening Case", {"tender": self.name})
		self.assertEqual(frappe.db.get_value("Proceeding", case.proceeding, ["state", "actual_start"]), ("Not held", None))
		decide = reads.get_opening(tender=self.name, user=AO)
		self.assertEqual((decide["next_step"]["kind"], decide["next_step"]["headline"]), (ns.KIND_YOUR_TURN, "Decide what happens next"))
		self.assertEqual(decide["decision"]["unavailable_text"], "A Tender decision is needed. Cancellation after submissions close is not available in this version.")
		member = reads.get_opening(tender=self.name, user=MEMBER)["next_step"]
		self.assertEqual(member["kind"], ns.KIND_WAITING)
		self.assertTrue(member["headline"].startswith("The opening did not take place. Waiting for "))
		self.assertEqual([r["title"] for r in my_work_provider.my_work_rows(AO)["assigned"] if r["reference"] == self.reference], [f"Decide what happens next for {self.reference}"])
		with self.assertRaises(Exception) as again:
			not_held.record_opening_not_held(tender=self.name, reason="again", expected_version=self.case_version(), idempotency_key=key(), user=AO)
		self.assertEqual(again.exception.code, "BOP_VERSION_CONFLICT")
		with self.assertRaises(Exception) as late:
			self.join(MEMBER)
		self.assertEqual(late.exception.code, "BOP_VERSION_CONFLICT")

	def test_a_cancellation_before_start_closes_the_case_without_a_decision_item(self):
		from kentender_procurement.tenders.services import cancellation
		from kentender_procurement.tenders.tests import fixtures as tender_fx

		self.prepared()
		root = frappe.get_doc("Tender", self.name)
		cancellation.cancel_tender(tender=self.name, ground="INADEQUATE_BUDGET", reason="The confirmed budget available for this procurement is insufficient to proceed.",
			expected_record_version=root.record_version, idempotency_key=key(), user=tender_fx.AO)
		self.assertEqual(self.sweep()["not_held"], 1)
		case = frappe.get_doc("Bid Opening Case", {"tender": self.name})
		self.assertEqual(case.state, "Not held")
		self.assertTrue(frappe.db.get_value("Proceeding", case.proceeding, "cancellation_reference"))
		self.assertEqual(frappe.db.count("Opening Decision Item", {"opening_case": case.name}), 0)
		self.assertEqual(reads.get_opening(tender=self.name, user=CHAIR)["next_step"]["headline"], "The opening did not take place.")


class TestEmptyBox(OpeningCase):
	"""An empty closed box (no submission): the same steps as a nonempty one."""

	def ready(self):
		self.prepared()
		self.at(self.minutes_before(0.5))
		for user in (CHAIR, MEMBER, INDEPENDENT):
			self.join(user)
		self.close_box()
		self.heartbeat_all()
		return self.receive()

	def test_bop_n10_the_box_is_received_once_and_members_take_part_in_the_release(self):
		self.prepared()
		self.assertFalse(self.receive()["received"])  # before the deadline
		received = self.ready()
		self.assertTrue(received["received"])
		case = frappe.get_doc("Bid Opening Case", {"tender": self.name})
		self.assertEqual(case.state, "Ready to open")
		self.assertEqual(frappe.db.get_value("Bid Opening Handoff", case.manifest_handoff, "delivery_status"), "Delivered")
		reference = prc_events(self.name, "ClosedManifestReference")
		self.assertEqual(len(reference), 1)
		self.assertEqual(len(prc_events(self.name, "CustodyParticipation")), 3)
		from kentender_procurement.bid_opening.services import custody_participation

		self.assertTrue(custody_participation.valid(case))
		self.assertFalse(self.receive()["received"])
		ready = reads.get_opening(tender=self.name, user=CHAIR)["next_step"]
		self.assertEqual((ready["kind"], ready["headline"], ready["primary_action"]), (ns.KIND_YOUR_TURN, "Ready to start", "start"))
		self.assertTrue(ready["sentence"].startswith("All three members have joined and submissions closed at "))

	def test_bop_n02_an_absent_member_blocks_start_by_name(self):
		self.prepared()
		self.at(self.minutes_before(0.5))
		self.join(CHAIR)
		self.join(MEMBER)
		self.close_box()
		self.receive()
		answer = reads.get_opening(tender=self.name, user=CHAIR)["next_step"]
		self.assertEqual((answer["kind"], answer["headline"]), (ns.KIND_WAITING, "Opening cannot start because Test Independent Member has not joined."))
		self.assertTrue(answer["sentence"].endswith("You can start once every appointed member has joined."))
		fix = next(f for b in answer["blockers"] for f in b["fixes"] if f["fix_id"] == "notify_member")
		self.assertEqual(fix["label"], "Notify Test Independent Member")
		from kentender_procurement.bid_opening.services import reminders

		self.assertTrue(reminders.notify_member(tender=self.name, member=INDEPENDENT, idempotency_key=key(), user=CHAIR)["notified"])
		with self.assertRaises(frappe.DoesNotExistError):
			reminders.notify_member(tender=self.name, member=INDEPENDENT, idempotency_key=key(), user=MEMBER)

	def test_branch_6_an_unavailable_opening_service_is_one_incident_and_a_retried_notice(self):
		self.ready()
		simulation.set_controls(opening_profile_down=1, notify_outcome="Fail")
		self.at(self.minutes_after(5 / 60))
		self.heartbeat_all()
		self.assertEqual(self.sweep()["incidents"], 1)
		self.assertEqual(self.sweep()["incidents"], 0)  # the same problem never opens a second incident
		case = frappe.db.get_value("Bid Opening Case", {"tender": self.name})
		[incident] = incidents.open_incidents(case)
		self.assertEqual((incident.incident_type, incident.notification_state), ("Opening profile unavailable", "Failed"))
		blocked = reads.get_opening(tender=self.name, user=CHAIR)["next_step"]
		self.assertEqual((blocked["kind"], blocked["headline"]), (ns.KIND_BLOCKED, "Bid opening isn’t available yet."))
		self.assertEqual(blocked["blockers"][0]["message"], "Support could not be notified. Try again.")
		self.assertEqual([f["label"] for f in blocked["fixes"]], ["Notify support", "View problem details"])
		self.assertEqual(ns.problems(blocked), [])
		simulation.set_controls(notify_outcome="Deliver")
		self.assertTrue(incidents.notify_support(tender=self.name, incident=incident.incident_id, idempotency_key=key(), user=CHAIR)["delivered"])
		told = reads.get_opening(tender=self.name, user=CHAIR)["next_step"]
		self.assertEqual((told["kind"], told["headline"], told["sentence"]), (ns.KIND_WAITING, "Bid opening isn’t available yet.", "Opening access support has been told."))
		self.assertEqual(frappe.db.count("Opening Access Incident", {"opening_case": case}), 1)
		simulation.set_controls(opening_profile_down=0)
		self.assertNotEqual(reads.get_opening(tender=self.name, user=CHAIR)["next_step"]["headline"], "Ready to start")  # support has not recorded resolution
		incidents.record_resolution(tender=self.name, incident=incident.incident_id, resolution_note="Opening service restored.", idempotency_key=key(), user=SUPPORT)
		self.assertEqual(reads.get_opening(tender=self.name, user=CHAIR)["next_step"]["headline"], "Ready to start")


def pre_start_views(case: OpeningCase) -> dict:
	"""What the chair and a member read before and after the box closes, with
	the Tender's own reference and times normalised (BOP-N01, BOP-A13)."""
	from kentender_procurement.bid_opening.services import labels

	def view(user: str) -> dict:
		out = reads.get_opening(tender=case.name, user=user)
		keep = {"next_step": out["next_step"], "start_guard": out["start_guard"], "box_received": out["opening"]["box_received"], "state": out["opening"]["state"],
			"keys": sorted(out), "opening_keys": sorted(out["opening"]), "incidents": out["incidents"]}
		text = json.dumps(keep, default=str)
		for volatile in (case.reference, labels.when(case.deadline), labels.time(case.deadline)):
			text = text.replace(volatile, "X")
		return json.loads(text)

	case.prepared()
	case.at(case.minutes_before(0.5))
	for user in (CHAIR, MEMBER, INDEPENDENT):
		case.join(user)
	before = view(CHAIR)
	case.close_box()
	case.heartbeat_all()
	case.receive()
	return {"before": before, "chair": view(CHAIR), "member": view(MEMBER)}


def expected_views() -> dict:
	chair_name = frappe.db.get_value("User", CHAIR, "full_name")
	keys = ["arrangements", "attendees", "cancellation", "candidates", "ceremony", "committee", "decision", "incidents", "journey", "next_step", "opening", "record", "start_guard", "technical_status", "viewer"]
	opening_keys = ["box_received", "closed", "deadline", "deadline_label", "opening_id", "record_version", "state", "status", "tender", "tender_reference", "title"]
	answer = lambda kind, label, headline, sentence="", holder=None, action="": {"kind": kind, "label": label, "headline": headline, "sentence": sentence,  # noqa: E731
		"stage": "open", "holder": holder, "since": None, "blockers": [], "fixes": [], "primary_action": action}
	allowed = {"allowed": True, "reason_code": "", "message": "", "headline": "", "figures": {}, "fixes": [], "facts": []}
	return {
		"before": {"next_step": answer("timed", "Scheduled", "Submissions close automatically at X.", holder={"role": "System", "people": [], "display": "System"}),
			"start_guard": None, "box_received": False, "state": "Awaiting deadline", "keys": keys, "opening_keys": opening_keys, "incidents": []},
		"chair": {"next_step": answer("your_turn", "Your turn", "Ready to start", "All three members have joined and submissions closed at X EAT.", action="start"),
			"start_guard": allowed, "box_received": True, "state": "Ready to open", "keys": keys, "opening_keys": opening_keys, "incidents": []},
		"member": {"next_step": answer("waiting", "Waiting on someone", f"Waiting for {chair_name} to start the opening",
			holder={"role": "Chair", "people": [chair_name], "display": f"{chair_name} (Chair)"}),
			"start_guard": allowed, "box_received": True, "state": "Ready to open", "keys": keys, "opening_keys": opening_keys, "incidents": []},
	}


class TestCountNeutralEmpty(OpeningCase):
	def test_bop_n01_an_empty_box_reads_exactly_the_expected_count_neutral_view(self):
		self.assertEqual(pre_start_views(self), expected_views())


class TestCountNeutralNonEmpty(OpeningCase, SubmissionCase):
	def test_bop_n01_a_nonempty_box_reads_exactly_the_same_view_and_leaks_nothing(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.assertEqual(pre_start_views(self), expected_views())
		text = json.dumps([reads.get_opening(tender=self.name, user=u) for u in (CHAIR, MEMBER, AO, AUDITOR, "Administrator")], default=str)
		for leak in ("Afya", "46,400,000", "46400000", "RCPT-", "envelope", "bidder"):
			self.assertNotIn(leak, text)
