# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-116 / AUD-XC-117 / AUD-XC-129 / AUD-XC-133 (Budget side) — Budget
money is exact: positions, floors, Needs Attention and affordability compare
`Decimal`s with no epsilon; money inputs are exact amounts at the currency's
scale (NaN/Infinity, exponent notation and excess scale fail typed, nothing
rounded); the scale comes from the currency, not a constant."""

from __future__ import annotations

from decimal import Decimal

import frappe

from kentender_budget.services import budget_commitment_contracts as commitment_svc
from kentender_budget.services import budget_contracts as contracts
from kentender_budget.services import budget_line_contracts as lines_svc
from kentender_budget.services import budget_money as money
from kentender_budget.services import budget_readiness_contracts as readiness
from kentender_budget.services.budget_service_principal import PRINCIPAL_BUDGET, PRINCIPAL_CONTRACT, service_caller
from kentender_budget.tests.test_bud_chg_001_phase3_lifecycle import FUNDING_SOURCE
from kentender_budget.tests.test_budget_service_principal import _PrincipalBase
from kentender_budget.utils.version_stamp import stamped

MONEY_CODE = "BUDGET_MONEY_PRECISION_INVALID"


def _title(ctx) -> str | None:
	"""The typed code of a raised `frappe.throw` (carried on the message log)."""
	titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
	return titles[-1] if titles else None


class _MoneyBase(_PrincipalBase):
	def _contract(self, reference: str):
		return service_caller(PRINCIPAL_CONTRACT, reference=reference)

	def _baseline(self, line_amount, other=1):
		budget, version = self._create_active_baseline(dhi_amount=line_amount, hwd_amount=other)
		line = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": version, "title": "DHI test line"}, "budget_line")
		return budget, version, line

	def _convert(self, reservation: str, amount, contract: str):
		self._as("Administrator")
		return commitment_svc.convert_reservation(
			reservation=reservation, contract=contract, amount=amount, idempotency_key=self._key("cv"),
			contract_event_id=f"{contract}:signed", contract_event_type="ContractSigned", caller=self._contract(contract),
		)

	def _raises_money(self, fn):
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			fn()
		self.assertEqual(_title(None), MONEY_CODE)


class TestExactPositions(_MoneyBase):
	def test_a_fully_subscribed_line_is_exactly_zero_available_and_not_needs_attention(self):
		"""AUD-XC-116 — 843,171,926.93 = 535,955,290.08 reserved + 307,216,636.85
		committed: available is exactly 0.00 (float arithmetic gave -5.96e-08) and
		revalidation must not flag a reservation on the line."""
		_budget, _version, line = self._baseline(Decimal("843171926.93"))
		reserved = self._reserve(line, "535955290.08", reference="REQ-EXACT-1", plan_item="TEST-PPI-EX1")
		committed = self._reserve(line, "307216636.85", reference="REQ-EXACT-2", plan_item="TEST-PPI-EX2")
		self._convert(committed, "307216636.85", f"CTR-EX-{self.suffix}")

		position = contracts._line_position_exact(line, frappe.get_doc("Procurement Budget Line Version", {"budget_line": line}))
		self.assertEqual(position["available"], Decimal("0.00"))
		self.assertEqual(position["reserved"], Decimal("535955290.08"))
		self.assertEqual(position["committed"], Decimal("307216636.85"))
		self.assertEqual(contracts._line_position(line, frappe.get_doc("Procurement Budget Line Version", {"budget_line": line}))["available"], 0.0)

		result = commitment_svc.revalidate_reservations([reserved], "EV-EXACT", "BudgetRevalidation", self._key("rv"), caller=service_caller(PRINCIPAL_BUDGET, reference="BUD-EXACT"))
		self.assertEqual(result["reservations"][0]["status"], "Active", result)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reserved, "status"), "Active")

	def test_the_floor_admits_a_line_set_to_exactly_reserved_plus_committed(self):
		"""AUD-XC-116 — 47,235,303.96 + 650,184,912.59 = 697,420,216.55 exactly
		(float sum 697420216.5500001): a successor setting the line to exactly that
		amount is not a floor breach."""
		budget, version, line = self._baseline(Decimal("800000000.00"), Decimal("1.00"))
		self._reserve(line, "47235303.96", reference="REQ-EXACT-3", plan_item="TEST-PPI-EX3")
		big = self._reserve(line, "650184912.59", reference="REQ-EXACT-4", plan_item="TEST-PPI-EX4")
		self._convert(big, "650184912.59", f"CTR-EX2-{self.suffix}")

		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Reduction"})
		self.assertTrue(succ["ok"], succ)
		new = succ["version"]["id"]
		self._track("Procurement Budget Version", new)
		total = Decimal("697420216.55") + Decimal("1.00")
		saved = contracts.save_budget_version_draft(stamped({"budget_version": new, "approval_reference": f"EX-{self.suffix}", "approval_date": frappe.utils.add_days(frappe.utils.nowdate(), -2), "authorised_total": total, "revision_type": "Reduction"}))
		self.assertTrue(saved["ok"], saved)
		lines = lines_svc.save_budget_lines_draft(stamped({"budget_version": new, "lines": [{"budget_line": line, "approved_amount": Decimal("697420216.55")}]}))
		self.assertTrue(lines["ok"], lines)
		issues = readiness._evaluate_readiness(frappe.get_doc("Procurement Budget Version", new))
		self.assertEqual([i["code"] for i in issues if "floor_breach" in i["code"]], [], issues)
		self._as("Administrator")

		# one cent below the floor is still refused, with the exact shortfall
		self._as(self.officer)
		lines = lines_svc.save_budget_lines_draft(stamped({"budget_version": new, "lines": [{"budget_line": line, "approved_amount": Decimal("697420216.54")}]}))
		self.assertTrue(lines["ok"], lines)
		issues = readiness._evaluate_readiness(frappe.get_doc("Procurement Budget Version", new))
		breach = [i for i in issues if "floor_breach" in i["code"]]
		self.assertEqual(len(breach), 1, issues)
		self.assertEqual(Decimal(str(breach[0]["detail"]["shortfall"])), Decimal("0.01"))
		self._as("Administrator")

	def test_planned_totals_are_compared_exactly(self):
		"""AUD-XC-116 — a planned total equal to the approved amount is within; one
		cent over is not (no epsilon either way)."""
		_budget, version, line = self._baseline(Decimal("100000000.00"))
		fy = frappe.db.get_value("Procurement Budget", frappe.db.get_value("Procurement Budget Version", version, "budget"), "fiscal_year")
		self._as(self.officer)
		exact = lines_svc.check_plan_affordability(fy, {line: "100000000.00"})
		self.assertTrue(exact["within_approved"], exact)
		over = lines_svc.check_plan_affordability(fy, {line: "100000000.01"})
		self.assertFalse(over["within_approved"])
		self.assertEqual(over["failing_lines"][0]["excess"], 0.01)
		self._as("Administrator")


class TestExactInputs(_MoneyBase):
	BAD = ("nan", "NaN", "inf", "-Infinity", "1e3", "1.005", "12.345678", "", " ", "abc", "1,000.00", float("nan"), float("inf"), True, None, "9" * 13)

	def test_parse_money_accepts_exact_amounts_and_refuses_the_rest(self):
		for good, expected in (("100.00", Decimal("100.00")), ("0.01", Decimal("0.01")), (5, Decimal("5.00")), (Decimal("12.5"), Decimal("12.50")), (1250000.5, Decimal("1250000.50")), ("999999999999.99", Decimal("999999999999.99"))):
			with self.subTest(good=good):
				self.assertEqual(money.parse_money(good), expected)
		for bad in self.BAD:
			with self.subTest(bad=bad):
				frappe.local.message_log = []
				with self.assertRaises(frappe.ValidationError):
					money.parse_money(bad)
				self.assertEqual(_title(None), MONEY_CODE)
		self.assertEqual(money.parse_money("0", allow_zero=True), Decimal("0.00"))
		with self.assertRaises(frappe.ValidationError):
			money.parse_money("0")
		with self.assertRaises(frappe.ValidationError):
			money.parse_money("-1")

	def test_a_line_save_refuses_a_malformed_amount_with_a_typed_code_and_writes_nothing(self):
		budget, version, line = self._baseline(Decimal("100000000.00"))
		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		new = succ["version"]["id"]
		self._track("Procurement Budget Version", new)
		before = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": new, "budget_line": line}, "approved_amount")
		for bad in ("nan", "inf", "1e3", "60000000.004", "60000000.123456789"):
			with self.subTest(bad=bad):
				result = lines_svc.save_budget_lines_draft(stamped({"budget_version": new, "lines": [{"budget_line": line, "approved_amount": bad}]}))
				self.assertFalse(result["ok"], result)
				self.assertEqual(result["code"], MONEY_CODE)
				self.assertIn("lines.0.approved_amount", result["errors"])
				self.assertEqual(frappe.db.get_value("Procurement Budget Line Version", {"budget_version": new, "budget_line": line}, "approved_amount"), before)
		self._as("Administrator")

	def test_the_approved_allocation_must_be_an_exact_amount(self):
		self._as(self.officer)
		for bad in ("nan", "inf", "1e3", "100.005", "9" * 13):
			with self.subTest(bad=bad):
				result = contracts.save_budget_version_draft({"fiscal_year": self._fresh_fy(), "approval_reference": f"IN-{self.suffix}", "approval_date": frappe.utils.add_days(frappe.utils.nowdate(), -2), "authorised_total": bad})
				self.assertFalse(result["ok"], result)
				self.assertIn("authorised_total", result["errors"])
		self._as("Administrator")

	def test_two_lines_that_each_overshoot_by_less_than_a_cent_do_not_reconcile(self):
		"""AUD-XC-117 reproduction — authorised 100,000,000.00 with lines
		60,000,000.004 and 40,000,000.004 (difference -0.008) used to pass
		`abs(diff) < 0.01`: the amounts are refused at the door, and stored legacy
		values of that shape no longer reconcile."""
		self.assertTrue(readiness._reconcile(Decimal("100000000.00"), Decimal("100000000.00"))["match"])
		stored_amount = readiness._reconcile(Decimal("100000000.00"), 100000000.008)
		self.assertFalse(stored_amount["match"])
		self.assertEqual(stored_amount["amount_over_allocation"], 0.008)

	def test_release_convert_and_adjust_refuse_malformed_amounts_before_any_effect(self):
		budget, version, line = self._baseline(Decimal("100000000.00"))
		reservation = self._reserve(line, "40000000.00", reference="REQ-EXACT-5", plan_item="TEST-PPI-EX5")
		contract = f"CTR-EX3-{self.suffix}"
		self._convert(reservation, "10000000.00", contract)
		commitment = frappe.db.get_value("Procurement Commitment", {"reservation": reservation}, "name")
		caller = self._contract(contract)
		self._as("Administrator")
		for bad in ("nan", "30000000.005", "1e7"):
			with self.subTest(bad=bad):
				self._raises_money(lambda: commitment_svc.release_reservation(reservation, bad, "EV", "ContractUnusedAmount", self._key("rl"), caller=caller))
				self._raises_money(lambda: commitment_svc.convert_reservation(reservation, contract, bad, self._key("cv"), contract_event_id="E", contract_event_type="T", caller=caller))
				self._raises_money(lambda: commitment_svc.adjust_commitment(commitment, bad, "EV", "ContractVariation", self._key("aj"), caller=caller))
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 30_000_000)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "current_amount"), 10_000_000)

	def test_there_is_no_tolerance_on_conversion_or_release(self):
		"""AUD-XC-117 — over-conversion by 0.00005 used to pass `> remaining + 0.0001`.
		It is now an input error; one cent over is the typed over-remainder error."""
		budget, version, line = self._baseline(Decimal("100000000.00"))
		reservation = self._reserve(line, "40000000.00", reference="REQ-EXACT-6", plan_item="TEST-PPI-EX6")
		contract = f"CTR-EX4-{self.suffix}"
		caller = self._contract(contract)
		self._as("Administrator")
		self._raises_money(lambda: commitment_svc.convert_reservation(reservation, contract, "40000000.00005", self._key("cv"), contract_event_id="E", contract_event_type="T", caller=caller))
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			commitment_svc.convert_reservation(reservation, contract, "40000000.01", self._key("cv"), contract_event_id="E", contract_event_type="T", caller=caller)
		self.assertEqual(_title(None), "BUDGET_CONVERSION_EXCEEDS_REMAINDER")
		converted = commitment_svc.convert_reservation(reservation, contract, "40000000.00", self._key("cv"), contract_event_id="E", contract_event_type="T", caller=caller)
		self.assertEqual(converted["reservation"]["status"], "Converted")
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 0)


class TestCurrencyBasis(_MoneyBase):
	def test_the_scale_comes_from_the_native_currency_record(self):
		basis = money.currency_basis("KES")
		self.assertEqual(basis["fraction_digits"], 2)
		self.assertEqual(basis["source_metadata_reference"], "Currency:KES")
		self.assertEqual(money.scale_for("KES"), 2)

	def test_a_missing_disabled_or_unsupported_currency_blocks_the_write(self):
		for currency in ("", "ZZZ-NOPE"):
			with self.subTest(currency=currency):
				frappe.local.message_log = []
				with self.assertRaises(frappe.ValidationError):
					money.currency_basis(currency)
				self.assertEqual(_title(None), "BUDGET_CURRENCY_PRECISION_UNSUPPORTED")
		self._as(self.officer)
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			contracts.save_budget_version_draft({"fiscal_year": self._fresh_fy(), "currency": "ZZZ-NOPE", "approval_reference": "C", "approval_date": frappe.utils.add_days(frappe.utils.nowdate(), -2), "authorised_total": 100})
		self.assertEqual(_title(None), "BUDGET_CURRENCY_PRECISION_UNSUPPORTED")
		self._as("Administrator")

	def test_a_currency_with_no_decimal_fraction_uses_scale_zero(self):
		"""The same code, another currency: whole-unit amounts only."""
		if not frappe.db.exists("Currency", "JPY"):
			self.skipTest("no JPY currency on this site")
		original = frappe.db.get_value("Currency", "JPY", ["enabled", "fraction_units"], as_dict=True)
		try:
			frappe.db.set_value("Currency", "JPY", {"enabled": 1, "fraction_units": 1})
			self.assertEqual(money.scale_for("JPY"), 0)
			self.assertEqual(money.parse_money("1500", scale=0), Decimal("1500"))
			with self.assertRaises(frappe.ValidationError):
				money.parse_money("1500.5", scale=0)
		finally:
			frappe.db.set_value("Currency", "JPY", {"enabled": original.enabled, "fraction_units": original.fraction_units})

	def test_the_decision_basis_names_the_currency_basis_not_a_constant(self):
		_budget, version, line = self._baseline(Decimal("100000000.00"))
		fy = frappe.db.get_value("Procurement Budget", frappe.db.get_value("Procurement Budget Version", version, "budget"), "fiscal_year")
		self._as(self.officer)
		basis = lines_svc.validate_plan_affordability_for_decision(fy, {line: "1000.00"})
		self.assertEqual(basis["currency_precision"], 2)
		self.assertEqual(basis["currency_basis"]["currency"], "KES")
		self.assertEqual(basis["currency_basis"]["source_metadata_reference"], "Currency:KES")
		self._as("Administrator")
