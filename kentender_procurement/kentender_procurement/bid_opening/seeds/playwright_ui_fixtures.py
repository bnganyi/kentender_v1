# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Browser-test worlds for Bid Opening (BOP-CHG-001 v0.10 plan Phase 8).

Built on the Bid Submission Playwright world (`bid_submission.seeds.
playwright_ui_fixtures`, on the Tenders test Tender, FY 2099-2100): Afya
(Test)'s bid submitted before the 12 Jun 2027 11:00 deadline. The opening
committee is the Tenders world's Head of Procurement Function (chair and
recorder) and Procurement Officer, with this world's own independent member;
the Accounting Officer is the Tenders world's. Every step runs the real
Bid Opening command as its actor at the board's instant, and the live pages
read the same instant through the shared test clock. `restore_site()`
removes this world's rows, its people and the journal entries the browser
pass left, then puts the Bid Submission world back.

Called by the Playwright specs through `bench execute`; never by a user."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import frappe

from kentender_procurement.bid_opening.seeds import clear
from kentender_procurement.bid_submission.seeds import playwright_ui_fixtures as bds_pw
from kentender_procurement.tenders.seeds import playwright_ui_fixtures as tender_pw

NAMESPACE = "PW_BID_OPENING"
PASSWORD = bds_pw.PASSWORD
AO = tender_pw.AO
CHAIR = tender_pw.HOPF  # chair and recorder
MEMBER = tender_pw.OFFICER
INDEPENDENT = "pw.bop.independent@example.test"
SUPPORT = "pw.bop.support@example.test"
AUDITOR = tender_pw.AUDITOR
OUTSIDER = tender_pw.OUTSIDER
PEOPLE = {INDEPENDENT: ("Playwright Independent", "Budget Approver"), SUPPORT: ("Playwright Opening Support", "Technical Operator")}
OBSERVER = "pw.bop.observer@example.test"  # a signed-in member of the public (boards p1, p2, p6)
OBSERVER_NAME = "Playwright Observer"
BROWSER_ACTORS = (AO, CHAIR, MEMBER, INDEPENDENT, SUPPORT, AUDITOR, "Administrator", "pw.bop.observer@example.test", bds_pw.SUPPLIERS["afya"]["representative"],
	bds_pw.SUPPLIERS["kisiwa"]["representative"])

# The boards' instants (BOP-CHG-001 v0.10 §10), in seconds from this world's
# deadline (the boards draw 12 Jun 2027, 11:00; appointment two days before).
DAY = 86400
AT = {"prepare": -(2 * DAY + 3000), "appoint": -(2 * DAY + 2700), "publish": -(2 * DAY + 2400)}

# Each stage is the stage it grows from and the boards it pictures. The
# `empty` family has no submitted bid; the `not-held` family never starts.
STAGES = {
	"prepared": (None, "a1 a2"),
	"appointed": ("prepared", "a3 a4"),
	"published": ("appointed", "a5"),
	"joined": ("published", "c1: all three joined before the deadline"),
	"missing": ("published", "c2: the independent member has not joined; the box is received"),
	"ready": ("published", "c3"),
	"access": ("ready", "c2b: the custody service is down"),
	"notify-failed": ("ready", "c2d: the opening service is down and support could not be told"),
	"not-available": ("notify-failed", "c2c: support has been told"),
	"started": ("ready", "c4"),
	"opened": ("started", "c5 (member), c6 (recorder)"),
	"read-out": ("opened", "c7 (the request form)"),
	"answered": ("read-out", "c8, c9, c13"),
	"account": ("answered", "c8b"),
	"commented": ("answered", "c13b"),
	"member-left": ("read-out", "c10"),
	"rejoined": ("member-left", "c10b"),
	"unreadable": ("started", "c11"),
	"resolved": ("unreadable", "c11b"),
	"unresolved": ("unreadable", "c11c (chair), c11e (Accounting Officer)"),
	"mismatch": ("started", "c11d"),
	"cancelled": ("answered", "c12"),
	"ended": ("answered", "r1 r2"),
	"frozen": ("ended", "r3"),
	"member-signed": ("frozen", "r4 (member), r3 (independent)"),
	"changed": ("member-signed", "r5"),
	"complete": ("member-signed", "r6 h1 h3 h4"),
	"corrected": ("complete", "h5"),
	"empty-started": ("ready", "z1 (no submitted bid)"),
	"empty-complete": ("empty-started", "h2"),
	"not-held-due": ("published", "n1: the attendance service was down; the opening never started"),
	"not-held": ("not-held-due", "n2"),
}
ROSTER = ({"user": CHAIR, "committee_role": "Chair and recorder"}, {"user": MEMBER, "committee_role": "Member"},
	{"user": INDEPENDENT, "committee_role": "Independent member"})
