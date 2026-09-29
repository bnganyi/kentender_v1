# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FinalizeProceeding and AppendSupplement (PRC-CHG-001 v0.9 §5, §7).

Finalization is the owner's guarded internal transition after the last
verified proof: every target of the current version needs a satisfying,
verified proof by its named member, or it is refused with every missing item
(PRC-A04). There is no generic approval. After finalization the original is
immutable and a correction is an append-only supplement (PRC-N05)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.proceedings.services import clock, owners, records, signing
from kentender_procurement.proceedings.services.errors import fail

SYSTEM_ACTOR = owners.SYSTEM_ACTOR
SUPPLEMENT = "Proceeding Supplement"


def missing_proofs(doc) -> list[dict[str, Any]]:
	current = frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.name, "version_number": cint(doc.current_minutes_version)}, "name")
	if not current:
		return [{"target_id": "", "required_member": "", "reason": "no_frozen_version"}]
	satisfied = {(p.target_id, p.member_user, p.target_digest) for p in frappe.get_all("Proceeding Attestation", filters={
		"proceeding": doc.name, "minutes_version": current, "satisfies_current": 1, "verification_result": signing.VERIFIED,
	}, fields=["target_id", "member_user", "target_digest"])}
	return [{"target_id": t.target_id, "required_member": t.required_member} for t in frappe.get_doc("Proceeding Minutes Version", current).targets
		if (t.target_id, t.required_member, t.target_digest) not in satisfied]


def finalize_proceeding(*, owner_type: str, owner_id: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Awaiting attestations",))
		missing = missing_proofs(doc)
		if missing:
			fail("PRC_EVIDENCE_INCOMPLETE", {"missing": missing})
		version = frappe.get_doc("Proceeding Minutes Version", {"proceeding": doc.name, "version_number": cint(doc.current_minutes_version)})
		version.state = "Finalized"
		records.save(version)
		event_id = records.event(doc, "ProceedingFinalized", source="System", actor=actor, owner_reference=version.name, payload={"digest": version.content_digest})
		records.bump(doc, state="Finalized", finalized_at=clock.now())
		return records.summary(doc, event_id, minutes_version=version.name)

	return records.command("FinalizeProceeding", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version}, body=body)


def append_supplement(*, owner_type: str, owner_id: str, expected_version: int, original_version: int, kind: str, correct_information: str, reason: str,
		idempotency_key: str, actor: str, evidence_reference: str = "") -> dict[str, Any]:
	"""The owner restricts which kinds it offers (BOP-CHG-001 v0.10 §10.6 four kinds)."""
	payload = {"expected_version": expected_version, "original_version": original_version, "kind": kind, "correct_information": correct_information,
		"reason": reason, "evidence_reference": evidence_reference}

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Finalized",))
		if cint(original_version) != cint(doc.current_minutes_version):
			fail("PRC_VERSION_CONFLICT", {"reason": "original_version", "current_version": cint(doc.current_minutes_version)})
		fields = {f: "Required." for f, v in (("kind", kind), ("correct_information", correct_information), ("reason", reason)) if not cstr(v).strip()}
		if fields:
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": fields})
		number = frappe.db.count(SUPPLEMENT, {"proceeding": doc.name}) + 1
		supplement_id = f"{doc.name}-S{number:02d}"
		original = frappe.db.get_value("Proceeding Minutes Version", {"proceeding": doc.name, "version_number": cint(doc.current_minutes_version)}, "name")
		records.insert(frappe.get_doc({
			"doctype": SUPPLEMENT, "supplement_id": supplement_id, "proceeding": doc.name, "original_version": original, "kind": cstr(kind).strip(),
			"correct_information": cstr(correct_information).strip(), "reason": cstr(reason).strip(), "evidence_reference": evidence_reference,
			"author": owners.user_or_none(actor), "recorded_at": clock.now(),
		}))
		event_id = records.event(doc, "SupplementAppended", source="Recorder", actor=actor, owner_reference=supplement_id, note=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, event_id, supplement_id=supplement_id)

	return records.command("AppendSupplement", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="recorder",
		payload=payload, body=body)
