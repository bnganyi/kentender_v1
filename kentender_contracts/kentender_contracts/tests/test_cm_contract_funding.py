# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.10 sections 20.4, 20.4A, 20.5, 20.6 (CM-AC-72 to -96): how Contract Management funds a contract signed before KenTender.

A stand-in for the funding owner records what Contract Management sends it and lets the test feed outcomes back, so that Contract Management's side of the journey is proved without Budget. The real
Award -> Contract Management -> Budget journey and the independent-contract journey, with both real owners, are run by `scripts/bud_v116_canonical_award_journey.py` and `scripts/bud_v116_independent_contract_journey.py`
(reports in `artifacts/`): Contract Management does not import Budget, so the two modules meet only in those scripts, never in this module.

The head of procurement records the route; Finance approval (never the Finance preparer of the same figures) confirms a year's charge as a versioned `ContractFundingBasis.v1`; the head raises one request per
year; outcomes arrive in order and idempotently; and what is not funded is held, scope by scope, and nothing else."""

from __future__ import annotations

import frappe
from frappe.utils import cstr
from unittest import mock

from kentender_contracts.services import contract_funding as funding
from kentender_contracts.services import errors, holds, records, work
from kentender_contracts.tests import thread_world as tw
from kentender_contracts.tests.support import ContractCase
from kentender_core.services import contract_funding_request_contract as seam

CASE = "Contract Case"
YEAR_1, YEAR_2, YEAR_3 = "KT-CMF-2051", "KT-CMF-2052", "KT-CMF-2053"


class _Owner:
	"""Records every call and answers like Budget would, minus the money."""

	def __init__(self):
		self.requests: list[dict] = []
		self.bases: list[dict] = []
		self.withdrawn: list[dict] = []
		self.refuse: str = ""
		self.active_years = {YEAR_1, YEAR_2}

	def receive(self, *, identity, request):
		if self.refuse:
			raise seam.Refused(self.refuse)
		self.requests.append({"identity": identity, **request})
		key = seam.scope_key(kind=request["kind"], contract=request["contract"], target_year=request.get("target_year", ""), subject_event=request.get("subject_event", ""))
		return {"ok": True, "created": True, "request": {"code": f"CFR-{len(self.requests)}", "scope_key": key}}

	def update_basis(self, *, identity, scope_key, basis, evidence):
		self.bases.append({"identity": identity, "scope_key": scope_key, "basis": basis, "evidence": evidence})
		return {"ok": True}

	def withdraw(self, *, identity, scope_key, reason):
		self.withdrawn.append({"scope_key": scope_key, "reason": reason})
		return {"ok": True}

	def lookup(self, *, scope_key):
		return None

	def year_status(self, *, fiscal_year):
		return {"fiscal_year": fiscal_year, "active": fiscal_year in self.active_years, "currency": "KES"}


class _FundingWorld(ContractCase):
	"""An independently registered contract with the test world's people, three financial years and a stand-in funding owner."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.people = tw.build()
		cls.addClassCleanup(tw.teardown)
		cls.years = []
		for number, name in ((2051, YEAR_1), (2052, YEAR_2), (2053, YEAR_3)):
			if not frappe.db.exists("Fiscal Year", name):
				frappe.get_doc({"doctype": "Fiscal Year", "year": name, "year_start_date": f"{number}-07-01", "year_end_date": f"{number + 1}-06-30"}).insert(ignore_permissions=True)
				cls.years.append(name)
		frappe.db.commit()
		cls.addClassCleanup(lambda: [frappe.delete_doc("Fiscal Year", name, force=1, ignore_permissions=True) for name in cls.years])

	def setUp(self):
		super().setUp()
		self.env = tw.Environment().__enter__()
		self.addCleanup(lambda: self.env.__exit__(None, None, None))
		self.p, self.n = self.people, 0
		self.owner = _Owner()
		previous = frappe.flags.get(seam.OWNER_FLAG)
		frappe.flags[seam.OWNER_FLAG] = [self.owner]
		self.addCleanup(lambda: frappe.flags.update({seam.OWNER_FLAG: previous}))
		patcher = mock.patch.object(funding, "current_year", return_value=YEAR_1)  # "now" is the first test year
		patcher.start()
		self.addCleanup(patcher.stop)
		self.case = records.new(CASE, contract_id=f"CM-FND-{frappe.generate_hash(length=6)}", source_kind="External record", lifecycle="Active", record_version=1, contract_value=900000, currency="KES",
			supplier_name="Afya Digital Supplies Limited", managing_unit=tw.unit(), title="Existing contract funding", current_agreement=1, intake_revision=1).name

	def k(self):
		self.n += 1
		return f"fnd-{self.id().rsplit('.', 1)[-1][:40]}-{self.n}"

	def version(self):
		return frappe.db.get_value(CASE, self.case, "record_version")

	def route(self, route=funding.ROUTE_BUDGET, who="charles", **o):
		values = dict(route=route, authority_name="Ministry Accounting Officer", approved_amount="900000.00", evidence=["Funding authority letter 1"],
			schedule=[{"year": YEAR_1, "amount": "300000.00"}, {"year": YEAR_2, "amount": "400000.00"}, {"year": YEAR_3, "amount": "200000.00"}])
		values.update(o)
		return funding.record_route(self.case, expected_version=self.version(), idempotency_key=self.k(), actor=self.p[who], **values)

	def prepare(self, year=YEAR_1, who="josphat", charge="300000.00"):
		return funding.prepare_year_basis(self.case, year=year, charge=charge, explanation="Prior activity and the year's obligation reconciled to the signed terms", evidence=["Signed contract 1", "Annual funding schedule 1"],
			expected_version=self.version(), idempotency_key=self.k(), actor=self.p[who])

	def confirm(self, year=YEAR_1, who="beatrice", **o):
		return funding.confirm_funding_evidence(self.case, year=year, expected_version=self.version(), idempotency_key=self.k(), actor=self.p[who], **o)

	def request(self, year=YEAR_1, who="charles"):
		return funding.request_funding(self.case, year=year, expected_version=self.version(), idempotency_key=self.k(), actor=self.p[who])

	def outcome(self, year, sequence, name, detail=None):
		rec = funding.get_record(self.case, year)
		return funding.receive_outcome({"request": "CFR-1", "scope_key": rec.scope_key, "sequence": sequence, "attempt": f"a{sequence}", "outcome": name, "detail": detail or {}})

	def rec(self, year):
		return funding.get_record(self.case, year)

	def invoice(self, number, date):
		return records.new("Contract Invoice", contract_case=self.case, invoice_no=number, claim_reference=f"CLM-{number}", invoice_date=date, received_at=f"{date} 09:00:00", claimed_amount=1000, state="Submitted",
			lines_json="[]", matching_json="{}", record_version=1)

	def refusal(self, fn, *a, **kw):
		try:
			fn(*a, **kw)
		except (errors.ContractError, errors.InputError) as exc:
			return exc
		raise AssertionError("expected a refusal")



