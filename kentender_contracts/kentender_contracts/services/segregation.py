# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The six separations of §6.1 (CM-CHG-001 v0.8; plan D11; tracker CM8-310), evaluated at commit time from the **actual** history.

Each function takes the identities that really signed, made or recorded (read by the caller from the signature, arrival, change and native-document records, never
from a task or an assignment), so a reassignment cannot erase an earlier act. A refusal is `CM_SEGREGATION`: it names only the actor's **own** earlier act and the
kind of person who can act, never another person's protected assignment ("Name eligible capacity without revealing protected assignments", §8). These are
KenTender product controls (CM-OD-09 and the §6.1 list); native permissions do not waive them.

Comparison ignores letter case: identities are e-mail addresses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from kentender_contracts.services.errors import fail


@dataclass(frozen=True)
class Separation:
	key: str
	rule: str  # §6.1, near-verbatim
	eligible: str  # who can act instead


SEPARATIONS: tuple[Separation, ...] = (
	Separation("certifier_not_acceptance_signer", "An acceptance-report signer cannot sign procurement certification of a claim supported by that acceptance (CM-OD-09).", "A separately authorised certifier"),
	Separation("receiver_not_acceptance_signer", "A receiver cannot sign acceptance for the same arrival they recorded.", "An appointed inspector who did not record the arrival"),
	Separation("change_roles_separate", "A change requester cannot sign its independent recommendation or make the final decision; an appointed reviewer cannot make that same final decision.", "The Accounting Officer, or the person the route names"),
	Separation("finance_independence", "A Finance maker cannot approve their own invoice or payment; a payment maker or procurement certifier cannot execute or confirm that same payment settlement.", "A different person holding Finance approval, who neither made nor certified the payment"),
	Separation("member_not_conflicted", "A conflicted member cannot observe, sign or decide the affected scope.", "A replacement appointed for the scope"),
	Separation("supplier_signs_only_as_signatory", "Only current supplier signatories sign agreements and amendments; bid submission power is not reused as contract invoice authority.", "A current supplier signatory (to sign) or a current supplier representative (to claim)"),
)
BY_KEY = {s.key: s for s in SEPARATIONS}


def _norm(users: Iterable[str]) -> set[str]:
	return {u.strip().lower() for u in users if u}


def _refuse(key: str, incompatibility: str) -> None:
	fail("CM_SEGREGATION", separation=key, incompatibility=incompatibility, rule=BY_KEY[key].rule, eligible=BY_KEY[key].eligible)


def certifier_not_acceptance_signer(actor: str, acceptance_signers: Iterable[str]) -> None:
	if actor.lower() in _norm(acceptance_signers):
		_refuse("certifier_not_acceptance_signer", "You signed the acceptance report that supports this claim.")


def receiver_not_acceptance_signer(actor: str, arrival_recorders: Iterable[str]) -> None:
	if actor.lower() in _norm(arrival_recorders):
		_refuse("receiver_not_acceptance_signer", "You recorded the arrival this acceptance covers.")


def change_roles_separate(actor: str, *, action: str, requesters: Iterable[str], recommenders: Iterable[str], reviewers: Iterable[str]) -> None:
	"""`action` is `recommend` or `decide`. A requester may do neither; a recommender or an appointed reviewer may not decide."""
	if action not in ("recommend", "decide"):
		raise ValueError("action is 'recommend' or 'decide'")
	me = actor.lower()
	if me in _norm(requesters):
		_refuse("change_roles_separate", f"You requested this change, so you cannot {action} it.")
	if action == "decide" and me in _norm(recommenders) | _norm(reviewers):
		_refuse("change_roles_separate", "You recommended or reviewed this change, so you cannot make the final decision on it.")


def finance_maker_not_approver(actor: str, makers: Iterable[str]) -> None:
	if actor.lower() in _norm(makers):
		_refuse("finance_independence", "You prepared this invoice or payment, so you cannot approve it.")


def settlement_confirmer_independent(actor: str, *, makers: Iterable[str], certifiers: Iterable[str]) -> None:
	me = actor.lower()
	if me in _norm(makers):
		_refuse("finance_independence", "You prepared this payment, so you cannot confirm its settlement.")
	if me in _norm(certifiers):
		_refuse("finance_independence", "You certified the invoice behind this payment, so you cannot confirm its settlement.")


def member_not_conflicted(actor: str, conflicted: Iterable[str]) -> None:
	if actor.lower() in _norm(conflicted):
		_refuse("member_not_conflicted", "You have a recorded conflict on this scope.")


def supplier_signs_only_as_signatory(actor: str, *, signatories: Iterable[str], action: str, representatives: Iterable[str] = ()) -> None:
	"""`action` is `sign` (agreement or amendment: a current signatory) or `claim` (invoice, correction, reply: a current representative or signatory)."""
	me = actor.lower()
	if action == "sign":
		if me not in _norm(signatories):
			_refuse("supplier_signs_only_as_signatory", "Only a current supplier signatory can sign for the supplier.")
	elif action == "claim":
		if me not in _norm(representatives) | _norm(signatories):
			_refuse("supplier_signs_only_as_signatory", "Only a current supplier representative or signatory can submit a claim for this contract.")
	else:
		raise ValueError("action is 'sign' or 'claim'")
