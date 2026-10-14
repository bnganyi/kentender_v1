"""Phase 2 spike S7 (tracker CM8-208): recovery by operation identity after a hard crash, and native reversals."""

from __future__ import annotations

import json
import os
import subprocess

import frappe
from frappe.utils import flt

from kentender_contracts.spike import native, world
from kentender_core.services.command_write_guard import command_write

CASE = "CM-SPIKE-CASE-S7"
NAMESPACE = "CM_SPIKE"
IDENTITY = f"{CASE}|agreement 1|1|Purchase order|crash-1"


def _case() -> None:
	if not frappe.db.exists("Contract Case", CASE):
		with command_write("Contract Management"):
			frappe.get_doc({"doctype": "Contract Case", "contract_id": CASE, "source_kind": "External record", "fixture_namespace": NAMESPACE}).insert(ignore_permissions=True)
		frappe.db.commit()


def _intent() -> "frappe.model.document.Document":
	existing = frappe.db.get_value("Contract Operation Intent", {"operation_identity": IDENTITY}, "name")
	if existing:
		return frappe.get_doc("Contract Operation Intent", existing)
	with command_write("Contract Management"):
		doc = frappe.get_doc({"doctype": "Contract Operation Intent", "contract_case": CASE, "subject": "agreement 1", "subject_version": 1, "operation_kind": "Purchase order",
			"operation_key": "crash-1", "operation_identity": IDENTITY, "state": "Recorded", "recovery_owner": "Technical recovery", "fixture_namespace": NAMESPACE})
		doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc


def crash_after_native_commit() -> None:
	"""Phase 1 of S7 (its own process): record the intent, create and commit the native order, then die before writing the link."""
	native._ensure_world()
	_case()
	intent = _intent()
	with command_write("Contract Management"):
		intent.state = "Attempting"
		intent.save(ignore_permissions=True)
	frappe.db.commit()
	po = native.create_purchase_order(IDENTITY, world.ITEM_FA, 10, 100000)
	frappe.db.commit()
	print(f"CRASH native order {po} committed; dying before the link is written", flush=True)
	os._exit(137)


def recover() -> dict:
	"""Technical recovery: read the owner first by operation identity, link what exists, only then create."""
	intent = _intent()
	found = native.find_by_identity("Purchase Order", IDENTITY)
	created = False
	if not found:
		found = native.create_purchase_order(IDENTITY, world.ITEM_FA, 10, 100000)
		created = True
	with command_write("Contract Management"):
		intent.reload()
		intent.result_reference = found
		intent.state = "Succeeded" if created else "Reconciled"
		intent.save(ignore_permissions=True)
	frappe.db.commit()
	return {"order": found, "created_new_order": created, "intent_state": intent.state}


def s7a_crash_recovery() -> list[dict]:
	bench = os.path.abspath(os.path.join(os.path.realpath(frappe.get_app_path("kentender_contracts")), "..", "..", "..", ".."))
	proc = subprocess.run(["bench", "--site", frappe.local.site, "execute", "kentender_contracts.spike.recovery.crash_after_native_commit"], cwd=bench, capture_output=True, text=True, timeout=240)
	native.record("S7a.process_crashed", exit_code=proc.returncode, output=[l for l in proc.stdout.splitlines() if l.startswith("CRASH")])
	frappe.db.rollback()
	native.record("S7a.state_after_crash", orders_with_identity=frappe.db.count("Purchase Order", {"cm_operation_identity": IDENTITY, "docstatus": 1}),
		intent_state=frappe.db.get_value("Contract Operation Intent", {"operation_identity": IDENTITY}, "state"), link=frappe.db.get_value("Contract Operation Intent", {"operation_identity": IDENTITY}, "result_reference"))
	native.attempt("S7a.recovery_reads_the_owner_first_and_links_the_existing_order", recover)
	native.attempt("S7a.second_recovery_is_a_no_op", recover)
	native.record("S7a.final", orders_with_identity=frappe.db.count("Purchase Order", {"cm_operation_identity": IDENTITY, "docstatus": 1}),
		intent_state=frappe.db.get_value("Contract Operation Intent", {"operation_identity": IDENTITY}, "state"), link=frappe.db.get_value("Contract Operation Intent", {"operation_identity": IDENTITY}, "result_reference"))
	return native.save("s7a_crash_recovery")


