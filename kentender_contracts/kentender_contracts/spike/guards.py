"""Phase 2 spike S5 (tracker CM8-206): native hook points on every payment-capable path, and the guard CM needs on them.

Inert unless the process sets `frappe.flags.cm_spike_mode` ("probe" records the events that fire; "enforce" also refuses).
Not product code: it is promoted to `services/` in Phase 3 once the spike shows which events carry each route.
"""

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe.utils import flt

FLAG = "cm_native_operation"  # opened in-process by the controlled KenTender operation, never read from a request
PAYMENT_METHODS = ("before_submit", "before_update_after_submit")


@contextmanager
def native_operation(identity: str):
	"""The controlled KenTender operation (`ApproveNativeFinanceRecord` and friends) opens this around the native call."""
	frappe.flags[FLAG] = identity
	try:
		yield
	finally:
		frappe.flags.pop(FLAG, None)


def _mode() -> str:
	return frappe.flags.get("cm_spike_mode") or ""


def _events() -> list:
	if "cm_probe_events" not in frappe.flags:
		frappe.flags.cm_probe_events = []
	return frappe.flags.cm_probe_events


def _allocations(doc) -> dict[str, float]:
	"""Amount this document allocates to each Purchase Invoice."""
	out: dict[str, float] = {}
	if doc.doctype == "Payment Entry":
		for r in doc.get("references") or []:
			if r.reference_doctype == "Purchase Invoice":
				out[r.reference_name] = out.get(r.reference_name, 0.0) + flt(r.allocated_amount)
	elif doc.doctype == "Journal Entry":
		for a in doc.get("accounts") or []:
			if a.reference_type == "Purchase Invoice" and a.reference_name:
				out[a.reference_name] = out.get(a.reference_name, 0.0) + flt(a.debit_in_account_currency)
	return out


def _new_allocations(doc, method: str) -> dict[str, float]:
	"""Allocations this posting adds. At first submission the whole entry is new (the stored draft already holds the same rows);
	on an update after submit (reconciliation) only the rows added by this change are."""
	now = _allocations(doc)
	if method == "before_submit":
		return now
	before = doc.get_doc_before_save() if not doc.is_new() else None
	if before is None:
		return now
	old = _allocations(before)
	return {k: v - old.get(k, 0.0) for k, v in now.items() if v - old.get(k, 0.0) > 0.005}


def entitlement(invoice: str, *, lock: bool = False) -> dict:
	row = frappe.db.get_value("Purchase Invoice", invoice, ["name", "cm_operation_identity", "cm_certified_amount", "grand_total", "outstanding_amount"], as_dict=True, for_update=lock)
	paid = flt(row.grand_total) - flt(row.outstanding_amount)
	return {"invoice": invoice, "cm_linked": bool(row.cm_operation_identity), "certified": flt(row.cm_certified_amount), "paid": paid, "available": flt(row.cm_certified_amount) - paid}


def _supplier_is_contract_linked(supplier: str | None) -> bool:
	return bool(supplier) and bool(frappe.db.exists("Purchase Invoice", {"supplier": supplier, "cm_operation_identity": ["!=", ""], "docstatus": 1}))


def _pays_a_contract_supplier(doc) -> bool:
	if doc.doctype == "Payment Entry":
		return doc.get("party_type") == "Supplier" and _supplier_is_contract_linked(doc.get("party"))
	if doc.doctype == "Journal Entry":
		return any(a.get("party_type") == "Supplier" and _supplier_is_contract_linked(a.get("party")) for a in doc.get("accounts") or [])
	return False


def _invalidate_pending_approval(doc) -> None:
	"""A changed amount, allocation or beneficiary on an entry awaiting approval sends it back to Draft (CM §5.12)."""
	before = doc.get_doc_before_save()
	if before is None or before.get("workflow_state") != "Pending Approval":
		return
	watched = ("paid_amount", "received_amount", "party", "party_bank_account", "paid_from", "paid_to", "reference_no")
	changed = [f for f in watched if str(before.get(f)) != str(doc.get(f))] + (["references"] if _allocations(before) != _allocations(doc) else [])
	if changed:
		doc.workflow_state = "Draft"
		frappe.flags.cm_approval_invalidated = changed


def on_event(doc, method=None) -> None:
	mode = _mode()
	if not mode:
		return
	_events().append(f"{doc.doctype}:{method}")
	if mode != "enforce":
		return
	if doc.doctype == "Payment Entry" and method == "validate" and not doc.is_new():
		_invalidate_pending_approval(doc)
		return
	if doc.doctype not in ("Payment Entry", "Journal Entry") or method not in PAYMENT_METHODS:
		return
	if not _pays_a_contract_supplier(doc):
		return  # an ordinary supplier outside any contract is untouched: ERPNext Accounts stays usable on its own
	if not frappe.flags.get(FLAG):
		frappe.throw("CM_HOLD: this payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation.", frappe.PermissionError)
	for invoice, amount in _new_allocations(doc, method).items():
		ent = entitlement(invoice, lock=not frappe.flags.get("cm_spike_no_lock"))  # row lock: a concurrent payment waits, then sees this one
		if not ent["cm_linked"]:
			continue
		if amount > ent["available"] + 0.005:
			frappe.throw(f"CM_HOLD: {invoice} is certified for {ent['certified']:,.2f}, already settled {ent['paid']:,.2f}; {amount:,.2f} exceeds the supported amount.", frappe.ValidationError)
