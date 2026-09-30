# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Owner-defined record versions of a multi-session proceeding: the
evaluation report and the verification report (EVL-CHG-001 v0.4 §5.4–§5.6,
§6 "Report frozen / changed / personal signature", plan D4).

A frozen version is exact content, its digest and the targets each named
member must prove personally. One frozen version of a kind is current at a
time; a change supersedes it with a reason, and earlier proofs stay as
history but satisfy nothing current (stale proofs cannot satisfy the current
report). Completion finalizes that version once every target has a verified
proof; the case itself stays open for later corrections, which are appended
and never rewrite the finalized version. Cancellation aborts the case and
keeps the partial record."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.proceedings.services import clock, owners, profiles, records, sessions, signing
from kentender_procurement.proceedings.services.errors import fail, unverified

VERSION = "Proceeding Minutes Version"
ATTESTATION = "Proceeding Attestation"
SUPPLEMENT = "Proceeding Supplement"
PREFIX = {"Evaluation report": "R", "Verification report": "V"}
TARGET_FIELDS = ("target_id", "target_type", "target_reference", "page_number", "target_digest", "required_member", "roster_segment")


def _kinds(doc) -> dict[str, tuple[str, ...]]:
	return profiles.profile(doc.proceeding_type)["record_kinds"]


def current(proceeding: str, record_kind: str, states=("Frozen",)) -> str | None:
	return frappe.db.get_value(VERSION, {"proceeding": proceeding, "record_kind": record_kind, "state": ("in", list(states))}, "name",
		order_by="version_number desc")


def _validate(doc, record_kind: str, content: str, targets: list[dict[str, Any]]) -> None:
	kinds = _kinds(doc)
	if record_kind not in kinds or record_kind not in PREFIX:
		fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"record_kind": "Choose a record kind of this proceeding."}})
	if not cstr(content).strip():
		fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"content": "The record has no content."}})
	if not targets:
		fail("PRC_EVIDENCE_INCOMPLETE", {"missing": ["targets"]})
	roster = {m.member_user for m in doc.members if cint(m.active)}
	seen = set()
	for target in targets:
		absent = [f for f in ("target_id", "target_type", "target_reference", "target_digest", "required_member") if not cstr(target.get(f)).strip()]
		if absent or target.get("target_type") not in kinds[record_kind]:
			fail("PRC_EVIDENCE_INCOMPLETE", {"target": cstr(target.get("target_id")), "missing": absent or ["target_type"]})
		pair = (target["target_id"], target["required_member"])
		if pair in seen:
			fail("PRC_EVIDENCE_INCOMPLETE", {"duplicate_target": target["target_id"]})
		seen.add(pair)
		if target["required_member"] not in roster:
			fail("PRC_MEMBER_REQUIRED", {"target": target["target_id"]})


def freeze_record(*, owner_type: str, owner_id: str, expected_version: int, record_kind: str, owner_reference: str, content: str,
		targets: list[dict[str, Any]], idempotency_key: str, actor: str) -> dict[str, Any]:
	"""FreezeEvaluationReport (and the verification report): one exact version."""
	payload = {"expected_version": expected_version, "record_kind": record_kind, "owner_reference": owner_reference, "content_digest": records.text_digest(content),
		"targets": targets}

	def body() -> dict[str, Any]:
		doc = sessions._open(owner_type, owner_id, expected_version)
		_validate(doc, record_kind, content, targets)
		if current(doc.name, record_kind):
			fail("PRC_VERSION_CONFLICT", {"reason": "frozen_version_exists", "record_kind": record_kind})
		number = frappe.db.count(VERSION, {"proceeding": doc.name, "record_kind": record_kind}) + 1
		version = frappe.get_doc({
			"doctype": VERSION, "minutes_version_id": f"{doc.name}-{PREFIX[record_kind]}{number:02d}", "proceeding": doc.name, "version_number": number,
			"record_kind": record_kind, "owner_reference": cstr(owner_reference), "content": content, "content_digest": records.text_digest(content),
			"page_count": 0, "event_ids_json": "[]", "authored_by": owners.user_or_none(actor), "frozen_at": clock.now(), "frozen_by": owners.user_or_none(actor),
			"state": "Frozen",
		})
		for target in targets:
			version.append("targets", {f: target.get(f) for f in TARGET_FIELDS})
		records.insert(version)
		event_id = records.event(doc, "RecordFrozen", source="System", actor=actor, owner_reference=version.name,
			payload={"kind": record_kind, "digest": version.content_digest, "owner_reference": cstr(owner_reference)})
		records.bump(doc)
		return records.summary(doc, event_id, record_version=version.name, version_number=number, content_digest=version.content_digest,
			targets=[{f: t.get(f) for f in TARGET_FIELDS} for t in version.targets])

	return records.command("FreezeRecord", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="recorder",
		payload=payload, body=body)


