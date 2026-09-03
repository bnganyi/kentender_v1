"""AUTH-ADR-001 v1.6 §11.1/§11.2 — the pre-cutover reconciliation. Never writes.

Produces the read-only inventory §11.1 requires — every retired authority
store, the organisation hierarchy, and the User Responsibility Assignments
they imply — so the cutover creates assignments from evidence rather than
assumption. One site is one Procuring Entity, so a proposal carries either
site-wide scope or one exact Organisation Unit; there is no PE dimension.

§11.2's mapping rules are enforced as *refusals*, not best guesses:

- convert a row only when user, business role, Organisation Unit and
  effective period are unambiguous;
- never infer a role from access scope alone, or scope from a role alone;
- never create a Fiscal Year assignment;
- never broaden a leaf Organisation Unit to its parent to reduce row count;
- map a Procurement Department to one exact Organisation Unit, or block it.

Anything that fails one of those rules lands in `blocked` with the reason,
for explicit administrator resolution (AUTH-AC-035).

§11.4's boundary is applied here too: only KenTender-owned User Permission
rows are migration debt. ERPNext and HRMS rows (Company, Cost Center,
Employee, Department, …) are load-bearing and are reported under
`preserved_framework_permissions`, never proposed for conversion or cleanup.

Invoke via:
  bench --site <site> execute \\
    kentender_core.scripts.responsibility_reconciliation.print_report
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services.business_role_registry import (
	REGISTRY,
	SCOPE_OU,
	SCOPE_SITE,
)

# Retired stores. Each is counted and read for evidence only — never as
# authority — and each may be absent on a site that has already been cleaned.
RETIRED_STORES = (
	"User Scope Assignment",
	"Capability Profile",
	"Operational Scope Assignment",
	"Authorization Delegation",
)

# §11.4 — the ONLY User Permission `allow` values KenTender owns. The cleanup
# enumerates its permitted values explicitly rather than filtering by
# exclusion; everything else is ERPNext/HRMS load-bearing data.
KENTENDER_OWNED_ALLOWS = (
	"Procuring Entity",
	"Organisation Unit",
	"Financial Year",
	"PE Fiscal Year Context",
	"Procuring Department",
)

BLOCK_UNREGISTERED_ROLE = "Role is not a registered KenTender responsibility"
BLOCK_MISSING_ORG_UNIT = "Departmental responsibility with no Organisation Unit evidence"
BLOCK_AMBIGUOUS_ORG_UNIT = "Several Organisation Units and no evidence of which applies"
BLOCK_UNKNOWN_ORG_UNIT = "Organisation Unit evidence names a unit that no longer exists"
BLOCK_DEPARTMENT_UNMAPPED = "Procurement Department maps to no exact Organisation Unit"


def _exists(doctype: str) -> bool:
	return bool(frappe.db.exists("DocType", doctype))


def _store_counts() -> dict[str, int]:
	counts = {name: frappe.db.count(name) for name in RETIRED_STORES if _exists(name)}
	if _exists("User Permission"):
		counts["User Permission (KenTender-owned)"] = frappe.db.count(
			"User Permission", {"allow": ("in", KENTENDER_OWNED_ALLOWS)}
		)
	return counts


def _preserved_framework_permissions() -> dict[str, int]:
	"""§11.4 — rows the cleanup must never touch, shown so a reviewer can see
	the boundary being respected."""
	if not _exists("User Permission"):
		return {}
	rows = frappe.get_all(
		"User Permission",
		filters={"allow": ("not in", KENTENDER_OWNED_ALLOWS)},
		fields=["allow"],
		limit_page_length=0,
	)
	out: dict[str, int] = {}
	for row in rows:
		out[row["allow"]] = out.get(row["allow"], 0) + 1
	return out


def _user_permission_units(user: str) -> set[str]:
	if not _exists("User Permission"):
		return set()
	return set(
		frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Organisation Unit"},
			pluck="for_value",
		)
	)


def _scope_assignment_rows(user: str) -> list[dict[str, Any]]:
	if not _exists("User Scope Assignment"):
		return []
	return frappe.get_all(
		"User Scope Assignment",
		filters={"user": user},
		fields=[
			"name",
			"role",
			"organisation_unit",
			"effective_from",
			"effective_to",
		],
	)


def _candidate_users() -> list[str]:
	"""Every enabled System User holding at least one registered projection."""
	projected: set[str] = set()
	for entry in REGISTRY.values():
		projected.update(entry.frappe_roles)
	if not projected:
		return []
	holders = set(
		frappe.get_all(
			"Has Role", filters={"role": ("in", sorted(projected))}, pluck="parent"
		)
	)
	enabled = set(
		frappe.get_all(
			"User",
			filters={"name": ("in", sorted(holders)), "enabled": 1, "user_type": "System User"},
			pluck="name",
		)
	) if holders else set()
	# Administrator is a technical account (§8): frappe.get_roles reports every
	# Role for it, which is projection noise, never business evidence — and
	# seeds shall not grant Administrator business roles anyway.
	enabled.discard("Administrator")
	return sorted(enabled)


def _held_responsibilities(user: str) -> list[str]:
	"""Registered responsibilities implied by this user's Frappe Roles.

	§11.2 forbids inferring a role from access scope alone, so the Frappe Role
	is the only admissible evidence of *which* responsibility a user holds.
	"""
	held = set(frappe.get_roles(user))
	return sorted(
		name for name, entry in REGISTRY.items() if set(entry.frappe_roles) & held
	)


def _already_assigned(user: str, business_role: str) -> bool:
	return bool(
		frappe.db.exists(
			"User Responsibility Assignment",
			{"user": user, "business_role": business_role, "status": "Enabled"},
		)
	)


def _propose(user: str, business_role: str) -> dict[str, Any]:
	"""One proposed assignment, or one blocked row with its exact reason."""
	entry = REGISTRY[business_role]

	if entry.scope_type == SCOPE_SITE:
		return {
			"user": user,
			"business_role": business_role,
			"organisation_unit": "",
			"sources": ["Has Role"],
		}

	assert entry.scope_type == SCOPE_OU
	# The departmental dimension must be exact. A user permitted on several
	# units gives no evidence of which one this responsibility applies to, and
	# choosing their parent to collapse the rows is exactly what §11.2
	# prohibits.
	sources: list[str] = []
	scope_rows = [row for row in _scope_assignment_rows(user) if row.get("role") == business_role]
	units = {row["organisation_unit"] for row in scope_rows if row.get("organisation_unit")}
	if units:
		sources.append("User Scope Assignment")
	else:
		units = _user_permission_units(user)
		if units:
			sources.append("User Permission")

	if not units:
		return {"user": user, "business_role": business_role, "blocked": BLOCK_MISSING_ORG_UNIT}
	missing = {unit for unit in units if not frappe.db.exists("Organisation Unit", unit)}
	if missing:
		return {
			"user": user,
			"business_role": business_role,
			"blocked": BLOCK_UNKNOWN_ORG_UNIT,
			"candidates": sorted(missing),
		}
	if len(units) > 1:
		return {
			"user": user,
			"business_role": business_role,
			"blocked": BLOCK_AMBIGUOUS_ORG_UNIT,
			"candidates": sorted(units),
		}
	return {
		"user": user,
		"business_role": business_role,
		"organisation_unit": units.pop(),
		"sources": sources,
	}


def _department_mapping() -> list[dict[str, Any]]:
	"""§11.2 — every Procurement Department must map to one exact OU."""
	if not _exists("Procuring Department"):
		return []
	rows: list[dict[str, Any]] = []
	for department in frappe.get_all(
		"Procuring Department", fields=["name", "department_name", "department_code"]
	):
		match = frappe.get_all(
			"Organisation Unit",
			filters={"unit_name": department.department_name},
			pluck="name",
		)
		rows.append(
			{
				"procurement_department": department.name,
				"department_name": department.department_name,
				"organisation_unit": match[0] if len(match) == 1 else "",
				"blocked": "" if len(match) == 1 else BLOCK_DEPARTMENT_UNMAPPED,
				"candidates": match,
			}
		)
	return rows


def _hierarchy_health() -> dict[str, Any]:
	"""§4.2 — the site-local tree the predicate depends on."""
	units = frappe.get_all(
		"Organisation Unit",
		fields=["name", "parent_organisation_unit", "lft", "rgt"],
	)
	unstamped = [u["name"] for u in units if not u.get("rgt")]
	names = {u["name"] for u in units}
	dangling = [
		u["name"]
		for u in units
		if u.get("parent_organisation_unit") and u["parent_organisation_unit"] not in names
	]
	roots = [u["name"] for u in units if not u.get("parent_organisation_unit")]
	return {
		"organisation_units": len(units),
		"roots": roots,
		"single_root": len(roots) == 1,
		"unstamped_ranges": unstamped,
		"dangling_parents": dangling,
	}


def _financial_year_grants() -> dict[str, int]:
	"""§11.2 — reported so they can be removed, never converted."""
	counts: dict[str, int] = {}
	if not _exists("User Permission"):
		return counts
	for allow in ("Financial Year", "PE Fiscal Year Context", "Procuring Department"):
		counts[allow] = frappe.db.count("User Permission", {"allow": allow})
	return counts


def build_report(users: list[str] | None = None) -> dict[str, Any]:
	"""The complete §11.1 reconciliation. Read-only; creates nothing."""
	candidates = users or _candidate_users()
	proposed: list[dict[str, Any]] = []
	blocked: list[dict[str, Any]] = []
	already: list[dict[str, str]] = []

	for user in candidates:
		responsibilities = _held_responsibilities(user)
		if not responsibilities:
			continue
		for business_role in responsibilities:
			if _already_assigned(user, business_role):
				already.append({"user": user, "business_role": business_role})
				continue
			row = _propose(user, business_role)
			(blocked if row.get("blocked") else proposed).append(row)

	departments = _department_mapping()
	report = {
		"generated_at": str(now_datetime()),
		"users_examined": len(candidates),
		"retired_store_counts": _store_counts(),
		"preserved_framework_permissions": _preserved_framework_permissions(),
		"financial_year_grants_to_remove": _financial_year_grants(),
		"organisation_hierarchy": _hierarchy_health(),
		"procurement_department_mapping": departments,
		"already_assigned": already,
		"proposed_assignments": proposed,
		"blocked": blocked + [row for row in departments if row.get("blocked")],
	}
	report["ok"] = not report["blocked"]
	return report


def print_report(users: list[str] | None = None) -> dict[str, Any]:
	"""Same report, rendered for a `bench execute` run."""
	report = build_report(users)
	print(f"AUTH-ADR-001 v1.6 reconciliation — {report['generated_at']}")
	print(f"  users examined              : {report['users_examined']}")
	print(f"  retired store row counts    : {report['retired_store_counts']}")
	print(f"  preserved ERPNext/HRMS perms: {report['preserved_framework_permissions']}")
	print(f"  FY/department grants        : {report['financial_year_grants_to_remove']}")
	print(f"  organisation hierarchy      : {report['organisation_hierarchy']}")
	print(f"  already assigned            : {len(report['already_assigned'])}")
	print(f"  proposed assignments        : {len(report['proposed_assignments'])}")
	print(f"  blocked, needs a decision   : {len(report['blocked'])}")
	for row in report["blocked"]:
		print(f"    - {row}")
	return report
