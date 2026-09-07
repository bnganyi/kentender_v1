# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10.2/D4 — `RecordHandoffConsumption`, the inbound
Tender Preparation would call once TPR-CHG-001 v0.5 exists (out of scope
this cycle per D4; this module is the seam's only real exerciser today)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import authorise, draft_commands as cmd, handoff, lifecycle
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionHandoffCase(IntegrationTestCase):
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

	def _authorised(self) -> dict:
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		prepared = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self._complete_draft(prepared)
		frappe.set_user(fx.HOD)
		root = frappe.get_doc("Procurement Requisition", prepared["requisition"])
		submitted = lifecycle.submit_requisition_to_procurement(requisition=prepared["requisition"], expected_record_version=root.record_version, idempotency_key=fx.key())
		frappe.set_user(fx.HOPF)
		root.reload()
		authorised = authorise.authorise_requisition(requisition=prepared["requisition"], task=submitted["task"], expected_record_version=root.record_version, idempotency_key=fx.key())
		return authorised


class TestRecordHandoffConsumption(RequisitionHandoffCase):
	def test_consumption_is_recorded_and_reflected_on_the_root(self):
		authorised = self._authorised()
		result = handoff.record_handoff_consumption(
			handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1",
			template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "consumed")
		doc = frappe.get_doc("Authorised Requisition Handoff", authorised["handoff"])
		self.assertEqual(doc.tender, "TND-0001")
		self.assertTrue(doc.consumed_at)
		root = frappe.get_doc("Procurement Requisition", frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "requisition"))
		self.assertTrue(root.handoff_consumed_at)

	def test_the_same_tender_replaying_is_a_no_op(self):
		authorised = self._authorised()
		key = fx.key()
		first = handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=key)
		second = handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=key)
		self.assertEqual(first["handoff"], second["handoff"])
		self.assertTrue(second["idempotent"])

	def test_a_second_different_tender_is_refused(self):
		authorised = self._authorised()
		handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=fx.key())
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0002", tender_version="TND-0002-V1", template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_HANDOFF_CONSUMED")

	def test_revoke_is_then_blocked_by_the_existing_guard(self):
		"""Not a new rule here — `authorise.py`'s own `REQ_HANDOFF_CONSUMED`
		guard, exercised end to end through the real consumption path
		rather than by setting the field directly."""
		authorised = self._authorised()
		handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-DEFAULT", template_version="1.0", idempotency_key=fx.key())
		requisition = frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "requisition")
		root = frappe.get_doc("Procurement Requisition", requisition)
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			authorise.revoke_unconsumed_authorisation(requisition=requisition, reason="Testing the consumed-handoff revoke guard end to end.", expected_record_version=root.record_version, idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_HANDOFF_CONSUMED")
