# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The ERPNext world the native (L2) tests need on the test site, built once per module and removed at its end (plan D18).

Everything is named so `teardown()` can remove it; nothing here runs on the dev site. It derives from the Phase 2 spike world
(S0) with its own names. The Payment Entry workflow is Finance configuration in a live site (readiness names it when missing);
here `ensure_workflow()` stands in for it and `drop_workflow()` removes it so other modules' payment tests are not affected."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, today

from kentender_contracts.native import adapter, fields
from kentender_core.services.command_write_guard import purge_doc

COMPANY = "KenTender"
ABBR = "K"
CURRENCY = "KES"
SUPPLIER = "CM Test Supplier"
OTHER_SUPPLIER = "CM Test Ordinary Supplier"  # no contract invoice: the guards must leave it alone
ITEM_FA = "CM-TEST-LAPTOP-FA"  # serialised fixed asset
ITEM_STK = "CM-TEST-LAPTOP-STK"  # serialised stock item, inspection required
ITEM_SERVICE = "CM-TEST-SERVICE"  # plain non-stock item for an ordinary invoice
ITEM_PLAIN = "CM-TEST-STOCK"  # a plain stock item (no serials, no inspection): the stock ledger reconciles to what was accepted
CATEGORY = "CM Test Electronic Equipment"
WAREHOUSE = f"Stores - {ABBR}"
LOCATION = "CM Test Store Room"
BANK_ACCOUNT = f"CM Test Bank - {ABBR}"
MODE = "Wire Transfer"
WORKFLOW = "CM Test Payment Approval"
CRITERION = "CM-TEST criterion 1 screen size at least 14 inch"
USERS = {"maker": "cm.test.maker@test.example.test", "approver": "cm.test.approver@test.example.test", "other": "cm.test.other@test.example.test"}
ROLES = {
	"maker": ["Accounts User", "Purchase User", "Stock User", "Item Manager"],
	"approver": ["Accounts Manager", "Purchase Manager", "Stock Manager"],
	"other": ["Accounts Manager", "Accounts User"],
}
IDENTITY = "CM_TEST|{subject}|1|{kind}|{key}"


def identity(subject: str, kind: str, key: str = "k-1") -> str:
	return IDENTITY.format(subject=subject, kind=kind, key=key)


def _account(name: str, parent_like: str, account_type: str, root_type: str = "Asset") -> str:
	full = f"{name} - {ABBR}"
	if frappe.db.exists("Account", full):
		return full
	parent = frappe.db.get_value("Account", {"company": COMPANY, "is_group": 1, "account_name": parent_like}, "name")
	if not parent:
		raise RuntimeError(f"no parent account {parent_like!r} in {COMPANY}")
	frappe.get_doc({"doctype": "Account", "account_name": name, "parent_account": parent, "company": COMPANY, "account_type": account_type, "root_type": root_type, "is_group": 0}).insert(ignore_permissions=True)
	return full


def _user(key: str) -> str:
	email = USERS[key]
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": f"CM Test {key.title()}", "enabled": 1, "send_welcome_email": 0, "user_type": "System User",
			"roles": [{"role": r} for r in ROLES[key]]}).insert(ignore_permissions=True)
	return email


