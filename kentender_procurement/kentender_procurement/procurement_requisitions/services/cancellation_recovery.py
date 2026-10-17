# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.20 §9.1D / §10.3 — whole-Tender cancellation recovery, coordinated by Requisitions.

When the Accounting Officer cancels a Tender, the exact unused Planning drawdown and Budget reservations its Requisition made are
restored together. Tenders owns the cancellation; Planning owns the allowance; Budget owns the reservations; Requisitions owns the
record that ties them (`Cancellation Resource Recovery`) and the two steps:

1. `register_cancellation_resource_recovery` — called by Tenders inside the cancellation transaction. It records one durable Pending
   recovery against the exact consumed lineage and places Planning's hold on every affected source. If it fails the cancellation does not
   commit. Once the cancellation commits it stays committed whatever the recovery does.
2. `recover_cancelled_tender_resources` — system-only, run by the scheduler sweep (or by an operator's retry). It asks Tenders for its
   verified basis, Budget for its account of each reservation, then in one transaction releases the complete reservation set, reverses
   the complete drawdown set, completes the recovery and removes the holds — or does none of it. Unavailable evidence leaves the
   recovery Pending (retried against the same intent with a backoff); an owner's proven refusal makes it Needs attention (never retried
   by itself); amounts are always those of the original authorisation, never recomputed, proportioned or guessed.

