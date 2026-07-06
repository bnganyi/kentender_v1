# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CFG-0230 — whitelisted Desk APIs for the STD Version Configurator."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tender_management.services import std_configurator_service as svc


def _parse_section_data(data: Any) -> Any:
	if data is None:
		return None
	if isinstance(data, (dict, list)):
		return data
	text = str(data).strip()
	if not text:
		return {}
	return frappe.parse_json(text)


@frappe.whitelist()
def get_std_configurator_context(template_code: str) -> dict[str, Any]:
	return svc.get_configurator_context(template_code)


@frappe.whitelist()
def get_std_configurator_section(template_code: str, section: str) -> dict[str, Any]:
	return svc.get_section(template_code, section)


@frappe.whitelist()
def save_std_configurator_section(template_code: str, section: str, data: Any = None) -> dict[str, Any]:
	return svc.save_section(template_code, section, _parse_section_data(data))


@frappe.whitelist()
def get_std_configurator_technical_json(template_code: str) -> dict[str, Any]:
	return svc.get_technical_json(template_code)


@frappe.whitelist()
def get_std_configurator_preview(template_code: str, mode: str | None = None) -> dict[str, Any]:
	return svc.get_preview(template_code, mode)


@frappe.whitelist()
def run_std_configurator_applicability_test(
	template_code: str, test_case: Any = None
) -> dict[str, Any]:
	return svc.run_applicability_test(template_code, _parse_section_data(test_case))


@frappe.whitelist()
def run_std_configurator_validation(template_code: str) -> dict[str, Any]:
	return svc.run_cross_section_validation(template_code)


@frappe.whitelist()
def submit_std_configurator_for_review(template_code: str, comment: str | None = None) -> dict[str, Any]:
	return svc.submit_configurator_for_review(template_code, comment)


@frappe.whitelist()
def activate_std_configurator_version(
	template_code: str,
	reason: str,
	active_from: str | None = None,
	active_until: str | None = None,
	is_default_active_version: int | str | bool = True,
) -> dict[str, Any]:
	return svc.activate_configurator_version(
		template_code,
		reason,
		active_from=active_from,
		active_until=active_until,
		is_default_active_version=bool(int(is_default_active_version))
		if isinstance(is_default_active_version, str) and is_default_active_version.isdigit()
		else bool(is_default_active_version),
	)
