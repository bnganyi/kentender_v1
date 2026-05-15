# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Idempotent ``Security Role`` + child grants seed — SEC-0110.

Bench::

	bench --site kentender.midas.com execute \\
		kentender_procurement.tender_management.security.permissions.seed_role_matrix.run
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_management.security.permissions.role_matrix import (
	ROLE_MATRIX,
	RoleMatrixEntry,
)
from kentender_procurement.tender_management.security.permissions.service import (
	PermissionService,
)


def _child_permissions_match(doc: Any, expected_sorted: list[str]) -> bool:
	current = [row.permission for row in doc.assigned_permissions if row.permission]
	return sorted(current) == expected_sorted


def _set_child_grants(doc: Any, grants_sorted: list[str]) -> None:
	for row in list(doc.assigned_permissions or []):
		doc.remove(row)
	for pid in grants_sorted:
		doc.append("assigned_permissions", {"permission": pid})


def upsert_role_matrix() -> dict[str, Any]:
	"""Insert or update canonical roles and their grant rows; safe to run repeatedly."""
	frappe.set_user("Administrator")
	PermissionService.ensure_catalog_seeded()

	roles_created = 0
	roles_updated = 0
	roles_unchanged = 0

	for role_code, entry in sorted(ROLE_MATRIX.items(), key=lambda x: x[0]):
		action = _upsert_one_role(role_code, entry)
		if action == "created":
			roles_created += 1
		elif action == "updated":
			roles_updated += 1
		else:
			roles_unchanged += 1

	return {
		"ok": True,
		"roles_created": roles_created,
		"roles_updated": roles_updated,
		"roles_unchanged": roles_unchanged,
		"roles_total": len(ROLE_MATRIX),
	}


def _upsert_one_role(role_code: str, entry: RoleMatrixEntry) -> str:
	grants_sorted = sorted(entry.grants)
	if frappe.db.exists("Security Role", role_code):
		doc = frappe.get_doc("Security Role", role_code)
		if (
			doc.role_name == entry.role_name
			and (doc.description or "") == (entry.description or "")
			and int(doc.active or 0) == 1
			and _child_permissions_match(doc, grants_sorted)
		):
			return "unchanged"
		doc.role_name = entry.role_name
		doc.description = entry.description or ""
		doc.active = 1
		_set_child_grants(doc, grants_sorted)
		doc.save(ignore_permissions=True)
		return "updated"

	doc = frappe.new_doc("Security Role")
	doc.role_code = role_code
	doc.role_name = entry.role_name
	doc.description = entry.description or ""
	doc.active = 1
	for pid in grants_sorted:
		doc.append("assigned_permissions", {"permission": pid})
	doc.insert(ignore_permissions=True)
	return "created"


def run() -> dict[str, Any]:
	"""``bench execute`` entrypoint."""
	return upsert_role_matrix()