ARRANGEMENTS = {"attendance_method": "Attend the public bid opening online",
	"access_instructions": "Select Join public opening on this Tender’s page from 10:55 EAT on 12 Jun 2027. You can listen, ask for a figure to be repeated, or make a procedural comment."}
REQUEST = {"exception_class": "Repeat request", "speaker_name": "David Ouma", "what": "Asked for the submitted total to be repeated",
	"response": "Charles Mutiso asked the member to repeat it. The total was repeated."}
ACCOUNT = "I heard the total repeated after the attendee’s request, but I could not hear the security reference clearly."
COMMENT = {"comment": "The security reference shown on the price page differs from the reference read aloud.",
	"response": "The observation is recorded for the Evaluation Committee to check. No decision is made at opening."}
NOT_HELD_REASON = "The public attendance service was unavailable; opening did not start"


def _key() -> str:
	return f"bop-pw-{uuid4().hex}"


def _ensure_people() -> None:
	from frappe.utils.password import update_password

	from kentender_core.services import responsibility_administration as administration

	for email, (name, role) in PEOPLE.items():
		tender_pw._user(email, name)
		if not frappe.db.exists("User Responsibility Assignment", {"user": email, "business_role": role, "status": "Enabled"}):
			administration.grant(user=email, business_role=role, organisation_unit="", fixture_namespace=NAMESPACE, actor="Administrator")
		update_password(email, PASSWORD)


def _ensure_observer() -> None:
	"""A Website User with no supplier account and no responsibility."""
	from frappe.utils.password import update_password

	if not frappe.db.exists("User", OBSERVER):
		frappe.get_doc({"doctype": "User", "email": OBSERVER, "first_name": "Playwright", "last_name": "Observer", "send_welcome_email": 0, "enabled": 1,
			"user_type": "Website User"}).insert(ignore_permissions=True)
	update_password(OBSERVER, PASSWORD)


def _remove_people() -> None:
	frappe.db.delete("Notification Log", {"for_user": OBSERVER})
	if frappe.db.exists("User", OBSERVER):
		frappe.delete_doc("User", OBSERVER, force=True, ignore_permissions=True)
	for email in PEOPLE:
		frappe.db.delete("User Responsibility Assignment", {"user": email})
		frappe.db.delete("Notification Log", {"for_user": email})
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)


def _wipe() -> None:
	"""This world's openings, and the journal rows the browser pass wrote as
	the fixture actors (a browser command carries no fixture namespace)."""
	clear.wipe(tenders=tender_pw_tenders(), namespace=NAMESPACE)
	frappe.db.delete("Opening Command Journal", {"actor": ("in", BROWSER_ACTORS)})
	frappe.db.delete("Proceeding Command Journal", {"actor": ("in", BROWSER_ACTORS)})
	frappe.db.delete("Notification Log", {"email_header": ("like", "bop-%"), "for_user": ("in", BROWSER_ACTORS)})


def tender_pw_tenders() -> list[str]:
	"""The Tenders world's Tenders: those its actors created."""
	return frappe.get_all("Tender", filters={"owner": ("in", tender_pw.ALL_ACTORS)}, pluck="name")


