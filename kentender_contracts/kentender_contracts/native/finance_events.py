# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ERPNext tells Contract Management what Finance did natively (CM-CHG-001 v0.8 section 7 `ReceiveFinanceResult`).

A credit note posted against an invoice of a contract is a Finance fact, made in ERPNext Accounts; Contract Management reads it and lifts the hold that waited for it. It writes no ledger row and never
blocks or fails the native submission: a problem reading the result is logged and Finance's document is left alone."""

from __future__ import annotations

import frappe


def on_purchase_invoice_submit(doc, method: str | None = None) -> None:
	if not doc.get("is_return") or not doc.get("return_against"):
		return
	try:
		row = frappe.db.get_value("Contract Invoice", {"native_invoice": doc.return_against}, ["contract_case"], as_dict=True)
		if row:
			from kentender_contracts.services import payment

			payment.receive_finance_result(row.contract_case, native_invoice=doc.return_against)
	except Exception:  # noqa: BLE001 - never block the native submission
		frappe.log_error(title="Contract Management could not read a native credit")


def on_payment_entry_cancel(doc, method: str | None = None) -> None:
	"""A payment entry of a contract's invoice was cancelled natively: the settlement it confirmed is reversed in the projection."""
	try:
		if frappe.db.exists("Contract Settlement", {"native_payment": doc.name, "state": "Confirmed"}):
			from kentender_contracts.services import payment

			payment.receive_payment_cancelled(doc.name)
	except Exception:  # noqa: BLE001 - never block the native cancellation
		frappe.log_error(title="Contract Management could not read a cancelled payment")
