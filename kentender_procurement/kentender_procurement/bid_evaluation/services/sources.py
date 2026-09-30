# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reading the opened bids (EVL-CHG-001 v0.4 §5.1, §6 "Template / BDS →
Evaluation"; plan D6, C23).

Every package comes from Bid Submission's published seam, bound to the
opening completion that opened it and to its sealed digest. The bid
definition it was made against is taken from the package itself and checked
against the Tender's published definition of that version (the opening
hand-off does not carry it, C23). Evaluation keeps no package bytes: a
package is read for a check run or a scoped evidence view and dropped. On a
test environment the intake fault switch can force the release outcome
(plan D16)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import simulation

VERIFIED = "Accepted/Verified"


def release(*, tender: str, package: dict[str, Any], completion_reference: str, correlation_id: str) -> dict[str, Any]:
	"""One opened package: {outcome, reason, body, definition} or a refusal."""
	forced = simulation.controls().get("intake_outcome")
	if forced:
		return {"outcome": forced, "reason": "simulation", "correlation_id": correlation_id}
	from kentender_procurement.bid_submission.services import evaluation_gateway

	out = evaluation_gateway.released_package(tender=tender, envelope_id=package["envelope_id"], package_digest=package["package_digest"],
		completion_reference=completion_reference, correlation_id=correlation_id)
	if out.get("outcome") != VERIFIED:
		return out
	try:
		body = json.loads(out["package"])
	except ValueError:
		return {"outcome": "Rejected", "reason": "unreadable", "correlation_id": correlation_id}
	if body.get("schema") != "kt-bds-package/1":
		return {"outcome": "Rejected", "reason": "unsupported_package", "correlation_id": correlation_id}
	definition = definition_of(tender, body)
	if definition is None:
		return {"outcome": "Rejected", "reason": "definition_mismatch", "correlation_id": correlation_id}
	return {"outcome": VERIFIED, "body": body, "definition": definition, "package_digest": out["package_digest"], "correlation_id": correlation_id,
		"simulation": out.get("simulation")}


def definition_of(tender: str, body: dict[str, Any]) -> dict[str, Any] | None:
	"""The exact published definition the bid was made against, or None when
	the package's identity does not match the Tender's record of it."""
	from kentender_procurement.tenders.services import evaluation_seam as tenders

	ident = body.get("tender") or {}
	stored = tenders.definition(tender, ident.get("definition_version"))
	if not stored or cstr(stored.get("definition_digest")) != cstr(ident.get("definition_digest")) \
			or cstr(stored.get("bid_definition_id")) != cstr(ident.get("bid_definition_id")):
		return None
	return stored


def cached_package(doc, bid) -> dict[str, Any]:
	"""The package of one Evaluation Bid for this request (a scoped read)."""
	cache = getattr(frappe.local, "kt_evl_packages", None)
	if cache is None:
		cache = frappe.local.kt_evl_packages = {}
	slot = f"{bid.name}:{bid.package_digest}"  # a name is reused when a test world is rebuilt; the digest is not
	if slot not in cache:
		cache[slot] = release(tender=doc.tender, package={"envelope_id": bid.envelope_id, "package_digest": bid.package_digest},
			completion_reference=cstr(doc.opening_handoff), correlation_id=f"read:{bid.name}")
	return cache[slot]