def _frozen(doc, record_version: str):
	row = frappe.db.get_value(VERSION, record_version, ["proceeding", "state", "record_kind"], as_dict=True)
	if not row or row.proceeding != doc.name:
		fail("PRC_TARGET_CHANGED", {"record_version": record_version})
	if row.state != "Frozen" or current(doc.name, row.record_kind) != record_version:
		fail("PRC_TARGET_CHANGED", {"record_version": record_version, "current": current(doc.name, row.record_kind)})
	return frappe.get_doc(VERSION, record_version)


def supersede_record(*, owner_type: str, owner_id: str, expected_version: int, record_version: str, reason: str, idempotency_key: str,
		actor: str) -> dict[str, Any]:
	"""SupersedeEvaluationReport: a concern, revision, return or source/roster
	change ends signature collection for this version (§5.5)."""

	def body() -> dict[str, Any]:
		doc = sessions._open(owner_type, owner_id, expected_version)
		if not cstr(reason).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"reason": "Give the reason for replacing this version."}})
		version = _frozen(doc, record_version)
		version.state, version.supersede_reason = "Superseded", cstr(reason).strip()
		records.save(version)
		for name in frappe.get_all(ATTESTATION, filters={"minutes_version": record_version, "satisfies_current": 1}, pluck="name"):
			proof = frappe.get_doc(ATTESTATION, name)
			proof.satisfies_current = 0
			records.save(proof)
		event_id = records.event(doc, "RecordSuperseded", source="System", actor=actor, owner_reference=record_version, note=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, event_id, record_version=record_version)

	return records.command("SupersedeRecord", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="recorder",
		payload={"expected_version": expected_version, "record_version": record_version, "reason": reason}, body=body)


def record_proof(*, owner_type: str, owner_id: str, expected_version: int, record_version: str, target_id: str, target_digest: str, action: str,
		idempotency_key: str, actor: str) -> dict[str, Any]:
	"""RecordEvaluationProof: the named member's own proof for one exact current
	target. An unverified proof is kept as evidence and satisfies nothing."""
	payload = {"expected_version": expected_version, "record_version": record_version, "target_id": target_id, "target_digest": target_digest, "action": action}

	def body() -> dict[str, Any]:
		doc = sessions._open(owner_type, owner_id, expected_version)
		version = _frozen(doc, record_version)
		target = next((t for t in version.targets if t.target_id == target_id and t.required_member == actor), None)
		if target is None:
			others = [t.required_member for t in version.targets if t.target_id == target_id]
			fail("PRC_MEMBER_REQUIRED" if others else "PRC_TARGET_CHANGED", {"target": target_id})
		if target.target_digest != target_digest:
			fail("PRC_TARGET_CHANGED", {"target": target_id})
		if action not in ("Sign", "Initial"):
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"action": "Choose sign or initial."}})
		existing = frappe.db.get_value(ATTESTATION, {"minutes_version": record_version, "target_id": target_id, "member_user": actor, "satisfies_current": 1},
			"attestation_id")
		if existing:
			return records.summary(doc, "", attestation_id=existing, verification_result=signing.VERIFIED)
		number = frappe.db.count(ATTESTATION, {"proceeding": doc.name}) + 1
		attestation_id = f"{doc.name}-P{number:04d}"
		proof = signing.attest(member=actor, target_id=target_id, target_digest=target_digest, minutes_version=record_version, action=action,
			correlation_id=attestation_id)
		verified = proof["outcome"] == signing.VERIFIED
		records.insert(frappe.get_doc({
			"doctype": ATTESTATION, "attestation_id": attestation_id, "proceeding": doc.name, "minutes_version": record_version, "target_id": target_id,
			"target_digest": target_digest, "member_user": actor, "action": action, "method": proof.get("method") or "Unavailable", "recorded_at": clock.now(),
			"proof_reference": proof.get("proof_reference") or "", "correlation_id": proof["correlation_id"], "verification_result": proof["outcome"],
			"satisfies_current": 1 if verified else 0,
		}))
		event_id = records.event(doc, "TargetAttested" if verified else "AttestationNotVerified", source="Member", actor=actor, owner_reference=attestation_id,
			payload={"record_version": record_version, "target": target_id, "digest": target_digest, "outcome": proof["outcome"]})
		records.bump(doc)
		if not verified:
			return unverified({"proceeding": doc.name, "record_version": cint(doc.record_version), "attestation_id": attestation_id,
				"verification_result": proof["outcome"]})
		return records.summary(doc, event_id, attestation_id=attestation_id, verification_result=proof["outcome"])

	return records.command("RecordProof", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="member",
		payload=payload, body=body)


