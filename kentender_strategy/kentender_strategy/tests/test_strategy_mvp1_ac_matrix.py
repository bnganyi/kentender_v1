# Copyright (c) 2026, KenTender and contributors
"""STR-SUP-005 wave 2 — STR-AC / §22 matrix samples for Strategy MVP-1.

Coverage map (001–030):
  001 yes — test_strategy_plan_structure (optional Sub-programme hierarchy)
  002 gated — test_strategy_ui_stitch_layout_guard + alignment nav (no redesign)
  003 yes — test_strategy_mvp1_domain.test_cross_version_parent_rejected
  004 yes — test_strategy_review_readiness
  005 yes — this module (SoD submitter≠approver)
  006 yes — Active immutability tests
  007 yes — test_strategy_plan_activation_concurrency
  008 yes — this module
  009 yes — this module
  010 retired — PVO applicability-trigger engine removed (STR-CHG-001 §1.3, no MVP replacement)
  011 retired — PVO applicability-trigger engine removed (STR-CHG-001 §1.3, no MVP replacement)
  012 yes — this module (Sep/Oct distinct measurement records)
  013 yes — duplicate block + supersede allow (this module)
  014 yes — test_strategy_measurement_verify
  015 yes — this module (compute_measurement_result matrix)
  016 yes — test_strategy_measurement_verify Off-track CA / exception
  017 yes — test_strategy_downstream_usage
  018 yes — this module (list_measurements wrong-PE deny) + role PW
  019 yes — this module (audit actor/reason sample)
  020 yes — seed tests
  021 yes — Budget/Demand/Planning XMOD tests
  022 yes — test_legacy_absence_active_path (+ Strategy Target DocType)
  023 gated — stitch layout + alignment nav gates
  024 yes — domain Viewer caps + strategy-role-matrix.spec (create deny / export)
  025 yes — test_strategy_performance outcome distribution
  026 yes — test_strategy_performance distinct exception kinds + routes
  027 partial — performance projection (residual polish)
  028 retired — Demand Value Treatment/PVC-adoption feature removed (Phase 0/2, cancelled XMOD-STR-008)
  029 yes — performance export meta
  030 yes — test_strategy_performance export wrong-PE + role PW
  Deferred: due/overdue notification job (XMOD-STR-009); full §12 role matrix.
"""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	TARGET_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_contracts import (
	list_active_targets,
	list_measurements,
	validate_strategy_reference,
)
from kentender_strategy.services.strategy_measurement import compute_measurement_result
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles
from kentender_strategy.services.strategy_transitions import transition_measurement, transition_plan
from kentender_strategy.services.strategy_writes import save_measurement_draft


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


