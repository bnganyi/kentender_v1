# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The renderer seam (BOP-CHG-001 v0.10 §7 OpenNextTender "derive page count
from approved rendering", SelectOpeningTargets; plan D5, D16).

A renderer, found on the `kt_bop_renderer_services` hook (the last provider
that answers wins), turns one revealed package into pages and returns the
page count, the renderer-identified price and change locations, the facts
read aloud and a render digest. Its answer is one of the four TRUST-ADR-001
v0.1 §4 outcomes; an exception is Indeterminate, never a guessed page."""

from __future__ import annotations

from typing import Any

import frappe

HOOK = "kt_bop_renderer_services"
VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = "Accepted/Verified", "Rejected", "Unavailable", "Indeterminate"


def service() -> Any | None:
	for path in reversed(frappe.get_hooks(HOOK) or []):
		found = frappe.get_attr(path)()
		if found is not None:
			return found
	return None


def healthy() -> bool:
	return service() is not None


def render_package(*, package: bytes, envelope_id: str, receipt_reference: str, correlation_id: str) -> dict[str, Any]:
	provider = service()
	if provider is None:
		return {"outcome": UNAVAILABLE, "correlation_id": correlation_id}
	try:
		result = dict(provider.render(package=package, envelope_id=envelope_id, receipt_reference=receipt_reference))
	except Exception:
		frappe.log_error(title="Bid Opening renderer failed")
		return {"outcome": INDETERMINATE, "correlation_id": correlation_id}
	if result.get("outcome") not in (VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE):
		result = {"outcome": INDETERMINATE}
	return {**result, "correlation_id": correlation_id}
