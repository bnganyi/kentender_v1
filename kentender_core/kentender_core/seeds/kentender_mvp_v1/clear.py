# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear KENTENDER_MVP_V1 fixture rows plus Playwright/test runtime leftovers.

Contract §8.3: do not wipe unrelated *Strategic* Plans. Demo reseed *does* wipe
extra Procurement Plans, Demands, `@test.local` users, and test budgets on PE-MOH /
PE-CGKIS so queues show only canonical demo data.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.kentender_mvp_v1 import constants as C

EDGE_NS = "KENTENDER_MVP_V1_EDGE"
LEGACY_EDGE_NS = "MOH_MVP_V1_EDGE"
TEST_ACTIVITY_NS = "KENTENDER_MVP_V1_BUDGET_TEST_ACT"

_NAMESPACES = (
	C.FIXTURE_NS,
	C.LEGACY_FIXTURE_NS,
	EDGE_NS,
	LEGACY_EDGE_NS,
	TEST_ACTIVITY_NS,
)

_BUDGET_CHILD_DOCTYPES = (
	"Expenditure Snapshot",
	"Procurement Commitment",
	"Funding Reservation",
	"Budget Revision",
	"Budget Audit Event",
	"Budget Line",
)

# Exact fixture budget codes (MOH + CGK + known edge codes).
_FIXTURE_BUDGET_CODES = (
	C.BUD_ACTIVE,
	C.BUD_DRAFT,
	C.BUD_CLOSED,
	C.CGK_BUD_ACTIVE,
	"MOH-BUD-0002",
	"MOH-BUD-0004",
)

_FIXTURE_PLAN_CODES = (C.PLAN_CODE, C.CGK_PLAN_CODE, "MOH-SP-0001")


def _unique(names: list[str]) -> list[str]:
	seen: set[str] = set()
	out: list[str] = []
	for name in names:
		if not name or name in seen:
			continue
		seen.add(name)
		out.append(name)
	return out


def _delete_budget_graph(budget_name: str, deleted: dict[str, int]) -> None:
	for doctype in _BUDGET_CHILD_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		if doctype == "Budget Audit Event":
			frappe.flags.allow_budget_audit_purge = True
		try:
			for name in frappe.get_all(doctype, filters={"budget": budget_name}, pluck="name"):
				if not frappe.db.exists(doctype, name):
					continue
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
				deleted[doctype] = deleted.get(doctype, 0) + 1
		finally:
			if doctype == "Budget Audit Event":
				frappe.flags.allow_budget_audit_purge = False
	if frappe.db.exists("Budget", budget_name):
		frappe.delete_doc("Budget", budget_name, force=1, ignore_permissions=True)
		deleted["Budget"] = deleted.get("Budget", 0) + 1


def _collect_fixture_budgets() -> list[str]:
	names: list[str] = []
	if frappe.db.has_column("Budget", "fixture_namespace"):
		names.extend(
			frappe.get_all(
				"Budget",
				filters={"fixture_namespace": ["in", list(_NAMESPACES)]},
				pluck="name",
			)
		)
	for code in _FIXTURE_BUDGET_CODES:
		names.extend(
			frappe.get_all("Budget", filters={"generated_reference": code}, pluck="name")
		)
	# Planning Finance tests: `MOH-BUD-PLN-<token>`.
	names.extend(
		frappe.get_all(
			"Budget",
			filters={"generated_reference": ["like", "MOH-BUD-PLN-%"]},
			pluck="name",
		)
	)
	return _unique(names)


