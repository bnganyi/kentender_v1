# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The contract-specific subject bindings Contract Management owns (CM-CHG-001 v0.8 sections 5.6, 6.2, 6.2.1; plan D11).

A binding **supplements** the registered responsibility (`authority.py`); neither grants alone. These providers read the records the packages create:

* inspector / technical certifier: the effective **appointment** (`Contract Appointment`, AO-appointed, within its dates), and for acting (not for reading) the member's own **declaration of interest**
  with no recorded conflict -- "Each member personally declares interest before acting. A declared conflict suspends that person's affected authority";
* entity signatory: the **mandate** named on the case's agreement (`terms_json.parties.entity`), which the preparer can name only for a person who holds the Entity contract signing responsibility.

`authority` falls back to these when no other provider is registered for a capacity, so every reader and every command sees the same answer without an import-order dependency."""

from __future__ import annotations

from typing import Any, Callable

import frappe
from frappe.utils import get_datetime

from kentender_contracts.services import clock, records

APPOINTMENT = "Contract Appointment"
AGREEMENT = "Contract Agreement Version"


def effective_appointment(case: str, at=None) -> dict[str, Any] | None:
	"""The appointment in force at `at`: the latest Appointed version whose dates cover it."""
	moment = get_datetime(at) if at else clock.now()
	for row in frappe.get_all(APPOINTMENT, filters={"contract_case": case, "state": "Appointed"}, fields=["name", "version_no", "members_json", "effective_from", "effective_to", "scope", "reference", "acceptance"],
			order_by="version_no desc"):
		if row.effective_from and get_datetime(row.effective_from) > moment:
			continue
		if row.effective_to and get_datetime(row.effective_to) <= moment:
			continue
		return {"appointment": row.name, "version": row.version_no, "members": records.loads(row.members_json, []), "scope": row.scope, "reference": row.reference, "acceptance": row.acceptance or "Committee accepts"}
	return None


def member(case: str, user: str, at=None) -> dict[str, Any] | None:
	found = effective_appointment(case, at)
	if not found:
		return None
	mine = next((m for m in found["members"] if m["user"].lower() == (user or "").lower()), None)
	return {**found, "member": mine} if mine else None


def _inspector(case: str, user: str, at, *, acting: bool) -> dict[str, Any] | None:
	found = member(case, user, at)
	if not found:
		return None
	mine = found["member"]
	if acting and (not mine.get("declared_at") or mine.get("conflict")):
		return None
	return {"appointment": found["appointment"], "capacity": mine.get("capacity", "")}


def inspector_act(case: str, user: str, at=None):
	return _inspector(case, user, at, acting=True)


def inspector_read(case: str, user: str, at=None):
	return _inspector(case, user, at, acting=False)


def _certifier(case: str, user: str, at, *, acting: bool):
	found = _inspector(case, user, at, acting=acting)
	if not found:
		return None
	mine = member(case, user, at)["member"]
	return found if mine.get("certifier") else None


def certifier_act(case: str, user: str, at=None):
	return _certifier(case, user, at, acting=True)


def certifier_read(case: str, user: str, at=None):
	return _certifier(case, user, at, acting=False)


def entity_signatory(case: str, user: str, at=None) -> dict[str, Any] | None:
	for row in frappe.get_all(AGREEMENT, filters={"contract_case": case, "state": ["!=", "Superseded"]}, fields=["name", "terms_json", "version_no"], order_by="version_no desc"):
		entity = ((records.loads(row.terms_json).get("parties") or {}).get("entity")) or {}
		if entity.get("user") and entity["user"].lower() == (user or "").lower():
			return {"mandate": row.name, "version": row.version_no}
	return None


ACT: dict[str, Callable] = {"inspector": inspector_act, "technical certifier": certifier_act, "entity signatory": entity_signatory}
READ: dict[str, Callable] = {"inspector": inspector_read, "technical certifier": certifier_read, "entity signatory": entity_signatory}
