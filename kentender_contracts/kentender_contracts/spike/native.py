"""Phase 2 spike (tracker CM8-202…208): minimal native-adapter probes against the real ERPNext on the test site.

Not product code: it only reaches ERPNext through its own documents and methods, and records what happened.
"""

from __future__ import annotations

import json
import traceback

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import add_days, flt, today

from kentender_contracts.spike import world

EVIDENCE: list[dict] = []
EVIDENCE_DIR = "docs/mvp-1-r1/21_contract_management/evidence/v0_8/spike"


def save(name: str) -> str:
	"""Write the evidence of one scenario next to the tracker and reset the buffer. Returns the path."""
	import os

	root = os.path.abspath(os.path.join(os.path.realpath(frappe.get_app_path("kentender_contracts")), "..", ".."))
	folder = os.path.join(root, EVIDENCE_DIR)
	os.makedirs(folder, exist_ok=True)
	path = os.path.join(folder, f"{name}.json")
	env = {"frappe": frappe.__version__, "erpnext": __import__("erpnext").__version__, "site": frappe.local.site, "date": today()}
	with open(path, "w") as fh:
		json.dump({"environment": env, "steps": EVIDENCE}, fh, indent=1, default=str)
		fh.write("\n")
	count = len(EVIDENCE)
	EVIDENCE.clear()
	print(f"evidence: {path} ({count} steps)")
	return path


def record(step: str, **facts) -> dict:
	entry = {"step": step, **facts}
	EVIDENCE.append(entry)
	return entry


def attempt(step: str, fn, **context):
	"""Run `fn`; record success with its result or the exact error (class and message)."""
	frappe.db.savepoint("cm_attempt")
	try:
		result = fn()
		frappe.db.commit()  # a later failed step must not roll back this one
		record(step, ok=True, result=result, **context)
		return result
	except Exception as exc:  # noqa: BLE001 - the spike records every failure verbatim
		try:
			frappe.db.rollback(save_point="cm_attempt")  # undo only this step, keep earlier uncommitted setup
		except Exception:  # noqa: BLE001 - the step committed internally, so the savepoint is gone; undo what is still open
			frappe.db.rollback()
		record(step, ok=False, error=f"{type(exc).__name__}: {str(exc)[:400]}", trace=traceback.format_exc().splitlines()[-3:], **context)
		return None


def ensure_custom_fields() -> None:
	"""The documented extension point for a fact ERPNext does not hold: the CM operation identity on each native
	document it creates, and the unit reference on an Asset. `no_copy` stops an amend from inheriting it."""
	ident = {"fieldname": "cm_operation_identity", "label": "Contract operation identity", "fieldtype": "Data", "read_only": 1, "no_copy": 1, "search_index": 1, "insert_after": "naming_series"}
	create_custom_fields({
		"Purchase Order": [ident],
		"Purchase Receipt": [ident],
		"Payment Entry": [ident],
		"Purchase Invoice": [ident, {"fieldname": "cm_certified_amount", "label": "Contract certified amount", "fieldtype": "Currency", "read_only": 1, "no_copy": 1, "insert_after": "cm_operation_identity"}],
		"Asset": [{"fieldname": "cm_unit_reference", "label": "Contract unit reference", "fieldtype": "Data", "read_only": 1, "no_copy": 1, "search_index": 1, "insert_after": "asset_name"}],
	}, update=True)
	frappe.clear_cache()


def remove_custom_fields() -> None:
	for dt, field in (("Purchase Order", "cm_operation_identity"), ("Purchase Receipt", "cm_operation_identity"), ("Purchase Invoice", "cm_operation_identity"),
			("Payment Entry", "cm_operation_identity"), ("Asset", "cm_unit_reference"), ("Purchase Invoice", "cm_certified_amount")):
		name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field})
		if name:
			frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
	frappe.clear_cache()


def find_by_identity(doctype: str, identity: str) -> str | None:
	return frappe.db.get_value(doctype, {"cm_operation_identity": identity, "docstatus": ["<", 2]}, "name")


def create_purchase_order(identity: str, item: str, qty: int, rate: float, due_in_days: int = 30) -> str:
	"""S1: one native Purchase Order per operation identity; a replay returns the document that already exists."""
	existing = find_by_identity("Purchase Order", identity)
	if existing:
		return existing
	po = frappe.get_doc({
		"doctype": "Purchase Order", "company": world.COMPANY, "supplier": world.SUPPLIER, "transaction_date": today(), "schedule_date": add_days(today(), due_in_days),
		"currency": "KES", "cm_operation_identity": identity,
		"items": [{"item_code": item, "qty": qty, "rate": rate, "schedule_date": add_days(today(), due_in_days), "warehouse": world.WAREHOUSE if frappe.db.get_value("Item", item, "is_stock_item") else None}],
	})
	po.insert(ignore_permissions=True)
	po.submit()
	return po.name


def snapshot(doctype: str, name: str, fields: list[str]) -> dict:
	return {f: frappe.db.get_value(doctype, name, f) for f in fields}


def gl(voucher_type: str, voucher_no: str) -> list[dict]:
	return [{"account": r.account, "debit": flt(r.debit), "credit": flt(r.credit), "party": r.party or ""} for r in
		frappe.get_all("GL Entry", filters={"voucher_type": voucher_type, "voucher_no": voucher_no, "is_cancelled": 0}, fields=["account", "debit", "credit", "party"], order_by="creation asc")]


def s1() -> list[dict]:
	"""S1 — agreement fields → one native Purchase Order, once; the same identity returns the same document."""
	world.build()
	ensure_custom_fields()
	identity = "SPIKE-S1|agreement 1|1|Purchase order|k-1"
	first = attempt("S1.create_po", lambda: create_purchase_order(identity, world.ITEM_FA, 10, 100000))
	again = attempt("S1.replay_returns_same_po", lambda: create_purchase_order(identity, world.ITEM_FA, 10, 100000))
	if first:
		record("S1.po_facts", **snapshot("Purchase Order", first, ["docstatus", "status", "grand_total", "per_received", "per_billed", "supplier", "company", "cm_operation_identity"]))
		record("S1.same_document", ok=bool(first and first == again), first=first, again=again,
			count_with_identity=frappe.db.count("Purchase Order", {"cm_operation_identity": identity}))
	return save(__import__('inspect').stack()[0].function)


