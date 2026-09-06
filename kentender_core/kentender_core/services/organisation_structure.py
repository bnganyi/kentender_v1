# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AUTH-ADR-001 v1.6 §14.1 — Organisation structure administration.

Maintains the site's one organisational tree without exposing nested-set
internals. The UI never sees `lft`, `rgt`, `old_parent`, a raw parent id or a
repair control, so every one of those stays inside this service.

Three rules shape the whole module:

- **Exactly one root.** The root represents the site's Procuring Entity and
  is created by first-run configuration (CFG-CHG-002 v0.6 §4.3), never
  through the add dialog. A site whose root is missing is reported as
  needing the governed repair (`site_configuration.repair_organisation_root`)
  rather than silently growing a second root.
- **No Procuring Entity dimension.** One site is one PE; every unit belongs
  to it by construction, so nothing here takes or returns a PE.
- **Nothing is ever deleted or reparented.** §14.1 omits both: deletion
  would break historical evidence, and reparenting would silently change the
  effective scope of assignments already granted against a subtree.
"""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe.model.naming import make_autoname

from kentender_core.services.authorization import (
	ASSIGNMENT_DOCTYPE,
	STATUS_ENABLED,
	descendants_of,
	is_technical,
)
from kentender_core.services.responsibility_errors import fail

UNIT_DOCTYPE = "Organisation Unit"
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"

NAME_MIN = 2
NAME_MAX = 160


def require_structure_administrator(actor: str | None = None) -> str:
	"""§8 — Administrator and System Manager maintain System setup."""
	principal = actor or frappe.session.user
	if not is_technical(principal):
		fail(
			"AUTH_RESPONSIBILITY_REQUIRED",
			"You are not allowed to maintain the organisation structure.",
		)
	return principal


# --------------------------------------------------------------------------
# Reads
# --------------------------------------------------------------------------


def get_organisation_structure(selected: str = "") -> dict[str, Any]:
	"""§9.2 `GetOrganisationStructure` — tree, selection and allowed actions.

	Loads the whole tree from the root in one authorised call (§14.1) and
	returns an explicit `state` rather than an empty tree, because §13.9
	forbids representing a missing root or a load failure as a successful
	empty structure.
	"""
	require_structure_administrator()

	from kentender_core.services.site_configuration import is_configured

	if not is_configured():
		return {"state": "no_procuring_entity", "tree": []}

	root = _root()
	if not root:
		return {"state": "needs_repair", "tree": []}

	units = frappe.get_all(
		UNIT_DOCTYPE,
		fields=["name", "unit_code", "unit_name", "parent_organisation_unit", "status", "lft", "rgt", "modified"],
		order_by="lft asc, unit_name asc",
		limit_page_length=0,
	)
	tree = _as_tree(units, root)
	state = "empty_root" if len(units) == 1 else "ready"

	selected = selected if any(u["name"] == selected for u in units) else root
	return {
		"state": state,
		"root": root,
		"tree": tree,
		"selected": get_unit_detail(selected),
	}


def get_unit_detail(unit_id: str) -> dict[str, Any]:
	"""Right-panel content for one unit: path, coverage, impact and actions."""
	row = frappe.db.get_value(
		UNIT_DOCTYPE,
		unit_id,
		["name", "unit_code", "unit_name", "parent_organisation_unit", "status", "modified"],
		as_dict=True,
	)
	if not row:
		fail("AUTH_CONFIGURATION_INVALID", "That organisation unit no longer exists.")

	is_root = not row.parent_organisation_unit
	descendants = descendants_of({unit_id}) - {unit_id}
	active_assignments = _active_assignment_count(unit_id)
	parent_active = (
		True
		if is_root
		else frappe.db.get_value(UNIT_DOCTYPE, row.parent_organisation_unit, "status") == STATUS_ACTIVE
	)
	active = row.status == STATUS_ACTIVE

	return {
		"id": row.name,
		"code": row.unit_code,
		"name": row.unit_name,
		"is_root": is_root,
		"status": row.status,
		"path": _path_of(unit_id),
		"descendant_count": len(descendants),
		"active_assignments": active_assignments,
		"expected_version": str(row.modified),
		# §14.1 — availability is decided by the server, never by the client.
		"actions": {
			"add_child": active,
			"rename": not is_root,
			"deactivate": active and not is_root,
			"reactivate": (not active) and (not is_root) and parent_active,
		},
	}


def _root() -> str:
	roots = frappe.get_all(
		UNIT_DOCTYPE,
		filters={"parent_organisation_unit": ("is", "not set")},
		pluck="name",
		order_by="creation asc",
		limit_page_length=0,
	)
	return roots[0] if roots else ""


def _as_tree(units: list[dict[str, Any]], root: str) -> list[dict[str, Any]]:
	"""Nest the flat rows, in `lft` order so siblings keep their tree order."""
	nodes = {
		row["name"]: {
			"id": row["name"],
			"code": row["unit_code"],
			"name": row["unit_name"],
			"status": row["status"],
			"is_root": not row["parent_organisation_unit"],
			"children": [],
		}
		for row in units
	}
	ordered: list[dict[str, Any]] = []
	for row in units:
		node = nodes[row["name"]]
		parent = nodes.get(row["parent_organisation_unit"] or "")
		if parent is None:
			ordered.append(node)
		else:
			parent["children"].append(node)
	# Only the site root is expected at the top; anything else means the repair
	# has not run, and showing it is better than hiding a real inconsistency.
	ordered.sort(key=lambda n: (n["id"] != root, n["name"]))
	return ordered


def _path_of(unit_id: str) -> list[str]:
	"""Root-first display path. Bounded so a corrupt parent chain cannot spin."""
	names: list[str] = []
	current = unit_id
	for _ in range(24):
		row = frappe.db.get_value(
			UNIT_DOCTYPE, current, ["unit_name", "parent_organisation_unit"], as_dict=True
		)
		if not row:
			break
		names.append(row.unit_name)
		if not row.parent_organisation_unit:
			break
		current = row.parent_organisation_unit
	return list(reversed(names))


def _active_assignment_count(unit_id: str) -> int:
	"""Enabled assignments naming this unit exactly.

	Deliberately not the subtree count: deactivating a unit affects the
	assignments made *on* it, and an assignment on an ancestor keeps covering
	the rest of its own subtree either way.
	"""
	return frappe.db.count(
		ASSIGNMENT_DOCTYPE, {"organisation_unit": unit_id, "status": STATUS_ENABLED}
	)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def add_organisation_unit(
	*, parent_id: str = "", name: str = "", idempotency_key: str = ""
) -> dict[str, Any]:
	"""§9.2 `AddOrganisationUnit` — one child beneath an existing unit.

	Opens beneath the selected parent, or beneath the root when none is
	given; unavailable while the root is missing (§14.1).
	"""
	require_structure_administrator()
	name = _clean_name(name)

	root = _root()
	if not root:
		fail(
			"AUTH_CONFIGURATION_INVALID",
			"The root organisation unit is missing. Run the governed repair before adding units.",
		)
	parent_id = parent_id or root
	parent = frappe.db.get_value(UNIT_DOCTYPE, parent_id, ["status"], as_dict=True)
	if not parent:
		fail("AUTH_CONFIGURATION_INVALID", "The parent organisation unit no longer exists.")
	if parent.status != STATUS_ACTIVE:
		fail(
			"AUTH_STATE_CHANGED",
			"Reactivate the parent organisation unit before adding a unit beneath it.",
		)

	# Idempotency is keyed on the business identity — same parent, same name —
	# not on the supplied key alone, so a retried request and a genuine
	# duplicate collapse onto the same answer (§9.2).
	existing = _sibling_with_name(parent_id, name)
	if existing:
		return {"unit": existing, "created": False}

	doc = frappe.get_doc(
		{
			"doctype": UNIT_DOCTYPE,
			"unit_code": _generate_code(),
			"unit_name": name,
			"parent_organisation_unit": parent_id,
			"status": STATUS_ACTIVE,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"unit": doc.name, "created": True}


def rename_organisation_unit(*, unit_id: str, name: str, expected_version: str = "") -> dict[str, Any]:
	"""§9.2 `RenameOrganisationUnit` — display name only; code immutable."""
	require_structure_administrator()
	name = _clean_name(name)
	doc = _locked(unit_id, expected_version)
	if not doc.parent_organisation_unit:
		fail("AUTH_STATE_CHANGED", "The root organisation unit is named after the site's Procuring Entity.")

	clash = _sibling_with_name(doc.parent_organisation_unit, name)
	if clash and clash != doc.name:
		fail(
			"AUTH_CONFIGURATION_INVALID",
			"Another organisation unit beneath the same parent already uses that name.",
		)

	doc.unit_name = name
	doc.save(ignore_permissions=True)
	return {"unit": doc.name, "name": doc.unit_name}


def set_organisation_unit_active(
	*, unit_id: str, active: bool, expected_version: str = ""
) -> dict[str, Any]:
	"""§9.2 `SetOrganisationUnitActive` — never a delete.

	Deactivation keeps every historical record and assignment visible; it only
	removes the unit from the offers a new assignment can be made against.
	"""
	require_structure_administrator()
	doc = _locked(unit_id, expected_version)
	if not doc.parent_organisation_unit:
		fail("AUTH_STATE_CHANGED", "The root organisation unit cannot be deactivated.")

	target = STATUS_ACTIVE if active else STATUS_INACTIVE
	if doc.status == target:
		return {"unit": doc.name, "status": doc.status, "changed": False}

	if active:
		parent_status = frappe.db.get_value(UNIT_DOCTYPE, doc.parent_organisation_unit, "status")
		if parent_status != STATUS_ACTIVE:
			fail(
				"AUTH_STATE_CHANGED",
				"Reactivate the parent organisation unit first.",
			)
	else:
		active_children = frappe.db.count(
			UNIT_DOCTYPE, {"parent_organisation_unit": doc.name, "status": STATUS_ACTIVE}
		)
		if active_children:
			fail(
				"AUTH_STATE_CHANGED",
				"Deactivate the organisation units beneath this one first.",
			)

	doc.status = target
	doc.save(ignore_permissions=True)
	return {"unit": doc.name, "status": doc.status, "changed": True}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def _clean_name(name: str) -> str:
	name = " ".join((name or "").split())
	if not (NAME_MIN <= len(name) <= NAME_MAX):
		fail(
			"AUTH_CONFIGURATION_INVALID",
			f"Enter an organisation unit name of {NAME_MIN}–{NAME_MAX} characters.",
		)
	return name


def _normalized(name: str) -> str:
	"""§4.2 — sibling uniqueness after normalised comparison."""
	return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def _sibling_with_name(parent_id: str, name: str) -> str:
	wanted = _normalized(name)
	for row in frappe.get_all(
		UNIT_DOCTYPE,
		filters={"parent_organisation_unit": parent_id, "status": STATUS_ACTIVE},
		fields=["name", "unit_name"],
		limit_page_length=0,
	):
		if _normalized(row["unit_name"]) == wanted:
			return row["name"]
	return ""


def _generate_code() -> str:
	"""CFG v0.6 §4.3 — `OU-{pe_code_suffix}-{sequence}`, generated on insert,
	immutable, never user-entered."""
	pe_code = (frappe.db.get_single_value("Site Procuring Entity", "pe_code") or "").upper()
	if pe_code.startswith("PE-"):
		pe_code = pe_code[3:]
	prefix = re.sub(r"[^A-Z0-9]+", "", pe_code) or "OU"
	return make_autoname(f"OU-{prefix}-.#####")


def _locked(unit_id: str, expected_version: str):
	"""Load one unit under a row lock, refusing a stale write.

	`modified` is Frappe's own optimistic-concurrency token, so this reuses the
	framework's mechanism rather than adding a parallel version column.
	"""
	frappe.db.sql(
		"select name from `tabOrganisation Unit` where name = %s for update", unit_id
	)
	if not frappe.db.exists(UNIT_DOCTYPE, unit_id):
		fail("AUTH_CONFIGURATION_INVALID", "That organisation unit no longer exists.")
	doc = frappe.get_doc(UNIT_DOCTYPE, unit_id)
	if expected_version and str(doc.modified) != str(expected_version):
		fail("AUTH_STATE_CHANGED", "This organisation unit changed. Reload and try again.")
	return doc
