# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Opening test world (BOP-CHG-001 v0.10 plan D14): a published Tender
from the Bid Submission test world, its Accounting Officer, a committee (the
Head of Procurement Function as chair and recorder, the Procurement Officer,
and an independent member who did not process the Tender), and an Opening
access support holder. All clocks move together. Everything the world
writes is removed afterwards (the always-remove-test-data rule)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_opening.services import (
	appointment, arrangements, case, close_intake, presence, simulation, sweep,
)
from kentender_procurement.bid_submission.tests.support import BidCase, key
from kentender_procurement.tenders.tests import fixtures as tender_fx

NS = "BOP_TEST"
AO = tender_fx.AO
CHAIR = tender_fx.HOPF  # chair and recorder
MEMBER = tender_fx.OFFICER
INDEPENDENT = "bopt.independent@example.test"
SUPPORT = "bopt.support@example.test"
AUDITOR = tender_fx.AUDITOR
OUTSIDER = tender_fx.OUTSIDER
PEOPLE = {INDEPENDENT: ("Test Independent Member", "Budget Approver"), SUPPORT: ("Test Opening Support", "Technical Operator")}


def ensure_people() -> None:
	from kentender_core.services import responsibility_administration as administration

	for email, (name, role) in PEOPLE.items():
		if not frappe.db.exists("User", email):
			frappe.get_doc({"doctype": "User", "email": email, "first_name": name, "send_welcome_email": 0, "enabled": 1, "user_type": "System User"}).insert(ignore_permissions=True)
			frappe.get_doc("User", email).add_roles("Desk User")
		if not frappe.db.exists("User Responsibility Assignment", {"user": email, "business_role": role, "status": "Enabled"}):
			administration.grant(user=email, business_role=role, organisation_unit="", fixture_namespace=NS, actor="Administrator")
	frappe.db.commit()


def remove_people() -> None:
	for email in PEOPLE:
		frappe.db.delete("User Responsibility Assignment", {"user": email})
		frappe.db.delete("Notification Log", {"for_user": email})
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	frappe.db.commit()


def wipe_openings() -> None:
	from kentender_procurement.bid_opening.seeds import clear

	clear.wipe(tenders=set(tender_fx.test_tenders()), namespace=NS)
	frappe.db.delete("Audit Event", {"entity": "Bid Opening", "document_name": "TND-DOES-NOT-EXIST"})  # test_bop_api's guessed route
	frappe.db.delete("Notification Log", {"email_header": ("like", "bop-%"), "for_user": ("in", (INDEPENDENT, SUPPORT, CHAIR, MEMBER, AO))})
	frappe.db.commit()


