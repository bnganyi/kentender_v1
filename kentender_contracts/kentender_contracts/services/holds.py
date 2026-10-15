# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Holds: scoped, independent restrictions (CM-CHG-001 v0.8 §3 Issue row, §5.17, §5.18, CM_HOLD in §8).

"Evaluate every open hold independently. The permitted action set is the intersection of all applicable guards; the most
prominent task never masks another restriction." A hold therefore (1) blocks named consequences (`capabilities.py`), never
"the contract"; (2) has an explicit scope: empty means the whole case, otherwise the subjects (line, quantity, invoice,
payment) it affects, and an unaffected subject stays eligible where separable; (3) names its owner and the evidence that
clears it. "A generic issue comment cannot lift it": nothing here lifts a hold. A hold exists only while its source condition
does, so it ends when the pending operation reconciles, the legal question is answered, or the issue is resolved by its
authorised disposition. Sources register a provider; the set of open holds is read fresh on every evaluation, so no stale
copy can allow an action. Providers: pending operations (below), the rule register (CM8-309), issues and corrections (Packages
B-E)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from kentender_contracts.services import intents, recovery
from kentender_contracts.services.capabilities import CAPABILITIES
from kentender_contracts.services.errors import Guards


@dataclass(frozen=True)
class Hold:
	key: str  # stable identity of the source condition, e.g. "operation:CM-OP-00012"
	kind: str  # Pending operation | Correction | Legal question | Issue | Restriction | Appointment
	reason: str  # plain words shown to the person who is blocked
	blocks: frozenset[str]
	owner: str  # who can act to clear it
	clearing: str  # the evidence that clears it
	scope: tuple[str, ...] = ()  # subjects affected; empty = the whole case

	def __post_init__(self) -> None:
		unknown = set(self.blocks) - set(CAPABILITIES)
		if unknown:
			raise ValueError(f"Hold {self.key} blocks consequences that do not exist: {sorted(unknown)}")

	def covers(self, subject: str | None) -> bool:
		"""A command that names its subject is blocked only by holds on that subject (or on the whole case). A command that names
		none, or a read of the whole case, sees every hold."""
		return not self.scope or subject is None or subject in self.scope


Provider = Callable[[str], Iterable[Hold]]
PROVIDERS: dict[str, Provider] = {}


def provider(name: str) -> Callable[[Provider], Provider]:
	def register(fn: Provider) -> Provider:
		PROVIDERS[name] = fn
		return fn

	return register


#: Modules that register a hold provider when imported. They are loaded the first time holds are read, so a process that never imported one cannot miss its hold.
PROVIDER_MODULES = ("kentender_contracts.services.security", "kentender_contracts.award_receiver", "kentender_contracts.services.payment", "kentender_contracts.services.adjustment", "kentender_contracts.services.warranty")


def _load() -> None:
	import importlib

	for name in PROVIDER_MODULES:
		importlib.import_module(name)


def open_holds(case: str) -> list[Hold]:
	"""Every hold open on the case, from every source, read fresh."""
	_load()
	return [hold for fn in PROVIDERS.values() for hold in fn(case)]


def blocking(case: str, capability: str, subject: str | None = None) -> list[Hold]:
	if capability not in CAPABILITIES:
		raise ValueError(f"{capability!r} is not a guarded consequence.")
	return [h for h in open_holds(case) if capability in h.blocks and h.covers(subject)]


def permitted(case: str, capability: str, subject: str | None = None) -> bool:
	return not blocking(case, capability, subject)


def permitted_set(case: str, subject: str | None = None) -> dict[str, list[Hold]]:
	"""Every consequence with the holds blocking it. The permitted set is the keys with an empty list: the intersection of all
	guards, in one pass."""
	holds = [h for h in open_holds(case) if h.covers(subject)]
	return {cap: [h for h in holds if cap in h.blocks] for cap in CAPABILITIES}


def require(case: str, capability: str, subject: str | None = None) -> None:
	"""Refuse with CM_HOLD, naming **every** hold that blocks, each with its reason, holder and what clears it."""
	guards = Guards()
	for hold in blocking(case, capability, subject):
		guards.add("CM_HOLD", hold=hold.key, kind=hold.kind, reason=hold.reason, holder=hold.owner, clears_with=hold.clearing, scope=list(hold.scope), consequence=capability)
	guards.raise_if_any()


def correction_hold(row_id: str, *, key: str, reason: str, scope: tuple[str, ...], clearing: str, owner: str = "") -> Hold:
	"""The hold a §5.18 correction places on the affected scope while its authorised decision is obtained."""
	row = recovery.correction(row_id)
	if not row.blocks:
		raise ValueError(f"{row_id} invalidates {row.invalidates}; it places no hold.")
	return Hold(key=key, kind="Correction", reason=reason, blocks=frozenset(row.blocks), owner=owner or row.owner, clearing=clearing, scope=scope)


@provider("operations")
def _pending_operations(case: str) -> list[Hold]:
	"""One hold per pending or failed cross-owner operation, shaped by its §5.17 row (`reconciliation/recovery_matrix.md`)."""
	found = []
	for op in intents.pending(case):
		row = recovery.operation_for(op["kind"], op["subject"], op["state"])
		if row is None or not row.blocks:
			continue
		found.append(Hold(key=f"operation:{op['intent']}", kind="Pending operation", reason=row.display or f"{row.name}.", blocks=frozenset(row.blocks),
			owner=op["recovery_owner"] or row.owner, clearing="The owner's result for this operation is read and linked, or it is refused and corrected.", scope=()))
	return found
