# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-012 — Released to Tender list and Planning Release Package detail API."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.released_to_tender_api import (
	get_planning_release_package_context,
	get_released_to_tender_rows,
)
from kentender_procurement.procurement_planning.services.released_to_tender_summary_view_model import (
	get_released_package_summary,
)


def _list_fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"total": 0,
		"rows": [],
		"filters_applied": {},
	}


def _detail_fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
	}


def _planning_read_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.RELEASED_TO_TENDER_READ,
		message=_("You do not have access to the Procurement Planning Released to Tender surface."),
		fail=_list_fail,
	)


def _detail_read_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.RELEASED_TO_TENDER_READ,
		message=_("You do not have access to the Planning Release Package detail."),
		fail=_detail_fail,
	)


def _parse_filters(
	search_text: str | None = None,
	handoff_status: str | None = None,
	consumption_status: str | None = None,
	package_status: str | None = None,
	fiscal_year: str | None = None,
	procuring_entity: str | None = None,
	start: int | str | None = 0,
	limit: int | str | None = 50,
	filters: str | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"search_text": (search_text or "").strip(),
		"handoff_status": (handoff_status or "").strip(),
		"consumption_status": (consumption_status or "").strip(),
		"package_status": (package_status or "").strip(),
		"fiscal_year": (fiscal_year or "").strip(),
		"procuring_entity": (procuring_entity or "").strip(),
		"start": max(cint(start or 0), 0),
		"limit": cint(limit or 50),
	}
	if filters:
		try:
			parsed = json.loads(filters) if isinstance(filters, str) else filters
		except (TypeError, ValueError, json.JSONDecodeError):
			parsed = {}
		if isinstance(parsed, dict):
			for key, value in parsed.items():
				if key in out and value not in (None, ""):
					out[key] = value
	return out


@frappe.whitelist()
def get_pp_released_to_tender(
	search_text: str | None = None,
	handoff_status: str | None = None,
	consumption_status: str | None = None,
	package_status: str | None = None,
	fiscal_year: str | None = None,
	procuring_entity: str | None = None,
	start: int | str | None = 0,
	limit: int | str | None = 50,
	filters: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted PP2 Released to Tender — release handoff cards with consumption status."""
	role_key, gate_err = _planning_read_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	parsed_filters = _parse_filters(
		search_text=search_text,
		handoff_status=handoff_status,
		consumption_status=consumption_status,
		package_status=package_status,
		fiscal_year=fiscal_year,
		procuring_entity=procuring_entity,
		start=start,
		limit=limit,
		filters=filters,
	)
	return get_released_to_tender_rows(parsed_filters, frappe.session.user)


@frappe.whitelist()
def get_pp_planning_release_package(release_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP2 Planning Release Package detail (Screen 19)."""
	role_key, gate_err = _detail_read_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	code = (release_code or "").strip()
	if not code:
		return _detail_fail(
			code="NOT_FOUND",
			message=_("Release not found."),
			role_key=role_key,
		)

	return get_planning_release_package_context(code, frappe.session.user)


@frappe.whitelist()
def get_pp_released_package_summary(package_code: str | None = None) -> dict[str, Any]:
	"""Whitelisted PP3 Released package follow-up summary (P7-003+)."""
	role_key, gate_err = _detail_read_gate()
	if gate_err:
		return gate_err
	assert role_key is not None
	return get_released_package_summary((package_code or "").strip(), frappe.session.user)