def missing_proofs(record_version: str) -> list[dict[str, Any]]:
	version = frappe.get_doc(VERSION, record_version)
	satisfied = {(p.target_id, p.member_user, p.target_digest) for p in frappe.get_all(ATTESTATION, filters={
		"minutes_version": record_version, "satisfies_current": 1, "verification_result": signing.VERIFIED}, fields=["target_id", "member_user", "target_digest"])}
	return [{"target_id": t.target_id, "required_member": t.required_member} for t in version.targets
		if (t.target_id, t.required_member, t.target_digest) not in satisfied]


def complete_record(*, owner_type: str, owner_id: str, expected_version: int, record_version: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""CompleteEvaluationRecord: the owner's internal transition after the last
	verified proof; refused with every missing item otherwise."""

	def body() -> dict[str, Any]:
		doc = sessions._open(owner_type, owner_id, expected_version)
		version = _frozen(doc, record_version)
		missing = missing_proofs(record_version)
		if missing:
			fail("PRC_EVIDENCE_INCOMPLETE", {"missing": missing})
		version.state = "Finalized"
		records.save(version)
		event_id = records.event(doc, "RecordCompleted", source="System", actor=actor, owner_reference=record_version, payload={"digest": version.content_digest})
		records.bump(doc)
		return records.summary(doc, event_id, record_version=record_version)

	return records.command("CompleteRecord", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "record_version": record_version}, body=body)


def append_correction(*, owner_type: str, owner_id: str, expected_version: int, record_version: str, kind: str, correct_information: str, reason: str,
		idempotency_key: str, actor: str, evidence_reference: str = "") -> dict[str, Any]:
	"""AppendEvaluationCorrection: a linked note against a finalized version;
	the finalized content never changes (§5.6)."""
	payload = {"expected_version": expected_version, "record_version": record_version, "kind": kind, "correct_information": correct_information, "reason": reason,
		"evidence_reference": evidence_reference}

	def body() -> dict[str, Any]:
		doc = sessions._open(owner_type, owner_id, expected_version)
		row = frappe.db.get_value(VERSION, record_version, ["proceeding", "state"], as_dict=True)
		if not row or row.proceeding != doc.name or row.state != "Finalized":
			fail("PRC_VERSION_CONFLICT", {"reason": "not_finalized", "record_version": record_version})
		fields = {f: "Required." for f, v in (("kind", kind), ("correct_information", correct_information), ("reason", reason)) if not cstr(v).strip()}
		if fields:
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": fields})
		number = frappe.db.count(SUPPLEMENT, {"proceeding": doc.name}) + 1
		supplement_id = f"{doc.name}-C{number:02d}"
		records.insert(frappe.get_doc({
			"doctype": SUPPLEMENT, "supplement_id": supplement_id, "proceeding": doc.name, "original_version": record_version, "kind": cstr(kind).strip(),
			"correct_information": cstr(correct_information).strip(), "reason": cstr(reason).strip(), "evidence_reference": evidence_reference,
			"author": owners.user_or_none(actor), "recorded_at": clock.now(),
		}))
		event_id = records.event(doc, "CorrectionAppended", source="Recorder", actor=actor, owner_reference=supplement_id, note=cstr(reason).strip())
		records.bump(doc)
		return records.summary(doc, event_id, supplement_id=supplement_id)

	return records.command("AppendCorrection", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="recorder",
		payload=payload, body=body)


def abort(*, owner_type: str, owner_id: str, expected_version: int, cancellation_reference: str, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""Authoritative cancellation: the case ends with its partial record kept;
	an active session ends, pending signature collection stops (§5.7)."""

	def body() -> dict[str, Any]:
		doc = sessions._open(owner_type, owner_id, expected_version)
		if not cstr(cancellation_reference).strip():
			fail("PRC_EVIDENCE_INCOMPLETE", {"fields": {"cancellation_reference": "The authoritative cancellation is required."}})
		session = sessions.active_session(doc.name)
		if session:
			sessions._close(doc, session, actor=actor, note="Cancelled")
		for name in frappe.get_all(VERSION, filters={"proceeding": doc.name, "state": "Frozen"}, pluck="name"):
			version = frappe.get_doc(VERSION, name)
			version.state, version.supersede_reason = "Superseded", "Cancelled"
			records.save(version)
		last = frappe.db.get_value(records.EVENT, {"proceeding": doc.name}, "event_id", order_by="sequence desc")
		event_id = records.event(doc, "ProceedingAborted", source="System", actor=actor, owner_reference=cstr(cancellation_reference), payload={"last_event": last})
		records.bump(doc, state="Aborted after start", ceased_at=clock.now(), cancellation_reference=cancellation_reference, current_session="")
		return records.summary(doc, event_id, last_event=last)

	return records.command("AbortProceeding", owner_type=owner_type, owner_id=owner_id, idempotency_key=idempotency_key, actor=actor, capacity="owner",
		payload={"expected_version": expected_version, "cancellation_reference": cancellation_reference}, body=body)


def read(*, owner_type: str, owner_id: str, user: str) -> dict[str, Any]:
	"""Owner-scoped read of the case: sessions with their attendance, events,
	record versions with targets and proofs, corrections. Anyone the owner does
	not authorise, technical users included, gets the protected Not found."""
	owners.require(owner_type, owner_id, user, "reader")
	name = records.find(owner_type, owner_id)
	if not name:
		fail("PRC_OWNER_UNAVAILABLE")
	doc = frappe.get_doc(records.PROCEEDING, name)
	out_sessions = []
	for row in frappe.get_all(sessions.SESSION, filters={"proceeding": name}, fields=["session_id", "session_number", "state", "subject", "started_by",
			"actual_start", "ended_by", "actual_end", "end_note"], order_by="session_number asc"):
		row["attendance"] = frappe.get_all(sessions.ATTENDANCE, filters={"proceeding": name, "session": row.session_id}, fields=["attendance_id", "person_name",
			"user", "capacity", "movement", "occurred_at"], order_by="occurred_at asc, creation asc")
		out_sessions.append(row)
	versions = []
	for vname in frappe.get_all(VERSION, filters={"proceeding": name}, order_by="creation asc", pluck="name"):
		version = frappe.get_doc(VERSION, vname)
		versions.append({
			"record_version": version.name, "record_kind": version.record_kind, "version_number": version.version_number, "state": version.state,
			"owner_reference": version.owner_reference, "content_digest": version.content_digest, "frozen_at": version.frozen_at, "supersede_reason": version.supersede_reason,
			"targets": [{f: t.get(f) for f in TARGET_FIELDS} for t in version.targets],
			"proofs": frappe.get_all(ATTESTATION, filters={"minutes_version": version.name}, fields=["attestation_id", "target_id", "member_user", "action", "recorded_at",
				"verification_result", "satisfies_current", "method"], order_by="recorded_at asc"),
		})
	return {
		"proceeding": name, "state": doc.state, "record_version": cint(doc.record_version), "title": doc.title,
		"members": [{f: m.get(f) for f in ("member_user", "full_name", "designation", "committee_capacity", "appointment_reference", "roster_segment", "active")}
			for m in doc.members],
		"sessions": out_sessions,
		"events": frappe.get_all(records.EVENT, filters={"proceeding": name}, fields=["event_id", "sequence", "event_type", "recorded_at", "actor", "source",
			"owner_event_id", "owner_reference", "note", "session", "linked_event"], order_by="sequence asc"),
		"records": versions,
		"corrections": frappe.get_all(SUPPLEMENT, filters={"proceeding": name}, fields=["supplement_id", "original_version", "kind", "correct_information", "reason",
			"author", "recorded_at"], order_by="recorded_at asc"),
		"current_record": {kind: current(name, kind, ("Frozen", "Finalized")) for kind in _kinds(doc)},
	}


def export(*, owner_type: str, owner_id: str, user: str) -> dict[str, Any]:
	"""Scoped export: the whole case with each version independently checkable."""
	view = read(owner_type=owner_type, owner_id=owner_id, user=user)
	for version in view["records"]:
		content = frappe.db.get_value(VERSION, version["record_version"], "content")
		version["content"] = content
		version["digest_verified"] = records.text_digest(content) == version["content_digest"]
	return json.loads(json.dumps(view, default=str))