def build() -> None:
	fields.ensure()
	_account("CM Test Bank", "Bank Accounts", "Bank")
	if not frappe.db.exists("Mode of Payment Account", {"parent": MODE, "company": COMPANY}):
		mop = frappe.get_doc("Mode of Payment", MODE)
		mop.append("accounts", {"company": COMPANY, "default_account": BANK_ACCOUNT})
		mop.save(ignore_permissions=True)
	for supplier in (SUPPLIER, OTHER_SUPPLIER):
		if not frappe.db.exists("Supplier", supplier):
			frappe.get_doc({"doctype": "Supplier", "supplier_name": supplier, "supplier_group": "Hardware", "supplier_type": "Company", "default_currency": CURRENCY}).insert(ignore_permissions=True)
	if not frappe.db.exists("Location", LOCATION):
		frappe.get_doc({"doctype": "Location", "location_name": LOCATION}).insert(ignore_permissions=True)
	if not frappe.db.exists("Asset Category", CATEGORY):
		frappe.get_doc({"doctype": "Asset Category", "asset_category_name": CATEGORY, "enable_cwip_accounting": 0,
			"finance_books": [{"depreciation_method": "Straight Line", "total_number_of_depreciations": 36, "frequency_of_depreciation": 1}],
			"accounts": [{"company_name": COMPANY, "fixed_asset_account": f"1720 - Electronic Equipment - {ABBR}",
				"accumulated_depreciation_account": f"1780 - Accumulated Depreciation - {ABBR}", "depreciation_expense_account": f"5203 - Depreciation - {ABBR}",
				"capital_work_in_progress_account": f"1790 - CWIP Account - {ABBR}"}]}).insert(ignore_permissions=True)
	common = {"doctype": "Item", "item_group": "Products", "stock_uom": "Nos", "is_purchase_item": 1, "is_sales_item": 0, "valuation_rate": 100000, "standard_rate": 100000}
	if not frappe.db.exists("Item", ITEM_FA):
		frappe.get_doc({**common, "item_code": ITEM_FA, "item_name": "CM Test Laptop (fixed asset)", "is_stock_item": 0, "is_fixed_asset": 1, "asset_category": CATEGORY,
			"auto_create_assets": 1, "asset_naming_series": "ACC-ASS-.YYYY.-"}).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", ITEM_STK):
		frappe.get_doc({**common, "item_code": ITEM_STK, "item_name": "CM Test Laptop (stock)", "is_stock_item": 1, "has_serial_no": 1, "serial_no_series": "CMTST-.#####",
			"inspection_required_before_purchase": 1}).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", ITEM_PLAIN):
		frappe.get_doc({**common, "item_code": ITEM_PLAIN, "item_name": "CM Test Laptop (plain stock)", "is_stock_item": 1}).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", ITEM_SERVICE):
		frappe.get_doc({**common, "item_code": ITEM_SERVICE, "item_name": "CM Test Service", "is_stock_item": 0}).insert(ignore_permissions=True)
	for key in USERS:
		_user(key)
	frappe.db.commit()


# -- documents the tests need -------------------------------------------------------------------------------------------------------
def order(key: str, item: str, qty: int, rate: float = 100000, *, supplier: str = SUPPLIER) -> str:
	name = adapter.create_purchase_order(identity("order " + key, "Purchase order"), company=COMPANY, supplier=supplier, currency=CURRENCY, schedule_date=add_days(today(), 30),
		items=[{"item_code": item, "qty": qty, "rate": rate, "warehouse": WAREHOUSE if frappe.db.get_value("Item", item, "is_stock_item") else None}])
	return name


def fixed_asset_receipt(key: str, units: int, *, references: list[str] | None = None) -> str:
	po = order(key, ITEM_FA, units)
	refs = references if references is not None else [f"CM-TEST-{key}-{n:02d}" for n in range(1, units + 1)]
	return adapter.receive(po, identity("receipt " + key, "Accepted receipt"), lines=[{"item_code": ITEM_FA, "qty": units, "unit_references": refs, "asset_location": LOCATION}])


def fresh_invoice(key: str, units: int = 1) -> str:
	"""A posted contract Purchase Invoice of `units` x KES 100,000 (order, receipt, invoice), once per key."""
	pr = fixed_asset_receipt(key, units)
	pi = adapter.invoice_receipt(pr, identity("invoice " + key, "Native invoice"), bill_no=f"INV-{key}")
	frappe.db.commit()
	return pi