Lock order (proved by `test_cancellation_recovery_integration`): Tender, Award case (inside Tenders' basis read), then Requisition root,
its handoff, the recovery, then Budget (Version rows, Line rows, reservations), then Planning (Annual Plan Item, Plan Item root,
drawdowns, holds) — the order authorisation and revocation already take.

Nothing here commits; the sweep commits one recovery at a time."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import add_to_date, cstr, now_datetime

from kentender_core.services import cancellation_recovery_contract as tender_seam
from kentender_core.utils.instants import to_utc_iso
from kentender_procurement.procurement_requisitions.services import digest, eligibility_gateway, envelope, events, funding_gateway, records
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.owner_refusal import OwnerRefusal
from kentender_procurement.procurement_requisitions.services.requisition_roles import DEPARTMENTAL_ROLES

DOCTYPE = "Cancellation Resource Recovery"
PENDING, COMPLETED, NEEDS_ATTENTION = "Pending", "Completed", "Needs attention"
SERVICE = "Requisitions recovery service"
MAX_BACKOFF_SECONDS = 3600

# the typed reasons a recovery carries (REQ-CHG-001 v1.20 §9.1D)
TENDER_UNAVAILABLE = "TENDER_BASIS_UNAVAILABLE"
TENDER_NEGATIVE = "TENDER_BASIS_NEGATIVE"
LINEAGE_MISMATCH = "LINEAGE_MISMATCH"
MAPPING_MISSING = "SOURCE_MAPPING_MISSING"
BUDGET_UNSUPPORTED = "BUDGET_DOES_NOT_SUPPORT_RELEASE"
OWNER_REFUSED = "OWNER_REFUSED"
OWNER_UNAVAILABLE = "OWNER_UNAVAILABLE"


# --------------------------------------------------------------------------
# What the recovery is made of
# --------------------------------------------------------------------------


def _source_rows(version) -> list[dict[str, Any]]:
	return [
		{
			"drawdown_line_id": cstr(line.drawdown_line_id), "allocation_id": cstr(line.plan_item_line_id), "contributing_org_unit": cstr(line.contributing_org_unit),
			"drawdown_reference": cstr(line.planning_drawdown_reference), "reservation_id": cstr(line.reservation_id),
			"quantity": cstr(line.requested_quantity), "value": cstr(line.requested_value), "unit": cstr(line.unit),
		}
		for line in version.drawdown_lines
	]


def _mapping_gaps(rows: list[dict[str, Any]]) -> list[str]:
	return [r["drawdown_line_id"] for r in rows if not (r["drawdown_reference"] and r["reservation_id"])]


def _planning_sources(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	return [
		{"plan_source_allocation_id": r["allocation_id"], "drawdown_reference": r["drawdown_reference"], "quantity": r["quantity"], "amount": r["value"]}
		for r in rows if r["drawdown_reference"]
	]


def _budget_releases(rows: list[dict[str, Any]], revisions: dict[str, str] | None = None) -> list[dict[str, Any]]:
	return [
		{
			"reservation": r["reservation_id"], "drawdown_line_id": r["drawdown_line_id"], "plan_source_allocation": r["allocation_id"], "amount": r["value"],
			"expected_revision": (revisions or {}).get(r["reservation_id"], ""),
		}
		for r in rows
	]


def _registration_digest(*, tender: str, cancellation: str, cancellation_digest: str, handoff: str, requisition: str, version: str, rows: list[dict[str, Any]]) -> str:
	return digest.sha256_hex(
		{
			"tender": tender, "cancellation": cancellation, "cancellation_digest": cancellation_digest, "handoff": handoff, "requisition": requisition, "version": version,
			"sources": sorted((r["drawdown_line_id"], r["allocation_id"], r["drawdown_reference"], r["reservation_id"], r["quantity"], r["value"]) for r in rows),
		}
	)


# --------------------------------------------------------------------------
# RegisterCancellationResourceRecovery
# --------------------------------------------------------------------------


def register_cancellation_resource_recovery(
	*, tender: str, cancellation: str, cancellation_digest: str, cancelled_at, handoff: str, registered_by: str, origin: str = "Cancellation",
	reconciliation_version: str = "", fixture_namespace: str = "",
) -> dict[str, Any]:
	"""§10.3 row 1 — called by Tenders inside the cancellation transaction (or by the legacy reconciliation, for a cancellation that was
	decided before this existed). One recovery per cancellation: the same lineage reuses it, changed facts conflict. Provisional until
	the caller's transaction commits; a rolled-back cancellation leaves no recovery and no hold."""
	handoff = cstr(handoff).strip()
	requisition = cstr(frappe.db.get_value("Authorised Requisition Handoff", handoff, "requisition")) if handoff else ""
	if not requisition:
		fail("REQ_CANCELLATION_RECOVERY_INVALID", detail={"cause": "The Tender names no authorised handoff."})
	# lock order: Requisition root, then its handoff (the order authorisation, revocation and consumption take)
	root = envelope.locked("Procurement Requisition", requisition)
	hand = envelope.locked("Authorised Requisition Handoff", handoff)
	if not hand.consumed_at or cstr(hand.tender) != cstr(tender):
		fail("REQ_CANCELLATION_RECOVERY_INVALID", detail={"cause": "The handoff was not consumed by this Tender.", "handoff": handoff})
	if root.current_state != "Authorised" or cstr(root.handoff) != hand.name or not root.authorised_version:
		fail("REQ_CANCELLATION_RECOVERY_INVALID", detail={"cause": "The Requisition is not the authorised owner of this handoff.", "requisition": root.name, "state": cstr(root.current_state)})
	# the recovery before the Version, as the recovery run takes them (one lock order)
	existing = frappe.db.get_value(DOCTYPE, {"cancellation": cstr(cancellation)}, "name", for_update=True)
	existing_doc = envelope.locked(DOCTYPE, existing) if existing else None
	version = envelope.locked("Requisition Version", root.authorised_version)
	rows = _source_rows(version)
	if not rows:
		fail("REQ_CANCELLATION_RECOVERY_INVALID", detail={"cause": "The authorised Requisition drew nothing."})
	registration = _registration_digest(
		tender=cstr(tender), cancellation=cstr(cancellation), cancellation_digest=cstr(cancellation_digest), handoff=hand.name, requisition=root.name, version=version.name, rows=rows,
	)

	if existing_doc is not None:
		doc = existing_doc
		if cstr(doc.payload_digest) != registration:
			fail("REQ_IDEMPOTENCY_CONFLICT", detail={"cause": "A recovery for this cancellation was registered with different facts.", "recovery": doc.name})
		return _registered(doc, reused=True)

	gaps = _mapping_gaps(rows)
	decision = frappe.db.get_value("Requisition Decision", {"requisition_version": version.name, "decision": "Authorise requisition"}, "name") or None
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE, "cancellation": cstr(cancellation), "tender": cstr(tender), "cancellation_digest": cstr(cancellation_digest), "cancelled_at": cancelled_at,
			"requisition": root.name, "requisition_version": version.name, "authorisation_decision": decision, "handoff": hand.name, "plan_item_id": cstr(root.plan_item_id),
			"origin": origin, "reconciliation_version": reconciliation_version, "status": NEEDS_ATTENTION if gaps else PENDING, "status_revision": 1,
			"reason_code": MAPPING_MISSING if gaps else "", "reason_detail": ("Planning or Budget evidence is missing for " + ", ".join(gaps) + ".") if gaps else "",
			"attempt_count": 0, "payload_digest": registration, "registered_by": cstr(registered_by), "record_version": 0, "fixture_namespace": fixture_namespace,
			"sources": [{**r, "currency": ""} for r in rows],
		}
	)
	envelope.insert(doc)
	# Planning's hold on every source that has an originating drawdown; a failure here fails the cancellation (nothing commits).
	held = _planning_sources(rows)
	if held:
		try:
			eligibility_gateway.register_cancellation_recovery_hold(
				recovery_id=doc.name, cancellation_id=cstr(cancellation), plan_item_id=cstr(root.plan_item_id), requisition_reference=root.requisition_reference, sources=held,
			)
		except OwnerRefusal as refusal:
			fail("REQ_CANCELLATION_RECOVERY_INVALID", detail={**refusal.detail, "owner": refusal.owner, "code": refusal.code})
		if gaps:
			eligibility_gateway.set_cancellation_recovery_status(recovery_id=doc.name, plan_item_id=cstr(root.plan_item_id), status=NEEDS_ATTENTION, reason=doc.reason_detail)
	_publish(doc, root=root)
	return _registered(doc, reused=False)


