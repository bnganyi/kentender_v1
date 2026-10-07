# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUD-XC-002 / AUD-XC-012 / AUD-BUD-012 / AUD-BUD-013 — the money-moving
Budget functions are in-process service calls authenticated by a named
service principal (BUD v1.12 §7, BUD-BR-015), not web endpoints and not a
session role. Matrix (owner decision 6 Oct 2026):

- Requisitions: check/reserve funding; release only the exact reservations its
  own requisition created and has not converted.
- Contract: convert, release an unused amount on an owner event, adjust.
- Planning, Tenders, Evaluation, Award, any session user: refused.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase  # noqa: F401  (base class lives in _FinanceTestBase)

from kentender_budget.services import budget_check_reserve_contracts as check_reserve
from kentender_budget.services import budget_commitment_contracts as commit
from kentender_budget.services import budget_service_principal as principals
from kentender_budget.services.budget_service_principal import (
	PRINCIPAL_AWARD,
	PRINCIPAL_BUDGET,
	PRINCIPAL_CONTRACT,
	PRINCIPAL_EVALUATION,
	PRINCIPAL_PLANNING,
	PRINCIPAL_REQUISITIONS,
	PRINCIPAL_TENDERS,
	service_caller,
)
from kentender_budget.tests.test_bud_chg_001_phase3_check_reserve import FUNDING_SOURCE, _FinanceTestBase, owner_ou
from kentender_budget.utils.version_stamp import stamped
from kentender_core.services.command_write_guard import purge_doc

FORBIDDEN = "BUDGET_DOWNSTREAM_FORBIDDEN"


def req(reference: str = "REQ-SP-1"):
	return service_caller(PRINCIPAL_REQUISITIONS, reference=reference)


def contract_caller(contract: str):
	return service_caller(PRINCIPAL_CONTRACT, reference=contract)


