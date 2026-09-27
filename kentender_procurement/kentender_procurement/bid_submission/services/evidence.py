# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid evidence (BDS-CHG-001 v0.8 §4.7, §5.5 and §7.2 `UploadBidEvidence`,
`LinkAccountEvidenceToBid`; plan D16).

Every file proves one published evidence requirement of this bid. It is
stored as a private File attached to its Bid Evidence row and checked by
kentender_core file_integrity: type, size and readability first, then the
registered scanner. A wrong, oversize, unreadable or infected file is
reported at once and nothing is kept. A file is usable (Accepted) only with a
clean scanner verdict; where no scanner answers it stays Pending and never
counts. Reusing Account evidence copies the exact bytes into the bid (the
digest must match the Account's) and records the source; later Account
changes never reach the bid. Removing a file keeps it in the bid's history.

Each change of a requirement's accepted files advances the Draft version and
is kept with the prior and new file lists."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import bid_context, clock, records, save, supplier_gateway
from kentender_procurement.bid_submission.services.errors import MESSAGES, fail, field_errors

EVIDENCE = "Bid Evidence"


class _Rejected(Exception):
	pass


def _reject(message: str) -> None:
	raise _Rejected(message)


def _field(ctx, handle: str):
	field = ctx.model.by_handle(cstr(handle))
	if not field or field.kind != "evidence" or field.task_key == "review":
		fail("BDS_UNKNOWN_RESPONSE")
	from kentender_procurement.bid_submission.services import validation

	if not validation.rule_holds(field.visibility_rule, ctx.group_values(field)):
		fail("BDS_UNKNOWN_RESPONSE")
	return field


def _accepted(ctx, key: str) -> list[str]:
	return [e["id"] for e in ctx.evidence.get(key, []) if e["scan_status"] == "Accepted"]


def _commit_change(ctx, field, *, before: list[str], actor: str, at, event: str, payload: dict) -> dict[str, Any]:
	ws = ctx.workspace
	ctx.evidence = bid_context.evidence_of(ws.name)
	after = _accepted(ctx, field.key)
	version = int(ws.current_draft_version or 0) + 1
	records.insert(frappe.get_doc({
		"doctype": "Bid Draft Change", "bid_workspace": ws.name, "draft_version": version, "section_key": field.task_key, "response_key": field.key,
		"change_kind": "Saved", "prior_value": json.dumps(before), "new_value": json.dumps(after), "actor": actor, "changed_at": at,
	}))
	status = save.refresh_derived(ctx)
	records.bump(ws, current_draft_version=version, last_saved_by=actor, last_saved_at=at, **save._status_values(ws, status, at))
	records.emit(event, tender=ws.tender, arrangement=ws.bidder_arrangement, workspace=ws.name, organisation=ws.lead_organisation, actor=actor, at=at, payload=payload)
	return {"draft_version": version, "record_version": int(ws.record_version), "status": status}


def _store(ctx, field, *, filename: str, content: bytes, actor: str, at, source: str = "", expected_digest: str = "") -> tuple[Any, dict]:
	"""Create the row and its private file, then check it. Raises _Rejected."""
	from kentender_core.services import file_integrity

	row = records.insert(frappe.get_doc({
		"doctype": EVIDENCE, "bid_workspace": ctx.workspace.name, "draft_version": int(ctx.workspace.current_draft_version or 0) + 1, "evidence_requirement": field.key,
		"original_filename": cstr(filename).strip().split("/")[-1].split("\\")[-1][:140], "scan_status": "Pending", "source_evidence": source, "status": "Current",
		"uploaded_by": actor, "uploaded_at": at,
	}))
	# A File created with its content keeps the exact bytes; file_manager.save_file
	# re-reads what it wrote as text and rewrites it (a small PDF grows).
	stored = frappe.get_doc({"doctype": "File", "file_name": row.original_filename, "attached_to_doctype": EVIDENCE, "attached_to_name": row.name, "is_private": 1, "content": content}).insert(ignore_permissions=True)
	try:
		checked = file_integrity.check_file(stored.name, fail=_reject)
		if expected_digest and checked["digest"] != expected_digest:
			_reject("The copy does not match the account's file.")
	except _Rejected:
		# the savepoint removes the rows; the stored bytes go with the File
		frappe.delete_doc("File", stored.name, force=True, ignore_permissions=True)
		raise
	verdict = cstr(checked["check_result"])
	row.update({
		"file": stored.name, "file_digest": checked["digest"], "media_type": checked["media_type"], "size_bytes": int(checked["size"]), "scan_result": verdict[:140],
		"scan_status": "Accepted" if verdict.lower().startswith("clean") else "Pending",
	})
	records.save(row)
	return row, checked


def upload_bid_evidence(*, bid_reference: str, handle: str, filename: str, content: bytes, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	import hashlib

	payload = {"bid_reference": cstr(bid_reference).strip(), "handle": cstr(handle), "filename": cstr(filename), "digest": hashlib.sha256(content or b"").hexdigest(), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "UploadBidEvidence", payload, lambda: _add(actor=actor, bid_reference=payload["bid_reference"], handle=handle, filename=filename, content=content, expected_record_version=expected_record_version, organisation=payload["organisation"]), actor=actor, organisation=payload["organisation"])


def link_account_evidence_to_bid(*, bid_reference: str, handle: str, account_evidence_id: str, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "handle": cstr(handle), "account_evidence_id": cstr(account_evidence_id).strip(), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "LinkAccountEvidenceToBid", payload, lambda: _add(actor=actor, bid_reference=payload["bid_reference"], handle=handle, account_evidence_id=payload["account_evidence_id"], expected_record_version=expected_record_version, organisation=payload["organisation"]), actor=actor, organisation=payload["organisation"])


def _add(*, actor: str, bid_reference: str, handle: str, expected_record_version, organisation: str, filename: str = "", content: bytes = b"", account_evidence_id: str = "") -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	save.require_open(ctx)
	records.check_version(ctx.workspace, expected_record_version)
	from kentender_procurement.bid_submission.services import addendum

	refreshed = addendum.refresh(ctx, actor=actor, at=at)
	if refreshed:
		return refreshed
	field = _field(ctx, handle)
	maximum = int((field.evidence_rule or {}).get("maximum") or field.validation_parameters.get("maximum") or 0)
	current = [e for e in ctx.evidence.get(field.key, []) if e["scan_status"] != "Rejected"]
	if maximum and len(current) >= maximum:
		return field_errors({field.handle: f"This requirement takes at most {maximum} file{'s' if maximum != 1 else ''}. Remove one before adding another."})
	expected = ""
	if account_evidence_id:
		source = supplier_gateway.account_evidence(organisation_id=ctx.workspace.lead_organisation)
		row = next((e for e in source if e.get("evidence_id") == account_evidence_id and e.get("status") == "Available"), None)
		copy = supplier_gateway.evidence_file(organisation_id=ctx.workspace.lead_organisation, evidence_id=account_evidence_id) if row else None
		if not copy:
			return field_errors({field.handle: "Choose an available file from the supplier account."})
		filename, content, expected = copy["file_name"], copy["content"], copy["digest"]
	before = _accepted(ctx, field.key)
	try:
		with records.atomic("add-bid-evidence"):
			row, _checked = _store(ctx, field, filename=filename, content=content, actor=actor, at=at, source=account_evidence_id, expected_digest=expected)
			change = _commit_change(ctx, field, before=before, actor=actor, at=at, event="BidEvidenceAdded", payload={"evidence": row.name, "scan_status": row.scan_status, "from_account": bool(account_evidence_id)})
	except _Rejected as rejected:
		return {"ok": False, "code": "BDS_EVIDENCE_REJECTED", "message": MESSAGES["BDS_EVIDENCE_REJECTED"], "errors": {field.handle: str(rejected)}}
	return {"ok": True, "evidence": row.name, "scan_status": row.scan_status, **change}


def remove_bid_evidence(*, bid_reference: str, evidence_id: str, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "evidence_id": cstr(evidence_id).strip(), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}

	def run() -> dict[str, Any]:
		at = clock.now()
		ctx = bid_context.load(payload["bid_reference"], actor=actor, organisation=payload["organisation"], at=at)
		save.require_open(ctx)
		records.check_version(ctx.workspace, expected_record_version)
		from kentender_procurement.bid_submission.services import addendum

		refreshed = addendum.refresh(ctx, actor=actor, at=at)
		if refreshed:
			return refreshed
		row = frappe.db.get_value(EVIDENCE, {"name": payload["evidence_id"], "bid_workspace": ctx.workspace.name, "status": "Current"}, ["name", "evidence_requirement"], as_dict=True)
		field = ctx.model.by_key(row.evidence_requirement) if row else None
		if not field:
			fail("BDS_UNKNOWN_RESPONSE")
		before = _accepted(ctx, field.key)
		with records.atomic("remove-bid-evidence"):
			records.save(frappe.get_doc(EVIDENCE, row.name).update({"status": "Removed", "removed_by": actor, "removed_at": at}))
			change = _commit_change(ctx, field, before=before, actor=actor, at=at, event="BidEvidenceRemoved", payload={"evidence": row.name})
		return {"ok": True, **change}

	return records.idempotent(idempotency_key, "RemoveBidEvidence", payload, run, actor=actor, organisation=payload["organisation"])


def get_bid_evidence_file(*, bid_reference: str, evidence_id: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""The bid's own file, for its own preparers only; Not found otherwise."""
	from kentender_core.services.file_integrity import read_bytes

	actor = authz.require_person(cstr(user or frappe.session.user))
	ws, _assignment = bid_context.workspace_for(bid_reference, actor=actor, organisation=organisation, at=clock.now())
	row = frappe.db.get_value(EVIDENCE, {"name": cstr(evidence_id), "bid_workspace": ws.name}, ["file", "original_filename", "file_digest"], as_dict=True)
	if not row or not row.file:
		raise frappe.DoesNotExistError("This file is unavailable.")
	return {"file_name": row.original_filename, "content": read_bytes(row.file), "digest": row.file_digest}