def _registered(doc, *, reused: bool) -> dict[str, Any]:
	"""What the cancellation event carries (TPR-CHG-001 v0.21 §4.11): the recovery and the exact consumed Requisition root, Version,
	authorisation event, handoff and drawdown references. A browser never supplies any of it."""
	return {
		"ok": True, "recovery": doc.name, "status": doc.status, "status_revision": int(doc.status_revision or 1), "reused": reused,
		"lineage": {
			"requisition": doc.requisition, "requisition_version": doc.requisition_version, "authorisation_decision": cstr(doc.authorisation_decision), "handoff": doc.handoff,
			"drawdown_references": [cstr(s.drawdown_reference) for s in doc.sources if s.drawdown_reference],
			"drawdown_lines": [cstr(s.drawdown_line_id) for s in doc.sources],
		},
	}


# --------------------------------------------------------------------------
# RecoverCancelledTenderResources
# --------------------------------------------------------------------------


def recover_cancelled_tender_resources(*, recovery: str, executing_service: str = SERVICE) -> dict[str, Any]:
	"""§10.3 row 3 — system-only. A recovery that is Completed returns its recorded outcome unchanged; a Needs attention recovery is not
	retried by itself; a Pending one is attempted once. Never commits: the caller (the sweep, a test, an operator's run) owns the
	transaction, so a crash before its commit leaves both owners' balances unchanged."""
	pre = frappe.db.get_value(DOCTYPE, recovery, ["tender", "cancellation", "requisition", "handoff", "status"], as_dict=True)
	if not pre:
		raise frappe.DoesNotExistError(f"{DOCTYPE} not found")
	if pre.status != PENDING:
		return _outcome(frappe.get_doc(DOCTYPE, recovery), acted=False)

	# Lock order step 1-2 — Tender, then Award case: inside Tenders' own basis read, FOR UPDATE. The answer is taken before any
	# Requisition lock so a cancellation and this recovery can never wait on each other.
	tender_basis = tender_seam.basis(tender=pre.tender, cancellation=pre.cancellation, recovery_id=recovery)

	root = envelope.locked("Procurement Requisition", pre.requisition)
	hand = envelope.locked("Authorised Requisition Handoff", pre.handoff)
	doc = envelope.locked(DOCTYPE, recovery)
	if doc.status != PENDING:
		return _outcome(doc, acted=False)
	version = envelope.locked("Requisition Version", doc.requisition_version)
	rows = _source_rows(version)
	attempts = int(doc.attempt_count or 0) + 1
	attempt = {"attempt_count": attempts, "last_attempt_at": now_datetime(), "executing_service": executing_service}

	state, code, reason = _verdict_before_effects(doc, hand, rows, tender_basis)
	budget_basis: dict[str, Any] = {}
	if state == "ok":
		try:
			budget_basis = funding_gateway.get_cancellation_release_basis(
				cancellation_id=doc.cancellation, requisition_reference=root.requisition_reference, releases=_budget_releases(rows),
			)
		except OwnerRefusal as refusal:
			state, code, reason = "attention", BUDGET_UNSUPPORTED, refusal.reason
		else:
			unsupported = [r for r in budget_basis.get("reservations", []) if r["verdict"] not in ("ok", "reused")]
			if unsupported:
				state, code, reason = "attention", BUDGET_UNSUPPORTED, "Budget — " + cstr((unsupported[0].get("detail") or {}).get("cause") or "the reservation cannot be released")

	if state == "pending":
		_move(doc, root, PENDING, code, reason, extra={**attempt, "next_attempt_at": _later(attempts)})
		return _outcome(doc, acted=True)
	if state == "attention":
		_move(doc, root, NEEDS_ATTENTION, code, reason, extra={**attempt, "next_attempt_at": None})
		return _outcome(doc, acted=True)


	revisions = {r["reservation"]: r["revision"] for r in budget_basis.get("reservations", [])}
	pinned = {"tender": tender_basis.get("revision") or digest.sha256_hex(tender_basis), "budget": revisions, "pinned_at": to_utc_iso(now_datetime())}
	try:
		with envelope.atomic("recover"):
			# Budget first, then Planning — the order authorisation and revocation take.
			released = funding_gateway.release_reservations_for_cancelled_tender(
				recovery_id=doc.name, cancellation_id=doc.cancellation, requisition_reference=root.requisition_reference,
				releases=_budget_releases(rows, revisions), idempotency_key=f"{doc.name}:budget",
			)
			restored = eligibility_gateway.reverse_requisition_drawdowns_for_cancellation(
				recovery_id=doc.name, cancellation_id=doc.cancellation, plan_item_id=cstr(root.plan_item_id), requisition_reference=root.requisition_reference,
				sources=_planning_sources(rows),
			)
			_record_effects(doc, released=released, restored=restored, budget_basis=budget_basis)
			envelope.bump(
				doc, status=COMPLETED, status_revision=int(doc.status_revision or 1) + 1, reason_code="", reason_detail="", completed_at=now_datetime(),
				pinned_basis_json=json.dumps(pinned, sort_keys=True), pinned_basis_digest=digest.sha256_hex(pinned), next_attempt_at=None, **attempt,
			)
			_publish(doc, root=root)
	except OwnerRefusal as refusal:
		# Both owners' effects rolled back together with the savepoint; the recovery needs attention with the owner's own reason.
		doc = envelope.locked(DOCTYPE, recovery)  # the in-memory copy carries effects that were rolled back
		_move(doc, root, NEEDS_ATTENTION, OWNER_REFUSED, refusal.reason, extra={**attempt, "next_attempt_at": None})
		return _outcome(doc, acted=True)
	except Exception:  # noqa: BLE001 — a lock wait, a database or service failure: not proof of anything, so retry the same intent
		frappe.log_error(title=f"Cancellation recovery {recovery} attempt {attempts} failed")
		doc = envelope.locked(DOCTYPE, recovery)
		_move(doc, root, PENDING, OWNER_UNAVAILABLE, "An owner could not complete the recovery this time. It will be tried again.", extra={**attempt, "next_attempt_at": _later(attempts)})
		return _outcome(doc, acted=True)
	return _outcome(doc, acted=True)


