"""KT-STD-001 v1.8 §3B — the shared next-step contract.

Run:
  bench --site kentender.midas.com run-tests --app kentender_core \\
    --module kentender_core.tests.test_next_step
"""

from __future__ import annotations

from frappe.tests import IntegrationTestCase

from kentender_core.services import next_step as ns

OVER = ns.guard(
	False,
	reason_code="PLN_PLAN_NOT_AFFORDABLE",
	message="The planned amount exceeds the approved budget on the lines shown.",
	headline="Over budget by KES 2,000,000 on Digital health workforce development",
	figures={"line": "MOH-BL-HWD-2027", "approved": 60000000, "planned": 62000000, "over": 2000000},
	fixes=[
		ns.fix("Request budget revision from Josphat Mwangi", responsibility="Budget Officer", kind=ns.FIX_COMMAND, fix_id="request_budget_revision", person="Josphat Mwangi", primary=True),
		ns.fix("Reduce a purchase", responsibility="Procurement Planner", kind=ns.FIX_FOCUS, fix_id="reduce_purchase", target="purchases"),
	],
)
METHOD = ns.guard(
	False,
	reason_code="PLN_PLAN_CONTENTS_INCOMPLETE",
	headline="1 purchase needs a procurement method",
	fixes=[ns.fix("Choose a procurement method", responsibility="Procurement Planner", kind=ns.FIX_ROUTE, target=["procurement-plan-item", "PPI-1"])],
)


class TestGuards(IntegrationTestCase):
	def test_a_refusal_cannot_be_built_without_a_reason_code(self):
		with self.assertRaises(ValueError):
			ns.guard(False)

	def test_combine_returns_every_refusal_together(self):
		combined = ns.combine(ns.allowed(), OVER, METHOD)
		self.assertFalse(combined["allowed"])
		self.assertEqual(combined["reason_code"], "PLN_PLAN_NOT_AFFORDABLE")
		self.assertEqual([b["reason_code"] for b in ns.blockers_of(combined)], ["PLN_PLAN_NOT_AFFORDABLE", "PLN_PLAN_CONTENTS_INCOMPLETE"])

	def test_combine_of_passing_guards_is_allowed_with_no_blockers(self):
		combined = ns.combine(ns.allowed(), ns.allowed())
		self.assertTrue(combined["allowed"])
		self.assertEqual(ns.blockers_of(combined), [])

	def test_unknown_fix_kind_is_refused(self):
		with self.assertRaises(ValueError):
			ns.fix("x", responsibility="r", kind="teleport")


class TestAnswer(IntegrationTestCase):
	def test_precedence_is_turn_then_blocked_then_waiting_then_done_then_not_involved(self):
		waiting = ns.answer(ns.KIND_WAITING, headline="Waiting for Finance", holder=ns.holder("Finance Confirmation Officer", ["Josphat Mwangi"]))
		done = ns.answer(ns.KIND_DONE, headline="Accepted")
		blocked = ns.answer(ns.KIND_BLOCKED, headline="Over budget", blockers=[ns.blocker(OVER)])
		turn = ns.answer(ns.KIND_YOUR_TURN, headline="Sign and submit")
		self.assertIs(ns.choose(done, waiting, None), waiting)
		self.assertIs(ns.choose(waiting, blocked, done), blocked)
		self.assertIs(ns.choose(blocked, turn), turn)
		self.assertEqual(ns.choose()["kind"], ns.KIND_NOT_INVOLVED)

	def test_blocked_answer_carries_fixes_from_its_blockers(self):
		result = ns.answer(ns.KIND_BLOCKED, headline="2 things stop this plan going to Finance", blockers=ns.blockers_of(ns.combine(OVER, METHOD)))
		self.assertEqual([f["fix_id"] for f in result["fixes"]], ["request_budget_revision", "reduce_purchase", "Choose a procurement method"])
		self.assertEqual(result["label"], "Your turn, blocked")

	def test_holder_display_names_people_then_role_or_role_alone(self):
		self.assertEqual(ns.holder("Budget Officer", ["Josphat Mwangi"])["display"], "Josphat Mwangi (Budget Officer)")
		self.assertEqual(ns.holder("Procurement Planner")["display"], "Procurement Planner")

	def test_since_is_none_without_a_recorded_instant(self):
		self.assertIsNone(ns.since(None, "x"))
		self.assertEqual(ns.since("2026-12-15 10:00:00", "15 Dec 2026, 10:00 EAT")["display"], "15 Dec 2026, 10:00 EAT")


