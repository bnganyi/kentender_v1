# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The controlled façade over ERPNext Buying, Stock, Assets and Accounts (CM-CHG-001 v0.8 §9.1; plan D7).

Contract Management never writes a ledger row, a Stock Entry for an asset receipt or a serial number of its own. It creates and
reverses the native documents through ERPNext's supported methods, each marked with its operation identity so a retry finds the
document instead of making another (`intents.py` reads the owner first with `find_by_identity`). Native records stay
authoritative; the `Contract Transaction Link` is provenance.

What ERPNext does not do for us, and the spike (S2, S3) showed it does not: it **invents a serial number** when a serialised item
is received without one, and an Asset has **no serial field**. So a receipt line for a serialised item must name exactly its
accepted units' serials, a fixed-asset line must name exactly its units' contract references, and anything else is refused before the
native call (`CM_QUANTITY`). The references are written onto the assets inside the receipt's own transaction. Reversal follows the
order ERPNext enforces (inspection then receipt, invoice then receipt, asset then receipt); a receipt with a downstream document is
refused with `CM_RECONCILE` naming it. The net payable after a credit note is read from the supplier ledger, because the native
credit note stands alone and leaves the original invoice's outstanding unchanged (FU-CM-53)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import flt, today

from kentender_contracts.native import payment_guard
from kentender_contracts.services import service_principal
from kentender_contracts.services.errors import fail

UNIT_REFERENCES = "cm_unit_references"  # flag: {(receipt, item_code): [reference, ...]} consumed as assets are created


def find_by_identity(doctype: str, identity: str) -> str | None:
	"""The owner's document for an operation identity, if it exists and is not cancelled."""
	return frappe.db.get_value(doctype, {"cm_operation_identity": identity, "docstatus": ["<", 2]}, "name")


# -- order -----------------------------------------------------------------------------------------------------------------------
def create_purchase_order(identity: str, *, company: str, supplier: str, items: list[dict[str, Any]], currency: str, schedule_date: str, transaction_date: str | None = None) -> str:
	"""One submitted Purchase Order per operation identity; a replay returns the document that exists. `items`: item_code, qty, rate, warehouse."""
	existing = find_by_identity("Purchase Order", identity)
	if existing:
		return existing
	po = frappe.get_doc({"doctype": "Purchase Order", "company": company, "supplier": supplier, "currency": currency, "transaction_date": transaction_date or today(),
		"schedule_date": schedule_date, "cm_operation_identity": identity,
		"items": [{"item_code": i["item_code"], "qty": i["qty"], "rate": i["rate"], "schedule_date": schedule_date, "warehouse": i.get("warehouse")} for i in items]})
	po.insert(ignore_permissions=True)
	po.submit()
	return po.name


# -- receipt ---------------------------------------------------------------------------------------------------------------------
def _refuse_unidentified_units(order_row_item: str, accepted: float, serials: list[str], unit_references: list[str]) -> None:
	item = frappe.db.get_value("Item", order_row_item, ["has_serial_no", "is_fixed_asset", "auto_create_assets"], as_dict=True)
	if item.has_serial_no and len(serials) != accepted:
		fail("CM_QUANTITY", item=order_row_item, accepted=accepted, serials_given=len(serials), reason="A serialised item is received only with the serial of each accepted unit; none is invented.")
	if item.is_fixed_asset and item.auto_create_assets:
		if len(unit_references) != accepted:
			fail("CM_QUANTITY", item=order_row_item, accepted=accepted, unit_references_given=len(unit_references), reason="Each accepted fixed-asset unit needs its own contract reference.")
		taken = frappe.get_all("Asset", filters={"cm_unit_reference": ["in", unit_references], "docstatus": ["<", 2]}, pluck="cm_unit_reference")
		if taken or len(set(unit_references)) != len(unit_references):
			fail("CM_QUANTITY", item=order_row_item, duplicates=sorted(set(taken) | {r for r in unit_references if unit_references.count(r) > 1}), reason="A unit reference identifies one unit only.")


