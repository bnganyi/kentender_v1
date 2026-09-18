# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §3 — pins on every sibling contract Tenders consumes
(tracker TND-204): the Requisitions handoff seam (`list_eligible_handoffs`,
`record_handoff_consumption`, `release_handoff_consumption`, the v1.3 payload
keys the snapshot reads, the correction outcome keys), Planning's milestone
event envelope and per-proceeding read, Configuration's Publication-
obligations payload shape and the schedule-profile resolver, and the
site-setup rows the rule snapshot depends on. A change on the owner's side
fails here first, never as a silent snapshot gap."""

from __future__ import annotations

import inspect

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds import site_setup
from kentender_core.services import procurement_settings, regulatory_reference
from kentender_procurement.procurement_planning.services import schedule
from kentender_procurement.procurement_requisitions.services import handoff, lifecycle as req_lifecycle, read as req_read

HANDOFF_KEYS = {
	"requisition_reference", "requisition_version", "content_digest", "plan_id", "plan_version_id", "plan_item_id", "fiscal_year",
	"contributing_org_unit_ids", "strategic_objective", "strategic_objective_path", "procurement_category", "plan_horizon",
	"drawdown_lines", "business_need", "expected_operational_result", "planned_method", "planned_dates", "requirement_title",
	"delivery_location", "latest_delivery_date", "items", "minimum_warranty_months", "onsite_support_required",
	"maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description",
	"technical_requirements", "related_services", "acceptance_requirements", "supporting_materials", "product_pattern",
	"reservation_category_value", "lotting_indicator", "handoff_version", "generated_at", "decisions", "handoff_digest",
}


class TestRequisitionSeam(IntegrationTestCase):
	def test_seam_signatures(self):
		self.assertEqual(set(inspect.signature(req_read.list_eligible_handoffs).parameters), {"user"})
		self.assertEqual(
			set(inspect.signature(handoff.record_handoff_consumption).parameters),
			{"handoff", "tender", "tender_version", "template_key", "template_version", "idempotency_key"},
		)
		self.assertEqual(set(inspect.signature(handoff.release_handoff_consumption).parameters), {"handoff", "tender", "reason", "idempotency_key", "user"})
		self.assertEqual(handoff.HANDOFF_VERSION, "1.3")

	def test_payload_keys_the_snapshot_consumes(self):
		source = inspect.getsource(handoff.build_payload) + inspect.getsource(handoff.build_and_insert)
		for key in HANDOFF_KEYS:
			self.assertIn(f'"{key}"', source, key)
		for key in ("requisition_item_id", "plan_item_line_id", "equipment_category", "item_name", "quantity", "unit", "intended_use"):
			self.assertIn(f'"{key}"', source, key)
		for key in ("technical_requirement_id", "applies_to_scope", "applies_to_id", "characteristic_key", "comparison", "required_value_json"):
			self.assertIn(f'"{key}"', source, key)
		for key in ("acceptance_requirement_id", "check_type", "pass_condition", "evidence_type", "service_requirement_id", "supporting_material_id", "file_digest", "reservation_id"):
			self.assertIn(f'"{key}"', source, key)

	def test_correction_outcome_keys(self):
		source = inspect.getsource(req_lifecycle)
		self.assertIn('"may_start_successor"', source)
		self.assertIn('"correcting_plan_version"', source)


class TestPlanningSeam(IntegrationTestCase):
	def test_milestone_event_envelope(self):
		params = set(inspect.signature(schedule.record_tender_milestone_actual).parameters)
		self.assertTrue({"plan_item_id", "milestone", "actual_date", "source_event_id", "producer", "proceeding_id", "proceeding_type", "producer_sequence", "coverage", "supersedes_event_id"} <= params)
		self.assertEqual(set(inspect.signature(schedule.current_proceeding_actual).parameters), {"plan_item_id", "milestone", "proceeding_id"})
		self.assertIn("invitation", schedule.MILESTONES)


class TestConfigurationSeam(IntegrationTestCase):
	def test_publication_obligations_payload_shape(self):
		self.assertIn("Publication obligations", regulatory_reference.REFERENCE_KINDS)
		validated = regulatory_reference._validate_publication_obligations_payload(
			{"obligation_id": "LAW-OB-PUB-INVITATION", "accountable_actor_role": "Head of Procurement Function", "recipient": "Public", "channel": "STATE_PORTAL", "trigger_event": "TenderInvitation", "due_rule": "Immediate", "source_reference": "PUB-RULE-MOH-OT-2027-01"}
		)
		self.assertEqual(set(validated), {"obligation_id", "accountable_actor_role", "recipient", "channel", "trigger_event", "due_rule", "days", "reporting_period", "integration_evidence_contract_code", "source_reference"})
		self.assertEqual(regulatory_reference.DUE_RULES, ("Immediate", "CalendarDaysAfter", "WorkingDaysAfter", "PeriodEndPlusDays"))
		self.assertEqual(set(inspect.signature(regulatory_reference.list_reference_sets).parameters), {"reference_kind"})
		self.assertEqual(set(inspect.signature(regulatory_reference.list_regulatory_reference_versions).parameters), {"reference_set"})

	def test_schedule_profile_resolver(self):
		self.assertEqual(set(inspect.signature(procurement_settings.resolve_schedule_profile).parameters), {"procurement_method", "procurement_category", "applicability_date"})
		self.assertEqual(procurement_settings.PERIOD_BY_MILESTONE.get("bid_opening"), procurement_settings.PERIOD_BY_MILESTONE["bid_opening"])
		self.assertIn("bid_opening", procurement_settings.MILESTONES)

	def test_site_setup_seeds_the_publication_rule_rows(self):
		"""§10.1: four Evidence-based invitation channels and two cancellation
		obligations under one rule id; none names an integration contract."""
		frappe.set_user("Administrator")
		site_setup._seed_publication_obligations()
		sets = {row["reference_key"]: row for row in regulatory_reference.list_reference_sets("Publication obligations")}
		for code, _label, _url in site_setup.PUBLICATION_CHANNELS:
			key = f"{site_setup.PUBLICATION_RULE}/{code}"
			self.assertIn(key, sets)
			self.assertTrue(sets[key]["has_version"], key)
			versions = regulatory_reference.list_regulatory_reference_versions(sets[key]["reference_set"])
			payload = versions[0]["payload"]
			self.assertEqual(payload["channel"], code)
			self.assertEqual(payload["trigger_event"], site_setup.PUBLICATION_TRIGGER_INVITATION)
			self.assertEqual(payload["integration_evidence_contract_code"], "")
		for code, _label, _recipient, due_rule, days in site_setup.CANCELLATION_OBLIGATIONS:
			key = f"{site_setup.PUBLICATION_RULE}/{code}"
			self.assertIn(key, sets)
			payload = regulatory_reference.list_regulatory_reference_versions(sets[key]["reference_set"])[0]["payload"]
			self.assertEqual((payload["trigger_event"], payload["due_rule"], payload["days"]), (site_setup.PUBLICATION_TRIGGER_CANCELLATION, due_rule, days))
