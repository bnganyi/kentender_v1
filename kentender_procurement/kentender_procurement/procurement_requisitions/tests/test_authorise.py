# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §7.2/§9.1A/§9.2 — one-transaction authorisation,
revocation and guarded consumption (REQ19-AC-025/026/027/028/029/030/031/040/
041/045/057/058/069/070/074, REQ-SMK-01/08/09/13/14)."""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe

from kentender_procurement.procurement_requisitions.services import authorise as authorise_service, envelope, handoff, lifecycle, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase
from kentender_procurement.tests.two_connections import BLOCKED_FOR, WAIT, Conn


def _effects(item_id: str, reference: str) -> tuple[int, int]:
	return (
		frappe.db.count("Funding Reservation", {"caller_reference": reference, "status": ("in", ("Active", "Partially Converted"))}),
		frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id, "drawdown_state": "Active"}),
	)


class TestAuthorise(RequisitionCase):
	def test_one_transaction_creates_every_effect_one_reservation_per_line_and_a_v14_handoff(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.submitted(item_id)
		result = fx.authorise(requisition)
		root, version, _ = records.load(requisition)
		self.assertEqual(root.current_state, "Authorised")
		self.assertEqual(len(result["reservations"]), 2)
		self.assertEqual(len(set(result["reservations"])), 2)
		self.assertEqual({l.reservation_id for l in version.drawdown_lines}, set(result["reservations"]))
		self.assertEqual(_effects(item_id, root.requisition_reference), (2, 2))
		self.assertTrue(frappe.db.get_value("Plan Item", item_id, "scope_locked_since"))
		payload = json.loads(frappe.db.get_value("Authorised Requisition Handoff", root.handoff, "payload_json"))
		self.assertEqual(payload["handoff_version"], "1.4")
		self.assertEqual(len(payload["drawdown_lines"]), 2)
		self.assertTrue(all(isinstance(l["requested_value"], str) for l in payload["drawdown_lines"]))
		self.assertEqual(len(payload["compatibility"]), 9)
		self.assertEqual(len(payload["technical_requirements"]), 11)
		self.assertEqual(len(payload["acceptance_requirements"]), 5)
		self.assertIn("reservation_rule_snapshot_ids", payload)
		self.assertNotIn("target_percent", json.dumps(payload))
		self.assertEqual(frappe.db.count("Tender", {"requisition_handoff": root.handoff}) if frappe.db.exists("DocType", "Tender") else 0, 0)
		# still open until Tender Preparation consumes it
		self.assertEqual(root.open_slot_key, item_id)

	def test_a_forced_failure_after_the_owner_calls_rolls_every_effect_back(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")
		with patch.object(handoff, "build_and_insert", side_effect=RuntimeError("handoff failed")):
			with self.assertRaises(RuntimeError):
				fx.authorise(requisition)
		self.assertEqual(_effects(item_id, reference), (0, 0))
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Submitted to Procurement")
		self.assertFalse(frappe.db.get_value("Plan Item", item_id, "scope_locked_since"))

	def test_insufficient_funding_creates_nothing(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")
		real = authorise_service.funding_gateway.check_funding

		def short(**kwargs):
			result = real(**kwargs)
			result["all_sufficient"] = False
			result["lines"] = [{**l, "sufficient": False, "shortfall": "10000000.00"} for l in result["lines"]]
			return result

		with patch.object(authorise_service.funding_gateway, "check_funding", side_effect=short):
			with self.assertRaises(ProcurementRequisitionsError) as ctx:
				fx.authorise(requisition)
		self.assertCode(ctx, "REQ_FUNDING_UNAVAILABLE")
		self.assertEqual(ctx.exception.detail["lines"][0]["shortfall"], "10000000.00")
		self.assertEqual(_effects(item_id, reference), (0, 0))

	def test_the_submitting_hod_cannot_authorise(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id, fx.HOPF)
		frappe.set_user(fx.HOPF)
		lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.authorise(requisition)
		self.assertCode(ctx, "REQ_SOD_BLOCKED")

	def test_a_planning_hold_blocks_authorisation_with_plannings_own_code(self):
		from kentender_procurement.procurement_planning.services import plan_requisition

		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		frappe.set_user(fx.HOD)
		plan_requisition.receive_plan_item_correction_request(plan_item_id=item_id, requisition_reference="REQ-OTHER-HOLD", requisition_version="RQV-OTHER", reason="Another requisition found a wrong Budget Line on this item.", idempotency_key=fx.key())
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.authorise(requisition)
		self.assertCode(ctx, "PLN_ITEM_AUTHORISATION_HELD")


class TestRevokeAndConsume(RequisitionCase):
	def _authorised(self):
		_, item_id = fx.active_item()
		requisition = fx.submitted(item_id)
		fx.authorise(requisition)
		return item_id, requisition

	def test_revoke_reverses_each_drawdown_and_reservation_once_and_keeps_the_scope_marker(self):
		item_id, requisition = self._authorised()
		reference = frappe.db.get_value("Procurement Requisition", requisition, "requisition_reference")
		frappe.set_user(fx.HOPF)
		authorise_service.revoke_unconsumed_authorisation(requisition=requisition, reason="The authorised warranty terms must be corrected before tendering.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Revoked")
		self.assertEqual(_effects(item_id, reference), (0, 0))
		self.assertTrue(frappe.db.get_value("Plan Item", item_id, "scope_locked_since"))

	def test_consumption_binds_one_tender_frees_the_slot_and_blocks_revocation(self):
		item_id, requisition = self._authorised()
		root = frappe.get_doc("Procurement Requisition", requisition)
		handoff.record_handoff_consumption(handoff=root.handoff, tender="TND-TEST-1", tender_version="TNV-1", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key())
		again = handoff.record_handoff_consumption(handoff=root.handoff, tender="TND-TEST-1", tender_version="TNV-1", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key())
		self.assertTrue(again["idempotent"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			handoff.record_handoff_consumption(handoff=root.handoff, tender="TND-TEST-2", tender_version="TNV-2", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_HANDOFF_CONFLICT")
		self.assertFalse(frappe.db.get_value("Procurement Requisition", requisition, "open_slot_key"))
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			authorise_service.revoke_unconsumed_authorisation(requisition=requisition, reason="Too late: Tender Preparation already began.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_HANDOFF_CONSUMED")

	def test_consumption_queues_on_the_requisition_root_without_holding_the_handoff(self):
		"""AUD-XC-109: authorise, revoke and consume lock Requisition root first,
		then handoff. Consumption used to take the handoff first and then wait on
		the root a revocation held, which is an AB-BA deadlock. While consumption
		waits for the root it must not hold the handoff row."""
		item_id, requisition = self._authorised()
		handoff_name = frappe.db.get_value("Procurement Requisition", requisition, "handoff")
		frappe.db.commit()
		holder = Conn("Administrator", lambda: envelope.locked("Procurement Requisition", requisition), hold=True)
		self.assertTrue(holder.ran.wait(WAIT))
		self.assertIsNone(holder.error, holder.error)
		consumer = Conn(
			"Administrator",
			lambda: handoff.record_handoff_consumption(handoff=handoff_name, tender="TND-LOCK-1", tender_version="TNV-1", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key()),
		)
		self.assertFalse(consumer.finished.wait(BLOCKED_FOR), "consumption must wait for the root lock")
		try:
			frappe.db.sql("select name from `tabAuthorised Requisition Handoff` where name=%s for update nowait", handoff_name)
		except Exception as exc:  # noqa: BLE001 - any lock-wait failure is the defect
			holder.commit()
			consumer.finished.wait(WAIT)
			frappe.db.rollback()
			self.fail(f"consumption holds the handoff row while it waits for the Requisition root: {exc!r}")
		frappe.db.rollback()
		holder.commit()
		self.assertTrue(consumer.finished.wait(WAIT))
		self.assertIsNone(consumer.error, consumer.error)
		frappe.db.commit()
		self.assertTrue(frappe.db.get_value("Authorised Requisition Handoff", handoff_name, "consumed_at"))

	def test_a_revoked_handoff_cannot_be_consumed(self):
		item_id, requisition = self._authorised()
		frappe.set_user(fx.HOPF)
		authorise_service.revoke_unconsumed_authorisation(requisition=requisition, reason="The authorised warranty terms must be corrected before tendering.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		handoff_name = frappe.db.get_value("Procurement Requisition", requisition, "handoff")
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			handoff.record_handoff_consumption(handoff=handoff_name, tender="TND-TEST-3", tender_version="TNV-3", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_HANDOFF_CONFLICT")

	def test_a_revoked_root_can_open_a_corrected_draft_while_its_baseline_is_eligible(self):
		from kentender_procurement.procurement_requisitions.services import correction

		item_id, requisition = self._authorised()
		frappe.set_user(fx.HOPF)
		authorise_service.revoke_unconsumed_authorisation(requisition=requisition, reason="The authorised warranty terms must be corrected before tendering.", expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		frappe.set_user(fx.AUTHOR)
		correction.create_requisition_correction_draft(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		root, version, package_version = records.load(requisition)
		self.assertEqual((root.current_state, version.version_status, root.open_slot_key), ("Draft", "Draft", item_id))
		self.assertEqual(package_version.standard_package_review_state, "Review required")
		self.assertFalse(any(l.reservation_id for l in version.drawdown_lines))
