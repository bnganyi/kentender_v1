# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable Bid Opening errors (BOP-CHG-001 v0.10 §8), verbatim.

§8 is a closed set of thirteen codes. Three carry the facts the sentence
names (the deadline, the member's full name) and two read differently before
and after Start. Proceedings errors are mapped to Bid Opening copy here
(§7.1 "Product vocabulary"), so no second conflict message is ever shown.
Each blocked action also returns its concrete reasons, holder and fix
(§8 closing rule); the message alone is never the whole answer."""

from __future__ import annotations

import frappe

MESSAGES: dict[str, str] = {
	"BOP_DEADLINE_NOT_REACHED": "Bids can be opened after submissions close at {deadline}.",
	"BOP_CLOSE_MANIFEST_UNAVAILABLE": "We can’t confirm the bids received at the deadline yet. Opening cannot start.",
	"BOP_COMMITTEE_INCOMPLETE": "Appoint at least three opening committee members before starting.",
	"BOP_INDEPENDENT_MEMBER_REQUIRED": "Appoint a committee member who was not involved in processing this Tender and will not evaluate it.",
	"BOP_MEMBER_ABSENT": "Opening cannot start because {name} has not joined.",
	"BOP_OPENING_PROFILE_UNAVAILABLE": "Bid opening isn’t available yet.",
	"BOP_CREDENTIAL_UNAVAILABLE": "Opening access is not ready yet.",
	"BOP_PACKAGE_MISMATCH": "Opening is paused while Opening access support checks this bid against the submissions received at the deadline.",
	"BOP_PACKAGE_UNREADABLE": "This bid could not be opened. Opening access support is checking it; you can retry when they resolve it.",
	"BOP_READOUT_INCOMPLETE": "Read out and record every opened bid before ending the opening.",
	"BOP_ATTESTATION_MISSING": "The opening record still needs signatures from the appointed members.",
	"BOP_REGISTER_NOT_READY": "The opening register is still being prepared. You can check its status here.",
	"BOP_VERSION_CONFLICT": "Someone updated this opening record. Refresh the page before continuing.",
}
AFTER_START: dict[str, str] = {
	"BOP_MEMBER_ABSENT": "Opening is paused because {name} is not present.",
	"BOP_CREDENTIAL_UNAVAILABLE": "Opening is paused because secure access is unavailable.",
}
ERROR_CODES: frozenset[str] = frozenset(MESSAGES)

#: BOP-CHG-001 v0.10 §7.1 and PRC-CHG-001 v0.9 §8: the Bid Opening wording of
#: each Proceedings error.
PRC_FINAL = "This opening record is final. Add a correction if a fact needs to change."
PRC_MAP: dict[str, tuple[str, str]] = {
	"PRC_VERSION_CONFLICT": ("BOP_VERSION_CONFLICT", MESSAGES["BOP_VERSION_CONFLICT"]),
	"PRC_ALREADY_FINALIZED": ("PRC_ALREADY_FINALIZED", PRC_FINAL),
	"PRC_TARGET_CHANGED": ("PRC_TARGET_CHANGED", "The opening record changed. Review the latest version before signing."),
	"PRC_MEMBER_REQUIRED": ("PRC_MEMBER_REQUIRED", "You are not an appointed member for this opening."),
	"PRC_PROOF_UNVERIFIED": ("PRC_PROOF_UNVERIFIED", "We could not verify your signature. Follow the steps shown here."),
	"PRC_EVIDENCE_INCOMPLETE": ("PRC_EVIDENCE_INCOMPLETE", "Some opening details are still missing. Review the items shown here."),
	"PRC_START_BLOCKED": ("PRC_START_BLOCKED", "The opening session cannot start yet. Review the opening requirement shown here."),
	"PRC_OWNER_UNAVAILABLE": ("PRC_OWNER_UNAVAILABLE", "This opening record is not available."),
}


class BidOpeningError(frappe.ValidationError):
	def __init__(self, code: str, message: str, detail: dict | None = None):
		self.code = code
		self.detail = detail or {}
		super().__init__(message)


def message(code: str, *, started: bool = False, **facts) -> str:
	if code not in ERROR_CODES:
		raise ValueError(f"{code!r} is not part of the BOP-CHG-001 v0.10 §8 error contract.")
	template = AFTER_START.get(code, MESSAGES[code]) if started else MESSAGES[code]
	return template.format(**facts)


def fail(code: str, detail: dict | None = None, *, started: bool = False, **facts) -> None:
	raise BidOpeningError(code, message(code, started=started, **facts), detail)


def from_prc(code: str) -> tuple[str, str]:
	return PRC_MAP[code]
