# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Engine core read APIs."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.std_engine.services import (
	governance_read_service,
	read_service,
	schema_read_service,
)

READ_ROLES = ("System Manager", "Administrator", "Auditor")


@frappe.whitelist(methods=["GET"])
def get_std_families() -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return read_service.get_std_families()


@frappe.whitelist(methods=["GET"])
def get_std_family(family_code: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return read_service.get_std_family(family_code)


@frappe.whitelist(methods=["GET"])
def get_std_version(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return read_service.get_std_version(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_source_traceability(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return read_service.get_std_version_source_traceability(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_sections(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return read_service.get_std_version_sections(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_clause(clause_key: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return read_service.get_std_clause(clause_key)


@frappe.whitelist(methods=["GET"])
def get_std_version_parameters(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_parameters(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_parameter(parameter_key: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_parameter(parameter_key)


@frappe.whitelist(methods=["GET"])
def get_std_version_rules(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_rules(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_rule(rule_key: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_rule(rule_key)


@frappe.whitelist(methods=["GET"])
def get_std_version_forms(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_forms(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_form(form_key: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_form(form_key)


@frappe.whitelist(methods=["GET"])
def get_std_version_requirements(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_requirements(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_price_schedules(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_price_schedules(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_evaluation_schema(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_evaluation_schema(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_render_blocks(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return schema_read_service.get_std_version_render_blocks(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_validation_report(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return governance_read_service.get_std_version_validation_report(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_audit_log(
	package_id: str,
	limit: int = 100,
	offset: int = 0,
) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return governance_read_service.get_std_version_audit_log(
		package_id,
		limit=limit,
		offset=offset,
	)


@frappe.whitelist(methods=["GET"])
def get_std_version_usage_bindings(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return governance_read_service.get_std_version_usage_bindings(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_version_import_runs(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return governance_read_service.get_std_version_import_runs(package_id)


@frappe.whitelist(methods=["GET"])
def get_std_import_run(import_run_key: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return governance_read_service.get_std_import_run(import_run_key)


@frappe.whitelist(methods=["GET"])
def get_std_version_diff(package_id: str) -> dict[str, Any]:
	frappe.only_for(READ_ROLES)
	return governance_read_service.get_std_version_diff(package_id)
