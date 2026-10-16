# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 sections 4.12, 8.6, 8.7, 8.8 (BUD25-AC-003 to -009, -013; CM-AC-86 to -89, -92, -95, -96): the funding of a contract that was signed before KenTender.

Contract Management raises one request for the contract and a target Budget year, with Finance's confirmed funding charge. A Budget Officer prepares one entry; a Budget Approver who is none of the
preparer, the submitter or a Finance confirmer decides it; approval creates every commitment or none. The fixture is the one the document gives: a confirmed charge of KES 600,000 for the year, KES 100,000
of it already held by Budget as a real commitment of this contract, so KES 500,000 is new, spread over two lines of the same year (HWD 300,000, DHI 200,000)."""

from __future__ import annotations

import frappe

from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import budget_commitment_corrections as corrections
from kentender_budget.services import budget_contract_funding as funding
from kentender_budget.services import budget_existing_contract_entry as entries
from kentender_budget.services.budget_contracts import _line_position_exact
from kentender_budget.services.budget_reference import allocate_commitment_reference
from kentender_budget.services.budget_service_principal import PRINCIPAL_CONTRACT, PRINCIPAL_REQUISITIONS, service_caller
from kentender_budget.services.budget_write_family import budget_write
from kentender_budget.tests.test_bud_chg_001_v19_usability import _V19Base
from kentender_core.services import contract_funding_request_contract as seam
from kentender_core.services.command_write_guard import purge_doc
from kentender_core.services.responsibility_errors import ResponsibilityError

DHI = "Digital health infrastructure programme"
HWD = "Digital health workforce development"
RECONCILIATION = "Existing funding checked against the confirmed current-year charge."


class _Receiver:
	"""Stands in for Contract Management: acknowledges outcomes, in the order offered, unless it is told to be down."""

	def __init__(self):
		self.outcomes: list[dict] = []
		self.down = False

	def receive_outcome(self, *, outcome):
		if self.down:
			raise RuntimeError("Contract Management is down")
		self.outcomes.append(outcome)
		return {"receipt": f"R{len(self.outcomes)}"}

	def waiting_item(self, *, scope_key):
		return {"holder": "Ruth Achieng", "responsibility": "Finance approval", "action": "Open contract review"}

	def names(self):
		return [o["outcome"] for o in self.outcomes]


class _FundingBase(_V19Base):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.confirmer = f"finance.confirmer.{cls.suffix}@example.test"

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		for budget in cls._budgets:
			fiscal_year = frappe.db.get_value("Procurement Budget", budget, "fiscal_year")
			for name in frappe.get_all("Existing Contract Commitment Entry", filters={"budget": budget}, pluck="name"):
				purge_doc("Existing Contract Commitment Entry", name)
			for request in frappe.get_all("Contract Funding Request", filters={"fiscal_year": fiscal_year}, pluck="name"):
				for outcome in frappe.get_all("Contract Funding Outcome", filters={"request": request}, pluck="name"):
					purge_doc("Contract Funding Outcome", outcome)
				purge_doc("Contract Funding Request", request)
			for name in frappe.get_all("Procurement Commitment", filters={"budget": budget}, pluck="name"):
				purge_doc("Procurement Commitment", name)
		super().tearDownClass()

	def setUp(self):
		super().setUp()
		self.contract = f"CM-EXT-{self.suffix}-{frappe.generate_hash(length=5)}"
		self.caller = service_caller(PRINCIPAL_CONTRACT, reference=self.contract)
		self.fy, self.budget, self.v1 = self._active()
		self.dhi, self.hwd = self._line(self.v1, DHI), self._line(self.v1, HWD)
		self.receiver = _Receiver()
		previous = frappe.flags.get(seam.RECEIVER_FLAG)
		frappe.flags[seam.RECEIVER_FLAG] = [self.receiver]
		self.addCleanup(lambda: frappe.flags.update({seam.RECEIVER_FLAG: previous}))

	# -- builders -------------------------------------------------------------------------------------------------------------
	def basis(self, charge="600000.00", *, year=None, digest=None, confirmers=None, **extra):
		return {
			"schema": seam.BASIS_SCHEMA, "contract": self.contract, "target_year": year or self.fy, "currency": "KES", "confirmed_charge": charge, "digest": digest or f"BASIS-{charge}-{frappe.generate_hash(length=6)}",
			"evidence": ["Signed contract 1", "Opening reconciliation 1", "Year allocation evidence 1"], "explanation": "Prior activity and the current-year obligation reconciled to the signed terms",
			"confirmers": confirmers if confirmers is not None else [{"user": self.confirmer, "assignment": "URA-FINANCE-1", "at": "2026-10-16 09:00:00"}], **extra,
		}

	def receive(self, *, kind="Initial", basis="default", year=None, identity=None, **extra):
		request = {
			"kind": kind, "contract": self.contract, "contract_reference": "CM-MOH-2027-EXT-001", "agreement_version": "1", "supplier_name": "Afya Digital Supplies Limited", "target_year": year or self.fy,
			"currency": "KES", "source_organisation_unit": self.ou_dhp, "basis": self.basis() if basis == "default" else basis, "evidence": ["Signed contract 1"], **extra,
		}
		return funding.receive_contract_funding_request(request, identity or f"rcv-{frappe.generate_hash(length=10)}", caller=self.caller)

	def cover(self, amount, *, line=None, status="Active"):
		"""A real Budget commitment of this contract in this year: the 'existing coverage' of the fixture, never inferred from a paid invoice."""
		commitment = frappe.get_doc({"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "origin": "Existing-contract entry", "budget": self.budget, "budget_line": line or self.hwd,
			"entry_row": f"SEED/{frappe.generate_hash(length=6)}", "contract": self.contract, "status": status, "current_amount": amount, "currency": "KES"})
		with budget_write():
			commitment.insert(ignore_permissions=True)
		return commitment.name

	def rows(self, hwd="300000.00", dhi="200000.00"):
		return [{"budget_line": self.hwd, "amount": hwd}, {"budget_line": self.dhi, "amount": dhi}]

	def prepare(self, request, *, rows=None, reconciliation=RECONCILIATION, entry=None, user=None):
		self._as(user or self.officer)
		return entries.record_existing_contract_commitment_entry({"request": request, "entry": entry, "rows": self.rows() if rows is None else rows, "reconciliation": reconciliation,
			"idempotency_key": f"rec-{frappe.generate_hash(length=10)}"})

	def submit(self, entry, *, user=None):
		self._as(user or self.officer)
		return entries.submit_existing_contract_commitment_entry({"entry": entry, "idempotency_key": f"sub-{frappe.generate_hash(length=10)}"})

	def decide(self, entry, decision="Approve", *, reason="", user=None, key=None):
		self._as(user or self.approver)
		return entries.decide_existing_contract_commitment_entry({"entry": entry, "decision": decision, "reason": reason, "idempotency_key": key or f"dec-{frappe.generate_hash(length=10)}"})

	def position(self, line):
		exact = _line_position_exact(line, commit._current_line_version(line))
		return {key: float(value) for key, value in exact.items()}

	def fixture(self):
		"""The document's fixture up to a submitted entry: charge 600,000, coverage 100,000, two rows. Returns (request id, entry id)."""
		self.cover("100000.00")
		request = self.receive()["request"]
		entry = self.prepare(request["id"])["entry"]
		self.assertTrue(self.submit(entry["id"])["ok"])
		return request["id"], entry["id"]

	def commitments(self, **filters):
		return frappe.get_all("Procurement Commitment", filters={"contract": self.contract, **filters}, fields=["name", "current_amount", "status", "origin", "budget_line", "reservation", "entry_row"], order_by="creation asc")