def make_receipt(po_name: str, identity: str, qty: int, *, serials: list[str] | None = None, rejected_qty: int = 0, submit: bool = True) -> str:
	"""Native Purchase Receipt for part of an order, once per operation identity. Only accepted units are on it."""
	existing = find_by_identity("Purchase Receipt", identity)
	if existing:
		return existing
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

	pr = make_purchase_receipt(po_name)
	pr.cm_operation_identity = identity
	row = pr.items[0]
	row.qty = qty
	row.received_qty = qty + rejected_qty
	row.rejected_qty = rejected_qty
	if frappe.db.get_value("Item", row.item_code, "is_fixed_asset"):
		row.asset_location = world.LOCATION
	if serials:
		row.serial_no = "\n".join(serials)
	pr.insert(ignore_permissions=True)
	if submit:
		pr.submit()
	return pr.name


def s2_s3_fixed_asset() -> list[dict]:
	"""S2/S3 (fixed asset): 8 of 10 received against the order, assets per unit, the 2 replacements consume the original order quantity."""
	po = find_by_identity("Purchase Order", "SPIKE-S1|agreement 1|1|Purchase order|k-1") or create_purchase_order("SPIKE-S1|agreement 1|1|Purchase order|k-1", world.ITEM_FA, 10, 100000)
	pr1 = attempt("S3.receive_8_of_10_fixed_asset", lambda: make_receipt(po, "SPIKE-S3|arrival 1|1|Accepted receipt|k-1", 8))
	if pr1:
		record("S3.po_after_partial_receipt", **snapshot("Purchase Order", po, ["status", "per_received", "per_billed"]))
		record("S3.pr_facts", **snapshot("Purchase Receipt", pr1, ["docstatus", "status", "total_qty", "grand_total", "per_billed"]))
		record("S3.pr_gl", gl=gl("Purchase Receipt", pr1))
		record("S3.stock_ledger_entries_for_fixed_asset_receipt", count=frappe.db.count("Stock Ledger Entry", {"voucher_no": pr1}))
		assets = frappe.get_all("Asset", filters={"purchase_receipt": pr1}, fields=["name", "status", "docstatus", "net_purchase_amount", "purchase_amount", "location", "asset_category", "asset_name"], order_by="name asc")
		record("S3.assets_from_receipt", count=len(assets), statuses=sorted({a.status for a in assets}), docstatuses=sorted({a.docstatus for a in assets}), first=assets[0] if assets else None,
			asset_fields_with_serial=[f.fieldname for f in frappe.get_meta("Asset").fields if "serial" in f.fieldname])
		# the unit reference has to be carried by a CM field: assign deterministically in creation order, inside one transaction
		def assign_units():
			names = [a.name for a in assets]
			for i, name in enumerate(names, 1):
				frappe.db.set_value("Asset", name, "cm_unit_reference", f"SPIKE-UNIT-{i:03d}")
			return [frappe.db.get_value("Asset", n, "cm_unit_reference") for n in names]
		attempt("S3.assign_unit_references_to_assets", assign_units)
	pr2 = attempt("S2.replacement_2_units_consume_original_order_quantity", lambda: make_receipt(po, "SPIKE-S2|arrival 2|1|Accepted receipt|k-1", 2))
	if pr2:
		record("S2.po_after_replacement", **snapshot("Purchase Order", po, ["status", "per_received", "per_billed"]))
	record("S2.native_receipt_of_a_fully_received_order_is_empty", items=len(__import__("erpnext.buying.doctype.purchase_order.purchase_order", fromlist=["x"]).make_purchase_receipt(po).items))

	def manual_over_receipt():
		row_name = frappe.db.get_value("Purchase Order Item", {"parent": po}, "name")
		pr = frappe.get_doc({"doctype": "Purchase Receipt", "company": world.COMPANY, "supplier": world.SUPPLIER, "posting_date": today(), "currency": "KES",
			"cm_operation_identity": "SPIKE-S2|arrival 3|1|Accepted receipt|k-1",
			"items": [{"item_code": world.ITEM_FA, "qty": 1, "rate": 100000, "purchase_order": po, "purchase_order_item": row_name, "asset_location": world.LOCATION}]})
		pr.insert(ignore_permissions=True)
		pr.submit()
		return pr.name
	attempt("S2.over_receipt_beyond_order_is_refused", manual_over_receipt)

	def submit_one_asset():
		asset_name = frappe.db.get_value("Asset", {"purchase_receipt": pr1}, "name", order_by="name asc")
		asset = frappe.get_doc("Asset", asset_name)
		asset.available_for_use_date = today()
		asset.save(ignore_permissions=True)
		asset.submit()
		return {"asset": asset.name, "status": asset.status, "docstatus": asset.docstatus, "gl": gl("Asset", asset.name), "depreciation_rows": len(asset.get("finance_books") or [])}
	if pr1:
		attempt("S3.submit_one_asset_after_receipt_no_second_valuation", submit_one_asset)
		record("S3.total_gl_for_receipt_vouchers", receipts=gl("Purchase Receipt", pr1), assets_gl_entries=frappe.db.count("GL Entry", {"voucher_type": "Asset"}))
	return save(__import__('inspect').stack()[0].function)


def _ensure_world() -> None:
	if not frappe.db.exists("Item", world.ITEM_FA):
		world.build()
	ensure_custom_fields()


def make_invoice(receipt: str, identity: str, bill_no: str, *, qty: float | None = None, submit: bool = True) -> str:
	"""Native Purchase Invoice from a receipt (accepted quantity only), once per operation identity."""
	existing = find_by_identity("Purchase Invoice", identity)
	if existing:
		return existing
	from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

	pi = make_purchase_invoice(receipt)
	pi.cm_operation_identity = identity
	pi.bill_no = bill_no
	pi.bill_date = today()
	if qty is not None:
		pi.items[0].qty = qty
	pi.insert(ignore_permissions=True)
	if submit:
		pi.submit()
	return pi.name


