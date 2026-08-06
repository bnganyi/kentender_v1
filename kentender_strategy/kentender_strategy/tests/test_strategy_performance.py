# Copyright (c) 2026, KenTender and contributors
"""STR-UI-15 / STR-FR-130+ Strategy Performance projection evidence."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_strategy.seeds.works_master_strategy_hierarchy import (
	STRATEGY_PLAN_CODE,
	upsert_works_master_strategy_hierarchy,
)
from kentender_strategy.services.strategy_performance import (
	can_export_strategy_performance,
	export_strategy_performance_report,
	get_strategy_performance,
)
from kentender_strategy.services.strategy_permissions import ensure_strategy_roles


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
		"Performance Officer",
		"Performance Verifier",
	):
		if role in have and role not in roles:
			user.remove_roles(role)
	user.add_roles(*roles)
	if procuring_entity:
		frappe.defaults.set_user_default("Procuring Entity", procuring_entity, user=email)
	return email


class TestStrategyPerformance(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_strategy_roles()
		cls.seed = upsert_works_master_strategy_hierarchy()
		cls.pe = cls.seed["procuring_entity"]

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_viewer_can_load_projection(self):
		_ensure_user("str.viewer.perf@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.perf@example.com")
		dto = get_strategy_performance(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)
		self.assertEqual(dto["plan"]["code"], STRATEGY_PLAN_CODE)
		self.assertIn("strip", dto)
		self.assertIn("as_at", dto)
		self.assertIn("source_coverage", dto)
		self.assertIn("outcomes", dto)
		self.assertIn("exceptions", dto)
		self.assertIn("procurement", dto)
		self.assertTrue(dto["capabilities"]["export_report"])
		self.assertFalse(dto["capabilities"]["open_portfolio"])

	def test_officer_cannot_export(self):
		_ensure_user("str.officer.perf@example.com", ["Strategy Officer"], self.pe)
		frappe.set_user("str.officer.perf@example.com")
		self.assertFalse(can_export_strategy_performance())
		with self.assertRaises(frappe.PermissionError):
			export_strategy_performance_report(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)

	def test_manager_export_includes_meta(self):
		_ensure_user("str.manager.perf@example.com", ["Strategy Manager"], self.pe)
		frappe.set_user("str.manager.perf@example.com")
		out = export_strategy_performance_report(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)
		self.assertTrue(out.get("ok"))
		self.assertIn("as_at", out)
		self.assertIn("source_coverage", out)
		self.assertIn("filters", out)
		self.assertIn("Strategy Performance", out["content"])
		self.assertIn(STRATEGY_PLAN_CODE, out["content"])
		# Formula injection guard — leading = becomes quoted
		self.assertNotRegex(out["content"], r"(?m)^=\+")

	def test_strip_and_stages_are_derived(self):
		frappe.set_user("Administrator")
		dto = get_strategy_performance(plan_code=STRATEGY_PLAN_CODE)
		strip = dto["strip"]
		self.assertGreaterEqual(strip["active_targets"], 1)
		# Lifecycle stages present and not presented as a single summed total field
		stages = dto["procurement"]["stages"]
		self.assertGreaterEqual(len(stages), 2)
		self.assertNotIn("total_procurement_value", dto["procurement"])
		self.assertIn("non_additivity_note", dto["procurement"]["funding"])

	def test_budget_contribution_via_primary_plan_version(self):
		"""STR-SUP-001 — Performance reads Budget Line primary_* (not strategy_plan_version)."""
		frappe.set_user("Administrator")
		from kentender_strategy.seeds.moh_downstream_usage import seed_moh_downstream_usage_refs

		seed = upsert_works_master_strategy_hierarchy()
		result = seed_moh_downstream_usage_refs(
			plan_name=seed["plan"], target_name=seed["target"]
		)
		self.assertTrue(result.get("ok"), result)
		self.assertTrue(result["linked"].get("budget_line"), result)

		dto = get_strategy_performance(plan_code=STRATEGY_PLAN_CODE)
		available = (dto.get("source_coverage") or {}).get("available") or []
		self.assertTrue(any("Budget" in str(x) for x in available), available)

		funding = (dto.get("procurement") or {}).get("funding") or {}
		self.assertTrue(funding.get("comparable"), funding)
		self.assertGreater(float(funding.get("budget") or 0), 0)

		stages = (dto.get("procurement") or {}).get("stages") or []
		approved = next(s for s in stages if s.get("stage") == "Approved budget")
		self.assertGreaterEqual(int(approved.get("aligned_records") or 0), 1)

	def test_pvc_adoption_uses_demand_value_treatments(self):
		"""XMOD-STR-007 / STR-AC-028 — adoption from Demand Value Treatment, not Demand count proxy."""
		frappe.set_user("Administrator")
		from kentender_procurement.demand_intake.services.demand_strategy_value import (
			TREATMENT_INCLUDED,
			apply_value_treatments_to_doc,
		)
		from kentender_strategy.seeds.moh_downstream_usage import seed_moh_downstream_usage_refs
		from kentender_strategy.services.strategy_contracts import list_plan_value_commitments

		seed = upsert_works_master_strategy_hierarchy()
		result = seed_moh_downstream_usage_refs(
			plan_name=seed["plan"], target_name=seed["target"]
		)
		self.assertTrue(result.get("ok"), result)
		demand_name = result["linked"].get("demand")
		if not demand_name or not frappe.db.exists("DocType", "Demand Value Treatment"):
			self.skipTest("Demand + Value Treatment fixture unavailable")

		pvc_rows = (list_plan_value_commitments(plan_version=seed["plan"]) or {}).get("rows") or []
		required = next(
			(
				r
				for r in pvc_rows
				if str(r.get("consideration_level") or "").startswith("Required")
			),
			None,
		)
		if not required:
			self.skipTest("No Required Plan Value Commitment on MOH plan")

		obj = required.get("objective") or {}
		pvc_id = required.get("id")
		pvc_code = obj.get("code") or "PVO-EFT-01"

		# Untreated: Required exception when aligned Demands exist.
		doc = frappe.get_doc("Demand", demand_name)
		doc.set("value_treatments", [])
		doc.save(ignore_permissions=True)
		dto_untreated = get_strategy_performance(plan_code=STRATEGY_PLAN_CODE)
		commit_u = next(
			(
				c
				for c in (dto_untreated.get("commitments") or [])
				if (c.get("id") == pvc_id)
				or ((c.get("objective") or {}).get("code") == pvc_code)
			),
			None,
		)
		self.assertTrue(commit_u, dto_untreated.get("commitments"))
		self.assertRegex(commit_u["downstream_adoption"], r"^0 of \d+ aligned Value Cases addressed$")
		exc_types = [e.get("type") for e in (dto_untreated.get("exceptions") or [])]
		self.assertIn("Required value commitment not addressed", exc_types)

		# Treated: Included clears the Required exception for this PVC.
		apply_value_treatments_to_doc(
			doc,
			[
				{
					"pvc_id": pvc_id,
					"pvc_code": pvc_code,
					"pvc_name": obj.get("name") or pvc_code,
					"requirement_level": required.get("consideration_level"),
					"treatment": TREATMENT_INCLUDED,
				}
			],
		)
		doc.save(ignore_permissions=True)
		dto = get_strategy_performance(plan_code=STRATEGY_PLAN_CODE)
		commit = next(
			(
				c
				for c in (dto.get("commitments") or [])
				if (c.get("id") == pvc_id) or ((c.get("objective") or {}).get("code") == pvc_code)
			),
			None,
		)
		self.assertTrue(commit)
		self.assertRegex(commit["downstream_adoption"], r"^[1-9]\d* of \d+ aligned Value Cases addressed$")
		exc_after = [
			e
			for e in (dto.get("exceptions") or [])
			if e.get("type") == "Required value commitment not addressed"
			and ((e.get("affected") or {}).get("code") == pvc_code or (e.get("affected") or {}).get("id") == pvc_id)
		]
		self.assertEqual(exc_after, [])

	def test_planning_stage_uses_package_estimated_value(self):
		"""XMOD-STR-007 — Procurement plan stage from package strategy_* + estimated_value."""
		frappe.set_user("Administrator")
		from kentender_strategy.seeds.moh_downstream_usage import (
			SEED_PACKAGE_CODE,
			seed_moh_downstream_usage_refs,
		)

		seed = upsert_works_master_strategy_hierarchy()
		result = seed_moh_downstream_usage_refs(
			plan_name=seed["plan"], target_name=seed["target"]
		)
		self.assertTrue(result.get("ok"), result)
		package_name = result["linked"].get("package")
		if not package_name:
			self.skipTest("PKG-MOH-2026-001 not available")

		if frappe.db.has_column("Procurement Package", "estimated_value"):
			frappe.db.set_value(
				"Procurement Package",
				package_name,
				"estimated_value",
				12_500_000,
				update_modified=False,
			)

		dto = get_strategy_performance(plan_code=STRATEGY_PLAN_CODE)
		stages = (dto.get("procurement") or {}).get("stages") or []
		plan_stage = next(s for s in stages if s.get("stage") == "Procurement plan")
		self.assertGreaterEqual(int(plan_stage.get("aligned_records") or 0), 1)
		if frappe.db.has_column("Procurement Package", "estimated_value"):
			self.assertGreater(float(plan_stage.get("current_value") or 0), 0)
			self.assertNotEqual(plan_stage.get("current_value_label"), "—")
		# Package business code remains on Downstream Usage; stage must not invent totals.
		self.assertNotIn("total_procurement_value", dto["procurement"])
		self.assertTrue(
			frappe.db.exists("Procurement Package", {"package_code": SEED_PACKAGE_CODE})
		)

	def test_entity_scope_blocks_other_pe(self):
		other = "PE-PERF-SCOPE-TEST"
		if not frappe.db.exists("Procuring Entity", {"entity_code": "PERF-SCOPE"}):
			frappe.get_doc(
				{
					"doctype": "Procuring Entity",
					"entity_code": "PERF-SCOPE",
					"entity_name": "Perf Scope PE",
				}
			).insert(ignore_permissions=True)
		other = frappe.db.get_value("Procuring Entity", {"entity_code": "PERF-SCOPE"}, "name")
		_ensure_user("str.viewer.scope.perf@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.viewer.scope.perf@example.com")
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			get_strategy_performance(procuring_entity=other)

	def test_str_ac_025_outcome_distribution_from_verified(self):
		"""STR-AC-025 — outcome rollup exposes distribution buckets from Verified actuals."""
		_ensure_user("str.ac025.viewer@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.ac025.viewer@example.com")
		dto = get_strategy_performance(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)
		outcomes = dto.get("outcomes") or []
		self.assertTrue(outcomes)
		expected_keys = {"On track", "At risk", "Off track", "No data", "Not due"}
		for o in outcomes:
			dist = o.get("distribution") or {}
			self.assertTrue(expected_keys.issubset(set(dist.keys())), msg=dist)
		# Seed has at least one Verified On-track outcome contribution.
		self.assertGreaterEqual(sum(int((o.get("distribution") or {}).get("On track") or 0) for o in outcomes), 1)

	def test_str_ac_026_exceptions_distinct_kinds_with_routes(self):
		"""STR-AC-026 — exceptions carry distinct kinds and drill routes."""
		_ensure_user("str.ac026.viewer@example.com", ["Strategy Viewer"], self.pe)
		frappe.set_user("str.ac026.viewer@example.com")
		dto = get_strategy_performance(procuring_entity=self.pe, plan_code=STRATEGY_PLAN_CODE)
		exceptions = dto.get("exceptions") or []
		self.assertTrue(exceptions, msg="expected seeded open CA / measurement exceptions")
		kinds = {e.get("kind") or e.get("type") for e in exceptions}
		self.assertGreaterEqual(len(kinds), 2, msg=f"expected distinct kinds; got {kinds}")
		for e in exceptions:
			route = e.get("route") or []
			self.assertTrue(route, msg=f"exception missing route: {e}")
			self.assertTrue(e.get("kind") or e.get("type"))

	def test_str_ac_030_export_blocks_other_pe(self):
		"""STR-AC-030 — export denies wrong-PE even when role can export."""
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
		_ensure_user("str.ac030.viewer@example.com", ["Strategy Viewer"], other)
		frappe.set_user("str.ac030.viewer@example.com")
		self.assertTrue(can_export_strategy_performance())
		with self.assertRaises((frappe.PermissionError, frappe.ValidationError)):
			export_strategy_performance_report(plan_code=STRATEGY_PLAN_CODE)