class TestFundingAnIndependentContract(_FundingWorld):
	# the route -------------------------------------------------------------------------------------------------------------------
	def test_the_head_records_the_route_with_its_evidence_and_the_year_shares(self):
		out = self.route()
		self.assertEqual(out["route"], funding.ROUTE_BUDGET)
		case = frappe.get_doc(CASE, self.case)
		self.assertEqual(case.funding_route, funding.ROUTE_BUDGET)
		self.assertEqual(records.loads(case.funding_authority_json)["evidence"], ["Funding authority letter 1"])
		self.assertEqual([(r.fiscal_year, r.schedule_amount) for r in funding.records_of(self.case)], [(YEAR_1, "300000.00"), (YEAR_2, "400000.00"), (YEAR_3, "200000.00")])

	def test_a_share_row_left_on_the_placeholder_is_no_year_at_all(self):
		from kentender_contracts.api import commands

		values = {"route": "KenTender Budget", "authority": "Ministry Accounting Officer", "approved_amount": "900000", "evidence": "Funding authority letter 1", "schedule.1.year": YEAR_1, "schedule.1.amount": "300000",
			"schedule.2.year": "Select", "schedule.2.amount": "", "schedule.3.year": "Select", "schedule.3.amount": ""}
		commands.COMMANDS["RecordContractFundingRoute"](self.case, {}, values, self.version(), self.k(), self.p["charles"])
		self.assertEqual([(r.fiscal_year, r.schedule_amount) for r in funding.records_of(self.case)], [(YEAR_1, "300000.00")])

	def test_only_the_head_records_the_route_and_it_needs_evidence_and_real_years(self):
		for who in ("josphat", "beatrice", "brian"):
			with self.subTest(who):
				self.assertEqual(self.refusal(self.route, who=who).code, "CM_AUTHORITY")
		self.assertIn("evidence", self.refusal(self.route, evidence=[]).fields)
		self.assertIn("schedule.1.year", self.refusal(self.route, schedule=[{"year": "NO-SUCH-YEAR", "amount": "1.00"}]).fields)
		self.assertIn("schedule", self.refusal(self.route, schedule=[{"year": YEAR_1, "amount": "999999999.00"}]).fields)
		self.assertEqual(frappe.db.get_value(CASE, self.case, "funding_route") or "", "")

	def test_an_outside_route_names_its_authority(self):
		self.assertIn("authority", self.refusal(self.route, route=funding.ROUTE_OUTSIDE, authority_name="").fields)
		self.assertEqual(self.route(route=funding.ROUTE_OUTSIDE)["route"], funding.ROUTE_OUTSIDE)

	def test_a_contract_an_award_funded_has_no_route_to_record(self):
		award = records.new(CASE, contract_id=f"CM-AWD-{frappe.generate_hash(length=5)}", source_kind="KenTender award", lifecycle="Active", record_version=1, contract_value=100, currency="KES").name
		exc = self.refusal(funding.record_route, award, route=funding.ROUTE_BUDGET, authority_name="x", approved_amount="", evidence=["e"], schedule=[], expected_version=1, idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(exc.code, "CM_CHANGED")

	# Finance confirms the basis, independently of whoever prepared it -----------------------------------------------------------------
	def test_finance_approval_confirms_the_year_as_a_versioned_basis_and_the_preparer_cannot(self):
		self.route()
		self.prepare()
		blocked = self.refusal(self.confirm, who="josphat")
		self.assertIn(blocked.code, ("CM_AUTHORITY", "CM_SEGREGATION"), "the preparer holds Finance preparation, not Finance approval, and could never confirm his own figures")
		out = self.confirm()
		self.assertEqual(out["revision"], 1)
		rec = self.rec(YEAR_1)
		confirmation = funding.confirmed(rec)
		self.assertEqual((confirmation["by"], confirmation["charge"], confirmation["revision"]), (self.p["beatrice"], "300000.00", 1))
		basis = funding.basis_of(rec, frappe.get_doc(CASE, self.case), confirmation)
		self.assertEqual((basis["schema"], basis["target_year"], basis["confirmed_charge"], basis["currency"]), (seam.BASIS_SCHEMA, YEAR_1, "300000.00", "KES"))
		self.assertEqual(seam.validate_basis(basis, contract=self.case, target_year=YEAR_1, currency="KES"), [], "Budget can rely on it")
		self.assertEqual(basis["confirmers"][0]["user"], self.p["beatrice"])

	def test_a_finance_approver_who_also_prepared_the_figures_cannot_confirm_them(self):
		self.route()
		funding.prepare_year_basis(self.case, year=YEAR_1, charge="300000.00", explanation="Reconciled to the signed terms", evidence=["Signed contract 1"], expected_version=self.version(), idempotency_key=self.k(), actor=self.p["josphat"])
		frappe.db.set_value("Contract Funding Record", self.rec(YEAR_1).name, "prepared_by", self.p["beatrice"])
		self.assertEqual(self.refusal(self.confirm, who="beatrice").code, "CM_SEGREGATION")

	def test_a_change_after_confirmation_is_unconfirmed_until_confirmed_again_and_the_earlier_version_stays(self):
		self.route()
		self.prepare()
		self.confirm()
		self.prepare(charge="310000.00")
		rec = self.rec(YEAR_1)
		self.assertIsNone(funding.confirmed(rec), "different figures are not the figures Finance confirmed")
		self.confirm()
		rec = self.rec(YEAR_1)
		self.assertEqual([(c["revision"], c["charge"]) for c in funding.confirmations(rec)], [(1, "300000.00"), (2, "310000.00")])
		self.assertEqual(funding.confirmed(rec)["revision"], 2)

	def test_only_finance_approval_confirms_a_funding_basis(self):
		self.route()
		self.prepare()
		for who in ("charles", "amina", "brian"):
			with self.subTest(who):
				self.assertEqual(self.refusal(self.confirm, who=who).code, "CM_AUTHORITY")

	# the request ------------------------------------------------------------------------------------------------------------------
	def test_a_request_can_be_raised_before_finance_has_confirmed_and_finance_gets_the_task(self):
		self.route()
		out = self.request()
		self.assertEqual(out["kind"], "Initial")
		sent = self.owner.requests[0]
		self.assertEqual((sent["kind"], sent["contract"], sent["target_year"], sent["basis"]), ("Initial", self.case, YEAR_1, {}))
		rec = self.rec(YEAR_1)
		self.assertEqual((rec.request_state, funding.label_of(rec, funding.ROUTE_BUDGET, year_now=YEAR_1)), ("Open", funding.S_YEAR_REQUIRED))
		live = {(t["command"], t["holder"], t["state"]) for t in work.live(self.case)}
		self.assertIn(("ConfirmContractFundingEvidence", self.p["beatrice"], "actionable"), live)
		self.assertIn((work.waiting_command("RequestExistingContractFunding", "finance"), self.p["charles"], "waiting"), live)

	def test_finance_confirming_later_refreshes_the_same_request_with_the_basis(self):
		self.route()
		self.request()
		self.prepare()
		self.confirm()
		self.assertEqual(len(self.owner.requests), 1, "no second request")
		self.assertEqual(len(self.owner.bases), 1)
		sent = self.owner.bases[0]
		self.assertEqual((sent["scope_key"], sent["basis"]["confirmed_charge"], sent["basis"]["target_year"]), (self.rec(YEAR_1).scope_key, "300000.00", YEAR_1))
		self.assertEqual(self.rec(YEAR_1).request_state, "Open")

	def test_a_request_with_the_basis_confirmed_carries_it(self):
		self.route()
		self.prepare()
		self.confirm()
		self.request()
		self.assertEqual(self.owner.requests[0]["basis"]["confirmed_charge"], "300000.00")
		live = {(t["command"], t["holder"], t["state"]) for t in work.live(self.case)}
		self.assertIn((work.waiting_command("RequestExistingContractFunding", "budget"), self.p["charles"], "waiting"), live)

	def test_only_the_head_requests_and_only_for_the_budget_route(self):
		self.route()
		self.assertEqual(self.refusal(self.request, who="beatrice").code, "CM_AUTHORITY")
		frappe.db.set_value(CASE, self.case, "funding_route", funding.ROUTE_OUTSIDE)
		self.assertEqual(self.refusal(self.request).code, "CM_CHANGED")
		self.assertEqual(self.owner.requests, [])

	def test_a_refusal_by_the_funding_owner_is_shown_not_swallowed_and_leaves_no_open_request(self):
		self.route()
		self.owner.refuse = "This contract was awarded through KenTender."
		exc = self.refusal(self.request)
		self.assertEqual(exc.code, "CM_FUNDING")
		self.assertIn("awarded through KenTender", cstr(exc.reasons[0]["detail"].get("reason")))
		self.assertNotEqual(self.rec(YEAR_1).request_state, "Open")

	def test_the_first_funded_year_is_initial_and_a_later_one_is_annual(self):
		self.route()
		self.request(YEAR_1)
		self.outcome(YEAR_1, 1, seam.OUTCOME_APPROVED)
		self.request(YEAR_2)
		self.assertEqual([r["kind"] for r in self.owner.requests], ["Initial", "Annual"])

	def test_cm_asks_whether_a_later_year_is_eligible_and_nothing_else(self):
		self.assertTrue(seam.year_status(YEAR_2)["active"])
		self.assertFalse(seam.year_status(YEAR_3)["active"])

	# outcomes ---------------------------------------------------------------------------------------------------------------------
	def test_outcomes_are_recorded_in_order_once_and_the_closing_one_completes_the_year(self):
		self.route()
		self.request()
		self.assertEqual(self.outcome(YEAR_1, 1, seam.OUTCOME_ENTRY_SUBMITTED)["receipt"], f"{self.rec(YEAR_1).name}:1")
		self.assertEqual(funding.label_of(self.rec(YEAR_1), funding.ROUTE_BUDGET, year_now=YEAR_1), funding.S_YEAR_REQUIRED)  # still no confirmed basis here
		self.outcome(YEAR_1, 2, seam.OUTCOME_SHORTFALL, {"shortfalls": [{"budget_line": "BL", "shortfall": "50000.00"}]})
		self.assertEqual((self.rec(YEAR_1).request_state, self.rec(YEAR_1).outcome), ("Open", seam.OUTCOME_SHORTFALL), "a shortfall leaves the request open")
		repeated = self.outcome(YEAR_1, 2, seam.OUTCOME_APPROVED)
		self.assertTrue(repeated.get("repeated"))
		self.assertEqual(self.rec(YEAR_1).outcome, seam.OUTCOME_SHORTFALL, "an outcome already received changes nothing")
		stale = self.outcome(YEAR_1, 1, seam.OUTCOME_APPROVED)
		self.assertTrue(stale.get("repeated"))
		self.outcome(YEAR_1, 3, seam.OUTCOME_APPROVED)
		rec = self.rec(YEAR_1)
		self.assertEqual((rec.request_state, rec.outcome, funding.label_of(rec, funding.ROUTE_BUDGET)), ("Completed", seam.OUTCOME_APPROVED, funding.S_APPROVED))
		self.assertIn(YEAR_1, funding.funded_years(self.case))

	def test_an_outcome_for_a_request_this_contract_management_does_not_hold_is_not_acknowledged(self):
		self.assertIsNone(funding.receive_outcome({"scope_key": "NOT|MINE|2101", "sequence": 1, "outcome": seam.OUTCOME_APPROVED, "attempt": "x"}))

	def test_already_covered_and_no_charge_complete_the_year_with_their_own_words(self):
		self.route()
		self.request(YEAR_1)
		self.outcome(YEAR_1, 1, seam.OUTCOME_ALREADY_COVERED)
		self.assertEqual(funding.label_of(self.rec(YEAR_1), funding.ROUTE_BUDGET), funding.S_ALREADY)
		self.request(YEAR_2)
		self.outcome(YEAR_2, 1, seam.OUTCOME_NO_CHARGE)
		self.assertEqual(funding.label_of(self.rec(YEAR_2), funding.ROUTE_BUDGET), funding.S_NO_CHARGE)
		self.assertEqual(funding.funded_years(self.case), {YEAR_1, YEAR_2})

	def test_a_decline_or_withdrawal_is_retained_and_the_same_year_can_be_requested_again(self):
		self.route()
		self.request()
		self.outcome(YEAR_1, 1, seam.OUTCOME_DECLINED, {"reason": "Correct the mapping first."})
		rec = self.rec(YEAR_1)
		self.assertEqual((rec.request_state, funding.label_of(rec, funding.ROUTE_BUDGET)), ("Declined", funding.S_DECLINED))
		self.request()
		self.assertEqual((self.rec(YEAR_1).request_state, len(self.owner.requests)), ("Open", 2))
		self.assertEqual(frappe.db.count("Contract Funding Record", {"contract_case": self.case, "fiscal_year": YEAR_1}), 1, "the same lineage, never a second record for the year")

	def test_the_head_withdraws_an_open_request_before_funding(self):
		self.route()
		self.request()
		out = funding.withdraw_funding_request(self.case, year=YEAR_1, reason="The contract is being corrected.", expected_version=self.version(), idempotency_key=self.k(), actor=self.p["charles"])
		self.assertTrue(out["ok"])
		self.assertEqual((self.rec(YEAR_1).request_state, self.owner.withdrawn[0]["reason"]), ("Withdrawn", "The contract is being corrected."))
		self.assertTrue(self.refusal(funding.withdraw_funding_request, self.case, year=YEAR_1, reason="again, for no reason", expected_version=self.version(), idempotency_key=self.k(), actor=self.p["charles"]))

	def test_a_correction_is_requested_citing_the_commitment_and_the_record_that_shows_the_error(self):
		self.route()
		out = funding.request_funding_correction(self.case, commitment="COM-0001", correction_reference="CM-CORR-1", reason="The final obligation included work never performed.", evidence=["Final obligation review 1"],
			expected_version=self.version(), idempotency_key=self.k(), actor=self.p["charles"])
		self.assertTrue(out["ok"])
		sent = self.owner.requests[-1]
		self.assertEqual((sent["kind"], sent["original_commitment"], sent["subject_event"]), ("Correction", "COM-0001", "CM-CORR-1"))
		bad = self.refusal(funding.request_funding_correction, self.case, commitment="", correction_reference="", reason="x", evidence=[], expected_version=self.version(), idempotency_key=self.k(), actor=self.p["charles"])
		self.assertEqual(set(bad.fields), {"commitment", "correction_reference", "reason", "evidence"})

	# what is held ------------------------------------------------------------------------------------------------------------------
	def test_a_contract_with_no_route_recorded_keeps_its_earlier_behaviour(self):
		self.invoice(1, "2051-08-15")
		self.assertEqual([h for h in holds.open_holds(self.case) if h.kind == "Funding"], [])

	def test_an_unfunded_year_holds_its_payments_and_the_current_years_new_spending_and_nothing_else(self):
		self.route()
		self.invoice(1, "2051-08-15")  # in the first year
		self.invoice(2, "2052-08-15")  # in the second
		pay_1, pay_2 = holds.blocking(self.case, "pay", "invoice 1"), holds.blocking(self.case, "pay", "invoice 2")
		self.assertEqual(([h.reason for h in pay_1], [h.reason for h in pay_2]), (["Funding is not confirmed for this payment."], ["Funding is not confirmed for this payment."]))
		self.assertTrue(holds.blocking(self.case, "new_spending"))
		self.assertTrue(holds.blocking(self.case, "vary_contract"))
		for capability in ("certify_invoice", "post_receipt", "confirm_settlement", "use_goods", "final_accept", "close_contract"):
			self.assertEqual([h for h in holds.blocking(self.case, capability) if h.kind == "Funding"], [], f"{capability} records or accepts a fact and is never held for funding")

	def test_funding_the_first_year_releases_its_payments_and_the_current_years_spending_but_not_a_later_years_payment(self):
		self.route()
		self.invoice(1, "2051-08-15")
		self.invoice(2, "2052-08-15")
		self.request(YEAR_1)
		self.outcome(YEAR_1, 1, seam.OUTCOME_APPROVED)
		self.assertEqual(holds.blocking(self.case, "pay", "invoice 1"), [])
		self.assertEqual(holds.blocking(self.case, "new_spending"), [])
		self.assertEqual(len(holds.blocking(self.case, "pay", "invoice 2")), 1, "a future year's share is not funded because the first year is")
		self.assertTrue(self.refusal(funding.recheck, self.case, "invoice 2", consequence="pay"))
		funding.recheck(self.case, "invoice 1", consequence="pay")  # covered: passes

	def test_a_payment_that_is_not_for_a_funded_year_is_refused_at_the_native_boundary_with_the_reason(self):
		self.route()
		self.invoice(1, "2051-08-15")
		exc = self.refusal(funding.recheck, self.case, "invoice 1", consequence="pay")
		self.assertEqual(exc.code, "CM_HOLD")
		self.assertEqual(exc.reasons[0]["detail"]["reason"], "Funding is not confirmed for this payment.")

	def test_an_advance_waits_for_the_current_years_funding(self):
		self.route()
		self.assertIsNotNone(funding.advance_hold(self.case))
		self.request(YEAR_1)
		self.outcome(YEAR_1, 1, seam.OUTCOME_APPROVED)
		self.assertIsNone(funding.advance_hold(self.case))

	def test_an_outside_route_holds_until_the_head_and_finance_have_both_confirmed(self):
		self.route(route=funding.ROUTE_OUTSIDE)
		self.assertTrue([h for h in holds.blocking(self.case, "pay") if h.kind == "Funding"])
		self.assertEqual(funding.view(self.case)["label"], funding.S_NOT_CONFIRMED)
		self.prepare()
		self.confirm()
		self.assertEqual([h for h in holds.blocking(self.case, "pay") if h.kind == "Funding"], [])
		self.assertEqual(funding.view(self.case)["label"], funding.S_OUTSIDE)
		self.assertEqual(self.owner.requests, [], "Budget is asked nothing for funding controlled elsewhere")

	def test_a_view_says_where_each_year_stands(self):
		self.route()
		self.prepare()
		self.confirm()
		self.request(YEAR_1)
		self.outcome(YEAR_1, 1, seam.OUTCOME_APPROVED)
		view = funding.view(self.case)
		by_year = {y["year"]: y["label"] for y in view["years"]}
		self.assertEqual(by_year, {YEAR_1: funding.S_APPROVED, YEAR_2: funding.S_FUTURE, YEAR_3: funding.S_FUTURE})
		self.assertEqual(next(y for y in view["years"] if y["year"] == YEAR_1)["confirmed_by"], self.p["beatrice"])


class TestTheOpeningConfirmationAlsoConfirmsThePreparedBasis(_FundingWorld):
	"""CM-CHG-001 v0.10 section 20.6: `ConfirmOpeningPosition` additionally confirms the funding basis in the same action. The funding part never invents a figure: it confirms only what Finance preparation already
	prepared for a year up to the current one, and never the confirming person's own preparation."""

	def contract(self):
		return frappe.get_doc(CASE, self.case)

	def test_a_prepared_basis_for_the_current_year_is_confirmed_by_the_same_action(self):
		self.route()
		self.prepare(YEAR_1)
		years = funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k())
		self.assertEqual(years, [YEAR_1])
		confirmation = funding.confirmed(self.rec(YEAR_1))
		self.assertEqual((confirmation["by"], confirmation["charge"], confirmation["revision"]), (self.p["beatrice"], "300000.00", 1))

	def test_a_year_nobody_prepared_and_a_later_year_are_left_alone(self):
		self.route()
		self.prepare(YEAR_2, charge="400000.00")  # a later year, prepared early
		self.assertEqual(funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k()), [])
		self.assertIsNone(funding.confirmed(self.rec(YEAR_1)), "the current year was never prepared, so nothing is invented")
		self.assertIsNone(funding.confirmed(self.rec(YEAR_2)))

	def test_the_person_who_prepared_the_figures_does_not_confirm_them_in_the_same_action(self):
		self.route()
		self.prepare(YEAR_1)
		frappe.db.set_value("Contract Funding Record", self.rec(YEAR_1).name, "prepared_by", self.p["beatrice"])
		self.assertEqual(funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k()), [])
		self.assertIsNone(funding.confirmed(self.rec(YEAR_1)))

	def test_a_contract_with_no_budget_route_confirms_nothing(self):
		self.assertEqual(funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k()), [])
		self.route(route=funding.ROUTE_OUTSIDE)
		self.assertEqual(funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k()), [])

	def test_the_same_year_is_not_confirmed_twice(self):
		self.route()
		self.prepare(YEAR_1)
		self.assertEqual(funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k()), [YEAR_1])
		self.assertEqual(funding.confirm_with_opening(self.contract(), self.p["beatrice"], self.k()), [])
		self.assertEqual(len(funding.confirmations(self.rec(YEAR_1))), 1)