def s4_invoice() -> list[dict]:
	"""S4 — Purchase Invoice for accepted quantity only; over-billing; credit note after the liability; duplicate invoice."""
	_ensure_world()
	po = create_purchase_order("SPIKE-S1|agreement 1|1|Purchase order|k-1", world.ITEM_FA, 10, 100000)
	pr1 = make_receipt(po, "SPIKE-S3|arrival 1|1|Accepted receipt|k-1", 8)
	pr2 = make_receipt(po, "SPIKE-S2|arrival 2|1|Accepted receipt|k-1", 2)
	frappe.db.commit()
	pi1 = attempt("S4.invoice_for_accepted_8_units", lambda: make_invoice(pr1, "SPIKE-S4|invoice 1|2|Native invoice|k-1", "INV-01-v2"))
	if pi1:
		record("S4.pi1_facts", **snapshot("Purchase Invoice", pi1, ["docstatus", "status", "grand_total", "outstanding_amount", "bill_no"]))
		record("S4.pi1_gl", gl=gl("Purchase Invoice", pi1))
		record("S4.after_invoice_1", po=snapshot("Purchase Order", po, ["status", "per_received", "per_billed"]), pr1=snapshot("Purchase Receipt", pr1, ["status", "per_billed"]))

	def over_bill():
		row = frappe.db.get_value("Purchase Receipt Item", {"parent": pr1}, ["name", "purchase_order_item"], as_dict=True)
		pi = frappe.get_doc({"doctype": "Purchase Invoice", "company": world.COMPANY, "supplier": world.SUPPLIER, "posting_date": today(), "bill_no": "INV-01-OVER", "bill_date": today(),
			"cm_operation_identity": "SPIKE-S4|invoice over|1|Native invoice|k-1", "currency": "KES",
			"items": [{"item_code": world.ITEM_FA, "qty": 1, "rate": 100000, "purchase_receipt": pr1, "pr_detail": row.name, "purchase_order": po, "po_detail": row.purchase_order_item,
				"is_fixed_asset": 1, "asset_location": world.LOCATION}]})
		pi.insert(ignore_permissions=True)
		pi.submit()
		return pi.name
	attempt("S4.second_invoice_beyond_received_billed_quantity_is_refused", over_bill)
	pi2 = attempt("S4.invoice_for_the_2_replacement_units", lambda: make_invoice(pr2, "SPIKE-S4|invoice 2|1|Native invoice|k-1", "INV-02"))
	if pi2:
		record("S4.after_invoice_2", po=snapshot("Purchase Order", po, ["status", "per_received", "per_billed"]), pi2=snapshot("Purchase Invoice", pi2, ["grand_total", "outstanding_amount"]))

		def credit_note():
			from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import make_debit_note

			dn = make_debit_note(pi2)
			dn.cm_operation_identity = "SPIKE-S4|credit 1|1|Native invoice|k-1"
			dn.bill_no = "CN-01"
			dn.items[0].qty = -2
			dn.insert(ignore_permissions=True)
			dn.submit()
			return {"debit_note": dn.name, "grand_total": dn.grand_total, "return_against": dn.return_against, "gl": gl("Purchase Invoice", dn.name),
				"original_outstanding_after": frappe.db.get_value("Purchase Invoice", pi2, "outstanding_amount"),
				"po": snapshot("Purchase Order", po, ["status", "per_billed"])}
		attempt("S4.credit_note_after_liability_native_return", credit_note)

	def duplicate(label: str):
		def go():
			pi = frappe.get_doc(frappe.get_doc("Purchase Invoice", pi1).as_dict())
			pi = frappe.copy_doc(frappe.get_doc("Purchase Invoice", pi1))
			pi.bill_no = "INV-01-v2"
			pi.cm_operation_identity = f"SPIKE-S4|duplicate {label}|1|Native invoice|k-1"
			pi.insert(ignore_permissions=True)
			return pi.name
		return go
	record("S4.supplier_invoice_uniqueness_setting_before", value=frappe.db.get_single_value("Accounts Settings", "check_supplier_invoice_uniqueness"))
	attempt("S4.duplicate_bill_no_with_uniqueness_check_off", duplicate("off"))
	frappe.db.set_single_value("Accounts Settings", "check_supplier_invoice_uniqueness", 1)
	frappe.db.commit()
	attempt("S4.duplicate_bill_no_with_uniqueness_check_on", duplicate("on"))
	frappe.db.set_single_value("Accounts Settings", "check_supplier_invoice_uniqueness", 0)
	frappe.db.commit()
	return save("s4_invoice")


def s4b_credit_note_net_position() -> list[dict]:
	"""S4b — after a credit note against a posted invoice, where does the net payable show: the invoice, the credit note, or the ledger?"""
	pi2 = find_by_identity("Purchase Invoice", "SPIKE-S4|invoice 2|1|Native invoice|k-1")
	dn = find_by_identity("Purchase Invoice", "SPIKE-S4|credit 1|1|Native invoice|k-1")
	pi1 = find_by_identity("Purchase Invoice", "SPIKE-S4|invoice 1|2|Native invoice|k-1")
	from erpnext.accounts.utils import get_balance_on

	record("S4b.invoices", **{name: snapshot("Purchase Invoice", name, ["docstatus", "status", "grand_total", "outstanding_amount", "is_return", "return_against", "update_outstanding_for_self"]) for name in (pi1, pi2, dn) if name})
	ple = frappe.get_all("Payment Ledger Entry", filters={"party": world.SUPPLIER, "delinked": 0}, fields=["voucher_no", "against_voucher_no", "amount", "account_type"], order_by="creation asc")
	record("S4b.payment_ledger_entries", rows=[{k: (flt(v) if k == "amount" else v) for k, v in r.items()} for r in ple])
	record("S4b.supplier_balance_in_ledger", gl_balance=get_balance_on(party_type="Supplier", party=world.SUPPLIER, date=today()))
	return save("s4b_credit_note_net_position")


# ---------------------------------------------------------------------------------------------------------------------
# S5 — payment control
# ---------------------------------------------------------------------------------------------------------------------
from contextlib import contextmanager

WORKFLOW = "CM Spike Payment Approval"
CRITERION = "CM-SPIKE criterion 1 screen size at least 14 inch"


@contextmanager
def as_user(email: str):
	previous = frappe.session.user
	frappe.set_user(email)
	try:
		yield
	finally:
		frappe.set_user(previous)


def fresh_invoice(tag: str, units: int = 1) -> str:
	"""A posted native Purchase Invoice of `units` x KES 100,000 (order → receipt → invoice), once per tag."""
	_ensure_world()
	po = create_purchase_order(f"SPIKE-S5|{tag}|1|Purchase order|k-1", world.ITEM_FA, units, 100000)
	pr = make_receipt(po, f"SPIKE-S5|{tag}|1|Accepted receipt|k-1", units)
	pi = make_invoice(pr, f"SPIKE-S5|{tag}|1|Native invoice|k-1", f"INV-{tag}")
	frappe.db.commit()
	return pi


