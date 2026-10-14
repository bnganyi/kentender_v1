# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Functions the native tests run in **separate processes** (`bench execute`): a hard crash and a concurrent race cannot be shown in-process.
Not product code."""

from __future__ import annotations

import json
import os
import time

import frappe
from frappe.utils import add_days, today

from kentender_contracts.native import adapter
from kentender_contracts.services import intents
from kentender_contracts.tests import native_world as world


def crash_after_native_commit(intent: str, identity: str) -> None:
	"""Carry the intent through `intents.execute`, create and commit the native order, then die before the link is written."""

	def executor(ident):
		po = adapter.create_purchase_order(ident, company=world.COMPANY, supplier=world.SUPPLIER, currency=world.CURRENCY, schedule_date=add_days(today(), 30),
			items=[{"item_code": world.ITEM_FA, "qty": 10, "rate": 100000}])
		frappe.db.commit()
		print(f"CRASH native order {po} committed; dying before the link is written", flush=True)
		os._exit(137)

	intents.execute(intent, executor, lambda ident: adapter.find_by_identity("Purchase Order", ident), native_doctype="Purchase Order")


def race_approve(pe: str, start_at: float) -> None:
	"""One contender of a race: wait for the common start instant, then approve inside the controlled operation."""
	time.sleep(max(0.0, start_at - time.time()))
	started = time.time()
	try:
		result = adapter.approve_payment(pe, f"CM_TEST|race {pe}|1|Native payment|k-1", world.USERS["approver"])
		frappe.db.commit()
		print("RACE " + json.dumps({"pe": pe, "ok": True, "result": result, "waited_s": round(time.time() - started, 2)}))
	except Exception as exc:  # noqa: BLE001
		frappe.db.rollback()
		print("RACE " + json.dumps({"pe": pe, "ok": False, "error": f"{type(exc).__name__}: {str(exc)[:200]}", "waited_s": round(time.time() - started, 2)}))


def job_submits_payment(pe: str) -> str:
	"""The body of a background job: what a queued task does when it submits a payment."""
	doc = frappe.get_doc("Payment Entry", pe)
	doc.submit()
	return doc.name