def credit_note(pi: str, units: int, key: str) -> str:
	"""Finance's native credit (debit) note against a posted invoice, for `units` at the invoice's rate: the document Finance makes in ERPNext Accounts when a liability must come down."""
	from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import make_debit_note

	note = make_debit_note(pi)
	note.cm_operation_identity = identity("credit " + key, "Native invoice")
	note.bill_no = f"CN-{key}"
	note.items[0].qty = -units
	note.insert(ignore_permissions=True)
	note.submit()
	frappe.db.commit()
	return note.name


def draft_payment(pi: str, key: str, *, amount: float | None = None, user: str | None = None, supplier_account: str | None = None) -> str:
	def build_entry():
		name = adapter.payment_draft(pi, identity("payment " + key, "Native payment"), amount=amount, mode_of_payment=MODE, paid_from=BANK_ACCOUNT, reference_no=f"BANK-{key}")
		if supplier_account:
			frappe.db.set_value("Payment Entry", name, "party_bank_account", supplier_account)
		return name

	if user:
		with as_user(user):
			return build_entry()
	return build_entry()


class as_user:
	def __init__(self, email: str):
		self.email = email

	def __enter__(self):
		self.previous = frappe.session.user
		frappe.set_user(self.email)

	def __exit__(self, *exc):
		frappe.set_user(self.previous)


# -- the Finance workflow stand-in --------------------------------------------------------------------------------------------------
def ensure_workflow() -> None:
	for state in ("Draft", "Pending Approval", "Approved"):
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)
	for action in ("Submit for approval", "Approve", "Return"):
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(ignore_permissions=True)
	if not frappe.db.exists("Workflow", WORKFLOW):
		frappe.get_doc({
			"doctype": "Workflow", "workflow_name": WORKFLOW, "document_type": "Payment Entry", "is_active": 1, "workflow_state_field": "workflow_state", "send_email_alert": 0,
			"states": [{"state": "Draft", "doc_status": "0", "allow_edit": "Accounts User"}, {"state": "Pending Approval", "doc_status": "0", "allow_edit": "Accounts Manager"},
				{"state": "Approved", "doc_status": "1", "allow_edit": "Accounts Manager"}],
			"transitions": [
				{"state": "Draft", "action": "Submit for approval", "next_state": "Pending Approval", "allowed": "Accounts User", "allow_self_approval": 1},
				{"state": "Pending Approval", "action": "Approve", "next_state": "Approved", "allowed": "Accounts Manager", "allow_self_approval": 0},
				{"state": "Pending Approval", "action": "Return", "next_state": "Draft", "allowed": "Accounts Manager", "allow_self_approval": 0},
			],
		}).insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()