class _World:
	"""Runs one stage's steps as their actors on the fixture clock."""

	def __init__(self, tender: str, reference: str):
		self.tender, self.reference = tender, reference
		self.deadline = frappe.db.get_value("Tender", tender, "submission_deadline")
		self.present: set[str] = set()
		self.instant = ""
		self.seconds: int | None = None

	def at(self, seconds: int) -> None:
		"""Move the clock and keep every present member's page alive (plan D7)."""
		from kentender_procurement.bid_opening.services import presence

		# The members' open pages beat every 30 s on the way (the lapse is 60 s).
		ticks = list(range(self.seconds + 30, seconds, 30)) if self.present and self.seconds is not None else []
		for tick in [*ticks, seconds]:
			self.instant = self._clock(tick)
			frappe.flags.kt_bop_clock = frappe.flags.kt_prc_clock = self.instant
			frappe.flags.kt_bds_clock = frappe.flags.kt_tenders_clock = self.instant
			for user in self.present:
				presence.heartbeat(tender=self.tender, user=user)
		self.seconds = seconds

	def version(self) -> int:
		return int(frappe.db.get_value("Bid Opening Case", {"tender": self.tender}, "record_version"))

	def case(self):
		return frappe.get_doc("Bid Opening Case", {"tender": self.tender})

	def join(self, user: str, seconds: int) -> None:
		from kentender_procurement.bid_opening.services import presence

		self.at(seconds)
		_ok(presence.join_opening(tender=self.tender, idempotency_key=_key(), user=user), f"join as {user}")
		self.present.add(user)

	def close(self) -> None:
		from kentender_procurement.bid_opening.services import close_intake

		bds_pw.close_world(tender_reference=self.reference, at=str(self.deadline))
		self.at(1)
		close_intake.receive_closed_box(tender=self.tender)

	def run(self, stage: str) -> None:
		parent = STAGES[stage][0]
		if parent:
			self.run(parent)
		getattr(self, "stage_" + stage.replace("-", "_"))()

	# -- preparation --------------------------------------------------------
	def stage_prepared(self) -> None:
		from kentender_procurement.bid_opening.services import case

		self.at(AT["prepare"])
		case.prepare_opening_case(tender=self.tender)

	def stage_appointed(self) -> None:
		from kentender_procurement.bid_opening.services import appointment

		self.at(AT["appoint"])
		_ok(appointment.appoint_opening_committee(tender=self.tender, members=[dict(r) for r in ROSTER], expected_version=self.version(), idempotency_key=_key(), user=AO), "appoint")

	def stage_published(self) -> None:
		from kentender_procurement.bid_opening.services import arrangements

		self.at(AT["publish"])
		_ok(arrangements.publish_opening_arrangements(tender=self.tender, expected_version=self.version(), idempotency_key=_key(), user=AO, **ARRANGEMENTS), "publish")

	# -- before Start ---------------------------------------------------------
	def stage_joined(self) -> None:
		for i, user in enumerate((CHAIR, MEMBER, INDEPENDENT)):
			self.join(user, -290 + 60 * i)
		self.at(-90)

	def stage_missing(self) -> None:
		self.join(CHAIR, -290)
		self.join(MEMBER, -230)
		self.close()
		self.at(5)

	def stage_ready(self) -> None:
		self.stage_joined()
		self.close()
		self.at(5)

	def stage_access(self) -> None:
		from kentender_procurement.bid_submission.services import simulation as bds_simulation

		bds_simulation.set_controls(custody_service_down=1)

	def stage_notify_failed(self) -> None:
		from kentender_procurement.bid_opening.services import simulation, sweep

		simulation.set_controls(opening_profile_down=1, notify_outcome="Fail")
		self.at(5)
		sweep.sweep_tender(self.tender)

	def stage_not_available(self) -> None:
		from kentender_procurement.bid_opening.services import incidents, simulation

		simulation.set_controls(notify_outcome="Deliver")
		self.at(41)
		[incident] = incidents.open_incidents(self.case().name)
		_ok(incidents.notify_support(tender=self.tender, incident=incident.incident_id, idempotency_key=_key(), user=CHAIR), "notify support")

	# -- the ceremony ---------------------------------------------------------
	def stage_started(self) -> None:
		from kentender_procurement.bid_opening.services import ceremony

		self.at(12)
		_ok(ceremony.begin_opening(tender=self.tender, expected_version=self.version(), idempotency_key=_key(), user=CHAIR), "begin")
		self.at(30)

	def _open_next(self) -> dict[str, Any]:
		from kentender_procurement.bid_opening.services import ceremony

		self.at(60)
		return ceremony.open_next_tender(tender=self.tender, expected_version=self.version(), idempotency_key=_key(), user=CHAIR)

	def stage_opened(self) -> None:
		self.entry = _ok(self._open_next(), "open the bid")["entry"]
		self.at(80)

	def stage_read_out(self) -> None:
		from kentender_procurement.bid_opening.services import readout

		self.at(105)
		_ok(readout.record_readout(tender=self.tender, entry=self.entry, speaker=MEMBER, designated_pages=[1], expected_version=self.version(),
			idempotency_key=_key(), user=CHAIR, reported_speech_at=self._clock(90)), "record the readout")
		self.at(120)

	def _clock(self, seconds: int) -> str:
		from datetime import timedelta

		from frappe.utils import get_datetime

		return str(get_datetime(self.deadline) + timedelta(seconds=seconds))

	def stage_answered(self) -> None:
		from kentender_procurement.bid_opening.services import interventions

		self.at(140)
		_ok(interventions.record_intervention(tender=self.tender, idempotency_key=_key(), user=CHAIR, entry=self.entry, reported_at=self._clock(120), **REQUEST),
			"record the request")
		self.at(142)

	def stage_account(self) -> None:
		from kentender_procurement.bid_opening.services import interventions

		self.at(145)
		_ok(interventions.record_member_account(tender=self.tender, account=ACCOUNT, idempotency_key=_key(), user=INDEPENDENT, entry=self.entry), "record the account")
		self.at(150)

	def stage_commented(self) -> None:
		from kentender_procurement.bid_opening.services import interventions

		self.at(160)
		_ok(interventions.record_comment_for_evaluation(tender=self.tender, entry=self.entry, made_by=INDEPENDENT, idempotency_key=_key(), user=CHAIR,
			reported_at=self._clock(145), **COMMENT), "record the comment")
		self.at(165)

	def stage_member_left(self) -> None:
		from kentender_procurement.bid_opening.services import presence

		self.at(130)
		_ok(presence.leave_opening(tender=self.tender, idempotency_key=_key(), user=INDEPENDENT), "leave")
		self.present.discard(INDEPENDENT)
		self.at(135)

	def stage_rejoined(self) -> None:
		self.join(INDEPENDENT, 300)
		self.at(310)

	def stage_unreadable(self) -> None:
		from kentender_procurement.bid_opening.services import simulation

		simulation.set_controls(render_outcome="Unreadable")
		self._open_next()
		self.at(70)

	def _incident(self) -> str:
		from kentender_procurement.bid_opening.services import incidents

		return incidents.open_incidents(self.case().name)[0].incident_id

	def stage_resolved(self) -> None:
		from kentender_procurement.bid_opening.services import incidents, simulation

		simulation.set_controls(render_outcome="Render")
		self.at(300)
		_ok(incidents.record_resolution(tender=self.tender, incident=self._incident(), resolution_note="Renderer restored.", idempotency_key=_key(), user=SUPPORT),
			"resolve")
		self.at(305)

	def stage_unresolved(self) -> None:
		from kentender_procurement.bid_opening.services import incidents

		self.at(300)
		_ok(incidents.record_unresolved(tender=self.tender, incident=self._incident(), resolution_note="The package cannot be rendered.", idempotency_key=_key(),
			user=SUPPORT), "record not resolved")
		self.at(310)

	def stage_mismatch(self) -> None:
		from kentender_procurement.bid_submission.services import simulation as bds_simulation

		bds_simulation.set_controls(reveal_outcome="Mismatch")
		self._open_next()
		self.at(61)

	def stage_cancelled(self) -> None:
		from kentender_procurement.bid_opening.services import cancellation

		self.at(180)
		cancellation.close_cancelled_opening(tender=self.tender, cancellation_reference="TND-PW-CANCEL-AFTER-START")
		self.at(190)

	# -- the record -------------------------------------------------------------
	def stage_ended(self) -> None:
		from kentender_procurement.bid_opening.services import finish

		self.at(240)
		_ok(finish.finish_ceremony(tender=self.tender, expected_version=self.version(), idempotency_key=_key(), user=CHAIR), "end")
		self.at(270)

	def stage_frozen(self) -> None:
		from kentender_procurement.bid_opening.services import record

		self.at(420)
		_ok(record.freeze_opening_minutes(tender=self.tender, expected_version=self.version(), idempotency_key=_key(), user=CHAIR), "finish the record")
		self.at(450)

	def sign(self, user: str, seconds: int) -> None:
		from kentender_procurement.bid_opening.services import signing

		self.at(seconds)
		version, mine = signing.my_targets(self.case(), user)
		_ok(signing.sign_opening_record(tender=self.tender, minutes_version=version, targets=[{"target_id": t["target_id"], "target_digest": t["target_digest"]}
			for t in mine], idempotency_key=_key(), user=user), f"sign as {user}")

	def stage_member_signed(self) -> None:
		self.sign(MEMBER, 480)
		self.at(510)

	def stage_changed(self) -> None:
		from kentender_procurement.bid_opening.services import record

		self.at(525)
		_ok(record.supersede_opening_minutes(tender=self.tender, reason="Add the attendee’s repeat request and the chair’s response",
			correction_note="The attendee’s repeat request and the chair’s response.", expected_version=self.version(), idempotency_key=_key(), user=CHAIR), "change the record")
		self.at(530)

	def stage_complete(self) -> None:
		self.sign(INDEPENDENT, 540)
		self.sign(CHAIR, 600)
		self.at(660)

	def stage_corrected(self) -> None:
		from kentender_procurement.bid_opening.services import correction

		self.at(900)
		_ok(correction.correct_opening_record(tender=self.tender, kind="Attendance note", correct_information="Jane Wanjiku left at 11:03 EAT",
			reason="Add the departure noted during the opening", expected_version=self.version(), idempotency_key=_key(), user=CHAIR), "correct")
		self.at(910)

	# -- no bids, and not held ----------------------------------------------------
	def stage_empty_started(self) -> None:
		self.stage_started()

	def stage_empty_complete(self) -> None:
		from kentender_procurement.bid_opening.services import finish

		self.at(60)
		_ok(finish.end_with_no_bids(tender=self.tender, expected_version=self.version(), idempotency_key=_key(), user=CHAIR), "end with no bids")
		self.stage_frozen()
		self.sign(MEMBER, 480)
		self.stage_complete()

	def stage_not_held_due(self) -> None:
		from kentender_procurement.bid_opening.services import simulation, sweep

		simulation.set_controls(attendance_service_down=1)
		self.at(-300)
		sweep.sweep_tender(self.tender)
		self.at(600)

	def stage_not_held(self) -> None:
		from kentender_procurement.bid_opening.services import not_held

		_ok(not_held.record_opening_not_held(tender=self.tender, reason=NOT_HELD_REASON, expected_version=self.version(), idempotency_key=_key(), user=AO),
			"record not held")
		self.at(610)


