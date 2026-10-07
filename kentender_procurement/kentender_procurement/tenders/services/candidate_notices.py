# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §4.9A / §7.4 — candidate notices (plan W3).

`freeze()` runs in the same transaction as the authoritative notice-bearing
decision (a general or direct clarification answer, an addendum becoming
Issued — which also carries any deadline change — or a cancellation): it
resolves the authoritative Active candidate audience at that instant from
the Bid Submission owner (`candidate_gateway`), snapshots each verified
mandatory-notice destination, and writes one `Queued` dispatch per
candidate. Dispatch and retry are asynchronous (`DispatchCandidateNotice`,
`RetryFailedCandidateNotice`): the scheduler sweeps Queued dispatches.

Delivery evidence is append-only per attempt. `Sent` (a provider accepted
the message) is never shown as `Delivered` without provider evidence, and a
failure never retracts an issued addendum, changes a deadline, reopens a
cancellation or fabricates receipt.

Transports are registered on the `kt_candidate_notice_transports` hook (the
last one wins). The default transport queues a Frappe email and can only
ever record `Sent`. A transport is a callable `(notice_row) -> dict` with
`result` (`Sent` / `Delivered` / `Failed`), `provider_reference` and
`failure_reason`.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.tenders.services import candidate_gateway, clock, digest, draft_commands, envelope, events
from kentender_procurement.tenders.services import tender_authorization as authz
from kentender_procurement.tenders.services.errors import fail
from kentender_procurement.tenders.services.tender_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION, ROLE_PROCUREMENT_OFFICER

DOCTYPE = "Tender Candidate Notice"
HOOK = "kt_candidate_notice_transports"
TYPES = ("Clarification response", "Addendum issued", "Deadline changed", "Tender cancelled")
SUBJECT_LINES = {
	"Clarification response": "Clarification answer — {ref}",
	"Addendum issued": "Addendum issued — {ref}",
	"Deadline changed": "Submission deadline changed — {ref}",
	"Tender cancelled": "Tender cancelled — {ref}",
}


# --------------------------------------------------------------------------
# transports
# --------------------------------------------------------------------------


def email_transport(notice) -> dict[str, Any]:
	"""Default: queue an email. The queue accepting it is `Sent`, never
	`Delivered` (no provider receipt exists)."""
	try:
		reference = cstr(frappe.db.get_value("Tender", notice.tender, "tender_reference"))
		frappe.sendmail(
			recipients=[cstr(notice.destination_snapshot)], subject=SUBJECT_LINES[notice.notice_type].format(ref=reference),
			message=cstr(notice.get("_body") or SUBJECT_LINES[notice.notice_type].format(ref=reference)), delayed=True, reference_doctype=DOCTYPE, reference_name=notice.name,
		)
	except Exception as exc:  # the transport's own failure is recorded, never raised
		return {"result": "Failed", "provider_reference": "", "failure_reason": cstr(exc)[:500]}
	return {"result": "Sent", "provider_reference": f"email-queue:{notice.name}", "failure_reason": ""}


def transport():
	injected = getattr(frappe.flags, "kt_tenders_notice_transport", None)
	if injected:
		return injected
	paths = frappe.get_hooks(HOOK) or []
	return frappe.get_attr(paths[-1]) if paths else email_transport


# --------------------------------------------------------------------------
# freeze (same transaction as the authoritative decision)
# --------------------------------------------------------------------------


def freeze(root, *, notice_type: str, subject_type: str, subject_id: str, subject_digest: str, content: dict[str, Any], only: str = "") -> list[Any]:
	"""One `Queued` dispatch per Active candidate at this instant (or to the
	asking candidate only, when `only` names one). The content digest never
	includes a clarification source's identity (§16(17))."""
	if notice_type not in TYPES:
		raise ValueError(notice_type)
	at = clock.now()
	audience = candidate_gateway.candidate_audience(tender=root.name, at=at)
	if only:
		audience = [a for a in audience if a["candidate_registration_id"] == only]
	content_digest = digest.sha256_hex(content)
	rows = []
	for member in audience:
		if frappe.db.exists(DOCTYPE, {"notice_type": notice_type, "subject_id": subject_id, "candidate_registration_id": member["candidate_registration_id"]}):
			continue
		rows.append(
			envelope.insert(
				frappe.get_doc(
					{
						"doctype": DOCTYPE, "tender": root.name, "notice_type": notice_type, "subject_type": subject_type, "subject_id": subject_id, "subject_digest": subject_digest,
						"audience_frozen_at": at, "candidate_registration_id": member["candidate_registration_id"], "destination_snapshot": member["destination"],
						"destination_version": cstr(member.get("destination_version")), "content_digest": content_digest, "status": "Queued", "attempt_count": 0,
						"record_version": 0, "fixture_namespace": root.fixture_namespace,
					}
				)
			)
		)
	if rows and getattr(frappe.flags, "kt_tenders_notice_sync", False):
		# seeds and tests dispatch at once with their injected transport; the
		# site sweeps Queued dispatches on the scheduler (no RQ job per notice:
		# this bench runs no worker by default and a queue would only grow)
		for row in rows:
			dispatch(row.name)
	return rows


# --------------------------------------------------------------------------
# DispatchCandidateNotice (internal outbox worker)
# --------------------------------------------------------------------------