class TestTechnicalReader(IntegrationTestCase):
	"""§3B.6 — Administrator and System Manager read everything, decide nothing."""

	def setUp(self):
		self.turn = ns.answer(ns.KIND_BLOCKED, headline="Over budget", stage="preparation", blockers=[ns.blocker(OVER)], primary_action="request_budget_revision")
		self.reader = ns.answer(ns.KIND_WAITING, headline="Plan being prepared by Mercy Kilonzo", stage="preparation", holder=ns.holder("Procurement Planner", ["Mercy Kilonzo"]))

	def test_a_turn_becomes_the_reader_answer_with_no_fix(self):
		result = ns.for_viewer(self.turn, technical=True, reader=self.reader)
		self.assertEqual(result["kind"], ns.KIND_WAITING)
		self.assertEqual(result["fixes"], [])
		self.assertEqual(result["primary_action"], "")

	def test_a_non_technical_viewer_keeps_the_turn(self):
		self.assertIs(ns.for_viewer(self.turn, technical=False, reader=self.reader), self.turn)

	def test_a_named_exception_keeps_the_turn_for_a_technical_operator(self):
		result = ns.for_viewer(self.turn, technical=True, reader=self.reader, allow_technical_turn=True)
		self.assertEqual(result["kind"], ns.KIND_BLOCKED)

	def test_a_turn_fallback_is_refused(self):
		with self.assertRaises(ValueError):
			ns.for_viewer(self.turn, technical=True, reader=self.turn)


class TestDeadEndProblems(IntegrationTestCase):
	def test_waiting_must_name_a_holder(self):
		self.assertIn("waiting without a named holder", ns.problems(ns.answer(ns.KIND_WAITING, headline="Waiting")))

	def test_blocked_must_have_a_blocker_with_a_fix(self):
		bare = ns.guard(False, reason_code="PLN_X", headline="Blocked")
		self.assertIn("blocker PLN_X offers no fix", ns.problems(ns.answer(ns.KIND_BLOCKED, headline="Blocked", blockers=[ns.blocker(bare)])))
		self.assertEqual(ns.problems(ns.answer(ns.KIND_BLOCKED, headline="Over", blockers=[ns.blocker(OVER)])), [])

	def test_your_turn_must_offer_a_way_to_act(self):
		bare = ns.answer(ns.KIND_YOUR_TURN, headline="Revise the line")
		self.assertIn("your turn without an action or a way to act", ns.problems(bare))
		self.assertEqual(ns.problems(bare, has_enabled_action=True), [])
		self.assertEqual(ns.problems(ns.answer(ns.KIND_YOUR_TURN, headline="Sign", primary_action="sign_and_submit")), [])
		link = ns.fix("Open the request", responsibility="Budget Officer", kind=ns.FIX_ROUTE, target=["budget-funding"])
		self.assertEqual(ns.problems(ns.answer(ns.KIND_YOUR_TURN, headline="Revise the line", fixes=[link])), [])

	def test_no_answer_is_a_dead_end_unless_an_action_is_enabled(self):
		self.assertEqual(ns.problems(None), ["no next-step answer"])
		self.assertEqual(ns.problems(None, has_enabled_action=True), [])


STAGES = [("preparation", "Preparation"), ("funding", "Funding confirmation"), ("signature", "Signature"), ("ao", "AO adoption"), ("statutory", "Cabinet Secretary approval"), ("publication", "Publication"), ("in_force", "In force")]


class TestJourney(IntegrationTestCase):
	def test_markers_follow_the_current_stage(self):
		j = ns.journey(STAGES, current="signature", holder_display="Charles Mutiso")
		self.assertEqual([s["marker"] for s in j["stages"]], ["done", "done", "current", "not_started", "not_started", "not_started", "not_started"])
		self.assertEqual([s["holder"] for s in j["stages"] if s["holder"]], ["Charles Mutiso"])
		self.assertEqual(j["reduced_text"], "Stage 3 of 7: Signature — Charles Mutiso")

	def test_a_blocked_current_stage_is_marked_blocked(self):
		j = ns.journey(STAGES, current="preparation", blocked=True, holder_display="Mercy Kilonzo")
		self.assertEqual(j["stages"][0]["marker"], "blocked")
		self.assertEqual(j["stages"][0]["marker_label"], "Blocked")

	def test_complete_marks_every_stage_done_and_names_no_holder(self):
		j = ns.journey(STAGES, complete=True, reduced=True)
		self.assertTrue(all(s["marker"] == "done" for s in j["stages"]))
		self.assertEqual(j["reduced_text"], "Stage 7 of 7: In force")

	def test_an_unknown_stage_is_refused(self):
		with self.assertRaises(ValueError):
			ns.journey(STAGES, current="nope")

	def test_a_tracker_link_never_mutates(self):
		with self.assertRaises(ValueError):
			ns.link("3 departmental requirements included", kind=ns.FIX_COMMAND)
