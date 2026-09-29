# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The dead-end gate (BOP-CHG-001 v0.10 BOP-A11, §15 state/actor matrix;
KT-STD-001 v1.10 §3B.7; plan BOP10-704).

Each world walks one path through the opening. At every state the
Accounting Officer, the chair and recorder, both members, the Auditor, an
administrator and an outsider read the opening through the API. Every reader
gets a sound next step (an enabled action, or a named holder and a reason);
a technical reader never gets a turn or a fix; an outsider gets Not found.
Paths: the ordinary nonempty opening to completion; an empty opening to
completion; an unreadable bid that support cannot fix; Not held; and a
cancellation after Start."""

from __future__ import annotations

import frappe

from kentender_core.services import next_step as ns
from kentender_procurement.bid_opening import api
from kentender_procurement.bid_opening.services import cancellation, finish, incidents, not_held, presence, record, simulation
from kentender_procurement.bid_opening.tests.support import AO, AUDITOR, CHAIR, INDEPENDENT, MEMBER, OUTSIDER, SUPPORT
from kentender_procurement.bid_opening.tests.test_bop_api import ApiCase
from kentender_procurement.bid_opening.tests.test_bop_record import RecordCase
from kentender_procurement.bid_submission.tests.support import key

READERS = (AO, CHAIR, MEMBER, INDEPENDENT, AUDITOR, "Administrator")


class DeadEndCase(RecordCase, ApiCase):
	def check(self, label: str, not_readers: tuple = ()) -> dict[str, dict]:
		"""`not_readers`: people with no reason to read the opening yet (before the
		appointment, the future independent member), who get Not found."""
		seen = {}
		for user in not_readers:
			with self.subTest(state=label, user=user), self.assertRaises(frappe.DoesNotExistError):
				self.as_user(user, api.get_opening, self.reference)
		for user in [u for u in READERS if u not in not_readers]:
			answer = self.as_user(user, api.get_opening, self.reference)["next_step"]
			seen[user] = answer
			with self.subTest(state=label, user=user):
				self.assertEqual(ns.problems(answer), [], f"{label} / {user}: {answer}")
				if user == "Administrator":
					self.assertNotIn(answer["kind"], ns.TURN_KINDS)
					self.assertEqual((answer["fixes"], answer["primary_action"]), ([], ""))
		with self.subTest(state=label, user=OUTSIDER), self.assertRaises(frappe.DoesNotExistError):
			self.as_user(OUTSIDER, api.get_opening, self.reference)
		self.matrix.append((label, {u: (a["kind"], a["headline"]) for u, a in seen.items()}))
		return seen

	def setUp(self):
		super().setUp()
		self.matrix = []


class TestOrdinaryPath(DeadEndCase):
	def test_every_state_of_a_nonempty_opening(self):
		self.assertTrue(self.submit(self.signed())["ok"])
		self.prepare_case()
		self.check("prepared, no committee", not_readers=(INDEPENDENT,))
		self.appoint()
		self.check("committee appointed")
		self.publish()
		self.check("attendance published")
		self.at(self.minutes_before(0.5))
		self.join(CHAIR)
		self.join(MEMBER)
		self.check("before close, one member missing")
		self.close_box()
		self.heartbeat_all((CHAIR, MEMBER))
		self.receive()
		self.check("closed, one member missing")
		self.join(INDEPENDENT)
		self.check("ready to start")
		self.at(self.minutes_after(0.2))
		self.begin()
		self.check("started")
		self.at(self.minutes_after(1))
		entry = self.open_next()["entry"]
		self.check("bid open, awaiting readout")
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		self.check("all read out")
		presence.leave_opening(tender=self.name, idempotency_key=key(), user=INDEPENDENT)
		self.check("paused, member left")
		self.join(INDEPENDENT)
		self.at(self.minutes_after(4))
		self.finish()
		self.check("readout complete")
		self.freeze()
		self.check("awaiting signatures")
		self.at(self.minutes_after(8))
		self.sign(MEMBER)
		self.check("one member signed")
		self.sign(INDEPENDENT)
		self.sign(CHAIR)
		seen = self.check("complete")
		self.assertEqual(seen[CHAIR]["kind"], ns.KIND_DONE)


class TestOtherPaths(DeadEndCase):
	def test_every_state_of_an_empty_opening(self):
		self.ready_to_open()
		self.check("empty, ready")
		self.at(self.minutes_after(0.2))
		self.begin()
		self.check("empty, started")
		self.at(self.minutes_after(1))
		finish.end_with_no_bids(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=CHAIR)
		self.check("empty, ended")
		self.freeze()
		self.check("empty, awaiting signatures")
		self.sign_all()
		self.check("empty, complete")

	def test_an_unreadable_bid_support_cannot_fix(self):
		self.started_with_one_bid()
		simulation.set_controls(render_outcome="Unreadable")
		self.at(self.minutes_after(1))
		self.open_next()
		self.check("paused, bid unreadable")
		[incident] = incidents.open_incidents(self.case_doc().name)
		incidents.record_unresolved(tender=self.name, incident=incident.incident_id, resolution_note="Cannot be rendered.", idempotency_key=key(), user=SUPPORT)
		self.check("paused, escalated to the Accounting Officer")

	def test_not_held_and_cancelled_after_start(self):
		self.prepared()
		self.at(self.minutes_after(10))
		not_held.record_opening_not_held(tender=self.name, reason="The public attendance service was unavailable; opening did not start",
			expected_version=self.case_version(), idempotency_key=key(), user=AO)
		self.check("not held")

	def test_cancelled_after_start(self):
		entry = self.opened()
		self.at(self.minutes_after(1.75))
		self.readout(entry)
		cancellation.close_cancelled_opening(tender=self.name, cancellation_reference="TEST-CANCEL-AFTER-START")
		self.check("cancelled after start")