def dispatch(notice_name: str, *, actor: str = "") -> dict[str, Any]:
	notice = envelope.locked(DOCTYPE, notice_name)
	if notice.status in ("Delivered", "Sent") or (notice.status == "Failed" and not actor):
		return {"ok": True, "idempotent": True, "status": notice.status}
	outcome = transport()(notice)
	result = cstr(outcome.get("result"))
	if result not in ("Sent", "Delivered", "Failed"):
		result, outcome = "Failed", {"failure_reason": f"Unknown transport result {result!r}."}
	at = clock.now()
	notice.append(
		"attempts",
		{"attempt_number": int(notice.attempt_count or 0) + 1, "attempted_at": at, "transport": getattr(transport(), "__name__", "transport"), "result": result,
		 "provider_reference": cstr(outcome.get("provider_reference")), "failure_reason": cstr(outcome.get("failure_reason")), "actor": actor or "system"},
	)
	values = {"status": result, "attempt_count": int(notice.attempt_count or 0) + 1, "last_attempt_at": at, "provider_reference": cstr(outcome.get("provider_reference")), "failure_reason": cstr(outcome.get("failure_reason")) if result == "Failed" else ""}
	if result == "Delivered":
		values["delivered_at"] = at
	envelope.bump(notice, **values)
	events.emit(
		tender=notice.tender, event_type="CandidateNoticeAttempted", command="DispatchCandidateNotice", actor=actor or "Administrator", previous_status="", resulting_status=result,
		subject_type=DOCTYPE, subject_id=notice.name, payload={"notice_type": notice.notice_type, "subject_id": notice.subject_id, "attempt": values["attempt_count"], "result": result},
		fixture_namespace=notice.fixture_namespace,
	)
	return {"ok": True, "idempotent": False, "status": result}


def dispatch_pending(tender: str = "") -> int:
	"""Scheduler sweep / after-commit job: every Queued dispatch."""
	filters: dict[str, Any] = {"status": "Queued"}
	if tender:
		filters["tender"] = tender
	count = 0
	for name in frappe.get_all(DOCTYPE, filters=filters, pluck="name", order_by="creation asc", limit_page_length=500):
		dispatch(name)
		count += 1
	if count and not getattr(frappe.flags, "in_test", False):
		frappe.db.commit()
	return count


# --------------------------------------------------------------------------
# RetryFailedCandidateNotice
# --------------------------------------------------------------------------


def retry_failed_candidate_notice(*, tender: str, notice: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""Same immutable subject, recipient and content; never a new business
	notice, audience or content, and never a Tender state change (§7.4)."""
	actor = authz.actor(user)
	authz.require_any_site_role((ROLE_PROCUREMENT_OFFICER, ROLE_HEAD_OF_PROCUREMENT_FUNCTION), actor)
	payload = {"tender": tender, "notice": notice}
	replay = envelope.replay_or_none(idempotency_key, payload, command="RetryFailedCandidateNotice", actor=actor)
	if replay:
		return replay
	root, _version = draft_commands.load(tender)
	envelope.check_record_version(root, expected_record_version)
	row = frappe.db.get_value(DOCTYPE, notice, ["name", "tender", "status"], as_dict=True)
	if not row or row.tender != root.name:
		authz.not_found()
	if row.status != "Failed":
		fail("TND_STALE_VERSION", "Only a failed candidate notice can be retried.")
	outcome = dispatch(notice, actor=actor)
	envelope.bump(root)
	result = {"ok": True, "idempotent": False, "action": "retried", "tender": root.name, "record_version": root.record_version, "notice": notice, "status": outcome["status"]}
	envelope.record_command(idempotency_key=idempotency_key, command="RetryFailedCandidateNotice", payload=payload, result=result, document_type=DOCTYPE, document_name=notice, actor=actor, fixture_namespace=root.fixture_namespace)
	return result


# --------------------------------------------------------------------------
# reads
# --------------------------------------------------------------------------


def rows_for(subject_id: str, *, notice_type: str = "", protected: bool = False) -> list[dict[str, Any]]:
	filters: dict[str, Any] = {"subject_id": subject_id}
	if notice_type:
		filters["notice_type"] = notice_type
	fields = ["name", "notice_type", "candidate_registration_id", "status", "attempt_count", "last_attempt_at", "delivered_at", "failure_reason", "record_version"]
	if protected:
		fields.append("destination_snapshot")
	rows = frappe.get_all(DOCTYPE, filters=filters, fields=fields, order_by="creation asc", limit_page_length=0)
	for row in rows:
		if not protected:
			row.pop("candidate_registration_id", None)
	return rows


def delivery_summary(subject_id: str, *, notice_type: str = "") -> dict[str, Any]:
	""""1 of 1 delivered" — Queued / Sent / Delivered / Failed kept distinct."""
	rows = frappe.get_all(DOCTYPE, filters={"subject_id": subject_id, **({"notice_type": notice_type} if notice_type else {})}, pluck="status")
	counts = {status: rows.count(status) for status in ("Queued", "Sent", "Delivered", "Failed")}
	total = len(rows)
	if not total:
		label = "No registered candidates"
	elif counts["Failed"]:
		label = f"{counts['Failed']} candidate notice{'s' if counts['Failed'] != 1 else ''} failed"
	else:
		label = f"{counts['Delivered']} of {total} delivered" + (f" · {counts['Sent']} sent" if counts["Sent"] else "") + (f" · {counts['Queued']} queued" if counts["Queued"] else "")
	return {"total": total, **{k.lower(): v for k, v in counts.items()}, "label": label}
