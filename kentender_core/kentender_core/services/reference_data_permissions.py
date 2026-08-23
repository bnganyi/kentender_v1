# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 permission wiring — built on kentender_core.services.authorization_policy
(the existing deny-by-default capability/profile engine), not a lightweight can_*()
clone. See docs/mvp-1-r1/05_pe_and_fy_maintenance/IMPLEMENTATION_TRACKER.md decision log.
"""

from __future__ import annotations

import frappe

from kentender_core.services.authorization_policy import ResourceContext, require_capability

# Procuring Entity capabilities (CFG-CHG-002 §6.1, §7)
PE_CREATE_DRAFT = "reference_data.pe.create_draft"
PE_PROPOSE_AMENDMENT = "reference_data.pe.propose_amendment"
PE_APPROVE_ACTIVATE = "reference_data.pe.approve_activate"
PE_SUSPEND = "reference_data.pe.suspend"
PE_REINSTATE = "reference_data.pe.reinstate"
PE_RETIRE = "reference_data.pe.retire"

# Financial Year capabilities (CFG-CHG-002 §6.2, §7)
FY_CREATE_DRAFT = "reference_data.fy.create_draft"
FY_APPROVE_AVAILABLE = "reference_data.fy.approve_available"
FY_RETIRE = "reference_data.fy.retire"

# PE/FY Context capabilities (CFG-CHG-002 §6.3, §7)
CTX_CREATE_DRAFT = "reference_data.context.create_draft"  # PE Configuration Steward: draft + submit
CTX_RECOMMEND = "reference_data.context.recommend"  # Professional Reviewer / HoPF
CTX_APPROVE = "reference_data.context.approve"  # Accounting Officer: approve/suspend/reinstate/close/reopen


def pe_resource_context(pe_name: str, *, prior_actions: list[dict[str, str]] | None = None) -> ResourceContext:
	return ResourceContext(
		resource_type="Procuring Entity",
		resource_id=pe_name,
		procuring_entity_id=pe_name,
		prior_actions=prior_actions or [],
	)


def require_pe_capability(
	user: str,
	capability: str,
	pe_name: str,
	*,
	prior_actions: list[dict[str, str]] | None = None,
	correlation_id: str = "",
):
	"""Raises frappe.PermissionError (via authorization_policy) if denied."""
	return require_capability(
		user,
		capability,
		pe_resource_context(pe_name, prior_actions=prior_actions),
		correlation_id=correlation_id,
	)


def _has_any_active_capability(user: str, capability: str) -> bool:
	import json

	rows = frappe.get_all(
		"Operational Scope Assignment",
		filters={"user_id": user, "status": "Active"},
		fields=["capability_profile_id"],
	)
	profile_ids = {row.capability_profile_id for row in rows}
	for profile_id in profile_ids:
		capabilities = json.loads(
			frappe.db.get_value("Capability Profile", profile_id, "capabilities") or "[]"
		)
		if capability in capabilities:
			return True
	return False


def require_pe_create_capability(user: str) -> None:
	"""Special-cased: Operational Scope Assignment.procuring_entity_id is a required
	Link to an existing Procuring Entity, so the normal per-PE evaluate_capability()
	path cannot express "may create a PE that doesn't exist yet" — there is no PE to
	scope the check against. Central Reference Data Stewards are not conceptually
	PE-scoped for creation anyway (they create entities precisely because those
	entities don't exist), so this checks for the capability on ANY active
	assignment for the user, not a specific resource. Every other PE action (submit,
	approve, suspend, retire, amend) targets an existing PE and uses the normal
	resource-scoped require_pe_capability() instead."""
	if _has_any_active_capability(user, PE_CREATE_DRAFT):
		return
	frappe.throw(
		"Not permitted to create a Procuring Entity", frappe.PermissionError, title="CAPABILITY_NOT_ASSIGNED"
	)


def prior_actions_for(document_type: str, document_name: str) -> list[dict[str, str]]:
	"""Prior committed actions on this document, for SoD evaluation."""
	rows = frappe.get_all(
		"Audit Event",
		filters={"document_type": document_type, "document_name": document_name},
		fields=["action", "performed_by"],
		order_by="creation asc",
	)
	return [{"user": row.performed_by, "capability": row.action} for row in rows if row.action]


def _sod_blocked(user: str, capability: str, prior_actions: list[dict[str, str]]) -> bool:
	prior = {row["capability"] for row in prior_actions if row.get("user") == user}
	if not prior:
		return False
	rules = frappe.get_all(
		"Separation of Duties Rule",
		filters={"status": "Active"},
		fields=["first_capability", "second_capability"],
	)
	for rule in rules:
		if capability == rule.first_capability and rule.second_capability in prior:
			return True
		if capability == rule.second_capability and rule.first_capability in prior:
			return True
	return False


def require_fy_capability(user: str, capability: str, *, fy_name: str | None = None) -> None:
	"""Financial Year is a shared calendar reference, not owned by any single PE —
	Operational Scope Assignment always requires a procuring_entity_id, so there is
	no natural resource to scope a FY action against at all (unlike PE actions,
	where only *creation* has this problem), and authorization_policy's own SoD
	check is reached only via its per-resource evaluate_capability() path. So FY
	uses the any-active-assignment capability check plus an explicit, separate
	SoD check against the same Separation of Duties Rule table, fed by this
	document's own audit trail — same rule data, different plumbing to reach it."""
	if not _has_any_active_capability(user, capability):
		frappe.throw(
			"Not permitted to perform this Financial Year action",
			frappe.PermissionError,
			title="CAPABILITY_NOT_ASSIGNED",
		)
	if fy_name and _sod_blocked(user, capability, prior_actions_for("Financial Year", fy_name)):
		frappe.throw(
			"You cannot perform this decision because you completed an incompatible earlier action.",
			frappe.PermissionError,
			title="SEPARATION_OF_DUTIES_BLOCKED",
		)


def prior_actions_for_pe(pe_name: str) -> list[dict[str, str]]:
	"""Prior committed actions on this PE, for SoD evaluation (creator != approver)."""
	return prior_actions_for("Procuring Entity", pe_name)


def context_resource_context(
	context_name: str,
	pe_name: str,
	fy_name: str,
	*,
	prior_actions: list[dict[str, str]] | None = None,
) -> ResourceContext:
	# financial_year_id is carried for documentation/downstream use, but note:
	# authorization_policy._scope_matches() does not currently filter on it —
	# scope matching is PE-granularity only, matching this spec's own role table
	# ("own PE contexts", not "own PE+FY contexts").
	return ResourceContext(
		resource_type="PE Fiscal Year Context",
		resource_id=context_name,
		procuring_entity_id=pe_name,
		financial_year_id=fy_name,
		prior_actions=prior_actions or [],
	)


def prior_actions_for_context(context_name: str) -> list[dict[str, str]]:
	return prior_actions_for("PE Fiscal Year Context", context_name)


def require_context_capability(
	user: str,
	capability: str,
	context_name: str,
	pe_name: str,
	fy_name: str,
	*,
	prior_actions: list[dict[str, str]] | None = None,
):
	return require_capability(
		user,
		capability,
		context_resource_context(context_name, pe_name, fy_name, prior_actions=prior_actions),
	)
