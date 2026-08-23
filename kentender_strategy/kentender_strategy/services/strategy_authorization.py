# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 §7 capability wiring, on kentender_core's authorization_policy
engine — same engine CFG-CHG-002 adopted (docs/mvp-1-r1/02_strategy/
IMPLEMENTATION_TRACKER.md decision log, 2026-08-23), not Strategy's older
org_scope_access.py mechanism.

Phase 2 defines the capability constants and the resource-context/SoD wiring
the lifecycle engine enforces against. Phase 3 seeds the production Capability
Profiles, Operational Scope Assignments and Separation of Duties Rules that
grant these capabilities to real Strategy Author/Reviewer/Approval Authority
actors — until then, every check here fails closed (no profile exists to
grant it), which is the correct, safe default, not a gap.
"""

from __future__ import annotations

import frappe

from kentender_core.services.authorization_policy import (
	ResourceContext,
	evaluate_capability,
	require_capability,
)
from kentender_strategy.services.strategy_audit import list_events

CAP_AUTHOR = "strategy.plan_version.author"
CAP_REVIEW = "strategy.plan_version.review"
CAP_APPROVE = "strategy.plan_version.approve"


def resource_context_for_version(version) -> ResourceContext:
	"""Build a ResourceContext for one Strategic Plan Version, resolving its
	owning Strategic Plan for PE/OU scope."""
	if isinstance(version, str):
		version = frappe.get_doc("Strategic Plan Version", version)
	plan = frappe.db.get_value(
		"Strategic Plan", version.plan_id, ["procuring_entity_id", "owner_org_unit_id"], as_dict=True
	)
	return ResourceContext(
		resource_type="Strategic Plan Version",
		resource_id=version.name,
		procuring_entity_id=(plan.procuring_entity_id if plan else "") or "",
		organisation_unit_id=(plan.owner_org_unit_id if plan else "") or "",
		state=version.status or "",
		prior_actions=prior_actions_for_version(version.name),
	)


def prior_actions_for_version(version_name: str) -> list[dict]:
	"""SoD history for one version, reconstructed from its own audit trail —
	the same pattern reference_data_permissions.prior_actions_for_pe/context
	uses. Only events that recorded which capability was exercised count."""
	out = []
	for event in list_events("Strategic Plan Version", version_name):
		capability = (event.get("metadata") or {}).get("capability")
		if capability:
			out.append({"user": event.get("performed_by"), "capability": capability})
	return out


def require_plan_version_capability(
	user: str, capability: str, version, *, correlation_id: str = ""
):
	return require_capability(
		user, capability, resource_context_for_version(version), correlation_id=correlation_id
	)


def has_plan_version_capability(user: str, capability: str, version) -> bool:
	return evaluate_capability(user, capability, resource_context_for_version(version)).allowed
