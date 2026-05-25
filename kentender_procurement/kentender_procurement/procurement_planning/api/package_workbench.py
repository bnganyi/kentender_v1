# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P4-005 — Package workbench list API."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from kentender_procurement.procurement_planning.permissions import pp_api_gates
from kentender_procurement.procurement_planning.services.package_workbench import (
	get_package_workbench_rows,
)


def _fail(*, code: str, message: str, role_key: str = "auditor") -> dict[str, Any]:
	return {
		"ok": False,
		"error_code": code,
		"message": str(message),
		"role_key": role_key,
		"total": 0,
		"rows": [],
		"filters_applied": {},
	}


def _planning_read_gate() -> tuple[str | None, dict[str, Any] | None]:
	return pp_api_gates.planning_api_read_gate(
		pp_api_gates.PLANNING_PACKAGE_READ,
		message=_("You do not have access to the Procurement Planning package workbench."),
		fail=_fail,
	)


def _parse_filters(
	search_text: str | None = None,
	status: str | None = None,
	category: str | None = None,
	method: str | None = None,
	fiscal_year: str | None = None,
	procuring_entity: str | None = None,
	readiness_status: str | None = None,
	handoff_status: str | None = None,
	plan: str | None = None,
	start: int | str | None = 0,
	limit: int | str | None = 50,
	filters: str | None = None,
) -> dict[str, Any]:
	out: dict[str, Any] = {
		"search_text": (search_text or "").strip(),
		"status": (status or "").strip(),
		"category": (category or "").strip(),
		"method": (method or "").strip(),
		"fiscal_year": (fiscal_year or "").strip(),
		"procuring_entity": (procuring_entity or "").strip(),
		"readiness_status": (readiness_status or "").strip(),
		"handoff_status": (handoff_status or "").strip(),
		"plan": (plan or "").strip(),
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
def get_pp_package_workbench(
	search_text: str | None = None,
	status: str | None = None,
	category: str | None = None,
	method: str | None = None,
	fiscal_year: str | None = None,
	procuring_entity: str | None = None,
	readiness_status: str | None = None,
	handoff_status: str | None = None,
	plan: str | None = None,
	start: int | str | None = 0,
	limit: int | str | None = 50,
	filters: str | None = None,
) -> dict[str, Any]:
	"""Whitelisted PP2 package workbench — list rows with state, readiness, and next action."""
	role_key, gate_err = _planning_read_gate()
	if gate_err:
		return gate_err
	assert role_key is not None

	parsed_filters = _parse_filters(
		search_text=search_text,
		status=status,
		category=category,
		method=method,
		fiscal_year=fiscal_year,
		procuring_entity=procuring_entity,
		readiness_status=readiness_status,
		handoff_status=handoff_status,
		plan=plan,
		start=start,
		limit=limit,
		filters=filters,
	)
	return get_package_workbench_rows(parsed_filters, frappe.session.user)