class TestStrategyMvp1AcMatrix(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_str_ac_009_active_targets_only(self):
		rows = list_active_targets(procuring_entity=self.seed["procuring_entity"])
		self.assertTrue(all(r.get("node_code") for r in rows))
		self.assertTrue(any(r["node_code"] == TARGET_CODE for r in rows))

	def test_str_ac_013_duplicate_period_blocked(self):
		tgt = self.seed["target"]
		with self.assertRaises(frappe.ValidationError):
			save_measurement_draft(
				{
					"performance_target": tgt,
					"plan_version": self.seed["plan"],
					"measurement_period_start": "2027-09-01",
					"measurement_period_end": "2027-09-30",
					"measurement_date": "2027-10-06",
					"actual_numeric": 99.5,
					"evidence_reference": "DUP",
					"evidence_source": "test",
				}
			)

	def test_str_ac_013_superseding_measurement_allowed(self):
		tgt = self.seed["target"]
		existing = frappe.db.get_value(
			"Performance Measurement",
			{
				"performance_target": tgt,
				"measurement_period_start": "2027-09-01",
				"measurement_period_end": "2027-09-30",
				"workflow_status": ["not in", ["Rejected"]],
			},
			"name",
		)
		self.assertTrue(existing)
		saved = save_measurement_draft(
			{
				"performance_target": tgt,
				"plan_version": self.seed["plan"],
				"measurement_period_start": "2027-09-01",
				"measurement_period_end": "2027-09-30",
				"measurement_date": "2027-10-07",
				"actual_numeric": 99.7,
				"evidence_reference": "SUPERSEDE",
				"evidence_source": "test",
				"supersedes_measurement": existing,
			}
		)
		self.assertTrue(saved.get("id"))
		frappe.delete_doc(
			"Performance Measurement", saved["id"], force=True, ignore_permissions=True
		)

	def test_str_ac_008_historical_reference_resolves(self):
		tgt = self.seed["target"]
		ref = validate_strategy_reference(
			{
				"plan_version_id": self.seed["plan"],
				"node_id": tgt,
				"node_type": "PerformanceTarget",
			}
		)
		self.assertTrue(ref["valid"])
		self.assertTrue(ref.get("historical_ok", True))

	def test_str_ac_005_submitter_cannot_approve_same_plan(self):
		dual = _ensure_user(
			"str.ac005.dual@example.com",
			["Strategy Manager", "Planning Authority"],
			self.pe,
		)
		plan = frappe.get_doc(
			{
				"doctype": "Strategic Plan",
				"plan_code": "MOH-SP-AC005",
				"version_number": 1,
				"title": "AC-005 SoD fixture",
				"procuring_entity": self.pe,
				"plan_type": "Entity Strategic Plan",
				"status": "Submitted",
				"start_date": "2026-07-01",
				"end_date": "2027-06-30",
				"submitted_by": dual,
			}
		).insert(ignore_permissions=True)
		self.addCleanup(
			lambda: frappe.delete_doc(
				"Strategic Plan", plan.name, force=True, ignore_permissions=True
			)
		)
		frappe.set_user(dual)
		with self.assertRaises(frappe.ValidationError):
			transition_plan(plan.name, "Approve")

	def test_str_ac_015_measurement_type_result_matrix(self):
		cases = [
			("Percentage", "At least", 99.9, 0.1, 99.95, None, "On track"),
			("Percentage", "At least", 99.9, 0.1, 99.85, None, "At risk"),
			("Percentage", "At least", 99.9, 0.1, 99.5, None, "Off track"),
			("Numeric", "At most", 10, 1, 9, None, "On track"),
			("Numeric", "At most", 10, 1, 10.5, None, "At risk"),
			("Numeric", "At most", 10, 1, 12, None, "Off track"),
			("Count", "Equal to", 5, 0, 5, None, "On track"),
			("Count", "Equal to", 5, 0, 4, None, "Off track"),
			("Boolean", None, None, None, 1, None, "On track"),
			("Boolean", None, None, None, 0, None, "Off track"),
			("Milestone", None, None, None, None, "achieved", "On track"),
			("Milestone", None, None, None, None, "pending", "Off track"),
			("Currency", "Increase to", 100, None, 120, None, "On track"),
			("Duration", "Reduce to", 30, 2, 29, None, "On track"),
		]
		for mtype, direction, target, tol, actual, text, expected in cases:
			out = compute_measurement_result(
				measurement_type=mtype,
				comparison_direction=direction,
				target_numeric=target,
				tolerance_value=tol,
				actual_numeric=actual,
				actual_text=text,
			)
			self.assertEqual(
				out["result_status"],
				expected,
				msg=f"{mtype}/{direction}/{actual}/{text} → {out}",
			)

	def test_str_ac_019_audit_records_actor_and_reason(self):
		officer = _ensure_user(
			"str.ac019.officer@example.com", ["Strategy Officer"], self.pe
		)
		verifier = _ensure_user(
			"str.ac019.verifier@example.com", ["Strategy Manager"], self.pe
		)
		frappe.set_user(officer)
		saved = save_measurement_draft(
			{
				"performance_target": self.seed["target"],
				"plan_version": self.seed["plan"],
				"measurement_period_start": "2028-04-01",
				"measurement_period_end": "2028-04-30",
				"measurement_date": "2028-04-30",
				"actual_numeric": 99.92,
				"evidence_reference": "AC019",
				"evidence_source": "audit matrix",
			}
		)
		mid = saved["id"]
		self.addCleanup(
			lambda: frappe.delete_doc(
				"Performance Measurement", mid, force=True, ignore_permissions=True
			)
			if frappe.db.exists("Performance Measurement", mid)
			else None
		)
		transition_measurement(mid, "Submit")
		submit_evt = frappe.get_all(
			"Strategy Audit Event",
			filters={"entity_type": "Performance Measurement", "entity_name": mid, "event_type": "Submit"},
			fields=["actor", "prior_state", "new_state", "event_at", "reason"],
			limit=1,
		)
		self.assertTrue(submit_evt)
		self.assertEqual(submit_evt[0].actor, officer)
		self.assertEqual(submit_evt[0].prior_state, "Draft")
		self.assertEqual(submit_evt[0].new_state, "Submitted")
		self.assertTrue(submit_evt[0].event_at)

		frappe.set_user(verifier)
		transition_measurement(mid, "Return", reason="Clarify evidence pack")
		ret_evt = frappe.get_all(
			"Strategy Audit Event",
			filters={"entity_type": "Performance Measurement", "entity_name": mid, "event_type": "Return"},
			fields=["actor", "reason", "new_state"],
			limit=1,
		)
		self.assertTrue(ret_evt)
		self.assertEqual(ret_evt[0].actor, verifier)
		self.assertEqual(ret_evt[0].reason, "Clarify evidence pack")
		self.assertEqual(ret_evt[0].new_state, "Returned")

	def test_str_ac_012_period_history_preserved_as_separate_records(self):
		"""STR-AC-012 — Sep/Oct actuals are distinct measurement records."""
		_ensure_user("str.ac012.viewer@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.ac012.viewer@example.com")
		dto = list_measurements(plan_code=STRATEGY_PLAN_CODE)
		rows = dto.get("measurements") or dto.get("rows") or []
		sep = [
			r
			for r in rows
			if str(r.get("period_start") or "").startswith("2027-09")
			or str(r.get("period_end") or "").startswith("2027-09")
		]
		oct_ = [
			r
			for r in rows
			if str(r.get("period_start") or "").startswith("2027-10")
			or str(r.get("period_end") or "").startswith("2027-10")
		]
		self.assertTrue(sep, msg=f"expected Sep 2027 measurement(s); got {rows!r}")
		self.assertTrue(oct_, msg=f"expected Oct 2027 measurement(s); got {rows!r}")
		sep_ids = {r["id"] for r in sep}
		oct_ids = {r["id"] for r in oct_}
		self.assertTrue(sep_ids.isdisjoint(oct_ids), msg="Sep/Oct must be separate records")

	def test_str_ac_018_list_measurements_blocks_other_pe(self):
		"""STR-AC-018 — wrong-PE Viewer cannot list MOH measurements."""
		other = frappe.db.get_value("Procuring Entity", {"entity_code": "PE-MOE"}, "name")
		if not other:
			doc = frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": "PE-MOE",
					"entity_name": "Ministry of Education",
				}
			)
			doc.insert(ignore_permissions=True)
			other = doc.name
		_ensure_user("str.ac018.viewer@example.com", ["Strategy Viewer"], other)
		frappe.set_user("str.ac018.viewer@example.com")
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			list_measurements(plan_code=STRATEGY_PLAN_CODE)

	def test_api_whitelist_surface(self):
		from kentender_strategy.api import strategy_api

		self.assertTrue(callable(strategy_api.get_strategy_portfolio))
		self.assertTrue(callable(strategy_api.validate_strategy_reference))
		self.assertTrue(callable(strategy_api.get_plan_readiness_api))
		_ = STRATEGY_PLAN_CODE  # keep seed constant referenced for matrix docs
