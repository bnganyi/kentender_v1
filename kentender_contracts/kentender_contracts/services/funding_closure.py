# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Asking the funding owner to close the commitment of a closed or terminated contract (CM-CHG-001 v0.8 sections 5.14, 5.14.1, 5.21; matrix row R17-08; plan Phases 8 and 9).

Closing is a **separate, acknowledged fact**: contract completion, accounting settlement and the Budget commitment's closure are three different things. Once a contract is closed or its termination settlement is
completed, Contract Management records one durable `Funding closure` operation and carries it out through the published seam (`kentender_core.services.contract_funding_contract.close`). The owner changes status and
attribution only: the amount and what is available stay as they are, and nothing is released. The final supported obligation is never typed here; it is the amount the contract's commitments hold after any lawful
final decrease, and a mismatch is the owner's refusal, never an adjustment. Until the owner acknowledges, the contract shows **Funding finalisation pending**, and an outstanding closure keeps funds from being
released or the contract from being shown as financially finalised (R17-08)."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_contracts.services import events, intents, records, work
from kentender_core.services import contract_funding_contract as funding_seam

SUBJECT = "closure"


def intent_of(case: str, subject: str = ""):
	filters = {"contract_case": case, "operation_kind": "Funding closure"}
	if subject:
		filters["subject"] = subject
	name = frappe.db.get_value(intents.INTENT, filters, "name", order_by="creation desc")
	return frappe.get_doc(intents.INTENT, name) if name else None


def request(case: str, *, subject: str, version: int, final_amount: float, event_type: str, evidence: list[str], actor: str) -> Any:
	"""Record the closure operation (idempotent on its identity) with what it must carry: the final supported obligation, the owner event and the evidence it rests on."""
	row = intents.record(case, subject, version, "Funding closure", "close", recovery_owner="Technical operator; Budget owner")
	detail = {"final_amount": float(final_amount), "event_type": event_type, "evidence": list(evidence)}
	if not frappe.db.get_value(intents.INTENT, row.name, "attempts_json"):
		records.update(row, attempts_json=records.dumps([{"at": "recorded", "outcome": "Recorded", "detail": detail}]))
	return row


def carried(row) -> dict[str, Any]:
	for entry in records.loads(row.attempts_json, []):
		if isinstance(entry, dict) and entry.get("detail") and "final_amount" in entry["detail"]:
			return entry["detail"]
	return {}


def carry_out(case: str, actor: str = "") -> list[dict[str, Any]]:
	"""Carry every pending closure through the owner, each in its own transaction. Safe to repeat: the owner is read first by identity."""
	out = []
	for name in frappe.get_all(intents.INTENT, filters={"contract_case": case, "operation_kind": "Funding closure", "state": ["in", list(intents.PENDING)]}, pluck="name"):
		row = frappe.get_doc(intents.INTENT, name)
		detail = carried(row)
		if not detail:
			continue

		def executor(identity, d=detail):
			try:
				done = funding_seam.close(identity, contract=case, final_amount=d["final_amount"], event_id=f"{case}|{row.subject}", event_type=d["event_type"], evidence=d["evidence"])
			except funding_seam.Refused as exc:
				raise intents.OwnerRefused(str(exc)) from exc
			return done["reference"], "Procurement Commitment"

		result = intents.execute(name, executor, lambda identity: (funding_seam.recall(identity) or {}).get("reference"), native_doctype="Procurement Commitment")
		out.append({"subject": row.subject, **result})
		with records.atomic():
			if result["state"] in intents.SETTLED:
				work.finish(case, command="RestoreContractOperation", subject=row.subject, actor=actor)
				events.record(case, "Funding closure acknowledged", actor, f"The funding owner closed the commitment ({result['reference']}).", intent=name, reference=result["reference"])
			else:
				work.incident(case, "RestoreContractOperation", "Restore contract operation", row.subject, row.subject_version)
				events.record(case, "Funding closure pending", actor, f"The funding closure did not complete ({result['state'].lower()}).", intent=name)
		frappe.db.commit()
	return out


def status(case: str, subject: str = "") -> str:
	"""`Acknowledged`, `Pending` or `Not requested`: the three truthful states of the commitment's closure."""
	row = intent_of(case, subject)
	if row is None:
		return "Not requested"
	return "Acknowledged" if row.state in intents.SETTLED else "Pending"
