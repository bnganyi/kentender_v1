# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10.2 — Draft-stage command tests, against a real
single-source Active, funded Plan Item from Procurement Planning's own
fixture world (D13)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_requisitions.services import draft_commands as cmd
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError
from kentender_procurement.procurement_requisitions.tests import fixtures as fx


class RequisitionDraftCase(IntegrationTestCase):
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
		fx.wipe_planning_rows()  # Planning's own per-test isolation; without
		# this, active_item() reuses the prior test's already-progressed DPP
		# (PLN_DPP_STALE) instead of starting a fresh one.
		self.addCleanup(frappe.set_user, "Administrator")

	def prepare(self, **kwargs) -> dict:
		_, item_id = fx.active_item(**kwargs)
		frappe.set_user(fx.AUTHOR)
		return cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())


class TestPrepare(RequisitionDraftCase):
	def test_prepare_creates_a_draft_root_version_and_package(self):
		result = self.prepare()
		self.assertEqual(result["action"], "created")
		root = frappe.get_doc("Procurement Requisition", result["requisition"])
		self.assertEqual(root.current_state, "Draft")
		self.assertTrue(root.requisition_reference.startswith("REQ-MOH-"))
		version = frappe.get_doc("Requisition Version", result["requisition_version"])
		self.assertEqual(version.version_status, "Draft")
		self.assertEqual(len(version.drawdown_lines), 1)
		self.assertAlmostEqual(version.drawdown_lines[0].requested_value, 50_000_000)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", result["package_version"])
		self.assertEqual(package_version.version_status, "Draft")

	def test_prepare_is_idempotent_by_key(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		key = fx.key()
		first = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=key)
		second = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=key)
		self.assertEqual(first["requisition"], second["requisition"])
		self.assertTrue(second["idempotent"])

	def test_prepare_reuses_the_open_draft_on_a_second_distinct_call(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.AUTHOR)
		first = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		second = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self.assertEqual(second["action"], "reused")
		self.assertEqual(first["requisition"], second["requisition"])

	def test_a_plain_planner_cannot_prepare(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.PLANNER)
		with self.assertRaises(frappe.DoesNotExistError):
			cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())

	def test_head_of_user_department_may_prepare_directly(self):
		_, item_id = fx.active_item()
		frappe.set_user(fx.HOD)
		result = cmd.prepare_it_equipment_requisition(plan_item_id=item_id, idempotency_key=fx.key())
		self.assertEqual(result["action"], "created")