def ensure_workflow() -> None:
	for state in ("Draft", "Pending Approval", "Approved"):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)
	for action in ("Submit for approval", "Approve", "Return"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
	if frappe.db.exists("Workflow", WORKFLOW):
		return
	frappe.get_doc({
		"doctype": "Workflow", "workflow_name": WORKFLOW, "document_type": "Payment Entry", "is_active": 1, "workflow_state_field": "workflow_state", "send_email_alert": 0,
		"states": [
			{"state": "Draft", "doc_status": "0", "allow_edit": "Accounts User"},
			{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Accounts Manager"},
			{"state": "Approved", "doc_status": "1", "allow_edit": "Accounts Manager"},
		],
		"transitions": [
			{"state": "Draft", "action": "Submit for approval", "next_state": "Pending Approval", "allowed": "Accounts User", "allow_self_approval": 1},
			{"state": "Pending Approval", "action": "Approve", "next_state": "Approved", "allowed": "Accounts Manager", "allow_self_approval": 0},
			{"state": "Pending Approval", "action": "Return", "next_state": "Draft", "allowed": "Accounts Manager", "allow_self_approval": 0},
		],
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()


def payment_draft(pi: str, identity: str, *, amount: float | None = None, user: str | None = None) -> str:
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	def build():
		pe = get_payment_entry("Purchase Invoice", pi)
		pe.mode_of_payment = "Wire Transfer"
		pe.paid_from = world.BANK_ACCOUNT
		pe.reference_no = f"BANK-{identity[-12:]}"
		pe.reference_date = today()
		pe.cm_operation_identity = identity
		if amount is not None:
			pe.paid_amount = pe.received_amount = amount
			pe.references[0].allocated_amount = amount
		pe.insert()
		return pe.name

	if user:
		with as_user(user):
			return build()
	return build()


def s5a_workflow_maker_approver() -> list[dict]:
	"""S5a — maker/approver separation through the configured native workflow, and the direct-submit bypasses."""
	_ensure_world()
	ensure_workflow()
	maker, approver, other = world.USERS["maker"], world.USERS["approver"], world.USERS["other"]
	pi_a = fresh_invoice("A")
	record("S5a.workflow", states=[(s.state, s.doc_status) for s in frappe.get_doc("Workflow", WORKFLOW).states], pe_has_workflow_state_field=frappe.get_meta("Payment Entry").has_field("workflow_state"))
	from frappe.model.workflow import apply_workflow

	pe = attempt("S5a.maker_creates_payment_draft", lambda: payment_draft(pi_a, "SPIKE-S5a|payment A|1|Native payment|k-1", user=maker))
	if pe:
		def act(user, action, name=pe):
			with as_user(user):
				doc = frappe.get_doc("Payment Entry", name)
				doc = apply_workflow(doc, action)
				return {"workflow_state": doc.workflow_state, "docstatus": doc.docstatus}
		attempt("S5a.maker_submits_for_approval", lambda: act(maker, "Submit for approval"))
		attempt("S5a.maker_cannot_approve_lacking_the_role", lambda: act(maker, "Approve"))
		approved = attempt("S5a.separate_approver_approves", lambda: act(approver, "Approve"))
		if approved:
			record("S5a.payment_posted", pe=snapshot("Payment Entry", pe, ["docstatus", "workflow_state", "paid_amount", "status"]), gl=gl("Payment Entry", pe), invoice=snapshot("Purchase Invoice", pi_a, ["status", "outstanding_amount"]))
	# own-entry approval by a user who holds both roles
	pi_b = fresh_invoice("B")
	pe_own = attempt("S5a.dual_role_user_creates_own_payment", lambda: payment_draft(pi_b, "SPIKE-S5a|payment B|1|Native payment|k-1", user=other))
	if pe_own:
		with as_user(other):
			apply_workflow(frappe.get_doc("Payment Entry", pe_own), "Submit for approval")
		attempt("S5a.own_entry_approval_is_refused_allow_self_approval_off", lambda: act(other, "Approve", pe_own))
	# bypass: submit directly, without the workflow, by users who hold submit rights
	pi_c = fresh_invoice("C")
	pe_c = attempt("S5a.draft_for_direct_submit", lambda: payment_draft(pi_c, "SPIKE-S5a|payment C|1|Native payment|k-1", user=other))
	if pe_c:
		def direct_submit(user):
			with as_user(user):
				doc = frappe.get_doc("Payment Entry", pe_c)
				doc.submit()
				return {"docstatus": doc.docstatus, "workflow_state": doc.get("workflow_state")}
		attempt("S5a.bypass_doc_submit_by_accounts_manager_in_draft_state", lambda: direct_submit(other))
		record("S5a.entry_after_bypass_attempt", **snapshot("Payment Entry", pe_c, ["docstatus", "workflow_state"]))
	pi_d = fresh_invoice("D")
	pe_d = attempt("S5a.draft_for_api_submit", lambda: payment_draft(pi_d, "SPIKE-S5a|payment D|1|Native payment|k-1", user=other))
	if pe_d:
		def api_submit():
			with as_user(other):
				from frappe.desk.form.save import savedocs

				doc = frappe.get_doc("Payment Entry", pe_d)
				savedocs(frappe.as_json(doc.as_dict()), "Submit")
				return snapshot("Payment Entry", pe_d, ["docstatus", "workflow_state"])
		attempt("S5a.bypass_desk_savedocs_submit_in_draft_state", api_submit)
		def admin_submit():
			with as_user("Administrator"):
				doc = frappe.get_doc("Payment Entry", pe_d)
				doc.submit()
				return snapshot("Payment Entry", pe_d, ["docstatus", "workflow_state"])
		attempt("S5a.bypass_doc_submit_by_administrator", admin_submit)
	return save("s5a_workflow_maker_approver")


def hold_invoice(pi: str) -> None:
	frappe.db.set_value("Purchase Invoice", pi, {"on_hold": 1, "release_date": add_days(today(), 30), "hold_comment": "CM SPIKE hold"})
	frappe.db.commit()


def certify(pi: str, amount: float) -> None:
	frappe.db.set_value("Purchase Invoice", pi, "cm_certified_amount", amount)
	frappe.db.commit()


def _creditors() -> str:
	return frappe.db.get_value("Company", world.COMPANY, "default_payable_account")


def path_direct_entry(pi: str) -> dict:
	other = world.USERS["other"]
	stage = "insert"
	name = payment_draft(pi, f"SPIKE-S5b|direct {pi}|1|Native payment|k-1", user=other)
	stage = "submit"
	with as_user(other):
		doc = frappe.get_doc("Payment Entry", name)
		doc.submit()
	return {"stage_reached": "posted", "payment_entry": name}


def path_api_entry(pi: str) -> dict:
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	with as_user(world.USERS["other"]):
		pe = get_payment_entry("Purchase Invoice", pi)
		pe.mode_of_payment, pe.paid_from, pe.reference_no, pe.reference_date = "Wire Transfer", world.BANK_ACCOUNT, f"API-{pi}", today()
		pe.cm_operation_identity = f"SPIKE-S5b|api {pi}|1|Native payment|k-1"
		inserted = frappe.client.insert(frappe.parse_json(frappe.as_json(pe.as_dict())))
		submitted = frappe.client.submit(frappe.parse_json(frappe.as_json(frappe.get_doc("Payment Entry", inserted["name"]).as_dict())))
	return {"stage_reached": "posted", "payment_entry": submitted["name"]}


def path_journal_entry(pi: str) -> dict:
	with as_user(world.USERS["other"]):
		je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": world.COMPANY, "posting_date": today(), "user_remark": f"CM SPIKE settlement {pi}",
			"accounts": [
				{"account": _creditors(), "party_type": "Supplier", "party": world.SUPPLIER, "debit_in_account_currency": 100000, "reference_type": "Purchase Invoice", "reference_name": pi},
				{"account": world.BANK_ACCOUNT, "credit_in_account_currency": 100000}]})
		je.insert()
		je.submit()
	return {"stage_reached": "posted", "journal_entry": je.name, "invoice_outstanding": frappe.db.get_value("Purchase Invoice", pi, "outstanding_amount")}


def path_reconcile_advance(pi: str) -> dict:
	"""An unreferenced supplier payment (advance), then Payment Reconciliation allocates it to the invoice."""
	other = world.USERS["other"]
	with as_user(other):
		adv = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Pay", "company": world.COMPANY, "posting_date": today(), "party_type": "Supplier", "party": world.SUPPLIER,
			"paid_from": world.BANK_ACCOUNT, "paid_to": _creditors(), "paid_amount": 100000, "received_amount": 100000, "mode_of_payment": "Wire Transfer",
			"reference_no": f"ADV-{pi}", "reference_date": today(), "cm_operation_identity": f"SPIKE-S5b|advance {pi}|1|Native payment|k-1"})
		adv.insert()
		if frappe.flags.get("cm_spike_advance_in_operation"):
			from kentender_contracts.spike import guards

			with guards.native_operation(f"SPIKE-advance-{pi}"):
				adv.submit()
		else:
			adv.submit()
		frappe.db.commit()
		pr = frappe.get_doc("Payment Reconciliation")
		pr.company, pr.party_type, pr.party, pr.receivable_payable_account = world.COMPANY, "Supplier", world.SUPPLIER, _creditors()
		pr.get_unreconciled_entries()
		invoices = [x.as_dict() for x in pr.invoices if x.invoice_number == pi]
		payments = [x.as_dict() for x in pr.payments if x.reference_name == adv.name]
		counts = {"invoices_listed": len(pr.invoices), "payments_listed": len(pr.payments), "invoice_found": len(invoices), "payment_found": len(payments)}
		try:
			pr.allocate_entries({"invoices": invoices, "payments": payments})
		except Exception as exc:  # noqa: BLE001 - say what Payment Reconciliation could see
			raise type(exc)(f"{exc} | what reconciliation listed: {counts}") from exc
		counts["allocation_rows"] = len(pr.allocation)
		for row in pr.allocation:
			row.allocated_amount = 100000
		frappe.flags.cm_probe_events = []  # only the reconcile step's events are of interest
		pr.reconcile()
	return {"stage_reached": "reconciled", "advance": adv.name, "counts": counts, "invoice_outstanding": frappe.db.get_value("Purchase Invoice", pi, "outstanding_amount")}


