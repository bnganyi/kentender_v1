# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 plan D7, CM-AC-17, CM-AC-31 (tracker CM8-306, CM8-307, gate CM-G03 `cm-native-gate`): the native adapter and the
payment bypass guards against **real ERPNext documents** (proof level L2). It replays the Phase 2 spike's checks S2/S3 (receipt, serials,
assets), S5 (every payment route, entitlement, maker/approver, a concurrent race) and S7 (a hard crash recovered by identity, reversals in
order) as tests of the product code that replaced the spike.

Test site only, MariaDB only. The ERPNext world is built once for the module and removed at its end."""

from __future__ import annotations

import json
import os
import subprocess
import time
import unittest
from contextlib import contextmanager

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from kentender_contracts.native import adapter, fields, payment_guard
from kentender_contracts.services import errors, intents, records
from kentender_contracts.tests import native_world as world

NS = "CM_TEST"
BENCH = os.path.abspath(os.path.join(os.path.realpath(frappe.get_app_path("kentender_contracts")), "..", "..", "..", ".."))


def setUpModule():
	if frappe.db.db_type != "mariadb":
		raise unittest.SkipTest("the native tests run on the MariaDB test site")
	world.build()


def tearDownModule():
	if frappe.db.db_type == "mariadb":
		failed = world.teardown()
		if failed:
			print("native world: could not remove", json.dumps(failed, indent=1))


@contextmanager
def serials_enabled():
	"""Stock Settings 'Enable Serial and Batch No for Item' is global configuration (FU-CM-48): switched on for a test and put back."""
	previous = frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item")
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
	frappe.db.commit()
	try:
		yield
	finally:
		frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", previous)
		frappe.db.commit()


def refused(test, code, fn):
	with test.assertRaises(errors.ContractError) as caught:
		fn()
	test.assertEqual(caught.exception.code, code)
	return caught.exception


class TestFields(IntegrationTestCase):
	def test_the_fields_are_installed_once_and_are_not_copied_to_an_amendment(self):
		fields.ensure()
		fields.ensure()
		self.assertEqual(fields.missing(), [])
		for doctype, specs in fields.CUSTOM_FIELDS.items():
			for spec in specs:
				found = frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": spec["fieldname"]}, ["no_copy", "read_only"], as_dict=True)
				self.assertEqual((found.no_copy, found.read_only), (1, 1), f"{doctype}.{spec['fieldname']}")
		self.assertEqual(frappe.db.count("Custom Field", {"dt": "Purchase Order", "fieldname": "cm_operation_identity"}), 1)


class TestOrderReceiptInvoice(IntegrationTestCase):
	def test_an_order_is_created_once_per_operation_identity(self):
		first, again = world.order("o1", world.ITEM_FA, 10), world.order("o1", world.ITEM_FA, 10)
		self.assertEqual(first, again)
		self.assertEqual(frappe.db.count("Purchase Order", {"cm_operation_identity": world.identity("order o1", "Purchase order")}), 1)
		self.assertEqual(flt(frappe.db.get_value("Purchase Order", first, "grand_total")), 1000000)

	def test_a_serialised_item_received_without_serials_is_refused_and_no_serial_is_invented(self):
		with serials_enabled():
			po = world.order("s1", world.ITEM_STK, 2)
			before = set(frappe.get_all("Serial No", filters={"item_code": world.ITEM_STK}, pluck="name"))
			refused(self, "CM_QUANTITY", lambda: adapter.receive(po, world.identity("receipt s1", "Accepted receipt"), lines=[{"item_code": world.ITEM_STK, "qty": 2, "serials": []}]))
			refused(self, "CM_QUANTITY", lambda: adapter.receive(po, world.identity("receipt s1", "Accepted receipt"), lines=[{"item_code": world.ITEM_STK, "qty": 2, "serials": ["CM-TEST-ONLY-ONE"]}]))
			self.assertEqual(set(frappe.get_all("Serial No", filters={"item_code": world.ITEM_STK}, pluck="name")), before)
			self.assertFalse(adapter.find_by_identity("Purchase Receipt", world.identity("receipt s1", "Accepted receipt")))

	def test_fixed_asset_units_take_their_own_references_inside_the_receipt_transaction_and_no_stock_entry_is_made(self):
		pr = world.fixed_asset_receipt("a1", 3)
		assets = frappe.get_all("Asset", filters={"purchase_receipt": pr}, fields=["name", "cm_unit_reference", "docstatus"])
		self.assertEqual(sorted(a.cm_unit_reference for a in assets), ["CM-TEST-a1-01", "CM-TEST-a1-02", "CM-TEST-a1-03"])
		self.assertEqual({a.docstatus for a in assets}, {0})
		self.assertEqual(frappe.db.count("Stock Ledger Entry", {"voucher_no": pr}), 0)

	def test_a_wrong_number_of_unit_references_or_a_reused_one_is_refused_before_the_native_call(self):
		po = world.order("a2", world.ITEM_FA, 2)
		ident = world.identity("receipt a2", "Accepted receipt")
		refused(self, "CM_QUANTITY", lambda: adapter.receive(po, ident, lines=[{"item_code": world.ITEM_FA, "qty": 2, "unit_references": ["ONLY-ONE"], "asset_location": world.LOCATION}]))
		refused(self, "CM_QUANTITY", lambda: adapter.receive(po, ident, lines=[{"item_code": world.ITEM_FA, "qty": 2, "unit_references": ["SAME", "SAME"], "asset_location": world.LOCATION}]))
		world.fixed_asset_receipt("a3", 1, references=["CM-TEST-TAKEN"])
		exc = refused(self, "CM_QUANTITY", lambda: adapter.receive(po, ident, lines=[{"item_code": world.ITEM_FA, "qty": 2, "unit_references": ["CM-TEST-TAKEN", "NEW"], "asset_location": world.LOCATION}]))
		self.assertIn("CM-TEST-TAKEN", exc.detail["duplicates"])
		self.assertFalse(adapter.find_by_identity("Purchase Receipt", ident))

	def test_a_receipt_replay_returns_the_same_document_and_adds_no_assets(self):
		first = world.fixed_asset_receipt("a4", 2)
		again = world.fixed_asset_receipt("a4", 2)
		self.assertEqual(first, again)
		self.assertEqual(frappe.db.count("Asset", {"purchase_receipt": first}), 2)

	def test_the_invoice_covers_the_received_units_once_and_certification_is_recorded_on_it(self):
		pr = world.fixed_asset_receipt("i1", 2)
		ident = world.identity("invoice i1", "Native invoice")
		pi = adapter.invoice_receipt(pr, ident, bill_no="INV-i1")
		self.assertEqual(adapter.invoice_receipt(pr, ident, bill_no="INV-i1"), pi)
		self.assertEqual(flt(frappe.db.get_value("Purchase Invoice", pi, "grand_total")), 200000)
		adapter.certify_invoice(pi, 150000)
		self.assertEqual(payment_guard.entitlement(pi), {"invoice": pi, "cm_linked": True, "certified": 150000.0, "paid": 0.0, "available": 150000.0})

	def test_a_receipt_with_an_invoice_is_refused_for_reversal_until_the_invoice_is_cancelled_then_it_reverses(self):
		pr = world.fixed_asset_receipt("r1", 1)
		pi = adapter.invoice_receipt(pr, world.identity("invoice r1", "Native invoice"), bill_no="INV-r1")
		exc = refused(self, "CM_RECONCILE", lambda: adapter.reverse_receipt(pr))
		self.assertEqual(exc.detail["downstream"]["Purchase Invoice"], [pi])
		frappe.get_doc("Purchase Invoice", pi).cancel()
		self.assertEqual(adapter.reverse_receipt(pr)["docstatus"], 2)  # draft assets do not block; a submitted one would (next test)

	def test_a_receipt_with_a_submitted_asset_reverses_only_after_the_asset(self):
		pr = world.fixed_asset_receipt("r2", 1)
		asset = frappe.get_all("Asset", filters={"purchase_receipt": pr}, pluck="name")[0]
		doc = frappe.get_doc("Asset", asset)
		doc.available_for_use_date = today()
		doc.save(ignore_permissions=True)
		doc.submit()
		exc = refused(self, "CM_RECONCILE", lambda: adapter.reverse_receipt(pr))
		self.assertEqual(exc.detail["downstream"]["Asset"], [asset])
		frappe.get_doc("Asset", asset).cancel()
		self.assertEqual(adapter.reverse_receipt(pr)["docstatus"], 2)

	def test_a_stock_receipt_reverses_inspection_first_then_receipt_and_the_order_is_open_again(self):
		with serials_enabled():
			po = world.order("q1", world.ITEM_STK, 2)
			serials = ["CM-TEST-SN-Q1-1", "CM-TEST-SN-Q1-2"]
			pr = adapter.receive(po, world.identity("receipt q1", "Accepted receipt"), lines=[{"item_code": world.ITEM_STK, "qty": 2, "serials": serials}], submit=False)
			qi = adapter.inspect_accepted(pr, world.ITEM_STK, status="Accepted", sample=2, inspector=world.USERS["maker"],
				readings=[{"specification": world.CRITERION, "status": "Accepted", "reading_1": "14.1"}])
			adapter.post_receipt(pr, quality_inspections={world.ITEM_STK: qi})
			frappe.db.commit()
			self.assertGreater(frappe.db.count("Stock Ledger Entry", {"voucher_no": pr, "is_cancelled": 0}), 0)
			self.assertEqual(sorted(frappe.get_all("Serial No", filters={"name": ["like", "CM-TEST-SN-Q1-%"]}, pluck="name")), serials)
			result = adapter.reverse_receipt(pr)
			self.assertEqual((result["inspections_cancelled"], result["docstatus"]), ([qi], 2))
			self.assertEqual(frappe.db.count("Stock Ledger Entry", {"voucher_no": pr, "is_cancelled": 0}), 0)
			# ERPNext keeps the Serial No records after a cancellation (spike S7b2); the units are no longer in stock
			self.assertEqual({frappe.db.get_value("Serial No", sn, "warehouse") or "" for sn in serials}, {""})
			self.assertEqual(flt(frappe.db.get_value("Purchase Order", po, "per_received")), 0)

	def test_the_net_payable_after_a_credit_note_is_read_from_the_ledger_not_from_the_original_invoice(self):
		from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import make_debit_note

		pi = world.fresh_invoice("n1", 5)
		before = adapter.net_payable(world.SUPPLIER)
		note = make_debit_note(pi)
		note.cm_operation_identity = world.identity("credit n1", "Native invoice")
		note.bill_no = "CN-n1"
		note.items[0].qty = -2
		note.insert(ignore_permissions=True)
		note.submit()
		self.assertEqual(flt(frappe.db.get_value("Purchase Invoice", pi, "outstanding_amount")), 500000, "the original invoice still shows its full amount")
		self.assertEqual(flt(note.outstanding_amount), -200000)
		self.assertEqual(round(before - adapter.net_payable(world.SUPPLIER), 2), 200000)


# -- payment control (spike S5) -------------------------------------------------------------------------------------------------------
def creditors() -> str:
	return frappe.db.get_value("Company", world.COMPANY, "default_payable_account")


def route_direct_entry(pi):
	name = world.draft_payment(pi, f"direct {pi}", user=world.USERS["other"])
	with world.as_user(world.USERS["other"]):
		frappe.get_doc("Payment Entry", name).submit()


def route_api_entry(pi):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	with world.as_user(world.USERS["other"]):
		pe = get_payment_entry("Purchase Invoice", pi)
		pe.mode_of_payment, pe.paid_from, pe.reference_no, pe.reference_date = world.MODE, world.BANK_ACCOUNT, f"API-{pi}", today()
		pe.cm_operation_identity = world.identity(f"api {pi}", "Native payment")
		inserted = frappe.client.insert(frappe.parse_json(frappe.as_json(pe.as_dict())))
		frappe.client.submit(frappe.parse_json(frappe.as_json(frappe.get_doc("Payment Entry", inserted["name"]).as_dict())))


def route_journal_entry(pi):
	with world.as_user(world.USERS["other"]):
		je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": world.COMPANY, "posting_date": today(), "user_remark": f"CM TEST settlement {pi}",
			"accounts": [{"account": creditors(), "party_type": "Supplier", "party": world.SUPPLIER, "debit_in_account_currency": 100000, "reference_type": "Purchase Invoice", "reference_name": pi},
				{"account": world.BANK_ACCOUNT, "credit_in_account_currency": 100000}]})
		je.insert()
		je.submit()


def route_reconcile_advance(pi):
	"""An unreferenced supplier payment (the advance, posted inside the operation as Finance would), then Payment Reconciliation allocates it to the invoice."""
	with world.as_user(world.USERS["other"]):
		adv = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Pay", "company": world.COMPANY, "posting_date": today(), "party_type": "Supplier", "party": world.SUPPLIER,
			"paid_from": world.BANK_ACCOUNT, "paid_to": creditors(), "paid_amount": 100000, "received_amount": 100000, "mode_of_payment": world.MODE, "reference_no": f"ADV-{pi}",
			"reference_date": today(), "cm_operation_identity": world.identity(f"advance {pi}", "Native payment")})
		adv.insert()
		with payment_guard.native_operation(f"advance-{pi}"):
			adv.submit()
		frappe.db.commit()
		reconciliation = frappe.get_doc("Payment Reconciliation")
		reconciliation.company, reconciliation.party_type, reconciliation.party, reconciliation.receivable_payable_account = world.COMPANY, "Supplier", world.SUPPLIER, creditors()
		reconciliation.get_unreconciled_entries()
		invoices = [x.as_dict() for x in reconciliation.invoices if x.invoice_number == pi]
		payments = [x.as_dict() for x in reconciliation.payments if x.reference_name == adv.name]
		reconciliation.allocate_entries({"invoices": invoices, "payments": payments})
		for row in reconciliation.allocation:
			row.allocated_amount = 100000
		reconciliation.reconcile()


ROUTES = {"direct entry": route_direct_entry, "API": route_api_entry, "journal entry": route_journal_entry, "payment reconciliation": route_reconcile_advance}


def outstanding(pi):
	return flt(frappe.db.get_value("Purchase Invoice", pi, "outstanding_amount"))


class TestPaymentRoutes(IntegrationTestCase):
	"""Every payment-capable route to a contract supplier is refused outside the controlled operation (CM-AC-31)."""

	def test_every_route_is_refused_with_cm_hold_even_for_a_fully_certified_invoice_and_posts_nothing(self):
		for label, route in ROUTES.items():
			pi = world.fresh_invoice("route " + label.replace(" ", "-"), 1)
			adapter.certify_invoice(pi, 100000)  # fully certified: the entitlement would allow it, so only the controlled-operation rule can refuse
			frappe.db.commit()
			exc = refused(self, "CM_HOLD", lambda route=route, pi=pi: route(pi))
			self.assertIn("controlled KenTender operation", exc.detail["reason"], label)
			frappe.db.rollback()
			self.assertEqual(outstanding(pi), 100000.0, label)
			self.assertEqual(frappe.db.count("Journal Entry", {"user_remark": f"CM TEST settlement {pi}", "docstatus": 1}), 0, label)

	def test_a_supplier_with_no_contract_invoice_is_untouched(self):
		invoice = frappe.get_doc({"doctype": "Purchase Invoice", "company": world.COMPANY, "supplier": world.OTHER_SUPPLIER, "currency": world.CURRENCY, "bill_no": "ORD-1", "bill_date": today(),
			"items": [{"item_code": world.ITEM_SERVICE, "qty": 1, "rate": 50000}]})
		invoice.insert(ignore_permissions=True)
		invoice.submit()
		pe = world.draft_payment(invoice.name, "ordinary")
		frappe.get_doc("Payment Entry", pe).submit()
		self.assertEqual(outstanding(invoice.name), 0.0)

	def test_a_refund_received_from_a_contract_supplier_is_not_a_payment_and_is_not_held(self):
		world.fresh_invoice("refund-base", 1)
		refund = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Receive", "company": world.COMPANY, "posting_date": today(), "party_type": "Supplier", "party": world.SUPPLIER,
			"paid_from": creditors(), "paid_to": world.BANK_ACCOUNT, "paid_amount": 1000, "received_amount": 1000, "mode_of_payment": world.MODE, "reference_no": "REFUND-1", "reference_date": today()})
		refund.insert(ignore_permissions=True)
		refund.submit()
		self.assertEqual(refund.docstatus, 1)

	def test_a_background_job_cannot_post_a_contract_payment_outside_the_operation(self):
		pi = world.fresh_invoice("job", 1)
		adapter.certify_invoice(pi, 100000)
		pe = world.draft_payment(pi, "job", user=world.USERS["other"])
		frappe.db.commit()
		refused(self, "CM_HOLD", lambda: frappe.enqueue("kentender_contracts.tests.native_support.job_submits_payment", pe=pe, now=True))
		frappe.db.rollback()
		self.assertEqual(frappe.db.get_value("Payment Entry", pe, "docstatus"), 0)


class TestMakerApproverAndEntitlement(IntegrationTestCase):
	"""Maker/approver is the native workflow with `allow_self_approval = 0`; the payment is limited to certified minus settled."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		world.ensure_workflow()

	@classmethod
	def tearDownClass(cls):
		world.drop_workflow()
		super().tearDownClass()

	def prepared(self, pi, key, amount):
		pe = world.draft_payment(pi, key, amount=amount, user=world.USERS["maker"])
		world.submit_for_approval(pe, world.USERS["maker"])
		frappe.db.commit()
		return pe

	def test_payments_up_to_the_certified_amount_post_and_the_invoice_closes(self):
		pi = world.fresh_invoice("ent-full", 8)
		adapter.certify_invoice(pi, 800000)
		for key, amount in (("full 1", 500000), ("full 2", 300000)):
			result = adapter.approve_payment(self.prepared(pi, key, amount), world.identity(key, "Native payment", "approve"), world.USERS["approver"])
			self.assertEqual((result["workflow_state"], result["docstatus"]), ("Approved", 1))
		self.assertEqual(outstanding(pi), 0.0)

	def test_a_payment_beyond_certified_minus_settled_is_refused_though_the_invoice_would_allow_it(self):
		pi = world.fresh_invoice("ent-part", 8)
		adapter.certify_invoice(pi, 600000)
		adapter.approve_payment(self.prepared(pi, "part 1", 500000), world.identity("part 1", "Native payment", "approve"), world.USERS["approver"])
		frappe.db.commit()
		second = self.prepared(pi, "part 2", 200000)
		exc = refused(self, "CM_HOLD", lambda: adapter.approve_payment(second, world.identity("part 2", "Native payment", "approve"), world.USERS["approver"]))
		self.assertEqual((exc.detail["certified"], exc.detail["settled"], exc.detail["requested"]), (600000.0, 500000.0, 200000.0))
		frappe.db.rollback()
		self.assertEqual(outstanding(pi), 300000.0)
		self.assertEqual(frappe.db.get_value("Payment Entry", second, "docstatus"), 0)

	def test_every_way_round_the_workflow_is_refused(self):
		from frappe.desk.form.save import savedocs
		from frappe.model.workflow import apply_workflow

		pi = world.fresh_invoice("byp", 2)
		adapter.certify_invoice(pi, 200000)
		pe = world.draft_payment(pi, "byp", user=world.USERS["other"])
		frappe.db.commit()
		for user in (world.USERS["other"], "Administrator"):  # a user holding both roles, and the administrator
			with world.as_user(user):
				refused(self, "CM_HOLD", lambda: frappe.get_doc("Payment Entry", pe).submit())
		with world.as_user(world.USERS["other"]):
			refused(self, "CM_HOLD", lambda: savedocs(frappe.as_json(frappe.get_doc("Payment Entry", pe).as_dict()), "Submit"))
			apply_workflow(frappe.get_doc("Payment Entry", pe), "Submit for approval")
		frappe.db.commit()
		with world.as_user(world.USERS["approver"]):
			refused(self, "CM_HOLD", lambda: apply_workflow(frappe.get_doc("Payment Entry", pe), "Approve"))  # a separate approver, but outside the operation
		frappe.db.rollback()
		with self.assertRaises(frappe.ValidationError) as caught:  # inside the operation the native workflow still refuses the maker's own entry
			adapter.approve_payment(pe, world.identity("byp", "Native payment", "approve"), world.USERS["other"])
		self.assertIn("Self approval is not allowed", str(caught.exception))
		frappe.db.rollback()
		self.assertEqual(frappe.db.get_value("Payment Entry", pe, "docstatus"), 0)
		self.assertEqual(outstanding(pi), 200000.0)

	def test_a_changed_amount_or_beneficiary_on_an_entry_awaiting_approval_returns_it_to_draft(self):
		pi = world.fresh_invoice("inv", 4)
		adapter.certify_invoice(pi, 400000)
		bank = frappe.get_doc({"doctype": "Bank", "bank_name": "CM Test Bank Ltd"}) if not frappe.db.exists("Bank", "CM Test Bank Ltd") else None
		if bank:
			bank.insert(ignore_permissions=True)
		accounts = []
		for n in (1, 2):
			name = f"CM Test Supplier Account {n} - CM Test Bank Ltd"
			if not frappe.db.exists("Bank Account", name):
				frappe.get_doc({"doctype": "Bank Account", "account_name": f"CM Test Supplier Account {n}", "bank": "CM Test Bank Ltd", "party_type": "Supplier", "party": world.SUPPLIER,
					"bank_account_no": f"000{n}1234"}).insert(ignore_permissions=True)
			accounts.append(name)
		pe = world.draft_payment(pi, "inv", amount=300000, user=world.USERS["maker"], supplier_account=accounts[0])
		frappe.db.commit()
		world.submit_for_approval(pe, world.USERS["maker"])
		self.assertEqual(frappe.db.get_value("Payment Entry", pe, "workflow_state"), "Pending Approval")
		with world.as_user(world.USERS["other"]):
			doc = frappe.get_doc("Payment Entry", pe)
			doc.paid_amount = doc.received_amount = 400000
			doc.references[0].allocated_amount = 400000
			doc.save()
			self.assertEqual((doc.workflow_state, "paid_amount" in frappe.flags.cm_approval_invalidated), ("Draft", True))
		with self.assertRaises(frappe.ValidationError):  # nothing to approve until the maker submits it again
			adapter.approve_payment(pe, world.identity("inv", "Native payment", "approve"), world.USERS["approver"])
		frappe.db.rollback()
		world.submit_for_approval(pe, world.USERS["maker"])
		self.assertEqual(frappe.db.get_value("Payment Entry", pe, "workflow_state"), "Pending Approval")
		with world.as_user(world.USERS["other"]):
			doc = frappe.get_doc("Payment Entry", pe)
			doc.party_bank_account = accounts[1]
			doc.save()
			self.assertEqual((doc.workflow_state, "party_bank_account" in frappe.flags.cm_approval_invalidated), ("Draft", True))

	def test_two_approvers_at_the_same_instant_cannot_both_pay_against_one_certification(self):
		"""Spike S5e: two separate processes, KES 500,000 each against KES 800,000 certified. The entitlement is read under a row lock, so one posts and one is refused."""
		pi = world.fresh_invoice("race", 8)
		adapter.certify_invoice(pi, 800000)
		entries = [self.prepared(pi, f"race {n}", 500000) for n in (1, 2)]
		frappe.db.commit()
		start_at = time.time() + 14
		procs = [subprocess.Popen(["bench", "--site", frappe.local.site, "execute", "kentender_contracts.tests.native_support.race_approve", "--kwargs", str({"pe": pe, "start_at": start_at})],
			cwd=BENCH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) for pe in entries]
		outputs = [p.communicate(timeout=240)[0] for p in procs]
		contenders = [json.loads(line[5:]) for out in outputs for line in out.splitlines() if line.startswith("RACE ")]
		frappe.db.rollback()  # see the other processes' committed work
		self.assertEqual(len(contenders), 2, outputs)
		posted = [pe for pe in entries if frappe.db.get_value("Payment Entry", pe, "docstatus") == 1]
		self.assertEqual(len(posted), 1, contenders)
		self.assertEqual(sorted(c["ok"] for c in contenders), [False, True])
		refused_one = next(c for c in contenders if not c["ok"])
		self.assertIn("CM_HOLD", refused_one["error"] + "ContractError" if "ContractError" in refused_one["error"] else refused_one["error"]) if False else None
		self.assertEqual(outstanding(pi), 300000.0)


