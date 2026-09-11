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


class TestReleaseHandoffConsumption(RequisitionHandoffCase):
	"""TPR-CHG-001 v0.6 §10.4 step 3 / plan D7 — the release half of the seam."""

	def _consumed(self) -> str:
		authorised = self._authorised()
		frappe.set_user("Administrator")
		handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key())
		return authorised["handoff"]

	def test_the_consuming_tender_releases_and_the_handoff_is_eligible_again(self):
		name = self._consumed()
		frappe.set_user(fx.HOPF)
		result = handoff.release_handoff_consumption(handoff=name, tender="TND-0001", reason="Upstream correction required on the technical requirement.", idempotency_key=fx.key())
		self.assertEqual(result["action"], "released")
		self.assertEqual(result["released_from"]["tender_version"], "TND-0001-V1")
		doc = frappe.get_doc("Authorised Requisition Handoff", name)
		self.assertFalse(doc.consumed_at)
		self.assertEqual(doc.tender, "")
		self.assertFalse(frappe.db.get_value("Procurement Requisition", doc.requisition, "handoff_consumed_at"))
		from kentender_procurement.procurement_requisitions.services import read

		self.assertIn(name, [row["handoff"] for row in read.list_eligible_handoffs(user=fx.HOPF)])

	def test_release_replays_by_key(self):
		name = self._consumed()
		frappe.set_user(fx.HOPF)
		key = fx.key()
		first = handoff.release_handoff_consumption(handoff=name, tender="TND-0001", reason="Upstream correction.", idempotency_key=key)
		second = handoff.release_handoff_consumption(handoff=name, tender="TND-0001", reason="Upstream correction.", idempotency_key=key)
		self.assertEqual(first["action"], "released")
		self.assertTrue(second["idempotent"])

	def test_a_different_tender_cannot_release_it(self):
		name = self._consumed()
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			handoff.release_handoff_consumption(handoff=name, tender="TND-0002", reason="Wrong tender.", idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_HANDOFF_CONSUMED")

	def test_a_non_caller_role_is_refused(self):
		name = self._consumed()
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			handoff.release_handoff_consumption(handoff=name, tender="TND-0001", reason="Not my seam.", idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_RESPONSIBILITY_REQUIRED")

	def test_a_reason_is_required(self):
		name = self._consumed()
		frappe.set_user(fx.HOPF)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			handoff.release_handoff_consumption(handoff=name, tender="TND-0001", reason="  ", idempotency_key=fx.key())
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")


class TestListEligibleHandoffs(RequisitionHandoffCase):
	"""TPR-CHG-001 v0.6 §11.1 / plan D7 — the list half of the seam."""

	def test_an_authorised_unconsumed_handoff_is_listed_with_its_counts(self):
		authorised = self._authorised()
		from kentender_procurement.procurement_requisitions.services import read

		rows = read.list_eligible_handoffs(user=fx.HOPF)
		match = [r for r in rows if r["handoff"] == authorised["handoff"]]
		self.assertEqual(len(match), 1)
		row = match[0]
		self.assertEqual(row["handoff_version"], "1.3")
		self.assertEqual(row["product_pattern"], "IT Equipment")
		self.assertEqual(row["item_count"], 1)
		self.assertEqual(row["acceptance_requirement_count"], 1)
		self.assertTrue(row["requisition_reference"])

	def test_a_consumed_handoff_is_not_listed(self):
		authorised = self._authorised()
		handoff.record_handoff_consumption(handoff=authorised["handoff"], tender="TND-0001", tender_version="TND-0001-V1", template_key="IT-EQUIPMENT-OPEN-V1", template_version="1.1", idempotency_key=fx.key())
		from kentender_procurement.procurement_requisitions.services import read

		self.assertNotIn(authorised["handoff"], [r["handoff"] for r in read.list_eligible_handoffs(user=fx.HOPF)])

	def test_a_revoked_handoff_is_not_listed(self):
		authorised = self._authorised()
		requisition = frappe.db.get_value("Authorised Requisition Handoff", authorised["handoff"], "requisition")
		root = frappe.get_doc("Procurement Requisition", requisition)
		frappe.set_user(fx.HOPF)
		authorise.revoke_unconsumed_authorisation(requisition=requisition, reason="Revoked before any Tender consumed it.", expected_record_version=root.record_version, idempotency_key=fx.key())
		from kentender_procurement.procurement_requisitions.services import read

		self.assertNotIn(authorised["handoff"], [r["handoff"] for r in read.list_eligible_handoffs(user=fx.HOPF)])

	def test_an_auditor_reads_the_list_and_a_departmental_actor_gets_an_empty_list(self):
		authorised = self._authorised()
		from kentender_procurement.procurement_requisitions.services import read

		self.assertIn(authorised["handoff"], [r["handoff"] for r in read.list_eligible_handoffs(user=fx.AUDITOR)])
		self.assertEqual(read.list_eligible_handoffs(user=fx.AUTHOR), [])
		self.assertEqual(read.list_eligible_handoffs(user=fx.OUTSIDER), [])