class TestTheFundingScreens(_FundingWorld):
	"""CM-CHG-001 v0.10 section 10.9 (CM-AC-94): funding appears within the existing screens, only to the contract's own people, with the exact words, and a held payment says why and who has the next step."""

	def context(self, who):
		from kentender_contracts.boards.context import Context

		return Context(self.case, self.p[who])

	def titles(self, board):
		return [r["t"] for r in board["regions"]]

	def test_the_head_sees_the_route_form_before_a_route_is_recorded_and_the_request_buttons_after(self):
		from kentender_contracts.boards import funding_board

		board = funding_board.d21f(self.context("charles"))
		self.assertIn("Record funding route", board["actions"])
		self.assertEqual([r for r in board["regions"][0]["b"][0]["items"] if r[0] == "Funding route"], [["Funding route", "Not yet recorded"]])
		self.route()
		board = funding_board.d21f(self.context("charles"))
		self.assertIn(f"Request funding for {YEAR_1}", board["actions"])
		self.assertTrue(any(label.startswith("Request annual funding for") for label in board["actions"]) is False, "the first request is the initial one, the annual wording follows a funded year")

	def test_the_route_dialog_offers_financial_years_before_any_year_is_recorded(self):
		from kentender_contracts.boards import funding_board

		board = funding_board.d21f(self.context("charles"))
		fields = [f for row in board["dialogs"]["route"]["b"] for f in (row.get("items") or [row]) if isinstance(f, dict)]
		year = next(f for f in fields if f.get("name") == "schedule.1.year")
		self.assertEqual(year["opts"][0], "Select")
		self.assertTrue(len(year["opts"]) > 1, "a head with no year recorded still has years to give a share to")

	def test_finance_sees_the_confirm_action_for_a_year_and_never_the_request(self):
		from kentender_contracts.boards import funding_board

		self.route()
		self.prepare(YEAR_1)
		board = funding_board.d21f(self.context("beatrice"))
		self.assertIn(f"Confirm the funding basis for {YEAR_1}", board["actions"])
		self.assertFalse([a for a in board["actions"] if a.startswith("Request ")])

	def test_a_supplier_or_a_reader_with_no_part_in_the_contract_does_not_see_the_funding_view(self):
		from kentender_contracts.boards import funding_board

		self.route()
		self.assertTrue(funding_board.visible(self.context("charles")))
		for who in ("mary", "david"):
			if who in self.p:
				self.assertFalse(funding_board.visible(self.context(who)), who)

	def test_the_intake_and_opening_screens_carry_a_funding_region_and_the_way_to_the_full_view(self):
		from kentender_contracts.boards import existing, funding_board

		self.route()
		ctx = self.context("charles")
		board = {"regions": [{"t": "Source", "b": []}, {"t": "Parties", "b": []}], "actions": {}, "s2": ["Cancel"], "tab": "Agreement"}
		funding_board.attach(ctx, board)
		self.assertEqual([r["t"] for r in board["regions"]], ["Source", "Funding", "Parties"])
		self.assertEqual(board["s2"], ["Cancel", funding_board.OPEN])
		self.assertEqual(board["actions"][funding_board.OPEN]["route"], [self.case, "agreement", "funding"])
		self.assertTrue(hasattr(existing, "d12") and hasattr(existing, "d21"))

	def test_a_payment_on_hold_for_funding_says_so_in_the_exact_words_and_names_the_holder(self):
		from kentender_contracts.boards import funding_board

		self.route()
		self.invoice(1, "2051-08-15")
		hold = holds.blocking(self.case, "pay", "invoice 1")[0]
		block = funding_board.held_block(self.context("charles"), hold)
		self.assertEqual((block["k"], block["h"], block["fixes"]), ("blk", "Funding is not confirmed for this payment.", [funding_board.OPEN]))
		self.assertIn("Responsible for the fix:", block["s"])
