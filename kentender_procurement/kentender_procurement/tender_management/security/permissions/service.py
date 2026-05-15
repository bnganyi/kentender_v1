# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Permission catalogue service — SEC-0100."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_management.security.permissions.catalog import (
	CANONICAL_PERMISSION_IDS,
	canonical_permission_definitions,
)
from kentender_procurement.tender_management.security.permissions.seed_catalog import (
	upsert_all_permissions,
)


class PermissionService:
	"""Canonical ``PERM_*`` catalogue persistence on ``Security Permission``."""

	@staticmethod
	def canonical_ids() -> frozenset[str]:
		return CANONICAL_PERMISSION_IDS

	@staticmethod
	def definitions() -> list[dict[str, Any]]:
		return canonical_permission_definitions()

	@staticmethod
	def ensure_catalog_seeded() -> dict[str, Any]:
		"""Idempotent seed of all pack §5 permissions."""
		return upsert_all_permissions()

	@staticmethod
	def get_permission_row(permission_id: str) -> dict[str, Any] | None:
		"""Return DB row as dict, or ``None`` if missing."""
		pid = (permission_id or "").strip()
		if not pid or not frappe.db.exists("Security Permission", pid):
			return None
		return frappe.db.get_value(
			"Security Permission",
			pid,
			[
				"name",
				"permission_id",
				"permission_name",
				"domain",
				"description",
				"risk_level",
				"audit_required",
				"active",
			],
			as_dict=True,
		)
