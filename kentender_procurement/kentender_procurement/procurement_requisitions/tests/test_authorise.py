# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §9.1A/§7 — AuthoriseRequisition / RevokeUnconsumedAuthorisation."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as cmd, lifecycle
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionAuthoriseCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		fx.ensure_world()
		cls.addClassCleanup(fx.restore_site)

	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		fx.wipe_requisition_rows()
		fx.wipe_planning_rows()
		if not frappe.db.exists("Delivery Location", "Test Delivery Location — Requisitions"):
			frappe.get_doc({"doctype": "Delivery Location", "location_name": "Test Delivery Location — Requisitions", "address": "1 Test Street", "status": "Active"}).insert(ignore_permissions=True)
		self.location = "Test Delivery Location — Requisitions"
		self.addCleanup(frappe.set_user, "Administrator")

	def _complete_draft(self, prepared: dict) -> None:
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
		cmd.save_requisition_summary(
			requisition=prepared["requisition"], values={"delivery_location": self.location, "latest_delivery_date": "2102-04-30"},
			expected_record_version=version.record_version, idempotency_key=fx.key(),
		)
		cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 1, "intended_use": "Clinical training"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		fx.confirm_all_proposed_requirements(prepared["requisition"], package_version)
		cmd.add_acceptance_requirement(
			requisition=prepared["requisition"],
			values={"applies_to_scope": "All items", "check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)

	def _submitted_via_hod_direct(self, *, indicative_amount: float = 50_000_000) -> tuple[dict, dict]:
		_, item_id = fx.active_item(indicative_amount=indicative_amount)
		frappe.set_user(fx.HOD)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self._complete_draft(prepared)
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		return prepared, submitted


class TestAuthoriseHappyPath(RequisitionAuthoriseCase):
	def test_authorise_creates_reservation_drawdown_and_handoff(self):
		prepared, submitted = self._submitted_via_hod_direct()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "authorised")
		self.assertEqual(len(result["reservations"]), 1)
		self.assertEqual(len(result["planning_drawdown_references"]), 1)

		root.reload()
		self.assertEqual(root.current_state, "Authorised")
		self.assertEqual(root.authorised_version, result["requisition_version"])
		self.assertTrue(root.handoff)

		version = frappe.get_doc("Requisition Version", result["requisition_version"])
		self.assertEqual(version.version_status, "Authorised")
		line = version.drawdown_lines[0]
		self.assertTrue(line.reservation_id)
		self.assertTrue(line.planning_drawdown_reference)
		reservation = frappe.get_doc("Funding Reservation", line.reservation_id)
		self.assertEqual(reservation.calling_module, "Procurement Requisitions")
		self.assertEqual(reservation.caller_reference, root.requisition_reference)

		handoff = frappe.get_doc("Authorised Requisition Handoff", root.handoff)
		self.assertEqual(handoff.handoff_version, "1.3")
		self.assertTrue(handoff.handoff_digest)
		self.assertEqual(frappe.db.count("Requisition Event", {"requisition": root.name, "event_type": "ProcurementRequisitionAuthorised.v1.3"}), 1)

	def test_authorise_is_idempotent_by_key(self):
		prepared, submitted = self._submitted_via_hod_direct()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		key = fx.key()
		first = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=key)
		second = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=key)
		self.assertEqual(first["handoff"], second["handoff"])
		self.assertTrue(second["idempotent"])


class TestAuthoriseSegregationOfDuties(RequisitionAuthoriseCase):
	def test_hopf_who_prepared_directly_cannot_also_authorise(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.HOPF)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self._complete_draft(prepared)
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		root.reload()
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_SOD_BLOCKED")


