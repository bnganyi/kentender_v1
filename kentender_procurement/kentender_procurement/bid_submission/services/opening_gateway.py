# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The published Bid Submission seam for Bid Opening (BOP-CHG-001 v0.10 §3,
§7 ReceiveClosedBox, ConfirmOpeningCustody, OpenNextTender; plan D4).

Bid Opening reads the sealed close and reaches the tender box only through
these functions; it never reads a Bid Submission record directly. Every
custody answer is one of the four TRUST-ADR-001 v0.1 §4 outcomes
("Accepted/Verified", "Rejected", "Unavailable", "Indeterminate") carrying the
caller's correlation identity; nothing is guessed on a timeout. Before close
there is no manifest and no reveal (BOP-CHG-001 v0.10 BOP-N01)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import clock, gateways, records

HANDOFF = "Bid Opening Handoff"
VERIFIED, REJECTED, UNAVAILABLE, INDETERMINATE = "Accepted/Verified", "Rejected", "Unavailable", "Indeterminate"


def closed_manifest(tender: str) -> dict[str, Any] | None:
	"""The one sealed hand-off for this Tender, digest-verified, or None before close."""
	row = frappe.db.get_value(HANDOFF, {"tender": tender}, ["handoff_id", "payload_json", "handoff_digest", "issued_at", "delivery_status"], as_dict=True)
	if not row:
		return None
	if hashlib.sha256(row.payload_json.encode("utf-8")).hexdigest() != row.handoff_digest:
		frappe.throw("The Bid Opening hand-off no longer matches its digest.")
	return {"handoff_id": row.handoff_id, "digest": row.handoff_digest, "issued_at": row.issued_at, "delivery_status": row.delivery_status,
		"payload": json.loads(row.payload_json)}


def acknowledge_handoff(handoff_id: str) -> None:
	"""Bid Opening has taken the hand-off; once only."""
	doc = frappe.get_doc(HANDOFF, handoff_id)
	if doc.delivery_status != "Delivered":
		doc.delivery_status = "Delivered"
		records.save(doc)


def custody_healthy() -> bool:
	return gateways.custody_healthy()


def _box():
	box = gateways.custody()
	return box if box is not None and gateways.custody_healthy() else None


def confirm_custody_participation(*, tender: str, member: str, independent: bool, manifest_digest: str, roster_digest: str, correlation_id: str) -> dict[str, Any]:
	box = _box()
	if box is None or not hasattr(box, "confirm_release"):
		return {"outcome": UNAVAILABLE, "correlation_id": correlation_id}
	try:
		result = box.confirm_release(tender=tender, member=member, independent=bool(independent), manifest_digest=manifest_digest, roster_digest=roster_digest,
			at=clock.now())
	except Exception:
		frappe.log_error(title="Tender box release confirmation failed")
		return {"outcome": INDETERMINATE, "correlation_id": correlation_id}
	return {**{k: v for k, v in result.items() if k in ("outcome", "reason", "participation_reference", "simulation")}, "correlation_id": correlation_id}


def reveal_envelope(*, tender: str, envelope_id: str, manifest_digest: str, roster_digest: str, correlation_id: str) -> dict[str, Any]:
	"""Release one current, timely envelope's exact package bytes. A superseded,
	withdrawn or unknown envelope is never released, and a package that does
	not match its sealed digest is withheld as a mismatch (BOP_PACKAGE_MISMATCH)."""
	manifest = closed_manifest(tender)
	if manifest is None:
		return {"outcome": REJECTED, "reason": "no_close", "correlation_id": correlation_id}
	payload = manifest["payload"]
	envelope = next((e for e in payload["envelopes"] if e["envelope_id"] == envelope_id), None)
	# the envelope ID is the tender box's own envelope reference (submission.py)
	inventory = set(payload["closed_box"].get("custody_inventory") or [])
	if envelope is None or envelope["status"] != "Submitted" or envelope_id not in inventory:
		return {"outcome": REJECTED, "reason": "not_current", "correlation_id": correlation_id}
	attempt = frappe.db.get_value("Bid Submission Attempt", {"submission_version": envelope["submission_version"], "status": "Accepted"}, "correlation_id")
	box = _box()
	if box is None or not hasattr(box, "reveal"):
		return {"outcome": UNAVAILABLE, "correlation_id": correlation_id}
	if not attempt:
		return {"outcome": REJECTED, "reason": "not_in_custody", "correlation_id": correlation_id}
	try:
		result = box.reveal(tender=tender, correlation_id=attempt, manifest_digest=manifest_digest, roster_digest=roster_digest)
	except Exception:
		frappe.log_error(title="Tender box reveal failed")
		return {"outcome": INDETERMINATE, "correlation_id": correlation_id}
	if result.get("outcome") != VERIFIED:
		return {"outcome": result.get("outcome", INDETERMINATE), "reason": cstr(result.get("reason")), "correlation_id": correlation_id}
	package = result["package"]
	if hashlib.sha256(package).hexdigest() != envelope["package_digest"]:
		return {"outcome": REJECTED, "reason": "package_mismatch", "correlation_id": correlation_id}
	return {"outcome": VERIFIED, "package": package, "package_digest": envelope["package_digest"], "envelope_id": envelope_id,
		"receipt_reference": envelope["receipt_reference"], "submission_version": envelope["submission_version"], "correlation_id": correlation_id,
		"simulation": bool(result.get("simulation"))}



def submitting_receipts(*, tender: str, user: str) -> list[str]:
	"""The current receipts of bids that an organisation `user` actively
	represents submitted to this Tender (BOP-CHG-001 v0.10 §7
	RequestOpeningRegister: "A verified submitting tenderer"). Attending or
	saying whom one represents proves nothing; only an active supplier-account
	assignment in the submitting organisation does."""
	from kentender_procurement.bid_submission.services import bid_authorization, supplier_gateway

	if not user or user == "Guest":
		return []
	organisations = {a["organisation_id"] for a in supplier_gateway.active_assignments(user=user) if a.get("active")
		and a.get("responsibility") in bid_authorization.PREPARERS}
	if not organisations:
		return []
	out = []
	for arrangement in frappe.get_all("Bidder Arrangement", filters={"tender": tender, "lead_organisation": ("in", list(organisations))}, pluck="name"):
		for workspace in frappe.get_all("Bid Workspace", filters={"bidder_arrangement": arrangement}, fields=["current_submission_version"]):
			if not workspace.current_submission_version:
				continue
			row = frappe.db.get_value("Bid Submission Version", workspace.current_submission_version, ["status", "receipt"], as_dict=True)
			if row and row.status == "Submitted" and row.receipt:
				out.append(row.receipt)
	return sorted(out)
