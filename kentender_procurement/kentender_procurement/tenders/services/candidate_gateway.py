# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §3 / §4.9–4.9A — the one seam to the Bid Submission
owner's Tender-bound candidate registry (plan D8′, W2).

Bid Submission (BDS-CHG-001 v0.8) creates a candidate registration only
through **Start bid** and answers, through its `kt_tender_candidate_registry`
provider, the exact Active `bidder_arrangement_id`s of a Tender and each
one's verified mandatory-notice destination version at an instant. Tenders
consumes that projection; it never creates or edits supplier contacts. The
Tenders stand-in registry is retired (FOLLOW_UPS FU-25; BDS v0.8 plan
Phase 5). A provider module exposes:

- `candidate_audience(*, tender: str, at) -> list[dict]` — rows with
  `candidate_registration_id`, `destination`, `destination_version`;
- `candidate_registration(*, tender: str, candidate_registration_id: str) -> dict | None`
  — the registration of that candidate on that Tender, with its `status`
  (Active, or Closed once the submission period closed: a closed period
  does not unregister the candidate, so protected reads keep its name).

Without a provider a Tender has no candidates: no notice audience and no
clarification intake.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import clock
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import INQUIRY_PRODUCER_ROLE

HOOK = "kt_tender_candidate_registry"


def _provider():
	"""The registered provider module (the last `kt_tender_candidate_registry`
	hook value), or None. Tests may set `frappe.flags.kt_tender_candidate_registry`
	to a provider object or a dotted module path; nothing else sets that flag."""
	override = frappe.flags.get("kt_tender_candidate_registry")
	if override:
		return frappe.get_module(override) if isinstance(override, str) else override
	paths = frappe.get_hooks(HOOK) or []
	return frappe.get_module(paths[-1]) if paths else None


def candidate_audience(*, tender: str, at=None) -> list[dict[str, Any]]:
	"""The authoritative Active candidates of `tender` at `at` (§4.9A: a
	candidate registered later is never a recipient of an earlier notice)."""
	provider = _provider()
	return list(provider.candidate_audience(tender=tender, at=at or clock.now())) if provider is not None else []


def candidate_registration(*, tender: str, candidate_registration_id: str) -> dict[str, Any] | None:
	provider = _provider()
	return provider.candidate_registration(tender=tender, candidate_registration_id=candidate_registration_id) if provider is not None else None


def candidate_name(*, tender: str, candidate_registration_id: str) -> str:
	"""Protected: authorised procurement / support / audit readers only."""
	row = candidate_registration(tender=tender, candidate_registration_id=candidate_registration_id)
	return cstr((row or {}).get("candidate_name"))


# --------------------------------------------------------------------------
# the bidder-facing producer identity (plan W2): the service user that hands
# a supplier's clarification question to Tenders
# --------------------------------------------------------------------------


def ensure_producer_role() -> None:
	if not frappe.db.exists("Role", INQUIRY_PRODUCER_ROLE):
		frappe.get_doc({"doctype": "Role", "role_name": INQUIRY_PRODUCER_ROLE, "desk_access": 0}).insert(ignore_permissions=True)


def require_producer(user: str | None = None) -> str:
	"""The bidder-facing service identity (never a business responsibility)."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest" or INQUIRY_PRODUCER_ROLE not in set(frappe.get_roles(principal)):
		fail("TND_RESPONSIBILITY_REQUIRED", "Only the registered bidder-facing service may deliver this event.")
	return principal
