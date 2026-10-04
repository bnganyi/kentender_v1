# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.9 §9.3 / KT-STD-001 §11 — idempotent replay for the seven
governance commands (tracker D7).

A client mints one `idempotency_key` per user attempt (save, submit, return,
approve, close). The first execution records the command's result on a
`Command recorded` Budget Audit Event carrying the key and a digest of the
immutable payload. A repeat with the same key and the same digest returns
the recorded result without a second effect; the same key with a different
digest is `BUDGET_IDEMPOTENCY_CONFLICT`. Commands without a key run as
before — the journal is additive, never a gate.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

import frappe
from frappe import _

EVENT_COMMAND = "Command recorded"
_EXCLUDED = ("idempotency_key",)


def payload_digest(payload: dict[str, Any]) -> str:
	clean = {k: v for k, v in (payload or {}).items() if k not in _EXCLUDED}
	text = json.dumps(clean, sort_keys=True, default=str, separators=(",", ":"))
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


def conflict(key: str) -> dict[str, Any]:
	return {
		"ok": False,
		"code": "BUDGET_IDEMPOTENCY_CONFLICT",
		"errors": {"idempotency_key": _("This request differs from the original attempt. Check the original result before retrying; no new effect was created.")},
		"idempotency_key": key,
	}


def run_idempotent(*, payload: dict[str, Any], fn: Callable[[], dict[str, Any]], budget_for: Callable[[dict[str, Any]], str | None]) -> dict[str, Any]:
	"""Run `fn` once per (key, payload digest). `budget_for(result)` names
	the Procurement Budget the journal row belongs to (the ledger's `budget`
	link is mandatory); when it cannot be resolved — a failed first create —
	nothing is journaled and a retry simply re-runs the same validation."""
	key = (payload.get("idempotency_key") or "").strip()
	if not key:
		return fn()
	digest = payload_digest(payload)
	hit = frappe.db.get_value(
		"Budget Audit Event", {"idempotency_key": key}, ["payload_digest", "command_result", "budget"], as_dict=True
	)
	if hit:
		if (hit.payload_digest or "") != digest:
			return conflict(key)
		try:
			replayed = json.loads(hit.command_result or "{}")
		except ValueError:
			replayed = {}
		replayed["replayed"] = True
		return replayed

	result = fn()
	budget = budget_for(result)
	if budget:
		from kentender_budget.services.budget_audit_contracts import safe_record_event

		safe_record_event(
			budget=budget,
			budget_version=(result.get("version") or {}).get("id") if isinstance(result.get("version"), dict) else None,
			event_type=EVENT_COMMAND,
			actor=frappe.session.user,
			correlation_id=key,
			calling_module="Budget & Funding",
			idempotency_key=key,
			payload_digest=digest,
			command_result=json.dumps(result, default=str),
		)
	return result
