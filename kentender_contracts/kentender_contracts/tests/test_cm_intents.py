# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §5.17, §7 last paragraph, §12 and plan D5 (tracker CM8-302): every cross-owner or uncertain effect is one
durable intent with one operation identity. The owner is read first by that identity, so a retry after a crash links what exists
instead of creating a second document; one native document belongs to one operation.

The owner here is a fake registry, so the state machine is proved on its own; the real ERPNext adapter is proved separately
(`test_cm_native`, L2)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.services import errors, intents, records

NS = "CM_TEST"
OWNER: dict[str, str] = {}  # operation identity -> native document name (the fake owner)


class Refused(intents.OwnerRefused):
	pass


def lookup(identity: str):
	return OWNER.get(identity)


class TestContractIntents(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = NS
		OWNER.clear()
		self.case = records.new("Contract Case", contract_id="CM-TEST-I1", source_kind="External record")
		frappe.db.commit()

	def tearDown(self) -> None:
		frappe.flags.kt_cm_fixture_namespace = ""
		records.wipe(NS)
		frappe.db.commit()

	def intent(self, key="k-1", kind="Purchase order", subject="agreement 1", version=1):
		return intents.record(self.case.name, subject, version, kind, key, recovery_owner="Technical recovery")

	# -- identity and recording ----------------------------------------------------------------------------------
	def test_identity_names_case_subject_version_kind_and_key(self):
		self.assertEqual(intents.identity("CM-1", "agreement 1", 2, "Purchase order", "k"), "CM-1|agreement 1|2|Purchase order|k")

	def test_recording_twice_returns_the_same_intent_in_state_recorded(self):
		a, b = self.intent(), self.intent()
		self.assertEqual(a.name, b.name)
		self.assertEqual((a.state, a.recovery_owner), ("Recorded", "Technical recovery"))
		self.assertEqual(frappe.db.count("Contract Operation Intent", {"fixture_namespace": NS}), 1)

	def test_an_unknown_kind_is_refused(self):
		with self.assertRaises(errors.InputError):
			intents.record(self.case.name, "x", 1, "Not a kind", "k", recovery_owner="x")

	# -- execution -------------------------------------------------------------------------------------------------
	def test_a_successful_execution_links_the_native_document_once_and_a_replay_does_not_call_the_owner(self):
		intent, calls = self.intent(), []

		def create(identity):
			calls.append(identity)
			OWNER[identity] = "PUR-ORD-1"
			return "PUR-ORD-1", "Purchase Order"

		first = intents.execute(intent.name, create, lookup)
		second = intents.execute(intent.name, create, lookup)
		self.assertEqual((first["state"], first["reference"], second["reference"]), ("Succeeded", "PUR-ORD-1", "PUR-ORD-1"))
		self.assertEqual(len(calls), 1)
		link = frappe.db.get_value("Contract Transaction Link", {"operation_identity": intent.operation_identity}, ["native_doctype", "native_name", "contract_case"], as_dict=True)
		self.assertEqual((link.native_doctype, link.native_name, link.contract_case), ("Purchase Order", "PUR-ORD-1", self.case.name))

	def test_the_owner_is_read_first_so_an_existing_document_is_linked_not_recreated(self):
		intent = self.intent()
		OWNER[intent.operation_identity] = "PUR-ORD-EXISTING"  # the native commit survived a crash before the link was written

		def create(identity):
			raise AssertionError("the owner must not be asked to create what already exists")

		result = intents.execute(intent.name, create, lookup, native_doctype="Purchase Order")
		self.assertEqual((result["state"], result["reference"]), ("Reconciled", "PUR-ORD-EXISTING"))

	def test_an_unexpected_failure_leaves_the_outcome_uncertain_and_the_retry_reconciles_without_a_second_document(self):
		intent = self.intent()

		def crash_after_native_commit(identity):
			OWNER[identity] = "PUR-ORD-7"
			raise RuntimeError("the connection dropped")

		first = intents.execute(intent.name, crash_after_native_commit, lookup)
		self.assertEqual((first["state"], first["reference"]), ("Uncertain", ""))
		self.assertEqual(frappe.db.get_value("Contract Operation Intent", intent.name, "state"), "Uncertain")

		def create(identity):
			raise AssertionError("a retry must read the owner first")

		retry = intents.execute(intent.name, create, lookup, native_doctype="Purchase Order")
		self.assertEqual((retry["state"], retry["reference"]), ("Reconciled", "PUR-ORD-7"))
		self.assertEqual(len(OWNER), 1)

	def test_a_definitive_refusal_is_failed_and_a_retry_after_the_fix_runs_again(self):
		intent = self.intent()

		def refuse(identity):
			raise Refused("The native document was refused")

		failed = intents.execute(intent.name, refuse, lookup)
		self.assertEqual((failed["state"], failed["reference"]), ("Failed", ""))
		self.assertIn("refused", failed["detail"].lower())
		self.assertFalse(frappe.db.exists("Contract Transaction Link", {"operation_identity": intent.operation_identity}))

		def create(identity):
			OWNER[identity] = "PUR-ORD-9"
			return "PUR-ORD-9", "Purchase Order"

		fixed = intents.execute(intent.name, create, lookup)
		self.assertEqual((fixed["state"], fixed["reference"]), ("Succeeded", "PUR-ORD-9"))

	def test_every_attempt_is_retained_with_its_outcome(self):
		intent = self.intent()
		intents.execute(intent.name, lambda i: (_ for _ in ()).throw(RuntimeError("down")), lookup)
		intents.execute(intent.name, lambda i: OWNER.setdefault(i, "PUR-ORD-2") and ("PUR-ORD-2", "Purchase Order"), lookup)
		attempts = records.loads(frappe.db.get_value("Contract Operation Intent", intent.name, "attempts_json"), [])
		self.assertEqual([a["outcome"] for a in attempts], ["Uncertain", "Succeeded"])
		self.assertTrue(all(a.get("at") for a in attempts))

	def test_technical_reconciliation_only_reads_the_owner(self):
		intent = self.intent()
		intents.execute(intent.name, lambda i: (_ for _ in ()).throw(RuntimeError("down")), lookup)
		self.assertIsNone(intents.reconcile(intent.name, lookup)["reference"] or None)
		OWNER[intent.operation_identity] = "PUR-ORD-3"
		found = intents.reconcile(intent.name, lookup, native_doctype="Purchase Order")
		self.assertEqual((found["state"], found["reference"]), ("Reconciled", "PUR-ORD-3"))

	# -- links -----------------------------------------------------------------------------------------------------
	def test_one_native_document_cannot_belong_to_two_operations(self):
		a, b = self.intent("k-a"), self.intent("k-b")
		OWNER[a.operation_identity] = "PUR-ORD-SAME"
		OWNER[b.operation_identity] = "PUR-ORD-SAME"
		intents.execute(a.name, lambda i: ("PUR-ORD-SAME", "Purchase Order"), lookup, native_doctype="Purchase Order")
		with self.assertRaises(errors.ContractError) as caught:
			intents.execute(b.name, lambda i: ("PUR-ORD-SAME", "Purchase Order"), lookup, native_doctype="Purchase Order")
		self.assertEqual(caught.exception.code, "CM_DUPLICATE")

	# -- the truthful state ------------------------------------------------------------------------------------------
	def test_the_pending_operations_of_a_case_are_those_not_yet_succeeded_or_reconciled(self):
		done, pending, broken = self.intent("k-1"), self.intent("k-2", "Accepted receipt"), self.intent("k-3", "Native invoice")
		intents.execute(done.name, lambda i: OWNER.setdefault(i, "A") and ("A", "Purchase Order"), lookup)
		intents.execute(broken.name, lambda i: (_ for _ in ()).throw(RuntimeError("down")), lookup)
		states = {r["kind"]: r["state"] for r in intents.pending(self.case.name)}
		self.assertEqual(states, {"Accepted receipt": "Recorded", "Native invoice": "Uncertain"})
		self.assertEqual({r["kind"]: r["recovery_owner"] for r in intents.pending(self.case.name)}["Native invoice"], "Technical recovery")
