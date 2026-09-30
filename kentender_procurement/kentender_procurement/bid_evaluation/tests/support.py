# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The Bid Evaluation test world (EVL-CHG-001 v0.4 plan D17): the Bid Opening
test world's published Tender, one bid answered from the Tender's own
published requirements (with named overrides for a branch), a completed
opening, and the evaluation people. All clocks move together. Everything the
world writes is removed afterwards (the always-remove-test-data rule): the
opening world purges its own rows, and this world purges Evaluation's."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_evaluation.seeds import clear
from kentender_procurement.bid_evaluation.services import simulation
from kentender_procurement.bid_evaluation.test_services import bid_answers
from kentender_procurement.bid_opening.tests.support import CHAIR as OPENING_CHAIR
from kentender_procurement.bid_opening.tests.test_bop_record import RecordCase
from kentender_procurement.bid_submission.tests.support import DAVID
from kentender_procurement.tenders.tests import fixtures as tender_fx

NS = "EVL_TEST"
AO = tender_fx.AO
HOP = tender_fx.HOPF
SECRETARY = tender_fx.OFFICER  # the Procurement Officer the Head appoints in writing
CHAIR = "evlt.chair@example.test"
MEMBER = "evlt.member@example.test"
MEMBER_2 = "evlt.member2@example.test"
REPLACEMENT = "evlt.replacement@example.test"
SUPPORT = "evlt.support@example.test"
AUDITOR = tender_fx.AUDITOR
OUTSIDER = tender_fx.OUTSIDER
SUPPLIER = DAVID
PEOPLE = {
	CHAIR: ("Test Evaluation Chair", "Budget Approver"),
	MEMBER: ("Test Evaluation Member", "Budget Approver"),
	MEMBER_2: ("Test Evaluation Member Two", "Budget Approver"),
	REPLACEMENT: ("Test Replacement Member", "Budget Approver"),
	SUPPORT: ("Test Evaluation Support", "Technical Operator"),
}


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


def wipe_evaluations() -> None:
	clear.wipe(tenders=set(tender_fx.test_tenders()), namespace=NS)
	frappe.db.commit()


ROSTER = [
	{"user": CHAIR, "department": "Human Resource Management and Development", "capacity": "Chair"},
	{"user": MEMBER, "department": "ICT", "capacity": "Member"},
	{"user": MEMBER_2, "department": "Finance", "capacity": "Member"},
]


WORLD_FLAGS = ("kt_supplier_account_provider", "kt_tender_candidate_registry", "kt_bds_fixture_namespace", "kt_bop_fixture_namespace",
	"kt_prc_fixture_namespace")
CLOCKS = ("kt_tenders_clock", "kt_bds_clock", "kt_bop_clock", "kt_prc_clock", "kt_evl_clock")

# The world the test module's classes share, and the base worlds' class
# clean-ups held until the module ends (see EvaluationCase).
_MODULE: dict[str, Any] = {"module": None, "key": None, "world": None, "release": None, "held": []}


def _module_state(module: str) -> dict[str, Any]:
	import unittest

	if _MODULE["module"] != module:
		_MODULE.update(module=module, key=None, world=None, release=None, held=[])
		unittest.addModuleCleanup(_release_module)
	return _MODULE


def _drop_world() -> None:
	"""Remove the shared world (its Tender, bid and opening)."""
	release, _MODULE["release"] = _MODULE["release"], None
	_MODULE.update(key=None, world=None)
	if release:
		release()


def _release_module() -> None:
	_drop_world()
	held, _MODULE["held"] = _MODULE["held"], []
	for fn, args, kwargs in reversed(held):
		fn(*args, **kwargs)
	frappe.db.commit()


