# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The durable Tender-level Award authority record (AWD-CHG-001 v0.9 §5.11,
§7 GetAwardAuthorityStatus, §7.2).

One row per Tender, registered by Award's Tender-publication integration
(`kt_tender_publication_registrars`, called in the publication transaction)
before any Award case exists. It is the only proof that no notice was issued
when there is no case: "no case found" proves nothing. It owns the Tender's
notification status (Not issued / Issue in progress / Issued / Unknown) and its
cancellation stamp, so the pre-notification cancellation and the first notice
serialise on one row. It creates no Award case, no opinion task and no bidder
notice.

Rules enforced here:

- registration is insert-if-absent: a replayed publication never resets a
  recorded notice or cancellation;
- the Tender-level status only moves forward. Once any notice was issued it is
  Issued for good (each batch keeps its own status); Unknown goes back to Not
  issued only with evidence that nothing was sent, never by timeout;
- the record carries its own evidence digest; one that fails it, or that
  disagrees with its case, is not believed (the caller answers Unknown);
- the case's `notification_status` is a projection of this record, written in
  the same transaction.

Lock order, on every path that takes more than one: Tender → this record →
Award case."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr, get_datetime

from kentender_procurement.award.services import clock, records
from kentender_procurement.award.services.errors import fail

DOCTYPE = "Award Tender Authority"
NOT_ISSUED = "Not issued"
IN_PROGRESS = "Issue in progress"
ISSUED = "Issued"
UNKNOWN = "Unknown"

PUBLICATION = "Publication"
DERIVED = "Derived from case"
BACKFILL = "Backfill"
REPLAY = "Replay"

# Tender states from which "no notice can exist" follows from the lifecycle itself: an open Tender has had no evaluation, and a cancelled one was
# cancelled only through a route that refuses once any notice is issued or being issued.
PROVABLE_STATUSES = ("Published — open",)


def _now():
	return get_datetime(clock.now()).replace(microsecond=0)


def _digest(*, tender: str, tender_reference: str, source_kind: str, source_event: str, registered_at) -> str:
	return records.digest({"tender": tender, "tender_reference": cstr(tender_reference), "source_kind": source_kind, "source_event": cstr(source_event),
		"registered_at": str(get_datetime(registered_at).replace(microsecond=0)) if registered_at else ""})


def read(tender: str):
	"""The record as last committed, or None. A plain read: for a decision under the fence use `lock`."""
	if not tender or not frappe.db.exists(DOCTYPE, tender):
		return None
	return frappe.get_doc(DOCTYPE, tender)


def lock(tender: str):
	"""The record, locked, as last committed (a locking read: MariaDB runs at REPEATABLE READ, so a plain read after the lock would return this
	transaction's older snapshot — AUD-XC-108). None when there is no record."""
	if not tender or not frappe.db.exists(DOCTYPE, tender):
		return None
	return frappe.get_doc(DOCTYPE, tender, for_update=True)


def intact(row) -> bool:
	"""The record still carries the evidence it was registered with."""
	return bool(row) and cstr(row.evidence_digest) == _digest(tender=row.tender, tender_reference=row.tender_reference, source_kind=row.source_kind,
		source_event=row.source_event, registered_at=row.registered_at)


def _summary(row, *, created: bool) -> dict[str, Any]:
	return {"ok": True, "tender": row.tender, "created": created, "notification_status": row.notification_status, "cancellation_ref": cstr(row.cancellation_ref),
		"award_case": cstr(row.award_case), "record_version": cint(row.record_version), "source_kind": row.source_kind}


