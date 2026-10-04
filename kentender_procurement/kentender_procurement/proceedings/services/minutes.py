# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""FreezeMinutes and SupersedeFrozenMinutes (PRC-CHG-001 v0.9 §4, §5, §7, §7.1).

A frozen version is exact content plus its digest and the list of targets
each named member must attest. Freeze reconciles against the owner's own
event set: every owner fact must be referenced and none invented. Before
finalization a correction makes a new version with a reason; earlier proofs
stay in history but no longer satisfy it (PRC-N06). After finalization the
only route is a supplement."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.proceedings.services import clock, owners, records
from kentender_procurement.proceedings.services.errors import fail

VERSION = "Proceeding Minutes Version"
TARGET_TYPES = ("Tender page", "Price location", "Change location", "Minutes page", "Final minutes page")


def _validate(doc, *, content: str, event_ids: list[str], targets: list[dict[str, Any]]) -> None:
	if not cstr(content).strip():
		fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"content": "The opening record has no content."}})
	known = set(frappe.get_all(records.EVENT, filters={"proceeding": doc.name}, pluck="event_id"))
	unknown = sorted(set(event_ids) - known)
	if unknown:
		fail("PRC_EVIDENCE_INCOMPLETE", {"unknown_events": unknown})
	owner_facts = frappe.get_all(records.EVENT, filters={"proceeding": doc.name, "source": "Owner"}, pluck="event_id")
	missing = sorted(set(owner_facts) - set(event_ids))
	if missing:
		fail("PRC_EVIDENCE_INCOMPLETE", {"missing_events": missing})
	if not targets:
		fail("PRC_EVIDENCE_INCOMPLETE", {"missing": ["targets"]})
	roster = {m.member_user for m in doc.members}
	seen = set()
	for target in targets:
		absent = [f for f in ("target_id", "target_type", "target_reference", "target_digest", "required_member") if not cstr(target.get(f)).strip()]
		if absent or target.get("target_type") not in TARGET_TYPES:
			fail("PRC_EVIDENCE_INCOMPLETE", {"target": cstr(target.get("target_id")), "missing": absent or ["target_type"]})
		pair = (target["target_id"], target["required_member"])
		if pair in seen:
			fail("PRC_EVIDENCE_INCOMPLETE", {"duplicate_target": target["target_id"]})
		seen.add(pair)
		if target["required_member"] not in roster:
			fail("PRC_MEMBER_REQUIRED", {"target": target["target_id"]})


def _freeze(doc, *, actor: str, content: str, page_count: int, register_reference: str, register_digest: str, event_ids: list[str], targets: list[dict[str, Any]],
		supersedes: str = "", reason: str = "") -> dict[str, Any]:
	number = frappe.db.count(VERSION, {"proceeding": doc.name}) + 1
	version = frappe.get_doc({
		"doctype": VERSION, "minutes_version_id": f"{doc.name}-M{number:02d}", "proceeding": doc.name, "version_number": number, "content": content,
		"content_digest": records.text_digest(content), "page_count": cint(page_count), "register_reference": register_reference, "register_digest": register_digest,
		"event_ids_json": json.dumps(sorted(event_ids)), "authored_by": owners.user_or_none(actor), "frozen_at": clock.now(), "frozen_by": owners.user_or_none(actor),
		"state": "Frozen", "supersedes_version": supersedes, "supersede_reason": reason,
	})
	for target in targets:
		version.append("targets", {f: target.get(f) for f in ("target_id", "target_type", "target_reference", "page_number", "target_digest", "required_member",
			"roster_segment")})
	records.insert(version)
	return {"minutes_version": version.name, "version_number": number, "content_digest": version.content_digest,
		"targets": [{f: t.get(f) for f in ("target_id", "target_type", "page_number", "target_digest", "required_member", "roster_segment")} for t in version.targets]}


def freeze_minutes(*, owner_type: str, owner_id: str, expected_version: int, content: str, page_count: int, register_reference: str, register_digest: str,
		event_ids: list[str], targets: list[dict[str, Any]], idempotency_key: str, actor: str) -> dict[str, Any]:
	payload = {"expected_version": expected_version, "content_digest": records.text_digest(content), "page_count": page_count, "register_reference": register_reference,
		"register_digest": register_digest, "event_ids": sorted(event_ids), "targets": targets}

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Session ended",))
		_validate(doc, content=content, event_ids=event_ids, targets=targets)
		frozen = _freeze(doc, actor=actor, content=content, page_count=page_count, register_reference=register_reference, register_digest=register_digest,
			event_ids=event_ids, targets=targets)
		event_id = records.event(doc, "MinutesFrozen", source="System", actor=actor, owner_reference=frozen["minutes_version"], payload={"digest": frozen["content_digest"]})
		records.bump(doc, state="Awaiting attestations", current_minutes_version=frozen["version_number"])
		return records.summary(doc, event_id, **frozen)

	return records.command("FreezeMinutes", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="recorder",
		payload=payload, body=body)


def supersede_minutes(*, owner_type: str, owner_id: str, expected_version: int, reason: str, content: str, page_count: int, register_reference: str,
		register_digest: str, event_ids: list[str], targets: list[dict[str, Any]], idempotency_key: str, actor: str) -> dict[str, Any]:
	payload = {"expected_version": expected_version, "reason": reason, "content_digest": records.text_digest(content), "page_count": page_count,
		"register_reference": register_reference, "register_digest": register_digest, "event_ids": sorted(event_ids), "targets": targets}

	def body() -> dict[str, Any]:
		doc = records.lock(owner_type, owner_id)
		records.check_version(doc, expected_version)
		records.require_state(doc, ("Awaiting attestations",))
		if not cstr(reason).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"reason": "Give the reason for correcting the opening record."}})
		_validate(doc, content=content, event_ids=event_ids, targets=targets)
		previous = frappe.db.get_value(VERSION, {"proceeding": doc.name, "version_number": cint(doc.current_minutes_version)}, "name")
		prior = frappe.get_doc(VERSION, previous)
		prior.state = "Superseded"
		records.save(prior)
		for name in frappe.get_all("Proceeding Attestation", filters={"proceeding": doc.name, "satisfies_current": 1}, pluck="name"):
			proof = frappe.get_doc("Proceeding Attestation", name)
			proof.satisfies_current = 0
			records.save(proof)
		frozen = _freeze(doc, actor=actor, content=content, page_count=page_count, register_reference=register_reference, register_digest=register_digest,
			event_ids=event_ids, targets=targets, supersedes=previous, reason=cstr(reason).strip())
		event_id = records.event(doc, "MinutesSuperseded", source="System", actor=actor, owner_reference=frozen["minutes_version"], note=cstr(reason).strip(),
			payload={"digest": frozen["content_digest"], "supersedes": previous})
		records.bump(doc, current_minutes_version=frozen["version_number"])
		return records.summary(doc, event_id, **frozen)

	return records.command("SupersedeFrozenMinutes", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="recorder",
		payload=payload, body=body)