PATHS = {"direct_entry": path_direct_entry, "api_entry": path_api_entry, "journal_entry": path_journal_entry, "reconcile_advance": path_reconcile_advance}


def s5b_paths(mode: str = "probe", hold: bool = False, tag: str = "") -> list[dict]:
	"""S5b — every payment-capable path against an uncertified invoice (optionally also held natively). mode: probe (record events) | enforce."""
	_ensure_world()
	frappe.flags.cm_spike_mode = mode
	for label, fn in PATHS.items():
		pi = fresh_invoice(f"{mode}{tag}-{label}")
		if hold:
			hold_invoice(pi)
		frappe.flags.cm_probe_events = []
		outcome = attempt(f"S5b.{mode}.{label}", lambda fn=fn, pi=pi: fn(pi), invoice=pi, native_hold=hold)
		record(f"S5b.{mode}.{label}.events", events=sorted(set(frappe.flags.cm_probe_events)), posted=bool(outcome), invoice=snapshot("Purchase Invoice", pi, ["status", "outstanding_amount", "on_hold"]))
	frappe.flags.cm_spike_mode = ""
	return save(f"s5b_paths_{mode}{tag}")


def approve_in_operation(pe: str, user: str):
	from frappe.model.workflow import apply_workflow

	from kentender_contracts.spike import guards

	with as_user(user), guards.native_operation(pe):
		doc = apply_workflow(frappe.get_doc("Payment Entry", pe), "Approve")
		return {"workflow_state": doc.workflow_state, "docstatus": doc.docstatus}


