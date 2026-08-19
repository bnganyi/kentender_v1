"""Whitelisted AUTH-G04 Desk API facade."""

import frappe

from kentender_core.services.authorization_administration import create_draft_assignment, create_revised_routing_rule, get_routing_rule_detail, get_user_operational_access
from kentender_core.services.authorization_diagnostics import diagnose_access
from kentender_core.services.authorization_policy import ResourceContext


@frappe.whitelist()
def user_access(target_user: str):
	return get_user_operational_access(target_user)


@frappe.whitelist()
def routing_rule(name: str):
	return get_routing_rule_detail(name)


@frappe.whitelist()
def revise_routing_rule(name: str):
	return create_revised_routing_rule(name)


@frappe.whitelist()
def add_assignment(values):
	return create_draft_assignment(frappe.parse_json(values))


@frappe.whitelist()
def diagnostic(tested_user: str, capability: str, resource_type: str, resource_id: str, procuring_entity_id: str, financial_year_id: str = "", organisation_unit_id: str = "", task_id: str = ""):
	return diagnose_access(tested_user=tested_user, capability=capability, resource=ResourceContext(resource_type, resource_id, procuring_entity_id, financial_year_id, organisation_unit_id), task_id=task_id)