class TestTheAmountIsCalculatedFromTheConfirmedChargeAndTheCoverageBudgetHolds(_FundingBase):
	def test_the_fixture_needs_500000_not_100000_600000_or_the_unpaid_balance(self):
		self.cover("100000.00")
		summary = self.receive()["request"]
		self.assertEqual((summary["confirmed_charge"], summary["coverage_total"], summary["amount_requiring_funding"]), ("600000.00", "100000.00", "500000.00"))
		self.assertEqual(summary["display_status"], "Ready to prepare")
		self.assertEqual(summary["holder"], "Budget Officer")

	def test_coverage_counts_active_and_closed_commitments_once_and_never_a_cancelled_one(self):
		self.cover("100000.00")
		self.cover("50000.00", status="Closed")
		self.cover("999999.00", status="Cancelled")
		self.assertEqual(self.receive()["request"]["coverage_total"], "150000.00")

	def test_coverage_of_another_contract_or_another_year_is_not_this_contracts(self):
		other_year = self._fresh_fy()
		self.cover("100000.00")
		other = frappe.get_doc({"doctype": "Procurement Commitment", "generated_reference": allocate_commitment_reference(), "origin": "Existing-contract entry", "budget": self.budget, "budget_line": self.hwd,
			"entry_row": "SEED/other", "contract": f"{self.contract}-OTHER", "status": "Active", "current_amount": 70000, "currency": "KES"})
		with budget_write():
			other.insert(ignore_permissions=True)
		summary = self.receive()["request"]
		self.assertEqual(summary["coverage_total"], "100000.00")
		self.assertTrue(other_year)

	def test_coverage_above_the_confirmed_charge_is_an_error_not_zero(self):
		self.cover("700000.00")
		request = self.receive()["request"]
		self.assertEqual(request["status"], "Open", "an over-covered request is not silently completed")
		prepared = self.prepare(request["id"])
		self.assertTrue(prepared["ok"], "Draft preparation is still possible")
		refused = self.submit(prepared["entry"]["id"])
		self.assertEqual((refused["ok"], refused["code"]), (False, "BUDGET_ENTRY_DUPLICATE"))
		self.assertEqual(len(self.commitments()), 1)

	def test_a_native_invoice_or_payment_is_not_coverage(self):
		# nothing about native accounting reaches Budget: with no commitment of this contract, the whole charge is new
		summary = self.receive()["request"]
		self.assertEqual((summary["coverage_total"], summary["amount_requiring_funding"]), ("0.00", "600000.00"))


