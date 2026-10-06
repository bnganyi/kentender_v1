# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""Named capabilities for the legacy KTSM supplier registry (AUD-XC-004/018/019).

The KTSM registry has no approved module document and no registered business
role (KenTender Approving Authority and the other KTSM Frappe Roles are legacy
projections — BDS FU-06). Until the owner registers real responsibilities, this
module is the one place that names who may do what, so every whitelisted entry
point asks the same question instead of carrying its own role set.

Two rules from AUTH-ADR-001 §5.7/§8 are applied here:

- a technical role (System Manager, Administrator) may *read* the registry but
  decides nothing: it appears in no mutation capability;
- a read capability never extends to portal / supplier accounts.
"""

import frappe
from frappe import _
from frappe.exceptions import PermissionError

TECHNICAL_ROLES = frozenset({"System Manager", "Administrator"})

APPROVER = "KenTender Approving Authority"
COMPLIANCE = "KenTender Compliance Officer"
REGISTRY_OFFICER = "KenTender Supplier Registry Officer"
AUDITOR = "KenTender Supplier Auditor"
BLACKLIST_AUTHORITY = "KenTender Supplier Blacklist Authority"

# capability -> Frappe Roles that grant it (legacy KTSM governance model, doc 4).
CAPABILITIES: dict[str, frozenset[str]] = {
	# Reads of the registry, its eligibility answers and the workbench.
	"read_registry": frozenset(
		{
			REGISTRY_OFFICER,
			COMPLIANCE,
			APPROVER,
			AUDITOR,
			BLACKLIST_AUTHORITY,
			"Procurement Officer",
			"Procurement Planner",
			"Planning Authority",
		}
	),
	# Submitted -> Under Review.
	"start_review": frozenset({REGISTRY_OFFICER, COMPLIANCE, APPROVER}),
	# Approve, return or reject a registration.
	"decide_registration": frozenset({APPROVER}),
	# Verify or reject a supplier document.
	"verify_documents": frozenset({COMPLIANCE, APPROVER}),
	# Suspend / reinstate a supplier.
	"change_operational_status": frozenset({APPROVER}),
	# Mark a supplier operationally Expired.
	"expire_supplier": frozenset({COMPLIANCE, APPROVER}),
	# Requested -> Under Review for a category.
	"start_category_review": frozenset({REGISTRY_OFFICER, COMPLIANCE, APPROVER}),
	# Qualify or reject a category.
	"decide_category": frozenset({COMPLIANCE, APPROVER}),
	# Blacklist (kept in supplier_policy.can_blacklist for compatibility).
	"blacklist": frozenset({BLACKLIST_AUTHORITY}),
}


def _roles(user: str | None = None) -> set[str]:
	return set(frappe.get_roles(user or frappe.session.user))


def has_capability(capability: str, user: str | None = None) -> bool:
	roles = _roles(user)
	if roles & CAPABILITIES[capability]:
		return True
	# Technical roles inspect the registry; they never act on it.
	return capability == "read_registry" and bool(roles & TECHNICAL_ROLES)


def require_capability(capability: str, message: str | None = None) -> None:
	if not has_capability(capability):
		frappe.throw(
			message or _("You are not permitted to do this in the supplier registry."),
			exc=PermissionError,
		)
