# Copyright (c) 2026, KenTender and contributors
"""STR-UI-03 Plan Structure — tree upsert, Active lock, delete guards."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import create_plan, get_strategy_tree
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_writes import delete_structure_node, upsert_structure_node


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


def _delete_plan_cascade(plan_id: str | None):
	if not plan_id or not frappe.db.exists("Strategic Plan", plan_id):
		return
	for dt in (
		"Plan Value Commitment",
		"Performance Target",
		"Performance Indicator",
		"Strategic Outcome",
		"Strategy Sub Programme",
		"Strategy Programme",
		"Strategy Audit Event",
	):
		for name in frappe.get_all(dt, filters={"plan_version": plan_id}, pluck="name"):
			frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
	frappe.delete_doc("Strategic Plan", plan_id, force=True, ignore_permissions=True)


class TestStrategyPlanStructure(FrappeTestCase):
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

	def test_officer_can_build_hierarchy_on_draft(self):
		_ensure_user("str.officer.struct@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.struct@example.com")
		code = f"STR-H-{frappe.generate_hash(length=5).upper()}"
		created = create_plan(
			{
				"plan_code": code,
				"title": "Structure Hierarchy Draft",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
		self.assertTrue(created.get("ok"))
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))

		prog = upsert_structure_node(
			{
				"type": "Programme",
				"plan_version": plan_id,
				"code": f"{code}-PROG",
				"title": "Digital Services",
				"description": "Programme description",
				"responsible_function": "ICT",
			}
		)
		self.assertTrue(prog.get("id"))
		out = upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"code": f"{code}-OUT",
				"title": "Reliable services",
				"description": "Outcome description",
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
				"definition": "Uptime of core systems",
				"measurement_type": "Percentage",
				"unit": "%",
				"measurement_frequency": "Monthly",
				"data_source": "Monitoring platform",
				"responsible_function": "ICT",
			}
		)
		tgt = upsert_structure_node(
			{
				"type": "PerformanceTarget",
				"plan_version": plan_id,
				"performance_indicator": ind["id"],
				"code": f"{code}-TGT",
				"title": "At least 99.9% availability",
				"comparison_direction": "At least",
				"target_numeric": 99.9,
				"baseline_status": "Known",
				"baseline_numeric": 97.8,
				"baseline_as_of": "2026-06-30",
				"baseline_source": "Approved report",
				"period_start": "2027-07-01",
				"period_end": "2028-06-30",
				"benefit_owner": "Director, Digital Health",
				"measurement_verifier": "Administrator",
				"status": "Active",
			}
		)
		tree = get_strategy_tree(plan_version=plan_id)
		self.assertEqual(tree["counts"]["programmes"], 1)
		self.assertEqual(tree["counts"]["outcomes"], 1)
		self.assertEqual(tree["counts"]["indicators"], 1)
		self.assertEqual(tree["counts"]["targets"], 1)
		self.assertTrue(tree["capabilities"]["editable"])
		# Enriched target fields for drawer/detail
		flat = []

		def walk(nodes):
			for n in nodes or []:
				flat.append(n)
				walk(n.get("children"))

		walk(tree["tree"])
		by_code = {n["code"]: n for n in flat}
		self.assertIn(tgt["code"], by_code)
		self.assertIn("fields", by_code[tgt["code"]])
		self.assertEqual(by_code[tgt["code"]]["fields"].get("target_numeric"), 99.9)
		self.assertEqual(by_code[out["code"]]["warnings"], [])

	def test_str_ac_001_hierarchy_with_optional_subprogramme(self):
		"""STR-AC-001 — Programme → Sub-programme → Outcome; Outcome-without-sub remains valid."""
		_ensure_user("str.officer.ac001@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.ac001@example.com")
		code = f"STR-AC1-{frappe.generate_hash(length=5).upper()}"
		created = create_plan(
			{
				"title": "AC001 optional sub-programme",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
		self.assertTrue(created.get("ok"))
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))

		prog = upsert_structure_node(
			{
				"type": "Programme",
				"plan_version": plan_id,
				"code": f"{code}-PROG",
				"title": "Infrastructure Programme",
				"description": "Programme with optional sub",
				"responsible_function": "Works",
			}
		)
		self.assertTrue(prog.get("id"))
		# Outcome directly under Programme (optional Sub-programme omitted) remains valid.
		direct_out = upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"code": f"{code}-OUT-D",
				"title": "Direct outcome",
				"description": "No sub-programme",
				"responsible_function": "Works",
				"executive_owner": "Director",
			}
		)
		self.assertTrue(direct_out.get("id"))
		sub = upsert_structure_node(
			{
				"type": "SubProgramme",
				"plan_version": plan_id,
				"programme": prog["id"],
				"code": f"{code}-SUB",
				"title": "Rural roads sub-programme",
				"description": "Optional layer",
				"responsible_function": "Works",
			}
		)
		self.assertTrue(sub.get("id"))
		sub_out = upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"sub_programme": sub["id"],
				"code": f"{code}-OUT-S",
				"title": "Sub outcome",
				"description": "Under sub-programme",
				"responsible_function": "Works",
				"executive_owner": "Director",
			}
		)
		self.assertTrue(sub_out.get("id"))
		tree = get_strategy_tree(plan_version=plan_id)
		self.assertEqual(tree["counts"]["programmes"], 1)
		self.assertEqual(tree["counts"]["sub_programmes"], 1)
		self.assertEqual(tree["counts"]["outcomes"], 2)

	def test_target_missing_benefit_owner_returns_field_errors(self):
		"""Structured {ok:false, errors} — no MandatoryError / Message dialog path."""
		_ensure_user("str.officer.struct.err@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.struct.err@example.com")
		code = f"STR-ERR-{frappe.generate_hash(length=6).upper()}"
		created = create_plan(
			{
				"title": "Structure field errors",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))
		prog = upsert_structure_node(
			{
				"type": "Programme",
				"plan_version": plan_id,
				"title": "Prog",
				"responsible_function": "ICT",
			}
		)
		self.assertTrue(prog.get("ok"))
		out = upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"title": "Out",
				"responsible_function": "ICT",
			}
		)
		ind = upsert_structure_node(
			{
				"type": "PerformanceIndicator",
				"plan_version": plan_id,
				"strategic_outcome": out["id"],
				"title": "Ind",
				"definition": "def",
				"measurement_type": "Percentage",
				"unit": "%",
				"measurement_frequency": "Monthly",
				"data_source": "src",
				"responsible_function": "ICT",
			}
		)
		result = upsert_structure_node(
			{
				"type": "PerformanceTarget",
				"plan_version": plan_id,
				"performance_indicator": ind["id"],
				"title": "Target without owner",
				"comparison_direction": "At least",
				"target_numeric": 99.9,
				"period_start": "2027-07-01",
				"period_end": "2028-06-30",
				"measurement_verifier": "Administrator",
				"status": "Active",
				# benefit_owner omitted on purpose
			}
		)
		self.assertFalse(result.get("ok"))
		self.assertIn("benefit_owner", result.get("errors") or {})
		self.assertNotIn("id", result)

	def test_active_plan_blocks_upsert_and_delete(self):
		_ensure_user("str.officer.struct.active@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.struct.active@example.com")
		tree = get_strategy_tree(plan_code=STRATEGY_PLAN_CODE)
		self.assertEqual(tree["plan"]["status"], "Active")
		self.assertFalse(tree["capabilities"]["editable"])
		with self.assertRaises(frappe.ValidationError):
			upsert_structure_node(
				{
					"type": "Programme",
					"plan_version": self.plan_id,
					"code": "MOH-PROG-BLOCKED",
					"title": "Should fail",
				}
			)
		tgt_id = frappe.db.get_value(
			"Performance Target",
			{"target_code": TARGET_CODE, "plan_version": self.plan_id},
			"name",
		)
		self.assertTrue(tgt_id)
		with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
			delete_structure_node("PerformanceTarget", tgt_id)

	def test_viewer_cannot_upsert(self):
		_ensure_user("str.viewer.struct@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.struct@example.com")
		with self.assertRaises(frappe.PermissionError):
			upsert_structure_node(
				{
					"type": "Programme",
					"plan_version": self.plan_id,
					"code": "VIEWER-PROG",
					"title": "Nope",
				}
			)

	def test_delete_target_blocked_when_measurements_exist(self):
		_ensure_user("str.manager.struct@example.com", ["Strategy Manager"], self.pe)
		# Need a Draft clone of target with measurements on Active — delete Active target fails domain;
		# create draft plan with target+measurement instead.
		frappe.set_user("Administrator")
		code = f"STR-DEL-{frappe.generate_hash(length=5).upper()}"
		created = create_plan(
			{
				"plan_code": code,
				"title": "Delete Guard Draft",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
		plan_id = created["plan"]["id"]
		self.addCleanup(lambda: _delete_plan_cascade(plan_id))
		frappe.set_user("str.manager.struct@example.com")
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
				"title": "Out",
				"description": "d",
				"responsible_function": "ICT",
			}
		)
		ind = upsert_structure_node(
			{
				"type": "PerformanceIndicator",
				"plan_version": plan_id,
				"strategic_outcome": out["id"],
				"code": f"{code}-I",
				"title": "Ind",
				"definition": "def",
				"measurement_type": "Percentage",
				"unit": "%",
				"measurement_frequency": "Monthly",
				"data_source": "src",
				"responsible_function": "ICT",
			}
		)
		tgt = upsert_structure_node(
			{
				"type": "PerformanceTarget",
				"plan_version": plan_id,
				"performance_indicator": ind["id"],
				"code": f"{code}-T",
				"title": "Tgt",
				"comparison_direction": "At least",
				"target_numeric": 99.0,
				"baseline_status": "Not applicable",
				"period_start": "2027-01-01",
				"period_end": "2027-12-31",
				"benefit_owner": "Director",
				"measurement_verifier": "Administrator",
				"status": "Active",
			}
		)
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "Performance Measurement",
				"plan_version": plan_id,
				"performance_target": tgt["id"],
				"measurement_period_start": "2027-09-01",
				"measurement_period_end": "2027-09-30",
				"measurement_date": "2027-09-30",
				"actual_numeric": 98.0,
				"evidence_reference": "EV-1",
				"evidence_source": "Monitoring report",
				"workflow_status": "Draft",
			}
		).insert(ignore_permissions=True)
		frappe.set_user("str.manager.struct@example.com")
		with self.assertRaises(frappe.ValidationError):
			delete_structure_node("PerformanceTarget", tgt["id"])

	def test_outcome_without_indicator_has_warning(self):
		_ensure_user("str.officer.struct.warn@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.struct.warn@example.com")
		code = f"STR-W-{frappe.generate_hash(length=5).upper()}"
		created = create_plan(
			{
				"plan_code": code,
				"title": "Warn Draft",
				"plan_type": "Entity Strategic Plan",
				"procuring_entity": self.pe,
				"start_date": "2026-07-01",
				"end_date": "2030-06-30",
			}
		)
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
		upsert_structure_node(
			{
				"type": "StrategicOutcome",
				"plan_version": plan_id,
				"programme": prog["id"],
				"code": f"{code}-O",
				"title": "Bare outcome",
				"description": "needs indicator",
				"responsible_function": "ICT",
			}
		)
		tree = get_strategy_tree(plan_version=plan_id)
		outcome = tree["tree"][0]["children"][0]
		self.assertEqual(outcome["type"], "StrategicOutcome")
		self.assertIn("Indicator required", outcome.get("warnings") or [])