def _receive_stock(po: str, tag: str, serials: list[str]) -> str:
	pr = native.make_receipt(po, f"SPIKE-S7b|{tag}|1|Accepted receipt|k-1", len(serials), serials=serials, submit=False)
	qi = native.make_quality_inspection(pr, world.ITEM_STK, "Accepted", sample=len(serials))
	doc = frappe.get_doc("Purchase Receipt", pr)
	doc.items[0].quality_inspection = qi
	doc.save(ignore_permissions=True)
	doc.submit()
	frappe.db.commit()
	return pr


def s7b_reversals() -> list[dict]:
	"""S7b — cancel, return and credit after posting, on real documents."""
	from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import make_debit_note
	from erpnext.accounts.utils import get_balance_on
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_return
	from frappe.utils import today

	native._ensure_world()
	previous = frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item")
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
	frappe.db.commit()

	def sle(pr):
		return [{"qty": flt(r.actual_qty), "cancelled": r.is_cancelled} for r in frappe.get_all("Stock Ledger Entry", filters={"voucher_no": pr}, fields=["actual_qty", "is_cancelled"], order_by="creation asc")]

	# 1. cancel a posted receipt that nothing depends on
	po1 = native.create_purchase_order("SPIKE-S7b|order 1|1|Purchase order|k-1", world.ITEM_STK, 2, 100000)
	pr1 = _receive_stock(po1, "cancel", ["SPIKE-SN-C01", "SPIKE-SN-C02"])
	native.record("S7b.receipt_posted", sle=sle(pr1), serials=sorted(frappe.get_all("Serial No", filters={"name": ["like", "SPIKE-SN-C%"]}, pluck="name")))

	def cancel_pr():
		frappe.get_doc("Purchase Receipt", pr1).cancel()
		return {"docstatus": frappe.db.get_value("Purchase Receipt", pr1, "docstatus"), "order_per_received": frappe.db.get_value("Purchase Order", po1, "per_received"), "sle": sle(pr1),
			"serials_after": sorted(frappe.get_all("Serial No", filters={"name": ["like", "SPIKE-SN-C%"]}, pluck="name")), "gl_active_rows": len(native.gl("Purchase Receipt", pr1))}
	native.attempt("S7b.cancel_receipt_without_downstream_documents", cancel_pr)

	# 2. a receipt that has been invoiced cannot simply be cancelled
	po2 = native.create_purchase_order("SPIKE-S7b|order 2|1|Purchase order|k-1", world.ITEM_STK, 3, 100000)
	pr2 = _receive_stock(po2, "invoiced", ["SPIKE-SN-I01", "SPIKE-SN-I02", "SPIKE-SN-I03"])
	pi2 = native.make_invoice(pr2, "SPIKE-S7b|invoice 2|1|Native invoice|k-1", "INV-S7b-2")
	frappe.db.commit()
	native.attempt("S7b.cancel_receipt_after_invoice_is_refused", lambda: frappe.get_doc("Purchase Receipt", pr2).cancel())

	# 3. accepted-and-paid goods returned: stock return + debit note, no cash inferred
	native.attempt("S7b.pay_the_invoice_natively", lambda: _pay(pi2))
	def return_one_unit():
		ret = make_purchase_return(pr2)
		ret.items[0].qty = -1
		ret.items[0].received_qty = -1
		ret.items[0].serial_no = "SPIKE-SN-I03"
		ret.cm_operation_identity = "SPIKE-S7b|return 1|1|Accepted receipt|k-1"
		ret.insert(ignore_permissions=True)
		ret.submit()
		return {"return_receipt": ret.name, "sle": sle(ret.name), "serial_status": frappe.db.get_value("Serial No", "SPIKE-SN-I03", "status") if frappe.db.exists("Serial No", "SPIKE-SN-I03") else "(removed)"}
	native.attempt("S7b.return_one_paid_unit_with_its_serial", return_one_unit)

	def credit():
		dn = make_debit_note(pi2)
		dn.cm_operation_identity = "SPIKE-S7b|credit 1|1|Native invoice|k-1"
		dn.bill_no = "CN-S7b-1"
		dn.items[0].qty = -1
		dn.insert(ignore_permissions=True)
		dn.submit()
		return {"debit_note": dn.name, "grand_total": dn.grand_total, "outstanding": dn.outstanding_amount, "original_outstanding": frappe.db.get_value("Purchase Invoice", pi2, "outstanding_amount"),
			"supplier_balance_in_ledger": get_balance_on(party_type="Supplier", party=world.SUPPLIER, date=today()),
			"payment_entries_for_refund_created_automatically": frappe.db.count("Payment Entry", {"party": world.SUPPLIER, "payment_type": "Receive"})}
	native.attempt("S7b.credit_note_for_the_returned_unit", credit)

	# 4. fixed assets
	po3 = native.create_purchase_order("SPIKE-S7b|order 3|1|Purchase order|k-1", world.ITEM_FA, 2, 100000)
	pr3 = native.make_receipt(po3, "SPIKE-S7b|assets|1|Accepted receipt|k-1", 2)
	frappe.db.commit()
	assets = frappe.get_all("Asset", filters={"purchase_receipt": pr3}, pluck="name", order_by="name asc")
	native.record("S7b.assets_after_receipt", assets=assets, docstatus=[frappe.db.get_value("Asset", a, "docstatus") for a in assets])

	def submit_asset():
		a = frappe.get_doc("Asset", assets[0])
		a.available_for_use_date = today()
		a.save(ignore_permissions=True)
		a.submit()
		return {"asset": a.name, "status": a.status}
	native.attempt("S7b.submit_one_asset", submit_asset)
	native.attempt("S7b.cancel_receipt_with_a_submitted_asset_is_refused", lambda: frappe.get_doc("Purchase Receipt", pr3).cancel())

	def cancel_asset_then_receipt():
		frappe.get_doc("Asset", assets[0]).cancel()
		frappe.get_doc("Purchase Receipt", pr3).cancel()
		return {"receipt_docstatus": frappe.db.get_value("Purchase Receipt", pr3, "docstatus"), "assets_left": frappe.db.count("Asset", {"purchase_receipt": pr3})}
	native.attempt("S7b.cancel_the_asset_first_then_the_receipt", cancel_asset_then_receipt)
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", previous)
	frappe.db.commit()
	return native.save("s7b_reversals")


