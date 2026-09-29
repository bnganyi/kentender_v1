# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AttestTarget (PRC-CHG-001 v0.9 §4 Attestation, §7; TRUST-ADR-001 v0.1 §1(4)).

Only the actual appointed member named on a target may attest it, and only
on the current frozen version's exact digest: no proxy, no stale target
(PRC-N02). The proof outcome comes from the shared signing service; a proof
that does not verify is kept as evidence but cannot satisfy the target
(PRC-A04)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.proceedings.services import clock, records, signing
from kentender_procurement.proceedings.services.errors import fail, unverified

ATTESTATION = "Proceeding Attestation"
ACTIONS = ("Sign", "Initial")


def attest_target(*, owner_type: str, owner_id: str, expected_version: int, minutes_version: str, target_id: str, target_digest: str, action: str,
		idempotency_key: str, actor: str) -> dict[str, Any]:
	payload = {"expected_version": expected_version, "minutes_version": minutes_version, "target_id": target_id, "target_digest": target_digest, "action": action}

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Awaiting attestations",))
		if actor not in {m.member_user for m in doc.members}:
			fail("PRC_MEMBER_REQUIRED")
		current = frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.name, "version_number": cint(doc.current_minutes_version)}, "name")
		if minutes_version != current:
			fail("PRC_TARGET_CHANGED", {"current_version": current})
		target = next((t for t in frappe.get_doc("Proceeding Minutes Version", current).targets if t.target_id == target_id and t.required_member == actor), None)
		if target is None:
			others = frappe.get_all("Proceeding Minutes Target", filters={"parent": current, "target_id": target_id}, pluck="required_member")
			fail("PRC_MEMBER_REQUIRED" if others else "PRC_TARGET_CHANGED", {"target": target_id})
		if target.target_digest != target_digest:
			fail("PRC_TARGET_CHANGED", {"target": target_id})
		if action not in ACTIONS:
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"action": "Choose sign or initial."}})
		existing = frappe.db.get_value(ATTESTATION, {"proceeding": doc.name, "minutes_version": current, "target_id": target_id, "member_user": actor,
			"satisfies_current": 1}, "attestation_id")
		if existing:
			return records.summary(doc, "", attestation_id=existing, verification_result=signing.VERIFIED)
		number = frappe.db.count(ATTESTATION, {"proceeding": doc.name}) + 1
		attestation_id = f"{doc.name}-P{number:04d}"
		proof = signing.attest(member=actor, target_id=target_id, target_digest=target_digest, minutes_version=current, action=action, correlation_id=attestation_id)
		verified = proof["outcome"] == signing.VERIFIED
		records.insert(frappe.get_doc({
			"doctype": ATTESTATION, "attestation_id": attestation_id, "proceeding": doc.name, "minutes_version": current, "target_id": target_id,
			"target_digest": target_digest, "member_user": actor, "action": action, "method": proof.get("method") or "Unavailable", "recorded_at": clock.now(),
			"proof_reference": proof.get("proof_reference") or "", "correlation_id": proof["correlation_id"], "verification_result": proof["outcome"],
			"satisfies_current": 1 if verified else 0,
		}))
		event_id = records.event(doc, "TargetAttested" if verified else "AttestationNotVerified", source="Member", actor=actor, owner_reference=attestation_id,
			payload={"target": target_id, "digest": target_digest, "outcome": proof["outcome"]})
		records.bump(doc)
		if not verified:
			return unverified({"proceeding": doc.name, "record_version": cint(doc.record_version), "attestation_id": attestation_id, "verification_result": proof["outcome"]})
		return records.summary(doc, event_id, attestation_id=attestation_id, verification_result=proof["outcome"])

	return records.command("AttestTarget", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="member",
		payload=payload, body=body)
