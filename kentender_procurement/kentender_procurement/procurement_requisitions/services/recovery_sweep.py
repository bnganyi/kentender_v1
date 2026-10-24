# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.20 §9.1D — the worker that carries out registered whole-Tender cancellation recoveries.

Run by the scheduler (`hooks.py`, every tick) and by an operator or a test through `run_one`. It selects Pending recoveries that are due
(never a Needs attention one: that waits for the owner to correct the cause and for a technical operator's retry), one per transaction,
oldest first, and commits each separately so one recovery's failure never undoes another's. This bench runs no RQ worker (AGENTS.md
§8.1) and the development site's scheduler is off, so `make cancellation-recovery-run` is the manual run; a recovery shown as Pending
there is truthfully waiting for it."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from kentender_procurement.procurement_requisitions.services import cancellation_recovery

DOCTYPE = cancellation_recovery.DOCTYPE


def due(limit: int = 25) -> list[str]:
	"""Pending recoveries whose next attempt time has come (or was never set), oldest first."""
	rows = frappe.db.sql(
		f"select name from `tab{DOCTYPE}` where status = %s and (next_attempt_at is null or next_attempt_at <= %s) order by creation asc limit %s",
		(cancellation_recovery.PENDING, now_datetime(), int(limit)),
	)
	return [row[0] for row in rows]


def run_one(recovery: str) -> dict:
	"""Attempt one recovery inside the caller's transaction (never commits)."""
	return cancellation_recovery.recover_cancelled_tender_resources(recovery=recovery)


def run(limit: int = 25) -> list[dict]:
	"""The scheduler entry: attempt each due recovery in its own transaction."""
	results = []
	for name in due(limit):
		try:
			results.append(run_one(name))
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"Cancellation recovery sweep failed for {name}")
	return results