class TestSummaryAndItems(RequisitionDraftCase):
	def test_save_summary_updates_title_location_date(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		result = cmd.save_requisition_summary(
			requisition=prepared["requisition"],
			values={"requirement_title": "Updated title", "delivery_location": "", "latest_delivery_date": "2027-09-30"},
			expected_record_version=0, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "saved")
		version = frappe.get_doc("Requisition Version", prepared["requisition_version"])
		self.assertEqual(version.requirement_title, "Updated title")

	def test_add_item_proposes_baseline_rows(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		result = cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": frappe.get_doc("Requisition Version", prepared["requisition_version"]).drawdown_lines[0].drawdown_line_id, "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "intended_use": "Clinical training"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "added")
		package_version.reload()
		proposed_keys = {r.characteristic_key for r in package_version.technical_requirements if r.applies_to_id == result["row_id"]}
		self.assertIn("electrical_compatibility", proposed_keys)
		self.assertIn("new_unused_equipment", proposed_keys)
		self.assertIn("storage_type", proposed_keys)
		for row in package_version.technical_requirements:
			self.assertEqual(row.row_status, "Proposed")

	def test_a_second_item_of_the_same_category_widens_the_shared_baseline_to_all_items(self):
		"""§13.7's own fixture: two Business laptops items share one set of
		baseline characteristics — "applies_to is All items, so nothing is
		entered twice." Confirmed live: without this, the naive per-item
		version doubled every shared characteristic (22 rows instead of the
		fixture's 11) the moment a second same-category item was added."""
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		line_id = frappe.get_doc("Requisition Version", prepared["requisition_version"]).drawdown_lines[0].drawdown_line_id
		first = cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": line_id, "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "intended_use": "Clinical training"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		package_version.reload()
		second = cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": line_id, "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 150, "intended_use": "Field deployment"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		package_version.reload()
		rows_by_key = {}
		for row in package_version.technical_requirements:
			rows_by_key.setdefault(row.characteristic_key, []).append(row)
		for key in ("electrical_compatibility", "new_unused_equipment", "storage_type"):
			self.assertEqual(len(rows_by_key[key]), 1, f"{key} should appear once, not once per item")
			self.assertEqual(rows_by_key[key][0].applies_to_scope, "All items")
		# A value-less proposal (e.g. Memory) still widens by key alone —
		# both items get the same "not yet set" placeholder to confirm once.
		self.assertEqual(len(rows_by_key["memory"]), 1)
		self.assertEqual(rows_by_key["memory"][0].applies_to_scope, "All items")

	def test_a_baseline_row_proposed_with_a_default_value_carries_its_display_text(self):
		"""Found live on the Department task screen (REQ-DES-08), which
		renders `required_value_display` directly with no fallback parser:
		a baseline proposal with a default (e.g. "storage_type": "NVMe
		SSD") had `required_value_json` but never `required_value_display`,
		so the screen showed a blank cell for a Confirmed row."""
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": frappe.get_doc("Requisition Version", prepared["requisition_version"]).drawdown_lines[0].drawdown_line_id, "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "intended_use": "Clinical training"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		package_version.reload()
		storage_type_row = next(r for r in package_version.technical_requirements if r.characteristic_key == "storage_type")
		self.assertEqual(storage_type_row.required_value_display, "NVMe SSD")

	def test_remove_item_blocked_while_technical_row_still_references_it(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		added = cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": "DL-001", "equipment_category": "Monitor", "item_name": "Monitor", "quantity": 1, "intended_use": "Test"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		package_version.reload()
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.remove_requisition_item(
				requisition=prepared["requisition"], requisition_item_id=added["row_id"],
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_QUANTITY_MISMATCH")


class TestTechnicalRequirements(RequisitionDraftCase):
	def _prepared_with_item(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		added = cmd.add_requisition_item(
			requisition=prepared["requisition"],
			values={"plan_item_line_id": "DL-001", "equipment_category": "Laptop", "item_name": "Business laptops", "quantity": 100, "intended_use": "Clinical training"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		return prepared, added["row_id"]

	def test_confirm_proposed_requirement_flips_status(self):
		prepared, item_row_id = self._prepared_with_item()
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		row = next(r for r in package_version.technical_requirements if r.characteristic_key == "electrical_compatibility")
		result = cmd.confirm_proposed_requirement(
			requisition=prepared["requisition"], technical_requirement_id=row.technical_requirement_id,
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "updated")
		package_version.reload()
		confirmed = next(r for r in package_version.technical_requirements if r.technical_requirement_id == row.technical_requirement_id)
		self.assertEqual(confirmed.row_status, "Confirmed")

	def test_confirming_a_value_less_proposed_row_without_a_value_is_rejected(self):
		"""A baseline rule that proposes no default (Memory, Storage
		capacity) must not be confirmable bare — that would silently
		produce a "Confirmed" row requiring nothing, the exact failure
		REQ-AC-011's visible confirm-or-remove moment exists to prevent."""
		prepared, item_row_id = self._prepared_with_item()
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		row = next(r for r in package_version.technical_requirements if r.characteristic_key == "memory")
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.confirm_proposed_requirement(
				requisition=prepared["requisition"], technical_requirement_id=row.technical_requirement_id,
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")

	def test_confirming_a_value_less_proposed_row_with_a_value_sets_it_and_confirms(self):
		prepared, item_row_id = self._prepared_with_item()
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		row = next(r for r in package_version.technical_requirements if r.characteristic_key == "memory")
		result = cmd.confirm_proposed_requirement(
			requisition=prepared["requisition"], technical_requirement_id=row.technical_requirement_id,
			expected_record_version=package_version.record_version, idempotency_key=fx.key(), value=16,
		)
		self.assertEqual(result["action"], "updated")
		package_version.reload()
		confirmed = next(r for r in package_version.technical_requirements if r.technical_requirement_id == row.technical_requirement_id)
		self.assertEqual(confirmed.row_status, "Confirmed")
		self.assertEqual(confirmed.required_value_display, "16 GB")

	def test_add_technical_requirement_validates_against_the_catalogue(self):
		prepared, item_row_id = self._prepared_with_item()
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.add_technical_requirement(
				requisition=prepared["requisition"],
				values={"characteristic_key": "memory", "value": 100000, "applies_to_scope": "All items"},
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")

	def test_add_technical_requirement_with_a_valid_value_succeeds(self):
		prepared, item_row_id = self._prepared_with_item()
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		result = cmd.add_technical_requirement(
			requisition=prepared["requisition"],
			values={"characteristic_key": "processor_requirement", "value": "64-bit business-class processor, minimum 10 cores or equivalent benchmark", "applies_to_scope": "All items"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "added")


class TestWarrantyServiceAcceptance(RequisitionDraftCase):
	def test_save_warranty_and_support(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		result = cmd.save_warranty_and_support(
			requisition=prepared["requisition"],
			values={"minimum_warranty_months": 36, "onsite_support_required": 1, "maximum_support_response_hours": 8, "manufacturer_support_required": 1, "service_location_constraint": "Within Kenya"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "saved")
		package_version.reload()
		self.assertEqual(package_version.minimum_warranty_months, 36)

	def test_save_warranty_and_support_rejects_an_out_of_range_warranty(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_warranty_and_support(
				requisition=prepared["requisition"],
				values={"minimum_warranty_months": 121},
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")

	def test_save_warranty_and_support_requires_support_response_hours_only_when_onsite_is_yes(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_warranty_and_support(
				requisition=prepared["requisition"],
				values={"onsite_support_required": 0, "maximum_support_response_hours": 8},
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")

	def test_save_warranty_and_support_rejects_an_out_of_range_support_response(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_warranty_and_support(
				requisition=prepared["requisition"],
				values={"onsite_support_required": 1, "maximum_support_response_hours": 169},
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")

	def test_save_warranty_and_support_rejects_an_unknown_service_location(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		with self.assertRaises(ProcurementRequisitionsError) as ctx:
			cmd.save_warranty_and_support(
				requisition=prepared["requisition"],
				values={"service_location_constraint": "Overseas"},
				expected_record_version=package_version.record_version, idempotency_key=fx.key(),
			)
		self.assertEqual(ctx.exception.code, "REQ_CONTROL_INVALID")

	def test_add_acceptance_requirement(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		package_version = frappe.get_doc("IT Equipment Requirement Package Version", prepared["package_version"])
		result = cmd.add_acceptance_requirement(
			requisition=prepared["requisition"],
			values={"applies_to_scope": "All items", "check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
			expected_record_version=package_version.record_version, idempotency_key=fx.key(),
		)
		self.assertEqual(result["action"], "added")
		self.assertTrue(result["row_id"].startswith("ACC-"))


class TestValidateRequisition(RequisitionDraftCase):
	def test_validate_reports_blocking_findings_for_an_empty_draft(self):
		prepared = self.prepare()
		frappe.set_user(fx.AUTHOR)
		report = cmd.validate_requisition(requisition=prepared["requisition"])
		self.assertGreater(report["blocking_count"], 0)
		self.assertFalse(report["steps"][5]["complete"])
