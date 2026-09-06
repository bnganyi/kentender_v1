# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.7 correction pass — the gaps the tracker's Phases 1–9 closed
on 2026-09-05, each pinned by the acceptance criterion it satisfies:

- STR-AC-031/033: no retired role, status, error code or scope field survives
  in executable Strategy code or in the live schema;
- STR-AC-035/§10: one `strategy` Desk Page with no Frappe role gate carries
  every canonical route; the Phase 7 pages are gone;
- STR-AC-013/STR-BR-004: the overlap guard holds when the command layer is
  bypassed;
- STR-AC-015/016/§7: `resolve_strategy_context` takes exactly one of
  as_of_date / fiscal_year, returns no Procuring Entity or organisation-unit
  key, and raises the typed zero/ambiguous errors;
- STR-BR-010/§12.3: a Fiscal Year target must overlap the plan period;
- §12.1: portfolio search/role/status filters are server-side;
- §12.4: an approval task route is denied to a caller without an Approver
  assignment, as data, not as a raised 403;
- §10: read contracts resolve the generated references the URLs carry.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_core.services import responsibility_administration as administration
from kentender_strategy.services import strategy_consumer as consumer
from kentender_strategy.services import strategy_ui_contracts as ui
from kentender_strategy.services.strategy_authorization import (
	ROLE_STRATEGY_APPROVER,
	ROLE_STRATEGY_AUTHOR,
	ensure_strategy_governance_roles,
)
from kentender_strategy.tests.fixtures import ensure_fiscal_year

APP_ROOT = Path(frappe.get_app_path("kentender_strategy"))
FY = "2040-2041"

RETIRED_TOKENS = (
	"Strategy Viewer",
	"Strategy Reviewer",
	"Strategy Approval Authority",
	"procuring_entity",  # covers procuring_entity_id as well
	"owner_org_unit_id",
	"pe_fy_context",
	"financial_year_id",
	"STRATEGY_SCOPE_REQUIRED",
	"STRATEGY_PERMISSION_DENIED",
	"Strategic Outcome",
	"Value Commitment",
)
# Patches legitimately name what they delete; this file names what it scans for.
SCAN_EXCLUDE = ("patches", "tests", "__pycache__", "node_modules", "dist")


def _executable_files():
	for path in APP_ROOT.rglob("*"):
		if not path.is_file() or path.suffix not in (".py", ".js", ".vue", ".json"):
			continue
		if any(part in SCAN_EXCLUDE for part in path.relative_to(APP_ROOT).parts):
			continue
		yield path


class TestStaticScan(FrappeTestCase):
	def test_no_retired_concept_in_executable_strategy_code(self):
		hits = []
		for path in _executable_files():
			text = path.read_text(encoding="utf-8", errors="ignore")
			for token in RETIRED_TOKENS:
				if token in text:
					hits.append(f"{path.relative_to(APP_ROOT)}: {token}")
		self.assertEqual(hits, [], "\n".join(hits))

	def test_live_schema_carries_no_retired_columns(self):
		for column in ("procuring_entity_id", "pe_fy_context", "owner_org_unit_id"):
			self.assertFalse(frappe.db.has_column("Strategic Plan", column), column)
		self.assertFalse(frappe.db.has_column("Performance Target", "financial_year_id"))
		self.assertTrue(frappe.db.has_column("Performance Target", "fiscal_year"))
		self.assertEqual(frappe.get_meta("Performance Target").get_field("fiscal_year").options, "Fiscal Year")

	def test_strategy_viewer_role_is_gone_and_auditor_reads(self):
		self.assertFalse(frappe.db.exists("Role", "Strategy Viewer"))
		for doctype in ("Strategic Plan", "Strategic Plan Version", "Strategy Node", "Performance Indicator", "Performance Target"):
			roles = {p.role for p in frappe.get_meta(doctype).permissions}
			self.assertNotIn("Strategy Viewer", roles, doctype)
			self.assertIn("Auditor", roles, doctype)
			self.assertEqual({r for r in roles if r not in ("System Manager", "Auditor")}, {ROLE_STRATEGY_AUTHOR, ROLE_STRATEGY_APPROVER}, doctype)


