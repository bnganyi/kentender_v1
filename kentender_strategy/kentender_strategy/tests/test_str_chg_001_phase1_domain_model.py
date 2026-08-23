# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.3 Phase 1 — domain model rebuild.

Focused tests for the new Strategic Plan / Strategic Plan Version / Strategy
Node / Performance Indicator / Performance Target schema and its domain
guards, reference generator, and audit routing. Does not exercise the
lifecycle engine (Phase 2), permissions/SoD (Phase 3), or contracts/API
(Phase 4) — those are separately scoped and not yet rebuilt.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.services.strategy_audit import list_events, record_event
from kentender_strategy.services.strategy_reference import REF_RE

PE = "PE-MOH"
FY = "FY-2027-2028"


def _plan(**kwargs) -> dict:
	data = {
		"doctype": "Strategic Plan",
		"title": "Phase 1 Test Plan",
		"procuring_entity_id": PE,
		"plan_role": "Primary",
		"period_start": "2027-07-01",
		"period_end": "2032-06-30",
	}
	data.update(kwargs)
	return data


class TestStrategicPlanDomainModel(FrappeTestCase):
	def setUp(self):
		self._cleanup = []

	def tearDown(self):
		for doctype, name in reversed(self._cleanup):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _track(self, doc):
		self._cleanup.append((doc.doctype, doc.name))
		return doc

	def test_plan_gets_generated_id_and_rejects_client_edit(self):
		plan = self._track(frappe.get_doc(_plan()).insert(ignore_permissions=True))
		self.assertRegex(plan.plan_id, REF_RE)
		self.assertTrue(plan.plan_id.startswith("MOH-SP-"))
		plan.plan_id = "HACKED-SP-0001"
		with self.assertRaises(frappe.ValidationError):
			plan.save(ignore_permissions=True)

	def test_primary_plan_must_not_have_parent(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(_plan(parent_primary_plan_id="whatever")).insert(ignore_permissions=True)

	def test_supporting_framework_requires_primary_parent_same_pe(self):
		primary = self._track(frappe.get_doc(_plan()).insert(ignore_permissions=True))
		# Missing parent
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(_plan(plan_role="Supporting Framework")).insert(ignore_permissions=True)
		# Valid: parent is Primary, same PE
		supporting = self._track(
			frappe.get_doc(
				_plan(plan_role="Supporting Framework", parent_primary_plan_id=primary.name)
			).insert(ignore_permissions=True)
		)
		self.assertEqual(supporting.parent_primary_plan_id, primary.name)

	def test_plan_period_start_before_end(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(_plan(period_start="2030-01-01", period_end="2029-01-01")).insert(
				ignore_permissions=True
			)

	def _version(self, plan_name: str, **kwargs) -> dict:
		data = {
			"doctype": "Strategic Plan Version",
			"plan_id": plan_name,
			"version_number": 1,
			"effective_from": "2027-07-01",
			"effective_to": "2032-06-30",
		}
		data.update(kwargs)
		return data

	def test_first_version_forbids_baseline_successor_requires_it(self):
		plan = self._track(frappe.get_doc(_plan()).insert(ignore_permissions=True))
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._version(plan.name, based_on_plan_version_id="whatever")).insert(
				ignore_permissions=True
			)
		v1 = self._track(frappe.get_doc(self._version(plan.name)).insert(ignore_permissions=True))
		self.assertRegex(v1.plan_version_id, REF_RE)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._version(plan.name, version_number=2)).insert(ignore_permissions=True)

	def test_successor_baseline_must_be_approved_or_active(self):
		plan = self._track(frappe.get_doc(_plan()).insert(ignore_permissions=True))
		v1 = self._track(frappe.get_doc(self._version(plan.name)).insert(ignore_permissions=True))
		# v1 is Draft — not a valid baseline
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._version(plan.name, version_number=2, based_on_plan_version_id=v1.name)
			).insert(ignore_permissions=True)
		frappe.db.set_value("Strategic Plan Version", v1.name, "status", "Active")
		v2 = self._track(
			frappe.get_doc(
				self._version(plan.name, version_number=2, based_on_plan_version_id=v1.name)
			).insert(ignore_permissions=True)
		)
		self.assertEqual(v2.based_on_plan_version_id, v1.name)

	def test_version_effective_dates_must_fall_within_plan_period(self):
		plan = self._track(frappe.get_doc(_plan()).insert(ignore_permissions=True))
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._version(plan.name, effective_from="2020-01-01")).insert(
				ignore_permissions=True
			)

	def _setup_plan_version(self) -> str:
		plan = self._track(frappe.get_doc(_plan()).insert(ignore_permissions=True))
		v1 = self._track(frappe.get_doc(self._version(plan.name)).insert(ignore_permissions=True))
		return v1.name

	def _node(self, plan_version_id: str, **kwargs) -> dict:
		data = {
			"doctype": "Strategy Node",
			"plan_version_id": plan_version_id,
			"node_type": "Pillar",
			"title": "Test Pillar",
			"display_order": 1,
		}
		data.update(kwargs)
		return data

	def test_pillar_has_no_parent_programme_requires_pillar_parent(self):
		pv = self._setup_plan_version()
		pillar = self._track(frappe.get_doc(self._node(pv)).insert(ignore_permissions=True))
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._node(pv, node_type="Pillar", parent_node_id=pillar.name)).insert(
				ignore_permissions=True
			)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._node(pv, node_type="Programme", title="No parent", display_order=2)
			).insert(ignore_permissions=True)
		programme = self._track(
			frappe.get_doc(
				self._node(
					pv, node_type="Programme", title="Prog", display_order=2, parent_node_id=pillar.name
				)
			).insert(ignore_permissions=True)
		)
		self.assertEqual(programme.parent_node_id, pillar.name)

	def test_programme_may_parent_objective_when_subprogramme_omitted(self):
		pv = self._setup_plan_version()
		pillar = self._track(frappe.get_doc(self._node(pv)).insert(ignore_permissions=True))
		programme = self._track(
			frappe.get_doc(
				self._node(
					pv, node_type="Programme", title="Prog", display_order=2, parent_node_id=pillar.name
				)
			).insert(ignore_permissions=True)
		)
		objective = self._track(
			frappe.get_doc(
				self._node(
					pv,
					node_type="Strategic Objective",
					title="Obj",
					display_order=3,
					parent_node_id=programme.name,
				)
			).insert(ignore_permissions=True)
		)
		self.assertEqual(objective.parent_node_id, programme.name)
		outcome = self._track(
			frappe.get_doc(
				self._node(
					pv,
					node_type="Strategic Outcome",
					title="Out",
					display_order=4,
					parent_node_id=objective.name,
				)
			).insert(ignore_permissions=True)
		)
		self.assertEqual(outcome.parent_node_id, objective.name)

	def test_sibling_display_order_must_be_unique(self):
		pv = self._setup_plan_version()
		self._track(frappe.get_doc(self._node(pv, title="A", display_order=1)).insert(ignore_permissions=True))
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._node(pv, title="B", display_order=1)).insert(ignore_permissions=True)

	def _objective(self, pv: str) -> str:
		pillar = self._track(frappe.get_doc(self._node(pv)).insert(ignore_permissions=True))
		programme = self._track(
			frappe.get_doc(
				self._node(pv, node_type="Programme", title="Prog", display_order=2, parent_node_id=pillar.name)
			).insert(ignore_permissions=True)
		)
		objective = self._track(
			frappe.get_doc(
				self._node(
					pv,
					node_type="Strategic Objective",
					title="Obj",
					display_order=3,
					parent_node_id=programme.name,
				)
			).insert(ignore_permissions=True)
		)
		return objective.name

	def _indicator(self, pv: str, node_id: str, **kwargs) -> dict:
		data = {
			"doctype": "Performance Indicator",
			"plan_version_id": pv,
			"measures_node_id": node_id,
			"indicator_name": "Test indicator",
			"definition": "A definition",
			"unit": "Percentage",
		}
		data.update(kwargs)
		return data

	def test_indicator_must_measure_objective_or_outcome(self):
		pv = self._setup_plan_version()
		pillar = self._track(
			frappe.get_doc(self._node(pv, title="Standalone Pillar", display_order=99)).insert(
				ignore_permissions=True
			)
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._indicator(pv, pillar.name)).insert(ignore_permissions=True)
		objective = self._objective(pv)
		indicator = self._track(
			frappe.get_doc(self._indicator(pv, objective)).insert(ignore_permissions=True)
		)
		self.assertRegex(indicator.indicator_id, REF_RE)

	def test_indicator_name_unique_under_measured_node(self):
		pv = self._setup_plan_version()
		objective = self._objective(pv)
		self._track(frappe.get_doc(self._indicator(pv, objective)).insert(ignore_permissions=True))
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._indicator(pv, objective)).insert(ignore_permissions=True)

	def _target(self, indicator_id: str, **kwargs) -> dict:
		data = {
			"doctype": "Performance Target",
			"indicator_id": indicator_id,
			"financial_year_id": FY,
			"comparison": "At least",
			"target_value": 85,
		}
		data.update(kwargs)
		return data

	def test_target_requires_exactly_one_period_anchor(self):
		pv = self._setup_plan_version()
		indicator = self._track(
			frappe.get_doc(self._indicator(pv, self._objective(pv))).insert(ignore_permissions=True)
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				self._target(indicator.name, financial_year_id=FY, target_by_date="2028-06-30")
			).insert(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._target(indicator.name, financial_year_id=None)).insert(
				ignore_permissions=True
			)
		target = self._track(frappe.get_doc(self._target(indicator.name)).insert(ignore_permissions=True))
		self.assertRegex(target.target_id, REF_RE)

	def test_percentage_target_value_out_of_range_rejected(self):
		pv = self._setup_plan_version()
		indicator = self._track(
			frappe.get_doc(self._indicator(pv, self._objective(pv))).insert(ignore_permissions=True)
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._target(indicator.name, target_value=150)).insert(ignore_permissions=True)

	def test_invalid_comparison_rejected(self):
		pv = self._setup_plan_version()
		indicator = self._track(
			frappe.get_doc(self._indicator(pv, self._objective(pv))).insert(ignore_permissions=True)
		)
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._target(indicator.name, comparison="Bogus")).insert(ignore_permissions=True)


class TestStrategyAuditMigratedToCoreEvent(FrappeTestCase):
	def test_record_event_writes_to_core_audit_event_not_bespoke_doctype(self):
		self.assertFalse(frappe.db.exists("DocType", "Strategy Audit Event"))
		audit_id = record_event(
			entity_type="Strategic Plan",
			entity_name="PHASE1-TEST-DUMMY",
			event_type="Created",
			new_state="Draft",
			summary="Phase 1 audit routing check",
		)
		self.addCleanup(lambda: frappe.delete_doc("Audit Event", audit_id, force=True, ignore_permissions=True))
		row = frappe.db.get_value(
			"Audit Event", audit_id, ["document_type", "document_name", "action"], as_dict=True
		)
		self.assertEqual(row.document_type, "Strategic Plan")
		self.assertEqual(row.document_name, "PHASE1-TEST-DUMMY")
		self.assertEqual(row.action, "Created")

		events = list_events("Strategic Plan", "PHASE1-TEST-DUMMY")
		self.assertEqual(len(events), 1)
		self.assertEqual(events[0]["metadata"]["summary"], "Phase 1 audit routing check")
