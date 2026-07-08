# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-LIB-0110 — Header action availability endpoint."""

from __future__ import annotations

import json
from collections.abc import Iterable

import frappe
from frappe import _

ACTION_IMPORT = "IMPORT_OFFICIAL_STD_PACKAGE"
ACTION_REGISTER_SOURCE = "REGISTER_SOURCE_DOCUMENT"
ACTION_VALIDATE_LIBRARY = "VALIDATE_LIBRARY"

SUPPORTED_ACTIONS: tuple[str, ...] = (
	ACTION_IMPORT,
	ACTION_REGISTER_SOURCE,
	ACTION_VALIDATE_LIBRARY,
)

_ACTION_ROLES: dict[str, tuple[str, ...]] = {
	ACTION_IMPORT: (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Importer",
	),
	ACTION_REGISTER_SOURCE: (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Importer",
	),
	ACTION_VALIDATE_LIBRARY: (
		"Administrator",
		"System Manager",
		"STD Template Administrator",
		"STD Template Reviewer",
		"STD Template Auditor",
	),
}


def _as_codes(action_codes: str | Iterable[str] | None) -> list[str]:
	if not action_codes:
		return list(SUPPORTED_ACTIONS)
	if isinstance(action_codes, str):
		text = action_codes.strip()
		if not text:
			return list(SUPPORTED_ACTIONS)
		if text.startswith("[") and text.endswith("]"):
			try:
				parsed = json.loads(text)
			except (TypeError, ValueError):
				parsed = None
			if isinstance(parsed, list):
				return [str(x).strip() for x in parsed if str(x).strip()]
		parts = [x.strip() for x in text.split(",")]
		return [x for x in parts if x]
	return [str(x).strip() for x in action_codes if str(x).strip()]


def _allow(action_code: str, roles: set[str]) -> tuple[bool, str | None, str]:
	needed = set(_ACTION_ROLES.get(action_code, ()))
	if not needed:
		return False, "STD_ACTION_UNSUPPORTED", _("Unavailable: unsupported action.")
	if roles & needed:
		return True, None, _("Allowed")
	return (
		False,
		"STD_AUTH_PERMISSION_DENIED",
		_("Unavailable: you do not have permission to perform this action."),
	)


@frappe.whitelist()
def get_std_library_action_availability(
	action_codes: str | list[str] | tuple[str, ...] | None = None,
	object_type: str | None = None,
	object_code: str | None = None,
) -> dict:
	"""Return action availability payload for STD library header controls."""
	if frappe.session.user in (None, "Guest"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	req_codes = _as_codes(action_codes)
	user_roles = set(frappe.get_roles(frappe.session.user) or [])
	actions: list[dict] = []

	for code in req_codes:
		allowed, denial_code, message = _allow(code, user_roles)
		if code not in SUPPORTED_ACTIONS:
			allowed = False
			denial_code = "STD_ACTION_UNSUPPORTED"
			message = _("Unavailable: unsupported action.")
		actions.append(
			{
				"action_code": code,
				"allowed": bool(allowed),
				"denial_code": denial_code,
				"message": message,
				"requires_confirmation": False,
				"risk_level": "High",
			}
		)

	return {
		"ok": True,
		"actions": actions,
		"context": {
			"object_type": object_type,
			"object_code": object_code,
		},
	}