def s5c_enforce() -> list[dict]:
	"""S5c — with the CM guard: every route refused outside the controlled operation; the legitimate path and entitlement limits work."""
	from frappe.model.workflow import apply_workflow

	_ensure_world()
	ensure_workflow()
	maker, approver, other = world.USERS["maker"], world.USERS["approver"], world.USERS["other"]
	frappe.flags.cm_spike_mode = "enforce"
	frappe.flags.cm_spike_advance_in_operation = True

	# 1. every payment-capable route against an uncertified contract invoice
	for label, fn in PATHS.items():
		pi = fresh_invoice(f"enf-{label}")
		before_pe = frappe.db.count("Payment Entry", {"party": world.SUPPLIER})
		before_je = frappe.db.count("Journal Entry", {"user_remark": ["like", "CM SPIKE%"], "docstatus": 1})
		attempt(f"S5c.route_{label}_outside_the_operation", lambda fn=fn, pi=pi: fn(pi), invoice=pi)
		record(f"S5c.route_{label}.state_after", invoice=snapshot("Purchase Invoice", pi, ["status", "outstanding_amount"]),
			submitted_payments_added=frappe.db.count("Payment Entry", {"party": world.SUPPLIER, "docstatus": 1}) - frappe.db.count("Payment Entry", {"party": world.SUPPLIER, "docstatus": 1, "creation": ["<", frappe.utils.now_datetime()]}) if False else None,
			journal_entries_posted_for_invoice=frappe.db.count("Journal Entry", {"user_remark": f"CM SPIKE settlement {pi}", "docstatus": 1}))

	# 2. the legitimate path, and the entitlement limits (CM-AC-39)
	pi_full = fresh_invoice("ent-full", units=8)
	certify(pi_full, 800000)
	pe1 = payment_draft(pi_full, "SPIKE-S5c|full payment 1|1|Native payment|k-1", amount=500000, user=maker)
	with as_user(maker):
		apply_workflow(frappe.get_doc("Payment Entry", pe1), "Submit for approval")
	attempt("S5c.approve_500k_inside_operation", lambda: approve_in_operation(pe1, approver))
	pe2 = payment_draft(pi_full, "SPIKE-S5c|full payment 2|1|Native payment|k-1", amount=300000, user=maker)
	with as_user(maker):
		apply_workflow(frappe.get_doc("Payment Entry", pe2), "Submit for approval")
	attempt("S5c.approve_300k_inside_operation", lambda: approve_in_operation(pe2, approver))
	record("S5c.invoice_after_500k_and_300k", **snapshot("Purchase Invoice", pi_full, ["status", "outstanding_amount", "cm_certified_amount"]))

	pi_part = fresh_invoice("ent-part", units=8)
	certify(pi_part, 600000)
	pa = payment_draft(pi_part, "SPIKE-S5c|part payment 1|1|Native payment|k-1", amount=500000, user=maker)
	with as_user(maker):
		apply_workflow(frappe.get_doc("Payment Entry", pa), "Submit for approval")
	attempt("S5c.certified_600k_first_500k_inside_operation", lambda: approve_in_operation(pa, approver))
	pb = payment_draft(pi_part, "SPIKE-S5c|part payment 2|1|Native payment|k-1", amount=200000, user=maker)
	with as_user(maker):
		apply_workflow(frappe.get_doc("Payment Entry", pb), "Submit for approval")
	attempt("S5c.certified_600k_next_200k_exceeds_the_supported_amount_even_though_the_invoice_allows_it", lambda: approve_in_operation(pb, approver))
	record("S5c.invoice_after_over_entitlement_attempt", **snapshot("Purchase Invoice", pi_part, ["status", "outstanding_amount", "cm_certified_amount"]), second_payment_state=snapshot("Payment Entry", pb, ["docstatus", "workflow_state"]))

	# 3. bypasses of the workflow itself, with a certified invoice (so only the controlled-operation rule stops them)
	pi_byp = fresh_invoice("byp", units=2)
	certify(pi_byp, 200000)
	pe_byp = payment_draft(pi_byp, "SPIKE-S5c|bypass|1|Native payment|k-1", user=other)

	def direct(user):
		with as_user(user):
			doc = frappe.get_doc("Payment Entry", pe_byp)
			doc.submit()
			return snapshot("Payment Entry", pe_byp, ["docstatus", "workflow_state"])
	attempt("S5c.bypass_direct_submit_by_dual_role_user", lambda: direct(other))
	attempt("S5c.bypass_direct_submit_by_administrator", lambda: direct("Administrator"))

	def savedocs_submit():
		from frappe.desk.form.save import savedocs

		with as_user(other):
			doc = frappe.get_doc("Payment Entry", pe_byp)
			savedocs(frappe.as_json(doc.as_dict()), "Submit")
			return snapshot("Payment Entry", pe_byp, ["docstatus", "workflow_state"])
	attempt("S5c.bypass_desk_savedocs_submit", savedocs_submit)
	with as_user(other):
		apply_workflow(frappe.get_doc("Payment Entry", pe_byp), "Submit for approval")

	def workflow_button():
		with as_user(approver):
			doc = apply_workflow(frappe.get_doc("Payment Entry", pe_byp), "Approve")
			return {"workflow_state": doc.workflow_state, "docstatus": doc.docstatus}
	attempt("S5c.bypass_workflow_approve_outside_the_operation_by_a_separate_approver", workflow_button)
	attempt("S5c.own_entry_approval_inside_the_operation_still_refused", lambda: approve_in_operation(pe_byp, other))
	record("S5c.bypass_target_state", **snapshot("Payment Entry", pe_byp, ["docstatus", "workflow_state"]), invoice=snapshot("Purchase Invoice", pi_byp, ["status", "outstanding_amount"]))

	# 4. a changed amount on an entry awaiting approval invalidates the approval (CM §5.12)
	pi_inv = fresh_invoice("inv", units=4)
	certify(pi_inv, 400000)
	pe_inv = payment_draft(pi_inv, "SPIKE-S5c|invalidate|1|Native payment|k-1", amount=300000, user=maker)
	with as_user(maker):
		apply_workflow(frappe.get_doc("Payment Entry", pe_inv), "Submit for approval")
	record("S5c.pending_before_edit", **snapshot("Payment Entry", pe_inv, ["workflow_state", "paid_amount"]))

	def edit_amount_while_pending():
		with as_user(other):
			doc = frappe.get_doc("Payment Entry", pe_inv)
			doc.paid_amount = doc.received_amount = 400000
			doc.references[0].allocated_amount = 400000
			doc.save()
			return {"workflow_state_after_save": doc.workflow_state, "paid_amount": doc.paid_amount, "invalidated_fields": frappe.flags.get("cm_approval_invalidated")}
	attempt("S5c.edit_amount_while_pending_returns_the_entry_to_draft", edit_amount_while_pending)
	attempt("S5c.approve_after_edit_without_resubmission_is_refused", lambda: approve_in_operation(pe_inv, approver))
	frappe.flags.cm_spike_mode = ""
	frappe.flags.cm_spike_advance_in_operation = False
	return save("s5c_enforce")


def race_approve(pe: str, start_at: float, lock: bool = True) -> None:
	"""One contender of the S5e race: wait for the common start instant, then approve inside the controlled operation."""
	import time

	frappe.flags.cm_spike_mode = "enforce"
	frappe.flags.cm_spike_no_lock = not lock
	time.sleep(max(0.0, start_at - time.time()))
	started = time.time()
	try:
		result = approve_in_operation(pe, world.USERS["approver"])
		frappe.db.commit()
		print("RACE " + json.dumps({"pe": pe, "ok": True, "result": result, "waited_s": round(time.time() - started, 2)}))
	except Exception as exc:  # noqa: BLE001
		frappe.db.rollback()
		print("RACE " + json.dumps({"pe": pe, "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:200]}", "waited_s": round(time.time() - started, 2)}))


