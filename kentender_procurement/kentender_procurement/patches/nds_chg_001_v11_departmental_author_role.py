# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §6 — establish the ``Departmental Author`` role.

v1.1 renames ``Departmental Need Requester`` to ``Departmental Author`` and
removes ``Departmental Review Delegate`` outright: an acting Head of User
Department uses the same ``Head of User Department`` role with a time-bound
native User Permission (§1.1, §6, NDS-AC-042).

Runs pre-model-sync because the Departmental Needs DocType permission tables
reference ``Departmental Author`` by name.
"""

from __future__ import annotations

import frappe

RETIRED_ROLES = ("Departmental Need Requester", "Departmental Review Delegate")


def execute():
	_ensure_departmental_author()
	_carry_over_role_holders()
	_remove_retired_roles()


def _ensure_departmental_author():
	if not frappe.db.exists("Role", "Departmental Author"):
		frappe.get_doc(
			{"doctype": "Role", "role_name": "Departmental Author", "desk_access": 1}
		).insert(ignore_permissions=True)


def _carry_over_role_holders():
	"""Everyone who authored Needs keeps that authority under the new role name."""
	holders = frappe.get_all(
		"Has Role",
		filters={"role": "Departmental Need Requester", "parenttype": "User"},
		pluck="parent",
	)
	for user in set(holders):
		if not frappe.db.exists("User", user):
			continue
		if frappe.db.exists("Has Role", {"parent": user, "parenttype": "User", "role": "Departmental Author"}):
			continue
		user_doc = frappe.get_doc("User", user)
		user_doc.append("roles", {"role": "Departmental Author"})
		user_doc.save(ignore_permissions=True)


def _remove_retired_roles():
	"""§1.1 deletes these concepts rather than renaming or retaining them."""
	for role in RETIRED_ROLES:
		if not frappe.db.exists("Role", role):
			continue
		frappe.db.delete("Has Role", {"role": role})
		frappe.db.delete("Custom DocPerm", {"role": role})
		frappe.db.delete("DocPerm", {"role": role})
		frappe.delete_doc("Role", role, force=True, ignore_permissions=True)
