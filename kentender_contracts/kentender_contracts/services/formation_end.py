# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""When a contract does not come into being (CM-CHG-001 v0.8 sections 5.3, 5.14 "Did not proceed"; plan Phase 5, tracker CM8-505, FU-CM-42).

**Did not proceed** is a reasoned terminal outcome before the agreement is in force. A refusal to sign or an expired signing window never substitutes another supplier, forfeits anything or ends the
contract on its own: it creates follow-up work for the head of procurement, who either records the outcome here or has Award extend the window. Recording keeps every record (the agreement versions,
the signatures that were made, the security instruments) and ends only the live work. A changed procurement outcome is the Accounting Officer's, recorded through Award's own route; this module does
not reach into it.

`RecordContractNotProceeding` is not in the specification's command table. It is the thin authored command that the section 5.14 lifecycle needs, recorded as an open item for the owner (FU-CM-42)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_contracts.services import clock, events, formation, formation_rules, intents, preflight, records, work
from kentender_contracts.services.errors import fail, invalid

CASE = "Contract Case"
AGREEMENT = "Contract Agreement Version"
SIGNATURE = "Contract Signature"
KINDS = ("The supplier declined to sign", "The signing window ended", "The award was withdrawn or changed", "Another reason")


def record_not_proceeding(case: str, *, kind: str, reason: str, expected_version: int, idempotency_key: str, actor: str) -> dict[str, Any]:
	"""`RecordContractNotProceeding`: the contract will not be formed. Reasoned, attributed, and only before the agreement is in force."""
	preflight.exists(case)

	def body() -> dict[str, Any]:
		doc = records.lock(case)
		records.check_version(doc, expected_version)
		preflight.lifecycle(doc, "Preparing", "Awaiting signatures")
		invalid({"kind": "" if kind in KINDS else "Choose why the contract did not proceed.", "reason": "" if cstr(reason).strip() else "Enter the reason."})
		if frappe.db.exists(intents.INTENT, {"contract_case": case, "operation_kind": "Signing attempt", "state": ["in", ["Attempting", "Uncertain", "Recorded"]]}):
			fail("CM_HOLD", hold="uncertain signature", kind="Pending operation", reason="A signing attempt is still unconfirmed, so the contract cannot be ended yet.", holder="Technical operator",
				clears_with="The signing attempt is recovered", consequence="close_formation")
		for agreement in frappe.get_all(AGREEMENT, filters={"contract_case": case, "state": ["in", ["Draft", "Frozen", "Awaiting signatures"]]}, pluck="name"):
			version = frappe.get_doc(AGREEMENT, agreement)
			records.update(version, state="Ended", record_version=cint(version.record_version) + 1)
		for slot in frappe.get_all(SIGNATURE, filters={"contract_case": case, "state": ["in", ["Waiting", "Requested", "Evidence recorded", "Failed"]]}, pluck="name"):
			records.update(frappe.get_doc(SIGNATURE, slot), state="Superseded")
		work.finish(case, state="Superseded", actor=actor)
		records.bump(doc, lifecycle="Did not proceed", outcome_reason=f"{kind}: {reason.strip()}", closed_at=clock.now())
		events.record(case, "Did not proceed", actor, f"The contract did not proceed: {kind.lower()}.", kind=kind, reason=reason.strip())
		return records.summary(doc, lifecycle="Did not proceed")

	return records.command("RecordContractNotProceeding", case=case, idempotency_key=idempotency_key, actor=actor, payload={"expected": expected_version, "kind": kind, "reason": reason}, body=body,
		authorise=lambda: preflight.acts_as_preparer(actor, frappe.db.get_value(CASE, case, "managing_unit") or ""))


def sweep_signing_windows() -> int:
	"""Scheduled: a contract whose evidenced signing window has ended gets one follow-up task for the head of procurement (never an automatic outcome). Returns how many were raised."""
	raised = 0
	for case in frappe.get_all(CASE, filters={"lifecycle": ["in", ["Preparing", "Awaiting signatures"]]}, pluck="name"):
		agreement = formation.current_agreement(case)
		if not agreement:
			continue
		ended = [f for f in formation_rules.window(records.loads(agreement.terms_json), clock.now()) if f.get("ended_on")]
		if not ended:
			continue
		subject = f"agreement {agreement.version_no}"
		made = work.assign(case, "RecordContractNotProceeding", "The signing window has ended.", subject, agreement.version_no, work.holders(work.HOP), role=work.HOP)
		if made:
			with records.atomic():
				events.record(case, "Signing window ended", "", f"The signing window ended on {ended[0]['ended_on']}.", ended_on=ended[0]["ended_on"])
			raised += 1
	frappe.db.commit()
	return raised
