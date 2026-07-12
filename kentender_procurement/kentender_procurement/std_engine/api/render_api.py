# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Engine render preview APIs."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.std_engine.services import render_service
from kentender_procurement.std_engine.services.envelope import build_package_context

RENDER_ROLES = ("System Manager", "Administrator", "Legal Reviewer", "Procurement Reviewer")


@frappe.whitelist(methods=["POST"])
def render_section_preview(
	package_id: str,
	section_key: str,
	parameter_values: str | dict | None = None,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	frappe.only_for(RENDER_ROLES)
	params = _parse_parameter_values(parameter_values)
	result = render_service.render_section_preview(
		package_id,
		section_key,
		parameter_values=params,
		simulate_active_for_test=bool(int(simulate_active_for_test) if str(simulate_active_for_test).isdigit() else simulate_active_for_test),
	)
	return {"ok": True, "packageContext": build_package_context(package_id), "data": result}


@frappe.whitelist(methods=["POST"])
def render_block_preview(
	package_id: str,
	block_key: str,
	parameter_values: str | dict | None = None,
	simulate_active_for_test: bool = False,
) -> dict[str, Any]:
	frappe.only_for(RENDER_ROLES)
	params = _parse_parameter_values(parameter_values)
	result = render_service.render_block_preview(
		package_id,
		block_key,
		parameter_values=params,
		simulate_active_for_test=bool(int(simulate_active_for_test) if str(simulate_active_for_test).isdigit() else simulate_active_for_test),
	)
	return {"ok": True, "packageContext": build_package_context(package_id), "data": result}


@frappe.whitelist(methods=["GET"])
def get_render_probe_status(package_id: str) -> dict[str, Any]:
	frappe.only_for(RENDER_ROLES)
	return {
		"ok": True,
		"packageContext": build_package_context(package_id),
		"data": render_service.get_render_probe_status(package_id),
	}


def _parse_parameter_values(raw: str | dict | None) -> dict[str, str]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return {str(k): str(v) for k, v in raw.items()}
	try:
		parsed = json.loads(raw)
	except (TypeError, json.JSONDecodeError):
		return {}
	if not isinstance(parsed, dict):
		return {}
	return {str(k): str(v) for k, v in parsed.items()}