class TestARequestIsOneRequestPerScope(_FundingBase):
	def test_an_identical_replay_returns_the_original_request(self):
		basis = self.basis()
		first = self.receive(identity="same-op", basis=basis)
		again = self.receive(identity="same-op", basis=basis)
		self.assertEqual((again["request"]["id"], again.get("replayed")), (first["request"]["id"], True))
		self.assertEqual(frappe.db.count("Contract Funding Request", {"contract": self.contract}), 1)

	def test_initial_and_annual_for_one_year_share_one_request(self):
		first = self.receive(kind="Initial")
		second = self.receive(kind="Annual")
		self.assertTrue(first["created"])
		self.assertEqual((second["created"], second["request"]["id"]), (False, first["request"]["id"]))

	def test_each_year_has_its_own_request(self):
		other_fy, other_budget, other_v = self._active(fiscal_year=self._fresh_fy())
		first = self.receive()
		second = self.receive(kind="Annual", year=other_fy, basis=self.basis("400000.00", year=other_fy))
		self.assertNotEqual(first["request"]["id"], second["request"]["id"])
		self.assertTrue(second["created"])

	def test_a_contract_an_award_funded_cannot_use_an_initial_or_annual_request_as_a_bypass(self):
		reservation = self._reserve(self.dhi, 1_000_000, ref=f"REQ-{self.contract}")
		self._as("Administrator")
		commit.convert_reservation(reservation, self.contract, 1_000_000, f"conv-{self.contract}", contract_event_id=f"{self.contract}:signed", contract_event_type="ContractSigned", caller=self.caller)
		refused = self.receive(kind="Initial")
		self.assertFalse(refused["ok"])
		self.assertEqual(refused["code"], "BUDGET_INVALID_STATE")
		self.assertEqual(frappe.db.count("Contract Funding Request", {"contract": self.contract}), 0)

	def test_a_completed_request_is_not_raised_again(self):
		self.cover("600000.00")  # already covered exactly
		done = self.receive()
		self.assertEqual(done["request"]["status"], "Completed")
		again = self.receive()
		self.assertEqual((again["ok"], again["code"]), (False, "BUDGET_ENTRY_DUPLICATE"))

	def test_only_the_contracts_own_service_may_raise_its_request(self):
		other = service_caller(PRINCIPAL_CONTRACT, reference="CM-SOMEONE-ELSE")
		with self.assertRaises(frappe.PermissionError):
			funding.receive_contract_funding_request({"kind": "Initial", "contract": self.contract, "target_year": self.fy, "currency": "KES"}, "x1", caller=other)
		with self.assertRaises(frappe.PermissionError):
			funding.receive_contract_funding_request({"kind": "Initial", "contract": self.contract, "target_year": self.fy, "currency": "KES"}, "x2", caller=service_caller(PRINCIPAL_REQUISITIONS, reference=self.contract))
		with self.assertRaises(frappe.PermissionError):
			funding.receive_contract_funding_request({"kind": "Initial", "contract": self.contract, "target_year": self.fy, "currency": "KES"}, "x3", caller=None)

	def test_an_additional_request_is_unique_by_its_increment_and_names_its_original_commitment(self):
		original = self.cover("100000.00", status="Closed")
		first = self.receive(kind="Additional", subject_event="INC-1", original_commitment=original, basis=self.basis("30000.00"))
		self.assertTrue(first["created"])
		other_increment = self.receive(kind="Additional", subject_event="INC-2", original_commitment=original, basis=self.basis("20000.00"))
		self.assertNotEqual(first["request"]["id"], other_increment["request"]["id"], "a different legitimate increment is its own request")
		self.assertEqual(first["request"]["coverage_total"], "0.00", "the original commitment is never subtracted from an unrelated increment")
		self.assertEqual(first["request"]["amount_requiring_funding"], "30000.00")
		missing = self.receive(kind="Additional", subject_event="INC-3", original_commitment="", basis=self.basis("1.00"))
		self.assertEqual(missing["code"], "BUDGET_INVALID_STATE")


class TestAMissingOrUnusableBasisDoesNotStopTheRequest(_FundingBase):
	def test_a_request_without_a_basis_waits_and_a_draft_can_still_be_saved(self):
		received = self.receive(basis=None)["request"]
		self.assertEqual((received["status"], received["year_allocation_status"], received["display_status"]), ("Open", "Year allocation required", "Year allocation required"))
		self.assertEqual(received["waiting_for"]["holder"], "Ruth Achieng", "the Finance holder is Contract Management's own, shown not stored")
		prepared = self.prepare(received["id"], rows=[{"budget_line": self.hwd, "amount": ""}], reconciliation="")
		self.assertTrue(prepared["ok"], prepared)
		self.assertEqual(prepared["entry"]["status"], "Draft")
		refused = self.submit(prepared["entry"]["id"])
		self.assertEqual((refused["ok"], refused["code"]), (False, "BUDGET_YEAR_ALLOCATION_REQUIRED"))
		self.assertEqual(self.commitments(), [])

	def test_a_basis_for_another_year_contract_or_currency_is_not_relied_on(self):
		for label, basis in (("another contract", {**self.basis(), "contract": "CM-OTHER"}), ("another year", {**self.basis(), "target_year": "1999-2000"}), ("another currency", {**self.basis(), "currency": "USD"}),
			("no digest", {**self.basis(), "digest": ""}), ("no evidence", {**self.basis(), "evidence": []}), ("no confirmer", {**self.basis(), "confirmers": []}), ("a negative charge", self.basis("-1.00"))):
			with self.subTest(label):
				received = self.receive(basis=basis, identity=f"basis-{label}", kind="Initial", year=self.fy)["request"]
				self.assertNotEqual(received["year_allocation_status"], "Confirmed", label)
				frappe.db.sql("delete from `tabContract Funding Request` where contract = %s", self.contract)

	def test_currency_outside_the_supported_scope_is_a_scope_review_not_a_conversion(self):
		received = self.receive(currency="USD", basis={**self.basis(), "currency": "USD"})["request"]
		self.assertEqual((received["year_allocation_status"], received["display_status"]), ("Scope review required", "This funding is outside the supported scope"))

	def test_the_basis_arriving_later_refreshes_the_same_request(self):
		received = self.receive(basis=None)["request"]
		updated = funding.update_contract_funding_basis(received["scope_key"], self.basis("600000.00"), ["Annual basis 1"], f"upd-{frappe.generate_hash(length=8)}", caller=self.caller)
		self.assertEqual((updated["request"]["id"], updated["request"]["year_allocation_status"], updated["request"]["amount_requiring_funding"]), (received["id"], "Confirmed", "600000.00"))
		self.assertIn(seam.OUTCOME_BASIS_CHANGED, self.receiver.names())


