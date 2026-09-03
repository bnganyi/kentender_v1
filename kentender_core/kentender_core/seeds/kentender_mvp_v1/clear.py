# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Clear explicitly owned KENTENDER_MVP_V1 and Playwright fixture rows.

Contract §8.3 forbids treating Procuring Entity ownership as fixture ownership.
Every deletion below therefore requires a namespace, exact canonical identity, or
a narrow legacy browser-test signature.
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
	C.PLAYWRIGHT_FIXTURE_NS,
	"DEMANDS_UI03_FACTORY",
	"DEMANDS_UI04_FACTORY",
	"DEMANDS_UI05_FACTORY",
	"DEMANDS_UI06_FACTORY",
	"DEMANDS_UI07_FACTORY",
	"DEMANDS_UI07_MM_FACTORY",
	"DEMANDS_UI09_FACTORY",
)

_PLAYWRIGHT_NAMESPACES = _NAMESPACES[2:]

_BUDGET_CHILD_DOCTYPES = (
	"Funding Reservation",
	"Budget Audit Event",
	"Budget Version",
	"Budget Line",
)

# Exact fixture budget codes (MOH + CGK + known edge codes).
_CANONICAL_BUDGET_CODES = (
	C.BUD_ACTIVE,
	C.CGK_BUD_ACTIVE,
)

