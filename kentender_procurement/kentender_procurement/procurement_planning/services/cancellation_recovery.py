# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.32 §5.4.7 / §7.8 — Planning's two halves of a whole-Tender
cancellation recovery.

Requisitions coordinates the recovery; Planning owns the allowance and so owns
both of these effects:

- `register_cancellation_recovery_hold` — inside the Accounting Officer's
  `CancelTender` transaction, one durable hold per affected source allocation,
  keyed by recovery and allocation. While a hold is Active that source cannot
  authorise a new draw; every other source and item is untouched. It is not a
  Plan Item correction hold (`scope_lock.recompute_hold` rewrites that one from
  correction requests alone) and no public command removes it.
- `reverse_requisition_drawdowns_for_cancellation` — inside the one recovery
  transaction, the cancellation mode of `ReverseRequisitionDrawdown`: flips the
  exact originating drawdowns to Reversed (restoring the exact quantity and
  value to the source's remaining allowance, counted by the stable allocation
  identity) and removes this recovery's holds in the same step. It never touches
  the permanent first-authorisation scope lock, and it validates against the
  facts pinned when the hold was registered, never against a caller's assertion.

Both are in-process calls authenticated by a minted `RecoveryCaller`
(`recovery_principal`). Neither commits, and neither claims a command-journal
key: idempotency is the immutable business key (recovery + source) plus a digest
of the pinned facts, so a retry with a new key reuses the effect and a changed
payload is a conflict.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, scope_lock
from kentender_procurement.procurement_planning.services import money as money_boundary
from kentender_procurement.procurement_planning.services.recovery_principal import require_recovery_caller
from kentender_procurement.procurement_planning.write_family import planning_command

HOLD = "Plan Cancellation Recovery Hold"
DRAWDOWN = "Plan Drawdown Reference"
REASON_CANCELLED = "TenderCancelled"
STATUS_PENDING = "Pending"
STATUS_NEEDS_ATTENTION = "Needs attention"


def hold_key(recovery_id: str, allocation_id: str) -> str:
	return f"{cstr(recovery_id).strip()}:{cstr(allocation_id).strip()}"


def _dec(value) -> Decimal:
	converted = money_boundary._to_decimal(value)
	return converted if converted is not None else Decimal(0)


def _parse_sources(sources) -> list[dict[str, Any]]:
	"""The pinned facts of each source, exact decimals; a binary float or a
	repeated allocation is refused (§4.11: no contributing source is omitted or
	counted twice)."""
	if not sources:
		fail("PLN_CANCELLATION_RECOVERY_CONFLICT", detail={"cause": "No source was named."})
	out, seen = [], set()
	for spec in sources:
		allocation_id = cstr(spec.get("plan_source_allocation_id")).strip()
		reference = cstr(spec.get("drawdown_reference")).strip()
		if not allocation_id or not reference:
			fail("PLN_CANCELLATION_RECOVERY_CONFLICT", detail={"cause": "A source must name its allocation and its originating drawdown."})
		if allocation_id in seen:
			fail("PLN_CANCELLATION_RECOVERY_CONFLICT", detail={"cause": "A source allocation appears more than once.", "allocation_id": allocation_id})
		seen.add(allocation_id)
		for field in ("quantity", "amount"):
			if isinstance(spec.get(field), float):
				fail("PLN_MONEY_PRECISION_INVALID", detail={"field": field, "offered": repr(spec.get(field))})
		quantity = money_boundary.parse_quantity(spec.get("quantity"), field="quantity")
		amount = money_boundary.parse_money(spec.get("amount"), field="amount")
		out.append({"allocation_id": allocation_id, "drawdown_reference": reference, "quantity": quantity, "amount": amount})
	return sorted(out, key=lambda s: s["allocation_id"])


def _digest(recovery_id: str, plan_item_id: str, source: dict[str, Any]) -> str:
	body = {
		"recovery_id": recovery_id, "plan_item_id": plan_item_id, "allocation_id": source["allocation_id"],
		"drawdown_reference": source["drawdown_reference"],
		"quantity": money_boundary.quantity_text(source["quantity"]), "amount": money_boundary.money_text(source["amount"]),
	}
	return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _conflict(cause: str, **detail) -> None:
	fail("PLN_CANCELLATION_RECOVERY_CONFLICT", detail={"cause": cause, **detail})


