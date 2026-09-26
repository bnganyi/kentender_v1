# Copyright (c) 2026, KenTender and contributors
"""CFG-CHG-002 v0.14 §7.4 / KT-STD-001 v1.7 §3A.6 / AUTH-ADR-001 v1.9 §8–9 —
System setup's technical-read registration.

Registered through `kt_technical_reference_resolvers` and
`kt_technical_read_probes` in kentender_core/hooks.py, so the shared
Technical record search (never a CFG-local search) resolves CFG records to
their own System setup links, and the conformance gate exercises CFG's reads
as a technical reader.

Record families: procurement rules (Regulatory Reference sets and versions,
method eligibility profiles), their source-check evidence, procurement
schedules, working-day calendars, funding sources and the per-module
submission controls. Routes end in a `#…` part: System setup keeps record
state in the URL fragment (§9), and the search page opens the path and then
the fragment. Native Fiscal Year / Company / UOM and AUTH-owned units and
assignments stay registered by their owners (§7.4). Single doctypes (site
entity, reminder settings, Supplier portal settings), rule versions and source-check events have no
searchable reference of their own (versions are hash-named; the gate admits
only real fields), so they are reached from their rule's link and covered
by the read probes.

Probes marked `setup_maintenance_exception` return the maintenance
capabilities CFG §3.1 CFG11-EX-001 keeps for Administrator and System
Manager; the conformance gate admits that one named exception only.
"""

from __future__ import annotations

import frappe

from kentender_core.api import procurement_settings_api as settings_api
from kentender_core.api import public_portal_api as portal_api
from kentender_core.api import site_configuration_api as site_api

PAGE = "system-setup"
# CFG-CHG-002 §3.1: the technical roles maintain System setup.
EX = "CFG11-EX-001"


def _link(fragment: str) -> list[str]:
	return [PAGE, f"#{fragment}"]


def _reference_set_route(name: str) -> list[str]:
	latest = frappe.get_all(
		"Regulatory Reference", filters={"reference_set": name}, pluck="name", order_by="version_number desc", limit=1
	)
	if not latest:
		return _link("procurement-settings/procurement-rules")
	return _link(f"procurement-settings/procurement-rules/{name}/versions/{latest[0]}")


def _reference_version_route(name: str) -> list[str]:
	set_name = frappe.db.get_value("Regulatory Reference", name, "reference_set") or name
	return _link(f"procurement-settings/procurement-rules/{set_name}/versions/{name}")


def _evidence_route(name: str) -> list[str]:
	target_doctype, target_name = frappe.db.get_value("Reference Verification Event", name, ["target_doctype", "target_name"])
	if target_doctype == "Business Day Calendar":
		return _link(f"procurement-settings/calendars/{target_name}")
	return _reference_version_route(target_name)


def reference_resolvers() -> list[dict]:
	return [
		{
			"doctype": "Regulatory Reference Set",
			"label": "Procurement rule",
			"reference_field": "reference_key",
			"title_field": "display_name",
			"status_field": None,
			"route": _reference_set_route,
		},
		{
			"doctype": "Procurement Method Profile",
			"label": "Method eligibility rule",
			"reference_field": "profile_reference",
			"title_field": "procurement_method",
			"status_field": "status",
			"route": lambda name: _link(f"procurement-settings/procurement-rules/{name}"),
		},
		{
			"doctype": "Procedure Schedule Profile",
			"label": "Procurement schedule",
			"reference_field": "profile_reference",
			"title_field": "profile_name",
			"status_field": "status",
			"route": lambda name: _link(f"procurement-settings/schedule-profiles/{name}"),
		},
		{
			"doctype": "Business Day Calendar",
			"label": "Working-day calendar",
			"reference_field": "calendar_reference",
			"title_field": "calendar_name",
			"status_field": "status",
			"route": lambda name: _link(f"procurement-settings/calendars/{name}"),
		},
		{
			"doctype": "Funding Source",
			"label": "Funding source",
			"reference_field": "label",
			"title_field": "label",
			"status_field": "record_status",
			"route": lambda name: _link(f"procurement-settings/funding-sources/{name}"),
		},
		{
			"doctype": "Intake Control",
			"label": "Submission period control",
			"reference_field": "module_key",
			"title_field": "module_key",
			"status_field": None,
			"route": lambda name: _link("fiscal-years"),
		},
	]


def _first(doctype: str, field: str = "name", filters: dict | None = None) -> str | None:
	rows = frappe.get_all(doctype, filters=filters or {}, pluck=field, order_by="modified desc", limit=1)
	return rows[0] if rows else None


def _fy_kwargs() -> dict | None:
	name = _first("Fiscal Year", filters={"disabled": 0})
	return {"fiscal_year": name} if name else None


def _named(doctype: str):
	def kwargs() -> dict | None:
		name = _first(doctype)
		return {"name": name} if name else None

	return kwargs


def _reference_set_kwargs() -> dict | None:
	name = _first("Regulatory Reference Set")
	return {"reference_set": name} if name else None


def _history_kwargs() -> dict | None:
	name = _first("Regulatory Reference")
	return {"target_doctype": "Regulatory Reference", "target_name": name} if name else None


def read_probes() -> list[dict]:
	return [
		{"label": "system_setup.get_site_configuration", "call": site_api.get_site_configuration, "kwargs": lambda: {}},
		{"label": "system_setup.list_fiscal_years", "call": site_api.list_fiscal_years, "kwargs": lambda: {}},
		{"label": "system_setup.list_fiscal_year_intake_history", "call": site_api.list_fiscal_year_intake_history, "kwargs": _fy_kwargs},
		{"label": "system_setup.get_disposal_plan_submission_state", "call": site_api.get_disposal_plan_submission_state, "kwargs": lambda: {}},
		{"label": "system_setup.get_method_profile", "call": settings_api.get_method_profile, "kwargs": _named("Procurement Method Profile"), "setup_maintenance_exception": EX},
		{"label": "system_setup.get_schedule_profile", "call": settings_api.get_schedule_profile, "kwargs": _named("Procedure Schedule Profile"), "setup_maintenance_exception": EX},
		{"label": "system_setup.get_regulatory_reference_version", "call": settings_api.get_regulatory_reference_version, "kwargs": _named("Regulatory Reference"), "setup_maintenance_exception": EX},
		{"label": "system_setup.get_procurement_settings", "call": settings_api.get_procurement_settings, "kwargs": lambda: {}, "setup_maintenance_exception": EX},
		{"label": "system_setup.get_public_portal_settings", "call": portal_api.get_public_portal_settings, "kwargs": lambda: {}, "setup_maintenance_exception": EX},
		{"label": "system_setup.get_system_setup_workspace", "call": site_api.get_system_setup_workspace, "kwargs": lambda: {}, "setup_maintenance_exception": EX},
		{"label": "system_setup.list_regulatory_reference_versions", "call": settings_api.list_regulatory_reference_versions, "kwargs": _reference_set_kwargs, "setup_maintenance_exception": EX},
		{"label": "system_setup.list_verification_history", "call": settings_api.list_verification_history, "kwargs": _history_kwargs},
		{"label": "system_setup.get_business_day_calendar", "call": settings_api.get_business_day_calendar, "kwargs": _named("Business Day Calendar"), "setup_maintenance_exception": EX},
	]
