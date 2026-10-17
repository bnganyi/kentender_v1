# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.32 §5.4.7 / §7.8 / §14.16 — Planning's owner halves of the
whole-Tender cancellation recovery (PLN-CR-AC-001, 004, 006, 007, 008).

Planning's suite synthesises the Requisitions-shaped inputs (recovery id,
cancellation id, the originating drawdown's reference and quantities) the way
`test_plan_requisition.py` does; the real Requisitions, Tenders and Budget
adapters run together in `procurement_requisitions/tests/test_cancellation_recovery_integration.py`.
The fixture is CR-F01 at Planning's grain: one source of 100 units / KES 10m,
an authorised draw of 60 units / KES 6m."""

from __future__ import annotations

import ast
import os
from decimal import Decimal

import frappe

from kentender_procurement.procurement_planning.errors import ProcurementPlanningError
from kentender_procurement.procurement_planning.services import (
	cancellation_recovery,
	dpp_lifecycle,
	dpp_validation,
	plan_finance,
	plan_read,
	plan_requisition,
	plan_workbench,
)
from kentender_procurement.procurement_planning.services.recovery_principal import RecoveryCaller, recovery_caller
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_progress import ProgressCase
from kentender_procurement.procurement_planning.tests.test_plan_requisition import key

QUANTITY = 100
AMOUNT = 10_000_000


class RecoveryCase(ProgressCase):
	"""CR-F01 at Planning's grain."""

	def confirmed_item(self, *, indicative_amount: float = AMOUNT, quantity: int = QUANTITY) -> tuple[dict, str]:
		frappe.set_user(fx.AUTHOR)
		opened = dpp_lifecycle.open_departmental_plan(organisation_unit=fx.OU_ALPHA, fiscal_year=fx.FY_OPEN, idempotency_key=key(), fixture_namespace=fx.NS)
		added = dpp_lifecycle.save_direct_requirement(
			dpp_version=opened["current_version"], values=fx.direct_values(indicative_amount=indicative_amount, quantity=quantity),
			expected_record_version=opened["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.HOD)
		submitted = dpp_lifecycle.submit_departmental_plan(
			dpp_version=opened["current_version"], certification_confirmed=True, expected_record_version=added["record_version"], idempotency_key=key(),
		)
		task = frappe.get_doc("Departmental Plan Validation Task", {"task_reference": submitted["task"]})
		frappe.set_user(fx.PLANNER)
		accepted = dpp_validation.accept_departmental_plan(task=task.name, classifications={added["entry_id"]: "Goods"}, task_token=task.task_token, idempotency_key=key())
		plan = plan_read.get_annual_plan(plan_reference=accepted["annual_plan"])
		formed = plan_workbench.form_plan_items(
			plan_version=accepted["annual_plan_version"], dpp_entries=[plan["unallocated_sources"][0]["dpp_entry"]], mode="each",
			expected_record_version=plan["record_version"], idempotency_key=key(),
		)
		item_id = formed["created_items"][0]
		self.complete_and_confirm(item_id)
		return accepted, item_id

	def world(self) -> tuple[dict, str, str]:
		accepted, item_id = self.active_item(indicative_amount=AMOUNT)
		return accepted, item_id, self.allocation_id_of(item_id)

	def read(self, item_id: str) -> dict:
		frappe.set_user(fx.PLANNER)
		return plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)

	def remaining(self, item_id: str) -> tuple[Decimal, Decimal]:
		read = self.read(item_id)
		return Decimal(read["remaining_quantity"]), Decimal(read["remaining_value"])

	def spend(self, item_id: str, allocation_id: str, *, quantity, amount, reference: str | None = None) -> dict:
		"""An authorised draw; returns the draw as a Requisitions-shaped source."""
		frappe.set_user(fx.PLANNER)
		read = plan_requisition.get_requisition_eligible_plan_item(plan_item_id=item_id)
		reference = reference or f"REQ-CR-{key()[:8]}"
		frappe.set_user(fx.HOPF)
		result = plan_requisition.authorise_requisition_drawdown(
			plan_item_id=item_id, requisition_reference=reference,
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": str(quantity), "amount": str(amount)}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		return {
			"plan_source_allocation_id": allocation_id, "drawdown_reference": result["drawdowns"][0]["drawdown_reference"],
			"quantity": str(quantity), "amount": str(amount), "requisition_reference": reference,
		}

	def register(self, recovery_id: str, item_id: str, draw: dict, *, cancellation_id: str | None = None, **overrides) -> dict:
		source = {k: draw[k] for k in ("plan_source_allocation_id", "drawdown_reference", "quantity", "amount")}
		args = {
			"caller": recovery_caller(recovery_id), "recovery_id": recovery_id, "cancellation_id": cancellation_id or f"TDC-{recovery_id}",
			"plan_item_id": item_id, "requisition_reference": draw["requisition_reference"], "sources": [source],
		}
		args.update(overrides)
		return cancellation_recovery.register_cancellation_recovery_hold(**args)

	def reverse(self, recovery_id: str, item_id: str, draw: dict, *, cancellation_id: str | None = None, **overrides) -> dict:
		source = {k: draw[k] for k in ("plan_source_allocation_id", "drawdown_reference", "quantity", "amount")}
		args = {
			"caller": recovery_caller(recovery_id), "recovery_id": recovery_id, "cancellation_id": cancellation_id or f"TDC-{recovery_id}",
			"plan_item_id": item_id, "requisition_reference": draw["requisition_reference"], "sources": [source],
		}
		args.update(overrides)
		return cancellation_recovery.reverse_requisition_drawdowns_for_cancellation(**args)

	def assertCode(self, code, fn, *args, **kwargs):
		with self.assertRaises(ProcurementPlanningError) as caught:
			fn(*args, **kwargs)
		self.assertEqual(caught.exception.code, code)
		return caught.exception


class TestAllowanceSurvivesAPlanSuccessor(RecoveryCase):
	"""PLN-CR-AC-008 — an Annual Plan successor copies every allocation as a new row and grants no extra allowance."""

	def test_a_successor_plan_version_remembers_what_was_drawn(self):
		accepted, item_id, allocation_id = self.world()
		self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		before = self.read(item_id)
		self.assertEqual((Decimal(before["remaining_quantity"]), Decimal(before["remaining_value"])), (Decimal("40"), Decimal("4000000")))

		self.correcting_active_version(accepted["annual_plan"])

		after = self.read(item_id)
		self.assertEqual((Decimal(after["remaining_quantity"]), Decimal(after["remaining_value"])), (Decimal(before["remaining_quantity"]), Decimal(before["remaining_value"])))
		self.assertEqual(Decimal(after["sources"][0]["remaining_amount"]), Decimal(before["sources"][0]["remaining_amount"]))

	def test_the_ceiling_is_not_redrawn_after_a_successor(self):
		accepted, item_id, allocation_id = self.world()
		self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.correcting_active_version(accepted["annual_plan"])
		read = self.read(item_id)
		frappe.set_user(fx.HOPF)
		self.assertCode(
			"PLN_ALLOWANCE_EXCEEDED", plan_requisition.authorise_requisition_drawdown,
			plan_item_id=item_id, requisition_reference="REQ-CR-OVER",
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": "50", "amount": "5000000"}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)


class TestRegisterTheHold(RecoveryCase):
	"""PLN-CR-AC-002 / 004 — one idempotent hold per source; conflicting lineage fails."""

	def test_one_hold_per_source_and_an_identical_replay_reuses_it(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		first = self.register("CRR-T1", item_id, draw)
		self.assertEqual([h["reused"] for h in first["holds"]], [False])
		second = self.register("CRR-T1", item_id, draw)
		self.assertEqual([h["reused"] for h in second["holds"]], [True])
		self.assertEqual(frappe.db.count(cancellation_recovery.HOLD, {"recovery_id": "CRR-T1"}), 1)
		hold = frappe.get_doc(cancellation_recovery.HOLD, first["holds"][0]["hold"])
		self.assertEqual((hold.state, hold.display_status, hold.hold_key), ("Active", "Pending", f"CRR-T1:{allocation_id}"))

	def test_a_changed_fact_is_a_conflict_and_nothing_is_written(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-T2", item_id, draw)
		self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.register, "CRR-T2", item_id, {**draw, "quantity": "59"})
		self.assertEqual(frappe.db.count(cancellation_recovery.HOLD, {"recovery_id": "CRR-T2"}), 1)

	def test_the_quantity_must_match_the_original_authorisation(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		error = self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.register, "CRR-T3", item_id, {**draw, "quantity": "61"})
		self.assertEqual(Decimal(error.detail["expected_quantity"]), Decimal("61"))
		self.assertEqual(Decimal(error.detail["actual_quantity"]), Decimal("60"))
		self.assertEqual(frappe.db.count(cancellation_recovery.HOLD, {"recovery_id": "CRR-T3"}), 0)

	def test_an_unknown_drawdown_is_a_conflict(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.register, "CRR-T4", item_id, {**draw, "drawdown_reference": "PDR-99999"})

	def test_a_drawdown_cannot_be_held_by_two_recoveries(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-T5", item_id, draw)
		self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.register, "CRR-T5B", item_id, draw)

	def test_only_the_requisitions_recovery_service_may_call_it(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		with self.assertRaises(frappe.PermissionError):
			self.register("CRR-T6", item_id, draw, caller=None)
		with self.assertRaises(frappe.PermissionError):
			self.register("CRR-T6", item_id, draw, caller=recovery_caller("CRR-SOMEONE-ELSE"))
		with self.assertRaises(TypeError):
			RecoveryCaller("CRR-T6")


class TestAHeldSourceDrawsNothing(RecoveryCase):
	"""PLN-CR-AC-007 — Pending or Needs attention blocks only the affected source."""

	def test_authorisation_on_the_held_source_is_refused_and_the_read_says_why(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=100, amount=AMOUNT)
		self.register("CRR-H1", item_id, draw)
		read = self.read(item_id)
		self.assertFalse(read["eligible"])
		self.assertEqual(read["sources"][0]["recovery"]["status"], "Pending")
		self.assertEqual(Decimal(read["sources"][0]["recovery"]["pending_restoration_quantity"]), Decimal("100"))
		self.assertFalse(read["sources"][0]["drawable"])
		frappe.set_user(fx.HOPF)
		self.assertCode(
			"PLN_CANCELLATION_RECOVERY_PENDING", plan_requisition.authorise_requisition_drawdown,
			plan_item_id=item_id, requisition_reference="REQ-CR-HELD",
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": "1", "amount": "1"}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)
		frappe.set_user(fx.PLANNER)
		cancellation_recovery.set_cancellation_recovery_status(caller=recovery_caller("CRR-H1"), recovery_id="CRR-H1", plan_item_id=item_id, status="Needs attention", reason="The Budget reservation was released for another reason.")
		self.assertEqual(self.read(item_id)["sources"][0]["recovery"]["status"], "Needs attention")
		frappe.set_user(fx.HOPF)
		self.assertCode(
			"PLN_CANCELLATION_RECOVERY_CONFLICT", plan_requisition.authorise_requisition_drawdown,
			plan_item_id=item_id, requisition_reference="REQ-CR-HELD",
			allocations=[{"plan_source_allocation_id": allocation_id, "quantity": "1", "amount": "1"}],
			expected_record_version=read["record_version"], idempotency_key=key(),
		)

	def test_an_unrelated_item_is_still_usable(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-H2", item_id, draw)
		listed = {row["plan_item_id"] for row in plan_requisition.list_requisition_eligible_plan_items()}
		# the held item's only draws were its 60 units; its other 40 are in a held source, so it is not offered
		self.assertNotIn(item_id, listed)

	def test_the_ordinary_reversal_route_never_reverses_a_held_drawdown(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-H3", item_id, draw)
		frappe.set_user(fx.HOPF)
		version = frappe.db.get_value("Plan Drawdown Reference", draw["drawdown_reference"], "record_version")
		self.assertCode(
			"PLN_CANCELLATION_RECOVERY_PENDING", plan_requisition.reverse_requisition_drawdown,
			drawdown_reference=draw["drawdown_reference"], expected_record_version=version, idempotency_key=key(),
		)
		self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", draw["drawdown_reference"], "drawdown_state"), "Active")


class TestTheCancellationModeOfTheReversal(RecoveryCase):
	"""PLN-CR-AC-001 / 004 / 006 / 008 — the exact original draw is restored once, the scope lock stays."""

	def test_cr_f01_the_exact_draw_is_restored_and_the_lock_is_kept(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.assertEqual(self.remaining(item_id), (Decimal("40"), Decimal("4000000")))
		root_before = frappe.db.get_value("Plan Item", item_id, ["scope_locked_since", "first_authorised_requisition"], as_dict=True)
		self.assertTrue(root_before.scope_locked_since)

		self.register("CRR-R1", item_id, draw)
		result = self.reverse("CRR-R1", item_id, draw)

		self.assertEqual(self.remaining(item_id), (Decimal("100"), Decimal("10000000")))
		self.assertEqual([(Decimal(r["quantity"]), Decimal(r["amount"]), r["reused"]) for r in result["reversals"]], [(Decimal("60"), Decimal("6000000"), False)])
		row = frappe.db.get_value(
			"Plan Drawdown Reference", draw["drawdown_reference"], ["drawdown_state", "reversal_reason", "recovery_id", "cancellation_id", "reversal_reference", "quantity", "amount"], as_dict=True,
		)
		self.assertEqual((row.drawdown_state, row.reversal_reason, row.recovery_id, row.cancellation_id), ("Reversed", "TenderCancelled", "CRR-R1", "TDC-CRR-R1"))
		self.assertEqual((float(row.quantity), float(row.amount)), (60.0, 6_000_000.0))  # the recorded evidence is never edited
		self.assertEqual(frappe.db.get_value(cancellation_recovery.HOLD, {"recovery_id": "CRR-R1"}, "state"), "Removed")
		root_after = frappe.db.get_value("Plan Item", item_id, ["scope_locked_since", "first_authorised_requisition"], as_dict=True)
		self.assertEqual(root_after, root_before)

	def test_a_replay_or_a_new_retry_changes_nothing(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-R2", item_id, draw)
		self.reverse("CRR-R2", item_id, draw)
		version = frappe.db.get_value("Plan Drawdown Reference", draw["drawdown_reference"], "record_version")
		again = self.reverse("CRR-R2", item_id, draw)
		self.assertTrue(again["idempotent"])
		self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", draw["drawdown_reference"], "record_version"), version)
		self.assertEqual(self.remaining(item_id), (Decimal("100"), Decimal("10000000")))

	def test_a_changed_fact_is_a_conflict_and_restores_nothing(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-R3", item_id, draw)
		self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.reverse, "CRR-R3", item_id, {**draw, "amount": "5999999"})
		self.assertEqual(self.remaining(item_id), (Decimal("40"), Decimal("4000000")))
		self.assertEqual(frappe.db.get_value(cancellation_recovery.HOLD, {"recovery_id": "CRR-R3"}, "state"), "Active")

	def test_no_hold_no_restoration(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.reverse, "CRR-R4", item_id, draw)
		self.assertEqual(self.remaining(item_id), (Decimal("40"), Decimal("4000000")))

	def test_a_draw_already_reversed_for_another_reason_is_never_restored_again(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		frappe.set_user(fx.HOPF)
		version = frappe.db.get_value("Plan Drawdown Reference", draw["drawdown_reference"], "record_version")
		plan_requisition.reverse_requisition_drawdown(drawdown_reference=draw["drawdown_reference"], expected_record_version=version, idempotency_key=key())
		frappe.set_user(fx.PLANNER)
		self.assertEqual(self.remaining(item_id), (Decimal("100"), Decimal("10000000")))
		self.assertCode("PLN_CANCELLATION_RECOVERY_CONFLICT", self.register, "CRR-R5", item_id, draw)
		self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", draw["drawdown_reference"], "reversal_reason"), "Requisition revoked")
		self.assertEqual(self.remaining(item_id), (Decimal("100"), Decimal("10000000")))

	def test_two_sequential_draws_restore_only_their_own_amounts(self):
		_, item_id, allocation_id = self.world()
		first = self.spend(item_id, allocation_id, quantity=30, amount=3_000_000)
		second = self.spend(item_id, allocation_id, quantity=20, amount=2_000_000)
		self.assertEqual(self.remaining(item_id), (Decimal("50"), Decimal("5000000")))
		self.register("CRR-S1", item_id, first)
		self.register("CRR-S2", item_id, second)
		self.reverse("CRR-S1", item_id, first)
		self.assertEqual(self.remaining(item_id), (Decimal("80"), Decimal("8000000")))
		self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", second["drawdown_reference"], "drawdown_state"), "Active")
		self.reverse("CRR-S2", item_id, second)
		self.assertEqual(self.remaining(item_id), (Decimal("100"), Decimal("10000000")))

	def test_a_fresh_draw_uses_the_restored_allowance_with_fresh_identities(self):
		_, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-F1", item_id, draw)
		self.reverse("CRR-F1", item_id, draw)
		fresh = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.assertNotEqual(fresh["drawdown_reference"], draw["drawdown_reference"])
		self.assertEqual(self.remaining(item_id), (Decimal("40"), Decimal("4000000")))
		# replaying the old recovery leaves the new balances alone
		self.reverse("CRR-F1", item_id, draw)
		self.assertEqual(self.remaining(item_id), (Decimal("40"), Decimal("4000000")))
		self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", fresh["drawdown_reference"], "drawdown_state"), "Active")

	def test_the_restoration_survives_a_plan_successor(self):
		accepted, item_id, allocation_id = self.world()
		draw = self.spend(item_id, allocation_id, quantity=60, amount=6_000_000)
		self.register("CRR-P1", item_id, draw)
		self.correcting_active_version(accepted["annual_plan"])
		self.reverse("CRR-P1", item_id, draw)
		self.assertEqual(self.remaining(item_id), (Decimal("100"), Decimal("10000000")))


class TestOnlyTheRequisitionsGatewayMintsACaller(RecoveryCase):
	"""The principal cannot be minted anywhere a web request could reach."""

	ALLOWED = {os.path.join("procurement_requisitions", "services", "eligibility_gateway.py")}

	def test_no_production_file_other_than_the_gateway_mints_a_recovery_caller(self):
		root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		offenders = []
		for base, dirs, files in os.walk(root):
			dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__", "node_modules")]
			for name in files:
				if not name.endswith(".py"):
					continue
				path = os.path.join(base, name)
				rel = os.path.relpath(path, root)
				if rel in self.ALLOWED or rel.endswith(os.path.join("procurement_planning", "services", "recovery_principal.py")):
					continue
				tree = ast.parse(open(path, encoding="utf-8").read())
				for node in ast.walk(tree):
					if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "recovery_caller":
						offenders.append(rel)
		self.assertEqual(sorted(set(offenders)), [])
