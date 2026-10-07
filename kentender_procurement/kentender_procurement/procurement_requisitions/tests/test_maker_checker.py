# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.14 §7.2/§7.3/§6.3 — the maker-checker rules on every path, the
submission-time rechecks and category applicability, against the real world
(REQ19-AC-009, -045). AUD-REQ-002, -003, -004, -005."""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_core.services import responsibility_administration as administration
from kentender_procurement.procurement_requisitions.services import authorise as authorise_service, draft_commands as cmd, eligibility_gateway, lifecycle, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx
from kentender_procurement.procurement_requisitions.tests.test_draft_commands import RequisitionCase

NS = "KT_TEST_REQMC"
SITE_WIDE = ""


class MakerCheckerCase(RequisitionCase):
	def setUp(self):
		super().setUp()
		self.addCleanup(self.release_grants)

	def release_grants(self):
		for name in frappe.get_all("User Responsibility Assignment", filters={"fixture_namespace": NS}, pluck="name"):
			administration.revoke(name, reason="Revoked inside the maker-checker test.", actor="Administrator")
		frappe.db.commit()

	def grant(self, user, role, unit):
		frappe.set_user("Administrator")
		administration.grant(user=user, business_role=role, organisation_unit=unit, fixture_namespace=NS, actor="Administrator")


class TestHeadOfDepartmentCannotCertifyWhatTheyPreparedOrSent(MakerCheckerCase):
	"""AUD-REQ-002"""

	def test_an_author_who_became_head_cannot_certify_the_draft_they_prepared(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)  # Grace prepares as a Departmental Author
		self.assertEqual(frappe.db.get_value("Requisition Version", records.load(requisition)[1].name, "prepared_capacity"), "Departmental Author")
		self.grant(fx.AUTHOR, "Head of User Department", fx.ou_alpha())
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_SOD_BLOCKED")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Draft")
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": requisition, "business_role": "Head of Procurement Function"}), 0)

	def test_a_different_head_still_certifies_an_authors_draft_and_a_head_still_submits_their_own(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		frappe.set_user(fx.HOD)
		lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Submitted to Procurement")

	def test_sending_records_who_sent_it_and_that_person_cannot_then_approve_it(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		version = records.load(requisition)[1]
		self.assertEqual(version.sent_for_approval_by, fx.AUTHOR)
		self.assertTrue(version.sent_for_approval_at)
		# a second Author sends it; the first, who only prepared it, is not the sender
		frappe.db.set_value("Requisition Version", version.name, {"prepared_by": fx.HOPF, "sent_for_approval_by": fx.AUTHOR}, update_modified=False)
		self.grant(fx.AUTHOR, "Head of User Department", fx.ou_alpha())
		frappe.set_user(fx.AUTHOR)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.submit_requisition_to_procurement(requisition=requisition, task=fx.open_task(requisition, "Head of User Department"), expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_SOD_BLOCKED")

	def test_the_offers_agree_with_the_command(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		from kentender_procurement.procurement_requisitions.services import read

		root = frappe.get_doc("Procurement Requisition", requisition)
		# Charles is a lead Head who is not a lead Author: offered Submit on an Author's Draft ...
		self.assertTrue(read.get_requisition_editor(root=root, actor=fx.HOPF)["actions"]["submit_to_procurement"])
		# ... but not on the Draft he prepared himself as an Author in another capacity.
		frappe.db.set_value("Requisition Version", records.load(requisition)[1].name, "prepared_by", fx.HOPF, update_modified=False)
		self.assertFalse(read.get_requisition_editor(root=root, actor=fx.HOPF)["actions"]["submit_to_procurement"])


class TestPreparerCannotAuthorise(MakerCheckerCase):
	"""AUD-REQ-003 — the preparer is not also the Procurement authoriser."""

	def test_the_actor_who_prepared_the_version_cannot_authorise_it(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)  # Grace prepares
		fx.send(requisition)
		fx.submit_as_hod(requisition)  # Peter certifies
		self.grant(fx.AUTHOR, "Head of Procurement Function", SITE_WIDE)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.authorise(requisition, user=fx.AUTHOR)
		self.assertCode(ctx, "REQ_SOD_BLOCKED")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Submitted to Procurement")
		self.assertEqual(fx.authorise(requisition)["action"], "authorised")  # the independent HOPF still can

	def test_the_task_view_does_not_offer_authorise_to_the_preparer(self):
		from kentender_procurement.procurement_requisitions.services import read

		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		fx.submit_as_hod(requisition)
		self.grant(fx.AUTHOR, "Head of Procurement Function", SITE_WIDE)
		task = fx.open_task(requisition, "Head of Procurement Function")
		self.assertFalse(read.get_procurement_authorisation_task(task=task, user=fx.AUTHOR)["actions"]["authorise"])


class TestSubmissionRechecksOnTheApprovalPath(MakerCheckerCase):
	"""AUD-REQ-004 — submitting from Awaiting Department Approval repeats the §7.2 rechecks."""

	def _gone(self, *args, **kwargs):
		projection = self._real(*args, **kwargs)
		return {**projection, "sources": [{**s, "remaining_quantity": "0", "remaining_amount": "0.00"} for s in projection.get("sources", [])]}

	def test_a_balance_that_changed_after_sending_stops_the_submission(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		self._real = eligibility_gateway.get_requisition_eligible_plan_item
		task = fx.open_task(requisition, "Head of User Department")
		frappe.set_user(fx.HOD)
		with patch.object(lifecycle.eligibility_gateway, "get_requisition_eligible_plan_item", side_effect=self._gone):
			with self.assertRaises(ProcurementRequisitionsError) as ctx:
				lifecycle.submit_requisition_to_procurement(requisition=requisition, task=task, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_BLOCKING_FINDINGS")
		self.assertIn("BALANCE_CHANGED", [f["code"] for f in ctx.exception.detail["findings"]])
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Awaiting Department Approval")
		self.assertEqual(frappe.db.count("Requisition Task", {"requisition": requisition, "business_role": "Head of Procurement Function"}), 0)

	def test_an_unsupported_product_after_sending_stops_the_submission(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		task = fx.open_task(requisition, "Head of User Department")
		frappe.set_user(fx.HOD)
		failure = ProcurementRequisitionsError("REQ_PRODUCT_UNSUPPORTED", "unsupported")
		with patch.object(lifecycle.compatibility, "require_compatible", side_effect=failure):
			with self.assertRaises(ProcurementRequisitionsError) as ctx:
				lifecycle.submit_requisition_to_procurement(requisition=requisition, task=task, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_PRODUCT_UNSUPPORTED")

	def test_an_unchanged_world_still_submits_from_the_approval_task(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		fx.send(requisition)
		self.assertEqual(fx.submit_as_hod(requisition)["action"], "submitted")


class TestCategoryApplicabilityIsEnforcedByTheCommands(MakerCheckerCase):
	"""AUD-REQ-005"""

	def _monitors(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		view = fx.editor(requisition)
		rows = [{"drawdown_line_id": r["drawdown_line_id"], "quantity": r["quantity"], "intended_use": f"Clinical display for {r['department']} staff"} for r in view["equipment"]["add_rows"] if r["quantity"] > 0]
		cmd.add_same_specification_items(requisition=requisition, shared={"equipment_category": "Monitor", "item_name": "Clinic monitors"}, rows=rows, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		return requisition

	def test_a_printer_only_row_is_refused_on_monitors_and_a_monitor_row_is_accepted(self):
		requisition = self._monitors()
		view = fx.editor(requisition)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.add_technical_requirement(requisition=requisition, values={"characteristic_key": "print_speed", "value": 30, "applies_to_scope": "All items"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_CONTROL_INVALID")
		self.assertIn("Print speed", str(ctx.exception))
		self.assertNotIn("print_speed", [r.characteristic_key for r in records.load(requisition)[2].technical_requirements])
		added = cmd.add_technical_requirement(requisition=requisition, values={"characteristic_key": "display_resolution", "value": "QHD", "applies_to_scope": "All items"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertTrue(added["ok"])

	def test_a_category_change_that_strands_a_confirmed_row_blocks_the_submission_until_it_is_removed(self):
		requisition = self._monitors()
		view = fx.editor(requisition)
		cmd.add_technical_requirement(requisition=requisition, values={"characteristic_key": "display_resolution", "value": "QHD", "applies_to_scope": "All items"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		view = fx.editor(requisition)
		ids = [r["requisition_item_id"] for r in view["equipment"]["rows"]]
		cmd.update_shared_item_details(requisition=requisition, requisition_item_ids=ids, shared={"equipment_category": "Printer", "item_name": "Clinic printers"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		package_version = records.load(requisition)[2]
		report = cmd.validation.validate(version=records.version_dict(records.load(requisition)[1]), package=records.package_dict(package_version), eligibility={})
		stranded = [f for f in report["findings"] if f["code"] == "CONTROL_INVALID" and "Display resolution" in f["message"]]
		self.assertEqual(len(stranded), 1)
		self.assertEqual(stranded[0]["severity"], "Blocking")
