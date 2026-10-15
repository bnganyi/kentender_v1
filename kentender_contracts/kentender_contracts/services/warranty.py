# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Warranty claims on accepted goods (CM-CHG-001 v0.8 sections 5.18 "Accepted-and-paid goods returned/replaced", 5.20, 7; plan Phase 8; boards D16-W, D16-P, D35, D35-V, D35-C, D35-H).

A warranty claim is an issue (`issues.py`) with a unit, a fault, the day notice was given, the remedy asked for and its own stages: the defect notice goes to the supplier; for a replacement the owner records the
actual collection of the faulty unit; Finance reconciles the return and credit against the native documents it holds; the replacement arrives and is inspected and accepted by the ordinary route; an appointed
technical capacity verifies the remedy; and a verified remedy closes the claim in the same act, with no further approval. The supplier can respond and propose a remedy but never accepts one.

The money stays what it was. The unit was accepted and paid for and that is history: a replacement fulfils the **existing** obligation (the returned unit no longer counts as accepted, so the line is short by
one until its replacement is accepted), it adds no second payable and no invoice entitlement, and it takes no universal new warranty period (the replacement's own acceptance starts the issued warranty). While
a returned unit's credit is not reconciled, new certification and payment wait (matrix row R18-06) and the claim cannot be closed."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import add_months, cint, cstr, getdate

from kentender_contracts.services import authority, bindings, change, clock, delivery, events, holds, issues, position, preflight, records, work
from kentender_contracts.services.errors import fail, invalid

ISSUE = "Contract Issue"
ACCEPTANCE = "Contract Acceptance"
INTENT = "Contract Operation Intent"
REMEDIES = ("Like-for-like replacement", "Repair")
STAGES = ("notice", "return", "reconcile", "replacement", "verify", "closed")


def get(case: str, number: int):
	return issues.get(case, number)


def facts(row) -> dict[str, Any]:
	return records.loads(row.facts_json)


def links(row) -> dict[str, Any]:
	return records.loads(row.links_json)


def stage(row) -> str:
	return links(row).get("stage", "notice")


def claims(case: str) -> list[Any]:
	return [frappe.get_doc(ISSUE, n) for n in frappe.get_all(ISSUE, filters={"contract_case": case, "kind": "Warranty claim"}, pluck="name", order_by="issue_no asc")]


def open_claims(case: str) -> list[Any]:
	return [c for c in claims(case) if c.state != "Closed"]


def _save(row, **parts) -> None:
	body = links(row)
	body.update(parts)
	records.update(row, links_json=records.dumps(body), record_version=cint(row.record_version) + 1)


def subject_of(row) -> str:
	return f"issue {row.issue_no}"


def accepted_on(case: str, unit: str):
	"""The day this unit's acceptance became effective: where its warranty starts (the issued terms: from each unit's acceptance)."""
	said = position.decisions(case).get(unit)
	if not said or said["disposition"] != "accepted":
		return None
	at = frappe.db.get_value(ACCEPTANCE, said["acceptance"], "decision_at")
	return getdate(at) if at else None


def warranty_ends(case: str, unit: str):
	months = cint(((change.operative_terms(case).get("warranty") or {}).get("months")))
	start = accepted_on(case, unit)
	return add_months(start, months) if start and months else None


def _item(case: str, line_id: str) -> str:
	line = next((l for l in change.operative_terms(case).get("lines", []) if l["line_id"] == line_id), {})
	return cstr(line.get("description") or line.get("item")).lower()


# -- the claim --------------------------------------------------------------------------------------------------------------------------------
def on_accepted(case: str, accepted: list[str], version: int, actor: str = "") -> None:
	"""Units were accepted: the issued warranty runs from each unit's acceptance, so a scheduled follow-up for the day it ends is part of the contract's work (it is a task state; the warranty itself stays active).
	The date comes from the issued terms; a contract whose terms give no warranty period gets none."""
	months = cint((change.operative_terms(case).get("warranty") or {}).get("months"))
	if not accepted or not months:
		return
	at = frappe.db.get_value(ACCEPTANCE, {"contract_case": case, "version_no": version}, "decision_at")
	if not at:
		return
	ends = add_months(getdate(at), months)
	work.assign(case, "RecordWarrantyClaim", f"Warranty for {len(accepted)} accepted unit{'' if len(accepted) == 1 else 's'}", f"warranty acceptance {version}", 1, [issues.owner_of(case)], role="Contract owner", state="Scheduled", due=ends, due_verified=True)


def record_claim(case: str, *, unit: str, fault: str, notice_date: str, remedy: str, expected_version: int, idempotency_key: str, actor: str, evidence: str = "") -> dict[str, Any]:
	"""`RecordWarrantyClaim`: the contract owner records the unit, the fault, the day notice was given and the remedy asked for. The claim must be made while the unit's warranty runs and for a unit that is
	accepted; the defect notice to the supplier is the owner's next step."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active", "Closed")
		have = position.position(case)["units"].get(unit)
		problems = {"unit": "" if have and have["status"] == "Accepted" else "Choose an accepted unit.", "fault": "" if cstr(fault).strip() else "Describe the fault.", "remedy": "" if remedy in REMEDIES else "Choose the remedy asked for."}
		try:
			noticed = getdate(notice_date)
		except Exception:  # noqa: BLE001
			noticed, problems["notice_date"] = None, "Enter the day notice was given."
		invalid(problems)
		ends = warranty_ends(case, unit)
		if ends is None:
			invalid({"unit": "The issued terms give this unit no warranty period."})
		if noticed > ends:
			invalid({"notice_date": f"The warranty for this unit ended on {ends.strftime('%-d %B %Y')}."})
		if any(facts(c).get("unit") == unit for c in open_claims(case)):
			fail("CM_CHANGED", reason="This unit already has a warranty claim in progress.", unit=unit)
		item = _item(case, have["line_id"])
		row = issues.open_issue(case, kind="Warranty claim", title=f"Warranty claim for {item} {unit}", facts={"unit": unit, "line_id": have["line_id"], "item": item, "fault": cstr(fault).strip(), "notice_date": str(noticed),
			"warranty_ends": str(ends), "evidence": cstr(evidence).strip(), "recorded_by": actor}, requested_remedy=remedy, units=[unit], links={"stage": "notice", "acceptance": have["acceptance"]}, draft=cstr(fault).strip(),
			actor=actor, first_task="Send the defect notice.")
		records.bump(doc)
		return records.summary(doc, issue=row.name, issue_no=row.issue_no)

	return records.command("RecordWarrantyClaim", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "unit": unit, "fault": fault, "notice": notice_date, "remedy": remedy,
		"evidence": evidence}, body=body, authorise=lambda: issues._may_manage(case, actor))


def on_notice_delivered(case: str, issue: str, actor: str) -> None:
	"""The defect notice reached the supplier: a replacement is arranged next (the owner records the collection); a repair goes straight to its verification."""
	row = frappe.get_doc(ISSUE, issue)
	if stage(row) != "notice":
		return
	if row.requested_remedy == "Repair":
		_save(row, stage="verify")
		_ask_verification(case, row, "Confirm the repair evidence.")
		return
	_save(row, stage="return")
	work.assign(case, "RecordWarrantyReturn", f"Arrange return of the faulty {facts(row)['item']}.", subject_of(row), 1, [row.owner_user], role="Contract owner")


def record_return(case: str, *, issue: str, collected_on: str, evidence: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordWarrantyReturn`: the actual collection of the faulty unit, with the evidence. This is a request for the authorised correction, not a custody-only removal: the unit stops counting as accepted, new
	certification and payment wait, and Finance is asked to reconcile the native return and credit. It does not claim the native return is posted."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ISSUE, issue)
		if row.contract_case != case or row.kind != "Warranty claim" or stage(row) != "return":
			fail("CM_CHANGED", issue=issue, state=row.state)
		try:
			day = getdate(collected_on)
		except Exception:  # noqa: BLE001
			day = None
		invalid({"collected_on": "" if day else "Enter the day the unit was collected.", "evidence": "" if cstr(evidence).strip() else "Enter the collection evidence."})
		unit = facts(row)["unit"]
		events.record(case, position.RETURN_EVENT, actor, f"Unit {unit} collected by the supplier under warranty claim {row.issue_no}.", units=[unit], evidence=cstr(evidence).strip(), warranty=row.name)
		_save(row, stage="reconcile", returned={"on": str(day), "evidence": cstr(evidence).strip(), "by": actor})
		work.finish(case, command="RecordWarrantyReturn", subject=subject_of(row), actor=actor)
		work.assign(case, "ReconcileWarrantyReturn", f"Reconcile the return and credit for the faulty {facts(row)['item']}.", subject_of(row), 1, work.holders("Finance preparation"), role="Finance preparation")
		events.record(case, "Warranty return recorded", actor, f"The faulty unit {unit} was collected on {day.strftime('%-d %B %Y')}; Finance reconciles the return.", issue=row.name)
		records.bump(doc)
		return records.summary(doc, issue=row.name, unit=unit)

	return records.command("RecordWarrantyReturn", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "on": collected_on, "evidence": evidence},
		body=body, authorise=lambda: issues._may_manage(case, actor))


# -- Finance reconciles the return and credit ----------------------------------------------------------------------------------------------
def _case_receipts(case: str) -> set[str]:
	from kentender_contracts.services import delivery

	return set(delivery.posted_receipts(case))


def _case_invoices(case: str) -> set[str]:
	return {i for i in frappe.get_all("Contract Invoice", filters={"contract_case": case, "native_invoice": ["is", "set"]}, pluck="native_invoice")}


def reconcile_return(case: str, *, issue: str, return_document: str = "", credit_document: str = "", note: str = "", expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`ReconcileWarrantyReturn`: Finance names the native documents that carry the return and the credit (a posted return of the receipt, a posted debit note against the invoice). Contract Management reads them
	and writes nothing natively; a document that is not a submitted return of this contract's own receipt or invoice is refused."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ISSUE, issue)
		if row.contract_case != case or row.kind != "Warranty claim" or stage(row) != "reconcile":
			fail("CM_CHANGED", issue=issue, state=row.state)
		problems = {}
		if not cstr(return_document).strip() and not cstr(credit_document).strip():
			problems["return_document"] = "Name the native return or credit that carries this unit's return."
		if cstr(return_document).strip():
			found = frappe.db.get_value("Purchase Receipt", return_document, ["docstatus", "is_return", "return_against"], as_dict=True)
			if not found or found.docstatus != 1 or not found.is_return or found.return_against not in _case_receipts(case):
				problems["return_document"] = "This is not a posted return of one of this contract's receipts."
		if cstr(credit_document).strip():
			found = frappe.db.get_value("Purchase Invoice", credit_document, ["docstatus", "is_return", "return_against"], as_dict=True)
			if not found or found.docstatus != 1 or not found.is_return or found.return_against not in _case_invoices(case):
				problems["credit_document"] = "This is not a posted credit against one of this contract's invoices."
		invalid(problems)
		_save(row, stage="replacement", reconciliation={"return_document": cstr(return_document).strip(), "credit_document": cstr(credit_document).strip(), "note": cstr(note).strip(), "by": actor, "at": str(clock.now())})
		work.finish(case, command="ReconcileWarrantyReturn", subject=subject_of(row), actor=actor)
		events.record(case, "Warranty return reconciled", actor, f"Finance reconciled the return and credit for the faulty unit {facts(row)['unit']}.", issue=row.name, **{k: v for k, v in (("return", return_document), ("credit", credit_document)) if v})
		_ask_verification_if_ready(case, frappe.get_doc(ISSUE, issue))
		records.bump(doc)
		return records.summary(doc, issue=row.name)

	recorded = records.command("ReconcileWarrantyReturn", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "return": return_document, "credit": credit_document,
		"note": note}, body=body, authorise=lambda: authority.require(actor, "Finance preparation"))
	frappe.db.commit()
	delivery.restore_receipts(case, actor)  # the replacement's receipt waits on the native return (ERPNext will not receive more than was ordered): it is posted now that the return exists
	return recorded


# -- the replacement and its verification ---------------------------------------------------------------------------------------------------
def replacement_of(case: str, unit: str) -> str:
	"""The accepted unit that replaces the faulty one: the arrival named it, and an effective report accepted it."""
	now = position.position(case)["units"]
	for new, row in now.items():
		if row["replaces"] == unit and row["status"] == "Accepted":
			return new
	return ""


def _certifiers(case: str) -> list[str]:
	found = bindings.effective_appointment(case)
	return sorted({m["user"] for m in (found["members"] if found else []) if m.get("certifier")})


def _ask_verification(case: str, row, title: str) -> None:
	work.assign(case, "VerifyContractRemedy", title, subject_of(row), 1, _certifiers(case) or work.holders(work.HOP), role="Technical certification")


def _ask_verification_if_ready(case: str, row) -> None:
	if stage(row) == "replacement" and replacement_of(case, facts(row)["unit"]):
		_save(row, stage="verify", replacement=replacement_of(case, facts(row)["unit"]))
		_ask_verification(case, row, "Confirm the remedy evidence.")  # the same obligation as the one asked when the replacement was accepted: an existing item is left as it is


def on_replacement_accepted(case: str, replaced: dict[str, str], actor: str) -> None:
	"""A replacement unit was accepted: a warranty claim for the unit it replaces is ready to be verified once Finance has reconciled the return."""
	for row in open_claims(case):
		if facts(row)["unit"] in set(replaced.values()) and stage(row) in ("reconcile", "replacement"):
			_save(row, replacement=replacement_of(case, facts(row)["unit"]), **({"stage": "verify"} if stage(row) == "replacement" else {}))
			_ask_verification(case, frappe.get_doc(ISSUE, row.name), "Confirm the remedy evidence.")  # asked at once; while Finance has not reconciled the return, the hold shows it blocked and names Finance
			events.record(case, "Warranty replacement accepted", actor, f"The replacement for unit {facts(row)['unit']} was accepted.", issue=row.name)


def missing_evidence(case: str, row) -> list[dict[str, str]]:
	"""What is still missing before this claim's remedy can be verified, each with the person or role who holds it. Empty means the remedy can be verified now."""
	found, out = facts(row), []
	if row.requested_remedy == "Repair":
		return out
	unit, replacement = found["unit"], replacement_of(case, found["unit"])
	finance = next(iter(work.holders("Finance preparation")), "Finance")
	if "reconciliation" not in links(row):
		out.append({"what": "Finance has not reconciled the return and credit of the faulty unit.", "holder": finance})
	if not replacement:
		out.append({"what": f"No replacement for unit {unit} has been accepted.", "holder": row.owner_user})
		return out
	version = frappe.db.get_value(ACCEPTANCE, position.position(case)["units"][replacement]["acceptance"], "version_no")
	receipt = frappe.db.get_value(INTENT, {"contract_case": case, "operation_kind": "Accepted receipt", "subject": f"acceptance {version}"}, "state")
	if receipt not in ("Succeeded", "Reconciled"):
		out.append({"what": "The replacement's receipt has not been posted.", "holder": "Technical operator"})
	return out


def verify_remedy(case: str, *, issue: str, evidence: str = "", expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`VerifyContractRemedy`: the current technical capacity confirms the remedy from the measured evidence. When every required link is already reconciled this one act commits the verification and closes
	the claim; otherwise the claim stays open and the refusal names what is missing and who holds it."""
	preflight.exists(case)

	def authorise() -> None:
		authority.require_capacity(case, actor, "technical certifier")

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		row = frappe.get_doc(ISSUE, issue)
		if row.contract_case != case or row.kind != "Warranty claim" or row.state == "Closed":
			fail("CM_CHANGED", issue=issue, state=row.state)
		if stage(row) not in ("verify", "replacement", "reconcile"):
			fail("CM_CHANGED", issue=issue, reason="The remedy is not ready to be verified.", stage=stage(row))
		if row.requested_remedy == "Repair":
			invalid({"evidence": "" if cstr(evidence).strip() else "Enter the measured repair evidence."})
		missing = missing_evidence(case, row)
		if missing:
			fail("CM_RECONCILE", issue=issue, reason="The remedy cannot be verified yet.", missing=missing, holder=missing[0]["holder"])
		found = facts(row)
		done = {"by": actor, "at": str(clock.now()), "evidence": cstr(evidence).strip(), "replacement": replacement_of(case, found["unit"]) if row.requested_remedy != "Repair" else ""}
		_save(row, stage="closed", verification=done)
		outcome = (f"Remedy verified: replacement unit {done['replacement']} accepted for unit {found['unit']}; no additional payment." if done["replacement"] else f"Remedy verified: unit {found['unit']} repaired.")
		work.finish(case, command="VerifyContractRemedy", subject=subject_of(row), actor=actor)
		issues.close(case, frappe.get_doc(ISSUE, issue), outcome, actor)
		events.record(case, "Remedy verified", actor, outcome, issue=row.name, unit=found["unit"])
		records.bump(doc)
		return records.summary(doc, issue=row.name, state="Closed")

	return records.command("VerifyContractRemedy", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "issue": issue, "evidence": evidence}, body=body, authorise=authorise)


@holds.provider("warranty")
def _unreconciled_return(case: str) -> list[holds.Hold]:
	"""A returned unit whose credit is not reconciled holds new certification and payment, and the claim's closing, until Finance reconciles it (matrix row R18-06). Independent work is not held."""
	found = []
	for row in open_claims(case):
		if stage(row) == "reconcile":
			owner = next(iter(work.holders("Finance preparation")), "Finance")
			found.append(holds.Hold(key=f"warranty return:{row.name}", kind="Correction", reason="Finance must reconcile the replacement.", blocks=frozenset({"certify_invoice", "pay", "close_claim"}), owner=owner,
				clearing="Finance names the native return and credit for the returned unit", scope=()))
	return found
