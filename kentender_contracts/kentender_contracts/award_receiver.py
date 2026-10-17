# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Contract Management as Award's Contracting receiver (AWD-CHG-001 v0.4 section 5.8, AWD-IF-05; CM-CHG-001 v0.8 sections 5.2, 7, 19.8; plan Phase 5, tracker CM8-501, 502, 510; FU-CM-33).

Award hands over three things and never more: the `AwardDecisionRecorded v1` event for each committed decision, the frozen Award package once every condition holds, and later restriction updates as
separate immutable records. This module is the receiver Award finds on `kt_award_contracting_receivers`. Each answer carries a durable receipt, which is what lets Award move the case to *Sent to
Contracting*; a refusal is an exception Award reads as "unavailable" and retries.

**Precedence (FU-CM-33).** Award walks the registered receivers last-registered first and the first that answers wins. Contract Management is installed after Award, so it would win everywhere, including
on a test environment whose Award tests rely on their own stand-in. So Contract Management declines when another receiver answers, unless the site names it explicitly (`kt_award_contracting_receiver`
set to `contracts`). On a live site no stand-in answers, so Contract Management does. Removing Contract Management leaves Award's delivery waiting with a named technical owner, as before it existed.

**What each receipt means.** Everything received is kept exactly as received in the **inbox**, once per Award reference (a retry returns the same receipt). A package creates one case and gives the head
of procurement one *Prepare contract* task. A decision event for a No award outcome creates no case. Events and updates may arrive before the package or after it: they wait in the inbox and are applied
when their case exists. An update never overwrites a version already out for signature; a restriction becomes a hold on signing and activation until the head of procurement records the owner's
resolution (Award sends no "lifted" message today, which is recorded as an open item for the Award owner)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_contracts.services import clock, events, formation, holds, preflight, records, work
from kentender_contracts.services.errors import ContractError, fail, invalid

HOOK = "kt_award_contracting_receivers"
PATH = "kentender_contracts.award_receiver.receiver"
SETTING = "kt_award_contracting_receiver"
CASE = "Contract Case"
INBOX = "Contract Award Inbox"


# -- who answers ------------------------------------------------------------------------------------------------------------------------
def _another_answers() -> bool:
	for path in frappe.get_hooks(HOOK) or []:
		if path == PATH:
			continue
		try:
			if frappe.get_attr(path)() is not None:
				return True
		except Exception:
			frappe.log_error(title=f"Award receiver {path} failed to load")
	return False


def answers() -> bool:
	"""Whether Contract Management is Award's receiver on this site."""
	chosen = cstr(frappe.conf.get(SETTING)).strip().lower()
	if chosen == "contracts":
		return True
	if chosen:
		return False
	return not _another_answers()


def receiver() -> "Receiver | None":
	return Receiver() if answers() else None


# -- the inbox --------------------------------------------------------------------------------------------------------------------------
def _receipt(reference: str) -> str:
	return f"CMR-{records.short(reference).upper()}"


def _keep(kind: str, payload: dict[str, Any]) -> tuple[Any, bool]:
	"""The inbox row for this Award reference, and whether it was already there."""
	reference = cstr(payload.get("reference")).strip()
	if not reference:
		raise RuntimeError("Award's payload carries no reference.")
	found = frappe.db.get_value(INBOX, {"reference": reference}, "name")
	if found:
		return frappe.get_doc(INBOX, found), True
	row = records.new(INBOX, reference=reference, kind=kind, award_case=cstr(payload.get("award_case")), outcome=cstr(payload.get("outcome")), payload_json=records.dumps(payload), receipt=_receipt(reference),
		received_at=clock.now(), state="Received", record_version=1, fixture_namespace=cstr(payload.get("fixture_namespace")))
	return row, False


def case_of(award_case: str) -> str:
	return cstr(frappe.db.get_value(CASE, {"source_kind": "KenTender award", "source_reference": award_case}, "name"))


def _apply(row) -> None:
	"""Apply a kept event or update to its case, once. A restriction update is recorded where the hold reads it."""
	case = case_of(row.award_case)
	if not case or row.state != "Received":
		return
	payload = records.loads(row.payload_json)
	doc = frappe.get_doc(CASE, case)
	if row.kind == "Decision event":
		events.record(case, "Award decision recorded", "", f"Award recorded the decision {payload.get('decision')}: {row.outcome}.", event=payload.get("event_id"), outcome=row.outcome)
	elif row.kind == "Update":
		events.record(case, "Award restriction received", "", f"Award reported a restriction: {payload.get('basis')} ({payload.get('scope')}).", issue=payload.get("issue"), basis=payload.get("basis"),
			scope=payload.get("scope"), effective_at=payload.get("effective_at"))
		if doc.lifecycle in ("Preparing", "Awaiting signatures"):
			work.assign(case, "ReviewAwardRestriction", "Review the award restriction.", f"restriction {payload.get('issue')}", 1, work.holders(work.HOP), role=work.HOP)
	records.update(row, contract_case=case, state="Applied", record_version=cint(row.record_version) + 1)


