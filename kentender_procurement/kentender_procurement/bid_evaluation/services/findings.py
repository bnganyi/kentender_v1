# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RecordEvidenceFinding and RaiseFindingConcern (EVL-CHG-001 v0.4 §4.3, §7.2,
§7.3 row 6; tracker EVL4-601, EVL4-602; boards D04, D04-AUTO, D04-CONCERN).

An eligible appointed member records a finding against one requirement of
one bid, with a result, reason and evidence reference. A system result is
never overwritten; a later finding supersedes the member's earlier one and
keeps it as history. Straightforward evidence checks need no second
approval: everyone reviews them in the report. Saving a finding as Needs
review, raising a concern or recording a finding contrary to an automatic
result creates or updates the one chair discussion item for that bid and
requirement; opening a form or reading never clears it."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_evaluation.services import aggregate, checks, clock, guards, notify, prc, records, roster
from kentender_procurement.bid_evaluation.services.errors import fail, invalid

FINDING = "Evaluation Finding"
ITEM = "Evaluation Discussion Item"
RESULTS = ("Meets", "Does not meet", "Needs review")


def require_member(doc, user: str) -> None:
	"""Bid access needs appointment and personal eligibility (§3)."""
	if user not in roster.member_users(doc.name):
		raise frappe.DoesNotExistError("Not found")
	standing = roster.status(doc.name, user)
	if not standing["declared"] and not standing["conflict"]:
		fail("EVL_DECLARATION_REQUIRED")
	if not standing["eligible"]:
		raise frappe.DoesNotExistError("Not found")


def _requirement(doc, bid: str, requirement_key: str) -> dict[str, Any]:
	run = checks.current_run(doc.name)
	if not run or not frappe.db.exists("Evaluation Bid", {"name": bid, "evaluation_case": doc.name}):
		raise frappe.DoesNotExistError("Not found")
	res = aggregate.bid_results(doc.name, run, bid)
	found = next((r for r in res["requirements"] if r["requirement_key"] == requirement_key), None)
	if found is None:
		raise frappe.DoesNotExistError("Not found")
	return found


def open_item(doc, bid: str, requirement_key: str, *, subject: str, user: str, finding: str) -> str:
	name = frappe.db.get_value(ITEM, {"evaluation_case": doc.name, "evaluation_bid": bid, "requirement_key": requirement_key, "status": "Open"}, "name")
	if name:
		item = frappe.get_doc(ITEM, name)
		item.last_finding = finding
		records.save(item)
		return item.name
	number = frappe.db.count(ITEM, {"evaluation_case": doc.name}) + 1
	item = records.insert(frappe.get_doc({
		"doctype": ITEM, "item_id": f"{doc.name}-ITEM-{number:02d}", "evaluation_case": doc.name, "evaluation_bid": bid, "requirement_key": requirement_key,
		"subject": subject, "status": "Open", "opened_at": clock.now(), "opened_by": user, "last_finding": finding,
	}))
	chair = roster.chair(doc.name)
	notify.tell(doc, [chair] if chair else [], subject=f"Resolve evaluation concern for {doc.tender_reference}", message=subject, key=f"concern-{item.name}")
	return item.name


def clear_item(doc, item: str, *, kind: str, reference: str) -> None:
	row = frappe.get_doc(ITEM, item)
	row.status = "Transferred" if kind in ("Clarification", "Verification", "Support issue") else "Resolved"
	row.resolution_kind, row.resolution_reference, row.cleared_at = kind, reference, clock.now()
	records.save(row)