def _pay(pi: str) -> dict:
	pe = native.payment_draft(pi, f"SPIKE-S7b|payment {pi}|1|Native payment|k-1")
	doc = frappe.get_doc("Payment Entry", pe)
	doc.submit()
	return {"payment_entry": pe, "invoice_status": frappe.db.get_value("Purchase Invoice", pi, "status")}


def s7b2_cancel_in_the_right_order() -> list[dict]:
	"""S7b2 — cancel the inspection, then the receipt: stock and serials reverse, the order's received percentage is restored."""
	native._ensure_world()
	previous = frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item")
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
	frappe.db.commit()
	po = native.find_by_identity("Purchase Order", "SPIKE-S7b|order 1|1|Purchase order|k-1")
	pr = native.find_by_identity("Purchase Receipt", "SPIKE-S7b|cancel|1|Accepted receipt|k-1")

	def go():
		qi = frappe.db.get_value("Purchase Receipt Item", {"parent": pr}, "quality_inspection")
		before = {"sle": frappe.db.count("Stock Ledger Entry", {"voucher_no": pr, "is_cancelled": 0}), "serials": frappe.db.count("Serial No", {"name": ["like", "SPIKE-SN-C%"]}), "order_per_received": frappe.db.get_value("Purchase Order", po, "per_received")}
		frappe.db.set_value("Purchase Receipt Item", {"parent": pr}, "quality_inspection", None)  # detach, as the adapter does before cancelling its own inspection
		frappe.get_doc("Quality Inspection", qi).cancel()
		frappe.get_doc("Purchase Receipt", pr).cancel()
		after = {"docstatus": frappe.db.get_value("Purchase Receipt", pr, "docstatus"), "live_sle": frappe.db.count("Stock Ledger Entry", {"voucher_no": pr, "is_cancelled": 0}),
			"cancelled_sle": frappe.db.count("Stock Ledger Entry", {"voucher_no": pr, "is_cancelled": 1}), "serials": frappe.db.count("Serial No", {"name": ["like", "SPIKE-SN-C%"]}),
			"order_per_received": frappe.db.get_value("Purchase Order", po, "per_received"), "active_gl_rows": len(native.gl("Purchase Receipt", pr))}
		return {"before": before, "after": after}
	native.attempt("S7b2.cancel_inspection_then_receipt", go)
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", previous)
	frappe.db.commit()
	return native.save("s7b2_cancel_in_the_right_order")