def register(*, tender: str, tender_reference: str = "", source_event: str = "", source_kind: str = PUBLICATION, initial_status: str = NOT_ISSUED,
		award_case: str = "", namespace: str = "") -> dict[str, Any]:
	"""RegisterTenderAuthority: insert-if-absent. An existing record is returned untouched, so receipt or replay of a publication cannot reset a
	notice or a cancellation already recorded."""
	if not tender:
		fail("AWD_STATUS_UNAVAILABLE", {"reason": "tender_required"})
	existing = frappe.db.exists(DOCTYPE, tender)
	if existing:
		return _summary(frappe.get_doc(DOCTYPE, tender), created=False)
	at = _now()
	savepoint = f"awdta_{frappe.generate_hash(length=10)}"
	frappe.db.savepoint(savepoint)
	try:
		row = records.new(DOCTYPE, tender=tender, tender_reference=cstr(tender_reference), award_case=cstr(award_case) or None, notification_status=initial_status,
			source_kind=source_kind, source_event=cstr(source_event), registered_at=at, verified_at=at, record_version=1,
			evidence_json=records.dumps({"source_kind": source_kind, "source_event": cstr(source_event), "tender_reference": cstr(tender_reference), "registered_at": str(at)}),
			evidence_digest=_digest(tender=tender, tender_reference=tender_reference, source_kind=source_kind, source_event=source_event, registered_at=at),
			fixture_namespace=cstr(namespace))
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		frappe.db.rollback(save_point=savepoint)
		frappe.clear_last_message()
		return _summary(frappe.get_doc(DOCTYPE, tender), created=False)
	frappe.db.release_savepoint(savepoint)
	return _summary(row, created=True)


def registrar(*, tender: str, tender_reference: str = "", event_key: str = "", **_ignored) -> dict[str, Any]:
	"""`kt_tender_publication_registrars`: Tenders calls this inside the transaction that publishes the Tender. The record belongs to the Tender (it
	goes with it, `clear.on_tenders_removed`), so it carries no fixture namespace of its own: an Award fixture wipe never removes it."""
	return register(tender=tender, tender_reference=tender_reference, source_event=event_key or f"TenderPublishedOpen:{tender}", source_kind=PUBLICATION)


def attach_case(*, tender: str, tender_reference: str, case: str, case_status: str = NOT_ISSUED):
	"""The Award case of this Tender now exists: link it. A Tender with no record (a world that never went through publication here) gets one
	derived from its case, which starts Not issued by construction. Takes the record's lock before the case is written."""
	register(tender=tender, tender_reference=tender_reference, source_event=f"case:{case}", source_kind=DERIVED, initial_status=case_status, award_case=case)
	row = lock(tender)
	if row is not None and cstr(row.award_case) != case:
		if row.award_case:
			fail("AWD_RECORD_CHANGED", {"reason": "another_case_is_linked", "case": cstr(row.award_case)})
		records.bump(row, award_case=case)
	return row


# ---------------------------------------------------------------- transitions


def _project(row, status: str, *, batch: str = "") -> None:
	"""The case's notification status follows this record, in the same transaction."""
	case = cstr(row.award_case) or frappe.db.get_value(records.CASE, {"tender": row.tender}, "name")
	if not case or not frappe.db.exists(records.CASE, case):
		return
	doc = frappe.get_doc(records.CASE, case)
	values = {"notification_status": status}
	if batch:
		values["current_batch"] = batch
	records.bump(doc, **values)


def set_notification(tender: str, status: str, *, token: str = "", batch: str = "", no_send_evidence: str = "") -> dict[str, Any]:
	"""Move the Tender-level notification status forward under the record's lock, and project it onto the case.

	Not issued → Issue in progress → Issued, with Unknown for an outcome that cannot be confirmed. Issued is final at Tender level (a later batch keeps
	its own status). Unknown or Issue in progress goes back to Not issued only with evidence that nothing was sent — never by timeout."""
	if status not in (NOT_ISSUED, IN_PROGRESS, ISSUED, UNKNOWN):
		fail("AWD_RECORD_CHANGED", {"reason": "unknown_status", "status": status})
	row = lock(tender)
	if row is None:
		fail("AWD_STATUS_UNAVAILABLE", {"reason": "no_tender_authority_record", "tender": tender})
	current = cstr(row.notification_status)
	if current == ISSUED:
		if status == NOT_ISSUED:
			fail("AWD_RECORD_CHANGED", {"reason": "issued_is_final", "tender": tender})
		# the Tender-level fact stays Issued; a later batch (revised notices) keeps its own status, and the case points at it
		if batch and status == IN_PROGRESS and cstr(row.current_batch) != batch:
			records.bump(row, current_batch=batch)
			_project(row, ISSUED, batch=batch)
		return {"ok": True, "changed": False, "notification_status": ISSUED}
	if status == current:
		return {"ok": True, "changed": False, "notification_status": current}
	if status == NOT_ISSUED and not cstr(no_send_evidence).strip():
		fail("AWD_RECORD_CHANGED", {"reason": "no_send_evidence_required", "from": current})
	if status == IN_PROGRESS and current == UNKNOWN:
		fail("AWD_RECORD_CHANGED", {"reason": "recover_before_issuing", "from": current})
	values: dict[str, Any] = {"notification_status": status}
	if status == IN_PROGRESS:
		values.update(issue_token=cstr(token), issue_started_at=clock.now(), current_batch=cstr(batch))
	elif status == NOT_ISSUED:
		values.update(issue_token="", issue_started_at=None)
	elif status == ISSUED:
		values.update(issue_token=cstr(token) or row.issue_token)
	records.bump(row, **values)
	_project(row, status, batch=batch)
	return {"ok": True, "changed": True, "notification_status": status, "record_version": cint(row.record_version)}