class TestAuthoriseAtomicity(RequisitionAuthoriseCase):
	def test_a_forced_internal_failure_rolls_back_this_modules_own_writes_only(self):
		"""Proves the `envelope.atomic()` savepoint actually works: a failure
		injected after the external Budget/Planning calls have already
		committed leaves THIS module's own state exactly as it was
		(Submitted to Procurement, no decision, no handoff, no event) —
		the documented D6 residual risk, not a silent corruption."""
		prepared, submitted = self._submitted_via_hod_direct()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		with patch(
			"kentender_procurement.procurement_requisitions.services.handoff.build_and_insert",
			side_effect=RuntimeError("forced failure inside the atomic block"),
		):
			with self.assertRaises(RuntimeError):
				authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())

		root.reload()
		self.assertEqual(root.current_state, "Submitted to Procurement", "root state must roll back to before the atomic block")
		self.assertIsNone(root.handoff or None)
		self.assertEqual(frappe.db.count("Authorised Requisition Handoff", {"requisition": root.name}), 0)
		self.assertEqual(frappe.db.count("Requisition Decision", {"requisition_version": submitted["requisition_version"]}), 0)
		version = frappe.get_doc("Requisition Version", submitted["requisition_version"])
		self.assertEqual(version.version_status, "Submitted to Procurement")

		# The documented residual risk: the external calls already committed.
		line = version.drawdown_lines[0]
		self.assertTrue(
			frappe.db.exists("Funding Reservation", {"caller_reference": root.requisition_reference}),
			"the Budget reservation from before the forced failure is expected to remain (D6)",
		)


class TestRevoke(RequisitionAuthoriseCase):
	def _authorised(self):
		prepared, submitted = self._submitted_via_hod_direct()
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		return prepared, result

	def test_revoke_releases_reservation_and_reverses_drawdown(self):
		prepared, authorised = self._authorised()
		version = frappe.get_doc("Requisition Version", authorised["requisition_version"])
		reservation_id = version.drawdown_lines[0].reservation_id
		drawdown_ref = version.drawdown_lines[0].planning_drawdown_reference
		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		result = authorise.revoke_unconsumed_authorisation(requisition=prepared["requisition"], reason="The department's stated need changed materially after authorisation.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(result["action"], "revoked")
		root.reload()
		self.assertEqual(root.current_state, "Revoked")
		self.assertEqual(frappe.db.get_value("Funding Reservation", reservation_id, "status"), "Released")
		self.assertEqual(frappe.db.get_value("Plan Drawdown Reference", drawdown_ref, "drawdown_state"), "Reversed")

	def test_revoke_is_blocked_after_handoff_consumption(self):
		prepared, authorised = self._authorised()
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		frappe.db.set_value("Procurement Requisition", root.name, "handoff_consumed_at", frappe.utils.now_datetime())
		frappe.set_user(fx.HOPF)
		root.reload()
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			authorise.revoke_unconsumed_authorisation(requisition=prepared["requisition"], reason="Attempted revoke after consumption, must be refused.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_HANDOFF_CONSUMED")


class TestFundingAndBalanceGuards(RequisitionAuthoriseCase):
	def test_authorisation_fails_with_a_named_shortfall_when_budget_is_insufficient(self):
		prepared, submitted = self._submitted_via_hod_direct(indicative_amount=50_000_000)
		# Exhaust the line's headroom between submission and authorisation.
		frappe.set_user(fx.HOPF)
		from kentender_procurement.procurement_planning.tests import fixtures as pln_fx
		from kentender_budget.api.budget_api import check_funding as budget_check, reserve_funding as budget_reserve

		checked = budget_check(
			plan_item="EXHAUST", plan_version="EXHAUST-V1", source_set_hash="exhaust-hash",
			allocations=[{"budget_line": pln_fx.BUDGET_LINE, "amount": 100_000_000, "plan_source_allocation": "EXHAUST-PSA"}], correlation_id=fx.key(),
			calling_module="Procurement Requisitions", caller_reference="EXHAUST",
		)
		budget_reserve(token=checked["token"], source_set_hash="exhaust-hash", idempotency_key=fx.key())

		frappe.set_user(fx.HOPF)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_FUNDING_UNAVAILABLE")
		root.reload()
		self.assertEqual(root.current_state, "Submitted to Procurement")
