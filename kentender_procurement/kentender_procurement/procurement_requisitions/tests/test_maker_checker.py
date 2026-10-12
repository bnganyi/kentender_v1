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

	def test_a_different_head_cannot_certify_an_authors_draft_directly_it_goes_through_the_approval_task(self):
		"""RG-14 — REQ v1.14 §7.1: only "a Head of User Department preparing directly" submits a Draft; the Draft
		an Author prepared goes through the department approval task, whoever the lead Head is."""
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)
		frappe.set_user(fx.HOD)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_SOD_BLOCKED")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Draft")
		fx.send(requisition)
		self.assertEqual(fx.submit_as_hod(requisition)["action"], "submitted")  # the approval task is the way

	def test_a_head_preparing_directly_still_submits_their_own_draft(self):
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id, fx.HOD)
		frappe.set_user(fx.HOD)
		lifecycle.submit_requisition_to_procurement(requisition=requisition, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Submitted to Procurement")

	def test_a_head_who_edited_an_authors_draft_cannot_then_approve_it(self):
		"""RG-14 — "prepared" is every editor, read from the immutable command audit, not only the creator."""
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)  # Grace prepares
		frappe.set_user(fx.HOD)  # Peter, the lead Head, edits the shared request information as a Head
		view = fx.editor(requisition, fx.HOD)
		cmd.save_requisition_summary(requisition=requisition, values={"requirement_title": "Edited by the Head"}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		fx.send(requisition)
		task = fx.open_task(requisition, "Head of User Department")
		frappe.set_user(fx.HOD)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			lifecycle.submit_requisition_to_procurement(requisition=requisition, task=task, expected_record_version=fx.root_version(requisition), idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_SOD_BLOCKED")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Awaiting Department Approval")
		# the Head who never touched it still approves
		self.grant(fx.HOD_BETA, "Head of User Department", fx.ou_alpha())
		self.assertEqual(fx.submit_as_hod(requisition, fx.HOD_BETA)["action"], "submitted")

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
		# A lead Head who did not prepare the Draft is not offered Submit on an Author's Draft (RG-14): it goes through the approval task ...
		self.assertFalse(read.get_requisition_editor(root=root, actor=fx.HOPF)["actions"]["submit_to_procurement"])
		self.assertFalse(read.get_requisition_editor(root=root, actor=fx.HOD)["actions"]["submit_to_procurement"])
		# ... while the Head who prepared it directly is.
		frappe.db.set_value("Requisition Version", records.load(requisition)[1].name, {"prepared_by": fx.HOD, "prepared_capacity": "Head of User Department"}, update_modified=False)
		self.assertTrue(read.get_requisition_editor(root=root, actor=fx.HOD)["actions"]["submit_to_procurement"])


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

	def test_an_officer_who_edited_the_draft_cannot_authorise_it(self):
		"""RG-14 — the authoriser's "prepared" set is every editor, not only the creator."""
		_, item_id = fx.active_item()
		requisition = fx.complete_draft(item_id)  # Grace prepares
		frappe.set_user(fx.HOPF)  # Charles also holds the Head of User Department role and edits the Draft
		view = fx.editor(requisition, fx.HOPF)
		cmd.save_requisition_summary(requisition=requisition, values={"requirement_title": "Edited by Charles"}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		fx.send(requisition)
		fx.submit_as_hod(requisition)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			fx.authorise(requisition)
		self.assertCode(ctx, "REQ_SOD_BLOCKED")
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "current_state"), "Submitted to Procurement")

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
		rows = [{"drawdown_line_id": r["drawdown_line_id"], "quantity": r["room"], "intended_use": f"Clinical display for {r['department']} staff"} for r in view["equipment"]["add_rows"] if r["room"] > 0]
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

	def test_a_category_change_takes_the_item_out_of_a_row_that_no_longer_applies_and_blocks_until_reviewed(self):
		"""REQ v1.18 §6.5A (v1.17 read: the row was left stranded and flagged CONTROL_INVALID): the row that covered
		the monitors is taken off the items that are now printers, and the package must be reviewed again."""
		requisition = self._monitors()
		view = fx.editor(requisition)
		cmd.add_technical_requirement(requisition=requisition, values={"characteristic_key": "display_resolution", "value": "QHD", "applies_to_scope": "All items"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		view = fx.editor(requisition)
		ids = [r["requisition_item_id"] for r in view["equipment"]["rows"]]
		cmd.update_shared_item_details(requisition=requisition, requisition_item_ids=ids, shared={"equipment_category": "Printer", "item_name": "Clinic printers"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		package_version = records.load(requisition)[2]
		self.assertNotIn("display_resolution", {r.characteristic_key for r in package_version.technical_requirements if r.row_state != "Proposed"}, "the row covered nothing that remains")
		self.assertEqual(package_version.standard_package_review_state, "Review required")
		report = cmd.validation.validate(version=records.version_dict(records.load(requisition)[1]), package=records.package_dict(package_version), eligibility={})
		self.assertFalse([f for f in report["findings"] if f["code"] == "CONTROL_INVALID" and "Display resolution" in f["message"]])
		review = [f for f in report["findings"] if f["code"] == "PACKAGE_REVIEW_REQUIRED"]
		self.assertEqual(len(review), 1)
		self.assertEqual(review[0]["severity"], "Blocking")
