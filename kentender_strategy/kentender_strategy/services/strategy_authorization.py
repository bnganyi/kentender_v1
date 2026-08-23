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

import json

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

# STR-CHG-001 §7: Viewer and Reviewer keep their exact existing Frappe Role
# names (already correct); Author and Approval Authority are new — the
# legacy "Strategy Officer"/"Strategy Manager"/"Planning Authority" roles
# stay in place only because strategy_writes.py/strategy_contracts.py
# (Phase 4/6/7 rebuild targets) still reference them, not because they are
# part of this rebuilt role set.
ROLE_STRATEGY_VIEWER = "Strategy Viewer"
ROLE_STRATEGY_AUTHOR = "Strategy Author"
ROLE_STRATEGY_REVIEWER = "Strategy Reviewer"
ROLE_STRATEGY_APPROVAL_AUTHORITY = "Strategy Approval Authority"

STRATEGY_GOVERNANCE_ROLES = (
	ROLE_STRATEGY_VIEWER,
	ROLE_STRATEGY_AUTHOR,
	ROLE_STRATEGY_REVIEWER,
	ROLE_STRATEGY_APPROVAL_AUTHORITY,
)

# profile_id -> (Role, [capabilities])
_GOVERNANCE_PROFILES: dict[str, tuple[str, list[str]]] = {
	"CAP-STRATEGY-AUTHOR": (ROLE_STRATEGY_AUTHOR, [CAP_AUTHOR]),
	"CAP-STRATEGY-REVIEWER": (ROLE_STRATEGY_REVIEWER, [CAP_REVIEW]),
	"CAP-STRATEGY-APPROVAL-AUTHORITY": (ROLE_STRATEGY_APPROVAL_AUTHORITY, [CAP_APPROVE]),
}

# (rule_id, first_capability, second_capability) — all 3 pairwise combinations
# of the 3 lifecycle capabilities. STR-CHG-001 §6.2 requires the submitter,
# reviewer and approver on one version to be 3 distinct actors; 3 pairwise
# rules already guarantee this (any 2-of-3 overlap is one of these 3 pairs) —
# no separate 3-way hand-check is needed, unlike CFG-CHG-002's context-reopen
# flow, which had no per-stage doctype state to key a pairwise check off of.
_SOD_PAIRS = (
	("SOD-STRATEGY-AUTHOR-REVIEWER", CAP_AUTHOR, CAP_REVIEW),
	("SOD-STRATEGY-AUTHOR-APPROVE", CAP_AUTHOR, CAP_APPROVE),
	("SOD-STRATEGY-REVIEW-APPROVE", CAP_REVIEW, CAP_APPROVE),
)


def ensure_strategy_governance_roles() -> dict:
	"""Idempotent: create the 4 STR-CHG-001 §7 Frappe Roles, the 3 lifecycle
	Capability Profiles, and the 3 pairwise Separation of Duties Rules.

	Does not grant any of this to a specific user — Operational Scope
	Assignments for real named actors are Phase 5's seed contract (§16),
	once the exact 9 actor identities exist."""
	created = {"roles": [], "profiles": [], "sod_rules": []}

	for role in STRATEGY_GOVERNANCE_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)
			created["roles"].append(role)

	for profile_id, (_role, capabilities) in _GOVERNANCE_PROFILES.items():
		if frappe.db.exists("Capability Profile", profile_id):
			existing = frappe.get_doc("Capability Profile", profile_id)
			if frappe.parse_json(existing.capabilities) != capabilities:
				existing.capabilities = json.dumps(capabilities)
				existing.save(ignore_permissions=True)
			continue
		frappe.get_doc(
			{
				"doctype": "Capability Profile",
				"profile_id": profile_id,
				"profile_name": profile_id.replace("-", " ").title(),
				"capabilities": json.dumps(capabilities),
				"allows_entity_wide": 1,
				"status": "Active",
				"concurrency_token": frappe.generate_hash(length=16),
			}
		).insert(ignore_permissions=True)
		created["profiles"].append(profile_id)

	for rule_id, first, second in _SOD_PAIRS:
		if frappe.db.exists("Separation of Duties Rule", rule_id):
			continue
		frappe.get_doc(
			{
				"doctype": "Separation of Duties Rule",
				"rule_id": rule_id,
				"rule_name": rule_id.replace("-", " ").title(),
				"first_capability": first,
				"second_capability": second,
				"enforcement_level": "Workflow instance",
				"module_name": "Strategy",
				"status": "Active",
				"effective_from": frappe.utils.add_days(frappe.utils.now_datetime(), -1),
			}
		).insert(ignore_permissions=True)
		created["sod_rules"].append(rule_id)

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
