# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The permitted-work and correction matrices of CM-CHG-001 v0.8 §5.17 and §5.18 as data (plan D5; tracker CM8-304).

The specification's wording stays in the specification. A row here carries the row's **name verbatim** (the first column),
which `test_cm_recovery_matrix` compares with the approved document, and the model the code needs: which operation raises
it, which consequences it blocks, who recovers it, and which wording the screens use. `reconciliation/recovery_matrix.md`
is generated from this file and the specification by `tools/build_recovery_matrix.py`.

Subject convention for operation intents (so a pending intent finds its row): `agreement`, `acceptance:<id>`, `invoice:<id>`,
`payment:<id>`, `amendment:<id>`, `closure`, `termination`. Pure Python, no Frappe."""

from __future__ import annotations

from dataclasses import dataclass

from kentender_contracts.services.capabilities import CAPABILITIES

IN_FLIGHT_OR_PENDING = ("Recorded", "Attempting", "Failed", "Uncertain")


@dataclass(frozen=True)
class Operation:
	"""A §5.17 row: a pending or failed cross-owner operation."""

	id: str
	name: str  # first column of the specification, verbatim
	kinds: tuple[str, ...]  # operation kinds whose pending intents raise this row ("" when it is raised by a state, not an intent)
	subject: str  # prefix of the intent subject that selects the row among rows sharing a kind ("" = any)
	states: tuple[str, ...]  # intent states in which the row applies
	blocks: tuple[str, ...]  # consequences blocked while the row applies (keys of CAPABILITIES)
	owner: str  # who recovers it (written onto the intent as its recovery owner)
	display: str = ""  # state wording quoted by the specification, shown as the truthful state
	condition: str = ""  # state-raised rows: the condition a provider reports


@dataclass(frozen=True)
class Correction:
	"""A §5.18 row: a changed fact and its required treatment."""

	id: str
	name: str  # first column of the specification, verbatim
	blocks: tuple[str, ...]  # consequences held for the affected scope while the correction is open
	owner: str
	invalidates: str = ""  # what the change invalidates instead of (or as well as) holding


OPERATIONS: tuple[Operation, ...] = (
	Operation("R17-01", "Signature outcome uncertain", ("Signing attempt",), "", ("Attempting", "Uncertain"),
		("new_signing_attempt", "activate_contract", "convert_funding", "create_order"), "Trust recovery"),
	Operation("R17-02", "Agreement effective; Budget conversion or PO failed", ("Funding conversion", "Purchase order"), "agreement", IN_FLIGHT_OR_PENDING,
		("post_receipt", "new_spending", "pay"), "Technical recovery; Budget owner", display="Contract signed — funding/order update pending"),
	Operation("R17-03", "Acceptance signed; receipt/asset posting failed", ("Accepted receipt",), "", IN_FLIGHT_OR_PENDING,
		("certify_invoice", "pay", "use_goods"), "Technical recovery"),
	Operation("R17-04", "Native invoice posting uncertain/failed", ("Native invoice",), "", IN_FLIGHT_OR_PENDING,
		("pay",), "Finance; technical recovery"),
	Operation("R17-05", "Native payment posting uncertain/failed", ("Native payment",), "", IN_FLIGHT_OR_PENDING,
		("pay", "confirm_settlement"), "Finance; technical recovery"),
	Operation("R17-06", "Posted payment; settlement not confirmed", (), "", (),
		("claim_cash_paid", "pay"), "Finance settlement authority", display="Payment recorded — settlement not confirmed", condition="settlement_unconfirmed"),
	Operation("R17-07", "Effective amendment; Budget/order update pending", ("Funding adjustment", "Purchase order"), "amendment", IN_FLIGHT_OR_PENDING,
		("new_spending", "pay"), "Technical recovery; Budget owner"),
	Operation("R17-08", "Closure signed; owner financial finalisation failed", ("Funding closure",), "", IN_FLIGHT_OR_PENDING,
		("mark_financially_finalised", "release_funds"), "Budget owner; Finance", display="Funding finalisation pending"),
)

CORRECTIONS: tuple[Correction, ...] = (
	Correction("R18-01", "Acceptance report before full proof", ("post_receipt",), "Inspection chair"),
	Correction("R18-02", "Effective acceptance before native posting", ("post_receipt",), "Inspection committee"),
	Correction("R18-03", "Acceptance/return after native receipt", ("certify_invoice", "pay", "use_goods"), "Technical recovery; Finance"),
	Correction("R18-04", "Corrected claim before native posting", ("pay",), "Head of procurement"),
	Correction("R18-05", "Claim/accepted quantity changed after liability posting", ("pay",), "Finance"),
	Correction("R18-06", "Accepted-and-paid goods returned/replaced", ("certify_invoice", "pay"), "Finance"),
	Correction("R18-07", "Amount/beneficiary changes during payment review", (), "Finance maker", invalidates="pending payment approval"),
	Correction("R18-08", "Payment reversed or settlement correction", ("pay",), "Finance"),
	Correction("R18-09", "New evidence after closure", ("pay", "certify_invoice", "release_funds", "vary_contract"), "Authorising officer"),
)

#: Native documents must be reversed in this order; the spike proved a later document blocks the cancellation of an earlier one.
REVERSAL_ORDER: tuple[tuple[str, str], ...] = (
	("Quality Inspection", "Purchase Receipt"),
	("Purchase Invoice", "Purchase Receipt"),
	("Asset", "Purchase Receipt"),
)


def _check() -> None:
	ids = [r.id for r in OPERATIONS + CORRECTIONS]
	assert len(ids) == len(set(ids)), "Matrix row ids must be unique."
	for row in OPERATIONS + CORRECTIONS:
		unknown = set(row.blocks) - set(CAPABILITIES)
		assert not unknown, f"{row.id} blocks consequences that do not exist: {sorted(unknown)}"


_check()


def operation_for(kind: str, subject: str = "", state: str = "") -> Operation | None:
	"""The §5.17 row a pending intent of this kind, subject and state raises. None when the kind has no row (a dispatch), or the
	row does not apply in this state (a settled intent). A kind that several rows share (a purchase order is created at formation
	and changed by an amendment) is told apart by the subject convention; an unrecognised subject is a programming error."""
	by_kind = [r for r in OPERATIONS if kind in r.kinds]
	applicable = [r for r in by_kind if not state or state in r.states]
	if not applicable:
		return None
	if len(applicable) == 1:
		return applicable[0]
	for row in applicable:
		if row.subject and subject.startswith(row.subject):
			return row
	raise ValueError(f"{kind!r} intent with subject {subject!r} matches none of {[r.id for r in applicable]}; follow the subject convention.")


def correction(row_id: str) -> Correction:
	return next(r for r in CORRECTIONS if r.id == row_id)