@holds.provider("award_restrictions")
def _restrictions(case: str):
	"""A restriction Award reported holds signing and activation until the head of procurement records the owner's resolution."""
	if frappe.db.get_value(CASE, case, "lifecycle") not in ("Preparing", "Awaiting signatures"):
		return []
	out = []
	for row in frappe.get_all(INBOX, filters={"contract_case": case, "kind": "Update", "state": "Applied"}, fields=["name", "payload_json"]):
		payload = records.loads(row.payload_json)
		out.append(holds.Hold(key=f"award restriction:{payload.get('issue')}", kind="Restriction", reason=f"Award reported a restriction on this award: {payload.get('basis')}.",
			blocks=frozenset({"new_signing_attempt", "activate_contract"}), owner="Head of procurement function", clearing="The restriction is resolved by its owner and the head of procurement records the resolution"))
	return out


def release_restriction(case: str, *, issue: str, reason: str, reference: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordRestrictionResolution` (authored; recorded for the owner as an open item): the owner of a restriction resolved it, and the head of procurement records that, with who resolved it and where."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing", "Awaiting signatures")
		invalid({"reason": "" if cstr(reason).strip() else "Enter how it was resolved.", "reference": "" if cstr(reference).strip() else "Enter the reference of the owner's resolution."})
		target = None
		for row in frappe.get_all(INBOX, filters={"contract_case": case, "kind": "Update", "state": "Applied"}, pluck="name"):
			doc_row = frappe.get_doc(INBOX, row)
			if records.loads(doc_row.payload_json).get("issue") == issue:
				target = doc_row
		if target is None:
			fail("CM_CHANGED", reason="This restriction is not open.")
		records.update(target, state="Released", release_reason=f"{reason.strip()} ({reference.strip()})", released_by=actor, released_at=clock.now(), record_version=cint(target.record_version) + 1)
		records.bump(doc)
		work.finish(case, command="ReviewAwardRestriction", subject=f"restriction {issue}", actor=actor)
		events.record(case, "Award restriction resolved", actor, f"The restriction was resolved: {reason.strip()} ({reference.strip()}).", issue=issue)
		return records.summary(doc, issue=issue)

	return records.command("RecordRestrictionResolution", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "reason": reason, "reference": reference},
		body=body, authorise=lambda: preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or ""))


# -- the receiver -----------------------------------------------------------------------------------------------------------------------
class Receiver:
	"""The three operations Award calls. Each returns `{"receipt", "received_at"}` (a package also names the person asked to prepare the contract).

	An answer never commits. Award calls it inside its own savepoint and releases that savepoint afterwards, so a commit here would destroy it and every real delivery would fail; the receipt becomes
	durable with Award's own transaction, which is the one that moves the case to *Sent to Contracting*. If Award's transaction is undone, the receipt is undone with it and the retry is a fresh answer."""

	def receive_decision_event(self, payload: dict[str, Any]) -> dict[str, Any]:
		row, again = _keep("Decision event", payload)
		_apply(row)
		return {"receipt": row.receipt, "received_at": row.received_at, "duplicate": again}

	def receive_package(self, payload: dict[str, Any]) -> dict[str, Any]:
		row, again = _keep("Package", payload)
		reference = cstr(payload.get("reference"))
		try:
			out = formation.receive_award_package(payload, handoff=list(payload.get("handoff") or []), managing_unit=cstr(payload.get("managing_unit")), idempotency_key=f"award-package:{reference}", actor="Administrator")
		except ContractError as exc:
			raise RuntimeError(f"Contract Management cannot accept the package: {exc}") from exc
		if row.state == "Received":
			records.update(row, contract_case=out["contract"], state="Applied", record_version=cint(row.record_version) + 1)
		for waiting in frappe.get_all(INBOX, filters={"award_case": row.award_case, "state": "Received", "kind": ["!=", "Package"]}, pluck="name"):
			_apply(frappe.get_doc(INBOX, waiting))  # an event or an update that arrived first
		holders = work.holders(work.HOP)
		return {"receipt": row.receipt, "received_at": row.received_at, "task_user": holders[0] if holders else None, "contract": out["contract"], "duplicate": again}

	def receive_update(self, payload: dict[str, Any]) -> dict[str, Any]:
		row, again = _keep("Update", payload)
		_apply(row)
		return {"receipt": row.receipt, "received_at": row.received_at, "duplicate": again}
