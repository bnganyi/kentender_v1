# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Phase 5 governance roles and separation-of-duties checks."""

from __future__ import annotations

import frappe
from frappe import _

ROLE_CONFIGURATOR = "BWMF Tender Configurator"
ROLE_REVIEWER = "BWMF Procurement Reviewer"
ROLE_APPROVER = "BWMF Tender Approver"
ROLE_PUBLICATION = "BWMF Publication Service"
ROLE_AUDITOR = "BWMF Auditor"

ALL_GOVERNANCE_ROLES = (
	ROLE_CONFIGURATOR,
	ROLE_REVIEWER,
	ROLE_APPROVER,
	ROLE_PUBLICATION,
	ROLE_AUDITOR,
)


def ensure_governance_roles() -> None:
	"""Idempotently create Frappe Role rows used by Phase 5 tests/services."""
	for role in ALL_GOVERNANCE_ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def actor_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	if user == "Administrator" or frappe.session.user == "Administrator":
		# Administrator is treated as holding all governance roles in tests/dev.
		return set(ALL_GOVERNANCE_ROLES)
	return set(frappe.get_roles(user))


def require_role(*allowed: str, user: str | None = None) -> str:
	user = user or frappe.session.user
	if not user or user == "Guest":
		frappe.throw(_("Authentication required."), title="BWMF_AUTH")
	roles = actor_roles(user)
	if not roles.intersection(allowed):
		frappe.throw(
			_("Actor lacks required role(s): {0}.").format(", ".join(allowed)),
			title="BWMF_ROLE_DENIED",
		)
	return user


def require_org_scope(organization: str, *, actor_org: str | None = None) -> None:
	"""Organization scope check — actor_org must match when provided."""
	if actor_org is not None and actor_org != organization:
		frappe.throw(_("Organization scope mismatch."), title="BWMF_ORG_SCOPE")


def assert_separation_of_duties(
	*,
	submitter: str,
	approver: str,
	separation_enabled: bool = True,
) -> None:
	if separation_enabled and submitter and approver and submitter == approver:
		frappe.throw(
			_("Approver cannot approve their own submission."),
			title="BWMF_SOD_VIOLATION",
		)
