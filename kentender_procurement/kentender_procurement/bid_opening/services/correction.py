# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Correct opening record after completion (BOP-CHG-001 v0.10 §10.6 CORRECT
COMPLETED RECORD, §11; binding row "Finalized correction" → PRC
`AppendSupplement`; BOP-N11, PRC-N05).

The authorised recorder adds a correction of exactly one of four kinds. It
is added under their name with the trusted time; any time it mentions is
their report. The original record, its signatures, the register, the
completion and the Evaluation handoff stay exactly as they were. Any other
kind is refused, so nothing can change a bid, an amount, a register row or a
signed page this way."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.bid_opening.services import ceremony, errors, prc, records

KINDS = ("Attendance note", "Procedural note", "Typographical error in a note", "Observer name or organisation")
DENIED = "This correction cannot change a bid or replace the signed opening record."


def correct_opening_record(*, tender: str, kind: str, correct_information: str, reason: str, expected_version: int, idempotency_key: str,
		user: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import finalize

	def body() -> dict[str, Any]:
		doc = records.lock(tender)
		ceremony.require_recorder(doc, user)
		records.check_version(doc, expected_version)
		if doc.state != "Opening complete":
			errors.fail("BOP_VERSION_CONFLICT", {"reason": "state", "state": doc.state})
		if kind not in KINDS:
			return {"ok": False, "code": "BOP_CORRECTION_NOT_ALLOWED", "message": DENIED}
		if not cstr(correct_information).strip() or not cstr(reason).strip():
			return {"ok": False, "errors": {"correct_information": "Enter the correct information and the reason."}}
		version = cint(frappe.db.get_value("Proceeding", doc.proceeding, "current_minutes_version"))
		added = finalize.append_supplement(**prc.ref(doc.name), original_version=version, kind=kind, correct_information=cstr(correct_information).strip(),
			reason=cstr(reason).strip(), idempotency_key=prc.key(idempotency_key, "supplement"), actor=user)
		records.bump(doc)
		return records.summary(doc, supplement=added["supplement_id"])

	return records.command("CorrectOpeningRecord", tender=tender, idempotency_key=idempotency_key, actor=user,
		payload={"kind": kind, "info": correct_information, "reason": reason, "expected_version": expected_version}, body=body)

