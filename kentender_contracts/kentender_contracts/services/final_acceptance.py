# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Final acceptance (CM-CHG-001 v0.8 sections 5.9, 7 `SignFinalContractAcceptance`, 19.3 CM-R-09; plan Phase 9; boards D32, D32-H).

Receipt and initial acceptance support stock and payment; **final acceptance** is the Accounting Officer's own act, where the issued terms require one; completion and close-out follow it. It is not tied to the end of a
warranty or to payment: the only things in its way are a completion defect that is still unresolved (an issue the supplier has not remedied, a timely warranty claim still open) and goods not yet all accepted. Its signing
instant is the event the security-return clock starts from (`security_actions.on_final_acceptance`), recorded apart from the committee's acceptance, from payment and from the head of procurement's completion
certificate, which is a separate output."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_contracts.services import authority, change, clock, events, position, preflight, records, security_actions, signing_flow, warranty, work
from kentender_contracts.services.errors import fail

CERTIFICATE = "Contract Certificate"
ISSUE = "Contract Issue"
CASE = "Contract Case"
SUBJECT = "final acceptance"


def required(case: str) -> bool:
	"""Whether the issued terms require the Accounting Officer's final acceptance."""
	return bool((change.operative_terms(case).get("final_acceptance") or {}).get("required"))


def basis(case: str) -> str:
	return cstr((change.operative_terms(case).get("final_acceptance") or {}).get("basis")) or "As the issued terms provide"


def current(case: str):
	name = frappe.db.get_value(CERTIFICATE, {"contract_case": case, "kind": "Final acceptance", "state": ["!=", "Superseded"]}, "name", order_by="creation desc")
	return frappe.get_doc(CERTIFICATE, name) if name else None


def signed(case: str) -> bool:
	row = current(case)
	return bool(row and row.state == "Signed")


def unresolved(case: str) -> list[dict[str, str]]:
	"""Completion defects nobody has resolved: a delivery issue still open, a timely warranty claim still open, each with the person who holds it."""
	out: list[dict[str, str]] = []
	for row in frappe.get_all(ISSUE, filters={"contract_case": case, "state": ["!=", "Closed"], "kind": ["in", ["Delivery issue", "Warranty claim"]]}, fields=["name", "issue_no", "kind", "title", "owner_user"], order_by="issue_no asc"):
		unit = (records.loads(frappe.db.get_value(ISSUE, row.name, "facts_json")) or {}).get("unit")
		out.append({"what": f"{'Unit ' + unit + ' still has an unresolved completion defect.' if unit else row.title + ' is not resolved.'}", "holder": row.owner_user, "ref": f"issue {row.issue_no}"})
	return out


def defects(case: str) -> list[dict[str, str]]:
	"""What still stands between the contract and final acceptance: goods not all accepted, and the unresolved completion defects, each with its holder."""
	out: list[dict[str, str]] = []
	now = position.position(case)
	if now["remaining"] or now["in_custody"] or any(line["pending_decision"] or line["deferred"] for line in now["lines"].values()):
		out.append({"what": "Not every ordered unit has been accepted.", "holder": "Inspection chair", "ref": "delivery"})
	return out + unresolved(case)


def offer(case: str, actor: str = "") -> bool:
	"""Everything ordered is accepted and the terms ask for a final acceptance: the Accounting Officer is asked to record it (the defects, if any, are shown with the request and stop its signing)."""
	doc = frappe.get_doc(CASE, case)
	if doc.lifecycle != "Active" or not required(case) or signed(case):
		return False
	now = position.position(case)
	if not now["ordered"] or now["remaining"]:
		return False
	work.assign(case, "SignFinalContractAcceptance", "Review the final acceptance evidence.", SUBJECT, 1, work.holders("Accounting Officer"), role="Accounting Officer")
	return True


def evidence(case: str) -> dict[str, Any]:
	"""The facts the Accounting Officer reviews: the units accepted and when each unit's warranty ends, the unresolved defects and the source's treatment."""
	now = position.position(case)
	accepted = [u for u, row in now["units"].items() if row["status"] == "Accepted"]
	ends = sorted({str(warranty.warranty_ends(case, u)) for u in accepted if warranty.warranty_ends(case, u)})
	return {"accepted": now["accepted"], "warranty_ends": ends, "defects": defects(case), "treatment": basis(case)}


def sign(case: str, *, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`SignFinalContractAcceptance`: the Accounting Officer's personal proof, through the shared facade, of the exact evidence reviewed. Refused while a completion defect is unresolved; recorded once."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Active")
		if not required(case):
			fail("CM_CHANGED", reason="The issued terms do not require a final acceptance.")
		if signed(case):
			return records.summary(doc, certificate=current(case).name, already=True)
		preflight.rules(doc, "SignFinalContractAcceptance").raise_if_any()
		found = defects(case)
		if found:
			fail("CM_CLOSURE", remaining=[{"kind": "Completion defect", "what": d["what"], "holder": d["holder"], "prevents": True} for d in found])
		content = evidence(case)
		row = current(case) or records.new(CERTIFICATE, contract_case=case, kind="Final acceptance", subject=SUBJECT, subject_version=1, state="Awaiting signature", content_json=records.dumps(content), record_version=1)
		intent = signing_flow.record(case, SUBJECT, 1, "sign")
		return records.summary(doc, certificate=row.name, intent=intent.name, digest=records.digest(content))

	recorded = records.command("SignFinalContractAcceptance", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version}, body=body, authorise=lambda: authority.require(actor, "Accounting Officer"))
	frappe.db.commit()
	if recorded.get("already"):
		return recorded
	result = signing_flow.carry_out(recorded["intent"], member=actor, target_id=recorded["certificate"], target_digest=recorded["digest"], version=1, action="Sign the final acceptance")
	if not signing_flow.settled(result):
		with records.atomic():
			work.incident(case, "RestoreContractOperation", "Restore signing", SUBJECT, 1)
		frappe.db.commit()
		signing_flow.unfinished(result, certificate=recorded["certificate"])
	with records.atomic():
		doc = records.lock(case)
		row = frappe.get_doc(CERTIFICATE, recorded["certificate"])
		if row.state != "Signed":
			records.update(row, state="Signed", signer=actor, proof_reference=result["reference"], signed_at=clock.now(), record_version=cint(row.record_version) + 1)
			records.bump(doc, obligation_state="Final acceptance recorded")
			work.finish(case, command="SignFinalContractAcceptance", subject=SUBJECT, actor=actor)
			work.finish(case, command="RestoreContractOperation", subject=SUBJECT, actor=actor)
			events.record(case, "Final acceptance recorded", actor, "The Accounting Officer recorded the final acceptance.", certificate=row.name, proof=result["reference"])
			security_actions.on_final_acceptance(case, actor)  # the security's return clock starts here, and nowhere else
			from kentender_contracts.services import closeout

			closeout.offer_completion(case)
		out = records.summary(doc, certificate=row.name, state="Signed")
	frappe.db.commit()
	return out
