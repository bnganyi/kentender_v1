# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §10.2 Draft commands against the real Planning world
(REQ19-AC-001/002/004/005/006/008/011/039/048/049/051/088–090/113–115)."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import catalogue, draft_commands as cmd, records
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionCase(IntegrationTestCase):
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
		self.addCleanup(frappe.set_user, "Administrator")
		self.addCleanup(fx.wipe_requisition_rows)

	def assertCode(self, ctx, code):
		self.assertEqual(getattr(ctx.exception, "code", None), code, str(ctx.exception))


class TestPrepare(RequisitionCase):
	def test_creates_one_draft_with_exact_default_amounts_and_no_budget_or_planning_effect(self):
		_, item_id = fx.active_combined_item()
		prepared = fx.prepare(item_id)
		self.assertEqual(prepared["action"], "created")
		root, version, package_version = records.load(prepared["requisition"])
		self.assertEqual(root.current_state, "Draft")
		self.assertEqual(root.open_slot_key, item_id)
		self.assertTrue(root.plan_item_version_id)
		self.assertEqual({row.organisation_unit for row in root.contributing_org_units}, {fx.ou_alpha(), fx.ou_beta()})
		self.assertEqual(root.lead_org_unit_id, fx.ou_alpha())  # the larger drawn value leads
		self.assertEqual(sorted((l.requested_quantity, l.requested_value) for l in version.drawdown_lines), [("100", "20000000.00"), ("150", "30000000.00")])
		self.assertEqual(version.prepared_by, fx.AUTHOR)
		self.assertEqual(package_version.standard_package_review_state, "Not generated")
		self.assertEqual(frappe.db.count("Funding Reservation", {"calling_module": "Procurement Requisitions"}), 0)
		self.assertEqual(frappe.db.count("Plan Drawdown Reference", {"plan_item_id": item_id}), 0)

	def test_a_second_prepare_by_another_department_returns_the_open_record_not_a_duplicate(self):
		_, item_id = fx.active_combined_item()
		first = fx.prepare(item_id)
		again = fx.prepare(item_id, fx.HOD_BETA)
		self.assertEqual(again["action"], "existing")
		self.assertEqual(again["requisition"], first["requisition"])
		self.assertEqual(frappe.db.count("Procurement Requisition", {"plan_item_id": item_id}), 1)

	def test_the_database_guard_refuses_a_second_open_slot_even_when_the_read_missed_it(self):
		_, item_id = fx.active_item()
		fx.prepare(item_id)
		with patch.object(records, "open_root_for", return_value=""):
			with self.assertRaises(ProcurementRequisitionsError) as ctx:
				fx.prepare(item_id)
		self.assertCode(ctx, "REQ_OPEN_EXISTS")
		self.assertEqual(frappe.db.count("Procurement Requisition", {"plan_item_id": item_id}), 1)

	def test_an_incompatible_item_creates_nothing(self):
		_, item_id = fx.active_item()
		with patch("kentender_procurement.procurement_requisitions.services.compatibility.template_support", return_value={"template_key": "IT-EQUIPMENT-OPEN-V1", "available": True, "categories": ("None",), "county_residents": False, "method": "Restricted Tender"}):
			with self.assertRaises(ProcurementRequisitionsError) as ctx:
				fx.prepare(item_id)
		self.assertCode(ctx, "REQ_PRODUCT_UNSUPPORTED")
		self.assertEqual(ctx.exception.detail["test"], "procurement_method")
		self.assertEqual(frappe.db.count("Procurement Requisition", {"plan_item_id": item_id}), 0)

	def test_an_outsider_is_masked(self):
		_, item_id = fx.active_item()
		with self.assertRaises(frappe.DoesNotExistError):
			fx.prepare(item_id, fx.PLANNER)