def receive(order: str, identity: str, *, lines: list[dict[str, Any]], submit: bool = True) -> str:
	"""One native Purchase Receipt for the **accepted** units of an order, once per operation identity.

	`lines`: item_code, qty (accepted), serials, unit_references, asset_location, quality_inspection. Rejected units never reach a receipt."""
	existing = find_by_identity("Purchase Receipt", identity)
	if existing:
		return existing
	for line in lines:
		_refuse_unidentified_units(line["item_code"], flt(line["qty"]), list(line.get("serials") or []), list(line.get("unit_references") or []))
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	receipt = make_purchase_receipt(order)
	receipt.cm_operation_identity = identity
	wanted = {line["item_code"]: line for line in lines}
	receipt.items = [row for row in receipt.items if row.item_code in wanted]
	for row in receipt.items:
		line = wanted[row.item_code]
		row.qty = row.received_qty = flt(line["qty"])
		row.rejected_qty = 0
		if frappe.db.get_value("Item", row.item_code, "is_fixed_asset") and line.get("asset_location"):
			row.asset_location = line["asset_location"]
		if line.get("serials"):
			row.serial_no = "\n".join(line["serials"])
		if line.get("quality_inspection"):
			row.quality_inspection = line["quality_inspection"]
	receipt.insert(ignore_permissions=True)
	if submit:
		post_receipt(receipt.name, unit_references={line["item_code"]: list(line["unit_references"]) for line in lines if line.get("unit_references")})
	return receipt.name


def post_receipt(receipt: str, *, quality_inspections: dict[str, str] | None = None, unit_references: dict[str, list[str]] | None = None) -> str:
	"""Submit a Draft receipt, attaching the inspection of each item and naming the units of each fixed-asset item. The references are written
	onto the assets as ERPNext creates them, in this transaction."""
	doc = frappe.get_doc("Purchase Receipt", receipt)
	if quality_inspections:
		for row in doc.items:
			if row.item_code in quality_inspections:
				row.quality_inspection = quality_inspections[row.item_code]
		doc.save(ignore_permissions=True)
	frappe.flags[UNIT_REFERENCES] = {(receipt, item): list(refs) for item, refs in (unit_references or {}).items()}
	try:
		doc.submit()
	finally:
		frappe.flags.pop(UNIT_REFERENCES, None)
	return doc.name


def assign_unit_references(receipt, method: str | None = None) -> None:
	"""`Purchase Receipt.on_submit`, after ERPNext's own: ERPNext creates a receipt's assets with `db_insert`, which fires no asset event, so the
	assets of a receipt this adapter submitted are numbered here, in the same transaction, in creation order. A receipt submitted any other way
	is untouched."""
	pending = frappe.flags.get(UNIT_REFERENCES) or {}
	for (name, item_code), references in pending.items():
		if name != receipt.name:
			continue
		assets = frappe.get_all("Asset", filters={"purchase_receipt": name, "item_code": item_code, "docstatus": 0}, pluck="name", order_by="creation asc, name asc")
		if len(assets) != len(references):
			fail("CM_QUANTITY", item=item_code, assets_created=len(assets), unit_references_given=len(references), reason="The receipt did not create one asset for each named unit.")
		for asset, reference in zip(assets, references):
			frappe.db.set_value("Asset", asset, "cm_unit_reference", reference, update_modified=False)


# -- inspection ------------------------------------------------------------------------------------------------------------------
def ensure_parameter(name: str, description: str = "") -> str:
	if not frappe.db.exists("Quality Inspection Parameter", name):
		frappe.get_doc({"doctype": "Quality Inspection Parameter", "parameter": name, "description": description or name}).insert(ignore_permissions=True)
	return name


def inspect_accepted(receipt: str, item_code: str, *, status: str, sample: int, inspector: str, readings: list[dict[str, Any]]) -> str:
	"""A native Quality Inspection for one receipt row. `readings`: specification, status, reading_1 (CM's frozen criterion and finding)."""
	row = frappe.db.get_value("Purchase Receipt Item", {"parent": receipt, "item_code": item_code}, ["name", "item_name"], as_dict=True)
	for reading in readings:
		ensure_parameter(reading["specification"])
	qi = frappe.get_doc({"doctype": "Quality Inspection", "inspection_type": "Incoming", "reference_type": "Purchase Receipt", "reference_name": receipt, "child_row_reference": row.name,
		"item_code": item_code, "item_name": row.item_name, "sample_size": sample, "inspected_by": inspector, "report_date": today(), "manual_inspection": 1, "status": status,
		"readings": [{**r, "manual_inspection": 1} for r in readings]})
	qi.insert(ignore_permissions=True)
	qi.submit()
	return qi.name


