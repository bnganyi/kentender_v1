# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 §7/§18.1 capability wiring, on AUTH-ADR-001's native
Frappe Role + User Permission engine (kentender_core.services.authorization_native)
— not kentender_core's older Operational Scope Assignment/Capability Profile
engine, and not Strategy's older org_scope_access.py mechanism either.

v1.5 collapses the 3-role/3-capability model (Author/Reviewer/Approval
Authority) onto 2 roles/capabilities (Author/Approver). Separation of duties
is no longer a pairwise Separation of Duties Rule table (there is only one
remaining pair, Author vs Approver, and the rule is version-specific, not a
general two-hat block): "the author of a submitted version cannot approve or
return it, even if that user also holds Strategy Approver" (§13.4/§18.1).
That is enforced directly here via the version's own audit trail, not via
kentender_core's general capability-pair SoD machinery.
"""

from __future__ import annotations

import frappe

from kentender_core.services.authorization_native import evaluate_role_capability, require_role_capability
from kentender_core.services.authorization_policy import ResourceContext
from kentender_strategy.services.strategy_audit import list_events

CAP_AUTHOR = "strategy.plan_version.author"
CAP_APPROVE = "strategy.plan_version.approve"

# STR-CHG-001 v1.5 §7/§18.1: only 2 Strategy workflow roles remain. Strategy
# Reviewer is removed outright (not renamed, not aliased). Strategy Approval
# Authority is renamed to Strategy Approver — same responsibility, new name.
# Strategy Viewer is intentionally NOT part of this governance-role tuple any
# more: "Read access is not a third Strategy workflow role" (§7) — it stays a
# plain Frappe Role driving ordinary DocType permissions, outside the
# capability engine entirely.
ROLE_STRATEGY_AUTHOR = "Strategy Author"
ROLE_STRATEGY_APPROVER = "Strategy Approver"

STRATEGY_GOVERNANCE_ROLES = (
	ROLE_STRATEGY_AUTHOR,
	ROLE_STRATEGY_APPROVER,
)


def ensure_strategy_governance_roles() -> dict:
	"""Idempotent: create the 2 STR-CHG-001 v1.5 §7 Frappe Roles. No
	Separation of Duties Rule is seeded any more — with only 2 capabilities
	the only remaining rule is the direct same-version self-check in
	`_blocked_by_self_approval` below, not a capability-pair rule.

	Does not grant any Role to a specific user — provisioning real named
	actors is a separate seed-contract concern, once the exact actor
	identities exist."""
	created = {"roles": [], "sod_rules": []}

	for role in STRATEGY_GOVERNANCE_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)
			created["roles"].append(role)

	return created


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
	)


def _submitted_by(version_name: str) -> str | None:
	"""The user who performed this version's own "Submit for approval" —
	read from its audit trail (§18.1: "the version's audit history for the
	no-self-approval check"), not a stored field."""
	for event in list_events("Strategic Plan Version", version_name):
		if event.get("action") == "Submit for approval":
			return event.get("performed_by")
	return None


def _blocked_by_self_approval(user: str, capability: str, version_name: str) -> bool:
	"""§6.2/§13.4/§18.1: "The author cannot approve the same version" / "even
	if that user also holds the Strategy Approver role" — a same-version
	self-check, not a general capability-pair rule."""
	if capability != CAP_APPROVE:
		return False
	return _submitted_by(version_name) == user


def require_plan_version_capability(
	user: str, capability: str, version, *, correlation_id: str = ""
):
	if isinstance(version, str):
		version_name = version
	else:
		version_name = version.name
	resource = resource_context_for_version(version)
	require_role_capability(
		user,
		capability,
		resource,
		sod_blocked=_blocked_by_self_approval(user, capability, version_name),
	)


def has_plan_version_capability(user: str, capability: str, version) -> bool:
	if isinstance(version, str):
		version_name = version
	else:
		version_name = version.name
	if _blocked_by_self_approval(user, capability, version_name):
		return False
	return evaluate_role_capability(user, capability, resource_context_for_version(version))[0]


def require_plan_create_capability(user: str, procuring_entity_id: str) -> None:
	"""Creating a brand-new Strategic Plan needs no bootstrap workaround (unlike
	reference_data's PE/FY Context case) — Strategy's scope granularity is
	Procuring Entity itself, and the PE already exists at plan-creation time,
	so a normal Role+PE-scope check applies directly."""
	require_role_capability(
		user,
		CAP_AUTHOR,
		ResourceContext(resource_type="Strategic Plan", resource_id="", procuring_entity_id=procuring_entity_id),
	)
