# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ReadProceeding and ExportProceeding (PRC-CHG-001 v0.9 §7, §9, §12).

Readable only by a reader the owner authorises; anyone else, technical users
included, gets the protected Not found (PRC-N03, PRC-A02). The owner applies
field-level disclosure on top. The export makes the final record, its
digest, each member's proof and each supplement independently reproducible,
and the original part never changes when a supplement is added (PRC-N05)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint

from kentender_procurement.proceedings.services import attendance, owners, records
from kentender_procurement.proceedings.services.errors import fail

EVENT_FIELDS = ["event_id", "sequence", "event_type", "recorded_at", "actor", "source", "owner_event_id", "owner_reference", "note", "reported_at", "reported_by",
	"pre_session", "linked_event"]
PROOF_FIELDS = ["attestation_id", "minutes_version", "target_id", "target_digest", "member_user", "action", "method", "recorded_at", "proof_reference",
	"correlation_id", "verification_result", "satisfies_current"]


def _doc(owner_type: str, owner_id: str, user: str):
	owners.require(owner_type, owner_id, user, "reader")
	name = records.find(owner_type, owner_id)
	if not name:
		fail("PRC_OWNER_UNAVAILABLE")
	return frappe.get_doc(records.PROCEEDING, name)


def _minutes(doc) -> list[dict[str, Any]]:
	out = []
	for name in frappe.get_all("Proceeding Minutes Version", filters={"proceeding": doc.name}, order_by="version_number asc", pluck="name"):
		version = frappe.get_doc("Proceeding Minutes Version", name)
		out.append({
			"minutes_version": version.name, "version_number": version.version_number, "state": version.state, "content": version.content,
			"content_digest": version.content_digest, "page_count": version.page_count, "register_reference": version.register_reference,
			"register_digest": version.register_digest, "event_ids": json.loads(version.event_ids_json or "[]"), "frozen_at": str(version.frozen_at),
			"frozen_by": version.frozen_by, "supersedes_version": version.supersedes_version, "supersede_reason": version.supersede_reason,
			"targets": [{f: t.get(f) for f in ("target_id", "target_type", "target_reference", "page_number", "target_digest", "required_member", "roster_segment")}
				for t in version.targets],
			"proofs": frappe.get_all("Proceeding Attestation", filters={"minutes_version": version.name}, fields=PROOF_FIELDS, order_by="recorded_at asc"),
		})
	return out


def read_proceeding(*, owner_type: str, owner_id: str, user: str) -> dict[str, Any]:
	doc = _doc(owner_type, owner_id, user)
	return {
		"proceeding": doc.name, "state": doc.state, "record_version": cint(doc.record_version), "title": doc.title, "actual_start": doc.actual_start,
		"actual_end": doc.actual_end, "ceased_at": doc.ceased_at, "not_held_reason": doc.not_held_reason, "finalized_at": doc.finalized_at,
		"members": [{f: m.get(f) for f in ("member_user", "full_name", "designation", "committee_capacity", "appointment_reference", "roster_segment", "active")}
			for m in doc.members],
		"attendance": attendance.rows(doc.name), "present": attendance.present(doc.name),
		"events": frappe.get_all(records.EVENT, filters={"proceeding": doc.name}, fields=EVENT_FIELDS, order_by="sequence asc"),
		"minutes": _minutes(doc),
		"supplements": frappe.get_all("Proceeding Supplement", filters={"proceeding": doc.name}, fields=[
			"supplement_id", "original_version", "kind", "correct_information", "reason", "evidence_reference", "author", "recorded_at"], order_by="recorded_at asc"),
	}


def export_proceeding(*, owner_type: str, owner_id: str, user: str) -> dict[str, Any]:
	view = read_proceeding(owner_type=owner_type, owner_id=owner_id, user=user)
	final = next((m for m in view["minutes"] if m["state"] == "Finalized"), None)
	finalized_at_sequence = next((e["sequence"] for e in view["events"] if e["event_type"] == "ProceedingFinalized"), None)
	events = [e for e in view["events"] if finalized_at_sequence is None or e["sequence"] <= finalized_at_sequence]
	original = json.loads(json.dumps({
		"proceeding": view["proceeding"], "title": view["title"], "actual_start": view["actual_start"], "actual_end": view["actual_end"],
		"members": view["members"], "attendance": view["attendance"], "events": events, "final_minutes": final,
	}, default=str))
	return {
		"original": original,
		"original_digest_verified": bool(final and records.text_digest(final["content"]) == final["content_digest"]),
		"supplements": json.loads(json.dumps(view["supplements"], default=str)),
		"history": json.loads(json.dumps([m for m in view["minutes"] if m is not final], default=str)),
	}
