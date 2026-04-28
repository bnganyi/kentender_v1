# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

"""Blocker / reason codes aligned with 6. Eligibility Service Contract."""

# Standard codes (eligibility)
NOT_APPROVED = "NOT_APPROVED"
NOT_ACTIVE = "NOT_ACTIVE"
SUSPENDED = "SUSPENDED"
BLACKLISTED = "BLACKLISTED"
EXPIRED = "EXPIRED"
COMPLIANCE_INCOMPLETE = "COMPLIANCE_INCOMPLETE"
COMPLIANCE_EXPIRED = "COMPLIANCE_EXPIRED"
NON_COMPLIANT = "NON_COMPLIANT"
CATEGORY_NOT_ASSIGNED = "CATEGORY_NOT_ASSIGNED"
CATEGORY_NOT_QUALIFIED = "CATEGORY_NOT_QUALIFIED"
CATEGORY_REJECTED = "CATEGORY_REJECTED"
CATEGORY_EXPIRED = "CATEGORY_EXPIRED"
ACCESS_REVOKED = "ACCESS_REVOKED"

HUMAN = {
	NOT_APPROVED: "Supplier is not approved",
	NOT_ACTIVE: "Supplier is not yet active for procurement",
	SUSPENDED: "Supplier is currently suspended",
	BLACKLISTED: "Supplier is blacklisted",
	EXPIRED: "Supplier has expired (operational or documents)",
	COMPLIANCE_INCOMPLETE: "Required documents are missing or not verified",
	COMPLIANCE_EXPIRED: "Required document(s) have expired",
	NON_COMPLIANT: "Supplier is marked non-compliant",
	CATEGORY_NOT_ASSIGNED: "No category assignment for this request",
	CATEGORY_NOT_QUALIFIED: "Category is not yet qualified",
	CATEGORY_REJECTED: "Category qualification was rejected",
	CATEGORY_EXPIRED: "Category qualification has expired",
	ACCESS_REVOKED: "External access is revoked or suspended",
}