def s5e_race() -> list[dict]:
	"""S5e — two approvers pay 500,000 each against an invoice certified for 800,000, from separate processes, at the same instant."""
	import os
	import subprocess
	import time
	from frappe.model.workflow import apply_workflow

	_ensure_world()
	ensure_workflow()
	bench = os.path.abspath(os.path.join(os.path.realpath(frappe.get_app_path("kentender_contracts")), "..", "..", "..", ".."))
	maker = world.USERS["maker"]
	for label, lock in (("without_row_lock", False), ("with_row_lock", True)):
		pi = fresh_invoice(f"race-{label}", units=8)
		certify(pi, 800000)
		pes = []
		for n in (1, 2):
			pe = payment_draft(pi, f"SPIKE-S5e|{label} {n}|1|Native payment|k-1", amount=500000, user=maker)
			with as_user(maker):
				apply_workflow(frappe.get_doc("Payment Entry", pe), "Submit for approval")
			pes.append(pe)
		frappe.db.commit()
		start_at = time.time() + 14
		procs = [subprocess.Popen(["bench", "--site", frappe.local.site, "execute", "kentender_contracts.spike.native.race_approve", "--kwargs",
			str({"pe": pe, "start_at": start_at, "lock": lock})], cwd=bench, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for pe in pes]
		outputs = [p.communicate(timeout=240)[0] for p in procs]
		contenders = [json.loads(line[5:]) for out in outputs for line in out.splitlines() if line.startswith("RACE ")]
		frappe.db.rollback()  # see the other processes' committed work
		posted = [frappe.db.get_value("Payment Entry", pe, "docstatus") for pe in pes]
		inv = frappe.db.get_value("Purchase Invoice", pi, ["outstanding_amount", "grand_total", "cm_certified_amount"], as_dict=True)
		cash = sum(flt(frappe.db.get_value("Payment Entry", pe, "paid_amount")) for pe, d in zip(pes, posted) if d == 1)
		shown = flt(inv.grand_total) - flt(inv.outstanding_amount)
		record(f"S5e.race_{label}", contenders=contenders, payments_posted=sum(1 for d in posted if d == 1), cash_posted_by_payment_entries=cash,
			settled_shown_on_the_invoice=shown, certified=flt(inv.cm_certified_amount), over_paid_in_cash=cash > flt(inv.cm_certified_amount) + 0.005,
			invoice_disagrees_with_cash=abs(cash - shown) > 0.005)
	return save("s5e_race")


def make_quality_inspection(pr: str, item: str, status: str, *, sample: int, serial: str | None = None) -> str:
	"""A native Quality Inspection for the accepted subset of one receipt row; readings carry CM's findings (manual result, no editable template)."""
	row = frappe.db.get_value("Purchase Receipt Item", {"parent": pr, "item_code": item}, ["name", "item_name"], as_dict=True)
	if not frappe.db.exists("Quality Inspection Parameter", CRITERION):
		frappe.get_doc({"doctype": "Quality Inspection Parameter", "parameter": CRITERION, "description": "Frozen contract criterion (spike)"}).insert(ignore_permissions=True)
	qi = frappe.get_doc({
		"doctype": "Quality Inspection", "inspection_type": "Incoming", "reference_type": "Purchase Receipt", "reference_name": pr, "child_row_reference": row.name,
		"item_code": item, "item_name": row.item_name, "sample_size": sample, "inspected_by": world.USERS["maker"], "report_date": today(), "manual_inspection": 1,
		"status": status, "readings": [{"specification": CRITERION, "status": status, "manual_inspection": 1, "reading_1": "14.1" if status == "Accepted" else "13.0"}],
	})
	qi.insert(ignore_permissions=True)
	qi.submit()
	return qi.name


def s2_stock_inspection() -> list[dict]:
	"""S2/S3 (stock): arrival makes no receipt; the accepted subset is inspected then received with serials; rejected units never appear."""
	_ensure_world()
	previous_serial_setting = frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item")
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)  # required configuration for serial items; restored below
	frappe.db.commit()
	record("S2.serial_batch_setting", before=previous_serial_setting, during_test=1)
	record("S2.settings_unchanged", **{k: frappe.db.get_single_value("Stock Settings", k) for k in ("action_if_quality_inspection_is_not_submitted", "action_if_quality_inspection_is_rejected")})
	po = create_purchase_order("SPIKE-S2s|agreement 1|1|Purchase order|k-1", world.ITEM_STK, 10, 100000)
	frappe.db.commit()
	record("S2.arrival_creates_no_receipt", receipts_for_order=frappe.db.count("Purchase Receipt Item", {"purchase_order": po, "docstatus": ["<", 2]}), order=snapshot("Purchase Order", po, ["per_received"]))
	accepted = [f"SPIKE-SN-{i:03d}" for i in range(1, 9)]
	pr = attempt("S2.draft_receipt_for_8_accepted_serials", lambda: make_receipt(po, "SPIKE-S2s|arrival 1|1|Accepted receipt|k-1", 8, serials=accepted, submit=False))
	if pr:
		attempt("S2.submit_receipt_without_a_submitted_inspection_is_stopped", lambda: frappe.get_doc("Purchase Receipt", pr).submit())
		bad = attempt("S2.inspection_with_a_failed_criterion", lambda: make_quality_inspection(pr, world.ITEM_STK, "Rejected", sample=8))
		if bad:
			def with_rejected():
				doc = frappe.get_doc("Purchase Receipt", pr)
				doc.items[0].quality_inspection = bad
				doc.save(ignore_permissions=True)
				doc.submit()
			attempt("S2.submit_receipt_pointing_at_a_rejected_inspection_is_stopped", with_rejected)
		good = attempt("S2.inspection_of_the_accepted_subset_all_criteria_met", lambda: make_quality_inspection(pr, world.ITEM_STK, "Accepted", sample=8))
		if good:
			def passing():
				doc = frappe.get_doc("Purchase Receipt", pr)
				doc.items[0].quality_inspection = good
				doc.save(ignore_permissions=True)
				doc.submit()
				return {"status": doc.status, "docstatus": doc.docstatus}
			attempt("S2.submit_receipt_with_the_accepted_inspection", passing)
			record("S3.stock_receipt_facts", po=snapshot("Purchase Order", po, ["status", "per_received"]), gl=gl("Purchase Receipt", pr),
				stock_ledger=[{"qty": flt(r.actual_qty), "warehouse": r.warehouse, "value": flt(r.stock_value_difference)} for r in frappe.get_all("Stock Ledger Entry", filters={"voucher_no": pr, "is_cancelled": 0}, fields=["actual_qty", "warehouse", "stock_value_difference"])],
				serial_nos=sorted(frappe.get_all("Serial No", filters={"item_code": world.ITEM_STK}, pluck="name")))
			record("S3.rejected_serials_never_exist", rejected_serials_present=[sn for sn in ("SPIKE-SN-009", "SPIKE-SN-010") if frappe.db.exists("Serial No", sn)])
	pr2 = attempt("S2.replacement_2_units_with_their_own_serials", lambda: make_receipt(po, "SPIKE-S2s|arrival 2|1|Accepted receipt|k-1", 2, serials=["SPIKE-SN-011", "SPIKE-SN-012"], submit=False))
	if pr2:
		qi2 = make_quality_inspection(pr2, world.ITEM_STK, "Accepted", sample=2)
		def second():
			doc = frappe.get_doc("Purchase Receipt", pr2)
			doc.items[0].quality_inspection = qi2
			doc.save(ignore_permissions=True)
			doc.submit()
			return {"po_per_received": frappe.db.get_value("Purchase Order", po, "per_received")}
		attempt("S2.replacement_receipt_posts_and_completes_the_order", second)

	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", previous_serial_setting)
	frappe.db.commit()
	return save("s2_stock_inspection")


