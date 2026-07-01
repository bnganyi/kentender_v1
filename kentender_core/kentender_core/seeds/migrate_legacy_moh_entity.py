"""One-time migration: legacy MOH Procuring Entity links → canonical PE-MOH.

Run::

    bench --site kentender.midas.com execute \\
        kentender_core.seeds.migrate_legacy_moh_entity.run
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.procuring_entity_canonical import CANONICAL_MOH_ENTITY, LEGACY_MOH_ENTITY


def _update_link_field(doctype: str, field: str) -> int:
	if not frappe.db.has_column(doctype, field):
		return 0
	before = frappe.db.count(doctype, {field: LEGACY_MOH_ENTITY})
	if not before:
		return 0
	frappe.db.sql(
		f"""
		UPDATE `tab{doctype}`
		SET `{field}` = %s, modified = modified
		WHERE `{field}` = %s
		""",
		(CANONICAL_MOH_ENTITY, LEGACY_MOH_ENTITY),
	)
	return before


def run() -> dict[str, Any]:
	"""Rewrite legacy MOH procuring entity links to PE-MOH where both records exist."""
	if not frappe.db.exists("Procuring Entity", CANONICAL_MOH_ENTITY):
		return {
			"ok": False,
			"message": f"Canonical entity {CANONICAL_MOH_ENTITY} not found; run WORKS master seed first.",
		}

	counts: dict[str, int] = {
		"demands": _update_link_field("Demand", "procuring_entity"),
		"departments": _update_link_field("Procuring Department", "procuring_entity"),
		"budgets": _update_link_field("Budget", "procuring_entity"),
		"budget_lines": _update_link_field("Budget Line", "procuring_entity"),
	}

	if frappe.db.has_column("User", "kt_procuring_entity"):
		user_before = frappe.db.count("User", {"kt_procuring_entity": LEGACY_MOH_ENTITY})
		if user_before:
			frappe.db.sql(
				"""
				UPDATE `tabUser`
				SET kt_procuring_entity = %s, modified = modified
				WHERE kt_procuring_entity = %s
				""",
				(CANONICAL_MOH_ENTITY, LEGACY_MOH_ENTITY),
			)
		counts["users"] = user_before

	# User Permission rows scoped to legacy MOH
	if frappe.db.exists("DocType", "User Permission"):
		perm_before = frappe.db.count(
			"User Permission",
			{"allow": "Procuring Entity", "for_value": LEGACY_MOH_ENTITY},
		)
		if perm_before:
			frappe.db.sql(
				"""
				UPDATE `tabUser Permission`
				SET for_value = %s, modified = modified
				WHERE allow = 'Procuring Entity' AND for_value = %s
				""",
				(CANONICAL_MOH_ENTITY, LEGACY_MOH_ENTITY),
			)
		counts["user_permissions"] = perm_before

	frappe.db.commit()
	return {"ok": True, "updated": counts, "canonical": CANONICAL_MOH_ENTITY}
