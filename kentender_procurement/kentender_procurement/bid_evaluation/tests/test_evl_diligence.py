# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Due diligence (EVL-CHG-001 v0.4 §5.4, §7.2, §7.3 rows 10–12; tracker
EVL4-801…805; acceptance EVL-A08 (service parts); boards D08-VERIFY-PLAN,
D08-DD, D08-DD-FREEZE, D08-DD-SIGN, D08-VERIFY-OUTCOME, D08-VERIFY-NEG).

The plan is a committee decision taken in session with the whole current
eligible roster present; its participants and lead come from that roster.
Each participant records their own observations; only the lead sends the
report for signing, and only once every participant has recorded; each
participant signs their own page and signature targets; the report counts as
signed only when every proof is in. The outcome is a committee conclusion
and a negative result never silently substitutes another bidder."""

from __future__ import annotations

import frappe

from kentender_procurement.bid_evaluation.services import diligence, my_work_provider
from kentender_procurement.bid_evaluation.services.errors import EvaluationError, InputError
from kentender_procurement.bid_evaluation.tests.support import CHAIR, MEMBER, MEMBER_2, SECRETARY, EvaluationCase
from kentender_procurement.bid_submission.tests.support import key

OBS = "Both customers confirmed the submitted contract details."


def titles(user: str) -> list[str]:
	return [r["title"] for r in my_work_provider.my_work_rows(user)["assigned"] if r["module"] == "Bid Evaluation"]


class DiligenceCase(EvaluationCase):
	def setUp(self):
		super().setUp()
		self.case = self.reviewing()
		self.resolve_all(self.case)
		self.bid = frappe.db.get_value("Evaluation Bid", {"evaluation_case": self.case}, "name")

	def plan(self, participants=(CHAIR, MEMBER_2), lead=CHAIR, **kw):
		return diligence.record_plan(tender=self.name, scope=kw.pop("scope", "Verify the two submitted comparable contracts"),
			basis=kw.pop("basis", "Due diligence; verify the two submitted comparable contracts"), participants_=list(participants), lead=lead,
			idempotency_key=key(), user=kw.pop("user", CHAIR), **kw)

	def observe(self, user):
		return diligence.record_observation(tender=self.name, findings_=OBS, idempotency_key=key(), user=user)

	def refused(self, fn, *args, **kwargs):
		with self.assertRaises((EvaluationError, InputError)) as ctx:
			fn(*args, **kwargs)
		return ctx.exception


class TestPlan(DiligenceCase):
	def test_a_plan_needs_the_committee_in_session_and_eligible_participants(self):
		self.assertEqual(self.refused(self.plan).code, "EVL_MEMBERS_ABSENT")  # no session: the committee is not present
		self.session()
		with self.assertRaises(frappe.DoesNotExistError):
			self.plan(user=MEMBER)  # only the chair records the plan
		error = self.refused(self.plan, participants=(CHAIR, SECRETARY), lead=MEMBER)
		self.assertEqual(set(error.fields), {"participants", "lead"})
		out = self.plan()
		self.assertTrue(out["ok"])
		for user in (CHAIR, MEMBER_2):
			self.assertIn(f"Record verification findings for {self.reference}", titles(user))
		self.assertNotIn(f"Record verification findings for {self.reference}", titles(MEMBER))
		# a revision needs its reason and supersedes the earlier plan
		self.assertIn("change_reason", self.refused(self.plan, participants=(CHAIR,)).fields)
		self.plan(participants=(CHAIR,), change_reason="One participant is enough to call both customers.")
		self.assertEqual(frappe.db.get_value("Evaluation Verification Plan", out["plan"], "status"), "Superseded")


class TestReport(DiligenceCase):
	def setUp(self):
		super().setUp()
		self.session()
		self.plan()
		self.end_session()

	def test_observe_freeze_sign_and_conclude(self):
		from kentender_procurement.bid_evaluation.services import conclusion

		with self.assertRaises(frappe.DoesNotExistError):
			self.observe(MEMBER)  # not a participant
		self.observe(MEMBER_2)
		error = self.refused(diligence.send_for_signing, tender=self.name, idempotency_key=key(), user=CHAIR)
		self.assertEqual((error.code, [m["user"] for m in error.detail["missing_observations"]]), ("EVL_REPORT_INCOMPLETE", [CHAIR]))
		self.observe(CHAIR)
		with self.assertRaises(frappe.DoesNotExistError):
			diligence.send_for_signing(tender=self.name, idempotency_key=key(), user=MEMBER_2)  # only the lead
		self.assertTrue(diligence.send_for_signing(tender=self.name, idempotency_key=key(), user=CHAIR)["ok"])
		self.assertEqual(self.refused(self.observe, MEMBER_2).code, "EVL_VERSION_CONFLICT")  # frozen
		plan = diligence.current_plan(self.case)
		doc = frappe.get_doc("Evaluation Case", self.case)
		kinds = {t["target_type"] for t in diligence.my_targets(doc, plan, MEMBER_2)}
		self.assertEqual(kinds, {"Verification report page", "Verification report signature"})
		self.assertEqual(diligence.sign(tender=self.name, idempotency_key=key(), user=CHAIR)["report_state"], "Frozen")  # one signer is not enough
		self.assertEqual(diligence.sign(tender=self.name, idempotency_key=key(), user=MEMBER_2)["report_state"], "Signed")
		self.assertIn(f"Review verification outcome for {self.reference}", [r["subject"] for r in frappe.get_all("Notification Log",
			filters={"for_user": CHAIR}, fields=["subject"])])
		# the outcome is a committee conclusion, in session
		self.session()
		requirement = self.requirement(self.case, "Comparable experience")["requirement_key"]
		self.assertIn("result", self.refused(diligence.record_outcome, tender=self.name, bid=self.bid, requirement_key=requirement, result="Needs review",
			reason="x", idempotency_key=key(), user=CHAIR).fields)
		out = diligence.record_outcome(tender=self.name, bid=self.bid, requirement_key=requirement, result="Does not meet",
			reason="One customer could not confirm the submitted contract.", idempotency_key=key(), user=CHAIR)
		self.assertIsNone(out["next_ranked"])  # one bid: nobody is substituted
		self.assertEqual(frappe.db.get_value("Evaluation Conclusion", out["conclusion"], ["kind", "result"]), ("Verification outcome", "Does not meet"))
		self.assertEqual(self.requirement(self.case, "Comparable experience")["result"], "Does not meet")
		self.assertEqual(frappe.db.get_value("Evaluation Verification Plan", plan.name, "status"), "Completed")
		del conclusion
