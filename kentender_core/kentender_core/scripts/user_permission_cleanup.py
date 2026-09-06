"""AUTH-ADR-001 v1.6 §11.4 — the scoped User Permission cleanup, DRY-RUN ONLY.

This module never deletes anything. It enumerates exactly which User
Permission rows *would* be removed at the removal phase, so the output can be
reviewed before execution (§18.3: "the cleanup dry-run output enumerating
exactly which User Permission rows would be deleted has been reviewed before
execution").

The §11.4 boundary is expressed as an explicit allow-list, never a filter by
exclusion: only rows whose `allow` names a KenTender-owned link doctype are
candidates. ERPNext and HRMS rows — Company, Cost Center, Employee,
Department and anything else — are load-bearing for accounting and payroll
and are NEVER touched (AUTH-AC-036).

The executable deletion lands only in the removal phase (§11.3 step 11),
after cutover evidence is complete, as a separate reviewed change.

Run:
  bench --site <site> execute \\
    kentender_core.scripts.user_permission_cleanup.dry_run
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.scripts.responsibility_reconciliation import KENTENDER_OWNED_ALLOWS


def dry_run() -> dict[str, Any]:
	if not frappe.db.exists("DocType", "User Permission"):
		print("No User Permission DocType on this site.")
		return {"would_delete": [], "preserved_counts": {}}

	candidates = frappe.get_all(
		"User Permission",
		filters={"allow": ("in", KENTENDER_OWNED_ALLOWS)},
		fields=["name", "user", "allow", "for_value", "applicable_for", "is_default"],
		order_by="allow asc, user asc",
		limit_page_length=0,
	)

	preserved: dict[str, int] = {}
	for row in frappe.get_all(
		"User Permission",
		filters={"allow": ("not in", KENTENDER_OWNED_ALLOWS)},
		fields=["allow"],
		limit_page_length=0,
	):
		preserved[row["allow"]] = preserved.get(row["allow"], 0) + 1

	print(f"KenTender-owned User Permission rows that WOULD be deleted: {len(candidates)}")
	for row in candidates:
		print(
			f"  - {row['name']}: {row['user']} · {row['allow']} = {row['for_value']}"
			+ (f" (applicable for {row['applicable_for']})" if row.get("applicable_for") else "")
		)
	print(f"Preserved ERPNext/HRMS User Permission rows (never touched): {preserved or 'none'}")
	print("DRY RUN — nothing was deleted. Execution belongs to the removal phase.")
	return {"would_delete": candidates, "preserved_counts": preserved}