def _ok(result: dict[str, Any], step: str) -> dict[str, Any]:
	if not result or result.get("ok") is False:
		frappe.throw(f"The Bid Opening world could not {step}: {result}")
	return result


def reset_opening_fixture(*, stage: str = "prepared", commit: bool = True) -> dict[str, Any]:
	"""A Bid Opening world at `stage` (see STAGES for the boards each pictures).
	The live pages then read the stage's own instant. An `empty-*` stage has no
	submitted bid, so the closed box is empty."""
	from kentender_procurement.bid_opening.services import simulation
	from kentender_procurement.bid_submission.services import simulation as bds_simulation

	if stage not in STAGES:
		raise ValueError(f"unknown Bid Opening world {stage!r}; one of {tuple(STAGES)}")
	world = bds_pw.reset_my_bids_fixture(state="ready" if stage.startswith("empty") else "submitted", commit=False)
	_wipe()
	_ensure_people()
	_ensure_observer()
	simulation.reset_controls()
	frappe.db.set_single_value("Bid Opening Settings", "register_self_service", None)
	bds_simulation.set_controls(custody_service_down=0, reveal_outcome="Deliver")
	tender = frappe.db.get_value("Tender", {"tender_reference": world["tender_reference"]}, "name")
	saved = {k: frappe.flags.get(k) for k in ("kt_bop_fixture_namespace", "kt_prc_fixture_namespace", "kt_bds_fixture_namespace", "kt_bop_clock", "kt_prc_clock",
		"kt_bds_clock", "kt_tenders_clock")}
	frappe.flags.kt_bop_fixture_namespace = frappe.flags.kt_prc_fixture_namespace = NAMESPACE
	frappe.flags.kt_bds_fixture_namespace = bds_pw.NAMESPACE
	walker = _World(tender, world["tender_reference"])
	try:
		walker.run(stage)
	finally:
		for k, v in saved.items():
			frappe.flags[k] = v
	bds_pw.set_instant(walker.instant)
	bds_simulation.set_controls(reveal_outcome="Deliver")
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()
	return {"stage": stage, "tender": tender, "tender_reference": world["tender_reference"], "password": PASSWORD, "instant": walker.instant,
		"independent": INDEPENDENT, "independent_name": PEOPLE[INDEPENDENT][0], "observer": OBSERVER, "supplier": bds_pw.SUPPLIERS["afya"]["representative"],
		"other_supplier": bds_pw.SUPPLIERS["kisiwa"]["representative"]}