class TestSaveIsNotSubmitAndTheAmountIsNeverTyped(_FundingBase):
	def test_incomplete_preparation_saves_and_moves_no_money(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		before = (self.position(self.hwd), self.position(self.dhi))
		prepared = self.prepare(request["id"], rows=[{"budget_line": self.hwd, "amount": "100000.00"}], reconciliation="")
		self.assertTrue(prepared["ok"], prepared)
		self.assertEqual((self.position(self.hwd), self.position(self.dhi)), before)
		refused = self.submit(prepared["entry"]["id"])
		self.assertFalse(refused["ok"])
		self.assertIn("reconciliation", refused["errors"])

	def test_rows_that_do_not_add_up_to_the_calculated_amount_are_refused_with_the_difference(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		entry = self.prepare(request["id"], rows=self.rows("300000.00", "199999.00"))["entry"]
		refused = self.submit(entry["id"])
		self.assertEqual((refused["code"], refused["required"], refused["rows_total"], refused["difference"]), ("BUDGET_ENTRY_ROWS_MISMATCH", "500000.00", "499999.00", "-1.00"))

	def test_a_row_must_be_an_eligible_line_of_the_target_year(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		other_fy, other_budget, other_v = self._active(fiscal_year=self._fresh_fy())
		foreign = self._line(other_v, HWD)
		result = self.prepare(request["id"], rows=[{"budget_line": foreign, "amount": "500000.00"}])
		self.assertFalse(result["ok"])
		self.assertTrue(any("not in the Budget for" in message for message in result["errors"].values()))

	def test_a_total_override_is_not_a_field(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		entry = self.prepare(request["id"])["entry"]
		self.assertEqual((entry["amount_requiring_funding"], entry["confirmed_charge"], entry["coverage_total"]), ("500000.00", "600000.00", "100000.00"))
		again = self.prepare(request["id"], entry=entry["id"])
		self.assertEqual(again["entry"]["amount_requiring_funding"], "500000.00", "the amount is the system's, whatever the payload says")

	def test_the_officer_role_is_required_to_prepare_and_submit(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		with self.assertRaises(ResponsibilityError):
			self.prepare(request["id"], user=self.approver)
		entry = self.prepare(request["id"])["entry"]
		with self.assertRaises(ResponsibilityError):
			self.submit(entry["id"], user=self.approver)


class TestApprovalCreatesEveryCommitmentOrNone(_FundingBase):
	def test_approval_funds_the_new_charge_once_on_two_lines_and_publishes_the_outcome(self):
		request, entry = self.fixture()
		hwd_before, dhi_before = self.position(self.hwd), self.position(self.dhi)  # with the existing 100,000 already in Committed
		decided = self.decide(entry)
		self.assertTrue(decided["ok"], decided)
		created = [c for c in self.commitments() if c.origin == "Existing-contract entry" and c.entry_row.startswith(entry)]
		self.assertEqual(sorted((c.budget_line == self.hwd, float(c.current_amount)) for c in created), [(False, 200000.0), (True, 300000.0)])
		self.assertTrue(all(c.reservation in (None, "") and c.status == "Active" for c in created))
		self.assertEqual(self.position(self.hwd)["committed"], hwd_before["committed"] + 300000)
		self.assertEqual(self.position(self.hwd)["available"], hwd_before["available"] - 300000)
		self.assertEqual(self.position(self.dhi)["committed"], dhi_before["committed"] + 200000)
		self.assertEqual(self.position(self.dhi)["reserved"], dhi_before["reserved"], "no reservation is created or touched")
		summary = frappe.get_doc("Contract Funding Request", request)
		self.assertEqual((summary.status, summary.outcome), ("Completed", seam.OUTCOME_APPROVED))
		self.assertEqual(self.receiver.names()[-1], seam.OUTCOME_APPROVED)
		self.assertEqual(sum(float(c["amount"]) for c in self.receiver.outcomes[-1]["detail"]["commitments"]), 500000.0)
		ledger = frappe.get_all("Budget Audit Event", filters={"budget": self.budget, "event_type": "Existing-contract commitment recorded"}, fields=["amount", "before_available", "after_available", "budget_line"])
		self.assertEqual(sorted(float(e.amount) for e in ledger), [200000.0, 300000.0])
		self.assertTrue(all(float(e.before_available) - float(e.after_available) == float(e.amount) for e in ledger))

	def test_after_approval_the_entry_is_immutable_and_cannot_be_decided_again(self):
		request, entry = self.fixture()
		self.assertTrue(self.decide(entry)["ok"])
		again = self.decide(entry)
		self.assertEqual((again["ok"], again["code"]), (False, "BUDGET_INVALID_STATE"))
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 3)
		edited = self.prepare(request, entry=entry)
		self.assertEqual((edited["ok"], edited["code"]), (False, "BUDGET_INVALID_STATE"))

	def test_a_replay_of_the_same_decision_creates_nothing_twice(self):
		request, entry = self.fixture()
		self.assertTrue(self.decide(entry, key="decide-once")["ok"])
		replay = self.decide(entry, key="decide-once")
		self.assertTrue(replay.get("replayed"))
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 3)
		self.assertEqual(self.receiver.names().count(seam.OUTCOME_APPROVED), 1)

	def test_a_shortfall_on_one_line_creates_no_commitment_and_returns_the_entry_with_the_grouped_shortfall(self):
		request, entry = self.fixture()
		# another demand takes most of the DHI line after the entry was submitted
		self._reserve(self.dhi, 99_900_000, ref="REQ-TAKE-DHI")
		before = (len(self.commitments()), self.position(self.hwd), self.position(self.dhi))
		result = self.decide(entry)
		self.assertEqual((result["ok"], result["code"]), (False, "BUDGET_INSUFFICIENT_FUNDS"))
		self.assertEqual([(s["budget_line"], s["shortfall"]) for s in result["shortfalls"]], [(self.dhi, "100000.00")])
		self.assertEqual((len(self.commitments()), self.position(self.hwd), self.position(self.dhi)), before, "no partial commitments")
		self.assertEqual(frappe.get_doc("Existing Contract Commitment Entry", entry).status, "Returned")
		self.assertEqual(frappe.get_doc("Contract Funding Request", request).status, "Open", "the request stays open for correction")
		self.assertEqual(self.receiver.names()[-1], seam.OUTCOME_SHORTFALL)
		summary = funding.summary(frappe.get_doc("Contract Funding Request", request))
		self.assertEqual((summary["display_status"], summary["holder"]), ("Funding shortfall", "Budget Officer"))

	def test_a_shortfall_is_also_found_when_the_entry_is_submitted(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		self._reserve(self.dhi, 99_900_000, ref="REQ-TAKE-DHI-2")
		entry = self.prepare(request["id"])["entry"]
		refused = self.submit(entry["id"])
		self.assertEqual((refused["ok"], refused["code"]), (False, "BUDGET_INSUFFICIENT_FUNDS"))
		self.assertEqual(frappe.get_doc("Existing Contract Commitment Entry", entry["id"]).status, "Draft")

	def test_the_decision_rechecks_the_target_budget_is_still_active(self):
		request, entry = self.fixture()
		frappe.db.sql("update `tabProcurement Budget Version` set status = 'Closed' where budget = %s and status = 'Active'", self.budget)
		try:
			result = self.decide(entry)
		finally:
			frappe.db.sql("update `tabProcurement Budget Version` set status = 'Active' where budget = %s and status = 'Closed'", self.budget)
		self.assertFalse(result["ok"])
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 1)


class TestTheApproverIsIndependent(_FundingBase):
	def test_the_preparer_cannot_approve_even_holding_both_responsibilities(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		entry = self.prepare(request["id"], user=self.dual)["entry"]
		self.assertTrue(self.submit(entry["id"], user=self.dual)["ok"])
		with self.assertRaises(ResponsibilityError):
			self.decide(entry["id"], user=self.dual)
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 1)
		self._as(self.dual)
		view = entries.get_contract_funding(request["id"])
		self.assertTrue(view["actions"]["blocked"], "the screen explains that another Approver must decide")
		self.assertFalse(view["actions"]["approve"])

	def test_a_finance_confirmer_of_the_relied_on_basis_cannot_approve(self):
		self.cover("100000.00")
		request = self.receive(basis=self.basis(confirmers=[{"user": self.approver, "assignment": "URA-FIN-9", "at": "2026-10-16 09:00:00"}]))["request"]
		entry = self.prepare(request["id"])["entry"]
		self.assertTrue(self.submit(entry["id"])["ok"])
		with self.assertRaises(ResponsibilityError):
			self.decide(entry["id"])
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 1)

	def test_one_of_several_confirmers_is_enough_to_block(self):
		self.cover("100000.00")
		confirmers = [{"user": self.confirmer, "assignment": "A", "at": "2026-10-16 09:00:00"}, {"user": self.approver, "assignment": "B", "at": "2026-10-16 09:05:00"}]
		request = self.receive(basis=self.basis(confirmers=confirmers))["request"]
		entry = self.prepare(request["id"])["entry"]
		self.submit(entry["id"])
		with self.assertRaises(ResponsibilityError):
			self.decide(entry["id"])

	def test_unclear_attribution_blocks_approval(self):
		request, entry = self.fixture()
		frappe.db.set_value("Existing Contract Commitment Entry", entry, "confirmers_json", "[]")
		with self.assertRaises(ResponsibilityError):
			self.decide(entry)

	def test_an_independent_approver_decides_without_another_stage(self):
		request, entry = self.fixture()
		decided = self.decide(entry)
		self.assertTrue(decided["ok"])
		stored = frappe.get_doc("Existing Contract Commitment Entry", entry)
		self.assertEqual((stored.status, stored.decided_by, stored.prepared_by, stored.submitted_by), ("Approved", self.approver, self.officer, self.officer))
		self.assertTrue(stored.decision_assignment, "the assignment exercised is recorded")


class TestAChangedBasisOrCoverageIsReturnedNeverSilentlyRecalculated(_FundingBase):
	def test_a_changed_funding_basis_after_submission_cannot_be_approved(self):
		request, entry = self.fixture()
		scope = frappe.get_doc("Contract Funding Request", request).scope_key
		funding.update_contract_funding_basis(scope, self.basis("650000.00"), ["Annual basis 2"], f"upd-{frappe.generate_hash(length=8)}", caller=self.caller)
		result = self.decide(entry)
		self.assertEqual((result["ok"], result["code"]), (False, "BUDGET_STALE_REVISION"))
		self.assertIn("The opening review has changed", result["errors"]["entry"])
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 1)
		view = entries.get_contract_funding(request)
		self.assertTrue(view["entry"]["basis_stale"])
		self.assertFalse(view["actions"].get("approve"))

	def test_the_approver_returns_it_and_the_officer_resubmits_against_the_new_basis(self):
		request, entry = self.fixture()
		scope = frappe.get_doc("Contract Funding Request", request).scope_key
		funding.update_contract_funding_basis(scope, self.basis("650000.00"), ["Annual basis 2"], f"upd-{frappe.generate_hash(length=8)}", caller=self.caller)
		returned = self.decide(entry, "Return", reason="Confirm the source allocation against the new basis.")
		self.assertTrue(returned["ok"])
		self.assertEqual(returned["entry"]["status"], "Returned")
		self.assertEqual(self.receiver.names()[-1], seam.OUTCOME_RETURNED)
		fresh = self.prepare(request, entry=entry, rows=self.rows("300000.00", "250000.00"))
		self.assertEqual(fresh["entry"]["amount_requiring_funding"], "550000.00")
		self.assertTrue(self.submit(entry)["ok"])
		self.assertTrue(self.decide(entry)["ok"])
		self.assertEqual(sum(float(c.current_amount) for c in self.commitments(origin="Existing-contract entry")), 650000.0)

	def test_coverage_that_changed_after_submission_cannot_be_approved(self):
		request, entry = self.fixture()
		self.cover("25000.00", line=self.dhi)
		result = self.decide(entry)
		self.assertEqual((result["ok"], result["code"]), (False, "BUDGET_STALE_REVISION"))

	def test_a_return_needs_a_reason_and_keeps_the_request_open(self):
		request, entry = self.fixture()
		short = self.decide(entry, "Return", reason="no")
		self.assertEqual((short["ok"], short["code"]), (False, "BUDGET_EVIDENCE_REQUIRED"))
		returned = self.decide(entry, "Return", reason="Confirm the source allocation")
		self.assertTrue(returned["ok"])
		self.assertEqual(frappe.get_doc("Contract Funding Request", request).status, "Open")
		self.assertEqual(frappe.get_doc("Existing Contract Commitment Entry", entry).decision_reason, "Confirm the source allocation")
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 1)