def purge_test_local_users() -> dict[str, int]:
	"""Remove Gate/Playwright helper users (`*@test.local`). Keep @example.test personas."""
	deleted: dict[str, int] = {}
	users = frappe.get_all(
		"User",
		filters={"name": ["like", "%@test.local"]},
		pluck="name",
	)
	keep = set(C.CANONICAL_USERS) | {"Administrator", "Guest"}
	for user in users:
		if user in keep:
			continue
		if frappe.db.exists("DocType", "Notification Log"):
			for name in frappe.get_all(
				"Notification Log", filters={"for_user": user}, pluck="name"
			):
				frappe.delete_doc("Notification Log", name, force=1, ignore_permissions=True)
				deleted["Notification Log"] = deleted.get("Notification Log", 0) + 1
		if frappe.db.exists("DocType", "User Scope Assignment"):
			for name in frappe.get_all(
				"User Scope Assignment", filters={"user": user}, pluck="name"
			):
				frappe.delete_doc(
					"User Scope Assignment", name, force=1, ignore_permissions=True
				)
				deleted["User Scope Assignment"] = deleted.get("User Scope Assignment", 0) + 1
		if frappe.db.exists("User Permission"):
			for name in frappe.get_all("User Permission", filters={"user": user}, pluck="name"):
				frappe.delete_doc("User Permission", name, force=1, ignore_permissions=True)
		if frappe.db.exists("User", user):
			frappe.delete_doc("User", user, force=1, ignore_permissions=True)
			deleted["User"] = deleted.get("User", 0) + 1
	return deleted


def clear_kentender_mvp_v1_budget() -> dict[str, Any]:
	deleted: dict[str, int] = {}
	for budget_name in _collect_fixture_budgets():
		_delete_budget_graph(budget_name, deleted)

	# Orphan fixture lines / ledger by exact known codes / prefixes under namespace.
	for code in (
		C.BL_DHI_2027,
		C.BL_HWD_2027,
		C.BL_DHI_2028,
		C.BL_HWD_2028,
		C.CGK_BL_COLDCHAIN,
		"MOH-BL-CLOSED-2026",
		"MOH-BL-0003",
		"MOH-BL-0005",
		"MOH-BL-0006",
	):
		for name in frappe.get_all(
			"Budget Line", filters={"generated_reference": code}, pluck="name"
		):
			if not frappe.db.exists("Budget Line", name):
				continue
			frappe.delete_doc("Budget Line", name, force=1, ignore_permissions=True)
			deleted["Budget Line"] = deleted.get("Budget Line", 0) + 1

	for doctype, field, codes in (
		("Funding Reservation", "generated_reference", (C.RSV_CODE, C.RSV_SHORT_CODE)),
		("Procurement Commitment", "generated_reference", (C.COM_CODE,)),
		("Expenditure Snapshot", "generated_reference", (C.EXP_CODE,)),
	):
		if not frappe.db.exists("DocType", doctype):
			continue
		for code in codes:
			for name in frappe.get_all(doctype, filters={field: code}, pluck="name"):
				if not frappe.db.exists(doctype, name):
					continue
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
				deleted[doctype] = deleted.get(doctype, 0) + 1
	return {"ok": True, "deleted": deleted}


def clear_kentender_mvp_v1_scope_assignments() -> dict[str, int]:
	deleted: dict[str, int] = {}
	for doctype in ("User Scope Assignment", "Strategy Scope Assignment"):
		if not frappe.db.exists("DocType", doctype):
			continue
		count = 0
		for name in frappe.get_all(
			doctype,
			filters={"fixture_namespace": ["in", list(_NAMESPACES)]},
			pluck="name",
		):
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			count += 1
		deleted[doctype] = count
	return deleted


def clear_kentender_mvp_v1(
	*,
	include_strategy: bool = True,
	include_budget: bool = True,
	include_demands: bool = True,
	include_planning: bool = False,
) -> dict[str, Any]:
	out: dict[str, Any] = {"ok": True}
	out["scope_assignments"] = clear_kentender_mvp_v1_scope_assignments()
	# Reverse dependency: Planning → Demands → Budget → Strategy.
	if include_planning:
		from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
			clear_planning_fixture_rows,
		)

		out["planning"] = {"ok": True, "deleted": clear_planning_fixture_rows()}
	if include_demands:
		from kentender_core.seeds.kentender_mvp_v1.clear_demands import (
			clear_kentender_mvp_v1_demands,
		)

		out["demands"] = clear_kentender_mvp_v1_demands()
	if include_budget:
		out["budget"] = clear_kentender_mvp_v1_budget()
	if include_strategy:
		from kentender_strategy.seeds.kentender_mvp_v1_strategy import (
			clear_kentender_mvp_v1_strategy,
		)

		out["strategy"] = clear_kentender_mvp_v1_strategy()
	# After documents: drop leftover Playwright / Gate helper users.
	out["test_local_users"] = purge_test_local_users()
	return out
