# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Browser-test worlds for Bid Evaluation (EVL-CHG-001 v0.4 plan Phase 11).

Built on the Bid Opening Playwright world (`bid_opening.seeds.
playwright_ui_fixtures`, on the Tenders test Tender): Afya (Test)'s bid,
answered from the Tender's own published requirements (the evaluation
answers of `test_services.bid_answers`, at KES 160,000.00 a unit), opened
and completed with every member's proof. The evaluation committee is this
world's own three people; the secretary is the Tenders world's Procurement
Officer; the Accounting Officer, Head of Procurement and auditor are the
Tenders world's. Every step runs the real Evaluation command as its actor at
the boards' instant (EVL-CHG-001 v0.4 §11.1), and the live pages read the
same instant through the shared test clock. `restore_site()` removes this
world's rows, its people and what the browser pass wrote, then puts the
Bid Opening world back.

Called by the Playwright specs through `bench execute`; never by a user."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import frappe

from kentender_procurement.bid_evaluation.seeds import clear
from kentender_procurement.bid_opening.seeds import playwright_ui_fixtures as bop_pw
from kentender_procurement.bid_submission.seeds import playwright_ui_fixtures as bds_pw
from kentender_procurement.tenders.seeds import playwright_ui_fixtures as tender_pw

NAMESPACE = "PW_BID_EVALUATION"
PASSWORD = bds_pw.PASSWORD
AO = tender_pw.AO
HOP = tender_pw.HOPF
SECRETARY = tender_pw.OFFICER
AUDITOR = tender_pw.AUDITOR
OUTSIDER = tender_pw.OUTSIDER
CHAIR = "pw.evl.chair@example.test"
MEMBER = "pw.evl.member@example.test"
MEMBER_2 = "pw.evl.member2@example.test"
REPLACEMENT = "pw.evl.replacement@example.test"
SUPPORT = "pw.evl.support@example.test"
PEOPLE = {
	CHAIR: ("Playwright Evaluation Chair", "Budget Approver"),
	MEMBER: ("Playwright Evaluation Member", "Budget Approver"),
	MEMBER_2: ("Playwright Evaluation Member Two", "Budget Approver"),
	REPLACEMENT: ("Playwright Replacement Member", "Budget Approver"),
	SUPPORT: ("Playwright Evaluation Support", "Technical Operator"),
}
SUPPLIER = bds_pw.SUPPLIERS["afya"]["representative"]
BROWSER_ACTORS = (AO, HOP, SECRETARY, AUDITOR, CHAIR, MEMBER, MEMBER_2, REPLACEMENT, SUPPORT, SUPPLIER, "Administrator")
ROSTER = [
	{"user": CHAIR, "department": "Human Resource Management and Development", "capacity": "Chair"},
	{"user": MEMBER, "department": "ICT", "capacity": "Member"},
	{"user": MEMBER_2, "department": "Finance", "capacity": "Member"},
]
Q1 = "Please identify the page and section of your submitted Kenya service-centre details that gives the Nairobi service address."
SCOPE = "Explain the submitted evidence. Do not change your offer or add a new service arrangement."
REPLY = "The service address is on page 2, section 3 of Kenya service-centre details: Westlands Business Park, Waiyaki Way, Nairobi."
NOTE = "Ask the bidder to identify the service address already recorded in its submitted evidence."
REASON = "The offered location meets the stated country requirement, but the supporting document is unclear."
UNIT_PRICE = "160000.00"
BOARD_DEADLINE = "2027-06-12 11:00:00"

# The boards' instants (EVL-CHG-001 v0.4 §11.1), on the opening world's own
# 12 Jun 2027, 11:00 deadline.
AT = {
	"prepare": "2027-06-11 08:58:00", "appoint": "2027-06-11 09:00:00", "secretary": "2027-06-11 09:05:00",
	"declare": ("2027-06-11 09:10:00", "2027-06-11 09:12:00", "2027-06-11 09:14:00"), "conflict": "2027-06-11 09:11:00",
	"intake": "2027-06-12 11:11:10", "review": "2027-06-14 08:45:00", "start": "2027-06-14 09:00:00", "join": ("2027-06-14 09:02:00", "2027-06-14 09:03:00"),
	"note": "2027-06-14 09:04:00", "authorise": "2027-06-14 09:05:00", "end": "2027-06-14 09:06:00", "send": "2027-06-14 09:10:00",
	"reply": "2027-06-15 10:00:00", "deadline": "2027-06-15 17:00:00", "restart": "2027-06-16 09:00:00", "dispose": "2027-06-16 09:05:00",
	"end2": "2027-06-16 09:06:00", "freeze": "2027-06-16 13:55:00", "sign": ("2027-06-16 14:05:00", "2027-06-16 14:06:00", "2027-06-16 14:07:00"),
	"after": "2027-06-16 14:08:00", "pause": "2027-06-14 09:55:00", "paused": "2027-06-14 10:00:00",
}