class TestOnePageRouteTable(FrappeTestCase):
	def test_one_strategy_page_with_no_role_gate(self):
		from kentender_strategy import hooks

		self.assertEqual(list(hooks.page_js.keys()), ["strategy"])
		self.assertTrue(frappe.db.exists("Page", "strategy"))
		self.assertEqual(frappe.get_all("Has Role", filters={"parenttype": "Page", "parent": "strategy"}), [])
		for legacy in ("strategy-portfolio", "strategy-plan-workspace", "strategy-review-task"):
			self.assertFalse(frappe.db.exists("Page", legacy), legacy)
			self.assertFalse((APP_ROOT / "kentender_strategy" / "page" / legacy.replace("-", "_")).exists(), legacy)

	def test_server_routes_follow_the_section_10_table(self):
		self.assertEqual(ui.plan_route("MOH-SP-0001"), ["strategy", "plan", "MOH-SP-0001"])
		self.assertEqual(
			ui.plan_route("MOH-SP-0001", "version", "2", "structure"),
			["strategy", "plan", "MOH-SP-0001", "version", "2", "structure"],
		)
		self.assertEqual(ui.approval_route("MOH-SPV-0002"), ["strategy", "approval", "MOH-SPV-0002"])


class CorrectionTestBase(FrappeTestCase):
	def setUp(self):
		ensure_strategy_governance_roles()
		ensure_fiscal_year(2040)
		self.suffix = uuid4().hex[:8]
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def _track(self, doc):
		self._cleanup.append((doc.doctype, doc.name))
		return doc

	def _user(self, label: str) -> str:
		email = f"kt.test.str.v17.{label}.{self.suffix}@test.local"
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": label,
				"enabled": 1,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
		doc.add_roles("Desk User")
		self._track(doc)
		return email

	def _grant(self, user: str, business_role: str) -> None:
		outcome = administration.grant(
			user=user,
			business_role=business_role,
			organisation_unit="",
			fixture_namespace="STR_V17_TESTS",
			actor="Administrator",
		)
		self._cleanup.append(("User Responsibility Assignment", outcome["assignment"]))
		return outcome["assignment"]

	def _plan(self, *, title: str | None = None, plan_role: str = "Primary", start="2040-07-01", end="2045-06-30", parent=None):
		return self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan",
					"title": title or f"v1.7 Test Plan {self.suffix}",
					"plan_role": plan_role,
					"parent_primary_plan_id": parent,
					"period_start": start,
					"period_end": end,
				}
			).insert(ignore_permissions=True)
		)

	def _version(self, plan, *, status="Draft", start="2040-07-01", end="2045-06-30", number=1, based_on=None):
		return self._track(
			frappe.get_doc(
				{
					"doctype": "Strategic Plan Version",
					"plan_id": plan.name,
					"version_number": number,
					"based_on_plan_version_id": based_on,
					"status": status,
					"effective_from": start,
					"effective_to": end,
				}
			).insert(ignore_permissions=True)
		)

	def _hierarchy(self, version, *, fiscal_year=FY):
		pillar = self._track(frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Pillar", "title": "Pillar", "display_order": 1}).insert(ignore_permissions=True))
		programme = self._track(frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Programme", "title": "Programme", "display_order": 2, "parent_node_id": pillar.name}).insert(ignore_permissions=True))
		objective = self._track(frappe.get_doc({"doctype": "Strategy Node", "plan_version_id": version.name, "node_type": "Strategic Objective", "title": "Objective", "display_order": 3, "parent_node_id": programme.name}).insert(ignore_permissions=True))
		indicator = self._track(frappe.get_doc({"doctype": "Performance Indicator", "plan_version_id": version.name, "measures_node_id": objective.name, "indicator_name": "Indicator", "definition": "Definition", "unit": "Percentage"}).insert(ignore_permissions=True))
		target = self._track(frappe.get_doc({"doctype": "Performance Target", "indicator_id": indicator.name, "fiscal_year": fiscal_year, "comparison": "At least", "target_value": 80}).insert(ignore_permissions=True))
		return {"objective": objective, "indicator": indicator, "target": target}


class TestOverlapGuardBypass(CorrectionTestBase):
	def test_overlap_guard_holds_when_the_command_layer_is_bypassed(self):
		"""STR-AC-013 — a raw doc.save() that makes a second overlapping
		Primary version Active is rejected by the doctype's own validate."""
		first = self._version(self._plan(title=f"First {self.suffix}"))
		frappe.db.set_value("Strategic Plan Version", first.name, "status", "Active")
		second = self._version(self._plan(title=f"Second {self.suffix}"), status="Submitted for approval")
		second.status = "Active"
		with self.assertRaises(frappe.ValidationError) as ctx:
			second.save(ignore_permissions=True)
		self.assertIn("overlapping", str(ctx.exception))

	def test_non_overlapping_primary_plans_may_both_be_active(self):
		first = self._version(self._plan(title=f"Early {self.suffix}"))
		frappe.db.set_value("Strategic Plan Version", first.name, "status", "Active")
		late = self._plan(title=f"Late {self.suffix}", start="2046-07-01", end="2050-06-30")
		second = self._version(late, status="Submitted for approval", start="2046-07-01", end="2050-06-30")
		second.status = "Active"
		second.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value("Strategic Plan Version", second.name, "status"), "Active")


class TestResolveStrategyContext(CorrectionTestBase):
	def test_fiscal_year_input_returns_the_covering_active_primary_and_no_scope_keys(self):
		plan = self._plan(title=f"Context {self.suffix}")
		version = self._version(plan)
		self._hierarchy(version)
		frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")

		out = consumer.resolve_strategy_context(fiscal_year=FY)
		self.assertEqual(set(out), {"as_of_date", "fiscal_year", "primary_plan", "supporting_plans"})
		self.assertEqual(out["fiscal_year"], FY)
		primary = out["primary_plan"]
		self.assertEqual(primary["id"], plan.name)
		self.assertEqual(primary["version_id"], version.name)
		self.assertEqual(primary["status"], "Active")
		self.assertEqual(primary["hierarchy_summary"]["strategic_objectives"], 1)
		for key in ("procuring_entity", "organisation_unit", "owner_org_unit_id"):
			self.assertNotIn(key, primary)
			self.assertNotIn(key, out)
		self.assertEqual(out["supporting_plans"], [])

		by_date = consumer.resolve_strategy_context(as_of_date="2042-01-01")
		self.assertEqual(by_date["primary_plan"]["version_id"], version.name)

	def test_supporting_frameworks_return_only_when_requested_in_title_order(self):
		plan = self._plan(title=f"Primary {self.suffix}")
		version = self._version(plan)
		frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")
		for title in (f"Zulu framework {self.suffix}", f"Alpha framework {self.suffix}"):
			sup = self._plan(title=title, plan_role="Supporting Framework", parent=plan.name)
			sv = self._version(sup)
			frappe.db.set_value("Strategic Plan Version", sv.name, "status", "Active")

		self.assertEqual(consumer.resolve_strategy_context(as_of_date="2042-01-01")["supporting_plans"], [])
		names = [s["name"] for s in consumer.resolve_strategy_context(as_of_date="2042-01-01", include_supporting=True)["supporting_plans"]]
		self.assertEqual(names, sorted(names))
		self.assertEqual(len(names), 2)

	def test_exactly_one_input_and_typed_zero_and_ambiguous_errors(self):
		with self.assertRaises(frappe.ValidationError):
			consumer.resolve_strategy_context()
		with self.assertRaises(frappe.ValidationError):
			consumer.resolve_strategy_context(as_of_date="2042-01-01", fiscal_year=FY)
		with self.assertRaises(frappe.DoesNotExistError):
			consumer.resolve_strategy_context(as_of_date="1999-01-01")

		for title in ("A", "B"):
			version = self._version(self._plan(title=f"Ambiguous {title} {self.suffix}"))
			# Bypass the guard deliberately to manufacture the ambiguous state.
			frappe.db.set_value("Strategic Plan Version", version.name, "status", "Active")
		with self.assertRaises(frappe.ValidationError) as ctx:
			consumer.resolve_strategy_context(as_of_date="2042-01-01")
		self.assertIn("More than one", str(ctx.exception))


class TestTargetPeriodRule(CorrectionTestBase):
	def test_fiscal_year_target_must_overlap_the_plan_period(self):
		version = self._version(self._plan())
		with self.assertRaises(frappe.ValidationError) as ctx:
			self._hierarchy(version, fiscal_year="2027-2028")
		self.assertIn("does not overlap", str(ctx.exception))

	def test_available_fiscal_years_are_narrowed_to_the_plan_period(self):
		plan = self._plan()
		names = [row["name"] for row in ui.list_available_fiscal_years(plan.name)]
		self.assertIn(FY, names)
		self.assertNotIn("2027-2028", names)
		# The generated reference resolves the same way the URL carries it.
		self.assertEqual(names, [row["name"] for row in ui.list_available_fiscal_years(plan.plan_id)])


class TestPortfolioAndReferences(CorrectionTestBase):
	def test_portfolio_filters_are_server_side_and_counts_match_rows(self):
		author = self._user("author")
		self._grant(author, ROLE_STRATEGY_AUTHOR)
		plan = self._plan(title=f"Filterable {self.suffix}")
		self._version(plan)
		frappe.set_user(author)
		try:
			out = ui.get_strategy_portfolio(search=self.suffix)
			self.assertEqual([p["id"] for p in out["plans"]], [plan.name])
			self.assertEqual(out["counts"]["plans"], 1)
			self.assertEqual(ui.get_strategy_portfolio(search=self.suffix, status="Active")["plans"], [])
			self.assertEqual(ui.get_strategy_portfolio(search=self.suffix, plan_role="Supporting Framework")["plans"], [])
			row = ui.get_strategy_portfolio(search=plan.plan_id)["plans"][0]
			self.assertEqual(row["available_action"], "Continue draft")
			self.assertEqual(row["action_route"], ["strategy", "plan", plan.plan_id, "version", "1", "structure"])
		finally:
			frappe.set_user("Administrator")

	def test_read_contracts_accept_generated_references(self):
		plan = self._plan()
		version = self._version(plan)
		workspace = ui.get_plan_workspace(plan.plan_id)
		self.assertEqual(workspace["plan"]["id"], plan.name)
		self.assertEqual(workspace["current_version"]["id"], version.name)
		self.assertEqual(workspace["routes"]["structure"], ["strategy", "plan", plan.plan_id, "version", "1", "structure"])
		self.assertEqual(ui.get_strategy_tree(version.plan_version_id)["version_id"], version.name)
		self.assertTrue(ui.get_plan_workspace("MOH-SP-does-not-exist")["not_found"])

	def test_approval_task_is_denied_as_data_without_an_approver_assignment(self):
		author = self._user("author2")
		self._grant(author, ROLE_STRATEGY_AUTHOR)
		version = self._version(self._plan(), status="Submitted for approval")
		frappe.set_user(author)
		try:
			out = ui.get_version_review_overview(version.plan_version_id)
		finally:
			frappe.set_user("Administrator")
		self.assertTrue(out["forbidden"])
		self.assertEqual(out["reason"], "approver_required")

		approver = self._user("approver2")
		self._grant(approver, ROLE_STRATEGY_APPROVER)
		frappe.set_user(approver)
		try:
			out = ui.get_version_review_overview(version.plan_version_id)
		finally:
			frappe.set_user("Administrator")
		self.assertFalse(out["forbidden"])
		self.assertEqual(out["routes"]["overview"], ["strategy", "approval", version.plan_version_id])


class TestAuditCarriesExercisedAssignment(CorrectionTestBase):
	"""§13 — each workflow event records the business role and the exercised
	responsibility assignment ID (tracker D2 / STR-505), not just a
	capability label."""

	def test_submit_event_records_business_role_and_assignment_id(self):
		from kentender_strategy.services.strategy_audit import list_events
		from kentender_strategy.services.strategy_transitions import transition_plan_version

		author = self._user("auditauthor")
		assignment = self._grant(author, ROLE_STRATEGY_AUTHOR)
		version = self._version(self._plan())
		self._hierarchy(version)
		frappe.set_user(author)
		try:
			transition_plan_version(version.plan_version_id, "Submit for approval")
		finally:
			frappe.set_user("Administrator")
		event = next(e for e in list_events("Strategic Plan Version", version.name) if e["action"] == "Submit for approval")
		self.assertEqual(event["performed_by"], author)
		self.assertEqual(event["metadata"]["business_role"], ROLE_STRATEGY_AUTHOR)
		self.assertEqual(event["metadata"]["assignment"], assignment)
		self.assertNotIn("procuring_entity", event["metadata"])
		self.assertNotIn("organisation_unit", event["metadata"])


class TestSeedFailsClosedOnMissingFiscalYear(FrappeTestCase):
	"""STR-AC-024 / §14.2 — a missing ERPNext Fiscal Year fails the seed with
	a typed error before any Strategy record is written; nothing is created
	or inferred in its place."""

	def test_missing_fiscal_year_aborts_before_any_write(self):
		from unittest.mock import patch

		from kentender_strategy.seeds import kentender_mvp_v1_strategy as seed

		before = frappe.db.count("Strategic Plan")
		real_exists = frappe.db.exists

		def exists_without_fy(*args, **kwargs):
			if args and args[0] == "Fiscal Year":
				return None
			return real_exists(*args, **kwargs)

		with patch.object(frappe.db, "exists", side_effect=exists_without_fy):
			with self.assertRaises(frappe.ValidationError) as ctx:
				seed.upsert_kentender_mvp_v1_strategy()
		self.assertIn("Missing Fiscal Year", str(ctx.exception))
		self.assertEqual(frappe.db.count("Strategic Plan"), before)
		self.assertTrue(frappe.db.exists("Fiscal Year", seed.FY_2027_2028), "the real Fiscal Year is untouched")