def drop_workflow() -> None:
	if frappe.db.exists("Workflow", WORKFLOW):
		frappe.delete_doc("Workflow", WORKFLOW, force=True, ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_cache()


def submit_for_approval(pe: str, user: str) -> None:
	from frappe.model.workflow import apply_workflow

	with as_user(user):
		apply_workflow(frappe.get_doc("Payment Entry", pe), "Submit for approval")


# -- teardown ---------------------------------------------------------------------------------------------------------------------
def teardown() -> dict:
	"""Cancel and delete every document the tests made, newest first, then the world. Returns what could not be removed."""
	failed: dict[str, str] = {}
	items = [ITEM_FA, ITEM_STK, ITEM_SERVICE, ITEM_PLAIN]
	suppliers = [SUPPLIER, OTHER_SUPPLIER]

	def drop(doctype: str, names: list[str]) -> None:
		for name in names:
			try:
				doc = frappe.get_doc(doctype, name)
				if getattr(doc, "docstatus", 0) == 1:
					doc.cancel()
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			except Exception as exc:  # noqa: BLE001 - report, keep going
				failed[f"{doctype} {name}"] = str(exc)[:160]

	drop_workflow()
	for doctype in ("Contract Operation Intent", "Contract Transaction Link", "Contract Command Journal", "Contract Case"):
		for name in frappe.get_all(doctype, filters={"fixture_namespace": "CM_TEST"}, pluck="name"):
			purge_doc(doctype, name)
	for supplier in suppliers:
		drop("Payment Entry", frappe.get_all("Payment Entry", filters={"party": supplier}, pluck="name", order_by="creation desc"))
	drop("Journal Entry", frappe.get_all("Journal Entry", filters={"user_remark": ["like", "CM TEST%"]}, pluck="name", order_by="creation desc"))
	for supplier in suppliers:
		drop("Purchase Invoice", frappe.get_all("Purchase Invoice", filters={"supplier": supplier}, pluck="name", order_by="creation desc"))
	for asset in frappe.get_all("Asset", filters={"item_code": ["in", items], "docstatus": 1}, pluck="name"):
		try:
			frappe.get_doc("Asset", asset).cancel()
		except Exception as exc:  # noqa: BLE001
			failed[f"Asset {asset}"] = str(exc)[:160]
	receipts = frappe.get_all("Purchase Receipt", filters={"supplier": ["in", suppliers]}, fields=["name", "is_return"], order_by="creation desc")
	for receipt in sorted(receipts, key=lambda r: not r.is_return):  # returns first, each group newest first
		frappe.db.set_value("Purchase Receipt Item", {"parent": receipt.name}, "quality_inspection", None)
		for qi in frappe.get_all("Quality Inspection", filters={"reference_name": receipt.name, "docstatus": 1}, pluck="name"):
			frappe.get_doc("Quality Inspection", qi).cancel()
		drop("Purchase Receipt", [receipt.name])
	for supplier in suppliers:
		drop("Purchase Order", frappe.get_all("Purchase Order", filters={"supplier": supplier}, pluck="name", order_by="creation desc"))
	drop("Quality Inspection", frappe.get_all("Quality Inspection", filters={"item_code": ["in", items]}, pluck="name"))
	if frappe.db.exists("Quality Inspection Parameter", CRITERION):
		frappe.delete_doc("Quality Inspection Parameter", CRITERION, force=True, ignore_permissions=True)
	for asset in frappe.get_all("Asset", filters={"item_code": ["in", items]}, pluck="name"):
		for movement in frappe.get_all("Asset Movement Item", filters={"asset": asset}, pluck="parent"):
			drop("Asset Movement", [movement])
	drop("Asset", frappe.get_all("Asset", filters={"item_code": ["in", items]}, pluck="name"))
	for serial in frappe.get_all("Serial No", filters={"item_code": ["in", items]}, pluck="name"):
		frappe.delete_doc("Serial No", serial, force=True, ignore_permissions=True)
	for doctype, name in [("Item", ITEM_FA), ("Item", ITEM_STK), ("Item", ITEM_SERVICE), ("Item", ITEM_PLAIN), ("Asset Category", CATEGORY), ("Supplier", SUPPLIER), ("Supplier", OTHER_SUPPLIER), ("Location", LOCATION)]:
		if frappe.db.exists(doctype, name):
			try:
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
			except Exception as exc:  # noqa: BLE001
				failed[f"{doctype} {name}"] = str(exc)[:160]
	if frappe.db.exists("Mode of Payment Account", {"parent": MODE, "company": COMPANY, "default_account": BANK_ACCOUNT}):
		mop = frappe.get_doc("Mode of Payment", MODE)
		mop.accounts = [row for row in mop.accounts if not (row.company == COMPANY and row.default_account == BANK_ACCOUNT)]
		mop.save(ignore_permissions=True)
	for bank_account in frappe.get_all("Bank Account", filters={"bank": "CM Test Bank Ltd"}, pluck="name"):
		frappe.delete_doc("Bank Account", bank_account, force=True, ignore_permissions=True)
	if frappe.db.exists("Bank", "CM Test Bank Ltd"):
		frappe.delete_doc("Bank", "CM Test Bank Ltd", force=True, ignore_permissions=True)
	for email in USERS.values():
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	frappe.db.commit()
	return failed
