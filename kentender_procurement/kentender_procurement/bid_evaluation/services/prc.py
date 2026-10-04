# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Calling Proceedings for one evaluation case (EVL-CHG-001 v0.4 §6; plan D4).

Always inside an Evaluation command (`records.command` puts `acting(case)` in
force), after Evaluation's own guards. Keys are derived from the Evaluation
command's own idempotency key so a replay reaches Proceedings with the same
identity."""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.bid_evaluation.services import prc_owner

OWNER_TYPE = prc_owner.OWNER_TYPE
SYSTEM = "system"


def ref(doc) -> dict[str, Any]:
	version = frappe.db.get_value("Proceeding", {"owner_key": f"{OWNER_TYPE}:{doc.name}"}, "record_version")
	return {"owner_type": OWNER_TYPE, "owner_id": doc.name, "expected_version": int(version or 0)}


def key(base: str, step: str) -> str:
	return f"{base}:{step}"


def bounded(owner_event_id: str) -> str:
	"""An owner event id within the Proceedings event key's length: a long id
	(a case, bid, requirement and idempotency key) keeps its kind and becomes
	a stable digest of the whole, so a replay reaches the same event."""
	import hashlib

	if len(owner_event_id) <= 60:
		return owner_event_id
	return f"{owner_event_id.split(':', 1)[0]}:{hashlib.sha256(owner_event_id.encode()).hexdigest()[:40]}"


def create(doc, idempotency_key: str) -> dict[str, Any]:
	from kentender_procurement.proceedings.services import lifecycle

	with prc_owner.acting(doc.name):
		return lifecycle.create_proceeding(owner_type=OWNER_TYPE, owner_id=doc.name, title=f"Bid evaluation {doc.tender_reference}",
			idempotency_key=key(idempotency_key, "prc-create"), actor=SYSTEM)


def owner_event(doc, event_type: str, owner_event_id: str, payload: dict[str, Any], *, idempotency_key: str, note: str = "") -> str:
	from kentender_procurement.proceedings.services import sessions

	with prc_owner.acting(doc.name):
		return sessions.append_owner_event(**ref(doc), event_type=event_type, owner_event_id=bounded(owner_event_id), payload=payload, note=note,
			idempotency_key=key(idempotency_key, f"prc-{owner_event_id}"), actor=SYSTEM)["event_id"]


def roster(doc, rows: list[dict[str, Any]], reason: str, *, owner_event_id: str, idempotency_key: str) -> str:
	from kentender_procurement.proceedings.services import sessions

	with prc_owner.acting(doc.name):
		return sessions.record_roster(**ref(doc), roster=rows, reason=reason, owner_event_id=bounded(owner_event_id), idempotency_key=key(idempotency_key, "prc-roster"),
			actor=SYSTEM)["event_id"]
