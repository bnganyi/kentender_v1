# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AttestOpeningTarget (BOP-CHG-001 v0.10 §5, §7, §10.4; TRUST-ADR-001 v0.1
§1(4), §2; binding row → PRC `AttestTarget`; BOP-N07, BOP-A07).

Each appointed member personally reviews the current version and signs or
initials exactly their own targets: one reviewed batch, but every target is
named with the digest the member saw, and each gets its own proof. A stale
digest or version is refused as a changed record; a proof that does not
verify is kept and does not count. The last verified proof completes the
opening automatically (no chair click)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.bid_opening.services import appointment, errors, prc, record, records


def my_targets(doc, user: str) -> tuple[str, list[dict[str, Any]]]:
	"""(current version id, this member's targets in it, each with whether it is satisfied)."""
	version = frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.proceeding, "state": ("in", ("Frozen", "Finalized"))}, "name",
		order_by="version_number desc")
	if not version:
		return "", []
	satisfied = {(p.target_id, p.target_digest): p for p in frappe.get_all("Proceeding Attestation", filters={"minutes_version": version, "member_user": user,
		"satisfies_current": 1}, fields=["target_id", "target_digest", "recorded_at"])}
	rows = []
	for t in frappe.get_doc("Proceeding Minutes Version", version).targets:
		if t.required_member != user:
			continue
		proof = satisfied.get((t.target_id, t.target_digest))
		what, action = record.what_you_do(t.target_type)
		rows.append({"target_id": t.target_id, "target_type": t.target_type, "target_reference": t.target_reference, "page_number": t.page_number,
			"target_digest": t.target_digest, "what_you_do": what, "action": action, "signed": bool(proof), "signed_at": str(proof.recorded_at) if proof else ""})
	return version, rows


def sign_opening_record(*, tender: str, minutes_version: str, targets: list[dict[str, str]], idempotency_key: str, user: str) -> dict[str, Any]:
	from kentender_procurement.bid_opening.services import completion
	from kentender_procurement.proceedings.services import attestation

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		if not appointment.member(doc.name, user) and not frappe.db.exists("Proceeding Member", {"parent": doc.proceeding, "member_user": user}):
			raise frappe.DoesNotExistError("Not found")
		if doc.state != "Awaiting attestations":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		version, mine = my_targets(doc, user)
		seen = {(t.get("target_id"), t.get("target_digest")) for t in targets or []}
		if minutes_version != version or any((t["target_id"], t["target_digest"]) not in seen for t in mine if not t["signed"]):
			code, message = errors.from_prc("PRC_TARGET_CHANGED")
			raise errors.BidOpeningError(code, message, {"current_version": version})
		for t in [t for t in mine if not t["signed"]]:
			out = attestation.attest_target(**prc.ref(doc.name), minutes_version=version, target_id=t["target_id"], target_digest=t["target_digest"],
				action=t["action"], idempotency_key=prc.key(idempotency_key, f"attest:{t['target_id']}"), actor=user)
			if not out["ok"]:
				records.bump(doc)
				code, message = errors.from_prc(out["code"])
				return {"ok": False, "code": code, "message": message, "target": t["target_id"], "verification_result": out.get("verification_result")}
		completed = completion.complete_if_ready(doc, idempotency_key)
		records.bump(doc)
		return records.summary(doc, signed=len([t for t in mine if not t["signed"]]), completed=completed)

	return records.command("AttestOpeningTarget", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"minutes_version": minutes_version, "targets": sorted((t.get("target_id"), t.get("target_digest")) for t in targets or [])}, body=body)