def _later(attempts: int):
	"""The next attempt: a minute after the first, doubling to an hour."""
	return add_to_date(now_datetime(), seconds=min(60 * (2 ** max(attempts - 1, 0)), MAX_BACKOFF_SECONDS))


def _verdict_before_effects(doc, hand, rows: list[dict[str, Any]], basis: dict[str, Any]) -> tuple[str, str, str]:
	"""`ok`, `pending` (evidence is unavailable, retry) or `attention` (an owner proves the allowance may not be restored)."""
	verdict = cstr(basis.get("verdict"))
	if verdict == tender_seam.UNAVAILABLE:
		return "pending", TENDER_UNAVAILABLE, cstr(basis.get("reason")) or "Tenders could not confirm the cancellation yet."
	if verdict != tender_seam.POSITIVE:
		return "attention", TENDER_NEGATIVE, cstr(basis.get("reason")) or "Tenders does not support restoring this allowance."
	lineage = basis.get("lineage") or {}
	theirs = sorted((cstr(s.get("drawdown_line_id")), cstr(s.get("reservation_id"))) for s in lineage.get("sources", []))
	ours = sorted((r["drawdown_line_id"], r["reservation_id"]) for r in rows)
	if cstr(lineage.get("handoff")) != hand.name or cstr(lineage.get("requisition")) != cstr(doc.requisition) or theirs != ours:
		return "attention", LINEAGE_MISMATCH, "The Tender's consumed lineage is not the lineage registered for this recovery."
	gaps = _mapping_gaps(rows)
	if gaps:
		return "attention", MAPPING_MISSING, "Planning or Budget evidence is missing for " + ", ".join(gaps) + "."
	return "ok", "", ""


