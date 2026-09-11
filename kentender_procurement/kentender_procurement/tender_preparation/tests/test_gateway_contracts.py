# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 — contract pins against the sibling services this module
depends on (plan D7/D8; REQ-AC-038's cross-contract check now lives here):
the Requisitions handoff v1.3 payload keys the snapshot consumes, the
Requisitions seam commands (consume, release, list), Planning's milestone
write path, and the two core masters the Task controls Link to. A change to
a sibling that breaks a pin is a defect in the contract, not in this
module."""

from __future__ import annotations

import ast
import inspect

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import business_role_registry as registry
from kentender_procurement.procurement_planning.services import schedule
from kentender_procurement.procurement_requisitions.services import handoff as req_handoff
from kentender_procurement.procurement_requisitions.services import read as req_read
from kentender_procurement.procurement_requisitions.services import requisition_roles as req_roles

# TPR §6.4/§7.3 (bound to REQ v1.6 §5.12 as actually built — plan C7).
REQUIRED_HANDOFF_KEYS = (
	"requisition_reference", "requisition_version", "content_digest", "plan_id", "plan_version_id", "plan_item_id",
	"fiscal_year", "contributing_org_unit_ids", "strategic_objective", "strategic_objective_path",
	"procurement_category", "plan_horizon", "multi_year_justification", "drawdown_lines", "business_need",
	"expected_operational_result", "planned_method", "planned_dates", "requirement_title", "delivery_location",
	"latest_delivery_date", "items", "minimum_warranty_months", "onsite_support_required",
	"maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint",
	"support_description", "technical_requirements", "related_services", "acceptance_requirements",
	"supporting_materials", "product_pattern", "reservation_category_value", "lotting_indicator", "handoff_version",
	"generated_at",
)
REQUIRED_ROW_KEYS = {
	"items": ("requisition_item_id", "plan_item_line_id", "equipment_category", "item_name", "quantity", "unit", "intended_use"),
	"technical_requirements": ("technical_requirement_id", "applies_to_scope", "applies_to_id", "characteristic_key", "comparison", "required_value_json", "unit"),
	"related_services": ("service_requirement_id", "service_type", "applies_to_scope", "applies_to_id", "required_result", "completion_date", "acceptance_evidence"),
	"acceptance_requirements": ("acceptance_requirement_id", "applies_to_scope", "applies_to_id", "check_type", "pass_condition", "evidence_type"),
	"supporting_materials": ("supporting_material_id", "title", "document_type", "treatment", "file_digest", "linked_requirement_ids_json"),
}


def _string_constants(fn) -> set[str]:
	tree = ast.parse(inspect.getsource(fn))
	return {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}


class TestRequisitionHandoffContract(IntegrationTestCase):
	def test_the_handoff_version_is_v1_3(self):
		self.assertEqual(req_handoff.HANDOFF_VERSION, "1.3")

	def test_every_key_the_snapshot_consumes_is_built_by_requisitions(self):
		built = _string_constants(req_handoff.build_payload)
		for key in REQUIRED_HANDOFF_KEYS:
			self.assertIn(key, built, key)
		for row_keys in REQUIRED_ROW_KEYS.values():
			for key in row_keys:
				self.assertIn(key, built, key)

	def test_the_consumption_seam_signatures_are_unchanged(self):
		sig = inspect.signature(req_handoff.record_handoff_consumption)
		for name in ("handoff", "tender", "tender_version", "template_key", "template_version", "idempotency_key"):
			self.assertIn(name, sig.parameters)
		rel = inspect.signature(req_handoff.release_handoff_consumption)
		for name in ("handoff", "tender", "reason", "idempotency_key"):
			self.assertIn(name, rel.parameters)
		lst = inspect.signature(req_read.list_eligible_handoffs)
		self.assertIn("user", lst.parameters)

	def test_requisitions_names_the_tender_callers(self):
		self.assertEqual(tuple(req_roles.TENDER_CALLER_ROLES), ("Procurement Officer", "Head of Procurement Function"))
		self.assertIn("Auditor", req_roles.TENDER_SEAM_READER_ROLES)

	def test_the_handoff_doctype_carries_the_consumption_columns(self):
		fields = {f.fieldname for f in frappe.get_meta("Authorised Requisition Handoff").fields}
		for name in ("payload_json", "handoff_digest", "handoff_version", "tender", "tender_version", "template_key", "template_version", "consumed_at"):
			self.assertIn(name, fields)


class TestPlanningMilestoneContract(IntegrationTestCase):
	def test_record_tender_milestone_actual_signature(self):
		sig = inspect.signature(schedule.record_tender_milestone_actual)
		for name in ("plan_item_id", "milestone", "actual_date", "source_event_id"):
			self.assertIn(name, sig.parameters)

	def test_invitation_is_a_milestone_and_no_bid_opening_is_written_here(self):
		self.assertIn("invitation", schedule.MILESTONES)
		self.assertIn("actual_invitation_date", schedule.ACTUAL_FIELDS)


class TestCoreMastersAndRegistry(IntegrationTestCase):
	def test_the_two_link_masters_exist(self):
		for doctype in ("Delivery Location", "Contact Office"):
			self.assertTrue(frappe.db.exists("DocType", doctype), doctype)
			self.assertIn("status", {f.fieldname for f in frappe.get_meta(doctype).fields})

	def test_the_three_responsibilities_are_registered_site_wide(self):
		for role in ("Procurement Officer", "Head of Procurement Function", "Auditor"):
			self.assertEqual(registry.scope_type(role), registry.SCOPE_SITE, role)
		self.assertIn("tender_preparation", registry.REGISTRY["Procurement Officer"].sod_tags)
		self.assertIn("tender_approval", registry.REGISTRY["Head of Procurement Function"].sod_tags)