def set_controls(**values) -> dict[str, Any]:
	"""A browser spec switches this world's test controls (a service coming
	back, a notice getting through) between two steps."""
	from kentender_procurement.bid_opening.services import simulation

	out = simulation.set_controls(**values)
	frappe.db.commit()
	return {k: out.get(k) for k in values}


def set_register_self_service(*, on: bool) -> dict[str, Any]:
	"""Board p4: with self-service off, the Accounting Officer provides each copy."""
	frappe.db.set_single_value("Bid Opening Settings", "register_self_service", 1 if on else 0)
	frappe.db.commit()
	return {"register_self_service": on}


def request_register(*, user: str) -> dict[str, Any]:
	"""The submitting supplier asks for the register (as the portal button does)."""
	from kentender_procurement.bid_opening.services import register_copy

	tender = frappe.db.get_value("Bid Opening Case", {"fixture_namespace": NAMESPACE}, "tender")
	frappe.set_user(user)
	try:
		out = register_copy.request_opening_register(tender=tender, idempotency_key=_key(), user=user)
	finally:
		frappe.set_user("Administrator")
	frappe.db.commit()
	return out


def capture_public(*, users: list[str] | None = None) -> dict[str, Any]:
	"""What each visitor's public opening page reads in the current world."""
	from kentender_procurement.bid_opening.services import public

	reference = frappe.db.get_value("Bid Opening Case", {"fixture_namespace": NAMESPACE}, "tender_reference")
	out = {}
	for user in users or ("Guest", OBSERVER, bds_pw.SUPPLIERS["afya"]["representative"]):
		out[user] = public.get_public_opening(tender_reference=reference, user=user)
	return frappe.parse_json(frappe.as_json(out))


def capture(*, users: list[str] | None = None) -> dict[str, Any]:
	"""What each reader's GetOpening returns in the current world: the
	component fixtures are these answers, never hand-written ones."""
	from kentender_procurement.bid_opening.services import reads

	tender = frappe.db.get_value("Bid Opening Case", {"fixture_namespace": NAMESPACE}, "tender")
	out = {}
	for user in users or (AO, CHAIR, MEMBER, INDEPENDENT, AUDITOR, "Administrator"):
		try:
			out[user] = reads.get_opening(tender=tender, user=user)
		except frappe.DoesNotExistError:
			out[user] = None
	return frappe.parse_json(frappe.as_json(out))


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import simulation

	frappe.set_user("Administrator")
	_wipe()
	simulation.reset_controls()
	_remove_people()
	out = bds_pw.restore_site(commit=False)
	if commit:
		frappe.db.commit()
	return {**out, "bid_opening_wiped": True}