class OpeningCase(BidCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_people()
		cls.addClassCleanup(remove_people)
		cls.addClassCleanup(wipe_openings)

	def setUp(self):
		wipe_openings()
		super().setUp()
		self._flag("kt_bop_fixture_namespace", NS)
		self._flag("kt_prc_fixture_namespace", NS)
		previous = frappe.conf.get("kt_bds_simulation_environment")
		frappe.conf["kt_bds_simulation_environment"] = 1
		self.addCleanup(frappe.conf.__setitem__, "kt_bds_simulation_environment", previous)
		simulation.reset_controls()
		self.addCleanup(simulation.reset_controls)
		self.addCleanup(wipe_openings)
		self.deadline = frappe.db.get_value("Tender", self.name, "submission_deadline")

	def at(self, instant) -> None:
		super().at(str(instant))
		frappe.flags.kt_bop_clock = str(instant)
		frappe.flags.kt_prc_clock = str(instant)
		self.addCleanup(setattr, frappe.flags, "kt_bop_clock", None)
		self.addCleanup(setattr, frappe.flags, "kt_prc_clock", None)

	def minutes_before(self, minutes: int) -> str:
		from datetime import timedelta

		from frappe.utils import get_datetime

		return str(get_datetime(self.deadline) - timedelta(minutes=minutes))

	def minutes_after(self, minutes: float) -> str:
		from datetime import timedelta

		from frappe.utils import get_datetime

		return str(get_datetime(self.deadline) + timedelta(seconds=int(minutes * 60)))

	# -- the ordinary path -----------------------------------------------------
	def case_version(self) -> int:
		return int(frappe.db.get_value("Bid Opening Case", {"tender": self.name}, "record_version"))

	def prepare_case(self) -> dict[str, Any]:
		return case.prepare_opening_case(tender=self.name)

	def roster(self, independent: str = INDEPENDENT) -> list[dict[str, str]]:
		return [{"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": MEMBER, "committee_role": "Member"},
			{"user": independent, "committee_role": "Independent member"}]

	def appoint(self, members: list[dict[str, str]] | None = None, user: str = AO) -> dict[str, Any]:
		return appointment.appoint_opening_committee(tender=self.name, members=members or self.roster(), expected_version=self.case_version(), idempotency_key=key(), user=user)

	def publish(self, user: str = AO) -> dict[str, Any]:
		return arrangements.publish_opening_arrangements(tender=self.name, attendance_method="Attend the public bid opening online",
			access_instructions="Select Join public opening on this Tender’s page.", expected_version=self.case_version(), idempotency_key=key(), user=user)

	def join(self, user: str) -> dict[str, Any]:
		return presence.join_opening(tender=self.name, idempotency_key=key(), user=user)

	def prepared(self) -> None:
		self.prepare_case()
		self.assertTrue(self.appoint()["ok"])
		self.assertTrue(self.publish()["ok"])

	def close_box(self) -> None:
		from kentender_procurement.bid_submission.services import close
		from kentender_procurement.tenders.services import submission_close

		self.at(self.deadline)
		submission_close.close_tender_submission_period(tender=self.name, idempotency_key=key(), user="Administrator")
		close.consume_tender_events(tender=self.name)

	def heartbeat_all(self, users=None) -> None:
		for user in users or (CHAIR, MEMBER, INDEPENDENT):
			presence.heartbeat(tender=self.name, user=user)

	def receive(self) -> dict[str, Any]:
		return close_intake.receive_closed_box(tender=self.name)

	def sweep(self) -> dict[str, int]:
		return sweep.sweep_tender(self.name)

	# -- the ceremony ------------------------------------------------------------
	def ready_to_open(self) -> None:
		self.prepared()
		self.at(self.minutes_before(0.5))
		for user in (CHAIR, MEMBER, INDEPENDENT):
			self.join(user)
		self.close_box()
		self.heartbeat_all()
		self.assertTrue(self.receive()["received"])

	def begin(self, user: str = CHAIR) -> dict[str, Any]:
		from kentender_procurement.bid_opening.services import ceremony

		return ceremony.begin_opening(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=user)

	def open_next(self, user: str = CHAIR) -> dict[str, Any]:
		from kentender_procurement.bid_opening.services import ceremony

		return ceremony.open_next_tender(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=user)

	def readout(self, entry: str, *, speaker: str = MEMBER, pages=(1,), reported=None, user: str = CHAIR) -> dict[str, Any]:
		from kentender_procurement.bid_opening.services import readout

		return readout.record_readout(tender=self.name, entry=entry, speaker=speaker, designated_pages=list(pages), expected_version=self.case_version(),
			idempotency_key=key(), user=user, reported_speech_at=reported)

	def finish(self, user: str = CHAIR) -> dict[str, Any]:
		from kentender_procurement.bid_opening.services import finish

		return finish.finish_ceremony(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=user)

	def case_doc(self):
		return frappe.get_doc("Bid Opening Case", {"tender": self.name})

	def next_step(self, user: str) -> dict[str, Any]:
		from kentender_procurement.bid_opening.services import reads

		return reads.get_opening(tender=self.name, user=user)["next_step"]