# Each stage is the stage it grows from and the boards it pictures.
STAGES = {
	"prepared": (None, "D01-APPOINT D02-A (Accounting Officer)"),
	"appointed": ("prepared", "D01-APPOINT-HOP D02-S (Head of Procurement), D02-D (members)"),
	"assigned": ("appointed", "D02-D, D02-CONFLICT (members)"),
	"conflict": ("assigned", "D02-REPLACE, D02-INELIGIBLE (Accounting Officer)"),
	"declared": ("assigned", "S-OPENING-AWAITED"),
	"reviewing": ("declared", "D03 (before findings), D04 (members), S-CHECKS"),
	"concern": ("reviewing", "D03 (chair), D04 service location Needs review"),
	"discussion": ("concern", "D05-START (chair), D05-JOIN (member), D05 (secretary)"),
	"joined": ("discussion", "D05 (secretary), D05-CONCLUSION (chair)"),
	"noted": ("joined", "D05-CHAIR"),
	"authorised": ("noted", "D05-MEMBER, D06-SEND (secretary)"),
	"sent": ("authorised", "D06-SUPPLIER (supplier), waiting"),
	"replied": ("sent", "D06-RECEIVED"),
	"outcome": ("replied", "D06-OUTCOME (chair, in session)"),
	"resolved": ("outcome", "D07-DRAFT (secretary), D03-READY (chair)"),
	"signing": ("resolved", "D07-SIGN (members), D07-REVISE (secretary)"),
	"chair-signed": ("signing", "D07-WAIT (chair)"),
	"report-sent": ("chair-signed", "D07-SENT, D07-HOP, S-AUDITOR"),
	"intake-first": (None, "D02-INTAKE-FIRST, D02-INTAKE-FIRST-HOP"),
	"no-bids": (None, "D02-NO-BIDS"),
	"paused": ("concern", "D08-PAUSED"),
	"cancelled": ("concern", "D08-CANCELLED"),
	"failed": (None, "D04-FAIL (8 GB memory)"),
	"failed-report": ("failed", "D07-NO-RESPONSIVE (every other check reviewed)"),
	"declare-first": ("intake-first", "D02-DECLARE-FIRST (appointed after intake, member not yet declared)"),
	"source-failed": ("declared", "D08-SOURCE, S-SOURCE-OPEN (the opening package could not be loaded)"),
	"member-left": ("joined", "D05-ABSENT, D05-ABSENT-CHAIR, D05-ABSENT-MEMBER"),
	"notice-failed": ("noted", "D06-DELIVERY (the clarification notice failed)"),
	"replacement": ("sent", "D06-WITHDRAW, D06-WITHDRAW-DLG (a replacement question authorised)"),
	"withdrawn": ("replacement", "D06-CLOSED (the supplier's draft on the withdrawn question stays private)"),
	"no-reply": ("sent", "D06-NO-REPLY, D06-LATE (the deadline passed with no reply)"),
	"no-reply-closed": ("no-reply", "D06-FINAL-CLOSED-NR (closed with no reply; the unsent draft stays private)"),
	"late-reply": ("sent", "D06-LATE-REVIEW (a late reply)"),
	"planned": ("resolved", "D08-DD (verification planned)"),
	"observed": ("planned", "D08-DD-FREEZE"),
	"dd-frozen": ("observed", "D08-DD-SIGN"),
	"dd-signed": ("dd-frozen", "D08-VERIFY-OUTCOME, D08-VERIFY-NEG"),
	"supplement": ("resolved", "D08-SUPPLEMENT (an opening correction before delivery)"),
	"no-agreement": ("resolved", "D07-NO-AGREEMENT"),
	"overdue": ("resolved", "D07-OVERDUE, D07-OVERDUE-SEC"),
	"expired": ("resolved", "D07-EXPIRED"),
	"delivery-failed": ("chair-signed", "D07-DELIVERY"),
	"resigning": ("chair-signed", "S-STALE-REPORT (report revised, signing again)"),
	"paused-sign": ("chair-signed", "P-SIGN"),
	"cancelled-sign": ("chair-signed", "C-SIGN"),
	"returned": ("report-sent", "D07-RETURNED"),
	"awarded": ("report-sent", "D08-CORRECTION, D07-DECISION-UNKNOWN(-CHAIR)"),
	"corrected": ("awarded", "D08-CORRECTION-HOP"),
	"decision-unknown": ("report-sent", "D07-DECISION-UNKNOWN, D07-DECISION-UNKNOWN-CHAIR (the later decision cannot be checked)"),
	"supplement-sent": ("report-sent", "D08-SUPPLEMENT-SENT, D08-SUPPLEMENT-HOP"),
	"paused-prep": ("prepared", "P-PREP (appointments permitted)"),
	"cancelled-prep": ("prepared", "C-PREP"),
}


def _key() -> str:
	return f"evl-pw-{uuid4().hex}"


def _ok(result: dict[str, Any], step: str) -> dict[str, Any]:
	if not result or result.get("ok") is False:
		frappe.throw(f"The Bid Evaluation world could not {step}: {result}")
	return result


def _ensure_people() -> None:
	from frappe.utils.password import update_password

	from kentender_core.services import responsibility_administration as administration

	for email, (name, role) in PEOPLE.items():
		tender_pw._user(email, name)
		if not frappe.db.exists("User Responsibility Assignment", {"user": email, "business_role": role, "status": "Enabled"}):
			administration.grant(user=email, business_role=role, organisation_unit="", fixture_namespace=NAMESPACE, actor="Administrator")
		update_password(email, PASSWORD)


def _remove_people() -> None:
	for email in PEOPLE:
		frappe.db.delete("User Responsibility Assignment", {"user": email})
		frappe.db.delete("Notification Log", {"for_user": email})
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)


def _wipe() -> None:
	"""This world's evaluations, and the journal and support rows the browser
	pass wrote as the fixture actors (a browser command carries no namespace)."""
	clear.wipe(tenders=bop_pw.tender_pw_tenders(), namespace=NAMESPACE)
	frappe.db.delete("Evaluation Command Journal", {"actor": ("in", BROWSER_ACTORS)})
	frappe.db.delete("Notification Log", {"email_header": ("like", "evl-%"), "for_user": ("in", BROWSER_ACTORS)})


