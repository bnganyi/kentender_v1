# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published Bid Submission seam for Bid Evaluation (EVL-CHG-001 v0.4
§5.1, §6 "Template / BDS → Evaluation"; EVL plan D6).

Bid Evaluation receives the unchanged submitted package of each bid opened at
a completed opening, only through `released_package`, and never reads a Bid
Submission record directly. The release is bound to the opening completion
that names the envelope and to the envelope's sealed digest: a superseded,
withdrawn or unknown envelope, a package that no longer matches its sealed
digest, or a box that is not closed is refused. Every answer is one of the
four TRUST-ADR-001 v0.1 §4 outcomes with the caller's correlation identity;
with no custody provider the answer is Unavailable, never a guess.
Evaluation keeps no package bytes: it reads them for its check run and for a
scoped evidence view, and writes nothing back."""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import opening_gateway

VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = opening_gateway.VERIFIED, opening_gateway.REJECTED, opening_gateway.UNAVAILABLE, opening_gateway.INDETERMINATE


def released_package(*, tender: str, envelope_id: str, package_digest: str, completion_reference: str, correlation_id: str) -> dict[str, Any]:
	manifest = opening_gateway.closed_manifest(tender)
	if manifest is None:
		return {"outcome": REJECTED, "reason": "no_close", "correlation_id": correlation_id}
	payload = manifest["payload"]
	envelope = next((e for e in payload["envelopes"] if e["envelope_id"] == envelope_id), None)
	inventory = set(payload["closed_box"].get("custody_inventory") or [])
	if envelope is None or envelope["status"] != "Submitted" or envelope_id not in inventory:
		return {"outcome": REJECTED, "reason": "not_current", "correlation_id": correlation_id}
	if cstr(package_digest) != cstr(envelope["package_digest"]):
		return {"outcome": REJECTED, "reason": "digest_mismatch", "correlation_id": correlation_id}
	attempt = frappe.db.get_value("Bid Submission Attempt", {"submission_version": envelope["submission_version"], "status": "Accepted"}, "correlation_id")
	box = opening_gateway._box()
	if box is None or not hasattr(box, "release_for_evaluation"):
		return {"outcome": UNAVAILABLE, "correlation_id": correlation_id}
	if not attempt:
		return {"outcome": REJECTED, "reason": "not_in_custody", "correlation_id": correlation_id}
	try:
		result = box.release_for_evaluation(tender=tender, correlation_id=attempt, completion_reference=completion_reference)
	except Exception:
		frappe.log_error(title="Tender box release for evaluation failed")
		return {"outcome": INDETERMINATE, "correlation_id": correlation_id}
	if result.get("outcome") != VERIFIED:
		return {"outcome": result.get("outcome", INDETERMINATE), "reason": cstr(result.get("reason")), "correlation_id": correlation_id}
	package = result["package"]
	if hashlib.sha256(package).hexdigest() != envelope["package_digest"]:
		return {"outcome": REJECTED, "reason": "package_mismatch", "correlation_id": correlation_id}
	return {"outcome": VERIFIED, "package": package, "package_digest": envelope["package_digest"], "envelope_id": envelope_id,
		"receipt_reference": envelope["receipt_reference"], "submission_version": envelope["submission_version"], "correlation_id": correlation_id,
		"simulation": bool(result.get("simulation"))}