def _lock_item_and_root(plan_item_id: str):
	"""The same first two locks `AuthoriseRequisitionDrawdown` takes, in the same
	order (Annual Plan Item, then the stable Plan Item root), so a registration or
	a reversal and a racing authorisation serialise instead of interleaving."""
	from kentender_procurement.procurement_planning.services import plan_requisition

	item_name = plan_requisition._requisition_item_name(plan_item_id)
	item = envelope.locked("Annual Plan Item", item_name)
	root = scope_lock.guard(item.plan_item_id)
	return item, root


def _allocation_id_of(drawdown) -> str:
	if cstr(drawdown.get("allocation_id")):
		return cstr(drawdown.allocation_id)
	return cstr(frappe.db.get_value("Plan Source Allocation", drawdown.allocation, "allocation_id"))


def _check_drawdown(drawdown, source: dict[str, Any], plan_item_id: str, requisition_reference: str) -> None:
	if cstr(drawdown.plan_item_id) != plan_item_id:
		_conflict("The drawdown belongs to a different Plan Item.", drawdown=drawdown.name)
	if _allocation_id_of(drawdown) != source["allocation_id"]:
		_conflict("The drawdown belongs to a different source allocation.", drawdown=drawdown.name, allocation_id=source["allocation_id"])
	if requisition_reference and cstr(drawdown.requisition_reference) != requisition_reference:
		_conflict("The drawdown was made for a different Requisition.", drawdown=drawdown.name)
	if _dec(drawdown.quantity) != source["quantity"] or _dec(drawdown.amount) != source["amount"]:
		_conflict(
			"The drawdown quantity or value differs from the original authorisation.",
			drawdown=drawdown.name, allocation_id=source["allocation_id"],
			expected_quantity=money_boundary.quantity_text(source["quantity"]), actual_quantity=money_boundary.quantity_text(_dec(drawdown.quantity)),
			expected_amount=money_boundary.money_text(source["amount"]), actual_amount=money_boundary.money_text(_dec(drawdown.amount)),
		)


def _find_drawdown(reference: str):
	if not reference or not frappe.db.exists(DRAWDOWN, reference):
		_conflict("The originating drawdown is not recorded.", drawdown=reference)
	return envelope.locked(DRAWDOWN, reference)


# --------------------------------------------------------------------------
# RegisterCancellationRecoveryHold
# --------------------------------------------------------------------------


@planning_command
def register_cancellation_recovery_hold(
	*, caller, recovery_id: str, cancellation_id: str, plan_item_id: str, requisition_reference: str, sources: list[dict[str, Any]], user: str | None = None,
) -> dict[str, Any]:
	"""§7.8 row 5 — one idempotent source hold per affected allocation, inside the
	`CancelTender` transaction. An identical replay reuses the hold; a conflicting
	lineage fails and the cancellation does not commit."""
	recovery_id = cstr(recovery_id).strip()
	require_recovery_caller(caller, recovery_id)
	cancellation_id, plan_item_id, requisition_reference = cstr(cancellation_id).strip(), cstr(plan_item_id).strip(), cstr(requisition_reference).strip()
	if not (recovery_id and cancellation_id and plan_item_id):
		_conflict("The recovery, cancellation and Plan Item must all be named.")
	parsed = _parse_sources(sources)

	item, _root = _lock_item_and_root(plan_item_id)
	plan_item_id = cstr(item.plan_item_id)
	holds: list[dict[str, Any]] = []
	for source in parsed:
		key = hold_key(recovery_id, source["allocation_id"])
		digest = _digest(recovery_id, plan_item_id, source)
		existing = frappe.db.get_value(HOLD, {"hold_key": key}, "name", for_update=True)
		if existing:
			hold = envelope.locked(HOLD, existing)
			if cstr(hold.facts_digest) != digest or cstr(hold.cancellation_id) != cancellation_id:
				_conflict("A hold for this recovery and source already exists with different facts.", allocation_id=source["allocation_id"], hold=hold.name)
			holds.append({"allocation_id": source["allocation_id"], "hold": hold.name, "reused": True, "state": hold.state})
			continue
		drawdown = _find_drawdown(source["drawdown_reference"])
		if drawdown.drawdown_state != "Active":
			_conflict("The originating drawdown is no longer in force.", drawdown=drawdown.name, allocation_id=source["allocation_id"], state=cstr(drawdown.drawdown_state))
		_check_drawdown(drawdown, source, plan_item_id, requisition_reference)
		# A drawdown can be under at most one Active hold: a second recovery for the same draw is a conflict.
		if frappe.db.get_value(HOLD, {"drawdown_reference": drawdown.name, "state": "Active"}, "name", for_update=True):
			_conflict("The drawdown is already held by another recovery.", drawdown=drawdown.name)
		doc = frappe.get_doc(
			{
				"doctype": HOLD, "hold_key": key, "recovery_id": recovery_id, "cancellation_id": cancellation_id,
				"plan_item": item.name, "plan_item_id": plan_item_id, "allocation_id": source["allocation_id"],
				"drawdown_reference": drawdown.name, "requisition_reference": requisition_reference or cstr(drawdown.requisition_reference),
				"quantity": money_boundary.quantity_text(source["quantity"]), "amount": money_boundary.money_text(source["amount"]),
				"facts_digest": digest, "state": "Active", "display_status": STATUS_PENDING, "registered_at": now_datetime(),
				"record_version": 0, "fixture_namespace": cstr(item.fixture_namespace),
			}
		).insert(ignore_permissions=True)
		holds.append({"allocation_id": source["allocation_id"], "hold": doc.name, "reused": False, "state": "Active"})
	return {"ok": True, "idempotent": all(h["reused"] for h in holds), "action": "held", "holds": holds}


