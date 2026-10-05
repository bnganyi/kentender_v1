"""HOME-CHG-001 v0.6 §7 — the one Home endpoint. Thin: the work is in
`kentender_core.services.home_workspace`."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import home_workspace


@frappe.whitelist()
def get_home_workspace(regions: Any = None, cursors: Any = None) -> dict[str, Any]:
	"""Home for the signed-in user. `regions` limits the read (a retry);
	`cursors` maps a region to the cursor of the rows already shown (Show more).
	Both arrive as JSON strings from the browser."""
	return home_workspace.get_workspace(
		frappe.session.user,
		regions=frappe.parse_json(regions) if regions else None,
		cursors=frappe.parse_json(cursors) if cursors else None,
	)