class TestRequestDetails(RequisitionCase):
	def test_a_contributor_edits_only_their_own_line_and_never_shared_fields(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition, fx.CONTRIBUTOR)
		self.assertEqual(view["mode"], "contributor")
		beta = next(r for r in view["amounts"] if r["contributing_org_unit"] == fx.ou_beta())
		alpha = next(r for r in view["amounts"] if r["contributing_org_unit"] == fx.ou_alpha())
		self.assertTrue(beta["editable"])
		self.assertFalse(alpha["editable"])
		cmd.save_requisition_summary(requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": beta["drawdown_line_id"], "requested_quantity": "80", "requested_value": "16000000.00"}]}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		view = fx.editor(requisition, fx.CONTRIBUTOR)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_requisition_summary(requisition=requisition, values={"requirement_title": "A contributor retitling the shared request"}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_RESPONSIBILITY_REQUIRED")
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_requisition_summary(requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": alpha["drawdown_line_id"], "requested_quantity": "1", "requested_value": "1.00"}]}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_RESPONSIBILITY_REQUIRED")

	def test_amounts_are_exact_and_bounded_by_what_remains(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		line = view["amounts"][0]
		for value, code in (("50000000.01", "REQ_BALANCE_CHANGED"), ("1.005", "REQ_MONEY_PRECISION_INVALID"), (100.0, "REQ_MONEY_PRECISION_INVALID")):
			with self.subTest(value=value):
				with self.assertRaises(ProcurementRequisitionsError) as ctx:
					cmd.save_requisition_summary(requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": line["drawdown_line_id"], "requested_quantity": "1", "requested_value": value}]}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
				self.assertCode(ctx, code)

	def test_the_lead_follows_the_drawn_amounts(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		alpha = next(r for r in view["amounts"] if r["contributing_org_unit"] == fx.ou_alpha())
		cmd.save_requisition_summary(requisition=requisition, values={"drawdown_lines": [{"drawdown_line_id": alpha["drawdown_line_id"], "requested_quantity": "10", "requested_value": "1000000.00"}]}, expected_record_version=view["header"]["version_record_version"], idempotency_key=fx.key())
		self.assertEqual(frappe.db.get_value("Procurement Requisition", requisition, "lead_org_unit_id"), fx.ou_beta())


class TestSameSpecificationItems(RequisitionCase):
	def test_one_shared_definition_creates_one_item_per_source_and_the_laptop_proposal(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		result = fx.add_laptops(requisition)
		self.assertEqual(len(result["items"]), 2)
		self.assertEqual(result["review_state"], "Review required")
		root, version, package_version = records.load(requisition)
		self.assertEqual({(i.drawdown_line_id, i.quantity) for i in package_version.items}, {(l.drawdown_line_id, int(l.requested_quantity)) for l in version.drawdown_lines})
		self.assertEqual(package_version.standard_profile_key, "LAPTOP-REQUIREMENTS-V1")
		self.assertEqual(sum(1 for r in package_version.technical_requirements if r.row_state == "Proposed"), 11)
		self.assertEqual(sum(1 for r in package_version.acceptance_requirements if r.row_state == "Proposed"), 5)
		self.assertEqual(package_version.minimum_warranty_months, 36)

	def test_a_bad_row_creates_nothing(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		rows = [{"drawdown_line_id": r["drawdown_line_id"], "quantity": r["quantity"], "intended_use": "Field deployment for staff"} for r in view["equipment"]["add_rows"]]
		rows[1]["quantity"] = rows[1]["quantity"] - 10
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.add_same_specification_items(requisition=requisition, shared={"equipment_category": "Laptop", "item_name": "Business laptops"}, rows=rows, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_BATCH_ITEM_INVALID")
		self.assertIn(rows[1]["drawdown_line_id"], ctx.exception.detail["rows"])
		# REQ-DES-04-VALIDATION: the field says what it must be; the notice
		# states the whole mismatch in the board's words.
		wanted = rows[1]["quantity"] + 10
		self.assertEqual(ctx.exception.detail["rows"][rows[1]["drawdown_line_id"]], f"Must be {wanted:,} Each")
		name = next(r["department"] for r in view["equipment"]["add_rows"] if r["drawdown_line_id"] == rows[1]["drawdown_line_id"])
		self.assertEqual(str(ctx.exception), f"Requested equipment quantity for {name} is {wanted - 10:,} Each but the approved requirement requests {wanted:,} Each")
		self.assertEqual(len(records.load(requisition)[2].items), 0)

	def test_shared_edit_changes_every_named_item_and_a_category_change_regenerates_the_proposal(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.add_laptops(requisition)
		fx.apply_standard_package(requisition)
		view = fx.editor(requisition)
		ids = [r["requisition_item_id"] for r in view["equipment"]["rows"]]
		cmd.update_shared_item_details(requisition=requisition, requisition_item_ids=ids, shared={"equipment_category": "Desktop computer", "item_name": "Business desktops"}, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		package_version = records.load(requisition)[2]
		self.assertEqual({i.item_name for i in package_version.items}, {"Business desktops"})
		self.assertEqual(package_version.standard_package_review_state, "Review required")
		self.assertEqual(package_version.standard_profile_key, catalogue.CATALOGUE_PROFILE_KEY)
		# confirmed history is kept, the fresh proposal is added as Proposed
		self.assertTrue(any(r.row_state == "Confirmed" for r in package_version.technical_requirements))


class TestStandardPackage(RequisitionCase):
	def _ready(self):
		_, item_id = fx.active_item()
		requisition = fx.prepare(item_id)["requisition"]
		fx.fill_request_information(requisition)
		fx.add_laptops(requisition)
		return requisition

	def test_apply_records_exactly_the_visible_selection_and_marks_reviewed(self):
		requisition = self._ready()
		view = fx.editor(requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		technical[4]["selected"] = False  # clear Storage type
		acceptance[0]["pass_condition"] = "Delivered quantities equal the authorised delivery schedule"
		req = view["requirements"]
		cmd.apply_selected_requirement_package(requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"], technical=technical, acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		package_version = records.load(requisition)[2]
		self.assertEqual(package_version.standard_package_review_state, "Reviewed")
		self.assertEqual(len(package_version.technical_requirements), 10)
		self.assertTrue(all(r.row_state == "Confirmed" for r in package_version.technical_requirements + package_version.acceptance_requirements))
		self.assertNotIn("storage_type", {r.characteristic_key for r in package_version.technical_requirements})
		self.assertEqual(package_version.acceptance_requirements[0].pass_condition, "Delivered quantities equal the authorised delivery schedule")
		tasks = {t["key"]: t["status"] for t in fx.editor(requisition)["tasks"]}
		self.assertEqual(tasks, {"request_details": "Complete", "requirements": "Complete", "review_submit": "Not started"})

	def test_a_stale_proposal_is_refused_and_nothing_changes(self):
		requisition = self._ready()
		view = fx.editor(requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.apply_selected_requirement_package(requisition=requisition, profile_key="LAPTOP-REQUIREMENTS-V1", profile_version="1", proposal_digest="not-what-was-shown", technical=technical, acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_STANDARD_PROPOSAL_STALE")
		self.assertEqual(records.load(requisition)[2].standard_package_review_state, "Review required")

	def test_clearing_every_acceptance_check_is_refused(self):
		requisition = self._ready()
		view = fx.editor(requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		for row in acceptance:
			row["selected"] = False
		req = view["requirements"]
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.apply_selected_requirement_package(requisition=requisition, profile_key=req["profile_key"], profile_version=req["profile_version"], proposal_digest=req["proposal_digest"], technical=technical, acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		self.assertCode(ctx, "REQ_CONTROL_INVALID")

	def test_save_draft_keeps_review_required_and_confirms_nothing(self):
		requisition = self._ready()
		view = fx.editor(requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		technical[0]["selected"] = False
		cmd.save_requirement_proposal_draft(requisition=requisition, proposal_digest=view["requirements"]["proposal_digest"], technical=technical, acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		package_version = records.load(requisition)[2]
		self.assertEqual(package_version.standard_package_review_state, "Review required")
		self.assertEqual(len(package_version.technical_requirements), 10)
		self.assertTrue(all(r.row_state == "Proposed" for r in package_version.technical_requirements))

	def test_reset_restores_the_code_owned_proposal(self):
		requisition = self._ready()
		view = fx.editor(requisition)
		technical, acceptance, support = fx.visible_proposal(view)
		cmd.save_requirement_proposal_draft(requisition=requisition, proposal_digest=view["requirements"]["proposal_digest"], technical=technical[:3], acceptance=acceptance, support=support, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		view = fx.editor(requisition)
		cmd.reset_standard_values(requisition=requisition, expected_record_version=view["package_record_version"], idempotency_key=fx.key())
		package_version = records.load(requisition)[2]
		self.assertEqual(len([r for r in package_version.technical_requirements if r.row_state == "Proposed"]), 11)
		self.assertEqual(package_version.standard_package_review_state, "Review required")


class TestEditorProjection(RequisitionCase):
	def test_a_page_read_creates_nothing(self):
		_, item_id = fx.active_item()
		before = frappe.db.count("Procurement Requisition")
		from kentender_procurement.procurement_requisitions.services import read

		frappe.set_user(fx.AUTHOR)
		preview = read.get_start_preview(plan_item_id=item_id)
		self.assertEqual(preview["state"], "ready")
		self.assertTrue(preview["may_start"])
		self.assertEqual(frappe.db.count("Procurement Requisition"), before)

	def test_the_des03_base_projection(self):
		_, item_id = fx.active_combined_item()
		requisition = fx.prepare(item_id)["requisition"]
		view = fx.editor(requisition)
		self.assertEqual(view["kind"], "editor")
		self.assertEqual([(t["label"], t["status"]) for t in view["tasks"]], [("Request details", "Needs attention"), ("Requirements", "Not started"), ("Review and submit", "Not started")])
		self.assertEqual(view["header"]["badge"]["label"], "Draft")
		self.assertEqual(len(view["amounts"]), 2)
		self.assertFalse(any(r["changed"] for r in view["amounts"]))
		self.assertEqual(view["footer_hints"]["request_details"], "Select the delivery location.")