# -- invoice and payment ---------------------------------------------------------------------------------------------------------
def invoice_receipt(receipt: str, identity: str, *, bill_no: str, bill_date: str | None = None, qty: float | None = None, submit: bool = True) -> str:
	"""A native Purchase Invoice from a receipt (accepted quantity only), once per operation identity. `submit=False` leaves it a Draft for the Finance maker to complete
	(`prepare_invoice`) and the Finance approver to post (`post_invoice`); the supplier's claim is recorded as a draft and posts only after certification and approval."""
	existing = find_by_identity("Purchase Invoice", identity)
	if existing:
		return existing
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	invoice = make_purchase_invoice(receipt)
	invoice.cm_operation_identity = identity
	invoice.bill_no = bill_no
	invoice.bill_date = bill_date or today()
	if qty is not None:
		invoice.items[0].qty = qty
	invoice.insert(ignore_permissions=True)
	if submit:
		invoice.submit()
	return invoice.name


def prepare_invoice(invoice: str, *, posting_date: str, payable_account: str, cost_centre: str, expense_account: str, tax_template: str = "") -> dict[str, Any]:
	"""The accounting details of a Draft native invoice, saved by the Finance maker: posting date, payable account, accounting treatment (the expense or asset account of each line), tax
	treatment and cost centre. The supplier's quantities and rates are untouched; a submitted invoice is refused."""
	doc = frappe.get_doc("Purchase Invoice", invoice)
	if doc.docstatus != 0:
		fail("CM_RECONCILE", invoice=invoice, reason="The accounting invoice is already posted.")
	doc.set_posting_time = 1
	doc.posting_date = posting_date
	doc.credit_to = payable_account
	if tax_template:
		doc.taxes_and_charges = tax_template
		doc.set_taxes()
	for row in doc.items:
		row.cost_center, row.expense_account = cost_centre, expense_account
	doc.cost_center = cost_centre
	doc.save(ignore_permissions=True)
	return {"invoice": invoice, "posting_date": str(doc.posting_date), "credit_to": doc.credit_to, "grand_total": doc.grand_total}


def post_invoice(invoice: str, user: str) -> dict[str, Any]:
	"""The approver's posting of a Draft invoice: the configured workflow's Approve if the site has one for Purchase Invoice, otherwise the native submission, taken as `user`."""
	from frappe.model.workflow import apply_workflow, get_workflow_name

	with service_principal.acting_as(user):
		doc = frappe.get_doc("Purchase Invoice", invoice)
		if get_workflow_name("Purchase Invoice"):
			doc = apply_workflow(doc, "Approve")
		else:
			doc.submit()
	return {"invoice": invoice, "docstatus": doc.docstatus}


def certify_invoice(invoice: str, amount: float) -> None:
	"""Record what procurement certified on the invoice: the ceiling the payment guard enforces. A direct write of the custom field."""
	frappe.db.set_value("Purchase Invoice", invoice, "cm_certified_amount", amount)


def payment_draft(invoice: str, identity: str, *, amount: float | None = None, mode_of_payment: str, paid_from: str, reference_no: str, reference_date: str | None = None) -> str:
	"""A Draft native Payment Entry for an invoice, once per operation identity. Submission is the controlled operation's, not this call's."""
	existing = find_by_identity("Payment Entry", identity)
	if existing:
		return existing
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	entry = get_payment_entry("Purchase Invoice", invoice)
	entry.mode_of_payment, entry.paid_from, entry.reference_no, entry.reference_date = mode_of_payment, paid_from, reference_no, reference_date or today()
	entry.cm_operation_identity = identity
	if amount is not None:
		entry.paid_amount = entry.received_amount = amount
		entry.references[0].allocated_amount = amount
	entry.insert()
	return entry.name


def update_payment_draft(entry: str, *, amount: float | None = None, mode_of_payment: str | None = None, paid_from: str | None = None, reference_no: str | None = None) -> str:
	"""The maker's changes to an unposted native payment. Saving an entry that is awaiting approval sends it back to Draft (the guard's rule for a changed amount)."""
	doc = frappe.get_doc("Payment Entry", entry)
	if doc.docstatus != 0:
		fail("CM_RECONCILE", payment=entry, reason="The payment is already posted.")
	if mode_of_payment:
		doc.mode_of_payment = mode_of_payment
	if paid_from:
		doc.paid_from = paid_from
	if reference_no:
		doc.reference_no = reference_no
	if amount is not None:
		doc.paid_amount = doc.received_amount = amount
		doc.references[0].allocated_amount = amount
	doc.save()
	return doc.name


