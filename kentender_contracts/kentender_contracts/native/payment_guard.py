# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bypass guards on every native payment-capable path (CM-CHG-001 v0.8 §5.12, §9.1; plan D7; CM-AC-17, CM-AC-31).

A payment to a supplier who has contract invoices may be posted only inside a controlled KenTender operation, and only up to
what procurement certified minus what is already settled. The spike (S5) found that native submit rights and workflow do not stop
a Draft payment submitted directly, through the API, as a Journal Entry or by Payment Reconciliation, so the guard sits on the
documents' own events (`hooks.py` `doc_events`), which every route reaches: `before_submit`, and `before_update_after_submit`
for reconciliation. Maker/approver separation stays the native workflow with `allow_self_approval = 0`.

The rule is by **supplier**: an entry to a supplier with a contract invoice is guarded wherever its allocation points, because an
unreferenced advance reconciled later would otherwise slip past an invoice-level rule. A supplier with no contract invoice is
untouched, so ERPNext Accounts stays usable on its own. A refund received from a supplier is not a payment and is not held.
The entitlement is read under a row lock so two concurrent approvals cannot both pass (spike S5e). A changed amount, allocation or
beneficiary on an entry awaiting approval returns it to Draft (§5.12)."""

from __future__ import annotations

from contextlib import contextmanager

import frappe
from frappe.utils import flt

from kentender_contracts.services.errors import fail

FLAG = "cm_native_operation"  # opened in-process by the controlled KenTender operation; never read from a request
PAYMENT_METHODS = ("before_submit", "before_update_after_submit")
WATCHED_ON_PENDING = ("paid_amount", "received_amount", "party", "party_bank_account", "paid_from", "paid_to", "reference_no")
PENDING_STATE = "Pending Approval"
DRAFT_STATE = "Draft"
TOLERANCE = 0.005


@contextmanager
def native_operation(identity: str):
	"""The controlled operation (`ApproveNativeFinanceRecord` and its kin) opens this around the native call."""
	previous = frappe.flags.get(FLAG)
	frappe.flags[FLAG] = identity
	try:
		yield
	finally:
		if previous is None:
			frappe.flags.pop(FLAG, None)
		else:
			frappe.flags[FLAG] = previous


def in_operation() -> bool:
	return bool(frappe.flags.get(FLAG))


def allocations(doc) -> dict[str, float]:
	"""Amount this document allocates to each Purchase Invoice."""
	out: dict[str, float] = {}
	if doc.doctype == "Payment Entry":
		for row in doc.get("references") or []:
			if row.reference_doctype == "Purchase Invoice":
				out[row.reference_name] = out.get(row.reference_name, 0.0) + flt(row.allocated_amount)
	elif doc.doctype == "Journal Entry":
		for row in doc.get("accounts") or []:
			if row.reference_type == "Purchase Invoice" and row.reference_name:
				out[row.reference_name] = out.get(row.reference_name, 0.0) + flt(row.debit_in_account_currency)
	return out


def order_allocations(doc) -> dict[str, float]:
	"""Amount a payment entry allocates to each Purchase Order: an advance against the order."""
	out: dict[str, float] = {}
	if doc.doctype == "Payment Entry":
		for row in doc.get("references") or []:
			if row.reference_doctype == "Purchase Order":
				out[row.reference_name] = out.get(row.reference_name, 0.0) + flt(row.allocated_amount)
	return out


def advance_entitlement(order: str, *, lock: bool = False) -> dict:
	"""What the contract supports advancing on one order: the advance procurement certified minus what has already been paid against it."""
	row = frappe.db.get_value("Purchase Order", order, ["name", "cm_operation_identity", "cm_advance_certified", "advance_paid"], as_dict=True, for_update=lock)
	return {"order": order, "cm_linked": bool(row.cm_operation_identity), "certified": flt(row.cm_advance_certified), "paid": flt(row.advance_paid), "available": flt(row.cm_advance_certified) - flt(row.advance_paid)}


def new_allocations(doc, method: str) -> dict[str, float]:
	"""Allocations this posting adds. At first submission the whole entry is new (the stored draft already holds the same rows); on an
	update after submit (reconciliation) only the rows added by this change are."""
	now = allocations(doc)
	if method == "before_submit":
		return now
	before = doc.get_doc_before_save() if not doc.is_new() else None
	if before is None:
		return now
	old = allocations(before)
	return {key: value - old.get(key, 0.0) for key, value in now.items() if value - old.get(key, 0.0) > TOLERANCE}


def entitlement(invoice: str, *, lock: bool = False) -> dict:
	"""What the contract supports paying on one invoice: certified minus settled. Settled is read from the invoice itself."""
	row = frappe.db.get_value("Purchase Invoice", invoice, ["name", "cm_operation_identity", "cm_certified_amount", "grand_total", "outstanding_amount"], as_dict=True, for_update=lock)
	paid = flt(row.grand_total) - flt(row.outstanding_amount)
	return {"invoice": invoice, "cm_linked": bool(row.cm_operation_identity), "certified": flt(row.cm_certified_amount), "paid": paid, "available": flt(row.cm_certified_amount) - paid}


def supplier_has_contract_invoices(supplier: str | None) -> bool:
	return bool(supplier) and bool(frappe.db.exists("Purchase Invoice", {"supplier": supplier, "cm_operation_identity": ["!=", ""], "docstatus": 1}))


def advances_a_contract_order(doc) -> bool:
	"""A payment entry that advances money against an order Contract Management made."""
	return any(row.reference_doctype == "Purchase Order" and frappe.db.get_value("Purchase Order", row.reference_name, "cm_operation_identity") for row in doc.get("references") or [])


def pays_a_contract_supplier(doc) -> bool:
	if doc.doctype == "Payment Entry":
		return doc.get("payment_type") == "Pay" and doc.get("party_type") == "Supplier" and (supplier_has_contract_invoices(doc.get("party")) or advances_a_contract_order(doc))
	if doc.doctype == "Journal Entry":
		return any(row.get("party_type") == "Supplier" and flt(row.get("debit_in_account_currency")) > 0 and supplier_has_contract_invoices(row.get("party")) for row in doc.get("accounts") or [])
	return False


def invalidate_pending_approval(doc) -> None:
	"""A changed amount, allocation or beneficiary on an entry awaiting approval sends it back to Draft."""
	before = doc.get_doc_before_save()
	if before is None or before.get("workflow_state") != PENDING_STATE:
		return
	changed = [field for field in WATCHED_ON_PENDING if str(before.get(field)) != str(doc.get(field))] + (["references"] if allocations(before) != allocations(doc) else [])
	if changed:
		doc.workflow_state = DRAFT_STATE
		frappe.flags.cm_approval_invalidated = changed


def on_event(doc, method: str | None = None) -> None:
	if doc.doctype == "Payment Entry" and method == "validate" and not doc.is_new():
		invalidate_pending_approval(doc)
		return
	if doc.doctype not in ("Payment Entry", "Journal Entry") or method not in PAYMENT_METHODS:
		return
	if not pays_a_contract_supplier(doc):
		return
	if not in_operation():
		fail("CM_HOLD", reason="This payment goes to a supplier with contract invoices and must be made through the controlled KenTender operation.", consequence="pay")
	if method == "before_submit":
		for order, amount in order_allocations(doc).items():
			held = advance_entitlement(order, lock=True)  # a concurrent advance waits here, then sees this one
			if held["cm_linked"] and amount > held["available"] + TOLERANCE:
				fail("CM_HOLD", reason=f"{order} has {held['certified']:,.2f} certified as an advance and {held['paid']:,.2f} already paid; {amount:,.2f} is more than the supported advance.",
					order=order, certified=held["certified"], paid=held["paid"], requested=amount, consequence="pay")
	for invoice, amount in new_allocations(doc, method).items():
		held = entitlement(invoice, lock=True)  # a concurrent payment waits here, then sees this one
		if not held["cm_linked"]:
			continue
		if amount > held["available"] + TOLERANCE:
			fail("CM_HOLD", reason=f"{invoice} is certified for {held['certified']:,.2f} and {held['paid']:,.2f} is already settled; {amount:,.2f} is more than the supported amount.",
				invoice=invoice, certified=held["certified"], settled=held["paid"], requested=amount, consequence="pay")
