"""AUTH-ADR-001 Phase 1 — read-only inventory and reconciliation (§12.1).

Classifies each user's Frappe Role holdings against their Operational Scope
Assignment-derived capability grants, so later migration phases map and
cut over from evidence instead of assumption. Never writes.

Invoke via: bench --site <site> execute kentender_core.scripts.auth_migration_inventory.build_inventory
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services.authorization_policy import _active_assignments, _profile_capabilities

# Capability Profile -> (target Frappe Role, classification) mapping approved
# for the AUTH-ADR-001 migration (Phase 4's table). Profiles not listed here
# are deliberately left unmapped rather than guessed — ADR §12.2 prohibits
# inferring a mapping from partial data.
CAPABILITY_ROLE_MAP: dict[str, tuple[str, str]] = {
	"REFDATA-STEWARD": ("Central Reference Data Steward", "global_central"),
	"REFDATA-APPROVER": ("Central Configuration Approver", "global_central"),
	"REFDATA-CTX-STEWARD": ("PE Configuration Steward", "pe_scoped"),
	"REFDATA-CTX-REVIEWER": ("Professional Configuration Reviewer / HoPF", "pe_scoped"),
	"REFDATA-CTX-APPROVER": ("Accounting Officer", "pe_scoped"),
}

MATCHED = "Matched"
ROLE_WITHOUT_CUSTOM_AUTHORITY = "Role without custom authority"
CUSTOM_AUTHORITY_WITHOUT_ROLE = "Custom authority without Role"
CONFLICTING_SCOPE = "Conflicting scope"
EXPIRED_OR_INACTIVE = "Expired or inactive"
AMBIGUOUS = "Ambiguous"

_BUCKET_PRIORITY = (
	AMBIGUOUS,
	CONFLICTING_SCOPE,
	ROLE_WITHOUT_CUSTOM_AUTHORITY,
	CUSTOM_AUTHORITY_WITHOUT_ROLE,
	EXPIRED_OR_INACTIVE,
	MATCHED,
)


def _native_pe_scope(user: str) -> set[str]:
	return set(frappe.get_all("User Permission", filters={"user": user, "allow": "Procuring Entity"}, pluck="for_value"))


def _overall_bucket(findings: list[dict[str, Any]]) -> str | None:
	if not findings:
		return None
	buckets = {f["bucket"] for f in findings}
	# The Amina Hassan shape — a visible Role backed by nothing, alongside an
	# unrelated active grant for a different Role — surfaces as BOTH
	# ROLE_WITHOUT_CUSTOM_AUTHORITY and CUSTOM_AUTHORITY_WITHOUT_ROLE at once;
	# report it under the Role-without-authority bucket since that is the
	# user-visible defect (the Role looks like it should work and doesn't).
	if ROLE_WITHOUT_CUSTOM_AUTHORITY in buckets and CUSTOM_AUTHORITY_WITHOUT_ROLE in buckets:
		return ROLE_WITHOUT_CUSTOM_AUTHORITY
	for bucket in _BUCKET_PRIORITY:
		if bucket in buckets:
			return bucket
	return MATCHED


def classify_user(user: str, at_time=None, role_map: dict[str, tuple[str, str]] | None = None) -> dict[str, Any]:
	"""Classify one user's authorization state per AUTH-ADR-001 §12.1. Read-only."""
	at = at_time or now_datetime()
	mapping = role_map if role_map is not None else CAPABILITY_ROLE_MAP
	held_roles = set(frappe.get_roles(user))
	native_pe_scope = _native_pe_scope(user)

	findings: list[dict[str, Any]] = []
	seen_target_roles: set[str] = set()

	for row in _active_assignments(user, at):
		profile_id = row.get("capability_profile_id")
		mapped = mapping.get(profile_id)
		if not mapped:
			findings.append({"bucket": AMBIGUOUS, "reason": f"Capability Profile {profile_id!r} has no approved Role mapping yet", "profile_id": profile_id})
			continue

		target_role, classification = mapped
		seen_target_roles.add(target_role)

		if not _profile_capabilities(profile_id, at):
			findings.append({"bucket": EXPIRED_OR_INACTIVE, "reason": f"Capability Profile {profile_id!r} is inactive or expired", "profile_id": profile_id})
			continue

		if target_role not in held_roles:
			findings.append({
				"bucket": CUSTOM_AUTHORITY_WITHOUT_ROLE,
				"reason": f"Active grant on {profile_id!r} maps to Role {target_role!r}, which the user does not hold",
				"profile_id": profile_id,
				"target_role": target_role,
			})
			continue

		if classification == "pe_scoped":
			pe_id = row.get("procuring_entity_id")
			if pe_id and pe_id not in native_pe_scope:
				findings.append({
					"bucket": CONFLICTING_SCOPE,
					"reason": f"Role {target_role!r} held and {profile_id!r} grants Procuring Entity {pe_id!r}, but no matching native User Permission scopes that Procuring Entity",
					"profile_id": profile_id,
					"target_role": target_role,
					"procuring_entity_id": pe_id,
				})
				continue

		findings.append({"bucket": MATCHED, "reason": f"{profile_id!r} and Role {target_role!r} agree", "profile_id": profile_id, "target_role": target_role})

	# Roles held that correspond to a mapped target Role but have no active
	# grant behind them at all — the Amina Hassan shape (visible Role, no or
	# mismatched active grant).
	governance_roles = {role for role, _classification in mapping.values()}
	for role in held_roles & governance_roles:
		if role not in seen_target_roles:
			findings.append({"bucket": ROLE_WITHOUT_CUSTOM_AUTHORITY, "reason": f"User holds Role {role!r} but has no active capability grant mapping to it", "target_role": role})

	return {"user": user, "bucket": _overall_bucket(findings), "findings": findings}


def build_inventory(users: list[str] | None = None) -> list[dict[str, Any]]:
	"""Read-only AUTH-ADR-001 §12.1 inventory across every enabled System User. Never writes."""
	at = now_datetime()
	if users is None:
		users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
	return [classify_user(user, at) for user in users]