@contextmanager
def _evaluation_answers(overrides: dict[str, Any] | None = None):
	"""While the opening world fills Afya (Test)'s bid, fill it with the
	evaluation answers (every automatic check can meet) and this world's price."""
	from kentender_procurement.bid_evaluation.test_services import bid_answers
	from kentender_procurement.bid_submission.seeds import filling

	original = filling.fill_everything

	def fill_everything(bid, *, user, tasks=("company", "requirements", "price"), answers=None):
		given = bid_answers.answers(bid, actor=user, at=bds_pw.ANSWERED_AT, overrides=overrides)
		given["price"] = {**_price(bid, user), **(given.get("price") or {})}
		return original(bid, user=user, tasks=tasks, answers={**given, **(answers or {})})

	filling.fill_everything = fill_everything
	try:
		yield
	finally:
		filling.fill_everything = original


def _price(bid: str, user: str) -> dict[str, Any]:
	from decimal import Decimal

	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_context

	ctx = bid_context.load(bid, actor=user, organisation="", at=get_datetime(bds_pw.ANSWERED_AT))
	handle = {f.response_id: f.handle for g in ctx.model.groups_of("price") for f in g.fields if getattr(f, "response_id", None)}
	out: dict[str, Any] = {}
	for row in ctx.model.price_rows:
		inputs = row.get("input_response_ids") or {}
		quantity = Decimal(str(row.get("quantity") or "0"))
		if inputs.get("unit_price") in handle:
			out[handle[inputs["unit_price"]]] = UNIT_PRICE
		if inputs.get("tax_amount") in handle:
			out[handle[inputs["tax_amount"]]] = str((Decimal(UNIT_PRICE) * quantity * Decimal("0.16")).quantize(Decimal("0.01")))
	return out


