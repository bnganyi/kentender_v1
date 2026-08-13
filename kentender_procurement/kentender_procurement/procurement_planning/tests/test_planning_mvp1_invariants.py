# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Cursor Prompt 01 — ten Planning domain invariants."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.mvp1_constants import (
	ALLOC_DRAFT,
	ALLOC_EFFECTIVE,
	ITEM_ACTIVE,
	VERSION_APPROVED,
	VERSION_DRAFT,
	VERSION_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services.add_demand_to_plan import add_demand_to_plan
from kentender_procurement.procurement_planning.services.approve_plan_version import (
	approve_plan_version,
)
from kentender_procurement.procurement_planning.services.create_procurement_plan import (
	create_procurement_plan,
)
from kentender_procurement.procurement_planning.services.open_or_create_plan_revision import (
	open_or_create_plan_revision,
)
from kentender_procurement.procurement_planning.tests._gate01_helpers import (
	PE,
	approve_plan_via_gate05,
	create_plan_as_planner,
	ensure_approver_user,
	ensure_planner_user,
	ensure_scope,
	make_approved_demand,
)


class TestPlanningMvp1Invariants(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		ensure_scope()

	def test_01_one_plan_per_pe_fy(self) -> None:
		planner = ensure_planner_user()
		scope = ensure_scope()
		fy = "2190/91"
		# clean prior
		for name in frappe.get_all(
			"Procurement Plan",
			filters={"procuring_entity": PE, "financial_year": fy},
			pluck="name",
		):
			frappe.delete_doc("Procurement Plan", name, force=True, ignore_permissions=True)
		a = create_procurement_plan(
			procuring_entity=PE,
			financial_year=fy,
			title="Dup A",
			currency="KES",
			coordinating_org_unit=scope["ou"],
			user=planner,
		)
		self.assertTrue(a["ok"])
		with self.assertRaises(frappe.ValidationError) as ctx:
			create_procurement_plan(
				procuring_entity=PE,
				financial_year=fy,
				title="Dup B",
				currency="KES",
				coordinating_org_unit=scope["ou"],
				user=planner,
			)
		self.assertIn("already exists", str(ctx.exception).lower())

	def test_02_at_most_one_current_approved(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		created = create_plan_as_planner(title="Approve chain")
		demand = make_approved_demand(title="Approve chain demand")
		add_demand_to_plan(
			plan=created["plan"],
			demand=demand["demand"],
			demand_item=demand["demand_item"],
			user=planner,
		)
		approve_plan_via_gate05(plan=created["plan"], version=created["version"], user=approver)
		rev = open_or_create_plan_revision(plan=created["plan"], user=planner)
		self.assertTrue(rev["created"])
		approve_plan_via_gate05(plan=created["plan"], version=rev["version"], user=approver)
		plan = frappe.get_doc("Procurement Plan", created["plan"])
		self.assertEqual(plan.current_approved_version, rev["version"])
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", created["version"], "status"),
			VERSION_SUPERSEDED,
		)
		self.assertEqual(
			frappe.db.get_value("Procurement Plan Version", rev["version"], "status"),
			VERSION_APPROVED,
		)
		# superseded remains readable
		self.assertTrue(frappe.db.exists("Procurement Plan Version", created["version"]))

	def test_03_at_most_one_open_draft(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		created = create_plan_as_planner(title="Draft singleton")
		demand = make_approved_demand(title="Draft singleton demand")
		add_demand_to_plan(
			plan=created["plan"],
			demand=demand["demand"],
			user=planner,
		)
		approve_plan_via_gate05(plan=created["plan"], version=created["version"], user=approver)
		a = open_or_create_plan_revision(plan=created["plan"], user=planner)
		b = open_or_create_plan_revision(plan=created["plan"], user=planner)
		self.assertEqual(a["version"], b["version"])
		self.assertFalse(b["created"])
		drafts = frappe.get_all(
			"Procurement Plan Version",
			filters={"plan": created["plan"], "status": VERSION_DRAFT},
			pluck="name",
		)
		self.assertEqual(len(drafts), 1)

	def test_04_immutable_approved_version(self) -> None:
		"""PLN-AC-011 — Approved Plan Version document cannot be mutated."""
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		created = create_plan_as_planner(title="Immutable")
		demand = make_approved_demand(title="Immutable demand")
		add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		approve_plan_via_gate05(plan=created["plan"], version=created["version"], user=approver)
		doc = frappe.get_doc("Procurement Plan Version", created["version"])
		doc.version_reason = "tamper"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_05_stable_plan_item_identity(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		created = create_plan_as_planner(title="Stable item")
		demand = make_approved_demand(title="Stable item demand")
		added = add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		code = added["plan_item_code"]
		approve_plan_via_gate05(plan=created["plan"], version=created["version"], user=approver)
		rev = open_or_create_plan_revision(plan=created["plan"], user=planner)
		item = frappe.get_doc("Procurement Plan Item", added["plan_item"])
		self.assertEqual(item.plan_item_code, code)
		self.assertEqual(item.baseline_state, ITEM_ACTIVE)
		draft_iv = frappe.db.get_value(
			"Procurement Plan Item Version",
			{"plan_item": item.name, "plan_version": rev["version"]},
			"name",
		)
		self.assertTrue(draft_iv)

	def test_06_draft_allocations_do_not_consume(self) -> None:
		planner = ensure_planner_user()
		created = create_plan_as_planner(title="No consume draft")
		demand = make_approved_demand(title="No consume demand")
		added = add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		self.assertEqual(added["allocation_status"], ALLOC_DRAFT)
		self.assertFalse(
			frappe.db.exists(
				"Planning Consumption",
				{"demand": demand["demand"], "plan_item_code": added["plan_item_code"]},
			)
		)
		usage = frappe.db.get_value("Demand", demand["demand"], "planning_usage")
		self.assertEqual(usage, "Not taken up")

	def test_07_approval_makes_allocations_effective_once(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		created = create_plan_as_planner(title="Effective once")
		demand = make_approved_demand(title="Effective once demand")
		added = add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		approve_plan_via_gate05(plan=created["plan"], version=created["version"], user=approver)
		status = frappe.db.get_value("Plan Demand Allocation", added["allocation"], "status")
		self.assertEqual(status, ALLOC_EFFECTIVE)
		self.assertTrue(
			frappe.db.exists(
				"Planning Consumption",
				{"demand": demand["demand"], "plan_item_code": added["plan_item_code"]},
			)
		)
		with self.assertRaises(frappe.ValidationError):
			approve_plan_version(
				version=created["version"],
				concurrency_token=frappe.db.get_value(
					"Procurement Plan Version", created["version"], "concurrency_token"
				),
				user=approver,
			)

	def test_08_same_pe_allocations(self) -> None:
		planner = ensure_planner_user()
		created = create_plan_as_planner(title="Same PE")
		other_pe = "PE-MOE"
		if not frappe.db.exists("Procuring Entity", other_pe):
			from kentender_core.seeds._common import ensure_procuring_entity

			ensure_procuring_entity(other_pe, "Ministry of Education")
		ou_moe = "MOE-TEST-OU"
		if not frappe.db.exists("Organisation Unit", ou_moe):
			ou_type = frappe.db.get_value("Organisation Unit Type", {}, "name")
			frappe.get_doc(
				{
					"doctype": "Organisation Unit",
					"unit_code": ou_moe,
					"unit_name": "MOE Test OU",
					"unit_type": ou_type,
					"procuring_entity": other_pe,
					"status": "Active",
				}
			).insert(ignore_permissions=True)
		foreign = make_approved_demand(pe=other_pe, ou=ou_moe, title="Foreign PE demand")
		with self.assertRaises(frappe.ValidationError) as ctx:
			add_demand_to_plan(
				plan=created["plan"],
				demand=foreign["demand"],
				user=planner,
			)
		self.assertIn("must match", str(ctx.exception).lower())

	def test_09_stale_version_protection(self) -> None:
		planner = ensure_planner_user()
		approver = ensure_approver_user()
		created = create_plan_as_planner(title="Stale token")
		demand = make_approved_demand(title="Stale token demand")
		add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		with self.assertRaises(frappe.ValidationError) as ctx:
			approve_plan_version(
				version=created["version"],
				concurrency_token="not-the-token",
				user=approver,
			)
		self.assertIn("changed by another user", str(ctx.exception).lower())

	def test_10_no_administrator_fallback(self) -> None:
		created = create_plan_as_planner(title="Admin denied")
		demand = make_approved_demand(title="Admin denied demand")
		planner = ensure_planner_user()
		add_demand_to_plan(plan=created["plan"], demand=demand["demand"], user=planner)
		token = frappe.db.get_value(
			"Procurement Plan Version", created["version"], "concurrency_token"
		)
		no_role_user = "pln.gate01.norole@test.local"
		if not frappe.db.exists("User", no_role_user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": no_role_user,
					"first_name": "No",
					"last_name": "Role",
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
		# Ensure System Manager only (no Planning operational roles)
		from kentender_procurement.procurement_planning.mvp1_constants import (
			PLANNING_OPERATIONAL_ROLES,
		)

		u = frappe.get_doc("User", no_role_user)
		for role in list(PLANNING_OPERATIONAL_ROLES):
			if role in {r.role for r in u.roles}:
				u.remove_roles(role)
		if "System Manager" not in {r.role for r in u.roles}:
			u.add_roles("System Manager")
		with self.assertRaises(frappe.PermissionError):
			approve_plan_version(
				version=created["version"],
				concurrency_token=token,
				user=no_role_user,
			)