def _record_effects(doc, *, released: dict[str, Any], restored: dict[str, Any], budget_basis: dict[str, Any]) -> None:
	by_line = {r["drawdown_line_id"]: r for r in released.get("released", [])}
	by_allocation = {r["plan_source_allocation_id"]: r for r in restored.get("reversals", [])}
	budget_facts = {r["drawdown_line_id"]: r for r in budget_basis.get("reservations", [])}
	for source in doc.sources:
		release = by_line.get(source.drawdown_line_id) or {}
		reversal = by_allocation.get(source.allocation_id) or {}
		facts = budget_facts.get(source.drawdown_line_id) or {}
		source.budget = cstr(release.get("budget") or facts.get("budget"))
		source.budget_line = cstr(release.get("budget_line") or facts.get("budget_line"))
		source.currency = cstr(release.get("currency") or facts.get("currency"))
		source.restored_quantity, source.restored_value = cstr(reversal.get("quantity")), cstr(reversal.get("amount"))
		source.released_value = cstr(release.get("amount"))
		source.reversal_reference, source.release_reference, source.ledger_event = cstr(reversal.get("reversal_reference")), cstr(release.get("release")), cstr(release.get("ledger_event"))


# --------------------------------------------------------------------------
# Status, outcome and read
# --------------------------------------------------------------------------


def _move(doc, root, status: str, code: str, reason: str, *, extra: dict[str, Any]) -> None:
	"""Record a new status of the recovery (a new status revision, and an outcome event, only when the status or its reason changed) and tell
	Planning, so a refused authorisation names the right state."""
	changed = doc.status != status or cstr(doc.reason_code) != code or cstr(doc.reason_detail) != reason
	revision = int(doc.status_revision or 1) + (1 if changed else 0)
	envelope.bump(doc, status=status, status_revision=revision, reason_code=code, reason_detail=reason, **extra)
	if changed and status != COMPLETED:
		if _planning_sources(_source_rows(frappe.get_doc("Requisition Version", doc.requisition_version))):
			eligibility_gateway.set_cancellation_recovery_status(recovery_id=doc.name, plan_item_id=cstr(root.plan_item_id), status=status, reason=reason)
		_publish(doc, root=root)


def _publish(doc, *, root) -> None:
	events.publish_recovery_outcome(
		requisition=doc.requisition, requisition_version=doc.requisition_version, recovery=doc.name, status_revision=int(doc.status_revision or 1),
		payload={
			"schema_version": 1, "recovery_id": doc.name, "cancellation_id": doc.cancellation, "cancellation_digest": cstr(doc.cancellation_digest), "tender": doc.tender,
			"requisition_id": doc.requisition, "requisition_reference": cstr(root.requisition_reference), "requisition_version_id": doc.requisition_version,
			"status": doc.status, "status_revision": int(doc.status_revision or 1), "reason_code": cstr(doc.reason_code), "reason": cstr(doc.reason_detail),
			"occurred_at_utc": to_utc_iso(now_datetime()),
			"sources": [
				{
					"drawdown_line_id": s.drawdown_line_id, "allocation_id": s.allocation_id, "reservation_id": cstr(s.reservation_id), "quantity": cstr(s.quantity), "value": cstr(s.value),
					"restored_quantity": cstr(s.restored_quantity), "restored_value": cstr(s.restored_value), "released_value": cstr(s.released_value),
					"reversal_reference": cstr(s.reversal_reference), "release_reference": cstr(s.release_reference),
				}
				for s in doc.sources
			],
		},
	)


def _outcome(doc, *, acted: bool) -> dict[str, Any]:
	return {
		"ok": True, "recovery": doc.name, "status": doc.status, "status_revision": int(doc.status_revision or 1), "reason_code": cstr(doc.reason_code),
		"reason": cstr(doc.reason_detail), "acted": acted, "idempotent": not acted,
	}