_PLAYWRIGHT_BUDGET_CODES = (
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
	# Procurement Commitment and Budget Line Version have no direct `budget`
	# field (only `reservation` / `budget_version` respectively), so each
	# needs its own hop through this Budget's own Funding Reservation / Budget
	# Version rows, deleted before those parents.
	if frappe.db.exists("DocType", "Procurement Commitment") and frappe.db.exists("DocType", "Funding Reservation"):
		reservation_names = frappe.get_all("Funding Reservation", filters={"budget": budget_name}, pluck="name")
		if reservation_names:
			for name in frappe.get_all(
				"Procurement Commitment", filters={"reservation": ["in", reservation_names]}, pluck="name"
			):
				frappe.delete_doc("Procurement Commitment", name, force=1, ignore_permissions=True)
				deleted["Procurement Commitment"] = deleted.get("Procurement Commitment", 0) + 1

	if frappe.db.exists("DocType", "Budget Line Version") and frappe.db.exists("DocType", "Budget Version"):
		version_names = frappe.get_all("Budget Version", filters={"budget": budget_name}, pluck="name")
		if version_names:
			for name in frappe.get_all(
				"Budget Line Version", filters={"budget_version": ["in", version_names]}, pluck="name"
			):
				frappe.delete_doc("Budget Line Version", name, force=1, ignore_permissions=True)
				deleted["Budget Line Version"] = deleted.get("Budget Line Version", 0) + 1

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


def _collect_fixture_budgets(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> list[str]:
	names: list[str] = []
	if frappe.db.has_column("Budget", "fixture_namespace"):
		namespaces = []
		if include_canonical:
			namespaces.extend((C.FIXTURE_NS, C.LEGACY_FIXTURE_NS))
		if include_playwright:
			namespaces.extend((EDGE_NS, LEGACY_EDGE_NS, TEST_ACTIVITY_NS, C.PLAYWRIGHT_FIXTURE_NS))
		if namespaces:
			names.extend(
				frappe.get_all(
					"Budget",
					filters={"fixture_namespace": ["in", namespaces]},
					pluck="name",
				)
			)
	for code in (
		list(_CANONICAL_BUDGET_CODES) if include_canonical else []
	) + (list(_PLAYWRIGHT_BUDGET_CODES) if include_playwright else []):
		names.extend(
			frappe.get_all("Budget", filters={"generated_reference": code}, pluck="name")
		)
	if include_playwright:
		# Planning Finance helpers have a reserved generated-reference prefix.
		names.extend(
			frappe.get_all(
				"Budget",
				filters={"generated_reference": ["like", "MOH-BUD-PLN-%"]},
				pluck="name",
			)
		)
	return _unique(names)


def _delete_test_users(users: list[str]) -> dict[str, int]:
	deleted: dict[str, int] = {}
	keep = set(C.CANONICAL_USERS) | {"Administrator", "Guest"}
	for user in _unique(users):
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
				deleted["User Permission"] = deleted.get("User Permission", 0) + 1
		# Frappe may create a Contact linked to a disposable System User. Keeping
		# that Contact while recreating the same browser persona causes the User
		# insert hook to race its own contact update and raises TimestampMismatch.
		if frappe.db.exists("DocType", "Contact") and frappe.db.has_column("Contact", "user"):
			for name in frappe.get_all("Contact", filters={"user": user}, pluck="name"):
				frappe.delete_doc("Contact", name, force=1, ignore_permissions=True)
				deleted["Contact"] = deleted.get("Contact", 0) + 1
		if frappe.db.exists("User", user):
			frappe.delete_doc("User", user, force=1, ignore_permissions=True)
			deleted["User"] = deleted.get("User", 0) + 1
	return deleted


def purge_dem_test_users(
	*, users: list[str] | tuple[str, ...] | str | None = None, commit: bool = True
) -> dict[str, Any]:
	"""Delete all, or an exact subset of, reserved `dem-*` test accounts."""
	frappe.only_for(("System Manager", "Administrator"))
	if users is None:
		users = frappe.get_all(
			"User",
			filters={"name": ["like", "dem-%@example.com"]},
			pluck="name",
		)
	if isinstance(users, str):
		users = frappe.parse_json(users)
	if not isinstance(users, (list, tuple)):
		frappe.throw("users must be a JSON list of dem-* test account emails")
	requested = _unique([str(user).strip() for user in users])
	invalid = [
		user
		for user in requested
		if not (user.startswith("dem-") and user.endswith("@example.com"))
	]
	if invalid:
		frappe.throw(f"Refusing to delete non-dem test users: {', '.join(invalid)}")

	try:
		deleted = _delete_test_users(requested)
		if commit:
			frappe.db.commit()
		return {"ok": True, "requested": requested, "deleted": deleted}
	except Exception:
		frappe.db.rollback()
		raise


def purge_test_local_users() -> dict[str, int]:
	"""Remove reserved automated-test users while keeping canonical personas."""
	users: list[str] = []
	for pattern in ("%@test.local", "dem-%@example.com"):
		users.extend(
			frappe.get_all(
				"User",
				filters={"name": ["like", pattern]},
				pluck="name",
			)
		)
	users.extend(user for user in C.PLAYWRIGHT_USERS if frappe.db.exists("User", user))
	return _delete_test_users(users)


def clear_kentender_mvp_v1_budget(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, Any]:
	deleted: dict[str, int] = {}
	for budget_name in _collect_fixture_budgets(
		include_canonical=include_canonical, include_playwright=include_playwright
	):
		_delete_budget_graph(budget_name, deleted)

	# Orphan fixture lines / ledger by exact known canonical codes.
	canonical_line_codes = (
		(
			C.BL_DHI_2027,
			C.BL_HWD_2027,
			C.CGK_BL_DIGSVC,
		)
		if include_canonical
		else ()
	)
	for code in canonical_line_codes:
		for name in frappe.get_all(
			"Budget Line", filters={"generated_reference": code}, pluck="name"
		):
			if not frappe.db.exists("Budget Line", name):
				continue
			frappe.delete_doc("Budget Line", name, force=1, ignore_permissions=True)
			deleted["Budget Line"] = deleted.get("Budget Line", 0) + 1

	canonical_ledger_codes = (
		(
			("Funding Reservation", "generated_reference", (C.RSV_CODE, C.RSV_SHORT_CODE)),
			("Procurement Commitment", "generated_reference", (C.COM_CODE,)),
			("Expenditure Snapshot", "generated_reference", (C.EXP_CODE,)),
		)
		if include_canonical
		else ()
	)
	for doctype, field, codes in canonical_ledger_codes:
		if not frappe.db.exists("DocType", doctype):
			continue
		for code in codes:
			for name in frappe.get_all(doctype, filters={field: code}, pluck="name"):
				if not frappe.db.exists(doctype, name):
					continue
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
				deleted[doctype] = deleted.get(doctype, 0) + 1
	return {"ok": True, "deleted": deleted}


def clear_kentender_mvp_v1_scope_assignments(
	*, include_canonical: bool = True, include_playwright: bool = True
) -> dict[str, int]:
	deleted: dict[str, int] = {}
	namespaces = []
	if include_canonical:
		namespaces.extend((C.FIXTURE_NS, C.LEGACY_FIXTURE_NS))
	if include_playwright:
		namespaces.extend(_PLAYWRIGHT_NAMESPACES)
	for doctype in ("User Scope Assignment", "Strategy Scope Assignment"):
		if not namespaces or not frappe.db.exists("DocType", doctype):
			continue
		count = 0
		for name in frappe.get_all(
			doctype,
			filters={"fixture_namespace": ["in", namespaces]},
			pluck="name",
		):
			frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			count += 1
		deleted[doctype] = count
	return deleted


def purge_kentender_playwright_data(*, commit: bool = True) -> dict[str, Any]:
	"""Remove known browser-test artifacts without deleting canonical or business records."""
	frappe.only_for(("System Manager", "Administrator"))
	frappe.set_user("Administrator")
	from kentender_core.seeds.kentender_mvp_v1.clear_demands import (
		clear_kentender_mvp_v1_demands,
	)
	from kentender_procurement.procurement_planning.seeds.kentender_mvp_v1 import (
		clear_planning_fixture_rows,
	)
	from kentender_strategy.seeds.kentender_mvp_v1_strategy import (
		clear_kentender_mvp_v1_strategy,
	)

	try:
		out = {
			"ok": True,
			"planning": clear_planning_fixture_rows(
				include_canonical=False, include_playwright=True
			),
			"demands": clear_kentender_mvp_v1_demands(
				include_canonical=False, include_playwright=True
			),
			"budget": clear_kentender_mvp_v1_budget(
				include_canonical=False, include_playwright=True
			),
			"strategy": clear_kentender_mvp_v1_strategy(
				include_canonical=False, include_playwright=True
			),
			"scope_assignments": clear_kentender_mvp_v1_scope_assignments(
				include_canonical=False, include_playwright=True
			),
			"users": purge_test_local_users(),
		}
		if commit:
			frappe.db.commit()
		return out
	except Exception:
		frappe.db.rollback()
		raise


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