class _PrincipalBase(_FinanceTestBase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.hopf = cls._make_user("hopfsp", ("Head of Procurement Function",))
		cls._keys = 0

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		budgets = [name for doctype, name in cls._cleanup if doctype == "Procurement Budget"]
		if budgets:
			frappe.flags.allow_budget_audit_purge = True
			try:
				reservations = frappe.get_all("Funding Reservation", filters={"budget": ["in", budgets]}, pluck="name")
				for name in frappe.get_all("Procurement Commitment", filters={"reservation": ["in", reservations or [""]]}, pluck="name"):
					frappe.db.delete("Budget Audit Event", {"commitment": name})
					purge_doc("Procurement Commitment", name)
				for name in reservations:
					frappe.db.delete("Budget Audit Event", {"reservation": name})
					purge_doc("Funding Reservation", name)
				frappe.db.delete("Budget Audit Event", {"budget": ["in", budgets]})
			finally:
				frappe.flags.allow_budget_audit_purge = False
		super().tearDownClass()

	def setUp(self):
		super().setUp()
		type(self)._contracts = getattr(type(self), "_contracts", 0) + 1
		self.contract = f"CTR-{self.suffix}-{type(self)._contracts}"

	def _key(self, label: str = "k") -> str:
		type(self)._keys += 1
		return f"SP-{self.suffix}-{label}-{self._keys}"

	def _reserve(self, line: str, amount, *, reference: str = "REQ-SP-1", plan_item: str = "TEST-PPI-SP") -> str:
		"""One reservation placed the only way Budget now allows: as the
		Requisitions principal."""
		self._as(self.hopf)
		correlation = self._key("corr")
		checked = check_reserve.check_funding(
			plan_item=plan_item, plan_version="TEST-PLN-SP", source_set_hash=f"HASH-{correlation}",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": f"PSA-{correlation}", "drawdown_line_id": f"DDL-{correlation}"}],
			correlation_id=correlation, caller=req(reference), caller_reference=reference,
		)
		result = check_reserve.reserve_funding(
			token=checked["token"], source_set_hash=f"HASH-{correlation}", idempotency_key=correlation, caller=req(reference)
		)
		return result["reservations"][0]["reservation_id"]

	def assert_forbidden(self, fn, *args, **kwargs):
		frappe.local.message_log = []
		with self.assertRaises(frappe.PermissionError):
			fn(*args, **kwargs)
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		self.assertIn(FORBIDDEN, titles)

	def _calls(self, caller):
		"""Every guarded action, with throwaway arguments: the principal check
		must refuse before any argument is looked at."""
		return {
			"check_funding": lambda: check_reserve.check_funding("p", "v", "h", [{"budget_line": "X", "amount": 1}], "c", caller=caller),
			"reserve_funding": lambda: check_reserve.reserve_funding("t", "h", "k", caller=caller),
			"release_reservation": lambda: commit.release_reservation("X", None, "E", "T", "K", caller=caller),
			"convert_reservation": lambda: commit.convert_reservation("X", "C", 1, "K", contract_event_id="E", contract_event_type="T", caller=caller),
			"adjust_commitment": lambda: commit.adjust_commitment("X", 0, "E", "T", "K", caller=caller),
			"revalidate_reservations": lambda: commit.revalidate_reservations(["X"], "E", "T", "K", caller=caller),
		}


class TestNoWebSurface(_PrincipalBase):
	NAMES = ("check_funding", "reserve_funding", "release_reservation", "convert_reservation", "adjust_commitment", "revalidate_reservations")

	def test_no_budget_api_endpoint_remains_for_the_guarded_actions(self):
		from kentender_budget.api import budget_api

		for name in self.NAMES:
			with self.subTest(name=name):
				self.assertFalse(hasattr(budget_api, name), f"budget_api.{name} is still published")

	def test_service_functions_are_not_whitelisted(self):
		for module in (check_reserve, commit):
			for name in self.NAMES:
				fn = getattr(module, name, None)
				if fn is not None:
					with self.subTest(name=name):
						self.assertNotIn(fn, frappe.whitelisted)

	def test_the_decision_time_affordability_check_is_not_a_web_endpoint(self):
		"""RG-22 — it takes whole-Budget row locks, so a reader who can reach it can stall reserve, approve and close.
		Planning calls it in-process (`procurement_planning.services.budget_gateway`)."""
		from kentender_budget.api import budget_api

		self.assertNotIn(budget_api.validate_plan_affordability_for_decision, frappe.whitelisted)
		self.assertIn(budget_api.check_plan_affordability, frappe.whitelisted)  # the non-locking display read stays published

	def test_the_dia_adapter_release_endpoint_is_gone(self):
		self.assertIsNone(importlib.util.find_spec("kentender_budget.api.dia_budget_control"))


class TestPrincipalMatrix(_PrincipalBase):
	def test_a_session_user_without_a_principal_is_refused_everywhere(self):
		for user in (self.finance_officer, self.hopf, self.officer, self.approver, "Administrator"):
			self._as(user)
			for action, call in self._calls(None).items():
				with self.subTest(user=user, action=action):
					self.assert_forbidden(call)

	def test_planning_tenders_evaluation_and_award_hold_no_budget_money_action(self):
		self._as("Administrator")
		for principal in (PRINCIPAL_PLANNING, PRINCIPAL_TENDERS, PRINCIPAL_EVALUATION, PRINCIPAL_AWARD):
			for action, call in self._calls(service_caller(principal, reference="X")).items():
				with self.subTest(principal=principal, action=action):
					self.assert_forbidden(call)

	def test_each_principal_is_refused_the_actions_that_are_not_its_own(self):
		self._as("Administrator")
		not_requisitions = ("convert_reservation", "adjust_commitment", "revalidate_reservations")
		not_contract = ("check_funding", "reserve_funding", "revalidate_reservations")
		not_budget = ("check_funding", "reserve_funding", "release_reservation", "convert_reservation", "adjust_commitment")
		for principal, refused in ((PRINCIPAL_REQUISITIONS, not_requisitions), (PRINCIPAL_CONTRACT, not_contract), (PRINCIPAL_BUDGET, not_budget)):
			calls = self._calls(service_caller(principal, reference="X"))
			for action in refused:
				with self.subTest(principal=principal, action=action):
					self.assert_forbidden(calls[action])

	def test_a_caller_cannot_be_forged(self):
		with self.assertRaises(TypeError):
			principals.ServiceCaller(PRINCIPAL_CONTRACT, "X")
		caller = contract_caller(self.contract)
		with self.assertRaises(AttributeError):
			caller.principal = PRINCIPAL_REQUISITIONS
		for forged in ({"principal": PRINCIPAL_CONTRACT}, PRINCIPAL_CONTRACT, "contract_management", object()):
			with self.subTest(forged=forged):
				self.assert_forbidden(self._calls(forged)["release_reservation"])
		with self.assertRaises(ValueError):
			service_caller("somebody_else")

	def test_only_the_owning_gateways_and_seeds_mint_principals(self):
		root = Path(frappe.get_app_path("kentender_budget")).parent.parent
		pattern = re.compile(r"\bservice_caller\(\s*(?:principals\.)?(PRINCIPAL_[A-Z]+)")
		allowed_gateway = {PRINCIPAL_REQUISITIONS: "procurement_requisitions/services/funding_gateway.py"}
		offenders = []
		for path in root.glob("kentender_*/**/*.py"):
			rel = str(path.relative_to(root))
			if "/tests/" in rel or "/node_modules/" in rel or rel.endswith("budget_service_principal.py"):
				continue
			text = path.read_text(encoding="utf-8", errors="ignore")
			for name in pattern.findall(text):
				principal = getattr(principals, name)
				if "/seeds/" in rel or "/seed/" in rel:
					continue
				if principal in allowed_gateway and rel.endswith(allowed_gateway[principal]):
					continue
				offenders.append((rel, name))
		self.assertEqual(offenders, [])


class TestRequisitionsRelease(_PrincipalBase):
	def test_requisitions_releases_the_reservation_its_own_requisition_created(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000, reference="REQ-OWN-1")
		result = commit.release_reservation(
			reservation, None, "REQ-OWN-1:revoked", "ProcurementRequisitionRevoked", self._key("rel"), caller=req("REQ-OWN-1")
		)
		self.assertEqual(result["reservation"]["status"], "Released")
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 0)

	def test_requisitions_cannot_release_another_requisitions_reservation(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000, reference="REQ-OWN-2")
		self.assert_forbidden(
			commit.release_reservation, reservation, None, "REQ-OTHER:revoked", "ProcurementRequisitionRevoked", self._key("rel"), caller=req("REQ-OTHER")
		)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "status"), "Active")

	def test_requisitions_cannot_release_a_reservation_it_did_not_create(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000, reference="REQ-OWN-3")
		frappe.db.set_value("Funding Reservation", reservation, {"calling_module": "Procurement Planning"})
		self.assert_forbidden(
			commit.release_reservation, reservation, None, "REQ-OWN-3:revoked", "ProcurementRequisitionRevoked", self._key("rel"), caller=req("REQ-OWN-3")
		)

	def test_requisitions_releases_the_whole_hold_only_and_never_a_converted_one(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000, reference="REQ-OWN-4")
		self.assert_forbidden(
			commit.release_reservation, reservation, 1_000_000, "E", "ProcurementRequisitionRevoked", self._key("rel"), caller=req("REQ-OWN-4")
		)
		self._as("Administrator")
		commit.convert_reservation(
			reservation, "CTR-OWN-4", 4_000_000, self._key("conv"),
			contract_event_id="CTR-OWN-4:signed", contract_event_type="ContractSigned", caller=contract_caller("CTR-OWN-4"),
		)
		self.assert_forbidden(
			commit.release_reservation, reservation, None, "E", "ProcurementRequisitionRevoked", self._key("rel"), caller=req("REQ-OWN-4")
		)

	def test_release_needs_the_downstream_event(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000, reference="REQ-OWN-5")
		self.assert_forbidden(commit.release_reservation, reservation, None, "", "", self._key("rel"), caller=req("REQ-OWN-5"))
		self.assert_forbidden(commit.release_reservation, reservation, None, "E", "T", "", caller=req("REQ-OWN-5"))