class TestNoNewEntryIsNeededWhenBudgetAlreadyCoversTheCharge(_FundingBase):
	def test_full_prior_coverage_completes_the_request_with_no_entry_commitment_or_ledger_event(self):
		self.cover("600000.00")
		events_before = frappe.db.count("Budget Audit Event", {"budget": self.budget, "event_type": ["in", ["Existing-contract commitment recorded", "Existing-contract entry approved"]]})
		done = self.receive()["request"]
		self.assertEqual((done["status"], done["outcome"], done["display_status"]), ("Completed", seam.OUTCOME_ALREADY_COVERED, "Already covered — no new entry required"))
		self.assertEqual(frappe.db.count("Existing Contract Commitment Entry", {"request": done["id"]}), 0)
		self.assertEqual(len(self.commitments()), 1)
		self.assertEqual(frappe.db.count("Budget Audit Event", {"budget": self.budget, "event_type": ["in", ["Existing-contract commitment recorded", "Existing-contract entry approved"]]}), events_before)
		self.assertEqual(self.receiver.names(), [seam.OUTCOME_ALREADY_COVERED])
		self.assertEqual(self.receiver.outcomes[0]["detail"]["coverage_total"], "600000.00")

	def test_a_zero_charge_for_the_year_is_its_own_outcome(self):
		done = self.receive(basis=self.basis("0.00"))["request"]
		self.assertEqual((done["status"], done["outcome"], done["display_status"]), ("Completed", seam.OUTCOME_NO_CHARGE, "No charge to this year"))
		self.assertEqual(self.commitments(), [])

	def test_neither_outcome_authorises_spending_or_creates_a_reservation(self):
		self.cover("600000.00")
		before = (self.position(self.hwd), self.position(self.dhi))
		self.receive()
		self.assertEqual((self.position(self.hwd), self.position(self.dhi)), before)


