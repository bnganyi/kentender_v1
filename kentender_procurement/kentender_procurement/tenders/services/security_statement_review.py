# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Published Tenders that never stated how their tender security may be submitted and whether an original is delivered
(Project Owner, 10 October 2026).

"Security required" never meant "a physical original is required": the Tender states each, in its own published
definition (`submission_method`, `original_delivery`). A Tender published before those statements existed says
nothing, and nothing here — or in Bid Submission — fills the gap for it: no physical requirement is invented and
no published requirement is changed. This list is the explicit review. For each Tender on it the Head of Procurement Function either records, as an auditable correction (`security_statement`), the requirement its published documents already make explicit, or — where the requirement is genuinely to change — issues an addendum before closing; a closed Tender keeps what it issued. Reading it writes nothing."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.tenders.services import bid_definition, tender_authorization as authz
from kentender_procurement.tenders.services import tender_roles

SECURITY_RULE = "RR-TENDER-SECURITY"


def stated_in(definition: dict[str, Any]) -> bool | None:
	"""True when the definition's security group states both facts, False when it states neither or half, None when it has no security group."""
	for section in definition.get("sections") or []:
		for group in section.get("groups") or []:
			if group.get("rule_id") == SECURITY_RULE:
				facts = group.get("published_facts") or {}
				return bool(facts.get("submission_method")) and bool(facts.get("original_delivery"))
	return None


def unstated() -> list[dict[str, str]]:
	"""Every published Tender whose current published definition does not state both."""
	out = []
	for row in frappe.get_all("Tender", filters={"published_at": ("is", "set")}, fields=["name", "tender_reference", "published_at", "overall_status"], order_by="published_at asc", limit_page_length=0):
		current = bid_definition.current(row.name)
		# a Tender whose requirement was recorded by an auditable correction is no longer unstated (security_statement)
		if current and stated_in(current["definition"]) is False and not frappe.db.exists("Tender Security Statement", {"tender": row.name}):
			out.append({"tender_reference": row.tender_reference, "published_at": str(row.published_at), "status": row.overall_status or ""})
	return out


def get_security_statement_review(*, user: str | None = None) -> dict[str, Any]:
	"""The review list for the people who run Tenders (Procurement Officer, Head of Procurement Function, Accounting Officer, Auditor)."""
	authz.require_any_site_role(tender_roles.SITE_WIDE_ROLES, user)
	rows = unstated()
	return {
		"rows": rows,
		"text": "These published Tenders do not state how tender security may be submitted or whether an original must be delivered. "
		"Bid Submission shows suppliers no original requirement for them until the requirement is recorded as an auditable correction or amended by addendum." if rows else "Every published Tender states how its tender security may be submitted.",
	}
