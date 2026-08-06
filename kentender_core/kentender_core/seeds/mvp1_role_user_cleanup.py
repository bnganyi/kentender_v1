# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Disable leftover Users/Roles after MVP-1 keep-set decisions (2026-08-06).

Decisions:
1. Drop Performance Officer / Performance Verifier Role docs (capabilities → Strategy Officer / Manager).
2. Keep STD library roles + stdinst* users.
3. Keep supplier portal Website Users.
4. Keep operator bnganyi@yahoo.com outside seed packs.

Idempotent. Prefer disable over hard delete.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.seeds.constants import SEED_USERS

KEEP_EMAILS = {
	"Administrator",
	"Guest",
	"bnganyi@yahoo.com",
	"system@moh.test",
	*[row[0] for row in SEED_USERS],
	# KENTENDER_MVP_V1 Contract v2.0 canonical demo personas
	"moh.medicalservices.officer@example.test",
	"moh.publichealth.officer@example.test",
	"moh.strategy.reviewer@example.test",
	"moh.budget.reviewer@example.test",
	"moh.budget.authority@example.test",
	"moh.viewer@example.test",
	"other.entity.officer@example.test",
	"moh.budget.officer.authority@example.test",
}

# STD library still in-scope — do not disable these prefixes/domains.
KEEP_PREFIXES = (
	"stdinst",
	"smoke.",
	"supplier.",
	"lean.bidder.",
	"s100.bidder.",
	"x100.bidder.",
	"moh.",
	"other.entity.",
)

KEEP_DOMAINS_PARTIAL = (
	"@kentender.test",  # smoke supplier cohort
	"@example.test",  # KENTENDER_MVP_V1 canonical personas
)

ROLES_TO_DISABLE = (
	"Performance Officer",
	"Performance Verifier",
	"BWMF Auditor",
	"BWMF Procurement Reviewer",
	"BWMF Publication Service",
	"BWMF Tender Approver",
	"BWMF Tender Configurator",
	"Approving Authority",
	"Auditor / Oversight User",
	"KenTender Approving Authority",
	"KenTender Compliance Officer",
	"Evaluation Committee Member",
	"Evaluation Coordinator",
	"Opening Committee Member",
	"Head of Procurement",
	"Tender Manager",
	"Procurement Manager",
	"Procurement Assistant",
	"Procurement Planning Officer",
	"Legal Reviewer",
	"Legal / Policy Reviewer",
	"Fulfillment User",
	"_Test Role",
	"_Test Role 2",
	"_Test Role 3",
	"_Test Role 4",
)


def _keep_user(email: str) -> bool:
	if email in KEEP_EMAILS:
		return True
	low = (email or "").lower()
	if any(low.startswith(p) for p in KEEP_PREFIXES):
		return True
	if any(p in low for p in KEEP_DOMAINS_PARTIAL):
		return True
	# Website User with KenTender External Supplier — supplier portal keep
	if frappe.db.exists("User", email):
		roles = set(frappe.get_roles(email))
		if "KenTender External Supplier" in roles:
			return True
	return False


def run_mvp1_role_user_cleanup(*, dry_run: bool = False) -> dict[str, Any]:
	"""Disable remove-candidate Users and Roles. Returns summary."""
	disabled_users: list[str] = []
	skipped_users: list[str] = []
	disabled_roles: list[str] = []

	for name in frappe.get_all("User", filters={"name": ["!=", "Guest"]}, pluck="name"):
		if _keep_user(name):
			skipped_users.append(name)
			continue
		if dry_run:
			disabled_users.append(name)
			continue
		# Disable + strip KenTender business roles so they cannot re-login usefully
		frappe.db.set_value("User", name, "enabled", 0, update_modified=False)
		disabled_users.append(name)

	for role in ROLES_TO_DISABLE:
		if not frappe.db.exists("Role", role):
			continue
		if dry_run:
			disabled_roles.append(role)
			continue
		# Remove Has Role links for disabled users first; then disable Role
		frappe.db.sql(
			"DELETE FROM `tabHas Role` WHERE role=%s AND parenttype='User'",
			role,
		)
		frappe.db.set_value("Role", role, "disabled", 1, update_modified=False)
		disabled_roles.append(role)

	if not dry_run:
		frappe.db.commit()

	return {
		"ok": True,
		"dry_run": dry_run,
		"disabled_users": sorted(disabled_users),
		"disabled_users_count": len(disabled_users),
		"kept_users_count": len(skipped_users),
		"disabled_roles": disabled_roles,
	}


def upsert_mvp1_role_user_cleanup() -> dict[str, Any]:
	"""Entry point for `bench execute`."""
	return run_mvp1_role_user_cleanup(dry_run=False)