# --------------------------------------------------------------------------
# ReverseRequisitionDrawdown — cancellation mode
# --------------------------------------------------------------------------


@planning_command
def reverse_requisition_drawdowns_for_cancellation(
	*, caller, recovery_id: str, cancellation_id: str, plan_item_id: str, requisition_reference: str, sources: list[dict[str, Any]], user: str | None = None,
) -> dict[str, Any]:
	"""§7.8 row 6a — restore the exact originating draws of a verified recovery.
	Validates the whole set against the pinned holds before writing any of it; a
	reversal made for any other reason, or by another recovery, is a conflict."""
	recovery_id = cstr(recovery_id).strip()
	require_recovery_caller(caller, recovery_id)
	cancellation_id, plan_item_id, requisition_reference = cstr(cancellation_id).strip(), cstr(plan_item_id).strip(), cstr(requisition_reference).strip()
	parsed = _parse_sources(sources)

	item, _root = _lock_item_and_root(plan_item_id)
	plan_item_id = cstr(item.plan_item_id)
	plan: list[tuple[dict[str, Any], Any, Any, bool]] = []
	for source in parsed:
		digest = _digest(recovery_id, plan_item_id, source)
		drawdown = _find_drawdown(source["drawdown_reference"])
		_check_drawdown(drawdown, source, plan_item_id, requisition_reference)
		hold_name = frappe.db.get_value(HOLD, {"hold_key": hold_key(recovery_id, source["allocation_id"])}, "name", for_update=True)
		hold = envelope.locked(HOLD, hold_name) if hold_name else None
		if hold is not None and (cstr(hold.facts_digest) != digest or cstr(hold.cancellation_id) != cancellation_id):
			_conflict("The registered hold differs from the facts presented.", allocation_id=source["allocation_id"], hold=hold.name)
		if drawdown.drawdown_state == "Reversed":
			if cstr(drawdown.reversal_reason) == REASON_CANCELLED and cstr(drawdown.recovery_id) == recovery_id:
				plan.append((source, drawdown, hold, True))
				continue
			_conflict(
				"The originating drawdown was already reversed for another reason.", drawdown=drawdown.name, allocation_id=source["allocation_id"],
				reversal_reason=cstr(drawdown.reversal_reason) or "unrecorded",
			)
		if hold is None or hold.state != "Active":
			_conflict("No active hold was registered for this source.", allocation_id=source["allocation_id"], drawdown=drawdown.name)
		plan.append((source, drawdown, hold, False))

	reversals: list[dict[str, Any]] = []
	now = now_datetime()
	for source, drawdown, hold, reused in plan:
		if not reused:
			envelope.bump(
				drawdown, drawdown_state="Reversed", reversal_reference=f"REV-{drawdown.name}", reversal_reason=REASON_CANCELLED,
				recovery_id=recovery_id, cancellation_id=cancellation_id, reversed_at=now,
			)
		if hold is not None and hold.state == "Active":
			envelope.bump(hold, state="Removed", removed_at=now)
		reversals.append(
			{
				"plan_source_allocation_id": source["allocation_id"], "drawdown_reference": drawdown.name, "reversal_reference": f"REV-{drawdown.name}",
				"quantity": money_boundary.quantity_text(source["quantity"]), "amount": money_boundary.money_text(source["amount"]), "reused": reused,
			}
		)
	return {"ok": True, "idempotent": all(r["reused"] for r in reversals), "action": "restored", "reversals": reversals}


