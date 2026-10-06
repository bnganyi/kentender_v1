# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The evidence manifest of a report version (OVS-CHG-001 v0.6 §3, §7; plan
D3, D16, D18; owner approval 4 Oct 2026, "OVS6-0213: Yes"; tracker
OVS6-0213, OVS6-0214).

The frozen report names no evaluated bid version and no submitted document,
and the committee record it holds stops short of conclusions, departures,
declarations and replies. OVS v0.6 §7 requires a delivered version to expose
"its exact report version, evaluated bid versions, findings, reasons,
clarifications and dispositions, due diligence, committee record and
signatures", and "all submitted documents belonging to those evaluated bid
versions … even if not individually cited", through "immutable associations
between the delivered version and its supporting records".

The manifest is that association. It is written when the report is frozen,
beside the content (not inside it: the content digest is what every member
signs, and a delivered version cannot change without breaking its
signatures), with its own digest. For a version delivered before this
existed, `backfill` reconstructs it from the case's insert-only rows and
labels it so. An oversight reader may open a bid's detail or one document
only if the manifest of the version they are reading lists it."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_evaluation.services import people, records, sources
from kentender_procurement.bid_evaluation.services.errors import fail

SCHEMA = "kt-evl-manifest/1"
VERSION = "Evaluation Report Version"
FROZEN = "Frozen at signing"
RECONSTRUCTED = "Reconstructed after delivery"


