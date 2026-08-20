# Copyright (c) 2026, KenTender and contributors
"""STR-UI-08 Measurement Register — list DTO, counts, display enrichment."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import create_plan, list_measurements
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_writes import (
	get_measurement,
	save_measurement_draft,
	upsert_structure_node,
)


def _delete_plan_cascade(plan_id: str | None) -> None:
	if not plan_id or not frappe.db.exists("Strategic Plan", plan_id):
		return
	for dt in (
		"Performance Measurement",
		"Strategy Value Commitment",
		"Performance Target",
		"Performance Indicator",
		"Strategic Outcome",
		"Strategy Sub Programme",
		"Strategy Programme",
	):
		if not frappe.db.exists("DocType", dt):
			continue
		for name in frappe.get_all(dt, filters={"plan_version": plan_id}, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)


def _ensure_user(email: str, roles: list[str], procuring_entity: str | None = None) -> str:
	ensure_strategy_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.insert(ignore_permissions=True)
	user = frappe.get_doc("User", email)
	user.enabled = 1
	user.save(ignore_permissions=True)
	have = set(frappe.get_roles(email))
	for role in (
		"Strategy Viewer",
		"Strategy Officer",
		"Strategy Manager",
		"Strategy Reviewer",
		"Planning Authority",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


class TestStrategyPlanMeasurements(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]
		cls.plan_id = cls.seed["plan"]
		if cls.plan_id:
			status = frappe.db.get_value("Strategic Plan", cls.plan_id, "status")
			if status != "Active":
				frappe.db.set_value("Strategic Plan", cls.plan_id, "status", "Active")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_active_moh_list_enriched_with_counts(self):
		_ensure_user("str.officer.meas@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.meas@example.com")
		dto = list_measurements(plan_code=STRATEGY_PLAN_CODE)
		self.assertIsInstance(dto, dict)
		self.assertEqual(dto["plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertEqual(dto["plan"]["status"], "Active")
		self.assertIn("counts", dto)
		for key in ("due", "submitted", "verified", "needs_attention"):
			self.assertIn(key, dto["counts"])
		self.assertGreaterEqual(dto["counts"]["verified"], 2)
		self.assertEqual(dto["counts"]["due"], 0)

		rows = dto["rows"]
		self.assertGreaterEqual(len(rows), 2)
		codes = {r["target"]["code"] for r in rows}
		self.assertIn(TARGET_CODE, codes)
		self.assertNotIn("MOH-TGT-02", codes)
		self.assertNotIn("MOH-TGT-03", codes)

		for r in rows:
			if r["target"]["code"] != TARGET_CODE:
				continue
			self.assertTrue(r["target"]["name"])
			self.assertTrue(r.get("period_label"))
			self.assertTrue(r.get("target_value_display"))
			self.assertIn(r["workflow_status"], ("Verified", "Submitted", "Draft", "Returned", "Rejected"))
			self.assertTrue(r.get("result_status"))
			self.assertIn(r.get("next_action"), ("view", "review", "submit", None))

		verified = [r for r in rows if r["workflow_status"] == "Verified"]
		self.assertGreaterEqual(len(verified), 2)
		self.assertTrue(all(r["next_action"] == "view" for r in verified))
		self.assertTrue(dto.get("default_target_code"))

	def test_get_measurement_by_target_code_prefers_active_plan(self):
		"""Multiple plan versions may share MOH-TGT-AVAIL-2028; resolve Active, never get_doc(None)."""
		_ensure_user("str.officer.meas.get@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.meas.get@example.com")
		m = get_measurement(target_code=TARGET_CODE)
		self.assertIsInstance(m, dict)
		self.assertEqual(m["performance_target"]["code"], TARGET_CODE)
		self.assertTrue(m["performance_target"]["id"])
		# Active MOH target must resolve a real measurement (open Submitted preferred over Verified).
		self.assertTrue(m.get("id"))
		self.assertIn(
			m.get("workflow_status"),
			("Draft", "Returned", "Submitted", "Verified"),
		)
		self.assertEqual(m["plan_version"], self.plan_id)

	def test_get_measurement_submit_purpose_skips_verified(self):
		"""Submit form must open a blank shell when only Verified history exists."""
		_ensure_user("str.officer.meas.submit@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.meas.submit@example.com")
		m = get_measurement(
			target_code=TARGET_CODE, plan_code=STRATEGY_PLAN_CODE, purpose="submit"
		)
		self.assertTrue(m.get("is_new"))
		self.assertIsNone(m.get("id"))
		self.assertEqual(m["performance_target"]["code"], TARGET_CODE)

	def test_get_measurement_scoped_to_plan_code(self):
		"""Submit from a plan must not load another plan's measurement for the same target code."""
		_ensure_user("str.officer.meas.scope@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.meas.scope@example.com")
		code = "TEST-MEAS-SCOPE-PLAN"
		created = create_plan(
			{
				"plan_code": code,
				"title": "Measurement scope plan",
				"plan_type": "Entity Strategic Plan",
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
				"procuring_entity": self.pe,
			}
		)
		self.assertTrue(created.get("ok"), created)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))

		prog = upsert_structure_node(
			{
				"type": "Programme",
				"plan_version": plan_id,
				"code": f"{code}-P",
				"title": "Prog",
				"responsible_function": "ICT",
			}
		)
		out = upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"code": f"{code}-O",
				"title": "Outcome",
				"description": "d",
				"responsible_function": "ICT",
				"executive_owner": "Director",
			}
		)
		ind = upsert_structure_node(
			{
				"type": "PerformanceIndicator",
				"plan_version": plan_id,
				"strategic_outcome": out["id"],
				"code": f"{code}-IND",
				"title": "Availability",
				"definition": "Uptime",
				"measurement_type": "Percentage",
				"unit": "%",
				"measurement_frequency": "Monthly",
				"data_source": "Reports",
				"responsible_function": "ICT",
			}
		)
		# Reuse MOH-TGT-AVAIL-2028 business code on this draft — must still scope by plan.
		tgt = upsert_structure_node(
			{
				"type": "PerformanceTarget",
				"plan_version": plan_id,
				"performance_indicator": ind["id"],
				"code": TARGET_CODE,
				"title": "Scoped empty target",
				"comparison_direction": "At least",
				"target_numeric": 50,
				"baseline_status": "Known",
				"baseline_numeric": 40,
				"baseline_as_of": "2026-06-30",
				"baseline_source": "Baseline report",
				"period_start": "2027-07-01",
				"period_end": "2028-06-30",
				"benefit_owner": "Director",
				"measurement_verifier": "Administrator",
				"status": "Active",
			}
		)

		m = get_measurement(target_code=TARGET_CODE, plan_code=code)
		self.assertTrue(m.get("is_new"))
		self.assertIsNone(m.get("id"))
		self.assertEqual(m["performance_target"]["id"], tgt["id"])
		self.assertEqual(m["plan_version"], plan_id)
		self.assertIsNone(m.get("actual_numeric"))

		dto = list_measurements(plan_code=code)
		self.assertEqual(dto["default_target_code"], TARGET_CODE)
		self.assertEqual(dto["rows"], [])

	def test_list_measurements_no_default_target_when_plan_has_none(self):
		_ensure_user("str.officer.meas.empty@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.meas.empty@example.com")
		created = create_plan(
			{
				"plan_code": "TEST-MEAS-EMPTY-PLAN",
				"title": "Empty measurements plan",
				"plan_type": "Entity Strategic Plan",
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
				"procuring_entity": self.pe,
			}
		)
		self.assertTrue(created.get("ok"), created)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))
		dto = list_measurements(plan_code="TEST-MEAS-EMPTY-PLAN")
		self.assertIsNone(dto.get("default_target_code"))
		self.assertEqual(dto["rows"], [])

	def test_evidence_reference_optional_on_draft(self):
		"""UI does not mark Evidence Reference required; DocType must allow blank."""
		frappe.set_user("Administrator")
		meta = frappe.get_meta("Performance Measurement")
		self.assertFalse(meta.get_field("evidence_reference").reqd)
		saved = save_measurement_draft(
			{
				"performance_target": self.seed["target"],
				"plan_version": self.plan_id,
				"measurement_period_start": "2028-01-01",
				"measurement_period_end": "2028-01-31",
				"measurement_date": "2028-02-01",
				"actual_numeric": 99.5,
				"evidence_source": "Annual plan",
				# evidence_reference intentionally omitted
			}
		)
		self.assertTrue(saved.get("id"))
		self.addCleanup(
			lambda: frappe.delete_doc(
				"Performance Measurement", saved["id"], force=True, ignore_permissions=True
			)
		)
		ref = frappe.db.get_value("Performance Measurement", saved["id"], "evidence_reference")
		self.assertFalse(ref)