def approve_payment(entry: str, identity: str, user: str) -> dict[str, Any]:
	"""The native workflow's Approve, taken as `user` inside the controlled operation. The workflow itself refuses an entry's own maker
	(`allow_self_approval = 0`); the guard checks the entitlement under a lock when the entry posts."""
	from frappe.model.workflow import apply_workflow

	with service_principal.acting_as(user):
		with payment_guard.native_operation(identity):
			doc = apply_workflow(frappe.get_doc("Payment Entry", entry), "Approve")
	return {"workflow_state": doc.workflow_state, "docstatus": doc.docstatus}


# -- reading and reversal --------------------------------------------------------------------------------------------------------
def net_payable(supplier: str, on: str | None = None) -> float:
	"""What is owed to the supplier, read from the ledger. After a credit note this, not the original invoice's outstanding, is the net:
	the native credit note stands alone and leaves the invoice it reduces unchanged. Positive means money owed to the supplier."""
	from erpnext.accounts.utils import get_balance_on

	return -flt(get_balance_on(party_type="Supplier", party=supplier, date=on or today()))


def receipt_facts(receipt: str) -> dict[str, Any]:
	"""What ERPNext holds for a posted receipt, read only: the quantity and value of each line, the stock it put on the ledger, the assets made from it and the general ledger it posted. Contract Management
	compares this with what the acceptance decided (`delivery.reconcile_receipt`); it never repairs a difference itself."""
	doc = frappe.get_doc("Purchase Receipt", receipt)
	items: dict[str, dict[str, float]] = {}
	for row in doc.items:
		entry = items.setdefault(row.item_code, {"qty": 0.0, "amount": 0.0})
		entry["qty"] += flt(row.qty)
		entry["amount"] += flt(row.amount)
	stock: dict[str, float] = {}
	for row in frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Purchase Receipt", "voucher_no": receipt, "is_cancelled": 0}, fields=["item_code", "actual_qty"]):
		stock[row.item_code] = stock.get(row.item_code, 0.0) + flt(row.actual_qty)
	ledger = frappe.db.sql("select coalesce(sum(debit), 0), coalesce(sum(credit), 0), count(*) from `tabGL Entry` where voucher_type = 'Purchase Receipt' and voucher_no = %s and is_cancelled = 0", receipt)[0]
	return {"docstatus": doc.docstatus, "items": items, "amount": sum(v["amount"] for v in items.values()), "stock": stock,
		"assets": frappe.db.count("Asset", {"purchase_receipt": receipt, "docstatus": ["<", 2]}), "ledger": {"debit": flt(ledger[0]), "credit": flt(ledger[1]), "entries": int(ledger[2])}}


def downstream_of_receipt(receipt: str) -> dict[str, list[str]]:
	"""The submitted documents that must be reversed before this receipt can be: invoices and assets."""
	invoices = frappe.get_all("Purchase Invoice Item", filters={"purchase_receipt": receipt, "docstatus": 1}, pluck="parent", distinct=True)
	assets = frappe.get_all("Asset", filters={"purchase_receipt": receipt, "docstatus": 1}, pluck="name")
	returns = frappe.get_all("Purchase Receipt", filters={"return_against": receipt, "docstatus": 1}, pluck="name")
	return {key: value for key, value in (("Purchase Invoice", invoices), ("Asset", assets), ("Purchase Receipt (return)", returns)) if value}


def reverse_receipt(receipt: str) -> dict[str, Any]:
	"""Cancel a posted receipt in the order ERPNext enforces: its inspections first, then the receipt. A receipt with a submitted invoice,
	asset or return is refused (`CM_RECONCILE`) naming them; those are reversed by their own corrections first."""
	blocking = downstream_of_receipt(receipt)
	if blocking:
		fail("CM_RECONCILE", receipt=receipt, downstream=blocking, reason="Reverse the documents that depend on this receipt first.")
	inspections = frappe.get_all("Quality Inspection", filters={"reference_name": receipt, "docstatus": 1}, pluck="name")
	for qi in inspections:
		frappe.db.set_value("Purchase Receipt Item", {"parent": receipt, "quality_inspection": qi}, "quality_inspection", None)  # detach, then cancel the inspection
		frappe.get_doc("Quality Inspection", qi).cancel()
	frappe.get_doc("Purchase Receipt", receipt).cancel()
	return {"receipt": receipt, "inspections_cancelled": inspections, "docstatus": frappe.db.get_value("Purchase Receipt", receipt, "docstatus")}
