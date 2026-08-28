"""AUTH-ADR-001 — the native Frappe Role + User Permission decision engine.

Replaces `authorization_policy`'s Operational Scope Assignment/Capability
Profile-based capability resolution. Deliberately narrow: this module answers
only "does this user hold the required Role, with the required scope, for
this capability?" (AUTH-ADR-001 §4's "Business scope" and "Functional role"
layers). Record/task state, delegation and segregation-of-duties stay
domain-owned checks layered on top by each caller (§8, §9, §10) — this keeps
the same separation of concerns `authorization_policy.evaluate_capability`
already had, without recreating a second generic grant store.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_core.services.authorization_policy import ResourceContext
from kentender_core.services.authorization_role_registry import CAPABILITY_ROLE_MAP, ROLE_CLASSIFICATIONS

AUTH_ROLE_REQUIRED = "AUTH_ROLE_REQUIRED"
AUTH_SCOPE_REQUIRED = "AUTH_SCOPE_REQUIRED"
AUTH_SEGREGATION_BLOCKED = "AUTH_SEGREGATION_BLOCKED"

_ERROR_MESSAGES = {
	AUTH_ROLE_REQUIRED: _("You do not have the required role for this action."),
	AUTH_SCOPE_REQUIRED: _(
		"This record is not available in your assigned Procuring Entity, Financial Year or department scope."
	),
	AUTH_SEGREGATION_BLOCKED: _("You cannot perform this action because you completed an incompatible earlier action."),
}


def _user_permission_values(user: str, doctype: str) -> set[str]:
	return set(frappe.get_all("User Permission", filters={"user": user, "allow": doctype}, pluck="for_value"))


def _scope_ok(user: str, classification: str, resource: ResourceContext) -> bool:
	if classification == "global_central":
		return True
	if classification == "pe_fy_scoped":
		if resource.pe_fy_context_id:
			return resource.pe_fy_context_id in _user_permission_values(user, "PE Fiscal Year Context")
		classification = "pe_scoped"  # resource carries no PE/FY Context — fall back per ADR §6.1
	if classification == "pe_ou_scoped":
		if resource.procuring_entity_id not in _user_permission_values(user, "Procuring Entity"):
			return False
		if resource.organisation_unit_id:
			ou_scope = _user_permission_values(user, "Organisation Unit")
			if ou_scope:
				return resource.organisation_unit_id in ou_scope
		return True
	if classification == "pe_scoped":
		return resource.procuring_entity_id in _user_permission_values(user, "Procuring Entity")
	return False


def evaluate_role_capability(user: str, capability: str, resource: ResourceContext) -> tuple[bool, str]:
	"""Deny-by-default Role+scope check. Read-only, no side effects, no audit write.

	Administrator is explicitly excluded: `frappe.get_roles("Administrator")`
	returns every Role in the system regardless of actual assignment (a real
	Frappe framework special-case), which would otherwise let Administrator
	silently pass any Role check — directly contradicting AUTH-ADR-001 §5.3
	("System Manager or Administrator technical access does not confer a
	business approval role") and AUTH-AC-012.
	"""
	if not user or user == "Guest" or user == "Administrator":
		return False, AUTH_ROLE_REQUIRED
	role = CAPABILITY_ROLE_MAP.get(capability)
	if not role or role not in frappe.get_roles(user):
		return False, AUTH_ROLE_REQUIRED
	classification = ROLE_CLASSIFICATIONS.get(role, "pe_scoped")
	if not _scope_ok(user, classification, resource):
		return False, AUTH_SCOPE_REQUIRED
	return True, "ALLOW"


def require_role_capability(
	user: str,
	capability: str,
	resource: ResourceContext,
	*,
	sod_blocked: bool = False,
) -> None:
	"""Raises frappe.PermissionError with an AUTH_* reason title on denial.

	`sod_blocked` is computed by the caller against its own domain's
	Separation of Duties Rule table (segregation stays a domain rule, not a
	permission-engine concern — AUTH-ADR-001 §10).
	"""
	allowed, reason = evaluate_role_capability(user, capability, resource)
	if allowed and sod_blocked:
		allowed, reason = False, AUTH_SEGREGATION_BLOCKED
	if not allowed:
		frappe.throw(_ERROR_MESSAGES.get(reason, _("Not permitted for this action.")), frappe.PermissionError, title=reason)
