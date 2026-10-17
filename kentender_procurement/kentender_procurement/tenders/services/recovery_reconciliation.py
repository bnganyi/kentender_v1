# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Reconciling Tenders cancelled before whole-Tender cancellation recovery existed (REQ-CHG-001 v1.20 §19.1 / §20, handoff step 6).

A cancelled Tender whose funding is still held is brought into the SAME verified recovery every new cancellation goes through, never
into a balance reset:

1. `inventory()` is read-only. For each cancelled Tender it asks the owners and classifies it: eligible; already registered; partial
   legacy effect; converted or surviving obligation; released for another reason; unmapped (the lineage or a reservation or a
   drawdown cannot be found); ambiguous (an owner could not say). Nothing is written, nothing is repaired.
2. `reconcile(dry_run=True)` reports what it would register. With `dry_run=False` it registers one recovery per unregistered cancelled
   Tender from the cancellation as it was decided (its recorded digest, time and Accounting Officer — no cancellation or approval event
   is fabricated and no decision rewritten), tagged `Legacy reconciliation` and `CR-LEGACY-1`, and lets the recovery worker carry it
   out: an eligible one is restored exactly, any other becomes Needs attention with the owner's own reason and keeps its resources held.
   It is idempotent: a Tender already registered is skipped, so a second run creates nothing.

Run it first on a copy, read the inventory with the owner, and apply it to a target site only under that site's own change process
(`make cancellation-recovery-inventory`, `make cancellation-recovery-reconcile`, `APPLY=1` to apply)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import recovery_legacy
from kentender_procurement.tenders.services import cancellation_recovery_basis, envelope, recovery_gateway

VERSION = "CR-LEGACY-1"
ELIGIBLE = "eligible"
REGISTERED = "already registered"
PARTIAL = "partial legacy effect"
OBLIGATION = "converted or surviving obligation"
OTHER_REASON = "released for another reason"
UNMAPPED = "unmapped"
AMBIGUOUS = "ambiguous"
CLASSES = (ELIGIBLE, REGISTERED, PARTIAL, OBLIGATION, OTHER_REASON, UNMAPPED, AMBIGUOUS)


def _cancelled() -> list[dict[str, Any]]:
	return frappe.get_all(
		"Tender", filters={"overall_status": "Cancelled", "cancellation": ("is", "set")},
		fields=["name", "tender_reference", "cancellation", "requisition_handoff", "requisition", "fixture_namespace"], order_by="creation asc", limit_page_length=0,
	)


def classify(tender: dict[str, Any]) -> dict[str, Any]:
	"""One cancelled Tender's class and reason, from the owners' own answers. Read-only."""
	base = {"tender": tender["name"], "tender_reference": tender["tender_reference"], "cancellation": tender["cancellation"]}
	owned = recovery_legacy.classify(tender=tender["name"], cancellation=tender["cancellation"], handoff=cstr(tender["requisition_handoff"]))
	if owned["class"] in (REGISTERED, UNMAPPED, AMBIGUOUS, PARTIAL, OBLIGATION, OTHER_REASON):
		return {**base, **owned}
	# the Requisitions side supports a recovery; Tenders adds what only the Tender and Award can say
	basis = cancellation_recovery_basis.recovery_basis(tender=tender["name"], cancellation=tender["cancellation"], recovery_id="")
	if basis["verdict"] == "negative":
		return {**base, **owned, "class": OBLIGATION, "reason": cstr(basis.get("reason"))}
	if basis["verdict"] == "unavailable":
		return {**base, **owned, "class": AMBIGUOUS, "reason": cstr(basis.get("reason"))}
	return {**base, **owned, "class": ELIGIBLE}


def inventory() -> dict[str, Any]:
	"""Every cancelled Tender with its class and reason, and the counts. Read-only."""
	rows = [classify(t) for t in _cancelled()]
	counts = {c: sum(1 for r in rows if r["class"] == c) for c in CLASSES}
	return {"version": VERSION, "total": len(rows), "counts": counts, "tenders": rows}


def reconcile(*, dry_run: bool = True) -> dict[str, Any]:
	"""Register the recovery of every unregistered cancelled Tender; the recovery worker then carries each out. `dry_run` writes
	nothing. Returns the inventory it acted on and what it did to each Tender."""
	report = inventory()
	actions = []
	for row in report["tenders"]:
		if row["class"] == REGISTERED:
			actions.append({"tender": row["tender"], "action": "skipped", "why": "already registered", "recovery": row.get("recovery")})
			continue
		if dry_run:
			actions.append({"tender": row["tender"], "action": "would register", "class": row["class"], "reason": row.get("reason", "")})
			continue
		actions.append(_register(row))
	return {"version": VERSION, "dry_run": dry_run, **{k: report[k] for k in ("total", "counts")}, "actions": actions}


def _register(row: dict[str, Any]) -> dict[str, Any]:
	root = frappe.get_doc("Tender", row["tender"])
	cancellation = frappe.get_doc("Tender Cancellation", row["cancellation"])
	savepoint = f"recon_{frappe.generate_hash(length=8)}"
	frappe.db.savepoint(savepoint)
	try:
		registered = recovery_gateway.register(
			root=root, cancellation=cancellation, cancellation_digest=cstr(cancellation.cancellation_digest), decided_at=cancellation.decided_at, actor=cstr(cancellation.decided_by),
			origin="Legacy reconciliation", reconciliation_version=VERSION,
		)
		if not cstr(cancellation.resource_recovery):
			envelope.bump(cancellation, resource_recovery=registered["recovery"])
		frappe.db.release_savepoint(savepoint)
	except Exception as exc:  # noqa: BLE001 — a Tender that cannot be registered is reported, never forced
		frappe.db.rollback(save_point=savepoint)
		code = getattr(exc, "requisitions_code", "") or (exc.__class__.__name__)
		return {"tender": row["tender"], "action": "not registered", "class": row["class"], "reason": cstr(exc)[:300], "code": code}
	return {"tender": row["tender"], "action": "registered", "class": row["class"], "recovery": registered["recovery"], "reused": registered["reused"]}