def _size(encoded: str) -> int:
	encoded = encoded or ""
	return max(0, len(encoded) * 3 // 4 - encoded[-2:].count("="))


def _documents(doc, bid) -> list[dict[str, Any]]:
	"""Every submitted document of one opened bid, cited by a finding or not."""
	source = sources.cached_package(doc, bid)
	if source.get("outcome") != sources.VERIFIED:
		fail("EVL_SOURCE_INCOMPLETE", {"bid": bid.name, "outcome": source.get("outcome"), "reason": source.get("reason"), "step": "manifest"})
	out = []
	for evidence in (source.get("body") or {}).get("evidence") or []:
		for f in evidence.get("files") or []:
			out.append({"response_id": cstr(evidence.get("response_id")), "file_digest": cstr(f.get("file_digest")), "filename": cstr(f.get("original_filename")),
				"media_type": cstr(f.get("media_type")), "size_bytes": f.get("size_bytes") or _size(f.get("content_base64"))})
	return out


def _upto(value, as_of) -> bool:
	return as_of is None or not value or get_datetime(value) <= get_datetime(as_of)


def _committee_record(doc, as_of) -> dict[str, Any]:
	"""The items the report content does not hold: declarations (without a
	conflict's description), conclusions, session attendance with departures,
	every clarification reply and the discussion notes."""
	from kentender_procurement.bid_evaluation.services import clarification, reads

	declarations = [{"member": people.full_name(d.member_user), "choice": d.choice, "declared_at": cstr(d.declared_at), "status": d.status}
		for d in frappe.get_all("Evaluation Declaration", filters={"evaluation_case": doc.name}, fields=["member_user", "choice", "declared_at", "status"],
			order_by="declared_at asc") if _upto(d.declared_at, as_of)]
	conclusions = [{"kind": c.kind, "result": c.result, "reason": c.reason, "recorded_by": people.full_name(c.recorded_by), "recorded_at": cstr(c.recorded_at),
		"bid": c.evaluation_bid, "requirement_key": c.requirement_key, "session": c.session}
		for c in frappe.get_all("Evaluation Conclusion", filters={"evaluation_case": doc.name}, fields=["session", "kind", "result", "reason", "recorded_by",
			"recorded_at", "evaluation_bid", "requirement_key"], order_by="recorded_at asc") if _upto(c.recorded_at, as_of)]
	sessions = []
	if doc.proceeding:
		for s in frappe.get_all("Proceeding Session", filters={"proceeding": doc.proceeding}, fields=["name", "session_number", "subject", "actual_start", "actual_end"],
				order_by="session_number asc"):
			if _upto(s.actual_start, as_of):
				sessions.append({"session": s.name, "number": s.session_number, "subject": s.subject, "start": cstr(s.actual_start), "end": cstr(s.actual_end),
					"attendance": reads._attendance(doc, s.name)})
	replies = []
	for r in frappe.get_all(clarification.REPLY, filters={"clarification": ("in", frappe.get_all("Evaluation Clarification", filters={"evaluation_case": doc.name},
			pluck="name") or [""])}, fields=["clarification", "state", "body", "attachments_json", "saved_at", "received_at", "timeliness"], order_by="creation asc"):
		if _upto(r.received_at or r.saved_at, as_of):
			replies.append({"clarification": r.clarification, "state": r.state, "body": r.body, "received_at": cstr(r.received_at), "timeliness": r.timeliness,
				"attachments": [{"filename": a.get("filename"), "size": a.get("size")} for a in json.loads(r.attachments_json or "[]")]})
	notes = [n for n in reads.notes(doc)]
	return {"declarations": declarations, "conclusions": conclusions, "sessions": sessions, "clarification_replies": replies, "notes": notes}


def build(doc, *, as_of=None) -> dict[str, Any]:
	"""The manifest of this case now (or as it stood at `as_of`)."""
	bids, documents = [], {}
	for row in frappe.get_all("Evaluation Bid", filters={"evaluation_case": doc.name}, fields=["name"], order_by="entry_number asc"):
		bid = frappe.get_doc("Evaluation Bid", row.name)
		bids.append({"bid": bid.name, "bid_reference": bid.bid_reference, "entry_reference": bid.entry_reference, "entry_number": bid.entry_number,
			"envelope_id": bid.envelope_id, "receipt_reference": bid.receipt_reference, "submission_version": bid.submission_version,
			"package_digest": bid.package_digest, "tenderer_name": bid.tenderer_name, "organisation_id": bid.organisation_id})
		documents[bid.name] = _documents(doc, bid)
	intake = frappe.db.get_value("Evaluation Source Intake", doc.source_intake, ["handoff_digest", "register_digest", "opening_record_digest", "definition_digest",
		"opening_handoff"], as_dict=True) if doc.source_intake else {}
	return {"schema": SCHEMA, "evaluation": doc.name, "tender": doc.tender_reference, "bids": bids, "documents": documents, "intake": dict(intake or {}),
		"committee_record": _committee_record(doc, as_of)}


def digest(manifest: dict[str, Any]) -> str:
	return records.digest(manifest)


def values(manifest: dict[str, Any], basis: str) -> dict[str, str]:
	"""The three fields a Report Version stores."""
	return {"evidence_manifest_json": json.dumps(manifest, sort_keys=True, default=str, ensure_ascii=False), "evidence_manifest_digest": digest(manifest),
		"evidence_manifest_basis": basis}


def of(version_name: str) -> dict[str, Any] | None:
	"""The stored manifest of a version, or None if it has none, or if its stored
	text no longer matches its recorded digest."""
	row = frappe.db.get_value(VERSION, version_name, ["evidence_manifest_json", "evidence_manifest_digest"], as_dict=True)
	if not row or not row.evidence_manifest_json:
		return None
	manifest = json.loads(row.evidence_manifest_json)
	return manifest if digest(manifest) == row.evidence_manifest_digest else None


def covers(manifest: dict[str, Any] | None, bid: str, file_digest: str) -> bool:
	"""Is this document one of the bid's documents in the manifest?"""
	return bool(manifest) and any(d.get("file_digest") == file_digest for d in (manifest.get("documents") or {}).get(bid, []))


def lists_bid(manifest: dict[str, Any] | None, bid: str) -> bool:
	return bool(manifest) and any(b.get("bid") == bid for b in manifest.get("bids") or [])


def backfill(version_name: str) -> bool:
	"""Reconstruct the manifest of a version delivered before manifests existed,
	from the case's insert-only rows as they stood when it was frozen, and say so."""
	row = frappe.db.get_value(VERSION, version_name, ["evaluation_case", "frozen_at", "evidence_manifest_json"], as_dict=True)
	if not row or row.evidence_manifest_json or not row.frozen_at:
		return False
	doc = frappe.get_doc("Evaluation Case", row.evaluation_case)
	version = frappe.get_doc(VERSION, version_name)
	version.flags.kt_evl_command = True
	version.update(values(build(doc, as_of=row.frozen_at), RECONSTRUCTED))
	version.save(ignore_permissions=True)
	return True