class EvaluationWorld:
	"""Runs one stage's steps as their actors on the fixture clock."""

	def __init__(self, opening: bop_pw.OpeningWorld):
		self.opening = opening
		self.tender, self.reference = opening.tender, opening.reference
		self.instant = opening.instant
		self.opening_done = False

	def at(self, instant: str) -> None:
		"""A board instant, moved by this world's own deadline (the boards draw 12 Jun 2027, 11:00)."""
		from frappe.utils import get_datetime

		instant = str(get_datetime(instant) + (get_datetime(self.opening.deadline) - get_datetime(BOARD_DEADLINE)))
		self.instant = instant
		for flag in ("kt_evl_clock", "kt_bop_clock", "kt_prc_clock", "kt_bds_clock", "kt_tenders_clock"):
			frappe.flags[flag] = instant

	def shifted(self, instant: str) -> str:
		from frappe.utils import get_datetime

		return str(get_datetime(instant) + (get_datetime(self.opening.deadline) - get_datetime(BOARD_DEADLINE)))

	def version(self) -> int:
		return int(frappe.db.get_value("Evaluation Case", {"tender": self.tender}, "record_version"))

	def bid(self) -> str:
		return frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case()}, "name")

	def case(self) -> str:
		return frappe.db.get_value("Evaluation Case", {"tender": self.tender}, "name")

	def requirement(self, label: str) -> dict[str, Any]:
		from kentender_procurement.bid_evaluation.services import aggregate, checks

		case = self.case()
		return next(r for r in aggregate.bid_results(case, checks.current_run(case), self.bid())["requirements"] if r["label"] == label)

	def complete_opening(self, *, stage: str = "complete") -> None:
		"""The rest of the opening, to its completion with every proof."""
		for name in _chain(bop_pw.STAGES, stage):
			if name not in self.opening.done:
				getattr(self.opening, "stage_" + name.replace("-", "_"))()
				self.opening.done.add(name)
		self.instant = self.opening.instant

	def run(self, stage: str) -> None:
		parent = STAGES[stage][0]
		if parent:
			self.run(parent)
		getattr(self, "stage_" + stage.replace("-", "_"))()

	# -- preparation -----------------------------------------------------------
	def stage_prepared(self) -> None:
		from kentender_procurement.bid_evaluation.services import preparation

		self.at(AT["prepare"])
		_ok(preparation.ensure_preparation(tender=self.tender), "prepare")

	def stage_appointed(self) -> None:
		from kentender_procurement.bid_evaluation.services import appointment

		self.at(AT["appoint"])
		_ok(appointment.appoint_committee(tender=self.tender, members=ROSTER, appointment_reference="MOH/EVAL/PW/2027", expected_version=self.version(),
			idempotency_key=_key(), user=AO), "appoint")

	def stage_assigned(self) -> None:
		from kentender_procurement.bid_evaluation.services import secretary

		self.at(AT["secretary"])
		_ok(secretary.assign_secretary(tender=self.tender, secretary=SECRETARY, appointment_reference="MOH/EVAL/SEC/PW/2027", expected_version=self.version(),
			idempotency_key=_key(), user=HOP), "assign the secretary")

	def stage_conflict(self) -> None:
		from kentender_procurement.bid_evaluation.services import declaration

		self.at(AT["conflict"])
		_ok(declaration.declare_interest(tender=self.tender, choice="Declare a conflict", conflict_description="I have a financial interest in Afya (Test).",
			confidentiality_accepted=True, idempotency_key=_key(), user=MEMBER), "declare a conflict")

	def stage_declared(self) -> None:
		from kentender_procurement.bid_evaluation.services import declaration

		for user, instant in zip((CHAIR, MEMBER, MEMBER_2), AT["declare"]):
			self.at(instant)
			_ok(declaration.declare_interest(tender=self.tender, choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=_key(), user=user),
				f"declare as {user}")

	# -- review ----------------------------------------------------------------
	def stage_reviewing(self) -> None:
		from kentender_procurement.bid_evaluation.services import intake

		self.complete_opening()
		self.at(AT["intake"])
		_ok(intake.receive_opening_package(tender=self.tender), "take up the opening")

	def stage_concern(self) -> None:
		"""Every evidence check reviewed as Meets, except the service location."""
		from kentender_procurement.bid_evaluation.services import aggregate, checks, findings

		self.at(AT["review"])
		case = self.case()
		for r in aggregate.bid_results(case, checks.current_run(case), self.bid())["requirements"]:
			if r["result"] != "Needs review":
				continue
			service = r["label"] == "Service location"
			_ok(findings.record_evidence_finding(tender=self.tender, bid=self.bid(), requirement_key=r["requirement_key"], result="Needs review" if service else "Meets",
				reason="The submitted evidence does not clearly identify the service address." if service else "Required evidence reviewed.",
				evidence_reference="Kenya service-centre details" if service else "Submitted evidence", idempotency_key=_key(), user=MEMBER), f"review {r['label']}")

	def stage_discussion(self) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		self.at(AT["start"])
		_ok(discussion.start_discussion(tender=self.tender, subject="Afya service-location evidence", idempotency_key=_key(), user=CHAIR), "start the discussion")
		_ok(discussion.join_discussion(tender=self.tender, idempotency_key=_key(), user=SECRETARY), "join as the secretary")

	def stage_joined(self) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		for user, instant in zip((MEMBER, MEMBER_2), AT["join"]):
			self.at(instant)
			_ok(discussion.join_discussion(tender=self.tender, idempotency_key=_key(), user=user), f"join as {user}")

	def stage_noted(self) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		self.at(AT["note"])
		_ok(discussion.record_note(tender=self.tender, subject="Afya service-location evidence", note=NOTE, reason=REASON, idempotency_key=_key(), user=SECRETARY),
			"record the note")

	def stage_authorised(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification

		self.at(AT["authorise"])
		_ok(clarification.authorise(tender=self.tender, bid=self.bid(), requirement_key=self.requirement("Service location")["requirement_key"], question=Q1,
			reply_scope=SCOPE, reply_deadline=self.shifted(AT["deadline"]), idempotency_key=_key(), user=CHAIR), "authorise the clarification")

	def _request(self) -> str:
		return frappe.db.get_value("Evaluation Clarification", {"evaluation_case": self.case()}, "name", order_by="creation desc")

	def stage_sent(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification, discussion

		self.at(AT["end"])
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end the discussion")
		self.at(AT["send"])
		_ok(clarification.send(tender=self.tender, clarification=self._request(), idempotency_key=_key(), user=SECRETARY), "send the clarification")

	def stage_replied(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification

		self.at(AT["reply"])
		_ok(clarification.submit_reply(tender=self.tender, clarification=self._request(), body=REPLY, idempotency_key=_key(), user=SUPPLIER), "reply")

	def stage_outcome(self) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		self.at(AT["restart"])
		_ok(discussion.start_discussion(tender=self.tender, subject="Resolve reply and complete findings", idempotency_key=_key(), user=CHAIR), "restart")
		for user in (SECRETARY, MEMBER, MEMBER_2):
			_ok(discussion.join_discussion(tender=self.tender, idempotency_key=_key(), user=user), f"rejoin as {user}")

	def stage_resolved(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification, discussion

		self.at(AT["dispose"])
		_ok(clarification.record_disposition(tender=self.tender, clarification=self._request(), disposition="Considered", result="Meets",
			reason="The address is present in the original submitted document and is within Kenya.", idempotency_key=_key(), user=CHAIR), "record the reply outcome")
		self.at(AT["end2"])
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end the second discussion")

	def stage_signing(self) -> None:
		from kentender_procurement.bid_evaluation.services import report, signing

		self.at(AT["freeze"])
		draft = report.draft(frappe.get_doc("Evaluation Case", self.case()))
		_ok(signing.send_for_signing(tender=self.tender, expected_version=draft.record_version, idempotency_key=_key(), user=SECRETARY), "send for signing")

	def _sign(self, user: str, instant: str) -> None:
		from kentender_procurement.bid_evaluation.services import signing

		self.at(instant)
		version = signing.signing_version(frappe.get_doc("Evaluation Case", self.case())).name
		_ok(signing.sign(tender=self.tender, report_version=version, idempotency_key=_key(), user=user), f"sign as {user}")

	def stage_chair_signed(self) -> None:
		self._sign(CHAIR, AT["sign"][0])

	def stage_report_sent(self) -> None:
		self._sign(MEMBER, AT["sign"][1])
		self._sign(MEMBER_2, AT["sign"][2])
		self.at(AT["after"])

	# -- branches ----------------------------------------------------------------
	def stage_intake_first(self) -> None:
		from kentender_procurement.bid_evaluation.services import sweep

		self.complete_opening()
		self.at(AT["intake"])
		sweep.sweep_tender(self.tender)

	def stage_no_bids(self) -> None:
		from kentender_procurement.bid_evaluation.services import sweep

		self.stage_prepared()
		self.stage_appointed()
		self.stage_assigned()
		self.stage_declared()
		self.complete_opening(stage="empty-complete")
		self.at(AT["intake"])
		sweep.sweep_tender(self.tender)

	def stage_paused(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at(AT["pause"])
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Suspension", instruction_reference="MOH/REVIEW/PW/2027", authority=AO), "suspend")
		self.at(AT["paused"])

	def stage_cancelled(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at(AT["pause"])
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Cancellation", instruction_reference="MOH/CANCEL/PW/2027", authority=AO,
			reason="Procurement proceedings terminated under the recorded decision."), "cancel")
		self.at(AT["paused"])

	def stage_failed(self) -> None:
		for name in ("prepared", "appointed", "assigned", "declared", "reviewing"):
			getattr(self, "stage_" + name)()


class _Branches:
	"""Branch stages (EVL-CHG-001 v0.4 §11.2), each from where it leaves the
	ordinary path; attached to EvaluationWorld below."""

	def stage_failed_report(self) -> None:
		self.at(AT["review"])
		self._review_all(skip=())

	def _review_all(self, *, skip=("Service location",)) -> None:
		from kentender_procurement.bid_evaluation.services import aggregate, checks, findings

		case = self.case()
		for r in aggregate.bid_results(case, checks.current_run(case), self.bid())["requirements"]:
			if r["result"] == "Needs review" and r["label"] not in skip:
				_ok(findings.record_evidence_finding(tender=self.tender, bid=self.bid(), requirement_key=r["requirement_key"], result="Meets",
					reason="Required evidence reviewed.", evidence_reference="Submitted evidence", idempotency_key=_key(), user=MEMBER), f"review {r['label']}")

	def stage_declare_first(self) -> None:
		from kentender_procurement.bid_evaluation.services import appointment

		self.at("2027-06-12 11:20:00")
		_ok(appointment.appoint_committee(tender=self.tender, members=ROSTER, appointment_reference="MOH/EVAL/PW/2027", expected_version=self.version(),
			idempotency_key=_key(), user=AO), "appoint after intake")

	def stage_source_failed(self) -> None:
		from kentender_procurement.bid_evaluation.services import intake, simulation

		self.complete_opening()
		self.at(AT["intake"])
		simulation.set_controls(intake_outcome="Unavailable")
		intake.receive_opening_package(tender=self.tender)

	def stage_member_left(self) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		self.at("2027-06-14 09:03:30")
		_ok(discussion.leave_discussion(tender=self.tender, idempotency_key=_key(), user=MEMBER_2), "leave")

	def stage_notice_failed(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification, discussion, simulation

		self.stage_authorised()
		self.at(AT["end"])
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end the discussion")
		simulation.set_controls(notice_outcome="Failed")
		self.at(AT["send"])
		clarification.send(tender=self.tender, clarification=self._request(), idempotency_key=_key(), user=SECRETARY)

	def _session(self, instant: str) -> None:
		from kentender_procurement.bid_evaluation.services import discussion

		self.at(instant)
		_ok(discussion.start_discussion(tender=self.tender, subject="Resolve reply and complete findings", idempotency_key=_key(), user=CHAIR), "start")
		for user in (SECRETARY, MEMBER, MEMBER_2):
			_ok(discussion.join_discussion(tender=self.tender, idempotency_key=_key(), user=user), f"join as {user}")

	def stage_replacement(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification

		self.at("2027-06-15 09:30:00")
		_ok(clarification.save_draft(tender=self.tender, clarification=self._request(), body=REPLY, idempotency_key=_key(), user=SUPPLIER), "save a draft")
		self._session("2027-06-15 09:40:00")
		self.at("2027-06-15 09:45:00")
		original = self._request()
		_ok(clarification.authorise(tender=self.tender, bid=self.bid(), requirement_key=self.requirement("Service location")["requirement_key"],
			question="In the document titled Kenya service-centre details submitted with your bid, identify the page and section containing the Nairobi service address.",
			reply_scope=SCOPE, reply_deadline=self.shifted("2027-06-16 17:00:00"), replaces=original, replacement_reason="Clarify the document reference.",
			idempotency_key=_key(), user=CHAIR), "authorise a replacement")

	def stage_no_reply(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification

		self.at("2027-06-15 12:00:00")
		_ok(clarification.save_draft(tender=self.tender, clarification=self._request(), body=REPLY, idempotency_key=_key(), user=SUPPLIER), "save a draft")
		self._session(AT["restart"])

	def stage_no_reply_closed(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification, discussion

		self.at(AT["dispose"])
		_ok(clarification.record_disposition(tender=self.tender, clarification=self._request(), disposition="No reply", result="Needs review",
			reason="No reply was received; assess the original evidence.", idempotency_key=_key(), user=CHAIR), "dispose with no reply")
		self.at(AT["end2"])
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end")

	def stage_withdrawn(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification, discussion

		first = frappe.db.get_value("Evaluation Clarification", {"evaluation_case": self.case(), "replaced_by": ("is", "set")}, "name")
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end")
		self.at("2027-06-15 09:46:00")
		_ok(clarification.withdraw(tender=self.tender, clarification=first, reason="Clarify the document reference.", idempotency_key=_key(), user=SECRETARY),
			"withdraw")
		self.at("2027-06-15 09:50:00")
		_ok(clarification.send(tender=self.tender, clarification=self._request(), idempotency_key=_key(), user=SECRETARY), "send the new question")
		self.at("2027-06-15 09:55:00")

	def stage_late_reply(self) -> None:
		from kentender_procurement.bid_evaluation.services import clarification

		self.at("2027-06-15 17:05:00")
		_ok(clarification.submit_reply(tender=self.tender, clarification=self._request(), body=REPLY, idempotency_key=_key(), user=SUPPLIER), "late reply")
		self._session(AT["restart"])

	def stage_planned(self) -> None:
		from kentender_procurement.bid_evaluation.services import diligence, discussion

		self._session("2027-06-16 09:10:00")
		self.at("2027-06-16 09:14:00")
		_ok(diligence.record_plan(tender=self.tender, scope="Verify the two submitted comparable contracts",
			basis="Due diligence under PPADA section 83; verify the two submitted comparable contracts", participants_=[CHAIR, MEMBER_2], lead=CHAIR,
			idempotency_key=_key(), user=CHAIR), "record the verification plan")
		self.at("2027-06-16 09:15:00")
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end")

	def stage_observed(self) -> None:
		from kentender_procurement.bid_evaluation.services import diligence

		for user, instant in ((MEMBER_2, "2027-06-16 10:00:00"), (CHAIR, "2027-06-16 10:30:00")):
			self.at(instant)
			_ok(diligence.record_observation(tender=self.tender, findings_="Both customers confirmed the submitted contract details.", idempotency_key=_key(),
				user=user), f"observe as {user}")

	def stage_dd_frozen(self) -> None:
		from kentender_procurement.bid_evaluation.services import diligence

		self.at("2027-06-16 10:50:00")
		_ok(diligence.send_for_signing(tender=self.tender, idempotency_key=_key(), user=CHAIR), "freeze the verification report")
		self.at("2027-06-16 10:55:00")
		_ok(diligence.sign(tender=self.tender, idempotency_key=_key(), user=CHAIR), "sign as the lead")

	def stage_dd_signed(self) -> None:
		from kentender_procurement.bid_evaluation.services import diligence

		self.at("2027-06-16 11:00:00")
		_ok(diligence.sign(tender=self.tender, idempotency_key=_key(), user=MEMBER_2), "sign as the participant")
		self._session("2027-06-16 11:10:00")

	def _opening_correction(self, instant: str) -> None:
		from kentender_procurement.bid_evaluation.services import correction
		from kentender_procurement.bid_opening.services import correction as opening_correction

		self.at(instant)
		with _opening_flags():
			_ok(opening_correction.correct_opening_record(tender=self.tender, kind="Attendance note", correct_information="David Ouma left at 11:05 EAT",
				reason="Add the departure noted during the opening", expected_version=self.opening.version(), idempotency_key=_key(), user=self.opening.chair),
				"correct the opening record")
		correction.consume_supplements(self.tender)

	def stage_supplement(self) -> None:
		self._opening_correction("2027-06-16 12:55:00")
		self.at("2027-06-16 13:00:00")

	def stage_supplement_sent(self) -> None:
		self._opening_correction("2027-06-17 09:55:00")
		self.at("2027-06-17 10:00:00")

	def stage_no_agreement(self) -> None:
		from kentender_procurement.bid_evaluation.services import conclusion, discussion

		self._session("2027-06-16 13:00:00")
		out = _ok(conclusion.record_case_conclusion(tender=self.tender, kind="No agreed recommendation",
			reason="The committee could not agree whether the evidence supports the service location.", idempotency_key=_key(), user=CHAIR), "no agreement")
		_ok(conclusion.record_disagreement(tender=self.tender, statement="I cannot establish that the submitted evidence supports the stated service location.",
			conclusion=out.get("conclusion", ""), idempotency_key=_key(), user=MEMBER_2), "disagree")
		_ok(discussion.end_discussion(tender=self.tender, idempotency_key=_key(), user=CHAIR), "end")

	def stage_overdue(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		# the dated rule Tenders does not yet publish (FU-EVL-18), as the owner event it will be
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Dated rule", instruction_reference="MOH/EVAL-PERIOD/PW/2027", authority=AO,
			effective_at=self.shifted("2027-07-12 11:00:00"), detail={"counting": "30 days from the completed opening", "timezone": "Site time (EAT)"}),
			"record the evaluation period")
		self.at("2027-07-13 09:00:00")

	def stage_expired(self) -> None:
		self.at("2027-10-12 09:00:00")

	def stage_delivery_failed(self) -> None:
		from kentender_procurement.bid_evaluation.services import simulation

		simulation.set_controls(delivery_outcome="Failed")
		self._sign(MEMBER, AT["sign"][1])
		self._sign(MEMBER_2, AT["sign"][2])
		self.at("2027-06-16 14:07:30")

	def stage_resigning(self) -> None:
		from kentender_procurement.bid_evaluation.services import report, signing

		self.at("2027-06-16 14:05:30")
		self.first_report = signing.signing_version(frappe.get_doc("Evaluation Case", self.case())).name
		_ok(signing.revise(tender=self.tender, reason="Correct the service-address page reference.", idempotency_key=_key(), user=SECRETARY), "revise")
		self.at("2027-06-16 14:20:00")
		draft = report.draft(frappe.get_doc("Evaluation Case", self.case()))
		_ok(signing.send_for_signing(tender=self.tender, expected_version=draft.record_version, idempotency_key=_key(), user=SECRETARY), "send report 2")

	def stage_paused_sign(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at("2027-06-16 14:05:20")
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Suspension", instruction_reference="MOH/REVIEW/PW/2027-SIGN", authority=AO), "suspend")
		self.at("2027-06-16 14:05:30")

	def stage_cancelled_sign(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at("2027-06-16 14:05:20")
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Cancellation", instruction_reference="MOH/CANCEL/PW/2027-SIGN", authority=AO,
			reason="Procurement proceedings terminated under the recorded decision."), "cancel")
		self.at("2027-06-16 14:05:30")

	def stage_returned(self) -> None:
		from kentender_procurement.bid_evaluation.services import correction

		self.at("2027-06-16 14:30:00")
		_ok(correction.return_report(tender=self.tender, comment="Correct the service-address page reference from page 3 to page 2.", idempotency_key=_key(),
			user=HOP), "return the report")
		self.at("2027-06-16 15:00:00")

	def stage_awarded(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at("2027-06-17 09:00:00")
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Award decision", instruction_reference="MOH/AWARD/PW/2027", authority=AO,
			effective_at=self.instant), "record the award decision")
		self.at("2027-06-17 10:00:00")

	def stage_decision_unknown(self) -> None:
		from kentender_procurement.bid_evaluation.services import simulation

		simulation.set_controls(downstream_status="Unknown")
		self.at("2027-06-17 10:00:00")

	def stage_corrected(self) -> None:
		from kentender_procurement.bid_evaluation.services import correction

		_ok(correction.record_correction_notice(tender=self.tender, reason="The report gives the wrong page reference for the service address.",
			correction="Read page 2, section 3, instead of page 3.", idempotency_key=_key(), user=CHAIR), "record the correction notice")

	def stage_paused_prep(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at("2027-06-11 08:55:00")
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Suspension", instruction_reference="MOH/REVIEW/PW/2027-PREP", authority=AO,
			permitted_actions=["appointments", "declarations"]), "suspend with appointments permitted")
		self.at(AT["prepare"])

	def stage_cancelled_prep(self) -> None:
		from kentender_procurement.bid_evaluation.services import tender_events

		self.at("2027-06-11 08:55:00")
		_ok(tender_events.record_simulated_event(tender=self.tender, kind="Cancellation", instruction_reference="MOH/CANCEL/PW/2027-PREP", authority=AO,
			reason="Procurement proceedings terminated under the recorded decision."), "cancel in preparation")
		self.at(AT["prepare"])


@contextmanager
def _opening_flags():
	saved = {k: frappe.flags.get(k) for k in ("kt_bop_fixture_namespace", "kt_prc_fixture_namespace")}
	frappe.flags.kt_bop_fixture_namespace = frappe.flags.kt_prc_fixture_namespace = bop_pw.NAMESPACE
	try:
		yield
	finally:
		for k, v in saved.items():
			frappe.flags[k] = v


for _name, _fn in vars(_Branches).items():
	if _name.startswith(("stage_", "_")) and callable(_fn) and not _name.startswith("__"):
		setattr(EvaluationWorld, _name, _fn)


def _chain(stages: dict[str, tuple], stage: str) -> list[str]:
	out = []
	while stage:
		out.insert(0, stage)
		stage = stages[stage][0]
	return out


FLAGS = ("kt_bop_fixture_namespace", "kt_prc_fixture_namespace", "kt_bds_fixture_namespace", "kt_evl_fixture_namespace", "kt_evl_clock", "kt_bop_clock",
	"kt_prc_clock", "kt_bds_clock", "kt_tenders_clock")


@contextmanager
def _world_flags(walker: "EvaluationWorld | None" = None):
	"""This world's namespaces and, when continuing a world, its clock."""
	saved = {k: frappe.flags.get(k) for k in FLAGS}
	frappe.flags.kt_bop_fixture_namespace = frappe.flags.kt_prc_fixture_namespace = bop_pw.NAMESPACE
	frappe.flags.kt_bds_fixture_namespace = bds_pw.NAMESPACE
	frappe.flags.kt_evl_fixture_namespace = NAMESPACE
	if walker is not None:
		for flag in ("kt_evl_clock", "kt_bop_clock", "kt_prc_clock", "kt_bds_clock", "kt_tenders_clock"):
			frappe.flags[flag] = walker.instant
	try:
		yield
	finally:
		for k, v in saved.items():
			frappe.flags[k] = v


def _finish(walker: "EvaluationWorld", *, commit: bool) -> None:
	from kentender_procurement.bid_submission.services import simulation as bds_simulation

	bds_pw.set_instant(walker.instant)
	bds_simulation.set_controls(reveal_outcome="Deliver")
	frappe.set_user("Administrator")
	if commit:
		frappe.db.commit()


def _start(stage: str) -> "EvaluationWorld":
	"""A fresh world at `stage` (see STAGES)."""
	from kentender_procurement.bid_evaluation.services import simulation
	from kentender_procurement.bid_opening.services import simulation as bop_simulation
	from kentender_procurement.bid_submission.services import simulation as bds_simulation

	if stage not in STAGES:
		raise ValueError(f"unknown Bid Evaluation world {stage!r}; one of {tuple(STAGES)}")
	_wipe()
	empty = stage == "no-bids"
	with _evaluation_answers({"memory": 8} if stage == "failed" else None):
		world = bds_pw.reset_my_bids_fixture(state="ready" if empty else "submitted", commit=False)
	bop_pw._wipe()
	bop_pw._ensure_people()
	_ensure_people()
	bop_simulation.reset_controls()
	simulation.reset_controls()
	bds_simulation.set_controls(custody_service_down=0, reveal_outcome="Deliver")
	tender = frappe.db.get_value("Tender", {"tender_reference": world["tender_reference"]}, "name")
	opening = bop_pw.OpeningWorld(tender, world["tender_reference"])
	opening.done = set()
	with _world_flags():
		# the opening arrangements are published before the evaluation is prepared
		for name in _chain(bop_pw.STAGES, "empty-started" if empty else "published")[:3]:
			getattr(opening, "stage_" + name)()
			opening.done.add(name)
		walker = EvaluationWorld(opening)
		walker.run(stage)
	return walker


def _summary(walker: "EvaluationWorld", stage: str) -> dict[str, Any]:
	case = frappe.db.get_value("Evaluation Case", {"tender": walker.tender}, "name")
	return {"stage": stage, "tender": walker.tender, "tender_reference": walker.reference, "password": PASSWORD, "instant": walker.instant, "evaluation": case or "",
		"bid": frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "name") if case else "",
		"clarification": frappe.db.get_value("Evaluation Clarification", {"evaluation_case": case}, "name", order_by="creation desc") if case else "",
		"people": {"ao": AO, "hop": HOP, "secretary": SECRETARY, "chair": CHAIR, "member": MEMBER, "member_2": MEMBER_2, "auditor": AUDITOR, "outsider": OUTSIDER,
			"replacement": REPLACEMENT, "support": SUPPORT, "supplier": SUPPLIER}}


def reset_evaluation_fixture(*, stage: str = "prepared", commit: bool = True) -> dict[str, Any]:
	"""A Bid Evaluation world at `stage` (see STAGES for the boards each pictures)."""
	walker = _start(stage)
	_finish(walker, commit=commit)
	return _summary(walker, stage)


# The component fixtures: one world walked along the ordinary path, captured
# at every stage, and each branch built once from where it leaves the path.
CAPTURE_PATHS = (
	("prepared", "appointed", "assigned", "declared", "reviewing", "concern", "discussion", "joined", "noted", "authorised", "sent", "replied", "outcome",
		"resolved", "signing", "chair-signed", "report-sent", "awarded", "corrected"),
	("conflict",), ("intake-first", "declare-first"), ("no-bids",), ("paused",), ("cancelled",), ("failed", "failed-report"), ("source-failed",),
	("member-left",), ("notice-failed",), ("replacement", "withdrawn"), ("no-reply", "no-reply-closed"), ("late-reply",), ("planned", "observed", "dd-frozen", "dd-signed"),
	("supplement",), ("no-agreement",), ("overdue", "expired"), ("delivery-failed",), ("resigning",), ("paused-sign",), ("cancelled-sign",), ("returned",),
	("supplement-sent",), ("paused-prep",), ("cancelled-prep",), ("decision-unknown",),
)


def capture_all(*, paths: list[list[str]] | None = None) -> dict[str, Any]:
	"""Write `public/js/bid_evaluation/fixtures/<stage>.json` for every stage:
	what each reader's reads return there. Builds one world per path."""
	import json
	import os

	out_dir = frappe.get_app_path("kentender_procurement", "public", "js", "bid_evaluation", "fixtures")
	os.makedirs(out_dir, exist_ok=True)
	written = []
	for path in paths or CAPTURE_PATHS:
		walker = _start(path[0])
		for i, stage in enumerate(path):
			if i:
				with _world_flags(walker):
					getattr(walker, "stage_" + stage.replace("-", "_"))()
			_finish(walker, commit=True)
			with open(os.path.join(out_dir, f"{stage}.json"), "w") as fh:
				json.dump(capture(), fh, sort_keys=True, separators=(",", ":"), default=str)
				fh.write("\n")
			written.append(stage)
	restore_site()
	return {"written": written}


def supplier_reply(*, body: str = REPLY) -> dict[str, Any]:
	"""The supplier's reply to the latest clarification, as the supplier
	portal will send it (the portal screens are Phase 12)."""
	from kentender_procurement.bid_evaluation.services import clarification

	case = frappe.db.get_value("Evaluation Case", {"fixture_namespace": NAMESPACE}, ["name", "tender"], as_dict=True)
	request = frappe.db.get_value("Evaluation Clarification", {"evaluation_case": case.name}, "name", order_by="creation desc")
	frappe.set_user(SUPPLIER)
	try:
		out = clarification.submit_reply(tender=case.tender, clarification=request, body=body, idempotency_key=_key(), user=SUPPLIER)
	finally:
		frappe.set_user("Administrator")
	frappe.db.commit()
	return out


def set_instant(*, instant: str = "") -> dict[str, Any]:
	"""The site's shared test instant (every module's trusted clock on a test
	site), returning the one it replaces so a walk can put it back."""
	from kentender_procurement.bid_submission.services import simulation as bds_simulation

	previous = bds_simulation.controls().get("current_instant") or ""
	bds_simulation.set_controls(current_instant=instant)
	frappe.db.commit()
	return {"previous": previous, "instant": instant}


def set_controls(**values) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import simulation

	out = simulation.set_controls(**values)
	frappe.db.commit()
	return {k: out.get(k) for k in values}


def capture(*, users: list[str] | None = None) -> dict[str, Any]:
	"""What each reader's reads return in the current world: the evaluation,
	the first bid, the report, the committee record and the appointment pick
	lists. The component fixtures are these answers, never hand-written ones."""
	from kentender_procurement.bid_evaluation.services import reads

	reference = frappe.db.get_value("Evaluation Case", {"fixture_namespace": NAMESPACE}, "tender_reference")
	case = frappe.db.get_value("Evaluation Case", {"fixture_namespace": NAMESPACE}, "name")
	bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "name") if case else None

	def attempt(fn, **kwargs):
		try:
			return fn(tender_reference=reference, **kwargs)
		except Exception:
			return None

	out = {}
	for user in users or (AO, HOP, CHAIR, MEMBER, MEMBER_2, SECRETARY, AUDITOR, "Administrator"):
		data = attempt(reads.resolve, user=user)
		if data is None:
			out[user] = None
			continue
		report = attempt(reads.report_view, user=user)
		earlier = [h for h in (report or {}).get("history") or [] if h.get("name") != (report or {}).get("report")]
		out[user] = {"data": data, "bid": attempt(reads.bid, bid=bid, user=user) if bid else None, "report": report,
			"report_previous": attempt(reads.report_view, user=user, version=earlier[-1]["name"]) if earlier else None,
			"record": attempt(reads.committee_record, user=user), "candidates": attempt(reads.candidates, user=user, purpose="secretary" if user == HOP else "committee"),
			"work": reads.list_work(user=user)}
	# the supplier's own requests, as the portal reads them
	supplier = []
	for request in frappe.get_all("Evaluation Clarification", filters={"evaluation_case": case, "status": ("!=", "Authorised")}, pluck="name",
			order_by="creation asc") if case else []:
		supplier.append(attempt(reads.own_clarification, clarification=request, user=SUPPLIER))
	out["supplier"] = {"data": None, "own": supplier}
	out = frappe.parse_json(frappe.as_json(out))
	# a read identical to an earlier reader's is kept once: {"$same_as": that reader}
	seen: dict[tuple[str, str], str] = {}
	for user, answer in out.items():
		for part, value in (answer or {}).items():
			if value in (None, [], {}):
				continue
			sig = (part, frappe.as_json(value))
			if sig in seen:
				answer[part] = {"$same_as": seen[sig]}
			else:
				seen[sig] = user
	return out


def restore_site(*, commit: bool = True) -> dict[str, Any]:
	from kentender_procurement.bid_evaluation.services import simulation

	frappe.set_user("Administrator")
	_wipe()
	simulation.reset_controls()
	_remove_people()
	out = bop_pw.restore_site(commit=False)
	if commit:
		frappe.db.commit()
	return {**out, "bid_evaluation_wiped": True}
