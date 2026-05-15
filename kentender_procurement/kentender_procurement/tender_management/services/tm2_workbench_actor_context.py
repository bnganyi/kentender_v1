# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Desk TM2 workbench — merge §7.3 authorization hints for whitelisted session users.

Until SEC wires ``Security Role`` assignments to Frappe users for every actor,
``Administrator`` and ``System Manager`` receive the minimum ``PERM_*`` grants
needed for P9-03 / P9-07 workbench flows (same pattern as Playwright smoke tests).
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)

# P9-07 wizard + P9-08 workbench detail / action bar — desk-only grants until SEC role wiring.
_WORKBENCH_DESK_GRANT_ACTION_CODES: tuple[str, ...] = (
	"TND2_CREATE_FROM_PACKAGE",
	"TND2_BIND_STD",
	"TND2_VIEW",
	"TND2_EDIT_DRAFT",
	"TND2_RUN_READINESS",
	"TND2_SUBMIT_PUBLICATION_REVIEW",
	"TND2_RETURN_CORRECTION",
	"TND2_APPROVE_PUBLICATION",
	"TND2_PUBLISH",
	"TND2_CANCEL",
	"TND2_MARK_RETENDER_REQUIRED",
	"TND2_SUPERSEDE",
	"AUD2_EXPORT_EVIDENCE",
)


def tm2_workbench_desk_security_context(actor: str) -> dict[str, Any]:
	"""Return a context fragment with ``granted_permissions`` for privileged desk users."""
	act = (actor or "").strip()
	if not act or not frappe.db.exists("User", act):
		return {}
	try:
		roles = set(frappe.get_roles(act))
	except Exception:
		roles = set()
	if act != "Administrator" and "System Manager" not in roles:
		return {}
	ids: list[str] = []
	for code in _WORKBENCH_DESK_GRANT_ACTION_CODES:
		spec = spec_for_action(code)
		if spec and spec.required_permission:
			ids.append(spec.required_permission)
	return {"granted_permissions": list(dict.fromkeys(ids))}