def record_cancellation(tender: str, *, cancellation_ref: str, cancelled_at=None) -> dict[str, Any]:
	"""Stamp the Tender's cancellation on its record, in the cancellation's own transaction. The same reference again changes nothing; another
	reference conflicts. Refused when a notice is issued, being issued or of unknown state (the caller's fence checked this under the same lock)."""
	row = lock(tender)
	if row is None:
		fail("AWD_STATUS_UNAVAILABLE", {"reason": "no_tender_authority_record", "tender": tender})
	if cstr(row.cancellation_ref):
		if cstr(row.cancellation_ref) != cstr(cancellation_ref):
			fail("AWD_RECORD_CHANGED", {"reason": "another_cancellation_is_recorded"})
		return {"ok": True, "changed": False, "cancellation_ref": cstr(row.cancellation_ref)}
	if cstr(row.notification_status) != NOT_ISSUED:
		fail("AWD_RECORD_CHANGED", {"reason": "notification_not_clear", "status": cstr(row.notification_status)})
	records.bump(row, cancellation_ref=cstr(cancellation_ref), cancelled_at=cancelled_at or clock.now())
	return {"ok": True, "changed": True, "cancellation_ref": cstr(cancellation_ref)}


def unlink_cases(cases: list[str]) -> int:
	"""A fixture reset removed these cases with their notices: the Tender's record no longer names them and its notification status goes back with
	the notices it described. Its cancellation stamp stays. Direct updates: this is not a business command and nothing else reads the record meanwhile."""
	count = 0
	for row in frappe.get_all(DOCTYPE, filters={"award_case": ("in", list(cases))}, pluck="name"):
		frappe.db.set_value(DOCTYPE, row, {"award_case": None, "notification_status": NOT_ISSUED, "issue_token": "", "issue_started_at": None, "current_batch": "",
			"record_version": cint(frappe.db.get_value(DOCTYPE, row, "record_version")) + 1}, update_modified=False)
		count += 1
	return count


# ---------------------------------------------------------------- repair


def backfill_cases() -> dict[str, int]:
	"""A case that predates the record gets one that copies the case, including a notice already issued."""
	made = 0
	for case in frappe.get_all(records.CASE, fields=["name", "tender", "tender_reference", "notification_status", "fixture_namespace"], limit_page_length=0):
		if frappe.db.exists(DOCTYPE, case.tender):
			continue
		register(tender=case.tender, tender_reference=case.tender_reference, source_event=f"case:{case.name}", source_kind=BACKFILL,
			initial_status=case.notification_status or UNKNOWN, award_case=case.name, namespace=cstr(case.fixture_namespace))
		made += 1
	return {"registered": made}


def backfill(facts: list[dict[str, Any]]) -> dict[str, int]:
	"""Register what the Tender's own lifecycle proves and leave the rest Unknown. An open Tender has had no evaluation and so no notice; a cancelled
	Tender was cancelled through a route that refuses once any notice is issued or in progress. A Tender past submission with no record and no case is
	not provable — absence of a case proves nothing — so it stays Unknown until the owner reconciles it."""
	registered = unknown = 0
	for fact in facts:
		tender = cstr(fact.get("tender"))
		if not tender or frappe.db.exists(DOCTYPE, tender):
			continue
		if fact.get("cancelled") or cstr(fact.get("overall_status")) in PROVABLE_STATUSES:
			register(tender=tender, tender_reference=cstr(fact.get("tender_reference")), source_event=f"backfill:{cstr(fact.get('overall_status'))}", source_kind=BACKFILL)
			registered += 1
		else:
			unknown += 1
	return {"registered": registered, "left_unknown": unknown}