class EvaluationCase(RecordCase):
	"""One evaluation world per test module (the published Tender, the bid and
	the opening are built once), and a clean evaluation for every test.

	Building the Tender, filling and submitting the bid and running the whole
	opening ceremony is what made each test cost 20–40 seconds; an evaluation
	test changes none of it. So the first test that needs a world builds it
	with the ordinary opening-world setup, and the clean-ups that would remove
	it (the base classes' per-test and per-class ones) are held until the
	module ends. Every test starts from the same point: no Evaluation rows, the
	opening's hand-off not yet taken up, the simulation switches off, and the
	clocks at the world's own instant.

	`world` picks where the world stops: "completed" (the ordinary opening,
	completed with every member's proof), "empty" (an opening that ended with
	no bids) or "open" (the bid filled but nothing submitted or opened);
	`overrides` changes the bid's answers. Classes with the same world and
	overrides share it; a class with a different one replaces it. A class whose
	tests each need the opening to happen at their own moment sets
	`shared_world = False` and builds per test, as before."""

	#: Requirement values to submit instead of the compliant ones (bid_answers).
	overrides: dict[str, Any] = {}
	world: str = "completed"
	shared_world: bool = True

	@classmethod
	def world_key(cls) -> tuple:
		return (cls.world, tuple(sorted(cls.overrides.items())))

	@classmethod
	def setUpClass(cls):
		if not cls.shared_world:
			_drop_world()  # its per-test setup wipes every test Tender
			super().setUpClass()
			ensure_people()
			cls.addClassCleanup(remove_people)
			cls.addClassCleanup(wipe_evaluations)
			return
		held = _module_state(cls.__module__)["held"]

		def hold(fn, *args, **kwargs):
			if not any(h[0] is fn and h[1] == args for h in held):
				held.append((fn, args, kwargs))

		cls.addClassCleanup = hold  # type: ignore[method-assign]
		# Frappe's class setup deep-copies the flags; the world's own flags hold
		# a module (the candidate registry), and every test sets them again.
		for flag in WORLD_FLAGS:
			frappe.flags.pop(flag, None)
		try:
			super().setUpClass()
		finally:
			del cls.addClassCleanup
		ensure_people()
		hold(remove_people)
		cls.addClassCleanup(wipe_evaluations)

	def setUp(self):
		if not self.shared_world:
			wipe_evaluations()
			super().setUp()
			self._fresh_evaluation()
			bid_answers.fill(self.bid, actor=SUPPLIER, at=str(frappe.flags.get("kt_bop_clock") or "2027-05-30 14:30:00"), overrides=self.overrides)
			return
		if not self._built():
			_drop_world()
			self._build_world()
		world = _MODULE["world"]
		self.__dict__.update(world["attrs"])
		for flag, value in world["flags"].items():
			frappe.flags[flag] = value
		frappe.set_user("Administrator")
		wipe_evaluations()
		self._reset_handoff()
		for flag in CLOCKS:
			frappe.flags[flag] = world["clocks"].get(flag)
			self.addCleanup(frappe.flags.__setitem__, flag, world["clocks"].get(flag))
		self._fresh_evaluation()

	def _built(self) -> bool:
		"""The module's shared world is this class's (so the opening it stands for has happened)."""
		return self.shared_world and _MODULE["world"] is not None and _MODULE["key"] == self.world_key()

	def _fresh_evaluation(self) -> None:
		self._flag("kt_evl_fixture_namespace", NS)
		simulation.reset_controls()
		self.addCleanup(simulation.reset_controls)
		self.set_lapse(0)  # participation lapse off unless a test turns it on
		self.addCleanup(wipe_evaluations)

	def _build_world(self) -> None:
		"""The shared world, with the opening world's per-test clean-ups held
		until the world is replaced or the module ends."""
		held: list[tuple] = []
		self.addCleanup = lambda fn, *args, **kwargs: held.append((fn, args, kwargs))  # type: ignore[method-assign]
		try:
			wipe_evaluations()
			super().setUp()
			bid_answers.fill(self.bid, actor=SUPPLIER, at=str(frappe.flags.get("kt_bop_clock") or "2027-05-30 14:30:00"), overrides=self.overrides)
			if self.world == "completed":
				super().completed()
			elif self.world == "empty":
				self._run_empty_opening()
			frappe.db.commit()
		except BaseException:
			for fn, args, kwargs in reversed(held):
				fn(*args, **kwargs)
			raise
		finally:
			del self.addCleanup

		def release() -> None:
			for fn, args, kwargs in reversed(held):
				fn(*args, **kwargs)
			frappe.db.commit()

		_MODULE.update(key=self.world_key(), release=release, world={
			"attrs": {k: v for k, v in self.__dict__.items() if not k.startswith("_")},
			"flags": {k: frappe.flags.get(k) for k in WORLD_FLAGS},
			"clocks": {k: frappe.flags.get(k) for k in CLOCKS},
		})

	def _reset_handoff(self) -> None:
		"""Test-world only: the opening's hand-off back to Pending, as it is
		before any evaluation takes it up (intake acknowledges it)."""
		frappe.db.set_value("Evaluation Handoff", {"tender": self.name, "consumer": "evaluation"}, "delivery_status", "Pending", update_modified=False)
		frappe.db.commit()

	def set_lapse(self, seconds: int) -> None:
		previous = frappe.db.get_single_value("Bid Evaluation Settings", "presence_lapse_seconds")
		frappe.db.set_single_value("Bid Evaluation Settings", "presence_lapse_seconds", seconds)
		self.addCleanup(frappe.db.set_single_value, "Bid Evaluation Settings", "presence_lapse_seconds", previous)

	def at(self, instant) -> None:
		super().at(instant)
		frappe.flags.kt_evl_clock = str(instant)
		self.addCleanup(setattr, frappe.flags, "kt_evl_clock", None)

	def completed_opening(self) -> dict[str, Any]:
		"""The ordinary opening, completed with every member's proof (already
		done by a shared "completed" world)."""
		if not (self._built() and self.world == "completed"):
			self.completed()
		from kentender_procurement.bid_opening.services import evaluation_seam

		completion = evaluation_seam.completion(self.name)
		self.assertIsNotNone(completion)
		return completion

	def prepared(self) -> None:
		"""The opening prepared, its committee appointed and arrangements
		published (already true in a shared "completed" or "empty" world)."""
		if self._built() and self.world in ("completed", "empty"):
			return
		super().prepared()

	def completed_empty_opening(self) -> None:
		"""A convened opening with no bids, completed with every member's proof
		(already done by a shared "empty" world)."""
		if self._built() and self.world == "empty":
			return
		self._run_empty_opening()

	def _run_empty_opening(self) -> None:
		from kentender_procurement.bid_opening.services import finish
		from kentender_procurement.bid_submission.tests.support import key

		self.ready_to_open()
		self.at(self.minutes_after(12 / 60))
		self.begin()
		self.at(self.minutes_after(1))
		finish.end_with_no_bids(tender=self.name, expected_version=self.case_version(), idempotency_key=key(), user=OPENING_CHAIR)
		self.freeze()
		self.sign_all()


	def reviewing(self) -> str:
		"""The ordinary preparation: appointed, secretary assigned, every member
		declared, the opening completed and taken up. Returns the case name."""
		from kentender_procurement.bid_evaluation.services import appointment, declaration, intake, preparation, secretary
		from kentender_procurement.bid_submission.tests.support import key

		case = preparation.ensure_preparation(tender=self.name)["evaluation"]
		version = lambda: int(frappe.db.get_value("Evaluation Case", case, "record_version"))  # noqa: E731
		appointment.appoint_committee(tender=self.name, members=ROSTER, appointment_reference="MOH/EVAL/TEST/2101", expected_version=version(),
			idempotency_key=key(), user=AO)
		secretary.assign_secretary(tender=self.name, secretary=SECRETARY, appointment_reference="MOH/EVAL/SEC/TEST", expected_version=version(),
			idempotency_key=key(), user=HOP)
		for user in (CHAIR, MEMBER, MEMBER_2):
			declaration.declare_interest(tender=self.name, choice="No conflict to declare", confidentiality_accepted=True, idempotency_key=key(), user=user)
		self.completed_opening()
		out = intake.receive_opening_package(tender=self.name)
		self.assertTrue(out["received"], out)
		return case

	def requirement(self, case: str, label: str) -> dict[str, Any]:
		from kentender_procurement.bid_evaluation.services import aggregate, checks

		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "name")
		res = aggregate.bid_results(case, checks.current_run(case), bid)
		return {**next(r for r in res["requirements"] if r["label"] == label), "bid": bid, "responsiveness": res["responsiveness"]}

	def resolve_all(self, case: str, *, user: str = MEMBER, skip: tuple[str, ...] = ()) -> int:
		"""Record a member's Meets finding on every requirement still Needs review
		(the ordinary evidence checks of §9.12), except the labels in `skip`."""
		from kentender_procurement.bid_evaluation.services import aggregate, checks, findings
		from kentender_procurement.bid_submission.tests.support import key

		bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": case}, "name")
		count = 0
		for r in aggregate.bid_results(case, checks.current_run(case), bid)["requirements"]:
			if r["result"] == "Needs review" and r["label"] not in skip:
				findings.record_evidence_finding(tender=self.name, bid=bid, requirement_key=r["requirement_key"], result="Meets",
					reason="Required evidence reviewed.", evidence_reference="Submitted evidence", idempotency_key=key(), user=user)
				count += 1
		return count

	def session(self, members=None) -> None:
		"""The chair starts a discussion and every other member joins."""
		from kentender_procurement.bid_evaluation.services import discussion
		from kentender_procurement.bid_submission.tests.support import key

		discussion.start_discussion(tender=self.name, subject="Committee discussion", idempotency_key=key(), user=CHAIR)
		for user in members or (MEMBER, MEMBER_2):
			discussion.join_discussion(tender=self.name, idempotency_key=key(), user=user)

	def end_session(self) -> None:
		from kentender_procurement.bid_evaluation.services import discussion
		from kentender_procurement.bid_submission.tests.support import key

		discussion.end_discussion(tender=self.name, idempotency_key=key(), user=CHAIR)
