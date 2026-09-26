"""CFG-CHG-002 v0.16 §7.1–7.2 — whitelisted Supplier portal settings endpoints
for the System setup section. Thin wrappers over
:mod:`kentender_core.services.public_portal` with explicit signatures (no
``**kwargs``); every authority check, validation and audit write happens in
the service. The bidder-safe projection is not exposed here: the portal
renders it server-side and Tenders / Bid Submission call the service
in-process.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_core.services import public_portal as portal


def _is_setup_actor() -> bool:
	user = frappe.session.user
	return user == "Administrator" or "System Manager" in frappe.get_roles(user)


@frappe.whitelist()
def get_public_portal_settings() -> dict[str, Any]:
	"""GetPublicPortalSettings. A denial is returned as data (KT-STD-001 §3A.2),
	matching the Procurement settings tab read."""
	if not _is_setup_actor():
		return {"outcome": "FORBIDDEN"}
	return {"outcome": "OK", **portal.get_public_portal_settings()}


@frappe.whitelist(methods=["POST"])
def update_public_portal_settings(
	supplier_support_email: str | None = None,
	supplier_support_phone: str | None = None,
	supplier_support_hours: str | None = None,
	privacy_notice_url: str | None = None,
	portal_terms_url: str | None = None,
	accessibility_statement_url: str | None = None,
	expected_version: int | str | None = None,
	idempotency_key: str | None = None,
) -> dict[str, Any]:
	return portal.update_public_portal_settings(
		supplier_support_email=supplier_support_email or "",
		supplier_support_phone=supplier_support_phone or "",
		supplier_support_hours=supplier_support_hours or "",
		privacy_notice_url=privacy_notice_url or "",
		portal_terms_url=portal_terms_url or "",
		accessibility_statement_url=accessibility_statement_url or "",
		expected_version=expected_version,
		idempotency_key=idempotency_key or "",
	)
