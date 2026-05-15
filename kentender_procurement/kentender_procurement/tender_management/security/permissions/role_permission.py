# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Role–permission alignment — SEC-0110."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_management.security.permissions.role_matrix import (
	CANONICAL_ROLE_CODES,
	RoleMatrixEntry,
	role_matrix_entry,
)
from kentender_procurement.tender_management.security.permissions.seed_role_matrix import (
	upsert_role_matrix,
)


class RolePermissionService:
	"""Canonical ``ROLE_*`` → ``PERM_*`` grant rows on ``Security Role``."""

	@staticmethod
	def canonical_role_codes() -> frozenset[str]:
		return CANONICAL_ROLE_CODES

	@staticmethod
	def matrix_entry(role_code: str) -> RoleMatrixEntry | None:
		return role_matrix_entry(role_code)

	@staticmethod
	def ensure_matrix_seeded() -> dict[str, Any]:
		"""Idempotent seed of pack §6 role grants (requires SEC-0100 catalogue)."""
		return upsert_role_matrix()

	@staticmethod
	def granted_ids_for_role(role_code: str) -> frozenset[str]:
		"""Return granted ``PERM_*`` names for ``role_code`` from DB, or empty."""
		rc = (role_code or "").strip()
		if not rc or not frappe.db.exists("Security Role", rc):
			return frozenset()
		doc = frappe.get_doc("Security Role", rc)
		return frozenset(
			row.permission for row in doc.assigned_permissions if row.permission
		)

	@staticmethod
	def expected_grants(role_code: str) -> frozenset[str]:
		"""Pack matrix grants for ``role_code`` (code-level, not DB)."""
		entry = role_matrix_entry(role_code)
		if not entry:
			return frozenset()
		return entry.grants