def retry_cancellation_recovery(*, recovery: str, user: str | None = None) -> dict[str, Any]:
	"""§9.1D — an authorised technical operator may retry the same intent after the owner corrected the cause through its governed route.
	The retry resets a Needs attention recovery to Pending (a new status revision); it changes no evidence and no amount, and the
	recovery still has to verify everything again before it restores anything."""
	actor = authz.actor(user)
	if not authz.is_technical(actor):
		authz.not_found()
	requisition = cstr(frappe.db.get_value(DOCTYPE, recovery, "requisition"))
	if not requisition:
		authz.not_found()
	root = records.require_root(requisition)  # the Requisition root before the recovery, as everywhere else
	doc = envelope.locked(DOCTYPE, recovery)
	if doc.status != NEEDS_ATTENTION:
		return _outcome(doc, acted=False)
	_move(doc, root, PENDING, "RETRY_REQUESTED", "A retry was requested after the cause was corrected.", extra={"next_attempt_at": now_datetime()})
	return _outcome(doc, acted=True)


def for_requisition(requisition: str) -> list[str]:
	return frappe.get_all(DOCTYPE, filters={"requisition": requisition}, pluck="name", order_by="creation asc")


def _reader_scope(actor: str) -> set[str] | None:
	"""None when the reader sees every source (technical, site-wide, oversight); otherwise the departments the reader holds."""
	if authz.is_technical(actor) or authz._holds_site_wide_reader_role(actor) or authz.is_oversight_reader(actor):
		return None
	scope: set[str] = set()
	for role in DEPARTMENTAL_ROLES:
		scope |= set(authz.permitted_ou_scopes(actor, role))
	return scope


def get_cancellation_resource_recovery(*, recovery: str = "", requisition: str = "", tender: str = "", user: str | None = None) -> dict[str, Any]:
	"""§10.3 row 4 — read-only, never an authority-free lookup: the caller must be allowed to read the Requisition the recovery belongs to
	(contributing-department scope, the site-wide roles, an Auditor, an Accounting Officer's oversight read once it is authorised, the
	technical operator). A departmental reader sees only the source rows of its own department and no aggregate that would reveal the
	others."""
	actor = authz.actor(user)
	filters = {"name": recovery} if recovery else ({"requisition": requisition} if requisition else {"tender": tender})
	name = frappe.db.get_value(DOCTYPE, filters, "name", order_by="creation desc")
	if not name:
		authz.not_found()
	doc = frappe.get_doc(DOCTYPE, name)
	root = frappe.get_doc("Procurement Requisition", doc.requisition)
	units = records.contributing_units(root)
	authz.require_requisition_reader(actor, contributing_org_units=units, state="Authorised")
	readable = _reader_scope(actor)
	shown = [s for s in doc.sources if readable is None or cstr(s.contributing_org_unit) in readable]
	return {
		"recovery": doc.name, "status": doc.status, "status_revision": int(doc.status_revision or 1), "reason_code": cstr(doc.reason_code), "reason": cstr(doc.reason_detail),
		"tender": doc.tender, "cancellation": doc.cancellation, "requisition": doc.requisition, "requisition_reference": cstr(root.requisition_reference),
		"plan_item_id": cstr(doc.plan_item_id), "origin": doc.origin, "attempt_count": int(doc.attempt_count or 0), "cancelled_at": cstr(doc.cancelled_at),
		"completed_at": cstr(doc.completed_at),
		"sources": [
			{
				"drawdown_line_id": s.drawdown_line_id, "allocation_id": s.allocation_id, "contributing_org_unit": cstr(s.contributing_org_unit), "quantity": cstr(s.quantity), "unit": cstr(s.unit),
				"value": cstr(s.value), "currency": cstr(s.currency), "restored_quantity": cstr(s.restored_quantity), "restored_value": cstr(s.restored_value), "released_value": cstr(s.released_value),
				"reservation_id": cstr(s.reservation_id), "drawdown_reference": cstr(s.drawdown_reference), "reversal_reference": cstr(s.reversal_reference), "release_reference": cstr(s.release_reference),
			}
			for s in shown
		],
		"all_sources_shown": len(shown) == len(doc.sources),
		"record_version": int(doc.record_version or 0),
	}