# --------------------------------------------------------------------------
# Status mirror and reads
# --------------------------------------------------------------------------


@planning_command
def set_cancellation_recovery_status(
	*, caller, recovery_id: str, plan_item_id: str, status: str, reason: str = "", user: str | None = None,
) -> dict[str, Any]:
	"""Requisitions tells Planning which of the two unresolved states the recovery
	is in, so the authorisation refusal can say Pending or Needs attention. Only
	the status and the owner's reason are written; nothing here releases a hold."""
	recovery_id = cstr(recovery_id).strip()
	require_recovery_caller(caller, recovery_id)
	if status not in (STATUS_PENDING, STATUS_NEEDS_ATTENTION):
		_conflict("Only Pending or Needs attention can be shown on a hold.", status=cstr(status))
	_lock_item_and_root(cstr(plan_item_id).strip())
	changed = 0
	for name in frappe.get_all(HOLD, filters={"recovery_id": recovery_id, "state": "Active"}, pluck="name", order_by="name asc"):
		hold = envelope.locked(HOLD, name)
		if hold.display_status != status or cstr(hold.reason) != cstr(reason):
			envelope.bump(hold, display_status=status, reason=cstr(reason))
			changed += 1
	return {"ok": True, "action": "status_set", "changed": changed}


def active_holds(plan_item_id: str, *, for_update: bool = False) -> list[dict[str, Any]]:
	"""The Active recovery holds on this stable Plan Item, one row per held source.
	A decision made under the stable-item guard reads with `for_update`: MariaDB
	runs at REPEATABLE READ, so a plain read could miss a hold another command
	committed while this one waited for the guard."""
	if for_update:
		rows = frappe.db.sql(
			f"select name, recovery_id, cancellation_id, allocation_id, drawdown_reference, quantity, amount, display_status, reason from `tab{HOLD}` "
			"where plan_item_id=%s and state='Active' for update",
			cstr(plan_item_id), as_dict=True,
		)
	else:
		rows = frappe.get_all(
			HOLD, filters={"plan_item_id": cstr(plan_item_id), "state": "Active"},
			fields=["name", "recovery_id", "cancellation_id", "allocation_id", "drawdown_reference", "quantity", "amount", "display_status", "reason"],
		)
	return [dict(r) for r in rows]


def refuse_if_held(plan_item_id: str, allocation_ids) -> None:
	"""`AuthoriseRequisitionDrawdown`: a held source draws nothing. Call under the
	stable-item guard. Needs attention names the conflict code; a Pending
	restoration names the pending code. Other sources are not affected."""
	wanted = {cstr(a) for a in allocation_ids}
	held = [h for h in active_holds(plan_item_id, for_update=True) if h["allocation_id"] in wanted]
	if not held:
		return
	needs_attention = any(h["display_status"] == STATUS_NEEDS_ATTENTION for h in held)
	fail(
		"PLN_CANCELLATION_RECOVERY_CONFLICT" if needs_attention else "PLN_CANCELLATION_RECOVERY_PENDING",
		detail={"plan_item_id": cstr(plan_item_id), "allocation_ids": sorted(h["allocation_id"] for h in held)},
	)


def drawdown_is_held(drawdown_reference: str) -> bool:
	return bool(frappe.db.exists(HOLD, {"drawdown_reference": cstr(drawdown_reference), "state": "Active"}))