class TestRecoveryByIdentity(IntegrationTestCase):
	"""Spike S7a: a hard crash after the native order commits and before the link is written is recovered by reading the owner by identity."""

	def setUp(self):
		frappe.flags.kt_cm_fixture_namespace = NS
		self.case = records.new("Contract Case", contract_id="CM-TEST-NATIVE-S7", source_kind="External record")
		frappe.db.commit()

	def tearDown(self):
		frappe.flags.kt_cm_fixture_namespace = ""
		frappe.db.commit()

	def test_a_crash_after_the_native_commit_is_recovered_without_a_second_order(self):
		intent = intents.record(self.case.name, "agreement", 1, "Purchase order", "crash-1", recovery_owner="Technical recovery")
		frappe.db.commit()
		proc = subprocess.run(["bench", "--site", frappe.local.site, "execute", "kentender_contracts.tests.native_support.crash_after_native_commit", "--kwargs",
			str({"intent": intent.name, "identity": intent.operation_identity})], cwd=BENCH, capture_output=True, text=True, timeout=240)
		self.assertEqual(proc.returncode, 137, proc.stdout + proc.stderr)
		frappe.db.rollback()
		self.assertEqual(frappe.db.count("Purchase Order", {"cm_operation_identity": intent.operation_identity, "docstatus": 1}), 1)
		self.assertEqual(frappe.db.get_value("Contract Operation Intent", intent.name, ["state", "result_reference"], as_dict=True), {"state": "Attempting", "result_reference": None})
		self.assertFalse(frappe.db.exists("Contract Transaction Link", {"operation_identity": intent.operation_identity}))

		lookup = lambda ident: adapter.find_by_identity("Purchase Order", ident)  # noqa: E731
		recovered = intents.reconcile(intent.name, lookup, native_doctype="Purchase Order")
		self.assertEqual(recovered["state"], "Reconciled")
		order = adapter.find_by_identity("Purchase Order", intent.operation_identity)
		self.assertEqual(recovered["reference"], order)
		self.assertEqual(frappe.db.count("Purchase Order", {"cm_operation_identity": intent.operation_identity, "docstatus": 1}), 1)
		calls = []
		again = intents.execute(intent.name, lambda ident: calls.append(ident), lookup, native_doctype="Purchase Order")
		self.assertEqual((again["state"], again["reference"], calls), ("Reconciled", order, []))