def s3_missing_serial() -> list[dict]:
	"""S3b — a receipt row for a serial item with no serial supplied: does ERPNext invent one (CM §5.4 forbids a fabricated serial)?"""
	_ensure_world()
	previous = frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item")
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
	frappe.db.commit()
	before = set(frappe.get_all("Serial No", filters={"item_code": world.ITEM_STK}, pluck="name"))

	def go():
		po2 = create_purchase_order("SPIKE-S3b|agreement 2|1|Purchase order|k-1", world.ITEM_STK, 1, 100000)
		frappe.db.commit()
		pr3 = make_receipt(po2, "SPIKE-S3b|arrival 3|1|Accepted receipt|k-1", 1, submit=False)
		qi3 = make_quality_inspection(pr3, world.ITEM_STK, "Accepted", sample=1)
		doc = frappe.get_doc("Purchase Receipt", pr3)
		doc.items[0].quality_inspection = qi3
		doc.save(ignore_permissions=True)
		doc.submit()
		after = set(frappe.get_all("Serial No", filters={"item_code": world.ITEM_STK}, pluck="name"))
		return {"submitted": True, "serials_created_without_being_supplied": sorted(after - before), "row_serial_no_field": frappe.db.get_value("Purchase Receipt Item", {"parent": pr3}, "serial_no")}
	attempt("S3b.receipt_row_without_a_serial", go)
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", previous)
	frappe.db.commit()
	return save("s3b_missing_serial")


def s5d_beneficiary_change() -> list[dict]:
	"""S5d — a changed beneficiary bank account on an entry awaiting approval sends it back to Draft (CM §5.12)."""
	from frappe.model.workflow import apply_workflow

	_ensure_world()
	ensure_workflow()
	maker, other = world.USERS["maker"], world.USERS["other"]
	if not frappe.db.exists("Bank", "CM Spike Bank Ltd"):
		frappe.get_doc({"doctype": "Bank", "bank_name": "CM Spike Bank Ltd"}).insert(ignore_permissions=True)
	accounts = []
	for n in (1, 2):
		name = f"CM Spike Supplier Account {n} - CM Spike Bank Ltd"
		if not frappe.db.exists("Bank Account", name):
			frappe.get_doc({"doctype": "Bank Account", "account_name": f"CM Spike Supplier Account {n}", "bank": "CM Spike Bank Ltd", "party_type": "Supplier", "party": world.SUPPLIER,
				"bank_account_no": f"000{n}1234"}).insert(ignore_permissions=True)
		accounts.append(name)
	frappe.flags.cm_spike_mode = "enforce"
	pi = fresh_invoice("beneficiary", units=2)
	certify(pi, 200000)
	pe = payment_draft(pi, "SPIKE-S5d|beneficiary|1|Native payment|k-1", user=maker)
	frappe.db.set_value("Payment Entry", pe, "party_bank_account", accounts[0])
	frappe.db.commit()
	with as_user(maker):
		apply_workflow(frappe.get_doc("Payment Entry", pe), "Submit for approval")
	record("S5d.pending_with_beneficiary_1", **snapshot("Payment Entry", pe, ["workflow_state", "party_bank_account"]))

	def swap():
		with as_user(other):
			doc = frappe.get_doc("Payment Entry", pe)
			doc.party_bank_account = accounts[1]
			doc.save()
			return {"workflow_state_after_save": doc.workflow_state, "party_bank_account": doc.party_bank_account, "invalidated_fields": frappe.flags.get("cm_approval_invalidated")}
	attempt("S5d.beneficiary_swapped_while_pending_returns_the_entry_to_draft", swap)
	attempt("S5d.approve_without_resubmission_is_refused", lambda: approve_in_operation(pe, world.USERS["approver"]))
	frappe.flags.cm_spike_mode = ""
	for name in accounts:
		frappe.delete_doc("Bank Account", name, force=True, ignore_permissions=True) if False else None
	return save("s5d_beneficiary_change")


def _job_submits_payment(pe: str) -> str:
	"""The body of a background job: what a queued task does when it submits a payment."""
	doc = frappe.get_doc("Payment Entry", pe)
	doc.submit()
	return doc.name


def s5f_background_and_import_routes() -> list[dict]:
	"""S5f — a background job (run inline with the same code path an RQ worker uses) cannot post a contract payment outside the operation."""
	_ensure_world()
	ensure_workflow()
	frappe.flags.cm_spike_mode = "enforce"
	pi = fresh_invoice("job", units=1)
	certify(pi, 100000)
	pe = payment_draft(pi, "SPIKE-S5f|job|1|Native payment|k-1", user=world.USERS["other"])
	frappe.db.commit()
	attempt("S5f.background_job_submitting_a_payment_outside_the_operation", lambda: frappe.enqueue("kentender_contracts.spike.native._job_submits_payment", pe=pe, now=True))
	record("S5f.state_after_job", payment=snapshot("Payment Entry", pe, ["docstatus", "workflow_state"]), invoice=snapshot("Purchase Invoice", pi, ["status", "outstanding_amount"]))
	frappe.flags.cm_spike_mode = ""
	return save("s5f_background_route")