class TestContractPrincipal(_PrincipalBase):
	def _convert(self, reservation, amount, *, contract=None, key=None):
		contract = contract or self.contract
		self._as("Administrator")
		return commit.convert_reservation(
			reservation, contract, amount, key or self._key("conv"),
			contract_event_id=f"{contract}:signed", contract_event_type="ContractSigned", caller=contract_caller(contract),
		)

	def test_contract_converts_a_reservation_into_a_commitment(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		result = self._convert(reservation, 6_000_000)
		self.assertEqual(result["commitment"]["current_amount"], 6_000_000)
		self.assertEqual(result["reservation"]["remaining_amount"], 4_000_000)

	def test_conversion_needs_a_contract_event_and_the_callers_own_contract(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		self._as("Administrator")
		self.assert_forbidden(
			commit.convert_reservation, reservation, self.contract, 1_000_000, self._key("conv"),
			contract_event_id="", contract_event_type="", caller=contract_caller(self.contract),
		)
		self.assert_forbidden(
			commit.convert_reservation, reservation, f"{self.contract}-2", 1_000_000, self._key("conv"),
			contract_event_id="E", contract_event_type="T", caller=contract_caller(self.contract),
		)

	def test_conversion_replays_on_the_same_key_and_conflicts_on_a_changed_payload(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		key = self._key("conv")
		first = self._convert(reservation, 6_000_000, key=key)
		replay = self._convert(reservation, 6_000_000, key=key)
		self.assertTrue(replay.get("replayed"))
		self.assertEqual(replay["commitment"]["commitment_id"], first["commitment"]["commitment_id"])
		self.assertEqual(frappe.db.count("Procurement Commitment", {"reservation": reservation}), 1)
		with self.assertRaises(frappe.ValidationError):
			self._convert(reservation, 7_000_000, key=key)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 4_000_000)

	def test_a_new_key_for_the_same_contract_with_another_amount_is_not_silently_accepted(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		self._convert(reservation, 6_000_000)
		with self.assertRaises(frappe.ValidationError):
			self._convert(reservation, 3_000_000)
		self.assertEqual(frappe.db.count("Procurement Commitment", {"reservation": reservation}), 1)

	def test_contract_releases_an_unused_amount_once_per_key(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		self._convert(reservation, 6_000_000)
		self._as("Administrator")
		key = self._key("rel")

		def release(amount, key=key, contract=None):
			return commit.release_reservation(reservation, amount, f"{self.contract}:unused", "ContractUnusedAmount", key, caller=contract_caller(contract or self.contract))

		first = release(1_000_000)
		self.assertEqual(first["reservation"]["remaining_amount"], 3_000_000)
		replay = release(1_000_000)
		self.assertTrue(replay.get("replayed"))
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 3_000_000)
		with self.assertRaises(frappe.ValidationError):
			release(2_000_000)
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation, "remaining_amount"), 3_000_000)

	def test_contract_cannot_release_more_than_remains_or_for_another_contract(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		self._convert(reservation, 6_000_000)
		self._as("Administrator")
		with self.assertRaises(frappe.ValidationError):
			commit.release_reservation(reservation, 9_000_000, "E", "T", self._key("rel"), caller=contract_caller(self.contract))
		self.assert_forbidden(commit.release_reservation, reservation, 1_000_000, "E", "T", self._key("rel"), caller=contract_caller(f"{self.contract}-OTHER"))
		self.assert_forbidden(commit.release_reservation, reservation, None, "E", "T", self._key("rel"), caller=contract_caller(self.contract))

	def test_contract_adjusts_a_commitment_and_the_key_dedupes(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		commitment = self._convert(reservation, 6_000_000)["commitment"]["commitment_id"]
		self._as("Administrator")
		key = self._key("adj")

		def adjust(new_total, key=key, contract=None):
			return commit.adjust_commitment(commitment, new_total, f"{self.contract}:variation-1", "ContractVariation", key, caller=contract_caller(contract or self.contract))

		self.assertEqual(adjust(5_000_000)["commitment"]["current_amount"], 5_000_000)
		replay = adjust(5_000_000)
		self.assertTrue(replay.get("replayed"))
		with self.assertRaises(frappe.ValidationError):
			adjust(4_000_000)
		self.assertEqual(frappe.db.get_value("Procurement Commitment", commitment, "current_amount"), 5_000_000)
		self.assert_forbidden(adjust, 1_000_000, key=self._key("adj"), contract=f"{self.contract}-OTHER")

	def test_adjustment_needs_a_variation_event(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		commitment = self._convert(reservation, 6_000_000)["commitment"]["commitment_id"]
		self._as("Administrator")
		self.assert_forbidden(commit.adjust_commitment, commitment, 1, "", "", self._key("adj"), caller=contract_caller(self.contract))


class TestBudgetInternalRevalidation(_PrincipalBase):
	def test_revalidation_is_budget_internal(self):
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 10_000_000)
		self._as("Administrator")
		result = commit.revalidate_reservations(
			[reservation], "EVT-SP-1", "BudgetVersionActivated", self._key("rev"), caller=service_caller(PRINCIPAL_BUDGET)
		)
		self.assertTrue(result["ok"])
		self.assert_forbidden(commit.revalidate_reservations, [reservation], "E", "T", self._key("rev"), caller=contract_caller(self.contract))
		self.assert_forbidden(commit.revalidate_reservations, [reservation], "E", "T", self._key("rev"), caller=req("REQ-SP-1"))


class TestCheckReserveCaller(_PrincipalBase):
	"""AUD-XC-012 / AUD-BUD-013."""

	def _check(self, line, caller, *, correlation=None, reference="REQ-CR-1", amount=1_000_000):
		correlation = correlation or self._key("corr")
		return correlation, check_reserve.check_funding(
			plan_item="TEST-PPI-CR", plan_version="TEST-PLN-CR", source_set_hash="HASH-CR",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": amount, "funding_source": FUNDING_SOURCE, "plan_source_allocation": f"PSA-{correlation}", "drawdown_line_id": f"DDL-{correlation}"}],
			correlation_id=correlation, caller=caller, caller_reference=reference,
		)

	def test_a_finance_confirmation_officer_cannot_place_a_hold(self):
		_, line = self._new_dhi_line()
		self._as(self.finance_officer)
		self.assert_forbidden(
			check_reserve.check_funding, plan_item="p", plan_version="v", source_set_hash="h",
			allocations=[{"budget_line": line, "source_organisation_unit": owner_ou(line), "amount": 1, "funding_source": FUNDING_SOURCE, "plan_source_allocation": "PSA-FCO"}],
			correlation_id=self._key("corr"),
		)
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 0)

	def test_the_calling_module_is_the_principal_not_a_declared_value(self):
		import inspect

		self.assertNotIn("calling_module", inspect.signature(check_reserve.check_funding).parameters)
		self.assertNotIn("actor", inspect.signature(check_reserve.reserve_funding).parameters)
		_, line = self._new_dhi_line()
		reservation = self._reserve(line, 1_000_000, reference="REQ-CR-2")
		doc = frappe.get_doc("Funding Reservation", reservation)
		self.assertEqual(doc.calling_module, "Procurement Requisitions")
		self.assertEqual(doc.caller_reference, "REQ-CR-2")

	def test_a_requisitions_caller_cannot_name_another_requisition(self):
		_, line = self._new_dhi_line()
		self._as(self.hopf)
		self.assert_forbidden(self._check, line, req("REQ-CR-3"), reference="REQ-SOMEONE-ELSE")

	def test_the_token_is_bound_to_the_actor_who_checked(self):
		_, line = self._new_dhi_line()
		self._as(self.hopf)
		correlation, checked = self._check(line, req("REQ-CR-4"), reference="REQ-CR-4")
		self._as(self.finance_officer)
		with self.assertRaises(frappe.ValidationError):
			check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-4"))
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 0)
		self._as(self.hopf)
		self.assertTrue(check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-4"))["ok"])

	def test_the_token_is_bound_to_the_requisition_that_checked(self):
		_, line = self._new_dhi_line()
		self._as(self.hopf)
		correlation, checked = self._check(line, req("REQ-CR-5"), reference="REQ-CR-5")
		with self.assertRaises(frappe.PermissionError):
			check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-6"))

	def test_a_budget_revision_between_check_and_reserve_makes_the_check_stale(self):
		budget, line = self._new_dhi_line()
		self._as(self.hopf)
		correlation, checked = self._check(line, req("REQ-CR-7"), reference="REQ-CR-7")
		self._supersede_active_version(budget)
		self._as(self.hopf)
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-7"))
		titles = [m.get("title") for m in frappe.local.message_log if isinstance(m, dict)]
		self.assertIn("BUDGET_CHECK_STALE", titles)
		self.assertEqual(frappe.db.count("Funding Reservation", {"budget_line": line}), 0)

	def _supersede_active_version(self, budget):
		"""A real governed revision: successor, submit, approve."""
		from kentender_budget.services import budget_contracts as contracts
		from kentender_budget.services import budget_line_contracts as lines_svc
		from kentender_budget.services import budget_readiness_contracts as readiness

		self._as(self.officer)
		succ = contracts.create_budget_successor_version(budget, {"revision_type": "Transfer"})
		self.assertTrue(succ["ok"], succ)
		new_version = succ["version"]["id"]
		self._track("Procurement Budget Version", new_version)
		active = frappe.db.get_value("Procurement Budget Version", {"budget": budget, "status": "Active"}, "name")
		dhi = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active, "title": "DHI test line"}, "budget_line")
		hwd = frappe.db.get_value("Procurement Budget Line Version", {"budget_version": active, "title": "HWD test line"}, "budget_line")
		saved = lines_svc.save_budget_lines_draft(stamped(
			{
				"budget_version": new_version,
				"lines": [
					{"budget_line": dhi, "approved_amount": 99_999_999},
					{"budget_line": hwd, "approved_amount": 2},
				],
			}
		))
		self.assertTrue(saved["ok"], saved.get("errors"))
		submitted = readiness.submit_budget_version(stamped({"budget_version": new_version}))
		self.assertTrue(submitted["ok"], submitted.get("blockers"))
		self._as(self.approver)
		approved = readiness.approve_budget_version(stamped({"budget_version": new_version}))
		self.assertTrue(approved["ok"], approved.get("blockers"))
		frappe.set_user("Administrator")

	def test_a_replay_with_a_changed_source_set_is_a_conflict_even_after_the_check_token_expired(self):
		"""RG-27 — same key + changed payload is refused (BUD section 8.3) whether or not the 300 s check
		token is still cached: the reservation carries the source-set hash it was reserved under."""
		_, line = self._new_dhi_line()
		self._as(self.hopf)
		correlation, checked = self._check(line, req("REQ-CR-27"), reference="REQ-CR-27")
		first = check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-27"))
		frappe.cache().delete_value(f"budget_check_token:{checked['token']}")  # the token has expired
		again = check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-27"))
		self.assertTrue(again["reused"])
		self.assertEqual(again["reservations"][0]["reservation_id"], first["reservations"][0]["reservation_id"])
		frappe.local.message_log = []
		with self.assertRaises(frappe.ValidationError):
			check_reserve.reserve_funding("an-expired-token", "HASH-CHANGED", correlation, caller=req("REQ-CR-27"))
		titles = [m.get("title") for m in (frappe.local.message_log or []) if isinstance(m, dict)]
		self.assertIn("BUDGET_IDEMPOTENCY_CONFLICT", titles)

	def test_reserve_replays_on_the_same_key(self):
		_, line = self._new_dhi_line()
		self._as(self.hopf)
		correlation, checked = self._check(line, req("REQ-CR-8"), reference="REQ-CR-8")
		first = check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-8"))
		again = check_reserve.reserve_funding(checked["token"], "HASH-CR", correlation, caller=req("REQ-CR-8"))
		self.assertTrue(again["reused"])
		self.assertEqual(again["reservations"][0]["reservation_id"], first["reservations"][0]["reservation_id"])