class TestDeclineWithdrawAndReopen(_FundingBase):
	def test_the_officer_declines_with_a_reason_and_unapproved_preparation_is_abandoned(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		entry = self.prepare(request["id"])["entry"]
		self._as(self.officer)
		short = funding.decline_contract_funding_request({"request": request["id"], "reason": "no", "idempotency_key": "d1"})
		self.assertEqual(short["code"], "BUDGET_EVIDENCE_REQUIRED")
		declined = funding.decline_contract_funding_request({"request": request["id"], "reason": "The funding mapping must be corrected in the contract first.", "idempotency_key": f"d-{frappe.generate_hash(length=6)}"})
		self.assertTrue(declined["ok"])
		self.assertEqual((frappe.get_doc("Contract Funding Request", request["id"]).status, frappe.get_doc("Existing Contract Commitment Entry", entry["id"]).status), ("Declined", "Superseded"))
		self.assertEqual(self.receiver.names()[-1], seam.OUTCOME_DECLINED)
		self.assertEqual(len(self.commitments()), 1, "no commitment changed")

	def test_only_contract_management_withdraws_and_only_before_funding(self):
		request, entry = self.fixture()
		scope = frappe.get_doc("Contract Funding Request", request).scope_key
		withdrawn = funding.withdraw_contract_funding_request(scope, "The contract is being corrected.", f"w-{frappe.generate_hash(length=6)}", caller=self.caller)
		self.assertTrue(withdrawn["ok"])
		self.assertEqual(frappe.get_doc("Existing Contract Commitment Entry", entry).status, "Superseded")
		self.assertEqual(self.receiver.names()[-1], seam.OUTCOME_WITHDRAWN)
		self.assertEqual(len(self.commitments(origin="Existing-contract entry")), 1)
		later = funding.withdraw_contract_funding_request(scope, "again", f"w2-{frappe.generate_hash(length=6)}", caller=self.caller)
		self.assertEqual(later["code"], "BUDGET_INVALID_STATE")

	def test_a_declined_request_raised_again_is_the_same_lineage_reopened_with_a_new_entry_version(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		first = self.prepare(request["id"])["entry"]
		self._as(self.officer)
		funding.decline_contract_funding_request({"request": request["id"], "reason": "Corrected in the contract first.", "idempotency_key": f"d-{frappe.generate_hash(length=6)}"})
		again = self.receive()
		self.assertEqual((again["created"], again["reopened"], again["request"]["id"], again["request"]["status"]), (False, True, request["id"], "Open"))
		second = self.prepare(request["id"])["entry"]
		self.assertNotEqual(first["id"], second["id"])
		self.assertEqual(second["version"], 2)
		self.assertEqual(frappe.get_doc("Existing Contract Commitment Entry", first["id"]).status, "Superseded", "the earlier attempt is retained")


class TestOutcomesAreOrderedAndNeverLost(_FundingBase):
	def test_a_receiver_that_is_down_leaves_the_outcome_pending_and_the_sweep_delivers_it_in_order(self):
		self.cover("100000.00")
		request = self.receive()["request"]
		self.receiver.down = True
		entry = self.prepare(request["id"])["entry"]
		self.assertTrue(self.submit(entry["id"])["ok"], "what Budget decided does not depend on the receiver")
		pending = frappe.get_all("Contract Funding Outcome", filters={"request": request["id"], "delivered_at": ["is", "not set"]}, fields=["sequence", "outcome"], order_by="sequence asc")
		self.assertEqual([p.outcome for p in pending], [seam.OUTCOME_ENTRY_SUBMITTED])
		self.assertEqual(self.receiver.names(), [seam.OUTCOME_ENTRY_SUBMITTED], "only the 'ready for Budget' outcome, sent while the receiver was up, has arrived")
		self.receiver.down = False
		self.assertGreaterEqual(funding.deliver_pending(request["id"]), 1)
		self.assertEqual([o["detail"].get("stage") for o in self.receiver.outcomes], ["Preparing", "Awaiting approval"])
		self.assertEqual(funding.deliver_pending(request["id"]), 0)

	def test_an_earlier_outcome_that_is_not_acknowledged_holds_back_the_later_ones(self):
		request, entry = self.fixture()
		arrived = len(self.receiver.outcomes)
		self.receiver.down = True
		self.assertTrue(self.decide(entry)["ok"])
		self.assertEqual(len(self.receiver.outcomes), arrived, "nothing arrived while the receiver was down")
		self.receiver.down = False
		funding.deliver_pending(request)
		sequences = [o["sequence"] for o in self.receiver.outcomes]
		self.assertEqual(sequences, sorted(sequences))
		self.assertEqual(self.receiver.names()[-1], seam.OUTCOME_APPROVED)


class TestAnnualFundingOfALaterYear(_FundingBase):
	"""The 300,000 / 400,000 / 200,000 contract: year 2 is funded for 400,000 on its own request and entry, without touching year 1 and without reopening anything."""

	def test_year_two_is_funded_on_its_own_lineage_and_year_one_is_untouched(self):
		year1 = self.cover("300000.00")  # year 1 is funded and stays as it was
		fy2, budget2, v2 = self._active(fiscal_year=self._fresh_fy())
		hwd2 = self._line(v2, HWD)
		before_year1 = self.position(self.hwd)
		received = self.receive(kind="Annual", year=fy2, basis=self.basis("400000.00", year=fy2))["request"]
		self.assertEqual((received["coverage_total"], received["amount_requiring_funding"]), ("0.00", "400000.00"), "year 1's commitment is neither subtracted from year 2 nor released to fund it")
		self._as(self.officer)
		entry = entries.record_existing_contract_commitment_entry({"request": received["id"], "rows": [{"budget_line": hwd2, "amount": "400000.00"}], "reconciliation": RECONCILIATION,
			"idempotency_key": f"rec-{frappe.generate_hash(length=8)}"})["entry"]
		self.assertTrue(self.submit(entry["id"])["ok"])
		self.assertTrue(self.decide(entry["id"])["ok"])
		self.assertEqual(self.position(self.hwd), before_year1, "year 1's line is exactly as it was")
		self.assertEqual(frappe.db.get_value("Procurement Commitment", year1, ["current_amount", "status"], as_dict=True), {"current_amount": 300000.0, "status": "Active"})
		self.assertEqual(float(self.position(hwd2)["committed"]), 400000.0)

	def test_a_second_request_for_year_two_is_the_same_request_never_a_second_charge(self):
		fy2, budget2, v2 = self._active(fiscal_year=self._fresh_fy())
		first = self.receive(kind="Annual", year=fy2, basis=self.basis("400000.00", year=fy2))["request"]
		again = self.receive(kind="Annual", year=fy2, basis=self.basis("400000.00", year=fy2), identity=f"another-{frappe.generate_hash(length=6)}")
		self.assertEqual((again["created"], again["request"]["id"]), (False, first["id"]))
		self.assertEqual(frappe.db.count("Contract Funding Request", {"contract": self.contract}), 1)

	def test_a_year_with_insufficient_funds_is_refused_without_partial_posting(self):
		fy2, budget2, v2 = self._active(fiscal_year=self._fresh_fy(), hwd=100_000)
		hwd2 = self._line(v2, HWD)
		received = self.receive(kind="Annual", year=fy2, basis=self.basis("400000.00", year=fy2))["request"]
		self._as(self.officer)
		entry = entries.record_existing_contract_commitment_entry({"request": received["id"], "rows": [{"budget_line": hwd2, "amount": "400000.00"}], "reconciliation": RECONCILIATION,
			"idempotency_key": f"rec-{frappe.generate_hash(length=8)}"})["entry"]
		refused = self.submit(entry["id"])
		self.assertEqual((refused["ok"], refused["code"]), (False, "BUDGET_INSUFFICIENT_FUNDS"))
		self.assertEqual(self.commitments(), [])

	def test_a_later_year_with_no_active_budget_can_be_requested_but_nothing_in_it_is_funded(self):
		year3 = self._fresh_fy()  # exists as a Fiscal Year; no Budget has been registered for it
		received = self.receive(kind="Annual", year=year3, basis=self.basis("200000.00", year=year3))["request"]
		self.assertEqual((received["status"], received["display_status"]), ("Open", "Ready to prepare"))
		self._as(self.officer)
		prepared = entries.record_existing_contract_commitment_entry({"request": received["id"], "rows": [{"budget_line": self.hwd, "amount": "200000.00"}], "reconciliation": RECONCILIATION,
			"idempotency_key": f"rec-{frappe.generate_hash(length=8)}"})
		self.assertFalse(prepared["ok"], "a line of another year's Budget cannot take year 3's funding")
		self.assertEqual(self.commitments(), [])


class TestACorrectionRequestHearsTheResult(_FundingBase):
	"""BUD-CHG-001 v1.16 4.11, 8.6 and CM-AC-74: Contract Management may ask for the correction of a Closed commitment, citing the record that shows the error. Budget's Officer records it, a different Approver
	decides it, and the request hears the result; a correction an Officer starts alone has no request and nobody is made to wait for one."""

	def ask(self, closed, reference="CM-CORR-1"):
		return self.receive(kind="Correction", subject_event=reference, original_commitment=closed, basis=None, evidence=["Final obligation review 1"])["request"]

	def record(self, closed, reference="CM-CORR-1", amount=40000):
		self._as(self.officer)
		return corrections.record_commitment_correction({"commitment": closed, "new_amount": amount, "reason": "The final obligation included work never performed.", "evidence": ["Final obligation review 1", "Closure 1"],
			"contract_reference": reference, "idempotency_key": f"cor-{frappe.generate_hash(length=8)}"})["correction"]

	def test_a_correction_request_needs_a_closed_commitment_it_names_and_is_not_a_funding_year(self):
		closed = self.cover("100000.00", status="Closed")
		request = self.ask(closed)
		self.assertEqual((request["kind"], request["status"], request["year_allocation_status"], request["display_status"]), ("Correction", "Open", "Confirmed", "Ready to prepare"))
		self.assertEqual(self.receiver.names(), [], "nothing is announced as ready for an entry: a correction has none")
		missing = self.receive(kind="Correction", subject_event="CM-CORR-2", original_commitment="", basis=None)
		self.assertEqual(missing["code"], "BUDGET_INVALID_STATE")

	def test_an_approved_correction_closes_the_request_and_tells_contract_management(self):
		closed = self.cover("100000.00", status="Closed")
		request = self.ask(closed)
		correction = self.record(closed)
		decided = self.decide_correction(correction["id"])
		self.assertTrue(decided["ok"], decided)
		self.assertEqual((frappe.get_doc("Contract Funding Request", request["id"]).status, self.receiver.names()), ("Completed", [seam.OUTCOME_CORRECTION_APPROVED]))
		detail = self.receiver.outcomes[-1]["detail"]
		self.assertEqual((detail["before_amount"], detail["after_amount"]), (100000.0, 40000.0))

	def test_a_returned_correction_leaves_the_request_open_for_a_corrected_record(self):
		closed = self.cover("100000.00", status="Closed")
		request = self.ask(closed)
		correction = self.record(closed)
		returned = self.decide_correction(correction["id"], "Return", "Evidence does not show the amount.")
		self.assertTrue(returned["ok"])
		self.assertEqual((frappe.get_doc("Contract Funding Request", request["id"]).status, self.receiver.names()), ("Open", [seam.OUTCOME_CORRECTION_RETURNED]))
		again = self.record(closed, amount=55000)
		self.assertTrue(self.decide_correction(again["id"])["ok"])
		self.assertEqual(self.receiver.names(), [seam.OUTCOME_CORRECTION_RETURNED, seam.OUTCOME_CORRECTION_APPROVED])

	def test_a_correction_the_officer_starts_alone_sends_nothing(self):
		closed = self.cover("100000.00", status="Closed")
		correction = self.record(closed, reference="OFFICER-STARTED")
		self.assertTrue(self.decide_correction(correction["id"])["ok"])
		self.assertEqual(self.receiver.outcomes, [])
		self.assertEqual(frappe.db.count("Contract Funding Request", {"contract": self.contract}), 0)

	def decide_correction(self, correction, decision="Approve", reason=""):
		self._as(self.approver)
		return corrections.decide_commitment_correction({"correction": correction, "decision": decision, "reason": reason, "idempotency_key": f"dc-{frappe.generate_hash(length=8)}"})
