# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Durable delivery of the existing `TenderCancelled` event to its consumers (TPR-CHG-001 v0.24 §5.12, §7.6; BOP-OF-AC-007).

There is one cancellation event family. `CancelTender` commits the event once; in the same transaction it writes one `Tender Event Delivery` row per
registered consumer (`kt_tender_cancellation_consumers`). A row turns Delivered only when the consumer returns its receipt; a failure is kept (attempts,
error code) and retried from the SAME event by `run`, which the cancelling request runs right after its commit and the scheduler runs again. The
cancellation itself is terminal whatever a consumer does: delivery is tracked independently and never reopens or undoes it, and a consumer that is down
only delays its own closure.

A consumer is a module with `NAME`, `LABEL`, `available() -> {"available": bool, "reason": str}` and
`deliver(*, tender, cancellation, event_id, payload) -> {"receipt": str}`. `deliver` must be idempotent on the cancellation: a replay, a duplicate or an
out-of-order delivery creates no second closure, task receipt or obligation."""

from __future__ import annotations

import importlib
import json
from typing import Any

import frappe
from frappe.utils import cint, cstr

from kentender_procurement.tenders.services import clock, envelope

DOCTYPE = "Tender Event Delivery"
EVENT_TYPE = "TenderCancelled"
HOOK = "kt_tender_cancellation_consumers"


def consumers() -> list[Any]:
	out = []
	for path in frappe.get_hooks(HOOK) or []:
		out.append(importlib.import_module(path))
	return out


def _module(name: str):
	return next((m for m in consumers() if m.NAME == name), None)


def availability() -> dict[str, Any]:
	"""Whether every consumer the cancellation must reach can take it now. A consumer that cannot say is unavailable."""
	reasons = []
	for module in consumers():
		try:
			answer = module.available() or {}
		except Exception:
			frappe.log_error(title=f"Cancellation consumer availability failed: {module.NAME}")
			answer = {"available": False, "reason": "The consumer could not be reached."}
		if not answer.get("available"):
			reasons.append({"consumer": module.NAME, "label": module.LABEL, "reason": cstr(answer.get("reason")) or "Unavailable"})
	return {"available": not reasons, "reasons": reasons}


def register(root, event, *, cancellation: str) -> list[Any]:
	"""One Pending row per consumer for this event, in the cancellation's own transaction. A repeat registers nothing."""
	rows = []
	for module in consumers():
		key = f"{event.event_id}:{module.NAME}"
		if frappe.db.exists(DOCTYPE, {"delivery_key": key}):
			continue
		rows.append(envelope.insert(frappe.get_doc({
			"doctype": DOCTYPE, "delivery_key": key, "event_id": event.event_id, "event_type": event.event_type, "tender": root.name, "consumer": module.NAME,
			"subject_id": cancellation, "status": "Pending", "attempts": 0, "fixture_namespace": cstr(root.fixture_namespace),
		})))
	return rows


def ensure_registered(tender: str) -> int:
	"""A Tender cancelled before the ledger existed has its event but no rows: register them from that same event (the sweep calls this)."""
	event = frappe.db.get_value("Tender Event", {"tender": tender, "event_type": EVENT_TYPE}, ["name", "event_id", "event_type", "subject_id"], as_dict=True)
	if not event:
		return 0
	root = frappe.db.get_value("Tender", tender, ["name", "fixture_namespace"], as_dict=True)
	return len(register(root, event, cancellation=cstr(event.subject_id)))


def attempt(name: str) -> dict[str, Any]:
	"""One delivery attempt of one row, from the original event. Returns the row's status. Commits."""
	row = frappe.get_doc(DOCTYPE, name, for_update=True)
	if row.status == "Delivered":
		frappe.db.commit()
		return {"delivery": name, "status": "Delivered"}
	module = _module(row.consumer)
	event = frappe.db.get_value("Tender Event", {"event_id": row.event_id}, ["payload"], as_dict=True)
	payload = json.loads(event.payload or "{}") if event else {}
	savepoint = f"ted_{frappe.generate_hash(length=10)}"
	frappe.db.savepoint(savepoint)
	try:
		if module is None:
			raise LookupError(f"no consumer {row.consumer}")
		answer = module.deliver(tender=row.tender, cancellation=cstr(row.subject_id), event_id=row.event_id, payload=payload) or {}
		receipt = cstr(answer.get("receipt")) if isinstance(answer, dict) else cstr(answer)
		if not receipt:
			raise ValueError("the consumer returned no receipt")
	except Exception as exc:  # noqa: BLE001 - kept on the row and retried; never undoes the cancellation
		frappe.db.rollback(save_point=savepoint)
		frappe.log_error(title=f"Cancellation delivery failed: {row.consumer} {row.tender}")
		envelope.bump(row, status="Failed", attempts=cint(row.attempts) + 1, last_attempt_at=clock.now(), error_code=type(exc).__name__, error_detail=cstr(exc)[:140])
		frappe.db.commit()
		return {"delivery": name, "status": "Failed"}
	frappe.db.release_savepoint(savepoint)
	envelope.bump(row, status="Delivered", attempts=cint(row.attempts) + 1, last_attempt_at=clock.now(), delivered_at=clock.now(), receipt_ref=receipt, error_code="", error_detail="")
	frappe.db.commit()
	return {"delivery": name, "status": "Delivered", "receipt": receipt}


def run(*, tender: str = "") -> dict[str, int]:
	"""Deliver every Pending or Failed row (of one Tender, when given), oldest first, each in its own transaction. Never raises."""
	done = {"delivered": 0, "failed": 0}
	filters: dict[str, Any] = {"status": ("in", ("Pending", "Failed"))}
	if tender:
		filters["tender"] = tender
	for name in frappe.get_all(DOCTYPE, filters=filters, pluck="name", order_by="creation asc"):
		try:
			result = attempt(name)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Cancellation delivery crashed: {name}")
			done["failed"] += 1
			continue
		done["delivered" if result["status"] == "Delivered" else "failed"] += 1
	return done


def after_commit(tender: str) -> None:
	"""The cancelling request delivers right after its commit, so no scheduler is needed for the usual case; the sweep covers a request that died first."""
	frappe.db.after_commit.add(lambda: run(tender=tender))


def status_for(tender: str) -> list[dict[str, Any]]:
	"""Per-consumer delivery state for the Tender page (read-only)."""
	out = []
	for row in frappe.get_all(DOCTYPE, filters={"tender": tender}, fields=["consumer", "status", "attempts", "receipt_ref", "error_code", "last_attempt_at", "delivered_at"],
			order_by="creation asc", limit_page_length=0):
		module = _module(row.consumer)
		out.append({"consumer": row.consumer, "label": getattr(module, "LABEL", row.consumer), "status": row.status, "attempts": cint(row.attempts), "receipt": cstr(row.receipt_ref),
			"error": cstr(row.error_code), "delivered_at": cstr(row.delivered_at)})
	return out
