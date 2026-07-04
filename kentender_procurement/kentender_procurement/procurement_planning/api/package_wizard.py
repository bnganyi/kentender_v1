# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PW2 — Planning Package Creation Wizard, Step 1 read APIs.

Whitelisted wrappers around `package_wizard_service` (eligible-demands list
+ multi-select compatibility check). Reuses the same create-package
permission gate as the legacy modal (`planning_inclusion.py`) since the
wizard fully replaces it — same actor may reach Step 1.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.api.planning_inclusion import _create_package_gate


def _parse_codes(raw: str | list | None) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, list):
		return [str(x).strip() for x in raw if str(x).strip()]
	text = str(raw).strip()
	if not text:
		return []
	try:
		import json

		parsed = json.loads(text)
		if isinstance(parsed, list):
			return [str(x).strip() for x in parsed if str(x).strip()]
	except (json.JSONDecodeError, TypeError):
		pass
	return [text]


@frappe.whitelist()
def list_pp_wizard_eligible_demands(
	plan_code: str | None = None,
	search: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted read — Step 1 "Select Demands" list."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.package_wizard_service import (
		list_wizard_eligible_demands,
	)

	plan_code = (plan_code or "").strip()
	if not plan_code:
		return {"ok": False, "error_code": "MISSING_PARAMS", "message": "Plan code is required.", "role_key": role_key}

	rows = list_wizard_eligible_demands(plan_code, search=search)
	return {"ok": True, "role_key": role_key, "demands": rows, "count": len(rows)}


@frappe.whitelist()
def check_pp_package_compatibility(inclusion_codes: str | list | None = None) -> dict[str, Any]:
	"""Whitelisted read — Step 1 multi-select compatibility check (§8.4)."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.package_wizard_service import (
		check_package_compatibility,
	)

	codes = _parse_codes(inclusion_codes)
	out = check_package_compatibility(codes)
	return {"ok": True, "role_key": role_key, **out}


def _parse_config(raw: str | dict | None) -> dict[str, Any]:
	if raw is None:
		return {}
	if isinstance(raw, dict):
		return raw
	text = str(raw).strip()
	if not text:
		return {}
	try:
		import json

		parsed = json.loads(text)
		return parsed if isinstance(parsed, dict) else {}
	except (json.JSONDecodeError, TypeError):
		return {}


@frappe.whitelist()
def get_pp_package_wizard_configuration_preview(
	inclusion_codes: str | list | None = None,
	config: str | dict | None = None,
) -> dict[str, Any]:
	"""Whitelisted read — Step 2 "Configure Package" preview (§9). Pure
	computation, never persists (Save Draft deferred)."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.package_wizard_service import (
		preview_package_configuration,
	)

	codes = _parse_codes(inclusion_codes)
	out = preview_package_configuration(codes, _parse_config(config))
	if not out.get("ok"):
		out["role_key"] = role_key
		return out
	return {"ok": True, "role_key": role_key, **out}


@frappe.whitelist()
def get_pp_package_wizard_document_path_preview(
	inclusion_codes: str | list | None = None,
	config: str | dict | None = None,
) -> dict[str, Any]:
	"""Whitelisted read — Step 2 "Document / STD Path" section preview (§9.7)."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.package_wizard_service import (
		preview_document_std_path,
	)

	codes = _parse_codes(inclusion_codes)
	out = preview_document_std_path(codes, _parse_config(config))
	if not out.get("ok"):
		out["role_key"] = role_key
		return out
	return {"ok": True, "role_key": role_key, **out}


@frappe.whitelist()
def get_pp_package_wizard_readiness(
	inclusion_codes: str | list | None = None,
	config: str | dict | None = None,
) -> dict[str, Any]:
	"""Whitelisted read — Step 3 "Review and Create" readiness preview +
	blocking conditions (§10.3/§10.5)."""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.package_wizard_service import (
		evaluate_wizard_readiness,
	)

	codes = _parse_codes(inclusion_codes)
	out = evaluate_wizard_readiness(codes, _parse_config(config))
	return {"ok": True, "role_key": role_key, **out}


@frappe.whitelist()
def create_pp_package_from_wizard(
	inclusion_codes: str | list | None = None,
	config: str | dict | None = None,
) -> dict[str, Any]:
	"""Whitelisted write — final "Create Package" commit (§10.4/§12).

	Re-validates readiness server-side (never trusts client staged state)
	before delegating to the canonical multi-line creation primitive.
	"""
	role_key, gate_err = _create_package_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	from kentender_procurement.procurement_planning.services.package_wizard_service import (
		create_package_from_wizard,
	)

	codes = _parse_codes(inclusion_codes)
	try:
		out = create_package_from_wizard(codes, _parse_config(config), frappe.session.user)
	except frappe.ValidationError as exc:
		return {
			"ok": False,
			"role_key": role_key,
			"error_code": getattr(exc, "title", None) or "VALIDATION_ERROR",
			"message": str(exc),
		}
	except frappe.PermissionError as exc:
		return {
			"ok": False,
			"role_key": role_key,
			"error_code": "PP_ACCESS_DENIED",
			"message": str(exc) or "You do not have permission to create a package.",
		}
	if not out.get("ok"):
		out["role_key"] = role_key
		return out
	return {"ok": True, "role_key": role_key, **out}