def _write(doc, *, bid: str, requirement_key: str, kind: str, result: str, reason: str, evidence_reference: str, user: str) -> Any:
	prior = frappe.db.get_value(FINDING, {"evaluation_case": doc.name, "evaluation_bid": bid, "requirement_key": requirement_key, "author": user, "kind": kind,
		"status": "Current"}, "name")
	if prior:
		records.save(frappe.get_doc(FINDING, prior).update({"status": "Superseded"}))
	number = frappe.db.count(FINDING, {"evaluation_case": doc.name}) + 1
	return records.insert(frappe.get_doc({
		"doctype": FINDING, "finding_id": f"{doc.name}-FND-{number:03d}", "evaluation_case": doc.name, "evaluation_bid": bid, "requirement_key": requirement_key,
		"kind": kind, "result": result, "reason": cstr(reason).strip(), "evidence_reference": cstr(evidence_reference).strip(), "author": user,
		"recorded_at": clock.now(), "prior_finding": prior, "status": "Current",
	}))


def record_evidence_finding(*, tender: str, bid: str, requirement_key: str, result: str, reason: str, evidence_reference: str = "", idempotency_key: str,
		user: str) -> dict[str, Any]:
	payload = {"bid": bid, "requirement_key": requirement_key, "result": result, "reason": reason, "evidence_reference": evidence_reference}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_member(doc, user)
		checks_ = guards.open_case(doc)
		if doc.state != "Reviewing":
			checks_.add("EVL_VERSION_CONFLICT", reason="not_reviewing", state=doc.state)
		checks_.raise_if_any()
		invalid({**({"result": "Choose Meets, Does not meet or Needs review."} if result not in RESULTS else {}),
			**({"reason": "Give the reason."} if not cstr(reason).strip() else {})})
		requirement = _requirement(doc, bid, requirement_key)
		contrary = requirement["automatic"] == "Does not meet" and result == "Meets"
		kind = "Contrary finding" if contrary else "Evidence finding"
		finding = _write(doc, bid=bid, requirement_key=requirement_key, kind=kind, result=result, reason=reason, evidence_reference=evidence_reference, user=user)
		item = ""
		if result == "Needs review" or contrary:
			item = open_item(doc, bid, requirement_key, subject=f"{requirement['label']} — supporting evidence needs review", user=user, finding=finding.name)
			records.save(frappe.get_doc(FINDING, finding.name).update({"discussion_item": item}))
		event = prc.owner_event(doc, "EvidenceFinding", f"finding:{finding.name}", {"bid": bid, "requirement": requirement_key, "result": result, "kind": kind},
			idempotency_key=idempotency_key, note=cstr(reason).strip())
		records.bump(doc, last_committed_event=event)
		return records.summary(doc, finding=finding.name, kind=kind, discussion_item=item)

	return records.command("RecordEvidenceFinding", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)


def raise_concern(*, tender: str, bid: str, requirement_key: str, reason: str, idempotency_key: str, user: str) -> dict[str, Any]:
	payload = {"bid": bid, "requirement_key": requirement_key, "reason": reason}

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		require_member(doc, user)
		checks_ = guards.open_case(doc)
		if doc.state != "Reviewing":
			checks_.add("EVL_VERSION_CONFLICT", reason="not_reviewing", state=doc.state)
		checks_.raise_if_any()
		invalid({"reason": "Give the reason."} if not cstr(reason).strip() else {})
		requirement = _requirement(doc, bid, requirement_key)
		finding = _write(doc, bid=bid, requirement_key=requirement_key, kind="Concern", result="Needs review", reason=reason, evidence_reference="", user=user)
		item = open_item(doc, bid, requirement_key, subject=f"{requirement['label']} — concern raised", user=user, finding=finding.name)
		records.save(frappe.get_doc(FINDING, finding.name).update({"discussion_item": item}))
		event = prc.owner_event(doc, "FindingConcern", f"concern:{finding.name}", {"bid": bid, "requirement": requirement_key}, idempotency_key=idempotency_key,
			note=cstr(reason).strip())
		records.bump(doc, last_committed_event=event)
		return records.summary(doc, finding=finding.name, discussion_item=item)

	return records.command("RaiseFindingConcern", tender=tender, idempotency_key=idempotency_key, actor=user, payload=payload, body=body)
