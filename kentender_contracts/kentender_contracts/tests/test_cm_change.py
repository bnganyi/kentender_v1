# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 sections 5.7, 5.11, 5.14, 7, 19.3 (CM-R-10, CM-R-11) and boards D27, D14, D34 (plan Phase 8; tracker CM8-802): changes and amendments.

The original contract stays operative while a request is pending; only the effective successor changes the terms. A quantity request is measured against the **original** quantity and the issued rate,
so a ceiling cannot be walked around in small steps and no officer edits a rate or a percentage. The reviewers are named by appointment reference, declare no conflict and sign; the Accounting Officer who
decides is never one who requested, reviewed or recommended. Approval generates an amendment the supplier signs first and the entity second; the second proof makes it effective, and the native order and the
funding owner follow as durable operations that can fail and be restored without a new signature."""

from __future__ import annotations

from kentender_contracts.simulation.timeline import D  # noqa: F401
from unittest import mock

import frappe

from kentender_contracts.rules import profile as profiles
from kentender_contracts.services import change, errors, formation, holds, position, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase


def refusal(fn, *args, **kwargs):
	try:
		fn(*args, **kwargs)
	except (errors.ContractError, errors.InputError) as exc:
		return exc
	raise AssertionError("expected a refusal")


EVIDENCE = [{"label": "Supplier request 1", "file": "/private/files/request-1.pdf"}]


class ChangeCase(ContractCase):
	native = True

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: (setattr(frappe.flags, "kt_cm_funding_fault", None), self.env.__exit__(None, None, None)))
		self.p = self.people
		self.t = tw.Thread(self.p, tag=self.id().rsplit(".", 1)[-1][:24])
		self.case = self.t.active()
		frappe.db.set_value("Contract Case", self.case, "responsible_user", self.p["julia"])

	# -- steps ---------------------------------------------------------------------------------------------------------------------
	def ask(self, kind="Extension", who="julia", request=None, **kw):
		request = request if request is not None else ({"proposed_date": D("2027-07-27")} if kind == "Extension" else {"quantities": {"L1": 11}})
		return change.request_change(self.case, kind=kind, request=request, reason=kw.pop("reason", "Supplier reports a seven-day shipment delay."), evidence=kw.pop("evidence", EVIDENCE),
			expected_version=self.t.version(), idempotency_key=self.t.key("ask"), actor=self.p[who], **kw)

	def roster(self, kind="Extension"):
		return dict(zip(change.REVIEW_KINDS[kind], (self.p["peter"], self.p["faith"], self.p["brian"]), strict=True))

	def appoint(self, number=1, kind="Extension", who="charles", roster=None):
		return change.appoint_reviewers(self.case, change=number, reference="AO/VAR/2027/001", reviewers=roster or self.roster(kind), expected_version=self.t.version(), idempotency_key=self.t.key("appoint"), actor=self.p[who])

	def review(self, kind, number=1, text="Approve the change without a price change.", reference="", declaration=change.NO_CONFLICT):
		reviewer = next(s["reviewer"] for s in change.slots(change.get(self.case, number)) if s["kind"] == kind)
		change.record_review(self.case, change=number, kind=kind, recommendation=text, declaration=declaration, reference=reference, expected_version=self.t.version(), idempotency_key=self.t.key("rec"), actor=reviewer)
		return change.sign_review(self.case, change=number, kind=kind, expected_version=self.t.version(), idempotency_key=self.t.key("sig"), actor=reviewer)

	def reviewed(self, kind="Extension", number=1):
		for review in change.REVIEW_KINDS[kind]:
			self.review(review, number, reference="QTY-01" if review == "Funding confirmation" else "")

	def submit(self, number=1, who="charles"):
		return change.submit_for_decision(self.case, change=number, expected_version=self.t.version(), idempotency_key=self.t.key("submit"), actor=self.p[who])

	def decide(self, decision="Approve", number=1, who="amina", reason="The documented grounds support the change."):
		return change.decide(self.case, change=number, decision=decision, reason=reason, expected_version=self.t.version(), idempotency_key=self.t.key("decide"), actor=self.p[who])

	def sign(self, party, number=1):
		return change.sign_amendment(self.case, change=number, party=party, expected_version=self.t.version(), idempotency_key=self.t.key(f"sign-{party}"), actor=self.p["mary" if party == "Supplier" else "amina"])

	def approved(self, kind="Extension", **kw):
		self.ask(kind, **kw)
		self.appoint(kind=kind)
		self.reviewed(kind)
		self.submit()
		self.decide()

	def effective(self, kind="Extension", **kw):
		self.approved(kind, **kw)
		self.sign("Supplier")
		return self.sign("Entity")

	def row(self, number=1):
		return change.get(self.case, number)

	def tasks(self, who):
		return {(x["command"].split(":")[0], x["title"], x["state"]) for x in work.live(self.case) if x["holder"] == self.p[who]}

	def operative(self):
		return change.operative_terms(self.case)

	def order(self):
		return formation.native_order(self.case)


class TestRequest(ChangeCase):
	def test_an_extension_is_recorded_against_the_terms_in_force_and_changes_nothing(self):
		out = self.ask()
		row = self.row()
		self.assertEqual((row.kind, row.state, row.requested_by), ("Extension", "Requested", self.p["julia"]))
		self.assertEqual((records.loads(row.baseline_json)["due"], change.proposal(row)["proposed_date"]), (D("2027-07-20"), D("2027-07-27")))
		self.assertEqual(self.operative()["delivery"]["due"], D("2027-07-20"))  # a pending request moves no date
		self.assertEqual(out["change_no"], 1)
		self.assertIn(("AppointContractChangeReviewers", "Name the reviewers for the requested change.", "actionable"), self.tasks("charles"))

	def test_the_supplier_or_the_owner_may_ask_and_a_stranger_may_not(self):
		self.ask(who="david")
		self.assertEqual(self.row().requested_by, self.p["david"])
		self.assertEqual(refusal(change.request_change, self.case, kind="Extension", request={"proposed_date": D("2027-07-27")}, reason="x", evidence=EVIDENCE, expected_version=self.t.version(), idempotency_key=self.t.key("s"),
			actor=self.p["stranger"]).code, "CM_AUTHORITY")

	def test_a_request_without_grounds_a_later_date_or_a_request_file_is_corrected_not_recorded(self):
		self.assertIn("reason", refusal(self.ask, reason=" ").fields)
		self.assertIn("evidence", refusal(self.ask, evidence=[]).fields)
		self.assertIn("proposed_date", refusal(self.ask, request={"proposed_date": D("2027-07-20")}).fields)  # not after the current date
		self.assertIn("proposed_date", refusal(self.ask, request={"proposed_date": "soon"}).fields)
		self.assertIn("kind", refusal(self.ask, kind="Price").fields)
		self.assertFalse(frappe.db.count("Contract Change", {"contract_case": self.case}))

	def test_one_change_is_decided_before_another_is_asked(self):
		self.ask()
		self.assertEqual(refusal(self.ask, request={"proposed_date": D("2027-08-03")}).code, "CM_CHANGED")

	def test_a_quantity_increase_is_calculated_at_the_issued_rate_and_nobody_edits_the_rate(self):
		self.ask("Quantity")
		note = records.loads(self.row().rule_json)
		self.assertEqual((note["current_total"], note["proposed_total"], note["delta"]), (1_000_000, 1_100_000, 100_000))
		self.assertEqual(note["lines"][0]["percent_of_original"], 10.0)
		self.assertEqual(change.proposal(self.row())["funding"], [{"reservation": "RSV-DEMO-1", "additional": 100000.0}])
		self.assertIn("rate", refusal(change.request_change, self.case, kind="Quantity", request={"quantities": {"L1": 11}, "rate": 90_000}, reason="x", evidence=EVIDENCE, expected_version=self.t.version(),
			idempotency_key=self.t.key("r"), actor=self.p["julia"]).fields)

	def test_a_quantity_above_the_ceiling_is_a_named_limit_not_a_field_to_retype(self):
		out = refusal(self.ask, "Quantity", request={"quantities": {"L1": 12}})
		self.assertEqual(out.code, "CM_HOLD")
		self.assertEqual(out.detail["hold"], "CHANGE_LIMIT_EXCEEDED")
		self.assertIn("20% above the original 10", out.detail["reason"])
		self.assertIn("15%", out.detail["reason"])
		self.assertFalse(frappe.db.count("Contract Change", {"contract_case": self.case}))

	def test_a_quantity_that_is_not_an_increase_of_a_goods_line_is_corrected(self):
		self.assertIn("quantity.L1", refusal(self.ask, "Quantity", request={"quantities": {"L1": 10}}).fields)
		self.assertIn("quantity.L1", refusal(self.ask, "Quantity", request={"quantities": {"L1": 9}}).fields)
		self.assertIn("quantity.L9", refusal(self.ask, "Quantity", request={"quantities": {"L9": 11}}).fields)
		self.assertIn("quantities", refusal(self.ask, "Quantity", request={"quantities": {}}).fields)

	def test_a_replayed_request_is_one_request(self):
		key = self.t.key("once")
		args = dict(kind="Extension", request={"proposed_date": D("2027-07-27")}, reason="Delay.", evidence=EVIDENCE, expected_version=self.t.version(), idempotency_key=key, actor=self.p["julia"])
		first = change.request_change(self.case, **args)
		self.assertEqual(change.request_change(self.case, **args), first)
		self.assertEqual(frappe.db.count("Contract Change", {"contract_case": self.case}), 1)


class TestReviewers(ChangeCase):
	def test_a_named_reviewer_reads_the_contract_while_the_change_is_open_and_nobody_else_does(self):
		"""Faith holds the inspection and technical responsibilities but is not an inspector of this contract: she reads it only because she is named to review its change, and only while that change is open."""
		from kentender_contracts.services import audience

		keys = lambda who: [g.audience for g in audience.readable(self.p[who], self.case)]
		self.assertEqual(keys("faith"), [])
		self.ask()
		self.assertEqual(keys("faith"), [])  # requested, nobody named yet
		self.appoint()
		self.assertEqual(keys("faith"), ["appointee"])
		self.assertEqual(audience.readable(self.p["faith"], self.case)[0].evidence["capacity"], "change reviewer")
		self.assertNotIn("deliberation", audience.field_sets(audience.readable(self.p["faith"], self.case)), "the appointee's projection: no deliberation, money or banking")
		self.assertEqual(keys("stranger"), [], "a person who is not named reads nothing more")
		frappe.db.set_value("Contract Change", self.row().name, "state", "Declined")
		self.assertEqual(keys("faith"), [], "the access ends with the change")

	def test_the_form_s_declaration_index_means_what_the_service_asks_for(self):
		"""A radio group sends the index of the chosen option; the command table says what that is, so a reviewer who picks "No conflict" is not asked to declare again."""
		from kentender_contracts.api import commands

		self.assertEqual([commands._declaration(v) for v in ("0", 0, "1", 1, None, "")], [change.NO_CONFLICT, change.NO_CONFLICT, "Conflict", "Conflict", "", ""])
		self.assertEqual(commands._declaration(change.NO_CONFLICT), change.NO_CONFLICT)

	def test_the_head_of_procurement_names_the_reviewers_by_appointment_reference(self):
		self.ask()
		self.appoint()
		found = {s["kind"]: s for s in change.slots(self.row())}
		self.assertEqual(sorted(found), sorted(change.REVIEW_KINDS["Extension"]))
		self.assertEqual({s["state"] for s in found.values()}, {"Appointed"})
		self.assertEqual(change.proposal(self.row())["appointment"]["reference"], "AO/VAR/2027/001")
		self.assertIn(("RecordContractChangeReview", "Record your technical review of the requested change.", "actionable"), self.tasks("peter"))
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "AppointContractChangeReviewers"})

	def test_only_the_head_of_procurement_or_a_preparer_names_them_and_never_the_requester(self):
		self.ask()
		self.assertEqual(refusal(self.appoint, who="stranger").code, "CM_AUTHORITY")
		self.assertIn("reference", refusal(change.appoint_reviewers, self.case, change=1, reference=" ", reviewers=self.roster(), expected_version=self.t.version(), idempotency_key=self.t.key("a"), actor=self.p["charles"]).fields)
		roster = {**self.roster(), "Legal review": self.p["julia"]}  # julia requested it
		self.assertIn("reviewers.Legal review", refusal(self.appoint, roster=roster).fields)
		self.assertIn("reviewers.Legal review", refusal(self.appoint, roster={**self.roster(), "Legal review": "nobody@nowhere.test"}).fields)
		self.assertIn("reviewers.Legal review", refusal(self.appoint, roster={**self.roster(), "Legal review": self.p["naomi"]}).fields)  # an auditor holds no contract responsibility
		self.assertIn("reviewers.Legal review", refusal(self.appoint, roster={**self.roster(), "Legal review": self.p["amina"]}).fields)  # the Accounting Officer decides and is not offered as a reviewer

	def test_only_the_appointed_reviewer_records_and_a_conflict_asks_for_another(self):
		self.ask()
		self.appoint()
		self.assertEqual(refusal(change.record_review, self.case, change=1, kind="Technical review", recommendation="Fine", declaration=change.NO_CONFLICT, expected_version=self.t.version(), idempotency_key=self.t.key("x"),
			actor=self.p["faith"]).code, "CM_AUTHORITY")
		self.assertIn("recommendation", refusal(change.record_review, self.case, change=1, kind="Technical review", recommendation=" ", declaration=change.NO_CONFLICT, expected_version=self.t.version(),
			idempotency_key=self.t.key("y"), actor=self.p["peter"]).fields)
		change.record_review(self.case, change=1, kind="Legal review", recommendation="I act for the supplier.", declaration="Conflict", expected_version=self.t.version(), idempotency_key=self.t.key("c"), actor=self.p["brian"])
		self.assertEqual(next(s["state"] for s in change.slots(self.row()) if s["kind"] == "Legal review"), "Conflicted")
		self.assertIn(("AppointContractChangeReviewers", "Name another reviewer for the legal review.", "actionable"), self.tasks("charles"))
		self.assertIn("reviewers.Legal review", refusal(self.appoint, roster={"Legal review": self.p["julia"]}).fields)  # still not the requester
		self.appoint(roster={"Legal review": self.p["faith"]})
		now = {s["kind"]: (s["reviewer"], s["state"]) for s in change.slots(self.row())}
		self.assertEqual(now["Legal review"], (self.p["faith"], "Appointed"))
		self.assertEqual(now["Technical review"], (self.p["peter"], "Appointed"))  # the others stand

	def test_a_recommendation_is_signed_before_it_counts_and_every_part_makes_the_change_reviewed(self):
		self.ask()
		self.appoint()
		self.assertEqual(refusal(change.sign_review, self.case, change=1, kind="Technical review", expected_version=self.t.version(), idempotency_key=self.t.key("s"), actor=self.p["peter"]).code, "CM_CHANGED")
		self.review("Technical review")
		self.review("Committee recommendation")
		self.assertEqual(self.row().state, "Requested")
		self.assertFalse({t for t in self.tasks("charles") if t[0] == "SubmitContractChangeForDecision"})
		self.review("Legal review")
		self.assertEqual(self.row().state, "Reviewed")
		self.assertTrue(all(s["proof"] for s in change.slots(self.row())))
		self.assertIn(("SubmitContractChangeForDecision", "Submit the supported request for decision.", "actionable"), self.tasks("charles"))

	def test_a_quantity_change_needs_the_funding_confirmation_with_its_reference(self):
		self.ask("Quantity")
		self.appoint(kind="Quantity")
		self.assertIn("reference", refusal(change.record_review, self.case, change=1, kind="Funding confirmation", recommendation="Funding is available.", declaration=change.NO_CONFLICT, expected_version=self.t.version(),
			idempotency_key=self.t.key("f"), actor=self.p["brian"]).fields)
		self.reviewed("Quantity")
		self.assertEqual(self.row().state, "Reviewed")
		self.assertEqual(next(s["reference"] for s in change.slots(self.row()) if s["kind"] == "Funding confirmation"), "QTY-01")


class TestDecision(ChangeCase):
	def test_submission_needs_every_review_and_a_verified_rule_profile(self):
		self.ask()
		self.appoint()
		self.assertEqual(refusal(self.submit).code, "CM_CHANGED")  # not reviewed yet
		self.reviewed()
		self.assertEqual(refusal(self.submit, who="stranger").code, "CM_AUTHORITY")
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "KE-PPADA-2015")  # the production profile is Draft until the legal owner verifies it
		out = refusal(self.submit)
		self.assertEqual((out.code, out.reasons[0]["detail"]["rule"]), ("CM_RULE", "CM-R-10"))
		frappe.db.set_value("Contract Case", self.case, "legal_profile", "SYNTHETIC-ILLUSTRATIVE")
		self.submit()
		self.assertEqual(self.row().state, "Submitted")
		self.assertIn(("DecideContractChange", "Decide the requested delivery date.", "actionable"), self.tasks("amina"))

	def test_an_early_total_increase_is_held_for_the_legal_question_unless_the_profile_answers_it(self):
		verified = profiles.Profile("VERIFIED-NO-ANSWER", "A verified profile that has not answered LQ-02", profiles.VERIFIED, False, profiles.STATUTORY)
		with mock.patch.dict(profiles.PROFILES, {verified.id: verified}):
			frappe.db.set_value("Contract Case", self.case, "legal_profile", verified.id)
			self.ask("Quantity")
			self.appoint(kind="Quantity")
			self.reviewed("Quantity")
			out = refusal(self.submit)
			self.assertEqual((out.code, out.reasons[0]["detail"]["question"], out.reasons[0]["detail"]["branch"]), ("CM_HOLD", "LQ-02", "early_total_increase"))
			self.assertEqual(self.row().state, "Reviewed")

	def test_an_extension_has_no_total_increase_to_hold(self):
		verified = profiles.Profile("VERIFIED-NO-ANSWER", "A verified profile that has not answered LQ-02", profiles.VERIFIED, False, profiles.STATUTORY)
		with mock.patch.dict(profiles.PROFILES, {verified.id: verified}):
			frappe.db.set_value("Contract Case", self.case, "legal_profile", verified.id)
			self.ask()
			self.appoint()
			self.reviewed()
			self.submit()
			self.assertEqual(self.row().state, "Submitted")

	def test_only_the_accounting_officer_decides_and_never_one_who_reviewed_or_requested(self):
		self.ask()
		self.appoint()
		self.reviewed()
		self.submit()
		found = records.loads(self.row().reviews_json)  # the Accounting Officer cannot be named a reviewer (they are not offered), so the record is made to say they were: the separation reads the actual history
		found[2]["reviewer"] = self.p["amina"]
		frappe.db.set_value("Contract Change", self.row().name, "reviews_json", records.dumps(found))
		self.assertEqual(refusal(self.decide, who="charles").code, "CM_AUTHORITY")
		self.assertEqual(refusal(self.decide).code, "CM_SEGREGATION")
		self.assertEqual(self.row().state, "Submitted")

	def test_a_decision_needs_a_reason_and_a_decline_changes_nothing(self):
		self.ask()
		self.appoint()
		self.reviewed()
		self.submit()
		self.assertIn("reason", refusal(self.decide, reason=" ").fields)
		self.decide("Decline", reason="The grounds are not supported.")
		self.assertEqual((self.row().state, records.loads(self.row().decision_json)["reason"]), ("Declined", "The grounds are not supported."))
		self.assertFalse(self.row().amendment_version)
		self.assertEqual(self.operative()["delivery"]["due"], D("2027-07-20"))
		self.assertFalse(frappe.db.exists("Contract Agreement Version", {"contract_case": self.case, "version_no": 2}))

	def test_a_returned_change_is_corrected_by_the_requester_and_reviewed_again(self):
		self.ask()
		self.appoint()
		self.reviewed()
		self.submit()
		self.decide("Return", reason="State the effect on the warranty.")
		self.assertEqual(self.row().state, "Returned")
		self.assertIn(("RequestContractChange", "Correct the change request.", "actionable"), self.tasks("julia"))
		self.ask(correcting=1, request={"proposed_date": D("2027-07-28")}, reason="Seven additional days; the warranty runs from acceptance.")
		row = self.row()
		self.assertEqual((row.state, change.proposal(row)["proposed_date"], change.draft_of(row), frappe.db.count("Contract Change", {"contract_case": self.case})), ("Requested", D("2027-07-28"), 2, 1))
		self.assertFalse(change.slots(row))  # the earlier reviews no longer stand; new reviewers are named
		self.assertEqual({s["state"] for s in change.slots(row, live=False)}, {"Superseded"})
		self.assertIn(("AppointContractChangeReviewers", "Name the reviewers for the requested change.", "actionable"), self.tasks("charles"))

	def test_approval_generates_an_amendment_and_the_original_stays_operative_until_it_is_effective(self):
		self.approved()
		row = self.row()
		self.assertEqual((row.state, row.amendment_version), ("Approved", 2))
		amendment = change.amendment_of(row)
		self.assertEqual((amendment.version_no, amendment.state, amendment.change), (2, "Awaiting signatures", row.name))
		self.assertEqual(records.loads(amendment.terms_json)["delivery"]["due"], D("2027-07-27"))
		self.assertIn(D("2027-07-20"), amendment.rendered_html)
		self.assertIn(D("2027-07-27"), amendment.rendered_html)
		self.assertEqual(self.operative()["delivery"]["due"], D("2027-07-20"))  # an approved but unsigned amendment changes no date
		self.assertEqual(formation.current_agreement(self.case).version_no, 1)  # the agreement is still agreement 1
		self.assertEqual(sorted(frappe.get_all("Contract Signature", filters={"contract_case": self.case, "agreement_version": 2}, pluck="party")), ["Entity", "Supplier"])
		self.assertIn(("SignContractVersion", "Review and sign amendment 1.", "actionable"), self.tasks("mary"))


class TestEffect(ChangeCase):
	def test_the_supplier_signs_first_the_wrong_person_cannot_and_the_entity_signs_second(self):
		self.approved()
		self.assertEqual(refusal(self.sign, "Entity").code, "CM_CHANGED")  # the supplier signs first
		self.assertEqual(refusal(change.sign_amendment, self.case, change=1, party="Supplier", expected_version=self.t.version(), idempotency_key=self.t.key("w"), actor=self.p["david"]).code, "CM_SEGREGATION")
		self.sign("Supplier")
		self.assertEqual(self.row().state, "Approved")
		self.assertEqual(self.operative()["delivery"]["due"], D("2027-07-20"))  # half-signed: still the original
		self.assertIn(("SignContractVersion", "Review and sign amendment 1.", "actionable"), self.tasks("amina"))
		out = self.sign("Entity")
		self.assertTrue(out["effective"])

	def test_an_effective_extension_moves_the_date_and_the_native_order_keeps_the_history(self):
		self.effective()
		self.assertEqual(self.row().state, "Effective")
		terms = self.operative()
		self.assertEqual((terms["delivery"]["due"], terms["delivery"]["original_due"], terms["delivery"]["extensions"][0]["to"]), (D("2027-07-27"), D("2027-07-20"), D("2027-07-27")))
		self.assertEqual(str(frappe.db.get_value("Purchase Order", self.order(), "schedule_date")), D("2027-07-27"))
		self.assertEqual(frappe.db.get_value("Purchase Order Item", {"parent": self.order()}, "schedule_date").isoformat(), D("2027-07-27"))
		self.assertEqual(float(frappe.db.get_value("Purchase Order", self.order(), "grand_total")), 1_000_000)
		self.assertFalse(frappe.db.exists("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Funding adjustment"}))  # the price did not change
		self.assertEqual(formation.current_agreement(self.case).version_no, 1)
		self.assertEqual(frappe.db.get_value("Contract Agreement Version", {"contract_case": self.case, "version_no": 2}, "state"), "Effective")

	def test_an_effective_quantity_increase_reaches_the_order_the_funding_owner_and_the_position(self):
		self.effective("Quantity")
		self.assertEqual(float(frappe.db.get_value("Contract Case", self.case, "contract_value")), 1_100_000)
		self.assertEqual(position.position(self.case)["lines"]["L1"]["ordered"], 11)
		self.assertEqual(position.position(self.case)["lines"]["L1"]["remaining"], 11)
		order = self.order()
		self.assertEqual((float(frappe.db.get_value("Purchase Order Item", {"parent": order}, "qty")), float(frappe.db.get_value("Purchase Order", order, "grand_total"))), (11, 1_100_000))
		from kentender_contracts.simulation import funding

		self.assertEqual(funding.Provider().position(self.case)["amount"], 1_100_000)
		self.assertEqual({i.operation_kind: i.state for i in frappe.get_all("Contract Operation Intent", filters={"contract_case": self.case, "subject": "amendment 1"}, fields=["operation_kind", "state"])},
			{"Purchase order": "Succeeded", "Funding adjustment": "Succeeded"})
		self.assertEqual(self.operative()["funding"]["allocations"][0]["amount"], 1_100_000)
		self.assertFalse(holds.open_holds(self.case))

	def test_the_ceiling_is_measured_from_the_original_quantity_not_the_operative_one(self):
		self.effective("Quantity")  # 10 -> 11, 10% of the original
		out = refusal(self.ask, "Quantity", request={"quantities": {"L1": 12}})  # 12 is 9.1% above 11 but 20% above the original 10
		self.assertEqual((out.code, out.detail["hold"]), ("CM_HOLD", "CHANGE_LIMIT_EXCEEDED"))
		self.assertIn("quantity.L1", refusal(self.ask, "Quantity", request={"quantities": {"L1": 11}}).fields)

	def test_a_second_change_is_numbered_and_judged_on_the_terms_the_first_left(self):
		self.effective()
		self.ask(request={"proposed_date": D("2027-08-03")})
		self.assertEqual(self.row(2).change_no, 2)
		self.assertEqual(records.loads(self.row(2).baseline_json)["due"], D("2027-07-27"))  # the date the first amendment made operative

	def test_a_pending_order_or_funding_update_holds_new_spending_until_it_is_restored_without_new_signatures(self):
		frappe.flags.kt_cm_funding_fault = "fail"
		self.approved("Quantity")
		self.sign("Supplier")
		self.sign("Entity")
		states = {i.operation_kind: i.state for i in frappe.get_all("Contract Operation Intent", filters={"contract_case": self.case, "subject": "amendment 1"}, fields=["operation_kind", "state"])}
		self.assertEqual(states, {"Purchase order": "Succeeded", "Funding adjustment": "Uncertain"})
		held = [h for h in holds.open_holds(self.case) if h.kind == "Pending operation"]
		self.assertTrue(held)
		self.assertTrue(holds.blocking(self.case, "new_spending") and holds.blocking(self.case, "pay"))
		self.assertEqual(self.operative()["total"], 1_100_000)  # the term is in force: only spending waits
		frappe.flags.kt_cm_funding_fault = None
		signatures = frappe.db.count("Contract Signature", {"contract_case": self.case, "state": "Signed"})
		formation.restore_operations(self.case, actor=self.p["daniel"])
		self.assertEqual({i.operation_kind: i.state for i in frappe.get_all("Contract Operation Intent", filters={"contract_case": self.case, "subject": "amendment 1"}, fields=["operation_kind", "state"])},
			{"Purchase order": "Succeeded", "Funding adjustment": "Succeeded"})
		self.assertFalse(holds.blocking(self.case, "new_spending"))
		self.assertEqual(frappe.db.count("Contract Signature", {"contract_case": self.case, "state": "Signed"}), signatures)
		self.assertEqual(frappe.db.count("Contract Simulated Funding", {"contract": self.case, "outcome": "Adjusted"}), 1)

	def test_a_funding_refusal_is_failed_and_the_order_is_not_adjusted_twice_on_a_retry(self):
		frappe.flags.kt_cm_funding_fault = "refuse"
		self.effective("Quantity")
		self.assertEqual(frappe.db.get_value("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Funding adjustment"}, "state"), "Failed")
		self.assertTrue(holds.blocking(self.case, "pay"))
		change.carry_out_effects(self.case, self.p["daniel"])
		change.carry_out_effects(self.case, self.p["daniel"])
		self.assertEqual(float(frappe.db.get_value("Purchase Order Item", {"parent": self.order()}, "qty")), 11)  # read the owner first: no second increase
		self.assertEqual(float(frappe.db.get_value("Purchase Order", self.order(), "grand_total")), 1_100_000)

	def test_an_order_update_that_could_not_reach_the_owner_is_restored_once(self):
		from kentender_contracts.native import adapter

		with mock.patch.object(adapter, "update_order", side_effect=RuntimeError("The buying module did not answer.")):
			self.effective("Quantity")
		self.assertEqual(frappe.db.get_value("Contract Operation Intent", {"contract_case": self.case, "operation_kind": "Purchase order", "subject": "amendment 1"}, "state"), "Uncertain")
		self.assertEqual(float(frappe.db.get_value("Purchase Order Item", {"parent": self.order()}, "qty")), 10)
		formation.restore_operations(self.case, actor=self.p["daniel"])
		formation.restore_operations(self.case, actor=self.p["daniel"])
		self.assertEqual(float(frappe.db.get_value("Purchase Order Item", {"parent": self.order()}, "qty")), 11)
		self.assertFalse(holds.blocking(self.case, "new_spending"))

	def test_an_update_the_owner_already_holds_is_linked_and_never_made_again(self):
		from kentender_contracts.native import adapter
		from kentender_core.services import contract_funding_contract as seam

		self.effective("Quantity")
		names = {i.operation_kind: i.name for i in frappe.get_all("Contract Operation Intent", filters={"contract_case": self.case, "subject": "amendment 1"}, fields=["operation_kind", "name"])}
		for name in names.values():  # the owners did their part; the outcome was not recorded (a crash between the owner's commit and ours)
			frappe.db.set_value("Contract Operation Intent", name, "state", "Uncertain")
		frappe.db.commit()
		with mock.patch.object(adapter, "update_order", side_effect=AssertionError("the order already holds the update")), mock.patch.object(seam, "adjust", side_effect=AssertionError("the commitment already holds the update")):
			change.carry_out_effects(self.case, self.p["daniel"])
		self.assertEqual({k: frappe.db.get_value("Contract Operation Intent", n, "state") for k, n in names.items()}, {"Purchase order": "Reconciled", "Funding adjustment": "Reconciled"})

	def test_a_future_effective_date_waits_signed_and_the_date_activates_it(self):
		self.ask(request={"proposed_date": D("2027-07-27")})
		row = self.row()
		body = change.proposal(row)
		frappe.db.set_value("Contract Change", row.name, "proposal_json", records.dumps({**body, "effective_on": D("2027-07-10")}))
		self.appoint()
		self.reviewed()
		self.submit()
		self.decide()
		self.sign("Supplier")
		out = self.sign("Entity")
		self.assertNotIn("effective", out)
		self.assertEqual(self.row().state, "Approved")
		self.assertEqual(self.operative()["delivery"]["due"], D("2027-07-20"))
		self.assertIn(("ActivateContractChange", "Bring amendment 1 into effect.", "scheduled"), self.tasks("charles"))
		self.assertEqual(refusal(change.activate_change, self.case, change=1, expected_version=self.t.version(), idempotency_key=self.t.key("act"), actor=self.p["charles"]).code, "CM_HOLD")
		frappe.flags.kt_cm_clock = D("2027-07-10 09:00:00")
		change.activate_change(self.case, change=1, expected_version=self.t.version(), idempotency_key=self.t.key("act2"), actor=self.p["charles"])
		self.assertEqual((self.row().state, self.operative()["delivery"]["due"]), ("Effective", D("2027-07-27")))

	def test_a_replayed_signature_or_activation_changes_nothing_more(self):
		self.approved("Quantity")
		key = self.t.key("sign-s")
		args = dict(change=1, party="Supplier", expected_version=self.t.version(), idempotency_key=key, actor=self.p["mary"])
		first = change.sign_amendment(self.case, **args)
		self.assertEqual(change.sign_amendment(self.case, **args), first)
		self.sign("Entity")
		change.carry_out_effects(self.case, self.p["daniel"])
		change.carry_out_effects(self.case, self.p["daniel"])
		self.assertEqual(frappe.db.count("Contract Simulated Funding", {"contract": self.case, "outcome": "Adjusted"}), 1)
		self.assertEqual(frappe.db.count("Contract Transaction Link", {"contract_case": self.case, "operation_identity": ["like", "%amendment 1%Purchase order%"]}), 1)

	def test_a_change_to_a_contract_that_is_not_active_is_refused(self):
		frappe.db.set_value("Contract Case", self.case, "lifecycle", "Closed")
		self.assertEqual(refusal(self.ask).code, "CM_CHANGED")
