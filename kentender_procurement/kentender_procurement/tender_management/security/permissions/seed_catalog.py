# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Idempotent ``Security Permission`` seed — SEC-0100.

Bench::

	bench --site kentender.midas.com execute \\
		kentender_procurement.tender_management.security.permissions.seed_catalog.run
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_management.security.permissions.catalog import (
	canonical_permission_definitions,
)


def upsert_all_permissions() -> dict[str, Any]:
	"""Insert or update all canonical rows; safe to run repeatedly."""
	frappe.set_user("Administrator")
	created = 0
	updated = 0
	for row in canonical_permission_definitions():
		pid = row["permission_id"]
		if not pid:
			continue
		if frappe.db.exists("Security Permission", pid):
			doc = frappe.get_doc("Security Permission", pid)
			changed = False
			for key in (
				"permission_name",
				"domain",
				"description",
				"risk_level",
				"audit_required",
				"active",
			):
				val = row.get(key)
				if doc.get(key) != val:
					doc.set(key, val)
					changed = True
			if changed:
				doc.save(ignore_permissions=True)
				updated += 1
		else:
			doc = frappe.new_doc("Security Permission")
			for key, val in row.items():
				doc.set(key, val)
			doc.insert(ignore_permissions=True)
			created += 1
	total = len(canonical_permission_definitions())
	return {
		"ok": True,
		"created": created,
		"updated": updated,
		"unchanged": total - created - updated,
		"total": total,
	}


def run() -> dict[str, Any]:
	"""``bench execute`` entrypoint."""
	return upsert_all_permissions()
